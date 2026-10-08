"""
LocalLearn AI - Visual Engine
-------------------------------
Algorithm-specific deterministic visual renderers for high-quality
educational animations.

IMPORTANT: This module uses lazy imports to avoid requiring ManimGL
at backend startup. Visual renderers are only imported when actually
generating scene files.
"""

from .base import VisualAction, VisualRenderer

# Lazy imports for renderers that require ManimGL
# These are only imported when actually needed in generate_scene_file()

__all__ = [
    "VisualAction",
    "VisualRenderer",
    "ArrayVisualizer",
    "InsertionSortRenderer",
    "BinarySearchRenderer",
    "BubbleSortRenderer",
    "SelectionSortRenderer",
]

def __getattr__(name):
    """Lazy import for visual renderers that require ManimGL."""
    if name == "ArrayVisualizer":
        from .array_visualizer import ArrayVisualizer
        return ArrayVisualizer
    elif name == "InsertionSortRenderer":
        from .insertion_sort import InsertionSortRenderer
        return InsertionSortRenderer
    elif name == "BinarySearchRenderer":
        from .binary_search import BinarySearchRenderer
        return BinarySearchRenderer
    elif name == "BubbleSortRenderer":
        from .bubble_sort import BubbleSortRenderer
        return BubbleSortRenderer
    elif name == "SelectionSortRenderer":
        from .selection_sort import SelectionSortRenderer
        return SelectionSortRenderer
    elif name == "LinearSearchRenderer":
        from .linear_search import LinearSearchRenderer
        return LinearSearchRenderer
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

