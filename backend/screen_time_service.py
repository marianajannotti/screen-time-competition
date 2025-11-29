"""Service layer for screen time operations."""

from datetime import date, datetime, timezone
from typing import Dict, Optional, Tuple, List

from .database import db
from .models import ScreenTimeLog
from .utils import canonicalize_app_name, list_allowed_apps


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
        """Create a new screen time entry.

        Args:
            user_id (int): ID of the user creating the entry.
            data (dict): Raw data from the request.

        Returns:
            ScreenTimeLog: The created log entry.

        Raises:
            ValidationError: If data is invalid.
        """
        app_name, total_minutes, entry_date = ScreenTimeService._validate_payload(data)

        new_log = ScreenTimeLog(
            user_id=user_id,
            app_name=app_name,
            date=entry_date,
            screen_time_minutes=total_minutes,
        )

        db.session.add(new_log)
        db.session.commit()

        return new_log

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
        start_date = ScreenTimeService._parse_date(start_date_str, "start_date")
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
