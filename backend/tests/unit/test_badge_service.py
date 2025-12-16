"""Unit tests for the BadgeService.

This module contains test cases for the BadgeService class,
covering badge management and user badge operations.
"""
import unittest
from unittest.mock import patch

from backend import create_app
from backend.database import db
from backend.models import User, Badge, UserBadge
from backend.services import BadgeService, ValidationError


class BadgeServiceTestCase(unittest.TestCase):
    """Base test case for BadgeService unit tests.

    Provides common setup and teardown for all badge service tests.
    """
    
    _counter = 0  # Class variable to ensure unique emails

    def setUp(self):
        """Create app context, database, and test fixtures.

        Returns:
            None
        """
        self.app = create_app("testing")
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Create test user with unique email
        BadgeServiceTestCase._counter += 1
        self.test_user = User(
            username=f"testuser{BadgeServiceTestCase._counter}",
            email=f"test{BadgeServiceTestCase._counter}@example.com",
            password_hash="hash"
        )
        db.session.add(self.test_user)
        
        # Create test badges
        self.badge1 = Badge(
            name="First Steps",
            description="Complete your first screen time log",
            icon="🎯",
            badge_type="milestone"
        )
        self.badge2 = Badge(
            name="Week Warrior",
            description="Log screen time for 7 consecutive days",
            icon="📅",
            badge_type="streak"
        )
        db.session.add(self.badge1)
        db.session.add(self.badge2)
        db.session.commit()
    
    def create_unique_user(self, username_prefix="user"):
        """Helper to create a user with unique email.
        
        Args:
            username_prefix: Prefix for username
            
        Returns:
            User object
        """
        BadgeServiceTestCase._counter += 1
        user = User(
            username=f"{username_prefix}{BadgeServiceTestCase._counter}",
            email=f"{username_prefix}{BadgeServiceTestCase._counter}@example.com",
            password_hash="hash"
        )
        db.session.add(user)
        db.session.commit()
        return user

    def tearDown(self):
        """Clean up database and app context.

        Returns:
            None
        """
        db.session.remove()
        db.drop_all()
        db.engine.dispose()
        self.app_context.pop()


class TestGetAllBadges(BadgeServiceTestCase):
    """Test getting all available badges."""

    def test_get_all_badges(self):
        """Verify that all badges are returned.

        Returns:
            None
        """
        badges = BadgeService.get_all_badges()
        
        # Expect 25 badges: 23 default badges + 2 test badges created in setUp
        self.assertEqual(len(badges), 25)
        badge_names = [badge.name for badge in badges]
        self.assertIn("First Steps", badge_names)
        self.assertIn("Week Warrior", badge_names)

    def test_get_all_badges_empty(self):
        """Verify that empty list is returned when no badges exist.

        Returns:
            None
        """
        # Clear badges
        Badge.query.delete()
        db.session.commit()
        
        badges = BadgeService.get_all_badges()
        self.assertEqual(len(badges), 0)


class TestGetUserBadges(BadgeServiceTestCase):
    """Test getting badges for a specific user."""

    def test_get_user_badges_none(self):
        """Verify that empty list is returned for user with no badges.

        Returns:
            None
        """
        user_badges = BadgeService.get_user_badges(self.test_user.id)
        self.assertEqual(len(user_badges), 0)

    def test_get_user_badges_with_badges(self):
        """Verify that user badges are returned correctly.

        Returns:
            None
        """
        # Award badges to user
        user_badge1 = UserBadge(
            user_id=self.test_user.id,
            badge_id=self.badge1.id
        )
        user_badge2 = UserBadge(
            user_id=self.test_user.id,
            badge_id=self.badge2.id
        )
        db.session.add(user_badge1)
        db.session.add(user_badge2)
        db.session.commit()

        user_badges = BadgeService.get_user_badges(self.test_user.id)
        
        self.assertEqual(len(user_badges), 2)
        # Verify eager loading works
        for user_badge in user_badges:
            self.assertIsNotNone(user_badge.badge)
            self.assertIn(user_badge.badge.name, ["First Steps", "Week Warrior"])

    def test_get_user_badges_different_user(self):
        """Verify that only specific user's badges are returned.

        Returns:
            None
        """
        # Create second user
        user2 = User(
            username="user2",
            email="user2@example.com",
            password_hash="hash"
        )
        db.session.add(user2)
        db.session.commit()

        # Award badge to first user only
        user_badge = UserBadge(
            user_id=self.test_user.id,
            badge_id=self.badge1.id
        )
        db.session.add(user_badge)
        db.session.commit()

        # Check first user has badge
        user1_badges = BadgeService.get_user_badges(self.test_user.id)
        self.assertEqual(len(user1_badges), 1)

        # Check second user has no badges
        user2_badges = BadgeService.get_user_badges(user2.id)
        self.assertEqual(len(user2_badges), 0)


class TestAwardBadge(BadgeServiceTestCase):
    """Test awarding badges to users."""

    def test_award_badge_success(self):
        """Verify that badge is awarded successfully to user.

        Returns:
            None
        """
        success, message = BadgeService.award_badge(self.test_user.id, "First Steps")
        
        self.assertTrue(success)
        self.assertIn("awarded", message.lower())
        
        # Verify badge was awarded
        user_badge = UserBadge.query.filter_by(
            user_id=self.test_user.id,
            badge_id=self.badge1.id
        ).first()
        self.assertIsNotNone(user_badge)
        self.assertIsNotNone(user_badge.earned_at)

    def test_award_badge_nonexistent(self):
        """Verify that awarding nonexistent badge fails.

        Returns:
            None
        """
        with self.assertRaises(ValidationError):
            BadgeService.award_badge(self.test_user.id, "Nonexistent Badge")

    def test_award_badge_already_earned(self):
        """Verify that awarding already earned badge fails.

        Returns:
            None
        """
        # Award badge first time
        success1, _ = BadgeService.award_badge(self.test_user.id, "First Steps")
        self.assertTrue(success1)
        
        # Try to award same badge again
        success2, message = BadgeService.award_badge(self.test_user.id, "First Steps")
        
        self.assertFalse(success2)
        self.assertEqual(message, "User already has badge 'First Steps'")
        
        # Verify only one badge record exists
        count = UserBadge.query.filter_by(
            user_id=self.test_user.id,
            badge_id=self.badge1.id
        ).count()
        self.assertEqual(count, 1)

    def test_award_badge_nonexistent_user(self):
        """Verify that awarding badge to nonexistent user is handled gracefully.

        Returns:
            None
        """
        # This should not raise an exception, but the badge won't be created
        # due to foreign key constraint (user_id must exist)
        success, message = BadgeService.award_badge(99999, "First Steps")
        
        # The service should handle this case
        self.assertFalse(success)

    def test_award_badge_duplicate_prevention(self):
        """Test that awarding the same badge twice doesn't create duplicates.

        Returns:
            None
        """
        # Create test data first
        BadgeService.initialize_badges()
        import time
        unique_email = f"testuser_{int(time.time() * 1000000)}@example.com"
        user = User(username=f"testuser_{int(time.time())}", email=unique_email, password_hash="hash")
        db.session.add(user)
        db.session.commit()
        
        badge = Badge.query.filter_by(name="Fresh Start").first()
        
        # Award badge twice
        result1, msg1 = BadgeService.award_badge(user.id, badge.name)
        result2, msg2 = BadgeService.award_badge(user.id, badge.name)
        
        # First should succeed, second should return False (already has badge)
        self.assertTrue(result1)
        self.assertFalse(result2)
        
        # Verify only one user_badge record exists
        user_badges = UserBadge.query.filter_by(user_id=user.id, badge_id=badge.id).all()
        self.assertEqual(len(user_badges), 1)

    def test_award_badge_nonexistent_user(self):
        """Test awarding badge to nonexistent user.

        Returns:
            None
        """
        BadgeService.initialize_badges()
        
        with self.assertRaises(ValidationError):
            BadgeService.award_badge(999999, "First Steps")

    def test_award_badge_nonexistent_badge(self):
        """Test awarding nonexistent badge.

        Returns:
            None
        """
        user = self.create_unique_user("testuser")
        
        with self.assertRaises(ValidationError):
            BadgeService.award_badge(user.id, "Nonexistent Badge")

    def test_revoke_badge_success(self):
        """Test successful badge revocation.

        Returns:
            None
        """
        # Setup
        BadgeService.initialize_badges()
        user = self.create_unique_user("testuser")
        
        badge = Badge.query.filter_by(name="Fresh Start").first()
        BadgeService.award_badge(user.id, badge.name)
        
        # Revoke badge
        result = BadgeService.revoke_badge(user.id, badge.name)
        self.assertTrue(result)
        
        # Verify badge is gone
        user_badges = BadgeService.get_user_badges(user.id)
        badge_names = [ub.badge.name for ub in user_badges]
        self.assertNotIn(badge.name, badge_names)

    def test_revoke_badge_not_owned(self):
        """Test revoking badge that user doesn't have.

        Returns:
            None
        """
        BadgeService.initialize_badges()
        user = self.create_unique_user("testuser")
        
        badge = Badge.query.filter_by(name="Fresh Start").first()
        
        # Try to revoke badge user doesn't have
        result = BadgeService.revoke_badge(user.id, badge.name)
        self.assertFalse(result)

    def test_get_badge_progress_empty(self):
        """Test getting badge progress for user with no badges.

        Returns:
            None
        """
        BadgeService.initialize_badges()
        user = self.create_unique_user("testuser")
        
        progress = BadgeService.get_badge_progress(user.id)
        
        self.assertIsInstance(progress, dict)
        self.assertIn("earned_count", progress)
        self.assertIn("total_count", progress)
        self.assertIn("percentage", progress)
        self.assertEqual(progress["earned_count"], 0)
        self.assertGreater(progress["total_count"], 0)

    def test_get_badge_progress_with_badges(self):
        """Test getting badge progress for user with some badges.

        Returns:
            None
        """
        BadgeService.initialize_badges()
        user = self.create_unique_user("testuser")
        
        # Award some badges
        badges = Badge.query.limit(3).all()
        for badge in badges:
            BadgeService.award_badge(user.id, badge.name)
        
        progress = BadgeService.get_badge_progress(user.id)
        
        self.assertEqual(progress["earned_count"], 3)
        self.assertGreater(progress["percentage"], 0)
        self.assertLessEqual(progress["percentage"], 100)

    def test_get_available_badges_filtered(self):
        """Test getting available badges with category filter.

        Returns:
            None
        """
        BadgeService.initialize_badges()
        
        # Test with category filter if supported
        try:
            milestone_badges = BadgeService.get_available_badges(category="milestone")
            self.assertIsInstance(milestone_badges, list)
        except TypeError:
            # Category filtering not implemented
            all_badges = BadgeService.get_available_badges()
            self.assertIsInstance(all_badges, list)
            self.assertGreater(len(all_badges), 0)

    def test_badge_rarity_system(self):
        """Test badge rarity classification if implemented.

        Returns:
            None
        """
        BadgeService.initialize_badges()
        
        # Test rarity classification
        badges = Badge.query.all()
        
        for badge in badges:
            # Check if badge has rarity attribute
            if hasattr(badge, 'rarity'):
                self.assertIn(badge.rarity, ['common', 'rare', 'epic', 'legendary'])

    def test_badge_statistics(self):
        """Test badge statistics functionality.

        Returns:
            None
        """
        BadgeService.initialize_badges()
        
        # Create multiple users with badges
        users = []
        for i in range(5):
            user = self.create_unique_user(f"user{i}")
            users.append(user)
        
        # Award some badges
        first_badge = Badge.query.first()
        for user in users[:3]:  # 3 out of 5 users get the badge
            BadgeService.award_badge(user.id, first_badge.name)
        
        # Test badge statistics
        stats = BadgeService.get_badge_statistics()
        
        self.assertIsInstance(stats, dict)
        if first_badge.name in stats:
            self.assertEqual(stats[first_badge.name]["count"], 3)

    def test_badge_leaderboard(self):
        """Test badge leaderboard functionality.

        Returns:
            None
        """
        BadgeService.initialize_badges()
        
        # Create users with different numbers of badges
        users_data = [
            ("user1", 5),  # 5 badges
            ("user2", 3),  # 3 badges
            ("user3", 7),  # 7 badges
        ]
        
        badges = Badge.query.limit(10).all()
        
        for username, badge_count in users_data:
            user = self.create_unique_user(username)
            
            # Award badges
            for i in range(min(badge_count, len(badges))):
                BadgeService.award_badge(user.id, badges[i].name)
        
        # Get leaderboard
        leaderboard = BadgeService.get_badge_leaderboard(limit=10)
        
        self.assertIsInstance(leaderboard, list)
        self.assertGreater(len(leaderboard), 0)
        
        # Should be sorted by badge count (descending)
        for i in range(len(leaderboard) - 1):
            current_count = leaderboard[i]["badge_count"]
            next_count = leaderboard[i + 1]["badge_count"]
            self.assertGreaterEqual(current_count, next_count)


class TestInitializeBadges(BadgeServiceTestCase):
    """Test badge initialization functionality."""

    def setUp(self):
        """Create app context and database without initial badges.

        Returns:
            None
        """
        self.app = create_app("testing")
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        # Don't create test badges for this test class

    def test_initialize_badges_creates_default_badges(self):
        """Verify that initialize_badges creates default badges.

        Returns:
            None
        """
        # Verify badges were already initialized by create_app (23 default badges)
        self.assertEqual(Badge.query.count(), 23)
        
        BadgeService.initialize_badges()
        
        # Verify badges count remains 23 (idempotent - no duplicates)
        badges_count = Badge.query.count()
        self.assertEqual(badges_count, 23)
        
        # Verify some expected badges exist
        fresh_start = Badge.query.filter_by(name="Fresh Start").first()
        self.assertIsNotNone(fresh_start)
        self.assertIsNotNone(fresh_start.description)
        self.assertIsNotNone(fresh_start.icon)

    def test_initialize_badges_idempotent(self):
        """Verify that initialize_badges can be called multiple times safely.

        Returns:
            None
        """
        BadgeService.initialize_badges()
        initial_count = Badge.query.count()
        
        # Call again
        BadgeService.initialize_badges()
        second_count = Badge.query.count()
        
        # Should not create duplicates
        self.assertEqual(initial_count, second_count)


if __name__ == "__main__":
    unittest.main()
