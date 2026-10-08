"""
LocalLearn AI - Binary Search Visual Renderer
-----------------------------------------------
Visual rendering for binary search algorithm.
"""

from manimlib import *
from .base import VisualRenderer, VisualAction
from .array_visualizer import ArrayVisualizer


class BinarySearchRenderer(VisualRenderer):
    """
    Renders binary search visual actions.
    
    Supported actions:
    - show_array: display sorted array
    - set_bounds: show search range (lo, hi)
    - check_middle: highlight and check middle element
    - found: indicate target found
    - eliminate_half: fade out eliminated portion
    - show_complexity: display O(log n)
    """
    
    def __init__(self, scene, language: str = "en"):
        super().__init__(scene, language)
        self.array_viz = None
    
    def render_action(self, action: VisualAction, beat_duration: float):
        action_type = action.action
        
        if action_type == "show_array":
            self._show_array(action, beat_duration)
        elif action_type == "check_middle":
            self._check_middle(action, beat_duration)
        elif action_type == "found":
            self._found(action, beat_duration)
        elif action_type == "eliminate_half":
            self._eliminate_half(action, beat_duration)
        elif action_type == "show_complexity":
            self._show_complexity(action, beat_duration)
        else:
            self._fallback_text(action, beat_duration)
    
    def _show_array(self, action: VisualAction, duration: float):
        values = action.data.get("values", [1, 3, 5, 7, 9, 11, 13])
        target = action.data.get("target", 7)
        
        self.array_viz = ArrayVisualizer(
            self.scene,
            values,
            position=ORIGIN + UP * 0.5,
            language=self.language
        )
        
        self.array_viz.show(run_time=duration * 0.4)
        
        # Show target label
        target_text = Text(f"Target: {target}", font_size=28)
        target_text.to_edge(DOWN, buff=0.5)
        self.scene.play(Write(target_text), run_time=duration * 0.3)
        self.state["target_label"] = target_text
        
        self.scene.wait(duration * 0.3)
    
    def _check_middle(self, action: VisualAction, duration: float):
        if self.array_viz is None:
            return
        
        mid_index = action.data.get("index", 0)
        
        self.array_viz.clear_all_highlights(run_time=0.2)
        self.array_viz.highlight([mid_index], color=YELLOW, run_time=duration * 0.4)
        self.array_viz.indicate_element(mid_index, run_time=duration * 0.4)
        self.scene.wait(duration * 0.2)
    
    def _found(self, action: VisualAction, duration: float):
        if self.array_viz is None:
            return
        
        found_index = action.data.get("index", 0)
        
        self.array_viz.clear_all_highlights(run_time=0.2)
        self.array_viz.highlight([found_index], color=GREEN, run_time=duration * 0.3)
        
        found_text = Text("FOUND!", font_size=36, color=GREEN)
        found_text.next_to(self.array_viz.cells[found_index], UP, buff=0.5)
        self.scene.play(Write(found_text), run_time=duration * 0.4)
        self.scene.wait(duration * 0.3)
    
    def _eliminate_half(self, action: VisualAction, duration: float):
        if self.array_viz is None:
            return
        
        eliminate_start = action.data.get("start", 0)
        eliminate_end = action.data.get("end", 0)
        
        self.array_viz.set_opacity_range(
            eliminate_start,
            eliminate_end,
            opacity=0.2,
            run_time=duration * 0.6
        )
        self.scene.wait(duration * 0.4)
    
    def _show_complexity(self, action: VisualAction, duration: float):
        complexity = action.data.get("value", "O(log n)")
        
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
