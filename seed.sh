#!/bin/bash

# Seed database script for macOS/Linux

echo "🌱 Seeding Screen Time Competition Database..."
echo ""

# Check for virtual environment
if [ -n "$VIRTUAL_ENV" ]; then
    echo "✅ Virtual environment already active: $VIRTUAL_ENV"
    PYTHON_CMD="python"
elif [ -d "venv" ]; then
    echo "📦 Activating virtual environment (./venv)..."
    source venv/bin/activate
    PYTHON_CMD="python"
elif [ -d "../venv" ]; then
    echo "📦 Activating virtual environment (../venv)..."
    source ../venv/bin/activate
    PYTHON_CMD="python"
else
    echo "⚠️  No virtual environment found. Using system Python."
    PYTHON_CMD="python3"
fi

# Check if Python is available
if ! command -v $PYTHON_CMD &> /dev/null; then
    echo "❌ Python is not installed or not in PATH"
    exit 1
fi

# Run the seed script
$PYTHON_CMD backend/seed_database.py

echo ""
echo "✨ Done! You can now start the app with ./start.sh"
