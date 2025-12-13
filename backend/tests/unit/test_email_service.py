"""Unit tests for the EmailService.

This module contains test cases for the email service functions,
covering password reset email sending functionality.
"""
import unittest
from unittest.mock import patch, MagicMock
from flask import Flask

from backend import create_app
from backend.services.email_service import send_password_reset_email


class EmailServiceTestCase(unittest.TestCase):
    """Base test case for EmailService unit tests.

    Provides common setup and teardown for all email service tests.
    """

    def setUp(self):
        """Create app context and test fixtures.

        Returns:
            None
        """
        self.app = create_app("testing")
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # Test data
        self.test_email = "test@example.com"
        self.test_token = "test_reset_token_123"

    def tearDown(self):
        """Clean up app context.

        Returns:
            None
        """
        self.app_context.pop()

    @patch('backend.mail')
    @patch('backend.services.email_service.render_template')
    def test_send_password_reset_email_success(self, mock_render_template, mock_mail):
        """Test successful password reset email sending.

        Args:
            mock_render_template: Mock for render_template function
            mock_mail: Mock for mail object

        Returns:
            None
        """
        # Setup mocks
        mock_render_template.side_effect = lambda template, **kwargs: f"rendered_{template}"
        mock_mail.send = MagicMock()

        # Execute
        send_password_reset_email(self.test_email, self.test_token)

        # Verify mail was sent
        mock_mail.send.assert_called_once()
        
        # Verify templates were rendered
        self.assertEqual(mock_render_template.call_count, 2)  # HTML and text templates

    @patch('backend.mail')
    @patch('backend.services.email_service.render_template')
    def test_send_password_reset_email_with_templates(self, mock_render_template, mock_mail):
        """Test password reset email with HTML and text templates.

        Args:
            mock_render_template: Mock for render_template function
            mock_mail: Mock for mail object

        Returns:
            None
        """
        # Setup mocks
        mock_render_template.side_effect = lambda template, **kwargs: f"rendered_{template}"
        mock_mail.send = MagicMock()

        # Execute
        send_password_reset_email(self.test_email, self.test_token)

        # Verify templates were rendered with correct context
        expected_calls = [
            unittest.mock.call('emails/password_reset.html', 
                             reset_url=f"http://localhost:5173/reset-password?token={self.test_token}"),
            unittest.mock.call('emails/password_reset.txt', 
                             reset_url=f"http://localhost:5173/reset-password?token={self.test_token}")
        ]
        mock_render_template.assert_has_calls(expected_calls, any_order=False)

    @patch('backend.services.email_service.current_app')
    @patch('backend.mail')
    def test_send_password_reset_email_custom_frontend_url(self, mock_mail, mock_current_app):
        """Test password reset email with custom frontend URL.

        Args:
            mock_mail: Mock for mail object
            mock_current_app: Mock for current_app

        Returns:
            None
        """
        # Setup mocks
        custom_url = "https://myapp.com"
        mock_current_app.config.get.return_value = custom_url
        mock_mail.send = MagicMock()

        # Execute
        send_password_reset_email(self.test_email, self.test_token)

        # Verify custom URL was used
        mock_current_app.config.get.assert_called_with("FRONTEND_URL", "http://localhost:5173")

    @patch('backend.mail')
    def test_send_password_reset_email_failure(self, mock_mail):
        """Test password reset email sending failure.

        Args:
            mock_mail: Mock for mail object that raises exception

        Returns:
            None
        """
        # Setup mock to raise exception
        mock_mail.send.side_effect = Exception("Mail server error")

        # Execute and verify exception is raised
        with self.assertRaises(Exception) as context:
            send_password_reset_email(self.test_email, self.test_token)

        self.assertEqual(str(context.exception), "Mail server error")

    @patch('backend.mail')
    def test_send_password_reset_email_with_special_token(self, mock_mail):
        """Test password reset email with special characters in token.

        Args:
            mock_mail: Mock for mail object

        Returns:
            None
        """
        # Setup mock
        mock_mail.send = MagicMock()
        
        special_token = "special.token.with.dots"
        
        # Execute - should not raise an exception
        send_password_reset_email(self.test_email, special_token)
        
        # Verify it completed successfully
        mock_mail.send.assert_called_once()

    @patch('backend.mail')  
    def test_send_password_reset_email_basic_functionality(self, mock_mail):
        """Test basic password reset email functionality.

        Args:
            mock_mail: Mock for mail object

        Returns:
            None
        """
        # Setup mock
        mock_mail.send = MagicMock()
        
        # Execute with various inputs
        test_cases = [
            ("user@example.com", "normal_token"),
            ("test.email+tag@domain.co.uk", "token_with_special_chars_123"),
            ("simple@test.com", "")  # Empty token
        ]
        
        for email, token in test_cases:
            with self.subTest(email=email, token=token):
                # Should not raise an exception
                send_password_reset_email(email, token)
                
        # Verify send was called for each test case
        self.assertEqual(mock_mail.send.call_count, len(test_cases))


if __name__ == '__main__':
    unittest.main()
