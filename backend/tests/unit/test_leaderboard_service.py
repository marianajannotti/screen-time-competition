"""Unit tests for the LeaderboardService.

This module contains test cases for the LeaderboardService class,
covering global leaderboard functionality and user ranking.
"""
import unittest
from datetime import date, timedelta

from backend import create_app
from backend.database import db
from backend.models import User, ScreenTimeLog, Goal
from backend.services import LeaderboardService


class LeaderboardServiceTestCase(unittest.TestCase):
    """Base test case for LeaderboardService unit tests.

    Provides common setup and teardown for all leaderboard service tests.
    """

    def setUp(self):
        """Create app context, database, and test fixtures.

        Returns:
            None
        """
        self.app = create_app("testing")
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Create test users
        self.user1 = User(
            username="alice",
            email="alice@example.com",
            password_hash="hash"
        )
        self.user2 = User(
            username="bob",
            email="bob@example.com",
            password_hash="hash"
        )
        self.user3 = User(
            username="charlie",
            email="charlie@example.com",
            password_hash="hash"
        )
        
        db.session.add_all([self.user1, self.user2, self.user3])
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

    def _add_screen_time(self, user_id, log_date, minutes):
        """Helper method to add screen time log for a user.

        Args:
            user_id (int): User ID to add screen time for
            log_date (date): Date of the screen time log
            minutes (int): Total minutes of screen time

        Returns:
            None
        """
        hours = minutes // 60
        remaining_minutes = minutes % 60
        
        log = ScreenTimeLog(
            user_id=user_id,
            app_name="Total",
            hours=hours,
            minutes=remaining_minutes,
            total_minutes=minutes,
            date=log_date
        )
        db.session.add(log)
        db.session.commit()


class TestGetGlobalLeaderboard(LeaderboardServiceTestCase):
    """Test global leaderboard functionality."""

    def test_get_global_leaderboard_empty(self):
        """Verify that empty leaderboard is returned when no screen time logged.

        Returns:
            None
        """
        leaderboard = LeaderboardService.get_global_leaderboard()
        
        self.assertEqual(len(leaderboard), 0)

    def test_get_global_leaderboard_single_user(self):
        """Verify that leaderboard works with single user.

        Returns:
            None
        """
        today = date.today()
        self._add_screen_time(self.user1.id, today, 120)
        
        leaderboard = LeaderboardService.get_global_leaderboard()
        
        self.assertEqual(len(leaderboard), 1)
        entry = leaderboard[0]
        self.assertEqual(entry["rank"], 1)
        self.assertEqual(entry["username"], "alice")
        self.assertEqual(entry["streak"], 1)
        self.assertEqual(entry["avg_per_day"], 120)
        self.assertEqual(entry["days_logged"], 1)

    def test_get_global_leaderboard_ranking_by_streak(self):
        """Verify that users are ranked by streak (higher is better).

        Returns:
            None
        """
        today = date.today()
        yesterday = today - timedelta(days=1)
        
        # Alice: 2-day streak
        self._add_screen_time(self.user1.id, yesterday, 120)
        self._add_screen_time(self.user1.id, today, 120)
        
        # Bob: 1-day streak
        self._add_screen_time(self.user2.id, today, 90)
        
        # Charlie: 3-day streak
        self._add_screen_time(self.user3.id, today - timedelta(days=2), 150)
        self._add_screen_time(self.user3.id, yesterday, 150)
        self._add_screen_time(self.user3.id, today, 150)
        
        leaderboard = LeaderboardService.get_global_leaderboard()
        
        # Should be ranked by streak: Charlie (3), Alice (2), Bob (1)
        self.assertEqual(len(leaderboard), 3)
        self.assertEqual(leaderboard[0]["username"], "charlie")
        self.assertEqual(leaderboard[0]["streak"], 3)
        self.assertEqual(leaderboard[1]["username"], "alice")
        self.assertEqual(leaderboard[1]["streak"], 2)
        self.assertEqual(leaderboard[2]["username"], "bob")
        self.assertEqual(leaderboard[2]["streak"], 1)

    def test_get_global_leaderboard_tiebreaker_avg_screen_time(self):
        """Verify that ties are broken by average screen time (lower is better).

        Returns:
            None
        """
        today = date.today()
        
        # Both users have same streak but different avg screen time
        self._add_screen_time(self.user1.id, today, 120)  # Alice: 120 avg
        self._add_screen_time(self.user2.id, today, 90)   # Bob: 90 avg
        
        leaderboard = LeaderboardService.get_global_leaderboard()
        
        # Bob should rank higher due to lower screen time
        self.assertEqual(len(leaderboard), 2)
        self.assertEqual(leaderboard[0]["username"], "bob")
        self.assertEqual(leaderboard[0]["avg_per_day"], 90)
        self.assertEqual(leaderboard[1]["username"], "alice")
        self.assertEqual(leaderboard[1]["avg_per_day"], 120)

    def test_get_global_leaderboard_with_limit(self):
        """Verify that limit parameter works correctly.

        Returns:
            None
        """
        today = date.today()
        
        # Create entries for all users
        self._add_screen_time(self.user1.id, today, 120)
        self._add_screen_time(self.user2.id, today, 90)
        self._add_screen_time(self.user3.id, today, 150)
        
        leaderboard = LeaderboardService.get_global_leaderboard(limit=2)
        
        self.assertEqual(len(leaderboard), 2)

    def test_get_global_leaderboard_calculates_avg_correctly(self):
        """Verify that average screen time per day is calculated correctly.

        Returns:
            None
        """
        today = date.today()
        yesterday = today - timedelta(days=1)
        
        # Alice: 120 + 180 = 300 total, 2 days = 150 avg
        self._add_screen_time(self.user1.id, yesterday, 120)
        self._add_screen_time(self.user1.id, today, 180)
        
        leaderboard = LeaderboardService.get_global_leaderboard()
        
        entry = leaderboard[0]
        self.assertEqual(entry["username"], "alice")
        self.assertEqual(entry["avg_per_day"], 150)
        self.assertEqual(entry["days_logged"], 2)

    def test_get_global_leaderboard_only_current_month(self):
        """Verify that only current month data is considered.

        Returns:
            None
        """
        today = date.today()
        last_month = date(today.year, today.month - 1, 15) if today.month > 1 else date(today.year - 1, 12, 15)
        
        # Add screen time from last month and this month
        self._add_screen_time(self.user1.id, last_month, 120)
        self._add_screen_time(self.user1.id, today, 90)
        
        leaderboard = LeaderboardService.get_global_leaderboard()
        
        entry = leaderboard[0]
        # Should only count current month data
        self.assertEqual(entry["days_logged"], 1)
        self.assertEqual(entry["avg_per_day"], 90)

    def test_get_global_leaderboard_with_goals(self):
        """Verify that leaderboard works correctly with user goals.

        Returns:
            None
        """
        today = date.today()
        yesterday = today - timedelta(days=1)
        
        # Create goal for user1 (120 minutes daily)
        goal = Goal(
            user_id=self.user1.id,
            goal_type="daily",
            target_minutes=120
        )
        db.session.add(goal)
        db.session.commit()
        
        # Alice meets goal both days (streak = 2)
        self._add_screen_time(self.user1.id, yesterday, 100)  # Under goal
        self._add_screen_time(self.user1.id, today, 110)     # Under goal
        
        # Bob has no goal, logs both days (streak = 2)
        self._add_screen_time(self.user2.id, yesterday, 150)
        self._add_screen_time(self.user2.id, today, 160)
        
        leaderboard = LeaderboardService.get_global_leaderboard()
        
        # Both should have streak of 2, ranked by avg screen time
        alice_entry = next(entry for entry in leaderboard if entry["username"] == "alice")
        bob_entry = next(entry for entry in leaderboard if entry["username"] == "bob")
        
        self.assertEqual(alice_entry["streak"], 2)
        self.assertEqual(bob_entry["streak"], 2)
        # Alice should rank higher due to lower avg screen time
        self.assertEqual(leaderboard[0]["username"], "alice")

    def test_get_global_leaderboard_goal_breaks_streak(self):
        """Verify that exceeding goal breaks streak.

        Returns:
            None
        """
        today = date.today()
        yesterday = today - timedelta(days=1)
        
        # Create goal for user1
        goal = Goal(
            user_id=self.user1.id,
            goal_type="daily",
            target_minutes=120
        )
        db.session.add(goal)
        db.session.commit()
        
        # Alice meets goal on day 1, exceeds on day 2
        self._add_screen_time(self.user1.id, yesterday, 100)  # Under goal
        self._add_screen_time(self.user1.id, today, 150)     # Over goal - breaks streak
        
        leaderboard = LeaderboardService.get_global_leaderboard()
        
        entry = leaderboard[0]
        self.assertEqual(entry["username"], "alice")
        self.assertEqual(entry["streak"], 1)  # Only day 1 counts


if __name__ == "__main__":
    unittest.main()
