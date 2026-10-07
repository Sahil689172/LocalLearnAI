"""
Simple script to run only the bug condition exploration tests.
This verifies that the fix (TIMEOUT_SECS = 240) allows complex topics to complete.
"""

import sys
import unittest

# Import the test class
from test_lesson_timeout_bugfix import TestBugConditionExploration

if __name__ == "__main__":
    # Create test suite with only bug condition exploration tests
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestBugConditionExploration)
    
    # Run with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*70)
    print("BUG CONDITION EXPLORATION TEST SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    
    if result.wasSuccessful():
        print("\n✓ ALL TESTS PASSED - Bug fix is validated!")
        print("  Complex topics now complete successfully within 240s timeout.")
        exit(0)
    else:
        print("\n✗ SOME TESTS FAILED - Fix may not be complete.")
        exit(1)
