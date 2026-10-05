"""
LocalLearn AI - Manim Runtime Repair
--------------------------------------
Standalone module used by render.py.

Accepts a broken Manim Python script and the Manim error output,
sends a repair request to Ollama, validates the result, and
returns the repaired code (or None on failure).

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
# CONFIGURATION  (mirrors generate.py — keep in sync)
# ---------------------------------------------------------------------------

OLLAMA_URL   = "http://localhost:11434/api/generate"
MODEL        = "llama3:latest"
TIMEOUT_SECS = 300

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

    # ---- 1. Find the most specific exception line -----------------------
    # Manim tracebacks end with the exception type and message, e.g.:
    #   TypeError: Object <class '...'> cannot be converted to an animation
    exc_pattern = re.compile(r'^([A-Z][a-zA-Z]+Error|Exception|TypeError|'
                             r'ValueError|AttributeError|NameError|'
                             r'RuntimeError|KeyError|IndexError|'
                             r'ImportError|ModuleNotFoundError):\s*(.*)')

    for line in reversed(lines):
        m = exc_pattern.match(line.strip())
        if m:
            result["error_type"] = m.group(1)
            result["error_msg"]  = m.group(2).strip()
            break

    # ---- 2. Find the line number inside generated_scene.py --------------
    # Traceback lines look like:
    #   File "generated_scene.py", line 29, in construct
    file_pattern = re.compile(
        r'File ".*generated_scene.*", line (\d+)'
    )
    source_lines_in_tb = []
    for i, line in enumerate(lines):
        m = file_pattern.search(line)
        if m:
            result["error_line"] = int(m.group(1))
            # The next line in the traceback is usually the source code
            if i + 1 < len(lines):
                source_lines_in_tb.append(lines[i + 1].strip())

    # Keep the last (most specific) source snippet
    if source_lines_in_tb:
        result["source_line"] = source_lines_in_tb[-1]

    # ---- 3. Fallback: grab last non-empty line as the message -----------
    if not result["error_msg"]:
        for line in reversed(lines):
            stripped = line.strip()
            if stripped:
                result["error_msg"] = stripped
                break

    return result


# ---------------------------------------------------------------------------
# RESPONSE CLEANER  (same logic as generate.py — duplicated to keep module
#                    self-contained without a circular import)
# ---------------------------------------------------------------------------

def _extract_python_code(raw: str) -> str:
    text = raw.strip()

    # 1. Extract from code fence
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

    # 2. Strip preamble before first import
    lines = text.splitlines()
    start = 0
    for i, line in enumerate(lines):
        s = line.strip()
        if s.startswith("from manim import") or s.startswith("import manim"):
            start = i
            break
    text = "\n".join(lines[start:]).strip()

    # 3. Strip trailing prose
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
# SYNTAX VALIDATION
# ---------------------------------------------------------------------------

def _check_syntax(code: str):
    """Returns (True, None) or (False, SyntaxError)."""
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
            "num_predict": 1200,
            "temperature": 0.1,   # very low — we want a faithful fix
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
# REPAIR PROMPT
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

    return (
        "You are debugging a Manim Community Edition Python program.\n"
        "The Python syntax is already valid, but Manim failed at runtime.\n"
        "\n"
        "Fix the Manim API/runtime error.\n"
        "Do not redesign the animation.\n"
        "Do not change the topic or educational content.\n"
        "Fix the minimum amount of code required to resolve the error.\n"
        "Return ONLY the complete corrected Python program.\n"
        "No Markdown. No explanation. No ``` fences.\n"
        "\n"
        f"Error type : {error_type}\n"
        f"Error line : {error_line}\n"
        f"Error      : {error_msg}\n"
        f"{source_hint}"
        "\n"
        "IMPORTANT MANIM RULES TO APPLY WHEN FIXING:\n"
        "- FadeIn, FadeOut, Write, Create must be called as FadeIn(mob),\n"
        "  not passed as bare classes.\n"
        "- LaggedStart receives Animation instances, e.g.:\n"
        "      LaggedStart(*[FadeIn(m) for m in group], lag_ratio=0.15)\n"
        "- Transform(a, b) requires two Mobject arguments.\n"
        "- Indicate(mob) and Circumscribe(mob) require a Mobject.\n"
        "- Do not call methods that do not exist on Text, VGroup, etc.\n"
        "\n"
        "Original program:\n"
        f"{code}\n"
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
    attempt_number : 1 or 2 (used only for display)

    Returns
    -------
    (repaired_code, elapsed_seconds)
        repaired_code is None if repair failed at any stage.
    """
    print()
    print(f"  Asking Ollama to repair the Manim code (attempt {attempt_number})...")

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

    # Syntax check
    print("  Validating repaired Python syntax...")
    syntax_ok, syntax_err = _check_syntax(repaired)
    if not syntax_err is None and not syntax_ok:
        err_msg  = syntax_err.msg    if hasattr(syntax_err, "msg")    else str(syntax_err)
        err_line = syntax_err.lineno if hasattr(syntax_err, "lineno") else "?"
        print(f"  Python syntax validation: FAIL")
        print(f"    Line {err_line}: {err_msg}")
        return None, elapsed
    print("  Python syntax validation: PASS")

    # Structure check
    struct_errors = _check_structure(repaired)
    if struct_errors:
        print("  Manim structure validation: FAIL")
        for e in struct_errors:
            print(f"    - {e}")
        return None, elapsed
    print("  Manim structure validation: PASS")

    return repaired, elapsed
