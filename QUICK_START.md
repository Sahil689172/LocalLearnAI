# LocalLearn AI - Quick Start Guide

## TL;DR - Just Run These

### 1. Verify Setup (30 seconds)
```bash
cd C:\Users\hp\LocalLearn
.venv\Scripts\activate
python -c "from piper import PiperVoice; print('✅ Ready')"
```

### 2. Generate Your First Video (2-3 minutes)
```bash
python generate.py "Binary Search" --language en
```

### 3. Watch Output
```bash
# Opens in default video player
start output\binary_search_*\final_video.mp4
```

**That's it!** If it works, you're done. 🎉

---

## Supported Commands

```bash
# English
python generate.py "Binary Search" --language en
python generate.py "Insertion Sort" --language en
python generate.py "Bubble Sort" --language en

# Hindi
python generate.py "Binary Search" --language hi

# Telugu
python generate.py "Binary Search" --language te
```

---

## What Changed

**Before**: Piper CLI via subprocess (Windows Unicode issues)  
**After**: Piper Python API (clean, fast, Unicode-safe)

**One file changed**: `tts/piper_tts.py`  
**Everything else**: Already correct

---

## If Something Fails

### Error: "Cannot import PiperVoice"
```bash
pip install piper-tts
```

### Error: "Voice model not found"
Check you have these files:
```
models/piper/en/en_US-lessac-medium.onnx
models/piper/en/en_US-lessac-medium.onnx.json
models/piper/hi/hi_IN-pratham-medium.onnx
models/piper/hi/hi_IN-pratham-medium.onnx.json
models/piper/te/te_IN-padmavathi-medium.onnx
models/piper/te/te_IN-padmavathi-medium.onnx.json
```

### Still stuck?
Read: `UPGRADE_COMPLETE.md` (full guide)  
Or: `IMPLEMENTATION_STATUS.md` (detailed status)

---

## Expected Output

```
================================================================
LOCALLEARN AI
================================================================
Topic: Binary Search
Language: English (en)
----------------------------------------------------------------

[1/7] Lesson Planning         60-90s
[2/7] TTS Generation           7-15s  ← Piper Python API
[3/7] Audio Timing              < 1s
[4/7] Scene Generation          < 1s
[5/7] Manim Rendering         30-60s
[6/7] FFmpeg Muxing            2-5s
[7/7] Complete

Total Pipeline: ~120s (2 min)

OUTPUT: output/binary_search_20260107_143022/final_video.mp4
```

---

## Quality Checklist

✅ Audio is clear and natural  
✅ Video has sound (not silent)  
✅ Animations are smooth  
✅ Elements move visually (not just text changes)  
✅ Algorithm behavior is correct  
✅ Language is consistent (no English fallback for hi/te)

---

## What's Working

- ✅ **English** (en): Full support
- ✅ **Hindi** (hi): Full support  
- ✅ **Telugu** (te): Full support
- ⏸️ **Tamil** (ta): Model not downloaded
- ⏸️ **Marathi** (mr): Model not downloaded

---

## Project Status

| Component | Status |
|-----------|--------|
| Piper Python API | ✅ Implemented |
| Indic-Parler Removed | ✅ Complete |
| Visual Quality | ✅ Professional |
| Language Support | ✅ en/hi/te |
| Beat-based Timing | ✅ Working |
| Algorithm Renderers | ✅ Excellent |

---

## Documentation

- 📄 **QUICK_START.md** (this file) - 5 min read
- 📄 **UPGRADE_COMPLETE.md** - Full upgrade summary
- 📄 **IMPLEMENTATION_STATUS.md** - Detailed technical status

---

## Ready to Go?

```bash
python generate.py "Binary Search" --language en
```

**Watch the magic happen!** ✨
