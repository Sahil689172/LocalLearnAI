#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Start the LocalLearn AI Backend API Server

.DESCRIPTION
    This script starts the FastAPI backend with proper configuration:
    - Excludes output/ and media/ directories from auto-reload
    - Runs on port 8000
    - Enables hot-reload for code changes

.EXAMPLE
    .\start_backend.ps1
#>

Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host ("=" * 59) -ForegroundColor Cyan
Write-Host "LocalLearn AI - Starting Backend API Server" -ForegroundColor Cyan
Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host ("=" * 59) -ForegroundColor Cyan
Write-Host ""

# Check if virtual environment exists
if (-not (Test-Path ".venv")) {
    Write-Host "Error: Virtual environment not found at .venv" -ForegroundColor Red
    Write-Host "Please create it with: python -m venv .venv" -ForegroundColor Yellow
    exit 1
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Green
& ".\.venv\Scripts\Activate.ps1"

# Check if FastAPI is installed
Write-Host "Checking dependencies..." -ForegroundColor Green
$pipList = & python -m pip list
if ($pipList -notmatch "fastapi") {
    Write-Host "Installing API dependencies..." -ForegroundColor Yellow
    & python -m pip install -r requirements-api.txt
}

# Start the server
Write-Host ""
Write-Host "Starting FastAPI server on http://localhost:8000" -ForegroundColor Green
Write-Host "Press CTRL+C to stop" -ForegroundColor Yellow
Write-Host ""

# Start uvicorn WITHOUT auto-reload (recommended for video generation)
# Auto-reload clears in-memory jobs, causing 404 errors
Write-Host "Starting backend WITHOUT auto-reload (jobs will persist)..." -ForegroundColor Green
& uvicorn backend_api:app --port 8000
