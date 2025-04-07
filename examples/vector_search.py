#!/usr/bin/env python3
"""
Example script demonstrating how to perform semantic search using vector databases.
"""

import os
import asyncio
import argparse
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()

async def generate_query_embedding(query: str) -> List[float]:
    """Generate embedding for a query using the Granite Embedding API.
    
    Args:
        query: Query text
        
    Returns:
        Query embedding as a list of floats
    """
    api_url = os.getenv('GRANITE_EMBEDDINGS_URL')
    api_key = os.getenv('GRANITE_EMBEDDINGS_API')
    model_name = os.getenv('GRANITE_EMBEDDINGS_MODEL_NAME')
    
    if not all([api_url, api_key, model_name]):
        raise ValueError("Missing required environment variables for embedding model.")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model_name,
        "input": query
    }
    
    response = requests.post(api_url, headers=headers, json=payload)
    response.raise_for_status()
    
    response_data = response.json()
    
    if "data" in response_data and len(response_data["data"]) > 0:
        if "embedding" in response_data["data"][0]:
            return response_data["data"][0]["embedding"]
    
    raise ValueError(f"Unexpected response format: {response_data}")

async def search_vector_db(query: str, 
                          collection_name: str = 'mcp', 
                          db_type: str = 'pgvector',
                          limit: int = 5,
                          filters: Optional[Dict[str, Any]] = None) -> None:
    """Search for documents in a vector database.
    
    Args:
        query: Query text
        collection_name: Name of the collection to search in
        db_type: Type of vector database to use
        limit: Maximum number of results to return
        filters: Optional filters to apply to the search
    """
    from docucrawler.vectordb.integration import search_documents
    
    # Generate embedding for the query
    print(f"Generating embedding for query: '{query}'")
    query_embedding = await generate_query_embedding(query)
    
    # Search for similar documents
    print(f"Searching for similar documents in {db_type} collection '{collection_name}'...")
    
    # Extract group_chunks parameter from filters if present
    group_chunks = True
    if filters and 'group_chunks' in filters:
        group_chunks = filters.pop('group_chunks')
    
    results = await search_documents(
        query_embedding=query_embedding,
        db_type=db_type,
        collection_name=collection_name,
        limit=limit,
        filters=filters,
        group_chunks=group_chunks
    )
    
    # Display results
    if not results:
        print("No results found.")
        return
    
    print(f"\nFound {len(results)} results:")
    for i, result in enumerate(results):
        print(f"\n{i+1}. {result.get('title', 'Untitled')} (Similarity: {result.get('similarity', 0):.4f})")
        print(f"   ID: {result.get('id', 'unknown')}")
        
        # Check if this result has chunks
        if 'chunks' in result and result['chunks']:
            print(f"   Contains {len(result['chunks'])} chunks")
            
            # Display the most relevant chunk
            most_relevant_chunk = max(result['chunks'], key=lambda x: x.get('similarity', 0))
            print(f"   Most relevant chunk: {most_relevant_chunk.get('content', '')[:200]}...")
        else:
            # Display regular content
            content = result.get('content', '')
            if content:
                print(f"   Content: {content[:200]}...")
            else:
                print("   No content available")

async def main():
    """Run the vector search example."""
    parser = argparse.ArgumentParser(description='Vector Database Search Example')
    parser.add_argument('query', help='Search query')
    parser.add_argument('--collection', default='mcp', help='Collection name to search in')
    parser.add_argument('--db-type', default='pgvector', choices=['pgvector', 'elasticsearch', 'weaviate'],
                        help='Vector database type to use')
    parser.add_argument('--limit', type=int, default=5, help='Maximum number of results to return')
    parser.add_argument('--no-group', action='store_true', help='Do not group chunks from the same document')
    
    args = parser.parse_args()
    
    await search_vector_db(
        query=args.query,
        collection_name=args.collection,
        db_type=args.db_type,
        limit=args.limit,
        filters={'group_chunks': not args.no_group}
    )

if __name__ == "__main__":
    asyncio.run(main())