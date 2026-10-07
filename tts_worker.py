"""
LocalLearn AI - TTS Worker
---------------------------
Standalone script that runs INSIDE .tts-venv (Python 3.12, has torch).
Spawned as a subprocess by generate.py which runs in .venv (no torch).

Protocol:
  stdin  <- JSON job spec
  stdout -> JSON result (single line)
  stderr -> progress messages (printed live to terminal)

Job spec:
{
    "beats": [{"id": "beat_1", "narration": "...", "language": "en"}, ...],
    "output_dir": "path/to/audio_output",
    "language": "en"
}

Success result:
{
    "ok": true,
    "enriched_beats": [
        {"id": "beat_1", "audio_file": "...", "audio_duration": 3.42,
         "start_time": 0.0, "end_time": 3.42, ...original beat fields...}
    ],
    "total_duration": 7.59,
    "beat_count": 2
}

Failure result:
{
    "ok": false,
    "error": "error message"
}
"""

import sys
import json
import os


def _fail(msg: str) -> None:
    """Print a JSON failure result to stdout and exit."""
    print(json.dumps({"ok": False, "error": msg}), flush=True)
    sys.exit(1)


def main():
    # ----------------------------------------------------------------
    # Read job from stdin
    # ----------------------------------------------------------------
    try:
        raw = sys.stdin.read()
        job = json.loads(raw)
    except Exception as e:
        _fail(f"Failed to parse job from stdin: {e}")

    beats      = job.get("beats", [])
    output_dir = job.get("output_dir", "audio_output")
    language   = job.get("language", "en")

    if not beats:
        _fail("No beats in job")

    os.makedirs(output_dir, exist_ok=True)

    # ----------------------------------------------------------------
    # Import TTS — only works inside .tts-venv
    # ----------------------------------------------------------------
    try:
        from tts.indic_parler import IndicParlerTTS, TTSConfig
        from tts.audio_utils import measure_audio_duration
    except ImportError as e:
        _fail(f"TTS import failed (run inside .tts-venv): {e}")

    # ----------------------------------------------------------------
    # Load model ONCE
    # ----------------------------------------------------------------
    print(f"[tts_worker] Loading model for language={language}...", file=sys.stderr, flush=True)
    try:
        tts = IndicParlerTTS(TTSConfig(language=language))
        tts.load()
    except Exception as e:
        _fail(f"Model load failed: {e}")

    # ----------------------------------------------------------------
    # Generate audio for each beat
    # ----------------------------------------------------------------
    enriched   = []
    cumulative = 0.0

    for i, beat in enumerate(beats):
        beat_id   = beat.get("id", f"beat_{i+1}")
        narration = beat.get("narration", "").strip()
        beat_lang = beat.get("language", language)

        if not narration:
            print(f"[tts_worker] SKIP {beat_id}: empty narration", file=sys.stderr, flush=True)
            continue

        wav_path = os.path.join(output_dir, f"{beat_id}.wav")
        print(f"[tts_worker] [{i+1}/{len(beats)}] {beat_id}", file=sys.stderr, flush=True)

        try:
            ok = tts.generate_speech(narration, beat_lang, wav_path)
            if not ok:
                raise RuntimeError("generate_speech returned False")
        except Exception as e:
            _fail(f"TTS failed for {beat_id}: {e}")

        try:
            duration = measure_audio_duration(wav_path)
        except Exception as e:
            _fail(f"Duration measurement failed for {beat_id}: {e}")

        enriched_beat = dict(beat)
        enriched_beat["audio_file"]    = wav_path
        enriched_beat["audio_duration"] = duration
        enriched_beat["start_time"]    = cumulative
        enriched_beat["end_time"]      = cumulative + duration
        enriched.append(enriched_beat)

        cumulative += duration
        print(f"[tts_worker]   -> {duration:.2f}s  (total: {cumulative:.2f}s)",
              file=sys.stderr, flush=True)

    # ----------------------------------------------------------------
    # Write result to stdout
    # ----------------------------------------------------------------
    result = {
        "ok":             True,
        "enriched_beats": enriched,
        "total_duration": cumulative,
        "beat_count":     len(enriched),
    }
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
