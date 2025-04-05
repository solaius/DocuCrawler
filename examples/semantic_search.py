#!/usr/bin/env python3
"""
Example script demonstrating how to perform semantic search using DocuCrawler embeddings.
"""

import os
import json
import numpy as np
from dotenv import load_dotenv
import requests
from typing import List, Dict, Any

# Load environment variables
load_dotenv()

def load_embeddings(directory: str) -> List[Dict[str, Any]]:
    """Load all embeddings from a directory.
    
    Args:
        directory: Directory containing embedding files
        
    Returns:
        List of documents with embeddings
    """
    documents = []
    
    if not os.path.exists(directory):
        print(f"Directory {directory} does not exist.")
        return documents
    
    for filename in os.listdir(directory):
        if filename.endswith('_embedded.json'):
            filepath = os.path.join(directory, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as file:
                    document = json.load(file)
                    if 'embedding' in document:
                        documents.append(document)
            except Exception as e:
                print(f"Error loading {filepath}: {e}")
    
    print(f"Loaded {len(documents)} documents with embeddings.")
    return documents

def generate_query_embedding(query: str) -> List[float]:
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

def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Calculate cosine similarity between two vectors.
    
    Args:
        a: First vector
        b: Second vector
        
    Returns:
        Cosine similarity score
    """
    a = np.array(a)
    b = np.array(b)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def search_documents(query: str, documents: List[Dict[str, Any]], top_k: int = 3) -> List[Dict[str, Any]]:
    """Search for documents similar to the query.
    
    Args:
        query: Query text
        documents: List of documents with embeddings
        top_k: Number of top results to return
        
    Returns:
        List of top_k most similar documents with similarity scores
    """
    if not documents:
        return []
    
    # Generate embedding for the query
    query_embedding = generate_query_embedding(query)
    
    results = []
    
    for doc in documents:
        doc_embedding = doc['embedding']
        
        # Handle both single embedding and list of chunk embeddings
        if isinstance(doc_embedding[0], list):
            # Multiple chunk embeddings, take the max similarity
            similarities = [cosine_similarity(query_embedding, chunk_emb) for chunk_emb in doc_embedding]
            similarity = max(similarities)
        else:
            # Single embedding
            similarity = cosine_similarity(query_embedding, doc_embedding)
        
        results.append({
            'title': doc['title'],
            'summary': doc['summary'],
            'similarity': similarity,
            'metadata': doc['metadata']
        })
    
    # Sort by similarity (highest first)
    results.sort(key=lambda x: x['similarity'], reverse=True)
    
    # Return top_k results
    return results[:top_k]

def main():
    """Run the semantic search example."""
    print("=== DocuCrawler Semantic Search Example ===")
    
    # Load embeddings
    embeddings_dir = os.path.join('docs', 'embeddings', 'langchain')
    documents = load_embeddings(embeddings_dir)
    
    if not documents:
        print("No documents with embeddings found. Please run the crawler first.")
        return
    
    # Example queries
    queries = [
        "How to use agents in LangChain?",
        "What are embeddings and how do they work?",
        "How to connect to external APIs?"
    ]
    
    for query in queries:
        print(f"\nQuery: {query}")
        results = search_documents(query, documents, top_k=3)
        
        print(f"Top {len(results)} results:")
        for i, result in enumerate(results):
            print(f"{i+1}. {result['title']} (Score: {result['similarity']:.4f})")
            print(f"   Summary: {result['summary'][:100]}...")
            print(f"   Source: {result['metadata'].get('source_file', 'Unknown')}")
    
    print("\n=== Example Completed Successfully ===")

if __name__ == "__main__":
    main()