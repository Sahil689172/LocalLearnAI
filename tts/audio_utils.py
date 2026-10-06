"""
LocalLearn AI - Audio Utilities
---------------------------------
Audio duration measurement and concatenation.
"""

import os
import wave
import subprocess
import json
from pathlib import Path


def measure_audio_duration(wav_path: str) -> float:
    """
    Measure the duration of a WAV file in seconds.
    
    Uses wave module for fast local reading.
    Falls back to ffprobe if wave fails.
    
    Returns 0.0 if the file cannot be read.
    """
    if not os.path.exists(wav_path):
        return 0.0
    
    # Try wave module first (fast, no subprocess)
    try:
        with wave.open(wav_path, 'rb') as wf:
            frames = wf.getnframes()
            rate = wf.getframerate()
            if rate > 0:
                return frames / float(rate)
    except Exception:
        pass
    
    # Fall back to ffprobe
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                wav_path,
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            duration = data.get("format", {}).get("duration")
            if duration:
                return float(duration)
    except Exception:
        pass
    
    return 0.0


def concatenate_audio_files(
    input_files: list[str],
    output_path: str,
    sample_rate: int = 24000,
) -> bool:
    """
    Concatenate multiple WAV files into one using FFmpeg.
    
    Normalizes sample rate and channels before concatenation.
    
    Parameters
    ----------
    input_files : list of paths to WAV files
    output_path : path where concatenated WAV will be written
    sample_rate : target sample rate (default 24000 for Indic-Parler)
    
    Returns
    -------
    True if successful, False otherwise.
    """
    if not input_files:
        return False
    
    # Filter out missing files
    existing = [f for f in input_files if os.path.exists(f)]
    if not existing:
        return False
    
    # If only one file, just copy it
    if len(existing) == 1:
        try:
            import shutil
            shutil.copy2(existing[0], output_path)
            return True
        except Exception:
            return False
    
    # Create a temporary concat file for FFmpeg
    concat_list_path = output_path + ".concat.txt"
    try:
        with open(concat_list_path, "w", encoding="utf-8") as f:
            for wav_file in existing:
                # Escape single quotes for FFmpeg
                escaped = wav_file.replace("'", "'\\''")
                f.write(f"file '{escaped}'\n")
        
        # FFmpeg concat with normalization
        result = subprocess.run(
            [
                "ffmpeg",
                "-y",  # overwrite
                "-f", "concat",
                "-safe", "0",
                "-i", concat_list_path,
                "-ar", str(sample_rate),  # normalize sample rate
                "-ac", "1",  # mono
                output_path,
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )
        
        success = result.returncode == 0 and os.path.exists(output_path)
        
        # Clean up temp file
        try:
            os.remove(concat_list_path)
        except Exception:
            pass
        
        return success
        
    except Exception:
        # Clean up temp file
        try:
            if os.path.exists(concat_list_path):
                os.remove(concat_list_path)
        except Exception:
            pass
        return False
