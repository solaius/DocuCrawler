"""
Connector implementations for specific documentation sources.
"""

import os
from typing import Dict, Any, List, Optional

from docucrawler.crawlers.web_crawler import WebCrawler


class LangChainConnector(WebCrawler):
    """Connector for LangChain documentation."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the LangChain connector.
        
        Args:
            config: Dictionary containing connector configuration (optional)
        """
        if config is None:
            config = {}
        
        # Set default configuration for LangChain
        default_config = {
            'sitemap_url': 'https://python.langchain.com/sitemap.xml',
            'base_url': 'https://python.langchain.com/docs/',
            'max_depth': 3,
            'output_dir': 'data/crawled/langchain',
            'source_name': 'langchain',
            'headless': True,
            'max_concurrent': 10,
            'incremental': True
        }
        
        # Merge default config with provided config
        merged_config = {**default_config, **config}
        super().__init__(merged_config)
        
        self.sitemap_url = merged_config['sitemap_url']
        self.base_url = merged_config['base_url']
        self.max_depth = merged_config['max_depth']
        self.output_dir = merged_config['output_dir']
    
    async def crawl_documentation(self) -> List[str]:
        """Crawl LangChain documentation.
        
        Returns:
            List of paths to saved files
        """
        print(f"Fetching URLs from LangChain sitemap: {self.sitemap_url}")
        urls = await self.get_urls(self.sitemap_url, self.base_url, self.max_depth)
        
        if not urls:
            print("No LangChain URLs found or sitemap inaccessible.")
            return []
        
        print(f"Found {len(urls)} LangChain URLs to crawl.")
        return await self.crawl(urls, self.output_dir)


class DoclingConnector(WebCrawler):
    """Connector for Docling documentation."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the Docling connector.
        
        Args:
            config: Dictionary containing connector configuration (optional)
        """
        if config is None:
            config = {}
        
        # Set default configuration for Docling
        default_config = {
            'sitemap_url': 'https://docling-project.github.io/docling/sitemap.xml',
            'base_url': 'https://docling-project.github.io/docling/',
            'max_depth': 3,
            'output_dir': 'data/crawled/docling',
            'source_name': 'docling',
            'headless': True,
            'max_concurrent': 10,
            'incremental': True
        }
        
        # Merge default config with provided config
        merged_config = {**default_config, **config}
        super().__init__(merged_config)
        
        self.sitemap_url = merged_config['sitemap_url']
        self.base_url = merged_config['base_url']
        self.max_depth = merged_config['max_depth']
        self.output_dir = merged_config['output_dir']
    
    async def crawl_documentation(self) -> List[str]:
        """Crawl Docling documentation.
        
        Returns:
            List of paths to saved files
        """
        print(f"Fetching URLs from Docling sitemap: {self.sitemap_url}")
        urls = await self.get_urls(self.sitemap_url, self.base_url, self.max_depth)
        
        if not urls:
            print("No Docling URLs found or sitemap inaccessible.")
            return []
        
        print(f"Found {len(urls)} Docling URLs to crawl.")
        return await self.crawl(urls, self.output_dir)


class LlamaStackConnector(WebCrawler):
    """Connector for Meta Llama Stack documentation."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the Llama Stack connector.
        
        Args:
            config: Dictionary containing connector configuration (optional)
        """
        if config is None:
            config = {}
        
        # Set default configuration for Llama Stack
        default_config = {
            'sitemap_url': 'https://llama-stack.readthedocs.io/sitemap.xml',
            'base_url': 'https://llama-stack.readthedocs.io/en/latest/',
            'max_depth': 3,
            'output_dir': 'data/crawled/llama-stack',
            'source_name': 'llama-stack',
            'headless': True,
            'max_concurrent': 10,
            'incremental': True
        }
        
        # Merge default config with provided config
        merged_config = {**default_config, **config}
        super().__init__(merged_config)
        
        self.sitemap_url = merged_config['sitemap_url']
        self.base_url = merged_config['base_url']
        self.max_depth = merged_config['max_depth']
        self.output_dir = merged_config['output_dir']
    
    async def crawl_documentation(self) -> List[str]:
        """Crawl Llama Stack documentation.
        
        Returns:
            List of paths to saved files
        """
        print(f"Fetching URLs from Llama Stack sitemap: {self.sitemap_url}")
        urls = await self.get_urls(self.sitemap_url, self.base_url, self.max_depth)
        
        if not urls:
            print("No Llama Stack URLs found or sitemap inaccessible.")
            return []
        
        print(f"Found {len(urls)} Llama Stack URLs to crawl.")
        return await self.crawl(urls, self.output_dir)


class MCPConnector(WebCrawler):
    """Connector for MCP documentation."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the MCP connector.
        
        Args:
            config: Dictionary containing connector configuration (optional)
        """
        if config is None:
            config = {}
        
        # Set default configuration for MCP
        default_config = {
            'sitemap_url': 'https://modelcontextprotocol.io/sitemap.xml',
            'base_url': 'https://modelcontextprotocol.io/',
            'max_depth': 3,
            'output_dir': 'data/crawled/mcp',
            'source_name': 'mcp',
            'headless': True,
            'max_concurrent': 10,
            'incremental': True
        }
        
        # Merge default config with provided config
        merged_config = {**default_config, **config}
        super().__init__(merged_config)
        
        self.sitemap_url = merged_config['sitemap_url']
        self.base_url = merged_config['base_url']
        self.max_depth = merged_config['max_depth']
        self.output_dir = merged_config['output_dir']
    
    async def crawl_documentation(self) -> List[str]:
        """Crawl MCP documentation.
        
        Returns:
            List of paths to saved files
        """
        print(f"Fetching URLs from MCP sitemap: {self.sitemap_url}")
        urls = await self.get_urls(self.sitemap_url, self.base_url, self.max_depth)
        
        if not urls:
            print("No MCP URLs found or sitemap inaccessible.")
            return []
        
        print(f"Found {len(urls)} MCP URLs to crawl.")
        return await self.crawl(urls, self.output_dir)