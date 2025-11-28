"""
Authentication Blueprint for Screen Time Competition
Handles user registration, login, logout
"""

from flask import Blueprint, request, jsonify, make_response
from flask_login import login_user, logout_user, login_required, current_user
from .database import db
from .auth_service import AuthService
from .utils import add_api_headers

# Create blueprint
auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.route("/register", methods=["POST"])
def register():
    """Register a new user.

    Expected JSON:
    {
        "username": "alice",
        "email": "alice@example.com",
        "password": "securepassword"
    }

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
    """Login user.

    Expected JSON:
    {
        "username": "alice",
        "password": "securepassword"
    }

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
    """Logout current user.

    Returns:
        Response: JSON response confirming logout
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
