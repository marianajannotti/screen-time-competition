"""
Goals Management Routes for Screen Time Competition

This module provides API endpoints for users to create, manage, and track their
screen time goals. Supports both daily and weekly goal types with real-time
progress tracking and gamification integration.

Key Features:
- Create and update daily/weekly screen time goals
- Real-time progress calculation and tracking
- Goal achievement detection for bonus points
- Integration with business logic for gamification
- Comprehensive validation and error handling

Goal Types Supported:
- Daily Goals: Target screen time limit for each day
- Weekly Goals: Target screen time limit for entire week

Business Logic Integration:
- Progress calculated using BusinessLogicService
- Goal achievements award bonus points to users
- Real-time validation against current usage
- Support for percentage-based progress tracking

API Endpoints:
- GET /api/goals/ - Retrieve all user goals
- POST /api/goals/ - Create or update goals
- GET /api/goals/{type} - Get specific goal by type
- DELETE /api/goals/{id} - Delete specific goal
- GET /api/goals/progress - Get progress on all goals
- GET /api/goals/progress/{type} - Get specific goal progress
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from .database import db
from .models import Goal
from .business_logic import BusinessLogicService

# Create goals blueprint with URL prefix
# All routes in this blueprint will be prefixed with /api/goals
goals_bp = Blueprint("goals", __name__, url_prefix="/api/goals")


@goals_bp.route("/", methods=["GET"])
@login_required
def get_goals():
    """
    Retrieve All User Goals
    
    Returns all screen time goals (daily and weekly) for the authenticated user.
    Goals are returned as a list with complete configuration details.
    
    Expected Request:
        Method: GET
        Authentication: Required (valid session)
        Parameters: None
    
    Success Response (200):
        {
            "data": [
                {
                    "id": 123,
                    "user_id": 456,
                    "goal_type": "daily",
                    "target_minutes": 120
                },
                {
                    "id": 124,
                    "user_id": 456, 
                    "goal_type": "weekly",
                    "target_minutes": 840
                }
            ]
        }
    
    Error Responses:
        401: User not authenticated
        500: Internal server error
    
    Returns:
        Response: JSON with list of user goals or error message
    """
    try:
        goals = Goal.query.filter_by(user_id=current_user.id).all()
        return jsonify({
            "data": [goal.to_dict() for goal in goals]
        }), 200
    except Exception as e:
        return jsonify({"error": f"Failed to fetch goals: {str(e)}"}), 500


@goals_bp.route("/", methods=["POST"])
@login_required
def create_goal():
    """
    Create or update a goal
    
    Expected JSON:
    {
        "goal_type": "daily",  # or "weekly"
        "target_minutes": 120
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        goal_type = data.get("goal_type")
        target_minutes = data.get("target_minutes")
        
        # Validation
        if goal_type not in ["daily", "weekly"]:
            return jsonify({"error": "goal_type must be 'daily' or 'weekly'"}), 400
            
        if not isinstance(target_minutes, int) or target_minutes <= 0:
            return jsonify({"error": "target_minutes must be a positive integer"}), 400
            
        # Check if goal already exists for this type
        existing_goal = Goal.query.filter_by(
            user_id=current_user.id,
            goal_type=goal_type
        ).first()
        
        if existing_goal:
            # Update existing goal
            existing_goal.target_minutes = target_minutes
            db.session.commit()
            
            return jsonify({
                "message": f"{goal_type.capitalize()} goal updated successfully",
                "data": existing_goal.to_dict()
            }), 200
        else:
            # Create new goal
            new_goal = Goal(
                user_id=current_user.id,
                goal_type=goal_type,
                target_minutes=target_minutes
            )
            
            db.session.add(new_goal)
            db.session.commit()
            
            return jsonify({
                "message": f"{goal_type.capitalize()} goal created successfully",
                "data": new_goal.to_dict()
            }), 201
            
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to create/update goal: {str(e)}"}), 500


@goals_bp.route("/<goal_type>", methods=["GET"])
@login_required
def get_goal_by_type(goal_type):
    """Get specific goal by type (daily/weekly)"""
    try:
        if goal_type not in ["daily", "weekly"]:
            return jsonify({"error": "goal_type must be 'daily' or 'weekly'"}), 400
            
        goal = Goal.query.filter_by(
            user_id=current_user.id,
            goal_type=goal_type
        ).first()
        
        if not goal:
            return jsonify({
                "data": None,
                "message": f"No {goal_type} goal set"
            }), 200
            
        return jsonify({"data": goal.to_dict()}), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to fetch {goal_type} goal: {str(e)}"}), 500


@goals_bp.route("/<int:goal_id>", methods=["DELETE"])
@login_required
def delete_goal(goal_id):
    """Delete a specific goal"""
    try:
        goal = Goal.query.filter_by(
            id=goal_id,
            user_id=current_user.id
        ).first()
        
        if not goal:
            return jsonify({"error": "Goal not found"}), 404
            
        db.session.delete(goal)
        db.session.commit()
        
        return jsonify({"message": "Goal deleted successfully"}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to delete goal: {str(e)}"}), 500


@goals_bp.route("/progress", methods=["GET"])
@login_required
def get_goal_progress():
    """Get progress on all user goals"""
    try:
        # Get daily goal progress
        daily_progress = BusinessLogicService.check_daily_goal_progress(current_user.id)
        
        # Get weekly goal progress  
        weekly_progress = BusinessLogicService.check_weekly_goal_progress(current_user.id)
        
        return jsonify({
            "data": {
                "daily": daily_progress,
                "weekly": weekly_progress
            }
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to fetch goal progress: {str(e)}"}), 500


@goals_bp.route("/progress/<goal_type>", methods=["GET"])
@login_required
def get_specific_goal_progress(goal_type):
    """Get progress on specific goal type (daily/weekly)"""
    try:
        if goal_type not in ["daily", "weekly"]:
            return jsonify({"error": "goal_type must be 'daily' or 'weekly'"}), 400
            
        if goal_type == "daily":
            progress = BusinessLogicService.check_daily_goal_progress(current_user.id)
        else:
            progress = BusinessLogicService.check_weekly_goal_progress(current_user.id)
            
        return jsonify({"data": progress}), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to fetch {goal_type} goal progress: {str(e)}"}), 500