"""
LocalLearn AI - Backend API Server
-----------------------------------
FastAPI server that wraps the existing LocalLearn AI pipeline.

Supports two video generation modes:
1. TOPIC MODE: User provides a topic → Ollama → TTS → Manim → FFmpeg
2. CUSTOM SCRIPT MODE: User provides ManimGL script → Manim → FFmpeg

Uses job-based generation with real-time phase tracking.
Frontend polls job status to display current workflow phase.

DO NOT RUN THIS FILE DIRECTLY.
Use: uvicorn backend_api:app --reload --port 8000
"""

import os
import sys
import json
import time
import uuid
import threading
import subprocess
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

# Import existing LocalLearn AI services
from lesson_planner import generate_lesson_plan
from visual_renderer import create_visual_renderer
from muxing_service import create_muxing_service
from manimgl_renderer import create_renderer
from language_codes import LanguageCode, validate_language
from config import MANIMGL_QUALITY, MANIMGL_TIMEOUT

# ---------------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------------

OUTPUT_ROOT = "output"
SCENE_CLASS = "GeneratedLessonScene"
TTS_TIMEOUT = 120

_HERE = os.path.dirname(os.path.abspath(__file__))
TTS_PYTHON = sys.executable
TTS_WORKER = os.path.join(_HERE, "tts_worker.py")

# ---------------------------------------------------------------------------
# JOB STATUS TRACKING
# ---------------------------------------------------------------------------

class JobStatus(str, Enum):
    """Job status values"""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class JobPhase(str, Enum):
    """Workflow phase identifiers"""
    # Topic mode phases
    LESSON_PLANNING = "lesson_planning"
    VOICE_GENERATION = "voice_generation"
    AUDIO_TIMING = "audio_timing"
    SCENE_GENERATION = "scene_generation"
    RENDERING = "rendering"
    MUXING = "muxing"
    
    # Custom script phases
    PREPARING_SCRIPT = "preparing_script"
    
    # Common phases
    COMPLETE = "complete"
    FAILED = "failed"

@dataclass
class Job:
    """Job state container"""
    job_id: str
    mode: str  # "topic" or "custom_script"
    topic: Optional[str]
    script: Optional[str]
    language: str
    status: JobStatus
    phase: JobPhase
    phase_label: str
    message: str
    video_url: Optional[str]
    duration: Optional[float]
    error: Optional[str]
    created_at: float
    updated_at: float
    output_dir: Optional[str]
    
    # Phase-specific metadata
    beat_count: Optional[int] = None
    audio_segments: Optional[int] = None
    audio_duration: Optional[float] = None

# Global job registry
jobs: Dict[str, Job] = {}
jobs_lock = threading.Lock()

# ---------------------------------------------------------------------------
# API MODELS
# ---------------------------------------------------------------------------

class GenerateVideoRequest(BaseModel):
    """Request to generate a video"""
    mode: str = Field(..., description="'topic' or 'custom_script'")
    topic: Optional[str] = Field(None, description="Topic for topic mode")
    script: Optional[str] = Field(None, description="ManimGL script for custom_script mode")
    narration: Optional[str] = Field(None, description="Narration text for custom_script mode (optional)")
    language: str = Field("en", description="Language code: en, hi, te")

class GenerateVideoResponse(BaseModel):
    """Response from generate endpoint"""
    success: bool
    job_id: str
    status: str
    message: str

class JobStatusResponse(BaseModel):
    """Job status response"""
    job_id: str
    status: str
    phase: str
    phase_label: str
    message: str
    video_url: Optional[str]
    duration: Optional[float]
    error: Optional[str]
    
    # Additional metadata
    beat_count: Optional[int] = None
    audio_segments: Optional[int] = None
    audio_duration: Optional[float] = None

# ---------------------------------------------------------------------------
# FASTAPI APP
# ---------------------------------------------------------------------------

app = FastAPI(
    title="LocalLearn AI API",
    description="Backend API for LocalLearn AI educational video generator",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # Frontend ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------------------------

def _safe_name(topic: str) -> str:
    """Convert topic to safe directory name"""
    import re
    name = topic.lower().strip()
    name = re.sub(r"[^\w\s-]", "", name)
    name = re.sub(r"[\s_-]+", "_", name)
    name = name.strip("_")
    return name[:60]

def _make_run_dir(topic: str) -> str:
    """Create unique output directory"""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dirname = f"{_safe_name(topic)}_{ts}"
    path = os.path.join(OUTPUT_ROOT, dirname)
    os.makedirs(path, exist_ok=True)
    return path

def _update_job(job_id: str, **updates):
    """Thread-safe job update"""
    with jobs_lock:
        if job_id in jobs:
            job = jobs[job_id]
            for key, value in updates.items():
                setattr(job, key, value)
            job.updated_at = time.time()

def _run_tts_subprocess(lesson_spec: dict, audio_dir: str) -> tuple:
    """Run TTS generation (from generate.py)"""
    if not os.path.exists(TTS_WORKER):
        raise RuntimeError(f"tts_worker.py not found: {TTS_WORKER}")

    beats = lesson_spec.get("beats", [])
    job = {
        "beats": beats,
        "output_dir": audio_dir,
        "language": lesson_spec.get("language", "en"),
    }

    proc = subprocess.run(
        [TTS_PYTHON, TTS_WORKER],
        input=json.dumps(job),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=TTS_TIMEOUT,
    )

    if proc.returncode != 0:
        raise RuntimeError(f"TTS worker failed: {proc.stderr}")

    stdout = (proc.stdout or "").strip()
    if not stdout:
        raise RuntimeError("TTS worker produced no output")

    response = json.loads(stdout)
    if not response.get("ok"):
        raise RuntimeError(f"TTS worker failed: {response.get('error', 'unknown')}")

    enriched_beats = response["enriched_beats"]
    metadata = {
        "total_duration": response["total_duration"],
        "beat_count": response["beat_count"],
        "audio_files": [b["audio_file"] for b in enriched_beats],
    }
    return enriched_beats, metadata

def _render_manim(scene_file: str, scene_class: str, quality_flag: str, output_dir: str) -> tuple:
    """
    Render ManimGL video.
    
    Uses the configured ManimGL executable from config.py.
    Returns detailed error information for diagnostics.
    """
    # Create ManimGL renderer
    renderer = create_renderer(quality=quality_flag)
    
    # Render scene
    result = renderer.render_scene(
        scene_file=scene_file,
        scene_class=scene_class,
        output_dir=output_dir,
        output_name="silent_video",
        write_to_movie=True
    )
    
    if not result.success:
        # Return detailed error information
        error_details = {
            "return_code": result.return_code,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "error_message": result.error_message
        }
        return False, None, result.elapsed_seconds, error_details
    
    return True, result.video_path, result.elapsed_seconds, None

# ---------------------------------------------------------------------------
# TOPIC MODE PIPELINE
# ---------------------------------------------------------------------------

def _run_topic_pipeline(job_id: str, topic: str, language: str):
    """
    Execute the full topic mode pipeline.
    
    This reuses the EXISTING LocalLearn AI pipeline from generate.py.
    Phases: lesson_planning → voice_generation → audio_timing → 
            scene_generation → rendering → muxing → complete
    """
    try:
        # Validate language
        try:
            lang_code = validate_language(language)
        except ValueError as e:
            _update_job(job_id, status=JobStatus.FAILED, phase=JobPhase.FAILED, error=str(e))
            return

        # Create output directory
        run_dir = _make_run_dir(topic)
        audio_dir = os.path.join(run_dir, "audio_output")
        os.makedirs(audio_dir, exist_ok=True)
        
        spec_path = os.path.join(run_dir, "lesson_spec.json")
        scene_path = os.path.join(run_dir, "generated_scene.py")
        final_video_path = os.path.join(run_dir, "final_video.mp4")
        
        _update_job(job_id, output_dir=run_dir)

        # PHASE 1: LESSON PLANNING
        _update_job(
            job_id,
            status=JobStatus.RUNNING,
            phase=JobPhase.LESSON_PLANNING,
            phase_label="Lesson Planning (Ollama)",
            message="Ollama is creating the lesson and visual plan..."
        )
        
        lesson_spec, planning_time = generate_lesson_plan(topic, language=lang_code)
        
        # Save lesson spec
        with open(spec_path, "w", encoding="utf-8") as f:
            json.dump(lesson_spec, f, indent=2)
        
        beats = lesson_spec.get("beats", [])
        _update_job(job_id, beat_count=len(beats))

        # PHASE 2: VOICE GENERATION
        _update_job(
            job_id,
            phase=JobPhase.VOICE_GENERATION,
            phase_label="Voice Generation (Piper TTS)",
            message=f"Generating narration for {len(beats)} beats..."
        )
        
        enriched_beats, audio_metadata = _run_tts_subprocess(lesson_spec, audio_dir)
        
        _update_job(
            job_id,
            audio_segments=audio_metadata['beat_count'],
            audio_duration=audio_metadata['total_duration']
        )

        # PHASE 3: AUDIO TIMING
        _update_job(
            job_id,
            phase=JobPhase.AUDIO_TIMING,
            phase_label="Audio Timing",
            message="Measuring narration timing..."
        )
        
        lesson_spec['beats'] = enriched_beats
        lesson_spec['measured_duration'] = audio_metadata['total_duration']
        
        with open(spec_path, "w", encoding="utf-8") as f:
            json.dump(lesson_spec, f, indent=2)

        # PHASE 4: SCENE GENERATION
        _update_job(
            job_id,
            phase=JobPhase.SCENE_GENERATION,
            phase_label="Scene Generation",
            message="Preparing ManimGL animation..."
        )
        
        visual_service = create_visual_renderer(output_dir=run_dir)
        scene_file = visual_service.generate_scene_file(
            beats=enriched_beats,
            output_filename="generated_scene.py"
        )

        # PHASE 5: MANIM RENDERING
        _update_job(
            job_id,
            phase=JobPhase.RENDERING,
            phase_label="Manim Rendering",
            message="Rendering educational animation..."
        )
        
        success, silent_video_path, manim_time, error_details = _render_manim(
            scene_file=scene_path,
            scene_class=SCENE_CLASS,
            quality_flag=MANIMGL_QUALITY,
            output_dir=run_dir
        )
        
        if not success:
            # Format detailed error message
            error_msg = "ManimGL rendering failed"
            if error_details:
                if error_details.get("error_message"):
                    error_msg = error_details["error_message"]
                elif error_details.get("stderr"):
                    error_msg = f"ManimGL rendering failed: {error_details['stderr'][:500]}"
            raise RuntimeError(error_msg)

        # PHASE 6: MUXING
        _update_job(
            job_id,
            phase=JobPhase.MUXING,
            phase_label="Audio + Video Muxing",
            message="Combining narration and animation..."
        )
        
        muxing_service = create_muxing_service()
        audio_files = [beat['audio_file'] for beat in enriched_beats]
        
        final_video = muxing_service.mux_video_with_beat_audio(
            video_path=silent_video_path,
            audio_files=audio_files,
            output_path=final_video_path,
            overwrite=True
        )
        
        # Get video duration
        try:
            video_info = muxing_service.get_video_info(final_video)
            video_duration = video_info.get('duration')
        except:
            video_duration = None

        # PHASE 7: COMPLETE
        video_url = f"/api/video/download/{job_id}"
        
        _update_job(
            job_id,
            status=JobStatus.COMPLETED,
            phase=JobPhase.COMPLETE,
            phase_label="Complete",
            message="Your educational video is ready",
            video_url=video_url,
            duration=video_duration
        )

    except Exception as e:
        _update_job(
            job_id,
            status=JobStatus.FAILED,
            phase=JobPhase.FAILED,
            phase_label="Failed",
            message="Video generation failed",
            error=str(e)
        )

# ---------------------------------------------------------------------------
# CUSTOM SCRIPT PIPELINE
# ---------------------------------------------------------------------------

def _run_custom_script_pipeline(job_id: str, script: str, narration: Optional[str], language: str):
    """
    Execute the custom script pipeline.
    
    Flow (with narration): preparing_script → rendering → voice_generation → audio_timing → muxing → complete
    Flow (no narration): preparing_script → rendering → complete
    
    If narration is provided, uses existing Piper TTS and FFmpeg services.
    The user's script is rendered as-is.
    """
    try:
        # Validate language
        try:
            lang_code = validate_language(language)
        except ValueError as e:
            _update_job(job_id, status=JobStatus.FAILED, phase=JobPhase.FAILED, error=str(e))
            return

        # Create output directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_dir = os.path.join(OUTPUT_ROOT, f"custom_script_{timestamp}")
        os.makedirs(run_dir, exist_ok=True)
        
        scene_path = os.path.join(run_dir, "custom_scene.py")
        final_video_path = os.path.join(run_dir, "final_video.mp4")
        audio_dir = os.path.join(run_dir, "audio_output")
        
        _update_job(job_id, output_dir=run_dir)

        # PHASE 1: PREPARING SCRIPT
        _update_job(
            job_id,
            status=JobStatus.RUNNING,
            phase=JobPhase.PREPARING_SCRIPT,
            phase_label="Preparing Script",
            message="Preparing your ManimGL script..."
        )
        
        # Basic validation
        if "from manimlib import" not in script and "from manim import" not in script:
            raise ValueError("Script must import from manimlib or manim")
        
        if "class" not in script or "Scene" not in script:
            raise ValueError("Script must contain a Scene class")
        
        # Extract scene class name (simple heuristic)
        import re
        scene_match = re.search(r'class\s+(\w+)\s*\([^)]*Scene[^)]*\)', script)
        if not scene_match:
            raise ValueError("Could not find a Scene class in the script")
        
        scene_class_name = scene_match.group(1)
        
        # Save script
        with open(scene_path, "w", encoding="utf-8") as f:
            f.write(script)

        # PHASE 2: RENDERING
        _update_job(
            job_id,
            phase=JobPhase.RENDERING,
            phase_label="ManimGL Rendering",
            message="Rendering your animation..."
        )
        
        success, video_path, manim_time, error_details = _render_manim(
            scene_file=scene_path,
            scene_class=scene_class_name,
            quality_flag=MANIMGL_QUALITY,
            output_dir=run_dir
        )
        
        if not success:
            # Format detailed error message
            error_msg = "ManimGL rendering failed"
            if error_details:
                if error_details.get("error_message"):
                    error_msg = error_details["error_message"]
                elif error_details.get("stderr"):
                    error_msg = f"ManimGL rendering failed: {error_details['stderr'][:500]}"
            raise RuntimeError(error_msg)
        
        # Get video duration
        muxing_service = create_muxing_service()
        video_info = muxing_service.get_video_info(video_path)
        video_duration = video_info.get('duration', 0)
        
        # Check if narration is provided
        has_narration = narration and narration.strip()
        
        if has_narration:
            # PHASE 3: VOICE GENERATION
            os.makedirs(audio_dir, exist_ok=True)
            
            _update_job(
                job_id,
                phase=JobPhase.VOICE_GENERATION,
                phase_label="Voice Generation (Piper TTS)",
                message="Generating narration audio..."
            )
            
            # Create a single "beat" for the narration
            # This reuses the existing TTS infrastructure
            lesson_spec = {
                "beats": [{
                    "id": "narration_1",
                    "narration": narration.strip(),
                    "language": language,
                }],
                "language": language,
            }
            
            try:
                enriched_beats, audio_metadata = _run_tts_subprocess(lesson_spec, audio_dir)
            except Exception as e:
                raise RuntimeError(f"TTS generation failed: {e}")
            
            audio_duration = audio_metadata['total_duration']
            audio_file = enriched_beats[0]['audio_file']
            
            _update_job(
                job_id,
                audio_segments=1,
                audio_duration=audio_duration
            )
            
            # PHASE 4: AUDIO TIMING
            _update_job(
                job_id,
                phase=JobPhase.AUDIO_TIMING,
                phase_label="Audio Timing",
                message=f"Audio: {audio_duration:.1f}s, Video: {video_duration:.1f}s"
            )
            
            # PHASE 5: MUXING
            _update_job(
                job_id,
                phase=JobPhase.MUXING,
                phase_label="Audio + Video Muxing",
                message="Combining animation and narration..."
            )
            
            # Mux video with narration audio
            try:
                final_video = muxing_service.mux_video_with_beat_audio(
                    video_path=video_path,
                    audio_files=[audio_file],
                    output_path=final_video_path,
                    overwrite=True
                )
            except Exception as e:
                raise RuntimeError(f"Audio+Video muxing failed: {e}")
            
            # Get final video info
            try:
                final_video_info = muxing_service.get_video_info(final_video)
                final_duration = final_video_info.get('duration')
            except:
                final_duration = max(video_duration, audio_duration)
        
        else:
            # No narration - use video directly
            import shutil
            shutil.copy2(video_path, final_video_path)
            final_duration = video_duration

        # PHASE 6: COMPLETE
        video_url = f"/api/video/download/{job_id}"
        
        _update_job(
            job_id,
            status=JobStatus.COMPLETED,
            phase=JobPhase.COMPLETE,
            phase_label="Complete",
            message="Your video is ready",
            video_url=video_url,
            duration=final_duration
        )

    except Exception as e:
        _update_job(
            job_id,
            status=JobStatus.FAILED,
            phase=JobPhase.FAILED,
            phase_label="Failed",
            message="Video generation failed",
            error=str(e)
        )

# ---------------------------------------------------------------------------
# API ENDPOINTS
# ---------------------------------------------------------------------------

@app.get("/")
def root():
    """Root endpoint"""
    return {
        "service": "LocalLearn AI API",
        "version": "1.0.0",
        "status": "running"
    }

@app.post("/api/video/generate", response_model=GenerateVideoResponse)
def generate_video(request: GenerateVideoRequest):
    """
    Generate a video (topic or custom script mode).
    
    Returns a job_id for tracking generation status.
    """
    # Validate request
    if request.mode not in ["topic", "custom_script"]:
        raise HTTPException(status_code=400, detail="mode must be 'topic' or 'custom_script'")
    
    if request.mode == "topic" and not request.topic:
        raise HTTPException(status_code=400, detail="topic is required for topic mode")
    
    if request.mode == "custom_script" and not request.script:
        raise HTTPException(status_code=400, detail="script is required for custom_script mode")
    
    # Create job
    job_id = str(uuid.uuid4())
    
    job = Job(
        job_id=job_id,
        mode=request.mode,
        topic=request.topic,
        script=request.script,
        language=request.language,
        status=JobStatus.QUEUED,
        phase=JobPhase.LESSON_PLANNING if request.mode == "topic" else JobPhase.PREPARING_SCRIPT,
        phase_label="Queued",
        message="Video generation queued...",
        video_url=None,
        duration=None,
        error=None,
        created_at=time.time(),
        updated_at=time.time(),
        output_dir=None
    )
    
    with jobs_lock:
        jobs[job_id] = job
    
    # Start generation in background thread
    if request.mode == "topic":
        thread = threading.Thread(
            target=_run_topic_pipeline,
            args=(job_id, request.topic, request.language),
            daemon=True
        )
    else:
        thread = threading.Thread(
            target=_run_custom_script_pipeline,
            args=(job_id, request.script, request.narration, request.language),
            daemon=True
        )
    
    thread.start()
    
    return GenerateVideoResponse(
        success=True,
        job_id=job_id,
        status=job.status,
        message="Video generation started"
    )

@app.get("/api/video/status/{job_id}", response_model=JobStatusResponse)
def get_job_status(job_id: str):
    """
    Get the current status of a video generation job.
    
    Frontend polls this endpoint to display workflow phase.
    """
    with jobs_lock:
        if job_id not in jobs:
            raise HTTPException(status_code=404, detail="Job not found")
        
        job = jobs[job_id]
        
        return JobStatusResponse(
            job_id=job.job_id,
            status=job.status,
            phase=job.phase,
            phase_label=job.phase_label,
            message=job.message,
            video_url=job.video_url,
            duration=job.duration,
            error=job.error,
            beat_count=job.beat_count,
            audio_segments=job.audio_segments,
            audio_duration=job.audio_duration
        )

@app.get("/api/video/download/{job_id}")
def download_video(job_id: str):
    """
    Download the generated video file.
    
    Only available when job status is completed.
    """
    with jobs_lock:
        if job_id not in jobs:
            raise HTTPException(status_code=404, detail="Job not found")
        
        job = jobs[job_id]
        
        if job.status != JobStatus.COMPLETED:
            raise HTTPException(status_code=400, detail="Video not ready")
        
        if not job.output_dir:
            raise HTTPException(status_code=500, detail="Output directory not found")
        
        video_path = os.path.join(job.output_dir, "final_video.mp4")
        
        if not os.path.exists(video_path):
            raise HTTPException(status_code=500, detail="Video file not found")
        
        return FileResponse(
            path=video_path,
            media_type="video/mp4",
            filename=f"locallearn_{job.mode}_{job_id[:8]}.mp4"
        )

@app.get("/api/jobs")
def list_jobs():
    """List all jobs (for debugging)"""
    with jobs_lock:
        return {
            "count": len(jobs),
            "jobs": [asdict(job) for job in jobs.values()]
        }

# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("ERROR: Do not run this file directly.")
    print("")
    print("RECOMMENDED (Stable - Jobs persist):")
    print("  uvicorn backend_api:app --port 8000")
    print("")
    print("DEVELOPMENT ONLY (Jobs lost on code changes):")
    print("  uvicorn backend_api:app --reload --port 8000")
    print("")
    print("Or use the startup scripts:")
    print("  start_backend.bat       (Windows CMD - Stable)")
    print("  start_backend_dev.bat   (Windows CMD - Auto-reload)")
    print("  start_backend.ps1       (PowerShell - Stable)")
    print("  start_backend_dev.ps1   (PowerShell - Auto-reload)")
    sys.exit(1)
