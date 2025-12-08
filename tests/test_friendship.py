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


if __name__ == "__main__":
    unittest.main()
