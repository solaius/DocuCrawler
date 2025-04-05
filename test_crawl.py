#!/usr/bin/env python3
"""
Test script for DocuCrawler's crawling functionality.
"""

import os
import asyncio
from dotenv import load_dotenv

from docucrawler.crawlers.connectors import LangChainConnector
from docucrawler.utils.common import ensure_directory_exists

# Load environment variables
load_dotenv()

async def test_langchain_crawl():
    """Test crawling LangChain documentation."""
    print("=== Testing LangChain Crawler ===")
    
    # Ensure output directory exists
    output_dir = os.path.join('docs', 'crawled', 'langchain')
    ensure_directory_exists(output_dir)
    
    # Create connector with custom configuration
    config = {
        'sitemap_url': 'https://python.langchain.com/sitemap.xml',
        'base_url': 'https://python.langchain.com/docs/',
        'max_depth': 1,  # Limit depth for testing
        'output_dir': output_dir,
        'max_concurrent': 2  # Limit concurrency for testing
    }
    
    connector = LangChainConnector(config)
    
    # Get URLs from sitemap
    print("Fetching URLs from sitemap...")
    urls = await connector.get_urls(config['sitemap_url'], config['base_url'], config['max_depth'])
    
    if not urls:
        print("No URLs found. Check sitemap URL and connectivity.")
        return
    
    print(f"Found {len(urls)} URLs. Testing with first 2 URLs...")
    test_urls = urls[:2]  # Only test with 2 URLs
    
    # Crawl the test URLs
    saved_files = await connector.crawl(test_urls, output_dir)
    
    print(f"Successfully crawled {len(saved_files)} files:")
    for file in saved_files:
        print(f"  - {file}")
    
    print("\nTest completed successfully!")

if __name__ == "__main__":
    asyncio.run(test_langchain_crawl())