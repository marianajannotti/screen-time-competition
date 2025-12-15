"""Integration tests for email notifications."""

import logging
import unittest
from unittest.mock import patch
from flask import Flask
from werkzeug.security import generate_password_hash

from backend import create_app
from backend.database import db
from backend.models import User, Friendship
from backend.services.badge_service import BadgeService
from backend.services.badge_achievement_service import BadgeAchievementService
from backend.services.friendship_service import FriendshipService

# Disable logging output during tests
logging.disable(logging.CRITICAL)


class TestEmailIntegration(unittest.TestCase):
    """Test email notifications triggered by user actions."""

    def setUp(self):
        """Set up test fixtures."""
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = self.app.test_client()
        
        with self.app.app_context():
            db.create_all()
            
            # Initialize badges
            BadgeService.initialize_badges()
            
            # Create test users
            self.user1 = User(
                username='user1',
                email='user1@example.com',
                password_hash=generate_password_hash('password123')
            )
            
            self.user2 = User(
                username='user2',
                email='user2@example.com',
                password_hash=generate_password_hash('password123')
            )
            
            db.session.add(self.user1)
            db.session.add(self.user2)
            db.session.commit()

    def tearDown(self):
        """Clean up after tests."""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    @patch('backend.mail')
    def test_registration_sends_welcome_email(self, mock_mail):
        """Test that user registration triggers welcome email."""
        response = self.client.post('/api/auth/register', json={
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'password123'
        }, content_type='application/json')
        
        self.assertEqual(response.status_code, 201)
        
        # Verify welcome email was sent
        mock_mail.send.assert_called()
        sent_message = mock_mail.send.call_args[0][0]
        self.assertEqual(sent_message.recipients, ['newuser@example.com'])
        self.assertIn('Welcome', sent_message.subject)

    @patch('backend.mail')
    def test_badge_award_sends_email(self, mock_mail):
        """Test that awarding a badge triggers email notification."""
        with self.app.app_context():
            # Award a badge using BadgeAchievementService
            # (which includes email sending)
            user = User.query.filter_by(username='user1').first()
            user.streak_count = 1  # Qualify for "Fresh Start" badge
            db.session.commit()
            
            awarded_badges = BadgeAchievementService.check_and_award_badges(
                user.id
            )
            
            # Verify badge was awarded
            self.assertIn('Fresh Start', awarded_badges)
            
            # Verify email was sent
            self.assertTrue(mock_mail.send.called)
            sent_message = mock_mail.send.call_args[0][0]
            self.assertEqual(sent_message.recipients, ['user1@example.com'])
            self.assertIn('Badge Unlocked', sent_message.subject)
            self.assertIn('Fresh Start', sent_message.subject)

    @patch('backend.mail')
    def test_friend_request_sends_email(self, mock_mail):
        """Test that sending friend request triggers email."""
        with self.app.app_context():
            user1 = User.query.filter_by(username='user1').first()
            user2 = User.query.filter_by(username='user2').first()
            
            # Send friend request
            friendship = FriendshipService.send_request(user1.id, 'user2')
            
            # Verify friend request was created
            self.assertEqual(friendship.status, 'pending')
            
            # Verify email was sent
            mock_mail.send.assert_called()
            sent_message = mock_mail.send.call_args[0][0]
            self.assertEqual(sent_message.recipients, ['user2@example.com'])
            self.assertIn('friend request', sent_message.subject)
            self.assertIn('user1', sent_message.subject)

    @patch('backend.mail')
    def test_accept_friend_request_sends_email(self, mock_mail):
        """Test that accepting friend request triggers email."""
        with self.app.app_context():
            user1 = User.query.filter_by(username='user1').first()
            user2 = User.query.filter_by(username='user2').first()
            
            # Create friend request
            friendship = Friendship(
                user_id=user1.id,
                friend_id=user2.id,
                status='pending'
            )
            db.session.add(friendship)
            db.session.commit()
            
            # Reset mock to clear the send_request call
            mock_mail.send.reset_mock()
            
            # Accept the request
            FriendshipService.accept_request(user2.id, friendship.id)
            
            # Verify email was sent to requester
            mock_mail.send.assert_called()
            sent_message = mock_mail.send.call_args[0][0]
            self.assertEqual(sent_message.recipients, ['user1@example.com'])
            self.assertIn('accepted', sent_message.subject)
            self.assertIn('user2', sent_message.subject)

    @patch('backend.mail')
    def test_email_failure_does_not_break_badge_awarding(self, mock_mail):
        """Test that email failures don't prevent badge awarding."""
        # Make email sending fail
        mock_mail.send.side_effect = Exception("SMTP Error")
        
        with self.app.app_context():
            user = User.query.filter_by(username='user1').first()
            user.streak_count = 7  # Qualify for "7-Day Focus" badge
            db.session.commit()
            
            # Award badges (should succeed despite email failure)
            awarded_badges = BadgeAchievementService.check_and_award_badges(
                user.id
            )
            
            # Verify badge was still awarded
            self.assertIn('7-Day Focus', awarded_badges)
            
            # Verify user has the badge
            user_badges = BadgeService.get_user_badges(user.id)
            badge_names = [ub.badge.name for ub in user_badges]
            self.assertIn('7-Day Focus', badge_names)

    @patch('backend.mail')
    def test_email_failure_does_not_break_friendship(self, mock_mail):
        """Test that email failures don't prevent friendship actions."""
        # Make email sending fail
        mock_mail.send.side_effect = Exception("SMTP Error")
        
        with self.app.app_context():
            user1 = User.query.filter_by(username='user1').first()
            
            # Send friend request (should succeed despite email failure)
            friendship = FriendshipService.send_request(user1.id, 'user2')
            
            # Verify friend request was still created
            self.assertEqual(friendship.status, 'pending')
            self.assertEqual(friendship.user_id, user1.id)

    @patch('backend.mail')
    def test_multiple_badges_send_multiple_emails(self, mock_mail):
        """Test that multiple badges trigger multiple emails."""
        with self.app.app_context():
            user = User.query.filter_by(username='user1').first()
            
            # Qualify for multiple badges
            user.streak_count = 30  # Fresh Start, 7-Day Focus, etc.
            db.session.commit()
            
            awarded_badges = BadgeAchievementService.check_and_award_badges(
                user.id
            )
            
            # Verify multiple badges awarded
            self.assertGreater(len(awarded_badges), 1)
            
            # Verify multiple emails sent (one per badge)
            self.assertEqual(mock_mail.send.call_count, len(awarded_badges))


if __name__ == '__main__':
    unittest.main()
