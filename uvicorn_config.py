"""
Uvicorn configuration for LocalLearn AI Backend
Excludes output and media directories from reload watching
"""

# Reload configuration
reload = True
reload_dirs = ["."]
reload_excludes = [
    "output",
    "media", 
    ".venv",
    ".tts-venv",
    "manim",
    "frontend",
    "models",
    "__pycache__",
    "*.pyc",
]

# Server configuration
host = "127.0.0.1"
port = 8000
