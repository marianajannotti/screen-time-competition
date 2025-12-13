"""Unit tests for the ScreenTimeService.

This module contains test cases for the ScreenTimeService class,
covering screen time entry creation, validation, and retrieval.
"""
import unittest
from datetime import date, timedelta

from backend import create_app
from backend.database import db
from backend.models import User, ScreenTimeLog
from backend.services import ScreenTimeService, ValidationError


class ScreenTimeServiceTestCase(unittest.TestCase):
    """Base test case for ScreenTimeService unit tests.

    Provides common setup and teardown for all screen time service tests.
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

        # Create test user
        self.test_user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hash"
        )
        db.session.add(self.test_user)
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


class TestCreateEntry(ScreenTimeServiceTestCase):
    """Test screen time entry creation."""

    def test_create_entry_with_app_name(self):
        """Verify that entry is created successfully with app name.

        Returns:
            None
        """
        data = {
            "app_name": "YouTube",
            "hours": 1,
            "minutes": 30,
            "date": date.today().isoformat()
        }
        
        entry = ScreenTimeService.create_entry(self.test_user.id, data)
        
        self.assertIsNotNone(entry)
        self.assertEqual(entry.user_id, self.test_user.id)
        self.assertEqual(entry.app_name, "YouTube")
        self.assertEqual(entry.screen_time_minutes, 90)  # 1h 30m = 90 minutes
        self.assertEqual(entry.date, date.today())
        # Test calculated fields from to_dict()
        entry_dict = entry.to_dict()
        self.assertEqual(entry_dict["hours"], 1)
        self.assertEqual(entry_dict["minutes"], 30)

    def test_create_entry_without_app_name_defaults_to_total(self):
        """Verify that entry without app name defaults to 'Total'.

        Returns:
            None
        """
        data = {
            "hours": 2,
            "minutes": 15
        }
        
        entry = ScreenTimeService.create_entry(self.test_user.id, data)
        
        self.assertEqual(entry.app_name, "Total")
        self.assertEqual(entry.hours, 2)
        self.assertEqual(entry.minutes, 15)
        self.assertEqual(entry.total_minutes, 135)

    def test_create_entry_with_custom_date(self):
        """Verify that entry is created with custom date.

        Returns:
            None
        """
        custom_date = date(2025, 1, 15)
        data = {
            "app_name": "Instagram",
            "hours": 0,
            "minutes": 45,
            "date": custom_date.isoformat()
        }
        
        entry = ScreenTimeService.create_entry(self.test_user.id, data)
        
        self.assertEqual(entry.date, custom_date)

    def test_create_entry_invalid_app_name(self):
        """Verify that invalid app name raises ValidationError.

        Returns:
            None
        """
        data = {
            "app_name": "InvalidApp",
            "hours": 1,
            "minutes": 0
        }
        
        with self.assertRaises(ValidationError) as context:
            ScreenTimeService.create_entry(self.test_user.id, data)
        
        self.assertIn("App name must be one of", str(context.exception))

    def test_create_entry_invalid_minutes(self):
        """Verify that minutes over 59 raise ValidationError.

        Returns:
            None
        """
        data = {
            "app_name": "YouTube",
            "hours": 1,
            "minutes": 75
        }
        
        with self.assertRaises(ValidationError) as context:
            ScreenTimeService.create_entry(self.test_user.id, data)
        
        self.assertIn("minutes must be between 0 and 59", str(context.exception))

    def test_create_entry_negative_hours(self):
        """Verify that negative hours raise ValidationError.

        Returns:
            None
        """
        data = {
            "app_name": "YouTube",
            "hours": -1,
            "minutes": 30
        }
        
        with self.assertRaises(ValidationError) as context:
            ScreenTimeService.create_entry(self.test_user.id, data)
        
        self.assertIn("hours must be non-negative", str(context.exception))

    def test_create_entry_negative_minutes(self):
        """Verify that negative minutes raise ValidationError.

        Returns:
            None
        """
        data = {
            "app_name": "YouTube",
            "hours": 1,
            "minutes": -30
        }
        
        with self.assertRaises(ValidationError) as context:
            ScreenTimeService.create_entry(self.test_user.id, data)
        
        self.assertIn("minutes must be between 0 and 59", str(context.exception))

    def test_create_entry_both_hours_and_minutes_zero(self):
        """Verify that zero hours and minutes raise ValidationError.

        Returns:
            None
        """
        data = {
            "app_name": "YouTube",
            "hours": 0,
            "minutes": 0
        }
        
        with self.assertRaises(ValidationError) as context:
            ScreenTimeService.create_entry(self.test_user.id, data)
        
        self.assertIn("must log at least 1 minute", str(context.exception))

    def test_create_entry_invalid_date_format(self):
        """Verify that invalid date format raises ValidationError.

        Returns:
            None
        """
        data = {
            "app_name": "YouTube",
            "hours": 1,
            "minutes": 30,
            "date": "invalid-date"
        }
        
        with self.assertRaises(ValidationError) as context:
            ScreenTimeService.create_entry(self.test_user.id, data)
        
        self.assertIn("Invalid date format", str(context.exception))


class TestGetEntries(ScreenTimeServiceTestCase):
    """Test screen time entry retrieval."""

    def setUp(self):
        """Create app context, database, and test entries.

        Returns:
            None
        """
        super().setUp()
        
        # Create test entries
        today = date.today()
        yesterday = today - timedelta(days=1)
        
        self.entry1 = ScreenTimeLog(
            user_id=self.test_user.id,
            app_name="YouTube",
            screen_time_minutes=90,  # 1h 30m
            date=today
        )
        self.entry2 = ScreenTimeLog(
            user_id=self.test_user.id,
            app_name="Instagram",
            screen_time_minutes=45,  # 45m
            date=yesterday
        )
        self.entry3 = ScreenTimeLog(
            user_id=self.test_user.id,
            app_name="Total",
            screen_time_minutes=135,  # 2h 15m
            date=today
        )
        
        db.session.add_all([self.entry1, self.entry2, self.entry3])
        db.session.commit()

    def test_get_entries_all(self):
        """Verify that all entries are returned by default.

        Returns:
            None
        """
        entries = ScreenTimeService.get_entries(self.test_user.id)
        
        self.assertEqual(len(entries), 3)

    def test_get_entries_with_limit(self):
        """Verify that limit parameter works correctly.

        Returns:
            None
        """
        entries = ScreenTimeService.get_entries(self.test_user.id, limit=2)
        
        self.assertEqual(len(entries), 2)

    def test_get_entries_by_date(self):
        """Verify that date filtering works correctly.

        Returns:
            None
        """
        today = date.today()
        entries = ScreenTimeService.get_entries(
            self.test_user.id, 
            date_str=today.isoformat()
        )
        
        # Should return entries from today only
        self.assertEqual(len(entries), 2)
        for entry in entries:
            self.assertEqual(entry.date, today)

    def test_get_entries_by_date_range(self):
        """Verify that date range filtering works correctly.

        Returns:
            None
        """
        start_date = (date.today() - timedelta(days=2)).isoformat()
        end_date = date.today().isoformat()
        
        entries = ScreenTimeService.get_entries(
            self.test_user.id,
            start_date_str=start_date,
            end_date_str=end_date
        )
        
        self.assertEqual(len(entries), 3)  # All entries within range

    def test_get_entries_by_app_name(self):
        """Verify that app name filtering works correctly.

        Returns:
            None
        """
        entries = ScreenTimeService.get_entries(
            self.test_user.id,
            app_name_filter="YouTube"
        )
        
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].app_name, "YouTube")

    def test_get_entries_invalid_date_format(self):
        """Verify that invalid date format raises ValidationError.

        Returns:
            None
        """
        with self.assertRaises(ValidationError) as context:
            ScreenTimeService.get_entries(
                self.test_user.id,
                date_str="invalid-date"
            )
        
        self.assertIn("Invalid date format", str(context.exception))

    def test_get_entries_different_user(self):
        """Verify that entries are filtered by user.

        Returns:
            None
        """
        # Create second user
        user2 = User(
            username="user2",
            email="user2@example.com",
            password_hash="hash"
        )
        db.session.add(user2)
        db.session.commit()
        
        # Get entries for second user (should be empty)
        entries = ScreenTimeService.get_entries(user2.id)
        self.assertEqual(len(entries), 0)


class TestGetAllowedApps(ScreenTimeServiceTestCase):
    """Test allowed apps functionality."""

    def test_get_allowed_apps_returns_list(self):
        """Verify that get_allowed_apps returns a list.

        Returns:
            None
        """
        apps = ScreenTimeService.get_allowed_apps()
        
        self.assertIsInstance(apps, list)
        self.assertGreater(len(apps), 0)

    def test_get_allowed_apps_contains_expected_apps(self):
        """Verify that allowed apps contains expected applications.

        Returns:
            None
        """
        apps = ScreenTimeService.get_allowed_apps()
        
        self.assertIn("Total", apps)
        self.assertIn("YouTube", apps)
        self.assertIn("Instagram", apps)
        self.assertIn("TikTok", apps)


class TestEdgeCases(ScreenTimeServiceTestCase):
    """Test edge cases and error handling."""

    def test_create_entry_zero_minutes(self):
        """Test creating screen time entry with zero minutes.

        Returns:
            None
        """
        data = {
            "app_name": "YouTube",
            "hours": 0,
            "minutes": 0,
            "date": date.today().isoformat()
        }
        
        with self.assertRaises(ValidationError) as context:
            ScreenTimeService.create_entry(self.test_user.id, data)
        
        self.assertIn("greater than zero", str(context.exception))

