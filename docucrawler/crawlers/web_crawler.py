"""
Web crawler implementation using crawl4ai.
"""

import os
import asyncio
import requests
from typing import List, Dict, Any, Optional
from xml.etree import ElementTree
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

from docucrawler.crawlers.base import BaseCrawler
from docucrawler.utils.common import ensure_directory_exists, log_memory_usage


class WebCrawler(BaseCrawler):
    """Web crawler implementation using crawl4ai."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the web crawler.
        
        Args:
            config: Dictionary containing crawler configuration
        """
        super().__init__(config)
        self.browser_config = BrowserConfig(
            headless=config.get('headless', True),
            verbose=config.get('verbose', False),
            extra_args=config.get('browser_args', ["--disable-gpu", "--disable-dev-shm-usage", "--no-sandbox"]),
        )
        self.crawl_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS if not config.get('use_cache', False) else CacheMode.READ_WRITE
        )
        self.max_concurrent = config.get('max_concurrent', 10)
    
    async def get_urls(self, source_url: str, base_url: Optional[str] = None, 
                      max_depth: int = 3) -> List[str]:
        """Get URLs to crawl from a sitemap.
        
        Args:
            source_url: Sitemap URL
            base_url: Base URL to filter links
            max_depth: Maximum depth of links to include
            
        Returns:
            List of URLs to crawl
        """
        try:
            response = requests.get(source_url)
            response.raise_for_status()

            # Parse XML content
            root = ElementTree.fromstring(response.content)
            namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
            
            urls = []
            for loc in root.findall('.//ns:loc', namespace):
                url = loc.text
                if base_url and not url.startswith(base_url):
                    continue
                
                if base_url:
                    # Calculate depth based on path segments after the base URL
                    path = url[len(base_url):].strip('/')
                    depth = len(path.split('/')) if path else 0
                    if depth > max_depth:
                        continue
                
                urls.append(url)
            
            return urls
        except Exception as e:
            print(f"Error fetching sitemap: {e}")
            return []
    
    async def crawl(self, urls: List[str], output_dir: str) -> List[str]:
        """Crawl the specified URLs and save the content.
        
        Args:
            urls: List of URLs to crawl
            output_dir: Directory to save crawled content
            
        Returns:
            List of paths to saved files
        """
        ensure_directory_exists(output_dir)
        saved_files = []
        
        crawler = AsyncWebCrawler(config=self.browser_config)
        await crawler.start()
        
        try:
            for i in range(0, len(urls), self.max_concurrent):
                batch = urls[i:i + self.max_concurrent]
                tasks = [crawler.arun(url=url, config=self.crawl_config) for url in batch]
                
                log_memory_usage(prefix=f"Before batch {i // self.max_concurrent + 1}: ")
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for url, result in zip(batch, results):
                    if isinstance(result, Exception):
                        print(f"Error crawling {url}: {result}")
                    elif result.success:
                        # Create a filename based on the URL path
                        url_path = url.rstrip('/').split('/')
                        filename = f"{url_path[-2]}_{url_path[-1]}" if len(url_path) > 1 else url_path[-1]
                        if not filename:
                            filename = "index"
                        
                        # Ensure filename is valid
                        filename = filename.replace('.', '_').replace('-', '_')
                        filepath = os.path.join(output_dir, f"{filename}.md")
                        
                        # We'll overwrite existing files to avoid creating duplicates with suffixes
                        # This ensures that re-running the crawler updates existing files rather than creating new ones
                        
                        with open(filepath, "w", encoding="utf-8") as file:
                            # Use markdown instead of markdown_v2 (which is deprecated)
                            file.write(result.markdown.raw_markdown)
                        
                        saved_files.append(filepath)
                        print(f"Crawled and saved: {url} -> {filepath}")
                    else:
                        print(f"Failed to crawl {url}: {result.error_message}")
                
                log_memory_usage(prefix=f"After batch {i // self.max_concurrent + 1}: ")
        finally:
            await crawler.close()
        
        return saved_files