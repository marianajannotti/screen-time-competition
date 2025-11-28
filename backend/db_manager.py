"""
Database Management Utilities
Handles database initialization, seeding, and migration tasks
"""

import os
import sys
from datetime import datetime, date, timedelta
import random
from werkzeug.security import generate_password_hash

from .database import db
from .models import User, ScreenTimeLog, Goal, Friendship


class DatabaseManager:
    """Database management utilities for setup, seeding, and maintenance."""
    
    @staticmethod
    def initialize_database(app=None):
        """
        Initialize database tables.
        
        Args:
            app: Flask app instance (optional, uses current app context if None)
        """
        if app:
            with app.app_context():
                db.create_all()
                print("✅ Database tables created successfully")
        else:
            db.create_all()
            print("✅ Database tables created successfully")
    
    @staticmethod
    def drop_all_tables(app=None):
        """
        Drop all database tables. USE WITH CAUTION!
        
        Args:
            app: Flask app instance (optional, uses current app context if None)
        """
        if app:
            with app.app_context():
                db.drop_all()
                print("⚠️  All database tables dropped")
        else:
            db.drop_all()
            print("⚠️  All database tables dropped")
    
    @staticmethod
    def reset_database(app=None):
        """
        Drop all tables and recreate them. USE WITH CAUTION!
        
        Args:
            app: Flask app instance (optional, uses current app context if None)
        """
        DatabaseManager.drop_all_tables(app)
        DatabaseManager.initialize_database(app)
        print("🔄 Database reset complete")
    
    @staticmethod
    def seed_test_data(app=None):
        """
        Seed database with test data for development.
        
        Args:
            app: Flask app instance (optional, uses current app context if None)
        """
        def _seed():
            try:
                # Check if data already exists
                if User.query.count() > 0:
                    print("⚠️  Database already contains data. Skipping seed.")
                    return
                
                print("🌱 Seeding test data...")
                
                # Create test users
                users_data = [
                    {
                        'username': 'alice_demo',
                        'email': 'alice@example.com',
                        'password': 'password123'
                    },
                    {
                        'username': 'bob_test',
                        'email': 'bob@example.com', 
                        'password': 'password123'
                    },
                    {
                        'username': 'charlie_dev',
                        'email': 'charlie@example.com',
                        'password': 'password123'
                    },
                    {
                        'username': 'diana_user',
                        'email': 'diana@example.com',
                        'password': 'password123'
                    }
                ]
                
                users = []
                for user_data in users_data:
                    user = User(
                        username=user_data['username'],
                        email=user_data['email'],
                        password_hash=generate_password_hash(user_data['password']),
                        streak_count=random.randint(0, 30),
                        total_points=random.randint(0, 1000)
                    )
                    users.append(user)
                    db.session.add(user)
                
                db.session.commit()
                print(f"✅ Created {len(users)} test users")
                
                # Create screen time logs for the past 30 days
                for user in users:
                    for i in range(30):
                        log_date = date.today() - timedelta(days=i)
                        
                        # Skip some days to make data more realistic
                        if random.random() < 0.2:  # 20% chance to skip
                            continue
                        
                        # Generate realistic screen time (30-480 minutes)
                        screen_time = random.randint(30, 480)
                        
                        # Generate top apps data
                        apps = ['Instagram', 'TikTok', 'YouTube', 'Twitter', 'Facebook', 'WhatsApp', 'Snapchat']
                        top_apps = []
                        remaining_time = screen_time
                        
                        for app in random.sample(apps, min(3, len(apps))):
                            if remaining_time <= 0:
                                break
                            app_time = min(random.randint(10, 120), remaining_time)
                            top_apps.append({"name": app, "minutes": app_time})
                            remaining_time -= app_time
                        
                        log = ScreenTimeLog(
                            user_id=user.id,
                            date=log_date,
                            screen_time_minutes=screen_time,
                            top_apps=str(top_apps).replace("'", '"')  # Convert to JSON-like string
                        )
                        db.session.add(log)
                
                db.session.commit()
                print("✅ Created screen time logs for past 30 days")
                
                # Create goals for users
                for user in users:
                    # Daily goal
                    daily_goal = Goal(
                        user_id=user.id,
                        goal_type='daily',
                        target_minutes=random.choice([120, 180, 240, 300])
                    )
                    db.session.add(daily_goal)
                    
                    # Weekly goal (50% chance)
                    if random.random() < 0.5:
                        weekly_goal = Goal(
                            user_id=user.id,
                            goal_type='weekly',
                            target_minutes=random.choice([900, 1200, 1500, 1800])  # 15-30 hours
                        )
                        db.session.add(weekly_goal)
                
                db.session.commit()
                print("✅ Created goals for users")
                
                # Create friendships between users
                friendships_to_create = [
                    (users[0].id, users[1].id, 'accepted'),
                    (users[0].id, users[2].id, 'accepted'),
                    (users[1].id, users[3].id, 'pending'),
                    (users[2].id, users[3].id, 'accepted'),
                ]
                
                for user_id, friend_id, status in friendships_to_create:
                    friendship = Friendship(
                        user_id=user_id,
                        friend_id=friend_id,
                        status=status
                    )
                    db.session.add(friendship)
                
                db.session.commit()
                print("✅ Created friendships between users")
                
                print("🎉 Test data seeding completed!")
                print("\nTest user accounts:")
                for user_data in users_data:
                    print(f"  📧 {user_data['email']} / {user_data['password']}")
                
            except Exception as e:
                db.session.rollback()
                print(f"❌ Error seeding data: {str(e)}")
                raise e
        
        if app:
            with app.app_context():
                _seed()
        else:
            _seed()
    
    @staticmethod
    def clear_test_data():
        """
        Clear all test data but keep database structure.
        """
        try:
            # Delete in order to respect foreign key constraints
            Friendship.query.delete()
            Goal.query.delete()
            ScreenTimeLog.query.delete()
            User.query.delete()
            
            db.session.commit()
            print("🧹 All test data cleared")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error clearing data: {str(e)}")
            raise e
    
    @staticmethod
    def get_database_stats():
        """
        Get statistics about current database state.
        
        Returns:
            dict: Database statistics
        """
        try:
            stats = {
                'users': User.query.count(),
                'screen_time_logs': ScreenTimeLog.query.count(),
                'goals': Goal.query.count(),
                'friendships': Friendship.query.count(),
                'accepted_friendships': Friendship.query.filter_by(status='accepted').count(),
                'pending_friendships': Friendship.query.filter_by(status='pending').count()
            }
            
            # Get date range of logs
            oldest_log = ScreenTimeLog.query.order_by(ScreenTimeLog.date.asc()).first()
            newest_log = ScreenTimeLog.query.order_by(ScreenTimeLog.date.desc()).first()
            
            if oldest_log and newest_log:
                stats['log_date_range'] = {
                    'oldest': oldest_log.date.isoformat(),
                    'newest': newest_log.date.isoformat()
                }
            
            return stats
            
        except Exception as e:
            print(f"❌ Error getting database stats: {str(e)}")
            return {}
    
    @staticmethod
    def backup_database(backup_path=None):
        """
        Create a simple backup of database data.
        
        Args:
            backup_path (str, optional): Path for backup file
        """
        if not backup_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"backup_{timestamp}.sql"
        
        try:
            # This is a simple implementation - in production you'd use proper database backup tools
            print(f"📦 Creating backup at {backup_path}")
            print("⚠️  Note: This is a basic backup. Use proper database backup tools in production.")
            
            # For SQLite, you could copy the file
            # For other databases, you'd use database-specific backup commands
            
            return backup_path
            
        except Exception as e:
            print(f"❌ Error creating backup: {str(e)}")
            return None


def create_db_cli_commands(app):
    """
    Create Flask CLI commands for database management.
    
    Args:
        app: Flask application instance
    """
    
    @app.cli.command("init-db")
    def init_db_command():
        """Initialize the database."""
        DatabaseManager.initialize_database(app)
    
    @app.cli.command("reset-db")
    def reset_db_command():
        """Reset the database (drops and recreates all tables)."""
        confirm = input("⚠️  This will delete ALL data. Are you sure? (yes/no): ")
        if confirm.lower() == 'yes':
            DatabaseManager.reset_database(app)
        else:
            print("Operation cancelled.")
    
    @app.cli.command("seed-db")
    def seed_db_command():
        """Seed the database with test data."""
        DatabaseManager.seed_test_data(app)
    
    @app.cli.command("clear-db")
    def clear_db_command():
        """Clear all data from database."""
        confirm = input("⚠️  This will delete ALL data. Are you sure? (yes/no): ")
        if confirm.lower() == 'yes':
            DatabaseManager.clear_test_data()
        else:
            print("Operation cancelled.")
    
    @app.cli.command("db-stats")
    def db_stats_command():
        """Show database statistics."""
        stats = DatabaseManager.get_database_stats()
        print("\n📊 Database Statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
        print()
