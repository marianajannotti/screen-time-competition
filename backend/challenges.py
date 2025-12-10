"""Challenge routes for creating and managing screen time challenges."""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, date

from .database import db
from .models import Challenge, ChallengeParticipant, User

challenges_bp = Blueprint('challenges', __name__, url_prefix='/api/challenges')


@challenges_bp.route('', methods=['POST'])
@login_required
def create_challenge():
    """Create a new challenge.
    
    Expected JSON:
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
    data = request.get_json()
    
    # Validate required fields
    required = ['name', 'target_app', 'target_minutes', 'start_date', 'end_date']
    if not all(field in data for field in required):
        return jsonify({'error': 'Missing required fields'}), 400
    
    try:
        start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
    
    # Validate dates
    if end_date <= start_date:
        return jsonify({'error': 'End date must be after start date'}), 400
    
    today = date.today()
    if start_date < today:
        return jsonify({'error': 'Start date cannot be in the past'}), 400
    
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
    
    return jsonify({
        'challenge': challenge.to_dict(),
        'message': 'Challenge created successfully'
    }), 201


@challenges_bp.route('', methods=['GET'])
@login_required
def get_challenges():
    """Get all challenges for the current user (owned or participating)."""
    
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
    
    return jsonify({'challenges': challenges_data}), 200


@challenges_bp.route('/<int:challenge_id>', methods=['GET'])
@login_required
def get_challenge(challenge_id):
    """Get a specific challenge with full details."""
    
    challenge = Challenge.query.get_or_404(challenge_id)
    
    # Check if user is a participant
    participation = ChallengeParticipant.query.filter_by(
        challenge_id=challenge_id,
        user_id=current_user.id
    ).first()
    
    if not participation:
        return jsonify({'error': 'You are not a participant in this challenge'}), 403
    
    challenge_dict = challenge.to_dict()
    challenge_dict['user_stats'] = participation.to_dict()
    
    return jsonify({'challenge': challenge_dict}), 200


@challenges_bp.route('/<int:challenge_id>/leaderboard', methods=['GET'])
@login_required
def get_leaderboard(challenge_id):
    """Get live leaderboard for a challenge showing all participants and their stats."""
    
    challenge = Challenge.query.get_or_404(challenge_id)
    
    # Check if user is a participant
    user_participation = ChallengeParticipant.query.filter_by(
        challenge_id=challenge_id,
        user_id=current_user.id
    ).first()
    
    if not user_participation:
        return jsonify({'error': 'You are not a participant in this challenge'}), 403
    
    # Get all participants with their stats
    participants = ChallengeParticipant.query.filter_by(
        challenge_id=challenge_id
    ).all()
    
    leaderboard = []
    for participant in participants:
        user = User.query.get(participant.user_id)
        if user:
            # Calculate average daily screen time for fair comparison
            avg_daily = (participant.total_screen_time_minutes / participant.days_logged 
                        if participant.days_logged > 0 else 999999)
            
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
    
    # Get owner info
    owner = User.query.get(challenge.owner_id)
    
    return jsonify({
        'challenge': challenge.to_dict(),
        'owner_username': owner.username if owner else 'Unknown',
        'leaderboard': leaderboard
    }), 200


@challenges_bp.route('/<int:challenge_id>/invite', methods=['POST'])
@login_required
def invite_to_challenge(challenge_id):
    """Invite additional members to a challenge (only owner can invite).
    
    Expected JSON:
        {
            "user_ids": [5, 6, 7]
        }
    """
    challenge = Challenge.query.get_or_404(challenge_id)
    
    # Only owner can invite
    if challenge.owner_id != current_user.id:
        return jsonify({'error': 'Only the challenge owner can invite members'}), 403
    
    # Can't invite to completed or deleted challenges
    if challenge.status in ['completed', 'deleted']:
        return jsonify({'error': 'Cannot invite to completed or deleted challenges'}), 400
    
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
    
    return jsonify({
        'message': f'Successfully invited {invited_count} member(s)',
        'invited_count': invited_count
    }), 200


@challenges_bp.route('/<int:challenge_id>/leave', methods=['POST'])
@login_required
def leave_challenge(challenge_id):
    """Leave a challenge (any participant can leave, except owner)."""
    
    challenge = Challenge.query.get_or_404(challenge_id)
    
    # Find user's participation
    participation = ChallengeParticipant.query.filter_by(
        challenge_id=challenge_id,
        user_id=current_user.id
    ).first()
    
    if not participation:
        return jsonify({'error': 'You are not a participant in this challenge'}), 400
    
    # Don't allow owner to leave (they should delete instead)
    if challenge.owner_id == current_user.id:
        return jsonify({'error': 'Challenge owner cannot leave. Delete the challenge instead.'}), 403
    
    # Remove participation
    db.session.delete(participation)
    db.session.commit()
    
    return jsonify({'message': 'Successfully left the challenge'}), 200


@challenges_bp.route('/<int:challenge_id>', methods=['DELETE'])
@login_required
def delete_challenge(challenge_id):
    """Delete a challenge (only owner can delete)."""
    
    challenge = Challenge.query.get_or_404(challenge_id)
    
    # Only owner can delete
    if challenge.owner_id != current_user.id:
        return jsonify({'error': 'Only the challenge owner can delete it'}), 403
    
    # Mark as deleted instead of actually deleting (preserve data)
    challenge.status = 'deleted'
    db.session.commit()
    
    return jsonify({'message': 'Challenge deleted successfully'}), 200


def _check_and_complete_challenge(challenge):
    """Helper to auto-complete a challenge if end_date has passed.
    
    Called when fetching challenges to automatically complete expired ones.
    End date is inclusive - challenge runs until end of that day.
    """
    today = date.today()
    
    # Auto-complete if end_date has passed and still active
    if today > challenge.end_date and challenge.status == 'active':
        # Get all participants
        participants = ChallengeParticipant.query.filter_by(
            challenge_id=challenge.id
        ).all()
        
        # Use helper function to assign ranks and winners
        _assign_ranks_and_winners(participants)
        
        # Mark challenge as completed
        challenge.status = 'completed'
        challenge.completed_at = datetime.utcnow()
        
        db.session.commit()


@challenges_bp.route('/<int:challenge_id>/complete', methods=['POST'])
@login_required
def complete_challenge(challenge_id):
    """Manually complete a challenge early (owner only).
    
    Normally challenges auto-complete when end_date passes.
    This allows owner to end a challenge early if needed.
    """
    
    challenge = Challenge.query.get_or_404(challenge_id)
    
    # Only owner can manually complete
    if challenge.owner_id != current_user.id:
        return jsonify({'error': 'Only the challenge owner can manually complete it'}), 403
    
    # Check if already completed
    if challenge.status == 'completed':
        return jsonify({'error': 'Challenge already completed'}), 400
    
    # Get all participants
    participants = ChallengeParticipant.query.filter_by(
        challenge_id=challenge_id
    ).all()
    
    # Use helper function to assign ranks and winners
    active_participants = _assign_ranks_and_winners(participants)
    
    # Mark challenge as completed
    challenge.status = 'completed'
    challenge.completed_at = datetime.utcnow()
    
    db.session.commit()
    
    winner_info = None
    if active_participants:
        winner_participant = active_participants[0]
        winner_user = User.query.get(winner_participant.user_id)
        if winner_user:
            winner_info = {
                'user_id': winner_user.id,
                'username': winner_user.username,
                'average_daily_minutes': round(
                    winner_participant.total_screen_time_minutes / winner_participant.days_logged, 2
                )
            }
    
    return jsonify({
        'message': 'Challenge completed successfully',
        'winner': winner_info
    }), 200

def _assign_ranks_and_winners(participants):
    """Helper function to assign ranks and determine winners.
    
    Args:
        participants: List of ChallengeParticipant objects
        
    Returns:
        List of active participants (those who logged at least once), sorted by rank
    """
    # Filter to those who logged at least once
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
    
    return active_participants
