"""Unit tests for the StreakService.

This module contains test cases for the StreakService class,
covering streak calculation with and without daily goals.
"""

import unittest
from datetime import date

from backend import create_app
from backend.database import db
from backend.models import User, Goal
from backend.streak_service import StreakService


class StreakServiceTestCase(unittest.TestCase):
    """Base test case for StreakService streak calculations.

    Provides common setup and teardown for all streak service tests.
    """

    def setUp(self):
        """Create app context, database, and test user.

        Returns:
            None
        """
        self.app = create_app("testing")
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Create test user
        self.user = User(
            username="streakuser",
            email="streak@test.com",
            password_hash="x"
        )
        db.session.add(self.user)
        db.session.commit()

    def tearDown(self):
        """Clean up database and app context.

        Returns:
            None
        """
        db.session.remove()
        db.drop_all()
        db.engine.dispose()
        self.app_context.pop()


class TestStreakWithoutGoal(StreakServiceTestCase):
    """Test streak calculation when user has no goal set.

    Verifies that streaks are counted as consecutive days
    with any screen time logged.
    """

    def test_empty_days_returns_zero(self):
        """Verify that no screen time logged returns 0 streak.

        Returns:
            None
        """
        month_days = [date(2025, 12, 1), date(2025, 12, 2), date(2025, 12, 3)]
        day_minutes = {}

        streak = StreakService.calculate_streak(
            self.user.id, month_days, day_minutes
        )

        self.assertEqual(streak, 0)

    def test_single_day_logged(self):
        """Verify that one day logged returns streak of 1.

        Returns:
            None
        """
        month_days = [date(2025, 12, 1), date(2025, 12, 2), date(2025, 12, 3)]
        day_minutes = {date(2025, 12, 1): 120}

        streak = StreakService.calculate_streak(
            self.user.id, month_days, day_minutes
        )

        self.assertEqual(streak, 1)

    def test_consecutive_days_logged(self):
        """Verify that three consecutive days returns streak of 3.

        Returns:
            None
        """
        month_days = [date(2025, 12, 1), date(2025, 12, 2), date(2025, 12, 3)]
        day_minutes = {
            date(2025, 12, 1): 100,
            date(2025, 12, 2): 150,
            date(2025, 12, 3): 200,
        }

        streak = StreakService.calculate_streak(
            self.user.id, month_days, day_minutes
        )

        self.assertEqual(streak, 3)

    def test_broken_streak_returns_longest(self):
        """Verify that gap in days returns longest consecutive streak.

        Returns:
            None
        """
        month_days = [
            date(2025, 12, 1),
            date(2025, 12, 2),
            date(2025, 12, 3),
            date(2025, 12, 4),
            date(2025, 12, 5),
        ]
        # Days 1-2 logged, day 3 missing, days 4-5 logged
        day_minutes = {
            date(2025, 12, 1): 100,
            date(2025, 12, 2): 100,
            # gap on day 3
            date(2025, 12, 4): 100,
            date(2025, 12, 5): 100,
        }

        streak = StreakService.calculate_streak(
            self.user.id, month_days, day_minutes
        )

        self.assertEqual(streak, 2)

    def test_longer_second_streak_is_returned(self):
        """Verify that longest streak is returned even if it comes later.

        Returns:
            None
        """
        month_days = [
            date(2025, 12, 1),
            date(2025, 12, 2),
            date(2025, 12, 3),
            date(2025, 12, 4),
            date(2025, 12, 5),
            date(2025, 12, 6),
        ]
        # Day 1 logged, gap on day 2, days 3-6 logged (4-day streak)
        day_minutes = {
            date(2025, 12, 1): 100,
            # gap on day 2
            date(2025, 12, 3): 100,
            date(2025, 12, 4): 100,
            date(2025, 12, 5): 100,
            date(2025, 12, 6): 100,
        }

        streak = StreakService.calculate_streak(
            self.user.id, month_days, day_minutes
        )

        self.assertEqual(streak, 4)

    def test_zero_minutes_does_not_count(self):
        """Verify that days with 0 minutes do not count toward streak.

        Returns:
            None
        """
        month_days = [date(2025, 12, 1), date(2025, 12, 2), date(2025, 12, 3)]
        day_minutes = {
            date(2025, 12, 1): 100,
            date(2025, 12, 2): 0,  # logged but 0 minutes
            date(2025, 12, 3): 100,
        }

        streak = StreakService.calculate_streak(
            self.user.id, month_days, day_minutes
        )

        self.assertEqual(streak, 1)


class TestStreakWithGoal(StreakServiceTestCase):
    """Test streak calculation when user has a daily goal.

    Verifies that streaks only count consecutive days where
    screen time was logged AND under/at the goal target.
    """

    def setUp(self):
        """Create app context, user, and daily goal.

        Returns:
            None
        """
        super().setUp()
        # Set daily goal of 120 minutes (2 hours)
        self.goal = Goal(
            user_id=self.user.id,
            goal_type="daily",
            target_minutes=120
        )
        db.session.add(self.goal)
        db.session.commit()

    def test_all_days_under_goal(self):
        """Verify that all days meeting goal count toward streak.

        Returns:
            None
        """
        month_days = [date(2025, 12, 1), date(2025, 12, 2), date(2025, 12, 3)]
        day_minutes = {
            date(2025, 12, 1): 100,  # under goal
            date(2025, 12, 2): 120,  # exactly at goal
            date(2025, 12, 3): 90,   # under goal
        }

        streak = StreakService.calculate_streak(
            self.user.id, month_days, day_minutes
        )

        self.assertEqual(streak, 3)

    def test_exceeding_goal_breaks_streak(self):
        """Verify that day exceeding goal breaks the streak.

        Returns:
            None
        """
        month_days = [date(2025, 12, 1), date(2025, 12, 2), date(2025, 12, 3)]
        day_minutes = {
            date(2025, 12, 1): 100,  # under goal
            date(2025, 12, 2): 150,  # over goal - breaks streak
            date(2025, 12, 3): 90,   # under goal
        }

        streak = StreakService.calculate_streak(
            self.user.id, month_days, day_minutes
        )

        self.assertEqual(streak, 1)

    def test_exactly_at_goal_counts(self):
        """Verify that day exactly at goal target counts toward streak.

        Returns:
            None
        """
        month_days = [date(2025, 12, 1), date(2025, 12, 2)]
        day_minutes = {
            date(2025, 12, 1): 120,  # exactly at goal
            date(2025, 12, 2): 120,  # exactly at goal
        }

        streak = StreakService.calculate_streak(
            self.user.id, month_days, day_minutes
        )

        self.assertEqual(streak, 2)

    def test_no_logs_with_goal_returns_zero(self):
        """Verify that no screen time logged returns 0 even with goal.

        Returns:
            None
        """
        month_days = [date(2025, 12, 1), date(2025, 12, 2)]
        day_minutes = {}

        streak = StreakService.calculate_streak(
            self.user.id, month_days, day_minutes
        )

        self.assertEqual(streak, 0)

    def test_zero_minutes_does_not_count_with_goal(self):
        """Verify that days with 0 minutes do not count even if under goal.

        Returns:
            None
        """
        month_days = [date(2025, 12, 1), date(2025, 12, 2), date(2025, 12, 3)]
        day_minutes = {
            date(2025, 12, 1): 100,
            date(2025, 12, 2): 0,  # 0 is under goal but shouldn't count
            date(2025, 12, 3): 100,
        }

        streak = StreakService.calculate_streak(
            self.user.id, month_days, day_minutes
        )

        self.assertEqual(streak, 1)

    def test_mixed_over_under_goal(self):
        """Verify complex scenario with mixed days over/under goal.

        Tests that the longest valid streak is returned when
        multiple streaks exist due to days exceeding goal.

        Returns:
            None
        """
        month_days = [
            date(2025, 12, 1),
            date(2025, 12, 2),
            date(2025, 12, 3),
            date(2025, 12, 4),
            date(2025, 12, 5),
            date(2025, 12, 6),
        ]
        day_minutes = {
            date(2025, 12, 1): 100,  # under goal
            date(2025, 12, 2): 200,  # over goal - breaks
            date(2025, 12, 3): 110,  # under goal - new streak starts
            date(2025, 12, 4): 90,   # under goal
            date(2025, 12, 5): 120,  # at goal
            date(2025, 12, 6): 180,  # over goal - breaks
        }

        streak = StreakService.calculate_streak(
            self.user.id, month_days, day_minutes
        )

        # Longest streak is days 3-5 (3 days)
        self.assertEqual(streak, 3)


class TestStreakHelperMethods(unittest.TestCase):
    """Test the internal helper methods directly.

    Verifies that the private helper methods work correctly
    when called without database context.
    """

    def test_calculate_streak_without_goal_directly(self):
        """Verify _calculate_streak_without_goal method works directly.

        Returns:
            None
        """
        month_days = [date(2025, 12, 1), date(2025, 12, 2), date(2025, 12, 3)]
        day_minutes = {
            date(2025, 12, 1): 50,
            date(2025, 12, 2): 60,
        }

        streak = StreakService._calculate_streak_without_goal(
            month_days, day_minutes
        )

        self.assertEqual(streak, 2)

    def test_calculate_streak_with_goal_directly(self):
        """Verify _calculate_streak_with_goal method works directly.

        Returns:
            None
        """
        month_days = [date(2025, 12, 1), date(2025, 12, 2), date(2025, 12, 3)]
        day_minutes = {
            date(2025, 12, 1): 50,
            date(2025, 12, 2): 60,
            date(2025, 12, 3): 70,
        }
        target_minutes = 100

        streak = StreakService._calculate_streak_with_goal(
            month_days, day_minutes, target_minutes
        )

        self.assertEqual(streak, 3)


if __name__ == "__main__":
    unittest.main()
