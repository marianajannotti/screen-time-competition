"""
SQLAlchemy Database Models for Screen Time Competition App

This module defines all database models using SQLAlchemy ORM. Each model
represents a table in the database and includes:
- Primary keys and relationships
- Data validation constraints  
- Utility methods for JSON serialization
- Flask-Login integration where needed

Models:
- User: User accounts with authentication and gamification
- ScreenTimeLog: Daily screen time entries with app usage details  
- Goal: User-defined screen time goals (daily/weekly limits)
- Friendship: Social connections between users for competition

Database Design Philosophy:
- Simple integer primary keys for performance
- Proper foreign key relationships with constraints
- Unique constraints to prevent data duplication
- Timestamps for audit trails
- JSON serialization methods for API responses
"""

from flask_login import UserMixin
from datetime import datetime
import json

# Import the shared SQLAlchemy database instance
from .database import db


class User(UserMixin, db.Model):
    """
    User model - represents people who use your app
    
    Inherits from UserMixin for Flask-Login compatibility.
    Tracks user authentication, profile info, and gamification stats.
    
    Attributes:
        id: Primary key, auto-incrementing integer
        username: Unique username for login (3-50 chars)
        email: Unique email address for account
        password_hash: Hashed password (never store plain text!)
        streak_count: Current consecutive days of logging screen time
        total_points: Total points earned from activities and goals
        created_at: When the user account was created
    """

    __tablename__ = "users"

    # Primary key - SQLAlchemy auto-increments: 1, 2, 3, 4...
    id = db.Column(db.Integer, primary_key=True)
    
    # User identification and authentication
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    email = db.Column(db.String(100), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)  # Never store plain passwords!

    # Gamification fields (automatically calculated by business logic)
    streak_count = db.Column(db.Integer, default=0)  # Consecutive days logged
    total_points = db.Column(db.Integer, default=0)  # Total points earned

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Flask-Login requirement - returns user ID as string
    def get_id(self):
        """Return user ID as string for Flask-Login session management."""
        return str(self.id)

    def to_dict(self):
        """
        Convert User object to dictionary for JSON API responses.
        
        Excludes sensitive information like password_hash and includes
        only data that should be exposed to the frontend application.
        
        Returns:
            dict: Clean user data for JSON serialization
                - id: User's unique identifier
                - username: Display name
                - email: Account email
                - streak_count: Current consecutive days streak
                - total_points: Total gamification points earned
                - created_at: Account creation timestamp (ISO format)
        """
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "streak_count": self.streak_count,
            "total_points": self.total_points,
            "created_at": self.created_at.isoformat()
        }

    def __repr__(self):
        """Developer-friendly string representation for debugging and logging."""
        return f"<User {self.username} (ID: {self.id})>"


class ScreenTimeLog(db.Model):
    """
    Screen Time Log Model - Daily screen usage tracking
    
    Stores manual screen time entries submitted by users. Each user can have
    exactly one entry per date, enforced by a unique constraint. This prevents
    duplicate entries and ensures data consistency.
    
    Key Features:
    - One entry per user per date (unique constraint)
    - Tracks total daily screen time in minutes
    - Optional detailed app usage breakdown (JSON format)
    - Automatic timestamp tracking for audit trails
    - Integration with gamification system (streaks, points)
    
    Relationships:
    - Belongs to User (many-to-one via user_id foreign key)
    
    Database Constraints:
    - Unique constraint on (user_id, date) prevents duplicates
    - Screen time minutes must be non-negative (enforced in validation)
    
    Attributes:
        id: Primary key
        user_id: Foreign key linking to User table
        date: The date this screen time was logged for
        screen_time_minutes: Total screen time in minutes for this date
        top_apps: JSON string containing app usage breakdown (optional)
        created_at: When this log entry was created
        updated_at: When this log entry was last modified
    """

    __tablename__ = "screen_time_logs"

    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign key to users table - which user this belongs to
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

<<<<<<< HEAD
    # Core screen time data
    date = db.Column(db.Date, nullable=False, index=True)  # Date being logged
    screen_time_minutes = db.Column(db.Integer, nullable=False, default=0)  # Total minutes
    
    # Optional: detailed app usage breakdown stored as JSON
    # Example: '[{"name": "Instagram", "minutes": 60}, {"name": "TikTok", "minutes": 45}]'
    top_apps = db.Column(db.Text)
=======
    # The actual data
    date = db.Column(db.Date, nullable=False)
    screen_time_minutes = db.Column(db.Integer, nullable=False, default=0)
    
    # Optional: track top apps manually
    top_apps = db.Column(db.Text)  # JSON string of app usage
>>>>>>> 9b67612dccc770a661f9a1a97dfe159e63e027eb

    # Audit timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

<<<<<<< HEAD
    # Database constraint: one entry per user per date
    __table_args__ = (db.UniqueConstraint('user_id', 'date', name='unique_user_date'),)

    def to_dict(self):
        """
        Convert ScreenTimeLog object to dictionary for JSON API responses.
        
        Safely parses the JSON string stored in top_apps field and handles
        any parsing errors gracefully. The top_apps field stores detailed
        app usage as JSON, which needs to be converted back to Python objects.
        
        JSON Format Example:
            top_apps: '[{"name": "Instagram", "minutes": 60}, {"name": "YouTube", "minutes": 30}]'
        
        Returns:
            dict: Complete screen time log data with:
                - id: Unique log entry identifier
                - user_id: ID of the user who owns this log
                - date: ISO format date string (YYYY-MM-DD)
                - screen_time_minutes: Total screen time for this date
                - top_apps: Parsed list of app usage objects
                - created_at: When log was created (ISO timestamp)
                - updated_at: When log was last modified (ISO timestamp or None)
        """
        # Parse top_apps JSON string safely with error handling
=======
    # Ensure one entry per user per date
    __table_args__ = (db.UniqueConstraint('user_id', 'date', name='unique_user_date'),)

    def to_dict(self):
        import json
>>>>>>> 9b67612dccc770a661f9a1a97dfe159e63e027eb
        top_apps_data = []
        if self.top_apps:
            try:
                top_apps_data = json.loads(self.top_apps)
<<<<<<< HEAD
            except (json.JSONDecodeError, TypeError):
                # If JSON parsing fails, return empty list to prevent API errors
=======
            except:
>>>>>>> 9b67612dccc770a661f9a1a97dfe159e63e027eb
                top_apps_data = []
                
        return {
            "id": self.id,
            "user_id": self.user_id,
            "date": self.date.isoformat(),  # Convert date object to ISO string
            "screen_time_minutes": self.screen_time_minutes,
<<<<<<< HEAD
            "top_apps": top_apps_data,  # Parsed app usage breakdown
=======
            "top_apps": top_apps_data,
>>>>>>> 9b67612dccc770a661f9a1a97dfe159e63e027eb
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        """Developer-friendly string representation for debugging and logging."""
        return f"<ScreenTimeLog {self.date}: {self.screen_time_minutes}min (User: {self.user_id})>"


class Goal(db.Model):
    """
    Goal Model - User-defined screen time targets
    
    Allows users to set daily or weekly screen time limits to help them
    manage their device usage. Goals are used by the gamification system
    to calculate points and track progress.
    
    Key Features:
    - Support for daily and weekly goal types
    - Target time specified in minutes
    - Integration with progress tracking system
    - Points awarded when goals are met
    
    Goal Types:
    - 'daily': Target screen time limit for each day
    - 'weekly': Target screen time limit for the entire week
    
    Business Logic Integration:
    - Goals are evaluated by BusinessLogicService
    - Meeting goals awards bonus points to users
    - Progress is calculated in real-time for API responses
    """

    __tablename__ = "goals"

    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign key to users table - which user this goal belongs to
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    # Goal configuration
    goal_type = db.Column(db.String(20), nullable=False, index=True)  # 'daily' or 'weekly'
    target_minutes = db.Column(db.Integer, nullable=False)  # Target screen time limit in minutes

    def to_dict(self):
        """
        Convert Goal object to dictionary for JSON API responses.
        
        Returns:
            dict: Goal data containing:
                - id: Unique goal identifier
                - user_id: ID of the user who owns this goal
                - goal_type: Type of goal ('daily' or 'weekly')
                - target_minutes: Target screen time limit in minutes
        """
        return {
            "id": self.id,
            "user_id": self.user_id,
            "goal_type": self.goal_type,
            "target_minutes": self.target_minutes,
        }

    def __repr__(self):
        """Developer-friendly string representation for debugging and logging."""
        return f"<Goal {self.goal_type}: {self.target_minutes}min (User: {self.user_id})>"


class Friendship(db.Model):
    """
    Friendship Model - Social connections between users
    
    Manages friend relationships for the social competition aspect of the app.
    Supports a friend request system with pending/accepted states.
    
    Key Features:
    - Friend request system (send, accept, reject)
    - Bidirectional friendship representation
    - Status tracking (pending, accepted)
    - Timestamp for friendship creation
    - Integration with leaderboard system
    
    Friendship States:
    - 'pending': Friend request sent but not yet accepted
    - 'accepted': Both users are friends and can see each other in leaderboards
    
    Database Design:
    - Each friendship is stored as a single record
    - user_id is the person who sent the friend request
    - friend_id is the person who received the friend request
    - When accepted, both users can see each other in leaderboards
    
    Social Features Integration:
    - Used by leaderboard system to show friends' progress
    - Enables friendly competition between users
    - Powers social features like friend-only leaderboards

    Simple integer IDs: 1, 2, 3, 4...
    """

    __tablename__ = "friendships"

    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign keys to users table - represents the friendship relationship
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)    # Friend request sender
    friend_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)  # Friend request recipient

    # Friendship status and metadata
    status = db.Column(db.String(20), default="pending", index=True)  # 'pending' or 'accepted'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)       # When friendship was initiated

    def to_dict(self):
        """
        Convert Friendship object to dictionary for JSON API responses.
        
        Returns:
            dict: Friendship data containing:
                - id: Unique friendship identifier
                - user_id: ID of the user who sent the friend request
                - friend_id: ID of the user who received the friend request
                - status: Current status ('pending' or 'accepted')
                - created_at: When the friendship was created (ISO timestamp)
        """
        return {
            "id": self.id,
            "user_id": self.user_id,
            "friend_id": self.friend_id,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
        }

    def __repr__(self):
        """Developer-friendly string representation for debugging and logging."""
        return f"<Friendship {self.user_id} -> {self.friend_id}: {self.status}>"
