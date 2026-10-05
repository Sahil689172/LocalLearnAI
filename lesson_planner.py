"""
LocalLearn AI - Lesson Planner
--------------------------------
Makes ONE compact Ollama call to get a structured JSON lesson spec.
Ollama decides WHAT to teach. Python decides HOW to animate it.

The prompt is deliberately short so llama3:latest responds quickly.
"""

import json
import time
import urllib.request
import urllib.error

OLLAMA_URL   = "http://localhost:11434/api/generate"
MODEL        = "llama3:latest"
TIMEOUT_SECS = 120   # compact JSON should arrive well within 2 minutes

# ---------------------------------------------------------------------------
# PROMPT
# ---------------------------------------------------------------------------

def build_planning_prompt(topic: str) -> str:
    return (
        "You are the lesson planner for LocalLearn AI.\n"
        "Create a compact JSON lesson specification for a 60-90 second "
        "educational animation about:\n"
        f"\n    {topic}\n\n"
        "Rules:\n"
        "- Return ONLY valid JSON. No markdown. No ```json fences. "
        "No explanation.\n"
        "- Use 5-8 scenes maximum.\n"
        "- Do NOT generate Python, Manim code, or animation instructions.\n"
        "- Keep text fields SHORT (one sentence each).\n"
        "\n"
        "Allowed scene types and their required fields:\n"
        '  {"type":"title",       "text":"...", "duration":4}\n'
        '  {"type":"definition",  "text":"...", "duration":6}\n'
        '  {"type":"explanation", "text":"...", "points":["...","..."], "duration":8}\n'
        '  {"type":"array_search","values":[...], "target":N, "duration":30}\n'
        '  {"type":"array_sort",  "values":[...], "duration":25}\n'
        '  {"type":"formula",     "text":"...", "formula":"O(log n)", "duration":7}\n'
        '  {"type":"comparison",  "items":[{"label":"A","value":"..."},{"label":"B","value":"..."}], "duration":8}\n'
        '  {"type":"complexity",  "text":"...", "value":"O(log n)", "duration":7}\n'
        '  {"type":"summary",     "text":"...", "points":["...","..."], "duration":8}\n'
        "\n"
        "Output format:\n"
        "{\n"
        '  "topic": "...",\n'
        '  "target_duration": 75,\n'
        '  "scenes": [ ... ]\n'
        "}\n"
    )

# ---------------------------------------------------------------------------
# OLLAMA CALL
# ---------------------------------------------------------------------------

def _call_ollama(prompt: str) -> str:
    payload = {
        "model":  MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "num_predict": 600,   # compact JSON — no need for more
            "temperature": 0.2,
        },
    }
    body = json.dumps(payload).encode("utf-8")
    req  = urllib.request.Request(
        url     = OLLAMA_URL,
        data    = body,
        headers = {"Content-Type": "application/json", "Accept": "application/json"},
        method  = "POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECS) as resp:
            raw_bytes = resp.read()
    except urllib.error.URLError as exc:
        reason = str(exc.reason) if hasattr(exc, "reason") else str(exc)
        if "refused" in reason.lower() or "11434" in reason.lower():
            raise RuntimeError(
                "Ollama is not running. Start Ollama and ensure "
                "llama3:latest is available."
            ) from exc
        if "timed out" in reason.lower() or "timeout" in reason.lower():
            raise TimeoutError(
                f"Ollama did not respond within {TIMEOUT_SECS} seconds."
            ) from exc
        raise RuntimeError(f"Ollama connection error: {reason}") from exc
    except Exception as exc:
        msg = str(exc).lower()
        if "timed out" in msg or "timeout" in msg:
            raise TimeoutError(
                f"Ollama did not respond within {TIMEOUT_SECS} seconds."
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
        raise ValueError("Ollama returned an empty response.")
    return content

# ---------------------------------------------------------------------------
# JSON EXTRACTION
# ---------------------------------------------------------------------------

def _extract_json(raw: str) -> dict:
    text = raw.strip()

    # Strip code fences if present
    if "```" in text:
        lines = text.splitlines()
        inside, json_lines = False, []
        for line in lines:
            if not inside:
                if line.strip().startswith("```"):
                    inside = True
            else:
                if line.strip() == "```":
                    break
                json_lines.append(line)
        if json_lines:
            text = "\n".join(json_lines).strip()

    # Find outermost { ... }
    first = text.find("{")
    if first == -1:
        raise ValueError("No JSON object found in Ollama response.")

    depth, last = 0, first
    for i in range(first, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                last = i
                break

    try:
        return json.loads(text[first:last + 1])
    except json.JSONDecodeError as exc:
        raise ValueError(f"JSON parse error: {exc}") from exc

# ---------------------------------------------------------------------------
# VALIDATION
# ---------------------------------------------------------------------------

def _validate(spec: dict) -> list:
    errors = []
    if "topic" not in spec and "title" not in spec:
        errors.append("Missing: topic or title")
    if "scenes" not in spec:
        errors.append("Missing: scenes list")
    elif not isinstance(spec["scenes"], list) or len(spec["scenes"]) == 0:
        errors.append("scenes must be a non-empty list")
    return errors

# ---------------------------------------------------------------------------
# PUBLIC API
# ---------------------------------------------------------------------------

def generate_lesson_plan(topic: str) -> tuple:
    """
    Returns (lesson_spec_dict, elapsed_seconds).
    elapsed_seconds covers only the Ollama call — not connection overhead.
    Raises RuntimeError, TimeoutError, ValueError on failure.
    """
    prompt = build_planning_prompt(topic)

    start   = time.perf_counter()
    raw     = _call_ollama(prompt)
    elapsed = time.perf_counter() - start

    spec   = _extract_json(raw)
    errors = _validate(spec)
    if errors:
        raise ValueError("Invalid lesson spec:\n  " + "\n  ".join(errors))

    # Normalise: accept either "topic" or "title"
    if "topic" not in spec and "title" in spec:
        spec["topic"] = spec["title"]
    if "target_duration" not in spec:
        spec["target_duration"] = 75

    return spec, elapsed
