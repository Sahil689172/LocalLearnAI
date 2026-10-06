"""
LocalLearn AI - Robustness Regression Tests
---------------------------------------------
Covers the fixes introduced for the Hindi insertion-sort integration failure:

  1. Numeric strings are converted to integers in numeric scene fields
  2. Integer numeric fields remain integers (idempotent normalisation)
  3. Insertion sort cannot silently become binary search
  4. Insertion sort does not receive binary-search-specific scenes
  5. Insertion sort complexity is not incorrectly accepted as O(log n)
  6. Binary search still accepts numeric arrays correctly
  7. Hindi insertion-sort LessonSpec preserves language = "hi"
  8. Existing language tests continue to pass (spot-check)

NO network calls.  NO Ollama.  NO Manim rendering.
All tests use deterministic in-process fixture specs.

Run with:
    python -m pytest test_robustness.py -v
    -- or --
    python test_robustness.py
"""

import sys
import unittest

from lesson_planner import (
    _normalise_numeric_scene_data,
    _validate_topic_scene_consistency,
    _repair_topic_scene_consistency,
    _validate_complexity_consistency,
    _normalise_spec,
    _detect_algorithm,
    build_planning_prompt,
)
from language_codes import LanguageCode

# ---------------------------------------------------------------------------
# FIXTURE HELPERS
# ---------------------------------------------------------------------------

def _insertion_sort_spec(language: str = "en", *, bad_scene: bool = False) -> dict:
    """
    Minimal valid insertion-sort LessonSpec.

    When bad_scene=True the spec contains an array_search scene (the exact
    bug seen during the Hindi integration test) so repair/validation logic
    can be exercised.
    """
    scenes = [
        {"type": "title",      "text": "Insertion Sort", "duration": 4},
        {"type": "definition", "text": "Builds a sorted list one item at a time.",
         "duration": 6},
    ]
    if bad_scene:
        # This is the wrong scene type for insertion sort — it implements
        # binary search, not insertion sort.
        scenes.append({
            "type":     "array_search",
            "values":   [5, 2, 8, 3, 1, 6, 4],
            "target":   3,
            "duration": 30,
        })
    else:
        scenes.append({
            "type":     "array_sort",
            "values":   [5, 2, 8, 3, 1, 6, 4],
            "duration": 25,
        })

    scenes += [
        {"type": "complexity", "text": "Time complexity",
         "value": "O(n^2)", "duration": 7},
        {"type": "summary", "text": "Insertion Sort Summary",
         "points": ["Simple", "Efficient for small arrays"], "duration": 8},
    ]

    return {
        "topic":           "insertion sort",
        "language":        language,
        "target_duration": 75,
        "scenes":          scenes,
        "beats": [
            {
                "id":         "beat_1",
                "concept":    "introduction",
                "narration":  "Insertion sort builds a sorted array one element at a time.",
                "visual_text": "Introduction",
                "importance": "normal",
                "language":   language,
            }
        ],
    }


def _binary_search_spec(language: str = "en") -> dict:
    """Minimal valid binary-search LessonSpec with correct scene types."""
    return {
        "topic":           "binary search",
        "language":        language,
        "target_duration": 75,
        "scenes": [
            {"type": "title",        "text": "Binary Search", "duration": 4},
            {"type": "definition",   "text": "Search in a sorted array.",
             "duration": 6},
            {"type": "array_search", "values": [1, 3, 5, 7, 9],
             "target": 5, "duration": 30},
            {"type": "complexity",   "text": "Time complexity",
             "value": "O(log n)", "duration": 7},
            {"type": "summary",      "text": "Binary Search Summary",
             "points": ["Divide and conquer"], "duration": 8},
        ],
        "beats": [],
    }


def _string_values_scene() -> dict:
    """array_search scene where Ollama returned values as strings."""
    return {
        "type":     "array_search",
        "values":   ["5", "2", "8", "3", "1", "6", "4"],
        "target":   "3",
        "duration": "30",
    }


def _int_values_scene() -> dict:
    """array_search scene that already has correct integer values."""
    return {
        "type":     "array_search",
        "values":   [5, 2, 8, 3, 1, 6, 4],
        "target":   3,
        "duration": 30,
    }


# ===========================================================================
# TEST 1 — Numeric strings are converted to integers
# ===========================================================================

class TestNumericStringNormalisation(unittest.TestCase):
    """
    _normalise_numeric_scene_data must convert string-typed values/target/
    duration fields to the correct Python numeric types.
    """

    def setUp(self):
        self.raw_scene = _string_values_scene()
        self.normalised = _normalise_numeric_scene_data([self.raw_scene])[0]

    def test_values_converted_to_list_of_int(self):
        values = self.normalised["values"]
        self.assertIsInstance(values, list)
        for v in values:
            self.assertIsInstance(v, int,
                msg=f"Expected int, got {type(v).__name__}: {v!r}")

    def test_specific_values_are_correct(self):
        self.assertEqual(self.normalised["values"], [5, 2, 8, 3, 1, 6, 4])

    def test_target_converted_to_int(self):
        self.assertIsInstance(self.normalised["target"], int)
        self.assertEqual(self.normalised["target"], 3)

    def test_duration_converted_to_float(self):
        self.assertIsInstance(self.normalised["duration"], float)
        self.assertEqual(self.normalised["duration"], 30.0)

    def test_array_sort_values_also_normalised(self):
        sort_scene = {
            "type":   "array_sort",
            "values": ["7", "3", "9", "1"],
            "duration": "25",
        }
        result = _normalise_numeric_scene_data([sort_scene])[0]
        self.assertEqual(result["values"], [7, 3, 9, 1])
        for v in result["values"]:
            self.assertIsInstance(v, int)

    def test_textual_fields_not_touched(self):
        scene = {
            "type":     "title",
            "text":     "Insertion Sort",
            "duration": "4",
        }
        result = _normalise_numeric_scene_data([scene])[0]
        # text must not be modified
        self.assertEqual(result["text"], "Insertion Sort")
        # duration should be coerced to float
        self.assertIsInstance(result["duration"], float)

    def test_non_array_scene_type_does_not_get_values_coercion(self):
        """A definition scene has no values field — normaliser must not add one."""
        scene = {"type": "definition", "text": "Some text", "duration": "6"}
        result = _normalise_numeric_scene_data([scene])[0]
        self.assertNotIn("values", result)
        self.assertNotIn("target", result)

    def test_mixed_valid_invalid_values(self):
        """Non-numeric strings in values list are left as-is rather than crashing."""
        scene = {
            "type":   "array_search",
            "values": ["5", "bad", "3"],
            "target": "5",
        }
        result = _normalise_numeric_scene_data([scene])[0]
        # Valid elements should be converted
        self.assertEqual(result["values"][0], 5)
        self.assertEqual(result["values"][2], 3)
        # Bad element stays as-is
        self.assertEqual(result["values"][1], "bad")


# ===========================================================================
# TEST 2 — Integer numeric fields remain integers (idempotent)
# ===========================================================================

class TestNumericNormalisationIdempotent(unittest.TestCase):
    """
    Running _normalise_numeric_scene_data on already-correct data must not
    change any values.
    """

    def setUp(self):
        self.scene = _int_values_scene()
        # Deep copy the expected values before normalising
        self.expected_values = list(self.scene["values"])
        self.expected_target = self.scene["target"]
        self.normalised = _normalise_numeric_scene_data([dict(self.scene)])[0]

    def test_values_remain_int(self):
        for v in self.normalised["values"]:
            self.assertIsInstance(v, int)

    def test_values_unchanged(self):
        self.assertEqual(self.normalised["values"], self.expected_values)

    def test_target_remains_int(self):
        self.assertIsInstance(self.normalised["target"], int)
        self.assertEqual(self.normalised["target"], self.expected_target)

    def test_normalise_twice_is_idempotent(self):
        once  = _normalise_numeric_scene_data([dict(self.scene)])[0]
        twice = _normalise_numeric_scene_data([dict(once)])[0]
        self.assertEqual(once["values"], twice["values"])
        self.assertEqual(once["target"], twice["target"])


# ===========================================================================
# TEST 3 — Insertion sort cannot silently become binary search
# ===========================================================================

class TestInsertionSortCannotBecomeBinarySearch(unittest.TestCase):
    """
    When an insertion-sort spec contains array_search scenes (the binary-search
    scene type), _repair_topic_scene_consistency must replace them — the
    pipeline must never silently render the wrong algorithm.
    """

    def setUp(self):
        self.bad_spec = _insertion_sort_spec(bad_scene=True)

    def test_consistency_check_detects_bad_scene(self):
        errors = _validate_topic_scene_consistency(self.bad_spec)
        self.assertGreater(len(errors), 0,
            "Expected at least one consistency error for array_search in insertion-sort spec")

    def test_repair_removes_array_search(self):
        repaired_spec, messages = _repair_topic_scene_consistency(self.bad_spec)
        scene_types = [s.get("type") for s in repaired_spec["scenes"]]
        self.assertNotIn("array_search", scene_types,
            f"array_search must be removed after repair; got scene types: {scene_types}")

    def test_repair_replaces_with_array_sort(self):
        repaired_spec, messages = _repair_topic_scene_consistency(self.bad_spec)
        scene_types = [s.get("type") for s in repaired_spec["scenes"]]
        self.assertIn("array_sort", scene_types,
            "array_search should be replaced with array_sort for a sorting topic")

    def test_repair_emits_messages(self):
        _, messages = _repair_topic_scene_consistency(self.bad_spec)
        self.assertGreater(len(messages), 0,
            "Repair should emit at least one message describing what was fixed")

    def test_repair_is_deterministic(self):
        """Running repair twice on the same input produces the same result."""
        import copy
        spec_a = copy.deepcopy(self.bad_spec)
        spec_b = copy.deepcopy(self.bad_spec)
        repaired_a, _ = _repair_topic_scene_consistency(spec_a)
        repaired_b, _ = _repair_topic_scene_consistency(spec_b)
        types_a = [s.get("type") for s in repaired_a["scenes"]]
        types_b = [s.get("type") for s in repaired_b["scenes"]]
        self.assertEqual(types_a, types_b)

    def test_after_repair_consistency_check_passes(self):
        repaired_spec, _ = _repair_topic_scene_consistency(self.bad_spec)
        errors = _validate_topic_scene_consistency(repaired_spec)
        self.assertEqual(errors, [],
            f"Consistency errors remain after repair: {errors}")

    def test_detect_algorithm_identifies_insertion_sort(self):
        self.assertEqual(_detect_algorithm("insertion sort"), "insertion_sort")
        self.assertEqual(_detect_algorithm("Insertion Sort"), "insertion_sort")
        self.assertEqual(_detect_algorithm("explain insertion sort"), "insertion_sort")


# ===========================================================================
# TEST 4 — Insertion sort scenes do not contain binary-search-specific types
# ===========================================================================

class TestInsertionSortForbiddenScenes(unittest.TestCase):
    """
    array_search is the binary-search scene type and must be forbidden
    for all sorting algorithm topics.
    """

    def _bad_spec_for(self, topic: str) -> dict:
        return {
            "topic":   topic,
            "language": "en",
            "target_duration": 75,
            "scenes": [
                {"type": "array_search", "values": [3, 1, 4, 1, 5],
                 "target": 4, "duration": 30},
            ],
            "beats": [],
        }

    def test_insertion_sort_rejects_array_search(self):
        errors = _validate_topic_scene_consistency(
            self._bad_spec_for("insertion sort"))
        self.assertGreater(len(errors), 0)

    def test_selection_sort_rejects_array_search(self):
        errors = _validate_topic_scene_consistency(
            self._bad_spec_for("selection sort"))
        self.assertGreater(len(errors), 0)

    def test_bubble_sort_rejects_array_search(self):
        errors = _validate_topic_scene_consistency(
            self._bad_spec_for("bubble sort"))
        self.assertGreater(len(errors), 0)

    def test_merge_sort_rejects_array_search(self):
        errors = _validate_topic_scene_consistency(
            self._bad_spec_for("merge sort"))
        self.assertGreater(len(errors), 0)

    def test_quick_sort_rejects_array_search(self):
        errors = _validate_topic_scene_consistency(
            self._bad_spec_for("quicksort"))
        self.assertGreater(len(errors), 0)

    def test_good_insertion_sort_spec_passes(self):
        good_spec = _insertion_sort_spec(bad_scene=False)
        errors = _validate_topic_scene_consistency(good_spec)
        self.assertEqual(errors, [],
            f"Good insertion-sort spec should have no errors: {errors}")

    def test_error_message_names_the_offending_scene_type(self):
        errors = _validate_topic_scene_consistency(
            self._bad_spec_for("insertion sort"))
        self.assertTrue(any("array_search" in e for e in errors),
            f"Error message should mention 'array_search': {errors}")

    def test_error_message_names_the_topic(self):
        errors = _validate_topic_scene_consistency(
            self._bad_spec_for("insertion sort"))
        self.assertTrue(any("insertion sort" in e for e in errors),
            f"Error message should mention the topic: {errors}")


# ===========================================================================
# TEST 5 — Insertion sort complexity is not accepted as O(log n)
# ===========================================================================

class TestInsertionSortComplexity(unittest.TestCase):
    """
    _validate_complexity_consistency must flag O(log n) for insertion sort.
    O(n^2) must not be flagged.
    """

    def _spec_with_complexity(self, topic: str, complexity_value: str) -> dict:
        return {
            "topic":   topic,
            "language": "en",
            "target_duration": 75,
            "scenes": [
                {"type": "complexity", "text": "Time complexity",
                 "value": complexity_value, "duration": 7},
            ],
            "beats": [],
        }

    def test_log_n_flagged_for_insertion_sort(self):
        spec = self._spec_with_complexity("insertion sort", "O(log n)")
        warnings = _validate_complexity_consistency(spec)
        self.assertGreater(len(warnings), 0,
            "O(log n) should be flagged as wrong for insertion sort")

    def test_n_squared_not_flagged_for_insertion_sort(self):
        spec = self._spec_with_complexity("insertion sort", "O(n^2)")
        warnings = _validate_complexity_consistency(spec)
        self.assertEqual(warnings, [],
            "O(n^2) is correct for insertion sort and must not be flagged")

    def test_log_n_flagged_for_selection_sort(self):
        spec = self._spec_with_complexity("selection sort", "O(log n)")
        warnings = _validate_complexity_consistency(spec)
        self.assertGreater(len(warnings), 0)

    def test_log_n_flagged_for_bubble_sort(self):
        spec = self._spec_with_complexity("bubble sort", "O(log n)")
        warnings = _validate_complexity_consistency(spec)
        self.assertGreater(len(warnings), 0)

    def test_n_squared_flagged_for_merge_sort(self):
        spec = self._spec_with_complexity("merge sort", "O(n^2)")
        warnings = _validate_complexity_consistency(spec)
        self.assertGreater(len(warnings), 0,
            "O(n^2) should be flagged as wrong for merge sort")

    def test_log_n_correct_for_binary_search(self):
        spec = self._spec_with_complexity("binary search", "O(log n)")
        warnings = _validate_complexity_consistency(spec)
        self.assertEqual(warnings, [],
            "O(log n) is correct for binary search and must not be flagged")

    def test_warning_message_names_wrong_complexity(self):
        spec = self._spec_with_complexity("insertion sort", "O(log n)")
        warnings = _validate_complexity_consistency(spec)
        self.assertTrue(any("O(log n)" in w for w in warnings),
            f"Warning should name 'O(log n)': {warnings}")

    def test_warning_message_names_expected_complexity(self):
        spec = self._spec_with_complexity("insertion sort", "O(log n)")
        warnings = _validate_complexity_consistency(spec)
        self.assertTrue(any("O(n^2)" in w for w in warnings),
            f"Warning should name expected complexity 'O(n^2)': {warnings}")

    def test_formula_field_also_checked(self):
        """complexity check must cover the 'formula' field, not just 'value'."""
        spec = {
            "topic":   "insertion sort",
            "language": "en",
            "target_duration": 75,
            "scenes": [
                {"type": "formula", "text": "Time complexity",
                 "formula": "O(log n)", "duration": 7},
            ],
            "beats": [],
        }
        warnings = _validate_complexity_consistency(spec)
        self.assertGreater(len(warnings), 0,
            "O(log n) in a formula scene should also be flagged for insertion sort")


# ===========================================================================
# TEST 6 — Binary search accepts numeric arrays correctly
# ===========================================================================

class TestBinarySearchNumericArrays(unittest.TestCase):
    """
    Binary search is the one algorithm where array_search is VALID.
    Numeric normalisation must not break it, and consistency validation
    must accept it.
    """

    def setUp(self):
        self.spec = _binary_search_spec()

    def test_binary_search_array_search_scene_accepted(self):
        errors = _validate_topic_scene_consistency(self.spec)
        self.assertEqual(errors, [],
            f"array_search is valid for binary search: {errors}")

    def test_binary_search_integer_values_stay_integers(self):
        scenes = _normalise_numeric_scene_data(list(self.spec["scenes"]))
        array_scene = next(s for s in scenes if s["type"] == "array_search")
        for v in array_scene["values"]:
            self.assertIsInstance(v, int)

    def test_binary_search_target_stays_int(self):
        scenes = _normalise_numeric_scene_data(list(self.spec["scenes"]))
        array_scene = next(s for s in scenes if s["type"] == "array_search")
        self.assertIsInstance(array_scene["target"], int)
        self.assertEqual(array_scene["target"], 5)

    def test_binary_search_string_values_normalised(self):
        """Binary search with string values must also be normalised correctly."""
        spec = _binary_search_spec()
        for s in spec["scenes"]:
            if s["type"] == "array_search":
                s["values"] = ["1", "3", "5", "7", "9"]
                s["target"] = "5"
        scenes = _normalise_numeric_scene_data(spec["scenes"])
        array_scene = next(s for s in scenes if s["type"] == "array_search")
        self.assertEqual(array_scene["values"], [1, 3, 5, 7, 9])
        self.assertEqual(array_scene["target"], 5)

    def test_binary_search_complexity_not_flagged(self):
        warnings = _validate_complexity_consistency(self.spec)
        self.assertEqual(warnings, [],
            f"O(log n) is correct for binary search: {warnings}")

    def test_detect_algorithm_identifies_binary_search(self):
        self.assertEqual(_detect_algorithm("binary search"), "binary_search")
        self.assertEqual(_detect_algorithm("Binary Search"), "binary_search")
        self.assertEqual(_detect_algorithm("explain binary search"), "binary_search")


# ===========================================================================
# TEST 7 — Hindi insertion-sort LessonSpec preserves language = "hi"
# ===========================================================================

class TestHindiInsertionSort(unittest.TestCase):
    """
    After normalisation through _normalise_spec, a Hindi insertion-sort spec
    must have language="hi" throughout — never reverted to English.
    The repair pipeline must not change the language field.
    """

    def _hindi_insertion_sort_spec_bad(self) -> dict:
        """Simulates the exact spec seen in the failing integration test."""
        return {
            "topic":           "insertion sort",
            "language":        "hi",    # Ollama wrote hi correctly
            "target_duration": 75,
            "scenes": [
                {"type": "title",
                 "text": "इंसर्शन सॉर्ट", "duration": 4},
                {"type": "definition",
                 "text": "एक तत्व को उसकी सही जगह पर डालकर सूची को क्रमबद्ध करना।",
                 "duration": 6},
                # This is the wrong scene type — the bug from the integration test
                {"type":     "array_search",
                 "values":   ["5", "2", "8", "3", "1", "6", "4"],
                 "target":   "3",
                 "duration": "30"},
                {"type": "complexity",
                 "text": "समय जटिलता",
                 "value": "O(n^2)", "duration": 7},
                {"type": "summary",
                 "text": "सारांश",
                 "points": ["सरल", "छोटे ऐरे के लिए अच्छा"],
                 "duration": 8},
            ],
            "beats": [
                {
                    "id":          "beat_1",
                    "concept":     "introduction",
                    "narration":   "इंसर्शन सॉर्ट एक सरल और प्रभावी क्रमबद्धता एल्गोरिदम है।",
                    "visual_text": "परिचय",
                    "importance":  "normal",
                }
            ],
        }

    def setUp(self):
        self.raw_spec = self._hindi_insertion_sort_spec_bad()
        self.normalised = _normalise_spec(
            dict(self.raw_spec), LanguageCode.HI
        )

    def test_language_is_hi_after_normalise(self):
        self.assertEqual(self.normalised["language"], "hi")

    def test_language_is_hi_after_numeric_normalisation(self):
        """Numeric normalisation must not touch the language field."""
        scenes = _normalise_numeric_scene_data(self.normalised["scenes"])
        # language is on the spec, not on scenes — just verify spec unchanged
        self.assertEqual(self.normalised["language"], "hi")

    def test_language_is_hi_after_repair(self):
        repaired, _ = _repair_topic_scene_consistency(dict(self.normalised))
        self.assertEqual(repaired["language"], "hi")

    def test_beats_language_is_hi(self):
        for beat in self.normalised["beats"]:
            self.assertEqual(beat.get("language"), "hi",
                f"Beat language should be 'hi': {beat}")

    def test_hindi_text_preserved_after_normalisation(self):
        title_scene = self.normalised["scenes"][0]
        self.assertIn("इंसर्शन", title_scene["text"],
            "Hindi title text must be preserved after normalisation")

    def test_string_values_normalised_in_hindi_spec(self):
        """The Hindi spec had string values — they must be coerced to int."""
        array_scene = next(
            s for s in self.normalised["scenes"]
            if s["type"] == "array_search"
        )
        for v in array_scene["values"]:
            self.assertIsInstance(v, int,
                f"Value {v!r} should be int after normalisation")

    def test_string_target_normalised_in_hindi_spec(self):
        array_scene = next(
            s for s in self.normalised["scenes"]
            if s["type"] == "array_search"
        )
        self.assertIsInstance(array_scene["target"], int)
        self.assertEqual(array_scene["target"], 3)

    def test_repair_fixes_bad_scene_in_hindi_spec(self):
        repaired, messages = _repair_topic_scene_consistency(
            dict(self.normalised)
        )
        scene_types = [s.get("type") for s in repaired["scenes"]]
        self.assertNotIn("array_search", scene_types,
            f"array_search must be removed after repair; types: {scene_types}")
        self.assertGreater(len(messages), 0)

    def test_correct_complexity_not_flagged_in_hindi_spec(self):
        warnings = _validate_complexity_consistency(self.normalised)
        self.assertEqual(warnings, [],
            f"O(n^2) is correct for insertion sort; unexpected warnings: {warnings}")


# ===========================================================================
# TEST 8 — Existing language support is not broken (spot-check)
# ===========================================================================

class TestExistingLanguageSupportUnbroken(unittest.TestCase):
    """
    The robustness additions must not break any behaviour from Subphase 1.
    This is a targeted spot-check — the full Subphase 1 test suite in
    test_language_spec.py is the authoritative source.
    """

    def test_validate_language_en_still_works(self):
        from language_codes import validate_language
        lc = validate_language("en")
        self.assertEqual(lc, LanguageCode.EN)

    def test_validate_language_hi_still_works(self):
        from language_codes import validate_language
        lc = validate_language("hi")
        self.assertEqual(lc, LanguageCode.HI)

    def test_unsupported_language_still_rejected(self):
        from language_codes import validate_language
        with self.assertRaises(ValueError) as ctx:
            validate_language("fr")
        self.assertIn("fr", str(ctx.exception))

    def test_normalise_spec_stamps_correct_language_tamil(self):
        raw = {
            "topic":  "Binary Search",
            "scenes": [{"type": "title", "text": "Binary Search", "duration": 4}],
        }
        result = _normalise_spec(raw, LanguageCode.TA)
        self.assertEqual(result["language"], "ta")

    def test_normalise_spec_stamps_correct_language_telugu(self):
        raw = {
            "topic":  "Binary Search",
            "scenes": [{"type": "title", "text": "Binary Search", "duration": 4}],
        }
        result = _normalise_spec(raw, LanguageCode.TE)
        self.assertEqual(result["language"], "te")

    def test_normalise_spec_stamps_correct_language_marathi(self):
        raw = {
            "topic":  "Binary Search",
            "scenes": [{"type": "title", "text": "Binary Search", "duration": 4}],
        }
        result = _normalise_spec(raw, LanguageCode.MR)
        self.assertEqual(result["language"], "mr")

    def test_prompt_for_hindi_binary_search_still_contains_language_block(self):
        prompt = build_planning_prompt("Binary Search", LanguageCode.HI)
        self.assertIn("Hindi", prompt)
        self.assertIn("CRITICAL", prompt)
        self.assertIn("hi", prompt)

    def test_prompt_for_hindi_insertion_sort_contains_algorithm_block(self):
        prompt = build_planning_prompt("insertion sort", LanguageCode.HI)
        self.assertIn("ALGORITHM AUTHORITY", prompt)
        self.assertIn("insertion_sort", prompt)
        self.assertIn("array_search", prompt)   # listed as forbidden

    def test_prompt_for_hindi_insertion_sort_contains_language_block(self):
        prompt = build_planning_prompt("insertion sort", LanguageCode.HI)
        self.assertIn("Hindi", prompt)
        self.assertIn("CRITICAL", prompt)

    def test_prompt_for_english_binary_search_has_algorithm_block(self):
        prompt = build_planning_prompt("binary search", LanguageCode.EN)
        self.assertIn("ALGORITHM AUTHORITY", prompt)
        self.assertIn("binary_search", prompt)

    def test_numeric_normalisation_does_not_affect_non_array_scenes(self):
        """Title / definition / summary scenes must pass through unchanged."""
        scenes = [
            {"type": "title",      "text": "बाइनरी सर्च", "duration": "4"},
            {"type": "definition", "text": "Sorted array search.", "duration": "6"},
            {"type": "summary",    "text": "Summary", "points": ["p1"], "duration": "8"},
        ]
        result = _normalise_numeric_scene_data(scenes)
        # Text fields must be untouched
        self.assertEqual(result[0]["text"], "बाइनरी सर्च")
        self.assertEqual(result[1]["text"], "Sorted array search.")
        # Duration should be normalised to float
        for s in result:
            self.assertIsInstance(s["duration"], float)
        # No values or target injected
        for s in result:
            self.assertNotIn("values", s)
            self.assertNotIn("target", s)

    def test_unknown_topic_skips_algorithm_validation(self):
        """A topic with no recognised algorithm should not cause any errors."""
        spec = {
            "topic":   "photosynthesis",
            "language": "en",
            "target_duration": 75,
            "scenes": [
                {"type": "title",      "text": "Photosynthesis", "duration": 4},
                {"type": "definition", "text": "...", "duration": 6},
            ],
            "beats": [],
        }
        errors   = _validate_topic_scene_consistency(spec)
        warnings = _validate_complexity_consistency(spec)
        self.assertEqual(errors,   [])
        self.assertEqual(warnings, [])


# ===========================================================================
# RUNNER
# ===========================================================================

if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite  = unittest.TestSuite()

    test_classes = [
        TestNumericStringNormalisation,
        TestNumericNormalisationIdempotent,
        TestInsertionSortCannotBecomeBinarySearch,
        TestInsertionSortForbiddenScenes,
        TestInsertionSortComplexity,
        TestBinarySearchNumericArrays,
        TestHindiInsertionSort,
        TestExistingLanguageSupportUnbroken,
    ]

    for cls in test_classes:
        suite.addTests(loader.loadTestsFromTestCase(cls))

    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
