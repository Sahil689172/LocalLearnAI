# Piper TTS Voice Models

This directory contains Piper TTS voice models for LocalLearn AI.

## Directory Structure

```
models/piper/
├── en/          # English voice models
├── hi/          # Hindi voice models
├── ta/          # Tamil voice models
├── te/          # Telugu voice models
├── mr/          # Marathi voice models
├── bin/         # Optional: Piper executable
└── README.md
```

## Required Files Per Language

For each language (e.g., `en`), you need two files:
- `{model_name}.onnx` - the voice model
- `{model_name}.onnx.json` - the model configuration

## Downloading Voice Models

### Option 1: Official Piper Releases (Recommended)

1. Visit: https://github.com/rhasspy/piper/releases/latest
2. Download voice models for your languages:
   - **English**: `en_US-lessac-medium.onnx` + `.onnx.json`
   - **Hindi**: `hi_IN-medium.onnx` + `.onnx.json` (if available)
   - **Tamil**: `ta_IN-medium.onnx` + `.onnx.json` (if available)
   - **Telugu**: `te_IN-medium.onnx` + `.onnx.json` (if available)
   - **Marathi**: `mr_IN-medium.onnx` + `.onnx.json` (if available)

3. Place files in the appropriate language directory:
   ```
   models/piper/en/en_US-lessac-medium.onnx
   models/piper/en/en_US-lessac-medium.onnx.json
   ```

### Option 2: Hugging Face Models

Visit: https://huggingface.co/rhasspy/piper-voices

Download .onnx and .json files for your desired languages.

## Piper Executable

### Windows

Download `piper.exe` from the Piper releases page and either:
- Add it to your PATH, or
- Place it in `models/piper/bin/piper.exe`

### Linux/Mac

```bash
# Install via pip
pip install piper-tts

# Or download binary from releases
# https://github.com/rhasspy/piper/releases
```

## Verifying Installation

After setup, test with:

```bash
echo "Hello world" | piper --model models/piper/en/en_US-lessac-medium.onnx --output_file test.wav
```

## Supported Languages

Current LocalLearn configuration (see `tts/piper_tts.py`):

| Language | Code | Voice Model          | Status |
|----------|------|----------------------|--------|
| English  | en   | en_US-lessac-medium  | ✓      |
| Hindi    | hi   | hi_IN-medium         | Check Piper releases |
| Tamil    | ta   | ta_IN-medium         | Check Piper releases |
| Telugu   | te   | te_IN-medium         | Check Piper releases |
| Marathi  | mr   | mr_IN-medium         | Check Piper releases |

**Note**: Not all languages may have official Piper models. Check the Piper releases for available languages.

## Adding New Languages

1. Download the .onnx and .json files for the language
2. Create a directory: `models/piper/{language_code}/`
3. Place the model files there
4. Update `PIPER_VOICES` dict in `tts/piper_tts.py`:
   ```python
   PIPER_VOICES = {
       "xx": ("model_name", "model_name.onnx.json"),
       # ...
   }
   ```
5. Add the language to `language_codes.py` if not already present

## Troubleshooting

### "Piper TTS executable not found"
- Install Piper or add it to PATH
- Or place `piper.exe` in `models/piper/bin/`

### "Piper voice model not found"
- Download the .onnx file for your language
- Place it in `models/piper/{language}/`

### "Piper voice config not found"
- Download the .onnx.json file (accompanies the .onnx file)
- Must be in the same directory as the .onnx file

### Model Download Sources

- GitHub Releases: https://github.com/rhasspy/piper/releases
- Hugging Face: https://huggingface.co/rhasspy/piper-voices
- Documentation: https://github.com/rhasspy/piper

## Performance

Piper is significantly faster than Indic-Parler:
- No large ML model loading
- Direct ONNX inference
- Lightweight subprocess execution
- Fast per-beat generation

Typical generation time: < 1 second per beat.
