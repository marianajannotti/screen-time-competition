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

    # Relationships for eager loading and serialization
    user = db.relationship(
        "User",
        foreign_keys=[user_id],
        backref="friendships_sent",
    )
    friend = db.relationship(
        "User",
        foreign_keys=[friend_id],
        backref="friendships_received",
    )

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


class Badge(db.Model):
    """Available badges that users can earn."""
    
    __tablename__ = "badges"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=False)
    badge_type = db.Column(db.String(50), nullable=False)  # streak, reduction, social, leaderboard, prestige
    icon = db.Column(db.String(10), default='🏆')  # emoji icon
    
    created_at = db.Column(db.DateTime, default=current_time_utc)
    
    def to_dict(self) -> dict:
        """Serialize badge for API responses."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "badge_type": self.badge_type,
            "icon": self.icon,
        }
    
    def __repr__(self):
        return f"<Badge {self.name}>"


class UserBadge(db.Model):
    """Junction table for user-earned badges with timestamps."""
    
    __tablename__ = "user_badges"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    badge_id = db.Column(db.Integer, db.ForeignKey("badges.id"), nullable=False)
    earned_at = db.Column(db.DateTime, default=current_time_utc)
    
    # Relationships
    user = db.relationship("User", backref="user_badges")
    badge = db.relationship("Badge", backref="user_badges")
    
    # Ensure a user can only earn each badge once
    __table_args__ = (db.UniqueConstraint('user_id', 'badge_id', name='uq_user_badge'),)
    
    def to_dict(self) -> dict:
        """Serialize user badge for API responses."""
        return {
            "id": self.id,
            "name": self.badge.name,
            "earned_at": self.earned_at.isoformat() if self.earned_at else None,
        }
    
    def __repr__(self):
        return f"<UserBadge {self.user_id} -> {self.badge_id}>"


class Challenge(db.Model):
    """Screen time challenges that users can create and participate in."""
    
    __tablename__ = "challenges"
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Challenge details
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    # Creator of the challenge
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    
    # Challenge criteria
    target_app = db.Column(db.String(120), nullable=False)  # '__TOTAL__' for overall, or specific app name
    target_minutes = db.Column(db.Integer, nullable=False)  # Daily target to stay under
    
    # Time period
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    
    # Challenge status: 'upcoming', 'active', 'completed', 'deleted'
    status = db.Column(db.String(20), default='upcoming', nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=current_time_utc)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    owner = db.relationship("User", backref="owned_challenges")
    participants = db.relationship("ChallengeParticipant", back_populates="challenge", cascade="all, delete-orphan")
    
    def to_dict(self) -> dict:
        """Serialize challenge for API responses."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "owner_id": self.owner_id,
            "target_app": self.target_app,
            "target_minutes": self.target_minutes,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }
    
    def __repr__(self):
        return f"<Challenge {self.name}: {self.status}>"


class ChallengeParticipant(db.Model):
    """Junction table tracking users participating in challenges with their stats."""
    
    __tablename__ = "challenge_participants"
    
    id = db.Column(db.Integer, primary_key=True)
    challenge_id = db.Column(db.Integer, db.ForeignKey("challenges.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    
    # Participation tracking
    joined_at = db.Column(db.DateTime, default=current_time_utc)
    
    # Daily performance tracking (cumulative stats for profile display)
    days_passed = db.Column(db.Integer, default=0)  # Days where total screen time was at or under target (only counts logged days)
    days_failed = db.Column(db.Integer, default=0)  # Total days exceeded target (only counts logged days)
    
    # Overall performance (calculated from screen time logs)
    total_screen_time_minutes = db.Column(db.Integer, default=0)  # Sum of screen time for all logged days
    days_logged = db.Column(db.Integer, default=0)  # Number of days with data (missing days ignored)
    
    # Final results when challenge completes
    final_rank = db.Column(db.Integer, nullable=True)  # 1 = winner (lowest total), 2 = second place, etc.
    is_winner = db.Column(db.Boolean, default=False)  # True only for whoever has lowest total screen time
    challenge_completed = db.Column(db.Boolean, default=False)  # True for everyone who joined AND logged at least once
    
    # Relationships
    challenge = db.relationship("Challenge", back_populates="participants")
    user = db.relationship("User", backref="challenge_participations")
    
    # Ensure a user can only join each challenge once
    __table_args__ = (db.UniqueConstraint('challenge_id', 'user_id', name='uq_challenge_participant'),)
    
    def to_dict(self) -> dict:
        """Serialize participant data for API responses."""
        return {
            "id": self.id,
            "challenge_id": self.challenge_id,
            "user_id": self.user_id,
            "joined_at": self.joined_at.isoformat() if self.joined_at else None,
            "days_passed": self.days_passed,
            "days_failed": self.days_failed,
            "total_screen_time_minutes": self.total_screen_time_minutes,
            "days_logged": self.days_logged,
            "final_rank": self.final_rank,
            "is_winner": self.is_winner,
            "challenge_completed": self.challenge_completed,
        }
    
    def __repr__(self):
        return f"<ChallengeParticipant user={self.user_id} challenge={self.challenge_id}>"
