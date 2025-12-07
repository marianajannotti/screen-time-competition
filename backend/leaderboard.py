"""Leaderboard API blueprint for global rankings."""

from flask import Blueprint, jsonify, request, make_response

from .leaderboard_service import LeaderboardService
from .utils import add_api_headers

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
            limit = max(1, min(int(limit_param), 100))
        except (TypeError, ValueError):
            limit = 50

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
        response = make_response(
            jsonify({"error": f"Failed to get leaderboard: {exc}"}),
            500,
        )
        return add_api_headers(response)
