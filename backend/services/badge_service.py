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
        """Award a badge to a user if they haven't earned it yet.
        
        Args:
            user_id: The user's ID
            badge_name: Name of the badge to award
            
        Returns:
            Tuple of (success: bool, message: str)
            
        Raises:
            ValidationError: If user or badge not found
        """
        from ..models import User
        from ..services.screen_time_service import ValidationError
        
        # Check if user exists
        user = User.query.get(user_id)
        if not user:
            raise ValidationError(f"User not found")
        
        # Check if badge exists
        badge = Badge.query.filter_by(name=badge_name).first()
        if not badge:
            raise ValidationError(f"Badge '{badge_name}' not found")
        
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
    def revoke_badge(user_id: int, badge_name: str):
        """Revoke a badge from a user.
        
        Args:
            user_id: The user's ID
            badge_name: Name of the badge to revoke
            
        Returns:
            bool: True if badge was revoked, False if user didn't have the badge
            
        Raises:
            ValidationError: If user or badge not found
        """
        from ..models import User
        from ..services.screen_time_service import ValidationError
        
        # Check if user exists
        user = User.query.get(user_id)
        if not user:
            raise ValidationError(f"User not found")
        
        # Check if badge exists
        badge = Badge.query.filter_by(name=badge_name).first()
        if not badge:
            raise ValidationError(f"Badge '{badge_name}' not found")
        
        # Find the user badge
        user_badge = UserBadge.query.filter_by(
            user_id=user_id,
            badge_id=badge.id
        ).first()
        
        if not user_badge:
            return False
        
        db.session.delete(user_badge)
        db.session.commit()
        
        return True
    
    @staticmethod
    def get_badge_progress(user_id: int):
        """Get progress toward earning badges for a user.
        
        Args:
            user_id: The user's ID
            
        Returns:
            dict: Badge progress information with earned and available badges
        """
        from ..models import User
        
        user = User.query.get(user_id)
        if not user:
            return {"earned": [], "available": []}
        
        # Get all badges the user has earned
        user_badges = BadgeService.get_user_badges(user_id)
        earned_badge_ids = [ub.badge_id for ub in user_badges]
        
        # Get all available badges
        all_badges = Badge.query.all()
        
        earned = []
        available = []
        
        for badge in all_badges:
            badge_dict = badge.to_dict()
            if badge.id in earned_badge_ids:
                # Find the earned_at timestamp
                user_badge = next((ub for ub in user_badges if ub.badge_id == badge.id), None)
                if user_badge:
                    badge_dict['earned_at'] = user_badge.earned_at.isoformat() if user_badge.earned_at else None
                earned.append(badge_dict)
            else:
                # Add progress information (placeholder - would need actual logic)
                badge_dict['progress'] = 0
                available.append(badge_dict)
        
        total_count = len(earned) + len(available)
        percentage = (len(earned) / total_count * 100) if total_count > 0 else 0
        
        return {
            "earned": earned,
            "available": available,
            "earned_count": len(earned),
            "available_count": len(available),
            "total_count": total_count,
            "percentage": round(percentage, 2)
        }
    
    @staticmethod
    def get_available_badges(badge_type=None):
        """Get all available badges, optionally filtered by type.
        
        Args:
            badge_type: Optional badge type to filter by (streak, reduction, social, etc.)
            
        Returns:
            list: List of Badge objects
        """
        query = Badge.query
        
        if badge_type:
            query = query.filter_by(badge_type=badge_type)
        
        return query.all()
    
    @staticmethod
    def get_badge_statistics():
        """Get statistics about badge distribution across all users.
        
        Returns:
            dict: Statistics including total badges, most earned badge, etc.
        """
        from sqlalchemy import func
        
        total_badges = Badge.query.count()
        total_awards = UserBadge.query.count()
        
        # Find most commonly earned badge
        most_earned = (
            db.session.query(
                Badge.name,
                func.count(UserBadge.id).label('count')
            )
            .join(UserBadge, Badge.id == UserBadge.badge_id)
            .group_by(Badge.id, Badge.name)
            .order_by(func.count(UserBadge.id).desc())
            .first()
        )
        
        # Find rarest badge
        rarest = (
            db.session.query(
                Badge.name,
                func.count(UserBadge.id).label('count')
            )
            .outerjoin(UserBadge, Badge.id == UserBadge.badge_id)
            .group_by(Badge.id, Badge.name)
            .order_by(func.count(UserBadge.id).asc())
            .first()
        )
        
        return {
            "total_badges": total_badges,
            "total_awards": total_awards,
            "most_earned": {
                "name": most_earned[0] if most_earned else None,
                "count": most_earned[1] if most_earned else 0
            },
            "rarest": {
                "name": rarest[0] if rarest else None,
                "count": rarest[1] if rarest else 0
            }
        }
    
    @staticmethod
    def get_badge_leaderboard(limit=10):
        """Get users ranked by number of badges earned.
        
        Args:
            limit: Maximum number of users to return
            
        Returns:
            list: List of users with badge counts, ordered by badge count descending
        """
        from ..models import User
        from sqlalchemy import func
        
        leaderboard = (
            db.session.query(
                User.id,
                User.username,
                func.count(UserBadge.id).label('badge_count')
            )
            .outerjoin(UserBadge, User.id == UserBadge.user_id)
            .group_by(User.id, User.username)
            .order_by(func.count(UserBadge.id).desc())
            .limit(limit)
            .all()
        )
        
        return [
            {
                "user_id": user_id,
                "username": username,
                "badge_count": badge_count
            }
            for user_id, username, badge_count in leaderboard
        ]

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
