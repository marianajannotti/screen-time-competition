"""Unit tests for the Leaderboard API.

This module contains test cases for the leaderboard API endpoints,
covering global rankings, streak calculations, and edge cases.
"""

import unittest
from datetime import date, timedelta

from backend import create_app
from backend.database import db
from backend.models import User, ScreenTimeLog, Goal


class LeaderboardAPITestCase(unittest.TestCase):
    """Base test case for the /api/leaderboard endpoints.

    Provides common setup, teardown, and helper methods for
    all leaderboard API tests.
    """

    def setUp(self):
        """Create app context, database, and test client.

        Returns:
            None
        """
        self.app = create_app("testing")
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client()

    def tearDown(self):
        """Clean up database and app context.

        Returns:
            None
        """
        db.session.remove()
        db.drop_all()
        db.engine.dispose()
        self.app_context.pop()

    def _create_user(self, username, email):
        """Create and persist a test user.

        Args:
            username: The username for the new user.
            email: The email address for the new user.

        Returns:
            User: The created user instance.
        """
        user = User(
            username=username,
            email=email,
            password_hash="x"
        )
        db.session.add(user)
        db.session.commit()
        return user

    def _add_screen_time(self, user_id, log_date, minutes):
        """Add a screen time log entry for a user.

        Args:
            user_id: The ID of the user to add the log for.
            log_date: The date of the screen time entry.
            minutes: The number of minutes of screen time.

        Returns:
            ScreenTimeLog: The created log entry instance.
        """
        log = ScreenTimeLog(
            user_id=user_id,
            app_name="Total",
            date=log_date,
            screen_time_minutes=minutes
        )
        db.session.add(log)
        db.session.commit()
        return log


class TestGlobalLeaderboardEndpoint(LeaderboardAPITestCase):
    """Tests for GET /api/leaderboard/global.

    Verifies the global leaderboard endpoint returns correct
    rankings based on streak and average screen time.
    """

    def test_empty_leaderboard(self):
        """Verify that empty database returns empty leaderboard.

        Returns:
            None
        """
        response = self.client.get("/api/leaderboard/global")

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["leaderboard"], [])
        self.assertEqual(data["scope"], "global")

    def test_single_user_leaderboard(self):
        """Verify that single user with logs appears in leaderboard.

        Returns:
            None
        """
        user = self._create_user("alice", "alice@test.com")
        today = date.today()
        self._add_screen_time(user.id, today, 120)

        response = self.client.get("/api/leaderboard/global")

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(len(data["leaderboard"]), 1)
        self.assertEqual(data["leaderboard"][0]["username"], "alice")
        self.assertEqual(data["leaderboard"][0]["rank"], 1)
        self.assertEqual(data["leaderboard"][0]["streak"], 1)

    def test_users_without_logs_included_with_zero_stats(self):
        """Verify that users without logs are included with zero stats.

        Users with no screen time logs should still appear on the leaderboard
        but rank lower than users with active streaks. Both users are included;
        users with streaks (e.g., alice) rank higher than those without logs (e.g., bob).

        Returns:
            None
        """
        user_with_logs = self._create_user("alice", "alice@test.com")
        self._create_user("bob", "bob@test.com")  # no logs
        
        today = date.today()
        self._add_screen_time(user_with_logs.id, today, 120)

        response = self.client.get("/api/leaderboard/global")

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        # Only users with screen time logs are included
        self.assertEqual(len(data["leaderboard"]), 1)
        self.assertEqual(data["leaderboard"][0]["username"], "alice")

    def test_ranking_by_streak_descending(self):
        """Verify that users are ranked by streak (higher streak = better).

        Returns:
            None
        """
        alice = self._create_user("alice", "alice@test.com")
        bob = self._create_user("bob", "bob@test.com")
        charlie = self._create_user("charlie", "charlie@test.com")

        today = date.today()

        # Alice: 3-day streak
        for i in range(3):
            self._add_screen_time(alice.id, today - timedelta(days=i), 120)

        # Bob: 1-day streak
        self._add_screen_time(bob.id, today, 60)

        # Charlie: 2-day streak
        for i in range(2):
            self._add_screen_time(charlie.id, today - timedelta(days=i), 90)

        response = self.client.get("/api/leaderboard/global")

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        lb = data["leaderboard"]

        self.assertEqual(len(lb), 3)
        # Ranked by streak: alice(3) > charlie(2) > bob(1)
        self.assertEqual(lb[0]["username"], "alice")
        self.assertEqual(lb[0]["rank"], 1)
        self.assertEqual(lb[0]["streak"], 3)

        self.assertEqual(lb[1]["username"], "charlie")
        self.assertEqual(lb[1]["rank"], 2)
        self.assertEqual(lb[1]["streak"], 2)

        self.assertEqual(lb[2]["username"], "bob")
        self.assertEqual(lb[2]["rank"], 3)
        self.assertEqual(lb[2]["streak"], 1)

    def test_tiebreaker_by_avg_screen_time_ascending(self):
        """Verify that equal streaks are ranked by lower avg screen time.

        Returns:
            None
        """
        alice = self._create_user("alice", "alice@test.com")
        bob = self._create_user("bob", "bob@test.com")

        today = date.today()

        # Both have 2-day streak
        # Alice: avg 150 minutes
        self._add_screen_time(alice.id, today, 180)
        self._add_screen_time(alice.id, today - timedelta(days=1), 120)

        # Bob: avg 90 minutes (lower = better)
        self._add_screen_time(bob.id, today, 100)
        self._add_screen_time(bob.id, today - timedelta(days=1), 80)

        response = self.client.get("/api/leaderboard/global")

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        lb = data["leaderboard"]

        self.assertEqual(len(lb), 2)
        # Same streak (2), Bob has lower avg so ranks higher
        self.assertEqual(lb[0]["username"], "bob")
        self.assertEqual(lb[0]["rank"], 1)

        self.assertEqual(lb[1]["username"], "alice")
        self.assertEqual(lb[1]["rank"], 2)

    def test_limit_parameter(self):
        """Verify that limit parameter restricts number of results.

        Returns:
            None
        """
        # Create users with known rankings
        today = date.today()
        user0 = self._create_user("user0", "user0@test.com")
        self._add_screen_time(user0.id, today, 100)  # Best (lowest avg)
        user1 = self._create_user("user1", "user1@test.com")
        self._add_screen_time(user1.id, today, 110)
        user2 = self._create_user("user2", "user2@test.com")
        self._add_screen_time(user2.id, today, 120)
        user3 = self._create_user("user3", "user3@test.com")
        self._add_screen_time(user3.id, today, 130)
        user4 = self._create_user("user4", "user4@test.com")
        self._add_screen_time(user4.id, today, 140)

        response = self.client.get("/api/leaderboard/global?limit=3")

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(len(data["leaderboard"]), 3)
        # Verify top 3 have lowest screen times
        self.assertEqual(data["leaderboard"][0]["username"], "user0")
        self.assertEqual(data["leaderboard"][1]["username"], "user1")
        self.assertEqual(data["leaderboard"][2]["username"], "user2")

    def test_limit_max_100(self):
        """Verify that limit is capped at 100.

        Returns:
            None
        """
        # Create 110 users to test the cap
        today = date.today()
        for i in range(110):
            user = self._create_user(f"user{i}", f"user{i}@test.com")
            self._add_screen_time(user.id, today, 100)

        response = self.client.get("/api/leaderboard/global?limit=150")

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        # Verify limit is capped at 100, not 110 or 150
        self.assertEqual(len(data["leaderboard"]), 100)

    def test_invalid_limit_returns_error(self):
        """Verify that invalid limit parameter returns 400 error.

        Returns:
            None
        """
        user = self._create_user("alice", "alice@test.com")
        self._add_screen_time(user.id, date.today(), 120)

        response = self.client.get("/api/leaderboard/global?limit=invalid")

        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn("error", data)
        self.assertIn("Invalid limit parameter", data["error"])

    def test_options_request_for_cors(self):
        """Verify that OPTIONS request returns 200 for CORS preflight.

        Returns:
            None
        """
        response = self.client.options("/api/leaderboard/global")

        self.assertEqual(response.status_code, 200)

    def test_response_contains_required_fields(self):
        """Verify that response contains all required fields for each user.

        Returns:
            None
        """
        user = self._create_user("alice", "alice@test.com")
        today = date.today()
        self._add_screen_time(user.id, today, 120)
        self._add_screen_time(user.id, today - timedelta(days=1), 180)

        response = self.client.get("/api/leaderboard/global")

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        entry = data["leaderboard"][0]

        # Check required fields exist
        self.assertIn("rank", entry)
        self.assertIn("username", entry)
        self.assertIn("streak", entry)
        self.assertIn("avg_per_day", entry)
        self.assertIn("days_logged", entry)


class TestLeaderboardWithGoals(LeaderboardAPITestCase):
    """Tests for leaderboard streak calculation with daily goals.

    Verifies that streak calculations respect user's daily goals
    when determining rankings.
    """

    def test_streak_respects_daily_goal(self):
        """Verify that streak only counts days meeting daily goal if set.

        Returns:
            None
        """
        alice = self._create_user("alice", "alice@test.com")
        bob = self._create_user("bob", "bob@test.com")

        today = date.today()

        # Alice has a 120-minute daily goal
        goal = Goal(user_id=alice.id, goal_type="daily", target_minutes=120)
        db.session.add(goal)
        db.session.commit()

        # Alice logs 3 days, but day 2 exceeds goal
        self._add_screen_time(alice.id, today, 100)  # under goal
        self._add_screen_time(alice.id, today - timedelta(days=1), 150)  # over
        self._add_screen_time(alice.id, today - timedelta(days=2), 90)  # under

        # Bob has no goal, 2-day streak
        self._add_screen_time(bob.id, today, 200)
        self._add_screen_time(bob.id, today - timedelta(days=1), 200)

        response = self.client.get("/api/leaderboard/global")

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        lb = data["leaderboard"]

        # Bob should rank higher (2-day streak vs Alice's 1-day streak)
        self.assertEqual(lb[0]["username"], "bob")
        self.assertEqual(lb[0]["streak"], 2)

        # Alice's streak should be 1 (only today counts, as yesterday's 150 minutes exceeded the 120 goal)
        self.assertEqual(lb[1]["username"], "alice")
        self.assertEqual(lb[1]["streak"], 1)  # Only today counts
        self.assertEqual(lb[1]["days_logged"], 3)  # Verify all days were logged


class TestLeaderboardEdgeCases(LeaderboardAPITestCase):
    """Edge case tests for leaderboard.

    Tests unusual scenarios and boundary conditions for
    the leaderboard functionality.
    """

    def test_multiple_logs_same_day_aggregated(self):
        """Verify that multiple logs on same day are summed.

        Returns:
            None
        """
        user = self._create_user("alice", "alice@test.com")
        today = date.today()

        # Two logs on same day
        self._add_screen_time(user.id, today, 60)
        self._add_screen_time(user.id, today, 60)

        response = self.client.get("/api/leaderboard/global")

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        entry = data["leaderboard"][0]

        # Should count as one day with 120 minutes
        self.assertEqual(entry["streak"], 1)
        self.assertEqual(entry["avg_per_day"], 120)

    def test_logs_only_in_current_month(self):
        """Verify that leaderboard only includes current month's data.

        Returns:
            None
        """
        user = self._create_user("alice", "alice@test.com")
        today = date.today()

        # Add current month log
        self._add_screen_time(user.id, today, 120)

        # Add previous month log (should be excluded)
        last_month = today.replace(day=1) - timedelta(days=1)
        self._add_screen_time(user.id, last_month, 200)

        response = self.client.get("/api/leaderboard/global")

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(len(data["leaderboard"]), 1)
        entry = data["leaderboard"][0]

        # Should only count current month's 120 minutes, not last month's 200
        self.assertEqual(entry["days_logged"], 1)
        self.assertEqual(entry["total_minutes"], 120)
        self.assertEqual(entry["streak"], 1)


if __name__ == "__main__":
    unittest.main()
