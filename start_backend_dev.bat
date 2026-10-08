@echo off
REM LocalLearn AI - Start Backend with Auto-Reload (Development Mode)
REM WARNING: Auto-reload will clear jobs when code changes!
REM Use start_backend.bat for stable video generation

echo ============================================================
echo LocalLearn AI - Backend with Auto-Reload (DEV MODE)
echo WARNING: Jobs will be lost on code changes!
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

REM Start the server with auto-reload
echo.
echo Starting FastAPI server on http://localhost:8000 with auto-reload
echo Press CTRL+C to stop
echo.

uvicorn backend_api:app --reload --port 8000
