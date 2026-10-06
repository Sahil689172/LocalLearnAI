"""
LocalLearn AI - Bubble Sort Visual Renderer
---------------------------------------------
Visual rendering for bubble sort algorithm.
"""

from manim import *
from .base import VisualRenderer, VisualAction
from .array_visualizer import ArrayVisualizer


class BubbleSortRenderer(VisualRenderer):
    """
    Renders bubble sort visual actions.
    
    Supported actions:
    - show_array: display initial array
    - compare: highlight two adjacent elements
    - swap: swap two elements
    - pass_complete: mark a pass as complete
    - show_complexity: display O(n²)
    """
    
    def __init__(self, scene, language: str = "en"):
        super().__init__(scene, language)
        self.array_viz = None
    
    def render_action(self, action: VisualAction, beat_duration: float):
        action_type = action.action
        
        if action_type == "show_array":
            self._show_array(action, beat_duration)
        elif action_type == "compare":
            self._compare(action, beat_duration)
        elif action_type == "swap":
            self._swap(action, beat_duration)
        elif action_type == "pass_complete":
            self._pass_complete(action, beat_duration)
        elif action_type == "show_complexity":
            self._show_complexity(action, beat_duration)
        else:
            self._fallback_text(action, beat_duration)
    
    def _show_array(self, action: VisualAction, duration: float):
        values = action.data.get("values", [5, 3, 8, 1, 9, 2])
        
        self.array_viz = ArrayVisualizer(
            self.scene,
            values,
            position=ORIGIN,
            language=self.language
        )
        
        self.array_viz.show(run_time=duration * 0.4)
        self.scene.wait(duration * 0.6)
    
    def _compare(self, action: VisualAction, duration: float):
        if self.array_viz is None:
            return
        
        i = action.data.get("i", 0)
        j = action.data.get("j", 1)
        
        self.array_viz.clear_all_highlights(run_time=0.2)
        self.array_viz.highlight([i, j], color=YELLOW, run_time=duration * 0.5)
        self.scene.wait(duration * 0.5)
    
    def _swap(self, action: VisualAction, duration: float):
        if self.array_viz is None:
            return
        
        i = action.data.get("i", 0)
        j = action.data.get("j", 1)
        
        self.array_viz.swap_visual(i, j, run_time=duration * 0.7)
        self.scene.wait(duration * 0.3)
    
    def _pass_complete(self, action: VisualAction, duration: float):
        if self.array_viz is None:
            return
        
        self.array_viz.clear_all_highlights(run_time=duration * 0.5)
        self.scene.wait(duration * 0.5)
    
    def _show_complexity(self, action: VisualAction, duration: float):
        complexity = action.data.get("value", "O(n²)")
        
        heading = Text("Time Complexity", font_size=32)
        heading.to_edge(UP, buff=0.5)
        formula = Text(complexity, font_size=56, color=BLUE)
        formula.move_to(ORIGIN)
        
        self.scene.play(Write(heading), run_time=duration * 0.3)
        self.scene.play(Write(formula), run_time=duration * 0.4)
        self.scene.wait(duration * 0.3)
    
    def _fallback_text(self, action: VisualAction, duration: float):
        text_content = action.data.get("text", str(action.action))
        text = Text(text_content, font_size=32)
        text.move_to(ORIGIN)
        
        self.scene.play(FadeIn(text), run_time=duration * 0.3)
        self.scene.wait(duration * 0.5)
        self.scene.play(FadeOut(text), run_time=duration * 0.2)
