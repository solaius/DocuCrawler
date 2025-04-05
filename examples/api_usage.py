#!/usr/bin/env python3
"""
Example script demonstrating how to use DocuCrawler as a Python API.
"""

import os
import asyncio
from dotenv import load_dotenv

from docucrawler.crawlers.connectors import LangChainConnector
from docucrawler.processors.markdown_processor import MarkdownProcessor
from docucrawler.embedders.granite_embedder import GraniteEmbedder
from docucrawler.utils.common import ensure_directory_exists

# Load environment variables
load_dotenv()

async def main():
    """Run a simple example of using DocuCrawler as an API."""
    print("=== DocuCrawler API Usage Example ===")
    
    # Set up directories
    base_dir = 'docs'
    source = 'langchain'
    crawl_dir = os.path.join(base_dir, 'crawled', source)
    process_dir = os.path.join(base_dir, 'processed', source)
    embed_dir = os.path.join(base_dir, 'embeddings', source)
    
    for directory in [crawl_dir, process_dir, embed_dir]:
        ensure_directory_exists(directory)
    
    # Step 1: Crawl documentation
    print("\n--- Step 1: Crawling Documentation ---")
    crawler_config = {
        'sitemap_url': 'https://python.langchain.com/sitemap.xml',
        'base_url': 'https://python.langchain.com/docs/',
        'max_depth': 1,  # Limit depth for example
        'output_dir': crawl_dir,
        'max_concurrent': 2  # Limit concurrency for example
    }
    
    crawler = LangChainConnector(crawler_config)
    crawled_files = await crawler.crawl_documentation()
    
    if not crawled_files:
        print("No files were crawled. Exiting.")
        return
    
    print(f"Successfully crawled {len(crawled_files)} files.")
    
    # Step 2: Process documentation
    print("\n--- Step 2: Processing Documentation ---")
    processor_config = {
        'max_concurrent': 5,
        'summary_length': 200
    }
    
    processor = MarkdownProcessor(processor_config)
    processed_files = await processor.process(crawl_dir, process_dir)
    
    print(f"Successfully processed {len(processed_files)} files.")
    
    # Step 3: Generate embeddings
    print("\n--- Step 3: Generating Embeddings ---")
    embedder_config = {
        'api_url': os.getenv('GRANITE_EMBEDDINGS_URL'),
        'api_key': os.getenv('GRANITE_EMBEDDINGS_API'),
        'model_name': os.getenv('GRANITE_EMBEDDINGS_MODEL_NAME'),
        'token_limit': int(os.getenv('EMBEDDINGS_TOKEN_LIMIT', '512')),
        'max_concurrent': 2
    }
    
    embedder = GraniteEmbedder(embedder_config)
    embedded_files = await embedder.generate_embeddings(process_dir, embed_dir)
    
    print(f"Successfully generated embeddings for {len(embedded_files)} files.")
    
    print("\n=== Example Completed Successfully ===")

if __name__ == "__main__":
    asyncio.run(main())