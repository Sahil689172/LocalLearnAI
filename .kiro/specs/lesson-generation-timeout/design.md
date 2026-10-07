# Lesson Generation Timeout Bugfix Design

## Overview

This bugfix addresses a timeout issue in lesson generation where complex topics (e.g., "binary search with hash tables") fail to complete within the current 120-second timeout limit. The lesson planner makes a single Ollama API call to generate a structured JSON lesson spec, and complex topics with multiple algorithmic concepts require more generation time than simpler, single-concept topics.

The fix increases the `TIMEOUT_SECS` constant from 120 seconds to 240 seconds in `lesson_planner.py`, allowing sufficient time for Ollama to generate comprehensive lesson plans for complex multi-concept topics while maintaining reasonable performance for simpler topics.

## Glossary

- **Bug_Condition (C)**: The condition that triggers the bug - when lesson generation times out at 120 seconds for complex topics
- **Property (P)**: The desired behavior when generating complex lesson topics - generation should complete successfully within 240 seconds
- **Preservation**: Existing lesson generation behavior for simple topics that must remain unchanged by the timeout increase
- **TIMEOUT_SECS**: The constant in `lesson_planner.py` (line 85) that defines the maximum duration for Ollama API calls
- **_call_ollama()**: The function in `lesson_planner.py` that makes HTTP requests to the Ollama API with timeout handling
- **Complex Topic**: A lesson topic that combines multiple algorithmic concepts (e.g., "binary search with hash tables"), requiring more generation time than single-concept topics

## Bug Details

### Bug Condition

The bug manifests when a user requests lesson generation for a complex topic that combines multiple algorithmic concepts. The `_call_ollama()` function times out after 120 seconds, raising a `TimeoutError` before Ollama can complete the lesson plan generation.

**Formal Specification:**
```
FUNCTION isBugCondition(input)
  INPUT: input of type LessonGenerationRequest
  OUTPUT: boolean
  
  RETURN input.topic is a complex multi-concept topic
         AND input.generationTime > 120 seconds
         AND input.generationTime <= 240 seconds
         AND TimeoutError is raised
END FUNCTION
```

### Examples

- **Example 1**: Topic "binary search with hash tables" - Expected: generates lesson with beats covering both binary search and hash table concepts. Actual: times out at 120 seconds with `TimeoutError: Ollama did not respond within 120 seconds.`
- **Example 2**: Topic "merge sort with complexity analysis" - Expected: generates lesson with algorithm steps and complexity explanation. Actual: may timeout at 120 seconds for detailed explanations.
- **Example 3**: Topic "insertion sort" (simple topic) - Expected: completes in <60 seconds. Actual: completes successfully (not affected by bug).
- **Edge case**: Topic at exactly 120 seconds generation time - Expected: should complete successfully with increased timeout. Actual: currently fails at the boundary.

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- Lesson generation for simple single-concept topics must continue to work exactly as before
- Generation time for simple topics should remain unchanged (typically <60 seconds)
- All error handling for network errors, JSON parsing, and validation must remain unchanged
- The Ollama prompt structure, model parameters, and response parsing logic must remain unchanged

**Scope:**
All lesson generation requests that complete within 120 seconds should be completely unaffected by this fix. This includes:
- Simple algorithm topics (insertion sort, bubble sort, linear search)
- Single-concept explanations
- Topics with short prompt requirements
- All existing test cases that currently pass

## Hypothesized Root Cause

Based on the bug description and code analysis, the most likely issues are:

1. **Insufficient Timeout Duration**: The 120-second timeout was reduced from 240 seconds (see line 85 comment: "Reduced from 240s - 2 minutes is sufficient"), but this optimization was too aggressive for complex topics
   - Complex topics require Ollama to reason about multiple algorithmic concepts
   - Beat generation for multi-concept topics requires more tokens (up to 2000 num_predict)
   - The combination of temperature 0.3 and complex reasoning may require more inference time

2. **Topic Complexity Not Accounted For**: The timeout is uniform across all topics, but generation time scales with topic complexity
   - Multi-concept topics ("binary search with hash tables") require significantly more generation time than single-concept topics
   - The prompt builder creates more detailed algorithm-specific guidance for detected algorithms
   - Ollama must synthesize information across multiple algorithm families

3. **Model Inference Performance**: The llama3:latest model may require more time for high-quality multi-concept lesson generation
   - Temperature 0.3 provides consistent output but may slow down token generation
   - The 4096 context window and 2000 token prediction limit require substantial processing

## Correctness Properties

Property 1: Bug Condition - Complex Topic Generation Completes

_For any_ lesson generation request where the topic is complex (multi-concept) and generation time is between 120 and 240 seconds, the fixed `_call_ollama()` function SHALL complete successfully and return a valid lesson spec JSON, without raising a `TimeoutError`.

**Validates: Requirements 2.1 (Complex topics complete within timeout), 2.2 (No TimeoutError for valid generation requests)**

Property 2: Preservation - Simple Topic Performance

_For any_ lesson generation request where the topic is simple (single-concept) and generation time is under 120 seconds, the fixed code SHALL produce exactly the same behavior as the original code, preserving the same generation time and output quality for simple topics.

**Validates: Requirements 3.1 (Simple topics unchanged), 3.2 (Generation time unchanged for fast requests), 3.3 (Error handling unchanged)**

## Fix Implementation

### Changes Required

The fix is minimal and localized to a single constant:

**File**: `c:\Users\hp\LocalLearn\lesson_planner.py`

**Line**: 85

**Specific Changes**:
1. **Increase TIMEOUT_SECS Constant**: Change value from 120 to 240
   - Change: `TIMEOUT_SECS = 120` → `TIMEOUT_SECS = 240`
   - Remove or update the comment to reflect the new reasoning

2. **Update Comment**: Reflect that 240 seconds is required for complex topics
   - Old comment: `# Reduced from 240s - 2 minutes is sufficient`
   - New comment: `# Allows complex multi-concept topics to complete generation`

**No other changes required**:
- The `urllib.request.urlopen()` call in `_call_ollama()` already uses `timeout=TIMEOUT_SECS`
- Error handling already catches timeout errors appropriately
- All downstream code is timeout-agnostic

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface counterexamples that demonstrate the bug on unfixed code (confirm 120s timeout fails for complex topics), then verify the fix works correctly (240s timeout succeeds) and preserves existing behavior (simple topics unchanged).

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the bug BEFORE implementing the fix. Confirm that complex topics timeout at 120 seconds but would succeed at 240 seconds.

**Test Plan**: Write tests that call `plan_lesson()` with complex multi-concept topics and mock the Ollama API to simulate long generation times (between 120-240 seconds). Run these tests on the UNFIXED code to observe timeout failures.

**Test Cases**:
1. **Binary Search + Hash Tables Test**: Call `plan_lesson("binary search with hash tables", LanguageCode.EN)` with mocked 180-second response time (will fail on unfixed code with TimeoutError)
2. **Merge Sort + Complexity Test**: Call `plan_lesson("merge sort with time complexity analysis", LanguageCode.EN)` with mocked 150-second response time (will fail on unfixed code)
3. **Quick Sort + Space Complexity Test**: Call `plan_lesson("quick sort with space complexity", LanguageCode.EN)` with mocked 200-second response time (will fail on unfixed code)
4. **Boundary Test**: Mock exactly 120-second response time (may fail on unfixed code at the boundary)

**Expected Counterexamples**:
- `TimeoutError: Ollama did not respond within 120 seconds` raised for all test cases
- Possible causes: TIMEOUT_SECS constant set too low for complex topic generation

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds (complex topics with 120-240s generation time), the fixed function produces the expected behavior (successful completion).

**Pseudocode:**
```
FOR ALL topic WHERE isComplexTopic(topic) AND generationTime IN [120, 240] DO
  result := plan_lesson_fixed(topic, language)
  ASSERT result is valid JSON lesson spec
  ASSERT no TimeoutError raised
  ASSERT result contains valid beats/scenes
END FOR
```

**Test Implementation**: Use mocked Ollama responses with controlled delays between 120-240 seconds. Verify that:
- No TimeoutError is raised
- Valid lesson spec JSON is returned
- The spec passes all existing validation checks

### Preservation Checking

**Goal**: Verify that for all inputs where the bug condition does NOT hold (simple topics completing under 120 seconds), the fixed function produces the same result as the original function.

**Pseudocode:**
```
FOR ALL topic WHERE isSimpleTopic(topic) AND generationTime < 120 DO
  ASSERT plan_lesson_original(topic, lang) = plan_lesson_fixed(topic, lang)
  ASSERT generationTime_original = generationTime_fixed
END FOR
```

**Testing Approach**: Property-based testing is recommended for preservation checking because:
- It generates many test cases automatically across different simple topics
- It catches edge cases that manual unit tests might miss (topics near boundaries, various algorithm types)
- It provides strong guarantees that behavior is unchanged for all fast-completing topics

**Test Plan**: Observe behavior on UNFIXED code first for simple topics, recording generation times and outputs, then write property-based tests capturing that exact behavior should be preserved after the fix.

**Test Cases**:
1. **Simple Algorithm Preservation**: Verify that "insertion sort", "bubble sort", "linear search" generate lessons in the same time (<60s typically) and produce identical output structure
2. **Generation Time Preservation**: Verify that simple topics still complete in their original time (no performance regression from larger timeout constant)
3. **Error Handling Preservation**: Verify that network errors, JSON parsing errors, and validation errors are handled identically
4. **Edge Cases Preservation**: Verify that topics at <120s boundary continue to work exactly as before

### Unit Tests

- Test `plan_lesson()` with mocked Ollama responses at various durations (60s, 120s, 180s, 240s)
- Test timeout error handling at the new 240-second boundary
- Test that simple topics (single algorithm) complete successfully
- Test edge cases: exactly 120s (old boundary), exactly 240s (new boundary)
- Test error handling is unchanged: network errors, malformed JSON, validation failures

### Property-Based Tests

- Generate random simple algorithm topics and verify generation time remains under 120 seconds across many runs
- Generate random complex multi-concept topics and verify successful completion within 240 seconds
- Test that output structure (beats, visual plans, narration) is consistent across timeout values for the same topic

### Integration Tests

- Test full lesson generation flow for "binary search with hash tables" with real Ollama API (if available in test environment)
- Test that generated lesson specs are valid and can be animated by downstream pipeline
- Test that timeout error messages are clear and actionable when 240s is exceeded
- Test that generated beats contain appropriate algorithm-specific content for multi-concept topics
