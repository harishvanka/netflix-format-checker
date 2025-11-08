"""
Netflix Format Checker - Flask Application Package
"""

from flask import Flask
import logging

def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__,
                template_folder='../templates',
                static_folder='../static')

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Register blueprints/routes
    from app.routes import bp
    app.register_blueprint(bp)

    # Add after_request handler
    @app.after_request
    def after_request(response):
        """Add headers to every response"""
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        return response

    return app
