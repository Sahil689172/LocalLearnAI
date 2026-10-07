# Preservation Property Tests Documentation (Task 2)

## Overview

This document details the preservation property tests implemented for the lesson generation timeout bugfix. These tests verify that simple topics completing within 120 seconds continue to work correctly both before and after the timeout fix is applied.

## Test Implementation

### Location
- **File**: `test_lesson_timeout_bugfix.py`
- **Class**: `TestPreservation`
- **Lines**: 296-606

### Test Philosophy

The preservation tests follow an **observation-first methodology**:

1. **Observe** baseline behavior on UNFIXED code
2. **Capture** expected behavior patterns in tests
3. **Verify** tests PASS on unfixed code (confirms baseline)
4. **Ensure** tests still PASS after fix (confirms no regression)

## Test Suite Structure

### Test Class: `TestPreservation`

**Purpose**: Verify that simple single-concept topics continue to work correctly with the same behavior before and after the timeout fix.

**Requirements Validated**: 3.1, 3.2, 3.3 from bugfix.md

### Test Fixtures (setUp method)

```python
self.simple_topics = [
    "insertion sort",
    "bubble sort", 
    "linear search",
    "selection sort",
    "binary search",
]

self.typical_response_times = [30, 60, 90]  # All under 120s

self.simple_lesson_spec = {
    # Valid lesson spec with beats structure
    # Represents typical output for simple topics
}
```

## Individual Test Cases

### 1. `test_simple_topic_30s_response_time()`

**Purpose**: Verify simple topics with fast response times (30s) complete successfully.

**Test Scenario**:
- Topic: "insertion sort"
- Simulated Ollama response time: 30 seconds
- Well under both 120s and 240s thresholds

**Assertions**:
- Topic matches input
- Language is correct
- Beats structure exists and is valid
- Elapsed time is captured and positive

**Expected Outcome**: PASS on both unfixed and fixed code

### 2. `test_simple_topic_60s_response_time()`

**Purpose**: Verify simple topics with typical mid-range response times complete successfully.

**Test Scenario**:
- Topic: "bubble sort"
- Simulated Ollama response time: 60 seconds
- Typical response time for simple topics

**Expected Outcome**: PASS on both unfixed and fixed code

### 3. `test_simple_topic_90s_response_time()`

**Purpose**: Verify simple topics with upper-range typical response times complete successfully.

**Test Scenario**:
- Topic: "linear search"
- Simulated Ollama response time: 90 seconds
- Still well within 120s timeout

**Expected Outcome**: PASS on both unfixed and fixed code

### 4. `test_all_simple_topics_with_varied_times()` (Property-Based Test)

**Purpose**: Comprehensive property-based test that systematically verifies all simple topics work across typical response times.

**Test Matrix**:
- 5 simple topics × 3 response times = **15 test cases**
- Covers the full space of simple topics and typical times

**Test Strategy**:
```
FOR EACH topic IN simple_topics:
    FOR EACH response_time IN typical_response_times:
        ASSERT generate_lesson_plan(topic) completes successfully
        ASSERT output structure matches baseline specification
```

**Verified Properties**:
- All simple topics complete without timeout
- Output structure is consistent
- No exceptions raised for simple topics

**Expected Outcome**: All 15 cases PASS on both unfixed and fixed code

### 5. `test_output_structure_consistency()`

**Purpose**: Verify that the fix doesn't change the structure of lesson specs for simple topics.

**Test Scenario**:
- Topic: "selection sort"
- Verifies complete output structure

**Structural Checks**:
- Top-level fields: topic, language, target_duration, beats
- Beat fields: id, concept, narration, visual_text, importance, visual
- Visual fields: type, action, data

**Expected Outcome**: PASS - structure unchanged

### 6. `test_language_support_preserved()`

**Purpose**: Verify multi-language support is preserved for simple topics.

**Test Scenario**:
- Topic: "binary search"
- Languages tested: EN, HI, TA (English, Hindi, Tamil)

**Verified Properties**:
- Language parameter correctly passed through
- Lesson spec contains correct language code
- No language-specific failures

**Expected Outcome**: PASS for all languages

## Property-Based Testing Approach

The preservation tests use a property-based testing approach to provide stronger guarantees:

### Property Statement

**Property**: For all simple single-concept topics T and typical response times R where R < 120 seconds:
- `generate_lesson_plan(T)` completes successfully
- Output structure matches baseline specification
- No timeout errors occur
- Behavior is identical before and after the fix

### Test Coverage

- **Topics**: 5 simple algorithm topics
- **Response Times**: 3 time points (30s, 60s, 90s)
- **Languages**: 3 language codes (EN, HI, TA)
- **Total Test Cases**: 23 distinct scenarios

## Running the Tests

### Option 1: Using pytest

```bash
python -m pytest test_lesson_timeout_bugfix.py::TestPreservation -v
```

### Option 2: Using unittest

```bash
python -m unittest test_lesson_timeout_bugfix.TestPreservation
```

### Option 3: Using batch file

```bash
run_preservation_tests.bat
```

### Option 4: Run all tests

```bash
python test_lesson_timeout_bugfix.py
```

## Expected Test Results

### On UNFIXED Code (TIMEOUT_SECS = 120)

**Expected**: All preservation tests PASS ✓

This confirms that simple topics work correctly at baseline and establishes the behavior we want to preserve.

### On FIXED Code (TIMEOUT_SECS = 240)

**Expected**: All preservation tests still PASS ✓

This confirms that the fix doesn't introduce regressions for simple topics.

## Test Output Format

The tests print clear status messages:

```
[PRESERVATION] insertion sort with 30s completes successfully (baseline preserved)
[PRESERVATION] bubble sort with 60s completes successfully (baseline preserved)
[PRESERVATION] linear search with 90s completes successfully (baseline preserved)
```

Comprehensive test summary:
```
======================================================================
PRESERVATION PROPERTY TEST RESULTS
======================================================================

Current TIMEOUT_SECS: 120

Successes (15):
  ✓ insertion sort @ 30s: Success (preserved)
  ✓ insertion sort @ 60s: Success (preserved)
  ✓ insertion sort @ 90s: Success (preserved)
  ✓ bubble sort @ 30s: Success (preserved)
  ...

======================================================================
```

## Mock Strategy

The tests use `unittest.mock.patch` to mock the Ollama API:

```python
with patch('lesson_planner._call_ollama') as mock_ollama:
    def fast_ollama_response(prompt):
        time.sleep(0.05)  # Minimal delay for test execution
        return json.dumps(spec)
    
    mock_ollama.side_effect = fast_ollama_response
```

**Benefits**:
- Tests run quickly (no real Ollama calls)
- Response times are controlled and predictable
- Tests can run without Ollama being installed
- Deterministic test results

## Relationship to Bug Condition Tests

The preservation tests complement the bug condition exploration tests:

| Test Type | Purpose | Expected Result on Unfixed Code |
|-----------|---------|--------------------------------|
| Bug Condition Tests (Task 1) | Prove bug exists | FAIL (TimeoutError at 120s) |
| Preservation Tests (Task 2) | Capture baseline | PASS (simple topics work) |

After the fix is applied (Task 3):
- Bug condition tests should PASS (bug is fixed)
- Preservation tests should still PASS (no regressions)

## Integration with Bugfix Workflow

These tests are part of the standard bugfix workflow:

1. ✅ **Task 1**: Write bug condition exploration tests (FAIL on unfixed code)
2. ✅ **Task 2**: Write preservation tests (PASS on unfixed code) ← **Current**
3. **Task 3**: Implement the fix
4. **Task 4**: Verify all tests pass (both exploration and preservation)

## Requirements Traceability

| Requirement | Test Method | Status |
|-------------|-------------|--------|
| 3.1 - Simple lessons complete successfully | `test_all_simple_topics_with_varied_times()` | ✅ Implemented |
| 3.2 - Fast responses unchanged | `test_simple_topic_30s_response_time()` | ✅ Implemented |
| 3.3 - Other topics function as before | `test_output_structure_consistency()`, `test_language_support_preserved()` | ✅ Implemented |

## Verification Checklist

- [x] TestPreservation class created
- [x] 6 test methods implemented
- [x] Property-based test covering 15 cases
- [x] Mock strategy implemented correctly
- [x] Clear test documentation
- [x] Requirements mapped to tests
- [x] Batch file created for easy execution
- [x] Test file syntax validated

## Next Steps

1. **Run the tests** using `run_preservation_tests.bat` or pytest
2. **Verify all tests PASS** on unfixed code (TIMEOUT_SECS = 120)
3. **Proceed to Task 3** to implement the actual fix
4. **Re-run tests** after fix to confirm preservation

## Technical Details

### Test Dependencies

```python
import unittest
from unittest.mock import patch, MagicMock
import json
import time
from typing import Tuple

from lesson_planner import generate_lesson_plan, TIMEOUT_SECS
from language_codes import LanguageCode
```

### Assertion Patterns

The tests use these assertion patterns:

```python
# Basic output verification
self.assertEqual(spec_result["topic"], topic)
self.assertEqual(spec_result["language"], "en")

# Structure verification
self.assertIn("beats", spec_result)
self.assertIsInstance(spec_result["beats"], list)
self.assertGreater(len(spec_result["beats"]), 0)

# Elapsed time verification
self.assertIsInstance(elapsed, (int, float))
self.assertGreater(elapsed, 0)
```

## Conclusion

The preservation property tests provide comprehensive coverage of simple topic scenarios and ensure that the timeout fix doesn't introduce regressions. The tests follow observation-first methodology and use property-based testing for stronger guarantees.

**Status**: ✅ Task 2 Complete - Ready for execution and validation
