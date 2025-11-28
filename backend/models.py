"""Database models and app-name helpers for the Screen Time backend."""

from datetime import datetime, timezone
from typing import List, Tuple

from flask_login import UserMixin

from .database import db

DEFAULT_APP_NAME = "Total"

# Canonical set of apps exposed to the frontend dropdown.
ALLOWED_APPS: Tuple[str, ...] = (
    DEFAULT_APP_NAME,
    "YouTube",
    "TikTok",
    "Instagram",
    "Safari",
    "Chrome",
    "Messages",
    "Mail",
    "Other",
)


def current_time_utc() -> datetime:
    """Return a timezone-aware UTC timestamp.

    Returns:
        datetime: Current UTC timestamp with tzinfo.
    """

    return datetime.now(timezone.utc)


def list_allowed_apps() -> List[str]:
    """Expose the allowed screen-time apps for dropdowns.

    Returns:
        list[str]: Canonical app labels in display order.
    """

    return list(ALLOWED_APPS)


def canonicalize_app_name(raw_name: str | None) -> str:
    """Normalize a user-provided app name to the canonical list.

    Args:
        raw_name (str | None): App label supplied by the client; may be blank
            or None when the user wants to log total usage.

    Returns:
        str: Canonical app label suitable for persistence.

    Raises:
        ValueError: If the given name is not part of the allowed set.
    """

    if raw_name is None:
        return DEFAULT_APP_NAME

    candidate = str(raw_name).strip()
    if not candidate:
        return DEFAULT_APP_NAME

    lower_candidate = candidate.lower()
    for allowed in ALLOWED_APPS:
        if lower_candidate == allowed.lower():
            return allowed

    raise ValueError(
        "App name must be one of: " + ", ".join(ALLOWED_APPS)
    )


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
            "created_at": self.created_at.isoformat(),
        }

    def __repr__(self):
        return (
            f"<Friendship {self.user_id} -> {self.friend_id}: {self.status}>"
        )
