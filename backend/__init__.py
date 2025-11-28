"""Flask application factory and extension wiring for the backend."""

from __future__ import annotations

from flask import Flask
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


def create_app(config_name: str | None = None) -> Flask:
    """Build and configure a Flask app instance.

    Args:
        config_name (str | None): Optional config key; falls back to
            ``FLASK_ENV`` or ``development`` when missing.

    Returns:
        Flask: Configured application with extensions and blueprints.
    """

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
    def load_user(user_id: str):
        """Look up the session user for Flask-Login callbacks.

        Args:
            user_id (str): Identifier stored in the session cookie.

        Returns:
            User | None: Matching user instance when found.
        """

        return User.query.get(int(user_id))

    # Register blueprints
    from .auth import auth_bp
    from .screen_time import screen_time_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(screen_time_bp)

    # Create database tables
    with app.app_context():
        db.create_all()

    return app
