"""Test suite for badge awarding in challenge contexts and tie handling."""

import unittest
from datetime import date, timedelta

from backend import create_app
from backend.database import db
from backend.models import Challenge, ChallengeParticipant, User
from backend.models.badge import Badge, UserBadge
from backend.services.challenges_service import ChallengesService


class BadgeChallengeIntegrationTestCase(unittest.TestCase):
    """Test cases for badge awarding in challenges and tie scenarios."""

    def setUp(self):
        """Create a fresh app context and authenticated test clients."""
        self.app = create_app("testing")
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Initialize badges
        from backend.services.badge_service import BadgeService
        BadgeService.initialize_badges()

        # Create users
        self.client = self.app.test_client()
        
        self.user1 = self._create_user("alice", "alice@test.com", "password123")
        self.user2 = self._create_user("bob", "bob@test.com", "password456")
        self.user3 = self._create_user("charlie", "charlie@test.com", "password789")
        self.user4 = self._create_user("diana", "diana@test.com", "password101")

        # Login as user1
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
        user = User.query.filter_by(username=username).first()
        return user

    def _login_user(self, client, username, password):
        """Helper to login a user with a given client."""
        login_payload = {"username": username, "password": password}
        response = client.post("/api/auth/login", json=login_payload)
        self.assertEqual(response.status_code, 200, f"Failed to login {username}")
        return client

    def _get_client_for_user(self, user_number):
        """Get an authenticated client for a specific user (1, 2, 3, 4)."""
        client = self.app.test_client()
        if user_number == 1:
            self._login_user(client, "alice", "password123")
        elif user_number == 2:
            self._login_user(client, "bob", "password456")
        elif user_number == 3:
            self._login_user(client, "charlie", "password789")
        elif user_number == 4:
            self._login_user(client, "diana", "password101")
        return client

    def _has_badge(self, user_id, badge_name):
        """Check if a user has been awarded a specific badge."""
        badge = Badge.query.filter_by(name=badge_name).first()
        if not badge:
            return False
        user_badge = UserBadge.query.filter_by(
            user_id=user_id,
            badge_id=badge.id
        ).first()
        return user_badge is not None

    # --- Badge Awarding Tests ---

    def test_challenge_accepted_badge_on_first_challenge(self):
        """Test that 'Challenge Accepted' badge is awarded when user joins first challenge."""
        today = date.today()
        start = today + timedelta(days=1)
        end = start + timedelta(days=6)

        # Create challenge and invite user2
        payload = {
            "name": "First Challenge",
            "target_app": "Instagram",
            "target_minutes": 30,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "invited_user_ids": [self.user2.id]
        }
        response = self.client.post("/api/challenges", json=payload)
        self.assertEqual(response.status_code, 201)
        challenge_id = response.get_json()["challenge"]["challenge_id"]

        # User1 (owner) should NOT have the badge yet - they created it, didn't accept an invitation
        self.assertFalse(self._has_badge(self.user1.id, "Challenge Accepted"))

        # User2 should not have it yet (invitation pending)
        self.assertFalse(self._has_badge(self.user2.id, "Challenge Accepted"))

        # Get participant_id for user2
        participant = ChallengeParticipant.query.filter_by(
            challenge_id=challenge_id,
            user_id=self.user2.id
        ).first()

        # Accept invitation as user2
        client2 = self._get_client_for_user(2)
        response = client2.post(f"/api/challenges/invitations/{participant.participant_id}/accept")
        self.assertEqual(response.status_code, 200)

        # User2 should now have the badge
        self.assertTrue(self._has_badge(self.user2.id, "Challenge Accepted"))

    def test_friendly_rival_badge_on_fifth_challenge(self):
        """Test that 'Friendly Rival' badge is awarded after accepting 5 challenge invitations."""
        today = date.today()
        
        # User3 creates 5 challenges and invites user2
        # User2 will accept all 5 to get badges
        client3 = self._get_client_for_user(3)
        for i in range(5):
            start = today + timedelta(days=i*7+1)
            end = start + timedelta(days=6)
            
            payload = {
                "name": f"Challenge {i+1}",
                "target_app": "Instagram",
                "target_minutes": 30,
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
                "invited_user_ids": [self.user2.id]
            }
            response = client3.post("/api/challenges", json=payload)
            self.assertEqual(response.status_code, 201)

        # User2 should not have badges yet (no acceptances)
        self.assertFalse(self._has_badge(self.user2.id, "Challenge Accepted"))
        self.assertFalse(self._has_badge(self.user2.id, "Friendly Rival"))

        # Accept all 5 invitations as user2
        client2 = self._get_client_for_user(2)
        participants = ChallengeParticipant.query.filter_by(
            user_id=self.user2.id,
            invitation_status='pending'
        ).all()
        
        self.assertEqual(len(participants), 5, "User2 should have 5 pending invitations")
        
        for idx, participant in enumerate(participants):
            response = client2.post(f"/api/challenges/invitations/{participant.participant_id}/accept")
            self.assertEqual(response.status_code, 200)
            
            # After first acceptance, should have Challenge Accepted
            if idx == 0:
                self.assertTrue(self._has_badge(self.user2.id, "Challenge Accepted"))
            
            # Check Friendly Rival badge status after each acceptance
            if idx < 4:
                # Should not have it until 5th challenge
                self.assertFalse(self._has_badge(self.user2.id, "Friendly Rival"))
            else:
                # Should have it after 5th challenge
                self.assertTrue(self._has_badge(self.user2.id, "Friendly Rival"))

    def test_community_champion_badge_on_winning_challenge(self):
        """Test that 'Community Champion' badge is awarded when user wins a challenge."""
        yesterday = date.today() - timedelta(days=1)
        week_ago = yesterday - timedelta(days=6)

        # Create expired challenge with user1 winning
        challenge = Challenge(
            name="Test Challenge",
            owner_id=self.user1.id,
            target_app="YouTube",
            target_minutes=60,
            start_date=week_ago,
            end_date=yesterday,
            status="active"
        )
        db.session.add(challenge)
        db.session.flush()

        # Add participants: user1 wins with lowest average
        participant1 = ChallengeParticipant(
            challenge_id=challenge.challenge_id,
            user_id=self.user1.id,
            invitation_status='accepted',
            days_logged=5,
            total_screen_time_minutes=200  # avg: 40 min/day
        )
        participant2 = ChallengeParticipant(
            challenge_id=challenge.challenge_id,
            user_id=self.user2.id,
            invitation_status='accepted',
            days_logged=5,
            total_screen_time_minutes=300  # avg: 60 min/day
        )
        db.session.add_all([participant1, participant2])
        db.session.commit()

        # Verify badges not awarded yet
        self.assertFalse(self._has_badge(self.user1.id, "Community Champion"))
        self.assertFalse(self._has_badge(self.user2.id, "Community Champion"))

        # Trigger auto-completion
        ChallengesService.check_and_complete_challenge(challenge)

        # Verify winner badge was awarded
        self.assertTrue(self._has_badge(self.user1.id, "Community Champion"))
        self.assertFalse(self._has_badge(self.user2.id, "Community Champion"))

    def test_declining_invitation_does_not_award_badge(self):
        """Test that declining a challenge invitation does not award 'Challenge Accepted'."""
        today = date.today()
        start = today + timedelta(days=1)
        end = start + timedelta(days=6)

        # Create challenge and invite user2
        payload = {
            "name": "Test Challenge",
            "target_app": "Instagram",
            "target_minutes": 30,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "invited_user_ids": [self.user2.id]
        }
        response = self.client.post("/api/challenges", json=payload)
        challenge_id = response.get_json()["challenge"]["challenge_id"]

        # Get participant_id for user2
        participant = ChallengeParticipant.query.filter_by(
            challenge_id=challenge_id,
            user_id=self.user2.id
        ).first()

        # Decline invitation as user2
        client2 = self._get_client_for_user(2)
        response = client2.post(f"/api/challenges/invitations/{participant.participant_id}/decline")
        self.assertEqual(response.status_code, 200)

        # User2 should not have the badge
        self.assertFalse(self._has_badge(self.user2.id, "Challenge Accepted"))

    # --- Tie Handling Tests ---

    def test_two_way_tie_for_first_place(self):
        """Test that when 2 users have identical averages, both are marked as winners with rank 1."""
        yesterday = date.today() - timedelta(days=1)
        week_ago = yesterday - timedelta(days=6)

        # Create expired challenge
        challenge = Challenge(
            name="Tie Challenge",
            owner_id=self.user1.id,
            target_app="Instagram",
            target_minutes=60,
            start_date=week_ago,
            end_date=yesterday,
            status="active"
        )
        db.session.add(challenge)
        db.session.flush()

        # Add participants with IDENTICAL averages (50 min/day)
        participant1 = ChallengeParticipant(
            challenge_id=challenge.challenge_id,
            user_id=self.user1.id,
            invitation_status='accepted',
            days_logged=4,
            total_screen_time_minutes=200  # avg: 50 min/day
        )
        participant2 = ChallengeParticipant(
            challenge_id=challenge.challenge_id,
            user_id=self.user2.id,
            invitation_status='accepted',
            days_logged=2,
            total_screen_time_minutes=100  # avg: 50 min/day
        )
        participant3 = ChallengeParticipant(
            challenge_id=challenge.challenge_id,
            user_id=self.user3.id,
            invitation_status='accepted',
            days_logged=5,
            total_screen_time_minutes=350  # avg: 70 min/day
        )
        db.session.add_all([participant1, participant2, participant3])
        db.session.commit()

        # Trigger completion
        ChallengesService.check_and_complete_challenge(challenge)

        # Refresh participants
        db.session.refresh(participant1)
        db.session.refresh(participant2)
        db.session.refresh(participant3)

        # Both user1 and user2 should be rank 1 and winners
        self.assertEqual(participant1.final_rank, 1)
        self.assertTrue(participant1.is_winner)
        self.assertTrue(participant1.challenge_completed)

        self.assertEqual(participant2.final_rank, 1)
        self.assertTrue(participant2.is_winner)
        self.assertTrue(participant2.challenge_completed)

        # User3 should be rank 3 (skipping rank 2 due to tie)
        self.assertEqual(participant3.final_rank, 3)
        self.assertFalse(participant3.is_winner)
        self.assertTrue(participant3.challenge_completed)

        # Both winners should receive Community Champion badge
        self.assertTrue(self._has_badge(self.user1.id, "Community Champion"))
        self.assertTrue(self._has_badge(self.user2.id, "Community Champion"))
        self.assertFalse(self._has_badge(self.user3.id, "Community Champion"))

    def test_three_way_tie_for_first_place(self):
        """Test that when 3 users have identical averages, all are marked as winners with rank 1."""
        yesterday = date.today() - timedelta(days=1)
        week_ago = yesterday - timedelta(days=6)

        challenge = Challenge(
            name="Three Way Tie",
            owner_id=self.user1.id,
            target_app="TikTok",
            target_minutes=30,
            start_date=week_ago,
            end_date=yesterday,
            status="active"
        )
        db.session.add(challenge)
        db.session.flush()

        # All three have 60 min/day average
        participant1 = ChallengeParticipant(
            challenge_id=challenge.challenge_id,
            user_id=self.user1.id,
            invitation_status='accepted',
            days_logged=3,
            total_screen_time_minutes=180  # avg: 60 min/day
        )
        participant2 = ChallengeParticipant(
            challenge_id=challenge.challenge_id,
            user_id=self.user2.id,
            invitation_status='accepted',
            days_logged=5,
            total_screen_time_minutes=300  # avg: 60 min/day
        )
        participant3 = ChallengeParticipant(
            challenge_id=challenge.challenge_id,
            user_id=self.user3.id,
            invitation_status='accepted',
            days_logged=2,
            total_screen_time_minutes=120  # avg: 60 min/day
        )
        participant4 = ChallengeParticipant(
            challenge_id=challenge.challenge_id,
            user_id=self.user4.id,
            invitation_status='accepted',
            days_logged=4,
            total_screen_time_minutes=320  # avg: 80 min/day
        )
        db.session.add_all([participant1, participant2, participant3, participant4])
        db.session.commit()

        # Trigger completion
        ChallengesService.check_and_complete_challenge(challenge)

        db.session.refresh(participant1)
        db.session.refresh(participant2)
        db.session.refresh(participant3)
        db.session.refresh(participant4)

        # All three tied users should be rank 1 and winners
        self.assertEqual(participant1.final_rank, 1)
        self.assertTrue(participant1.is_winner)
        self.assertEqual(participant2.final_rank, 1)
        self.assertTrue(participant2.is_winner)
        self.assertEqual(participant3.final_rank, 1)
        self.assertTrue(participant3.is_winner)

        # Fourth place should be rank 4 (skipping 2 and 3)
        self.assertEqual(participant4.final_rank, 4)
        self.assertFalse(participant4.is_winner)

        # All three winners get the badge
        self.assertTrue(self._has_badge(self.user1.id, "Community Champion"))
        self.assertTrue(self._has_badge(self.user2.id, "Community Champion"))
        self.assertTrue(self._has_badge(self.user3.id, "Community Champion"))
        self.assertFalse(self._has_badge(self.user4.id, "Community Champion"))

    def test_zero_hour_challenge_no_logs_win(self):
        """Test that users with no logs win zero-hour challenges (0 target)."""
        yesterday = date.today() - timedelta(days=1)
        week_ago = yesterday - timedelta(days=6)

        # Create challenge with 0 minute target (complete abstinence)
        challenge = Challenge(
            name="Zero TikTok Week",
            owner_id=self.user1.id,
            target_app="TikTok",
            target_minutes=0,  # Zero target
            start_date=week_ago,
            end_date=yesterday,
            status="active"
        )
        db.session.add(challenge)
        db.session.flush()

        # User1: No logs at all (perfect abstinence) - should win
        participant1 = ChallengeParticipant(
            challenge_id=challenge.challenge_id,
            user_id=self.user1.id,
            invitation_status='accepted',
            days_logged=0,
            total_screen_time_minutes=0
        )
        # User2: Also no logs - should also win (tie)
        participant2 = ChallengeParticipant(
            challenge_id=challenge.challenge_id,
            user_id=self.user2.id,
            invitation_status='accepted',
            days_logged=0,
            total_screen_time_minutes=0
        )
        # User3: Logged some time - should lose
        participant3 = ChallengeParticipant(
            challenge_id=challenge.challenge_id,
            user_id=self.user3.id,
            invitation_status='accepted',
            days_logged=3,
            total_screen_time_minutes=45  # avg: 15 min/day
        )
        db.session.add_all([participant1, participant2, participant3])
        db.session.commit()

        # Trigger completion
        ChallengesService.check_and_complete_challenge(challenge)

        db.session.refresh(participant1)
        db.session.refresh(participant2)
        db.session.refresh(participant3)

        # Both users with no logs should win with rank 1
        self.assertEqual(participant1.final_rank, 1)
        self.assertTrue(participant1.is_winner)
        self.assertEqual(participant2.final_rank, 1)
        self.assertTrue(participant2.is_winner)

        # User3 should be rank 3 (tied users skip rank 2)
        self.assertEqual(participant3.final_rank, 3)
        self.assertFalse(participant3.is_winner)

        # Both winners get Community Champion badge
        self.assertTrue(self._has_badge(self.user1.id, "Community Champion"))
        self.assertTrue(self._has_badge(self.user2.id, "Community Champion"))
        self.assertFalse(self._has_badge(self.user3.id, "Community Champion"))

    def test_exact_same_hours_and_days_tie(self):
        """Test that users with EXACTLY the same total minutes AND days logged tie."""
        yesterday = date.today() - timedelta(days=1)
        week_ago = yesterday - timedelta(days=6)

        challenge = Challenge(
            name="Exact Tie Test",
            owner_id=self.user1.id,
            target_app="Instagram",
            target_minutes=60,
            start_date=week_ago,
            end_date=yesterday,
            status="active"
        )
        db.session.add(challenge)
        db.session.flush()

        # All three have EXACTLY 100 total minutes and 2 days logged
        # Average: 50 min/day for all
        participant1 = ChallengeParticipant(
            challenge_id=challenge.challenge_id,
            user_id=self.user1.id,
            invitation_status='accepted',
            days_logged=2,
            total_screen_time_minutes=100  # avg: 50 min/day
        )
        participant2 = ChallengeParticipant(
            challenge_id=challenge.challenge_id,
            user_id=self.user2.id,
            invitation_status='accepted',
            days_logged=2,
            total_screen_time_minutes=100  # avg: 50 min/day
        )
        participant3 = ChallengeParticipant(
            challenge_id=challenge.challenge_id,
            user_id=self.user3.id,
            invitation_status='accepted',
            days_logged=2,
            total_screen_time_minutes=100  # avg: 50 min/day
        )
        db.session.add_all([participant1, participant2, participant3])
        db.session.commit()

        # Trigger completion
        ChallengesService.check_and_complete_challenge(challenge)

        db.session.refresh(participant1)
        db.session.refresh(participant2)
        db.session.refresh(participant3)

        # All should be rank 1 and winners (3-way tie)
        self.assertEqual(participant1.final_rank, 1)
        self.assertTrue(participant1.is_winner)
        self.assertEqual(participant2.final_rank, 1)
        self.assertTrue(participant2.is_winner)
        self.assertEqual(participant3.final_rank, 1)
        self.assertTrue(participant3.is_winner)

        # All get Community Champion badge
        self.assertTrue(self._has_badge(self.user1.id, "Community Champion"))
        self.assertTrue(self._has_badge(self.user2.id, "Community Champion"))
        self.assertTrue(self._has_badge(self.user3.id, "Community Champion"))

    def test_tie_for_second_place_not_winners(self):
        """Test that users tied for 2nd place are not marked as winners."""
        yesterday = date.today() - timedelta(days=1)
        week_ago = yesterday - timedelta(days=6)

        challenge = Challenge(
            name="Second Place Tie",
            owner_id=self.user1.id,
            target_app="YouTube",
            target_minutes=60,
            start_date=week_ago,
            end_date=yesterday,
            status="active"
        )
        db.session.add(challenge)
        db.session.flush()

        # Clear winner at rank 1, tie for rank 2
        participant1 = ChallengeParticipant(
            challenge_id=challenge.challenge_id,
            user_id=self.user1.id,
            invitation_status='accepted',
            days_logged=5,
            total_screen_time_minutes=200  # avg: 40 min/day - WINNER
        )
        participant2 = ChallengeParticipant(
            challenge_id=challenge.challenge_id,
            user_id=self.user2.id,
            invitation_status='accepted',
            days_logged=4,
            total_screen_time_minutes=200  # avg: 50 min/day - TIE
        )
        participant3 = ChallengeParticipant(
            challenge_id=challenge.challenge_id,
            user_id=self.user3.id,
            invitation_status='accepted',
            days_logged=2,
            total_screen_time_minutes=100  # avg: 50 min/day - TIE
        )
        db.session.add_all([participant1, participant2, participant3])
        db.session.commit()

        # Trigger completion
        ChallengesService.check_and_complete_challenge(challenge)

        db.session.refresh(participant1)
        db.session.refresh(participant2)
        db.session.refresh(participant3)

        # Only user1 is winner
        self.assertEqual(participant1.final_rank, 1)
        self.assertTrue(participant1.is_winner)

        # User2 and user3 are tied for 2nd
        self.assertEqual(participant2.final_rank, 2)
        self.assertFalse(participant2.is_winner)
        self.assertEqual(participant3.final_rank, 2)
        self.assertFalse(participant3.is_winner)

        # Only winner gets the badge
        self.assertTrue(self._has_badge(self.user1.id, "Community Champion"))
        self.assertFalse(self._has_badge(self.user2.id, "Community Champion"))
        self.assertFalse(self._has_badge(self.user3.id, "Community Champion"))


if __name__ == "__main__":
    unittest.main()
