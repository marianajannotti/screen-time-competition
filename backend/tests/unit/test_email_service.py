"""Unit tests for email service functions."""

import unittest
from unittest.mock import patch
import os
from flask import Flask
from flask_mail import Mail

from backend.services.email_service import (
    send_password_reset_email,
    send_badge_notification,
    send_friend_request_notification,
    send_friend_request_accepted_notification,
    send_welcome_email
)


class TestEmailService(unittest.TestCase):
    """Test email service functions."""

    def setUp(self):
        """Set up test fixtures."""
        # Get the template directory path
        base_dir = os.path.dirname(__file__)
        template_dir = os.path.join(base_dir, '..', '..', 'templates')
        
        self.app = Flask(__name__, template_folder=template_dir)
        self.app.config['TESTING'] = True
        self.app.config['MAIL_SERVER'] = 'smtp.gmail.com'
        self.app.config['MAIL_PORT'] = 587
        self.app.config['MAIL_USE_TLS'] = True
        self.app.config['MAIL_USERNAME'] = 'test@example.com'
        self.app.config['MAIL_PASSWORD'] = 'testpassword'
        self.app.config['MAIL_DEFAULT_SENDER'] = 'test@example.com'
        self.app.config['FRONTEND_URL'] = 'http://localhost:5173'
        
        # Initialize Flask-Mail
        self.mail = Mail(self.app)
        
        # Create application context
        self.ctx = self.app.app_context()
        self.ctx.push()

    def tearDown(self):
        """Clean up after tests."""
        self.ctx.pop()

    @patch('backend.mail')
    def test_send_password_reset_email(self, mock_mail):
        """Test sending password reset email."""
        email = 'user@example.com'
        reset_token = 'test-token-123'
        
        send_password_reset_email(email, reset_token)
        
        # Verify email was sent
        mock_mail.send.assert_called_once()
        
        # Get the message that was sent
        sent_message = mock_mail.send.call_args[0][0]
        
        # Verify email properties
        self.assertEqual(sent_message.recipients, [email])
        self.assertIn('Password Reset', sent_message.subject)
        self.assertIn(reset_token, sent_message.html)
        self.assertIn(reset_token, sent_message.body)

    @patch('backend.mail')
    def test_send_badge_notification(self, mock_mail):
        """Test sending badge earned notification."""
        email = 'user@example.com'
        username = 'testuser'
        badge_name = 'Fresh Start'
        
        send_badge_notification(email, username, badge_name)
        
        # Verify email was sent
        mock_mail.send.assert_called_once()
        
        # Get the message
        sent_message = mock_mail.send.call_args[0][0]
        
        # Verify properties
        self.assertEqual(sent_message.recipients, [email])
        self.assertIn('Badge Unlocked', sent_message.subject)
        self.assertIn(badge_name, sent_message.subject)
        self.assertIn(username, sent_message.html)
        self.assertIn(badge_name, sent_message.html)

    @patch('backend.mail')
    def test_send_friend_request_notification(self, mock_mail):
        """Test sending friend request notification."""
        recipient_email = 'recipient@example.com'
        recipient_username = 'recipient'
        requester_username = 'requester'
        
        send_friend_request_notification(
            recipient_email,
            recipient_username,
            requester_username
        )
        
        # Verify email was sent
        mock_mail.send.assert_called_once()
        
        # Get the message
        sent_message = mock_mail.send.call_args[0][0]
        
        # Verify properties
        self.assertEqual(sent_message.recipients, [recipient_email])
        self.assertIn('friend request', sent_message.subject)
        self.assertIn(requester_username, sent_message.subject)
        self.assertIn(recipient_username, sent_message.html)
        self.assertIn(requester_username, sent_message.html)

    @patch('backend.mail')
    def test_send_friend_request_accepted_notification(self, mock_mail):
        """Test sending friend request accepted notification."""
        requester_email = 'requester@example.com'
        requester_username = 'requester'
        accepter_username = 'accepter'
        
        send_friend_request_accepted_notification(
            requester_email,
            requester_username,
            accepter_username
        )
        
        # Verify email was sent
        mock_mail.send.assert_called_once()
        
        # Get the message
        sent_message = mock_mail.send.call_args[0][0]
        
        # Verify properties
        self.assertEqual(sent_message.recipients, [requester_email])
        self.assertIn('accepted', sent_message.subject)
        self.assertIn(accepter_username, sent_message.subject)
        self.assertIn(requester_username, sent_message.html)
        self.assertIn(accepter_username, sent_message.html)

    @patch('backend.mail')
    def test_send_welcome_email(self, mock_mail):
        """Test sending welcome email."""
        email = 'newuser@example.com'
        username = 'newuser'
        
        send_welcome_email(email, username)
        
        # Verify email was sent
        mock_mail.send.assert_called_once()
        
        # Get the message
        sent_message = mock_mail.send.call_args[0][0]
        
        # Verify properties
        self.assertEqual(sent_message.recipients, [email])
        self.assertIn('Welcome', sent_message.subject)
        self.assertIn(username, sent_message.html)

    @patch('backend.mail')
    def test_email_contains_frontend_url(self, mock_mail):
        """Test that emails contain the configured frontend URL."""
        email = 'user@example.com'
        username = 'testuser'
        
        send_welcome_email(email, username)
        
        # Get the message
        sent_message = mock_mail.send.call_args[0][0]
        
        # Verify frontend URL is in the email
        self.assertIn('http://localhost:5173', sent_message.html)

    @patch('backend.mail')
    def test_email_has_plain_text_version(self, mock_mail):
        """Test that emails include plain text versions."""
        email = 'user@example.com'
        username = 'testuser'
        badge_name = 'Test Badge'
        
        send_badge_notification(email, username, badge_name)
        
        # Get the message
        sent_message = mock_mail.send.call_args[0][0]
        
        # Verify both HTML and plain text versions exist
        self.assertIsNotNone(sent_message.html)
        self.assertIsNotNone(sent_message.body)
        self.assertIn(badge_name, sent_message.body)


if __name__ == '__main__':
    unittest.main()
