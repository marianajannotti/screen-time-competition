"""Service layer for streak calculation operations."""

from datetime import date
from typing import Dict, List

from ..models import Goal


class StreakService:
    """Service class for streak calculation logic."""

    @staticmethod
    def calculate_streak(
        user_id: int,
        month_days: List[date],
        day_minutes: Dict[date, int]
    ) -> int:
        """Calculate the longest streak of days meeting daily goal.

        If user has a daily goal set, streak counts consecutive days
        where screen time was logged AND under/at the goal.
        
        If no goal is set, streak counts consecutive days with any logs.

        Args:
            user_id: The user's ID.
            month_days: List of days in the month (in order).
            day_minutes: Dict mapping day to total minutes logged.

        Returns:
            Longest streak count for the month.
        """
        # Get user's daily goal
        goal = Goal.query.filter_by(
            user_id=user_id,
            goal_type="daily"
        ).first()

        if not goal:
            # No goal set - streak is count of consecutive days with logs
            return StreakService._calculate_streak_without_goal(
                month_days, day_minutes
            )

        # With goal: count consecutive days meeting goal
        return StreakService._calculate_streak_with_goal(
            month_days, day_minutes, goal.target_minutes
        )

    @staticmethod
    def _calculate_streak_without_goal(
        month_days: List[date],
        day_minutes: Dict[date, int]
    ) -> int:
        """Calculate streak as consecutive days with any screen time logged.

        Args:
            month_days: List of days in the month (in chronological order).
            day_minutes: Dict mapping day to total minutes logged.

        Returns:
            Longest streak count.
        """
        max_streak = 0
        current_streak = 0

        for day in month_days:
            if day in day_minutes and day_minutes[day] > 0:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 0

        return max_streak

    @staticmethod
    def _calculate_streak_with_goal(
        month_days: List[date],
        day_minutes: Dict[date, int],
        target_minutes: int
    ) -> int:
        """Calculate streak as consecutive days meeting daily goal.

        A day counts toward the streak if:
        - Screen time was logged (minutes > 0)
        - Total minutes is at or under the target goal

        Args:
            month_days: List of days in the month (in chronological order).
            day_minutes: Dict mapping day to total minutes logged.
            target_minutes: Daily goal target in minutes.

        Returns:
            Longest streak count.
        """
        max_streak = 0
        current_streak = 0

        for day in month_days:
            minutes = day_minutes.get(day, 0)
            # Met goal if logged and under/at target
            if minutes > 0 and minutes <= target_minutes:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 0

        return max_streak
