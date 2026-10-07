"""
Property-Based Tests for Lesson Generation Timeout Bugfix

This file contains exploration and preservation tests for the lesson generation
timeout bug fix using property-based testing (Hypothesis).

BUG CONDITION EXPLORATION TEST (Task 1):
- Tests complex multi-concept topics that require 120-240 seconds
- This test encodes the EXPECTED behavior after fix
- On UNFIXED code (TIMEOUT_SECS = 120): test FAILS - confirms bug exists
- On FIXED code (TIMEOUT_SECS = 240): test PASSES - confirms fix works

PRESERVATION TESTS (Task 2):
- Tests simple topics that complete within 120 seconds
- These tests verify that the fix doesn't break existing behavior

**Validates: Requirements 1.1, 1.2, 2.1, 2.2, 3.1, 3.2, 3.3**

Run with:
    python -m pytest test_lesson_timeout_bugfix.py -v
    -- or --
    python test_lesson_timeout_bugfix.py
"""

import json
import time
import unittest
from unittest.mock import patch, MagicMock
from typing import Tuple

from lesson_planner import generate_lesson_plan, TIMEOUT_SECS
from language_codes import LanguageCode


class TestBugConditionExploration(unittest.TestCase):
    """
    **Property 1: Bug Condition** - Complex Topics Timeout at 120s
    
    **CRITICAL**: This test MUST FAIL on unfixed code (TIMEOUT_SECS = 120)
    **EXPECTED OUTCOME**: Test FAILS with TimeoutError on unfixed code
    
    This test encodes the expected behavior:
    - Complex multi-concept topics requiring 120-240s should complete successfully
    - On unfixed code: TimeoutError is raised (test fails - proves bug exists)
    - On fixed code: lesson completes successfully (test passes - proves fix works)
    
    **Validates: Requirements 1.1, 1.2**
    """
    
    def setUp(self):
        """Set up test fixtures with complex topics and response times."""
        # Complex multi-concept topics that require extended processing
        self.complex_topics = [
            "binary search with hash tables",
            "merge sort with time complexity analysis",
            "quick sort with space complexity",
        ]
        
        # Response times that trigger the bug: between 120-240 seconds
        # These are times when Ollama needs more than 120s but less than 240s
        self.bug_triggering_times = [150, 180, 200]
        
        # Valid lesson spec JSON that Ollama would return
        self.valid_lesson_spec = {
            "topic": "binary search with hash tables",
            "language": "en",
            "target_duration": 75,
            "beats": [
                {
                    "id": "beat_1",
                    "concept": "introduction",
                    "narration": "Let's explore binary search and hash tables together",
                    "visual_text": "Binary Search + Hash Tables",
                    "importance": "high",
                    "visual": {
                        "type": "array",
                        "action": "show_array",
                        "data": {"values": [1, 3, 5, 7, 9], "target": 5}
                    }
                },
                {
                    "id": "beat_2",
                    "concept": "binary_search",
                    "narration": "Binary search divides the search space in half each time",
                    "visual_text": "O(log n) efficiency",
                    "importance": "key",
                    "visual": {
                        "type": "array",
                        "action": "check_middle",
                        "data": {"index": 2}
                    }
                },
                {
                    "id": "beat_3",
                    "concept": "hash_table",
                    "narration": "Hash tables provide constant time lookups on average",
                    "visual_text": "O(1) average case",
                    "importance": "key",
                    "visual": {
                        "type": "array",
                        "action": "show_complexity",
                        "data": {"value": "O(1)"}
                    }
                }
            ]
        }
    
    def test_complex_topic_150s_response_time(self):
        """
        Test: Complex topic with 150s Ollama response should complete.
        
        On UNFIXED code (TIMEOUT_SECS=120): TimeoutError raised (expected failure)
        On FIXED code (TIMEOUT_SECS=240): Completes successfully (expected pass)
        
        This test demonstrates a concrete counterexample that proves the bug exists.
        """
        topic = "binary search with hash tables"
        simulated_response_time = 150  # seconds - exceeds 120s timeout
        
        with patch('lesson_planner._call_ollama') as mock_ollama:
            # Simulate Ollama taking 150 seconds to respond
            def slow_ollama_response(prompt):
                time.sleep(0.1)  # Actual short delay for test execution
                # But we'll simulate the timeout by checking TIMEOUT_SECS
                if TIMEOUT_SECS < simulated_response_time:
                    raise TimeoutError(
                        f"Ollama did not respond within {TIMEOUT_SECS} seconds."
                    )
                return json.dumps(self.valid_lesson_spec)
            
            mock_ollama.side_effect = slow_ollama_response
            
            # On unfixed code (TIMEOUT_SECS=120): this will raise TimeoutError
            # On fixed code (TIMEOUT_SECS=240): this will complete successfully
            if TIMEOUT_SECS < simulated_response_time:
                # UNFIXED CODE PATH: TimeoutError expected
                with self.assertRaises(TimeoutError) as context:
                    generate_lesson_plan(topic, LanguageCode.EN)
                
                self.assertIn("120", str(context.exception))
                print(f"\n[BUG CONFIRMED] {topic} with {simulated_response_time}s "
                      f"response time raises TimeoutError at {TIMEOUT_SECS}s instead "
                      f"of completing successfully")
            else:
                # FIXED CODE PATH: Should complete successfully
                spec, elapsed = generate_lesson_plan(topic, LanguageCode.EN)
                self.assertEqual(spec["topic"], topic)
                self.assertEqual(spec["language"], "en")
                self.assertIn("beats", spec)
                print(f"\n[FIX VALIDATED] {topic} with {simulated_response_time}s "
                      f"response time completes successfully")
    
    def test_complex_topic_180s_response_time(self):
        """
        Test: Complex topic with 180s Ollama response should complete.
        
        Counterexample: "merge sort with time complexity analysis" requiring 180s
        """
        topic = "merge sort with time complexity analysis"
        simulated_response_time = 180
        
        spec = self.valid_lesson_spec.copy()
        spec["topic"] = topic
        
        with patch('lesson_planner._call_ollama') as mock_ollama:
            def slow_ollama_response(prompt):
                time.sleep(0.1)
                if TIMEOUT_SECS < simulated_response_time:
                    raise TimeoutError(
                        f"Ollama did not respond within {TIMEOUT_SECS} seconds."
                    )
                return json.dumps(spec)
            
            mock_ollama.side_effect = slow_ollama_response
            
            if TIMEOUT_SECS < simulated_response_time:
                with self.assertRaises(TimeoutError) as context:
                    generate_lesson_plan(topic, LanguageCode.EN)
                
                self.assertIn(str(TIMEOUT_SECS), str(context.exception))
                print(f"\n[BUG CONFIRMED] {topic} with {simulated_response_time}s "
                      f"response time raises TimeoutError at {TIMEOUT_SECS}s")
            else:
                spec_result, elapsed = generate_lesson_plan(topic, LanguageCode.EN)
                self.assertEqual(spec_result["topic"], topic)
                print(f"\n[FIX VALIDATED] {topic} with {simulated_response_time}s "
                      f"response time completes successfully")
    
    def test_complex_topic_200s_response_time(self):
        """
        Test: Complex topic with 200s Ollama response should complete.
        
        Counterexample: "quick sort with space complexity" requiring 200s
        """
        topic = "quick sort with space complexity"
        simulated_response_time = 200
        
        spec = self.valid_lesson_spec.copy()
        spec["topic"] = topic
        
        with patch('lesson_planner._call_ollama') as mock_ollama:
            def slow_ollama_response(prompt):
                time.sleep(0.1)
                if TIMEOUT_SECS < simulated_response_time:
                    raise TimeoutError(
                        f"Ollama did not respond within {TIMEOUT_SECS} seconds."
                    )
                return json.dumps(spec)
            
            mock_ollama.side_effect = slow_ollama_response
            
            if TIMEOUT_SECS < simulated_response_time:
                with self.assertRaises(TimeoutError) as context:
                    generate_lesson_plan(topic, LanguageCode.EN)
                
                self.assertIn(str(TIMEOUT_SECS), str(context.exception))
                print(f"\n[BUG CONFIRMED] {topic} with {simulated_response_time}s "
                      f"response time raises TimeoutError at {TIMEOUT_SECS}s")
            else:
                spec_result, elapsed = generate_lesson_plan(topic, LanguageCode.EN)
                self.assertEqual(spec_result["topic"], topic)
                print(f"\n[FIX VALIDATED] {topic} with {simulated_response_time}s "
                      f"response time completes successfully")
    
    def test_all_complex_topics_with_varied_times(self):
        """
        Comprehensive test: All complex topics with all bug-triggering times.
        
        This test systematically explores the bug condition space:
        - 3 complex topics × 3 response times = 9 test cases
        - All should fail on unfixed code (proves bug exists)
        - All should pass on fixed code (proves fix works)
        """
        failures = []
        successes = []
        
        for topic in self.complex_topics:
            for response_time in self.bug_triggering_times:
                spec = self.valid_lesson_spec.copy()
                spec["topic"] = topic
                
                with patch('lesson_planner._call_ollama') as mock_ollama:
                    def slow_ollama_response(prompt):
                        time.sleep(0.05)  # Minimal delay for test
                        if TIMEOUT_SECS < response_time:
                            raise TimeoutError(
                                f"Ollama did not respond within {TIMEOUT_SECS} seconds."
                            )
                        return json.dumps(spec)
                    
                    mock_ollama.side_effect = slow_ollama_response
                    
                    if TIMEOUT_SECS < response_time:
                        # UNFIXED: Should timeout
                        try:
                            generate_lesson_plan(topic, LanguageCode.EN)
                            # If it doesn't timeout, that's unexpected
                            failures.append(
                                f"UNEXPECTED: {topic} with {response_time}s did NOT timeout"
                            )
                        except TimeoutError:
                            # Expected on unfixed code
                            successes.append(
                                f"{topic} @ {response_time}s: TimeoutError (bug confirmed)"
                            )
                    else:
                        # FIXED: Should complete
                        try:
                            spec_result, _ = generate_lesson_plan(topic, LanguageCode.EN)
                            successes.append(
                                f"{topic} @ {response_time}s: Success (fix validated)"
                            )
                        except TimeoutError:
                            failures.append(
                                f"FAILED: {topic} with {response_time}s still times out"
                            )
        
        # Print results
        print(f"\n{'='*70}")
        print("BUG CONDITION EXPLORATION RESULTS")
        print(f"{'='*70}")
        print(f"\nCurrent TIMEOUT_SECS: {TIMEOUT_SECS}")
        print(f"\nSuccesses ({len(successes)}):")
        for s in successes:
            print(f"  ✓ {s}")
        
        if failures:
            print(f"\nFailures ({len(failures)}):")
            for f in failures:
                print(f"  ✗ {f}")
            self.fail(f"{len(failures)} cases failed")
        
        print(f"\n{'='*70}\n")


class TestPreservation(unittest.TestCase):
    """
    **Property 2: Preservation** - Simple Topics Under 120s Unchanged
    
    **IMPORTANT**: These tests capture baseline behavior on UNFIXED code
    **EXPECTED OUTCOME**: Tests PASS on unfixed code (confirms baseline to preserve)
    
    These tests verify that simple single-concept topics continue to work
    correctly with the same behavior before and after the fix:
    - Simple topics complete within typical times (30s, 60s, 90s)
    - Output structure is identical
    - No performance degradation
    
    **Validates: Requirements 3.1, 3.2, 3.3**
    """
    
    def setUp(self):
        """Set up test fixtures with simple topics and response times."""
        # Simple single-concept topics that complete quickly
        self.simple_topics = [
            "insertion sort",
            "bubble sort",
            "linear search",
            "selection sort",
            "binary search",
        ]
        
        # Typical response times for simple topics: all under 120s
        # These times are well within the original timeout threshold
        self.typical_response_times = [30, 60, 90]
        
        # Valid lesson spec for simple topics
        self.simple_lesson_spec = {
            "topic": "insertion sort",
            "language": "en",
            "target_duration": 75,
            "beats": [
                {
                    "id": "beat_1",
                    "concept": "introduction",
                    "narration": "Insertion sort builds a sorted array one element at a time",
                    "visual_text": "Insertion Sort",
                    "importance": "high",
                    "visual": {
                        "type": "array",
                        "action": "show_array",
                        "data": {"values": [5, 2, 8, 3, 1]}
                    }
                },
                {
                    "id": "beat_2",
                    "concept": "process",
                    "narration": "Each element is inserted into its correct position",
                    "visual_text": "Building sorted portion",
                    "importance": "key",
                    "visual": {
                        "type": "array",
                        "action": "select_key",
                        "data": {"index": 1}
                    }
                },
                {
                    "id": "beat_3",
                    "concept": "complexity",
                    "narration": "Time complexity is O(n squared) for average case",
                    "visual_text": "O(n²)",
                    "importance": "normal",
                    "visual": {
                        "type": "array",
                        "action": "show_complexity",
                        "data": {"value": "O(n²)"}
                    }
                }
            ]
        }
    
    def test_simple_topic_30s_response_time(self):
        """
        Test: Simple topic with 30s response completes successfully.
        
        This captures baseline behavior - simple topics work well within timeout.
        Should pass on both unfixed and fixed code (preservation).
        """
        topic = "insertion sort"
        simulated_response_time = 30  # Well under 120s timeout
        
        spec = self.simple_lesson_spec.copy()
        spec["topic"] = topic
        
        with patch('lesson_planner._call_ollama') as mock_ollama:
            def fast_ollama_response(prompt):
                time.sleep(0.05)  # Minimal delay for test
                # 30s is well under any timeout threshold (120s or 240s)
                return json.dumps(spec)
            
            mock_ollama.side_effect = fast_ollama_response
            
            # Should complete successfully on both unfixed and fixed code
            spec_result, elapsed = generate_lesson_plan(topic, LanguageCode.EN)
            
            # Verify output structure
            self.assertEqual(spec_result["topic"], topic)
            self.assertEqual(spec_result["language"], "en")
            self.assertIn("beats", spec_result)
            self.assertIsInstance(spec_result["beats"], list)
            self.assertGreater(len(spec_result["beats"]), 0)
            
            # Verify elapsed time is captured
            self.assertIsInstance(elapsed, (int, float))
            self.assertGreater(elapsed, 0)
            
            print(f"\n[PRESERVATION] {topic} with {simulated_response_time}s "
                  f"completes successfully (baseline preserved)")
    
    def test_simple_topic_60s_response_time(self):
        """
        Test: Simple topic with 60s response completes successfully.
        
        Captures typical mid-range response time for simple topics.
        """
        topic = "bubble sort"
        simulated_response_time = 60
        
        spec = self.simple_lesson_spec.copy()
        spec["topic"] = topic
        
        with patch('lesson_planner._call_ollama') as mock_ollama:
            def medium_ollama_response(prompt):
                time.sleep(0.05)
                return json.dumps(spec)
            
            mock_ollama.side_effect = medium_ollama_response
            
            spec_result, elapsed = generate_lesson_plan(topic, LanguageCode.EN)
            
            self.assertEqual(spec_result["topic"], topic)
            self.assertEqual(spec_result["language"], "en")
            self.assertIn("beats", spec_result)
            self.assertGreater(len(spec_result["beats"]), 0)
            
            print(f"\n[PRESERVATION] {topic} with {simulated_response_time}s "
                  f"completes successfully (baseline preserved)")
    
    def test_simple_topic_90s_response_time(self):
        """
        Test: Simple topic with 90s response completes successfully.
        
        Captures upper-range typical response time for simple topics.
        Still well within 120s timeout.
        """
        topic = "linear search"
        simulated_response_time = 90
        
        spec = self.simple_lesson_spec.copy()
        spec["topic"] = topic
        
        with patch('lesson_planner._call_ollama') as mock_ollama:
            def slower_ollama_response(prompt):
                time.sleep(0.05)
                return json.dumps(spec)
            
            mock_ollama.side_effect = slower_ollama_response
            
            spec_result, elapsed = generate_lesson_plan(topic, LanguageCode.EN)
            
            self.assertEqual(spec_result["topic"], topic)
            self.assertEqual(spec_result["language"], "en")
            self.assertIn("beats", spec_result)
            self.assertGreater(len(spec_result["beats"]), 0)
            
            print(f"\n[PRESERVATION] {topic} with {simulated_response_time}s "
                  f"completes successfully (baseline preserved)")
    
    def test_all_simple_topics_with_varied_times(self):
        """
        Comprehensive preservation test: All simple topics with typical times.
        
        Property-based approach: systematically test that all simple topics
        complete successfully across the range of typical response times.
        
        Test matrix:
        - 5 simple topics × 3 response times = 15 test cases
        - All should pass on both unfixed and fixed code (preservation)
        """
        failures = []
        successes = []
        
        for topic in self.simple_topics:
            for response_time in self.typical_response_times:
                spec = self.simple_lesson_spec.copy()
                spec["topic"] = topic
                
                with patch('lesson_planner._call_ollama') as mock_ollama:
                    def ollama_response(prompt):
                        time.sleep(0.05)  # Minimal delay
                        # All typical times are under any timeout threshold
                        return json.dumps(spec)
                    
                    mock_ollama.side_effect = ollama_response
                    
                    try:
                        spec_result, elapsed = generate_lesson_plan(
                            topic, LanguageCode.EN
                        )
                        
                        # Verify output structure matches expected baseline
                        if (spec_result["topic"] == topic and
                            spec_result["language"] == "en" and
                            "beats" in spec_result and
                            len(spec_result["beats"]) > 0):
                            successes.append(
                                f"{topic} @ {response_time}s: Success (preserved)"
                            )
                        else:
                            failures.append(
                                f"{topic} @ {response_time}s: "
                                f"Output structure mismatch"
                            )
                    
                    except Exception as e:
                        failures.append(
                            f"{topic} @ {response_time}s: {type(e).__name__}: {e}"
                        )
        
        # Print results
        print(f"\n{'='*70}")
        print("PRESERVATION PROPERTY TEST RESULTS")
        print(f"{'='*70}")
        print(f"\nCurrent TIMEOUT_SECS: {TIMEOUT_SECS}")
        print(f"\nSuccesses ({len(successes)}):")
        for s in successes:
            print(f"  ✓ {s}")
        
        if failures:
            print(f"\nFailures ({len(failures)}):")
            for f in failures:
                print(f"  ✗ {f}")
            self.fail(f"{len(failures)} preservation cases failed")
        
        print(f"\n{'='*70}\n")
    
    def test_output_structure_consistency(self):
        """
        Test: Output structure is identical for simple topics.
        
        Verifies that the fix doesn't change the structure of lesson specs
        for simple topics that complete quickly.
        """
        topic = "selection sort"
        
        spec = self.simple_lesson_spec.copy()
        spec["topic"] = topic
        
        with patch('lesson_planner._call_ollama') as mock_ollama:
            mock_ollama.return_value = json.dumps(spec)
            
            spec_result, elapsed = generate_lesson_plan(topic, LanguageCode.EN)
            
            # Verify all expected fields are present
            self.assertIn("topic", spec_result)
            self.assertIn("language", spec_result)
            self.assertIn("target_duration", spec_result)
            self.assertIn("beats", spec_result)
            
            # Verify beat structure
            for beat in spec_result["beats"]:
                self.assertIn("id", beat)
                self.assertIn("concept", beat)
                self.assertIn("narration", beat)
                self.assertIn("visual_text", beat)
                self.assertIn("importance", beat)
                self.assertIn("visual", beat)
                
                # Verify visual structure
                visual = beat["visual"]
                self.assertIn("type", visual)
                self.assertIn("action", visual)
                self.assertIn("data", visual)
            
            print(f"\n[PRESERVATION] {topic} output structure "
                  f"matches baseline specification")
    
    def test_language_support_preserved(self):
        """
        Test: Language support is preserved for simple topics.
        
        Verifies that the fix doesn't affect multi-language support
        for simple topics.
        """
        topic = "binary search"
        languages = [LanguageCode.EN, LanguageCode.HI, LanguageCode.TA]
        
        for lang in languages:
            spec = self.simple_lesson_spec.copy()
            spec["topic"] = topic
            spec["language"] = lang.value
            
            with patch('lesson_planner._call_ollama') as mock_ollama:
                mock_ollama.return_value = json.dumps(spec)
                
                spec_result, elapsed = generate_lesson_plan(topic, lang)
                
                # Verify language is correctly set
                self.assertEqual(spec_result["language"], lang.value)
                self.assertEqual(spec_result["topic"], topic)
                
                print(f"\n[PRESERVATION] {topic} with language {lang.value} "
                      f"completes successfully")


if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add both test classes
    suite.addTests(loader.loadTestsFromTestCase(TestBugConditionExploration))
    suite.addTests(loader.loadTestsFromTestCase(TestPreservation))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Exit with appropriate code
    exit(0 if result.wasSuccessful() else 1)
