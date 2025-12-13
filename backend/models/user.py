"""User model for authentication and user management."""

from flask_login import UserMixin

from ..database import db
from ..utils import current_time_utc


class User(UserMixin, db.Model):
    """Authenticated user tracked by Flask-Login."""

    __tablename__ = "users"

    # Simple integer ID - SQLAlchemy auto-increments: 1, 2, 3, 4...
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    # Gamification (for profile page)
    streak_count = db.Column(db.Integer, default=0)
    total_points = db.Column(db.Integer, default=0)

    # Password reset
    reset_token = db.Column(db.String(100), nullable=True)
    reset_token_expiry = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, default=current_time_utc)

    def get_id(self) -> str:
        """Return the user identifier required by Flask-Login."""

        return str(self.id)

    def to_dict(self) -> dict:
        """Serialize the user for JSON responses.

        Returns:
            dict: Public user fields consumed by the frontend.
        """

        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "streak_count": self.streak_count,
            "total_points": self.total_points,
        }

    def __repr__(self):
        return f"<User {self.username}>"
