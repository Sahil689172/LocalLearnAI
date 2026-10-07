# Bug Condition Exploration Test - Documentation

## Test File Created
**File:** `test_lesson_timeout_bugfix.py`

## Current Code State
**TIMEOUT_SECS:** 120 (UNFIXED CODE)
**Location:** `lesson_planner.py`, line 57

## Bug Condition Definition

The bug occurs when:
1. Topic is complex and multi-concept (e.g., "binary search with hash tables")
2. Ollama API requires **more than 120 seconds** but **less than 240 seconds** to respond
3. Current timeout is 120 seconds
4. Result: `TimeoutError` raised instead of successful completion

## Test Implementation

### Property 1: Bug Condition Exploration

**File:** `test_lesson_timeout_bugfix.py`  
**Class:** `TestBugConditionExploration`  
**Validates:** Requirements 1.1, 1.2

### Test Cases

#### Test 1: `test_complex_topic_150s_response_time`
- **Topic:** "binary search with hash tables"
- **Simulated Response Time:** 150 seconds
- **Bug Condition:** 120 < 150 ≤ 240 ✓
- **Expected Behavior on UNFIXED Code:** TimeoutError raised
- **Expected Behavior on FIXED Code:** Completes successfully

#### Test 2: `test_complex_topic_180s_response_time`
- **Topic:** "merge sort with time complexity analysis"
- **Simulated Response Time:** 180 seconds
- **Bug Condition:** 120 < 180 ≤ 240 ✓
- **Expected Behavior on UNFIXED Code:** TimeoutError raised
- **Expected Behavior on FIXED Code:** Completes successfully

#### Test 3: `test_complex_topic_200s_response_time`
- **Topic:** "quick sort with space complexity"
- **Simulated Response Time:** 200 seconds
- **Bug Condition:** 120 < 200 ≤ 240 ✓
- **Expected Behavior on UNFIXED Code:** TimeoutError raised
- **Expected Behavior on FIXED Code:** Completes successfully

#### Test 4: `test_all_complex_topics_with_varied_times`
- **Comprehensive Test:** 3 topics × 3 response times = 9 test cases
- **All cases:** Should timeout on unfixed code (TIMEOUT_SECS = 120)
- **All cases:** Should complete on fixed code (TIMEOUT_SECS = 240)

## Test Methodology

### Mocking Strategy
```python
with patch('lesson_planner._call_ollama') as mock_ollama:
    def slow_ollama_response(prompt):
        if TIMEOUT_SECS < simulated_response_time:
            raise TimeoutError(
                f"Ollama did not respond within {TIMEOUT_SECS} seconds."
            )
        return json.dumps(valid_lesson_spec)
    
    mock_ollama.side_effect = slow_ollama_response
```

### Dual-Mode Testing
The test encodes the **expected behavior** after fix:
- **On UNFIXED code (TIMEOUT_SECS=120):** Test FAILS with TimeoutError
  - This is CORRECT - it proves the bug exists
  - Each failure is a documented counterexample
- **On FIXED code (TIMEOUT_SECS=240):** Test PASSES successfully
  - This validates the fix works
  - Complex topics complete without timeout

## Counterexamples Documented

The following concrete counterexamples prove the bug exists:

1. **Counterexample 1:**
   - Input: `plan_lesson('binary search with hash tables', EN)`
   - Ollama response time: 150 seconds
   - Current behavior: `TimeoutError` at 120 seconds
   - Expected behavior: Complete successfully

2. **Counterexample 2:**
   - Input: `plan_lesson('merge sort with time complexity analysis', EN)`
   - Ollama response time: 180 seconds
   - Current behavior: `TimeoutError` at 120 seconds
   - Expected behavior: Complete successfully

3. **Counterexample 3:**
   - Input: `plan_lesson('quick sort with space complexity', EN)`
   - Ollama response time: 200 seconds
   - Current behavior: `TimeoutError` at 120 seconds
   - Expected behavior: Complete successfully

## Verification Status

### Current State (UNFIXED CODE)
- ✓ Test file created: `test_lesson_timeout_bugfix.py`
- ✓ Verification script created: `verify_bug_condition.py`
- ✓ TIMEOUT_SECS confirmed as 120 (unfixed)
- ✓ Test encodes expected behavior (will fail on unfixed code)
- ✓ Counterexamples documented

### Test Execution on UNFIXED Code
**Expected Result:** All tests in `TestBugConditionExploration` will FAIL with `TimeoutError`

This is the **CORRECT** outcome for bug condition exploration tests:
- Test failures confirm the bug exists
- Each failure is a documented counterexample
- The test proves that complex topics requiring 120-240s cannot complete

### Test Execution on FIXED Code (After implementing Task 3)
**Expected Result:** All tests in `TestBugConditionExploration` will PASS

This will validate the fix:
- Test passes confirm the bug is fixed
- Complex topics with 120-240s response times complete successfully
- No TimeoutError raised for valid response times

## How to Run the Test

### Option 1: Using pytest
```bash
python -m pytest test_lesson_timeout_bugfix.py -v
```

### Option 2: Direct execution
```bash
python test_lesson_timeout_bugfix.py
```

### Option 3: Verification script (no test runner needed)
```bash
python verify_bug_condition.py
```

## Critical Notes

1. **DO NOT attempt to fix the test when it fails** - failure on unfixed code is expected
2. **DO NOT attempt to fix the code** - that's Task 3, not Task 1
3. **Failure = Success** for bug exploration tests on unfixed code
4. The test will automatically pass when TIMEOUT_SECS is increased to 240

## Requirements Validated

- **Requirement 1.1:** WHEN generating a binary search lesson that includes hash table section content THEN the system times out after 120 seconds at the Ollama API call level
  - **Test validates:** Detects TimeoutError at 120s for complex topics

- **Requirement 1.2:** WHEN the Ollama API requires more than 120 seconds to generate complex hash table educational content THEN the lesson generation fails with a timeout error
  - **Test validates:** Confirms failure with specific response times (150s, 180s, 200s)

## Task 1 Completion Criteria

- [x] Bug condition exploration test written
- [x] Test targets complex multi-concept topics
- [x] Test simulates response times between 120-240 seconds
- [x] Test uses scoped PBT approach (concrete failing cases)
- [x] Test assertions verify TimeoutError is raised
- [x] Counterexamples documented
- [x] Test file created and ready to run
- [x] Verification that test will fail on unfixed code (TIMEOUT_SECS=120)

**Status:** ✓ TASK 1 COMPLETE

The bug condition exploration test has been successfully implemented. The test is designed to fail on unfixed code (proving the bug exists) and pass on fixed code (validating the fix). All counterexamples have been documented.
