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

ROBUSTNESS ADDITIONS
--------------------
- _normalise_numeric_scene_data(): coerces string-typed numeric fields
  (values, target, duration) to the correct Python types before any
  downstream code sees them.
- build_planning_prompt(): now contains an explicit "algorithm authority"
  block so Ollama cannot substitute one algorithm for another, plus
  concise per-algorithm scene guidance to keep scenes correct.
- _validate_topic_scene_consistency(): detects binary-search-specific
  scenes being generated for non-binary-search topics and either repairs
  the spec deterministically or raises a clear ValueError.
- _validate_complexity_consistency(): warns when an obviously wrong
  complexity value is present for a known algorithm.
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
TIMEOUT_SECS = 240   # allow up to 4 minutes for high-quality planning

# ---------------------------------------------------------------------------
# ALGORITHM CLASSIFICATION TABLE
#
# Maps lowercase keyword substrings found in a topic string to a canonical
# algorithm family name.  Used by both the prompt builder (to inject
# algorithm-specific scene guidance) and the spec validator (to detect
# scene-type mismatches).
#
# Keys   : lowercase substrings — checked with ``in topic.lower()``
# Values : canonical family name (used as a dict key below)
# ---------------------------------------------------------------------------

_ALGO_KEYWORDS: list[tuple[str, str]] = [
    # sorting
    ("insertion sort",  "insertion_sort"),
    ("selection sort",  "selection_sort"),
    ("bubble sort",     "bubble_sort"),
    ("merge sort",      "merge_sort"),
    ("quick sort",      "quick_sort"),
    ("quicksort",       "quick_sort"),
    # searching
    ("binary search",   "binary_search"),
    ("linear search",   "linear_search"),
]

# Scene types that are ONLY valid for binary search.
# Any other algorithm should not use these.
_BINARY_SEARCH_ONLY_SCENES = {"array_search"}

# Per-algorithm: which scene types are appropriate (advisory — not exhaustive).
# scene_builder supports: title, definition, explanation, array_search,
#   array_sort, formula, comparison, complexity, summary
_ALGO_SCENE_GUIDANCE: dict[str, dict] = {
    "insertion_sort": {
        "preferred":    ["title", "definition", "explanation",
                         "array_sort", "complexity", "summary"],
        "forbidden":    ["array_search"],
        "complexity":   "O(n^2)",
        "description":  "insertion sort — builds sorted array one element at a time",
    },
    "selection_sort": {
        "preferred":    ["title", "definition", "explanation",
                         "array_sort", "complexity", "summary"],
        "forbidden":    ["array_search"],
        "complexity":   "O(n^2)",
        "description":  "selection sort — repeatedly selects the minimum element",
    },
    "bubble_sort": {
        "preferred":    ["title", "definition", "explanation",
                         "array_sort", "complexity", "summary"],
        "forbidden":    ["array_search"],
        "complexity":   "O(n^2)",
        "description":  "bubble sort — repeatedly swaps adjacent out-of-order elements",
    },
    "merge_sort": {
        "preferred":    ["title", "definition", "explanation",
                         "complexity", "summary"],
        "forbidden":    ["array_search"],
        "complexity":   "O(n log n)",
        "description":  "merge sort — divide-and-conquer, merges sorted halves",
    },
    "quick_sort": {
        "preferred":    ["title", "definition", "explanation",
                         "complexity", "summary"],
        "forbidden":    ["array_search"],
        "complexity":   "O(n log n)",
        "description":  "quick sort — divide-and-conquer using a pivot element",
    },
    "binary_search": {
        "preferred":    ["title", "definition", "explanation",
                         "array_search", "complexity", "summary"],
        "forbidden":    [],
        "complexity":   "O(log n)",
        "description":  "binary search — halves the search space on each step",
    },
    "linear_search": {
        "preferred":    ["title", "definition", "explanation",
                         "complexity", "summary"],
        "forbidden":    ["array_search"],
        "complexity":   "O(n)",
        "description":  "linear search — scans each element sequentially",
    },
}


def _detect_algorithm(topic: str) -> str | None:
    """
    Return the canonical algorithm family for *topic*, or None if unknown.

    Checks are ordered from most-specific to least-specific so that
    "insertion sort" is matched before a hypothetical bare "sort".
    """
    t = topic.lower()
    for keyword, family in _ALGO_KEYWORDS:
        if keyword in t:
            return family
    return None

# ---------------------------------------------------------------------------
# PROMPT
# ---------------------------------------------------------------------------

def build_planning_prompt(topic: str, language: LanguageCode) -> str:
    """
    Build the Ollama planning prompt for topic and language.
    
    Generates a structured lesson with beats, where each beat contains:
    - Educational narration in the selected language
    - Concrete visual plan with specific actions
    
    Quality over speed — takes up to 240 seconds if needed.
    """
    lang_display = LANGUAGE_NAMES[language]
    lang_native  = LANGUAGE_NATIVE_NAMES[language]
    lang_code    = language.value

    # Language instruction
    if language == LanguageCode.EN:
        language_instruction = (
            "Language: English (en)\n"
            "Generate all narration and visual labels in English."
        )
    else:
        language_instruction = (
            f"Selected language: {lang_display} ({lang_code})\n"
            f"Native name: {lang_native}\n"
            "\n"
            f"CRITICAL: Generate ALL narration and visual_text DIRECTLY in {lang_display}.\n"
            f"Do NOT generate in English first. Do NOT translate.\n"
            f"Write educational content natively in {lang_display}.\n"
            "JSON keys, action names, and algorithm identifiers remain in English."
        )

    # Algorithm-specific guidance
    algo_family = _detect_algorithm(topic)
    if algo_family and algo_family in _ALGO_SCENE_GUIDANCE:
        guidance    = _ALGO_SCENE_GUIDANCE[algo_family]
        complexity  = guidance["complexity"]
        description = guidance["description"]
        
        # Build visual action examples specific to this algorithm
        if algo_family == "insertion_sort":
            visual_examples = """
Example visual plans for INSERTION SORT:
{
  "visual": {
    "type": "array",
    "action": "show_array",
    "data": {"values": [5, 2, 8, 3, 1]}
  }
}
{
  "visual": {
    "type": "array",
    "action": "select_key",
    "data": {"index": 1}
  }
}
{
  "visual": {
    "type": "array",
    "action": "compare",
    "data": {"compare_with": 0}
  }
}
{
  "visual": {
    "type": "array",
    "action": "shift",
    "data": {"indices": [0]}
  }
}
{
  "visual": {
    "type": "array",
    "action": "insert",
    "data": {"index": 0, "value": 2}
  }
}
{
  "visual": {
    "type": "array",
    "action": "mark_sorted",
    "data": {"sorted_until": 2}
  }
}
{
  "visual": {
    "type": "array",
    "action": "show_complexity",
    "data": {"value": "O(n²)"}
  }
}"""
        elif algo_family == "binary_search":
            visual_examples = """
Example visual plans for BINARY SEARCH:
{
  "visual": {
    "type": "array",
    "action": "show_array",
    "data": {"values": [1, 3, 5, 7, 9], "target": 5}
  }
}
{
  "visual": {
    "type": "array",
    "action": "check_middle",
    "data": {"index": 2}
  }
}
{
  "visual": {
    "type": "array",
    "action": "found",
    "data": {"index": 2}
  }
}
{
  "visual": {
    "type": "array",
    "action": "eliminate_half",
    "data": {"start": 0, "end": 2}
  }
}
{
  "visual": {
    "type": "array",
    "action": "show_complexity",
    "data": {"value": "O(log n)"}
  }
}"""
        else:
            visual_examples = """
Use appropriate visual actions for the algorithm.
For sorting: show_array, compare, swap, mark_sorted, show_complexity
For searching: show_array, check_middle, found, eliminate_half"""
        
        algorithm_instruction = (
            f"\n"
            f"ALGORITHM: {algo_family}\n"
            f"Description: {description}\n"
            f"Time complexity: {complexity}\n"
            f"\n"
            f"{visual_examples}\n"
        )
    else:
        algorithm_instruction = (
            f"\nGenerate educational beats for: {topic}\n"
        )

    return (
        "You are LocalLearn AI's high-quality lesson planner.\n"
        f"Create a structured 60-120 second educational video about:\n"
        f"\n    {topic}\n\n"
        "---\n"
        f"{language_instruction}\n"
        "---\n"
        f"{algorithm_instruction}"
        "\n"
        "OUTPUT FORMAT — JSON ONLY:\n"
        "{\n"
        '  "topic": "...",\n'
        f'  "language": "{lang_code}",\n'
        '  "algorithm": "insertion_sort",  // if applicable\n'
        '  "target_duration": 90,\n'
        '  "learning_objectives": ["...", "..."],\n'
        '  "beats": [\n'
        '    {\n'
        '      "id": "beat_1",\n'
        '      "concept": "introduction",\n'
        f'      "narration": "<full sentence in {lang_display}>",\n'
        f'      "visual_text": "<short label in {lang_display}>",\n'
        '      "importance": "high",\n'
        '      "visual": {\n'
        '        "type": "array",  // or "text", "diagram"\n'
        '        "action": "show_array",  // concrete action\n'
        '        "data": {"values": [5, 2, 8, 3, 1]},  // action-specific\n'
        '        "emphasis": [1]  // optional: indices to highlight\n'
        '      }\n'
        '    },\n'
        '    // ... 6-12 beats total\n'
        '  ]\n'
        '}\n'
        "\n"
        "CRITICAL RULES:\n"
        "1. Return ONLY valid JSON. No markdown fences. No ```json. No explanatory text before or after. The very first character of your response must be { and the very last must be }.\n"
        "2. Generate 6-12 beats that teach the concept step-by-step.\n"
        f"3. All narration and visual_text MUST be in {lang_display}.\n"
        "4. Visual plans MUST be concrete:\n"
        '   - Good: {"action": "select_key", "data": {"index": 1}}\n'
        '   - Bad:  {"action": "show concept", "data": {}}\n'
        "5. Each beat narration is ONE complete sentence.\n"
        "6. Beat IDs: beat_1, beat_2, ...\n"
        "7. Concepts: introduction, definition, step_1, step_2, ..., complexity, summary\n"
        "8. Visual actions must match the algorithm (see examples above).\n"
        f"9. For {topic}, use time complexity: {_ALGO_SCENE_GUIDANCE.get(algo_family, {}).get('complexity', 'appropriate value')}\n"
        "10. Do NOT mix algorithms (e.g., binary search for sorting).\n"
        "\n"
        "Quality is more important than speed. Take your time.\n"
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
            "num_predict": 2400,  # beats+visual plans need ~1500-2500 tokens
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
    """
    Robustly extract the outermost JSON object from an Ollama response.

    Handles:
    - Pure JSON
    - JSON wrapped in ```json ... ``` or ``` ... ``` fences
    - JSON preceded or followed by explanatory prose
    - Trailing commas inside objects/arrays (best-effort via re)
    - Windows-style single-quote JSON is NOT accepted (never eval)

    Raises ValueError with a clear message if extraction fails.
    """
    import re

    text = raw.strip()

    # ----------------------------------------------------------------
    # Step 1: strip markdown code fences
    # Handles ```json, ```JSON, ``` (any fence opener)
    # ----------------------------------------------------------------
    fence_re = re.compile(r"```[a-zA-Z]*\n(.*?)```", re.DOTALL)
    fence_match = fence_re.search(text)
    if fence_match:
        text = fence_match.group(1).strip()

    # ----------------------------------------------------------------
    # Step 2: find the first '{' and scan for the matching '}'
    # Uses a depth counter — safe, no eval.
    # ----------------------------------------------------------------
    first = text.find("{")
    if first == -1:
        raise ValueError(
            "No JSON object found in Ollama response.\n"
            f"Response preview: {raw[:200]!r}"
        )

    depth = 0
    last  = -1
    in_string  = False
    escape_next = False

    for i in range(first, len(text)):
        ch = text[i]

        if escape_next:
            escape_next = False
            continue

        if ch == "\\" and in_string:
            escape_next = True
            continue

        if ch == '"' and not escape_next:
            in_string = not in_string
            continue

        if in_string:
            continue

        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                last = i
                break

    if last == -1:
        raise ValueError(
            "Unmatched braces in Ollama JSON response.\n"
            f"Response preview: {raw[:200]!r}"
        )

    candidate = text[first : last + 1]

    # ----------------------------------------------------------------
    # Step 3: try strict parse first
    # ----------------------------------------------------------------
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        pass

    # ----------------------------------------------------------------
    # Step 4: best-effort cleanup — remove trailing commas
    # Only touches commas before } or ] — safe transformation.
    # ----------------------------------------------------------------
    cleaned = re.sub(r",\s*([}\]])", r"\1", candidate)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"JSON parse error after cleanup: {exc}\n"
            f"Candidate (first 400 chars): {candidate[:400]!r}"
        ) from exc


# ---------------------------------------------------------------------------
# SPEC VALIDATION
# ---------------------------------------------------------------------------

def _validate(spec: dict) -> list:
    errors = []
    if "topic" not in spec and "title" not in spec:
        errors.append("Missing: topic or title")
    
    # New structure: beats (preferred)
    # Legacy support: scenes (still allowed)
    has_beats = "beats" in spec and isinstance(spec["beats"], list) and len(spec["beats"]) > 0
    has_scenes = "scenes" in spec and isinstance(spec["scenes"], list) and len(spec["scenes"]) > 0
    
    if not has_beats and not has_scenes:
        errors.append("Missing: beats or scenes list (must be non-empty)")
    
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
        
        # Check required fields
        missing = required - beat.keys()
        if missing:
            warnings.append(f"Beat {i} ({beat.get('id','?')}): missing fields {missing}")
        
        # Check importance value
        imp = beat.get("importance")
        if imp and imp not in valid_importance:
            warnings.append(
                f"Beat {i} ({beat.get('id','?')}): "
                f"importance '{imp}' should be 'normal' or 'key'"
            )
        
        # Validate visual plan if present
        visual = beat.get("visual")
        if visual:
            if not isinstance(visual, dict):
                warnings.append(f"Beat {i} ({beat.get('id','?')}): visual must be a dict")
                continue
            
            # Check required visual fields
            if "type" not in visual:
                warnings.append(f"Beat {i} ({beat.get('id','?')}): visual missing 'type'")
            if "action" not in visual:
                warnings.append(f"Beat {i} ({beat.get('id','?')}): visual missing 'action'")
            if "data" not in visual:
                warnings.append(f"Beat {i} ({beat.get('id','?')}): visual missing 'data'")
            elif not isinstance(visual.get("data"), dict):
                warnings.append(f"Beat {i} ({beat.get('id','?')}): visual.data must be a dict")
    
    return warnings


# ---------------------------------------------------------------------------
# NUMERIC SCENE DATA NORMALISATION
# ---------------------------------------------------------------------------

# Scene types that carry numeric array/target fields
_NUMERIC_ARRAY_SCENES = {"array_search", "array_sort"}


def _normalise_numeric_scene_data(scenes: list) -> list:
    """
    Coerce string-typed numeric fields in scene dicts to correct Python types.

    Ollama occasionally returns numeric values as JSON strings, e.g.:
        "values": ["5", "2", "8"]   instead of  "values": [5, 2, 8]
        "target": "3"               instead of  "target": 3

    This helper fixes those in-place and returns the same list.

    Only fields that are semantically numeric are touched:
        - ``values``   in array_search / array_sort  → list[int]
        - ``target``   in array_search               → int
        - ``duration`` in any scene                  → float

    Normal textual fields (text, heading, narration, …) are never touched.
    """
    for scene in scenes:
        if not isinstance(scene, dict):
            continue

        scene_type = scene.get("type", "")

        # --- duration (every scene type) ---
        if "duration" in scene:
            try:
                scene["duration"] = float(scene["duration"])
            except (TypeError, ValueError):
                pass  # leave malformed value; validator will catch it

        # --- numeric array fields ---
        if scene_type in _NUMERIC_ARRAY_SCENES:
            # values: coerce each element to int
            if "values" in scene and isinstance(scene["values"], list):
                coerced = []
                for v in scene["values"]:
                    try:
                        coerced.append(int(v))
                    except (TypeError, ValueError):
                        coerced.append(v)  # keep as-is; validator will catch it
                scene["values"] = coerced

            # target: coerce to int
            if "target" in scene:
                try:
                    scene["target"] = int(scene["target"])
                except (TypeError, ValueError):
                    pass

    return scenes


# ---------------------------------------------------------------------------
# ALGORITHM / TOPIC SCENE-MISMATCH VALIDATION
# ---------------------------------------------------------------------------

def _validate_topic_scene_consistency(spec: dict) -> list:
    """
    Detect scenes that are algorithmically inconsistent with the topic.

    Returns a list of error strings.  An empty list means the spec is clean.

    Current checks:
    - A sorting topic (insertion/selection/bubble/merge/quick sort) must NOT
      contain ``array_search`` scenes.  Those scenes implement binary search
      and would silently render the wrong algorithm.
    """
    topic      = spec.get("topic", "")
    scenes     = spec.get("scenes", [])
    algo_family = _detect_algorithm(topic)
    errors     = []

    if algo_family is None:
        return errors   # unknown algorithm — no opinion

    guidance = _ALGO_SCENE_GUIDANCE.get(algo_family, {})
    forbidden = set(guidance.get("forbidden", []))

    if not forbidden:
        return errors

    bad_scenes = [
        (i + 1, s.get("type"))
        for i, s in enumerate(scenes)
        if isinstance(s, dict) and s.get("type") in forbidden
    ]

    if bad_scenes:
        bad_desc = ", ".join(f"scene {n} ({t!r})" for n, t in bad_scenes)
        errors.append(
            f"Topic '{topic}' ({algo_family}) contains forbidden scene type(s): "
            f"{bad_desc}. "
            f"These scene types are not valid for {algo_family}. "
            f"Forbidden types for this algorithm: {sorted(forbidden)}"
        )

    return errors


def _repair_topic_scene_consistency(spec: dict) -> tuple[dict, list]:
    """
    Attempt a deterministic repair of scene-type mismatches.

    Strategy: replace forbidden scene types with ``array_sort`` for sorting
    algorithms (the correct scene type for sorting visualisation), keeping
    the values field if present.

    Returns (repaired_spec, list_of_repair_messages).
    """
    topic       = spec.get("topic", "")
    algo_family = _detect_algorithm(topic)
    messages    = []

    if algo_family is None:
        return spec, messages

    guidance  = _ALGO_SCENE_GUIDANCE.get(algo_family, {})
    forbidden = set(guidance.get("forbidden", []))

    # Sorting algorithms: safe replacement is array_sort
    sorting_families = {
        "insertion_sort", "selection_sort", "bubble_sort",
        "merge_sort", "quick_sort",
    }

    for i, scene in enumerate(spec.get("scenes", [])):
        if not isinstance(scene, dict):
            continue
        stype = scene.get("type")
        if stype in forbidden:
            if algo_family in sorting_families:
                # Keep values if present, drop target (not needed for sort)
                repaired_scene = {
                    "type":     "array_sort",
                    "duration": scene.get("duration", 25),
                }
                if "values" in scene:
                    repaired_scene["values"] = scene["values"]
                spec["scenes"][i] = repaired_scene
                messages.append(
                    f"  [REPAIR] Scene {i + 1}: replaced forbidden '{stype}' "
                    f"with 'array_sort' for topic '{topic}'"
                )
            else:
                # For non-sorting algorithms, replace with explanation
                spec["scenes"][i] = {
                    "type":     "explanation",
                    "text":     scene.get("text", topic),
                    "points":   [],
                    "duration": scene.get("duration", 8),
                }
                messages.append(
                    f"  [REPAIR] Scene {i + 1}: replaced forbidden '{stype}' "
                    f"with 'explanation' for topic '{topic}'"
                )

    return spec, messages


# ---------------------------------------------------------------------------
# COMPLEXITY CONSISTENCY CHECK
# ---------------------------------------------------------------------------

def _validate_complexity_consistency(spec: dict) -> list:
    """
    Warn (non-fatal) when a formula/complexity scene carries an obviously
    incorrect complexity value for the detected algorithm.

    Returns a list of warning strings (empty = all clear).
    """
    topic       = spec.get("topic", "")
    algo_family = _detect_algorithm(topic)
    warnings    = []

    if algo_family is None:
        return warnings

    guidance         = _ALGO_SCENE_GUIDANCE.get(algo_family, {})
    expected_complexity = guidance.get("complexity")
    if not expected_complexity:
        return warnings

    # Pairs of (algo_family, wrong_complexity) that are clearly wrong
    # and should be flagged.
    _WRONG_COMPLEXITY: dict[str, list[str]] = {
        "insertion_sort": ["O(log n)", "O(log n) "],
        "selection_sort": ["O(log n)"],
        "bubble_sort":    ["O(log n)"],
        "merge_sort":     ["O(n^2)", "O(log n)"],
        "quick_sort":     ["O(n^2)", "O(log n)"],
        "linear_search":  ["O(log n)"],
    }

    wrong_values = _WRONG_COMPLEXITY.get(algo_family, [])
    if not wrong_values:
        return warnings

    for i, scene in enumerate(spec.get("scenes", [])):
        if not isinstance(scene, dict):
            continue
        stype = scene.get("type")
        if stype not in ("formula", "complexity"):
            continue

        # Check both "formula" and "value" fields
        for field in ("formula", "value"):
            val = scene.get(field, "").strip()
            if val in wrong_values:
                warnings.append(
                    f"  [WARN] Scene {i + 1} ({stype}): "
                    f"complexity '{val}' is incorrect for {algo_family}. "
                    f"Expected: {expected_complexity}"
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
    - Coerces string-typed numeric fields in visual plans to correct Python types.
    - Normalises ``importance`` values ("high"/"key" → "key", others → "normal").
    """
    # Normalise topic key
    if "topic" not in spec and "title" in spec:
        spec["topic"] = spec["title"]

    # Language is the single source of truth — always override with the
    # value the user explicitly chose; never trust what Ollama wrote.
    spec["language"] = language.value

    # Defaults
    if "target_duration" not in spec:
        spec["target_duration"] = 90

    # Ensure beats list exists
    if "beats" not in spec or not isinstance(spec["beats"], list):
        spec["beats"] = []

    # Process each beat
    for beat in spec["beats"]:
        if not isinstance(beat, dict):
            continue
        
        # Inject language
        beat["language"] = language.value
        
        # Normalise importance
        imp = beat.get("importance", "normal")
        if imp in ("high", "key"):
            beat["importance"] = "key"
        else:
            beat["importance"] = "normal"
        
        # Process visual plan if present
        visual = beat.get("visual")
        if isinstance(visual, dict):
            data = visual.get("data")
            if isinstance(data, dict):
                # Coerce numeric fields to correct types
                
                # values: list of strings → list of ints
                if "values" in data and isinstance(data["values"], list):
                    coerced = []
                    for v in data["values"]:
                        try:
                            coerced.append(int(v))
                        except (TypeError, ValueError):
                            coerced.append(v)
                    data["values"] = coerced
                
                # target: string → int
                if "target" in data:
                    try:
                        data["target"] = int(data["target"])
                    except (TypeError, ValueError):
                        pass
                
                # index: string → int
                if "index" in data:
                    try:
                        data["index"] = int(data["index"])
                    except (TypeError, ValueError):
                        pass
                
                # indices: list of strings → list of ints
                if "indices" in data and isinstance(data["indices"], list):
                    coerced = []
                    for idx in data["indices"]:
                        try:
                            coerced.append(int(idx))
                        except (TypeError, ValueError):
                            coerced.append(idx)
                    data["indices"] = coerced
                
                # compare_with: string → int
                if "compare_with" in data:
                    try:
                        data["compare_with"] = int(data["compare_with"])
                    except (TypeError, ValueError):
                        pass
                
                # sorted_until: string → int
                if "sorted_until" in data:
                    try:
                        data["sorted_until"] = int(data["sorted_until"])
                    except (TypeError, ValueError):
                        pass
                
                # start, end: strings → ints
                for field in ("start", "end"):
                    if field in data:
                        try:
                            data[field] = int(data[field])
                        except (TypeError, ValueError):
                            pass
            
            # emphasis: list of strings → list of ints
            emphasis = visual.get("emphasis")
            if isinstance(emphasis, list):
                coerced = []
                for e in emphasis:
                    try:
                        coerced.append(int(e))
                    except (TypeError, ValueError):
                        coerced.append(e)
                visual["emphasis"] = coerced

    # Legacy support: maintain scenes list if present
    if "scenes" in spec and isinstance(spec["scenes"], list):
        spec["scenes"] = _normalise_numeric_scene_data(spec["scenes"])

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

    # --- Algorithm / topic scene-mismatch check ---
    # First attempt a deterministic repair; if it cannot be fixed, fail.
    consistency_errors = _validate_topic_scene_consistency(spec)
    if consistency_errors:
        spec, repair_messages = _repair_topic_scene_consistency(spec)
        for msg in repair_messages:
            print(msg)
        # Re-validate after repair
        remaining_errors = _validate_topic_scene_consistency(spec)
        if remaining_errors:
            raise ValueError(
                "Lesson spec contains scenes inconsistent with the topic "
                "and could not be automatically repaired:\n  "
                + "\n  ".join(remaining_errors)
            )

    # --- Complexity consistency (non-fatal warnings) ---
    complexity_warnings = _validate_complexity_consistency(spec)
    for w in complexity_warnings:
        print(w)

    # --- Beat structure warnings (non-fatal) ---
    beat_warnings = _validate_beats(spec["beats"])
    for w in beat_warnings:
        print(f"  [WARN] Beat validation: {w}")

    return spec, elapsed
