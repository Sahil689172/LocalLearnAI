"""
LocalLearn AI - Configuration
------------------------------
Centralized configuration for LocalLearn AI.

CRITICAL: This project uses ManimGL (not Manim Community Edition).
The ManimGL executable path must point to a working ManimGL installation.
"""

import os
from pathlib import Path

# ---------------------------------------------------------------------------
# MANIMGL CONFIGURATION
# ---------------------------------------------------------------------------

# IMPORTANT: LocalLearn uses ManimGL syntax (from manimlib import *)
# This executable path points to the verified working ManimGL installation.
# 
# Verified ManimGL installation:
#   Path: C:\Users\hp\LLAI\.venv\Scripts\manimgl.exe
#   Version: ManimGL v1.7.2
#   Import: from manimlib import * (works correctly)
#
# DO NOT change this to use Manim Community Edition.
# DO NOT use "manim" or "manimce" commands.
MANIMGL_EXECUTABLE = r"C:\Users\hp\LLAI\.venv\Scripts\manimgl.exe"

# ManimGL rendering timeout (seconds)
MANIMGL_TIMEOUT = 600  # 10 minutes

# Quality flags for ManimGL
# -l = low quality (fast)
# -m = medium quality
# -h = high quality
MANIMGL_QUALITY = "-l"  # default to low for fast rendering

# ---------------------------------------------------------------------------
# OLLAMA CONFIGURATION
# ---------------------------------------------------------------------------

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3:latest"

# ---------------------------------------------------------------------------
# OUTPUT CONFIGURATION
# ---------------------------------------------------------------------------

OUTPUT_ROOT = "output"
SCENE_CLASS = "GeneratedLessonScene"

# ---------------------------------------------------------------------------
# TTS CONFIGURATION
# ---------------------------------------------------------------------------

TTS_TIMEOUT = 120  # 2 minutes for Piper TTS

# ---------------------------------------------------------------------------
# VALIDATION
# ---------------------------------------------------------------------------

def validate_manimgl_installation() -> tuple[bool, str]:
    """
    Validate that the ManimGL executable exists and is accessible.
    
    Returns:
        (is_valid: bool, message: str)
    """
    manimgl_path = Path(MANIMGL_EXECUTABLE)
    
    if not manimgl_path.exists():
        return False, f"ManimGL executable not found at: {MANIMGL_EXECUTABLE}"
    
    if not manimgl_path.is_file():
        return False, f"ManimGL path is not a file: {MANIMGL_EXECUTABLE}"
    
    # Check if it's an executable (Windows .exe)
    if not str(manimgl_path).endswith('.exe'):
        return False, f"ManimGL path does not appear to be a Windows executable: {MANIMGL_EXECUTABLE}"
    
    return True, f"ManimGL executable found: {MANIMGL_EXECUTABLE}"


def get_manimgl_version_info() -> dict:
    """
    Get ManimGL configuration info for diagnostics.
    
    Returns:
        Dictionary with ManimGL configuration details.
    """
    is_valid, message = validate_manimgl_installation()
    
    return {
        "executable": MANIMGL_EXECUTABLE,
        "exists": Path(MANIMGL_EXECUTABLE).exists(),
        "is_valid": is_valid,
        "message": message,
        "timeout": MANIMGL_TIMEOUT,
        "quality": MANIMGL_QUALITY,
    }
