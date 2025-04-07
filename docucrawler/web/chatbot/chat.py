"""
Chat endpoints for DocuCrawler Web Application.

This module provides endpoints for interacting with the chatbot.
"""

from flask import jsonify, request
import os
import requests
import json
import asyncio
from docucrawler.web.chatbot import chatbot_bp
from docucrawler.vectordb.integration import search_documents
from docucrawler.web.api.search import generate_query_embedding

# Get Granite LLM API credentials from environment variables
GRANITE_LLM_URL = os.getenv('GRANITE_LLM_URL')
GRANITE_LLM_API_KEY = os.getenv('GRANITE_LLM_API_KEY')
GRANITE_LLM_MODEL = os.getenv('GRANITE_LLM_MODEL', 'granite-7b-chat')

@chatbot_bp.route('/chat', methods=['POST'])
def chat():
    """Chat endpoint.
    
    Returns:
        JSON response with chatbot reply.
    """
    data = request.json
    
    if not data:
        return jsonify({
            'error': 'Request body is required'
        }), 400
    
    message = data.get('message', '')
    collection = data.get('collection', 'mcp')
    db_type = data.get('db_type', 'pgvector')
    history = data.get('history', [])
    
    if not message:
        return jsonify({
            'error': 'Message is required'
        }), 400
    
    # Check if Granite LLM API credentials are available
    if not GRANITE_LLM_URL or not GRANITE_LLM_API_KEY:
        return jsonify({
            'error': 'Granite LLM API credentials not configured'
        }), 500
    
    try:
        # First, search for relevant documents
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Generate embedding for the query
            query_embedding = loop.run_until_complete(generate_query_embedding(message))
            
            if not query_embedding:
                return jsonify({
                    'error': 'Failed to generate query embedding'
                }), 500
            
            # Search for documents
            results = loop.run_until_complete(search_documents(
                query_embedding=query_embedding,
                db_type=db_type,
                collection_name=collection,
                limit=5,
                group_chunks=True
            ))
        finally:
            loop.close()
        
        # Extract content from search results to use as context
        context = ""
        for result in results:
            content = result.get('content', '')
            if content:
                context += content + "\n\n"
        
        # Prepare the prompt for the LLM
        system_prompt = f"""You are DocuCrawler Assistant, a helpful AI that answers questions about documentation.
Use the following context to answer the user's question. If you don't know the answer, say so.

Context:
{context}"""
        
        # Prepare the messages for the LLM
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        # Add history messages
        for msg in history:
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            if role and content:
                messages.append({"role": role, "content": content})
        
        # Add the current message
        messages.append({"role": "user", "content": message})
        
        # Call the Granite LLM API
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {GRANITE_LLM_API_KEY}"
        }
        
        payload = {
            "model": GRANITE_LLM_MODEL,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        response = requests.post(
            GRANITE_LLM_URL,
            headers=headers,
            json=payload
        )
        
        if response.status_code != 200:
            return jsonify({
                'error': f'Granite LLM API error: {response.text}'
            }), 500
        
        # Parse the response
        response_data = response.json()
        
        # Extract the assistant's reply
        assistant_reply = response_data.get('choices', [{}])[0].get('message', {}).get('content', '')
        
        return jsonify({
            'reply': assistant_reply,
            'sources': [{'title': r.get('title', ''), 'id': r.get('id', '')} for r in results]
        })
    
    except Exception as e:
        return jsonify({
            'error': f'Error processing request: {str(e)}'
        }), 500