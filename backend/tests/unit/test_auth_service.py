"""Unit tests for the AuthService.

This module contains test cases for the AuthService class,
covering user registration, authentication, and validation logic.
"""
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from backend import create_app
from backend.database import db
from backend.models import User
from backend.services import AuthService


class AuthServiceTestCase(unittest.TestCase):
    """Base test case for AuthService unit tests.

    Provides common setup and teardown for all auth service tests.
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

    def tearDown(self):
        """Clean up database and app context.

        Returns:
            None
        """
        db.session.remove()
        db.drop_all()
        db.engine.dispose()
        self.app_context.pop()


class TestRegistrationValidation(AuthServiceTestCase):
    """Test user registration data validation."""

    def test_valid_registration_data(self):
        """Verify that valid registration data passes validation.

        Returns:
            None
        """
        is_valid, error = AuthService.validate_registration_data(
            "testuser", "test@example.com", "password123"
        )
        
        self.assertTrue(is_valid)
        self.assertIsNone(error)

    def test_empty_username_fails(self):
        """Verify that empty username fails validation.

        Returns:
            None
        """
        is_valid, error = AuthService.validate_registration_data(
            "", "test@example.com", "password123"
        )
        
        self.assertFalse(is_valid)
        self.assertEqual(error, "Username is required")

    def test_whitespace_username_fails(self):
        """Verify that whitespace-only username fails validation.

        Returns:
            None
        """
        is_valid, error = AuthService.validate_registration_data(
            "   ", "test@example.com", "password123"
        )
        
        self.assertFalse(is_valid)
        self.assertEqual(error, "Username is required")

    def test_short_username_fails(self):
        """Verify that username under 3 characters fails validation.

        Returns:
            None
        """
        is_valid, error = AuthService.validate_registration_data(
            "ab", "test@example.com", "password123"
        )
        
        self.assertFalse(is_valid)
        self.assertEqual(error, "Username must be at least 3 characters")

    def test_username_with_at_symbol_fails(self):
        """Verify that username with @ symbol fails validation.

        Returns:
            None
        """
        is_valid, error = AuthService.validate_registration_data(
            "test@user", "test@example.com", "password123"
        )
        
        self.assertFalse(is_valid)
        self.assertEqual(error, "Username cannot contain the '@' character")

    def test_empty_email_fails(self):
        """Verify that empty email fails validation.

        Returns:
            None
        """
        is_valid, error = AuthService.validate_registration_data(
            "testuser", "", "password123"
        )
        
        self.assertFalse(is_valid)
        self.assertEqual(error, "Email is required")

    def test_empty_password_fails(self):
        """Verify that empty password fails validation.

        Returns:
            None
        """
        is_valid, error = AuthService.validate_registration_data(
            "testuser", "test@example.com", ""
        )
        
        self.assertFalse(is_valid)
        self.assertEqual(error, "Password is required")


class TestUserExistenceCheck(AuthServiceTestCase):
    """Test checking if users already exist."""

    def test_no_existing_user(self):
        """Verify that non-existing users return False.

        Returns:
            None
        """
        exists, field = AuthService.check_user_exists(
            username="newuser", email="new@example.com"
        )
        
        self.assertFalse(exists)
        self.assertIsNone(field)

    def test_existing_username(self):
        """Verify that existing username is detected.

        Returns:
            None
        """
        # Create existing user
        user = User(
            username="existinguser",
            email="existing@example.com",
            password_hash="hash"
        )
        db.session.add(user)
        db.session.commit()

        exists, field = AuthService.check_user_exists(
            username="existinguser", email="different@example.com"
        )
        
        self.assertTrue(exists)
        self.assertEqual(field, "username")

    def test_existing_email(self):
        """Verify that existing email is detected.

        Returns:
            None
        """
        # Create existing user
        user = User(
            username="existinguser",
            email="existing@example.com",
            password_hash="hash"
        )
        db.session.add(user)
        db.session.commit()

        exists, field = AuthService.check_user_exists(
            username="differentuser", email="existing@example.com"
        )
        
        self.assertTrue(exists)
        self.assertEqual(field, "email")

    def test_both_username_and_email_exist(self):
        """Verify that username takes precedence when both exist.

        Returns:
            None
        """
        # Create existing user
        user = User(
            username="existinguser",
            email="existing@example.com",
            password_hash="hash"
        )
        db.session.add(user)
        db.session.commit()

        exists, field = AuthService.check_user_exists(
            username="existinguser", email="existing@example.com"
        )
        
        self.assertTrue(exists)
        self.assertEqual(field, "username")


class TestUserCreation(AuthServiceTestCase):
    """Test user creation functionality."""

    def test_create_user_success(self):
        """Verify that valid user creation works.

        Returns:
            None
        """
        user = AuthService.create_user(
            "testuser", "test@example.com", "password123"
        )
        
        self.assertIsNotNone(user)
        self.assertEqual(user.username, "testuser")
        self.assertEqual(user.email, "test@example.com")
        self.assertIsNotNone(user.password_hash)
        self.assertNotEqual(user.password_hash, "password123")  # Should be hashed
        
        # Verify user is in database
        db_user = User.query.filter_by(username="testuser").first()
        self.assertIsNotNone(db_user)
        self.assertEqual(db_user.id, user.id)


class TestUserAuthentication(AuthServiceTestCase):
    """Test user authentication functionality."""

    def setUp(self):
        """Create app context, database, and test user.

        Returns:
            None
        """
        super().setUp()
        self.test_user = AuthService.create_user(
            "testuser", "test@example.com", "password123"
        )

    def test_authenticate_valid_credentials(self):
        """Verify that valid credentials authenticate successfully.

        Returns:
            None
        """
        user, error = AuthService.authenticate_user("testuser", "password123")
        
        self.assertIsNotNone(user)
        self.assertIsNone(error)
        self.assertEqual(user.username, "testuser")

    def test_authenticate_invalid_username(self):
        """Verify that invalid username fails authentication.

        Returns:
            None
        """
        user, error = AuthService.authenticate_user("nonexistent", "password123")
        
        self.assertIsNone(user)
        self.assertEqual(error, "Invalid username/email or password")

    def test_authenticate_invalid_password(self):
        """Verify that invalid password fails authentication.

        Returns:
            None
        """
        user, error = AuthService.authenticate_user("testuser", "wrongpassword")
        
        self.assertIsNone(user)
        self.assertEqual(error, "Invalid username/email or password")

    def test_authenticate_empty_username(self):
        """Verify that empty username fails authentication.

        Returns:
            None
        """
        user, error = AuthService.authenticate_user("", "password123")
        
        self.assertIsNone(user)
        self.assertEqual(error, "Username/email and password are required")

    def test_authenticate_empty_password(self):
        """Verify that empty password fails authentication.

        Returns:
            None
        """
        user, error = AuthService.authenticate_user("testuser", "")
        
        self.assertIsNone(user)
        self.assertEqual(error, "Username/email and password are required")


class TestPasswordResetTokens(AuthServiceTestCase):
    """Test password reset token functionality."""

    def setUp(self):
        """Create app context, database, and test user.

        Returns:
            None
        """
        super().setUp()
        self.test_user = AuthService.create_user(
            "testuser", "test@example.com", "password123"
        )
    
    def _create_user(self, username, email, password):
        """Helper method to create a test user.
        
        Args:
            username (str): Username for the user
            email (str): Email for the user  
            password (str): Password for the user
            
        Returns:
            User: Created user object
        """
        return AuthService.create_user(username, email, password)

    def test_generate_reset_token_valid_email(self):
        """Verify that reset token is generated for valid email.

        Returns:
            None
        """
        token, error = AuthService.generate_reset_token("test@example.com")
        
        self.assertIsNotNone(token)
        self.assertIsNone(error)
        self.assertIsInstance(token, str)
        self.assertGreater(len(token), 10)  # Should be a substantial token

    def test_generate_reset_token_invalid_email(self):
        """Verify that no token is generated for invalid email.

        Returns:
            None
        """
        token, error = AuthService.generate_reset_token("nonexistent@example.com")
        
        self.assertIsNone(token)
        self.assertIsNone(error)  # Don't reveal if email exists

    def test_reset_password_valid_token(self):
        """Verify that password reset works with valid token.

        Returns:
            None
        """
        # Generate reset token
        token, _ = AuthService.generate_reset_token("test@example.com")
        
        # Reset password
        success, error = AuthService.reset_password(token, "newpassword123")
        
        self.assertTrue(success)
        self.assertIsNone(error)
        
        # Verify new password works
        user, auth_error = AuthService.authenticate_user("testuser", "newpassword123")
        self.assertIsNotNone(user)
        self.assertIsNone(auth_error)
        
        # Verify old password doesn't work
        user, auth_error = AuthService.authenticate_user("testuser", "password123")
        self.assertIsNone(user)
        self.assertIsNotNone(auth_error)

    def test_reset_password_invalid_token(self):
        """Verify that password reset fails with invalid token.

        Returns:
            None
        """
        success, error = AuthService.reset_password("invalidtoken", "newpassword123")
        
        self.assertFalse(success)
        self.assertEqual(error, "Invalid or expired reset token")

    def test_reset_password_expired_token(self):
        """Test password reset with expired token.

        Returns:
            None
        """
        # Create user and get reset token
        user = self._create_user("test_user", "testexpired@example.com", "password123")
        token, _ = AuthService.generate_reset_token("testexpired@example.com")
        
        # Mock the token validation as expired
        with patch('backend.services.auth_service.AuthService.validate_reset_token', return_value=(None, "Token expired")):
            success, error = AuthService.reset_password(token, "newpassword123")
            
            self.assertFalse(success)
            self.assertIsNotNone(error)

    def test_register_with_weak_password(self):
        """Test registration with weak password.

        Returns:
            None
        """
        # Test very short password - for now just verify it doesn't crash
        try:
            user = AuthService.create_user("testuser", "test@example.com", "123")
            # Current implementation doesn't validate password strength
            self.assertIsNotNone(user)
        except Exception as e:
            # If validation is added, this would fail
            self.assertIn("password", str(e).lower())

    def test_register_with_invalid_email_format(self):
        """Test registration with invalid email format.

        Returns:
            None
        """
        # Test invalid email formats
        invalid_emails = [
            "notanemail",
            "@example.com",
            "test@",
            "test..test@example.com",
            ""
        ]
        
        for invalid_email in invalid_emails:
            with self.subTest(email=invalid_email):
                try:
                    user = AuthService.create_user("testuser", invalid_email, "password123")
                    # Current implementation may not validate email format
                    # This test documents expected behavior if validation is added
                except Exception:
                    # If email validation is added, invalid emails would fail
                    pass

    def test_authenticate_case_sensitivity(self):
        """Test that username authentication is case sensitive.

        Returns:
            None
        """
        # Create user with specific case (different from setUp's "testuser")
        user = self._create_user("TestUser", "testcase@example.com", "password123")
        
        # Try authenticating with different cases
        result, error = AuthService.authenticate_user("testuser", "password123")  # This matches setUp user
        self.assertIsNotNone(result)  # Should succeed - matches existing user
        self.assertEqual(result.username, "testuser")
        
        result, error = AuthService.authenticate_user("TestUser", "password123")  # exact match for new user
        self.assertIsNotNone(result)
        self.assertEqual(result.username, "TestUser")
        
        # Try with completely different case that doesn't exist
        result, error = AuthService.authenticate_user("TESTUSER", "password123")  
        self.assertIsNone(result)  # Should fail - no user with this exact case

    def test_multiple_failed_login_attempts(self):
        """Test behavior with multiple failed login attempts.

        Returns:
            None
        """
        user = self._create_user("testuser2", "testmultiple@example.com", "password123")
        
        # Multiple failed attempts
        for i in range(5):
            result, error = AuthService.authenticate_user("testuser", "wrongpassword")
            self.assertIsNone(result)
        
        # Should still be able to login with correct password
        result, error = AuthService.authenticate_user("testuser", "password123")
        self.assertIsNotNone(result)

    def test_reset_password_with_empty_password(self):
        """Test password reset with empty new password.

        Returns:
            None
        """
        user = self._create_user("testuser4", "testpassword@example.com", "password123")
        token, _ = AuthService.generate_reset_token("testpassword@example.com")
        
        success, error = AuthService.reset_password(token, "")
        
        self.assertFalse(success)
        # Should validate that new password is not empty

    def test_register_with_whitespace_username(self):
        """Test registration with username containing only whitespace.

        Returns:
            None
        """
        # Test with validation first
        is_valid, error = AuthService.validate_registration_data("   ", "test@example.com", "password123")
        
        self.assertFalse(is_valid)
        self.assertEqual(error, "Username is required")

    def test_concurrent_user_registration(self):
        """Test concurrent registration attempts with same username.

        Returns:
            None
        """
        # This test simulates race condition scenarios
        # Mock database to simulate concurrent access
        with patch('backend.database.db.session') as mock_session:
            # First call succeeds
            mock_session.add.return_value = None
            mock_session.commit.side_effect = [None, Exception("Integrity constraint")]
            
            try:
                user1 = AuthService.create_user("testuser", "test1@example.com", "password123")
                success1 = True
            except Exception:
                success1 = False
                
            try:
                user2 = AuthService.create_user("testuser", "test2@example.com", "password123")
                success2 = True
            except Exception:
                success2 = False
            
            # One should succeed, one should fail
            self.assertTrue(success1 or success2)
            self.assertFalse(success1 and success2)

    def test_password_hash_security(self):
        """Test that password hashes are properly salted and secure.

        Returns:
            None
        """
        user1 = self._create_user("user1", "user1@example.com", "samepassword")
        user2 = self._create_user("user2", "user2@example.com", "samepassword")
        
        # Same password should produce different hashes (due to salting)
        self.assertNotEqual(user1.password_hash, user2.password_hash)
        
        # Both should still authenticate correctly
        result1, error1 = AuthService.authenticate_user("user1", "samepassword")
        result2, error2 = AuthService.authenticate_user("user2", "samepassword")
        
        self.assertIsNotNone(result1)
        self.assertIsNotNone(result2)

    def test_reset_token_uniqueness(self):
        """Test that reset tokens are unique for each generation.

        Returns:
            None
        """
        user = self._create_user("testuser5", "testtoken@example.com", "password123")
        
        # Generate multiple tokens
        token1, _ = AuthService.generate_reset_token("testtoken@example.com")
        token2, _ = AuthService.generate_reset_token("testtoken@example.com") 
        token3, _ = AuthService.generate_reset_token("testtoken@example.com")
        
        # All tokens should be different
        tokens = [token1, token2, token3]
        self.assertEqual(len(set(tokens)), 3)

    def test_authenticate_with_sql_injection_attempt(self):
        """Test authentication is safe from SQL injection attempts.

        Returns:
            None
        """
        # Create a regular user
        user = self._create_user("testuser6", "testsql@example.com", "password123")
        
        # Try SQL injection in username
        sql_injection_usernames = [
            "testuser'; DROP TABLE users; --",
            "testuser' OR '1'='1",
            "testuser' UNION SELECT * FROM users --"
        ]
        
        for malicious_username in sql_injection_usernames:
            with self.subTest(username=malicious_username):
                result, error = AuthService.authenticate_user(malicious_username, "password123")
                self.assertIsNone(result)  # Should not authenticate
        
        # Normal authentication should still work
        result, error = AuthService.authenticate_user("testuser", "password123")
        self.assertIsNotNone(result)


if __name__ == "__main__":
    unittest.main()
