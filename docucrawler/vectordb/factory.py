"""
Vector database factory for creating vector database instances.
"""

import os
from typing import Dict, Any, Optional

from docucrawler.vectordb.base import BaseVectorDB
from docucrawler.vectordb.pgvector_db import PGVectorDB
from docucrawler.vectordb.elasticsearch_db import ElasticsearchDB
from docucrawler.vectordb.weaviate_db import WeaviateDB


class VectorDBFactory:
    """Factory for creating vector database instances."""
    
    @staticmethod
    def create_vector_db(db_type: str, config: Optional[Dict[str, Any]] = None) -> BaseVectorDB:
        """Create a vector database instance.
        
        Args:
            db_type: Type of vector database to create
            config: Configuration for the vector database
            
        Returns:
            Vector database instance
            
        Raises:
            ValueError: If the database type is not supported
        """
        if config is None:
            config = {}
        
        if db_type.lower() == 'pgvector':
            # Extract PGVector configuration from environment variables if not provided
            if not config:
                config = {
                    'url': os.getenv('PGVECTOR_URL', 'http://localhost:5432'),
                    'db': os.getenv('PGVECTOR_DB', 'postgres'),
                    'user': os.getenv('PGVECTOR_USER', 'postgres'),
                    'password': os.getenv('PGVECTOR_PASSWORD', 'postgres')
                }
            return PGVectorDB(config)
        
        elif db_type.lower() == 'elasticsearch':
            # Extract Elasticsearch configuration from environment variables if not provided
            if not config:
                config = {
                    'url': os.getenv('ELASTICSEARCH_URL', 'http://localhost:9200'),
                    'index_prefix': os.getenv('ELASTICSEARCH_INDEX', 'docucrawler'),
                    'user': os.getenv('ELASTICSEARCH_USER'),
                    'password': os.getenv('ELASTICSEARCH_PASSWORD')
                }
            return ElasticsearchDB(config)
        
        elif db_type.lower() == 'weaviate':
            # Extract Weaviate configuration from environment variables if not provided
            if not config:
                config = {
                    'url': os.getenv('WEAVIATE_URL', 'http://localhost:8080'),
                    'api_key': os.getenv('WEAVIATE_API_KEY'),
                    'class_prefix': os.getenv('WEAVIATE_CLASS', 'DocuCrawler')
                }
            return WeaviateDB(config)
        
        else:
            raise ValueError(f"Unsupported vector database type: {db_type}")