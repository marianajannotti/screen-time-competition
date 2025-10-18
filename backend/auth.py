"""
Authentication Blueprint for Screen Time Competition
Handles user registration, login, logout
"""

from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from .database import db  # Import shared db instance
from .models import User  # Import User model

# Create blueprint
auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.route("/register", methods=["POST"])
def register():
    """
    Register a new user

    Expected JSON:
    {
        "username": "alice",
        "email": "alice@example.com",
        "password": "securepassword"
    }
    """
    try:
        data = request.get_json()

        # Validate required fields
        if (
            not data
            or not data.get("username")
            or not data.get("email")
            or not data.get("password")
        ):
            return jsonify({"error": "Missing username, email, or password"}), 400

        username = data["username"].strip()
        email = data["email"].strip().lower()
        password = data["password"]

        # Check if user already exists
        if User.query.filter_by(username=username).first():
            return jsonify({"error": "Username already exists"}), 400

        if User.query.filter_by(email=email).first():
            return jsonify({"error": "Email already registered"}), 400

        # Create new user
        password_hash = generate_password_hash(password)
        new_user = User(username=username, email=email, password_hash=password_hash)

        db.session.add(new_user)
        db.session.commit()

        return (
            jsonify(
                {"message": "User registered successfully", "user": new_user.to_dict()}
            ),
            201,
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Registration failed: {str(e)}"}), 500


@auth_bp.route("/login", methods=["POST"])
def login():
    """
    Login user

    Expected JSON:
    {
        "username": "alice",
        "password": "securepassword"
    }
    """
    try:
        data = request.get_json()

        if not data or not data.get("username") or not data.get("password"):
            return jsonify({"error": "Missing username or password"}), 400

        username = data["username"].strip()
        password = data["password"]

        # Find user
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return jsonify({"message": "Login successful", "user": user.to_dict()}), 200
        else:
            return jsonify({"error": "Invalid username or password"}), 401

    except Exception as e:
        return jsonify({"error": f"Login failed: {str(e)}"}), 500


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    """Logout current user"""
    logout_user()
    return jsonify({"message": "Logged out successfully"}), 200


@auth_bp.route("/me", methods=["GET"])
@login_required
def get_current_user():
    """Get current logged-in user info"""
    return jsonify({"user": current_user.to_dict()}), 200


@auth_bp.route("/status", methods=["GET"])
def auth_status():
    """Check if user is logged in (no login required)"""
    if current_user.is_authenticated:
        return jsonify({"authenticated": True, "user": current_user.to_dict()}), 200
    else:
        return jsonify({"authenticated": False}), 200
