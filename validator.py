"""
LocalLearn AI - Code Validator and Duration Estimator
------------------------------------------------------
Validates generated Manim code and estimates video duration
without actually rendering.

Validation layers:
  1. Python syntax        (ast.parse)
  2. Manim structure      (required boilerplate)
  3. Suspicious API scan  (catches RGB, bare LaggedStart, etc.)
  4. Duration estimation  (static regex — no rendering required)
"""

import ast
import re

# ---------------------------------------------------------------------------
# LAYER 1 — PYTHON SYNTAX
# ---------------------------------------------------------------------------

def check_python_syntax(code: str):
    """
    Validate Python syntax using ast.parse().

    Returns:
        (True, None)          — valid
        (False, SyntaxError)  — invalid
    """
    try:
        ast.parse(code)
        return True, None
    except SyntaxError as exc:
        return False, exc

# ---------------------------------------------------------------------------
# LAYER 2 — MANIM STRUCTURE
# ---------------------------------------------------------------------------

def check_manim_structure(code: str) -> list:
    """
    Check for required Manim boilerplate.

    Returns:
        List of error strings (empty = valid)
    """
    errors = []

    if "from manim import" not in code and "import manim" not in code:
        errors.append("Missing: from manim import *")

    if "class LocalLearnScene" not in code:
        errors.append("Missing: class LocalLearnScene(Scene):")

    if "def construct" not in code:
        errors.append("Missing: def construct(self):")

    return errors

# ---------------------------------------------------------------------------
# LAYER 3 — SUSPICIOUS API SCAN
# ---------------------------------------------------------------------------

# Patterns that indicate a known-invalid or dangerous Manim API usage.
# Each entry is (human_label, compiled_regex).
# Keep this list focused on high-confidence problems — do not over-block.
_SUSPICIOUS_PATTERNS = [

    # RGB is not a Manim Community symbol — use color constants instead
    (
        "RGB() is not a valid Manim color (use RED, BLUE, GREEN, etc.)",
        re.compile(r'\bRGB\s*\('),
    ),

    # ManimGL-only interpolation color
    (
        "color_gradient() is ManimGL only — use ManimCE color_gradient if available",
        re.compile(r'\bcolor_gradient\s*\('),
    ),

    # Bare animation class passed to LaggedStart
    # e.g.  LaggedStart(FadeIn, obj)  or  LaggedStart(Write, group)
    (
        "LaggedStart receives Animation instances, not classes "
        "(e.g. LaggedStart(*[FadeIn(m) for m in grp], lag_ratio=0.1))",
        re.compile(
            r'LaggedStart\s*\(\s*(?:FadeIn|FadeOut|Write|Create|'
            r'GrowArrow|Indicate|Circumscribe|Transform|'
            r'ReplacementTransform|ShowCreation)\s*,'
        ),
    ),

    # AnimationGroup with bare class
    (
        "AnimationGroup receives Animation instances, not bare classes",
        re.compile(
            r'AnimationGroup\s*\(\s*(?:FadeIn|FadeOut|Write|Create)\s*,'
        ),
    ),

    # ShowCreation was removed in Manim CE 0.18 — replaced by Create
    (
        "ShowCreation was removed in Manim CE 0.18 — use Create() instead",
        re.compile(r'\bShowCreation\s*\('),
    ),

    # get_graph / axes.plot confusion (common hallucination)
    (
        "get_graph() does not exist on Axes — use axes.plot() instead",
        re.compile(r'\.get_graph\s*\('),
    ),

    # scene.add_sound is ManimGL / not available in CE without extra setup
    (
        "add_sound() is not reliably available in Manim CE — omit audio calls",
        re.compile(r'\badd_sound\s*\('),
    ),
]


def scan_suspicious_apis(code: str) -> list:
    """
    Scan the code for known invalid or risky Manim API patterns.

    Returns:
        List of warning dicts with keys:
            "label"    — human-readable description
            "lines"    — list of (line_number, line_text) matches
    """
    warnings = []

    code_lines = code.splitlines()

    for label, pattern in _SUSPICIOUS_PATTERNS:
        matches = []
        for lineno, line in enumerate(code_lines, start=1):
            if pattern.search(line):
                matches.append((lineno, line.strip()))

        if matches:
            warnings.append({
                "label": label,
                "lines": matches,
            })

    return warnings

# ---------------------------------------------------------------------------
# LAYER 4 — DURATION ESTIMATION
# ---------------------------------------------------------------------------

def estimate_duration(code: str) -> tuple:
    """
    Estimate video duration by parsing run_time and wait() calls.

    This is a static estimate — not a guarantee of actual render time.

    Returns:
        (estimated_seconds, classification)

        classification: "TOO_SHORT", "SHORT", "TARGET", "LONG"
    """
    total_seconds = 0.0

    # 1. Explicit run_time= arguments
    run_time_pattern = re.compile(r'run_time\s*=\s*([\d.]+)')
    for match in run_time_pattern.finditer(code):
        try:
            total_seconds += float(match.group(1))
        except ValueError:
            pass

    # 2. self.wait(X) calls
    wait_pattern = re.compile(r'self\.wait\s*\(\s*([\d.]+)\s*\)')
    for match in wait_pattern.finditer(code):
        try:
            total_seconds += float(match.group(1))
        except ValueError:
            pass

    # 3. self.play() calls without explicit run_time -> default 1 second each
    play_pattern = re.compile(r'self\.play\s*\(')
    play_count = len(play_pattern.findall(code))
    explicit_run_times = len(run_time_pattern.findall(code))
    implicit_plays = max(0, play_count - explicit_run_times)
    total_seconds += implicit_plays * 1.0

    # 4. Classify
    if total_seconds < 45:
        classification = "TOO_SHORT"
    elif total_seconds < 60:
        classification = "SHORT"
    elif total_seconds <= 90:
        classification = "TARGET"
    else:
        classification = "LONG"

    return total_seconds, classification

# ---------------------------------------------------------------------------
# PUBLIC API
# ---------------------------------------------------------------------------

def validate_and_estimate(code: str) -> dict:
    """
    Run all validation layers and estimate duration.

    Returns:
        {
            "syntax_valid":            bool,
            "syntax_error":            SyntaxError | None,
            "structure_errors":        list[str],
            "api_warnings":            list[dict],
            "estimated_duration":      float,
            "duration_classification": str,
            "is_valid":                bool
        }
    """
    syntax_valid, syntax_error = check_python_syntax(code)
    structure_errors            = check_manim_structure(code)
    api_warnings                = scan_suspicious_apis(code)

    if syntax_valid:
        estimated_duration, classification = estimate_duration(code)
    else:
        estimated_duration = 0.0
        classification     = "UNKNOWN"

    return {
        "syntax_valid":            syntax_valid,
        "syntax_error":            syntax_error,
        "structure_errors":        structure_errors,
        "api_warnings":            api_warnings,
        "estimated_duration":      estimated_duration,
        "duration_classification": classification,
        "is_valid":                syntax_valid and not structure_errors,
    }
