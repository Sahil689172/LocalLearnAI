"""
LocalLearn AI - Manim Script Generator
---------------------------------------
Usage:
    python generate.py "Explain Bubble Sort"

Pipeline:
    Topic -> Ollama llama3:latest -> Python syntax validation
          -> Manim structure validation -> generated_scene.py

Render the result manually with render.py:
    python render.py generated_scene.py LocalLearnScene --low
"""

import sys
import os
import ast
import json
import time
import urllib.request
import urllib.error

# ---------------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------------

OLLAMA_URL        = "http://localhost:11434/api/generate"
MODEL             = "llama3:latest"
OUTPUT_FILE       = "generated_scene.py"
INVALID_FILE      = "generated_scene_invalid.py"
TIMEOUT_SECS      = 300    # large Manim prompts can take 60-100+ s locally
MAX_REPAIR_ATTEMPTS = 2

# ---------------------------------------------------------------------------
# PROMPT BUILDERS
# ---------------------------------------------------------------------------

def build_prompt(topic: str) -> str:
    """Primary generation prompt — concise, code-focused."""
    return (
        "You are LocalLearn AI, an expert Manim Community Edition programmer.\n"
        "Generate a complete educational animation for the user's topic.\n"
        "\n"
        "STRICT OUTPUT RULE:\n"
        "Return ONLY valid Python code.\n"
        "Do NOT include explanations, Markdown, ```python fences, or ``` fences.\n"
        "Do NOT truncate the program.\n"
        "Return the COMPLETE Python program.\n"
        "\n"
        "SYNTAX RULE:\n"
        "Before returning the code, mentally verify that every opening\n"
        "parenthesis '(', bracket '[', and brace '{' has a matching closing\n"
        "symbol. The output must be valid Python syntax.\n"
        "\n"
        "The program must:\n"
        "- start with: from manim import *\n"
        "- define exactly: class LocalLearnScene(Scene):\n"
        "- define: def construct(self):\n"
        "- visually explain the topic across 6-8 distinct animation stages\n"
        "- use VGroup to group every shape with its own label before arranging\n"
        "- use arrange(), next_to(), to_edge(), align_to() for all layout\n"
        "- keep all objects inside the visible frame\n"
        "- never overlap text, shapes, arrows, or labels\n"
        "- use self.wait() between stages\n"
        "- use font sizes: title 44-52, heading 32-36, body 24-28\n"
        "- avoid arbitrary coordinates; prefer relative positioning\n"
        "- use only standard Manim — no external APIs or images\n"
        "- be a complete standalone renderable Python script\n"
        "\n"
        "GROUPING RULE — always pair a shape with its label:\n"
        "    cell = VGroup(box, label)   # CORRECT\n"
        "    cells.add(cell)\n"
        "    cells.arrange(RIGHT, buff=0.2)\n"
        "\n"
        "MANIM ANIMATION RULES — follow these exactly:\n"
        "- FadeIn must be called as FadeIn(mobject), never as a bare class.\n"
        "- FadeOut must be called as FadeOut(mobject), never as a bare class.\n"
        "- Write must be called as Write(mobject).\n"
        "- Create must be called as Create(mobject).\n"
        "- Transform requires two Mobject arguments: Transform(a, b).\n"
        "- Indicate requires a Mobject: Indicate(mob).\n"
        "- Circumscribe requires a Mobject: Circumscribe(mob).\n"
        "- LaggedStart receives Animation instances, not animation classes:\n"
        "      CORRECT: LaggedStart(*[FadeIn(m) for m in group], lag_ratio=0.15)\n"
        "      WRONG:   LaggedStart(FadeIn, group)\n"
        "- Do not pass animation classes (FadeIn, Write, etc.) as arguments.\n"
        "  Always instantiate them with a Mobject first.\n"
        "- Do not call methods that do not exist on Text, MathTex, VGroup,\n"
        "  Square, Circle, Arrow, or other Mobjects.\n"
        "- Use valid Manim Community Edition APIs only.\n"
        "- Prefer simple, reliable animations over complex compositions.\n"
        "\n"
        f"Topic: {topic}\n"
    )


def build_repair_prompt(code: str, error: str, line: int) -> str:
    """Repair prompt sent when ast.parse() fails on the generated code."""
    return (
        "You generated a Python program for Manim, but it contains a Python "
        "syntax error.\n"
        "\n"
        "Fix ONLY the syntax error and any directly related malformed code.\n"
        "Do not redesign the animation.\n"
        "Do not change the educational content unnecessarily.\n"
        "Return ONLY the complete corrected Python code.\n"
        "Do not use Markdown fences.\n"
        "\n"
        f"Syntax error: {error}\n"
        f"Line: {line}\n"
        "\n"
        "Original code:\n"
        f"{code}\n"
    )

# ---------------------------------------------------------------------------
# RESPONSE CLEANER
# ---------------------------------------------------------------------------

def extract_python_code(raw: str) -> str:
    """
    Robustly extract Python code from the model response.

    Handles:
      - ```python ... ``` fences
      - ``` ... ``` fences
      - "Here is the code:" preamble before 'from manim import'
      - trailing explanation text after the last code line
    """
    text = raw.strip()

    # ---- 1. Extract from a code fence if one is present ------------------
    if "```" in text:
        lines = text.splitlines()
        inside    = False
        code_lines = []
        for line in lines:
            stripped = line.strip()
            if not inside:
                if stripped.startswith("```"):
                    inside = True        # skip the opening fence line
            else:
                if stripped == "```":
                    break                # stop at closing fence
                code_lines.append(line)
        if code_lines:
            text = "\n".join(code_lines).strip()

    # ---- 2. Strip preamble prose before the first import -----------------
    lines = text.splitlines()
    start_index = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        if (stripped.startswith("from manim import")
                or stripped.startswith("import manim")):
            start_index = i
            break
    text = "\n".join(lines[start_index:]).strip()

    # ---- 3. Strip trailing non-code prose --------------------------------
    # Walk backwards; keep dropping blank lines and lines that look like
    # plain English (no Python syntax markers).
    python_markers = (
        "def ", "class ", "self.", "return", "#", "=", "(",
        ")", "[", "]", ":", "import", "from ", "    ",
    )
    code_lines = text.splitlines()
    last_code_line = len(code_lines)
    for i in range(len(code_lines) - 1, -1, -1):
        line = code_lines[i]
        if not line.strip():
            continue
        if any(
            line.startswith(m) or line.strip().startswith(m)
            for m in python_markers
        ):
            last_code_line = i + 1
            break

    return "\n".join(code_lines[:last_code_line]).strip()

# ---------------------------------------------------------------------------
# SYNTAX VALIDATION
# ---------------------------------------------------------------------------

def check_python_syntax(code: str):
    """
    Attempt to parse the code with ast.parse().

    Returns:
        (True,  None)          — valid syntax
        (False, SyntaxError)   — invalid syntax; the exception carries
                                 .lineno, .offset, .msg
    """
    try:
        ast.parse(code)
        return True, None
    except SyntaxError as exc:
        return False, exc

# ---------------------------------------------------------------------------
# MANIM STRUCTURE VALIDATION
# ---------------------------------------------------------------------------

def check_manim_structure(code: str) -> list:
    """
    Basic static checks for required Manim boilerplate.
    Returns a list of error strings (empty = pass).
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
# OLLAMA REQUEST
# ---------------------------------------------------------------------------

def call_ollama(prompt: str) -> str:
    """
    POST to /api/generate (stream=false) and return the 'response' string.

    Raises:
        RuntimeError  — Ollama not running / connection refused / model missing
        TimeoutError  — generation exceeded TIMEOUT_SECS
        ValueError    — unexpected or empty JSON response
    """
    payload = {
        "model":  MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "num_predict": 1200,   # cap output length — keep scripts compact
            "temperature": 0.2,    # low temp = reliable code generation
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
        if "refused" in reason.lower() or "11434" in reason.lower():
            raise RuntimeError(
                "\n  Ollama is not running.\n"
                "  Start Ollama and make sure llama3:latest is available.\n"
                "  Then re-run: python generate.py \"<your topic>\"\n"
            ) from exc
        # urllib wraps socket.timeout as a URLError on Windows
        if "timed out" in reason.lower() or "timeout" in reason.lower():
            raise TimeoutError(
                f"\n  Ollama generation exceeded {TIMEOUT_SECS} seconds.\n"
            ) from exc
        raise RuntimeError(f"\n  Ollama connection error: {reason}\n") from exc

    except TimeoutError as exc:
        raise TimeoutError(
            f"\n  Ollama generation exceeded {TIMEOUT_SECS} seconds.\n"
        ) from exc

    except Exception as exc:
        msg = str(exc).lower()
        if "timed out" in msg or "timeout" in msg:
            raise TimeoutError(
                f"\n  Ollama generation exceeded {TIMEOUT_SECS} seconds.\n"
            ) from exc
        raise

    # ---- Parse JSON -------------------------------------------------------
    try:
        data = json.loads(raw_bytes.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(
            "\n  Ollama returned a non-JSON response.\n"
            f"  Raw output (first 200 chars): {raw_bytes[:200]}\n"
        ) from exc

    if "error" in data:
        error_msg = data["error"]
        if "not found" in error_msg.lower():
            raise RuntimeError(
                f"\n  Model '{MODEL}' was not found in Ollama.\n"
                f"  Pull it with:  ollama pull {MODEL}\n"
            )
        raise RuntimeError(f"\n  Ollama error: {error_msg}\n")

    content = data.get("response", "").strip()
    if not content:
        raise ValueError(
            "\n  Ollama returned an empty 'response' field.\n"
            f"  Keys in response: {list(data.keys())}\n"
        )

    return content

# ---------------------------------------------------------------------------
# SAVE HELPERS
# ---------------------------------------------------------------------------

def save_file(path: str, topic: str, code: str) -> None:
    header = (
        f"# Generated by LocalLearn AI\n"
        f"# Topic : {topic}\n"
        f"# Model : {MODEL}\n"
        f"# Render: manim {OUTPUT_FILE} LocalLearnScene\n"
        f"#\n"
        f"# Re-generate with: python generate.py \"{topic}\"\n\n"
    )
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(header + code + "\n")


def existing_output_is_valid() -> bool:
    """Return True if the current OUTPUT_FILE passes Manim structure checks."""
    if not os.path.exists(OUTPUT_FILE):
        return False
    with open(OUTPUT_FILE, "r", encoding="utf-8") as fh:
        existing = fh.read()
    syntax_ok, _ = check_python_syntax(existing)
    structure_errors = check_manim_structure(existing)
    return syntax_ok and not structure_errors

# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main() -> None:

    pipeline_start = time.perf_counter()

    # -----------------------------------------------------------------------
    # 1. Argument
    # -----------------------------------------------------------------------
    if len(sys.argv) < 2 or not sys.argv[1].strip():
        print(
            "\nUsage:\n"
            "    python generate.py \"<educational topic>\"\n\n"
            "Example:\n"
            "    python generate.py \"Explain Bubble Sort\"\n"
        )
        sys.exit(1)

    topic = sys.argv[1].strip()

    # -----------------------------------------------------------------------
    # 2. Banner
    # -----------------------------------------------------------------------
    print()
    print("  LocalLearn AI")
    print("  " + "-" * 43)
    print(f"  Topic  : {topic}")
    print(f"  Model  : {MODEL}")
    print(f"  Output : {OUTPUT_FILE}")
    print("  " + "-" * 43)
    print()

    # -----------------------------------------------------------------------
    # 3. Connect & generate
    # -----------------------------------------------------------------------
    print("  Connecting to Ollama...")

    prompt = build_prompt(topic)

    conn_start = time.perf_counter()
    try:
        raw_response = call_ollama(prompt)
    except RuntimeError as exc:
        print(f"\n[ERROR]{exc}")
        sys.exit(1)
    except TimeoutError as exc:
        print(f"\n[TIMEOUT]{exc}")
        sys.exit(1)
    except ValueError as exc:
        print(f"\n[RESPONSE ERROR]{exc}")
        sys.exit(1)
    conn_end = time.perf_counter()

    # The connection itself is near-instant; generation takes the bulk of time.
    # We report both from a single elapsed measurement since urllib doesn't
    # expose a separate connect/transfer split without lower-level sockets.
    generation_secs = conn_end - conn_start

    print("  Ollama connection successful.")
    print(f"  Connection time: {generation_secs:.2f} seconds")
    print()
    print("  Generating Manim script...")
    print()
    print(f"  Ollama generation time: {generation_secs:.2f} seconds")
    print()

    # -----------------------------------------------------------------------
    # 4. Clean the response
    # -----------------------------------------------------------------------
    code = extract_python_code(raw_response)

    if not code:
        print(
            "[ERROR]\n"
            "  The response did not contain any Python code.\n"
            f"  Raw response (first 300 chars):\n  {raw_response[:300]}\n"
        )
        sys.exit(1)

    # -----------------------------------------------------------------------
    # 5. Syntax validation + auto-repair loop
    # -----------------------------------------------------------------------
    val_start = time.perf_counter()

    print("  Validating Python syntax...")

    syntax_ok, syntax_err = check_python_syntax(code)
    repair_attempts = 0

    while not syntax_ok and repair_attempts < MAX_REPAIR_ATTEMPTS:
        repair_attempts += 1

        err_msg = syntax_err.msg if hasattr(syntax_err, "msg") else str(syntax_err)
        err_line = syntax_err.lineno if hasattr(syntax_err, "lineno") else "?"
        err_col  = syntax_err.offset if hasattr(syntax_err, "offset") else "?"

        print()
        print("  Python syntax validation: FAIL")
        print(f"    SyntaxError detected")
        print(f"    Line   : {err_line}")
        print(f"    Column : {err_col}")
        print(f"    Error  : {err_msg}")
        print()
        print(f"  Attempting automatic repair (attempt {repair_attempts}"
              f" of {MAX_REPAIR_ATTEMPTS})...")

        repair_prompt = build_repair_prompt(code, err_msg, err_line)

        try:
            raw_repair = call_ollama(repair_prompt)
        except (RuntimeError, TimeoutError, ValueError) as exc:
            print(f"\n  Repair request failed: {exc}")
            break

        code = extract_python_code(raw_repair)
        syntax_ok, syntax_err = check_python_syntax(code)

        if syntax_ok:
            print(f"  Python syntax validation: PASS  (repaired on attempt {repair_attempts})")

    val_end = time.perf_counter()
    val_secs = val_end - val_start

    # ---- Handle permanent syntax failure ----------------------------------
    if not syntax_ok:
        err_msg  = syntax_err.msg     if hasattr(syntax_err, "msg")    else str(syntax_err)
        err_line = syntax_err.lineno  if hasattr(syntax_err, "lineno") else "?"
        err_col  = syntax_err.offset  if hasattr(syntax_err, "offset") else "?"

        print()
        print("  Python syntax validation: FAIL")
        print(f"    SyntaxError detected")
        print(f"    Line   : {err_line}")
        print(f"    Column : {err_col}")
        print(f"    Error  : {err_msg}")
        print()
        print(f"  Automatic repair failed after {MAX_REPAIR_ATTEMPTS} attempts.")
        print()

        # Save invalid code for inspection — do NOT overwrite a good file
        save_file(INVALID_FILE, topic, code)
        print(f"  Invalid code saved to: {INVALID_FILE}  (for inspection)")

        if existing_output_is_valid():
            print(f"  Existing '{OUTPUT_FILE}' is valid and was NOT overwritten.")
        print()
        total_secs = time.perf_counter() - pipeline_start
        print("  " + "-" * 43)
        print(f"  TOTAL GENERATION TIME: {total_secs:.2f} seconds")
        print("  " + "-" * 43)
        print()
        sys.exit(1)

    # ---- Syntax passed on first attempt -----------------------------------
    if repair_attempts == 0:
        print("  Python syntax validation: PASS")

    print(f"  Validation time: {val_secs:.2f} seconds")
    print()

    # -----------------------------------------------------------------------
    # 6. Manim structure validation
    # -----------------------------------------------------------------------
    print("  Validating Manim structure...")

    structure_errors = check_manim_structure(code)

    if structure_errors:
        print("  Manim structure validation: FAIL")
        for e in structure_errors:
            print(f"    - {e}")
        print()

        save_file(INVALID_FILE, topic, code)
        print(f"  Invalid code saved to: {INVALID_FILE}  (for inspection)")

        if existing_output_is_valid():
            print(f"  Existing '{OUTPUT_FILE}' is valid and was NOT overwritten.")

        print()
        total_secs = time.perf_counter() - pipeline_start
        print("  " + "-" * 43)
        print(f"  TOTAL GENERATION TIME: {total_secs:.2f} seconds")
        print("  " + "-" * 43)
        print()
        sys.exit(1)

    print("  Manim structure validation: PASS")
    print()

    # -----------------------------------------------------------------------
    # 7. Save
    # -----------------------------------------------------------------------
    save_file(OUTPUT_FILE, topic, code)

    total_secs = time.perf_counter() - pipeline_start

    # -----------------------------------------------------------------------
    # 8. Success summary
    # -----------------------------------------------------------------------
    print("  Generation successful.")
    print(f"  Saved: {OUTPUT_FILE}")
    print()
    print("  " + "-" * 43)
    print(f"  Ollama generation time : {generation_secs:.2f} seconds")
    print(f"  Validation time        : {val_secs:.2f} seconds")
    print(f"  TOTAL GENERATION TIME  : {total_secs:.2f} seconds")
    print("  " + "-" * 43)
    print()
    print("  To render (low quality preview):")
    print(f"    python render.py {OUTPUT_FILE} LocalLearnScene --low")
    print()
    print("  To render (full quality):")
    print(f"    python render.py {OUTPUT_FILE} LocalLearnScene --high")
    print()


if __name__ == "__main__":
    main()
