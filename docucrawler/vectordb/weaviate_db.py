"""
Weaviate database implementation for storing and searching document embeddings.
"""

import os
import json
import uuid
import numpy as np
from typing import List, Dict, Any, Optional, Union, Tuple
from urllib.parse import urlparse

from docucrawler.vectordb.base import BaseVectorDB

# Import Weaviate
try:
    import weaviate
    from weaviate.util import generate_uuid5
except ImportError:
    raise ImportError("weaviate-client package is required. Install it with 'pip install weaviate-client'")


class WeaviateDB(BaseVectorDB):
    """Weaviate database implementation."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the Weaviate database.
        
        Args:
            config: Dictionary containing Weaviate configuration
        """
        super().__init__(config)
        
        # Extract configuration
        self.url = config.get('url', 'http://localhost:8080')
        self.api_key = config.get('api_key')
        self.class_prefix = config.get('class_prefix', 'DocuCrawler')
        
        # Initialize client
        self.client = None
        
        # Track created collections and their dimensions
        self.collections = {}
    
    async def connect(self) -> bool:
        """Connect to the Weaviate database.
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            # Create auth configuration
            auth_config = None
            if self.api_key:
                auth_config = weaviate.auth.AuthApiKey(api_key=self.api_key)
            
            # Create client
            self.client = weaviate.Client(
                url=self.url,
                auth_client_secret=auth_config
            )
            
            # Check connection
            meta = self.client.get_meta()
            print(f"Successfully connected to Weaviate {meta['version']}")
            return True
        except Exception as e:
            print(f"Error connecting to Weaviate: {e}")
            return False
    
    async def create_collection(self, collection_name: str, dimension: int = 768) -> bool:
        """Create a collection in the Weaviate database.
        
        Args:
            collection_name: Name of the collection to create
            dimension: Dimension of the vectors to store
            
        Returns:
            True if creation is successful, False otherwise
        """
        try:
            # Store collection dimension
            self.collections[collection_name] = dimension
            
            # Create class name (Weaviate requires PascalCase)
            class_name = f"{self.class_prefix}{collection_name.capitalize()}"
            
            # Check if class exists
            schema = self.client.schema.get()
            existing_classes = [cls['class'] for cls in schema['classes']] if 'classes' in schema else []
            
            if class_name in existing_classes:
                print(f"Class '{class_name}' already exists")
                return True
            
            # Create class
            class_obj = {
                "class": class_name,
                "description": f"Documents from {collection_name} collection",
                "vectorizer": "none",  # We'll provide our own vectors
                "properties": [
                    {
                        "name": "document_id",
                        "dataType": ["string"],
                        "description": "Unique identifier for the document",
                        "indexInverted": True
                    },
                    {
                        "name": "title",
                        "dataType": ["text"],
                        "description": "Document title",
                        "indexInverted": True
                    },
                    {
                        "name": "content",
                        "dataType": ["text"],
                        "description": "Document content",
                        "indexInverted": True
                    },
                    {
                        "name": "metadata",
                        "dataType": ["object"],
                        "description": "Document metadata",
                        "indexInverted": True
                    }
                ]
            }
            
            self.client.schema.create_class(class_obj)
            print(f"Successfully created class '{class_name}'")
            return True
        except Exception as e:
            print(f"Error creating class for collection '{collection_name}': {e}")
            return False
    
    async def insert_document(self, 
                             collection_name: str, 
                             document_id: str, 
                             embedding: Union[List[float], List[List[float]]], 
                             metadata: Dict[str, Any]) -> bool:
        """Insert a document with its embedding and metadata into the Weaviate database.
        
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
                embedding_vector = embedding[0]
            else:
                embedding_vector = embedding
            
            # Extract content and title from metadata
            content = metadata.get('content', '')
            title = metadata.get('title', '')
            
            # Create class name
            class_name = f"{self.class_prefix}{collection_name.capitalize()}"
            
            # Create document
            document = {
                "document_id": document_id,
                "title": title,
                "content": content,
                "metadata": metadata
            }
            
            # Generate UUID based on document_id for idempotency
            uuid_obj = generate_uuid5(document_id)
            
            # Insert document with vector
            self.client.data_object.create(
                data_object=document,
                class_name=class_name,
                uuid=uuid_obj,
                vector=embedding_vector
            )
            
            print(f"Successfully inserted document '{document_id}' into class '{class_name}'")
            return True
        except Exception as e:
            print(f"Error inserting document '{document_id}' into collection '{collection_name}': {e}")
            return False
    
    async def search(self, 
                    collection_name: str, 
                    query_embedding: List[float], 
                    limit: int = 10, 
                    filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search for similar documents in the Weaviate database.
        
        Args:
            collection_name: Name of the collection to search in
            query_embedding: Query embedding as a list of floats
            limit: Maximum number of results to return
            filters: Optional filters to apply to the search
            
        Returns:
            List of documents with their metadata and similarity scores
        """
        try:
            # Create class name
            class_name = f"{self.class_prefix}{collection_name.capitalize()}"
            
            # Build query
            query = self.client.query.get(class_name, ["document_id", "title", "content", "metadata"])
            
            # Apply filters if provided
            if filters:
                filter_clauses = []
                for key, value in filters.items():
                    if key == 'title':
                        filter_clauses.append({
                            "path": ["title"],
                            "operator": "Like",
                            "valueText": f"*{value}*"
                        })
                    elif key == 'content':
                        filter_clauses.append({
                            "path": ["content"],
                            "operator": "Like",
                            "valueText": f"*{value}*"
                        })
                    elif key.startswith('metadata.'):
                        # Handle metadata filters
                        metadata_key = key.split('.', 1)[1]
                        filter_clauses.append({
                            "path": ["metadata", metadata_key],
                            "operator": "Equal",
                            "valueText": value
                        })
                
                if filter_clauses:
                    query = query.with_where({
                        "operator": "And",
                        "operands": filter_clauses
                    })
            
            # Execute search with vector
            results = query.with_near_vector({
                "vector": query_embedding,
                "certainty": 0.7  # Minimum similarity threshold
            }).with_limit(limit).do()
            
            # Format results
            formatted_results = []
            if "data" in results and "Get" in results["data"]:
                objects = results["data"]["Get"][class_name]
                for obj in objects:
                    formatted_results.append({
                        'id': obj['document_id'],
                        'title': obj.get('title', ''),
                        'content': obj.get('content', ''),
                        'metadata': obj.get('metadata', {}),
                        'similarity': obj.get('_additional', {}).get('certainty', 0.0)
                    })
            
            return formatted_results
        except Exception as e:
            print(f"Error searching in collection '{collection_name}': {e}")
            return []
    
    async def delete_document(self, collection_name: str, document_id: str) -> bool:
        """Delete a document from the Weaviate database.
        
        Args:
            collection_name: Name of the collection to delete from
            document_id: Unique identifier for the document
            
        Returns:
            True if deletion is successful, False otherwise
        """
        try:
            # Create class name
            class_name = f"{self.class_prefix}{collection_name.capitalize()}"
            
            # Generate UUID based on document_id
            uuid_obj = generate_uuid5(document_id)
            
            # Delete document
            self.client.data_object.delete(uuid=uuid_obj, class_name=class_name)
            
            print(f"Successfully deleted document '{document_id}' from class '{class_name}'")
            return True
        except Exception as e:
            print(f"Error deleting document '{document_id}' from collection '{collection_name}': {e}")
            return False
    
    async def delete_collection(self, collection_name: str) -> bool:
        """Delete a collection from the Weaviate database.
        
        Args:
            collection_name: Name of the collection to delete
            
        Returns:
            True if deletion is successful, False otherwise
        """
        try:
            # Create class name
            class_name = f"{self.class_prefix}{collection_name.capitalize()}"
            
            # Delete class
            self.client.schema.delete_class(class_name)
            
            # Remove collection from tracking
            if collection_name in self.collections:
                del self.collections[collection_name]
            
            print(f"Successfully deleted class '{class_name}'")
            return True
        except Exception as e:
            print(f"Error deleting collection '{collection_name}': {e}")
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect from the Weaviate database.
        
        Returns:
            True if disconnection is successful, False otherwise
        """
        try:
            # Weaviate client doesn't have a disconnect method
            self.client = None
            print("Successfully disconnected from Weaviate")
            return True
        except Exception as e:
            print(f"Error disconnecting from Weaviate: {e}")
            return False