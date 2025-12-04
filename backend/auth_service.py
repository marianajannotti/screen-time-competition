"""
Authentication Service Layer
Handles all authentication business logic separate from HTTP routes
"""

import secrets
from datetime import datetime, timedelta
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

        username_clean = username.strip()
        
        if not email or not email.strip():
            return False, "Email is required"
        
        if not password:
            return False, "Password is required"
        
        # Additional validation
        if len(username_clean) < 3:
            return False, "Username must be at least 3 characters"

        if "@" in username_clean:
            return False, "Username cannot contain the '@' character"
        
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
    def authenticate_user(identifier, password):
        """Authenticate a user with username or email plus password.

        Args:
            identifier (str): Username or email provided by the client.
            password (str): Plain text password to verify.

        Returns:
            tuple: (User or None, str or None)
                Returns (User, None) if authentication succeeds.
                Returns (None, error_message) if authentication fails.
        """

        if not identifier or not password:
            return None, "Username/email and password are required"

        identifier = identifier.strip()
        if "@" in identifier:
            user = User.query.filter_by(email=identifier.lower()).first()
        else:
            user = User.query.filter_by(username=identifier).first()

        if not user or not check_password_hash(user.password_hash, password):
            return None, "Invalid username/email or password"

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

    @staticmethod
    def generate_reset_token(email):
        """Generate a password reset token for a user.
        
        Args:
            email (str): User's email address
            
        Returns:
            tuple: (str or None, str or None) - (reset_token, error_message)
                   Returns (token, None) if successful
                   Returns (None, error_message) if user not found
        """
        user = AuthService.get_user_by_email(email)
        
        if not user:
            # Don't reveal if email exists (security best practice)
            return None, None
        
        # Generate secure random token
        reset_token = secrets.token_urlsafe(32)
        
        # Set token expiry to 30 minutes from now
        expiry = datetime.utcnow() + timedelta(minutes=30)
        
        # Save token to database
        user.reset_token = reset_token
        user.reset_token_expiry = expiry
        db.session.commit()
        
        return reset_token, None

    @staticmethod
    def validate_reset_token(token):
        """Validate a password reset token.
        
        Args:
            token (str): Reset token to validate
            
        Returns:
            tuple: (User or None, str or None) - (user, error_message)
                   Returns (User, None) if token is valid
                   Returns (None, error_message) if token is invalid/expired
        """
        if not token:
            return None, "Reset token is required"
        
        # Find user with this token
        user = User.query.filter_by(reset_token=token).first()
        
        if not user:
            return None, "Invalid or expired reset token"
        
        # Check if token has expired
        if user.reset_token_expiry < datetime.utcnow():
            # Clear expired token
            user.reset_token = None
            user.reset_token_expiry = None
            db.session.commit()
            return None, "Reset token has expired"
        
        return user, None

    @staticmethod
    def reset_password(token, new_password):
        """Reset user's password using a valid token.
        
        Args:
            token (str): Valid reset token
            new_password (str): New password to set
            
        Returns:
            tuple: (bool, str or None) - (success, error_message)
                   Returns (True, None) if successful
                   Returns (False, error_message) if failed
        """
        # Validate token
        user, error = AuthService.validate_reset_token(token)
        
        if error:
            return False, error
        
        # Validate new password
        if not new_password or len(new_password) < 6:
            return False, "Password must be at least 6 characters"
        
        # Hash and update password
        user.password_hash = generate_password_hash(new_password)
        
        # Clear reset token (single-use)
        user.reset_token = None
        user.reset_token_expiry = None
        
        db.session.commit()
        
        return True, None
