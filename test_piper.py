"""
LocalLearn AI - Piper TTS Test Script
--------------------------------------
Quick verification that Piper TTS is properly configured.

Usage:
    python test_piper.py
"""

import sys
import os
from pathlib import Path

def test_piper_executable():
    """Test 1: Check if Piper executable is available."""
    print("\n[Test 1] Checking Piper executable...")
    
    from tts.piper_tts import PiperTTS
    
    tts = PiperTTS()
    exe = tts._find_piper_executable()
    
    if exe:
        print(f"  ✓ Piper executable found: {exe}")
        return True
    else:
        print(f"  ✗ Piper executable not found")
        print(f"    Install with: pip install piper-tts")
        print(f"    Or download from: https://github.com/rhasspy/piper/releases")
        return False


def test_voice_models():
    """Test 2: Check if voice models are available."""
    print("\n[Test 2] Checking voice models...")
    
    project_root = Path(__file__).parent
    models_dir = project_root / "models" / "piper"
    
    languages = ["en", "hi", "ta", "te", "mr"]
    found = []
    missing = []
    
    for lang in languages:
        lang_dir = models_dir / lang
        if lang_dir.exists():
            onnx_files = list(lang_dir.glob("*.onnx"))
            json_files = list(lang_dir.glob("*.onnx.json"))
            
            if onnx_files and json_files:
                print(f"  ✓ {lang}: {onnx_files[0].name}")
                found.append(lang)
            else:
                print(f"  ✗ {lang}: directory exists but no model files")
                missing.append(lang)
        else:
            print(f"  ✗ {lang}: directory not found")
            missing.append(lang)
    
    if found:
        print(f"\n  Found models for: {', '.join(found)}")
    
    if missing:
        print(f"\n  Missing models for: {', '.join(missing)}")
        print(f"  Download with: python setup_piper.py --language en")
    
    return len(found) > 0


def test_piper_load():
    """Test 3: Load Piper TTS service."""
    print("\n[Test 3] Loading Piper TTS service...")
    
    try:
        from tts.piper_tts import PiperTTS, PiperConfig
        
        tts = PiperTTS(PiperConfig(language="en"))
        tts.load()
        
        print("  ✓ Piper TTS loaded successfully")
        print(f"    Model: {tts.model_path.name}")
        print(f"    Config: {tts.config_path.name}")
        
        return True
    
    except FileNotFoundError as e:
        print(f"  ✗ Model files not found")
        print(f"    {e}")
        return False
    
    except Exception as e:
        print(f"  ✗ Load failed: {e}")
        return False


def test_generation():
    """Test 4: Generate a test audio file."""
    print("\n[Test 4] Generating test audio...")
    
    try:
        from tts.piper_tts import PiperTTS, PiperConfig
        
        tts = PiperTTS(PiperConfig(language="en"))
        tts.load()
        
        test_text = "This is a test of Piper text to speech for LocalLearn AI."
        test_output = "test_piper_output.wav"
        
        print(f"  Text: {test_text}")
        print(f"  Output: {test_output}")
        
        success = tts.generate_audio(test_text, test_output)
        
        if success and os.path.exists(test_output):
            file_size = os.path.getsize(test_output)
            print(f"  ✓ Audio generated: {file_size / 1024:.1f} KB")
            
            # Measure duration
            from tts.audio_utils import measure_audio_duration
            duration = measure_audio_duration(test_output)
            print(f"  ✓ Duration: {duration:.2f}s")
            
            # Cleanup
            os.remove(test_output)
            print(f"  ✓ Test file cleaned up")
            
            return True
        else:
            print(f"  ✗ Generation failed")
            return False
    
    except Exception as e:
        print(f"  ✗ Generation error: {e}")
        return False


def test_worker():
    """Test 5: Test TTS worker subprocess."""
    print("\n[Test 5] Testing TTS worker...")
    
    import json
    import subprocess
    
    try:
        job = {
            "beats": [
                {
                    "id": "test_beat_1",
                    "narration": "Testing TTS worker with Piper.",
                    "language": "en"
                }
            ],
            "output_dir": "test_worker_audio",
            "language": "en"
        }
        
        result = subprocess.run(
            [sys.executable, "tts_worker.py"],
            input=json.dumps(job),
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            print(f"  ✗ Worker failed")
            print(f"    stderr: {result.stderr[:200]}")
            return False
        
        # Parse response
        response = json.loads(result.stdout.strip())
        
        if response.get("ok"):
            print(f"  ✓ Worker succeeded")
            print(f"    Beats processed: {response['beat_count']}")
            print(f"    Total duration: {response['total_duration']:.2f}s")
            
            # Cleanup
            import shutil
            if os.path.exists("test_worker_audio"):
                shutil.rmtree("test_worker_audio")
                print(f"  ✓ Test files cleaned up")
            
            return True
        else:
            print(f"  ✗ Worker error: {response.get('error')}")
            return False
    
    except json.JSONDecodeError as e:
        print(f"  ✗ JSON parse error: {e}")
        print(f"    stdout: {result.stdout[:200]}")
        return False
    
    except Exception as e:
        print(f"  ✗ Worker test error: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 70)
    print("LocalLearn AI - Piper TTS Test Suite")
    print("=" * 70)
    
    tests = [
        ("Piper Executable", test_piper_executable),
        ("Voice Models", test_voice_models),
        ("Service Load", test_piper_load),
        ("Audio Generation", test_generation),
        ("TTS Worker", test_worker),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n  ✗ Test crashed: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {name}")
    
    print()
    print(f"  Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All tests passed! Piper TTS is ready.")
        print("\nNext steps:")
        print("  python generate.py \"linear search\" --language en")
    else:
        print("\n✗ Some tests failed. See error messages above.")
        print("\nCommon fixes:")
        print("  1. Install Piper: pip install piper-tts")
        print("  2. Download models: python setup_piper.py --language en")
        print("  3. See: models/piper/README.md")
    
    print()
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
