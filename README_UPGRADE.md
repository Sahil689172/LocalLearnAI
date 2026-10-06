# LocalLearn AI - Architecture Upgrade

## Overview

LocalLearn AI has been completely upgraded from a basic text animation system to a professional-quality educational video generator with:

- **TTS Integration**: Native multilingual narration (5 languages)
- **Audio-Driven Timing**: Precise synchronization between narration and visuals
- **Structured Visual Plans**: Algorithm-specific renderers with concrete visual actions
- **FFmpeg Muxing**: Professional video+audio combination
- **Quality Over Speed**: Ollama planning up to 240 seconds for high-quality content

## Architecture

### 7-Stage Pipeline

```
[1/7] Lesson Planning (Ollama)
      ↓ lesson_spec.json (beats + visual plans)
[2/7] TTS Generation
      ↓ audio files per beat
[3/7] Audio Timing Measurement
      ↓ enriched beats (duration, start_time, end_time)
[4/7] Scene File Generation
      ↓ generated_scene.py (deterministic)
[5/7] Manim Rendering
      ↓ silent_video.mp4
[6/7] Audio+Video Muxing (FFmpeg)
      ↓ final_video.mp4
[7/7] Complete ✓
```

### Data Flow

```
Topic String
    ↓
Ollama (240s timeout)
    ↓
LessonSpec {
    topic, language, algorithm,
    beats: [{
        id, concept, narration, visual_text, importance,
        visual: {type, action, data, emphasis}
    }]
}
    ↓
TTS Service (Indic-Parler)
    ↓
Enriched Beats {
    ...beat fields,
    audio_file, audio_duration, start_time, end_time
}
    ↓
Visual Renderer (deterministic)
    ↓
Manim Scene File
    ↓
Manim CE 0.21.0
    ↓
Silent Video
    ↓
FFmpeg Muxing
    ↓
Final Video (with audio)
```

## Module Structure

### 1. TTS Module (`tts/`)

- **`indic_parler.py`**: Indic-Parler TTS service
  - Loads model once, generates multiple beats
  - Correct tokenizer arrangement (speech + description)
  - Supports 5 languages with native voice descriptions

- **`language_config.py`**: Language configurations
  - English, Hindi, Tamil, Telugu, Marathi
  - Native voice descriptions per language

- **`audio_utils.py`**: Audio utilities
  - `measure_audio_duration()`: Wave module (fast) with ffprobe fallback
  - `concatenate_audio_files()`: FFmpeg concatenation

### 2. Visual Engine (`visuals/`)

- **`base.py`**: Base abstractions
  - `VisualAction`: Data structure for animation actions
  - `VisualRenderer`: Base class for algorithm renderers

- **`array_visualizer.py`**: Reusable array component
  - Methods: highlight, swap, shift, insert, set_opacity, add_label, indicate
  - Used by all algorithm renderers

- **Algorithm Renderers**:
  - `insertion_sort.py`: show_array, select_key, compare, shift, insert, mark_sorted, show_complexity
  - `binary_search.py`: show_array, check_middle, found, eliminate_half, show_complexity
  - `bubble_sort.py`: show_array, compare_adjacent, swap, mark_sorted, show_complexity
  - `selection_sort.py`: show_array, find_min, swap_with_min, mark_sorted, show_complexity

### 3. Services

- **`lesson_planner.py`**: Ollama integration
  - Timeout: 240 seconds (quality over speed)
  - Generates structured beats with visual plans
  - Algorithm-specific guidance (insertion_sort, binary_search, etc.)

- **`timing_service.py`**: Audio timing orchestration
  - `TimingService.measure_beats()`: Generate TTS + measure durations
  - Returns enriched beats with timing metadata

- **`visual_renderer.py`**: Deterministic scene generation
  - `LessonScene`: Manim scene that consumes visual plans
  - Routes actions to algorithm-specific renderers
  - `VisualRenderService.generate_scene_file()`: Creates standalone .py files

- **`muxing_service.py`**: FFmpeg integration
  - `MuxingService.mux_video_with_beat_audio()`: Concatenate + mux
  - Video codec copy (no re-encode)
  - AAC audio encoding, 192k bitrate

### 4. Main Pipeline

- **`generate.py`**: 7-stage orchestrator
  - Comprehensive error handling
  - Timing display per stage
  - Output structure: `output/<topic>_<timestamp>/`

## Usage

### Basic Usage

```bash
# English (default)
python generate.py "insertion sort"

# Hindi
python generate.py "insertion sort" --language hi

# Tamil
python generate.py "binary search" --language ta
```

### Supported Languages

| Code | Language | Native Name |
|------|----------|-------------|
| `en` | English  | English     |
| `hi` | Hindi    | हिंदी       |
| `ta` | Tamil    | தமிழ்       |
| `te` | Telugu   | తెలుగు      |
| `mr` | Marathi  | मराठी       |

### Supported Algorithms

- **Sorting**: insertion sort, selection sort, bubble sort
- **Searching**: binary search, linear search
- More coming soon

## Output Structure

```
output/
└── insertion_sort_20260106_123045/
    ├── lesson_spec.json           # Planning output
    ├── audio_output/              # TTS-generated audio
    │   ├── beat_1.wav
    │   ├── beat_2.wav
    │   └── ...
    ├── generated_scene.py         # Manim scene file
    ├── media/                     # Manim working directory
    │   └── videos/...
    ├── silent_video.mp4           # Manim output (no audio)
    └── final_video.mp4            # FINAL OUTPUT ✓
```

## Testing

### Run All Tests

```bash
python test_pipeline.py all
```

### Run Individual Tests

```bash
python test_pipeline.py test_lesson_planning
python test_pipeline.py test_tts
python test_pipeline.py test_timing
python test_pipeline.py test_visual_renderer
python test_pipeline.py test_muxing
```

## Performance

### Expected Timings (Quality Mode)

| Stage | Time | Notes |
|-------|------|-------|
| Lesson Planning | 60-240s | Ollama generates structured beats |
| TTS Generation | 20-60s | Depends on beat count |
| Audio Timing | <1s | Fast measurement |
| Scene Generation | <1s | Deterministic |
| Manim Rendering | 30-120s | Depends on complexity |
| Muxing | 5-15s | FFmpeg combination |
| **Total** | **2-7 min** | **High quality output** |

## Requirements

### Python Dependencies

```
manim==0.21.0
torch
transformers
parler-tts
indic-parler-tts
numpy
```

### External Tools

- **Ollama**: `llama3:latest` model
- **FFmpeg**: For audio/video muxing

### TTS Model

The Indic-Parler model is cached at:
```
C:\Users\hp\.cache\huggingface\hub\models--ai4bharat--indic-parler-tts
```

## Key Design Decisions

### 1. No Code Generation
❌ Old: Ollama generates arbitrary Python code
✅ New: Ollama generates structured JSON plans → deterministic renderer

### 2. Audio-Driven Timing
❌ Old: Estimated durations
✅ New: Actual measured audio durations → perfect sync

### 3. Algorithm-Specific Renderers
❌ Old: Generic text animations
✅ New: Specialized renderers per algorithm (insertion_sort, binary_search, etc.)

### 4. Quality Over Speed
❌ Old: 120s Ollama timeout
✅ New: 240s timeout for better planning

### 5. Native Language Support
❌ Old: English only or post-translation
✅ New: Native generation per language from the start

## Troubleshooting

### Ollama Timeout
If planning times out, ensure Ollama is running:
```bash
ollama serve
ollama list  # Check llama3:latest is installed
```

### TTS Errors
Verify the model is installed:
```bash
python -c "from transformers import AutoTokenizer; AutoTokenizer.from_pretrained('ai4bharat/indic-parler-tts')"
```

### FFmpeg Not Found
Install FFmpeg and add to PATH:
- Windows: Download from https://ffmpeg.org/
- Linux: `sudo apt install ffmpeg`

### Manim Errors
Ensure Manim CE 0.21.0 is installed:
```bash
pip install manim==0.21.0
```

## Migration Notes

### Old Architecture (Deprecated)
- `scene_builder.py` - Generated Python code (removed)
- `validator.py` - Validated generated code (removed)
- `manim_repair.py` - Fixed syntax errors (removed)
- 5-stage pipeline

### New Architecture
- Structured visual plans (JSON)
- Deterministic rendering
- 7-stage pipeline
- No validation/repair needed (deterministic = correct by construction)

## Future Enhancements

- [ ] More algorithm renderers (merge sort, quick sort, graph algorithms)
- [ ] Custom voice selection per language
- [ ] Video quality profiles (low/medium/high)
- [ ] Background music integration
- [ ] Subtitle generation
- [ ] Multi-resolution output
- [ ] Batch processing mode

## License

Same as LocalLearn AI main project.

## Credits

- **Manim Community**: Animation framework
- **Ollama**: Local LLM orchestration
- **Hugging Face**: Indic-Parler TTS model
- **AI4Bharat**: Multilingual TTS for Indian languages
