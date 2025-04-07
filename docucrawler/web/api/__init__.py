"""
API Blueprint for DocuCrawler Web Application.

This module provides API endpoints for searching and retrieving documentation.
"""

from flask import Blueprint, jsonify, request
import os

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint.
    
    Returns:
        JSON response with status information.
    """
    return jsonify({
        'status': 'ok',
        'version': '0.1.0'
    })

# Import and register other API routes
from docucrawler.web.api.search import *