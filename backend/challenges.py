"""Challenge routes for creating and managing screen time challenges."""

from flask import Blueprint, request, jsonify, make_response
from flask_login import login_required, current_user
from datetime import datetime, date
from sqlalchemy.orm import joinedload

from .database import db
from .models import Challenge, ChallengeParticipant, User
from .utils import current_time_utc, add_api_headers

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
        
        # Validate required fields
        required = ['name', 'target_app', 'target_minutes', 'start_date', 'end_date']
        if not all(field in data for field in required):
            response = make_response(jsonify({'error': 'Missing required fields'}), 400)
            return add_api_headers(response)
        
        try:
            start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
            end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
        except ValueError:
            response = make_response(jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400)
            return add_api_headers(response)
        
        # Validate dates
        if end_date <= start_date:
            response = make_response(jsonify({'error': 'End date must be after start date'}), 400)
            return add_api_headers(response)
        
        today = date.today()
        if start_date < today:
            response = make_response(jsonify({'error': 'Start date cannot be in the past'}), 400)
            return add_api_headers(response)
        
        # Determine initial status
        # Note: end_date is inclusive - challenge runs until end of that day (23:59:59)
        if start_date > today:
            status = 'upcoming'
        else:  # start_date == today
            status = 'active'
        
        # Create challenge
        challenge = Challenge(
            name=data['name'],
            description=data.get('description'),
            owner_id=current_user.id,
            target_app=data['target_app'],
            target_minutes=data['target_minutes'],
            start_date=start_date,
            end_date=end_date,
            status=status
        )
        
        db.session.add(challenge)
        db.session.flush()  # Get challenge.id
        
        # Add owner as participant
        owner_participant = ChallengeParticipant(
            challenge_id=challenge.id,
            user_id=current_user.id
        )
        db.session.add(owner_participant)
        
        # Add invited users as participants
        invited_ids = data.get('invited_user_ids', [])
        for user_id in invited_ids:
            if user_id != current_user.id:  # Don't duplicate owner
                participant = ChallengeParticipant(
                    challenge_id=challenge.id,
                    user_id=user_id
                )
                db.session.add(participant)
        
        db.session.commit()
        
        response = make_response(jsonify({
            'challenge': challenge.to_dict(),
            'message': 'Challenge created successfully'
        }), 201)
        return add_api_headers(response)
    
    except Exception as e:
        db.session.rollback()
        response = make_response(
            jsonify({'error': f'Failed to create challenge: {str(e)}'}), 500
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
    
    # Get all participations for current user
    participations = ChallengeParticipant.query.filter_by(
        user_id=current_user.id
    ).all()
    
    challenges_data = []
    for participation in participations:
        challenge = participation.challenge
        
        # Auto-complete expired challenges
        _check_and_complete_challenge(challenge)
        
        if challenge.status != 'deleted':  # Don't show deleted challenges
            challenge_dict = challenge.to_dict()
            # Add user's participation data
            challenge_dict['user_stats'] = participation.to_dict()
            challenges_data.append(challenge_dict)
    
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
    
    challenge = Challenge.query.get_or_404(challenge_id)
    
    # Check if user is a participant
    participation = ChallengeParticipant.query.filter_by(
        challenge_id=challenge_id,
        user_id=current_user.id
    ).first()
    
    if not participation:
        response = make_response(jsonify({'error': 'You are not a participant in this challenge'}), 403)
        return add_api_headers(response)
    
    challenge_dict = challenge.to_dict()
    challenge_dict['user_stats'] = participation.to_dict()
    
    response = make_response(jsonify({'challenge': challenge_dict}), 200)
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
    
    # Eager load owner to avoid N+1 query
    challenge = Challenge.query.options(joinedload(Challenge.owner)).get_or_404(challenge_id)
    
    # Check if user is a participant
    user_participation = ChallengeParticipant.query.filter_by(
        challenge_id=challenge_id,
        user_id=current_user.id
    ).first()
    
    if not user_participation:
        response = make_response(jsonify({'error': 'You are not a participant in this challenge'}), 403)
        return add_api_headers(response)
    
    # Get all participants with their stats
    participants = ChallengeParticipant.query.filter_by(
        challenge_id=challenge_id
    ).all()
    
    leaderboard = []
    for participant in participants:
        user = User.query.get(participant.user_id)
        if user:
            # Calculate average daily screen time for fair comparison
            # Division by zero is prevented by the conditional check (days_logged > 0)
            # Participants with no logged days are assigned a high value to sort last
            avg_daily = (participant.total_screen_time_minutes / participant.days_logged 
                        if participant.days_logged > 0 else float('inf'))
            
            leaderboard.append({
                'user_id': user.id,
                'username': user.username,
                'total_screen_time_minutes': participant.total_screen_time_minutes,
                'days_logged': participant.days_logged,
                'days_passed': participant.days_passed,
                'days_failed': participant.days_failed,
                'average_daily_minutes': round(avg_daily, 2),
                'final_rank': participant.final_rank,
                'is_winner': participant.is_winner
            })
    
    # Sort by average daily screen time (lowest first)
    leaderboard.sort(key=lambda x: x['average_daily_minutes'])
    
    response = make_response(jsonify({
        'challenge': challenge.to_dict(),
        'owner_username': challenge.owner.username if challenge.owner else 'Unknown',
        'leaderboard': leaderboard
    }), 200)
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
        challenge = Challenge.query.get_or_404(challenge_id)
        
        # Only owner can invite
        if challenge.owner_id != current_user.id:
            response = make_response(jsonify({'error': 'Only the challenge owner can invite members'}), 403)
            return add_api_headers(response)
        
        # Can't invite to completed or deleted challenges
        if challenge.status in ['completed', 'deleted']:
            response = make_response(jsonify({'error': 'Cannot invite to completed or deleted challenges'}), 400)
            return add_api_headers(response)
        
        data = request.get_json()
        user_ids = data.get('user_ids', [])
        
        invited_count = 0
        for user_id in user_ids:
            # Check if already participating
            existing = ChallengeParticipant.query.filter_by(
                challenge_id=challenge_id,
                user_id=user_id
            ).first()
            
            if not existing:
                participant = ChallengeParticipant(
                    challenge_id=challenge_id,
                    user_id=user_id
                )
                db.session.add(participant)
                invited_count += 1
        
        db.session.commit()
        
        response = make_response(jsonify({
            'message': f'Successfully invited {invited_count} member(s)',
            'invited_count': invited_count
        }), 200)
        return add_api_headers(response)
    
    except Exception as e:
        db.session.rollback()
        response = make_response(
            jsonify({'error': f'Failed to invite members: {str(e)}'}), 500
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
    # Enforce JSON Content-Type for consistency with other POST endpoints
    if not request.is_json:
        return jsonify({'error': 'Content-Type must be application/json'}), 415
    try:
        challenge = Challenge.query.get_or_404(challenge_id)
        
        # Find user's participation
        participation = ChallengeParticipant.query.filter_by(
            challenge_id=challenge_id,
            user_id=current_user.id
        ).first()
        
        if not participation:
            response = make_response(jsonify({'error': 'You are not a participant in this challenge'}), 400)
            return add_api_headers(response)
        
        # Don't allow owner to leave (they should delete instead)
        if challenge.owner_id == current_user.id:
            response = make_response(jsonify({'error': 'Challenge owner cannot leave. Delete the challenge instead.'}), 403)
            return add_api_headers(response)
        
        # Remove participation
        db.session.delete(participation)
        db.session.commit()
        
        response = make_response(jsonify({'message': 'Successfully left the challenge'}), 200)
        return add_api_headers(response)
    
    except Exception as e:
        db.session.rollback()
        response = make_response(
            jsonify({'error': f'Failed to leave challenge: {str(e)}'}), 500
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
        challenge = Challenge.query.get_or_404(challenge_id)
        
        # Only owner can delete
        if challenge.owner_id != current_user.id:
            response = make_response(jsonify({'error': 'Only the challenge owner can delete it'}), 403)
            return add_api_headers(response)
        
        # Mark as deleted instead of actually deleting (preserve data)
        challenge.status = 'deleted'
        db.session.commit()
        
        response = make_response(jsonify({'message': 'Challenge deleted successfully'}), 200)
        return add_api_headers(response)
    
    except Exception as e:
        db.session.rollback()
        response = make_response(
            jsonify({'error': f'Failed to delete challenge: {str(e)}'}), 500
        )
        return add_api_headers(response)


def _check_and_complete_challenge(challenge):
    """
    Checks if the challenge's end date has passed and, if so, completes the challenge.
    Assigns final ranks and winner(s) to participants who logged screen time, and marks the challenge as completed.
    Args:
        challenge (Challenge): The Challenge object to check and complete if needed.
    Returns:
        None. Modifies the challenge and its participants in-place and commits changes to the database.
    Notes:
        - Called when fetching challenges to automatically complete expired ones.
        - End date is inclusive; challenge runs until the end of that day.
        - Only participants who logged at least once are ranked and considered for winning.
    """
    today = date.today()
    
    # Auto-complete if end_date has passed and still active
    if today > challenge.end_date and challenge.status == 'active':
        # Get all participants
        participants = ChallengeParticipant.query.filter_by(
            challenge_id=challenge.id
        ).all()
        # Assign ranks and determine winners (inline logic)
        active_participants = [p for p in participants if p.days_logged > 0]
        if active_participants:
            # Sort by average daily screen time (lowest wins)
            active_participants.sort(key=lambda p: p.total_screen_time_minutes / p.days_logged)
            # Find the minimum average daily screen time
            min_avg = active_participants[0].total_screen_time_minutes / active_participants[0].days_logged
            # Assign ranks and mark completed
            for rank, participant in enumerate(active_participants, start=1):
                participant.final_rank = rank
                avg = participant.total_screen_time_minutes / participant.days_logged
                participant.is_winner = (avg == min_avg)
                participant.challenge_completed = True
        # Mark challenge as completed
        challenge.status = 'completed'
        challenge.completed_at = current_time_utc()
        db.session.commit()




