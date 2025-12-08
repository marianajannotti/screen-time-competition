"""Database models and app-name helpers for the Screen Time backend."""


from flask_login import UserMixin

from .database import db
from .utils import current_time_utc


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


class ScreenTimeLog(db.Model):
    """Per-day screen time entries keyed to an app (or total)."""

    __tablename__ = "screen_time_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    app_name = db.Column(db.String(120), nullable=False)

    # The actual data
    date = db.Column(db.Date, nullable=False)
    screen_time_minutes = db.Column(db.Integer, nullable=False, default=0)

    created_at = db.Column(db.DateTime, default=current_time_utc)

    def to_dict(self) -> dict:
        """Serialize the log for API responses.

        Returns:
            dict: Log metadata plus derived hour/minute fields.
        """

        return {
            "id": self.id,
            "user_id": self.user_id,
            "app_name": self.app_name,
            "date": self.date.isoformat(),
            "screen_time_minutes": self.screen_time_minutes,
            "hours": self.screen_time_minutes // 60,
            "minutes": self.screen_time_minutes % 60,
            "created_at": (
                self.created_at.isoformat() if self.created_at else None
            ),
        }

    def __repr__(self):
        return f"<ScreenTime {self.date}: {self.screen_time_minutes}min>"


class Goal(db.Model):
    """Daily/weekly screen-time goals."""

    __tablename__ = "goals"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    # Goal settings
    goal_type = db.Column(db.String(20), nullable=False)  # 'daily' or 'weekly'
    target_minutes = db.Column(db.Integer, nullable=False)

    def to_dict(self) -> dict:
        """Serialize goal metadata for API responses."""

        return {
            "id": self.id,
            "user_id": self.user_id,
            "goal_type": self.goal_type,
            "target_minutes": self.target_minutes,
        }

    def __repr__(self):
        return f"<Goal {self.goal_type}: {self.target_minutes}min>"


class Friendship(db.Model):
    """Friend relationships used by leaderboard features."""

    __tablename__ = "friendships"
    __table_args__ = (
        db.UniqueConstraint(
            "user_id", "friend_id", name="uq_friendships_pair"
        ),
        db.CheckConstraint(
            "user_id != friend_id", name="chk_friendships_no_self"
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    friend_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
    )

    # Status of friendship
    status = db.Column(db.String(20), default="pending")  # pending/accepted
    created_at = db.Column(db.DateTime, default=current_time_utc)

    def to_dict(self) -> dict:
        """Serialize friendship metadata for API responses."""

        return {
            "id": self.id,
            "user_id": self.user_id,
            "friend_id": self.friend_id,
            "status": self.status,
            "created_at": (
                self.created_at.isoformat() if self.created_at else None
            ),
        }

    def __repr__(self):
        return (
            f"<Friendship {self.user_id} -> {self.friend_id}: {self.status}>"
        )
