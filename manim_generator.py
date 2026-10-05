"""
LocalLearn AI - Manim Code Generator (Stage 2)
-----------------------------------------------
Converts a LessonSpec (JSON) into executable Manim Python code.

This stage does NOT redesign the lesson. It faithfully implements
the planned scenes from Stage 1.
"""

import json
import urllib.request
import urllib.error

# ---------------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------------

OLLAMA_URL   = "http://localhost:11434/api/generate"
MODEL        = "llama3:latest"
TIMEOUT_SECS = 300

# ---------------------------------------------------------------------------
# CODE GENERATION PROMPT
# ---------------------------------------------------------------------------

def build_code_generation_prompt(lesson_spec: dict) -> str:
    """
    Build the prompt for Stage 2: Manim code generation.

    The LLM receives the complete lesson plan and must implement it
    faithfully in Manim Python code.
    """
    lesson_json = json.dumps(lesson_spec, indent=2)

    return (
        "You are LocalLearn AI's Manim code generator.\n"
        "You will receive a complete lesson plan as JSON.\n"
        "Your job is to convert it into executable Manim Community Edition "
        "Python code.\n"
        "\n"
        "STRICT OUTPUT RULE:\n"
        "Return ONLY valid Python code.\n"
        "Do NOT include explanations.\n"
        "Do NOT include Markdown.\n"
        "Do NOT include ```python fences or ``` fences.\n"
        "Do NOT truncate the program.\n"
        "Return the COMPLETE Python program.\n"
        "\n"
        "IMPLEMENTATION RULES:\n"
        "- Implement ALL scenes from the lesson plan faithfully.\n"
        "- Do NOT skip scenes.\n"
        "- Do NOT redesign the lesson.\n"
        "- Follow the specified scene sequence exactly.\n"
        "- Use the target durations as guidance for timing.\n"
        "- Implement the visual descriptions and animations specified.\n"
        "\n"
        "PYTHON STRUCTURE:\n"
        "- Start with: from manim import *\n"
        "- Define exactly: class LocalLearnScene(Scene):\n"
        "- Define: def construct(self):\n"
        "- Implement each scene as a logical section in construct()\n"
        "\n"
        "MANIM API SAFETY (CRITICAL — READ CAREFULLY):\n"
        "You are generating code for Manim Community Edition 0.21.0.\n"
        "Never invent an API. Only use classes, functions, constants, and\n"
        "methods that belong to Manim Community Edition.\n"
        "Prefer simple, well-known Manim constructs over obscure APIs.\n"
        "\n"
        "COLORS — use ONLY these known Manim color constants:\n"
        "    RED, BLUE, GREEN, YELLOW, ORANGE, PURPLE,\n"
        "    WHITE, BLACK, GRAY, GREY, PINK, TEAL, GOLD,\n"
        "    RED_A through RED_E, BLUE_A through BLUE_E,\n"
        "    GREEN_A through GREEN_E, YELLOW_A through YELLOW_E\n"
        "Do NOT use RGB(...) — it is not a valid Manim CE symbol.\n"
        "Do NOT use color_gradient() from ManimGL.\n"
        "Do NOT use matplotlib, pygame, or any other library's color API.\n"
        "\n"
        "ANIMATION RULES (MUST FOLLOW EXACTLY):\n"
        "- FadeIn(mobject) — never pass FadeIn as a bare class\n"
        "- FadeOut(mobject) — never pass FadeOut as a bare class\n"
        "- Write(mobject)\n"
        "- Create(mobject)  — do NOT use ShowCreation (removed in CE 0.18)\n"
        "- Transform(a, b) — requires two Mobject arguments\n"
        "- Indicate(mobject)\n"
        "- Circumscribe(mobject)\n"
        "- LaggedStart(*[FadeIn(m) for m in group], lag_ratio=0.15)\n"
        "  NEVER: LaggedStart(FadeIn, group) — this is wrong\n"
        "  NEVER: LaggedStart(Write, group)  — this is wrong\n"
        "- Always instantiate animations with a Mobject first\n"
        "- Do not call methods that do not exist on Text, MathTex, VGroup,\n"
        "  Square, Circle, Arrow, Axes, or other Mobjects\n"
        "- For Axes: use axes.plot() not axes.get_graph()\n"
        "- Do not use add_sound()\n"
        "- Use only valid Manim Community Edition 0.21 APIs\n"
        "\n"
        "MANIM QUALITY REQUIREMENTS:\n"
        "- Use VGroup to group every shape with its own label\n"
        "- Use arrange(), next_to(), to_edge(), align_to() for layout\n"
        "- Never use arbitrary coordinates; prefer relative positioning\n"
        "- Keep all objects inside the visible frame\n"
        "- Never overlap text, shapes, arrows, or labels\n"
        "- Use font sizes: title 44-52, heading 32-36, body 24-28\n"
        "\n"
        "OBJECT GROUPING (CRITICAL):\n"
        "When creating arrays, nodes, or labeled shapes:\n"
        "  cell = VGroup(box, label)   # group each element\n"
        "  cells.add(cell)\n"
        "  cells.arrange(RIGHT, buff=0.2)\n"
        "This prevents overlap and makes animation reliable.\n"
        "\n"
        "TIMING:\n"
        "- Use realistic run_time values: 1, 1.5, 2 seconds\n"
        "- Use self.wait() between scenes: 0.5 to 2 seconds typically\n"
        "- Do NOT use giant waits like self.wait(60)\n"
        "- Let the video naturally reach the target duration through "
        "meaningful animations\n"
        "\n"
        "TEXT SAFETY:\n"
        "- Text must never overlap other objects or frame edges\n"
        "- Use next_to(), to_edge(), arrange() to position text\n"
        "- Keep explanations concise\n"
        "- Split long text into multiple Text objects\n"
        "\n"
        "SYNTAX:\n"
        "- Every opening parenthesis, bracket, brace must have a "
        "matching closing symbol\n"
        "- The output must be valid Python syntax\n"
        "- Do not truncate the program\n"
        "\n"
        "LESSON PLAN:\n"
        f"{lesson_json}\n"
        "\n"
        "Generate the complete Manim Python code now:\n"
    )

# ---------------------------------------------------------------------------
# OLLAMA CALL
# ---------------------------------------------------------------------------

def call_ollama(prompt: str) -> str:
    """POST to /api/generate and return the response string."""
    payload = {
        "model":  MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "num_predict": 1500,
            "temperature": 0.15,
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
            raise RuntimeError("Ollama is not running.") from exc
        if "timed out" in reason.lower() or "timeout" in reason.lower():
            raise TimeoutError(
                f"Ollama code generation exceeded {TIMEOUT_SECS} seconds."
            ) from exc
        raise RuntimeError(f"Ollama connection error: {reason}") from exc
    except Exception as exc:
        msg = str(exc).lower()
        if "timed out" in msg or "timeout" in msg:
            raise TimeoutError(
                f"Ollama code generation exceeded {TIMEOUT_SECS} seconds."
            ) from exc
        raise

    try:
        data = json.loads(raw_bytes.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Ollama returned non-JSON: {raw_bytes[:200]}"
        ) from exc

    if "error" in data:
        raise RuntimeError(f"Ollama error: {data['error']}")

    content = data.get("response", "").strip()
    if not content:
        raise ValueError("Ollama returned an empty response.")

    return content

# ---------------------------------------------------------------------------
# CODE EXTRACTION
# ---------------------------------------------------------------------------

def extract_python_code(raw: str) -> str:
    """
    Robustly extract Python code from the model response.

    Handles:
      - ```python ... ``` fences
      - ``` ... ``` fences
      - preamble text before 'from manim import'
      - trailing explanation text after the code
    """
    text = raw.strip()

    # 1. Extract from code fence if present
    if "```" in text:
        lines = text.splitlines()
        inside = False
        code_lines = []
        for line in lines:
            stripped = line.strip()
            if not inside:
                if stripped.startswith("```"):
                    inside = True
            else:
                if stripped == "```":
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
# PUBLIC API
# ---------------------------------------------------------------------------

def generate_manim_code(lesson_spec: dict) -> tuple:
    """
    Generate Manim Python code from a LessonSpec.

    Returns:
        (python_code_str, elapsed_seconds)

    Raises:
        RuntimeError, TimeoutError, ValueError on errors
    """
    import time

    prompt = build_code_generation_prompt(lesson_spec)

    start = time.perf_counter()
    raw_response = call_ollama(prompt)
    elapsed = time.perf_counter() - start

    code = extract_python_code(raw_response)

    if not code:
        raise ValueError("No Python code found in response.")

    return code, elapsed
