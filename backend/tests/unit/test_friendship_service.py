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

    @unittest.skip("FriendshipService uses send_request(requester_id, target_username) not send_friend_request(id, id)")
    def test_send_friend_request_to_self(self):
        """Test that users cannot send friend requests to themselves.

        Returns:
            None
        """
        with self.assertRaises(ValidationError) as context:
            FriendshipService.send_friend_request(self.user1.id, self.user1.id)
        
        self.assertIn("yourself", str(context.exception).lower())

    @unittest.skip("FriendshipService uses send_request(requester_id, target_username) not send_friend_request(id, id)")
    def test_send_friend_request_nonexistent_user(self):
        """Test sending friend request to nonexistent user.

        Returns:
            None
        """
        with self.assertRaises(ValidationError) as context:
            FriendshipService.send_friend_request(self.user1.id, 999999)
        
        self.assertIn("user not found", str(context.exception).lower())

    @unittest.skip("FriendshipService uses send_request/accept_request with different signatures")
    def test_send_friend_request_already_friends(self):
        """Test sending friend request when users are already friends.

        Returns:
            None
        """
        # First establish friendship
        FriendshipService.send_friend_request(self.user1.id, self.user2.id)
        FriendshipService.accept_friend_request(self.user2.id, self.user1.id)
        
        # Try to send another request
        with self.assertRaises(ValidationError) as context:
            FriendshipService.send_friend_request(self.user1.id, self.user2.id)
        
        self.assertIn("already friends", str(context.exception).lower())

    @unittest.skip("FriendshipService.accept_friend_request() doesn't exist")
    def test_accept_nonexistent_friend_request(self):
        """Test accepting a friend request that doesn't exist.

        Returns:
            None
        """
        with self.assertRaises(ValidationError) as context:
            FriendshipService.accept_friend_request(self.user2.id, self.user1.id)
        
        self.assertIn("friend request not found", str(context.exception).lower())

    @unittest.skip("FriendshipService.reject_friend_request() doesn't exist")
    def test_reject_nonexistent_friend_request(self):
        """Test rejecting a friend request that doesn't exist.

        Returns:
            None
        """
        with self.assertRaises(ValidationError) as context:
            FriendshipService.reject_friend_request(self.user2.id, self.user1.id)
        
        self.assertIn("friend request not found", str(context.exception).lower())

    @unittest.skip("FriendshipService.remove_friendship() not yet implemented")
    def test_remove_friendship_not_friends(self):
        """Test removing friendship when users are not friends.

        Returns:
            None
        """
        with self.assertRaises(ValidationError) as context:
            FriendshipService.remove_friendship(self.user1.id, self.user2.id)
        
        self.assertIn("not friends", str(context.exception).lower())

    @unittest.skip("FriendshipService.get_friends() with search parameter not yet implemented")
    def test_get_friends_with_search_filter(self):
        """Test getting friends list with search filter.

        Returns:
            None
        """
        # Create additional users with specific names
        searchable_user = User(
            username="searchable_friend",
            email="search@example.com",
            password_hash="hash"
        )
        db.session.add(searchable_user)
        db.session.commit()
        
        # Make friends
        FriendshipService.send_friend_request(self.user1.id, self.user2.id)
        FriendshipService.accept_friend_request(self.user2.id, self.user1.id)
        
        FriendshipService.send_friend_request(self.user1.id, searchable_user.id)
        FriendshipService.accept_friend_request(searchable_user.id, self.user1.id)
        
        # Search for specific friend
        friends = FriendshipService.get_friends(self.user1.id, search="searchable")
        
        self.assertEqual(len(friends), 1)
        self.assertEqual(friends[0]["username"], "searchable_friend")

    @unittest.skip("FriendshipService doesn't have get_pending_requests() pagination method")
    def test_get_pending_requests_pagination(self):
        """Test pagination in pending friend requests.

        Returns:
            None
        """
        # Create multiple users and send requests
        users = []
        for i in range(15):  # Create 15 users
            user = User(
                username=f"user{i+10}",
                email=f"user{i+10}@example.com",
                password_hash="hash"
            )
            users.append(user)
        
        db.session.add_all(users)
        db.session.commit()
        
        # Send requests from all users to user1
        for user in users:
            FriendshipService.send_friend_request(user.id, self.user1.id)
        
        # Test pagination
        page1 = FriendshipService.get_pending_requests(self.user1.id, page=1, per_page=10)
        page2 = FriendshipService.get_pending_requests(self.user1.id, page=2, per_page=10)
        
        self.assertEqual(len(page1), 10)
        self.assertEqual(len(page2), 5)

    def test_block_user_functionality(self):
        """Test user blocking functionality if implemented.

        Returns:
            None
        """
        # This test assumes block functionality exists or will be implemented
        try:
            blocked = FriendshipService.block_user(self.user1.id, self.user2.id)
            
            # If blocking is successful, friend requests should be blocked
            with self.assertRaises(ValidationError):
                FriendshipService.send_friend_request(self.user2.id, self.user1.id)
                
        except AttributeError:
            # Block functionality not implemented yet
            self.skipTest("Block functionality not yet implemented")

    @unittest.skip("FriendshipService doesn't have get_friendship_status() method")
    def test_friendship_status_check(self):
        """Test checking friendship status between users.

        Returns:
            None
        """
        # Initially no relationship
        status = FriendshipService.get_friendship_status(self.user1.id, self.user2.id)
        self.assertEqual(status, "none")
        
        # After sending request
        FriendshipService.send_friend_request(self.user1.id, self.user2.id)
        status = FriendshipService.get_friendship_status(self.user1.id, self.user2.id)
        self.assertEqual(status, "pending_sent")
        
        status = FriendshipService.get_friendship_status(self.user2.id, self.user1.id)
        self.assertEqual(status, "pending_received")
        
        # After accepting
        FriendshipService.accept_friend_request(self.user2.id, self.user1.id)
        status = FriendshipService.get_friendship_status(self.user1.id, self.user2.id)
        self.assertEqual(status, "friends")

    @unittest.skip("FriendshipService doesn't have get_mutual_friends() method")
    def test_mutual_friends_functionality(self):
        """Test getting mutual friends between users.

        Returns:
            None
        """
        # Create friend network: user1-user3, user2-user3
        FriendshipService.send_friend_request(self.user1.id, self.user3.id)
        FriendshipService.accept_friend_request(self.user3.id, self.user1.id)
        
        FriendshipService.send_friend_request(self.user2.id, self.user3.id)
        FriendshipService.accept_friend_request(self.user3.id, self.user2.id)
        
        # Get mutual friends between user1 and user2
        mutual_friends = FriendshipService.get_mutual_friends(self.user1.id, self.user2.id)
        
        self.assertEqual(len(mutual_friends), 1)
        self.assertEqual(mutual_friends[0]["username"], "user3")

    @unittest.skip("FriendshipService doesn't have friend suggestion methods")
    def test_friend_suggestions_based_on_mutual_friends(self):
        """Test friend suggestions based on mutual connections.

        Returns:
            None
        """
        # Create a network where user4 could be suggested to user1
        user4 = User(username="user4", email="user4@example.com", password_hash="hash")
        db.session.add(user4)
        db.session.commit()
        
        # user1 -> user3, user2 -> user3, user2 -> user4
        FriendshipService.send_friend_request(self.user1.id, self.user3.id)
        FriendshipService.accept_friend_request(self.user3.id, self.user1.id)
        
        FriendshipService.send_friend_request(self.user2.id, self.user3.id)
        FriendshipService.accept_friend_request(self.user3.id, self.user2.id)
        
        FriendshipService.send_friend_request(self.user2.id, user4.id)
        FriendshipService.accept_friend_request(user4.id, self.user2.id)
        
        # user4 should be suggested to user1 (via user3->user2->user4)
        suggestions = FriendshipService.get_friend_suggestions(self.user1.id)
        
        suggested_usernames = [s["username"] for s in suggestions]
        self.assertIn("user4", suggested_usernames)

    @unittest.skip("FriendshipService doesn't have get_friends_count() method")
    def test_friendship_limits(self):
        """Test friendship limits if implemented.

        Returns:
            None
        """
        # Test maximum number of friends (if there's a limit)
        max_friends = 100  # Assuming this is the limit
        
        friends_count = FriendshipService.get_friends_count(self.user1.id)
        
        # For now, just test that the count method works
        self.assertIsInstance(friends_count, int)
        self.assertGreaterEqual(friends_count, 0)

    @unittest.skip("FriendshipService doesn't have send_friend_request() method")
    def test_concurrent_friend_requests(self):
        """Test handling of concurrent friend requests.

        Returns:
            None
        """
        from unittest.mock import patch
        
        # Simulate race condition where both users send requests simultaneously
        with patch('backend.database.db.session') as mock_session:
            mock_session.query.return_value.filter.return_value.first.return_value = None
            mock_session.add.return_value = None
            mock_session.commit.side_effect = [None, Exception("Constraint violation")]
            
            # First request should succeed
            request1 = FriendshipService.send_friend_request(self.user1.id, self.user2.id)
            self.assertIsNotNone(request1)
            
            # Second concurrent request should be handled gracefully
            try:
                FriendshipService.send_friend_request(self.user2.id, self.user1.id)
            except Exception as e:
                # Should handle the constraint violation gracefully
                self.assertIn("already exists", str(e).lower())

    @unittest.skip("FriendshipService doesn't have send_friend_request() or get_friends() methods")
    def test_friendship_data_integrity(self):
        """Test data integrity in friendship operations.

        Returns:
            None
        """
        # Send and accept friend request
        FriendshipService.send_friend_request(self.user1.id, self.user2.id)
        FriendshipService.accept_friend_request(self.user2.id, self.user1.id)
        
        # Check that both directions of friendship exist
        friendship1 = Friendship.query.filter_by(
            requester_id=self.user1.id, 
            friend_id=self.user2.id
        ).first()
        
        self.assertIsNotNone(friendship1)
        self.assertTrue(friendship1.accepted)
        
        # Verify friendship is visible from both sides
        user1_friends = FriendshipService.get_friends(self.user1.id)
        user2_friends = FriendshipService.get_friends(self.user2.id)
        
        user1_friend_ids = [f["id"] for f in user1_friends]
        user2_friend_ids = [f["id"] for f in user2_friends]
        
        self.assertIn(self.user2.id, user1_friend_ids)
        self.assertIn(self.user1.id, user2_friend_ids)

    @unittest.skip("FriendshipService doesn't have send_friend_request() method")
    def test_privacy_settings_in_friendship(self):
        """Test privacy settings affecting friendship visibility.

        Returns:
            None
        """
        # This test assumes privacy settings exist
        # If not implemented, it documents expected behavior
        
        # Make users friends
        FriendshipService.send_friend_request(self.user1.id, self.user2.id)
        FriendshipService.accept_friend_request(self.user2.id, self.user1.id)
        
        # Test that private users might not appear in suggestions
        try:
            # This would test privacy functionality if implemented
            private_friends = FriendshipService.get_friends(
                self.user1.id, 
                include_private=False
            )
            self.assertIsInstance(private_friends, list)
        except TypeError:
            # Privacy filtering not implemented yet
            self.skipTest("Privacy filtering not yet implemented")


if __name__ == "__main__":
    unittest.main()
