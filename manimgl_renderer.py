"""
LocalLearn AI - ManimGL Renderer Service
-----------------------------------------
Handles all ManimGL rendering operations using the external ManimGL executable.

IMPORTANT: This uses ManimGL (not Manim Community Edition).
All scene files must use ManimGL syntax: from manimlib import *
"""

import os
import subprocess
import time
from pathlib import Path
from typing import Optional, Tuple
from dataclasses import dataclass

from config import MANIMGL_EXECUTABLE, MANIMGL_TIMEOUT, MANIMGL_QUALITY


@dataclass
class RenderResult:
    """Result from ManimGL rendering"""
    success: bool
    video_path: Optional[str]
    elapsed_seconds: float
    return_code: Optional[int]
    stdout: str
    stderr: str
    error_message: Optional[str]


class ManimGLRenderer:
    """
    Service for rendering ManimGL scenes.
    
    Uses the external ManimGL executable to render scene files.
    Captures detailed output for error diagnostics.
    """
    
    def __init__(self, executable_path: Optional[str] = None, quality: Optional[str] = None):
        """
        Initialize the ManimGL renderer.
        
        Parameters
        ----------
        executable_path : str, optional
            Path to manimgl.exe. Defaults to config.MANIMGL_EXECUTABLE.
        quality : str, optional
            Quality flag (-l, -m, -h). Defaults to config.MANIMGL_QUALITY.
        """
        self.executable_path = executable_path or MANIMGL_EXECUTABLE
        self.quality = quality or MANIMGL_QUALITY
        self.timeout = MANIMGL_TIMEOUT
        
        # Validate executable exists
        if not Path(self.executable_path).exists():
            raise FileNotFoundError(
                f"ManimGL executable not found: {self.executable_path}\n"
                f"Ensure ManimGL is installed at the configured location."
            )
    
    def render_scene(
        self,
        scene_file: str,
        scene_class: str,
        output_dir: str,
        output_name: str = "video",
        write_to_movie: bool = True
    ) -> RenderResult:
        """
        Render a ManimGL scene to video.
        
        Parameters
        ----------
        scene_file : str
            Absolute path to the Python scene file.
        scene_class : str
            Name of the Scene class to render.
        output_dir : str
            Directory where video should be saved.
        output_name : str, optional
            Name for output video file (without extension).
        write_to_movie : bool, optional
            Whether to write to video file (default: True).
        
        Returns
        -------
        RenderResult
            Detailed result with video path, timing, and error info.
        """
        scene_file = os.path.abspath(scene_file)
        output_dir = os.path.abspath(output_dir)
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Build ManimGL command
        # ManimGL CLI: manimgl <scene_file> <scene_class> [options]
        cmd = [
            self.executable_path,
            scene_file,
            scene_class,
        ]
        
        # Add quality flag
        if self.quality:
            cmd.append(self.quality)
        
        # Add write to movie flag
        if write_to_movie:
            cmd.append("-w")  # --write_to_movie
        
        # IMPORTANT: Don't add --skip_animations as it prevents video generation
        # Instead, ManimGL will render the full animation to video without preview window
        # The -w flag alone is sufficient for headless rendering
        
        start_time = time.time()
        
        try:
            # Set up environment with PYTHONPATH to ensure visuals module can be found
            # Get the LocalLearn project root (parent directory of the renderer)
            project_root = str(Path(__file__).parent.absolute())
            env = os.environ.copy()
            
            # Add project root to PYTHONPATH so visuals module can be imported
            existing_pythonpath = env.get('PYTHONPATH', '')
            if existing_pythonpath:
                env['PYTHONPATH'] = f"{project_root}{os.pathsep}{existing_pythonpath}"
            else:
                env['PYTHONPATH'] = project_root
            
            # Run ManimGL with the working directory set to output_dir
            # This ensures ManimGL writes output to the correct location
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=output_dir,  # Run in output directory
                env=env,  # Pass environment with PYTHONPATH set
                shell=False,
            )
            
            elapsed = time.time() - start_time
            
            # Check for success
            if result.returncode != 0:
                error_msg = self._format_error_message(
                    cmd=cmd,
                    returncode=result.returncode,
                    stdout=result.stdout,
                    stderr=result.stderr,
                    scene_file=scene_file,
                    scene_class=scene_class
                )
                
                return RenderResult(
                    success=False,
                    video_path=None,
                    elapsed_seconds=elapsed,
                    return_code=result.returncode,
                    stdout=result.stdout,
                    stderr=result.stderr,
                    error_message=error_msg
                )
            
            # Find the generated video
            video_path = self._find_video_output(output_dir, scene_class)
            
            if not video_path:
                error_msg = (
                    f"ManimGL rendering completed but video file not found.\n"
                    f"Expected location: {output_dir}\n"
                    f"Scene class: {scene_class}\n"
                    f"ManimGL stdout:\n{result.stdout}\n"
                    f"ManimGL stderr:\n{result.stderr}"
                )
                
                return RenderResult(
                    success=False,
                    video_path=None,
                    elapsed_seconds=elapsed,
                    return_code=result.returncode,
                    stdout=result.stdout,
                    stderr=result.stderr,
                    error_message=error_msg
                )
            
            # Success
            return RenderResult(
                success=True,
                video_path=video_path,
                elapsed_seconds=elapsed,
                return_code=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
                error_message=None
            )
        
        except subprocess.TimeoutExpired as e:
            elapsed = time.time() - start_time
            
            error_msg = (
                f"ManimGL rendering timed out after {self.timeout} seconds.\n"
                f"Scene file: {scene_file}\n"
                f"Scene class: {scene_class}\n"
                f"Consider increasing MANIMGL_TIMEOUT in config.py"
            )
            
            # Try to capture partial output
            stdout = e.stdout.decode('utf-8') if e.stdout else ""
            stderr = e.stderr.decode('utf-8') if e.stderr else ""
            
            return RenderResult(
                success=False,
                video_path=None,
                elapsed_seconds=elapsed,
                return_code=None,
                stdout=stdout,
                stderr=stderr,
                error_message=error_msg
            )
        
        except FileNotFoundError:
            elapsed = time.time() - start_time
            
            error_msg = (
                f"ManimGL executable not found: {self.executable_path}\n"
                f"Verify ManimGL installation at the configured path.\n"
                f"Config location: config.py -> MANIMGL_EXECUTABLE"
            )
            
            return RenderResult(
                success=False,
                video_path=None,
                elapsed_seconds=elapsed,
                return_code=None,
                stdout="",
                stderr="",
                error_message=error_msg
            )
        
        except Exception as e:
            elapsed = time.time() - start_time
            
            error_msg = (
                f"Unexpected error during ManimGL rendering: {e}\n"
                f"Scene file: {scene_file}\n"
                f"Scene class: {scene_class}\n"
                f"Executable: {self.executable_path}"
            )
            
            return RenderResult(
                success=False,
                video_path=None,
                elapsed_seconds=elapsed,
                return_code=None,
                stdout="",
                stderr=str(e),
                error_message=error_msg
            )
    
    def _find_video_output(self, output_dir: str, scene_class: str) -> Optional[str]:
        """
        Find the ManimGL-generated video file.
        
        ManimGL typically outputs to:
        - videos/<scene_class>.mp4
        - media/videos/<scene_class>/<quality>/<scene_class>.mp4
        
        This searches common output locations.
        """
        search_patterns = [
            # Direct output in working directory
            os.path.join(output_dir, f"{scene_class}.mp4"),
            # videos subdirectory
            os.path.join(output_dir, "videos", f"{scene_class}.mp4"),
            # media/videos structure (similar to Manim CE)
            os.path.join(output_dir, "media", "videos", "**", "*.mp4"),
        ]
        
        # Check direct paths first
        for pattern in search_patterns[:2]:
            if os.path.exists(pattern) and os.path.isfile(pattern):
                return pattern
        
        # Search recursively in output_dir for any MP4
        for root, dirs, files in os.walk(output_dir):
            for file in files:
                if file.endswith(".mp4"):
                    # Prefer files matching scene class name
                    if scene_class in file:
                        return os.path.join(root, file)
        
        # Return any MP4 found
        for root, dirs, files in os.walk(output_dir):
            for file in files:
                if file.endswith(".mp4"):
                    return os.path.join(root, file)
        
        return None
    
    def _format_error_message(
        self,
        cmd: list,
        returncode: int,
        stdout: str,
        stderr: str,
        scene_file: str,
        scene_class: str
    ) -> str:
        """
        Format a detailed error message for ManimGL rendering failures.
        """
        cmd_str = ' '.join(cmd)
        
        error_lines = [
            "ManimGL rendering failed",
            "",
            f"Scene file: {scene_file}",
            f"Scene class: {scene_class}",
            f"Return code: {returncode}",
            "",
            f"Command executed:",
            f"  {cmd_str}",
            "",
        ]
        
        if stderr:
            error_lines.extend([
                "ManimGL stderr:",
                "---",
                stderr.strip(),
                "---",
                "",
            ])
        
        if stdout:
            error_lines.extend([
                "ManimGL stdout:",
                "---",
                stdout.strip(),
                "---",
                "",
            ])
        
        error_lines.append(
            "Tip: Check that the scene file uses ManimGL syntax (from manimlib import *)"
        )
        
        return '\n'.join(error_lines)


def create_renderer(executable_path: Optional[str] = None, quality: Optional[str] = None) -> ManimGLRenderer:
    """
    Factory function to create a ManimGL renderer instance.
    
    Parameters
    ----------
    executable_path : str, optional
        Path to manimgl.exe. Defaults to config.MANIMGL_EXECUTABLE.
    quality : str, optional
        Quality flag (-l, -m, -h). Defaults to config.MANIMGL_QUALITY.
    
    Returns
    -------
    ManimGLRenderer
        Configured renderer instance.
    """
    return ManimGLRenderer(executable_path=executable_path, quality=quality)
