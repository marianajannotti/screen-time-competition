"""Friendship API blueprint."""

from flask import Blueprint, jsonify, make_response, request
from flask_login import current_user, login_required

from .database import db
from .friendship_service import FriendshipService, ValidationError
from .utils import add_api_headers

friendship_bp = Blueprint(
    "friendship",
    __name__,
    url_prefix="/api/friendships",
)


@friendship_bp.route("/", methods=["GET"])
@login_required
def list_friendships():
    """Return accepted friends plus incoming/outgoing pending requests."""

    data = FriendshipService.list_friendships(user_id=current_user.id)
    response = make_response(jsonify(data), 200)
    return add_api_headers(response)


@friendship_bp.route("/request", methods=["POST"])
@login_required
def send_request():
    """Create a pending request to another user.

    Input JSON: {"username": "target_username"}
    Returns 201 with serialized friendship on success.
    """

    if request.content_type != "application/json":
        response = make_response(
            jsonify({"error": "Content-Type must be application/json"}), 415
        )
        return add_api_headers(response)

    try:
        payload = request.get_json() or {}
        friendship = FriendshipService.send_request(
            requester_id=current_user.id,
            target_username=payload.get("username"),
        )

        response = make_response(
            jsonify(
                {
                    "message": "Friend request sent.",
                    "friendship": FriendshipService.serialize(
                        friendship, viewer_id=current_user.id
                    ),
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
            jsonify({"error": f"Unable to send request: {exc}"}), 500
        )
        return add_api_headers(response)


@friendship_bp.route("/<int:friendship_id>/accept", methods=["POST"])
@login_required
def accept_request(friendship_id: int):
    """Accept a pending request targeted at the authenticated user."""

    try:
        friendship = FriendshipService.accept_request(
            user_id=current_user.id, friendship_id=friendship_id
        )
        response = make_response(
            jsonify(
                {
                    "message": "Friend request accepted.",
                    "friendship": FriendshipService.serialize(
                        friendship, viewer_id=current_user.id
                    ),
                }
            ),
            200,
        )
        return add_api_headers(response)

    except ValidationError as exc:
        response = make_response(jsonify({"error": str(exc)}), 400)
        return add_api_headers(response)
    except Exception as exc:  # pragma: no cover - bubbled to client
        db.session.rollback()
        response = make_response(
            jsonify({"error": f"Unable to accept request: {exc}"}), 500
        )
        return add_api_headers(response)


@friendship_bp.route("/<int:friendship_id>/reject", methods=["POST"])
@login_required
def reject_request(friendship_id: int):
    """Reject a pending request targeted at the authenticated user."""

    try:
        friendship = FriendshipService.reject_request(
            user_id=current_user.id, friendship_id=friendship_id
        )
        response = make_response(
            jsonify(
                {
                    "message": "Friend request rejected.",
                    "friendship": FriendshipService.serialize(
                        friendship, viewer_id=current_user.id
                    ),
                }
            ),
            200,
        )
        return add_api_headers(response)

    except ValidationError as exc:
        response = make_response(jsonify({"error": str(exc)}), 400)
        return add_api_headers(response)
    except Exception as exc:  # pragma: no cover - bubbled to client
        db.session.rollback()
        response = make_response(
            jsonify({"error": f"Unable to reject request: {exc}"}), 500
        )
        return add_api_headers(response)


@friendship_bp.route("/<int:friendship_id>/cancel", methods=["POST"])
@login_required
def cancel_request(friendship_id: int):
    """Cancel a pending outgoing request created by the authenticated user."""

    try:
        FriendshipService.cancel_request(
            user_id=current_user.id, friendship_id=friendship_id
        )
        response = make_response(
            jsonify({"message": "Friend request canceled."}), 200
        )
        return add_api_headers(response)

    except ValidationError as exc:
        response = make_response(jsonify({"error": str(exc)}), 400)
        return add_api_headers(response)
    except Exception as exc:  # pragma: no cover - bubbled to client
        db.session.rollback()
        response = make_response(
            jsonify({"error": "Unable to cancel request."}), 500
        )
        return add_api_headers(response)