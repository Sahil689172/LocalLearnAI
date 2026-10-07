"""
LocalLearn AI - Piper TTS Service
-----------------------------------
Fast, lightweight TTS using Piper Python API with local voice models.

Uses Piper's Python API directly to avoid Windows Unicode/subprocess issues.
Model is loaded ONCE per language and reused for all beats.

Model location:
    models/piper/{language}/

Usage:
    tts = PiperTTS(language="hi")
    tts.load()
    tts.generate_audio("नमस्ते", "output.wav")
    tts.generate_audio("दूसरा वाक्य", "output2.wav")  # reuses loaded model
"""

import os
import sys
import wave
from dataclasses import dataclass
from pathlib import Path

# Piper Python API
try:
    from piper import PiperVoice
    PIPER_AVAILABLE = True
except ImportError:
    PIPER_AVAILABLE = False
    PiperVoice = None


@dataclass
class PiperConfig:
    """Configuration for Piper TTS generation."""
    language: str = "en"
    model_path: str | None = None
    config_path: str | None = None
    use_cuda: bool = False


# Language to Piper voice model mapping
# Format: language_code -> (model_name, config_name)
# These match the actual downloaded models
PIPER_VOICES = {
    "en": ("en_US-lessac-medium", "en_US-lessac-medium.onnx.json"),
    "hi": ("hi_IN-pratham-medium", "hi_IN-pratham-medium.onnx.json"),
    "te": ("te_IN-padmavathi-medium", "te_IN-padmavathi-medium.onnx.json"),
}


class PiperTTS:
    """
    Piper TTS service for LocalLearn AI using Python API.
    
    Loads voice model ONCE and reuses for all beats in a lesson.
    Uses Piper's Python API directly to avoid Windows Unicode issues.
    
    Supports: en, hi, te (based on downloaded models)
    """
    
    def __init__(self, config: PiperConfig | None = None):
        if config is None:
            config = PiperConfig()
        
        self.config = config
        self.voice = None  # PiperVoice instance (loaded once)
        self.model_path = None
        self.config_path = None
        self._is_loaded = False
        
    def load(self):
        """
        Load Piper voice model into memory ONCE.
        
        The voice model stays loaded and is reused for all generate_audio calls.
        This is critical for performance — avoid reloading per beat.
        """
        if self._is_loaded and self.voice is not None:
            return  # Already loaded
        
        if not PIPER_AVAILABLE:
            raise RuntimeError(
                "Piper Python API not available.\n"
                "Install with: pip install piper-tts\n"
                "Make sure 'piper' package (not 'piper-tts' CLI) is installed."
            )
        
        # Determine model paths
        voice_name, config_name = self._get_voice_for_language(self.config.language)
        
        # Model directory structure: models/piper/{language}/
        project_root = Path(__file__).parent.parent
        models_dir = project_root / "models" / "piper" / self.config.language
        
        self.model_path = models_dir / f"{voice_name}.onnx"
        self.config_path = models_dir / config_name
        
        # Validate model files exist
        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Piper voice model not found:\n"
                f"  Language: {self.config.language}\n"
                f"  Expected: {self.model_path}\n"
                f"\n"
                f"Available models:\n"
                f"  English (en): models/piper/en/en_US-lessac-medium.onnx\n"
                f"  Hindi   (hi): models/piper/hi/hi_IN-pratham-medium.onnx\n"
                f"  Telugu  (te): models/piper/te/te_IN-padmavathi-medium.onnx\n"
            )
        
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Piper voice config not found:\n"
                f"  Language: {self.config.language}\n"
                f"  Expected: {self.config_path}\n"
                f"\n"
                f"Download both .onnx and .onnx.json files for the voice model.\n"
            )
        
        print(f"[Piper] Loading voice model for {self.config.language}...", file=sys.stderr)
        print(f"[Piper]   Model: {self.model_path.name}", file=sys.stderr)
        
        try:
            # Load voice using Piper Python API
            self.voice = PiperVoice.load(
                str(self.model_path),
                config_path=str(self.config_path),
                use_cuda=self.config.use_cuda
            )
            print(f"[Piper] Voice loaded successfully.", file=sys.stderr)
            self._is_loaded = True
            
        except Exception as e:
            raise RuntimeError(
                f"Failed to load Piper voice model:\n"
                f"  Model: {self.model_path}\n"
                f"  Error: {e}\n"
            ) from e
    
    def _get_voice_for_language(self, language: str) -> tuple[str, str]:
        """
        Get voice model name and config name for a language.
        
        Returns (model_name, config_name) or raises ValueError.
        """
        if language not in PIPER_VOICES:
            supported = ", ".join(PIPER_VOICES.keys())
            raise ValueError(
                f"Unsupported language '{language}' for Piper TTS.\n"
                f"Supported languages: {supported}\n"
                f"\n"
                f"Currently working models:\n"
                f"  en - English (en_US-lessac-medium)\n"
                f"  hi - Hindi (hi_IN-pratham-medium)\n"
                f"  te - Telugu (te_IN-padmavathi-medium)\n"
            )
        
        return PIPER_VOICES[language]
    
    def generate_audio(self, text: str, output_path: str) -> bool:
        """
        Generate audio for text and save to WAV file.
        
        Uses the already-loaded voice model (no reload per call).
        
        Parameters
        ----------
        text : str
            Narration text in the selected language.
            Can contain Unicode characters (Hindi, Telugu, etc.)
        output_path : str
            Where to save the WAV file.
        
        Returns
        -------
        bool
            True if successful, False otherwise.
        """
        if not self._is_loaded or self.voice is None:
            self.load()
        
        if not text.strip():
            print(f"[Piper] Warning: Empty text, skipping: {output_path}", file=sys.stderr)
            return False
        
        try:
            # Generate audio using Piper Python API
            # Opens WAV file and writes directly
            with wave.open(output_path, "wb") as wav_file:
                self.voice.synthesize(text, wav_file)
            
            # Verify file was created
            if not os.path.exists(output_path):
                print(f"[Piper] Error: Output file not created: {output_path}", file=sys.stderr)
                return False
            
            # Check file size (should be > 100 bytes for any real audio)
            file_size = os.path.getsize(output_path)
            if file_size < 100:
                print(f"[Piper] Error: Generated file too small ({file_size} bytes): {output_path}", file=sys.stderr)
                return False
            
            return True
            
        except Exception as e:
            print(f"[Piper] Error generating audio: {e}", file=sys.stderr)
            return False
    
    def generate_beats(self, beats: list[dict], output_dir: str, language: str = None) -> list[dict]:
        """
        Generate audio for all beats in a lesson.
        
        Loads voice ONCE and generates all beats sequentially.
        Returns enriched beats with audio metadata.
        
        Parameters
        ----------
        beats : list[dict]
            List of beat dicts, each with "id" and "narration".
        output_dir : str
            Directory where beat WAV files will be saved.
        language : str, optional
            Language override. If None, uses self.config.language.
        
        Returns
        -------
        list[dict]
            Enriched beats with audio_file, audio_duration, etc.
        """
        if language and language != self.config.language:
            # Switch language if needed
            print(f"[Piper] Switching language: {self.config.language} → {language}", file=sys.stderr)
            self.config.language = language
            self._is_loaded = False
            self.voice = None
            self.load()
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Import audio utils for duration measurement
        from .audio_utils import measure_audio_duration
        
        enriched_beats = []
        cumulative_time = 0.0
        
        print(f"[Piper] Generating {len(beats)} beats...", file=sys.stderr)
        
        for i, beat in enumerate(beats):
            beat_id = beat.get("id", f"beat_{i+1}")
            narration = beat.get("narration", "").strip()
            
            if not narration:
                print(f"[Piper]   [{i+1}/{len(beats)}] {beat_id}: SKIP (empty narration)", file=sys.stderr)
                continue
            
            # Generate filename
            wav_filename = f"beat_{i+1:03d}.wav"
            wav_path = os.path.join(output_dir, wav_filename)
            
            print(f"[Piper]   [{i+1}/{len(beats)}] {beat_id}: generating...", file=sys.stderr)
            
            # Generate audio
            success = self.generate_audio(narration, wav_path)
            
            if not success:
                print(f"[Piper]   [{i+1}/{len(beats)}] {beat_id}: FAILED", file=sys.stderr)
                continue
            
            # Measure actual duration
            try:
                duration = measure_audio_duration(wav_path)
            except Exception as e:
                print(f"[Piper]   [{i+1}/{len(beats)}] {beat_id}: Failed to measure duration: {e}", file=sys.stderr)
                duration = 0.0
            
            # Create enriched beat
            enriched_beat = beat.copy()
            enriched_beat["audio_file"] = wav_path
            enriched_beat["audio_duration"] = duration
            enriched_beat["start_time"] = cumulative_time
            enriched_beat["end_time"] = cumulative_time + duration
            
            enriched_beats.append(enriched_beat)
            cumulative_time += duration
            
            print(f"[Piper]   [{i+1}/{len(beats)}] {beat_id}: {duration:.2f}s (cumulative: {cumulative_time:.2f}s)", file=sys.stderr)
        
        print(f"[Piper] Generation complete. Total duration: {cumulative_time:.2f}s", file=sys.stderr)
        
        return enriched_beats
    
    def generate_speech(self, text: str, language: str, output_path: str) -> bool:
        """
        Alias for compatibility with TimingService.
        
        Switches language if different from current.
        """
        if language != self.config.language:
            print(f"[Piper] Switching language: {self.config.language} → {language}", file=sys.stderr)
            self.config.language = language
            self._is_loaded = False
            self.voice = None
            self.load()
        
        return self.generate_audio(text, output_path)
    
    def unload(self):
        """Release the loaded voice model."""
        if self.voice is not None:
            self.voice = None
            self._is_loaded = False
            print(f"[Piper] Voice model unloaded.", file=sys.stderr)

