@echo off
REM Seed database script for Windows

echo Seeding Screen Time Competition Database...
echo.

REM Check for virtual environment
set PYTHON_EXE=python
if exist "venv\Scripts\python.exe" (
    echo Activating virtual environment...
    set PYTHON_EXE=venv\Scripts\python.exe
) else if exist "..\venv\Scripts\python.exe" (
    echo Activating virtual environment from parent directory...
    set PYTHON_EXE=..\venv\Scripts\python.exe
) else (
    echo No virtual environment found. Using system Python.
)

REM Check if Python is available
%PYTHON_EXE% --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Run the seed script
%PYTHON_EXE% backend\seed_database.py

echo.
echo Done! You can now start the app with start.bat
pause
