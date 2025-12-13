"""Flask application factory and extension wiring for the backend."""

from __future__ import annotations

from flask import Flask
from flask_login import LoginManager
from flask_cors import CORS
from flask_mail import Mail
from dotenv import load_dotenv
import os

# Import shared database instance
from .database import db

# Load environment variables from .env file
load_dotenv()


# Initialize extensions
login_manager = LoginManager()
mail = Mail()


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
    mail.init_app(app)

    # Setup CORS for React frontend with credentials (cookies)
    CORS(
        app,
        origins=app.config["CORS_ORIGINS"],
        supports_credentials=True,
        allow_headers=[
            "Content-Type",
            "Authorization",
            "Accept",
            "Cache-Control",
            "Pragma",
        ],
        methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
    )

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
    from .api import (
        auth_bp,
        screen_time_bp,
        friendship_bp,
        badges_bp,
        leaderboard_bp,
        challenges_bp,
    )

    app.register_blueprint(auth_bp)
    app.register_blueprint(screen_time_bp)
    app.register_blueprint(friendship_bp)
    app.register_blueprint(badges_bp)
    app.register_blueprint(leaderboard_bp)
    app.register_blueprint(challenges_bp)

    # Create database tables
    with app.app_context():
        db.create_all()

    return app
