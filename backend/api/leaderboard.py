"""Leaderboard API blueprint for global rankings."""

from flask import Blueprint, jsonify, request, make_response, current_app

from ..services.leaderboard_service import LeaderboardService
from ..utils.helpers import add_api_headers

leaderboard_bp = Blueprint(
    "leaderboard",
    __name__,
    url_prefix="/api/leaderboard",
)


@leaderboard_bp.route("/global", methods=["GET", "OPTIONS"])
def get_global_leaderboard():
    """Get the global leaderboard.

    Ranked by highest streak, with lowest avg screen time as tiebreaker.

    Query params:
        limit (int): Maximum users to return (default 50, max 100)

    Returns:
        Response: JSON with ranked list of users and their stats.
    """
    # Handle CORS preflight
    if request.method == "OPTIONS":
        response = make_response("", 200)
        return add_api_headers(response)

    try:
        limit_param = request.args.get("limit", 50)
        try:
            limit = int(limit_param)
            if limit < 1:
                raise ValueError("Limit must be at least 1")
            limit = min(limit, 100)
        except (TypeError, ValueError) as e:
            response = make_response(
                jsonify({"error": f"Invalid limit parameter: {e}"}),
                400,
            )
            return add_api_headers(response)

        leaderboard = LeaderboardService.get_global_leaderboard(limit=limit)

        response = make_response(
            jsonify({
                "leaderboard": leaderboard,
                "scope": "global",
            }),
            200,
        )
        return add_api_headers(response)

    except Exception as exc:
        # Log the actual error for debugging
        current_app.logger.error(f"Leaderboard error: {exc}")
        response = make_response(
            jsonify({"error": "Failed to retrieve leaderboard"}),
            500,
        )
        return add_api_headers(response)
