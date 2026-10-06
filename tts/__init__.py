"""
LocalLearn AI - TTS Service
-----------------------------
Indic-Parler TTS integration for multilingual educational narration.
"""

from .indic_parler import IndicParlerTTS, TTSConfig
from .language_config import LANGUAGE_VOICE_CONFIGS
from .audio_utils import measure_audio_duration, concatenate_audio_files

__all__ = [
    "IndicParlerTTS",
    "TTSConfig",
    "LANGUAGE_VOICE_CONFIGS",
    "measure_audio_duration",
    "concatenate_audio_files",
]
