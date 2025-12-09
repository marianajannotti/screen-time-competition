"""
One-time script to clean up duplicate screen time entries.

This removes duplicate entries for the same (user_id, app_name, date)
combination, keeping only the most recent entry (by created_at timestamp).

Run this script once to fix existing database inconsistencies:
    python -m backend.cleanup_duplicates
"""

from collections import defaultdict

from backend import create_app
from backend.database import db
from backend.models import ScreenTimeLog


def cleanup_duplicates():
    """Remove duplicate screen time entries, keeping the most recent."""
    app = create_app()

    with app.app_context():
        # Group all entries by (user_id, app_name, date)
        entries_by_key = defaultdict(list)

        all_entries = ScreenTimeLog.query.all()
        for entry in all_entries:
            key = (entry.user_id, entry.app_name, entry.date)
            entries_by_key[key].append(entry)

        # Find and delete duplicates
        total_deleted = 0
        for key, entries in entries_by_key.items():
            if len(entries) > 1:
                # Sort by created_at descending (most recent first)
                entries.sort(key=lambda e: e.created_at, reverse=True)

                # Keep the first (most recent), delete the rest
                to_delete = entries[1:]
                user_id, app_name, date = key

                print(
                    f"Found {len(entries)} duplicates for user {user_id}, "
                    f"app '{app_name}', date {date}"
                )
                print(f"  Keeping entry ID {entries[0].id} "
                      f"({entries[0].screen_time_minutes} minutes)")
                
                for entry in to_delete:
                    print(f"  Deleting entry ID {entry.id} "
                          f"({entry.screen_time_minutes} minutes)")
                    db.session.delete(entry)
                    total_deleted += 1

        if total_deleted > 0:
            db.session.commit()
            print(f"\n✅ Deleted {total_deleted} duplicate entries")
        else:
            print("✅ No duplicates found!")


if __name__ == "__main__":
    cleanup_duplicates()
