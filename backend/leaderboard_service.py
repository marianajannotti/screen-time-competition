"""Service layer for leaderboard operations."""

from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple

from .models import User, ScreenTimeLog
from .streak_service import StreakService


class LeaderboardService:
    """Service class for leaderboard business logic."""

    @staticmethod
    def get_month_range(
        reference_date: Optional[date] = None
    ) -> Tuple[date, date, List[date]]:
        """Get the start, end, and all days of the current month.

        Args:
            reference_date: Date to use for month calculation.
                           Defaults to today. If in the future, returns
                           empty days list.

        Returns:
            Tuple of (start_date, end_date, list_of_days)
        """
        if reference_date is None:
            reference_date = date.today()

        year = reference_date.year
        month = reference_date.month

        # First day of month
        start = date(year, month, 1)

        # Last day of month
        if month == 12:
            end = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end = date(year, month + 1, 1) - timedelta(days=1)

        # All days in the month up to today
        today = date.today()
        actual_end = min(end, today)

        days = []
        current = start
        while current <= actual_end:
            days.append(current)
            current += timedelta(days=1)

        return start, end, days

    @staticmethod
    def compute_user_monthly_stats(
        user_id: int,
        reference_date: Optional[date] = None
    ) -> Dict:
        """Compute monthly statistics for a user.

        Args:
            user_id: The user's ID.
            reference_date: Date to use for month calculation.

        Returns:
            Dict with avg_per_day, total_minutes, days_logged, streak
        """
        start, end, days = LeaderboardService.get_month_range(reference_date)

        # Get all screen time logs for this user in the month
        logs = ScreenTimeLog.query.filter(
            ScreenTimeLog.user_id == user_id,
            ScreenTimeLog.date >= start,
            ScreenTimeLog.date <= end
        ).all()

        # Group by date and sum minutes (using Total or sum of all apps)
        daily_totals = {}
        for log in logs:
            day = log.date
            if day not in daily_totals:
                daily_totals[day] = {}

            app = log.app_name
            daily_totals[day][app] = (
                daily_totals[day].get(app, 0) + log.screen_time_minutes
            )

        # Calculate total for each day
        day_minutes = {}
        for day, apps in daily_totals.items():
            # Use "Total" if available, otherwise sum all apps
            if "Total" in apps:
                day_minutes[day] = apps["Total"]
            else:
                day_minutes[day] = sum(apps.values())

        # Filter out days with 0 minutes
        days_with_data = {d: m for d, m in day_minutes.items() if m > 0}

        total_minutes = sum(days_with_data.values())
        days_logged = len(days_with_data)
        avg_per_day = total_minutes / days_logged if days_logged > 0 else None

        # Calculate streak (consecutive days meeting daily goal)
        streak = StreakService.calculate_streak(
            user_id, days, days_with_data
        )

        return {
            "avg_per_day": round(avg_per_day, 1) if avg_per_day else None,
            "total_minutes": total_minutes,
            "days_logged": days_logged,
            "streak": streak,
        }

    @staticmethod
    def get_global_leaderboard(limit: int = 50) -> List[Dict]:
        """Get the global leaderboard ranked by highest streak.

        Tiebreaker: Lower average screen time wins.

        Args:
            limit: Maximum number of users to return.

        Returns:
            List of user dicts with stats, ordered by rank.
        """
        # Get all users
        # Note: Computes stats for ALL users before limiting.
        # Consider pagination/caching for large user bases.
        users = User.query.all()

        # Compute stats for each user
        user_stats = []
        for user in users:
            stats = LeaderboardService.compute_user_monthly_stats(user.id)
            user_stats.append({
                "user_id": user.id,
                "username": user.username,
                "avg_per_day": stats["avg_per_day"],
                "total_minutes": stats["total_minutes"],
                "days_logged": stats["days_logged"],
                "streak": stats["streak"],
            })

        # Sort by:
        # 1. Streak descending (higher streak = better)
        # 2. Avg screen time ascending (lower = better) as tiebreaker
        # Users with no data go to the bottom
        def sort_key(u):
            streak = u["streak"] or 0
            avg = u["avg_per_day"]

            if avg is None:
                # No data at all: sort to bottom, then by username
                return (1, 0, 0, u["username"])
            # The case where streak > 0 and avg is None cannot occur because
            # streak is only > 0 when days_logged > 0, which guarantees avg_per_day is calculated.

            # Normal case: sort by streak desc, then avg asc
            return (0, -streak, avg, u["username"])

        user_stats.sort(key=sort_key)

        # Add rank
        for i, u in enumerate(user_stats):
            u["rank"] = i + 1

        return user_stats[:limit]
