"""
Backend package for Screen Time Competition
Flask app factory pattern with environment variables
"""

from flask import Flask, jsonify
from flask_login import LoginManager
from flask_cors import CORS
from dotenv import load_dotenv
import os

# Import shared database instance
from .database import db

# Load environment variables from .env file
load_dotenv()


# Initialize extensions 
login_manager = LoginManager()


def create_app(config_name=None):
    """
    Application factory pattern
    Creates and configures the Flask app
    """
    # Create Flask app
    app = Flask(__name__)

    # Load configuration
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "development")

    from .config import config

    app.config.from_object(config[config_name])

    # Initialize extensions with app
    db.init_app(app)

    # Setup CORS for React frontend
    CORS(app, origins=app.config["CORS_ORIGINS"])

    # Setup Flask-Login
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    # Import models
    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        """Load user for Flask-Login"""
        return User.query.get(int(user_id))

    # Register blueprints
    from .auth import auth_bp
    from .screentime_routes import screentime_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(screentime_bp)

    @app.route("/", methods=["GET"])
    def root_index():
        """Simple root endpoint to avoid 404 on /"""
        return jsonify({"message": "API root. See /api/auth and /api/screentime"}), 200

    # Create database tables
    with app.app_context():
        db.create_all()

    return app


# Create a default app instance so `flask run` can import `backend.app` and
# routes are registered when the package is imported by the Flask CLI.
# This keeps the factory pattern but provides an `app` variable for CLI convenience.
app = create_app(os.environ.get("FLASK_ENV", "development"))
