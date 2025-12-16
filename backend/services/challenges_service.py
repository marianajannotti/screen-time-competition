"""Service layer for challenges operations."""

from datetime import date
from typing import Dict, List, Optional, Tuple
import logging

from sqlalchemy.orm import joinedload

from ..database import db
from ..models import Challenge, ChallengeParticipant, User
from ..utils import current_time_utc

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Raised when a request payload fails validation rules."""


class ChallengesService:
    """Service class for challenges business logic."""

    @staticmethod
    def validate_challenge_creation(data: Dict, current_user_id: int) -> Tuple[str, str, str, int, date, date, str]:
        """
        Validate challenge creation data.
        
        Args:
            data: Dictionary containing challenge creation data
            current_user_id: ID of the user creating the challenge
            
        Returns:
            Tuple of (name, description, target_app, target_minutes, start_date, end_date, status)
            
        Raises:
            ValidationError: If validation fails
        """
        # Validate required fields
        required = ['name', 'target_app', 'target_minutes', 'start_date', 'end_date']
        if not all(field in data for field in required):
            raise ValidationError('Missing required fields')
        
        # Validate challenge name
        name = data['name'].strip() if isinstance(data['name'], str) else ''
        if not name:
            raise ValidationError('Challenge name cannot be empty')
        if len(name) > 200:
            raise ValidationError('Challenge name must be 200 characters or less')
        
        # Validate description
        description = data.get('description')
        
        # Validate target_app
        target_app = data['target_app']
        
        # Validate target_minutes (0 is valid for "no app" challenges)
        if not isinstance(data['target_minutes'], int) or data['target_minutes'] < 0:
            raise ValidationError('Target minutes must be a non-negative integer')
        target_minutes = data['target_minutes']
        
        # Parse and validate dates
        try:
            from datetime import datetime
            start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
            end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
        except ValueError:
            raise ValidationError('Invalid date format. Use YYYY-MM-DD')
        
        # Validate dates (end_date can equal start_date for one-day challenges)
        if end_date < start_date:
            raise ValidationError('End date cannot be before start date')
        
        today = date.today()
        if start_date < today:
            raise ValidationError('Start date cannot be in the past')
        
        # Determine initial status
        if start_date > today:
            status = 'upcoming'
        else:  # start_date == today
            status = 'active'
        
        return name, description, target_app, target_minutes, start_date, end_date, status

    @staticmethod
    def validate_user_ids(user_ids: List[int], exclude_user_id: Optional[int] = None) -> None:
        """
        Validate that all user IDs exist in the database.
        
        Args:
            user_ids: List of user IDs to validate
            exclude_user_id: Optional user ID to exclude from validation
            
        Raises:
            ValidationError: If any user ID doesn't exist
        """
        invalid_ids = []
        for user_id in user_ids:
            if exclude_user_id and user_id == exclude_user_id:
                continue
            user = db.session.get(User, user_id)
            if not user:
                invalid_ids.append(user_id)
        
        if invalid_ids:
            raise ValidationError(f'User IDs not found: {invalid_ids}')

    @staticmethod
    def create_challenge(
        name: str,
        description: Optional[str],
        owner_id: int,
        target_app: str,
        target_minutes: int,
        start_date: date,
        end_date: date,
        status: str,
        invited_user_ids: List[int]
    ) -> Challenge:
        """
        Create a new challenge and add participants.
        
        Args:
            name: Challenge name
            description: Optional challenge description
            owner_id: ID of the user creating the challenge
            target_app: Target app name or "__TOTAL__"
            target_minutes: Target minutes per day
            start_date: Challenge start date
            end_date: Challenge end date
            status: Initial challenge status
            invited_user_ids: List of user IDs to invite
            
        Returns:
            Created Challenge object
        """
        # Create challenge
        challenge = Challenge(
            name=name,
            description=description,
            owner_id=owner_id,
            target_app=target_app,
            target_minutes=target_minutes,
            start_date=start_date,
            end_date=end_date,
            status=status
        )
        
        db.session.add(challenge)
        db.session.flush()  # Get challenge.challenge_id
        
        # Add owner as participant with 'accepted' status
        owner_participant = ChallengeParticipant(
            challenge_id=challenge.challenge_id,
            user_id=owner_id,
            invitation_status='accepted'
        )
        db.session.add(owner_participant)
        
        # Add invited users as participants with 'pending' status (excluding owner)
        for user_id in invited_user_ids:
            if user_id != owner_id:
                participant = ChallengeParticipant(
                    challenge_id=challenge.challenge_id,
                    user_id=user_id,
                    invitation_status='pending'
                )
                db.session.add(participant)
        
        db.session.commit()
        
        # Recalculate challenge stats for owner from existing screen time logs
        try:
            from .screen_time_service import ScreenTimeService
            ScreenTimeService.recalculate_challenge_stats(challenge.challenge_id, owner_id)
        except Exception as e:
            logger.error(f"Error recalculating challenge stats after creation: {e}")
        
        # Note: Challenge Accepted badge is NOT awarded here
        # It should only be awarded when accepting an INVITATION to a challenge
        # The owner creates the challenge, they don't "accept" it
        
        return challenge

    @staticmethod
    def update_challenge(
        challenge_id: int,
        user_id: int,
        name: Optional[str] = None,
        new_invited_user_ids: Optional[List[int]] = None
    ) -> Challenge:
        """
        Update a challenge's name and/or add new participants.
        
        Args:
            challenge_id: ID of the challenge to update
            user_id: ID of the user making the update (must be owner)
            name: Optional new name for the challenge
            new_invited_user_ids: Optional list of new user IDs to invite
            
        Returns:
            Updated Challenge object
            
        Raises:
            ValidationError: If user is not the owner or validation fails
        """
        challenge = db.session.get(Challenge, challenge_id)
        if not challenge:
            raise ValidationError('Challenge not found')
        
        # Only owner can edit
        if challenge.owner_id != user_id:
            raise ValidationError('Only the challenge owner can edit it')
        
        # Cannot edit completed or deleted challenges
        if challenge.status in ['completed', 'deleted']:
            raise ValidationError(f'Cannot edit {challenge.status} challenges')
        
        # Update name if provided
        if name is not None:
            name = name.strip()
            if not name:
                raise ValidationError('Challenge name cannot be empty')
            if len(name) > 200:
                raise ValidationError('Challenge name must be 200 characters or less')
            challenge.name = name
        
        # Add new participants if provided
        if new_invited_user_ids:
            # Validate new user IDs exist
            ChallengesService.validate_user_ids(new_invited_user_ids, exclude_user_id=None)
            
            # Get existing participant user IDs
            existing_participants = {p.user_id for p in challenge.participants}
            
            # Add only new participants with 'pending' invitation status
            for user_id_to_add in new_invited_user_ids:
                if user_id_to_add not in existing_participants:
                    participant = ChallengeParticipant(
                        challenge_id=challenge.challenge_id,
                        user_id=user_id_to_add,
                        invitation_status='pending'
                    )
                    db.session.add(participant)
        
        db.session.commit()
        
        return challenge

    @staticmethod
    def get_user_challenges(user_id: int) -> List[Dict]:
        """
        Get all accepted challenges for a user (owned or participating), excluding deleted and pending invitations.
        
        Args:
            user_id: ID of the user
            
        Returns:
            List of challenge dictionaries with user stats
        """
        # Get all accepted participations for user
        participations = ChallengeParticipant.query.filter_by(
            user_id=user_id,
            invitation_status='accepted'
        ).all()
        
        challenges_data = []
        for participation in participations:
            challenge = participation.challenge
            
            # Auto-complete expired challenges
            ChallengesService.check_and_complete_challenge(challenge)
            
            if challenge.status != 'deleted':  # Don't show deleted challenges
                challenge_dict = challenge.to_dict()
                # Add user's participation data
                challenge_dict['user_stats'] = participation.to_dict()
                challenges_data.append(challenge_dict)
        
        return challenges_data

    @staticmethod
    def get_pending_invitations(user_id: int) -> List[Dict]:
        """
        Get all pending challenge invitations for a user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            List of challenge dictionaries with invitation details and owner info
        """
        # Get all pending participations for user
        participations = ChallengeParticipant.query.filter_by(
            user_id=user_id,
            invitation_status='pending'
        ).all()
        
        invitations = []
        for participation in participations:
            challenge = participation.challenge
            
            if challenge.status != 'deleted':  # Don't show deleted challenges
                challenge_dict = challenge.to_dict()
                challenge_dict['participant_id'] = participation.participant_id
                # Add owner information
                challenge_dict['owner_username'] = challenge.owner.username if challenge.owner else 'Unknown'
                invitations.append(challenge_dict)
        
        return invitations

    @staticmethod
    def respond_to_invitation(user_id: int, participant_id: int, accept: bool) -> ChallengeParticipant:
        """
        Accept or decline a challenge invitation.
        
        Args:
            user_id: ID of the user responding
            participant_id: ID of the participant record
            accept: True to accept, False to decline
            
        Returns:
            Updated ChallengeParticipant object
            
        Raises:
            ValidationError: If invitation not found or not pending
        """
        participation = db.session.get(ChallengeParticipant, participant_id)
        
        if not participation:
            raise ValidationError('Invitation not found')
        
        if participation.user_id != user_id:
            raise ValidationError('This invitation is not for you')
        
        if participation.invitation_status != 'pending':
            raise ValidationError('Invitation has already been responded to')
        
        if accept:
            participation.invitation_status = 'accepted'
        else:
            participation.invitation_status = 'declined'
            # Optionally, we could delete declined invitations instead
            # db.session.delete(participation)
        
        db.session.commit()
        
        # If accepted, recalculate challenge stats from existing screen time logs
        if accept:
            try:
                from .screen_time_service import ScreenTimeService
                ScreenTimeService.recalculate_challenge_stats(participation.challenge_id, user_id)
            except Exception as e:
                logger.error(f"Error recalculating challenge stats after accepting invitation: {e}")
            
            # Check and award challenge-related badges
            try:
                from .badge_achievement_service import BadgeAchievementService
                BadgeAchievementService.check_and_award_badges(user_id)
            except Exception as e:
                logger.error(f"Error checking badges after accepting challenge: {e}")
        
        return participation

    @staticmethod
    def get_challenge_by_id(challenge_id: int, user_id: int) -> Tuple[Challenge, ChallengeParticipant]:
        """
        Get a specific challenge if user is a participant.
        
        Args:
            challenge_id: ID of the challenge
            user_id: ID of the requesting user
            
        Returns:
            Tuple of (Challenge, ChallengeParticipant)
            
        Raises:
            ValidationError: If user is not a participant
        """
        challenge = Challenge.query.get_or_404(challenge_id)
        
        # Check if user is a participant
        participation = ChallengeParticipant.query.filter_by(
            challenge_id=challenge_id,
            user_id=user_id
        ).first()
        
        if not participation:
            raise ValidationError('You are not a participant in this challenge')
        
        return challenge, participation

    @staticmethod
    def get_leaderboard(challenge_id: int, user_id: int) -> Tuple[Challenge, List[Dict]]:
        """
        Get leaderboard for a challenge.
        
        Args:
            challenge_id: ID of the challenge
            user_id: ID of the requesting user
            
        Returns:
            Tuple of (Challenge, leaderboard list)
            
        Raises:
            ValidationError: If user is not a participant
        """
        # Eager load owner to avoid N+1 query
        challenge = Challenge.query.options(joinedload(Challenge.owner)).get_or_404(challenge_id)
        
        # Check if user is a participant
        user_participation = ChallengeParticipant.query.filter_by(
            challenge_id=challenge_id,
            user_id=user_id
        ).first()
        
        if not user_participation:
            raise ValidationError('You are not a participant in this challenge')
        
        # Get all participants with their stats
        participants = ChallengeParticipant.query.options(
            joinedload(ChallengeParticipant.user)
        ).filter_by(
            challenge_id=challenge_id
        ).all()
        
        leaderboard = []
        for participant in participants:
            user = participant.user
            if not user:
                continue  # Skip if user was deleted
            
            # Calculate average daily screen time for fair comparison
            if participant.days_logged > 0:
                avg_daily = round(participant.total_screen_time_minutes / participant.days_logged, 2)
            else:
                avg_daily = None  # Use None instead of infinity for JSON serialization
            
            leaderboard.append({
                'user_id': user.id,
                'username': user.username,
                'total_screen_time_minutes': participant.total_screen_time_minutes,
                'days_logged': participant.days_logged,
                'days_passed': participant.days_passed,
                'days_failed': participant.days_failed,
                'average_daily_minutes': avg_daily,
                'final_rank': participant.final_rank,
                'is_winner': participant.is_winner,
                'invitation_status': participant.invitation_status
            })
        
        # Sort by average daily screen time (lowest first, None values sort last)
        leaderboard.sort(key=lambda x: (x['average_daily_minutes'] is None, x['average_daily_minutes'] or 0))
        
        return challenge, leaderboard

    @staticmethod
    def invite_users(challenge_id: int, user_ids: List[int], current_user_id: int) -> int:
        """
        Invite users to a challenge.
        
        Args:
            challenge_id: ID of the challenge
            user_ids: List of user IDs to invite
            current_user_id: ID of the user making the request
            
        Returns:
            Count of successfully invited users
            
        Raises:
            ValidationError: If validation fails
        """
        challenge = Challenge.query.get_or_404(challenge_id)
        
        # Only owner can invite
        if challenge.owner_id != current_user_id:
            raise ValidationError('Only the challenge owner can invite members')
        
        # Can't invite to completed or deleted challenges
        if challenge.status in ['completed', 'deleted']:
            raise ValidationError('Cannot invite to completed or deleted challenges')
        
        # Validate all user IDs exist
        ChallengesService.validate_user_ids(user_ids)
        
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
        
        return invited_count

    @staticmethod
    def leave_challenge(challenge_id: int, user_id: int) -> None:
        """
        Remove a user from a challenge.
        
        Args:
            challenge_id: ID of the challenge
            user_id: ID of the user leaving
            
        Raises:
            ValidationError: If user is not a participant or is the owner
        """
        # Find user's participation
        participation = ChallengeParticipant.query.filter_by(
            challenge_id=challenge_id,
            user_id=user_id
        ).first()
        
        if not participation:
            raise ValidationError('You are not a participant in this challenge')
        
        # Don't allow owner to leave (they should delete instead)
        if participation.challenge.owner_id == user_id:
            raise ValidationError('Challenge owner cannot leave. Delete the challenge instead.')
        
        # Remove participation
        db.session.delete(participation)
        db.session.commit()

    @staticmethod
    def delete_challenge(challenge_id: int, user_id: int) -> None:
        """
        Mark a challenge as deleted (soft delete).
        
        Args:
            challenge_id: ID of the challenge
            user_id: ID of the user making the request
            
        Raises:
            ValidationError: If user is not the owner
        """
        challenge = Challenge.query.get_or_404(challenge_id)
        
        # Only owner can delete
        if challenge.owner_id != user_id:
            raise ValidationError('Only the challenge owner can delete it')
        
        # Mark as deleted instead of actually deleting (preserve data)
        challenge.status = 'deleted'
        db.session.commit()

    @staticmethod
    def check_and_complete_challenge(challenge: Challenge) -> None:
        """
        Check if challenge's end date has passed and complete it if needed.
        Assigns final ranks and winner(s) to participants.
        
        Args:
            challenge: The Challenge object to check and complete if needed
            
        Returns:
            None. Modifies the challenge and its participants in-place.
        """
        today = date.today()
        
        # Auto-complete if end_date has passed and still active
        if today > challenge.end_date and challenge.status == 'active':
            # Get all accepted participants
            participants = ChallengeParticipant.query.filter_by(
                challenge_id=challenge.challenge_id,
                invitation_status='accepted'
            ).all()
            
            if participants:
                # Calculate average daily screen time for each participant
                # For zero-hour challenges (target 0), users with no logs (0 avg) should win
                participant_averages = []
                for p in participants:
                    if p.days_logged > 0:
                        avg = p.total_screen_time_minutes / p.days_logged
                    else:
                        # No logs means 0 average (perfect for zero-target challenges)
                        avg = 0.0
                    participant_averages.append((p, avg))
                
                # Sort by average daily screen time (lowest wins)
                participant_averages.sort(key=lambda x: x[1])
                
                # Find the minimum average daily screen time
                min_avg = participant_averages[0][1]
                
                # Assign ranks with proper skipping for ties
                current_rank = 1
                for i, (participant, avg) in enumerate(participant_averages):
                    # If not first and average differs from previous, update rank
                    if i > 0 and avg != participant_averages[i-1][1]:
                        current_rank = i + 1
                    
                    participant.final_rank = current_rank
                    participant.is_winner = (avg == min_avg)
                    participant.challenge_completed = True
            
            # Mark challenge as completed
            challenge.status = 'completed'
            challenge.completed_at = current_time_utc()
            db.session.commit()
            
            # Check and award badges for all winners
            try:
                from .badge_achievement_service import BadgeAchievementService
                for participant in participants:
                    if participant.is_winner:
                        BadgeAchievementService.check_and_award_badges(participant.user_id)
            except Exception as e:
                logger.error(f"Error checking badges after completing challenge: {e}")
