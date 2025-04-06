"""
Base vector database module that defines the interface for all vector databases.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union


class BaseVectorDB(ABC):
    """Base class for all vector databases."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the vector database with configuration.
        
        Args:
            config: Dictionary containing vector database configuration
        """
        self.config = config
    
    @abstractmethod
    async def connect(self) -> bool:
        """Connect to the vector database.
        
        Returns:
            True if connection is successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def create_collection(self, collection_name: str, dimension: int) -> bool:
        """Create a collection/index/table in the vector database.
        
        Args:
            collection_name: Name of the collection to create
            dimension: Dimension of the vectors to store
            
        Returns:
            True if creation is successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def insert_document(self, 
                             collection_name: str, 
                             document_id: str, 
                             embedding: Union[List[float], List[List[float]]], 
                             metadata: Dict[str, Any]) -> bool:
        """Insert a document with its embedding and metadata into the vector database.
        
        Args:
            collection_name: Name of the collection to insert into
            document_id: Unique identifier for the document
            embedding: Document embedding as a list of floats or list of list of floats
            metadata: Document metadata
            
        Returns:
            True if insertion is successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def search(self, 
                    collection_name: str, 
                    query_embedding: List[float], 
                    limit: int = 10, 
                    filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search for similar documents in the vector database.
        
        Args:
            collection_name: Name of the collection to search in
            query_embedding: Query embedding as a list of floats
            limit: Maximum number of results to return
            filters: Optional filters to apply to the search
            
        Returns:
            List of documents with their metadata and similarity scores
        """
        pass
    
    @abstractmethod
    async def delete_document(self, collection_name: str, document_id: str) -> bool:
        """Delete a document from the vector database.
        
        Args:
            collection_name: Name of the collection to delete from
            document_id: Unique identifier for the document
            
        Returns:
            True if deletion is successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def delete_collection(self, collection_name: str) -> bool:
        """Delete a collection from the vector database.
        
        Args:
            collection_name: Name of the collection to delete
            
        Returns:
            True if deletion is successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """Disconnect from the vector database.
        
        Returns:
            True if disconnection is successful, False otherwise
        """
        pass