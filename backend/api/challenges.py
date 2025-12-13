"""Challenge routes for creating and managing screen time challenges."""

from flask import Blueprint, request, jsonify, make_response
from flask_login import login_required, current_user

from ..database import db
from ..services.challenges_service import ChallengesService, ValidationError
from ..utils import add_api_headers

challenges_bp = Blueprint('challenges', __name__, url_prefix='/api/challenges')


@challenges_bp.route('', methods=['POST'])
@login_required
def create_challenge():
    """
    Create a new challenge.
    Args:
        None (uses JSON body from request)
    Returns:
        JSON response with created challenge or error message.
    Example JSON:
        {
            "name": "1 week without TikTok",
            "description": "Optional description",
            "target_app": "TikTok" or "__TOTAL__",
            "target_minutes": 30,
            "start_date": "2025-12-10",
            "end_date": "2025-12-17",
            "invited_user_ids": [2, 3, 4]
        }
    """
    if request.content_type != "application/json":
        response = make_response(
            jsonify({'error': 'Content-Type must be application/json'}), 415
        )
        return add_api_headers(response)
    
    try:
        data = request.get_json()
        
        # Validate and extract challenge data
        name, description, target_app, target_minutes, start_date, end_date, status = \
            ChallengesService.validate_challenge_creation(data, current_user.id)
        
        # Validate invited user IDs exist
        invited_ids = data.get('invited_user_ids', [])
        if invited_ids:
            ChallengesService.validate_user_ids(invited_ids, exclude_user_id=current_user.id)
        
        # Create challenge with participants
        challenge = ChallengesService.create_challenge(
            name=name,
            description=description,
            owner_id=current_user.id,
            target_app=target_app,
            target_minutes=target_minutes,
            start_date=start_date,
            end_date=end_date,
            status=status,
            invited_user_ids=invited_ids
        )
        
        response = make_response(jsonify({
            'challenge': challenge.to_dict(),
            'message': 'Challenge created successfully'
        }), 201)
        return add_api_headers(response)
    
    except ValidationError as e:
        response = make_response(jsonify({'error': str(e)}), 400)
        return add_api_headers(response)
    
    except Exception as e:  # pragma: no cover - bubbled to client
        db.session.rollback()
        from flask import current_app
        current_app.logger.error(f'Failed to create challenge: {str(e)}')
        response = make_response(
            jsonify({'error': 'Failed to create challenge'}), 500
        )
        return add_api_headers(response)


@challenges_bp.route('', methods=['GET'])
@login_required
def get_challenges():
    """
    Get all challenges for the current user (owned or participating).
    Args:
        None
    Returns:
        JSON response with a list of challenges and user stats.
    """
    challenges_data = ChallengesService.get_user_challenges(current_user.id)
    
    response = make_response(jsonify({'challenges': challenges_data}), 200)
    return add_api_headers(response)


@challenges_bp.route('/<int:challenge_id>', methods=['GET'])
@login_required
def get_challenge(challenge_id):
    """
    Get a specific challenge with full details.
    Args:
        challenge_id: ID of the challenge to retrieve.
    Returns:
        JSON response with challenge details and user stats.
    """
    try:
        challenge, participation = ChallengesService.get_challenge_by_id(challenge_id, current_user.id)
        
        challenge_dict = challenge.to_dict()
        challenge_dict['user_stats'] = participation.to_dict()
        
        response = make_response(jsonify({'challenge': challenge_dict}), 200)
        return add_api_headers(response)
    
    except ValidationError as e:
        response = make_response(jsonify({'error': str(e)}), 403)
        return add_api_headers(response)


@challenges_bp.route('/<int:challenge_id>/leaderboard', methods=['GET'])
@login_required
def get_leaderboard(challenge_id):
    """
    Get live leaderboard for a challenge showing all participants and their stats.
    Args:
        challenge_id: ID of the challenge.
    Returns:
        JSON response with challenge info, owner username, and leaderboard list.
    """
    try:
        challenge, leaderboard = ChallengesService.get_leaderboard(challenge_id, current_user.id)
        
        response = make_response(jsonify({
            'challenge': challenge.to_dict(),
            'owner_username': challenge.owner.username if challenge.owner else 'Unknown',
            'leaderboard': leaderboard
        }), 200)
        return add_api_headers(response)
    
    except ValidationError as e:
        response = make_response(jsonify({'error': str(e)}), 403)
        return add_api_headers(response)


@challenges_bp.route('/<int:challenge_id>/invite', methods=['POST'])
@login_required
def invite_to_challenge(challenge_id):
    """
    Invite additional members to a challenge (only owner can invite).
    Args:
        challenge_id: ID of the challenge.
    Returns:
        JSON response with invite result and count.
    Example JSON:
        {
            "user_ids": [5, 6, 7]
        }
    """
    if request.content_type != "application/json":
        response = make_response(
            jsonify({'error': 'Content-Type must be application/json'}), 415
        )
        return add_api_headers(response)
    
    try:
        data = request.get_json()
        user_ids = data.get('user_ids', [])
        
        invited_count = ChallengesService.invite_users(challenge_id, user_ids, current_user.id)
        
        response = make_response(jsonify({
            'message': f'Successfully invited {invited_count} member(s)',
            'invited_count': invited_count
        }), 200)
        return add_api_headers(response)
    
    except ValidationError as e:
        # Determine appropriate status code based on error message
        status_code = 403 if 'owner' in str(e).lower() else 400
        response = make_response(jsonify({'error': str(e)}), status_code)
        return add_api_headers(response)
    
    except Exception as e:  # pragma: no cover - bubbled to client
        db.session.rollback()
        from flask import current_app
        current_app.logger.error(f'Failed to invite members: {str(e)}')
        response = make_response(
            jsonify({'error': 'Failed to invite members'}), 500
        )
        return add_api_headers(response)


@challenges_bp.route('/<int:challenge_id>/leave', methods=['POST'])
@login_required
def leave_challenge(challenge_id):
    """
    Leave a challenge (any participant can leave, except owner).
    Args:
        challenge_id: ID of the challenge to leave.
    Returns:
        JSON response with success or error message.
    """
    try:
        ChallengesService.leave_challenge(challenge_id, current_user.id)
        
        response = make_response(jsonify({'message': 'Successfully left the challenge'}), 200)
        return add_api_headers(response)
    
    except ValidationError as e:
        # Determine appropriate status code based on error message
        status_code = 403 if 'owner' in str(e).lower() else 400
        response = make_response(jsonify({'error': str(e)}), status_code)
        return add_api_headers(response)
    
    except Exception as e:  # pragma: no cover - bubbled to client
        db.session.rollback()
        from flask import current_app
        current_app.logger.error(f'Failed to leave challenge: {str(e)}')
        response = make_response(
            jsonify({'error': 'Failed to leave challenge'}), 500
        )
        return add_api_headers(response)


@challenges_bp.route('/<int:challenge_id>', methods=['DELETE'])
@login_required
def delete_challenge(challenge_id):
    """
    Delete a challenge (only owner can delete).
    Args:
        challenge_id: ID of the challenge to delete.
    Returns:
        JSON response with success or error message.
    """
    try:
        ChallengesService.delete_challenge(challenge_id, current_user.id)
        
        response = make_response(jsonify({'message': 'Challenge deleted successfully'}), 200)
        return add_api_headers(response)
    
    except ValidationError as e:
        response = make_response(jsonify({'error': str(e)}), 403)
        return add_api_headers(response)
    
    except Exception as e:  # pragma: no cover - bubbled to client
        db.session.rollback()
        from flask import current_app
        current_app.logger.error(f'Failed to delete challenge: {str(e)}')
        response = make_response(
            jsonify({'error': 'Failed to delete challenge'}), 500
        )
        return add_api_headers(response)
