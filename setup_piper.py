"""
LocalLearn AI - Piper TTS Setup Helper
---------------------------------------
Helps download and configure Piper TTS for LocalLearn AI.

Usage:
    python setup_piper.py --language en
    python setup_piper.py --language hi --language ta
    python setup_piper.py --all
"""

import argparse
import os
import sys
import urllib.request
import json
from pathlib import Path

# Piper voice model URLs (GitHub releases)
# Format: language -> (model_name, base_url)
PIPER_VOICE_URLS = {
    "en": (
        "en_US-lessac-medium",
        "https://github.com/rhasspy/piper/releases/download/v1.2.0/en_US-lessac-medium.onnx",
        "https://github.com/rhasspy/piper/releases/download/v1.2.0/en_US-lessac-medium.onnx.json",
    ),
    # Add more languages as they become available in Piper releases
    # Check: https://github.com/rhasspy/piper/releases/latest
}

# Note: Indic languages (hi, ta, te, mr) may not have official Piper models yet.
# Users will need to find/train models separately if needed.


def download_file(url: str, destination: Path) -> bool:
    """Download a file from URL to destination."""
    try:
        print(f"  Downloading: {url}")
        print(f"  → {destination}")
        
        with urllib.request.urlopen(url, timeout=300) as response:
            data = response.read()
            destination.parent.mkdir(parents=True, exist_ok=True)
            with open(destination, 'wb') as f:
                f.write(data)
        
        print(f"  ✓ Downloaded ({len(data) / 1024 / 1024:.1f} MB)")
        return True
    
    except urllib.error.HTTPError as e:
        print(f"  ✗ HTTP Error {e.code}: {e.reason}")
        return False
    except urllib.error.URLError as e:
        print(f"  ✗ URL Error: {e.reason}")
        return False
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def setup_language(language: str, models_dir: Path) -> bool:
    """Download and setup Piper voice for a language."""
    
    if language not in PIPER_VOICE_URLS:
        print(f"\n[{language}] No automatic download available.")
        print(f"  Please manually download Piper voice model for '{language}'")
        print(f"  and place in: {models_dir / language}/")
        print(f"  Sources:")
        print(f"    - https://github.com/rhasspy/piper/releases")
        print(f"    - https://huggingface.co/rhasspy/piper-voices")
        return False
    
    model_name, onnx_url, json_url = PIPER_VOICE_URLS[language]
    lang_dir = models_dir / language
    
    onnx_path = lang_dir / f"{model_name}.onnx"
    json_path = lang_dir / f"{model_name}.onnx.json"
    
    print(f"\n[{language}] Setting up {model_name}...")
    
    # Check if already exists
    if onnx_path.exists() and json_path.exists():
        print(f"  ✓ Already installed")
        return True
    
    # Download .onnx file
    if not onnx_path.exists():
        if not download_file(onnx_url, onnx_path):
            return False
    
    # Download .onnx.json file
    if not json_path.exists():
        if not download_file(json_url, json_path):
            return False
    
    print(f"  ✓ Setup complete")
    return True


def check_piper_executable() -> bool:
    """Check if Piper executable is available."""
    import subprocess
    
    exe_name = "piper.exe" if sys.platform == "win32" else "piper"
    
    try:
        result = subprocess.run(
            [exe_name, "--version"],
            capture_output=True,
            timeout=5
        )
        if result.returncode == 0:
            print(f"✓ Piper executable found: {exe_name}")
            return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    print(f"✗ Piper executable not found")
    print(f"  Please install Piper:")
    print(f"    pip install piper-tts")
    print(f"  Or download from:")
    print(f"    https://github.com/rhasspy/piper/releases")
    
    return False


def main():
    parser = argparse.ArgumentParser(
        description="Setup Piper TTS for LocalLearn AI"
    )
    parser.add_argument(
        "--language",
        action="append",
        choices=["en", "hi", "ta", "te", "mr"],
        help="Language to setup (can specify multiple times)"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Setup all supported languages"
    )
    
    args = parser.parse_args()
    
    # Determine project root
    script_dir = Path(__file__).parent
    models_dir = script_dir / "models" / "piper"
    
    print("=" * 70)
    print("LocalLearn AI - Piper TTS Setup")
    print("=" * 70)
    print()
    
    # Check Piper executable
    piper_ok = check_piper_executable()
    print()
    
    # Determine languages to setup
    if args.all:
        languages = ["en"]  # Only en has automatic download
        print("Setting up all available languages...")
    elif args.language:
        languages = args.language
    else:
        print("No language specified. Use --language or --all")
        print("Example: python setup_piper.py --language en")
        sys.exit(1)
    
    # Setup each language
    success_count = 0
    for lang in languages:
        if setup_language(lang, models_dir):
            success_count += 1
    
    # Summary
    print()
    print("=" * 70)
    print("Setup Summary")
    print("=" * 70)
    print(f"Piper executable: {'✓' if piper_ok else '✗'}")
    print(f"Languages setup: {success_count}/{len(languages)}")
    print()
    
    if success_count > 0:
        print("✓ Setup complete!")
        print()
        print("Test with:")
        print(f'  python generate.py "linear search" --language en')
    else:
        print("✗ Setup incomplete")
        print()
        print("Manual setup required:")
        print(f"  1. Download voice models from:")
        print(f"     https://github.com/rhasspy/piper/releases")
        print(f"  2. Place in: {models_dir}/<language>/")
        print(f"  3. See: {models_dir}/README.md")
    
    print()


if __name__ == "__main__":
    main()
