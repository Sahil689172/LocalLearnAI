# LocalLearn AI - Piper TTS Migration

## Overview

LocalLearn has been migrated from **Indic-Parler TTS** to **Piper TTS** for improved performance and reduced complexity.

## What Changed

### TTS Implementation

**Before (Indic-Parler):**
- Heavy dependencies: torch, transformers, parler-tts, DAC
- Required separate `.tts-venv` with Python 3.12
- Model loading time: ~20+ seconds
- Generation time: ~5+ seconds per beat
- Large memory footprint
- CPU-only models

**After (Piper):**
- Lightweight: subprocess + ONNX models
- Runs in main `.venv` 
- Model validation: < 1 second
- Generation time: < 1 second per beat
- Small memory footprint
- Fast ONNX inference

### Architecture Changes

| Component | Before | After |
|-----------|--------|-------|
| TTS Engine | Indic-Parler | Piper |
| Python Environment | Separate `.tts-venv` | Main `.venv` |
| Model Format | PyTorch checkpoints | ONNX |
| Subprocess | Python → Python | Python → Piper executable |
| Worker | `.tts-venv/Scripts/python.exe` | `sys.executable` |
| Timeout | 600s | 120s |

### Files Modified

1. **tts/piper_tts.py** (NEW)
   - Piper TTS service implementation
   - Subprocess management
   - Voice configuration per language

2. **tts_worker.py**
   - Changed: `IndicParlerTTS` → `PiperTTS`
   - Simplified imports

3. **generate.py**
   - Changed: TTS_PYTHON from `.tts-venv` to `sys.executable`
   - Reduced timeout: 600s → 120s
   - Updated docstrings

4. **timing_service.py**
   - Changed: Import `PiperTTS` instead of `IndicParlerTTS`
   - Removed `tts_venv_path` parameter

5. **lesson_planner.py**
   - Reduced timeout: 240s → 120s
   - Optimized Ollama parameters
   - Streamlined prompt
   - Added `num_ctx` and `top_p` for faster generation

6. **models/piper/** (NEW)
   - Voice model storage
   - Language-specific directories
   - Setup instructions

7. **setup_piper.py** (NEW)
   - Helper script for downloading Piper models

### Files Deprecated (Not Deleted)

These files remain but are no longer used in the production pipeline:

- `tts/indic_parler.py` - Old TTS implementation
- `tts/language_config.py` - Indic-Parler voice descriptions
- `.tts-venv/` - Separate virtual environment (can be removed)

## Performance Improvements

### Planning Stage
- **Before**: ~195 seconds for 7 beats
- **Target**: ~60-90 seconds
- **Optimizations**:
  - Reduced timeout: 240s → 120s
  - Streamlined prompt (50% shorter)
  - Optimized Ollama parameters
  - Added `top_p` nucleus sampling

### TTS Stage
- **Before**: ~34 seconds for 7 beats
- **Target**: ~7-10 seconds for 7 beats
- **Improvements**:
  - No model loading overhead
  - Fast ONNX inference
  - Lightweight subprocess

### Total Pipeline
- **Before**: 571.55s (incorrect timing bug)
- **Target**: 60-120 seconds
- **Fixed**: Accurate timing calculation using `time.perf_counter()`

## Language Support

Current configuration (update `PIPER_VOICES` in `tts/piper_tts.py`):

| Language | Code | Voice | Availability |
|----------|------|-------|--------------|
| English  | en   | en_US-lessac-medium | ✓ Official |
| Hindi    | hi   | hi_IN-medium | Check Piper releases |
| Tamil    | ta   | ta_IN-medium | Check Piper releases |
| Telugu   | te   | te_IN-medium | Check Piper releases |
| Marathi  | mr   | mr_IN-medium | Check Piper releases |

**Note**: Indic language support depends on Piper model availability. Users may need to:
1. Find/download Indic models separately
2. Train custom Piper models
3. Use alternative voices

## Setup Instructions

### 1. Install Piper Executable

**Option A: Via pip**
```bash
pip install piper-tts
```

**Option B: Download binary**
```bash
# Download from: https://github.com/rhasspy/piper/releases
# Place piper.exe in models/piper/bin/
```

### 2. Download Voice Models

**Automatic (English only):**
```bash
python setup_piper.py --language en
```

**Manual:**
1. Visit: https://github.com/rhasspy/piper/releases
2. Download `.onnx` and `.onnx.json` files
3. Place in `models/piper/{language}/`

See: `models/piper/README.md` for details.

### 3. Test Installation

```bash
# Test Piper directly
echo "Hello world" | piper --model models/piper/en/en_US-lessac-medium.onnx --output_file test.wav

# Test LocalLearn pipeline
python generate.py "linear search" --language en
```

## Migration Steps

If you were using Indic-Parler, follow these steps:

### Step 1: Backup (Optional)
```bash
# Backup your .tts-venv if you want to keep it
# (Not needed for LocalLearn anymore)
```

### Step 2: Install Piper
```bash
pip install piper-tts
```

### Step 3: Download Models
```bash
python setup_piper.py --language en
```

### Step 4: Test
```bash
python generate.py "insertion sort" --language en
```

### Step 5: Cleanup (Optional)
```bash
# Remove .tts-venv if no longer needed
# rm -rf .tts-venv  # Linux/Mac
# Remove-Item -Recurse -Force .tts-venv  # Windows PowerShell
```

## Breaking Changes

### API Changes

**timing_service.py:**
```python
# Before
from tts.indic_parler import IndicParlerTTS
tts = IndicParlerTTS(TTSConfig(language="hi"))

# After
from tts.piper_tts import PiperTTS, PiperConfig
tts = PiperTTS(PiperConfig(language="hi"))
```

**generate.py:**
```python
# Before
TTS_PYTHON = os.path.join(_HERE, ".tts-venv", "Scripts", "python.exe")

# After
TTS_PYTHON = sys.executable
```

### Environment Variables

None. All configuration is file-based.

### Dependencies

**Removed:**
- torch
- transformers
- parler-tts
- DAC encoder
- FLAN-T5

**Added:**
- piper-tts (executable, not Python package)
- ONNX runtime (bundled with Piper)

## Troubleshooting

### "Piper TTS executable not found"

**Fix:**
```bash
pip install piper-tts
# Or download from releases and add to PATH
```

### "Piper voice model not found"

**Fix:**
```bash
python setup_piper.py --language en
# Or manually download to models/piper/en/
```

### "Piper voice config not found"

**Fix:**
Download both `.onnx` and `.onnx.json` files.

### TTS Worker JSON Parse Error

**Fixed** in this migration. The worker now:
- Prints ALL logs to stderr (not stdout)
- Prints ONLY JSON to stdout
- Ensures clean IPC protocol

### Incorrect Pipeline Timing

**Fixed** in this migration. Now uses:
```python
stage_start = time.perf_counter()
# ... work ...
stage_time = time.perf_counter() - stage_start
```

## Rollback

If you need to revert to Indic-Parler:

1. **Restore tts_worker.py:**
```python
from tts.indic_parler import IndicParlerTTS, TTSConfig
tts = IndicParlerTTS(TTSConfig(language=language))
```

2. **Restore generate.py:**
```python
TTS_PYTHON = os.path.join(_HERE, ".tts-venv", "Scripts", "python.exe")
TTS_TIMEOUT = 600
```

3. **Restore timing_service.py:**
```python
from tts.indic_parler import IndicParlerTTS
```

4. **Reinstall dependencies:**
```bash
cd .tts-venv
Scripts\pip install torch parler-tts soundfile transformers
```

## Future Enhancements

### Potential Improvements

1. **Streaming TTS**: Generate audio while Ollama is planning
2. **Model Caching**: Piper process pooling for even faster generation
3. **Voice Variety**: Multiple voices per language
4. **Speed Control**: Adjustable speaking rate
5. **Emotion**: Prosody control (if supported by models)

### Indic Language Support

Current status:
- Piper may not have official Indic models yet
- Community/custom models may be available
- Alternative: Keep Indic-Parler for Hindi/Tamil/Telugu/Marathi

Hybrid approach possible:
```python
if language in ["hi", "ta", "te", "mr"]:
    use_indic_parler()  # Heavy but accurate
else:
    use_piper()  # Fast for other languages
```

## References

- Piper TTS: https://github.com/rhasspy/piper
- Piper Models: https://huggingface.co/rhasspy/piper-voices
- Piper Releases: https://github.com/rhasspy/piper/releases
- ONNX Runtime: https://onnxruntime.ai/

## Support

Issues related to:
- **LocalLearn integration**: Open issue in LocalLearn repo
- **Piper itself**: Open issue in https://github.com/rhasspy/piper
- **Model availability**: Check Piper releases and community models

---

**Migration Date**: [Current Date]
**LocalLearn Version**: Post-Piper Migration
**Piper Version**: v1.2.0+ recommended
