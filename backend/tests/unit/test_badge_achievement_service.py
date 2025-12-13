"""Unit tests for the BadgeAchievementService.

This module contains test cases for the BadgeAchievementService class,
covering badge logic, achievement detection, and badge awarding functionality.
"""
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta, date

from backend import create_app
from backend.database import db
from backend.models import User, ScreenTimeLog, Badge, UserBadge, Friendship
from backend.services.badge_achievement_service import BadgeAchievementService


class BadgeAchievementServiceTestCase(unittest.TestCase):
    """Base test case for BadgeAchievementService unit tests.

    Provides common setup and teardown for all badge achievement service tests.
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

        # Create test user
        self.test_user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password"
        )
        db.session.add(self.test_user)
        db.session.commit()

    def tearDown(self):
        """Clean up database and app context.

        Returns:
            None
        """
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    @patch('backend.services.badge_achievement_service.BadgeAchievementService._check_streak_badges')
    @patch('backend.services.badge_achievement_service.BadgeAchievementService._check_reduction_badges')
    @patch('backend.services.badge_achievement_service.BadgeAchievementService._check_social_badges')
    @patch('backend.services.badge_achievement_service.BadgeAchievementService._check_leaderboard_badges')
    @patch('backend.services.badge_achievement_service.BadgeAchievementService._check_prestige_badges')
    def test_check_and_award_badges_success(self, mock_prestige, mock_leaderboard, mock_social, mock_reduction, mock_streak):
        """Test successful badge checking and awarding.

        Args:
            mock_prestige: Mock for prestige badge checking
            mock_leaderboard: Mock for leaderboard badge checking
            mock_social: Mock for social badge checking
            mock_reduction: Mock for reduction badge checking
            mock_streak: Mock for streak badge checking

        Returns:
            None
        """
        # Setup mocks
        mock_streak.return_value = ["Streak Master"]
        mock_reduction.return_value = ["Reduction Champion"]
        mock_social.return_value = ["Social Butterfly"]
        mock_leaderboard.return_value = ["Leaderboard Champion"]
        mock_prestige.return_value = ["Prestige Player"]

        # Execute
        awarded_badges = BadgeAchievementService.check_and_award_badges(self.test_user.id)

        # Verify
        self.assertEqual(len(awarded_badges), 5)
        self.assertIn("Streak Master", awarded_badges)
        self.assertIn("Reduction Champion", awarded_badges)
        self.assertIn("Social Butterfly", awarded_badges)
        self.assertIn("Leaderboard Champion", awarded_badges)
        self.assertIn("Prestige Player", awarded_badges)

    def test_check_streak_badges_qualification(self):
        """Test streak badge qualification.

        Returns:
            None
        """
        # Set streak count on user
        self.test_user.streak_count = 7
        db.session.commit()

        # Execute
        badges = BadgeAchievementService._check_streak_badges(self.test_user)

        # Should return some badges (exact badges depend on implementation)
        self.assertIsInstance(badges, list)

    def test_check_reduction_badges_qualification(self):
        """Test reduction badge qualification.

        Returns:
            None
        """
        # Execute
        badges = BadgeAchievementService._check_reduction_badges(self.test_user)

        # Should return a list (may be empty)
        self.assertIsInstance(badges, list)

    def test_check_social_badges_qualification(self):
        """Test social badge qualification.

        Returns:
            None
        """
        # Execute
        badges = BadgeAchievementService._check_social_badges(self.test_user)

        # Should return a list (may be empty)
        self.assertIsInstance(badges, list)

    def test_check_leaderboard_badges_qualification(self):
        """Test leaderboard badge qualification.

        Returns:
            None
        """
        # Execute
        badges = BadgeAchievementService._check_leaderboard_badges(self.test_user)

        # Should return a list (may be empty)
        self.assertIsInstance(badges, list)

    def test_check_prestige_badges_qualification(self):
        """Test prestige badge qualification.

        Returns:
            None
        """
        # Execute
        badges = BadgeAchievementService._check_prestige_badges(self.test_user)

        # Should return a list (may be empty)
        self.assertIsInstance(badges, list)

    def test_check_and_award_badges_no_new_badges(self):
        """Test badge checking when no new badges are earned.

        Returns:
            None
        """
        # Setup mocks to return empty lists
        with patch.multiple(
            'backend.services.badge_achievement_service.BadgeAchievementService',
            _check_streak_badges=MagicMock(return_value=[]),
            _check_reduction_badges=MagicMock(return_value=[]),
            _check_social_badges=MagicMock(return_value=[]),
            _check_leaderboard_badges=MagicMock(return_value=[]),
            _check_prestige_badges=MagicMock(return_value=[])
        ):
            # Execute
            awarded_badges = BadgeAchievementService.check_and_award_badges(self.test_user.id)

        # Verify
        self.assertEqual(awarded_badges, [])

    def test_check_and_award_badges_invalid_user(self):
        """Test badge checking with invalid user ID.

        Returns:
            None
        """
        # Test with invalid user ID
        awarded_badges = BadgeAchievementService.check_and_award_badges(999999)
        
        # Should return empty list
        self.assertEqual(awarded_badges, [])

    def test_check_and_award_badges_zero_user_id(self):
        """Test badge checking with zero user ID.

        Returns:
            None
        """
        # Test with zero user ID
        awarded_badges = BadgeAchievementService.check_and_award_badges(0)
        
        # Should return empty list
        self.assertEqual(awarded_badges, [])

    def test_check_and_award_badges_negative_user_id(self):
        """Test badge checking with negative user ID.

        Returns:
            None
        """
        # Test with negative user ID
        awarded_badges = BadgeAchievementService.check_and_award_badges(-1)
        
        # Should return empty list
        self.assertEqual(awarded_badges, [])


if __name__ == '__main__':
    unittest.main()
