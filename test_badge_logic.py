#!/usr/bin/env python3
"""
Test script to update a user's streak and trigger badge logic.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend import create_app
from backend.models import User
from backend.database import db
from backend.badge_logic import BadgeLogic

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
