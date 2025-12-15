"""Unit tests for the FriendshipService.

This module contains test cases for the FriendshipService class,
covering friend request management and friendship operations.
"""
import unittest

from backend import create_app
from backend.database import db
from backend.models import User, Friendship
from backend.services import FriendshipService
from backend.services.friendship_service import ValidationError


class FriendshipServiceTestCase(unittest.TestCase):
    """Base test case for FriendshipService unit tests.

    Provides common setup and teardown for all friendship service tests.
    """

    def setUp(self):
        """Create app context, database, and test fixtures.

        Returns:
            None
        """
        self.app = create_app("testing")
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Create test users
        self.user1 = User(
            username="user1",
            email="user1@example.com",
            password_hash="hash"
        )
        self.user2 = User(
            username="user2",
            email="user2@example.com",
            password_hash="hash"
        )
        self.user3 = User(
            username="user3",
            email="user3@example.com",
            password_hash="hash"
        )
        
        db.session.add_all([self.user1, self.user2, self.user3])
        db.session.commit()

    def tearDown(self):
        """Clean up database and app context.

        Returns:
            None
        """
        db.session.remove()
        db.drop_all()
        db.engine.dispose()
        self.app_context.pop()


class TestListFriendships(FriendshipServiceTestCase):
    """Test listing friendships functionality."""

    def test_list_friendships_empty(self):
        """Verify that empty lists are returned for user with no friendships.

        Returns:
            None
        """
        data = FriendshipService.list_friendships(self.user1.id)
        
        self.assertEqual(len(data["friends"]), 0)
        self.assertEqual(len(data["incoming"]), 0)
        self.assertEqual(len(data["outgoing"]), 0)

    def test_list_friendships_with_accepted_friends(self):
        """Verify that accepted friendships appear in friends list.

        Returns:
            None
        """
        # Create accepted friendship
        friendship = Friendship(
            user_id=self.user1.id,
            friend_id=self.user2.id,
            status="accepted"
        )
        db.session.add(friendship)
        db.session.commit()

        data = FriendshipService.list_friendships(self.user1.id)
        
        self.assertEqual(len(data["friends"]), 1)
        self.assertEqual(data["friends"][0]["counterpart"]["username"], "user2")

    def test_list_friendships_with_incoming_requests(self):
        """Verify that incoming pending requests appear in incoming list.

        Returns:
            None
        """
        # Create pending friendship where user1 is target
        friendship = Friendship(
            user_id=self.user2.id,
            friend_id=self.user1.id,
            status="pending"
        )
        db.session.add(friendship)
        db.session.commit()

        data = FriendshipService.list_friendships(self.user1.id)
        
        self.assertEqual(len(data["incoming"]), 1)
        self.assertEqual(data["incoming"][0]["counterpart"]["username"], "user2")

    def test_list_friendships_with_outgoing_requests(self):
        """Verify that outgoing pending requests appear in outgoing list.

        Returns:
            None
        """
        # Create pending friendship where user1 is requester
        friendship = Friendship(
            user_id=self.user1.id,
            friend_id=self.user2.id,
            status="pending"
        )
        db.session.add(friendship)
        db.session.commit()

        data = FriendshipService.list_friendships(self.user1.id)
        
        self.assertEqual(len(data["outgoing"]), 1)
        self.assertEqual(data["outgoing"][0]["counterpart"]["username"], "user2")


class TestSendRequest(FriendshipServiceTestCase):
    """Test sending friend requests."""

    def test_send_request_success(self):
        """Verify that friend request is sent successfully.

        Returns:
            None
        """
        friendship = FriendshipService.send_request(
            requester_id=self.user1.id,
            target_username="user2"
        )
        
        self.assertIsNotNone(friendship)
        self.assertEqual(friendship.user_id, self.user1.id)
        self.assertEqual(friendship.friend_id, self.user2.id)
        self.assertEqual(friendship.status, "pending")

    def test_send_request_to_nonexistent_user(self):
        """Verify that request to nonexistent user raises ValidationError.

        Returns:
            None
        """
        with self.assertRaises(ValidationError):
            FriendshipService.send_request(
                requester_id=self.user1.id,
                target_username="nonexistent"
            )

    def test_send_request_to_self(self):
        """Verify that request to self raises ValidationError.

        Returns:
            None
        """
        with self.assertRaises(ValidationError):
            FriendshipService.send_request(
                requester_id=self.user1.id,
                target_username="user1"
            )

    def test_send_request_empty_username(self):
        """Verify that empty username raises ValidationError.

        Returns:
            None
        """
        with self.assertRaises(ValidationError):
            FriendshipService.send_request(
                requester_id=self.user1.id,
                target_username=""
            )

    def test_send_request_duplicate_pending(self):
        """Verify that duplicate pending request raises ValidationError.

        Returns:
            None
        """
        # Send first request
        FriendshipService.send_request(
            requester_id=self.user1.id,
            target_username="user2"
        )
        
        # Try to send another request
        with self.assertRaises(ValidationError):
            FriendshipService.send_request(
                requester_id=self.user1.id,
                target_username="user2"
            )

    def test_send_request_already_friends(self):
        """Verify that request to existing friend raises ValidationError.

        Returns:
            None
        """
        # Create accepted friendship
        friendship = Friendship(
            user_id=self.user1.id,
            friend_id=self.user2.id,
            status="accepted"
        )
        db.session.add(friendship)
        db.session.commit()

        # Try to send request
        with self.assertRaises(ValidationError):
            FriendshipService.send_request(
                requester_id=self.user1.id,
                target_username="user2"
            )


class TestAcceptRequest(FriendshipServiceTestCase):
    """Test accepting friend requests."""

    def test_accept_request_success(self):
        """Verify that friend request is accepted successfully.

        Returns:
            None
        """
        # Create pending friendship - user1 sends request to user2
        friendship = Friendship(
            user_id=self.user1.id,  # requester
            friend_id=self.user2.id,  # target
            status="pending"
        )
        db.session.add(friendship)
        db.session.commit()

        # user2 accepts the request
        accepted_friendship = FriendshipService.accept_request(
            user_id=self.user2.id,
            friendship_id=friendship.id
        )
        
        self.assertEqual(accepted_friendship.status, "accepted")

    def test_accept_request_not_found(self):
        """Verify that accepting nonexistent request raises ValidationError.

        Returns:
            None
        """
        with self.assertRaises(ValidationError):
            FriendshipService.accept_request(
                user_id=self.user1.id,
                friendship_id=99999
            )

    def test_accept_request_not_target(self):
        """Verify that accepting request for wrong user raises ValidationError.

        Returns:
            None
        """
        # Create pending friendship where user1 sends to user2
        friendship = Friendship(
            user_id=self.user1.id,  # requester
            friend_id=self.user2.id,  # target
            status="pending"
        )
        db.session.add(friendship)
        db.session.commit()

        # Try to accept as user3 (not the target)
        with self.assertRaises(ValidationError):
            FriendshipService.accept_request(
                user_id=self.user3.id,
                friendship_id=friendship.id
            )

    def test_accept_request_already_accepted(self):
        """Verify that accepting already accepted request raises ValidationError.

        Returns:
            None
        """
        # Create accepted friendship
        friendship = Friendship(
            user_id=self.user1.id,
            friend_id=self.user2.id,
            status="accepted"
        )
        db.session.add(friendship)
        db.session.commit()

        with self.assertRaises(ValidationError):
            FriendshipService.accept_request(
                user_id=self.user2.id,
                friendship_id=friendship.id
            )


class TestRejectRequest(FriendshipServiceTestCase):
    """Test rejecting friend requests."""

    def test_reject_request_success(self):
        """Verify that friend request is rejected successfully.

        Returns:
            None
        """
        # Create pending friendship
        friendship = Friendship(
            user_id=self.user1.id,
            friend_id=self.user2.id,
            status="pending"
        )
        db.session.add(friendship)
        db.session.commit()

        rejected_friendship = FriendshipService.reject_request(
            user_id=self.user2.id,
            friendship_id=friendship.id
        )
        
        self.assertEqual(rejected_friendship.status, "rejected")

    def test_reject_request_not_found(self):
        """Verify that rejecting nonexistent request raises ValidationError.

        Returns:
            None
        """
        with self.assertRaises(ValidationError):
            FriendshipService.reject_request(
                user_id=self.user1.id,
                friendship_id=99999
            )

    def test_reject_request_already_accepted(self):
        """Verify that rejecting accepted request raises ValidationError.

        Returns:
            None
        """
        # Create accepted friendship
        friendship = Friendship(
            user_id=self.user1.id,
            friend_id=self.user2.id,
            status="accepted"
        )
        db.session.add(friendship)
        db.session.commit()

        with self.assertRaises(ValidationError):
            FriendshipService.reject_request(
                user_id=self.user2.id,
                friendship_id=friendship.id
            )


class TestCancelRequest(FriendshipServiceTestCase):
    """Test canceling friend requests."""

    def test_cancel_request_success(self):
        """Verify that friend request is canceled successfully.

        Returns:
            None
        """
        # Create pending friendship
        friendship = Friendship(
            user_id=self.user1.id,
            friend_id=self.user2.id,
            status="pending"
        )
        db.session.add(friendship)
        db.session.commit()

        FriendshipService.cancel_request(
            user_id=self.user1.id,
            friendship_id=friendship.id
        )
        
        # Verify friendship was deleted
        deleted_friendship = Friendship.query.get(friendship.id)
        self.assertIsNone(deleted_friendship)

    def test_cancel_request_not_found(self):
        """Verify that canceling nonexistent request raises ValidationError.

        Returns:
            None
        """
        with self.assertRaises(ValidationError):
            FriendshipService.cancel_request(
                user_id=self.user1.id,
                friendship_id=99999
            )

    def test_cancel_request_not_requester(self):
        """Verify that canceling request for wrong user raises ValidationError.

        Returns:
            None
        """
        # Create pending friendship where user1 is requester
        friendship = Friendship(
            user_id=self.user1.id,
            friend_id=self.user2.id,
            status="pending"
        )
        db.session.add(friendship)
        db.session.commit()

        # Try to cancel as user3 (not the requester)
        with self.assertRaises(ValidationError):
            FriendshipService.cancel_request(
                user_id=self.user3.id,
                friendship_id=friendship.id
            )

    def test_cancel_request_already_accepted(self):
        """Verify that canceling accepted request raises ValidationError.

        Returns:
            None
        """
        # Create accepted friendship
        friendship = Friendship(
            user_id=self.user1.id,
            friend_id=self.user2.id,
            status="accepted"
        )
        db.session.add(friendship)
        db.session.commit()

        with self.assertRaises(ValidationError):
            FriendshipService.cancel_request(
                user_id=self.user1.id,
                friendship_id=friendship.id
            )


class TestSerialize(FriendshipServiceTestCase):
    """Test friendship serialization."""

    def test_serialize_friendship_as_requester(self):
        """Verify that friendship is serialized correctly from requester perspective.

        Returns:
            None
        """
        friendship = Friendship(
            user_id=self.user1.id,
            friend_id=self.user2.id,
            status="pending"
        )
        db.session.add(friendship)
        db.session.commit()

        serialized = FriendshipService.serialize(friendship, viewer_id=self.user1.id)
        
        self.assertEqual(serialized["id"], friendship.id)
        self.assertEqual(serialized["status"], "pending")
        self.assertEqual(serialized["counterpart"]["username"], "user2")
        self.assertEqual(serialized["direction"], "outgoing")

    def test_serialize_friendship_as_target(self):
        """Verify that friendship is serialized correctly from target perspective.

        Returns:
            None
        """
        friendship = Friendship(
            user_id=self.user1.id,
            friend_id=self.user2.id,
            status="pending"
        )
        db.session.add(friendship)
        db.session.commit()

        serialized = FriendshipService.serialize(friendship, viewer_id=self.user2.id)
        
        self.assertEqual(serialized["counterpart"]["username"], "user1")
        self.assertEqual(serialized["direction"], "incoming")


if __name__ == "__main__":
    unittest.main()
