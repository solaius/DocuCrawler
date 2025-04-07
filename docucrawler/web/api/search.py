"""
Search API endpoints for DocuCrawler Web Application.

This module provides API endpoints for searching documentation.
"""

from flask import jsonify, request
import asyncio
import os
from docucrawler.web.api import api_bp
from docucrawler.vectordb.integration import search_documents
from docucrawler.embedders.enhanced.granite_embedder import EnhancedGraniteEmbedder

# Initialize the embedder
embedder_config = {
    'api_url': os.getenv('GRANITE_EMBEDDINGS_URL'),
    'api_key': os.getenv('GRANITE_EMBEDDINGS_API'),
    'model_name': os.getenv('GRANITE_EMBEDDINGS_MODEL_NAME'),
    'token_limit': int(os.getenv('EMBEDDINGS_TOKEN_LIMIT', '512')),
    'max_concurrent': 5,
    'max_retries': 3,
    'use_advanced_chunking': True
}

embedder = EnhancedGraniteEmbedder(embedder_config)

async def generate_query_embedding(query):
    """Generate embedding for a query.
    
    Args:
        query: The search query.
        
    Returns:
        The query embedding.
    """
    # Use the embedder to generate an embedding for the query
    result = await embedder.embed_document(query)
    
    # Extract the embedding from the result
    if result and 'chunks' in result and len(result['chunks']) > 0:
        return result['chunks'][0]['embedding']
    
    return None

@api_bp.route('/search', methods=['GET', 'POST'])
def search():
    """Search endpoint.
    
    Returns:
        JSON response with search results.
    """
    if request.method == 'POST':
        data = request.json
        query = data.get('query', '')
        collection = data.get('collection', 'mcp')
        db_type = data.get('db_type', 'pgvector')
        limit = data.get('limit', 10)
        group_chunks = data.get('group_chunks', True)
        filters = data.get('filters', {})
        search_type = filters.get('searchType', 'semantic')
    else:
        query = request.args.get('query', '')
        collection = request.args.get('collection', 'mcp')
        db_type = request.args.get('db_type', 'pgvector')
        limit = int(request.args.get('limit', 10))
        group_chunks = request.args.get('group_chunks', 'true').lower() == 'true'
        search_type = request.args.get('search_type', 'semantic')
        filters = {}
    
    if not query:
        return jsonify({
            'error': 'Query parameter is required'
        }), 400
        
    # Process advanced filters
    search_filters = {}
    
    # Add document type filters if provided
    if filters and 'docTypes' in filters:
        search_filters['doc_type'] = filters['docTypes']
    
    # Add content feature filters if provided
    if filters and 'contentFeatures' in filters:
        for feature in filters['contentFeatures']:
            if feature == 'code':
                search_filters['has_code'] = True
            elif feature == 'images':
                search_filters['has_images'] = True
    
    # Run the search asynchronously
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        results = []
        
        # Handle different search types
        if search_type == 'semantic' or search_type == 'hybrid':
            # Generate embedding for the query
            query_embedding = loop.run_until_complete(generate_query_embedding(query))
            
            if not query_embedding:
                return jsonify({
                    'error': 'Failed to generate query embedding'
                }), 500
            
            # Search for documents using vector search
            results = loop.run_until_complete(search_documents(
                query_embedding=query_embedding,
                db_type=db_type,
                collection_name=collection,
                limit=limit,
                filters=search_filters,
                group_chunks=group_chunks
            ))
        
        # For keyword or hybrid search, we would add keyword search here
        # This is a placeholder for future implementation
        if search_type == 'keyword' or search_type == 'hybrid':
            # For now, just log that keyword search was requested
            print(f"Keyword search requested for query: {query}")
            
            # In a real implementation, we would:
            # 1. Perform keyword search
            # 2. If hybrid, merge with semantic results
            # 3. Re-rank combined results
            
            # Placeholder for keyword search
            if search_type == 'keyword' and not results:
                # Simple keyword matching for demonstration
                # In a real implementation, this would use a proper text search engine
                keyword_results = []
                
                # This is just a placeholder and would be replaced with actual keyword search
                # For now, we'll just return the semantic results
        
        # Add search metadata to results
        for result in results:
            result['search_type'] = search_type
        
        return jsonify({
            'query': query,
            'collection': collection,
            'db_type': db_type,
            'search_type': search_type,
            'filters': search_filters,
            'results': results
        })
    
    finally:
        loop.close()

@api_bp.route('/collections', methods=['GET'])
def get_collections():
    """Get available collections.
    
    Returns:
        JSON response with available collections.
    """
    # This is a placeholder. In a real implementation, we would query the database
    # to get the available collections.
    collections = [
        {'id': 'mcp', 'name': 'Model Context Protocol', 'count': 46},
        {'id': 'langchain', 'name': 'LangChain', 'count': 0},
        {'id': 'docling', 'name': 'Docling', 'count': 0},
        {'id': 'llama-stack', 'name': 'Meta Llama Stack', 'count': 0}
    ]
    
    return jsonify({
        'collections': collections
    })

@api_bp.route('/db-types', methods=['GET'])
def get_db_types():
    """Get available database types.
    
    Returns:
        JSON response with available database types.
    """
    db_types = [
        {'id': 'pgvector', 'name': 'PGVector'},
        {'id': 'elasticsearch', 'name': 'Elasticsearch'},
        {'id': 'weaviate', 'name': 'Weaviate'}
    ]
    
    return jsonify({
        'db_types': db_types
    })