#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Start the LocalLearn AI Frontend Development Server

.DESCRIPTION
    This script starts the React + Vite frontend development server

.EXAMPLE
    .\start_frontend.ps1
#>

Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host ("=" * 59) -ForegroundColor Cyan
Write-Host "LocalLearn AI - Starting Frontend Dev Server" -ForegroundColor Cyan
Write-Host "=" -ForegroundColor Cyan -NoNewline
Write-Host ("=" * 59) -ForegroundColor Cyan
Write-Host ""

# Check if node_modules exists
if (-not (Test-Path "frontend\node_modules")) {
    Write-Host "Installing frontend dependencies..." -ForegroundColor Yellow
    Set-Location frontend
    & npm install
    Set-Location ..
}

# Start the frontend
Write-Host ""
Write-Host "Starting frontend development server..." -ForegroundColor Green
Write-Host "Press CTRL+C to stop" -ForegroundColor Yellow
Write-Host ""

Set-Location frontend
& npm run dev
