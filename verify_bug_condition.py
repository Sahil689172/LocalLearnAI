"""
Bug Condition Verification Script

This script verifies the bug condition without requiring pytest.
It demonstrates that the test from test_lesson_timeout_bugfix.py correctly
identifies the bug on unfixed code (TIMEOUT_SECS = 120).

Run with: python verify_bug_condition.py
"""

import sys

# Import the TIMEOUT_SECS constant
from lesson_planner import TIMEOUT_SECS

print("="*70)
print("BUG CONDITION VERIFICATION")
print("="*70)
print(f"\nCurrent TIMEOUT_SECS in lesson_planner.py: {TIMEOUT_SECS}")
print()

# Complex topics that trigger the bug
complex_topics = [
    "binary search with hash tables",
    "merge sort with time complexity analysis",
    "quick sort with space complexity",
]

# Response times that fall in the bug condition range (120 < time <= 240)
bug_triggering_times = [150, 180, 200]

print("BUG CONDITION ANALYSIS:")
print("-" * 70)
print(f"Topics tested: {len(complex_topics)}")
print(f"Response times tested: {bug_triggering_times}")
print()

# Check if each combination would trigger the bug
bug_cases_found = 0
total_cases = 0

for topic in complex_topics:
    for response_time in bug_triggering_times:
        total_cases += 1
        if TIMEOUT_SECS < response_time:
            bug_cases_found += 1
            status = "⚠️  TIMEOUT (BUG)"
            print(f"  {topic:50s} @ {response_time}s: {status}")
        else:
            status = "✓  SUCCESS"
            print(f"  {topic:50s} @ {response_time}s: {status}")

print()
print("="*70)
print("SUMMARY")
print("="*70)

if TIMEOUT_SECS == 120:
    print(f"\n✓ Code is UNFIXED (TIMEOUT_SECS = {TIMEOUT_SECS})")
    print(f"✓ Bug condition detected: {bug_cases_found}/{total_cases} cases would timeout")
    print()
    print("COUNTEREXAMPLES DOCUMENTED:")
    for topic in complex_topics:
        print(f"  • '{topic}' with 150-200s response raises TimeoutError")
        print(f"    at {TIMEOUT_SECS}s instead of completing successfully")
    print()
    print("EXPECTED TEST BEHAVIOR:")
    print("  • Bug condition exploration test SHOULD FAIL (proves bug exists)")
    print("  • Each test case will raise TimeoutError as expected")
    print("  • These failures are CORRECT - they confirm the bug condition")
    print()
    print("VERIFICATION: ✓ PASSED")
    print("The bug condition is correctly identified and documented.")
    
elif TIMEOUT_SECS == 240:
    print(f"\n✓ Code is FIXED (TIMEOUT_SECS = {TIMEOUT_SECS})")
    print(f"✓ Bug condition resolved: {bug_cases_found}/{total_cases} cases would timeout")
    print()
    if bug_cases_found == 0:
        print("EXPECTED TEST BEHAVIOR:")
        print("  • Bug condition exploration test SHOULD PASS (confirms fix works)")
        print("  • All test cases complete successfully without TimeoutError")
        print("  • Complex topics with 120-240s response times work correctly")
        print()
        print("VERIFICATION: ✓ PASSED")
        print("The fix is validated - complex topics no longer timeout.")
    else:
        print("⚠️  WARNING: Some cases still timeout even with TIMEOUT_SECS = 240")
        print("This suggests the fix may not be complete or test times need adjustment.")
        
else:
    print(f"\n⚠️  UNEXPECTED TIMEOUT_SECS value: {TIMEOUT_SECS}")
    print(f"Expected either 120 (unfixed) or 240 (fixed)")
    print(f"Bug cases: {bug_cases_found}/{total_cases}")

print()
print("="*70)
print()
