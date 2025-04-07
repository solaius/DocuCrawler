"""
Integration module for connecting the embedding pipeline with vector databases.
"""

import os
import json
import asyncio
from typing import List, Dict, Any, Optional, Union

from docucrawler.utils.common import load_json
from docucrawler.vectordb.factory import VectorDBFactory
from docucrawler.vectordb.base import BaseVectorDB


async def store_embeddings(input_dir: str, 
                          db_type: str = 'pgvector', 
                          collection_name: Optional[str] = None,
                          config: Optional[Dict[str, Any]] = None) -> List[str]:
    """Store embeddings from files in a directory to a vector database.
    
    Args:
        input_dir: Directory containing embedding files
        db_type: Type of vector database to use
        collection_name: Name of the collection to store embeddings in (defaults to directory name)
        config: Configuration for the vector database
        
    Returns:
        List of document IDs that were stored
    """
    # Determine collection name if not provided
    if collection_name is None:
        collection_name = os.path.basename(input_dir)
    
    # Create vector database
    vector_db = VectorDBFactory.create_vector_db(db_type, config)
    
    # Connect to vector database
    connected = await vector_db.connect()
    if not connected:
        print(f"Failed to connect to {db_type} database")
        return []
    
    try:
        # Create collection
        dimension = 768  # Default dimension
        created = await vector_db.create_collection(collection_name, dimension)
        if not created:
            print(f"Failed to create collection '{collection_name}'")
            return []
        
        # Get embedding files
        files = [f for f in os.listdir(input_dir) if f.endswith('_embedded.json')]
        if not files:
            print(f"No embedding files found in {input_dir}")
            return []
        
        # Store embeddings
        stored_ids = []
        for filename in files:
            filepath = os.path.join(input_dir, filename)
            
            try:
                # Load embedding file
                data = load_json(filepath)
                
                # Extract document ID from filename
                document_id = filename.replace('_embedded.json', '')
                
                # Handle different embedding formats
                embedding = data.get('embedding')
                chunks = data.get('chunks', [])
                
                # If no direct embedding but chunks exist (enhanced embedder format)
                if embedding is None and chunks:
                    print(f"Found enhanced embedder format with {len(chunks)} chunks for {document_id}")
                    
                    # Store each chunk as a separate document
                    chunk_count = 0
                    for i, chunk in enumerate(chunks):
                        if 'embedding' not in chunk:
                            continue
                            
                        chunk_id = f"{document_id}_chunk_{i}"
                        chunk_content = chunk.get('content', '')
                        
                        # Store chunk embedding
                        chunk_success = await vector_db.insert_document(
                            collection_name=collection_name,
                            document_id=chunk_id,
                            embedding=chunk['embedding'],
                            metadata={
                                'title': data.get('title', ''),
                                'summary': data.get('summary', ''),
                                'content': chunk_content,
                                'metadata': {
                                    'parent_id': document_id,
                                    'chunk_index': i,
                                    'chunk_count': len(chunks),
                                    'is_chunk': True,
                                    **data.get('metadata', {})
                                }
                            }
                        )
                        
                        if chunk_success:
                            chunk_count += 1
                    
                    if chunk_count > 0:
                        print(f"Stored {chunk_count} chunks for document '{document_id}'")
                        stored_ids.append(document_id)
                    continue
                
                # Skip if no embedding (standard format)
                if embedding is None:
                    print(f"No embedding found in {filepath}, skipping")
                    continue
                
                # Store embedding (standard format)
                success = await vector_db.insert_document(
                    collection_name=collection_name,
                    document_id=document_id,
                    embedding=embedding,
                    metadata={
                        'title': data.get('title', ''),
                        'summary': data.get('summary', ''),
                        'content': data.get('content', ''),
                        'metadata': data.get('metadata', {})
                    }
                )
                
                if success:
                    stored_ids.append(document_id)
                else:
                    print(f"Failed to store embedding for document '{document_id}'")
            
            except Exception as e:
                print(f"Error processing {filepath}: {e}")
        
        return stored_ids
    
    finally:
        # Disconnect from vector database
        await vector_db.disconnect()


async def search_documents(query_embedding: List[float], 
                          db_type: str = 'pgvector', 
                          collection_name: str = 'default',
                          limit: int = 10,
                          filters: Optional[Dict[str, Any]] = None,
                          config: Optional[Dict[str, Any]] = None,
                          group_chunks: bool = True) -> List[Dict[str, Any]]:
    """Search for similar documents in a vector database.
    
    Args:
        query_embedding: Query embedding as a list of floats
        db_type: Type of vector database to use
        collection_name: Name of the collection to search in
        limit: Maximum number of results to return
        filters: Optional filters to apply to the search
        config: Configuration for the vector database
        group_chunks: Whether to group chunks from the same document
        
    Returns:
        List of documents with their metadata and similarity scores
    """
    # Create vector database
    vector_db = VectorDBFactory.create_vector_db(db_type, config)
    
    # Connect to vector database
    connected = await vector_db.connect()
    if not connected:
        print(f"Failed to connect to {db_type} database")
        return []
    
    try:
        # Search for similar documents
        results = await vector_db.search(
            collection_name=collection_name,
            query_embedding=query_embedding,
            # Request more results if we're grouping chunks
            limit=limit * 3 if group_chunks else limit,
            filters=filters
        )
        
        # If we're not grouping chunks, return as is
        if not group_chunks:
            return results[:limit]
        
        # Group chunks by parent document
        grouped_results = {}
        for result in results:
            # Check if this is a chunk
            metadata = result.get('metadata', {})
            is_chunk = metadata.get('is_chunk', False)
            
            if is_chunk:
                # Get parent document ID
                parent_id = metadata.get('parent_id')
                if not parent_id:
                    continue
                
                # Add to grouped results
                if parent_id not in grouped_results:
                    # Create a new entry for the parent document
                    grouped_results[parent_id] = {
                        'id': parent_id,
                        'title': result.get('title', ''),
                        'content': '',
                        'chunks': [],
                        'similarity': result.get('similarity', 0)
                    }
                
                # Add this chunk to the parent document
                grouped_results[parent_id]['chunks'].append({
                    'content': result.get('content', ''),
                    'similarity': result.get('similarity', 0),
                    'index': metadata.get('chunk_index', 0)
                })
                
                # Update parent similarity to the highest chunk similarity
                if result.get('similarity', 0) > grouped_results[parent_id]['similarity']:
                    grouped_results[parent_id]['similarity'] = result.get('similarity', 0)
            else:
                # Regular document, add directly
                doc_id = result.get('id', '')
                if doc_id and doc_id not in grouped_results:
                    grouped_results[doc_id] = result
        
        # Sort grouped results by similarity
        sorted_results = sorted(
            grouped_results.values(), 
            key=lambda x: x.get('similarity', 0), 
            reverse=True
        )
        
        # For each grouped result, combine chunk content
        for result in sorted_results:
            if 'chunks' in result and result['chunks']:
                # Sort chunks by index
                sorted_chunks = sorted(result['chunks'], key=lambda x: x.get('index', 0))
                
                # Combine chunk content
                result['content'] = '\n\n'.join([
                    f"{chunk.get('content', '')}" 
                    for chunk in sorted_chunks
                ])
                
                # Keep only the top chunks to avoid overwhelming the response
                result['chunks'] = sorted_chunks[:3]
        
        return sorted_results[:limit]
    
    finally:
        # Disconnect from vector database
        await vector_db.disconnect()


async def delete_document(document_id: str, 
                         db_type: str = 'pgvector', 
                         collection_name: str = 'default',
                         config: Optional[Dict[str, Any]] = None) -> bool:
    """Delete a document from a vector database.
    
    Args:
        document_id: Unique identifier for the document
        db_type: Type of vector database to use
        collection_name: Name of the collection to delete from
        config: Configuration for the vector database
        
    Returns:
        True if deletion is successful, False otherwise
    """
    # Create vector database
    vector_db = VectorDBFactory.create_vector_db(db_type, config)
    
    # Connect to vector database
    connected = await vector_db.connect()
    if not connected:
        print(f"Failed to connect to {db_type} database")
        return False
    
    try:
        # Delete document
        success = await vector_db.delete_document(
            collection_name=collection_name,
            document_id=document_id
        )
        
        return success
    
    finally:
        # Disconnect from vector database
        await vector_db.disconnect()


async def delete_collection(collection_name: str, 
                           db_type: str = 'pgvector',
                           config: Optional[Dict[str, Any]] = None) -> bool:
    """Delete a collection from a vector database.
    
    Args:
        collection_name: Name of the collection to delete
        db_type: Type of vector database to use
        config: Configuration for the vector database
        
    Returns:
        True if deletion is successful, False otherwise
    """
    # Create vector database
    vector_db = VectorDBFactory.create_vector_db(db_type, config)
    
    # Connect to vector database
    connected = await vector_db.connect()
    if not connected:
        print(f"Failed to connect to {db_type} database")
        return False
    
    try:
        # Delete collection
        success = await vector_db.delete_collection(collection_name)
        
        return success
    
    finally:
        # Disconnect from vector database
        await vector_db.disconnect()