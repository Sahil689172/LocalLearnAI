"""
LocalLearn AI - TTS Service
-----------------------------
Indic-Parler TTS integration for multilingual educational narration.

IndicParlerTTS and TTSConfig are NOT imported here at package level because
they would trigger torch imports. Import them directly when needed:
    from tts.indic_parler import IndicParlerTTS, TTSConfig
"""

from .language_config import LANGUAGE_VOICE_CONFIGS
from .audio_utils import measure_audio_duration, concatenate_audio_files

__all__ = [
    "LANGUAGE_VOICE_CONFIGS",
    "measure_audio_duration",
    "concatenate_audio_files",
]
