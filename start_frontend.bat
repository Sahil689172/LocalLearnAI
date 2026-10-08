@echo off
REM LocalLearn AI - Start Frontend Development Server

echo ============================================================
echo LocalLearn AI - Starting Frontend Dev Server
echo ============================================================
echo.

REM Check if node_modules exists
if not exist "frontend\node_modules" (
    echo Installing frontend dependencies...
    cd frontend
    call npm install
    cd ..
)

REM Start the frontend
echo.
echo Starting frontend development server...
echo Press CTRL+C to stop
echo.

cd frontend
call npm run dev
