"""
FFmpeg audio+video muxing service for LocalLearn AI.

This module handles the final step: combining Manim's silent video output
with TTS-generated audio to produce the complete educational video.
"""

import os
import subprocess
from pathlib import Path
from typing import Optional


class MuxingService:
    """
    Service for muxing audio and video using FFmpeg.
    
    This combines silent Manim video output with TTS audio to create
    the final educational video with synchronized narration.
    """
    
    def __init__(self, ffmpeg_path: str = "ffmpeg"):
        """
        Initialize the muxing service.
        
        Parameters
        ----------
        ffmpeg_path : str, optional
            Path to ffmpeg executable. Default: "ffmpeg" (assumes in PATH).
        """
        self.ffmpeg_path = ffmpeg_path
        self._verify_ffmpeg()
    
    def _verify_ffmpeg(self) -> None:
        """
        Verify that FFmpeg is available.
        
        Raises
        ------
        RuntimeError
            If FFmpeg is not found or not executable.
        """
        try:
            result = subprocess.run(
                [self.ffmpeg_path, "-version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                raise RuntimeError(
                    f"FFmpeg returned error code {result.returncode}"
                )
            print(f"[MuxingService] FFmpeg verified: {result.stdout.splitlines()[0]}")
        except FileNotFoundError:
            raise RuntimeError(
                f"FFmpeg not found at '{self.ffmpeg_path}'. "
                "Please install FFmpeg and ensure it's in your PATH."
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError("FFmpeg verification timed out")
    
    def mux_video_audio(
        self,
        video_path: str | Path,
        audio_path: str | Path,
        output_path: str | Path,
        overwrite: bool = True
    ) -> str:
        """
        Mux a video file with an audio file.
        
        This is the main entry point for combining Manim video with TTS audio.
        
        Parameters
        ----------
        video_path : str | Path
            Path to the input video file (typically from Manim, no audio).
        audio_path : str | Path
            Path to the audio file (WAV, MP3, etc.).
        output_path : str | Path
            Path for the output video file.
        overwrite : bool, optional
            If True, overwrite existing output file. Default: True.
        
        Returns
        -------
        str
            Path to the output video file.
        
        Raises
        ------
        FileNotFoundError
            If video_path or audio_path doesn't exist.
        RuntimeError
            If FFmpeg command fails.
        """
        video_path = Path(video_path)
        audio_path = Path(audio_path)
        output_path = Path(output_path)
        
        # Validation
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        # Prepare output directory
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Build FFmpeg command
        cmd = [
            self.ffmpeg_path,
            "-i", str(video_path),  # Input video
            "-i", str(audio_path),  # Input audio
            "-c:v", "copy",         # Copy video codec (no re-encode)
            "-c:a", "aac",          # Encode audio to AAC
            "-b:a", "192k",         # Audio bitrate
            "-shortest",            # End when shortest stream ends
        ]
        
        if overwrite:
            cmd.append("-y")  # Overwrite output file
        
        cmd.append(str(output_path))
        
        print(f"[MuxingService] Muxing video and audio...")
        print(f"  Video: {video_path}")
        print(f"  Audio: {audio_path}")
        print(f"  Output: {output_path}")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode != 0:
                raise RuntimeError(
                    f"FFmpeg muxing failed with code {result.returncode}:\n"
                    f"STDERR: {result.stderr}"
                )
            
            print(f"[MuxingService] Muxing complete: {output_path}")
            return str(output_path)
        
        except subprocess.TimeoutExpired:
            raise RuntimeError("FFmpeg muxing timed out after 300 seconds")
        except Exception as e:
            raise RuntimeError(f"FFmpeg muxing failed: {e}") from e
    
    def mux_video_with_beat_audio(
        self,
        video_path: str | Path,
        audio_files: list[str],
        output_path: str | Path,
        concat_audio_path: Optional[str | Path] = None,
        overwrite: bool = True
    ) -> str:
        """
        Mux video with multiple beat audio files.
        
        This concatenates individual beat audio files and then muxes with video.
        
        Parameters
        ----------
        video_path : str | Path
            Path to the input video file.
        audio_files : list[str]
            List of audio file paths (one per beat, in order).
        output_path : str | Path
            Path for the output video file.
        concat_audio_path : str | Path | None, optional
            Path to save concatenated audio. If None, uses temp file.
        overwrite : bool, optional
            If True, overwrite existing files. Default: True.
        
        Returns
        -------
        str
            Path to the output video file.
        
        Raises
        ------
        ValueError
            If audio_files is empty.
        RuntimeError
            If concatenation or muxing fails.
        """
        if not audio_files:
            raise ValueError("No audio files provided")
        
        # Import audio concatenation utility
        from tts.audio_utils import concatenate_audio_files
        
        # Determine concatenated audio path
        if concat_audio_path is None:
            output_dir = Path(output_path).parent
            concat_audio_path = output_dir / "concatenated_audio.wav"
        
        print(f"[MuxingService] Concatenating {len(audio_files)} audio files...")
        
        # Convert all audio file paths to absolute paths to avoid working directory issues
        audio_files_abs = [str(Path(f).resolve()) for f in audio_files]
        
        # Concatenate audio files
        try:
            success = concatenate_audio_files(
                input_files=audio_files_abs,
                output_path=str(concat_audio_path)
            )
            if not success:
                raise RuntimeError(
                    f"concatenate_audio_files returned False (check logs)"
                )
            
            # Verify the file was actually created
            if not Path(concat_audio_path).exists():
                raise RuntimeError(
                    f"Concatenated audio file was not created: {concat_audio_path}"
                )
            
            file_size = Path(concat_audio_path).stat().st_size
            if file_size == 0:
                raise RuntimeError(
                    f"Concatenated audio file is empty: {concat_audio_path}"
                )
            
            print(f"[MuxingService] Audio concatenated successfully: {file_size} bytes")
            
        except Exception as e:
            raise RuntimeError(f"Audio concatenation failed: {e}") from e
        
        # Mux video with concatenated audio
        try:
            result = self.mux_video_audio(
                video_path=video_path,
                audio_path=concat_audio_path,
                output_path=output_path,
                overwrite=overwrite
            )
            
            # Clean up concatenated audio only AFTER successful mux
            if concat_audio_path and Path(concat_audio_path).name == "concatenated_audio.wav":
                try:
                    Path(concat_audio_path).unlink()
                    print(f"[MuxingService] Cleaned up temp audio: {concat_audio_path}")
                except Exception:
                    pass
            
            return result
            
        except Exception as e:
            # Don't delete concatenated audio on mux failure — user may want to inspect it
            raise RuntimeError(f"Video muxing failed: {e}") from e
    
    def add_audio_to_silent_video(
        self,
        silent_video: str | Path,
        audio: str | Path,
        output: str | Path
    ) -> str:
        """
        Convenience method: add audio to a silent video.
        
        This is an alias for mux_video_audio with clearer naming.
        
        Parameters
        ----------
        silent_video : str | Path
            Path to silent video (e.g., from Manim).
        audio : str | Path
            Path to audio file (e.g., from TTS).
        output : str | Path
            Path for output video.
        
        Returns
        -------
        str
            Path to output video.
        """
        return self.mux_video_audio(
            video_path=silent_video,
            audio_path=audio,
            output_path=output
        )
    
    def extract_audio_from_video(
        self,
        video_path: str | Path,
        audio_output_path: str | Path,
        audio_format: str = "wav"
    ) -> str:
        """
        Extract audio track from a video file.
        
        Useful for testing or audio analysis.
        
        Parameters
        ----------
        video_path : str | Path
            Path to input video.
        audio_output_path : str | Path
            Path for extracted audio.
        audio_format : str, optional
            Output audio format (wav, mp3, aac). Default: wav.
        
        Returns
        -------
        str
            Path to extracted audio file.
        
        Raises
        ------
        RuntimeError
            If extraction fails.
        """
        video_path = Path(video_path)
        audio_output_path = Path(audio_output_path)
        
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        cmd = [
            self.ffmpeg_path,
            "-i", str(video_path),
            "-vn",  # No video
            "-acodec", "pcm_s16le" if audio_format == "wav" else "copy",
            "-y",   # Overwrite
            str(audio_output_path)
        ]
        
        print(f"[MuxingService] Extracting audio from {video_path}...")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                raise RuntimeError(
                    f"Audio extraction failed: {result.stderr}"
                )
            
            print(f"[MuxingService] Audio extracted: {audio_output_path}")
            return str(audio_output_path)
        
        except subprocess.TimeoutExpired:
            raise RuntimeError("Audio extraction timed out")
        except Exception as e:
            raise RuntimeError(f"Audio extraction failed: {e}") from e
    
    def get_video_info(self, video_path: str | Path) -> dict:
        """
        Get information about a video file using ffprobe.
        
        Parameters
        ----------
        video_path : str | Path
            Path to video file.
        
        Returns
        -------
        dict
            Video information including:
            - duration: duration in seconds
            - width: video width
            - height: video height
            - fps: frames per second
            - has_audio: whether video has audio track
        
        Raises
        ------
        RuntimeError
            If ffprobe fails.
        """
        video_path = Path(video_path)
        
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        # Try using ffprobe (usually comes with ffmpeg)
        ffprobe_path = self.ffmpeg_path.replace("ffmpeg", "ffprobe")
        
        cmd = [
            ffprobe_path,
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            str(video_path)
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                raise RuntimeError(f"ffprobe failed: {result.stderr}")
            
            import json
            data = json.loads(result.stdout)
            
            # Extract relevant info
            info = {
                "duration": float(data.get("format", {}).get("duration", 0)),
                "has_audio": False,
                "width": 0,
                "height": 0,
                "fps": 0
            }
            
            for stream in data.get("streams", []):
                if stream.get("codec_type") == "video":
                    info["width"] = stream.get("width", 0)
                    info["height"] = stream.get("height", 0)
                    fps_str = stream.get("r_frame_rate", "0/1")
                    if "/" in fps_str:
                        num, den = fps_str.split("/")
                        info["fps"] = float(num) / float(den) if float(den) != 0 else 0
                elif stream.get("codec_type") == "audio":
                    info["has_audio"] = True
            
            return info
        
        except subprocess.TimeoutExpired:
            raise RuntimeError("ffprobe timed out")
        except Exception as e:
            raise RuntimeError(f"Failed to get video info: {e}") from e


def create_muxing_service(ffmpeg_path: str = "ffmpeg") -> MuxingService:
    """
    Factory function to create a MuxingService.
    
    Parameters
    ----------
    ffmpeg_path : str, optional
        Path to ffmpeg executable.
    
    Returns
    -------
    MuxingService
        Ready-to-use muxing service.
    """
    return MuxingService(ffmpeg_path=ffmpeg_path)
