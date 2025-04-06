"""
Web crawler implementation using crawl4ai.
"""

import os
import asyncio
import requests
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from xml.etree import ElementTree
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

from docucrawler.crawlers.base import BaseCrawler
from docucrawler.utils.common import ensure_directory_exists, log_memory_usage
from docucrawler.utils.document_tracker import DocumentTracker


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
        self.output_dir = config.get('output_dir', 'data/crawled')
        self.incremental = config.get('incremental', True)
        self.source_name = config.get('source_name', os.path.basename(self.output_dir))
        
        # Ensure output directory exists
        ensure_directory_exists(self.output_dir)
        
        # Initialize document tracker
        self.document_tracker = DocumentTracker()
    
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
    
    async def crawl(self, urls: List[str], output_dir: str = None) -> List[str]:
        """Crawl the specified URLs and save the content.
        
        Args:
            urls: List of URLs to crawl
            output_dir: Directory to save crawled content (defaults to self.output_dir)
            
        Returns:
            List of paths to saved files
        """
        if output_dir is None:
            output_dir = self.output_dir
            
        ensure_directory_exists(output_dir)
        saved_files = []
        updated_files = []
        skipped_files = []
        
        # Get the source name from the output directory if not set
        source_name = self.source_name
        
        # Track URLs that need to be crawled
        urls_to_crawl = []
        url_to_filename = {}
        
        # Check which URLs need to be crawled (if incremental mode is enabled)
        if self.incremental:
            print(f"Incremental mode enabled. Checking for changes...")
            last_crawl_time = self.document_tracker.get_last_crawl_time(source_name)
            if last_crawl_time:
                print(f"Last crawl time: {last_crawl_time}")
            else:
                print("No previous crawl found. Crawling all URLs.")
            
            # First pass: check which URLs need to be crawled
            for url in urls:
                # Create a filename based on the URL path
                url_path = url.rstrip('/').split('/')
                filename = f"{url_path[-2]}_{url_path[-1]}" if len(url_path) > 1 else url_path[-1]
                if not filename:
                    filename = "index"
                
                # Ensure filename is valid
                filename = filename.replace('.', '_').replace('-', '_')
                url_to_filename[url] = filename
                
                # Always crawl in non-incremental mode
                urls_to_crawl.append(url)
        else:
            # Non-incremental mode: crawl all URLs
            urls_to_crawl = urls
            for url in urls:
                # Create a filename based on the URL path
                url_path = url.rstrip('/').split('/')
                filename = f"{url_path[-2]}_{url_path[-1]}" if len(url_path) > 1 else url_path[-1]
                if not filename:
                    filename = "index"
                
                # Ensure filename is valid
                filename = filename.replace('.', '_').replace('-', '_')
                url_to_filename[url] = filename
        
        # If no URLs to crawl, return early
        if not urls_to_crawl:
            print("No URLs need to be crawled.")
            return saved_files
        
        print(f"Crawling {len(urls_to_crawl)} URLs...")
        
        crawler = AsyncWebCrawler(config=self.browser_config)
        await crawler.start()
        
        try:
            for i in range(0, len(urls_to_crawl), self.max_concurrent):
                batch = urls_to_crawl[i:i + self.max_concurrent]
                tasks = [crawler.arun(url=url, config=self.crawl_config) for url in batch]
                
                log_memory_usage(prefix=f"Before batch {i // self.max_concurrent + 1}: ")
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for url, result in zip(batch, results):
                    if isinstance(result, Exception):
                        print(f"Error crawling {url}: {result}")
                    elif result.success:
                        # Get the filename for this URL
                        filename = url_to_filename[url]
                        filepath = os.path.join(output_dir, f"{filename}.md")
                        
                        # Get the content
                        content = result.markdown.raw_markdown
                        
                        # Check if the content has changed
                        is_new, has_changed = self.document_tracker.update_document(
                            source=source_name,
                            document_id=filename,
                            content=content,
                            metadata={'url': url, 'title': result.title}
                        )
                        
                        if is_new or has_changed:
                            # Write the content to file
                            with open(filepath, "w", encoding="utf-8") as file:
                                file.write(content)
                            
                            saved_files.append(filepath)
                            if is_new:
                                print(f"Crawled and saved new document: {url} -> {filepath}")
                            else:
                                print(f"Crawled and updated document: {url} -> {filepath}")
                                updated_files.append(filepath)
                        else:
                            print(f"Document unchanged, skipping: {url}")
                            skipped_files.append(url)
                    else:
                        print(f"Failed to crawl {url}: {result.error_message}")
                
                log_memory_usage(prefix=f"After batch {i // self.max_concurrent + 1}: ")
            
            # Print summary
            print(f"\nCrawl Summary:")
            print(f"  New documents: {len(saved_files) - len(updated_files)}")
            print(f"  Updated documents: {len(updated_files)}")
            print(f"  Unchanged documents: {len(skipped_files)}")
            print(f"  Total documents: {len(saved_files) + len(skipped_files)}")
        finally:
            await crawler.close()
        
        return saved_files