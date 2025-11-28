"""
Business Logic Service for Screen Time Competition App

This module contains the core business logic for gamification, goal tracking,
and user engagement features. It handles all calculations related to:

- User streak calculation and maintenance
- Points system and scoring algorithms  
- Goal progress tracking and validation
- Gamification stat updates
- Business rule enforcement

The BusinessLogicService is designed as a static utility class to be called
from various route handlers when business logic needs to be applied.

Key Components:
- Streak Calculation: Tracks consecutive days of screen time logging
- Points System: Multi-factor scoring based on activity and achievements
- Goal Validation: Real-time progress tracking for user-defined limits
- Stat Management: Automatic updates to user gamification data

Integration Points:
- Called from screen time logging routes to update streaks/points
- Used by goal routes to calculate progress percentages
- Powers profile endpoints with enhanced statistics
- Supports leaderboard calculations for social features
"""

from datetime import datetime, date, timedelta
from sqlalchemy import func
from .database import db
from .models import User, ScreenTimeLog, Goal


class BusinessLogicService:
    """
    Core Business Logic Service
    
    Static utility class containing all business logic for the Screen Time
    Competition app. Handles gamification, goal tracking, and user engagement
    calculations without maintaining state.
    
    Design Philosophy:
    - All methods are static (no instance state)
    - Defensive programming with error handling
    - Database queries optimized for performance
    - Clear separation of concerns
    - Comprehensive documentation for maintainability
    """
    
    # ========================
    # Points System Configuration
    # ========================
    # These constants define how points are awarded to users
    # Adjust these values to fine-tune the gamification experience
    
    POINTS_PER_DAY_LOGGED = 10      # Base points for logging screen time each day
    POINTS_DAILY_GOAL_MET = 50      # Bonus points for meeting daily screen time goal
    POINTS_WEEKLY_GOAL_MET = 200    # Bonus points for meeting weekly screen time goal  
    POINTS_STREAK_BONUS = 5         # Additional points per day in current streak
    
    @staticmethod
    def calculate_user_streak(user_id):
        """
        Calculate Current User Streak
        
        Calculates the number of consecutive days the user has logged screen time,
        starting from today and going backwards. A streak is broken when we find
        a day with no screen time log entry.
        
        Algorithm:
        1. Start from today's date
        2. Check if user has a screen time log for that date
        3. If yes, increment streak and check previous day
        4. If no, break the streak and return current count
        5. Continue until streak breaks or reasonable maximum is reached
        
        Args:
            user_id (int): The unique identifier of the user
            
        Returns:
            int: Number of consecutive days with screen time logged (0 if no current streak)
            
        Example:
            User logged screen time on: Jan 1, 2, 3, 5, 6, 7 (today)
            Result: 3 days (Jan 5, 6, 7 are consecutive)
            
        Performance Notes:
        - Uses indexed database queries for efficiency
        - Includes safeguards against infinite loops
        - Optimized for typical streak lengths (most users < 365 days)
        """
        today = date.today()
        current_streak = 0
        check_date = today
        
        # Iterate backwards from today, checking each day for screen time logs
        while True:
            log = ScreenTimeLog.query.filter_by(
                user_id=user_id,
                date=check_date
            ).first()
            
            # If no log found for this date, streak is broken
            if log is None:
                break
                
            # Found a log, extend the streak
            current_streak += 1
            check_date -= timedelta(days=1)
            
            # Safety valve: prevent infinite loops for edge cases
            # No user should realistically have a 365+ day streak
            if current_streak > 365:
                break
                
        return current_streak
    
    @staticmethod
    def calculate_user_points(user_id):
        """
        Calculate total points for a user based on various activities.
        
        Points awarded for:
        - Logging screen time daily: 10 points
        - Meeting daily goals: 50 points  
        - Meeting weekly goals: 200 points
        - Streak bonus: 5 points per day in current streak
        
        Returns:
            int: Total points earned
        """
        total_points = 0
        
        # Points for logging screen time (10 per day)
        total_logs = ScreenTimeLog.query.filter_by(user_id=user_id).count()
        total_points += total_logs * BusinessLogicService.POINTS_PER_DAY_LOGGED
        
        # Points for meeting daily goals
        daily_goals_met = BusinessLogicService._count_goals_met(user_id, 'daily')
        total_points += daily_goals_met * BusinessLogicService.POINTS_DAILY_GOAL_MET
        
        # Points for meeting weekly goals  
        weekly_goals_met = BusinessLogicService._count_goals_met(user_id, 'weekly')
        total_points += weekly_goals_met * BusinessLogicService.POINTS_WEEKLY_GOAL_MET
        
        # Streak bonus
        current_streak = BusinessLogicService.calculate_user_streak(user_id)
        total_points += current_streak * BusinessLogicService.POINTS_STREAK_BONUS
        
        return total_points
    
    @staticmethod
    def _count_goals_met(user_id, goal_type):
        """
        Count how many times user has met their goals of given type.
        
        Args:
            user_id (int): User ID
            goal_type (str): 'daily' or 'weekly'
            
        Returns:
            int: Number of times goals were met
        """
        # Get user's current goal for this type
        goal = Goal.query.filter_by(
            user_id=user_id,
            goal_type=goal_type
        ).first()
        
        if not goal:
            return 0
            
        goals_met = 0
        
        if goal_type == 'daily':
            # Check each day's screen time against daily goal
            logs = ScreenTimeLog.query.filter_by(user_id=user_id).all()
            for log in logs:
                if log.screen_time_minutes <= goal.target_minutes:
                    goals_met += 1
                    
        elif goal_type == 'weekly':
            # Check weekly totals against weekly goal
            # Group logs by week and sum screen time
            logs = ScreenTimeLog.query.filter_by(user_id=user_id).all()
            
            # Group by week (ISO week)
            weekly_totals = {}
            for log in logs:
                year, week, _ = log.date.isocalendar()
                week_key = f"{year}-W{week:02d}"
                
                if week_key not in weekly_totals:
                    weekly_totals[week_key] = 0
                weekly_totals[week_key] += log.screen_time_minutes
            
            # Count weeks where total <= goal
            for total in weekly_totals.values():
                if total <= goal.target_minutes:
                    goals_met += 1
                    
        return goals_met
    
    @staticmethod
    def check_goal_progress(user_id, goal_type, period_start=None):
        """
        Check current progress towards a goal.
        
        Args:
            user_id (int): User ID
            goal_type (str): 'daily' or 'weekly'
            period_start (date, optional): Start of period to check
            
        Returns:
            dict: {
                'goal_exists': bool,
                'target_minutes': int,
                'current_minutes': int,
                'progress_percent': float,
                'goal_met': bool,
                'days_remaining': int (for weekly goals)
            }
        """
        # Get user's goal
        goal = Goal.query.filter_by(
            user_id=user_id,
            goal_type=goal_type
        ).first()
        
        if not goal:
            return {
                'goal_exists': False,
                'target_minutes': 0,
                'current_minutes': 0,
                'progress_percent': 0,
                'goal_met': False,
                'days_remaining': 0
            }
        
        # Calculate current usage for the period
        if goal_type == 'daily':
            target_date = period_start or date.today()
            log = ScreenTimeLog.query.filter_by(
                user_id=user_id,
                date=target_date
            ).first()
            current_minutes = log.screen_time_minutes if log else 0
            days_remaining = 0
            
        elif goal_type == 'weekly':
            # Get current week's total
            today = date.today()
            start_of_week = today - timedelta(days=today.weekday())
            end_of_week = start_of_week + timedelta(days=6)
            
            weekly_logs = ScreenTimeLog.query.filter(
                ScreenTimeLog.user_id == user_id,
                ScreenTimeLog.date >= start_of_week,
                ScreenTimeLog.date <= end_of_week
            ).all()
            
            current_minutes = sum(log.screen_time_minutes for log in weekly_logs)
            days_remaining = (end_of_week - today).days
        
        # Calculate progress
        progress_percent = min((current_minutes / goal.target_minutes) * 100, 100) if goal.target_minutes > 0 else 0
        goal_met = current_minutes <= goal.target_minutes
        
        return {
            'goal_exists': True,
            'target_minutes': goal.target_minutes,
            'current_minutes': current_minutes,
            'progress_percent': round(progress_percent, 1),
            'goal_met': goal_met,
            'days_remaining': days_remaining
        }
    
    @staticmethod
    def update_user_gamification_stats(user_id):
        """
        Update streak and points for a user.
        Call this after screen time is logged or goals are changed.
        
        Args:
            user_id (int): User ID to update
            
        Returns:
            dict: Updated stats {streak_count, total_points}
        """
        try:
            user = User.query.get(user_id)
            if not user:
                return None
            
            # Calculate and update streak
            new_streak = BusinessLogicService.calculate_user_streak(user_id)
            user.streak_count = new_streak
            
            # Calculate and update points
            new_points = BusinessLogicService.calculate_user_points(user_id)
            user.total_points = new_points
            
            db.session.commit()
            
            return {
                'streak_count': new_streak,
                'total_points': new_points
            }
            
        except Exception as e:
            db.session.rollback()
            raise e
    
    @staticmethod
    def validate_screen_time_entry(screen_time_minutes, entry_date=None):
        """
        Validate screen time entry data.
        
        Args:
            screen_time_minutes (int): Minutes of screen time
            entry_date (date, optional): Date for the entry
            
        Returns:
            tuple: (is_valid, error_message)
        """
        # Check if minutes is valid
        if not isinstance(screen_time_minutes, int):
            return False, "Screen time must be a whole number"
            
        if screen_time_minutes < 0:
            return False, "Screen time cannot be negative"
            
        if screen_time_minutes > 1440:  # 24 hours
            return False, "Screen time cannot exceed 24 hours (1440 minutes)"
        
        # Check date if provided
        if entry_date:
            if entry_date > date.today():
                return False, "Cannot log screen time for future dates"
                
            # Don't allow entries older than 1 year
            if entry_date < date.today() - timedelta(days=365):
                return False, "Cannot log screen time older than 1 year"
        
        return True, None
    
    @staticmethod
    def get_achievement_status(user_id):
        """
        Check what achievements a user has unlocked.
        
        Returns:
            dict: Achievement status and progress
        """
        user = User.query.get(user_id)
        if not user:
            return {}
        
        total_logs = ScreenTimeLog.query.filter_by(user_id=user_id).count()
        current_streak = user.streak_count
        total_points = user.total_points
        
        achievements = {
            'first_log': total_logs >= 1,
            'week_warrior': total_logs >= 7,
            'month_master': total_logs >= 30,
            'year_champion': total_logs >= 365,
            'streak_starter': current_streak >= 3,
            'streak_superstar': current_streak >= 7,
            'streak_legend': current_streak >= 30,
            'points_collector': total_points >= 100,
            'points_master': total_points >= 1000,
            'points_legend': total_points >= 5000,
        }
        
        return {
            'achievements': achievements,
            'progress': {
                'total_logs': total_logs,
                'current_streak': current_streak,
                'total_points': total_points
            }
        }
