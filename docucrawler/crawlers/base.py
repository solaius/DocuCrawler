"""
Base crawler module that defines the interface for all crawlers.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class BaseCrawler(ABC):
    """Base class for all crawlers."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the crawler with configuration.
        
        Args:
            config: Dictionary containing crawler configuration
        """
        self.config = config
    
    @abstractmethod
    async def crawl(self, urls: List[str], output_dir: str) -> List[str]:
        """Crawl the specified URLs and save the content.
        
        Args:
            urls: List of URLs to crawl
            output_dir: Directory to save crawled content
            
        Returns:
            List of paths to saved files
        """
        pass
    
    @abstractmethod
    async def get_urls(self, source_url: str, base_url: Optional[str] = None, 
                      max_depth: int = 3) -> List[str]:
        """Get URLs to crawl from a source URL (e.g., sitemap).
        
        Args:
            source_url: URL to extract links from (e.g., sitemap URL)
            base_url: Base URL to filter links (optional)
            max_depth: Maximum depth of links to include
            
        Returns:
            List of URLs to crawl
        """
        pass