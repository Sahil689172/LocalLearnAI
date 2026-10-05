"""
LocalLearn AI - Manim Renderer with Automatic Runtime Repair
-------------------------------------------------------------
Runs Manim, captures errors, and asks Ollama to repair runtime
failures automatically (up to 2 attempts).

Usage:
    python render.py                                           # defaults
    python render.py generated_scene.py LocalLearnScene       # explicit
    python render.py generated_scene.py LocalLearnScene --low
    python render.py generated_scene.py LocalLearnScene --medium
    python render.py generated_scene.py LocalLearnScene --high

Quality flags (default: --low):
    --low     -ql   480p15   fast preview
    --medium  -qm   720p30
    --high    -qh   1080p60
"""

import sys
import os
import time
import shutil
import subprocess

from manim_repair import extract_manim_error, repair_manim_code

# ---------------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------------

DEFAULT_SCENE_FILE  = "generated_scene.py"
DEFAULT_SCENE_CLASS = "LocalLearnScene"
DEFAULT_QUALITY     = "--low"
MAX_REPAIR_ATTEMPTS = 2

QUALITY_FLAGS = {
    "--low":    "-ql",
    "--medium": "-qm",
    "--high":   "-qh",
}

QUALITY_LABELS = {
    "--low":    "Low  (480p15)  — fast preview",
    "--medium": "Medium (720p30)",
    "--high":   "High (1080p60) — production quality",
}

# ---------------------------------------------------------------------------
# ARGUMENT PARSING
# ---------------------------------------------------------------------------

def parse_args():
    args = sys.argv[1:]

    quality_arg = DEFAULT_QUALITY
    for flag in QUALITY_FLAGS:
        if flag in args:
            quality_arg = flag
            args = [a for a in args if a != flag]
            break

    scene_file  = args[0] if len(args) > 0 else DEFAULT_SCENE_FILE
    scene_class = args[1] if len(args) > 1 else DEFAULT_SCENE_CLASS

    return scene_file, scene_class, quality_arg

# ---------------------------------------------------------------------------
# MANIM RUNNER
# ---------------------------------------------------------------------------

def run_manim(scene_file: str, scene_class: str, quality_flag: str) -> tuple:
    """
    Run Manim on scene_file.

    Strategy:
    - Stream output live to the terminal (so the user sees progress).
    - Also capture it via tee into a buffer so we can parse errors.

    Returns:
        (return_code, combined_output_str, elapsed_seconds)
    """
    cmd = [
        sys.executable, "-m", "manim",
        quality_flag,
        scene_file,
        scene_class,
    ]

    start = time.perf_counter()
    output_lines = []

    try:
        # Use Popen so we can stream AND capture simultaneously
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,   # merge stderr into stdout
            text=True,
            bufsize=1,                  # line-buffered
        )

        for line in process.stdout:
            print(line, end="", flush=True)
            output_lines.append(line)

        process.wait()
        returncode = process.returncode

    except FileNotFoundError:
        elapsed = time.perf_counter() - start
        return -1, "", elapsed
    except KeyboardInterrupt:
        elapsed = time.perf_counter() - start
        print()
        print("  [INTERRUPTED] Rendering cancelled by user.")
        sys.exit(1)

    elapsed = time.perf_counter() - start
    combined = "".join(output_lines)
    return returncode, combined, elapsed

# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def read_scene_code(scene_file: str) -> str:
    with open(scene_file, "r", encoding="utf-8") as fh:
        return fh.read()


def write_scene_code(path: str, code: str) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(code)


def print_error_summary(error_info: dict) -> None:
    print()
    print("  " + "-" * 43)
    print("  MANIM RUNTIME ERROR")
    print("  " + "-" * 43)
    print(f"  Error type : {error_info['error_type']}")
    if error_info["error_line"]:
        print(f"  Error line : {error_info['error_line']}")
    print(f"  Error      : {error_info['error_msg']}")
    if error_info["source_line"]:
        print(f"  Source     : {error_info['source_line']}")
    print()

# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main() -> None:

    scene_file, scene_class, quality_arg = parse_args()
    quality_flag = QUALITY_FLAGS[quality_arg]

    pipeline_start = time.perf_counter()

    # -----------------------------------------------------------------------
    # Pre-flight check
    # -----------------------------------------------------------------------
    if not os.path.exists(scene_file):
        print()
        print(f"  [ERROR] Scene file not found: {scene_file}")
        print()
        print("  Generate a scene first:")
        print("    python generate.py \"<your topic>\"")
        print()
        sys.exit(1)

    # -----------------------------------------------------------------------
    # Banner
    # -----------------------------------------------------------------------
    print()
    print("  LocalLearn AI")
    print("  " + "-" * 43)
    print(f"  Rendering : {scene_file}")
    print(f"  Scene     : {scene_class}")
    print(f"  Quality   : {QUALITY_LABELS[quality_arg]}")
    print("  " + "-" * 43)
    print()

    # -----------------------------------------------------------------------
    # Render / repair loop
    # -----------------------------------------------------------------------
    # Keep a pristine copy of the original so we never lose working code.
    original_code   = read_scene_code(scene_file)
    current_file    = scene_file    # the file we actually render each attempt
    total_attempts  = 0
    total_render_time = 0.0
    success         = False

    for attempt in range(1, MAX_REPAIR_ATTEMPTS + 2):
        # Attempt MAX_REPAIR_ATTEMPTS + 1 total renders:
        #   render 1  → (optional) repair 1 → render 2
        #               (optional) repair 2 → render 3

        total_attempts += 1
        print(f"  Render attempt: {attempt}")
        print()

        returncode, combined_output, render_secs = run_manim(
            current_file, scene_class, quality_flag
        )
        total_render_time += render_secs

        print()
        print(f"  Render time: {render_secs:.2f} seconds")

        # -------------------------------------------------------------------
        # SUCCESS
        # -------------------------------------------------------------------
        if returncode == 0:
            success = True

            # If we rendered a repair candidate, promote it to generated_scene.py
            if current_file != scene_file:
                shutil.copy2(current_file, scene_file)
                print(f"  Repaired scene saved to: {scene_file}")

            break

        # -------------------------------------------------------------------
        # FAILURE — no more repair attempts left
        # -------------------------------------------------------------------
        if attempt > MAX_REPAIR_ATTEMPTS:
            break

        # -------------------------------------------------------------------
        # FAILURE — extract error and attempt repair
        # -------------------------------------------------------------------
        print_error_summary(extract_manim_error(combined_output))

        print(f"  Attempt {attempt} failed.")

        # Read whatever file we just tried (may be a previous repair candidate)
        failed_code = read_scene_code(current_file)
        error_info  = extract_manim_error(combined_output)

        repaired_code, repair_secs = repair_manim_code(
            failed_code, error_info, attempt_number=attempt
        )

        if repaired_code is None:
            print()
            print(f"  Automatic Manim repair failed (attempt {attempt}).")
            # Continue the loop — will hit the "no more attempts" guard above
            # but we need to break here since we have nothing to render
            break

        # Save repair candidate — do NOT touch the original scene_file yet
        repair_candidate = f"generated_scene_repair_{attempt}.py"
        write_scene_code(repair_candidate, repaired_code)
        print(f"  Repair candidate saved: {repair_candidate}")
        print()
        print(f"  Rendering repaired scene...")
        print()

        # Next loop iteration will render the candidate
        current_file = repair_candidate

    # -----------------------------------------------------------------------
    # Final summary
    # -----------------------------------------------------------------------
    total_elapsed = time.perf_counter() - pipeline_start

    print()
    print("  " + "-" * 43)

    if success:
        print("  Rendering completed successfully.")
        print(f"  Total render attempts : {total_attempts}")
        print(f"  Total render time     : {total_render_time:.2f} seconds")
        print()
        print("  " + "-" * 43)
        print("  VIDEO RENDER COMPLETE")
        print("  " + "-" * 43)
    else:
        print("  Rendering FAILED.")
        print(f"  Total render attempts : {total_attempts}")
        print(f"  Total render time     : {total_render_time:.2f} seconds")
        print()
        if total_attempts > 1:
            print(f"  Automatic Manim repair failed after {total_attempts - 1} attempt(s).")
        print()
        print("  Options:")
        print("    1. Re-generate with a fresh Ollama call:")
        print("         python generate.py \"<your topic>\"")
        print("    2. Inspect the error above and edit generated_scene.py manually.")
        print("    3. Check generated_scene_repair_*.py files if any were created.")
        print("  " + "-" * 43)
        sys.exit(1)

    print()


if __name__ == "__main__":
    main()
