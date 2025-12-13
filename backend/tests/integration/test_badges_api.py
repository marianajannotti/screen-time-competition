import unittest

from backend import create_app
from backend.database import db
from backend.models import User


class BadgesAPITestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app("testing")
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client()

        self.username = "badge_tester"
        self.password = "secret123"
        self.email = "badge_tester@example.com"

        self._register_user()
        self._login_user()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        db.engine.dispose()
        self.app_context.pop()

    def _register_user(self):
        payload = {
            "username": self.username,
            "email": self.email,
            "password": self.password,
        }
        response = self.client.post("/api/auth/register", json=payload)
        self.assertEqual(response.status_code, 201)

    def _login_user(self):
        payload = {"username": self.username, "password": self.password}
        response = self.client.post("/api/auth/login", json=payload)
        self.assertEqual(response.status_code, 200)

    def _get_current_user(self) -> User:
        return User.query.filter_by(username=self.username).first()

    def test_get_all_badges(self):
        # Should return 200 even if no badges initialized yet
        resp = self.client.get("/api/badges")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIsInstance(data, list)

    def test_initialize_requires_admin(self):
        # Normal user should be forbidden
        resp = self.client.post("/api/badges/initialize")
        self.assertEqual(resp.status_code, 403)

    def test_initialize_as_admin_succeeds(self):
        # Mark the current user as admin (transient attribute is enough for getattr)
        user = self._get_current_user()
        user.is_admin = True  # transient attribute checked via getattr
        db.session.commit()

        resp = self.client.post("/api/badges/initialize")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("message", resp.get_json())

    def test_user_badges_access_control(self):
        # Create another user
        payload = {
            "username": "other",
            "email": "other@example.com",
            "password": "pass12345",
        }
        r = self.client.post("/api/auth/register", json=payload)
        self.assertEqual(r.status_code, 201)

        # Attempt to get other user's badges should be forbidden
        other = User.query.filter_by(username="other").first()
        resp = self.client.get(f"/api/users/{other.id}/badges")
        self.assertEqual(resp.status_code, 403)

    def test_award_badge_to_self(self):
        # Initialize badges as admin
        user = self._get_current_user()
        user.is_admin = True
        db.session.commit()
        self.assertEqual(self.client.post("/api/badges/initialize").status_code, 200)

        # Award a badge to self
        payload = {"badge_name": "Fresh Start"}
        resp = self.client.post(f"/api/users/{user.id}/badges", json=payload)
        self.assertIn(resp.status_code, (200, 201, 400))  # 400 if already awarded
        data = resp.get_json()
        self.assertTrue("message" in data or "error" in data)

    def test_check_user_badges_endpoint(self):
        user = self._get_current_user()
        # Calling check should be allowed for self
        resp = self.client.post(f"/api/users/{user.id}/badges/check")
        self.assertEqual(resp.status_code, 200)
        body = resp.get_json()
        self.assertIn("message", body)
        self.assertIn("awarded_badges", body)


if __name__ == "__main__":
    unittest.main()
