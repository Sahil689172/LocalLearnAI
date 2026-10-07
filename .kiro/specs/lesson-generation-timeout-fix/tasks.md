# Implementation Plan

- [x] 1. Write bug condition exploration test
  - **Property 1: Bug Condition** - Complex Topics Timeout at 120s
  - **CRITICAL**: This test MUST FAIL on unfixed code - failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the expected behavior - it will validate the fix when it passes after implementation
  - **GOAL**: Surface counterexamples that demonstrate the bug exists
  - **Scoped PBT Approach**: Scope the property to concrete failing cases: complex multi-concept topics (e.g., "binary search with hash tables") with mocked Ollama response times between 120-240 seconds
  - Test that `plan_lesson(topic, language)` times out for complex topics when Ollama takes 120-240 seconds to respond (from Bug Condition in design)
  - Mock Ollama API to simulate response times of 150s, 180s, 200s for topics like "binary search with hash tables", "merge sort with time complexity analysis", "quick sort with space complexity"
  - The test assertions should verify that TimeoutError is raised with unfixed code (validates bug exists)
  - Run test on UNFIXED code (TIMEOUT_SECS = 120)
  - **EXPECTED OUTCOME**: Test FAILS with TimeoutError (this is correct - it proves the bug exists)
  - Document counterexamples found: "plan_lesson('binary search with hash tables', EN) with 180s response time raises TimeoutError at 120s instead of completing successfully"
  - Mark task complete when test is written, run, and failure is documented
  - _Requirements: 1.1, 1.2_

- [x] 2. Write preservation property tests (BEFORE implementing fix)
  - **Property 2: Preservation** - Simple Topics Under 120s Unchanged
  - **IMPORTANT**: Follow observation-first methodology
  - Observe behavior on UNFIXED code for simple single-concept topics (e.g., "insertion sort", "bubble sort", "linear search")
  - Record generation times (typically <60 seconds) and output structure
  - Write property-based tests capturing observed behavior patterns: for all simple topics, generation completes in <120s with identical output structure (from Preservation Requirements in design)
  - Property-based testing generates many test cases for stronger guarantees that simple topics are unaffected
  - Mock Ollama API to simulate typical simple topic response times (30s, 60s, 90s)
  - Verify tests PASS on UNFIXED code (confirms baseline behavior to preserve)
  - Run tests on UNFIXED code (TIMEOUT_SECS = 120)
  - **EXPECTED OUTCOME**: Tests PASS (this confirms baseline behavior to preserve)
  - Mark task complete when tests are written, run, and passing on unfixed code
  - _Requirements: 3.1, 3.2, 3.3_

- [ ] 3. Fix for lesson generation timeout

  - [x] 3.1 Implement the fix
    - Open `c:\Users\hp\LocalLearn\lesson_planner.py`
    - Navigate to line 85
    - Change `TIMEOUT_SECS = 120` to `TIMEOUT_SECS = 240`
    - Update comment from `# Reduced from 240s - 2 minutes is sufficient` to `# Allows complex multi-concept topics to complete generation`
    - Save the file
    - _Bug_Condition: isBugCondition(input) where input.topic is complex multi-concept AND input.generationTime > 120 AND input.generationTime <= 240_
    - _Expected_Behavior: For all complex topics with 120-240s generation time, plan_lesson() completes successfully without TimeoutError and returns valid lesson spec JSON_
    - _Preservation: Simple topics completing under 120s must continue to work exactly as before with identical generation time and output quality_
    - _Requirements: 1.1, 1.2, 2.1, 2.2, 3.1, 3.2, 3.3, 3.4_

  - [x] 3.2 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - Complex Topics Complete Within 240s
    - **IMPORTANT**: Re-run the SAME test from task 1 - do NOT write a new test
    - The test from task 1 encodes the expected behavior
    - When this test passes, it confirms the expected behavior is satisfied
    - Run bug condition exploration test from step 1
    - Verify that `plan_lesson()` now completes successfully for complex topics with 120-240s mocked response times
    - **EXPECTED OUTCOME**: Test PASSES (confirms bug is fixed)
    - Verify no TimeoutError is raised for mocked times of 150s, 180s, 200s
    - Verify valid lesson spec JSON is returned
    - _Requirements: 2.1, 2.2_

  - [-] 3.3 Verify preservation tests still pass
    - **Property 2: Preservation** - Simple Topics Still Under 120s
    - **IMPORTANT**: Re-run the SAME tests from task 2 - do NOT write new tests
    - Run preservation property tests from step 2
    - Verify that simple topics still complete in <120s with identical behavior
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions)
    - Verify generation time for simple topics is unchanged
    - Verify output structure is identical to unfixed code behavior
    - Confirm all tests still pass after fix (no regressions)
    - _Requirements: 3.1, 3.2, 3.3_

- [~] 4. Checkpoint - Ensure all tests pass
  - Run all unit tests for lesson_planner.py
  - Run property-based tests for both bug condition and preservation
  - Verify no test failures or regressions
  - If any tests fail, investigate root cause before proceeding
  - Ask the user if questions arise
