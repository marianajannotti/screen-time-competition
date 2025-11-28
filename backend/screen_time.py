"""Screen time API blueprint with validation helpers and allowed apps list."""

from datetime import date, datetime, timezone
from typing import Dict, Optional, Tuple

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from .database import db
from .models import ScreenTimeLog, canonicalize_app_name, list_allowed_apps

screen_time_bp = Blueprint(
    "screen_time",
    __name__,
    url_prefix="/api/screen-time",
)


class ValidationError(Exception):
    """Raised when a request payload fails validation rules."""


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
    except ValueError as exc:  # pragma: no cover - message important to client
        raise ValidationError(
            f"{field_name} must be formatted as YYYY-MM-DD."
        ) from exc


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
        _parse_date(provided_date, "date")
        if provided_date
        else datetime.now(timezone.utc).date()
    )

    return app_name, total_minutes, entry_date


@screen_time_bp.route("/", methods=["POST"])
@login_required
def create_screen_time_entry():
    """Persist a new screen time entry for the authenticated user.

    Returns:
        Response: JSON payload with the saved log or validation errors.
    """

    try:
        app_name, total_minutes, entry_date = _validate_payload(
            request.get_json()
        )

        new_log = ScreenTimeLog(
            user_id=current_user.id,
            app_name=app_name,
            date=entry_date,
            screen_time_minutes=total_minutes,
        )

        db.session.add(new_log)
        db.session.commit()

        return (
            jsonify(
                {
                    "message": "Screen time entry saved",
                    "log": new_log.to_dict(),
                }
            ),
            201,
        )

    except ValidationError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:  # pragma: no cover - bubbled to client
        db.session.rollback()
        return jsonify({"error": f"Unable to save entry: {exc}"}), 500


@screen_time_bp.route("/", methods=["GET"])
@login_required
def list_screen_time_entries():
    """Return screen time logs for the authenticated user with filters."""

    try:
        date_filter = _parse_date(request.args.get("date"), "date")
        start_date = _parse_date(request.args.get("start_date"), "start_date")
        end_date = _parse_date(request.args.get("end_date"), "end_date")
    except ValidationError as exc:
        return jsonify({"error": str(exc)}), 400

    limit_param = request.args.get("limit", 20)
    try:
        limit = max(1, min(int(limit_param), 100))
    except (TypeError, ValueError):
        return jsonify({"error": "limit must be an integer."}), 400

    app_name_filter = request.args.get("app_name")

    query = ScreenTimeLog.query.filter_by(user_id=current_user.id)

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

    logs = (
        query.order_by(
            ScreenTimeLog.date.desc(),
            ScreenTimeLog.created_at.desc(),
        )
        .limit(limit)
        .all()
    )

    return jsonify({"logs": [log.to_dict() for log in logs]}), 200


@screen_time_bp.route("/apps", methods=["GET"])
def get_allowed_apps():
    """Expose the canonical list of apps for dropdown selectors."""

    return jsonify({"apps": list_allowed_apps()}), 200
