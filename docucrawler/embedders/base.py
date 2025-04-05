"""
Base embedder module that defines the interface for all embedding generators.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Union


class BaseEmbedder(ABC):
    """Base class for all embedding generators."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the embedder with configuration.
        
        Args:
            config: Dictionary containing embedder configuration
        """
        self.config = config
    
    @abstractmethod
    async def generate_embeddings(self, input_dir: str, output_dir: str) -> List[str]:
        """Generate embeddings for documents in the input directory and save to output directory.
        
        Args:
            input_dir: Directory containing documents to embed
            output_dir: Directory to save documents with embeddings
            
        Returns:
            List of paths to files with embeddings
        """
        pass
    
    @abstractmethod
    def embed_document(self, content: str) -> Union[List[float], List[List[float]]]:
        """Generate embeddings for a single document.
        
        Args:
            content: Document content to embed
            
        Returns:
            Document embeddings as a list of floats or list of list of floats (for chunked content)
        """
        pass
    
    @abstractmethod
    def chunk_content(self, content: str, token_limit: int) -> List[str]:
        """Chunk content into smaller pieces based on token limit.
        
        Args:
            content: Content to chunk
            token_limit: Maximum number of tokens per chunk
            
        Returns:
            List of content chunks
        """
        pass