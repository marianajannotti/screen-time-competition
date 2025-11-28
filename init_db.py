#!/usr/bin/env python3
"""
Database Initialization Script
Run this to set up your database with sample data
"""

import os
import sys
from datetime import datetime, date, timedelta

# Add project root to path
project_root = os.path.dirname(__file__)
sys.path.insert(0, project_root)

from backend import create_app
from backend.database import db
from backend.db_manager import DatabaseManager


def init_database():
    """Initialize the database with tables and sample data."""
    print("🚀 Initializing Screen Time Competition Database...")
    
    # Create app
    app = create_app('development')
    
    with app.app_context():
        try:
            # Drop existing tables (if any)
            print("\n📋 Dropping existing tables...")
            DatabaseManager.drop_all_tables()
            
            # Create new tables
            print("🏗️  Creating database tables...")
            DatabaseManager.initialize_database()
            
            # Seed with sample data
            print("🌱 Seeding database with sample data...")
            DatabaseManager.seed_sample_data()
            
            print("\n✅ Database initialization completed successfully!")
            print("\n📊 Sample data created:")
            print("   - 5 test users (user1-user5, all password: 'password')")
            print("   - Screen time logs for the past 30 days")
            print("   - Sample goals and friendships")
            print("   - Calculated streaks and points")
            
            print("\n🔑 Test login credentials:")
            print("   Username: user1, Password: password")
            print("   Username: user2, Password: password")
            print("   etc.")
            
        except Exception as e:
            print(f"\n❌ Error initializing database: {e}")
            return False
    
    return True


if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1)
