"""
Simple SQLAlchemy Models for Screen Time Competition
Starting with just the basics - we can add more later
"""

from flask_login import UserMixin
from datetime import datetime

# Import the shared database instance
from .database import db


class User(UserMixin, db.Model):
    """
    User model - represents people who use your app

    Much simpler with integer IDs: 1, 2, 3, 4...
    """

    __tablename__ = "users"

    # Simple integer ID - SQLAlchemy auto-increments: 1, 2, 3, 4...
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    # Gamification (for profile page)
    streak_count = db.Column(db.Integer, default=0)
    total_points = db.Column(db.Integer, default=0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Flask-Login requirement
    def get_id(self):
        return str(self.id)  # Flask-Login needs string

    # Convert to JSON for React
    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "streak_count": self.streak_count,
            "total_points": self.total_points,
        }

    def __repr__(self):
        return f"<User {self.username}>"


class ScreenTimeLog(db.Model):
    """
    Screen time entries - for home page

    Simple integer IDs: 1, 2, 3, 4...
    """

    __tablename__ = "screen_time_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    # The actual data
    date = db.Column(db.Date, nullable=False)
    screen_time_minutes = db.Column(db.Integer, nullable=False, default=0)
    
    # Optional: track top apps manually
    top_apps = db.Column(db.Text)  # JSON string of app usage

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Ensure one entry per user per date
    __table_args__ = (db.UniqueConstraint('user_id', 'date', name='unique_user_date'),)

    def to_dict(self):
        import json
        top_apps_data = []
        if self.top_apps:
            try:
                top_apps_data = json.loads(self.top_apps)
            except:
                top_apps_data = []
                
        return {
            "id": self.id,
            "user_id": self.user_id,
            "date": self.date.isoformat(),
            "screen_time_minutes": self.screen_time_minutes,
            "top_apps": top_apps_data,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<ScreenTime {self.date}: {self.screen_time_minutes}min>"


class Goal(db.Model):
    """
    User goals - daily/weekly limits for home page

    Simple integer IDs: 1, 2, 3, 4...
    """

    __tablename__ = "goals"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    # Goal settings
    goal_type = db.Column(db.String(20), nullable=False)  # 'daily' or 'weekly'
    target_minutes = db.Column(db.Integer, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "goal_type": self.goal_type,
            "target_minutes": self.target_minutes,
        }

    def __repr__(self):
        return f"<Goal {self.goal_type}: {self.target_minutes}min>"


class Friendship(db.Model):
    """
    Friend connections - for leaderboard page

    Simple integer IDs: 1, 2, 3, 4...
    """

    __tablename__ = "friendships"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    friend_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    # Status of friendship
    status = db.Column(db.String(20), default="pending")  # pending/accepted
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "friend_id": self.friend_id,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
        }

    def __repr__(self):
        return f"<Friendship {self.user_id} -> {self.friend_id}: {self.status}>"
