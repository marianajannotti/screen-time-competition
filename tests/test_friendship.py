import unittest

from backend import create_app
from backend.database import db


class FriendshipAPITestCase(unittest.TestCase):
    """End-to-end tests for friendship API flows."""
    def setUp(self):
        self.app = create_app("testing")
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client()

        self.user1 = {
            "username": "alice",
            "email": "alice@example.com",
            "password": "password1",
        }
        self.user2 = {
            "username": "bob",
            "email": "bob@example.com",
            "password": "password2",
        }

        self._register_user(self.user1)
        self._register_user(self.user2)
        self._login(self.user1)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        db.engine.dispose()
        self.app_context.pop()

    def _register_user(self, payload):
        """Helper to register a user via API."""
        response = self.client.post("/api/auth/register", json=payload)
        self.assertEqual(response.status_code, 201)

    def _login(self, payload):
        """Helper to login and capture session cookies."""
        response = self.client.post(
            "/api/auth/login",
            json={
                "username": payload["username"],
                "password": payload["password"],
            },
        )
        self.assertEqual(response.status_code, 200)

    def _logout(self):
        """Helper to clear session between user switches."""
        self.client.post("/api/auth/logout")

    def test_send_friend_request_and_block_duplicates(self):
        response = self.client.post(
            "/api/friendships/request",
            json={"username": self.user2["username"]},
        )
        self.assertEqual(response.status_code, 201)

        duplicate = self.client.post(
            "/api/friendships/request",
            json={"username": self.user2["username"]},
        )
        self.assertEqual(duplicate.status_code, 400)
        self.assertIn("pending", duplicate.get_json()["error"])

    def test_accept_flow(self):
        send_resp = self.client.post(
            "/api/friendships/request",
            json={"username": self.user2["username"]},
        )
        self.assertEqual(send_resp.status_code, 201)
        friendship_id = send_resp.get_json()["friendship"]["id"]

        self._logout()
        self._login(self.user2)

        list_resp = self.client.get("/api/friendships/")
        self.assertEqual(list_resp.status_code, 200)
        self.assertEqual(len(list_resp.get_json()["incoming"]), 1)

        accept_resp = self.client.post(
            f"/api/friendships/{friendship_id}/accept"
        )
        self.assertEqual(accept_resp.status_code, 200)

        after_accept = self.client.get("/api/friendships/")
        data = after_accept.get_json()
        self.assertEqual(len(data["incoming"]), 0)
        self.assertEqual(len(data["friends"]), 1)

        self._logout()
        self._login(self.user1)
        data_user1 = self.client.get("/api/friendships/").get_json()
        self.assertEqual(len(data_user1["friends"]), 1)

    def test_reject_flow(self):
        send_resp = self.client.post(
            "/api/friendships/request",
            json={"username": self.user2["username"]},
        )
        friendship_id = send_resp.get_json()["friendship"]["id"]

        self._logout()
        self._login(self.user2)

        reject_resp = self.client.post(
            f"/api/friendships/{friendship_id}/reject"
        )
        self.assertEqual(reject_resp.status_code, 200)

        after_reject = self.client.get("/api/friendships/").get_json()
        self.assertEqual(len(after_reject["incoming"]), 0)
        self.assertEqual(len(after_reject["friends"]), 0)

    def test_cancel_outgoing_request(self):
        send_resp = self.client.post(
            "/api/friendships/request",
            json={"username": self.user2["username"]},
        )
        friendship_id = send_resp.get_json()["friendship"]["id"]

        cancel_resp = self.client.post(
            f"/api/friendships/{friendship_id}/cancel"
        )
        self.assertEqual(cancel_resp.status_code, 200)

        data = self.client.get("/api/friendships/").get_json()
        self.assertEqual(len(data["outgoing"]), 0)
        self.assertEqual(len(data["friends"]), 0)

    def test_cannot_friend_self(self):
        response = self.client.post(
            "/api/friendships/request",
            json={"username": self.user1["username"]},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("cannot add yourself", response.get_json()["error"])

    def test_user_not_found(self):
        """Test sending a friend request to a non-existent username."""
        response = self.client.post(
            "/api/friendships/request",
            json={"username": "nonexistent_user_123"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("User not found", response.get_json()["error"])

    def test_empty_username(self):
        """Test sending a request with empty/blank username."""
        # Test with empty string
        response = self.client.post(
            "/api/friendships/request",
            json={"username": ""},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Username is required", response.get_json()["error"])

        # Test with whitespace only
        response = self.client.post(
            "/api/friendships/request",
            json={"username": "   "},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Username is required", response.get_json()["error"])

    def test_already_friends(self):
        """Test trying to send a request when already friends."""
        # First, send request
        send_resp = self.client.post(
            "/api/friendships/request",
            json={"username": self.user2["username"]},
        )
        self.assertEqual(send_resp.status_code, 201)
        friendship_id = send_resp.get_json()["friendship"]["id"]

        # Accept the request
        self._logout()
        self._login(self.user2)
        accept_resp = self.client.post(
            f"/api/friendships/{friendship_id}/accept"
        )
        self.assertEqual(accept_resp.status_code, 200)

        # Try to send another request from user2 to user1
        response = self.client.post(
            "/api/friendships/request",
            json={"username": self.user1["username"]},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("already friends", response.get_json()["error"])

    def test_content_type_validation(self):
        """Test sending non-JSON request to /request endpoint."""
        response = self.client.post(
            "/api/friendships/request",
            data="username=bob",
            content_type="application/x-www-form-urlencoded",
        )
        self.assertEqual(response.status_code, 415)
        self.assertIn(
            "Content-Type must be application/json",
            response.get_json()["error"],
        )

    def test_cannot_accept_someone_elses_request(self):
        """Test trying to accept a request not directed at you."""
        # User3 sends a request to user2
        user3 = {
            "username": "charlie",
            "email": "charlie@example.com",
            "password": "password3",
        }
        self._register_user(user3)

        self._logout()
        self._login(user3)
        send_resp = self.client.post(
            "/api/friendships/request",
            json={"username": self.user2["username"]},
        )
        self.assertEqual(send_resp.status_code, 201)
        friendship_id = send_resp.get_json()["friendship"]["id"]

        # User1 tries to accept the request (not authorized)
        self._logout()
        self._login(self.user1)
        accept_resp = self.client.post(
            f"/api/friendships/{friendship_id}/accept"
        )
        self.assertEqual(accept_resp.status_code, 400)
        self.assertIn("Request not found", accept_resp.get_json()["error"])

    def test_cannot_reject_someone_elses_request(self):
        """Test trying to reject a request not directed at you."""
        # User1 sends a request to user2
        send_resp = self.client.post(
            "/api/friendships/request",
            json={"username": self.user2["username"]},
        )
        self.assertEqual(send_resp.status_code, 201)
        friendship_id = send_resp.get_json()["friendship"]["id"]

        # User1 tries to reject their own outgoing request (should fail)
        reject_resp = self.client.post(
            f"/api/friendships/{friendship_id}/reject"
        )
        self.assertEqual(reject_resp.status_code, 400)
        self.assertIn("Request not found", reject_resp.get_json()["error"])

    def test_cannot_cancel_someone_elses_request(self):
        """Test trying to cancel a request you didn't create."""
        # User1 sends a request to user2
        send_resp = self.client.post(
            "/api/friendships/request",
            json={"username": self.user2["username"]},
        )
        self.assertEqual(send_resp.status_code, 201)
        friendship_id = send_resp.get_json()["friendship"]["id"]

        # User2 tries to cancel the request (should fail)
        self._logout()
        self._login(self.user2)
        cancel_resp = self.client.post(
            f"/api/friendships/{friendship_id}/cancel"
        )
        self.assertEqual(cancel_resp.status_code, 400)
        self.assertIn("Request not found", cancel_resp.get_json()["error"])

    def test_cannot_accept_already_accepted_request(self):
        """Test trying to accept an already accepted friendship."""
        # Send and accept a request
        send_resp = self.client.post(
            "/api/friendships/request",
            json={"username": self.user2["username"]},
        )
        friendship_id = send_resp.get_json()["friendship"]["id"]

        self._logout()
        self._login(self.user2)
        accept_resp = self.client.post(
            f"/api/friendships/{friendship_id}/accept"
        )
        self.assertEqual(accept_resp.status_code, 200)

        # Try to accept again
        accept_again = self.client.post(
            f"/api/friendships/{friendship_id}/accept"
        )
        self.assertEqual(accept_again.status_code, 400)
        self.assertIn(
            "Only pending requests can be accepted",
            accept_again.get_json()["error"],
        )

    def test_cannot_reject_already_accepted_request(self):
        """Test trying to reject an already accepted friendship."""
        # Send and accept a request
        send_resp = self.client.post(
            "/api/friendships/request",
            json={"username": self.user2["username"]},
        )
        friendship_id = send_resp.get_json()["friendship"]["id"]

        self._logout()
        self._login(self.user2)
        accept_resp = self.client.post(
            f"/api/friendships/{friendship_id}/accept"
        )
        self.assertEqual(accept_resp.status_code, 200)

        # Try to reject the accepted friendship
        reject_resp = self.client.post(
            f"/api/friendships/{friendship_id}/reject"
        )
        self.assertEqual(reject_resp.status_code, 400)
        self.assertIn(
            "Only pending requests can be rejected",
            reject_resp.get_json()["error"],
        )

    def test_cannot_cancel_already_accepted_request(self):
        """Test trying to cancel an already accepted friendship."""
        # Send and accept a request
        send_resp = self.client.post(
            "/api/friendships/request",
            json={"username": self.user2["username"]},
        )
        friendship_id = send_resp.get_json()["friendship"]["id"]

        self._logout()
        self._login(self.user2)
        accept_resp = self.client.post(
            f"/api/friendships/{friendship_id}/accept"
        )
        self.assertEqual(accept_resp.status_code, 200)

        # User1 tries to cancel the accepted friendship
        self._logout()
        self._login(self.user1)
        cancel_resp = self.client.post(
            f"/api/friendships/{friendship_id}/cancel"
        )
        self.assertEqual(cancel_resp.status_code, 400)
        self.assertIn(
            "Only pending requests can be canceled",
            cancel_resp.get_json()["error"],
        )


if __name__ == "__main__":
    unittest.main()