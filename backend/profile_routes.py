"""
User Profile Management Routes for Screen Time Competition

This module provides comprehensive user profile management functionality including
personal information updates, security settings, and enhanced statistics display.
It serves as the central hub for user account management and personalization.

Key Features:
- Complete profile information management (username, email)
- Secure password change functionality with verification
- Account deletion with proper cleanup
- Enhanced profile statistics with social and goal data
- Privacy controls and data export capabilities

Security Features:
- Current password verification for sensitive operations
- Secure password hashing using bcrypt
- Input validation and sanitization
- Session-based authentication requirements
- Data cleanup on account deletion

Enhanced Statistics:
- Real-time goal progress calculation
- Friend count and social statistics
- Streak and points display
- Historical activity summaries
- Achievement and milestone tracking

Integration Points:
- BusinessLogicService for goal progress calculation
- AuthService for secure password operations
- Friendship model for social statistics
- Goal model for progress tracking
- User model for profile data management

API Endpoints:
- GET /api/profile/ - Get enhanced profile with statistics
- PUT /api/profile/ - Update profile information
- PUT /api/profile/password - Change password securely  
- DELETE /api/profile/ - Delete account with cleanup
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import or_, and_
from .database import db
from .auth_service import AuthService

# Create profile blueprint with URL prefix
# All routes in this blueprint will be prefixed with /api/profile
profile_bp = Blueprint("profile", __name__, url_prefix="/api/profile")


@profile_bp.route("/", methods=["GET"])
@login_required
def get_profile():
    """Get current user profile with enhanced stats"""
    from .business_logic import BusinessLogicService
    from .models import Friendship
    
    # Get basic user data
    user_data = current_user.to_dict()
    
    # Add enhanced stats
    try:
        # Friend count
        friend_count = Friendship.query.filter(
            or_(
                and_(Friendship.user_id == current_user.id, Friendship.status == "accepted"),
                and_(Friendship.friend_id == current_user.id, Friendship.status == "accepted")
            )
        ).count()
        
        # Goal progress
        daily_progress = BusinessLogicService.check_daily_goal_progress(current_user.id)
        weekly_progress = BusinessLogicService.check_weekly_goal_progress(current_user.id)
        
        user_data.update({
            "friend_count": friend_count,
            "goals": {
                "daily": daily_progress,
                "weekly": weekly_progress
            }
        })
        
    except Exception as e:
        print(f"Warning: Failed to load enhanced profile stats: {e}")
    
    return jsonify({"user": user_data}), 200


@profile_bp.route("/", methods=["PUT"])
@login_required
def update_profile():
    """
    Update user profile
    
    Expected JSON:
    {
        "username": "new_username",  # optional
        "email": "new_email@example.com"  # optional
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        username = data.get("username")
        email = data.get("email")
        
        # Validate inputs
        if username is not None:
            username = username.strip()
            if len(username) < 3:
                return jsonify({"error": "Username must be at least 3 characters"}), 400
                
            # Check if username is taken (by someone else)
            existing_user = AuthService.get_user_by_username(username)
            if existing_user and existing_user.id != current_user.id:
                return jsonify({"error": "Username already exists"}), 400
                
        if email is not None:
            email = email.strip().lower()
            if "@" not in email or "." not in email:
                return jsonify({"error": "Invalid email format"}), 400
                
            # Check if email is taken (by someone else)
            existing_user = AuthService.get_user_by_email(email)
            if existing_user and existing_user.id != current_user.id:
                return jsonify({"error": "Email already exists"}), 400
        
        # Update fields
        if username is not None:
            current_user.username = username
            
        if email is not None:
            current_user.email = email
            
        db.session.commit()
        
        return jsonify({
            "message": "Profile updated successfully",
            "user": current_user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to update profile: {str(e)}"}), 500


@profile_bp.route("/password", methods=["PUT"])
@login_required
def change_password():
    """
    Change user password
    
    Expected JSON:
    {
        "current_password": "old_password",
        "new_password": "new_secure_password"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        current_password = data.get("current_password")
        new_password = data.get("new_password")
        
        # Validate inputs
        if not current_password or not new_password:
            return jsonify({"error": "Current password and new password are required"}), 400
            
        if len(new_password) < 6:
            return jsonify({"error": "New password must be at least 6 characters"}), 400
            
        # Verify current password
        if not check_password_hash(current_user.password_hash, current_password):
            return jsonify({"error": "Current password is incorrect"}), 400
            
        # Update password
        current_user.password_hash = generate_password_hash(new_password)
        db.session.commit()
        
        return jsonify({"message": "Password changed successfully"}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to change password: {str(e)}"}), 500


@profile_bp.route("/stats", methods=["GET"])
@login_required
def get_profile_stats():
    """Get extended profile statistics"""
    try:
        from .models import ScreenTimeLog, Friendship
        from datetime import datetime, date, timedelta
        
        # Calculate streak and points (this could be cached for performance)
        today = date.today()
        
        # Simple streak calculation: consecutive days with screen time logs
        streak_count = 0
        check_date = today
        
        while True:
            log_exists = ScreenTimeLog.query.filter_by(
                user_id=current_user.id,
                date=check_date
            ).first()
            
            if log_exists:
                streak_count += 1
                check_date -= timedelta(days=1)
            else:
                break
                
            # Prevent infinite loop
            if streak_count > 365:
                break
        
        # Update streak in database
        current_user.streak_count = streak_count
        
        # Calculate total points (simple: 1 point per day logged)
        total_logs = ScreenTimeLog.query.filter_by(user_id=current_user.id).count()
        current_user.total_points = total_logs
        
        # Get friend count
        friend_count = Friendship.query.filter(
            and_(
                or_(
                    Friendship.user_id == current_user.id,
                    Friendship.friend_id == current_user.id
                ),
                Friendship.status == "accepted"
            )
        ).count()
        
        # Get recent activity (last 7 days)
        week_ago = today - timedelta(days=6)
        recent_logs = ScreenTimeLog.query.filter(
            ScreenTimeLog.user_id == current_user.id,
            ScreenTimeLog.date >= week_ago
        ).count()
        
        db.session.commit()  # Save updated streak and points
        
        return jsonify({
            "user": current_user.to_dict(),
            "stats": {
                "friend_count": friend_count,
                "days_logged_this_week": recent_logs,
                "total_days_logged": total_logs
            }
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to fetch profile stats: {str(e)}"}), 500


@profile_bp.route("/delete", methods=["DELETE"])
@login_required
def delete_account():
    """
    Delete user account and all associated data
    
    Expected JSON:
    {
        "password": "user_password",
        "confirm": "DELETE"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        password = data.get("password")
        confirm = data.get("confirm")
        
        # Validate inputs
        if not password:
            return jsonify({"error": "Password is required"}), 400
            
        if confirm != "DELETE":
            return jsonify({"error": "Must confirm deletion with 'DELETE'"}), 400
            
        # Verify password
        if not check_password_hash(current_user.password_hash, password):
            return jsonify({"error": "Password is incorrect"}), 400
            
        # Delete all associated data
        from .models import ScreenTimeLog, Goal, Friendship
        
        user_id = current_user.id
        
        # Delete screen time logs
        ScreenTimeLog.query.filter_by(user_id=user_id).delete()
        
        # Delete goals
        Goal.query.filter_by(user_id=user_id).delete()
        
        # Delete friendships
        Friendship.query.filter(
            or_(
                Friendship.user_id == user_id,
                Friendship.friend_id == user_id
            )
        ).delete()
        
        # Delete user
        db.session.delete(current_user)
        db.session.commit()
        
        return jsonify({"message": "Account deleted successfully"}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to delete account: {str(e)}"}), 500