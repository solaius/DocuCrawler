"""
Elasticsearch database implementation for storing and searching document embeddings.
"""

import os
import json
import numpy as np
from typing import List, Dict, Any, Optional, Union, Tuple
from urllib.parse import urlparse

from docucrawler.vectordb.base import BaseVectorDB

# Import Elasticsearch
try:
    from elasticsearch import AsyncElasticsearch
    from elasticsearch.helpers import async_bulk
except ImportError:
    raise ImportError("elasticsearch package is required. Install it with 'pip install elasticsearch'")


class ElasticsearchDB(BaseVectorDB):
    """Elasticsearch database implementation."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the Elasticsearch database.
        
        Args:
            config: Dictionary containing Elasticsearch configuration
        """
        super().__init__(config)
        
        # Extract configuration
        self.url = config.get('url', 'http://localhost:9200')
        self.index_prefix = config.get('index_prefix', 'docucrawler')
        self.username = config.get('user')
        self.password = config.get('password')
        
        # Initialize client
        self.client = None
        
        # Track created collections and their dimensions
        self.collections = {}
    
    async def connect(self) -> bool:
        """Connect to the Elasticsearch database.
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            # Create client
            auth = None
            if self.username and self.password:
                auth = (self.username, self.password)
            
            self.client = AsyncElasticsearch(
                [self.url],
                basic_auth=auth,
                verify_certs=False  # For development only, should be True in production
            )
            
            # Check connection
            info = await self.client.info()
            print(f"Successfully connected to Elasticsearch {info['version']['number']}")
            return True
        except Exception as e:
            print(f"Error connecting to Elasticsearch: {e}")
            return False
    
    async def create_collection(self, collection_name: str, dimension: int = 768) -> bool:
        """Create a collection in the Elasticsearch database.
        
        Args:
            collection_name: Name of the collection to create
            dimension: Dimension of the vectors to store
            
        Returns:
            True if creation is successful, False otherwise
        """
        try:
            # Store collection dimension
            self.collections[collection_name] = dimension
            
            # Create index name
            index_name = f"{self.index_prefix}_{collection_name}"
            
            # Check if index exists
            exists = await self.client.indices.exists(index=index_name)
            if exists:
                print(f"Index '{index_name}' already exists")
                return True
            
            # Create index with vector search capabilities
            index_settings = {
                "mappings": {
                    "properties": {
                        "id": {"type": "keyword"},
                        "title": {"type": "text"},
                        "content": {"type": "text"},
                        "metadata": {"type": "object"},
                        "embedding": {
                            "type": "dense_vector",
                            "dims": dimension,
                            "index": True,
                            "similarity": "cosine"
                        }
                    }
                },
                "settings": {
                    "number_of_shards": 1,
                    "number_of_replicas": 0
                }
            }
            
            await self.client.indices.create(index=index_name, body=index_settings)
            print(f"Successfully created index '{index_name}' with dimension {dimension}")
            return True
        except Exception as e:
            print(f"Error creating index for collection '{collection_name}': {e}")
            return False
    
    async def insert_document(self, 
                             collection_name: str, 
                             document_id: str, 
                             embedding: Union[List[float], List[List[float]]], 
                             metadata: Dict[str, Any]) -> bool:
        """Insert a document with its embedding and metadata into the Elasticsearch database.
        
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
            
            # Create document
            document = {
                "id": document_id,
                "title": title,
                "content": content,
                "metadata": metadata,
                "embedding": embedding_vector
            }
            
            # Insert document
            index_name = f"{self.index_prefix}_{collection_name}"
            await self.client.index(index=index_name, id=document_id, document=document)
            
            print(f"Successfully inserted document '{document_id}' into index '{index_name}'")
            return True
        except Exception as e:
            print(f"Error inserting document '{document_id}' into collection '{collection_name}': {e}")
            return False
    
    async def search(self, 
                    collection_name: str, 
                    query_embedding: List[float], 
                    limit: int = 10, 
                    filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search for similar documents in the Elasticsearch database.
        
        Args:
            collection_name: Name of the collection to search in
            query_embedding: Query embedding as a list of floats
            limit: Maximum number of results to return
            filters: Optional filters to apply to the search
            
        Returns:
            List of documents with their metadata and similarity scores
        """
        try:
            # Create index name
            index_name = f"{self.index_prefix}_{collection_name}"
            
            # Build query
            query = {
                "size": limit,
                "query": {
                    "script_score": {
                        "query": {"match_all": {}},
                        "script": {
                            "source": "cosineSimilarity(params.query_vector, 'embedding') + 1.0",
                            "params": {"query_vector": query_embedding}
                        }
                    }
                }
            }
            
            # Apply filters if provided
            if filters:
                filter_clauses = []
                for key, value in filters.items():
                    if key == 'title':
                        filter_clauses.append({"match": {"title": value}})
                    elif key == 'content':
                        filter_clauses.append({"match": {"content": value}})
                    elif key.startswith('metadata.'):
                        # Handle metadata filters
                        metadata_key = key.split('.', 1)[1]
                        filter_clauses.append({"match": {f"metadata.{metadata_key}": value}})
                
                if filter_clauses:
                    query["query"] = {
                        "bool": {
                            "must": [query["query"]],
                            "filter": filter_clauses
                        }
                    }
            
            # Execute search
            response = await self.client.search(index=index_name, body=query)
            
            # Format results
            results = []
            for hit in response['hits']['hits']:
                source = hit['_source']
                results.append({
                    'id': source['id'],
                    'title': source.get('title', ''),
                    'content': source.get('content', ''),
                    'metadata': source.get('metadata', {}),
                    'similarity': hit['_score'] - 1.0  # Adjust score to be between 0 and 1
                })
            
            return results
        except Exception as e:
            print(f"Error searching in collection '{collection_name}': {e}")
            return []
    
    async def delete_document(self, collection_name: str, document_id: str) -> bool:
        """Delete a document from the Elasticsearch database.
        
        Args:
            collection_name: Name of the collection to delete from
            document_id: Unique identifier for the document
            
        Returns:
            True if deletion is successful, False otherwise
        """
        try:
            # Create index name
            index_name = f"{self.index_prefix}_{collection_name}"
            
            # Delete document
            response = await self.client.delete(index=index_name, id=document_id, ignore=[404])
            
            if response.get('result') == 'deleted':
                print(f"Successfully deleted document '{document_id}' from index '{index_name}'")
                return True
            else:
                print(f"Document '{document_id}' not found in index '{index_name}'")
                return False
        except Exception as e:
            print(f"Error deleting document '{document_id}' from collection '{collection_name}': {e}")
            return False
    
    async def delete_collection(self, collection_name: str) -> bool:
        """Delete a collection from the Elasticsearch database.
        
        Args:
            collection_name: Name of the collection to delete
            
        Returns:
            True if deletion is successful, False otherwise
        """
        try:
            # Create index name
            index_name = f"{self.index_prefix}_{collection_name}"
            
            # Delete index
            response = await self.client.indices.delete(index=index_name, ignore=[404])
            
            if response.get('acknowledged', False):
                print(f"Successfully deleted index '{index_name}'")
                
                # Remove collection from tracking
                if collection_name in self.collections:
                    del self.collections[collection_name]
                
                return True
            else:
                print(f"Index '{index_name}' not found")
                return False
        except Exception as e:
            print(f"Error deleting collection '{collection_name}': {e}")
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect from the Elasticsearch database.
        
        Returns:
            True if disconnection is successful, False otherwise
        """
        try:
            if self.client:
                await self.client.close()
            
            print("Successfully disconnected from Elasticsearch")
            return True
        except Exception as e:
            print(f"Error disconnecting from Elasticsearch: {e}")
            return False