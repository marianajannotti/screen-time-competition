"""
Configuration Management for Screen Time Competition App

This module defines configuration classes for different deployment environments
(development, testing, production). Each environment has specific settings for:
- Database connections and security
- CORS policies for frontend integration
- JWT token configuration
- Rate limiting and security controls
- Debug and logging levels

Environment Selection:
The configuration is selected based on the FLASK_ENV environment variable:
- 'development': Local development with debugging enabled
- 'testing': Automated testing with in-memory database
- 'production': Production deployment with security hardened

Security Considerations:
- SECRET_KEY should be a strong random value in production
- Database URLs should use encrypted connections in production
- CORS origins should be restricted to your actual domain in production
- Rate limiting helps prevent abuse and DoS attacks

Usage:
    from backend.config import config
    app.config.from_object(config['development'])
"""

import os


class Config:
    """
    Base Configuration Class
    
    Contains common settings shared across all environments. Specific environments
    inherit from this class and override settings as needed.
    
    Environment Variables Used:
    - SECRET_KEY: Flask secret key for session signing
    - JWT_SECRET_KEY: Separate key for JWT token signing  
    - RATE_LIMIT_ENABLED: Enable/disable rate limiting
    - RATE_LIMIT_PER_MINUTE: Max requests per minute per user
    - RATE_LIMIT_PER_HOUR: Max requests per hour per IP
    """

    # Get secret key from environment variable
    SECRET_KEY = os.environ.get("SECRET_KEY") or "fallback-key-for-development"

    # Database settings
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # Saves memory

    # Allow React frontend to connect (CORS = Cross-Origin Resource Sharing)
    CORS_ORIGINS = ["http://localhost:3000"]
    
    # JWT settings
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY") or SECRET_KEY
    JWT_ACCESS_TOKEN_EXPIRES = False  # Tokens don't expire by default
    
    # Rate limiting settings
    RATE_LIMIT_ENABLED = os.environ.get("RATE_LIMIT_ENABLED", "true").lower() == "true"
    RATE_LIMIT_PER_MINUTE = int(os.environ.get("RATE_LIMIT_PER_MINUTE", "60"))
    RATE_LIMIT_PER_HOUR = int(os.environ.get("RATE_LIMIT_PER_HOUR", "1000"))


class DevelopmentConfig(Config):
    """Settings while you're coding"""

    DEBUG = True  # Show helpful error pages
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or "sqlite:///app.db"


class TestingConfig(Config):
    """Settings for running tests"""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"  # Temporary database


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
