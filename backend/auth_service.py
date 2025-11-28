"""
Authentication Service Layer
Handles all authentication business logic separate from HTTP routes
"""

from werkzeug.security import generate_password_hash, check_password_hash
from .database import db
from .models import User


class AuthService:
    """Service class for authentication operations.
    
    Handles user registration, login validation, and user management
    without direct coupling to Flask routes.
    """

    @staticmethod
    def validate_registration_data(username, email, password):
        """Validate user registration data.
        
        Args:
            username (str): Desired username
            email (str): User's email address
            password (str): User's password
            
        Returns:
            tuple: (bool, str) - (is_valid, error_message)
                   Returns (True, None) if valid
                   Returns (False, error_message) if invalid
        """
        if not username or not username.strip():
            return False, "Username is required"
        
        if not email or not email.strip():
            return False, "Email is required"
        
        if not password:
            return False, "Password is required"
        
        # Additional validation
        if len(username.strip()) < 3:
            return False, "Username must be at least 3 characters"
        
        if len(password) < 6:
            return False, "Password must be at least 6 characters"
        
        if "@" not in email or "." not in email:
            return False, "Invalid email format"
        
        return True, None

    @staticmethod
    def check_user_exists(username=None, email=None):
        """Check if a user already exists by username or email.
        
        Args:
            username (str, optional): Username to check
            email (str, optional): Email to check
            
        Returns:
            tuple: (bool, str) - (exists, field_name)
                   Returns (True, 'username') if username exists
                   Returns (True, 'email') if email exists
                   Returns (False, None) if neither exists
        """
        if username:
            if User.query.filter_by(username=username.strip()).first():
                return True, "username"
        
        if email:
            if User.query.filter_by(email=email.strip().lower()).first():
                return True, "email"
        
        return False, None

    @staticmethod
    def create_user(username, email, password):
        """Create a new user account.
        
        Args:
            username (str): Username for the new account
            email (str): Email address for the new account
            password (str): Plain text password (will be hashed)
            
        Returns:
            User: The newly created User object
            
        Raises:
            Exception: If database commit fails
        """
        # Normalize inputs
        username = username.strip()
        email = email.strip().lower()
        
        # Hash password
        password_hash = generate_password_hash(password)
        
        # Create user object
        new_user = User(
            username=username,
            email=email,
            password_hash=password_hash
        )
        
        # Save to database
        db.session.add(new_user)
        db.session.commit()
        
        return new_user

    @staticmethod
    def authenticate_user(username, password):
        """Authenticate a user with username and password.
        
        Args:
            username (str): Username to authenticate
            password (str): Plain text password to verify
            
        Returns:
            tuple: (User or None, str or None)
                   Returns (User, None) if authentication successful
                   Returns (None, error_message) if authentication failed
        """
        if not username or not password:
            return None, "Username and password are required"
        
        # Find user
        user = User.query.filter_by(username=username.strip()).first()
        
        if not user:
            return None, "Invalid username or password"
        
        # Verify password
        if not check_password_hash(user.password_hash, password):
            return None, "Invalid username or password"
        
        return user, None

    @staticmethod
    def get_user_by_id(user_id):
        """Get a user by their ID.
        
        Args:
            user_id (int): The user's ID
            
        Returns:
            User or None: The User object if found, None otherwise
        """
        return User.query.get(user_id)

    @staticmethod
    def get_user_by_username(username):
        """Get a user by their username.
        
        Args:
            username (str): The username to search for
            
        Returns:
            User or None: The User object if found, None otherwise
        """
        return User.query.filter_by(username=username.strip()).first()

    @staticmethod
    def get_user_by_email(email):
        """Get a user by their email address.
        
        Args:
            email (str): The email address to search for
            
        Returns:
            User or None: The User object if found, None otherwise
        """
        return User.query.filter_by(email=email.strip().lower()).first()
