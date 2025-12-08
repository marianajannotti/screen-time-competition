#!/bin/bash

# Start Screen Time Competition App
# Runs both backend (Flask) and frontend (Vite) concurrently

echo "🚀 Starting Screen Time Competition App..."
echo ""

# Check if already in a virtual environment
if [ -n "$VIRTUAL_ENV" ]; then
    echo "✅ Virtual environment already active: $VIRTUAL_ENV"
else
    # Detect and activate Python virtual environment if it exists
if [ -d "venv" ]; then
    echo "📦 Activating virtual environment (./venv)..."
    source venv/bin/activate
elif [ -d "../venv" ]; then
    echo "📦 Activating virtual environment (../venv)..."
    source ../venv/bin/activate
elif [ -d "../../venv" ]; then
    echo "📦 Activating virtual environment (../../venv)..."
    source ../../venv/bin/activate
    else
        echo "⚠️  No virtual environment found. Using system Python."
        echo "   Consider creating one with: python -m venv venv"
    fi
fi

# Check if Python is available
if ! command -v python &> /dev/null; then
    echo "❌ Python is not installed or not in PATH"
    exit 1
fi

echo "   Using Python: $(which python)"
echo "   Version: $(python --version)"

# Check if npm is available
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed or not in PATH"
    exit 1
fi

# Check if backend dependencies are installed
echo "🔍 Checking backend dependencies..."
if ! python -c "import flask, flask_login, flask_cors, flask_mail, flask_sqlalchemy" 2>/dev/null; then
    echo "⚠️  Some backend dependencies missing. Installing..."
    pip install -r requirements.txt
else
    echo "✅ Backend dependencies installed"
fi

# Check if frontend dependencies are installed
if [ ! -d "offy-front/node_modules" ]; then
    echo "⚠️  Frontend dependencies not found. Installing..."
    cd offy-front && npm install && cd ..
fi

# Function to cleanup background processes on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down servers..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit
}

trap cleanup SIGINT SIGTERM

# Check if backend port is already in use
if lsof -Pi :5001 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "⚠️  Port 5001 is already in use. Killing existing process..."
    kill -9 $(lsof -Pi :5001 -sTCP:LISTEN -t) 2>/dev/null
    sleep 1
fi

# Start backend
echo "📦 Starting Flask backend on http://localhost:5001..."
python run.py &
BACKEND_PID=$!

# Wait a bit for backend to start
sleep 2

# Start frontend
echo "⚛️  Starting Vite frontend on http://localhost:5173..."
cd offy-front && npm run dev &
FRONTEND_PID=$!

echo ""
echo "✅ Both servers are running!"
echo "   Backend:  http://localhost:5001"
echo "   Frontend: Check terminal above (usually http://localhost:5173)"
echo ""
echo "Press Ctrl+C to stop both servers"

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID
