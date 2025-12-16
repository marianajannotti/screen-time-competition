"""Badge service for managing badges and user badge achievements."""

import logging
from ..database import db
from ..models import Badge, UserBadge
from ..utils.helpers import current_time_utc
from sqlalchemy.orm import joinedload

logger = logging.getLogger(__name__)

class BadgeService:
    """Service class for badge-related operations."""
    
    @staticmethod
    def get_all_badges():
        """Get all available badges."""
        return Badge.query.all()
    
    @staticmethod
    def get_user_badges(user_id: int):
        """Get all badges earned by a specific user with eager-loaded Badge relation."""
        user_badges = (
            db.session.query(UserBadge)
            .options(joinedload(UserBadge.badge))
            .filter(UserBadge.user_id == user_id)
            .all()
        )
        return user_badges
    
    @staticmethod
    def award_badge(user_id: int, badge_name: str):
        """Award a badge to a user if they haven't earned it yet."""
        # Check if badge exists
        badge = Badge.query.filter_by(name=badge_name).first()
        if not badge:
            return False, f"Badge '{badge_name}' not found"
        
        # Check if user already has this badge
        existing = UserBadge.query.filter_by(
            user_id=user_id, 
            badge_id=badge.id
        ).first()
        
        if existing:
            return False, f"User already has badge '{badge_name}'"
        
        # Award the badge
        user_badge = UserBadge(
            user_id=user_id,
            badge_id=badge.id,
            earned_at=current_time_utc()
        )
        
        db.session.add(user_badge)
        db.session.commit()
        
        return True, f"Badge '{badge_name}' awarded successfully"
    
    @staticmethod
    def initialize_badges():
        """Initialize the database with default badges if they don't exist."""
        default_badges = [
            # Streak & Consistency
            {'name': 'Fresh Start', 'desc': 'Complete your first day meeting your screen-time goal.', 'type': 'streak', 'icon': '🔥'},
            {'name': 'Weekend Warrior', 'desc': 'Hit your goal on a Saturday and Sunday.', 'type': 'streak', 'icon': '🔥'},
            {'name': '7-Day Focus', 'desc': '7 days in a row hitting daily goal.', 'type': 'streak', 'icon': '🔥'},
            {'name': 'Habit Builder', 'desc': '14-day streak.', 'type': 'streak', 'icon': '🔥'},
            {'name': 'Unstoppable', 'desc': '30-day streak.', 'type': 'streak', 'icon': '🔥'},
            {'name': 'Bounce Back', 'desc': 'Lose a streak, then start a new one the next day.', 'type': 'streak', 'icon': '🔥'},
            
            # Screen-Time Reduction
            {'name': 'Tiny Wins', 'desc': 'Reduce total time by 5% from your baseline week.', 'type': 'reduction', 'icon': '📉'},
            {'name': 'The Declutter', 'desc': 'Reduce total screen time by 10% from baseline.', 'type': 'reduction', 'icon': '📉'},
            {'name': 'Half-Life', 'desc': 'Reduce screen time by 50% from baseline.', 'type': 'reduction', 'icon': '📉'},
            {'name': 'One Hour Club', 'desc': 'Stay under 1h of social media in a day.', 'type': 'reduction', 'icon': '📉'},
            {'name': 'Digital Minimalist', 'desc': 'Average < 2 hours/day over a whole week.', 'type': 'reduction', 'icon': '📉'},
            
            # Social & Community
            {'name': 'Team Player', 'desc': 'Add your first friend.', 'type': 'social', 'icon': '👥'},
            {'name': 'The Connector', 'desc': 'Add 10 friends.', 'type': 'social', 'icon': '👥'},
            {'name': 'Challenge Accepted', 'desc': 'Join your first challenge.', 'type': 'social', 'icon': '👥'},
            {'name': 'Friendly Rival', 'desc': 'Participate in 5 challenges.', 'type': 'social', 'icon': '👥'},
            {'name': 'Community Champion', 'desc': 'Win a challenge among friends.', 'type': 'social', 'icon': '👥'},
            
            # Leaderboard
            {'name': 'Top 10%', 'desc': 'Be in top 10% of the leaderboard in a week.', 'type': 'leaderboard', 'icon': '🏆'},
            {'name': 'Top 3', 'desc': 'Finish as #1, #2, or #3 among friends.', 'type': 'leaderboard', 'icon': '🏆'},
            {'name': 'The Phantom', 'desc': 'Win a challenge with the lowest screen time without chatting.', 'type': 'leaderboard', 'icon': '🏆'},
            {'name': 'Comeback Kid', 'desc': 'Go from bottom half to top 3 in the next challenge.', 'type': 'leaderboard', 'icon': '🏆'},
            
            # Prestige / Long-Term
            {'name': 'Offline Legend', 'desc': 'Average < 2h/day for a full month.', 'type': 'prestige', 'icon': '⭐'},
            {'name': 'Master of Attention', 'desc': 'Maintain a 30-day goal streak and < 2h/day average.', 'type': 'prestige', 'icon': '⭐'},
            {'name': 'Life > Screen', 'desc': 'Complete a full 24h digital detox.', 'type': 'prestige', 'icon': '⭐'},
        ]
        
        # Only add badges that don't already exist
        for badge_data in default_badges:
            existing_badge = Badge.query.filter_by(name=badge_data['name']).first()
            if not existing_badge:
                badge = Badge(
                    name=badge_data['name'],
                    description=badge_data['desc'],
                    badge_type=badge_data['type'],
                    icon=badge_data['icon']
                )
                db.session.add(badge)
        
        db.session.commit()
        logger.info("Initialized %d badges in database", len(default_badges))
