"""
LocalLearn AI - Linear Search Visual Renderer
----------------------------------------------
Visual rendering for linear search algorithm.

Shows step-by-step search through an unsorted array:
- Pointer movement from element to element
- Comparisons with target value
- Visual feedback for matches/mismatches
- Result display with comparison count
"""

from manim import *
from .base import VisualRenderer, VisualAction
from .array_visualizer import ArrayVisualizer


class LinearSearchRenderer(VisualRenderer):
    """
    Renders linear search visual actions.
    
    Supported actions:
    - show_array: display array with target value
    - set_pointer: initialize pointer at an index
    - move_pointer: animate pointer moving from one index to another
    - compare_element: highlight and compare element with target
    - found: indicate target found at index
    - not_found: indicate target not found in array
    - show_result: display search statistics (comparisons, index)
    - show_complexity: display time complexity (best/average/worst)
    """
    
    def __init__(self, scene, language: str = "en"):
        super().__init__(scene, language)
        self.array_viz = None
        self.pointer = None
        self.target_label = None
        self.comparison_count = 0
    
    def render_action(self, action: VisualAction, beat_duration: float):
        """Render a linear search visual action."""
        action_type = action.action
        
        if action_type == "show_array":
            self._show_array(action, beat_duration)
        elif action_type == "set_pointer":
            self._set_pointer(action, beat_duration)
        elif action_type == "move_pointer":
            self._move_pointer(action, beat_duration)
        elif action_type == "compare_element":
            self._compare_element(action, beat_duration)
        elif action_type == "found":
            self._found(action, beat_duration)
        elif action_type == "not_found":
            self._not_found(action, beat_duration)
        elif action_type == "show_result":
            self._show_result(action, beat_duration)
        elif action_type == "show_complexity":
            self._show_complexity(action, beat_duration)
        else:
            self._fallback_text(action, beat_duration)
    
    def _show_array(self, action: VisualAction, duration: float):
        """Display the array and target value."""
        values = action.data.get("values", [12, 7, 23, 45, 9, 31])
        target = action.data.get("target", 45)
        
        self.array_viz = ArrayVisualizer(
            self.scene,
            values,
            position=ORIGIN + UP * 0.5,
            language=self.language
        )
        
        # Show array
        self.array_viz.show(run_time=duration * 0.4)
        
        # Show target label
        target_text = Text(f"Target: {target}", font_size=32, color=YELLOW)
        target_text.to_edge(DOWN, buff=1.0)
        self.scene.play(Write(target_text), run_time=duration * 0.3)
        self.target_label = target_text
        self.state["target"] = target
        
        self.scene.wait(duration * 0.3)
    
    def _set_pointer(self, action: VisualAction, duration: float):
        """Set pointer at specified index."""
        if self.array_viz is None:
            return
        
        index = action.data.get("index", 0)
        
        # Create pointer (arrow pointing up at the element)
        pointer = Arrow(
            start=ORIGIN,
            end=UP * 0.6,
            color=RED,
            buff=0.1
        )
        pointer.next_to(self.array_viz.cells[index], DOWN, buff=0.2)
        
        # Add pointer label
        pointer_label = Text("▲", font_size=36, color=RED)
        pointer_label.next_to(pointer, DOWN, buff=0.1)
        
        pointer_group = VGroup(pointer, pointer_label)
        
        self.scene.play(FadeIn(pointer_group), run_time=duration * 0.5)
        self.pointer = pointer_group
        self.state["pointer_index"] = index
        
        self.scene.wait(duration * 0.5)
    
    def _move_pointer(self, action: VisualAction, duration: float):
        """Animate pointer moving from one index to another."""
        if self.pointer is None or self.array_viz is None:
            return
        
        from_index = action.data.get("from", self.state.get("pointer_index", 0))
        to_index = action.data.get("to", from_index + 1)
        
        # Clear previous highlight
        self.array_viz.clear_all_highlights(run_time=0.1)
        
        # Move pointer to new position
        new_position = self.array_viz.cells[to_index].get_bottom() + DOWN * 0.8
        self.scene.play(
            self.pointer.animate.move_to(new_position),
            run_time=duration * 0.7
        )
        
        self.state["pointer_index"] = to_index
        self.scene.wait(duration * 0.3)
    
    def _compare_element(self, action: VisualAction, duration: float):
        """Highlight and compare element with target."""
        if self.array_viz is None:
            return
        
        index = action.data.get("index", self.state.get("pointer_index", 0))
        target = self.state.get("target", action.data.get("target"))
        current_value = self.array_viz.values[index] if index < len(self.array_viz.values) else None
        
        # Highlight current element
        self.array_viz.clear_all_highlights(run_time=0.1)
        self.array_viz.highlight([index], color=BLUE, run_time=duration * 0.3)
        
        # Show comparison
        if current_value is not None:
            comparison_text = Text(
                f"{current_value} ≠ {target}" if current_value != target else f"{current_value} = {target}",
                font_size=28,
                color=GREEN if current_value == target else ORANGE
            )
            comparison_text.next_to(self.array_viz.cells[index], UP, buff=0.5)
            
            self.scene.play(Write(comparison_text), run_time=duration * 0.4)
            self.scene.wait(duration * 0.2)
            self.scene.play(FadeOut(comparison_text), run_time=0.1)
        
        self.comparison_count += 1
    
    def _found(self, action: VisualAction, duration: float):
        """Indicate target found at index."""
        if self.array_viz is None:
            return
        
        found_index = action.data.get("index", 0)
        value = action.data.get("value", self.state.get("target"))
        
        # Highlight found element
        self.array_viz.clear_all_highlights(run_time=0.1)
        self.array_viz.highlight([found_index], color=GREEN, run_time=duration * 0.3)
        
        # Show "FOUND!" message
        found_text = Text("FOUND!", font_size=48, color=GREEN, weight=BOLD)
        found_text.next_to(self.array_viz.cells[found_index], UP, buff=0.7)
        
        self.scene.play(
            Write(found_text),
            self.array_viz.indicate_element(found_index, color=GREEN, run_time=duration * 0.4)
        )
        self.scene.wait(duration * 0.3)
    
    def _not_found(self, action: VisualAction, duration: float):
        """Indicate target not found in array."""
        # Show "NOT FOUND" message
        not_found_text = Text("NOT FOUND", font_size=42, color=RED)
        not_found_text.move_to(ORIGIN)
        
        self.scene.play(Write(not_found_text), run_time=duration * 0.5)
        self.scene.wait(duration * 0.5)
    
    def _show_result(self, action: VisualAction, duration: float):
        """Display search result statistics."""
        comparisons = action.data.get("comparisons", self.comparison_count)
        index = action.data.get("index", -1)
        
        # Create result display
        result_text = Text("Search Result", font_size=32, weight=BOLD)
        result_text.to_edge(UP, buff=0.5)
        
        if index >= 0:
            detail_text = Text(
                f"Index: {index}\nComparisons: {comparisons}",
                font_size=28
            )
        else:
            detail_text = Text(
                f"Not found\nComparisons: {comparisons}",
                font_size=28
            )
        detail_text.next_to(result_text, DOWN, buff=0.3)
        
        result_group = VGroup(result_text, detail_text)
        
        self.scene.play(FadeIn(result_group), run_time=duration * 0.5)
        self.scene.wait(duration * 0.5)
    
    def _show_complexity(self, action: VisualAction, duration: float):
        """Display time complexity analysis."""
        best = action.data.get("best", "O(1)")
        average = action.data.get("average", "O(n)")
        worst = action.data.get("worst", "O(n)")
        
        # If single complexity value provided
        if "value" in action.data:
            complexity = action.data.get("value")
            heading = Text("Time Complexity", font_size=32)
            heading.to_edge(UP, buff=0.5)
            formula = Text(complexity, font_size=56, color=BLUE)
            formula.move_to(ORIGIN)
            
            self.scene.play(Write(heading), run_time=duration * 0.3)
            self.scene.play(Write(formula), run_time=duration * 0.4)
            self.scene.wait(duration * 0.3)
        else:
            # Show all three cases
            heading = Text("Time Complexity", font_size=32, weight=BOLD)
            heading.to_edge(UP, buff=0.5)
            
            best_line = Text(f"Best Case: {best}", font_size=28, color=GREEN)
            avg_line = Text(f"Average Case: {average}", font_size=28, color=YELLOW)
            worst_line = Text(f"Worst Case: {worst}", font_size=28, color=RED)
            
            complexity_group = VGroup(best_line, avg_line, worst_line)
            complexity_group.arrange(DOWN, buff=0.3)
            complexity_group.move_to(ORIGIN)
            
            self.scene.play(Write(heading), run_time=duration * 0.2)
            self.scene.play(Write(best_line), run_time=duration * 0.2)
            self.scene.play(Write(avg_line), run_time=duration * 0.2)
            self.scene.play(Write(worst_line), run_time=duration * 0.2)
            self.scene.wait(duration * 0.2)
    
    def _fallback_text(self, action: VisualAction, duration: float):
        """Fallback for unknown actions — show as text."""
        text_content = action.data.get("text", str(action.action))
        
        text = Text(text_content, font_size=32)
        text.move_to(ORIGIN)
        
        self.scene.play(FadeIn(text, shift=UP * 0.2), run_time=duration * 0.3)
        self.scene.wait(duration * 0.5)
        self.scene.play(FadeOut(text), run_time=duration * 0.2)
