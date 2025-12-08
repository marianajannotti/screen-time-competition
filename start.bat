@echo off
REM Start Screen Time Competition App
REM Runs both backend (Flask) and frontend (Vite) concurrently

echo 🚀 Starting Screen Time Competition App...
echo.

REM Check for virtual environment
if exist "venv\Scripts\activate.bat" (
    echo 📦 Activating virtual environment...
    call venv\Scripts\activate.bat
) else if exist "..\venv\Scripts\activate.bat" (
    echo 📦 Activating virtual environment from parent directory...
    call ..\venv\Scripts\activate.bat
) else (
    echo ⚠️  No virtual environment found. Using system Python.
    echo    Consider creating one with: python -m venv venv
)

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    pause
    exit /b 1
)

echo    Using Python: 
where python
python --version

REM Check if npm is available
npm --version >nul 2>&1
if errorlevel 1 (
    echo ❌ npm is not installed or not in PATH
    pause
    exit /b 1
)

REM Check if backend dependencies are installed
python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Flask not found. Installing backend dependencies...
    pip install -r requirements.txt
)

REM Check if frontend dependencies are installed
if not exist "offy-front\node_modules" (
    echo ⚠️  Frontend dependencies not found. Installing...
    cd offy-front
    call npm install
    cd ..
)

echo.
echo ✅ Starting servers...
echo    Backend:  http://localhost:5001
echo    Frontend: Check terminal window (usually http://localhost:5173)
echo.
echo Press Ctrl+C to stop both servers
echo.

REM Start backend in background
start "Flask Backend" cmd /c "python run.py"

REM Wait a bit for backend to start
timeout /t 2 /nobreak >nul

REM Start frontend in background
cd offy-front
start "Vite Frontend" cmd /c "npm run dev"
cd ..

echo.
echo ✅ Both servers are running in separate windows!
echo Close this window or press any key to stop tracking...
pause >nul
