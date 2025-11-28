"""
Friends & Social Features Routes for Screen Time Competition

This module provides API endpoints for the social competition aspects of the app.
Users can send friend requests, manage friendships, and compete on leaderboards
to see who has the best screen time management.

Key Features:
- Complete friend request system (send, accept, reject)
- Bidirectional friendship management
- Social leaderboards comparing screen time between friends
- User search functionality for adding new friends
- Privacy controls and friendship status tracking

Social Competition Elements:
- Friend-only leaderboards showing comparative screen time
- Streak comparisons between friends
- Points-based rankings and achievements
- Weekly/monthly social challenges
- Friend activity feeds and notifications

Database Design:
- Friendship model supports bidirectional relationships
- Status tracking (pending, accepted) for friend requests
- Efficient queries using SQLAlchemy relationships
- Optimized leaderboard calculations

API Endpoints:
- GET /api/friends/ - Get accepted friends list
- POST /api/friends/request - Send friend request
- GET /api/friends/requests - Get pending friend requests
- PUT /api/friends/accept/{id} - Accept friend request
- PUT /api/friends/reject/{id} - Reject friend request
- DELETE /api/friends/{id} - Remove friend
- GET /api/friends/search - Search users to add as friends
- GET /api/friends/leaderboard - Get friends leaderboard
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, date, timedelta
from sqlalchemy import or_, and_
from .database import db
from .models import User, Friendship, ScreenTimeLog

# Create friends blueprint with URL prefix
# All routes in this blueprint will be prefixed with /api/friends
friends_bp = Blueprint("friends", __name__, url_prefix="/api/friends")


@friends_bp.route("/", methods=["GET"])
@login_required
def get_friends():
    """
    Get Accepted Friends List
    
    Retrieves all users who have an accepted friendship relationship with the
    current authenticated user. Handles bidirectional friendships where the
    current user could be either the sender or receiver of the friend request.
    
    Expected Request:
        Method: GET
        Authentication: Required (valid session)
        Parameters: None
    
    Database Query Logic:
    1. Find all friendships where current user is involved (user_id OR friend_id)
    2. Filter for only 'accepted' status friendships
    3. Extract the friend user IDs (excluding current user's ID)
    4. Retrieve full User objects for all friend IDs
    5. Return user data (excluding sensitive information)
    
    Success Response (200):
        {
            "data": [
                {
                    "id": 123,
                    "username": "alice",
                    "email": "alice@example.com",
                    "streak_count": 15,
                    "total_points": 1200,
                    "created_at": "2024-01-01T12:00:00"
                },
                // ... more friends
            ]
        }
    
    Error Responses:
        401: User not authenticated
        500: Internal server error
    
    Returns:
        Response: JSON with list of friend user data or error message
    """
    try:
        # Get all accepted friendships where user is either sender or receiver
        friendships = Friendship.query.filter(
            and_(
                or_(
                    Friendship.user_id == current_user.id,
                    Friendship.friend_id == current_user.id
                ),
                Friendship.status == "accepted"
            )
        ).all()
        
        # Extract friend user IDs
        friend_ids = []
        for friendship in friendships:
            if friendship.user_id == current_user.id:
                friend_ids.append(friendship.friend_id)
            else:
                friend_ids.append(friendship.user_id)
        
        # Get friend user objects
        friends = User.query.filter(User.id.in_(friend_ids)).all() if friend_ids else []
        
        return jsonify({
            "data": [friend.to_dict() for friend in friends]
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to fetch friends: {str(e)}"}), 500


@friends_bp.route("/requests", methods=["GET"])
@login_required
def get_friend_requests():
    """Get pending friend requests for current user"""
    try:
        # Get pending requests where current user is the receiver
        pending_requests = Friendship.query.filter_by(
            friend_id=current_user.id,
            status="pending"
        ).all()
        
        # Get sender user objects
        sender_ids = [req.user_id for req in pending_requests]
        senders = User.query.filter(User.id.in_(sender_ids)).all() if sender_ids else []
        
        # Create response data
        requests_data = []
        for request in pending_requests:
            sender = next((u for u in senders if u.id == request.user_id), None)
            if sender:
                requests_data.append({
                    "id": request.id,
                    "sender": sender.to_dict(),
                    "created_at": request.created_at.isoformat()
                })
        
        return jsonify({"data": requests_data}), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to fetch friend requests: {str(e)}"}), 500


@friends_bp.route("/add", methods=["POST"])
@login_required
def send_friend_request():
    """
    Send friend request
    
    Expected JSON:
    {
        "username": "alice"
    }
    """
    try:
        data = request.get_json()
        
        if not data or not data.get("username"):
            return jsonify({"error": "Username is required"}), 400
            
        username = data["username"].strip()
        
        # Can't add yourself
        if username == current_user.username:
            return jsonify({"error": "You cannot add yourself as a friend"}), 400
            
        # Find target user
        target_user = User.query.filter_by(username=username).first()
        if not target_user:
            return jsonify({"error": "User not found"}), 404
            
        # Check if friendship already exists
        existing_friendship = Friendship.query.filter(
            or_(
                and_(Friendship.user_id == current_user.id, Friendship.friend_id == target_user.id),
                and_(Friendship.user_id == target_user.id, Friendship.friend_id == current_user.id)
            )
        ).first()
        
        if existing_friendship:
            if existing_friendship.status == "accepted":
                return jsonify({"error": "You are already friends with this user"}), 400
            else:
                return jsonify({"error": "Friend request already pending"}), 400
                
        # Create friend request
        friend_request = Friendship(
            user_id=current_user.id,
            friend_id=target_user.id,
            status="pending"
        )
        
        db.session.add(friend_request)
        db.session.commit()
        
        return jsonify({
            "message": f"Friend request sent to {username}",
            "data": friend_request.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to send friend request: {str(e)}"}), 500


@friends_bp.route("/accept/<int:request_id>", methods=["POST"])
@login_required
def accept_friend_request(request_id):
    """Accept a friend request"""
    try:
        # Find the friend request
        friend_request = Friendship.query.filter_by(
            id=request_id,
            friend_id=current_user.id,
            status="pending"
        ).first()
        
        if not friend_request:
            return jsonify({"error": "Friend request not found"}), 404
            
        # Accept the request
        friend_request.status = "accepted"
        db.session.commit()
        
        return jsonify({
            "message": "Friend request accepted",
            "data": friend_request.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to accept friend request: {str(e)}"}), 500


@friends_bp.route("/reject/<int:request_id>", methods=["POST"])
@login_required
def reject_friend_request(request_id):
    """Reject a friend request"""
    try:
        # Find the friend request
        friend_request = Friendship.query.filter_by(
            id=request_id,
            friend_id=current_user.id,
            status="pending"
        ).first()
        
        if not friend_request:
            return jsonify({"error": "Friend request not found"}), 404
            
        # Delete the request (reject)
        db.session.delete(friend_request)
        db.session.commit()
        
        return jsonify({"message": "Friend request rejected"}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to reject friend request: {str(e)}"}), 500


@friends_bp.route("/remove/<int:friend_id>", methods=["DELETE"])
@login_required
def remove_friend(friend_id):
    """Remove a friend"""
    try:
        # Find the friendship
        friendship = Friendship.query.filter(
            and_(
                or_(
                    and_(Friendship.user_id == current_user.id, Friendship.friend_id == friend_id),
                    and_(Friendship.user_id == friend_id, Friendship.friend_id == current_user.id)
                ),
                Friendship.status == "accepted"
            )
        ).first()
        
        if not friendship:
            return jsonify({"error": "Friendship not found"}), 404
            
        # Remove the friendship
        db.session.delete(friendship)
        db.session.commit()
        
        return jsonify({"message": "Friend removed successfully"}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to remove friend: {str(e)}"}), 500


@friends_bp.route("/leaderboard", methods=["GET"])
@login_required
def get_leaderboard():
    """
    Get leaderboard for friends
    Query params:
    - period: 'daily', 'weekly' (default: 'weekly')
    """
    try:
        period = request.args.get("period", "weekly")
        
        if period not in ["daily", "weekly"]:
            return jsonify({"error": "Period must be 'daily' or 'weekly'"}), 400
            
        # Calculate date range
        end_date = date.today()
        if period == "daily":
            start_date = end_date
        else:  # weekly
            start_date = end_date - timedelta(days=6)
            
        # Get friend IDs
        friendships = Friendship.query.filter(
            and_(
                or_(
                    Friendship.user_id == current_user.id,
                    Friendship.friend_id == current_user.id
                ),
                Friendship.status == "accepted"
            )
        ).all()
        
        friend_ids = [current_user.id]  # Include current user
        for friendship in friendships:
            if friendship.user_id == current_user.id:
                friend_ids.append(friendship.friend_id)
            else:
                friend_ids.append(friendship.user_id)
        
        # Get screen time data for all friends
        screen_time_data = {}
        for user_id in friend_ids:
            logs = ScreenTimeLog.query.filter(
                ScreenTimeLog.user_id == user_id,
                ScreenTimeLog.date >= start_date,
                ScreenTimeLog.date <= end_date
            ).all()
            
            total_minutes = sum(log.screen_time_minutes for log in logs)
            screen_time_data[user_id] = total_minutes
            
        # Get user objects
        users = User.query.filter(User.id.in_(friend_ids)).all()
        
        # Create leaderboard
        leaderboard = []
        for user in users:
            screen_time = screen_time_data.get(user.id, 0)
            leaderboard.append({
                "user": user.to_dict(),
                "screen_time_minutes": screen_time,
                "is_current_user": user.id == current_user.id
            })
            
        # Sort by screen time (ascending - less is better)
        leaderboard.sort(key=lambda x: x["screen_time_minutes"])
        
        # Add rankings
        for i, entry in enumerate(leaderboard):
            entry["rank"] = i + 1
            
        return jsonify({
            "period": period,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "data": leaderboard
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to fetch leaderboard: {str(e)}"}), 500