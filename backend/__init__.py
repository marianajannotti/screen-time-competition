"""
Backend Package for Screen Time Competition App

This module provides the Flask application factory and configuration for the 
Screen Time Competition backend. It implements the Flask app factory pattern
for flexible configuration across different environments.

Key Features:
- Flask app factory pattern for multiple environments (dev, test, prod)
- JWT-based authentication with Flask-Login
- CORS configuration for React frontend integration
- Centralized database and extension initialization
- Blueprint registration for modular routing

Usage:
    # Direct app creation
    app = create_app('development')
    
    # Using environment variable
    app = create_app()  # Uses FLASK_ENV environment variable
"""

from flask import Flask, jsonify
from flask_login import LoginManager
from flask_cors import CORS
from dotenv import load_dotenv
import os

# Import shared database instance for SQLAlchemy integration
from .database import db

# Load environment variables from .env file for configuration
# This must be called early to ensure variables are available
load_dotenv()

# Initialize Flask-Login manager (will be configured in create_app)
login_manager = LoginManager()


def create_app(config_name=None):
    """
    Flask Application Factory
    
    Creates and configures a Flask application instance with all necessary
    extensions, blueprints, and configurations. Uses the app factory pattern
    to support multiple environments and testing scenarios.
    
    Args:
        config_name (str, optional): Configuration environment name.
                                   Options: 'development', 'testing', 'production'
                                   Defaults to FLASK_ENV environment variable or 'development'
    
    Returns:
        Flask: Configured Flask application instance
        
    Example:
        app = create_app('development')  # Development configuration
        app = create_app('production')   # Production configuration
        app = create_app()              # Uses FLASK_ENV or defaults to development
    """
    # Create Flask application instance
    app = Flask(__name__)

    # Determine configuration environment
    # Priority: parameter > environment variable > default
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "development")

    # Import and apply configuration class
    from .config import config
    app.config.from_object(config[config_name])

    # Initialize SQLAlchemy database with app context
    db.init_app(app)

    # Configure CORS (Cross-Origin Resource Sharing) for React frontend
    # Allows the React app to make API calls to this Flask backend
    CORS(app, origins=app.config["CORS_ORIGINS"])

    # Configure Flask-Login for user session management
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"  # Redirect endpoint for unauthorized access

    # Import User model for Flask-Login integration
    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        """
        Flask-Login User Loader Function
        
        Required by Flask-Login to reload a user object from the user ID 
        stored in the session. This function is called on every request
        to an endpoint that requires authentication.
        
        Args:
            user_id (str): User ID stored in the session (Flask-Login passes this as string)
            
        Returns:
            User|None: User object if found, None if user doesn't exist
        """
        return User.query.get(int(user_id))

<<<<<<< HEAD
    # ========================
    # Blueprint Registration
    # ========================
    # Import all route blueprints for modular organization
    # Each blueprint handles a specific domain of functionality
    
    from .auth import auth_bp                    # Authentication: login, register, logout
    from .screentime_routes import screentime_bp  # Screen time: logging, history, stats
    from .goals_routes import goals_bp           # Goals: create, update, progress tracking
    from .friends_routes import friends_bp       # Social: friends, requests, leaderboard
    from .profile_routes import profile_bp       # Profile: user management, settings

    # Register all blueprints with the Flask application
    # This makes all routes from each blueprint available under their URL prefixes
    app.register_blueprint(auth_bp)        # /api/auth/*
    app.register_blueprint(screentime_bp)  # /api/screentime/*
    app.register_blueprint(goals_bp)       # /api/goals/*
    app.register_blueprint(friends_bp)     # /api/friends/*
    app.register_blueprint(profile_bp)     # /api/profile/*
=======
    # Register blueprints
    from .auth import auth_bp
    from .screentime_routes import screentime_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(screentime_bp)

    @app.route("/", methods=["GET"])
    def root_index():
        """Simple root endpoint to avoid 404 on /"""
        return jsonify({"message": "API root. See /api/auth and /api/screentime"}), 200
>>>>>>> 9b67612dccc770a661f9a1a97dfe159e63e027eb

    @app.route("/", methods=["GET"])
    def root_index():
        """
        Root API Endpoint
        
        Simple health check endpoint that returns basic API information.
        Helps verify the API is running and provides guidance on available endpoints.
        
        Returns:
            tuple: JSON response with API info and 200 status code
        """
        return jsonify({
            "message": "Screen Time Competition API",
            "version": "1.0.0",
            "endpoints": {
                "authentication": "/api/auth",
                "screen_time": "/api/screentime", 
                "goals": "/api/goals",
                "friends": "/api/friends",
                "profile": "/api/profile"
            },
            "documentation": "/api/docs"
        }), 200

    # ========================
    # Database Initialization
    # ========================
    # Create all database tables if they don't exist
    # This runs in the application context to ensure proper setup
    with app.app_context():
        db.create_all()

    return app


<<<<<<< HEAD
# ========================
# Default App Instance
# ========================
# Create a default app instance for Flask CLI compatibility
# This allows running `flask run` from the command line while maintaining
# the factory pattern for flexibility in testing and deployment
=======
# Create a default app instance so `flask run` can import `backend.app` and
# routes are registered when the package is imported by the Flask CLI.
# This keeps the factory pattern but provides an `app` variable for CLI convenience.
>>>>>>> 9b67612dccc770a661f9a1a97dfe159e63e027eb
app = create_app(os.environ.get("FLASK_ENV", "development"))
