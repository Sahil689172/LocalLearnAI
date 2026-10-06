"""
Comprehensive test suite for LocalLearn AI upgraded architecture.

Run individual tests:
    python test_pipeline.py test_lesson_planning
    python test_pipeline.py test_tts
    python test_pipeline.py test_timing
    python test_pipeline.py test_visual_renderer
    python test_pipeline.py test_muxing

Run all tests:
    python test_pipeline.py all
"""

import sys
import os
import json
import time
from pathlib import Path

from lesson_planner import generate_lesson_plan
from timing_service import create_timing_service
from visual_renderer import create_visual_renderer
from muxing_service import create_muxing_service
from language_codes import LanguageCode


# Test output directory
TEST_OUTPUT = "test_output"
Path(TEST_OUTPUT).mkdir(exist_ok=True)


def print_test_header(test_name: str):
    """Print a formatted test header."""
    print()
    print("=" * 70)
    print(f"  TEST: {test_name}")
    print("=" * 70)
    print()


def print_test_result(test_name: str, passed: bool, message: str = ""):
    """Print test result."""
    status = "✓ PASS" if passed else "✗ FAIL"
    print()
    print(f"  [{status}] {test_name}")
    if message:
        print(f"  {message}")
    print()


# ===========================================================================
# TEST 1: LESSON PLANNING
# ===========================================================================

def test_lesson_planning():
    """Test Ollama lesson planning with beat-based structure."""
    print_test_header("Lesson Planning (Ollama)")
    
    topic = "insertion sort"
    language = LanguageCode.ENGLISH
    
    try:
        print(f"  Generating lesson plan for: {topic}")
        print(f"  Language: {language.value}")
        print()
        
        start = time.perf_counter()
        spec, planning_time = generate_lesson_plan(topic, language)
        elapsed = time.perf_counter() - start
        
        # Validation checks
        errors = []
        
        if "topic" not in spec:
            errors.append("Missing 'topic' field")
        
        if "beats" not in spec:
            errors.append("Missing 'beats' field")
        elif not isinstance(spec["beats"], list):
            errors.append("'beats' is not a list")
        elif len(spec["beats"]) == 0:
            errors.append("'beats' list is empty")
        else:
            # Validate beat structure
            for i, beat in enumerate(spec["beats"]):
                if not isinstance(beat, dict):
                    errors.append(f"Beat {i} is not a dict")
                    continue
                
                required = {"id", "concept", "narration", "visual_text", "importance"}
                missing = required - beat.keys()
                if missing:
                    errors.append(f"Beat {i} missing fields: {missing}")
                
                # Check visual plan
                if "visual" in beat:
                    visual = beat["visual"]
                    if not isinstance(visual, dict):
                        errors.append(f"Beat {i}: visual is not a dict")
                    else:
                        visual_required = {"type", "action", "data"}
                        visual_missing = visual_required - visual.keys()
                        if visual_missing:
                            errors.append(f"Beat {i}: visual missing {visual_missing}")
        
        # Save spec for inspection
        spec_path = Path(TEST_OUTPUT) / "test_lesson_spec.json"
        with open(spec_path, 'w', encoding='utf-8') as f:
            json.dump(spec, f, indent=2)
        
        print(f"  Planning time: {planning_time:.2f}s")
        print(f"  Total elapsed: {elapsed:.2f}s")
        print(f"  Beats generated: {len(spec.get('beats', []))}")
        print(f"  Spec saved: {spec_path}")
        
        if errors:
            print()
            print("  Validation errors:")
            for err in errors:
                print(f"    - {err}")
            print_test_result("Lesson Planning", False, "Spec validation failed")
            return False
        
        print_test_result("Lesson Planning", True, f"Generated {len(spec['beats'])} beats successfully")
        return True
    
    except Exception as e:
        print(f"  ERROR: {e}")
        print_test_result("Lesson Planning", False, str(e))
        return False


# ===========================================================================
# TEST 2: TTS GENERATION
# ===========================================================================

def test_tts():
    """Test TTS generation for sample beats."""
    print_test_header("TTS Generation")
    
    # Create sample beats
    sample_beats = [
        {
            "id": "beat_1",
            "concept": "introduction",
            "narration": "Insertion sort is a simple sorting algorithm.",
            "visual_text": "Insertion Sort",
            "importance": "key",
            "language": "en",
            "visual": {
                "type": "array",
                "action": "show_array",
                "data": {"values": [5, 2, 8, 3, 1]}
            }
        },
        {
            "id": "beat_2",
            "concept": "step_1",
            "narration": "We start by selecting the second element as the key.",
            "visual_text": "Select Key",
            "importance": "normal",
            "language": "en",
            "visual": {
                "type": "array",
                "action": "select_key",
                "data": {"index": 1}
            }
        }
    ]
    
    lesson_spec = {
        "topic": "insertion sort test",
        "language": "en",
        "beats": sample_beats
    }
    
    try:
        audio_dir = Path(TEST_OUTPUT) / "test_audio"
        audio_dir.mkdir(exist_ok=True)
        
        print(f"  Generating audio for {len(sample_beats)} beats...")
        print(f"  Output directory: {audio_dir}")
        print()
        
        timing_service = create_timing_service(output_dir=str(audio_dir))
        
        start = time.perf_counter()
        enriched_beats, metadata = timing_service.measure_beats(lesson_spec)
        elapsed = time.perf_counter() - start
        
        print(f"  TTS generation time: {elapsed:.2f}s")
        print(f"  Total audio duration: {metadata['total_duration']:.2f}s")
        print(f"  Audio files generated: {metadata['beat_count']}")
        print()
        
        # Validation
        errors = []
        for i, beat in enumerate(enriched_beats):
            if "audio_file" not in beat:
                errors.append(f"Beat {i} missing 'audio_file'")
            elif not Path(beat["audio_file"]).exists():
                errors.append(f"Beat {i} audio file not found: {beat['audio_file']}")
            
            if "audio_duration" not in beat:
                errors.append(f"Beat {i} missing 'audio_duration'")
            elif beat["audio_duration"] <= 0:
                errors.append(f"Beat {i} has invalid duration: {beat['audio_duration']}")
            
            if "start_time" not in beat or "end_time" not in beat:
                errors.append(f"Beat {i} missing timing fields")
        
        if errors:
            print("  Validation errors:")
            for err in errors:
                print(f"    - {err}")
            print_test_result("TTS Generation", False, "Beat enrichment validation failed")
            return False
        
        print_test_result("TTS Generation", True, f"Generated {metadata['beat_count']} audio files")
        return True
    
    except Exception as e:
        print(f"  ERROR: {e}")
        print_test_result("TTS Generation", False, str(e))
        return False


# ===========================================================================
# TEST 3: TIMING SERVICE
# ===========================================================================

def test_timing():
    """Test audio timing measurement accuracy."""
    print_test_header("Timing Service")
    
    try:
        from tts.audio_utils import measure_audio_duration
        
        # Check if we have test audio files from previous test
        audio_dir = Path(TEST_OUTPUT) / "test_audio"
        if not audio_dir.exists():
            print("  No audio files found. Run test_tts first.")
            print_test_result("Timing Service", False, "Missing audio files")
            return False
        
        audio_files = list(audio_dir.glob("*.wav"))
        if not audio_files:
            print("  No WAV files found in test_audio directory.")
            print_test_result("Timing Service", False, "No audio files to measure")
            return False
        
        print(f"  Measuring {len(audio_files)} audio files...")
        print()
        
        total_duration = 0.0
        errors = []
        
        for audio_file in audio_files:
            try:
                duration = measure_audio_duration(str(audio_file))
                total_duration += duration
                print(f"    {audio_file.name}: {duration:.3f}s")
                
                if duration <= 0:
                    errors.append(f"{audio_file.name}: invalid duration {duration}")
            except Exception as e:
                errors.append(f"{audio_file.name}: {e}")
        
        print()
        print(f"  Total measured duration: {total_duration:.2f}s")
        
        if errors:
            print()
            print("  Measurement errors:")
            for err in errors:
                print(f"    - {err}")
            print_test_result("Timing Service", False, "Duration measurement failed")
            return False
        
        print_test_result("Timing Service", True, f"Measured {len(audio_files)} files successfully")
        return True
    
    except Exception as e:
        print(f"  ERROR: {e}")
        print_test_result("Timing Service", False, str(e))
        return False


# ===========================================================================
# TEST 4: VISUAL RENDERER
# ===========================================================================

def test_visual_renderer():
    """Test visual renderer scene generation."""
    print_test_header("Visual Renderer")
    
    # Create enriched beats (simulating timing service output)
    enriched_beats = [
        {
            "id": "beat_1",
            "concept": "introduction",
            "narration": "Insertion sort is a simple sorting algorithm.",
            "visual_text": "Insertion Sort",
            "importance": "key",
            "language": "en",
            "audio_file": "beat_1.wav",
            "audio_duration": 3.5,
            "start_time": 0.0,
            "end_time": 3.5,
            "visual": {
                "type": "array",
                "action": "show_array",
                "data": {"values": [5, 2, 8, 3, 1]}
            }
        },
        {
            "id": "beat_2",
            "concept": "step_1",
            "narration": "We start by selecting the second element as the key.",
            "visual_text": "Select Key",
            "importance": "normal",
            "language": "en",
            "audio_file": "beat_2.wav",
            "audio_duration": 4.2,
            "start_time": 3.5,
            "end_time": 7.7,
            "visual": {
                "type": "array",
                "action": "select_key",
                "data": {"index": 1}
            }
        }
    ]
    
    try:
        print(f"  Generating scene file for {len(enriched_beats)} beats...")
        print()
        
        visual_service = create_visual_renderer(output_dir=TEST_OUTPUT)
        
        # Validate beats first
        validation_errors = visual_service.validate_beats(enriched_beats)
        if validation_errors:
            print("  Beat validation warnings:")
            for err in validation_errors[:5]:
                print(f"    - {err}")
            if len(validation_errors) > 5:
                print(f"    ... and {len(validation_errors) - 5} more")
            print()
        
        start = time.perf_counter()
        scene_file = visual_service.generate_scene_file(
            beats=enriched_beats,
            output_filename="test_scene.py"
        )
        elapsed = time.perf_counter() - start
        
        print(f"  Scene generation time: {elapsed:.4f}s")
        print(f"  Scene file: {scene_file}")
        print()
        
        # Validate generated file
        if not Path(scene_file).exists():
            print_test_result("Visual Renderer", False, "Scene file not created")
            return False
        
        # Check file content
        with open(scene_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        errors = []
        required_imports = ["from manim import Scene", "from visual_renderer import LessonScene"]
        for imp in required_imports:
            if imp not in content:
                errors.append(f"Missing import: {imp}")
        
        if "BEATS = " not in content:
            errors.append("Missing BEATS data")
        
        if "class GeneratedLessonScene" not in content:
            errors.append("Missing GeneratedLessonScene class")
        
        if errors:
            print("  Content validation errors:")
            for err in errors:
                print(f"    - {err}")
            print_test_result("Visual Renderer", False, "Scene file validation failed")
            return False
        
        file_size = Path(scene_file).stat().st_size
        print(f"  Scene file size: {file_size} bytes")
        
        print_test_result("Visual Renderer", True, "Scene file generated successfully")
        return True
    
    except Exception as e:
        print(f"  ERROR: {e}")
        print_test_result("Visual Renderer", False, str(e))
        return False


# ===========================================================================
# TEST 5: MUXING SERVICE
# ===========================================================================

def test_muxing():
    """Test FFmpeg muxing service setup and validation."""
    print_test_header("Muxing Service")
    
    try:
        print("  Initializing muxing service...")
        print()
        
        start = time.perf_counter()
        muxing_service = create_muxing_service()
        elapsed = time.perf_counter() - start
        
        print(f"  Initialization time: {elapsed:.3f}s")
        print("  FFmpeg verification passed")
        print()
        
        # Note: We can't test actual muxing without video/audio files
        # But we can validate the service is ready
        
        print("  Muxing service ready for:")
        print("    - mux_video_audio()")
        print("    - mux_video_with_beat_audio()")
        print("    - get_video_info()")
        print("    - extract_audio_from_video()")
        
        print_test_result("Muxing Service", True, "Service initialized and FFmpeg verified")
        return True
    
    except Exception as e:
        print(f"  ERROR: {e}")
        print_test_result("Muxing Service", False, str(e))
        return False


# ===========================================================================
# TEST RUNNER
# ===========================================================================

def run_all_tests():
    """Run all tests and report summary."""
    print()
    print("=" * 70)
    print("  LOCALLEARN AI - COMPREHENSIVE TEST SUITE")
    print("=" * 70)
    
    tests = [
        ("Lesson Planning", test_lesson_planning),
        ("TTS Generation", test_tts),
        ("Timing Service", test_timing),
        ("Visual Renderer", test_visual_renderer),
        ("Muxing Service", test_muxing),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed))
        except Exception as e:
            print(f"\n  FATAL ERROR in {test_name}: {e}")
            results.append((test_name, False))
    
    # Summary
    print()
    print("=" * 70)
    print("  TEST SUMMARY")
    print("=" * 70)
    print()
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  [{status}] {test_name}")
    
    print()
    print(f"  Results: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print()
        print("  ✓ ALL TESTS PASSED")
        print()
        return True
    else:
        print()
        print("  ✗ SOME TESTS FAILED")
        print()
        return False


# ===========================================================================
# MAIN
# ===========================================================================

def main():
    if len(sys.argv) < 2:
        print()
        print("Usage:")
        print("  python test_pipeline.py all                    # Run all tests")
        print("  python test_pipeline.py test_lesson_planning   # Run specific test")
        print("  python test_pipeline.py test_tts")
        print("  python test_pipeline.py test_timing")
        print("  python test_pipeline.py test_visual_renderer")
        print("  python test_pipeline.py test_muxing")
        print()
        sys.exit(1)
    
    test_name = sys.argv[1]
    
    if test_name == "all":
        success = run_all_tests()
        sys.exit(0 if success else 1)
    elif test_name in globals():
        test_func = globals()[test_name]
        success = test_func()
        sys.exit(0 if success else 1)
    else:
        print(f"\nUnknown test: {test_name}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
