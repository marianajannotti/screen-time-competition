"""Friendship model for social features."""

from ..database import db
from ..utils import current_time_utc


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
