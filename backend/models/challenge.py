"""Challenge models for screen time competitions."""

from ..database import db
from ..utils import current_time_utc


class Challenge(db.Model):
    """Screen time challenges that users can create and participate in."""
    
    __tablename__ = "challenges"
    
    challenge_id = db.Column(db.Integer, primary_key=True)
    
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
            "challenge_id": self.challenge_id,
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
    
    participant_id = db.Column(db.Integer, primary_key=True)
    challenge_id = db.Column(db.Integer, db.ForeignKey("challenges.challenge_id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    
    # Invitation status: 'pending', 'accepted', 'declined'
    invitation_status = db.Column(db.String(20), default='pending', nullable=False)
    
    # Participation tracking
    joined_at = db.Column(db.DateTime, default=current_time_utc)
    
    # Daily performance tracking (cumulative stats for profile display)
    days_passed = db.Column(db.Integer, default=0)  # Days where total screen time was at or under target (only counts logged days)
    days_failed = db.Column(db.Integer, default=0)  # Total days exceeded target (only counts logged days)
    
    # Today's status (for real-time UI updates)
    today_minutes = db.Column(db.Integer, default=0)  # Minutes logged today for this challenge
    today_passed = db.Column(db.Boolean, default=None, nullable=True)  # None = no data, True = passed today, False = failed today
    
    # Overall performance (calculated from screen time logs)
    total_screen_time_minutes = db.Column(db.Integer, default=0)  # Sum of screen time for all logged days
    days_logged = db.Column(db.Integer, default=0)  # Number of days with data (missing days ignored)
    
    # Final results when challenge completes
    final_rank = db.Column(db.Integer, nullable=True)  # 1 = winner (lowest total), 2 = second place, etc.
    is_winner = db.Column(db.Boolean, default=False)  # True only for whoever has lowest total screen time
    challenge_completed = db.Column(db.Boolean, default=False)  # True for participants who joined AND logged at least once; remains False for those who never logged any screen time during the challenge
    
    # Relationships
    challenge = db.relationship("Challenge", back_populates="participants")
    user = db.relationship("User", backref="challenge_participations")
    
    # Ensure a user can only join each challenge once
    __table_args__ = (db.UniqueConstraint('challenge_id', 'user_id', name='uq_challenge_participant'),)
    
    def to_dict(self) -> dict:
        """Serialize participant data for API responses."""
        return {
            "participant_id": self.participant_id,
            "challenge_id": self.challenge_id,
            "user_id": self.user_id,
            "invitation_status": self.invitation_status,
            "joined_at": self.joined_at.isoformat() if self.joined_at else None,
            "days_passed": self.days_passed,
            "days_failed": self.days_failed,
            "today_minutes": self.today_minutes,
            "today_passed": self.today_passed,
            "total_screen_time_minutes": self.total_screen_time_minutes,
            "days_logged": self.days_logged,
            "final_rank": self.final_rank,
            "is_winner": self.is_winner,
            "challenge_completed": self.challenge_completed,
        }
    
    def __repr__(self):
        return f"<ChallengeParticipant user={self.user_id} challenge={self.challenge_id}>"
