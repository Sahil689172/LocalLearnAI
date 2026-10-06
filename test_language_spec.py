"""
LocalLearn AI - Subphase 1 Test Suite
----------------------------------------
Tests for language-aware LessonSpec, beats, validation, serialisation,
and scene builder integration.

Run with:
    python -m pytest test_language_spec.py -v
    -- or --
    python test_language_spec.py

NO network calls are made.  NO Ollama is required.  NO Manim rendering.
All tests operate on in-process data structures only.
"""

import json
import sys
import unittest

# ---------------------------------------------------------------------------
# Modules under test
# ---------------------------------------------------------------------------
from language_codes import (
    LanguageCode,
    DEFAULT_LANGUAGE,
    LANGUAGE_NAMES,
    LANGUAGE_NATIVE_NAMES,
    validate_language,
    language_display,
)
from lesson_planner import (
    build_planning_prompt,
    _normalise_spec,
    _validate,
    _validate_beats,
)
from scene_builder import build_manim_code, _label


# ---------------------------------------------------------------------------
# HELPERS — build minimal valid specs without touching Ollama
# ---------------------------------------------------------------------------

def _make_spec(language: str, *, include_beats: bool = True) -> dict:
    """
    Build a minimal but structurally valid LessonSpec dict for testing.
    Mirrors what _normalise_spec would return after an Ollama call.
    """
    beats = []
    if include_beats:
        beats = [
            {
                "id": "beat_1",
                "concept": "introduction",
                "narration": "This is the introduction narration.",
                "visual_text": "Introduction",
                "importance": "normal",
                "language": language,
            },
            {
                "id": "beat_2",
                "concept": "core_concept",
                "narration": "This is the core concept narration.",
                "visual_text": "Core Concept",
                "importance": "key",
                "language": language,
            },
        ]

    return {
        "topic": "Binary Search",
        "language": language,
        "target_duration": 75,
        "scenes": [
            {"type": "title",        "text": "Binary Search", "duration": 4},
            {"type": "definition",   "text": "Search in sorted array", "duration": 6},
            {"type": "array_search", "values": [1, 3, 5, 7, 9], "target": 5, "duration": 30},
        ],
        "beats": beats,
    }


def _make_hindi_spec() -> dict:
    spec = _make_spec("hi")
    spec["scenes"][0]["text"]    = "बाइनरी सर्च"
    spec["scenes"][1]["text"]    = "क्रमबद्ध ऐरे में खोज"
    spec["beats"][0]["narration"]  = (
        "बाइनरी सर्च एक ऐसी खोज तकनीक है जो क्रमबद्ध ऐरे में तेजी से काम करती है।"
    )
    spec["beats"][0]["visual_text"] = "परिचय"
    spec["beats"][1]["narration"]   = (
        "यह तकनीक हर चरण में खोज क्षेत्र को आधा कर देती है।"
    )
    spec["beats"][1]["visual_text"] = "मध्य तत्व"
    return spec


# ===========================================================================
# TEST 1 — English LessonSpec
# ===========================================================================

class TestEnglishSpec(unittest.TestCase):
    """LessonSpec with language='en' is accepted and well-formed."""

    def setUp(self):
        self.spec = _make_spec("en")

    def test_language_field_is_en(self):
        self.assertEqual(self.spec["language"], "en")

    def test_topic_present(self):
        self.assertIn("topic", self.spec)
        self.assertTrue(self.spec["topic"])

    def test_scenes_non_empty(self):
        self.assertIsInstance(self.spec["scenes"], list)
        self.assertGreater(len(self.spec["scenes"]), 0)

    def test_validate_passes(self):
        errors = _validate(self.spec)
        self.assertEqual(errors, [], msg=f"Unexpected errors: {errors}")

    def test_manim_code_contains_language_comment(self):
        code = build_manim_code(self.spec)
        self.assertIn("# Language: en", code)

    def test_manim_code_english_outro(self):
        code = build_manim_code(self.spec)
        self.assertIn("Learn", code)
        self.assertIn("Visualize", code)
        self.assertIn("Understand", code)


# ===========================================================================
# TEST 2 — Hindi LessonSpec
# ===========================================================================

class TestHindiSpec(unittest.TestCase):
    """LessonSpec with language='hi' carries Hindi content correctly."""

    def setUp(self):
        self.spec = _make_hindi_spec()

    def test_language_field_is_hi(self):
        self.assertEqual(self.spec["language"], "hi")

    def test_topic_present(self):
        self.assertIn("topic", self.spec)

    def test_scenes_non_empty(self):
        self.assertGreater(len(self.spec["scenes"]), 0)

    def test_validate_passes(self):
        errors = _validate(self.spec)
        self.assertEqual(errors, [])

    def test_hindi_title_text(self):
        title_scene = self.spec["scenes"][0]
        self.assertIn("बाइनरी", title_scene["text"])

    def test_manim_code_contains_language_comment(self):
        code = build_manim_code(self.spec)
        self.assertIn("# Language: hi", code)

    def test_manim_code_hindi_found_label(self):
        """array_search scene should embed the Hindi FOUND label."""
        code = build_manim_code(self.spec)
        self.assertIn("मिल गया", code)

    def test_manim_code_hindi_target_prefix(self):
        """array_search scene should use Hindi target prefix."""
        code = build_manim_code(self.spec)
        self.assertIn("लक्ष्य", code)

    def test_manim_code_hindi_outro(self):
        code = build_manim_code(self.spec)
        self.assertIn("सीखें", code)


# ===========================================================================
# TEST 3 — Tamil LessonSpec
# ===========================================================================

class TestTamilSpec(unittest.TestCase):
    """LessonSpec with language='ta' is accepted and produces Tamil labels."""

    def setUp(self):
        self.spec = _make_spec("ta")

    def test_language_field_is_ta(self):
        self.assertEqual(self.spec["language"], "ta")

    def test_validate_passes(self):
        errors = _validate(self.spec)
        self.assertEqual(errors, [])

    def test_manim_code_language_comment(self):
        code = build_manim_code(self.spec)
        self.assertIn("# Language: ta", code)

    def test_manim_code_tamil_found_label(self):
        code = build_manim_code(self.spec)
        self.assertIn("கண்டுபிடிக்கப்பட்டது", code)

    def test_manim_code_tamil_outro(self):
        code = build_manim_code(self.spec)
        self.assertIn("கற்றல்", code)


# ===========================================================================
# TEST 4 — Telugu LessonSpec
# ===========================================================================

class TestTeluguSpec(unittest.TestCase):
    """LessonSpec with language='te' produces Telugu labels."""

    def setUp(self):
        self.spec = _make_spec("te")

    def test_language_field_is_te(self):
        self.assertEqual(self.spec["language"], "te")

    def test_validate_passes(self):
        errors = _validate(self.spec)
        self.assertEqual(errors, [])

    def test_manim_code_language_comment(self):
        code = build_manim_code(self.spec)
        self.assertIn("# Language: te", code)

    def test_manim_code_telugu_found_label(self):
        code = build_manim_code(self.spec)
        self.assertIn("దొరికింది", code)

    def test_manim_code_telugu_outro(self):
        code = build_manim_code(self.spec)
        self.assertIn("నేర్చుకోండి", code)


# ===========================================================================
# TEST 5 — Marathi LessonSpec
# ===========================================================================

class TestMarathiSpec(unittest.TestCase):
    """LessonSpec with language='mr' produces Marathi labels."""

    def setUp(self):
        self.spec = _make_spec("mr")

    def test_language_field_is_mr(self):
        self.assertEqual(self.spec["language"], "mr")

    def test_validate_passes(self):
        errors = _validate(self.spec)
        self.assertEqual(errors, [])

    def test_manim_code_language_comment(self):
        code = build_manim_code(self.spec)
        self.assertIn("# Language: mr", code)

    def test_manim_code_marathi_found_label(self):
        code = build_manim_code(self.spec)
        self.assertIn("सापडले", code)

    def test_manim_code_marathi_outro(self):
        code = build_manim_code(self.spec)
        self.assertIn("शिका", code)


# ===========================================================================
# TEST 6 — Unsupported language rejection
# ===========================================================================

class TestUnsupportedLanguageRejection(unittest.TestCase):
    """validate_language() must raise ValueError for unsupported codes."""

    def _assert_rejected(self, code: str):
        with self.assertRaises(ValueError) as ctx:
            validate_language(code)
        msg = str(ctx.exception)
        # Message must name the bad code
        self.assertIn(code, msg)
        # Message must list the supported languages
        self.assertIn("en", msg)
        self.assertIn("hi", msg)
        self.assertIn("ta", msg)
        self.assertIn("te", msg)
        self.assertIn("mr", msg)

    def test_french_rejected(self):
        self._assert_rejected("fr")

    def test_german_rejected(self):
        self._assert_rejected("de")

    def test_garbage_rejected(self):
        self._assert_rejected("xyz")

    def test_empty_string_rejected(self):
        with self.assertRaises(ValueError):
            validate_language("")

    def test_valid_code_not_rejected(self):
        # Sanity: valid codes must NOT raise
        for code in ("en", "hi", "ta", "te", "mr"):
            result = validate_language(code)
            self.assertEqual(result.value, code)

    def test_case_insensitive_accepted(self):
        # Upper-case should normalise without error
        result = validate_language("HI")
        self.assertEqual(result, LanguageCode.HI)

    def test_error_message_format(self):
        """The error message must match the specified format."""
        with self.assertRaises(ValueError) as ctx:
            validate_language("fr")
        msg = str(ctx.exception)
        # Must contain the prescribed wording
        self.assertIn("Unsupported language", msg)
        self.assertIn("Supported languages", msg)


# ===========================================================================
# TEST 7 — Language preserved during serialisation / deserialisation
# ===========================================================================

class TestLanguageSerialisationRoundtrip(unittest.TestCase):
    """
    Language must survive JSON serialise → deserialise intact.
    LanguageCode is a str-enum so json.dumps works without a custom encoder.
    """

    def _roundtrip(self, lang_code: str) -> dict:
        spec = _make_spec(lang_code)
        serialised   = json.dumps(spec, ensure_ascii=False)
        deserialised = json.loads(serialised)
        return deserialised

    def test_english_roundtrip(self):
        rt = self._roundtrip("en")
        self.assertEqual(rt["language"], "en")

    def test_hindi_roundtrip(self):
        rt = self._roundtrip("hi")
        self.assertEqual(rt["language"], "hi")

    def test_tamil_roundtrip(self):
        rt = self._roundtrip("ta")
        self.assertEqual(rt["language"], "ta")

    def test_telugu_roundtrip(self):
        rt = self._roundtrip("te")
        self.assertEqual(rt["language"], "te")

    def test_marathi_roundtrip(self):
        rt = self._roundtrip("mr")
        self.assertEqual(rt["language"], "mr")

    def test_beats_survive_roundtrip(self):
        spec = _make_hindi_spec()
        serialised   = json.dumps(spec, ensure_ascii=False)
        deserialised = json.loads(serialised)
        self.assertIn("beats", deserialised)
        self.assertGreater(len(deserialised["beats"]), 0)

    def test_hindi_text_survives_roundtrip(self):
        spec = _make_hindi_spec()
        serialised   = json.dumps(spec, ensure_ascii=False)
        deserialised = json.loads(serialised)
        title_text = deserialised["scenes"][0]["text"]
        self.assertIn("बाइनरी", title_text)

    def test_language_enum_serialises_as_string(self):
        """LanguageCode (str-enum) must dump as a plain string, not an object."""
        lc = LanguageCode.HI
        dumped = json.dumps({"lang": lc})
        parsed = json.loads(dumped)
        self.assertEqual(parsed["lang"], "hi")
        self.assertIsInstance(parsed["lang"], str)

    def test_normalise_spec_stamps_correct_language(self):
        """
        _normalise_spec must overwrite whatever Ollama wrote with the
        user-chosen language — the language is the single source of truth.
        """
        raw_spec = {
            "topic": "Binary Search",
            "language": "en",          # Ollama "forgot" and wrote English
            "target_duration": 75,
            "scenes": [{"type": "title", "text": "...", "duration": 4}],
        }
        normalised = _normalise_spec(raw_spec, LanguageCode.HI)
        self.assertEqual(normalised["language"], "hi",
                         "language must be overridden by the user-chosen value")

    def test_normalise_spec_injects_language_into_beats(self):
        raw_spec = {
            "topic": "Binary Search",
            "language": "hi",
            "target_duration": 75,
            "scenes": [{"type": "title", "text": "...", "duration": 4}],
            "beats": [
                {
                    "id": "beat_1",
                    "concept": "intro",
                    "narration": "परिचय",
                    "visual_text": "परिचय",
                    "importance": "normal",
                    # language NOT yet present — normalise should inject it
                }
            ],
        }
        normalised = _normalise_spec(raw_spec, LanguageCode.HI)
        self.assertEqual(normalised["beats"][0]["language"], "hi")


# ===========================================================================
# TEST 8 — Beat structure
# ===========================================================================

class TestBeatStructure(unittest.TestCase):
    """Beats must carry all required fields with correct types."""

    def setUp(self):
        self.spec = _make_hindi_spec()
        self.beats = self.spec["beats"]

    def test_beats_is_list(self):
        self.assertIsInstance(self.beats, list)

    def test_at_least_one_beat(self):
        self.assertGreater(len(self.beats), 0)

    def test_each_beat_has_id(self):
        for beat in self.beats:
            self.assertIn("id", beat, f"Beat missing 'id': {beat}")
            self.assertIsInstance(beat["id"], str)
            self.assertTrue(beat["id"].strip())

    def test_each_beat_has_concept(self):
        for beat in self.beats:
            self.assertIn("concept", beat)
            self.assertIsInstance(beat["concept"], str)

    def test_each_beat_has_narration(self):
        for beat in self.beats:
            self.assertIn("narration", beat)
            self.assertIsInstance(beat["narration"], str)
            self.assertTrue(beat["narration"].strip(),
                            f"narration must not be empty: {beat}")

    def test_each_beat_has_visual_text(self):
        for beat in self.beats:
            self.assertIn("visual_text", beat)
            self.assertIsInstance(beat["visual_text"], str)

    def test_each_beat_has_importance(self):
        for beat in self.beats:
            self.assertIn("importance", beat)
            self.assertIn(beat["importance"], ("normal", "key"),
                          f"importance value invalid: {beat['importance']}")

    def test_beat_ids_are_ascii(self):
        """Beat IDs must be stable ASCII identifiers — not translated."""
        for beat in self.beats:
            bid = beat.get("id", "")
            self.assertTrue(
                bid.isascii(),
                f"Beat id '{bid}' must be ASCII — do not translate IDs"
            )

    def test_beat_concepts_are_ascii(self):
        """Beat concepts are internal slugs — must be ASCII."""
        for beat in self.beats:
            concept = beat.get("concept", "")
            self.assertTrue(
                concept.isascii(),
                f"Beat concept '{concept}' must be ASCII — do not translate concepts"
            )

    def test_beat_validation_warns_on_missing_field(self):
        incomplete_beats = [
            {"id": "beat_x", "concept": "test"}  # missing narration, visual_text, importance
        ]
        warnings = _validate_beats(incomplete_beats)
        self.assertGreater(len(warnings), 0)

    def test_beat_validation_clean_on_valid_beats(self):
        warnings = _validate_beats(self.beats)
        self.assertEqual(warnings, [],
                         f"Unexpected beat warnings: {warnings}")


# ===========================================================================
# TEST 9 — Narration field
# ===========================================================================

class TestNarrationField(unittest.TestCase):
    """Narration must be present, non-empty, and in the right language."""

    def _beats_for(self, lang_code: str) -> list:
        spec = _make_spec(lang_code)
        return spec["beats"]

    def test_english_beats_have_narration(self):
        for beat in self._beats_for("en"):
            self.assertIn("narration", beat)
            self.assertTrue(beat["narration"].strip())

    def test_hindi_beats_have_narration(self):
        for beat in _make_hindi_spec()["beats"]:
            self.assertIn("narration", beat)
            self.assertTrue(beat["narration"].strip())

    def test_hindi_narration_contains_devanagari(self):
        """Hindi narration must contain Devanagari script characters."""
        for beat in _make_hindi_spec()["beats"]:
            narration = beat["narration"]
            has_devanagari = any("\u0900" <= ch <= "\u097F" for ch in narration)
            self.assertTrue(
                has_devanagari,
                f"Hindi narration should contain Devanagari: '{narration}'"
            )

    def test_narration_is_distinct_from_visual_text(self):
        """
        Narration is a full sentence; visual_text is a short label.
        They should not be identical.
        """
        for beat in _make_hindi_spec()["beats"]:
            self.assertNotEqual(
                beat["narration"], beat["visual_text"],
                "narration and visual_text should not be identical"
            )

    def test_narration_longer_than_visual_text(self):
        """Narration (full sentence) should generally be longer than visual_text."""
        for beat in _make_hindi_spec()["beats"]:
            self.assertGreater(
                len(beat["narration"]), len(beat["visual_text"]),
                f"narration should be longer than visual_text: {beat}"
            )

    def test_narration_language_tag_matches_spec(self):
        """Each beat's language tag must match the top-level spec language."""
        for lang in ("en", "hi", "ta", "te", "mr"):
            spec = _make_spec(lang)
            for beat in spec["beats"]:
                self.assertEqual(
                    beat.get("language"), lang,
                    f"beat.language '{beat.get('language')}' != spec language '{lang}'"
                )


# ===========================================================================
# TEST 10 — Visual text field
# ===========================================================================

class TestVisualTextField(unittest.TestCase):
    """
    Visual text must be present in beats, and the scene builder must embed
    language-aware fallback labels (not hardcoded English) in generated code.
    """

    def test_each_beat_has_visual_text(self):
        for lang in ("en", "hi", "ta", "te", "mr"):
            with self.subTest(language=lang):
                spec = _make_spec(lang)
                for beat in spec["beats"]:
                    self.assertIn("visual_text", beat)
                    self.assertIsInstance(beat["visual_text"], str)

    def test_visual_text_is_short_label(self):
        """visual_text should be a short label, not a paragraph."""
        for beat in _make_hindi_spec()["beats"]:
            vt = beat["visual_text"]
            self.assertLess(len(vt), 60,
                            f"visual_text should be short: '{vt}'")

    def test_english_found_label_in_code(self):
        spec = _make_spec("en")
        code = build_manim_code(spec)
        self.assertIn("FOUND!", code)

    def test_hindi_found_label_in_code(self):
        spec = _make_spec("hi")
        code = build_manim_code(spec)
        self.assertIn("मिल गया", code)
        # Must NOT contain the English fallback when Hindi is chosen
        self.assertNotIn("FOUND!", code)

    def test_tamil_found_label_in_code(self):
        spec = _make_spec("ta")
        code = build_manim_code(spec)
        self.assertIn("கண்டுபிடிக்கப்பட்டது", code)

    def test_telugu_found_label_in_code(self):
        spec = _make_spec("te")
        code = build_manim_code(spec)
        self.assertIn("దొరికింది", code)

    def test_marathi_found_label_in_code(self):
        spec = _make_spec("mr")
        code = build_manim_code(spec)
        self.assertIn("सापडले", code)

    def test_internal_ids_not_translated(self):
        """
        concept_id / beat id must remain ASCII regardless of language.
        visual_text is translated; internal metadata is not.
        """
        for lang in ("hi", "ta", "te", "mr"):
            with self.subTest(language=lang):
                spec = _make_spec(lang)
                for beat in spec["beats"]:
                    self.assertTrue(
                        beat["id"].isascii(),
                        f"[{lang}] beat id must stay ASCII: '{beat['id']}'"
                    )
                    self.assertTrue(
                        beat["concept"].isascii(),
                        f"[{lang}] beat concept must stay ASCII: '{beat['concept']}'"
                    )

    def test_label_helper_fallback_to_english(self):
        """
        _label() must fall back to English for an unknown language code
        rather than raising or returning None/empty.
        """
        result = _label("found_label", "zz")   # "zz" not in the table
        self.assertEqual(result, "FOUND!",
                         "_label should fall back to English for unknown lang")

    def test_prompt_contains_language_instruction(self):
        """
        The Ollama planning prompt for Hindi must contain an explicit
        instruction to generate in Hindi — not translate from English.
        """
        prompt = build_planning_prompt("Binary Search", LanguageCode.HI)
        self.assertIn("Hindi", prompt)
        self.assertIn("hi", prompt)
        # Must tell Ollama to generate directly, not translate
        self.assertIn("CRITICAL", prompt)
        self.assertNotIn("translate from English", prompt.lower()
                         .replace("do not translate from english", ""))

    def test_prompt_english_neutral_phrasing(self):
        """
        The English prompt must NOT contain a CRITICAL translation warning
        (it uses neutral phrasing because English is the default).
        """
        prompt = build_planning_prompt("Binary Search", LanguageCode.EN)
        self.assertIn("English", prompt)
        # No alarming translation instruction needed for English
        self.assertNotIn("Do NOT generate in English first", prompt)


# ===========================================================================
# RUNNER
# ===========================================================================

if __name__ == "__main__":
    loader  = unittest.TestLoader()
    suite   = unittest.TestSuite()

    test_classes = [
        TestEnglishSpec,
        TestHindiSpec,
        TestTamilSpec,
        TestTeluguSpec,
        TestMarathiSpec,
        TestUnsupportedLanguageRejection,
        TestLanguageSerialisationRoundtrip,
        TestBeatStructure,
        TestNarrationField,
        TestVisualTextField,
    ]

    for cls in test_classes:
        suite.addTests(loader.loadTestsFromTestCase(cls))

    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
