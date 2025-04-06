"""
Integration module for connecting the embedding pipeline with vector databases.
"""

import os
import json
import asyncio
from typing import List, Dict, Any, Optional, Union

from docucrawler.utils.common import load_json
from docucrawler.vectordb.factory import VectorDBFactory
from docucrawler.vectordb.base import BaseVectorDB


async def store_embeddings(input_dir: str, 
                          db_type: str = 'pgvector', 
                          collection_name: Optional[str] = None,
                          config: Optional[Dict[str, Any]] = None) -> List[str]:
    """Store embeddings from files in a directory to a vector database.
    
    Args:
        input_dir: Directory containing embedding files
        db_type: Type of vector database to use
        collection_name: Name of the collection to store embeddings in (defaults to directory name)
        config: Configuration for the vector database
        
    Returns:
        List of document IDs that were stored
    """
    # Determine collection name if not provided
    if collection_name is None:
        collection_name = os.path.basename(input_dir)
    
    # Create vector database
    vector_db = VectorDBFactory.create_vector_db(db_type, config)
    
    # Connect to vector database
    connected = await vector_db.connect()
    if not connected:
        print(f"Failed to connect to {db_type} database")
        return []
    
    try:
        # Create collection
        dimension = 768  # Default dimension
        created = await vector_db.create_collection(collection_name, dimension)
        if not created:
            print(f"Failed to create collection '{collection_name}'")
            return []
        
        # Get embedding files
        files = [f for f in os.listdir(input_dir) if f.endswith('_embedded.json')]
        if not files:
            print(f"No embedding files found in {input_dir}")
            return []
        
        # Store embeddings
        stored_ids = []
        for filename in files:
            filepath = os.path.join(input_dir, filename)
            
            try:
                # Load embedding file
                data = load_json(filepath)
                
                # Skip if no embedding
                if 'embedding' not in data:
                    print(f"No embedding found in {filepath}, skipping")
                    continue
                
                # Extract document ID from filename
                document_id = filename.replace('_embedded.json', '')
                
                # Store embedding
                success = await vector_db.insert_document(
                    collection_name=collection_name,
                    document_id=document_id,
                    embedding=data['embedding'],
                    metadata={
                        'title': data.get('title', ''),
                        'summary': data.get('summary', ''),
                        'content': data.get('content', ''),
                        'metadata': data.get('metadata', {})
                    }
                )
                
                if success:
                    stored_ids.append(document_id)
                    print(f"Stored embedding for document '{document_id}'")
                else:
                    print(f"Failed to store embedding for document '{document_id}'")
            
            except Exception as e:
                print(f"Error processing {filepath}: {e}")
        
        return stored_ids
    
    finally:
        # Disconnect from vector database
        await vector_db.disconnect()


async def search_documents(query_embedding: List[float], 
                          db_type: str = 'pgvector', 
                          collection_name: str = 'default',
                          limit: int = 10,
                          filters: Optional[Dict[str, Any]] = None,
                          config: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Search for similar documents in a vector database.
    
    Args:
        query_embedding: Query embedding as a list of floats
        db_type: Type of vector database to use
        collection_name: Name of the collection to search in
        limit: Maximum number of results to return
        filters: Optional filters to apply to the search
        config: Configuration for the vector database
        
    Returns:
        List of documents with their metadata and similarity scores
    """
    # Create vector database
    vector_db = VectorDBFactory.create_vector_db(db_type, config)
    
    # Connect to vector database
    connected = await vector_db.connect()
    if not connected:
        print(f"Failed to connect to {db_type} database")
        return []
    
    try:
        # Search for similar documents
        results = await vector_db.search(
            collection_name=collection_name,
            query_embedding=query_embedding,
            limit=limit,
            filters=filters
        )
        
        return results
    
    finally:
        # Disconnect from vector database
        await vector_db.disconnect()


async def delete_document(document_id: str, 
                         db_type: str = 'pgvector', 
                         collection_name: str = 'default',
                         config: Optional[Dict[str, Any]] = None) -> bool:
    """Delete a document from a vector database.
    
    Args:
        document_id: Unique identifier for the document
        db_type: Type of vector database to use
        collection_name: Name of the collection to delete from
        config: Configuration for the vector database
        
    Returns:
        True if deletion is successful, False otherwise
    """
    # Create vector database
    vector_db = VectorDBFactory.create_vector_db(db_type, config)
    
    # Connect to vector database
    connected = await vector_db.connect()
    if not connected:
        print(f"Failed to connect to {db_type} database")
        return False
    
    try:
        # Delete document
        success = await vector_db.delete_document(
            collection_name=collection_name,
            document_id=document_id
        )
        
        return success
    
    finally:
        # Disconnect from vector database
        await vector_db.disconnect()


async def delete_collection(collection_name: str, 
                           db_type: str = 'pgvector',
                           config: Optional[Dict[str, Any]] = None) -> bool:
    """Delete a collection from a vector database.
    
    Args:
        collection_name: Name of the collection to delete
        db_type: Type of vector database to use
        config: Configuration for the vector database
        
    Returns:
        True if deletion is successful, False otherwise
    """
    # Create vector database
    vector_db = VectorDBFactory.create_vector_db(db_type, config)
    
    # Connect to vector database
    connected = await vector_db.connect()
    if not connected:
        print(f"Failed to connect to {db_type} database")
        return False
    
    try:
        # Delete collection
        success = await vector_db.delete_collection(collection_name)
        
        return success
    
    finally:
        # Disconnect from vector database
        await vector_db.disconnect()