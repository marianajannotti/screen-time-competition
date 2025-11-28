"""
Database Configuration for Screen Time Competition App

This module provides the shared SQLAlchemy database instance used throughout
the application. Using a single shared instance ensures all models and routes
use the same database connection and configuration.

Database Architecture:
- SQLAlchemy ORM for database operations
- Support for SQLite (development) and PostgreSQL (production)
- Automatic table creation and migration support
- Connection pooling and transaction management

Usage Pattern:
1. Import the db instance in models and routes
2. Initialize with Flask app using db.init_app(app)
3. Create tables with db.create_all() in app context
4. Use db.session for database operations

Key Benefits:
- Centralized database configuration
- Consistent connection management across modules
- Support for multiple database backends
- Automatic cleanup and connection pooling
- Integration with Flask application factory pattern

Example:
    from backend.database import db
    from backend.models import User
    
    # In route handler
    user = User.query.get(user_id)
    db.session.commit()
"""

from flask_sqlalchemy import SQLAlchemy

# Create the shared SQLAlchemy database instance
# This instance will be initialized with the Flask app in the factory function
# and used by all models and routes for database operations
db = SQLAlchemy()
