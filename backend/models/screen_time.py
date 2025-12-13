"""Screen time log and goal models."""

from ..database import db
from ..utils import current_time_utc


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
