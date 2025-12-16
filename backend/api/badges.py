"""Badge API endpoints for the Screen Time Competition backend."""

from flask import Blueprint, jsonify, request, make_response
from flask_login import login_required, current_user

from ..services.badge_service import BadgeService
from ..utils.helpers import add_api_headers

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
        response = make_response(jsonify([badge.to_dict() for badge in badges]), 200)
        return add_api_headers(response)
    except Exception as e:
        response = make_response(jsonify({"error": str(e)}), 500)
        return add_api_headers(response)


@badges_bp.route("/users/<int:user_id>/badges", methods=["GET"])
@login_required
def get_user_badges(user_id: int):
    """Get badges earned by a specific user.
    
    Args:
        user_id (int): ID of the user
        
    Returns:
        JSON: List of badges earned by the user with timestamps
    """
    # Validate user_id
    if user_id <= 0:
        response = make_response(jsonify({"error": "Invalid user ID"}), 400)
        return add_api_headers(response)
    
    # Only allow users to view their own badges or admin functionality
    if not current_user.is_authenticated or current_user.id != user_id:
        response = make_response(jsonify({"error": "Access denied"}), 403)
        return add_api_headers(response)
    
    try:
        user_badges = BadgeService.get_user_badges(user_id)
        response = make_response(jsonify([user_badge.to_dict() for user_badge in user_badges]), 200)
        return add_api_headers(response)
    except Exception as e:
        response = make_response(jsonify({"error": str(e)}), 500)
        return add_api_headers(response)


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
    # Validate user_id
    if user_id <= 0:
        response = make_response(jsonify({"error": "Invalid user ID"}), 400)
        return add_api_headers(response)
    
    try:
        data = request.get_json()
        if not data or 'badge_name' not in data:
            response = make_response(jsonify({"error": "badge_name is required"}), 400)
            return add_api_headers(response)
        
        badge_name = data['badge_name']
        
        # For now, only allow users to award badges to themselves (for testing)
        # In production, this might be admin-only or system-triggered
        if current_user.id != user_id:
            response = make_response(jsonify({"error": "Access denied"}), 403)
            return add_api_headers(response)
        
        success, message = BadgeService.award_badge(user_id, badge_name)
        
        if success:
            response = make_response(jsonify({"message": message}), 201)
            return add_api_headers(response)
        else:
            response = make_response(jsonify({"error": message}), 400)
            return add_api_headers(response)
            
    except Exception as e:
        response = make_response(jsonify({"error": str(e)}), 500)
        return add_api_headers(response)


@badges_bp.route("/users/<int:user_id>/badges/check", methods=["POST"])
@login_required
def check_user_badges(user_id: int):
    """Manually check and award badges for a user (for testing/admin use).
    
    Args:
        user_id (int): ID of the user to check badges for
        
    Returns:
        JSON: List of newly awarded badges
    """
    # Validate user_id
    if user_id <= 0:
        response = make_response(jsonify({"error": "Invalid user ID"}), 400)
        return add_api_headers(response)
    
    try:
        # Only allow users to check their own badges or admin functionality
        if current_user.id != user_id:
            response = make_response(jsonify({"error": "Access denied"}), 403)
            return add_api_headers(response)
        
        from ..services import BadgeAchievementService
        awarded_badges = BadgeAchievementService.check_and_award_badges(user_id)
        
        response = make_response(jsonify({
            "message": f"Badge check completed for user {user_id}",
            "awarded_badges": awarded_badges
        }), 200)
        return add_api_headers(response)
        
    except Exception as e:
        response = make_response(jsonify({"error": str(e)}), 500)
        return add_api_headers(response)


@badges_bp.route("/badges/initialize", methods=["POST"])
@login_required
def initialize_badges():
    """Initialize default badges in the database (admin/setup use).
    
    Returns:
        JSON: Success message
    """
    # Require admin privileges
    if not getattr(current_user, "is_admin", False):
        response = make_response(jsonify({"error": "Admin access required"}), 403)
        return add_api_headers(response)
    
    try:
        BadgeService.initialize_badges()
        response = make_response(jsonify({"message": "Badges initialized successfully"}), 200)
        return add_api_headers(response)
    except Exception as e:
        response = make_response(jsonify({"error": str(e)}), 500)
        return add_api_headers(response)
