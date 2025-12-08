"""Service layer for friendship operations."""

from __future__ import annotations

from typing import Dict, List, Optional

from sqlalchemy import or_
from sqlalchemy.orm import selectinload

from .database import db
from .models import Friendship, User
from .utils import current_time_utc


class ValidationError(Exception):
    """Raised when a friendship request fails validation."""


class FriendshipService:
    """Business logic for managing friendship relationships."""

    @staticmethod
    def _find_existing_pair(
        user_id: int, friend_id: int
    ) -> Optional[Friendship]:
        """Lookup any friendship between two users in either direction."""

        return Friendship.query.filter(
            or_(
                (Friendship.user_id == user_id)
                & (Friendship.friend_id == friend_id),
                (Friendship.user_id == friend_id)
                & (Friendship.friend_id == user_id),
            )
        ).first()

    @staticmethod
    def _get_user_by_username(username: str) -> Optional[User]:
        """Return user by username or None when missing."""

        return User.query.filter_by(username=username.strip()).first()

    @staticmethod
    def send_request(requester_id: int, target_username: str) -> Friendship:
        """Create or revive a friend request.

        Args:
            requester_id (int): Authenticated user id issuing the request.
            target_username (str): Username to be added as friend.

        Returns:
            Friendship: Pending friendship record.

        Raises:
            ValidationError: When user not found, self add, or duplicate.
        """

        if not target_username or not target_username.strip():
            raise ValidationError("Username is required.")

        target_user = FriendshipService._get_user_by_username(target_username)
        if not target_user:
            raise ValidationError("User not found.")

        if target_user.id == requester_id:
            raise ValidationError("You cannot add yourself as a friend.")

        existing = FriendshipService._find_existing_pair(
            requester_id, target_user.id
        )

        if existing:
            if existing.status == "accepted":
                raise ValidationError("You are already friends.")

            if existing.status == "pending":
                raise ValidationError("A pending request already exists.")

            if existing.status == "rejected":
                # Delete the rejected record and create a new pending request
                db.session.delete(existing)
                db.session.commit()
                friendship = Friendship(
                    user_id=requester_id,
                    friend_id=target_user.id,
                    status="pending",
                )
                db.session.add(friendship)
                db.session.commit()
                return friendship

        friendship = Friendship(
            user_id=requester_id,
            friend_id=target_user.id,
            status="pending",
        )

        db.session.add(friendship)
        db.session.commit()

        return friendship

    @staticmethod
    def accept_request(user_id: int, friendship_id: int) -> Friendship:
        """Mark a pending request as accepted by the target user.

        Args:
            user_id (int): Authenticated user expected to be the target.
            friendship_id (int): Identifier of the friendship row.

        Returns:
            Friendship: Updated friendship marked accepted.

        Raises:
            ValidationError: When not found or not pending.
        """

        friendship = Friendship.query.get(friendship_id)

        if not friendship or friendship.friend_id != user_id:
            raise ValidationError("Request not found.")

        if friendship.status != "pending":
            raise ValidationError("Only pending requests can be accepted.")

        friendship.status = "accepted"
        db.session.commit()
        return friendship

    @staticmethod
    def reject_request(user_id: int, friendship_id: int) -> Friendship:
        """Mark a pending request as rejected by the target user.

        Args:
            user_id (int): Authenticated user expected to be the target.
            friendship_id (int): Identifier of the friendship row.

        Returns:
            Friendship: Updated friendship marked rejected.

        Raises:
            ValidationError: When not found or not pending.
        """

        friendship = Friendship.query.get(friendship_id)

        if not friendship or friendship.friend_id != user_id:
            raise ValidationError("Request not found.")

        if friendship.status != "pending":
            raise ValidationError("Only pending requests can be rejected.")

        friendship.status = "rejected"
        db.session.commit()
        return friendship

    @staticmethod
    def cancel_request(user_id: int, friendship_id: int) -> None:
        """Delete a pending outgoing request created by the requester.

        Args:
            user_id (int): Authenticated user expected to be requester.
            friendship_id (int): Identifier of the friendship row.

        Raises:
            ValidationError: When not found or not pending.
        """

        friendship = Friendship.query.get(friendship_id)

        if not friendship or friendship.user_id != user_id:
            raise ValidationError("Request not found.")

        if friendship.status != "pending":
            raise ValidationError("Only pending requests can be canceled.")

        db.session.delete(friendship)
        db.session.commit()

    @staticmethod
    def list_friendships(user_id: int) -> Dict[str, List[Dict]]:
        """Return friends and pending requests grouped by status.

        Args:
            user_id (int): Authenticated user for whom to list data.

        Returns:
            dict: Keys friends/incoming/outgoing with serialized payloads.
        """

        accepted = (
            Friendship.query.options(
                selectinload(Friendship.user), selectinload(Friendship.friend)
            )
            .filter(
                Friendship.status == "accepted",
                or_(
                    Friendship.user_id == user_id,
                    Friendship.friend_id == user_id,
                ),
            )
            .all()
        )

        incoming = (
            Friendship.query.options(
                selectinload(Friendship.user), selectinload(Friendship.friend)
            )
            .filter_by(status="pending", friend_id=user_id)
            .all()
        )

        outgoing = (
            Friendship.query.options(
                selectinload(Friendship.user), selectinload(Friendship.friend)
            )
            .filter_by(status="pending", user_id=user_id)
            .all()
        )

        return {
            "friends": [
                FriendshipService.serialize(f, viewer_id=user_id)
                for f in accepted
            ],
            "incoming": [
                FriendshipService.serialize(f, viewer_id=user_id)
                for f in incoming
            ],
            "outgoing": [
                FriendshipService.serialize(f, viewer_id=user_id)
                for f in outgoing
            ],
        }

    @staticmethod
    def serialize(friendship: Friendship, viewer_id: int) -> Dict:
        """Return a viewer-specific representation with counterpart details.

        Args:
            friendship (Friendship): Row to serialize.
            viewer_id (int): Authenticated user id to infer direction.

        Returns:
            dict: Friendship payload with direction and counterpart info.
        """

        # Use preloaded relationships instead of separate queries
        counterpart = (
            friendship.friend
            if friendship.user_id == viewer_id
            else friendship.user
        )

        return {
            **friendship.to_dict(),
            "direction": (
                "outgoing" if friendship.user_id == viewer_id else "incoming"
            ),
            "counterpart": counterpart.to_dict() if counterpart else None,
        }
