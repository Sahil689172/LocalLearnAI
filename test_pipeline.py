"""
Comprehensive test suite for LocalLearn AI upgraded architecture.

TEST CATEGORIES
---------------
FAST (offline, no models):
    test_json_parser       -- _extract_json edge cases
    test_lesson_planning   -- mocked Ollama response (fast, offline)
    test_visual_renderer   -- scene file generation
    test_muxing            -- FFmpeg availability check

LIVE (requires running Ollama / .tts-venv):
    test_lesson_planning_live  -- real Ollama call
    test_tts                   -- real Indic-Parler model (needs .tts-venv)
    test_timing                -- measures WAV files produced by test_tts

Usage:
    python test_pipeline.py all                    # fast tests only
    python test_pipeline.py test_json_parser
    python test_pipeline.py test_lesson_planning
    python test_pipeline.py test_visual_renderer
    python test_pipeline.py test_muxing
    python test_pipeline.py test_lesson_planning_live
    python test_pipeline.py test_tts              # LIVE - needs .tts-venv
    python test_pipeline.py test_timing           # depends on test_tts
"""

import sys
import os
import json
import time
from pathlib import Path

from language_codes import LanguageCode

TEST_OUTPUT = "test_output"
Path(TEST_OUTPUT).mkdir(exist_ok=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _header(name: str) -> None:
    print()
    print("=" * 70)
    print(f"  TEST: {name}")
    print("=" * 70)
    print()


def _result(name: str, passed: bool, msg: str = "") -> bool:
    status = "✓ PASS" if passed else "✗ FAIL"
    print()
    print(f"  [{status}] {name}")
    if msg:
        print(f"  {msg}")
    print()
    return passed


# ---------------------------------------------------------------------------
# TEST: JSON parser edge cases (FAST, no model)
# ---------------------------------------------------------------------------

def test_json_parser():
    """Verify _extract_json handles all realistic Ollama output shapes."""
    _header("JSON Parser (offline)")

    from lesson_planner import _extract_json

    VALID_CORE = {
        "topic": "insertion sort",
        "language": "en",
        "algorithm": "insertion_sort",
        "target_duration": 60,
        "beats": [],
    }

    cases = [
        # (label, raw_input, should_succeed)
        ("A: pure JSON",
         json.dumps(VALID_CORE),
         True),

        ("B: JSON inside ```json fence",
         "```json\n" + json.dumps(VALID_CORE) + "\n```",
         True),

        ("C: JSON inside plain ``` fence",
         "```\n" + json.dumps(VALID_CORE) + "\n```",
         True),

        ("D: explanatory text before JSON",
         "Here is the lesson plan:\n\n" + json.dumps(VALID_CORE),
         True),

        ("E: whitespace around JSON",
         "   \n\n  " + json.dumps(VALID_CORE) + "  \n\n  ",
         True),

        ("F: trailing comma in object (best-effort)",
         '{"topic": "insertion sort", "beats": [],}',
         True),

        ("G: completely malformed — must fail",
         "This is not JSON at all.",
         False),

        ("H: empty string — must fail",
         "",
         False),
    ]

    errors = []
    for label, raw, should_succeed in cases:
        try:
            result = _extract_json(raw)
            if should_succeed:
                print(f"    ✓ {label}")
            else:
                errors.append(f"{label}: expected failure but got {result}")
                print(f"    ✗ {label}: expected failure but parsed successfully")
        except ValueError as exc:
            if not should_succeed:
                print(f"    ✓ {label} (correctly rejected: {exc!s:.60})")
            else:
                errors.append(f"{label}: unexpected failure: {exc}")
                print(f"    ✗ {label}: {exc}")

    if errors:
        return _result("JSON Parser", False, f"{len(errors)} case(s) failed")
    return _result("JSON Parser", True, f"All {len(cases)} cases passed")


# ---------------------------------------------------------------------------
# TEST: Lesson planning with mocked Ollama (FAST, offline)
# ---------------------------------------------------------------------------

_MOCK_OLLAMA_RESPONSE = {
    "topic": "insertion sort",
    "language": "en",
    "algorithm": "insertion_sort",
    "target_duration": 90,
    "learning_objectives": ["understand insertion sort", "know its complexity"],
    "beats": [
        {
            "id": "beat_1",
            "concept": "introduction",
            "narration": "Insertion sort builds a sorted array one element at a time.",
            "visual_text": "Insertion Sort",
            "importance": "key",
            "visual": {
                "type": "array",
                "action": "show_array",
                "data": {"values": [5, 2, 8, 3, 1]},
            },
        },
        {
            "id": "beat_2",
            "concept": "step_1",
            "narration": "We pick the second element and compare it with those before it.",
            "visual_text": "Select Key",
            "importance": "normal",
            "visual": {
                "type": "array",
                "action": "select_key",
                "data": {"index": 1},
            },
        },
        {
            "id": "beat_3",
            "concept": "complexity",
            "narration": "Insertion sort has a time complexity of O of n squared.",
            "visual_text": "O(n²)",
            "importance": "key",
            "visual": {
                "type": "array",
                "action": "show_complexity",
                "data": {"value": "O(n²)"},
            },
        },
    ],
}


def test_lesson_planning():
    """
    Lesson planning test using a mocked Ollama response (FAST, offline).
    Validates LessonSpec structure, beat fields, and visual plans.
    """
    _header("Lesson Planning (mocked Ollama, offline)")

    from lesson_planner import _extract_json, _normalise_spec, _validate, _validate_beats
    from language_codes import LanguageCode

    # Simulate what _extract_json + _normalise_spec do on a real Ollama reply
    raw = json.dumps(_MOCK_OLLAMA_RESPONSE)

    try:
        spec = _extract_json(raw)
    except Exception as e:
        return _result("Lesson Planning", False, f"_extract_json failed: {e}")

    errors = _validate(spec)
    if errors:
        return _result("Lesson Planning", False, "Validation errors: " + "; ".join(errors))

    spec = _normalise_spec(spec, LanguageCode.EN)

    # Check required top-level fields
    top_errors = []
    for field in ("topic", "language", "target_duration", "beats"):
        if field not in spec:
            top_errors.append(f"Missing field: {field}")
    if spec.get("language") != "en":
        top_errors.append(f"language mismatch: {spec.get('language')!r}")

    beats = spec.get("beats", [])
    if not beats:
        top_errors.append("beats list is empty")

    beat_errors = _validate_beats(beats)

    # Check visual plans
    visual_errors = []
    for i, beat in enumerate(beats):
        visual = beat.get("visual")
        if not visual:
            visual_errors.append(f"Beat {i} ({beat.get('id','?')}): no visual plan")
            continue
        for key in ("type", "action", "data"):
            if key not in visual:
                visual_errors.append(f"Beat {i}: visual missing '{key}'")

    all_errors = top_errors + beat_errors + visual_errors
    if all_errors:
        for e in all_errors:
            print(f"    - {e}")
        return _result("Lesson Planning", False, f"{len(all_errors)} error(s)")

    # Save for inspection
    spec_path = Path(TEST_OUTPUT) / "test_lesson_spec.json"
    spec_path.write_text(json.dumps(spec, indent=2), encoding="utf-8")

    print(f"  Beats: {len(beats)}")
    print(f"  Algorithm: {spec.get('algorithm', 'not set')}")
    print(f"  Language: {spec['language']}")
    print(f"  Spec saved: {spec_path}")

    return _result("Lesson Planning", True, f"{len(beats)} beats validated")


# ---------------------------------------------------------------------------
# TEST: Lesson planning — LIVE Ollama call
# ---------------------------------------------------------------------------

def test_lesson_planning_live():
    """
    LIVE TEST: makes a real Ollama call. Requires Ollama running with llama3:latest.
    """
    _header("Lesson Planning LIVE (real Ollama)")
    print("  NOTE: This test calls Ollama and may take up to 240 seconds.")
    print()

    from lesson_planner import generate_lesson_plan

    try:
        start = time.perf_counter()
        spec, planning_time = generate_lesson_plan("insertion sort", LanguageCode.EN)
        elapsed = time.perf_counter() - start

        beats = spec.get("beats", [])
        print(f"  Planning time: {planning_time:.2f}s  (total: {elapsed:.2f}s)")
        print(f"  Beats: {len(beats)}")
        print(f"  Algorithm: {spec.get('algorithm', 'not set')}")

        if not beats:
            return _result("Lesson Planning LIVE", False, "No beats generated")

        spec_path = Path(TEST_OUTPUT) / "test_lesson_spec_live.json"
        spec_path.write_text(json.dumps(spec, indent=2), encoding="utf-8")
        print(f"  Spec saved: {spec_path}")

        return _result("Lesson Planning LIVE", True, f"{len(beats)} beats")

    except Exception as e:
        return _result("Lesson Planning LIVE", False, str(e))


# ---------------------------------------------------------------------------
# TEST: TTS Generation — LIVE (needs .tts-venv)
# ---------------------------------------------------------------------------

def test_tts():
    """
    LIVE TTS TEST: loads the real Indic-Parler model via .tts-venv.
    Run with: .tts-venv\\Scripts\\python.exe test_pipeline.py test_tts
    """
    _header("TTS Generation (LIVE — Indic-Parler)")
    print("  NOTE: This test loads Indic-Parler (~3.75 GB) and may take several minutes.")
    print("  Run inside .tts-venv for torch/parler_tts support.")
    print()

    sample_beats = [
        {
            "id": "beat_1",
            "concept": "introduction",
            "narration": "Insertion sort is a simple sorting algorithm.",
            "visual_text": "Insertion Sort",
            "importance": "key",
            "language": "en",
        },
        {
            "id": "beat_2",
            "concept": "step_1",
            "narration": "We start by selecting the second element as the key.",
            "visual_text": "Select Key",
            "importance": "normal",
            "language": "en",
        },
    ]
    lesson_spec = {"topic": "insertion sort test", "language": "en", "beats": sample_beats}

    audio_dir = Path(TEST_OUTPUT) / "test_audio"
    audio_dir.mkdir(exist_ok=True)

    try:
        from timing_service import create_timing_service

        print(f"  Generating audio for {len(sample_beats)} beats...")
        print(f"  Output: {audio_dir}")
        print()

        svc = create_timing_service(output_dir=str(audio_dir))

        start = time.perf_counter()
        enriched, meta = svc.measure_beats(lesson_spec)
        elapsed = time.perf_counter() - start

        print(f"  Generation time:  {elapsed:.2f}s")
        print(f"  Total duration:   {meta['total_duration']:.2f}s")
        print(f"  Files generated:  {meta['beat_count']}")

        errs = []
        for i, beat in enumerate(enriched):
            af = beat.get("audio_file", "")
            if not af or not Path(af).exists():
                errs.append(f"Beat {i}: audio file missing: {af!r}")
            dur = beat.get("audio_duration", 0)
            if dur <= 0:
                errs.append(f"Beat {i}: invalid duration {dur}")
            if "start_time" not in beat or "end_time" not in beat:
                errs.append(f"Beat {i}: missing timing fields")

        if errs:
            for e in errs:
                print(f"    - {e}")
            return _result("TTS Generation", False, "Beat validation failed")

        return _result("TTS Generation", True, f"{meta['beat_count']} files generated")

    except ImportError as e:
        return _result("TTS Generation", False,
                       f"Import error (are you in .tts-venv?): {e}")
    except Exception as e:
        return _result("TTS Generation", False, str(e))


# ---------------------------------------------------------------------------
# TEST: Timing — measures WAVs produced by test_tts
# ---------------------------------------------------------------------------

def test_timing():
    """Measures WAV durations produced by test_tts. Depends on test_tts having run first."""
    _header("Timing Service")

    from tts.audio_utils import measure_audio_duration

    audio_dir = Path(TEST_OUTPUT) / "test_audio"
    if not audio_dir.exists():
        return _result("Timing Service", False, "Run test_tts first to generate WAV files")

    wav_files = sorted(audio_dir.glob("*.wav"))
    if not wav_files:
        return _result("Timing Service", False, "No WAV files found — run test_tts first")

    print(f"  Measuring {len(wav_files)} WAV files...")
    print()

    total = 0.0
    errs = []
    for wf in wav_files:
        try:
            dur = measure_audio_duration(str(wf))
            total += dur
            print(f"    {wf.name}: {dur:.3f}s")
            if dur <= 0:
                errs.append(f"{wf.name}: duration {dur} <= 0")
        except Exception as e:
            errs.append(f"{wf.name}: {e}")

    print()
    print(f"  Total: {total:.2f}s")

    if errs:
        for e in errs:
            print(f"    - {e}")
        return _result("Timing Service", False, "Measurement errors")

    return _result("Timing Service", True, f"{len(wav_files)} files, {total:.2f}s total")


# ---------------------------------------------------------------------------
# TEST: Visual renderer (FAST, offline)
# ---------------------------------------------------------------------------

def test_visual_renderer():
    """Test deterministic scene file generation (offline, no model)."""
    _header("Visual Renderer")

    enriched_beats = [
        {
            "id": "beat_1", "concept": "introduction",
            "narration": "Insertion sort is a simple sorting algorithm.",
            "visual_text": "Insertion Sort", "importance": "key", "language": "en",
            "audio_file": "beat_1.wav", "audio_duration": 3.5,
            "start_time": 0.0, "end_time": 3.5,
            "visual": {"type": "array", "action": "show_array",
                       "data": {"values": [5, 2, 8, 3, 1]}},
        },
        {
            "id": "beat_2", "concept": "step_1",
            "narration": "We select the second element as the key.",
            "visual_text": "Select Key", "importance": "normal", "language": "en",
            "audio_file": "beat_2.wav", "audio_duration": 4.2,
            "start_time": 3.5, "end_time": 7.7,
            "visual": {"type": "array", "action": "select_key",
                       "data": {"index": 1}},
        },
    ]

    try:
        from visual_renderer import create_visual_renderer
        svc = create_visual_renderer(output_dir=TEST_OUTPUT)

        start = time.perf_counter()
        scene_file = svc.generate_scene_file(enriched_beats, output_filename="test_scene.py")
        elapsed = time.perf_counter() - start

        print(f"  Generation time: {elapsed:.4f}s")
        print(f"  Scene file: {scene_file}")

        if not Path(scene_file).exists():
            return _result("Visual Renderer", False, "Scene file not created")

        content = Path(scene_file).read_text(encoding="utf-8")
        errs = []
        for token in ("from manim import Scene", "from visual_renderer import LessonScene",
                      "BEATS = ", "class GeneratedLessonScene"):
            if token not in content:
                errs.append(f"Missing: {token!r}")

        if errs:
            for e in errs:
                print(f"    - {e}")
            return _result("Visual Renderer", False, "Scene file content invalid")

        size = Path(scene_file).stat().st_size
        print(f"  File size: {size} bytes")
        return _result("Visual Renderer", True, "Scene file generated and validated")

    except Exception as e:
        return _result("Visual Renderer", False, str(e))


# ---------------------------------------------------------------------------
# TEST: Muxing service (FAST, offline)
# ---------------------------------------------------------------------------

def test_muxing():
    """Verify FFmpeg is available and MuxingService initialises."""
    _header("Muxing Service")

    try:
        start = time.perf_counter()
        from muxing_service import create_muxing_service
        svc = create_muxing_service()
        elapsed = time.perf_counter() - start

        print(f"  Init time: {elapsed:.3f}s")
        print("  FFmpeg verified")
        return _result("Muxing Service", True, "Service initialised, FFmpeg available")

    except Exception as e:
        return _result("Muxing Service", False, str(e))


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

FAST_TESTS = [
    ("JSON Parser",      test_json_parser),
    ("Lesson Planning",  test_lesson_planning),
    ("Visual Renderer",  test_visual_renderer),
    ("Muxing Service",   test_muxing),
]


def run_all_tests():
    print()
    print("=" * 70)
    print("  LOCALLEARN AI — FAST TEST SUITE (offline, no models)")
    print("=" * 70)
    print("  For live tests: python test_pipeline.py test_lesson_planning_live")
    print("  For TTS tests:  .tts-venv\\Scripts\\python.exe test_pipeline.py test_tts")

    results = []
    for name, fn in FAST_TESTS:
        try:
            results.append((name, fn()))
        except Exception as e:
            print(f"\n  FATAL ERROR in {name}: {e}")
            results.append((name, False))

    print()
    print("=" * 70)
    print("  TEST SUMMARY")
    print("=" * 70)
    print()
    for name, ok in results:
        print(f"  [{'✓ PASS' if ok else '✗ FAIL'}] {name}")
    passed = sum(1 for _, ok in results if ok)
    print()
    print(f"  Results: {passed}/{len(results)} passed")
    print()
    return passed == len(results)


def main():
    dispatch = {
        "all":                      run_all_tests,
        "test_json_parser":         test_json_parser,
        "test_lesson_planning":     test_lesson_planning,
        "test_lesson_planning_live": test_lesson_planning_live,
        "test_tts":                 test_tts,
        "test_timing":              test_timing,
        "test_visual_renderer":     test_visual_renderer,
        "test_muxing":              test_muxing,
    }

    if len(sys.argv) < 2 or sys.argv[1] not in dispatch:
        print("\nUsage: python test_pipeline.py <test>\n")
        print("Available tests:")
        for name in dispatch:
            print(f"  {name}")
        print()
        sys.exit(1)

    success = dispatch[sys.argv[1]]()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
