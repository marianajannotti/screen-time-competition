"""Test configuration and utilities for the backend tests.

This module provides common test configuration, fixtures, and utilities
that can be shared across all test modules.
"""
import unittest
import tempfile
import os
from unittest.mock import MagicMock

from backend import create_app
from backend.database import db
from backend.models import User


class BaseTestCase(unittest.TestCase):
    """Base test case class with common setup and utilities.
    
    This class provides common functionality for all test cases including:
    - App and database setup
    - Test user creation
    - Common assertions
    - Cleanup utilities
    """

    def setUp(self):
        """Set up test environment with app context and clean database.
        
        Returns:
            None
        """
        # Create temporary database file
        self.db_fd, self.db_path = tempfile.mkstemp()
        
        # Create app with test configuration
        self.app = create_app("testing")
        self.app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{self.db_path}'
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.app.config['SECRET_KEY'] = 'test-secret-key'
        
        # Set up app context
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # Create all database tables
        db.create_all()
        
        # Create test client
        self.client = self.app.test_client()

    def tearDown(self):
        """Clean up test environment.
        
        Returns:
            None
        """
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def create_test_user(self, username="testuser", email="test@example.com", password="testpassword"):
        """Create and return a test user.
        
        Args:
            username (str): Username for the test user
            email (str): Email for the test user  
            password (str): Password for the test user
            
        Returns:
            User: The created test user
        """
        from werkzeug.security import generate_password_hash
        user = User(
            username=username, 
            email=email,
            password_hash=generate_password_hash(password)
        )
        db.session.add(user)
        db.session.commit()
        return user

    def login_user(self, user, password="testpassword"):
        """Log in a user via the test client.
        
        Args:
            user (User): The user to log in
            password (str): The user's password
            
        Returns:
            bool: True if login was successful, False otherwise
        """
        response = self.client.post('/api/auth/login', json={
            'username': user.username,
            'password': password
        })
        return response.status_code == 200

    def assert_json_response(self, response, expected_status=200, expected_keys=None):
        """Assert that a response is valid JSON with expected status and keys.
        
        Args:
            response: Flask test response
            expected_status (int): Expected HTTP status code
            expected_keys (list): List of keys that should be present in JSON
            
        Returns:
            dict: The parsed JSON response data
        """
        self.assertEqual(response.status_code, expected_status)
        self.assertEqual(response.content_type, 'application/json')
        
        import json
        data = json.loads(response.data)
        
        if expected_keys:
            for key in expected_keys:
                self.assertIn(key, data)
        
        return data

    def assert_error_response(self, response, expected_status=400, expected_error_message=None):
        """Assert that a response is an error with expected status and message.
        
        Args:
            response: Flask test response
            expected_status (int): Expected HTTP status code
            expected_error_message (str): Expected error message
            
        Returns:
            dict: The parsed JSON response data
        """
        data = self.assert_json_response(response, expected_status, ['error'])
        
        if expected_error_message:
            self.assertEqual(data['error'], expected_error_message)
        
        return data


class MockDatabaseTestCase(unittest.TestCase):
    """Base test case for mocking database operations.
    
    This class provides utilities for testing service classes with mocked
    database operations, useful for pure unit tests.
    """

    def setUp(self):
        """Set up mocks for database operations.
        
        Returns:
            None
        """
        # Create mock app context
        self.mock_app = MagicMock()
        self.mock_app_context = MagicMock()
        self.mock_app.app_context.return_value = self.mock_app_context

        # Mock database session
        self.mock_db_session = MagicMock()
        self.mock_db = MagicMock()
        self.mock_db.session = self.mock_db_session

    def create_mock_user(self, user_id=1, username="testuser", email="test@example.com"):
        """Create a mock user object.
        
        Args:
            user_id (int): User ID
            username (str): Username
            email (str): Email
            
        Returns:
            MagicMock: Mock user object with specified attributes
        """
        mock_user = MagicMock()
        mock_user.id = user_id
        mock_user.username = username
        mock_user.email = email
        mock_user.check_password.return_value = True
        return mock_user


# Test discovery helper
def create_test_suite():
    """Create a test suite containing all backend tests.
    
    Returns:
        unittest.TestSuite: Test suite with all test cases
    """
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Unit tests
    from backend.tests.unit import (
        test_auth_service,
        test_badge_service,
        test_badge_achievement_service,
        test_email_service,
        test_friendship_service,
        test_leaderboard_service,
        test_screen_time_service,
        test_streak_service
    )
    
    # Integration tests  
    from backend.tests.integration import (
        test_auth_api,
        test_badges_api,
        test_friendship,
        test_leaderboard,
        test_screen_time
    )
    
    # Add unit test modules
    unit_modules = [
        test_auth_service,
        test_badge_service, 
        test_badge_achievement_service,
        test_email_service,
        test_friendship_service,
        test_leaderboard_service,
        test_screen_time_service,
        test_streak_service
    ]
    
    for module in unit_modules:
        suite.addTests(loader.loadTestsFromModule(module))
    
    # Add integration test modules
    integration_modules = [
        test_auth_api,
        test_badges_api,
        test_friendship,
        test_leaderboard,
        test_screen_time
    ]
    
    for module in integration_modules:
        suite.addTests(loader.loadTestsFromModule(module))
    
    return suite


if __name__ == '__main__':
    # Run all tests
    runner = unittest.TextTestRunner(verbosity=2)
    suite = create_test_suite()
    runner.run(suite)
