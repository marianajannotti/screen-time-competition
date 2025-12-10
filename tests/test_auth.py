import os
import sys
import unittest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend import create_app  # noqa: E402
from backend.database import db  # noqa: E402


class TestAuthAutoLogin(unittest.TestCase):
    """Verify registration establishes an authenticated session."""

    def setUp(self):
        self.app = create_app("testing")
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client()

        self.user_payload = {
            "username": "freshuser",
            "email": "fresh@example.com",
            "password": "password123",
        }

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        db.engine.dispose()
        self.app_context.pop()

    def test_register_auto_logs_in(self):
        """Register should set a logged-in session without explicit login."""

        resp = self.client.post("/api/auth/register", json=self.user_payload)
        self.assertEqual(resp.status_code, 201)

        status = self.client.get("/api/auth/status")
        self.assertEqual(status.status_code, 200)
        data = status.get_json()
        self.assertTrue(data.get("authenticated"))
        self.assertEqual(
            data.get("user", {}).get("username"),
            self.user_payload["username"],
        )

        # /me should also succeed in the same session
        me = self.client.get("/api/auth/me")
        self.assertEqual(me.status_code, 200)
        self.assertEqual(
            me.get_json().get("user", {}).get("username"),
            self.user_payload["username"],
        )


if __name__ == "__main__":
    unittest.main()
