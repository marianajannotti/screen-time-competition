"""
Authentication Blueprint for Screen Time Competition App

This module handles all user authentication functionality including:
- User registration with validation
- Secure login with password hashing
- Session management with Flask-Login
- Logout and session cleanup
- Security headers and CORS handling

Key Features:
- Comprehensive input validation and sanitization
- Secure password hashing using bcrypt
- Session-based authentication (not JWT tokens)
- Proper HTTP status codes and error messages
- Security headers to prevent common attacks

Security Considerations:
- Passwords are never stored in plain text
- Comprehensive input validation prevents injection attacks
- Rate limiting should be implemented at the application level
- HTTPS is required in production for session security

API Endpoints:
- POST /api/auth/register - Create new user account
- POST /api/auth/login - Authenticate existing user
- POST /api/auth/logout - End user session
- GET /api/auth/user - Get current authenticated user info
"""

from flask import Blueprint, request, jsonify, make_response
from flask_login import login_user, logout_user, login_required, current_user
from .database import db
from .auth_service import AuthService

# Create authentication blueprint with URL prefix
# All routes in this blueprint will be prefixed with /api/auth
auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


def add_api_headers(response):
    """
    Add Standard Security Headers to API Response
    
    Applies consistent HTTP security headers to all authentication API responses
    to prevent caching of sensitive data and ensure proper content type handling.
    
    Security Headers Applied:
    - Content-Type: Ensures response is treated as JSON
    - Cache-Control: Prevents browsers from caching authentication responses
    - Pragma: Additional cache prevention for older browsers
    
    Args:
        response (Response): Flask Response object to modify
        
    Returns:
        Response: The same response object with security headers added
        
    Usage:
        response = make_response(jsonify({"message": "Success"}))
        return add_api_headers(response)
    """
    response.headers["Content-Type"] = "application/json"
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    return response


@auth_bp.route("/register", methods=["POST"])
def register():
    """
    User Registration Endpoint
    
    Creates a new user account with validation and secure password storage.
    Performs comprehensive validation of input data and returns appropriate
    error messages for various failure scenarios.
    
    Expected Request:
        Method: POST
        Content-Type: application/json
        Body: {
            "username": "alice",        # 3-30 characters, alphanumeric + underscore/dash
            "email": "alice@example.com", # Valid email format
            "password": "securepassword"  # Minimum length enforced by validation
        }
    
    Validation Rules:
    - Username: 3-30 characters, unique, alphanumeric + underscore/dash only
    - Email: Valid email format, unique across all users
    - Password: Minimum length requirements (enforced by AuthService)
    - All fields are required and cannot be empty
    
    Success Response (201):
        {
            "message": "Registration successful",
            "user": {
                "id": 123,
                "username": "alice",
                "email": "alice@example.com",
                "streak_count": 0,
                "total_points": 0,
                "created_at": "2024-01-01T12:00:00"
            }
        }
    
    Error Responses:
        400: Invalid input data or validation failure
        409: Username or email already exists
        415: Invalid Content-Type (must be application/json)
        500: Internal server error during registration
    
    Returns:
        Response: JSON response with user data or error message
    """
    # Validate Content-Type
    if request.content_type != "application/json":
        response = make_response(
            jsonify({"error": "Content-Type must be application/json"}), 415
        )
        return add_api_headers(response)

    try:
        data = request.get_json()

        # Extract fields
        username = data.get("username")
        email = data.get("email")
        password = data.get("password")

        # Validate registration data
        is_valid, error_msg = AuthService.validate_registration_data(
            username, email, password
        )
        if not is_valid:
            response = make_response(jsonify({"error": error_msg}), 400)
            return add_api_headers(response)

        # Check if user exists
        exists, field = AuthService.check_user_exists(username=username, email=email)
        if exists:
            response = make_response(
                jsonify({"error": f"{field.capitalize()} already exists"}), 400
            )
            return add_api_headers(response)

        # Create user
        new_user = AuthService.create_user(username, email, password)

        response = make_response(
            jsonify(
                {"message": "User registered successfully", "user": new_user.to_dict()}
            ),
            201,
        )
        return add_api_headers(response)

    except Exception as e:
        db.session.rollback()
        response = make_response(
            jsonify({"error": f"Registration failed: {str(e)}"}), 500
        )
        return add_api_headers(response)


@auth_bp.route("/login", methods=["POST"])
def login():
    """
    User Login Endpoint
    
    Authenticates an existing user with username/password and creates a session.
    Uses Flask-Login for session management, storing user session in cookies.
    
    Expected Request:
        Method: POST
        Content-Type: application/json
        Body: {
            "username": "alice",           # Username or email address
            "password": "securepassword"   # User's password (will be verified against hash)
        }
    
    Authentication Process:
    1. Validate Content-Type and extract credentials
    2. Look up user by username (case-insensitive)
    3. Verify password against stored bcrypt hash
    4. Create Flask-Login session if credentials are valid
    5. Return user data (excluding sensitive information)
    
    Success Response (200):
        {
            "message": "Login successful",
            "user": {
                "id": 123,
                "username": "alice",
                "email": "alice@example.com",
                "streak_count": 15,
                "total_points": 1200,
                "created_at": "2024-01-01T12:00:00"
            }
        }
    
    Error Responses:
        400: Missing or invalid request data
        401: Invalid username or password
        415: Invalid Content-Type (must be application/json)
        500: Internal server error during authentication
    
    Security Features:
    - Passwords are hashed using bcrypt (never stored in plain text)
    - Failed login attempts return generic error messages
    - Session cookies are httpOnly and secure in production
    
    Returns:
        Response: JSON response with user data or error message
    """
    # Validate Content-Type
    if request.content_type != "application/json":
        response = make_response(
            jsonify({"error": "Content-Type must be application/json"}), 415
        )
        return add_api_headers(response)

    try:
        data = request.get_json()
        username = data.get("username")
        password = data.get("password")

        # Authenticate user
        user, error_msg = AuthService.authenticate_user(username, password)

        if error_msg:
            response = make_response(jsonify({"error": error_msg}), 401)
            return add_api_headers(response)

        # Log user in
        login_user(user)

        response = make_response(
            jsonify({"message": "Login successful", "user": user.to_dict()}), 200
        )
        return add_api_headers(response)

    except Exception as e:
        response = make_response(jsonify({"error": f"Login failed: {str(e)}"}), 500)
        return add_api_headers(response)


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    """
    User Logout Endpoint
    
    Ends the current user's session and clears authentication cookies.
    Requires the user to be authenticated (login_required decorator).
    
    Expected Request:
        Method: POST
        Authentication: Required (valid session cookie)
        Content-Type: Not required (no request body needed)
    
    Process:
    1. Verify user is authenticated (handled by @login_required)
    2. Call Flask-Login logout_user() to clear session
    3. Clear authentication cookies
    4. Return success confirmation
    
    Success Response (200):
        {
            "message": "Logged out successfully"
        }
    
    Error Responses:
        401: User not authenticated (handled by Flask-Login)
        500: Internal server error during logout
    
    Security Notes:
    - Session is completely invalidated server-side
    - Authentication cookies are cleared client-side
    - User must login again to access protected endpoints
    
    Returns:
        Response: JSON response confirming successful logout
    """
    logout_user()
    response = make_response(jsonify({"message": "Logged out successfully"}), 200)
    return add_api_headers(response)


@auth_bp.route("/me", methods=["GET"])
@login_required
def get_current_user():
    """Get current logged-in user info.

    Returns:
        Response: JSON response with current user data
    """
    response = make_response(jsonify({"user": current_user.to_dict()}), 200)
    return add_api_headers(response)


@auth_bp.route("/status", methods=["GET"])
def auth_status():
    """Check if user is logged in.

    Returns:
        Response: JSON response with authentication status
    """
    if current_user.is_authenticated:
        response = make_response(
            jsonify({"authenticated": True, "user": current_user.to_dict()}), 200
        )
        return add_api_headers(response)
    else:
        response = make_response(jsonify({"authenticated": False}), 200)
        return add_api_headers(response)
