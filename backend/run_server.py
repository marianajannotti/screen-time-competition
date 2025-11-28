#!/usr/bin/env python3
"""
Development server runner for Screen Time Competition Backend
Run this script to start the Flask development server
"""

import os
from backend import create_app

if __name__ == "__main__":
    # Set development environment if not already set
    if not os.environ.get("FLASK_ENV"):
        os.environ["FLASK_ENV"] = "development"
    
    # Create app instance
    app = create_app()
    
    # Run the development server
    print("Starting Screen Time Competition Backend...")
    print("API will be available at: http://localhost:5000")
    print("API endpoints:")
    print("  - Authentication: /api/auth/*")
    print("  - Screen Time: /api/screentime/*")
    print("  - Goals: /api/goals/*")
    print("  - Friends: /api/friends/*")
    print("  - Profile: /api/profile/*")
    
    app.run(
        debug=True,
        host="0.0.0.0",  # Allow external connections
        port=5000
    )