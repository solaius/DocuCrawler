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

# Get Granite Instruct API credentials from environment variables
GRANITE_INSTRUCT_URL = os.getenv('GRANITE_INSTRUCT_URL')
GRANITE_INSTRUCT_API = os.getenv('GRANITE_INSTRUCT_API')
GRANITE_INSTRUCT_MODEL_NAME = os.getenv('GRANITE_INSTRUCT_MODEL_NAME', 'granite-3-8b-instruct')

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
    
    # Check if Granite Instruct API credentials are available
    if not GRANITE_INSTRUCT_URL or not GRANITE_INSTRUCT_API:
        return jsonify({
            'error': 'Granite Instruct API credentials not configured'
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
        
        # Prepare the prompt for the Instruct model
        # Format the conversation history and context into a single prompt
        prompt = "You are DocuCrawler Assistant, a helpful AI that answers questions about documentation.\n\n"
        
        # Add conversation history
        if history:
            prompt += "Previous conversation:\n"
            for msg in history:
                role = msg.get('role', 'user')
                content = msg.get('content', '')
                if role and content:
                    if role == 'user':
                        prompt += f"User: {content}\n"
                    else:
                        prompt += f"Assistant: {content}\n"
            prompt += "\n"
        
        # Add context from search results
        prompt += f"Context information from documentation:\n{context}\n\n"
        
        # Add the current question
        prompt += f"User: {message}\n\nAssistant: "
        
        # Call the Granite Instruct API
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {GRANITE_INSTRUCT_API}"
        }
        
        # Construct the API URL with the /v1/chat/completions endpoint
        api_url = f"{GRANITE_INSTRUCT_URL.rstrip('/')}/v1/chat/completions"
        
        payload = {
            "model": GRANITE_INSTRUCT_MODEL_NAME,
            "prompt": prompt,
            "temperature": 0.7,
            "max_tokens": 1000,
            "stop": ["User:", "\n\n"]
        }
        
        print(f"Calling Granite Instruct API at: {api_url}")
        
        response = requests.post(
            api_url,
            headers=headers,
            json=payload
        )
        
        if response.status_code != 200:
            print(f"API Error: {response.status_code} - {response.text}")
            return jsonify({
                'error': f'Granite Instruct API error: {response.text}'
            }), 500
        
        # Parse the response
        response_data = response.json()
        print(f"API Response: {response_data}")
        
        # Extract the assistant's reply
        assistant_reply = response_data.get('choices', [{}])[0].get('text', '')
        
        return jsonify({
            'reply': assistant_reply,
            'sources': [{'title': r.get('title', ''), 'id': r.get('id', '')} for r in results]
        })
    
    except Exception as e:
        return jsonify({
            'error': f'Error processing request: {str(e)}'
        }), 500