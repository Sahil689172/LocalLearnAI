# LocalLearn AI - Troubleshooting Guide

## Issue: Ollama Timeout

### Symptom
```
[ERROR] Lesson planning failed: Ollama did not respond within 120 seconds.
```

### Causes & Solutions

#### 1. Ollama Not Running
**Check**:
```bash
# Visit in browser:
http://localhost:11434

# Should show: "Ollama is running"
```

**Fix**:
```bash
# Start Ollama
ollama serve

# Or restart the Ollama application
```

#### 2. Model Not Loaded
**Check**:
```bash
ollama list
```

**Should show**: `llama3:latest`

**Fix if missing**:
```bash
ollama pull llama3:latest
```

#### 3. Topic Not in Algorithm List

**Symptom**: Works for "Binary Search" but not for "Double Hashing"

**Cause**: Topic not in algorithm-specific guidance

**Status**: ✅ **FIXED** - Added support for:
- Double Hashing
- Linear Probing
- Quadratic Probing
- Hash Table
- Hash Map

**Now supported topics**:
```bash
# Sorting
python generate.py "Insertion Sort" --language en
python generate.py "Selection Sort" --language en
python generate.py "Bubble Sort" --language en
python generate.py "Merge Sort" --language en
python generate.py "Quick Sort" --language en

# Searching
python generate.py "Binary Search" --language en
python generate.py "Linear Search" --language en

# Hashing (NEW)
python generate.py "Double Hashing" --language en
python generate.py "Linear Probing" --language en
python generate.py "Quadratic Probing" --language en
python generate.py "Hash Table" --language en
python generate.py "Hash Map" --language en
```

#### 4. System Resources

**Symptom**: Ollama times out inconsistently

**Cause**: Low RAM or CPU

**Check**:
- Task Manager → RAM usage should be < 80%
- CPU usage should have capacity

**Fix**:
- Close other applications
- Increase Ollama timeout (see below)

#### 5. Increase Timeout (Last Resort)

**File**: `lesson_planner.py`

**Change**:
```python
TIMEOUT_SECS = 120   # Change to 180 or 240
```

**Note**: This indicates underlying issue (Ollama too slow)

---

## Issue: Piper TTS Errors

### "Cannot import PiperVoice"

**Fix**:
```bash
pip install piper-tts
```

### "Voice model not found"

**Check model files exist**:
```bash
dir models\piper\en\
# Should show: en_US-lessac-medium.onnx and .onnx.json
```

**Verify in code**:
File: `tts/piper_tts.py`
```python
PIPER_VOICES = {
    "en": ("en_US-lessac-medium", "en_US-lessac-medium.onnx.json"),
    "hi": ("hi_IN-pratham-medium", "hi_IN-pratham-medium.onnx.json"),
    "te": ("te_IN-padmavathi-medium", "te_IN-padmavathi-medium.onnx.json"),
}
```

Names must match actual files.

---

## Issue: Unicode Errors

### Symptom
```
UnicodeEncodeError: 'charmap' codec can't encode character...
```

**Should NOT happen** with Python API.

**If it does**:
1. Verify using Python API (not subprocess):
   ```python
   # In tts/piper_tts.py - should see:
   from piper import PiperVoice
   voice.synthesize(text, wav_file)
   
   # NOT:
   subprocess.run([piper, ...], input=text)
   ```

2. Check console encoding:
   ```bash
   # Windows
   chcp 65001  # Set UTF-8
   ```

---

## Issue: Video Quality Poor

### Animations Choppy

**Cause**: Low quality render setting

**Fix**: Edit `generate.py`
```python
QUALITY_FLAG = "-qm"  # Change from -ql to -qm (medium)
# or
QUALITY_FLAG = "-qh"  # High quality (slower)
```

### Audio/Video Out of Sync

**Check**:
1. `lesson_spec.json` - verify `audio_duration` values
2. Generated WAV files - verify they play correctly
3. `generated_scene.py` - verify uses `beat["audio_duration"]`

**Debug**:
```bash
# Check WAV duration manually
python -c "from tts.audio_utils import measure_audio_duration; print(measure_audio_duration('path/to/beat_001.wav'))"
```

---

## Issue: Wrong Language Generated

### Symptom
Requested Hindi but got English

**Check**:
1. Command line: `--language hi` (not `--language en`)
2. Console output: Should show `Language: Hindi (hi)`
3. lesson_spec.json: `"language": "hi"`

**Debug**:
```bash
# Check lesson spec
cat output\topic_*\lesson_spec.json | grep language
```

---

## Issue: Empty or Failed Output

### No beats generated

**Check Ollama response**:
```bash
# Manual test
curl http://localhost:11434/api/generate -d '{
  "model": "llama3:latest",
  "prompt": "Explain binary search in 3 steps",
  "stream": false
}'
```

### No audio files

**Check TTS worker**:
```bash
# Manual test
echo '{"beats":[{"id":"test","narration":"Hello world"}],"output_dir":"test_audio","language":"en"}' | python tts_worker.py
```

**Should output JSON with**:
```json
{"ok": true, "enriched_beats": [...], ...}
```

---

## Quick Diagnostic Commands

### Check Everything
```bash
# 1. Ollama
curl http://localhost:11434/api/tags

# 2. Piper Python API
python -c "from piper import PiperVoice; print('✅ OK')"

# 3. Models
dir models\piper\en\
dir models\piper\hi\
dir models\piper\te\

# 4. TTS Worker
echo '{"beats":[{"id":"test","narration":"Test"}],"output_dir":"test_audio","language":"en"}' | python tts_worker.py

# 5. Full pipeline (simple topic)
python generate.py "Binary Search" --language en
```

---

## Performance Issues

### Ollama Too Slow (> 90s)

**Try**:
1. Simpler topics
2. Faster model: `ollama pull llama3.2:latest` and update `generate.py`
3. More RAM for Ollama

### TTS Too Slow (> 20s for 7 beats)

**Check**:
- Voice should load ONCE per video
- Console should show:
  ```
  [Piper] Loading voice model for en...  ← ONCE
  [Piper] Voice loaded successfully.
  [Piper] Generating 7 beats...
  ```
- NOT multiple "Loading voice model" messages

**If loading multiple times**: Bug - voice not being reused

### Manim Too Slow (> 90s)

**Normal** for complex animations.

**To speed up**:
- Use `-ql` (low quality) for testing
- Reduce beat count (simpler prompts to Ollama)
- Upgrade hardware

---

## Common Mistakes

### ❌ Running without activating venv
```bash
# Wrong
python generate.py "topic" 

# Right
.venv\Scripts\activate
python generate.py "topic"
```

### ❌ Using unsupported language
```bash
# Wrong - Tamil not configured
python generate.py "topic" --language ta

# Right - Use supported language
python generate.py "topic" --language en  # or hi, te
```

### ❌ Topic with typo
```bash
# Wrong
python generate.py "bianry search"

# Right
python generate.py "binary search"
```

### ❌ Expecting instant results
**Reality**: 2-3 minutes is normal for a good quality video

---

## Getting Help

### Information to Provide

When reporting issues, include:

1. **Command used**:
   ```bash
   python generate.py "double hashing" --language en
   ```

2. **Console output** (full text, not screenshot)

3. **System info**:
   ```bash
   python --version
   ollama --version
   pip list | grep piper
   ```

4. **Files in output directory**:
   ```bash
   dir output\topic_*\
   ```

5. **lesson_spec.json content** (if generated)

---

## Success Indicators

### ✅ Everything Working If:

1. Console shows all 7 stages complete:
   ```
   [1/7] Lesson Planning    ✓
   [2/7] TTS Generation     ✓
   [3/7] Audio Timing       ✓
   [4/7] Scene Generation   ✓
   [5/7] Manim Rendering    ✓
   [6/7] FFmpeg Muxing      ✓
   [7/7] Complete           ✓
   ```

2. Final video exists and plays:
   ```bash
   start output\topic_*\final_video.mp4
   ```

3. Audio is clear and matches language requested

4. Animations are smooth and educational

5. Total time is reasonable (2-5 minutes)

---

## Still Stuck?

1. Read `IMPLEMENTATION_STATUS.md` for detailed technical info
2. Read `UPGRADE_COMPLETE.md` for setup verification
3. Check `QUICK_START.md` for basic commands

---

**Updated**: 2026-01-07  
**Note**: After adding hashing algorithms, "double hashing" should now work!
