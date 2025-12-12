"""Service layer for screen time operations."""

from datetime import date, datetime, timezone, timedelta
from typing import Dict, Optional, Tuple, List
import logging

from sqlalchemy import func, and_

from .database import db
from .models import ScreenTimeLog, User
from .utils import canonicalize_app_name, list_allowed_apps

logger = logging.getLogger(__name__)

class ValidationError(Exception):
    """Raised when a request payload fails validation rules."""


class ScreenTimeService:
    """Service class for screen time business logic."""

    @staticmethod
    def _parse_date(value: Optional[str], field_name: str) -> Optional[date]:
        """Convert a YYYY-MM-DD string into a ``date``.

        Args:
            value (str | None): Raw date string from query params or JSON.
            field_name (str): Name of the field for error messaging.

        Returns:
            date | None: Parsed date object when provided, else ``None``.

        Raises:
            ValidationError: If the string cannot be parsed.
        """

        if value in (None, ""):
            return None

        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError as exc:
            raise ValidationError(
                f"{field_name} must be formatted as YYYY-MM-DD."
            ) from exc

    @staticmethod
    def _validate_payload(data: Optional[Dict]) -> Tuple[str, int, date]:
        """Validate incoming JSON payload for the create endpoint.

        Args:
            data (dict | None): JSON body provided by the client.

        Returns:
            tuple[str, int, date]: Canonical app, total minutes, and entry date.

        Raises:
            ValidationError: If any field fails validation.
        """

        if not data:
            raise ValidationError("Request body is required.")

        try:
            app_name = canonicalize_app_name(data.get("app_name"))
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc

        if "hours" not in data and "minutes" not in data:
            raise ValidationError("Provide hours and/or minutes for the entry.")

        try:
            hours = int(data.get("hours", 0) or 0)
            minutes = int(data.get("minutes", 0) or 0)
        except (TypeError, ValueError) as exc:
            raise ValidationError(
                "Hours and minutes must be whole numbers."
            ) from exc

        if hours < 0:
            raise ValidationError("Hours must be zero or greater.")

        if minutes < 0 or minutes >= 60:
            raise ValidationError("Minutes must be between 0 and 59.")

        total_minutes = hours * 60 + minutes
        if total_minutes <= 0:
            raise ValidationError(
                "Total screen time must be greater than zero minutes."
            )

        provided_date = data.get("date")
        entry_date = (
            ScreenTimeService._parse_date(provided_date, "date")
            if provided_date
            else datetime.now(timezone.utc).date()
        )

        return app_name, total_minutes, entry_date

    @staticmethod
    def create_entry(user_id: int, data: Dict) -> ScreenTimeLog:
        """
        Create or update a screen time entry and update all relevant challenge stats for the user.

        If an entry already exists for the same user, app, and date,
        it will be updated with the new time. Otherwise, a new entry
        is created.

        Args:
            user_id (int): ID of the user creating the entry.
            data (dict): Raw data from the request.

        Returns:
            ScreenTimeLog: The created or updated log entry.

        Raises:
            ValidationError: If data is invalid.

        Side Effects:
            - Updates ChallengeParticipant stats for all active challenges the user is in (days_logged, total_screen_time_minutes, days_passed, days_failed).
            - Triggers badge logic to check and award badges if criteria are met.
            - Commits all changes to the database.
        """
        validated = ScreenTimeService._validate_payload(data)
        app_name, total_minutes, entry_date = validated

        # Check for existing entry with same user_id, app_name, and date
        existing_log = ScreenTimeLog.query.filter_by(
            user_id=user_id,
            app_name=app_name,
            date=entry_date
        ).first()

        # Validate total screen time consistency
        if app_name == "Total":
            # Get sum of all individual app times for this date
            app_logs = ScreenTimeLog.query.filter_by(
                user_id=user_id,
                date=entry_date
            ).filter(ScreenTimeLog.app_name != "Total").all()
            
            sum_of_apps = sum(log.screen_time_minutes for log in app_logs)
            
            if total_minutes < sum_of_apps:
                raise ValidationError(
                    f"Total screen time ({total_minutes // 60}h "
                    f"{total_minutes % 60}m) cannot be less than the sum "
                    f"of individual app times ({sum_of_apps // 60}h "
                    f"{sum_of_apps % 60}m)."
                )

        if existing_log:
            # Update existing entry
            existing_log.screen_time_minutes = total_minutes
            db.session.commit()
            log_to_return = existing_log
        else:
            # Create new entry
            new_log = ScreenTimeLog(
                user_id=user_id,
                app_name=app_name,
                date=entry_date,
                screen_time_minutes=total_minutes,
            )
            db.session.add(new_log)
            db.session.commit()
            log_to_return = new_log

        # --- Challenge stats update logic ---
        # Wrapped in try-except to ensure screen time log succeeds even if challenge stats fail
        try:
            from .models import Challenge, ChallengeParticipant
            from sqlalchemy.orm import selectinload
            
            # Find all active challenges for this user with eager loading to avoid N+1 queries
            active_challenges = Challenge.query.join(ChallengeParticipant).filter(
                ChallengeParticipant.user_id == user_id,
                Challenge.status == 'active',
                Challenge.start_date <= entry_date,
                Challenge.end_date >= entry_date,
                (Challenge.target_app == app_name) | (Challenge.target_app == '__TOTAL__')
            ).options(selectinload(Challenge.participants)).all()
            
            # Fetch all relevant screen time logs once for all challenges
            # Get the min/max date range across all challenges
            if active_challenges:
                # Bulk fetch all relevant ChallengeParticipant records for this user and these challenges
                challenge_ids = [challenge.id for challenge in active_challenges]
                participants = ChallengeParticipant.query.filter(
                    ChallengeParticipant.challenge_id.in_(challenge_ids),
                    ChallengeParticipant.user_id == user_id
                ).all()
                participant_map = {p.challenge_id: p for p in participants}
                
                min_start = min(c.start_date for c in active_challenges)
                max_end = max(c.end_date for c in active_challenges)
                
                # Fetch all logs in this date range in a single query
                all_logs = ScreenTimeLog.query.filter(
                    ScreenTimeLog.user_id == user_id,
                    ScreenTimeLog.date >= min_start,
                    ScreenTimeLog.date <= max_end
                ).all()
                
                # Process each challenge using the pre-fetched logs
                for challenge in active_challenges:
                    participant = participant_map.get(challenge.id)
                    if not participant:
                        continue
                    
                    # Filter logs for this specific challenge in Python
                    relevant_logs = [
                        log for log in all_logs
                        if challenge.start_date <= log.date <= challenge.end_date
                        and (challenge.target_app == '__TOTAL__' or log.app_name == challenge.target_app)
                    ]
                    
                    # Calculate stats from the filtered logs
                    if relevant_logs:
                        # Group by date and sum minutes per day
                        day_totals = {}
                        for log in relevant_logs:
                            day_totals[log.date] = day_totals.get(log.date, 0) + log.screen_time_minutes
                        
                        days_logged = len(day_totals)
                        total_minutes = sum(day_totals.values())
                        days_passed = sum(1 for daily_total in day_totals.values() if daily_total <= challenge.target_minutes)
                        days_failed = days_logged - days_passed
                    else:
                        days_logged = 0
                        total_minutes = 0
                        days_passed = 0
                        days_failed = 0
                    
                    # Update participant stats
                    participant.days_logged = days_logged
                    participant.total_screen_time_minutes = total_minutes
                    participant.days_passed = days_passed
                    participant.days_failed = days_failed
            
            db.session.commit()
        except Exception as e:
            db.session.rollback()  # Only rolls back challenge stats changes
            logger.error(f"Error updating challenge stats for user {user_id}: {e}")
            # Screen time log was already committed, so it succeeds regardless

        # Check and award badges after creating/updating a screen time entry
        try:
            from .badge_logic import BadgeLogic
        except ImportError as e:
            # Badge logic module is missing; log and continue
            logger.error(f"Badge logic import error for user {user_id}: {e}")
        else:
            try:
                awarded_badges = BadgeLogic.check_and_award_badges(user_id)
                if awarded_badges:
                    logger.info(
                        f"Awarded badges to user {user_id}: {awarded_badges}"
                    )
            except Exception as e:
                # Don't fail the screen time entry if badge logic fails
                logger.error(f"Badge logic error for user {user_id}: {e}")

        return log_to_return

    @staticmethod
    def get_entries(
        user_id: int,
        date_str: Optional[str] = None,
        start_date_str: Optional[str] = None,
        end_date_str: Optional[str] = None,
        app_name_filter: Optional[str] = None,
        limit: int = 20,
    ) -> List[ScreenTimeLog]:
        """Retrieve screen time entries with filtering.

        Args:
            user_id (int): ID of the user.
            date_str (str, optional): Specific date to filter by.
            start_date_str (str, optional): Start date for range filter.
            end_date_str (str, optional): End date for range filter.
            app_name_filter (str, optional): App name substring to filter by.
            limit (int): Maximum number of results to return.

        Returns:
            List[ScreenTimeLog]: List of matching log entries.

        Raises:
            ValidationError: If date strings are invalid.
        """
        date_filter = ScreenTimeService._parse_date(date_str, "date")
        start_date = ScreenTimeService._parse_date(
            start_date_str, "start_date"
        )
        end_date = ScreenTimeService._parse_date(end_date_str, "end_date")

        query = ScreenTimeLog.query.filter_by(user_id=user_id)

        if app_name_filter:
            query = query.filter(
                ScreenTimeLog.app_name.ilike(f"%{app_name_filter}%")
            )

        if date_filter:
            query = query.filter(ScreenTimeLog.date == date_filter)
        else:
            if start_date:
                query = query.filter(ScreenTimeLog.date >= start_date)
            if end_date:
                query = query.filter(ScreenTimeLog.date <= end_date)

        return (
            query.order_by(
                ScreenTimeLog.date.desc(),
                ScreenTimeLog.created_at.desc(),
            )
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_allowed_apps() -> List[str]:
        """Return the list of allowed apps."""
        return list_allowed_apps()

    # Statistical Analysis Methods
    @staticmethod
    def get_baseline_average(user_id: int) -> Optional[float]:
        """Get user's baseline average (first week of data).
        
        Args:
            user_id (int): ID of the user
            
        Returns:
            float or None: Average screen time in minutes for the first week, or None if insufficient data
        """
        try:
            first_log = ScreenTimeLog.query.filter_by(user_id=user_id).order_by(ScreenTimeLog.date).first()
            if not first_log:
                return None
            
            baseline_start = first_log.date
            baseline_end = baseline_start + timedelta(days=6)
            
            result = db.session.query(func.avg(ScreenTimeLog.screen_time_minutes)).filter(
                and_(
                    ScreenTimeLog.user_id == user_id,
                    ScreenTimeLog.date >= baseline_start,
                    ScreenTimeLog.date <= baseline_end
                )
            ).scalar()
            
            return result
        except Exception:
            return None
    
    @staticmethod
    def get_recent_week_average(user_id: int) -> Optional[float]:
        """Get user's average screen time for the most recent week.
        
        Args:
            user_id (int): ID of the user
            
        Returns:
            float or None: Average screen time in minutes for the recent week, or None if insufficient data
        """
        try:
            end_date = date.today()
            start_date = end_date - timedelta(days=6)
            
            result = db.session.query(func.avg(ScreenTimeLog.screen_time_minutes)).filter(
                and_(
                    ScreenTimeLog.user_id == user_id,
                    ScreenTimeLog.date >= start_date,
                    ScreenTimeLog.date <= end_date
                )
            ).scalar()
            
            return result
        except Exception:
            return None
    
    @staticmethod
    def get_monthly_average(user_id: int) -> Optional[float]:
        """Get user's average screen time for the past month.
        
        Args:
            user_id (int): ID of the user
            
        Returns:
            float or None: Average screen time in minutes for the past month, or None if insufficient data
        """
        try:
            end_date = date.today()
            start_date = end_date - timedelta(days=29)  # 30 days total
            
            result = db.session.query(func.avg(ScreenTimeLog.screen_time_minutes)).filter(
                and_(
                    ScreenTimeLog.user_id == user_id,
                    ScreenTimeLog.date >= start_date,
                    ScreenTimeLog.date <= end_date
                )
            ).scalar()
            
            return result
        except Exception:
            return None
    
    @staticmethod
    def get_user_weekly_rank(user_id: int) -> Optional[int]:
        """Get user's rank for the current week based on lowest screen time.
        
        Args:
            user_id (int): ID of the user
            
        Returns:
            int or None: User's rank (1-based), or None if no data
        """
        try:
            end_date = date.today()
            start_date = end_date - timedelta(days=6)
            
            # Get weekly totals for all users
            weekly_totals = db.session.query(
                ScreenTimeLog.user_id,
                func.sum(ScreenTimeLog.screen_time_minutes).label('total_minutes')
            ).filter(
                and_(
                    ScreenTimeLog.date >= start_date,
                    ScreenTimeLog.date <= end_date
                )
            ).group_by(ScreenTimeLog.user_id).order_by('total_minutes').all()
            
            # Find user's rank (1-based)
            for rank, (uid, _) in enumerate(weekly_totals, 1):
                if uid == user_id:
                    return rank
            
            return None
        except Exception:
            return None
    
    @staticmethod
    def check_weekend_achievement(user_id: int, threshold_minutes: int = 180) -> bool:
        """Check if user met goals on both Saturday and Sunday of any weekend.
        
        Args:
            user_id (int): ID of the user
            threshold_minutes (int): Maximum minutes allowed per day (default: 180 = 3 hours)
            
        Returns:
            bool: True if user has a weekend where both days are under threshold
        """
        try:
            # Get recent weekend days (Saturday=5, Sunday=6)
            logs = ScreenTimeLog.query.filter(
                ScreenTimeLog.user_id == user_id
            ).order_by(ScreenTimeLog.date.desc()).limit(60).all()
            
            # Filter weekend days in Python for cross-database compatibility
            weekend_logs = [log for log in logs if log.date.weekday() in [5, 6]]  # Saturday=5, Sunday=6
            
            # Group by weekend and check if both days are under threshold
            weekends = {}
            for log in weekend_logs:
                week_start = log.date - timedelta(days=log.date.weekday())
                if week_start not in weekends:
                    weekends[week_start] = []
                weekends[week_start].append(log.screen_time_minutes)
            
            # Check if any weekend has both days under threshold
            for weekend_logs_list in weekends.values():
                if len(weekend_logs_list) >= 2 and all(minutes < threshold_minutes for minutes in weekend_logs_list):
                    return True
            
            return False
        except Exception:
            return False
    
    @staticmethod
    def check_low_usage_day(user_id: int, max_minutes: int = 60) -> bool:
        """Check if user had any day under the specified usage threshold.
        
        Args:
            user_id (int): ID of the user
            max_minutes (int): Maximum minutes threshold (default: 60 = 1 hour)
            
        Returns:
            bool: True if user has at least one day under the threshold
        """
        try:
            low_usage_day = ScreenTimeLog.query.filter(
                and_(
                    ScreenTimeLog.user_id == user_id,
                    ScreenTimeLog.screen_time_minutes < max_minutes
                )
            ).first()
            
            return low_usage_day is not None
        except Exception:
            return False
