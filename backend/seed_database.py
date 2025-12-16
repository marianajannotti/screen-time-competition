#!/usr/bin/env python3
"""
Database seeding script for Screen Time Competition App.

Creates consistent test data including:
- Sample users with known passwords
- Friendships between users
- Screen time entries
- Badges
- Challenges

Run with: python backend/seed_database.py
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone
from werkzeug.security import generate_password_hash

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend import create_app
from backend.database import db
from backend.models import (
    User,
    Friendship,
    ScreenTimeLog,
    Badge,
    UserBadge,
    Challenge,
    ChallengeParticipant,
)


def clear_database():
    """Drop all tables and recreate them."""
    print("🗑️  Clearing existing database...")
    db.drop_all()
    db.create_all()
    print("✅ Database cleared and recreated")


def seed_users():
    """Create sample users with known passwords."""
    print("\n👤 Creating users...")

    users_data = [
        {
            "username": "alice",
            "email": "alice@example.com",
            "password": "password123",
        },
        {"username": "bob", "email": "bob@example.com", "password": "password123"},
        {
            "username": "charlie",
            "email": "charlie@example.com",
            "password": "password123",
        },
        {"username": "diana", "email": "diana@example.com", "password": "password123"},
        {"username": "eve", "email": "eve@example.com", "password": "password123"},
    ]

    users = []
    for data in users_data:
        user = User(
            username=data["username"],
            email=data["email"],
            password_hash=generate_password_hash(data["password"]),
        )
        db.session.add(user)
        users.append(user)
        print(
            f"  ✓ Created user: {data['username']} (email: {data['email']}, password: {data['password']})"
        )

    db.session.commit()
    print(f"✅ Created {len(users)} users")
    return users


def seed_friendships(users):
    """Create friendships between users."""
    print("\n🤝 Creating friendships...")

    friendships_data = [
        # Alice is friends with everyone
        (0, 1, "accepted"),  # alice <-> bob
        (0, 2, "accepted"),  # alice <-> charlie
        (0, 3, "accepted"),  # alice <-> diana
        (0, 4, "pending"),  # alice -> eve (pending)
        # Bob and Charlie are friends
        (1, 2, "accepted"),  # bob <-> charlie
        # Diana has a pending request from Charlie
        (2, 3, "pending"),  # charlie -> diana (pending)
    ]

    for requester_idx, target_idx, status in friendships_data:
        friendship = Friendship(
            user_id=users[requester_idx].id,
            friend_id=users[target_idx].id,
            status=status,
        )
        db.session.add(friendship)
        print(
            f"  ✓ {users[requester_idx].username} -> {users[target_idx].username} ({status})"
        )

    db.session.commit()
    print(f"✅ Created {len(friendships_data)} friendships")


def seed_screen_time(users):
    """Create screen time entries for users."""
    print("\n📊 Creating screen time entries...")

    today = datetime.now().date()
    entries_count = 0

    # Alice - active user with varied apps
    for days_ago in range(7):
        date = today - timedelta(days=days_ago)

        # Total screen time
        total_entry = ScreenTimeLog(
            user_id=users[0].id,
            date=date,
            app_name="__TOTAL__",
            screen_time_minutes=240 - (days_ago * 20),
        )
        db.session.add(total_entry)
        entries_count += 1

        # Individual apps
        apps = [
            ("Instagram", 80),
            ("TikTok", 60),
            ("YouTube", 50),
            ("Reddit", 30),
        ]
        for app, minutes in apps:
            entry = ScreenTimeLog(
                user_id=users[0].id,
                date=date,
                app_name=app,
                screen_time_minutes=minutes - (days_ago * 3),
            )
            db.session.add(entry)
            entries_count += 1

    # Bob - moderate user
    for days_ago in range(5):
        date = today - timedelta(days=days_ago)
        entry = ScreenTimeLog(
            user_id=users[1].id,
            date=date,
            app_name="__TOTAL__",
            screen_time_minutes=180 - (days_ago * 15),
        )
        db.session.add(entry)
        entries_count += 1

    # Charlie - light user
    for days_ago in range(3):
        date = today - timedelta(days=days_ago)
        entry = ScreenTimeLog(
            user_id=users[2].id,
            date=date,
            app_name="__TOTAL__",
            screen_time_minutes=120,
        )
        db.session.add(entry)
        entries_count += 1

    db.session.commit()
    print(f"✅ Created {entries_count} screen time entries")


def seed_badges():
    """Create default badges."""
    print("\n🏆 Creating badges...")

    badges_data = [
        {
            "name": "First Steps",
            "description": "Log your first day of screen time",
            "icon": "🎯",
            "badge_type": "milestone",
        },
        {
            "name": "Week Warrior",
            "description": "Log screen time for 7 consecutive days",
            "icon": "🔥",
            "badge_type": "streak",
        },
        {
            "name": "Digital Minimalist",
            "description": "Keep screen time under 2 hours for 5 days",
            "icon": "🌟",
            "badge_type": "reduction",
        },
        {
            "name": "Social Butterfly",
            "description": "Add 5 friends to your network",
            "icon": "🦋",
            "badge_type": "social",
        },
        {
            "name": "Challenge Accepted",
            "description": "Win your first challenge",
            "icon": "🏅",
            "badge_type": "challenge",
        },
    ]

    badges = []
    for data in badges_data:
        badge = Badge(**data)
        db.session.add(badge)
        badges.append(badge)
        print(f"  ✓ Created badge: {data['name']}")

    db.session.commit()
    print(f"✅ Created {len(badges)} badges")
    return badges


def seed_user_badges(users, badges):
    """Award badges to users."""
    print("\n🎖️  Awarding badges to users...")

    # Alice gets First Steps and Week Warrior
    user_badges = [
        (users[0], badges[0]),  # Alice - First Steps
        (users[0], badges[1]),  # Alice - Week Warrior
        (users[1], badges[0]),  # Bob - First Steps
    ]

    for user, badge in user_badges:
        user_badge = UserBadge(
            user_id=user.id, badge_id=badge.id, earned_at=datetime.now(timezone.utc)
        )
        db.session.add(user_badge)
        print(f"  ✓ Awarded '{badge.name}' to {user.username}")

    db.session.commit()
    print(f"✅ Awarded {len(user_badges)} badges")


def seed_challenges(users):
    """Create sample challenges."""
    print("\n🎯 Creating challenges...")

    today = datetime.now().date()

    challenges_data = [
        {
            "name": "Weekend Digital Detox",
            "description": "Keep total screen time under 2 hours",
            "owner_id": users[0].id,  # Alice
            "target_app": "__TOTAL__",
            "target_minutes": 120,
            "start_date": today - timedelta(days=2),
            "end_date": today + timedelta(days=5),
            "status": "active",
            "participants": [users[0], users[1], users[2]],  # Alice, Bob, Charlie
        },
        {
            "name": "No TikTok Week",
            "description": "Stay off TikTok for an entire week",
            "owner_id": users[1].id,  # Bob
            "target_app": "TikTok",
            "target_minutes": 0,
            "start_date": today,
            "end_date": today + timedelta(days=7),
            "status": "active",
            "participants": [users[1], users[0]],  # Bob, Alice
        },
        {
            "name": "Completed Challenge",
            "description": "Reduce Instagram to 30 min/day",
            "owner_id": users[0].id,  # Alice
            "target_app": "Instagram",
            "target_minutes": 30,
            "start_date": today - timedelta(days=10),
            "end_date": today - timedelta(days=3),
            "status": "completed",
            "participants": [users[0], users[1]],  # Alice, Bob
        },
    ]

    for data in challenges_data:
        participants = data.pop("participants")

        challenge = Challenge(**data)
        db.session.add(challenge)
        db.session.commit()  # Commit to get challenge.challenge_id
        db.session.refresh(challenge)  # Refresh to ensure id is loaded

        # Add participants
        for participant in participants:
            challenge_participant = ChallengeParticipant(
                challenge_id=challenge.challenge_id,
                user_id=participant.id,
                invitation_status="accepted",  # All seeded participants auto-accept
            )
            db.session.add(challenge_participant)

        db.session.commit()  # Commit participants
        participants_count = len(participants)
        print(
            f"  ✓ Created challenge: {challenge.name} ({participants_count} participants)"
        )

    print(f"✅ Created {len(challenges_data)} challenges")


def main():
    """Main seeding function."""
    app = create_app("development")

    with app.app_context():
        print("=" * 60)
        print("🌱 SEEDING DATABASE")
        print("=" * 60)

        # Clear and recreate database
        clear_database()

        # Seed data in order
        users = seed_users()
        seed_friendships(users)
        seed_screen_time(users)
        badges = seed_badges()
        seed_user_badges(users, badges)
        seed_challenges(users)

        print("\n" + "=" * 60)
        print("✅ DATABASE SEEDING COMPLETE!")
        print("=" * 60)
        print("\n📝 Test Accounts Created:")
        print("   All passwords: password123")
        print("")
        print("   alice@example.com   - Active user with most data")
        print("   bob@example.com     - Moderate user")
        print("   charlie@example.com - Light user")
        print("   diana@example.com   - New user")
        print("   eve@example.com     - New user")
        print("\n🚀 You can now login with any of these accounts!")
        print("=" * 60)


if __name__ == "__main__":
    main()
