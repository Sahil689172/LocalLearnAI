# Running LocalLearn AI Servers (Windows CMD)

## Quick Start with Batch Files

### Option 1: Using Batch Scripts (Recommended)

**Terminal 1 - Backend (CMD):**
```cmd
start_backend.bat
```

**Terminal 2 - Frontend (CMD):**
```cmd
start_frontend.bat
```

## Manual Commands for CMD

### Backend

```cmd
REM Activate virtual environment
.venv\Scripts\activate.bat

REM Install dependencies (first time only)
pip install -r requirements-api.txt

REM Start backend - Note the quotes around exclude patterns!
uvicorn backend_api:app --reload --port 8000 --reload-exclude="output/*" --reload-exclude="media/*"
```

### Frontend

```cmd
cd frontend

REM Install dependencies (first time only)
npm install

REM Start frontend
npm run dev
```

## Important Notes for Windows CMD

1. **Use double quotes** around exclude patterns: `--reload-exclude="output/*"`
2. **Don't use wildcards directly** in CMD without quotes
3. **Use .bat scripts** for convenience (they handle quoting properly)

## Testing

```cmd
python test_backend.py
```

## Troubleshooting

### If you get "unexpected extra arguments" error

**Wrong (PowerShell/CMD without quotes):**
```cmd
uvicorn backend_api:app --reload --reload-exclude output/*
```

**Correct (with quotes):**
```cmd
uvicorn backend_api:app --reload --reload-exclude="output/*"
```

### Shell Comparison

| Shell | Command |
|-------|---------|
| PowerShell | Use `start_backend.ps1` or quote patterns |
| CMD | Use `start_backend.bat` or use `--reload-exclude="pattern"` |
| Bash/Linux | Use `--reload-exclude 'pattern'` |

## See Also

- Full documentation: `RUNNING_SERVERS.md`
- Test backend: `python test_backend.py`
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
