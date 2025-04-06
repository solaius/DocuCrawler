"""
PGVector database implementation for storing and searching document embeddings.
"""

import os
import json
import numpy as np
from typing import List, Dict, Any, Optional, Union, Tuple
from urllib.parse import urlparse
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, String, Text, Integer, Float, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.future import select
from sqlalchemy.sql import text

from docucrawler.vectordb.base import BaseVectorDB

# Import pgvector extension
try:
    from pgvector.sqlalchemy import Vector
except ImportError:
    raise ImportError("pgvector package is required. Install it with 'pip install pgvector'")

Base = declarative_base()

class Document(Base):
    """Document model for storing document metadata and embeddings."""
    
    __tablename__ = "documents"
    
    id = Column(String, primary_key=True)
    collection = Column(String, nullable=False, index=True)
    title = Column(String, nullable=True)
    content = Column(Text, nullable=True)
    doc_metadata = Column(JSONB, nullable=True)  # Renamed from 'metadata' to avoid conflict
    embedding = Column(Vector(768))  # Default dimension, will be set dynamically
    
    def __repr__(self):
        return f"<Document(id='{self.id}', collection='{self.collection}', title='{self.title}')>"


class PGVectorDB(BaseVectorDB):
    """PGVector database implementation."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the PGVector database.
        
        Args:
            config: Dictionary containing PGVector configuration
        """
        super().__init__(config)
        
        # Extract configuration
        self.host = self._extract_host_from_url(config.get('url', 'http://localhost:5432'))
        self.port = self._extract_port_from_url(config.get('url', 'http://localhost:5432'))
        self.database = config.get('db', 'postgres')
        self.user = config.get('user', 'postgres')
        self.password = config.get('password', 'postgres')
        
        # Create connection string
        self.connection_string = f"postgresql+psycopg2://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
        self.async_connection_string = f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
        
        # Initialize engine and session
        self.engine = None
        self.async_engine = None
        self.async_session = None
        self.Session = None
        
        # Track created collections and their dimensions
        self.collections = {}
    
    def _extract_host_from_url(self, url: str) -> str:
        """Extract host from URL.
        
        Args:
            url: URL to extract host from
            
        Returns:
            Host part of the URL
        """
        # Handle special case for IP addresses without protocol
        if url and not url.startswith(('http://', 'https://')):
            # Check if it's an IP address with port
            if ':' in url:
                return url.split(':')[0]
            return url
            
        parsed_url = urlparse(url)
        return parsed_url.hostname or 'localhost'
    
    def _extract_port_from_url(self, url: str) -> int:
        """Extract port from URL.
        
        Args:
            url: URL to extract port from
            
        Returns:
            Port part of the URL
        """
        # Handle special case for IP addresses without protocol
        if url and not url.startswith(('http://', 'https://')):
            # Check if it's an IP address with port
            if ':' in url:
                try:
                    return int(url.split(':')[1])
                except (IndexError, ValueError):
                    return 5432
            return 5432
            
        parsed_url = urlparse(url)
        return parsed_url.port or 5432
    
    async def connect(self) -> bool:
        """Connect to the PGVector database.
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            # Create synchronous engine for setup operations
            self.engine = sa.create_engine(self.connection_string)
            
            # Create asynchronous engine for async operations
            self.async_engine = create_async_engine(self.async_connection_string)
            self.async_session = sessionmaker(
                self.async_engine, expire_on_commit=False, class_=AsyncSession
            )
            
            # Create pgvector extension if it doesn't exist
            with self.engine.connect() as conn:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                conn.commit()
            
            print(f"Successfully connected to PGVector database at {self.host}:{self.port}")
            return True
        except Exception as e:
            print(f"Error connecting to PGVector database: {e}")
            return False
    
    async def create_collection(self, collection_name: str, dimension: int = 768) -> bool:
        """Create a collection in the PGVector database.
        
        Args:
            collection_name: Name of the collection to create
            dimension: Dimension of the vectors to store
            
        Returns:
            True if creation is successful, False otherwise
        """
        try:
            # Store collection dimension
            self.collections[collection_name] = dimension
            
            # Create tables if they don't exist
            # We're using the same table for all collections, differentiating by the collection column
            async with self.async_engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            
            print(f"Successfully created collection '{collection_name}' with dimension {dimension}")
            return True
        except Exception as e:
            print(f"Error creating collection '{collection_name}': {e}")
            return False
    
    async def insert_document(self, 
                             collection_name: str, 
                             document_id: str, 
                             embedding: Union[List[float], List[List[float]]], 
                             metadata: Dict[str, Any]) -> bool:
        """Insert a document with its embedding and metadata into the PGVector database.
        
        Args:
            collection_name: Name of the collection to insert into
            document_id: Unique identifier for the document
            embedding: Document embedding as a list of floats or list of list of floats
            metadata: Document metadata
            
        Returns:
            True if insertion is successful, False otherwise
        """
        try:
            # Handle case where embedding is a list of embeddings (chunked content)
            if isinstance(embedding, list) and isinstance(embedding[0], list):
                # For simplicity, we'll use the first embedding for now
                # In a more advanced implementation, we might want to store all embeddings
                embedding_vector = embedding[0]
            else:
                embedding_vector = embedding
            
            # Extract content and title from metadata
            content = metadata.get('content', '')
            title = metadata.get('title', '')
            
            # Create document
            document = Document(
                id=document_id,
                collection=collection_name,
                title=title,
                content=content,
                doc_metadata=metadata,
                embedding=embedding_vector
            )
            
            # Insert document
            async with self.async_session() as session:
                async with session.begin():
                    # Check if document already exists
                    stmt = select(Document).where(
                        Document.id == document_id,
                        Document.collection == collection_name
                    )
                    result = await session.execute(stmt)
                    existing_document = result.scalar_one_or_none()
                    
                    if existing_document:
                        # Update existing document
                        existing_document.title = title
                        existing_document.content = content
                        existing_document.doc_metadata = metadata
                        existing_document.embedding = embedding_vector
                    else:
                        # Insert new document
                        session.add(document)
            
            print(f"Successfully inserted document '{document_id}' into collection '{collection_name}'")
            return True
        except Exception as e:
            print(f"Error inserting document '{document_id}' into collection '{collection_name}': {e}")
            return False
    
    async def search(self, 
                    collection_name: str, 
                    query_embedding: List[float], 
                    limit: int = 10, 
                    filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search for similar documents in the PGVector database.
        
        Args:
            collection_name: Name of the collection to search in
            query_embedding: Query embedding as a list of floats
            limit: Maximum number of results to return
            filters: Optional filters to apply to the search
            
        Returns:
            List of documents with their metadata and similarity scores
        """
        try:
            async with self.async_session() as session:
                # Build query
                query = select(
                    Document,
                    # Calculate cosine similarity
                    (Document.embedding.cosine_distance(query_embedding)).label('distance')
                ).where(
                    Document.collection == collection_name
                ).order_by(
                    sa.text('distance')  # Order by distance (ascending)
                ).limit(limit)
                
                # Apply filters if provided
                if filters:
                    for key, value in filters.items():
                        if key == 'title':
                            query = query.where(Document.title.ilike(f"%{value}%"))
                        elif key == 'content':
                            query = query.where(Document.content.ilike(f"%{value}%"))
                        elif key.startswith('metadata.'):
                            # Handle metadata filters
                            metadata_key = key.split('.', 1)[1]
                            query = query.where(Document.doc_metadata[metadata_key].astext == str(value))
                
                # Execute query
                result = await session.execute(query)
                rows = result.all()
                
                # Format results
                results = []
                for row in rows:
                    document, distance = row
                    results.append({
                        'id': document.id,
                        'title': document.title,
                        'content': document.content,
                        'metadata': document.doc_metadata,
                        'similarity': 1.0 - distance  # Convert distance to similarity score
                    })
                
                return results
        except Exception as e:
            print(f"Error searching in collection '{collection_name}': {e}")
            return []
    
    async def delete_document(self, collection_name: str, document_id: str) -> bool:
        """Delete a document from the PGVector database.
        
        Args:
            collection_name: Name of the collection to delete from
            document_id: Unique identifier for the document
            
        Returns:
            True if deletion is successful, False otherwise
        """
        try:
            async with self.async_session() as session:
                async with session.begin():
                    stmt = select(Document).where(
                        Document.id == document_id,
                        Document.collection == collection_name
                    )
                    result = await session.execute(stmt)
                    document = result.scalar_one_or_none()
                    
                    if document:
                        await session.delete(document)
                        print(f"Successfully deleted document '{document_id}' from collection '{collection_name}'")
                        return True
                    else:
                        print(f"Document '{document_id}' not found in collection '{collection_name}'")
                        return False
        except Exception as e:
            print(f"Error deleting document '{document_id}' from collection '{collection_name}': {e}")
            return False
    
    async def delete_collection(self, collection_name: str) -> bool:
        """Delete a collection from the PGVector database.
        
        Args:
            collection_name: Name of the collection to delete
            
        Returns:
            True if deletion is successful, False otherwise
        """
        try:
            async with self.async_session() as session:
                async with session.begin():
                    # Delete all documents in the collection
                    stmt = sa.delete(Document).where(Document.collection == collection_name)
                    await session.execute(stmt)
            
            # Remove collection from tracking
            if collection_name in self.collections:
                del self.collections[collection_name]
            
            print(f"Successfully deleted collection '{collection_name}'")
            return True
        except Exception as e:
            print(f"Error deleting collection '{collection_name}': {e}")
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect from the PGVector database.
        
        Returns:
            True if disconnection is successful, False otherwise
        """
        try:
            if self.engine:
                self.engine.dispose()
            
            if self.async_engine:
                await self.async_engine.dispose()
            
            print("Successfully disconnected from PGVector database")
            return True
        except Exception as e:
            print(f"Error disconnecting from PGVector database: {e}")
            return False