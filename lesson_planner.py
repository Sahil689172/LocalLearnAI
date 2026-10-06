"""
LocalLearn AI - Lesson Planner
--------------------------------
Makes ONE compact Ollama call to get a structured JSON lesson spec.
Ollama decides WHAT to teach. Python decides HOW to animate it.

The prompt is deliberately short so llama3:latest responds quickly.

SUBPHASE 1 ADDITIONS
---------------------
- Accepts a ``language`` parameter (LanguageCode or string code).
- Language is validated and stored as the top-level ``"language"`` key in
  the returned spec — this is the single source of truth for all downstream
  pipeline stages.
- The Ollama prompt instructs the model to generate ALL user-facing text
  (title, scene text, narration, labels) DIRECTLY in the selected language.
  It does NOT generate English first and translate later.
- The spec now includes a ``"beats"`` list.  Each beat is one small
  synchronised teaching unit that carries:
      id          — stable internal identifier  (always English/ASCII)
      concept     — short English slug for the concept  (internal metadata)
      narration   — one sentence in the selected language
      visual_text — the visible on-screen label in the selected language
      importance  — "normal" | "key"
  Beats are language-independent in structure but language-native in content.
"""

import json
import time
import urllib.request
import urllib.error

from language_codes import (
    LanguageCode,
    DEFAULT_LANGUAGE,
    LANGUAGE_NAMES,
    LANGUAGE_NATIVE_NAMES,
    validate_language,
)

OLLAMA_URL   = "http://localhost:11434/api/generate"
MODEL        = "llama3:latest"
TIMEOUT_SECS = 300   # increased from 120 — Hindi/multilingual planning can take longer

# ---------------------------------------------------------------------------
# PROMPT
# ---------------------------------------------------------------------------

def build_planning_prompt(topic: str, language: LanguageCode) -> str:
    """
    Build the Ollama planning prompt for the given topic and language.

    The prompt explicitly instructs Ollama to generate the lesson DIRECTLY
    in the selected language — not in English with a subsequent translation.
    Technical identifiers, JSON keys, and internal metadata remain in English.
    """
    lang_display = LANGUAGE_NAMES[language]
    lang_native  = LANGUAGE_NATIVE_NAMES[language]
    lang_code    = language.value

    # Compose the language instruction block that is injected into the prompt.
    # For English we use a neutral phrasing; for all other languages we are
    # explicit that the model must write in that language directly.
    if language == LanguageCode.EN:
        language_instruction = (
            "Language: English (en)\n"
            "Generate all user-facing text in English."
        )
    else:
        language_instruction = (
            f"Selected language: {lang_display}\n"
            f"Language code: {lang_code}\n"
            f"Native name: {lang_native}\n"
            "\n"
            f"CRITICAL: Generate ALL user-facing text DIRECTLY in {lang_display}.\n"
            "Do NOT generate in English first.\n"
            "Do NOT translate from English.\n"
            f"Write titles, scene text, narration, visual labels, and\n"
            f"explanations natively in {lang_display} from the start.\n"
            "Technical JSON keys, internal IDs, and enum values must remain\n"
            "in English (ASCII). Only human-readable content is translated."
        )

    return (
        "You are the lesson planner for LocalLearn AI.\n"
        "Create a compact JSON lesson specification for a 60-90 second "
        "educational animation about:\n"
        f"\n    {topic}\n\n"
        "---\n"
        f"{language_instruction}\n"
        "---\n"
        "\n"
        "Rules:\n"
        "- Return ONLY valid JSON. No markdown. No ```json fences. "
        "No explanation.\n"
        "- Use 5-8 scenes maximum.\n"
        "- Do NOT generate Python, Manim code, or animation instructions.\n"
        "- Keep text fields SHORT (one sentence each).\n"
        "- The \"language\" field MUST be set to the language code exactly.\n"
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
        "Additionally include a top-level \"beats\" list with 3-6 beats.\n"
        "Each beat is ONE small teaching unit:\n"
        "{\n"
        '  "id": "beat_1",\n'
        '  "concept": "introduction",\n'
        f'  "narration": "<one sentence in {lang_display}>",\n'
        f'  "visual_text": "<short label in {lang_display}>",\n'
        '  "importance": "normal"\n'
        "}\n"
        "Rules for beats:\n"
        "- id and concept MUST be ASCII/English identifiers.\n"
        f"- narration and visual_text MUST be in {lang_display}.\n"
        '- importance is either "normal" or "key".\n'
        "\n"
        "Output format:\n"
        "{\n"
        '  "topic": "...",\n'
        f'  "language": "{lang_code}",\n'
        '  "target_duration": 75,\n'
        '  "scenes": [ ... ],\n'
        '  "beats": [ ... ]\n'
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
            "num_predict": 800,   # slightly larger than before to fit beats
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
# SPEC VALIDATION
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


def _validate_beats(beats: list) -> list:
    """
    Validate the structure of each beat in the beats list.
    Returns a list of warning strings (non-fatal).
    """
    warnings = []
    required = {"id", "concept", "narration", "visual_text", "importance"}
    valid_importance = {"normal", "key"}

    for i, beat in enumerate(beats):
        if not isinstance(beat, dict):
            warnings.append(f"Beat {i}: not a dict")
            continue
        missing = required - beat.keys()
        if missing:
            warnings.append(f"Beat {i} ({beat.get('id','?')}): missing fields {missing}")
        imp = beat.get("importance")
        if imp and imp not in valid_importance:
            warnings.append(
                f"Beat {i} ({beat.get('id','?')}): "
                f"importance '{imp}' should be 'normal' or 'key'"
            )
    return warnings


# ---------------------------------------------------------------------------
# SPEC NORMALISATION
# ---------------------------------------------------------------------------

def _normalise_spec(spec: dict, language: LanguageCode) -> dict:
    """
    Apply defaults and normalise the spec returned by Ollama.

    - Ensures ``topic`` key exists (falls back to ``title``).
    - Ensures ``language`` is always the value the user requested,
      regardless of what Ollama wrote (Ollama may misquote).
    - Ensures ``target_duration`` exists.
    - Ensures ``beats`` exists (empty list if Ollama omitted it).
    - Injects ``language`` into every beat for downstream convenience.
    """
    # Normalise topic key
    if "topic" not in spec and "title" in spec:
        spec["topic"] = spec["title"]

    # Language is the single source of truth — always override with the
    # value the user explicitly chose; never trust what Ollama wrote.
    spec["language"] = language.value

    # Defaults
    if "target_duration" not in spec:
        spec["target_duration"] = 75

    # Ensure beats list exists
    if "beats" not in spec or not isinstance(spec["beats"], list):
        spec["beats"] = []

    # Inject language into each beat for downstream convenience
    for beat in spec["beats"]:
        if isinstance(beat, dict):
            beat["language"] = language.value

    return spec


# ---------------------------------------------------------------------------
# PUBLIC API
# ---------------------------------------------------------------------------

def generate_lesson_plan(
    topic: str,
    language: str | LanguageCode = DEFAULT_LANGUAGE,
) -> tuple:
    """
    Generate a language-aware lesson plan via Ollama.

    Parameters
    ----------
    topic : str
        The educational topic, e.g. "Binary Search".
    language : str | LanguageCode, optional
        A supported language code ("en", "hi", "ta", "te", "mr") or the
        corresponding LanguageCode enum member.
        Defaults to ``DEFAULT_LANGUAGE`` (English).

    Returns
    -------
    (lesson_spec_dict, elapsed_seconds)
        ``elapsed_seconds`` covers only the Ollama call time.
        The returned dict always contains the keys:
            "topic", "language", "target_duration", "scenes", "beats"

    Raises
    ------
    ValueError
        If the language code is unsupported or the spec is structurally invalid.
    RuntimeError
        If Ollama is unreachable or returns an error.
    TimeoutError
        If Ollama does not respond within TIMEOUT_SECS.
    """
    # Validate and normalise the language code
    lang = validate_language(str(language)) if not isinstance(language, LanguageCode) else language

    prompt = build_planning_prompt(topic, lang)

    start   = time.perf_counter()
    raw     = _call_ollama(prompt)
    elapsed = time.perf_counter() - start

    spec   = _extract_json(raw)
    errors = _validate(spec)
    if errors:
        raise ValueError("Invalid lesson spec:\n  " + "\n  ".join(errors))

    spec = _normalise_spec(spec, lang)

    # Non-fatal beat validation — print warnings but do not abort
    beat_warnings = _validate_beats(spec["beats"])
    for w in beat_warnings:
        print(f"  [WARN] Beat validation: {w}")

    return spec, elapsed
