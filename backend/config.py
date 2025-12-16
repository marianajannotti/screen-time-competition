"""
Simple Configuration for Screen Time App
Just the essentials to get started!
"""

import os


class Config:
    """Basic settings that all environments need"""

    # Get secret key from environment variable
    SECRET_KEY = os.environ.get("SECRET_KEY") or "fallback-key-for-development"

    # Database settings
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # Saves memory

    # Allow React frontend to connect (CORS = Cross-Origin Resource Sharing)
    # Include typical React dev ports (3000 Create React App, 5173/5174 Vite)
    CORS_ORIGINS = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174",
    ]

    # Flask-Mail configuration for Gmail SMTP
    MAIL_SERVER = "smtp.gmail.com"
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_USERNAME")  # Use same email as sender


class DevelopmentConfig(Config):
    """Settings while you're coding"""

    DEBUG = True  # Show helpful error pages
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or "sqlite:///app.db"


class TestingConfig(Config):
    """Settings for running tests"""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"  # Temporary database
    
    # Override mail settings for testing
    MAIL_DEFAULT_SENDER = "test@example.com"
    MAIL_SUPPRESS_SEND = True  # Don't actually send emails during tests


class ProductionConfig(Config):
    """Settings for live app (when you deploy)"""

    DEBUG = False  # Don't show errors to users
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or "sqlite:///app_prod.db"


# Easy way to pick which config to use
config = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,  # Use this if nothing specified
}
