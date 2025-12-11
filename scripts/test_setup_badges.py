#!/usr/bin/env python3
"""
Test script to create a user and award some badges for testing the badge system.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend import create_app
from backend.models import User, UserBadge, Badge
from backend.database import db
from werkzeug.security import generate_password_hash

def main():
    app = create_app("development")
    
    with app.app_context():
        # Create test user if doesn't exist
        user = User.query.filter_by(username='testuser').first()
        if not user:
            user = User(
                username='testuser',
                email='test@example.com',
                password_hash=generate_password_hash('testpassword'),
                streak_count=7,
                total_points=150
            )
            db.session.add(user)
            db.session.commit()
            print(f"Created test user: {user.username} (ID: {user.id})")
        else:
            print(f"Test user already exists: {user.username} (ID: {user.id})")
        
        # Award some test badges
        badge_names_to_award = ['7-Day Focus', 'Digital Minimalist', 'One Hour Club', 'Top 3']
        
        for badge_name in badge_names_to_award:
            badge = Badge.query.filter_by(name=badge_name).first()
            if badge:
                # Check if user already has this badge
                existing = UserBadge.query.filter_by(user_id=user.id, badge_id=badge.id).first()
                if not existing:
                    user_badge = UserBadge(user_id=user.id, badge_id=badge.id)
                    db.session.add(user_badge)
                    print(f"Awarded badge: {badge_name}")
                else:
                    print(f"User already has badge: {badge_name}")
            else:
                print(f"Badge not found: {badge_name}")
        
        db.session.commit()
        
        # Show user's badges
        user_badges = UserBadge.query.filter_by(user_id=user.id).all()
        print(f"\nUser {user.username} has {len(user_badges)} badges:")
        for ub in user_badges:
            print(f"  - {ub.badge.name}: {ub.badge.description}")

if __name__ == "__main__":
    main()
