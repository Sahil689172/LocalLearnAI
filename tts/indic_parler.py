"""
LocalLearn AI - Indic-Parler TTS Service
------------------------------------------
Production-ready TTS service using the pre-installed Indic-Parler model.

Model location:
    C:\\Users\\hp\\.cache\\huggingface\\hub\\models--ai4bharat--indic-parler-tts\\snapshots\\7b527af5ee8ed1f9a28d80b19703ed9bb8ba10ca

Uses the .tts-venv Python 3.12 environment (model was tested there).
Main environment is Python 3.13.
"""

import os
import sys
from dataclasses import dataclass
from pathlib import Path

# torch, soundfile, parler_tts, and transformers are deferred to load()
# so this module can be imported from environments that don't have them installed.

from .language_config import get_voice_config


# Indic-Parler model path
MODEL_PATH = r"C:\Users\hp\.cache\huggingface\hub\models--ai4bharat--indic-parler-tts\snapshots\7b527af5ee8ed1f9a28d80b19703ed9bb8ba10ca"


@dataclass
class TTSConfig:
    """Configuration for TTS generation."""
    language: str = "en"
    device: str = "cpu"
    sampling_rate: int = 24000  # Indic-Parler default


class IndicParlerTTS:
    """
    Indic-Parler TTS service for LocalLearn AI.
    
    Loads the model once and reuses it for all beats in a lesson.
    Supports: en, hi, ta, te, mr
    
    Usage:
        tts = IndicParlerTTS(language="hi")
        tts.generate_audio("नमस्ते", "output.wav")
        tts.generate_audio("यह एक परीक्षण है", "output2.wav")
    """
    
    def __init__(self, config: TTSConfig | None = None):
        if config is None:
            config = TTSConfig()
        self.config = config
        self.model = None
        self.tokenizer = None
        self.description_tokenizer = None
        self.voice_config = get_voice_config(config.language)
        self._torch = None
        self._sf = None
        
    def load(self):
        """Load the Indic-Parler model and tokenizers."""
        if self.model is not None:
            return  # Already loaded

        # Deferred heavy imports — only available in .tts-venv
        try:
            import torch
            self._torch = torch
        except ImportError as exc:
            raise ImportError(
                "torch not available. Run TTS code inside .tts-venv:\n"
                "  .tts-venv\\Scripts\\python.exe your_script.py"
            ) from exc

        try:
            import soundfile as sf
            from parler_tts import ParlerTTSForConditionalGeneration
            from transformers import AutoTokenizer
            self._sf = sf
        except ImportError as exc:
            raise ImportError(
                f"Missing ML dependency: {exc}\n"
                "Ensure you are running inside .tts-venv."
            ) from exc

        print(f"  Loading Indic-Parler TTS model...")
        print(f"    Model: {MODEL_PATH}")
        print(f"    Language: {self.voice_config['language_name']} ({self.config.language})")
        print(f"    Device: {self.config.device}")
        
        self.model = ParlerTTSForConditionalGeneration.from_pretrained(
            MODEL_PATH,
            local_files_only=True
        ).to(self.config.device)
        
        self.model.eval()
        
        # CRITICAL: Correct tokenizer arrangement
        # Speech text tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            MODEL_PATH,
            local_files_only=True
        )
        
        # Speaker/style description tokenizer
        self.description_tokenizer = AutoTokenizer.from_pretrained(
            self.model.config.text_encoder._name_or_path
        )
        
        print(f"  Model loaded successfully.")
        
    def generate_audio(self, text: str, output_path: str) -> bool:
        """
        Generate audio for a text string and save to output_path.
        
        Parameters
        ----------
        text : narration text in the selected language
        output_path : where to save the WAV file
        
        Returns
        -------
        True if successful, False otherwise
        """
        if self.model is None:
            self.load()
        
        torch = self._torch
        sf    = self._sf

        if not text.strip():
            print(f"    [WARN] Empty text, skipping: {output_path}")
            return False
        
        try:
            # Speaker/style description (consistent per language)
            description = self.voice_config["description"]
            
            # Tokenize speech text
            prompt_inputs = self.tokenizer(
                text,
                return_tensors="pt",
                padding=True
            )
            prompt_input_ids = prompt_inputs.input_ids.to(self.config.device)
            prompt_attention_mask = prompt_inputs.attention_mask.to(self.config.device)
            
            # Tokenize speaker description
            description_inputs = self.description_tokenizer(
                description,
                return_tensors="pt",
                padding=True
            )
            input_ids = description_inputs.input_ids.to(self.config.device)
            attention_mask = description_inputs.attention_mask.to(self.config.device)
            
            # Generate audio
            with torch.no_grad():
                generation = self.model.generate(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    prompt_input_ids=prompt_input_ids,
                    prompt_attention_mask=prompt_attention_mask,
                )
            
            audio = generation.cpu().numpy().squeeze()
            
            # Save WAV
            sf.write(
                output_path,
                audio,
                self.model.config.sampling_rate
            )
            
            return os.path.exists(output_path)
            
        except Exception as e:
            print(f"    [ERROR] TTS generation failed: {e}")
            return False
    
    def generate_beats(self, beats: list[dict], output_dir: str) -> dict[str, str]:
        """
        Generate audio for all beats in a lesson.
        
        Parameters
        ----------
        beats : list of beat dicts, each with "id" and "narration"
        output_dir : directory where beat WAV files will be saved
        
        Returns
        -------
        dict mapping beat_id -> wav_path for successfully generated files
        """
        os.makedirs(output_dir, exist_ok=True)
        
        results = {}
        
        for i, beat in enumerate(beats):
            beat_id = beat.get("id", f"beat_{i+1}")
            narration = beat.get("narration", "").strip()
            
            if not narration:
                print(f"    [SKIP] Beat {i+1} ({beat_id}): no narration")
                continue
            
            # Pad index for sorting
            wav_filename = f"beat_{i+1:02d}.wav"
            wav_path = os.path.join(output_dir, wav_filename)
            
            print(f"    Beat {i+1}/{len(beats)} ({beat_id}): generating...")
            
            success = self.generate_audio(narration, wav_path)
            
            if success:
                results[beat_id] = wav_path
                print(f"      → {wav_path}")
            else:
                print(f"      → FAILED")
        
        return results

    def generate_speech(self, text: str, language: str, output_path: str) -> bool:
        """Alias used by TimingService. Updates voice config if language changes."""
        if language != self.config.language:
            self.config.language = language
            self.voice_config = get_voice_config(language)
        return self.generate_audio(text, output_path)
