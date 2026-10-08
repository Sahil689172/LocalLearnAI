#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Start LocalLearn AI Backend with Auto-Reload (Development)

.DESCRIPTION
    Starts FastAPI backend WITH auto-reload for development.
    WARNING: Auto-reload clears in-memory jobs!
    Use start_backend.ps1 for stable video generation.

.EXAMPLE
    .\start_backend_dev.ps1
#>

Write-Host "=" -ForegroundColor Yellow -NoNewline
Write-Host ("=" * 59) -ForegroundColor Yellow
Write-Host "LocalLearn AI - Backend with Auto-Reload (DEV MODE)" -ForegroundColor Yellow
Write-Host "WARNING: Jobs will be lost on code changes!" -ForegroundColor Red
Write-Host "=" -ForegroundColor Yellow -NoNewline
Write-Host ("=" * 59) -ForegroundColor Yellow
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

# Start the server with auto-reload
Write-Host ""
Write-Host "Starting FastAPI server on http://localhost:8000 with auto-reload" -ForegroundColor Green
Write-Host "Press CTRL+C to stop" -ForegroundColor Yellow
Write-Host ""

& uvicorn backend_api:app --reload --port 8000
