"""
Chatbot Blueprint for DocuCrawler Web Application.

This module provides endpoints for interacting with the chatbot.
"""

from flask import Blueprint, jsonify, request
import os

chatbot_bp = Blueprint('chatbot', __name__, url_prefix='/chatbot')

@chatbot_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint.
    
    Returns:
        JSON response with status information.
    """
    return jsonify({
        'status': 'ok',
        'version': '0.1.0'
    })

# Import and register other chatbot routes
from docucrawler.web.chatbot.chat import *