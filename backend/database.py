"""
Database configuration for Screen Time Competition
Shared SQLAlchemy instance
"""

from flask_sqlalchemy import SQLAlchemy

# Create the shared database instance
db = SQLAlchemy()
