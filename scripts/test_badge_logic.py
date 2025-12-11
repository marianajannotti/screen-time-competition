#!/usr/bin/env python3
"""
Test script to update a user's streak and trigger badge logic.

Test instructions:
1) Ensure the Flask backend dependencies are installed:
   pip install -r backend/requirements.txt
2) Make sure you have a development database set up (instance/app.db) and migrations applied if any.
   The repo uses a simple SQLite db by default; running `python run.py` will initialize it.
3) Start the backend once to create tables:
   python run.py
4) Then run this test file directly to validate badge logic:
   python test_badge_logic.py
5) Alternatively, run all tests:
   python -m pytest -q
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend import create_app
from backend.models import User
from backend.database import db
from backend.services import BadgeLogic

def main():
    app = create_app("development")
    
    with app.app_context():
        # Update the test user's streak
        user = User.query.filter_by(username='badgeuser').first()
        if user:
            print(f"Found user: {user.username} (ID: {user.id})")
            
            # Update streak to trigger different badges
            user.streak_count = 7  # This should trigger 'Fresh Start' and '7-Day Focus' badges
            db.session.commit()
            print(f"Updated user streak to: {user.streak_count}")
            
            # Check and award badges
            awarded_badges = BadgeLogic.check_and_award_badges(user.id)
            print(f"Awarded badges: {awarded_badges}")
            
        else:
            print("User 'badgeuser' not found")

if __name__ == "__main__":
    main()
