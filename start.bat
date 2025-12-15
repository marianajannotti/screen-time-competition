@echo off
setlocal enabledelayedexpansion


REM Start Screen Time Competition App
REM Runs both backend (Flask) and frontend (Vite) concurrently

echo Starting Screen Time Competition App...
echo.

REM Check for virtual environment
set PYTHON_EXE=python
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    set PYTHON_EXE=venv\Scripts\python.exe

) else if exist "..\venv\Scripts\activate.bat" (
    echo Activating virtual environment from parent directory...
    set PYTHON_EXE=..\venv\Scripts\python.exe

) else (
    echo  No virtual environment found. Using system Python.
    echo    Consider creating one with: python -m venv venv
    pause
    exit /b 1
)

REM Check if Python is available
!PYTHON_EXE! --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed or not in PATH
    pause
    exit /b 1
)

echo Using Python: !PYTHON_EXE!
!PYTHON_EXE! --version


REM Check if npm is available
call npm --version >nul 2>&1
if errorlevel 1 (
    echo npm is not installed or not in PATH
    pause
    exit /b 1
)

REM Check if backend dependencies are installed
echo Checking backend dependencies...
!PYTHON_EXE! -c "import flask, flask_login, flask_cors, flask_mail, flask_sqlalchemy" >nul 2>&1
if errorlevel 1 (
    echo  Some backend dependencies missing. Installing...
    !PYTHON_EXE! -m pip install -r backend/requirements.txt
) else (
    echo Backend dependencies installed
)

REM Check if frontend dependencies are installed
if not exist "frontend\node_modules" (
    echo  Frontend dependencies not found. Installing...
    cd frontend
    call npm install
    cd ..
)

echo.
echo Starting servers...
echo    Backend:  http://localhost:5001
echo    Frontend: Check terminal window (usually http://localhost:5173)
echo.
echo Press Ctrl+C to stop both servers
echo.

REM Start backend in background
start "Flask Backend" cmd /c "!PYTHON_EXE! run_backend.py"

REM Wait a bit for backend to start
timeout /t 2 /nobreak >nul

REM Start frontend in background
cd frontend
start "Vite Frontend" cmd /c "npm run dev"
cd ..

echo.
echo ✅ Both servers are running in separate windows!
echo Close this window or press any key to stop tracking...
pause >nul
