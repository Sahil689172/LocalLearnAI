"""
Audio-driven timing measurement service for LocalLearn AI.

This module orchestrates TTS generation and audio duration measurement
to create beats with accurate timing information for animation synchronization.
"""

import os
from pathlib import Path
from typing import Any

from tts.indic_parler import IndicParlerTTS
from tts.audio_utils import measure_audio_duration
from language_codes import LanguageCode


class TimingService:
    """
    Service that generates TTS audio and measures durations for lesson beats.
    
    This is the bridge between lesson planning and animation rendering:
    - Takes structured lesson spec with beats
    - Generates audio for each beat's narration
    - Measures actual audio duration
    - Returns enriched beats with timing data
    """
    
    def __init__(self, tts_service: IndicParlerTTS, output_dir: str | Path = "audio_output"):
        """
        Initialize the timing service.
        
        Parameters
        ----------
        tts_service : IndicParlerTTS
            Pre-initialized TTS service (already loaded model).
        output_dir : str | Path, optional
            Directory to store generated audio files.
        """
        self.tts_service = tts_service
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def measure_beats(self, lesson_spec: dict) -> tuple[list[dict], dict[str, Any]]:
        """
        Generate audio and measure timing for all beats in a lesson spec.
        
        This is the main entry point for audio-driven timing calculation.
        
        Parameters
        ----------
        lesson_spec : dict
            The lesson specification with beats, each containing:
            - id: unique beat identifier
            - narration: text to speak
            - language: language code
            - (other fields preserved as-is)
        
        Returns
        -------
        (enriched_beats, metadata)
            enriched_beats : list[dict]
                Beats with added fields:
                - audio_file: path to generated audio
                - audio_duration: measured duration in seconds
                - start_time: cumulative start time
                - end_time: cumulative end time
            
            metadata : dict
                Overall timing information:
                - total_duration: sum of all audio durations
                - beat_count: number of beats
                - audio_files: list of all generated audio paths
        
        Raises
        ------
        ValueError
            If lesson_spec is missing required fields or beats are malformed.
        RuntimeError
            If TTS generation or audio measurement fails.
        """
        beats = lesson_spec.get("beats", [])
        if not beats:
            raise ValueError("Lesson spec has no beats to measure")
        
        language = lesson_spec.get("language", "en")
        
        # Validate that all beats have required fields
        for i, beat in enumerate(beats):
            if not isinstance(beat, dict):
                raise ValueError(f"Beat {i} is not a dict")
            if "narration" not in beat:
                raise ValueError(f"Beat {i} ({beat.get('id', '?')}) missing 'narration'")
            if "id" not in beat:
                raise ValueError(f"Beat {i} missing 'id' field")
        
        enriched_beats = []
        audio_files = []
        cumulative_time = 0.0
        
        print(f"[TimingService] Generating audio for {len(beats)} beats...")
        
        for i, beat in enumerate(beats):
            beat_id = beat["id"]
            narration = beat["narration"]
            
            # Use beat's language if specified, otherwise use lesson's language
            beat_lang = beat.get("language", language)
            
            # Generate filename
            audio_filename = f"{beat_id}.wav"
            audio_path = self.output_dir / audio_filename
            
            print(f"  [{i+1}/{len(beats)}] Generating: {beat_id}")
            
            # Generate TTS audio
            try:
                self.tts_service.generate_speech(
                    text=narration,
                    language=beat_lang,
                    output_path=str(audio_path)
                )
            except Exception as e:
                raise RuntimeError(
                    f"Failed to generate audio for beat {beat_id}: {e}"
                ) from e
            
            # Measure duration
            try:
                duration = measure_audio_duration(str(audio_path))
            except Exception as e:
                raise RuntimeError(
                    f"Failed to measure audio duration for {audio_path}: {e}"
                ) from e
            
            # Enrich beat with timing data
            enriched_beat = beat.copy()
            enriched_beat["audio_file"] = str(audio_path)
            enriched_beat["audio_duration"] = duration
            enriched_beat["start_time"] = cumulative_time
            enriched_beat["end_time"] = cumulative_time + duration
            
            enriched_beats.append(enriched_beat)
            audio_files.append(str(audio_path))
            cumulative_time += duration
            
            print(f"    Duration: {duration:.2f}s (cumulative: {cumulative_time:.2f}s)")
        
        metadata = {
            "total_duration": cumulative_time,
            "beat_count": len(enriched_beats),
            "audio_files": audio_files,
        }
        
        print(f"[TimingService] Complete. Total duration: {cumulative_time:.2f}s")
        
        return enriched_beats, metadata
    
    def measure_single_beat(
        self,
        beat: dict,
        output_filename: str | None = None
    ) -> tuple[dict, float]:
        """
        Generate audio and measure timing for a single beat.
        
        Useful for testing or incremental generation.
        
        Parameters
        ----------
        beat : dict
            Single beat with 'id', 'narration', and optionally 'language'.
        output_filename : str | None, optional
            Custom output filename. If None, uses beat['id'] + '.wav'.
        
        Returns
        -------
        (enriched_beat, duration)
            enriched_beat : dict
                Beat with added 'audio_file' and 'audio_duration'.
            duration : float
                Audio duration in seconds.
        """
        if "narration" not in beat:
            raise ValueError(f"Beat missing 'narration': {beat}")
        if "id" not in beat:
            raise ValueError(f"Beat missing 'id': {beat}")
        
        beat_id = beat["id"]
        narration = beat["narration"]
        language = beat.get("language", "en")
        
        if output_filename is None:
            output_filename = f"{beat_id}.wav"
        
        audio_path = self.output_dir / output_filename
        
        # Generate TTS
        self.tts_service.generate_speech(
            text=narration,
            language=language,
            output_path=str(audio_path)
        )
        
        # Measure
        duration = measure_audio_duration(str(audio_path))
        
        # Enrich
        enriched_beat = beat.copy()
        enriched_beat["audio_file"] = str(audio_path)
        enriched_beat["audio_duration"] = duration
        
        return enriched_beat, duration
    
    def cleanup_audio_files(self, audio_files: list[str]) -> None:
        """
        Delete generated audio files (useful for cleanup after muxing).
        
        Parameters
        ----------
        audio_files : list[str]
            List of audio file paths to delete.
        """
        for audio_file in audio_files:
            try:
                if os.path.exists(audio_file):
                    os.remove(audio_file)
                    print(f"[TimingService] Deleted: {audio_file}")
            except Exception as e:
                print(f"[TimingService] Warning: could not delete {audio_file}: {e}")


def create_timing_service(
    output_dir: str | Path = "audio_output",
    tts_venv_path: str | Path = ".tts-venv"
) -> TimingService:
    """
    Factory function to create a TimingService with a pre-loaded TTS model.
    
    This handles the TTS service initialization so the caller doesn't need
    to worry about TTS setup details.
    
    Parameters
    ----------
    output_dir : str | Path, optional
        Directory for audio output files.
    tts_venv_path : str | Path, optional
        Path to Python virtual environment with TTS dependencies.
    
    Returns
    -------
    TimingService
        Ready-to-use timing service with loaded TTS model.
    """
    print("[TimingService] Initializing TTS service...")
    tts_service = IndicParlerTTS()
    tts_service.load_model()
    print("[TimingService] TTS model loaded successfully.")
    
    return TimingService(tts_service=tts_service, output_dir=output_dir)
