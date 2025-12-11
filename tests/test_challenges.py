"""Test suite for challenge creation, participation, and leaderboard functionality."""

import unittest
from datetime import date, timedelta

from backend import create_app
from backend.database import db
from backend.models import Challenge, ChallengeParticipant, User


class ChallengesAPITestCase(unittest.TestCase):
    """Test cases for challenge endpoints and business logic."""

    def setUp(self):
        """Create a fresh app context and authenticated test clients."""
        self.app = create_app("testing")
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Create users first, then create clients
        # This ensures user IDs are assigned in order
        self.client = self.app.test_client()
        
        self.user1 = self._create_user("alice", "alice@test.com", "password123")
        self.user2 = self._create_user("bob", "bob@test.com", "password456")
        self.user3 = self._create_user("charlie", "charlie@test.com", "password789")

        # Login with default client as user1
        self._login_user(self.client, "alice", "password123")

    def tearDown(self):
        """Clean up database artifacts between tests."""
        db.session.remove()
        db.drop_all()
        db.engine.dispose()
        self.app_context.pop()

    def _create_user(self, username, email, password):
        """Helper to register a user and return the user object."""
        register_payload = {
            "username": username,
            "email": email,
            "password": password,
        }
        response = self.client.post("/api/auth/register", json=register_payload)
        self.assertEqual(response.status_code, 201, f"Failed to register {username}")

        # Get user object
        user = User.query.filter_by(username=username).first()
        return user

    def _login_user(self, client, username, password):
        """Helper to login a user with a given client."""
        login_payload = {"username": username, "password": password}
        response = client.post("/api/auth/login", json=login_payload)
        self.assertEqual(response.status_code, 200, f"Failed to login {username}")
        return client

    def _get_client_for_user(self, user_number):
        """Get an authenticated client for a specific user (1, 2, or 3)."""
        client = self.app.test_client()
        if user_number == 1:
            self._login_user(client, "alice", "password123")
        elif user_number == 2:
            self._login_user(client, "bob", "password456")
        elif user_number == 3:
            self._login_user(client, "charlie", "password789")
        return client

    # --- Challenge Creation Tests ---

    def test_create_challenge_success(self):
        """Test successful challenge creation with all required fields."""
        today = date.today()
        start = today + timedelta(days=1)
        end = start + timedelta(days=6)

        payload = {
            "name": "1 Week TikTok Challenge",
            "description": "Keep TikTok usage under 30 mins per day",
            "target_app": "TikTok",
            "target_minutes": 30,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "invited_user_ids": [self.user2.id, self.user3.id]
        }

        response = self.client.post("/api/challenges", json=payload)
        self.assertEqual(response.status_code, 201)

        data = response.get_json()
        self.assertIn("challenge", data)
        self.assertEqual(data["challenge"]["name"], "1 Week TikTok Challenge")
        self.assertEqual(data["challenge"]["target_app"], "TikTok")
        self.assertEqual(data["challenge"]["status"], "upcoming")
        self.assertEqual(data["challenge"]["owner_id"], self.user1.id)

        # Verify participants were added (owner + 2 invited)
        challenge_id = data["challenge"]["id"]
        participants = ChallengeParticipant.query.filter_by(challenge_id=challenge_id).all()
        self.assertEqual(len(participants), 3)

    def test_create_challenge_starts_today(self):
        """Test that a challenge starting today gets 'active' status."""
        today = date.today()
        end = today + timedelta(days=6)

        payload = {
            "name": "Start Today Challenge",
            "target_app": "__TOTAL__",
            "target_minutes": 120,
            "start_date": today.isoformat(),
            "end_date": end.isoformat(),
        }

        response = self.client.post("/api/challenges", json=payload)
        self.assertEqual(response.status_code, 201)

        data = response.get_json()
        self.assertEqual(data["challenge"]["status"], "active")

    def test_create_challenge_missing_fields(self):
        """Test that missing required fields returns 400 error."""
        payload = {
            "name": "Incomplete Challenge",
            # Missing target_app, target_minutes, dates
        }

        response = self.client.post("/api/challenges", json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.get_json())

    def test_create_challenge_invalid_date_format(self):
        """Test that invalid date format returns 400 error."""
        payload = {
            "name": "Bad Date Challenge",
            "target_app": "YouTube",
            "target_minutes": 60,
            "start_date": "2025-13-45",  # Invalid date
            "end_date": "2025-12-31",
        }

        response = self.client.post("/api/challenges", json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid date format", response.get_json()["error"])

    def test_create_challenge_end_before_start(self):
        """Test that end date before start date returns error."""
        today = date.today()
        start = today + timedelta(days=7)
        end = today + timedelta(days=1)

        payload = {
            "name": "Backward Challenge",
            "target_app": "Instagram",
            "target_minutes": 45,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
        }

        response = self.client.post("/api/challenges", json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("End date must be after start date", response.get_json()["error"])

    def test_create_challenge_past_start_date(self):
        """Test that start date in the past returns error."""
        yesterday = date.today() - timedelta(days=1)
        end = date.today() + timedelta(days=6)

        payload = {
            "name": "Past Challenge",
            "target_app": "Total",
            "target_minutes": 180,
            "start_date": yesterday.isoformat(),
            "end_date": end.isoformat(),
        }

        response = self.client.post("/api/challenges", json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Start date cannot be in the past", response.get_json()["error"])

    # --- Get Challenges Tests ---

    def test_get_challenges_returns_user_challenges(self):
        """Test that GET /challenges returns all challenges user participates in."""
        # Create two challenges
        today = date.today()
        start = today + timedelta(days=1)
        end = start + timedelta(days=6)

        payload1 = {
            "name": "Challenge 1",
            "target_app": "TikTok",
            "target_minutes": 30,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
        }
        self.client.post("/api/challenges", json=payload1)

        payload2 = {
            "name": "Challenge 2",
            "target_app": "__TOTAL__",
            "target_minutes": 120,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
        }
        self.client.post("/api/challenges", json=payload2)

        # Get all challenges
        response = self.client.get("/api/challenges")
        self.assertEqual(response.status_code, 200)

        data = response.get_json()
        self.assertIn("challenges", data)
        self.assertEqual(len(data["challenges"]), 2)

        # Each challenge should include user_stats
        for challenge in data["challenges"]:
            self.assertIn("user_stats", challenge)
            self.assertEqual(challenge["user_stats"]["user_id"], self.user1.id)

    def test_get_challenges_excludes_deleted(self):
        """Test that deleted challenges are not returned."""
        today = date.today()
        start = today + timedelta(days=1)
        end = start + timedelta(days=6)

        # Create challenge
        payload = {
            "name": "To Be Deleted",
            "target_app": "YouTube",
            "target_minutes": 60,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
        }
        response = self.client.post("/api/challenges", json=payload)
        challenge_id = response.get_json()["challenge"]["id"]

        # Delete it
        self.client.delete(f"/api/challenges/{challenge_id}")

        # Get challenges - should be empty
        response = self.client.get("/api/challenges")
        data = response.get_json()
        self.assertEqual(len(data["challenges"]), 0)

    # --- Get Single Challenge Tests ---

    def test_get_challenge_by_id_success(self):
        """Test retrieving a specific challenge by ID."""
        today = date.today()
        start = today + timedelta(days=1)
        end = start + timedelta(days=6)

        payload = {
            "name": "Specific Challenge",
            "target_app": "Instagram",
            "target_minutes": 45,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
        }
        response = self.client.post("/api/challenges", json=payload)
        challenge_id = response.get_json()["challenge"]["id"]

        # Retrieve the challenge
        response = self.client.get(f"/api/challenges/{challenge_id}")
        self.assertEqual(response.status_code, 200)

        data = response.get_json()
        self.assertEqual(data["challenge"]["id"], challenge_id)
        self.assertEqual(data["challenge"]["name"], "Specific Challenge")
        self.assertIn("user_stats", data["challenge"])

    def test_get_challenge_non_participant_forbidden(self):
        """Test that non-participants cannot view a challenge."""
        today = date.today()
        start = today + timedelta(days=1)
        end = start + timedelta(days=6)

        # User1 creates challenge without inviting user2
        payload = {
            "name": "Private Challenge",
            "target_app": "TikTok",
            "target_minutes": 30,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
        }
        response = self.client.post("/api/challenges", json=payload)
        challenge_id = response.get_json()["challenge"]["id"]

        # User2 tries to view it
        response = self._get_client_for_user(2).get(f"/api/challenges/{challenge_id}")
        self.assertEqual(response.status_code, 403)
        self.assertIn("not a participant", response.get_json()["error"])

    def test_get_challenge_not_found(self):
        """Test that requesting non-existent challenge returns 404."""
        response = self.client.get("/api/challenges/99999")
        self.assertEqual(response.status_code, 404)

    # --- Leaderboard Tests ---

    def test_get_leaderboard_success(self):
        """Test retrieving leaderboard for a challenge."""
        today = date.today()
        start = today
        end = today + timedelta(days=6)

        # Create active challenge
        payload = {
            "name": "Leaderboard Test",
            "target_app": "TikTok",
            "target_minutes": 60,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "invited_user_ids": [self.user2.id, self.user3.id]
        }
        response = self.client.post("/api/challenges", json=payload)
        challenge_id = response.get_json()["challenge"]["id"]

        # Add some screen time logs for participants
        log_payload1 = {
            "app_name": "TikTok",
            "hours": 0,
            "minutes": 45,
            "date": today.isoformat()
        }
        self.client.post("/api/screen-time/", json=log_payload1)

        log_payload2 = {
            "app_name": "TikTok",
            "hours": 1,
            "minutes": 30,
            "date": today.isoformat()
        }
        self._get_client_for_user(2).post("/api/screen-time/", json=log_payload2)

        # Get leaderboard
        response = self.client.get(f"/api/challenges/{challenge_id}/leaderboard")
        self.assertEqual(response.status_code, 200)

        data = response.get_json()
        self.assertIn("leaderboard", data)
        self.assertIn("challenge", data)
        self.assertIn("owner_username", data)
        self.assertEqual(data["owner_username"], "alice")

        # Leaderboard should include all participants
        self.assertEqual(len(data["leaderboard"]), 3)

        # Should be sorted by average daily minutes (lowest first)
        self.assertLessEqual(
            data["leaderboard"][0]["average_daily_minutes"],
            data["leaderboard"][1]["average_daily_minutes"]
        )

    def test_get_leaderboard_non_participant_forbidden(self):
        """Test that non-participants cannot view leaderboard."""
        today = date.today()
        start = today + timedelta(days=1)
        end = start + timedelta(days=6)

        # User1 creates challenge without user2
        payload = {
            "name": "Private Leaderboard",
            "target_app": "YouTube",
            "target_minutes": 90,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
        }
        response = self.client.post("/api/challenges", json=payload)
        challenge_id = response.get_json()["challenge"]["id"]

        # User2 tries to view leaderboard
        response = self._get_client_for_user(2).get(f"/api/challenges/{challenge_id}/leaderboard")
        self.assertEqual(response.status_code, 403)

    # --- Invite Tests ---

    def test_invite_to_challenge_success(self):
        """Test owner can invite additional members."""
        today = date.today()
        start = today + timedelta(days=1)
        end = start + timedelta(days=6)

        # Create challenge with only owner
        payload = {
            "name": "Invite Test",
            "target_app": "Instagram",
            "target_minutes": 45,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
        }
        response = self.client.post("/api/challenges", json=payload)
        challenge_id = response.get_json()["challenge"]["id"]

        # Invite users
        invite_payload = {
            "user_ids": [self.user2.id, self.user3.id]
        }
        response = self.client.post(f"/api/challenges/{challenge_id}/invite", json=invite_payload)
        self.assertEqual(response.status_code, 200)

        data = response.get_json()
        self.assertEqual(data["invited_count"], 2)

        # Verify participants were added
        participants = ChallengeParticipant.query.filter_by(challenge_id=challenge_id).all()
        self.assertEqual(len(participants), 3)  # Owner + 2 invited

    def test_invite_non_owner_forbidden(self):
        """Test that non-owners cannot invite members."""
        today = date.today()
        start = today + timedelta(days=1)
        end = start + timedelta(days=6)

        # User1 creates and invites user2
        payload = {
            "name": "Invite Permission Test",
            "target_app": "TikTok",
            "target_minutes": 30,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "invited_user_ids": [self.user2.id]
        }
        response = self.client.post("/api/challenges", json=payload)
        challenge_id = response.get_json()["challenge"]["id"]

        # User2 tries to invite user3
        invite_payload = {
            "user_ids": [self.user3.id]
        }
        response = self._get_client_for_user(2).post(f"/api/challenges/{challenge_id}/invite", json=invite_payload)
        self.assertEqual(response.status_code, 403)
        self.assertIn("Only the challenge owner", response.get_json()["error"])

    def test_invite_to_completed_challenge_fails(self):
        """Test that invites to completed challenges are rejected."""
        today = date.today()
        start = today - timedelta(days=7)
        end = today - timedelta(days=1)

        # Create and manually mark as completed
        challenge = Challenge(
            name="Completed Challenge",
            owner_id=self.user1.id,
            target_app="YouTube",
            target_minutes=60,
            start_date=start,
            end_date=end,
            status="completed"
        )
        db.session.add(challenge)
        db.session.flush()

        participant = ChallengeParticipant(
            challenge_id=challenge.id,
            user_id=self.user1.id
        )
        db.session.add(participant)
        db.session.commit()

        # Try to invite
        invite_payload = {
            "user_ids": [self.user2.id]
        }
        response = self.client.post(f"/api/challenges/{challenge.id}/invite", json=invite_payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Cannot invite to completed", response.get_json()["error"])

    def test_invite_duplicate_user_ignored(self):
        """Test that inviting already-participating user doesn't duplicate."""
        today = date.today()
        start = today + timedelta(days=1)
        end = start + timedelta(days=6)

        # Create challenge with user2
        payload = {
            "name": "Duplicate Invite Test",
            "target_app": "TikTok",
            "target_minutes": 30,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "invited_user_ids": [self.user2.id]
        }
        response = self.client.post("/api/challenges", json=payload)
        challenge_id = response.get_json()["challenge"]["id"]

        # Try to invite user2 again
        invite_payload = {
            "user_ids": [self.user2.id, self.user3.id]
        }
        response = self.client.post(f"/api/challenges/{challenge_id}/invite", json=invite_payload)
        self.assertEqual(response.status_code, 200)

        data = response.get_json()
        self.assertEqual(data["invited_count"], 1)  # Only user3 invited

    # --- Leave Challenge Tests ---

    def test_leave_challenge_success(self):
        """Test that a participant can leave a challenge."""
        today = date.today()
        start = today + timedelta(days=1)
        end = start + timedelta(days=6)

        # Create challenge with user2
        payload = {
            "name": "Leave Test",
            "target_app": "Instagram",
            "target_minutes": 45,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "invited_user_ids": [self.user2.id]
        }
        response = self.client.post("/api/challenges", json=payload)
        challenge_id = response.get_json()["challenge"]["id"]

        # User2 leaves
        response = self._get_client_for_user(2).post(f"/api/challenges/{challenge_id}/leave")
        self.assertEqual(response.status_code, 200)

        # Verify user2 is no longer a participant
        participation = ChallengeParticipant.query.filter_by(
            challenge_id=challenge_id,
            user_id=self.user2.id
        ).first()
        self.assertIsNone(participation)

    def test_leave_challenge_owner_forbidden(self):
        """Test that owner cannot leave their own challenge."""
        today = date.today()
        start = today + timedelta(days=1)
        end = start + timedelta(days=6)

        # Create challenge
        payload = {
            "name": "Owner Leave Test",
            "target_app": "TikTok",
            "target_minutes": 30,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
        }
        response = self.client.post("/api/challenges", json=payload)
        challenge_id = response.get_json()["challenge"]["id"]

        # Owner tries to leave
        response = self.client.post(f"/api/challenges/{challenge_id}/leave")
        self.assertEqual(response.status_code, 403)
        self.assertIn("owner cannot leave", response.get_json()["error"])

    def test_leave_challenge_not_participant(self):
        """Test that non-participants get error when trying to leave."""
        today = date.today()
        start = today + timedelta(days=1)
        end = start + timedelta(days=6)

        # User1 creates challenge without user2
        payload = {
            "name": "Not Participant Test",
            "target_app": "YouTube",
            "target_minutes": 60,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
        }
        response = self.client.post("/api/challenges", json=payload)
        challenge_id = response.get_json()["challenge"]["id"]

        # User2 tries to leave
        response = self._get_client_for_user(2).post(f"/api/challenges/{challenge_id}/leave")
        self.assertEqual(response.status_code, 400)
        self.assertIn("not a participant", response.get_json()["error"])

    # --- Delete Challenge Tests ---

    def test_delete_challenge_success(self):
        """Test that owner can delete a challenge."""
        today = date.today()
        start = today + timedelta(days=1)
        end = start + timedelta(days=6)

        # Create challenge
        payload = {
            "name": "Delete Test",
            "target_app": "TikTok",
            "target_minutes": 30,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
        }
        response = self.client.post("/api/challenges", json=payload)
        challenge_id = response.get_json()["challenge"]["id"]

        # Delete it
        response = self.client.delete(f"/api/challenges/{challenge_id}")
        self.assertEqual(response.status_code, 200)

        # Verify status is 'deleted'
        challenge = Challenge.query.get(challenge_id)
        self.assertEqual(challenge.status, "deleted")

    def test_delete_challenge_non_owner_forbidden(self):
        """Test that non-owners cannot delete a challenge."""
        today = date.today()
        start = today + timedelta(days=1)
        end = start + timedelta(days=6)

        # User1 creates and invites user2
        payload = {
            "name": "Delete Permission Test",
            "target_app": "Instagram",
            "target_minutes": 45,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "invited_user_ids": [self.user2.id]
        }
        response = self.client.post("/api/challenges", json=payload)
        challenge_id = response.get_json()["challenge"]["id"]

        # User2 tries to delete
        response = self._get_client_for_user(2).delete(f"/api/challenges/{challenge_id}")
        self.assertEqual(response.status_code, 403)
        self.assertIn("Only the challenge owner", response.get_json()["error"])

    # --- Challenge Stats Update Tests ---

    def test_screen_time_log_updates_challenge_stats(self):
        """Test that logging screen time updates challenge participant stats."""
        today = date.today()
        start = today
        end = today + timedelta(days=6)

        # Create active challenge
        payload = {
            "name": "Stats Update Test",
            "target_app": "TikTok",
            "target_minutes": 60,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
        }
        response = self.client.post("/api/challenges", json=payload)
        challenge_id = response.get_json()["challenge"]["id"]

        # Log screen time under target
        log_payload = {
            "app_name": "TikTok",
            "hours": 0,
            "minutes": 45,
            "date": today.isoformat()
        }
        self.client.post("/api/screen-time/", json=log_payload)

        # Check participant stats
        participant = ChallengeParticipant.query.filter_by(
            challenge_id=challenge_id,
            user_id=self.user1.id
        ).first()

        self.assertEqual(participant.days_logged, 1)
        self.assertEqual(participant.total_screen_time_minutes, 45)
        self.assertEqual(participant.days_passed, 1)
        self.assertEqual(participant.days_failed, 0)

        # Log another day over target
        tomorrow = today + timedelta(days=1)
        log_payload2 = {
            "app_name": "TikTok",
            "hours": 1,
            "minutes": 30,
            "date": tomorrow.isoformat()
        }
        self.client.post("/api/screen-time/", json=log_payload2)

        # Refresh participant
        db.session.refresh(participant)

        self.assertEqual(participant.days_logged, 2)
        self.assertEqual(participant.total_screen_time_minutes, 135)  # 45 + 90
        self.assertEqual(participant.days_passed, 1)
        self.assertEqual(participant.days_failed, 1)

    def test_challenge_auto_completes_after_end_date(self):
        """Test that challenges auto-complete when end date passes."""
        yesterday = date.today() - timedelta(days=1)
        week_ago = yesterday - timedelta(days=6)

        # Create expired challenge
        challenge = Challenge(
            name="Expired Challenge",
            owner_id=self.user1.id,
            target_app="YouTube",
            target_minutes=60,
            start_date=week_ago,
            end_date=yesterday,
            status="active"
        )
        db.session.add(challenge)
        db.session.flush()

        # Add participants with logs
        participant1 = ChallengeParticipant(
            challenge_id=challenge.id,
            user_id=self.user1.id,
            days_logged=5,
            total_screen_time_minutes=250
        )
        participant2 = ChallengeParticipant(
            challenge_id=challenge.id,
            user_id=self.user2.id,
            days_logged=5,
            total_screen_time_minutes=350
        )
        db.session.add_all([participant1, participant2])
        db.session.commit()

        # Trigger auto-complete by fetching challenges
        response = self.client.get("/api/challenges")
        self.assertEqual(response.status_code, 200)

        # Verify challenge is completed
        db.session.refresh(challenge)
        self.assertEqual(challenge.status, "completed")
        self.assertIsNotNone(challenge.completed_at)

        # Verify ranks and winner
        db.session.refresh(participant1)
        db.session.refresh(participant2)

        self.assertEqual(participant1.final_rank, 1)
        self.assertEqual(participant1.is_winner, True)
        self.assertEqual(participant1.challenge_completed, True)

        self.assertEqual(participant2.final_rank, 2)
        self.assertEqual(participant2.is_winner, False)
        self.assertEqual(participant2.challenge_completed, True)

    def test_total_app_challenge_sums_all_apps(self):
        """Test that __TOTAL__ challenges sum screen time across all apps."""
        today = date.today()
        start = today
        end = today + timedelta(days=6)

        # Create total challenge
        payload = {
            "name": "Total Screen Time Challenge",
            "target_app": "__TOTAL__",
            "target_minutes": 180,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
        }
        response = self.client.post("/api/challenges", json=payload)
        challenge_id = response.get_json()["challenge"]["id"]

        # Log multiple apps
        self.client.post("/api/screen-time/", json={
            "app_name": "TikTok",
            "hours": 1,
            "minutes": 0,
            "date": today.isoformat()
        })
        self.client.post("/api/screen-time/", json={
            "app_name": "Instagram",
            "hours": 0,
            "minutes": 45,
            "date": today.isoformat()
        })
        self.client.post("/api/screen-time/", json={
            "app_name": "YouTube",
            "hours": 1,
            "minutes": 30,
            "date": today.isoformat()
        })

        # Check participant stats
        participant = ChallengeParticipant.query.filter_by(
            challenge_id=challenge_id,
            user_id=self.user1.id
        ).first()

        self.assertEqual(participant.days_logged, 1)
        self.assertEqual(participant.total_screen_time_minutes, 195)  # 60 + 45 + 90
        self.assertEqual(participant.days_failed, 1)  # Over 180 target

    def test_specific_app_challenge_filters_correctly(self):
        """Test that specific app challenges only count that app's usage."""
        today = date.today()
        start = today
        end = today + timedelta(days=6)

        # Create TikTok-specific challenge
        payload = {
            "name": "TikTok Only Challenge",
            "target_app": "TikTok",
            "target_minutes": 60,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
        }
        response = self.client.post("/api/challenges", json=payload)
        challenge_id = response.get_json()["challenge"]["id"]

        # Log TikTok and other apps
        self.client.post("/api/screen-time/", json={
            "app_name": "TikTok",
            "hours": 0,
            "minutes": 45,
            "date": today.isoformat()
        })
        self.client.post("/api/screen-time/", json={
            "app_name": "Instagram",
            "hours": 2,
            "minutes": 0,
            "date": today.isoformat()
        })

        # Check participant stats - should only count TikTok
        participant = ChallengeParticipant.query.filter_by(
            challenge_id=challenge_id,
            user_id=self.user1.id
        ).first()

        self.assertEqual(participant.total_screen_time_minutes, 45)
        self.assertEqual(participant.days_passed, 1)  # Under 60 target


if __name__ == "__main__":
    unittest.main()
