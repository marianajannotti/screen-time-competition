"""Screen time API blueprint with validation helpers and allowed apps list."""

from flask import Blueprint, jsonify, request, make_response
from flask_login import current_user, login_required

from ..database import db
from ..services.screen_time_service import ScreenTimeService, ValidationError
from ..utils.helpers import add_api_headers

screen_time_bp = Blueprint(
    "screen_time",
    __name__,
    url_prefix="/api/screen-time",
)


@screen_time_bp.route("/", methods=["POST"])
@login_required
def create_screen_time_entry():
    """Persist a new screen time entry for the authenticated user.

    Returns:
        Response: JSON payload with the saved log or validation errors.
    """

    try:
        new_log = ScreenTimeService.create_entry(
            user_id=current_user.id, data=request.get_json()
        )

        response = make_response(
            jsonify(
                {
                    "message": "Screen time entry saved",
                    "log": new_log.to_dict(),
                }
            ),
            201,
        )
        return add_api_headers(response)

    except ValidationError as exc:
        response = make_response(jsonify({"error": str(exc)}), 400)
        return add_api_headers(response)
    except Exception as exc:  # pragma: no cover - bubbled to client
        db.session.rollback()
        response = make_response(
            jsonify({"error": f"Unable to save entry: {exc}"}), 500
        )
        return add_api_headers(response)


@screen_time_bp.route("/", methods=["GET"])
@login_required
def list_screen_time_entries():
    """Return screen time logs for the authenticated user with filters."""

    try:
        limit_param = request.args.get("limit", 20)
        try:
            limit = max(1, min(int(limit_param), 100))
        except (TypeError, ValueError):
            response = make_response(
                jsonify({"error": "limit must be an integer."}), 400
            )
            return add_api_headers(response)

        logs = ScreenTimeService.get_entries(
            user_id=current_user.id,
            date_str=request.args.get("date"),
            start_date_str=request.args.get("start_date"),
            end_date_str=request.args.get("end_date"),
            app_name_filter=request.args.get("app_name"),
            limit=limit,
        )

        response = make_response(
            jsonify({"logs": [log.to_dict() for log in logs]}), 200
        )
        return add_api_headers(response)

    except ValidationError as exc:
        response = make_response(jsonify({"error": str(exc)}), 400)
        return add_api_headers(response)


@screen_time_bp.route("/apps", methods=["GET"])
def get_allowed_apps():
    """Expose the canonical list of apps for dropdown selectors."""

    response = make_response(
        jsonify({"apps": ScreenTimeService.get_allowed_apps()}), 200
    )
    return add_api_headers(response)
