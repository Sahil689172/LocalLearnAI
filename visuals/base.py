"""
LocalLearn AI - Visual Engine Base Classes
--------------------------------------------
Base abstractions for algorithm-specific visual renderers.
"""

from typing import Any
from dataclasses import dataclass


@dataclass
class VisualAction:
    """
    A single visual action to be rendered by Manim.
    
    Describes WHAT should happen visually (e.g., "highlight element 2"),
    not HOW to implement it in Manim (which is the renderer's job).
    """
    type: str  # e.g., "array", "tree", "graph"
    action: str  # e.g., "select_key", "compare", "swap", "highlight"
    data: dict[str, Any]  # action-specific data
    emphasis: list[int] = None  # indices to emphasize
    duration: float = 1.0  # base duration hint (can be overridden by audio)
    
    def __post_init__(self):
        if self.emphasis is None:
            self.emphasis = []


class VisualRenderer:
    """
    Base class for algorithm-specific visual renderers.
    
    A VisualRenderer consumes structured VisualAction objects and produces
    Manim animations. It maintains visual state across actions (e.g., the
    current array, highlighted elements, sorted region).
    
    Subclasses implement algorithm-specific rendering logic.
    """
    
    def __init__(self, scene, language: str = "en"):
        """
        Initialize the renderer.
        
        Parameters
        ----------
        scene : Manim Scene instance
        language : language code for labels ("en", "hi", etc.)
        """
        self.scene = scene
        self.language = language
        self.state = {}  # algorithm-specific state
    
    def render_action(self, action: VisualAction, beat_duration: float):
        """
        Render a single VisualAction on the Manim scene.
        
        Parameters
        ----------
        action : the visual action to render
        beat_duration : actual audio duration for this beat (in seconds)
        
        This method should be overridden by subclasses.
        """
        raise NotImplementedError("Subclasses must implement render_action")
    
    def reset(self):
        """Reset the visual state (called between beats if needed)."""
        self.state = {}
