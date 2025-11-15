import unittest
from datetime import date

from backend import create_app
from backend.database import db


class ScreenTimeAPITestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app("testing")
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client()

        self.username = "tester"
        self.password = "secret123"
        self.email = "tester@example.com"

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

    def test_create_screen_time_entry(self):
        payload = {
            "app_name": "YouTube",
            "hours": 1,
            "minutes": 30,
            "date": date.today().isoformat(),
        }
        response = self.client.post("/api/screen-time/", json=payload)
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertIn("log", data)
        self.assertEqual(data["log"]["app_name"], "YouTube")
        self.assertEqual(data["log"]["hours"], 1)
        self.assertEqual(data["log"]["minutes"], 30)

        list_response = self.client.get("/api/screen-time/")
        self.assertEqual(list_response.status_code, 200)
        logs = list_response.get_json()["logs"]
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]["app_name"], "YouTube")

    def test_invalid_minutes_rejected(self):
        payload = {"app_name": "TikTok", "hours": 0, "minutes": 75}
        response = self.client.post("/api/screen-time/", json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.get_json())


if __name__ == "__main__":
    unittest.main()
