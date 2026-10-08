"""Quick test to verify visuals module imports work"""
import sys

# Add LocalLearn project root to path
PROJECT_ROOT = r"c:\Users\hp\LocalLearn"
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

print(f"Python sys.path: {sys.path}")
print(f"Attempting to import visuals.base...")

try:
    from visuals.base import VisualRenderer, VisualAction
    print("SUCCESS: visuals.base imported")
except ImportError as e:
    print(f"ERROR: Failed to import visuals.base: {e}")
    sys.exit(1)

try:
    from visuals.insertion_sort import InsertionSortRenderer
    print("SUCCESS: InsertionSortRenderer imported")
except ImportError as e:
    print(f"ERROR: Failed to import InsertionSortRenderer: {e}")
    sys.exit(1)

print("\nAll imports successful!")
