@echo off
REM LocalLearn AI - Start Backend API Server
REM This script starts the FastAPI backend with proper configuration

echo ============================================================
echo LocalLearn AI - Starting Backend API Server
echo ============================================================
echo.

REM Check if virtual environment exists
if not exist ".venv" (
    echo Error: Virtual environment not found at .venv
    echo Please create it with: python -m venv .venv
    pause
    exit /b 1
)

REM Activate virtual environment
echo Activating virtual environment...
call .venv\Scripts\activate.bat

REM Check if FastAPI is installed
echo Checking dependencies...
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo Installing API dependencies...
    pip install -r requirements-api.txt
)

REM Start the server with proper exclusions
echo.
echo Starting FastAPI server on http://localhost:8000
echo Press CTRL+C to stop
echo.

REM Start backend WITHOUT auto-reload (recommended for video generation)
REM Auto-reload clears in-memory jobs, causing 404 errors
echo Starting backend WITHOUT auto-reload (jobs will persist)...
uvicorn backend_api:app --port 8000
