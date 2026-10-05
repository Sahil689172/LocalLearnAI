"""
LocalLearn AI - Manim Runtime Repair
--------------------------------------
Standalone module used by render.py.

Accepts a broken Manim Python script and the Manim error output,
sends a dynamically-constructed repair request to Ollama,
validates the result, and returns the repaired code (or None on failure).

Public API
----------
repair_manim_code(code, manim_error, attempt_number) -> (str | None, float)
extract_manim_error(combined_output)                 -> dict
"""

import ast
import json
import time
import urllib.request
import urllib.error
import re

# ---------------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------------

OLLAMA_URL   = "http://localhost:11434/api/generate"
MODEL        = "llama3:latest"
TIMEOUT_SECS = 300
MAX_REPAIR_ATTEMPTS = 2

# ---------------------------------------------------------------------------
# ERROR EXTRACTION
# ---------------------------------------------------------------------------

def extract_manim_error(combined_output: str) -> dict:
    """
    Parse Manim's stderr/stdout to extract useful error details.

    Returns a dict with keys:
        error_type  (str)   e.g. "TypeError"
        error_msg   (str)   human-readable message
        error_line  (int|None)
        source_line (str)   the offending source line if found
        raw         (str)   the full combined output (truncated to 3000 chars)
    """
    result = {
        "error_type":  "Unknown",
        "error_msg":   "",
        "error_line":  None,
        "source_line": "",
        "raw":         combined_output[:3000],
    }

    lines = combined_output.splitlines()

    # Find the most specific exception line
    exc_pattern = re.compile(
        r'^([A-Z][a-zA-Z]+Error|Exception|TypeError|ValueError|'
        r'AttributeError|NameError|RuntimeError|KeyError|IndexError|'
        r'ImportError|ModuleNotFoundError):\s*(.*)'
    )
    for line in reversed(lines):
        m = exc_pattern.match(line.strip())
        if m:
            result["error_type"] = m.group(1)
            result["error_msg"]  = m.group(2).strip()
            break

    # Find line number inside generated_scene*.py
    file_pattern = re.compile(
        r'File ".*(?:generated_scene|LocalLearnScene).*", line (\d+)'
    )
    source_lines_in_tb = []
    for i, line in enumerate(lines):
        m = file_pattern.search(line)
        if m:
            result["error_line"] = int(m.group(1))
            if i + 1 < len(lines):
                source_lines_in_tb.append(lines[i + 1].strip())

    if source_lines_in_tb:
        result["source_line"] = source_lines_in_tb[-1]

    # Fallback
    if not result["error_msg"]:
        for line in reversed(lines):
            stripped = line.strip()
            if stripped:
                result["error_msg"] = stripped
                break

    return result

# ---------------------------------------------------------------------------
# RESPONSE CLEANER
# ---------------------------------------------------------------------------

def _extract_python_code(raw: str) -> str:
    text = raw.strip()

    if "```" in text:
        fence_lines = text.splitlines()
        inside, code_lines = False, []
        for line in fence_lines:
            if not inside:
                if line.strip().startswith("```"):
                    inside = True
            else:
                if line.strip() == "```":
                    break
                code_lines.append(line)
        if code_lines:
            text = "\n".join(code_lines).strip()

    lines = text.splitlines()
    start = 0
    for i, line in enumerate(lines):
        s = line.strip()
        if s.startswith("from manim import") or s.startswith("import manim"):
            start = i
            break
    text = "\n".join(lines[start:]).strip()

    python_markers = (
        "def ", "class ", "self.", "return", "#", "=", "(",
        ")", "[", "]", ":", "import", "from ", "    ",
    )
    code_lines = text.splitlines()
    last = len(code_lines)
    for i in range(len(code_lines) - 1, -1, -1):
        ln = code_lines[i]
        if not ln.strip():
            continue
        if any(ln.startswith(m) or ln.strip().startswith(m)
               for m in python_markers):
            last = i + 1
            break
    return "\n".join(code_lines[:last]).strip()

# ---------------------------------------------------------------------------
# SYNTAX + STRUCTURE VALIDATION
# ---------------------------------------------------------------------------

def _check_syntax(code: str):
    try:
        ast.parse(code)
        return True, None
    except SyntaxError as exc:
        return False, exc


def _check_structure(code: str) -> list:
    errors = []
    if "from manim import" not in code and "import manim" not in code:
        errors.append("Missing: from manim import *")
    if "class LocalLearnScene" not in code:
        errors.append("Missing: class LocalLearnScene(Scene):")
    if "def construct" not in code:
        errors.append("Missing: def construct(self):")
    return errors

# ---------------------------------------------------------------------------
# OLLAMA CALL
# ---------------------------------------------------------------------------

def _call_ollama(prompt: str) -> str:
    payload = {
        "model":  MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "num_predict": 1500,
            "temperature": 0.1,
        },
    }
    body = json.dumps(payload).encode("utf-8")
    req  = urllib.request.Request(
        url     = OLLAMA_URL,
        data    = body,
        headers = {
            "Content-Type": "application/json",
            "Accept":       "application/json",
        },
        method  = "POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECS) as resp:
            raw_bytes = resp.read()
    except urllib.error.URLError as exc:
        reason = str(exc.reason) if hasattr(exc, "reason") else str(exc)
        raise RuntimeError(f"Ollama connection error: {reason}") from exc
    except Exception as exc:
        msg = str(exc).lower()
        if "timed out" in msg or "timeout" in msg:
            raise TimeoutError(
                f"Ollama repair request timed out after {TIMEOUT_SECS}s."
            ) from exc
        raise

    try:
        data = json.loads(raw_bytes.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Ollama returned non-JSON: {raw_bytes[:200]}") from exc

    if "error" in data:
        raise RuntimeError(f"Ollama error: {data['error']}")

    content = data.get("response", "").strip()
    if not content:
        raise ValueError("Ollama returned an empty response field.")
    return content

# ---------------------------------------------------------------------------
# REPAIR PROMPT — dynamically built from the actual error
# ---------------------------------------------------------------------------

def _build_repair_prompt(code: str, error_info: dict) -> str:
    error_type  = error_info.get("error_type",  "Unknown")
    error_msg   = error_info.get("error_msg",   "")
    error_line  = error_info.get("error_line",  "unknown")
    source_line = error_info.get("source_line", "")

    source_hint = (
        f"\nOffending source line:\n    {source_line}\n"
        if source_line else ""
    )

    # Build a specific, actionable rule based on the actual error type/message
    specific_rule = _make_specific_rule(error_type, error_msg, source_line)

    return (
        "You are repairing a Manim Community Edition 0.21.0 Python program.\n"
        "The Python syntax is already valid, but Manim failed at runtime.\n"
        "\n"
        "ERROR:\n"
        f"{error_type}: {error_msg}\n"
        f"Line: {error_line}\n"
        f"{source_hint}"
        "\n"
        f"RULE:\n{specific_rule}\n"
        "\n"
        "IMPORTANT — PRESERVATION RULES:\n"
        "- Preserve the educational content exactly.\n"
        "- Preserve the animation sequence.\n"
        "- Preserve the scene structure.\n"
        "- Do NOT redesign the lesson.\n"
        "- Do NOT shorten the video.\n"
        "- Do NOT remove animations just to make it work.\n"
        "- Fix ONLY the invalid Python/Manim code.\n"
        "- Return the COMPLETE corrected Python file.\n"
        "- Return ONLY executable Python code.\n"
        "- No Markdown. No explanation.\n"
        "\n"
        "MANIM API SAFETY RULES:\n"
        "- Use only Manim Community Edition 0.21.0 APIs.\n"
        "- Colors: use RED, BLUE, GREEN, YELLOW, ORANGE, PURPLE,\n"
        "  WHITE, BLACK, GRAY, GREY — do NOT use RGB(...).\n"
        "- FadeIn(mob), FadeOut(mob), Write(mob), Create(mob).\n"
        "- LaggedStart(*[FadeIn(m) for m in group], lag_ratio=0.1).\n"
        "  NEVER: LaggedStart(FadeIn, group).\n"
        "- Transform(a, b) requires two Mobjects.\n"
        "- Indicate(mob) and Circumscribe(mob) require a Mobject.\n"
        "- Use Create() not ShowCreation() (removed in CE 0.18).\n"
        "- axes.plot() not axes.get_graph().\n"
        "\n"
        "Original program:\n"
        f"{code}\n"
    )


def _make_specific_rule(error_type: str, error_msg: str, source_line: str) -> str:
    """
    Return a targeted, human-readable rule that directly addresses
    the specific error encountered. This is injected into the repair prompt
    so Ollama understands exactly what to fix.
    """
    msg_lower = error_msg.lower()
    src_lower = source_line.lower()

    # NameError: name 'RGB' is not defined
    if error_type == "NameError" and "rgb" in msg_lower:
        return (
            "Only use colors supported by Manim Community Edition 0.21.0.\n"
            "The code incorrectly uses RGB(...) which is not a valid Manim CE symbol.\n"
            "Replace RGB(...) with a valid Manim color constant such as:\n"
            "    RED, BLUE, GREEN, YELLOW, ORANGE, PURPLE, WHITE, BLACK, GRAY\n"
            "or a hex string like ManimColor('#FF5733')."
        )

    # TypeError: Object <class 'FadeIn'> cannot be converted to an animation
    if error_type == "TypeError" and "cannot be converted to an animation" in msg_lower:
        return (
            "Animations must be instantiated with a Mobject before being passed.\n"
            "The code passed a bare animation class (e.g. FadeIn) instead of an instance.\n"
            "Fix example:\n"
            "    WRONG:   LaggedStart(FadeIn, group)\n"
            "    CORRECT: LaggedStart(*[FadeIn(m) for m in group], lag_ratio=0.1)"
        )

    # NameError: ShowCreation
    if "showcreation" in msg_lower or "showcreation" in src_lower:
        return (
            "ShowCreation was removed in Manim Community Edition 0.18.\n"
            "Replace ShowCreation(mob) with Create(mob)."
        )

    # AttributeError: 'Axes' object has no attribute 'get_graph'
    if error_type == "AttributeError" and "get_graph" in msg_lower:
        return (
            "Axes.get_graph() does not exist in Manim CE.\n"
            "Replace axes.get_graph(func) with axes.plot(func)."
        )

    # Generic NameError
    if error_type == "NameError":
        name_match = re.search(r"name '(\w+)' is not defined", error_msg)
        name = name_match.group(1) if name_match else "the undefined name"
        return (
            f"The name '{name}' is not defined in Manim Community Edition 0.21.0.\n"
            "Only use classes, functions, and constants that are part of "
            "Manim CE.\n"
            f"Remove or replace '{name}' with a valid Manim CE equivalent."
        )

    # Generic AttributeError
    if error_type == "AttributeError":
        return (
            "A method or attribute was called on a Manim object that does not exist.\n"
            "Only call methods that are defined in Manim Community Edition 0.21.0."
        )

    # Generic TypeError
    if error_type == "TypeError":
        return (
            "A Manim function received an incorrect argument type.\n"
            "Check that all animations are properly instantiated with Mobject arguments."
        )

    # Fallback — generic
    return (
        f"Fix the {error_type}: {error_msg}\n"
        "Ensure all Manim APIs used are valid for Manim Community Edition 0.21.0."
    )

# ---------------------------------------------------------------------------
# PUBLIC API
# ---------------------------------------------------------------------------

def repair_manim_code(
    code: str,
    error_info: dict,
    attempt_number: int,
) -> tuple:
    """
    Ask Ollama to repair a Manim runtime error.

    Parameters
    ----------
    code           : the full Python source that failed
    error_info     : dict returned by extract_manim_error()
    attempt_number : 1 or 2 (for display purposes)

    Returns
    -------
    (repaired_code, elapsed_seconds)
        repaired_code is None if repair failed at any stage.
    """
    print()
    print(f"  Asking Ollama to repair the Manim code (attempt {attempt_number}"
          f" of {MAX_REPAIR_ATTEMPTS})...")

    prompt = _build_repair_prompt(code, error_info)

    repair_start = time.perf_counter()
    try:
        raw = _call_ollama(prompt)
    except (RuntimeError, TimeoutError, ValueError) as exc:
        elapsed = time.perf_counter() - repair_start
        print(f"  Repair request failed: {exc}")
        return None, elapsed
    elapsed = time.perf_counter() - repair_start

    print(f"  Repair generation time: {elapsed:.2f} seconds")

    repaired = _extract_python_code(raw)

    if not repaired:
        print("  Repair produced empty code.")
        return None, elapsed

    print("  Validating repaired Python syntax...")
    syntax_ok, syntax_err = _check_syntax(repaired)
    if not syntax_ok:
        err_msg  = syntax_err.msg    if hasattr(syntax_err, "msg")    else str(syntax_err)
        err_line = syntax_err.lineno if hasattr(syntax_err, "lineno") else "?"
        print(f"  Python syntax validation: FAIL")
        print(f"    Line {err_line}: {err_msg}")
        return None, elapsed
    print("  Python syntax validation: PASS")

    struct_errors = _check_structure(repaired)
    if struct_errors:
        print("  Manim structure validation: FAIL")
        for e in struct_errors:
            print(f"    - {e}")
        return None, elapsed
    print("  Manim structure validation: PASS")

    return repaired, elapsed
