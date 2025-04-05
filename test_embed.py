#!/usr/bin/env python3
"""
Test script for DocuCrawler's embedding functionality.
"""

import os
import json
import asyncio
from dotenv import load_dotenv

from docucrawler.embedders.granite_embedder import GraniteEmbedder
from docucrawler.utils.common import ensure_directory_exists, save_json

# Load environment variables
load_dotenv()

async def create_test_processed_document():
    """Create a test processed document for embedding."""
    test_dir = os.path.join('docs', 'test', 'processed')
    ensure_directory_exists(test_dir)
    
    # Create a test processed document
    test_doc = {
        "title": "Test Document Title",
        "summary": "This is a test document for the embedding generator.",
        "content": "This is a test document for the embedding generator. It contains some text that will be used to generate embeddings. The embeddings will be used for semantic search and other NLP tasks.",
        "metadata": {
            "length": 150,
            "source_file": "test_document.md"
        }
    }
    
    # Save the test document
    test_file = os.path.join(test_dir, 'test_document.json')
    save_json(test_file, test_doc)
    
    return test_dir, [test_file]

async def test_granite_embedder():
    """Test the Granite embedder."""
    print("=== Testing Granite Embedder ===")
    
    # Check if environment variables are set
    api_url = os.getenv('GRANITE_EMBEDDINGS_URL')
    api_key = os.getenv('GRANITE_EMBEDDINGS_API')
    model_name = os.getenv('GRANITE_EMBEDDINGS_MODEL_NAME')
    
    if not all([api_url, api_key, model_name]):
        print("Error: Missing required environment variables for embedding model.")
        print("Please set GRANITE_EMBEDDINGS_URL, GRANITE_EMBEDDINGS_API, and GRANITE_EMBEDDINGS_MODEL_NAME.")
        return
    
    # Create test documents
    input_dir, test_files = await create_test_processed_document()
    print(f"Created test documents in {input_dir}")
    
    # Set up output directory
    output_dir = os.path.join('docs', 'test', 'embeddings')
    ensure_directory_exists(output_dir)
    
    # Create embedder with configuration from environment variables
    config = {
        'api_url': api_url,
        'api_key': api_key,
        'model_name': model_name,
        'token_limit': int(os.getenv('EMBEDDINGS_TOKEN_LIMIT', '512')),
        'max_concurrent': 2,
        'max_retries': 3
    }
    
    embedder = GraniteEmbedder(config)
    
    # Test chunking
    print("\nTesting content chunking:")
    long_content = "This is a test. " * 100  # Create a long string
    chunks = embedder.chunk_content(long_content, 50)  # Small token limit for testing
    print(f"Split content into {len(chunks)} chunks")
    print(f"First chunk: {chunks[0][:50]}...")
    
    # Test embedding generation for a single document
    print("\nTesting single document embedding:")
    with open(test_files[0], 'r', encoding='utf-8') as file:
        data = json.load(file)
    
    try:
        embedding = embedder.embed_document(data['content'])
        if isinstance(embedding, list):
            if isinstance(embedding[0], list):
                print(f"Generated {len(embedding)} chunk embeddings")
                print(f"First chunk embedding dimension: {len(embedding[0])}")
            else:
                print(f"Generated embedding with dimension: {len(embedding)}")
        
        # Process all documents in the directory
        print("\nTesting directory processing:")
        embedded_files = await embedder.generate_embeddings(input_dir, output_dir)
        
        print(f"Successfully embedded {len(embedded_files)} files:")
        for file in embedded_files:
            print(f"  - {file}")
        
        print("\nTest completed successfully!")
    except Exception as e:
        print(f"Error during embedding test: {e}")
        print("Check your API credentials and connectivity.")

if __name__ == "__main__":
    asyncio.run(test_granite_embedder())