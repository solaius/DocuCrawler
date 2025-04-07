"""
DocuCrawler Web Application Module.

This module provides a web interface for searching and interacting with documentation
crawled and processed by DocuCrawler.
"""

from flask import Flask
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

def create_app(test_config=None):
    """Create and configure the Flask application.
    
    Args:
        test_config: Test configuration to use instead of instance configuration.
        
    Returns:
        The configured Flask application.
    """
    # Create and configure the app
    app = Flask(__name__, 
                instance_relative_config=True,
                static_folder='static',
                template_folder='templates')
    
    # Set default configuration
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('FLASK_SECRET_KEY', 'dev'),
        DATABASE=os.path.join(app.instance_path, 'docucrawler.sqlite'),
    )

    if test_config is None:
        # Load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # Load the test config if passed in
        app.config.from_mapping(test_config)

    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Register blueprints
    from docucrawler.web.api import api_bp
    app.register_blueprint(api_bp)
    
    from docucrawler.web.chatbot import chatbot_bp
    app.register_blueprint(chatbot_bp)
    
    # A simple route to confirm the app is working
    @app.route('/')
    def index():
        return app.send_static_file('index.html')

    return app