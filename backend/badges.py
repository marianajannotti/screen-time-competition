"""Badge API endpoints for the Screen Time Competition backend."""

from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user

from .badge_service import BadgeService
from .models import User


# Create the blueprint
badges_bp = Blueprint("badges", __name__, url_prefix="/api")


@badges_bp.route("/badges", methods=["GET"])
def get_all_badges():
    """Get all available badges.
    
    Returns:
        JSON: List of all badges with their metadata
    """
    try:
        badges = BadgeService.get_all_badges()
        return jsonify([badge.to_dict() for badge in badges]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@badges_bp.route("/users/<int:user_id>/badges", methods=["GET"])
@login_required
def get_user_badges(user_id: int):
    """Get badges earned by a specific user.
    
    Args:
        user_id (int): ID of the user
        
    Returns:
        JSON: List of badges earned by the user with timestamps
    """
    try:
        # Only allow users to view their own badges or admin functionality
        if current_user.id != user_id:
            return jsonify({"error": "Access denied"}), 403
            
        user_badges = BadgeService.get_user_badges(user_id)
        return jsonify([user_badge.to_dict() for user_badge in user_badges]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@badges_bp.route("/users/<int:user_id>/badges", methods=["POST"])
@login_required
def award_badge(user_id: int):
    """Award a badge to a user (admin or system use).
    
    Args:
        user_id (int): ID of the user to award badge to
        
    Request JSON:
        badge_name (str): Name of the badge to award
        
    Returns:
        JSON: Success/error message
    """
    try:
        data = request.get_json()
        if not data or 'badge_name' not in data:
            return jsonify({"error": "badge_name is required"}), 400
        
        badge_name = data['badge_name']
        
        # For now, only allow users to award badges to themselves (for testing)
        # In production, this might be admin-only or system-triggered
        if current_user.id != user_id:
            return jsonify({"error": "Access denied"}), 403
        
        success, message = BadgeService.award_badge(user_id, badge_name)
        
        if success:
            return jsonify({"message": message}), 201
        else:
            return jsonify({"error": message}), 400
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@badges_bp.route("/users/<int:user_id>/badges/check", methods=["POST"])
@login_required
def check_user_badges(user_id: int):
    """Manually check and award badges for a user (for testing/admin use).
    
    Args:
        user_id (int): ID of the user to check badges for
        
    Returns:
        JSON: List of newly awarded badges
    """
    try:
        # Only allow users to check their own badges or admin functionality
        if current_user.id != user_id:
            return jsonify({"error": "Access denied"}), 403
        
        from .badge_logic import BadgeLogic
        awarded_badges = BadgeLogic.check_and_award_badges(user_id)
        
        return jsonify({
            "message": f"Badge check completed for user {user_id}",
            "awarded_badges": awarded_badges
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@badges_bp.route("/badges/initialize", methods=["POST"])
def initialize_badges():
    """Initialize default badges in the database (admin/setup use).
    
    Returns:
        JSON: Success message
    """
    try:
        BadgeService.initialize_badges()
        return jsonify({"message": "Badges initialized successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
