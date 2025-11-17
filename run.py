"""
Development server runner for Screen Time Competition
Run this file to start the Flask development server
"""

from backend import create_app

# Create the Flask app using our factory
app = create_app("development")  # Use development mode

# Show current app mode
if app.config.get("TESTING"):
    print("🧪 Running in TESTING mode")
elif app.config.get("DEBUG"):
    print("🔧 Running in DEVELOPMENT mode")
else:
    print("🚀 Running in PRODUCTION mode")

if __name__ == "__main__":
    # Run in development mode
    app.run(host="127.0.0.1", port=5001, debug=True)
