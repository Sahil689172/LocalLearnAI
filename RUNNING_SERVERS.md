# Running LocalLearn AI Servers

This guide explains how to run the backend and frontend servers for LocalLearn AI.

## Quick Start

### Recommended: No Auto-Reload (Stable)

**Terminal 1 - Backend:**
```cmd
start_backend.bat
```

**Terminal 2 - Frontend:**
```cmd
start_frontend.bat
```

This runs the backend **without auto-reload**, which prevents job loss during video generation.

### Alternative: With Auto-Reload (Development)

Only use this when actively developing backend code. Jobs will be lost when code changes!

**Terminal 1 - Backend:**
```cmd
start_backend_dev.bat
```

## Why No Auto-Reload?

The backend stores jobs **in memory**. When uvicorn's auto-reload detects ANY file change (including files created in `output/` during video generation), it restarts the server and **clears all jobs**.

### The Problem with Auto-Reload

```
1. Frontend creates job → job_id: abc-123
2. Backend generates video → creates output/video.mp4
3. Uvicorn detects file change → restarts server
4. Job registry cleared → job_id abc-123 doesn't exist
5. Frontend polls status → 404 Not Found
```

### The Solution: No Auto-Reload

```
1. Frontend creates job → job_id: abc-123
2. Backend generates video → creates output/video.mp4
3. Server keeps running (no auto-reload)
4. Job registry intact → job_id abc-123 exists
5. Frontend polls status → 200 OK ✓
```

## Manual Commands

### Backend (Stable - No Auto-Reload)

```cmd
.venv\Scripts\activate.bat
pip install -r requirements-api.txt
uvicorn backend_api:app --port 8000
```

### Backend (Development - With Auto-Reload)

```cmd
.venv\Scripts\activate.bat
pip install -r requirements-api.txt
uvicorn backend_api:app --reload --port 8000
```

⚠️ **Warning:** With `--reload`, you must complete video generation before making code changes, or the job will be lost.

### Frontend

```cmd
cd frontend
npm install
npm run dev
```

## Testing the Backend

Before using the frontend, verify the backend is working:

```powershell
python test_backend.py
```

This will:
1. Check if the backend is running
2. Test video generation (topic mode)
3. Test job status polling
4. Test custom script mode

## Accessing the Application

- **Frontend:** http://localhost:5173 (or whatever Vite shows)
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs (Swagger UI)

## Troubleshooting

### Backend Won't Start

**Error:** `ModuleNotFoundError: No module named 'fastapi'`

**Solution:**
```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements-api.txt
```

### Frontend Can't Connect to Backend

**Error:** `Failed to fetch` or `Network error`

**Solution:**
1. Check if backend is running: http://localhost:8000
2. Check CORS configuration in `backend_api.py`
3. Verify frontend API URL in `frontend/src/config/api.ts`

## Troubleshooting

### Jobs Disappear (404 errors)

**Error:** `GET http://localhost:8000/api/video/status/{job_id} 404 (Not Found)`

**Cause:** Backend auto-reload is restarting the server (in-memory jobs are cleared)

**Solution:**
1. Stop the backend (CTRL+C)
2. Restart WITHOUT auto-reload:
   ```cmd
   start_backend.bat
   ```
   Or manually:
   ```cmd
   uvicorn backend_api:app --port 8000
   ```

**Note:** The `--reload-exclude` pattern doesn't work reliably in uvicorn on Windows. The only reliable solution is to disable auto-reload entirely.

### Video Generation Fails

Check the backend terminal for error messages. Common issues:

1. **Ollama not running:** Start Ollama before using topic mode
2. **ManimGL not found:** Check `config.py` for correct ManimGL path
3. **Piper TTS missing:** Run `python setup_piper.py`
4. **FFmpeg not found:** Install FFmpeg and add to PATH

## Production Deployment

For production, run the backend without `--reload`:

```powershell
uvicorn backend_api:app --host 0.0.0.0 --port 8000
```

Note: The in-memory job registry is not suitable for production. Consider:
- Using a database (PostgreSQL, Redis)
- Implementing persistent job storage
- Adding job cleanup/expiration
- Using a task queue (Celery, RQ)

## Architecture

```
┌─────────────┐         ┌──────────────┐
│  Frontend   │  HTTP   │   Backend    │
│   (Vite)    │◄───────►│  (FastAPI)   │
│  Port 5173  │         │  Port 8000   │
└─────────────┘         └──────────────┘
                              │
                              ├─► Ollama (lesson planning)
                              ├─► Piper TTS (voice generation)
                              ├─► ManimGL (animation)
                              └─► FFmpeg (video muxing)
```

## Development Workflow

1. Start backend in Terminal 1
2. Start frontend in Terminal 2
3. Open browser to http://localhost:5173
4. Make changes to code
5. Both servers auto-reload (frontend hot-reloads, backend reloads on .py changes)

**Important:** Existing jobs are lost when backend reloads. Complete video generation before making backend code changes, or disable `--reload` for backend.
