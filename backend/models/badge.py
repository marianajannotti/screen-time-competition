"""Badge models for gamification system."""

from ..database import db
from ..utils import current_time_utc


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
