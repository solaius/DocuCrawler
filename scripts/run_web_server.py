#!/usr/bin/env python3
"""
Script to run the DocuCrawler web server.
"""

import os
import argparse
from docucrawler.web import create_app

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description='Run the DocuCrawler web server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    # Create the Flask application
    app = create_app()
    
    # Run the application
    app.run(host=args.host, port=args.port, debug=args.debug)

if __name__ == '__main__':
    main()