"""Badge achievement logic for automatically awarding badges based on user activities."""

import logging
from datetime import timedelta, date
from sqlalchemy import func, and_
from ..models import User, ScreenTimeLog, Friendship  
from .badge_service import BadgeService
from .screen_time_service import ScreenTimeService
from .email_service import send_badge_notification

logger = logging.getLogger(__name__)


class BadgeAchievementService:
    """Logic for determining and awarding badges based on user achievements."""
    
    @staticmethod
    def check_and_award_badges(user_id: int):
        """Check all badge conditions and award applicable badges to a user atomically.
        
        Args:
            user_id (int): ID of the user to check badges for
            
        Returns:
            list: List of badge names that were newly awarded
        """
        if user_id <= 0:
            return []
            
        user = User.query.get(user_id)
        if not user:
            return []
        
        awarded_badges = []
        
        # Check all badge types (transaction is already managed by the caller)
        try:
            awarded_badges.extend(BadgeAchievementService._check_streak_badges(user))
            awarded_badges.extend(BadgeAchievementService._check_reduction_badges(user))
            awarded_badges.extend(BadgeAchievementService._check_social_badges(user))
            awarded_badges.extend(BadgeAchievementService._check_leaderboard_badges(user))
            awarded_badges.extend(BadgeAchievementService._check_prestige_badges(user))
        except Exception as e:
            logger.error(f"Error checking badges for user {user_id}: {str(e)}")
            return []
        
        # Send email notifications for newly awarded badges
        for badge_name in awarded_badges:
            try:
                send_badge_notification(user.email, user.username, badge_name)
            except Exception as e:
                # Log the error but don't fail the badge awarding
                logger.warning(
                    f"Failed to send badge email for {badge_name} "
                    f"to {user.email}: {str(e)}"
                )
        
        return awarded_badges
    
    @staticmethod
    def _check_streak_badges(user: User):
        """Check and award streak-related badges."""
        awarded = []
        streak_count = user.streak_count or 0
        
        # Define streak badge thresholds
        streak_badges = [
            ('Fresh Start', 1),
            ('7-Day Focus', 7),
            ('Habit Builder', 14),
            ('Unstoppable', 30),
        ]
        
        for badge_name, required_streak in streak_badges:
            if streak_count >= required_streak:
                success, _ = BadgeService.award_badge(user.id, badge_name)
                if success:
                    awarded.append(badge_name)
        
        # Weekend Warrior - check if user met goals on both Saturday and Sunday
        if ScreenTimeService.check_weekend_achievement(user.id, threshold_minutes=180):
            success, _ = BadgeService.award_badge(user.id, 'Weekend Warrior')
            if success:
                awarded.append('Weekend Warrior')
        
        return awarded
    
    @staticmethod
    def _check_reduction_badges(user: User):
        """Check and award screen time reduction badges."""
        awarded = []
        
        # Get user's baseline week (first week of data)
        baseline_avg = ScreenTimeService.get_baseline_average(user.id)
        if baseline_avg is None or baseline_avg <= 0:
            return awarded
        
        # Get recent week average
        recent_avg = ScreenTimeService.get_recent_week_average(user.id)
        if recent_avg is None:
            return awarded
        
        # Calculate reduction percentage
        reduction_percent = ((baseline_avg - recent_avg) / baseline_avg) * 100
        
        # Check reduction badges
        if reduction_percent >= 5:
            success, _ = BadgeService.award_badge(user.id, 'Tiny Wins')
            if success:
                awarded.append('Tiny Wins')
        
        if reduction_percent >= 10:
            success, _ = BadgeService.award_badge(user.id, 'The Declutter')
            if success:
                awarded.append('The Declutter')
        
        if reduction_percent >= 50:
            success, _ = BadgeService.award_badge(user.id, 'Half-Life')
            if success:
                awarded.append('Half-Life')
        
        # One Hour Club - check if user stayed under 1h social media in a day
        if ScreenTimeService.check_low_usage_day(user.id, max_minutes=60):
            success, _ = BadgeService.award_badge(user.id, 'One Hour Club')
            if success:
                awarded.append('One Hour Club')
        
        # Digital Minimalist - average < 2h/day for a week
        if recent_avg < 120:  # 2 hours = 120 minutes
            success, _ = BadgeService.award_badge(user.id, 'Digital Minimalist')
            if success:
                awarded.append('Digital Minimalist')
        
        return awarded
    
    @staticmethod
    def _check_social_badges(user: User):
        """Check and award social interaction badges."""
        awarded = []
        
        # Count friendships
        friend_count = Friendship.query.filter(
            and_(
                Friendship.user_id == user.id,
                Friendship.status == 'accepted'
            )
        ).count()
        
        # Team Player - first friend
        if friend_count >= 1:
            success, _ = BadgeService.award_badge(user.id, 'Team Player')
            if success:
                awarded.append('Team Player')
        
        # The Connector - 10 friends
        if friend_count >= 10:
            success, _ = BadgeService.award_badge(user.id, 'The Connector')
            if success:
                awarded.append('The Connector')
        
        return awarded
    
    @staticmethod
    def _check_leaderboard_badges(user: User):
        """Check and award leaderboard-related badges."""
        awarded = []
        
        # Get user's rank for the current week
        rank = ScreenTimeService.get_user_weekly_rank(user.id)
        
        if rank is not None and rank > 0:
            if rank <= 3:
                success, _ = BadgeService.award_badge(user.id, 'Top 3')
                if success:
                    awarded.append('Top 3')
            
            # Top 10% - need to calculate based on total user count
            total_users = User.query.count()
            if total_users > 0 and rank <= max(1, int(total_users * 0.1)):
                success, _ = BadgeService.award_badge(user.id, 'Top 10%')
                if success:
                    awarded.append('Top 10%')
        
        return awarded
    
    @staticmethod
    def _check_prestige_badges(user: User):
        """Check and award prestige/long-term badges."""
        awarded = []
        
        # Offline Legend - average < 2h/day for a full month
        monthly_avg = ScreenTimeService.get_monthly_average(user.id)
        if monthly_avg is not None and monthly_avg < 120:  # 2 hours
            success, _ = BadgeService.award_badge(user.id, 'Offline Legend')
            if success:
                awarded.append('Offline Legend')
        
        # Master of Attention - 30-day streak + < 2h/day average
        if user.streak_count >= 30 and monthly_avg is not None and monthly_avg < 120:
            success, _ = BadgeService.award_badge(user.id, 'Master of Attention')
            if success:
                awarded.append('Master of Attention')
        
        return awarded
