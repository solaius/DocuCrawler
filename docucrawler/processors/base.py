"""
Base processor module that defines the interface for all document processors.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List


class BaseProcessor(ABC):
    """Base class for all document processors."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the processor with configuration.
        
        Args:
            config: Dictionary containing processor configuration
        """
        self.config = config
    
    @abstractmethod
    async def process(self, input_dir: str, output_dir: str) -> List[str]:
        """Process documents in the input directory and save results to output directory.
        
        Args:
            input_dir: Directory containing documents to process
            output_dir: Directory to save processed documents
            
        Returns:
            List of paths to processed files
        """
        pass
    
    @abstractmethod
    def process_document(self, content: str) -> Dict[str, Any]:
        """Process a single document.
        
        Args:
            content: Document content to process
            
        Returns:
            Processed document as a dictionary
        """
        pass