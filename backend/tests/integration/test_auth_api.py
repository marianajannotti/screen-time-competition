"""Integration tests for the Auth API endpoints.

This module contains integration test cases for the authentication API,
covering user registration, login, logout, and password reset functionality.
"""
import unittest
import json
from unittest.mock import patch, MagicMock

from backend import create_app
from backend.database import db
from backend.models import User


class AuthAPIIntegrationTestCase(unittest.TestCase):
    """Integration test case for Auth API endpoints.

    Provides common setup and teardown for all auth API integration tests.
    """

    def setUp(self):
        """Create app, client, database, and test fixtures.

        Returns:
            None
        """
        self.app = create_app("testing")
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Test user data
        self.test_user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword123"
        }

        # Create a test user for login tests
        from werkzeug.security import generate_password_hash
        self.existing_user = User(
            username="existing",
            email="existing@example.com",
            password_hash=generate_password_hash("existingpassword")
        )
        db.session.add(self.existing_user)
        db.session.commit()

    def tearDown(self):
        """Clean up database and app context.

        Returns:
            None
        """
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_register_success(self):
        """Test successful user registration.

        Returns:
            None
        """
        response = self.client.post(
            "/api/auth/register",
            data=json.dumps(self.test_user_data),
            content_type="application/json"
        )

        self.assertEqual(response.status_code, 201)
        response_data = json.loads(response.data)
        self.assertEqual(response_data["message"], "User registered successfully")
        self.assertIn("user", response_data)
        self.assertEqual(response_data["user"]["username"], self.test_user_data["username"])
        self.assertEqual(response_data["user"]["email"], self.test_user_data["email"])
        self.assertNotIn("password", response_data["user"])

    def test_register_invalid_content_type(self):
        """Test registration with invalid content type.

        Returns:
            None
        """
        response = self.client.post(
            "/api/auth/register",
            data="invalid data",
            content_type="text/plain"
        )

        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.data)
        self.assertEqual(response_data["error"], "Content-Type must be application/json")

    def test_register_missing_fields(self):
        """Test registration with missing required fields.

        Returns:
            None
        """
        incomplete_data = {
            "username": "testuser"
            # Missing email and password
        }

        response = self.client.post(
            "/api/auth/register",
            data=json.dumps(incomplete_data),
            content_type="application/json"
        )

        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.data)
        self.assertEqual(response_data["error"], "Missing required fields")

    def test_register_duplicate_username(self):
        """Test registration with duplicate username.

        Returns:
            None
        """
        # Use existing user's username
        duplicate_data = self.test_user_data.copy()
        duplicate_data["username"] = self.existing_user.username
        duplicate_data["email"] = "different@example.com"

        response = self.client.post(
            "/api/auth/register",
            data=json.dumps(duplicate_data),
            content_type="application/json"
        )

        self.assertEqual(response.status_code, 409)
        response_data = json.loads(response.data)
        self.assertEqual(response_data["error"], "Username already exists")

    def test_register_duplicate_email(self):
        """Test registration with duplicate email.

        Returns:
            None
        """
        # Use existing user's email
        duplicate_data = self.test_user_data.copy()
        duplicate_data["username"] = "different"
        duplicate_data["email"] = self.existing_user.email

        response = self.client.post(
            "/api/auth/register",
            data=json.dumps(duplicate_data),
            content_type="application/json"
        )

        self.assertEqual(response.status_code, 409)
        response_data = json.loads(response.data)
        self.assertEqual(response_data["error"], "Email already exists")

    def test_login_success(self):
        """Test successful user login.

        Returns:
            None
        """
        login_data = {
            "username": self.existing_user.username,
            "password": "existingpassword"
        }

        response = self.client.post(
            "/api/auth/login",
            data=json.dumps(login_data),
            content_type="application/json"
        )

        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data)
        self.assertEqual(response_data["message"], "Login successful")
        self.assertIn("user", response_data)
        self.assertEqual(response_data["user"]["username"], self.existing_user.username)

    def test_login_invalid_credentials(self):
        """Test login with invalid credentials.

        Returns:
            None
        """
        login_data = {
            "username": self.existing_user.username,
            "password": "wrongpassword"
        }

        response = self.client.post(
            "/api/auth/login",
            data=json.dumps(login_data),
            content_type="application/json"
        )

        self.assertEqual(response.status_code, 401)
        response_data = json.loads(response.data)
        self.assertEqual(response_data["error"], "Invalid username or password")

    def test_login_nonexistent_user(self):
        """Test login with nonexistent username.

        Returns:
            None
        """
        login_data = {
            "username": "nonexistent",
            "password": "password"
        }

        response = self.client.post(
            "/api/auth/login",
            data=json.dumps(login_data),
            content_type="application/json"
        )

        self.assertEqual(response.status_code, 401)
        response_data = json.loads(response.data)
        self.assertEqual(response_data["error"], "Invalid username or password")

    def test_login_missing_fields(self):
        """Test login with missing required fields.

        Returns:
            None
        """
        incomplete_data = {
            "username": "testuser"
            # Missing password
        }

        response = self.client.post(
            "/api/auth/login",
            data=json.dumps(incomplete_data),
            content_type="application/json"
        )

        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.data)
        self.assertEqual(response_data["error"], "Missing username or password")

    def test_logout_success(self):
        """Test successful user logout.

        Returns:
            None
        """
        # First login
        with self.client.session_transaction() as sess:
            sess['_user_id'] = str(self.existing_user.id)
            sess['_fresh'] = True

        response = self.client.post("/api/auth/logout")

        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data)
        self.assertEqual(response_data["message"], "Logout successful")

    def test_logout_not_logged_in(self):
        """Test logout when not logged in.

        Returns:
            None
        """
        response = self.client.post("/api/auth/logout")

        # Should still return success (Flask-Login behavior)
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data)
        self.assertEqual(response_data["message"], "Logout successful")

    def test_current_user_authenticated(self):
        """Test getting current user info when authenticated.

        Returns:
            None
        """
        # Login first
        with self.client.session_transaction() as sess:
            sess['_user_id'] = str(self.existing_user.id)
            sess['_fresh'] = True

        response = self.client.get("/api/auth/current_user")

        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data)
        self.assertIn("user", response_data)
        self.assertEqual(response_data["user"]["username"], self.existing_user.username)

    def test_current_user_not_authenticated(self):
        """Test getting current user info when not authenticated.

        Returns:
            None
        """
        response = self.client.get("/api/auth/current_user")

        self.assertEqual(response.status_code, 401)
        response_data = json.loads(response.data)
        self.assertEqual(response_data["error"], "Not authenticated")

    @patch('backend.services.email_service.send_password_reset_email')
    def test_forgot_password_success(self, mock_send_email):
        """Test successful password reset request.

        Args:
            mock_send_email: Mock for email sending function

        Returns:
            None
        """
        reset_data = {
            "email": self.existing_user.email
        }

        response = self.client.post(
            "/api/auth/forgot-password",
            data=json.dumps(reset_data),
            content_type="application/json"
        )

        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data)
        self.assertEqual(response_data["message"], "Password reset email sent")
        mock_send_email.assert_called_once()

    def test_forgot_password_nonexistent_email(self):
        """Test password reset request with nonexistent email.

        Returns:
            None
        """
        reset_data = {
            "email": "nonexistent@example.com"
        }

        response = self.client.post(
            "/api/auth/forgot-password",
            data=json.dumps(reset_data),
            content_type="application/json"
        )

        self.assertEqual(response.status_code, 404)
        response_data = json.loads(response.data)
        self.assertEqual(response_data["error"], "Email not found")

    def test_forgot_password_missing_email(self):
        """Test password reset request with missing email.

        Returns:
            None
        """
        response = self.client.post(
            "/api/auth/forgot-password",
            data=json.dumps({}),
            content_type="application/json"
        )

        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.data)
        self.assertEqual(response_data["error"], "Email is required")

    def test_reset_password_success(self):
        """Test successful password reset with valid token.

        Returns:
            None
        """
        # Generate reset token for existing user using AuthService
        from backend.services import AuthService
        reset_token, _ = AuthService.generate_reset_token(self.existing_user.email)

        reset_data = {
            "token": reset_token,
            "password": "newpassword123"
        }

        response = self.client.post(
            "/api/auth/reset-password",
            data=json.dumps(reset_data),
            content_type="application/json"
        )

        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data)
        self.assertEqual(response_data["message"], "Password reset successful")

        # Verify password was actually changed by trying to login with new password
        login_response = self.client.post(
            "/api/auth/login",
            data=json.dumps({
                "username": self.existing_user.username,
                "password": "newpassword123"
            }),
            content_type="application/json"
        )
        self.assertEqual(login_response.status_code, 200)

    def test_reset_password_invalid_token(self):
        """Test password reset with invalid token.

        Returns:
            None
        """
        reset_data = {
            "token": "invalid_token",
            "password": "newpassword123"
        }

        response = self.client.post(
            "/api/auth/reset-password",
            data=json.dumps(reset_data),
            content_type="application/json"
        )

        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.data)
        self.assertEqual(response_data["error"], "Invalid or expired reset token")

    def test_reset_password_missing_fields(self):
        """Test password reset with missing required fields.

        Returns:
            None
        """
        incomplete_data = {
            "token": "some_token"
            # Missing password
        }

        response = self.client.post(
            "/api/auth/reset-password",
            data=json.dumps(incomplete_data),
            content_type="application/json"
        )

        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.data)
        self.assertEqual(response_data["error"], "Token and password are required")


if __name__ == '__main__':
    unittest.main()
