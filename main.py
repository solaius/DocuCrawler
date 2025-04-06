#!/usr/bin/env python3
"""
DocuCrawler - Documentation Aggregation System

This script serves as the main entry point for the DocuCrawler application,
which crawls, processes, and generates embeddings for documentation from
various sources.
"""

import os
import argparse
import asyncio
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Import modules from the new modular architecture
from docucrawler.utils.common import ensure_directory_exists
from docucrawler.crawlers.connectors import (
    LangChainConnector, DoclingConnector, LlamaStackConnector, MCPConnector
)
from docucrawler.processors.markdown_processor import MarkdownProcessor
from docucrawler.embedders.granite_embedder import GraniteEmbedder

# Load environment variables
load_dotenv()

def setup_directories():
    """Set up the necessary directory structure."""
    base_dir = 'data'
    directories = [
        os.path.join(base_dir, 'crawled'),
        os.path.join(base_dir, 'processed'),
        os.path.join(base_dir, 'embeddings')
    ]
    
    for directory in directories:
        ensure_directory_exists(directory)
    
    # Create subdirectories for each documentation source
    sources = ['langchain', 'docling', 'llama-stack', 'mcp']
    for source in sources:
        for subdir in ['crawled', 'processed', 'embeddings']:
            ensure_directory_exists(os.path.join(base_dir, subdir, source))
    
    return base_dir

async def run_crawl_step(sources: Optional[List[str]] = None):
    """Run the crawling step for specified sources.
    
    Args:
        sources: List of sources to crawl (default: all sources)
    """
    if sources is None:
        sources = ['langchain', 'docling', 'llama-stack', 'mcp']
    
    connectors = {
        'langchain': LangChainConnector(),
        'docling': DoclingConnector(),
        'llama-stack': LlamaStackConnector(),
        'mcp': MCPConnector()
    }
    
    for source in sources:
        if source in connectors:
            print(f"\n--- Crawling {source.upper()} documentation ---")
            connector = connectors[source]
            await connector.crawl_documentation()
        else:
            print(f"Warning: Unknown source '{source}', skipping.")

async def run_process_step(sources: Optional[List[str]] = None):
    """Run the processing step for specified sources.
    
    Args:
        sources: List of sources to process (default: all sources)
    """
    if sources is None:
        sources = ['langchain', 'docling', 'llama-stack', 'mcp']
    
    processor_config = {
        'max_concurrent': 10,
        'summary_length': 200,
        'language_detection': False  # Set to True if langdetect is installed
    }
    
    processor = MarkdownProcessor(processor_config)
    
    for source in sources:
        input_dir = os.path.join('data', 'crawled', source)
        output_dir = os.path.join('data', 'processed', source)
        
        if os.path.exists(input_dir) and os.listdir(input_dir):
            print(f"\n--- Processing {source.upper()} documentation ---")
            await processor.process(input_dir, output_dir)
        else:
            print(f"Warning: No documents found for {source}, skipping processing.")

async def run_embed_step(sources: Optional[List[str]] = None):
    """Run the embedding step for specified sources.
    
    Args:
        sources: List of sources to embed (default: all sources)
    """
    if sources is None:
        sources = ['langchain', 'docling', 'llama-stack', 'mcp']
    
    # Get embedding configuration from environment variables
    embedder_config = {
        'api_url': os.getenv('GRANITE_EMBEDDINGS_URL'),
        'api_key': os.getenv('GRANITE_EMBEDDINGS_API'),
        'model_name': os.getenv('GRANITE_EMBEDDINGS_MODEL_NAME'),
        'token_limit': int(os.getenv('EMBEDDINGS_TOKEN_LIMIT', '512')),
        'max_concurrent': 5,  # Lower concurrency for API calls
        'max_retries': 3
    }
    
    # Validate required configuration
    if not all([embedder_config['api_url'], embedder_config['api_key'], embedder_config['model_name']]):
        print("Error: Missing required environment variables for embedding model.")
        print("Please set GRANITE_EMBEDDINGS_URL, GRANITE_EMBEDDINGS_API, and GRANITE_EMBEDDINGS_MODEL_NAME.")
        return
    
    embedder = GraniteEmbedder(embedder_config)
    
    for source in sources:
        input_dir = os.path.join('data', 'processed', source)
        output_dir = os.path.join('data', 'embeddings', source)
        
        if os.path.exists(input_dir) and os.listdir(input_dir):
            print(f"\n--- Generating embeddings for {source.upper()} documentation ---")
            await embedder.generate_embeddings(input_dir, output_dir)
        else:
            print(f"Warning: No processed documents found for {source}, skipping embedding.")

async def run_vectordb_step(sources: Optional[List[str]] = None, db_type: str = 'pgvector'):
    """Run the vector database integration step for specified sources.
    
    Args:
        sources: List of sources to process (default: all sources)
        db_type: Type of vector database to use
    """
    if sources is None:
        sources = ['langchain', 'docling', 'llama-stack', 'mcp']
    
    from docucrawler.vectordb.integration import store_embeddings
    
    for source in sources:
        input_dir = os.path.join('data', 'embeddings', source)
        
        if os.path.exists(input_dir) and os.listdir(input_dir):
            print(f"\n--- Storing embeddings for {source.upper()} documentation in {db_type} ---")
            stored_ids = await store_embeddings(
                input_dir=input_dir,
                db_type=db_type,
                collection_name=source
            )
            print(f"Stored {len(stored_ids)} documents in {db_type} database")
        else:
            print(f"Warning: No embeddings found for {source}, skipping vector database integration")

async def run_pipeline(steps: Optional[List[str]] = None, sources: Optional[List[str]] = None, db_type: Optional[str] = None):
    """Run the complete pipeline or specific steps for specified sources.
    
    Args:
        steps: List of steps to run (default: all steps)
        sources: List of sources to process (default: all sources)
        db_type: Type of vector database to use (default: from environment)
    """
    if steps is None:
        steps = ['crawl', 'preprocess', 'embed', 'vectordb']
    
    # Determine vector database type
    if db_type is None:
        # Check environment variables to determine which vector database to use
        if os.getenv('PGVECTOR_URL'):
            db_type = 'pgvector'
        elif os.getenv('ELASTICSEARCH_URL'):
            db_type = 'elasticsearch'
        elif os.getenv('WEAVIATE_URL'):
            db_type = 'weaviate'
        else:
            db_type = 'pgvector'  # Default to pgvector
    
    # Set up directories
    setup_directories()
    
    # Execute each step in the pipeline
    if 'crawl' in steps:
        print("\n=== Starting Crawling Phase ===")
        await run_crawl_step(sources)
    
    if 'preprocess' in steps:
        print("\n=== Starting Preprocessing Phase ===")
        await run_process_step(sources)
    
    if 'embed' in steps:
        print("\n=== Starting Embedding Generation Phase ===")
        await run_embed_step(sources)
    
    if 'vectordb' in steps:
        print("\n=== Starting Vector Database Integration Phase ===")
        await run_vectordb_step(sources, db_type)
    
    print("\n=== Pipeline Completed Successfully ===")

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='DocuCrawler - Documentation Aggregation System')
    parser.add_argument('--steps', nargs='+', choices=['crawl', 'preprocess', 'embed', 'vectordb'], 
                        help='Specify which steps to run (default: all steps)')
    parser.add_argument('--sources', nargs='+', choices=['langchain', 'docling', 'llama-stack', 'mcp'],
                        help='Specify which documentation sources to process (default: all sources)')
    parser.add_argument('--db-type', choices=['pgvector', 'elasticsearch', 'weaviate'],
                        help='Specify which vector database to use (default: determined from environment)')
    
    return parser.parse_args()

def main_cli():
    """Entry point for the console script."""
    args = parse_arguments()
    asyncio.run(run_pipeline(args.steps, args.sources, args.db_type))

if __name__ == "__main__":
    main_cli()