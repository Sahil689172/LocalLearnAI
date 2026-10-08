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
        self.temporary_objects = []  # Track temporary text/objects for cleanup
    
    def _cleanup_temporary_objects(self, run_time: float = 0.2):
        """Remove all temporary objects from the scene."""
        if self.temporary_objects:
            self.scene.play(
                *[FadeOut(obj) for obj in self.temporary_objects],
                run_time=run_time
            )
            self.temporary_objects = []
    
    def _add_temporary(self, *objects):
        """Mark objects as temporary (will be cleaned up before next action)."""
        self.temporary_objects.extend(objects)
    
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
        """Display the array and target value with enhanced animations."""
        values = action.data.get("values", [12, 7, 23, 45, 9, 31])
        target = action.data.get("target", 45)
        
        # Create array visualizer
        self.array_viz = ArrayVisualizer(
            self.scene,
            values,
            position=ORIGIN + UP * 0.5,
            language=self.language
        )
        
        # Animate array appearance with staggered effect (35% of duration)
        array_show_time = duration * 0.35
        self.array_viz.show(run_time=array_show_time)
        
        # Create title with animation (20% of duration)
        title = Text("Linear Search", font_size=36, weight=BOLD, color=WHITE)
        title.to_edge(UP, buff=0.5)
        title_time = duration * 0.2
        self.scene.play(Write(title), run_time=title_time)
        self._add_temporary(title)
        
        # Show target label with emphasis (25% of duration)
        target_text = Text(f"Target: {target}", font_size=32, color=YELLOW)
        target_text.to_edge(DOWN, buff=1.0)
        target_show_time = duration * 0.25
        
        # Animate target with grow effect
        self.scene.play(
            GrowFromCenter(target_text),
            run_time=target_show_time
        )
        self.target_label = target_text
        self.state["target"] = target
        
        # Brief pause to let viewer absorb the setup (20%)
        remaining_time = duration - array_show_time - title_time - target_show_time
        if remaining_time > 0:
            self.scene.wait(remaining_time)
    
    def _set_pointer(self, action: VisualAction, duration: float):
        """Set pointer at specified index with enhanced animation."""
        if self.array_viz is None:
            self.scene.wait(duration)
            return
        
        # Clean up any previous temporary objects
        cleanup_time = 0.2 if self.temporary_objects else 0
        if self.temporary_objects:
            self._cleanup_temporary_objects(run_time=cleanup_time)
        
        index = action.data.get("index", 0)
        
        # Create explanatory text (20% of remaining duration)
        explain_text = Text("Start at first element", font_size=24, color=BLUE_C)
        explain_text.next_to(self.array_viz.cells[0], UP, buff=1.2)
        explain_time = (duration - cleanup_time) * 0.2
        self.scene.play(FadeIn(explain_text, shift=DOWN * 0.2), run_time=explain_time)
        self._add_temporary(explain_text)
        
        # Create pointer (arrow pointing up at the element)
        pointer = Arrow(
            start=ORIGIN,
            end=UP * 0.6,
            color=RED,
            buff=0.1,
            stroke_width=6
        )
        pointer.next_to(self.array_viz.cells[index], DOWN, buff=0.2)
        
        # Add pointer label
        pointer_label = Text("▲", font_size=36, color=RED)
        pointer_label.next_to(pointer, DOWN, buff=0.1)
        
        pointer_group = VGroup(pointer, pointer_label)
        
        # Animate pointer with grow effect (40% of remaining duration)
        anim_time = (duration - cleanup_time - explain_time) * 0.6
        self.scene.play(
            GrowFromCenter(pointer_group),
            self.array_viz.cells[index].animate.scale(1.15),
            run_time=anim_time
        )
        self.scene.play(
            self.array_viz.cells[index].animate.scale(1/1.15),
            run_time=anim_time * 0.3
        )
        self.pointer = pointer_group
        self.state["pointer_index"] = index
        
        # Wait for remaining duration
        remaining_time = duration - cleanup_time - explain_time - anim_time - (anim_time * 0.3)
        if remaining_time > 0:
            self.scene.wait(remaining_time)
    
    def _move_pointer(self, action: VisualAction, duration: float):
        """Animate pointer moving from one index to another with enhanced visuals."""
        if self.pointer is None or self.array_viz is None:
            self.scene.wait(duration)
            return
        
        # Clean up temporary objects first
        cleanup_time = 0.15 if self.temporary_objects else 0
        if self.temporary_objects:
            self._cleanup_temporary_objects(run_time=cleanup_time)
        
        from_index = action.data.get("from", self.state.get("pointer_index", 0))
        to_index = action.data.get("to", from_index + 1)
        
        # Clear previous highlights (quick)
        if self.array_viz.highlights:
            self.array_viz.clear_all_highlights(run_time=0.1)
        
        # Create movement label (15% of remaining duration)
        move_text = Text("Move to next →", font_size=22, color=BLUE_C)
        move_text.next_to(self.pointer, RIGHT, buff=0.5)
        label_time = (duration - cleanup_time) * 0.15
        self.scene.play(FadeIn(move_text, shift=RIGHT * 0.2), run_time=label_time)
        
        # Animate pointer movement with arc trajectory (50% of remaining duration)
        new_position = self.array_viz.cells[to_index].get_bottom() + DOWN * 0.8
        move_time = (duration - cleanup_time - label_time) * 0.5
        
        # Create curved path for pointer movement
        self.scene.play(
            self.pointer.animate.move_to(new_position),
            FadeOut(move_text, shift=RIGHT * 0.2),
            run_time=move_time
        )
        
        # Brief pulse on new element (15% of remaining duration)
        pulse_time = (duration - cleanup_time - label_time - move_time) * 0.4
        self.scene.play(
            Indicate(self.array_viz.cells[to_index], color=BLUE, scale_factor=1.15),
            run_time=pulse_time
        )
        
        self.state["pointer_index"] = to_index
        
        # Wait for remaining duration
        remaining_time = duration - cleanup_time - label_time - move_time - pulse_time - 0.1
        if remaining_time > 0:
            self.scene.wait(remaining_time)
    
    def _compare_element(self, action: VisualAction, duration: float):
        """Highlight and compare element with target - enhanced with animations."""
        if self.array_viz is None:
            self.scene.wait(duration)
            return
        
        # Clean up temporary objects first
        cleanup_time = 0.12 if self.temporary_objects else 0
        if self.temporary_objects:
            self._cleanup_temporary_objects(run_time=cleanup_time)
        
        index = action.data.get("index", self.state.get("pointer_index", 0))
        target = self.state.get("target", action.data.get("target"))
        current_value = self.array_viz.values[index] if index < len(self.array_viz.values) else None
        
        # Clear previous highlights (quick)
        if self.array_viz.highlights:
            self.array_viz.clear_all_highlights(run_time=0.08)
        
        # Highlight current element with pulse (20% of remaining duration)
        highlight_time = (duration - cleanup_time) * 0.2
        self.array_viz.highlight([index], color=BLUE, run_time=highlight_time * 0.6)
        self.scene.play(
            Indicate(self.array_viz.cells[index], color=BLUE, scale_factor=1.2),
            run_time=highlight_time * 0.4
        )
        
        # Show comparison with animated appearance (45% of remaining duration)
        if current_value is not None:
            is_match = current_value == target
            
            # Create comparison equation
            value_text = Text(str(current_value), font_size=32, color=WHITE)
            comparison_symbol = Text("=" if is_match else "≠", font_size=32, color=GREEN if is_match else ORANGE)
            target_text = Text(str(target), font_size=32, color=YELLOW)
            
            comparison_eq = VGroup(value_text, comparison_symbol, target_text)
            comparison_eq.arrange(RIGHT, buff=0.3)
            comparison_eq.next_to(self.array_viz.cells[index], UP, buff=0.6)
            
            # Animate comparison with staggered appearance
            show_time = (duration - cleanup_time - highlight_time) * 0.35
            self.scene.play(
                LaggedStart(
                    FadeIn(value_text, shift=DOWN * 0.2),
                    GrowFromCenter(comparison_symbol),
                    FadeIn(target_text, shift=DOWN * 0.2),
                    lag_ratio=0.3
                ),
                run_time=show_time
            )
            
            # Add visual feedback for result (15% of remaining duration)
            feedback_time = (duration - cleanup_time - highlight_time - show_time) * 0.3
            if is_match:
                # Checkmark for match
                checkmark = Text("✓", font_size=40, color=GREEN, weight=BOLD)
                checkmark.next_to(comparison_eq, RIGHT, buff=0.3)
                self.scene.play(GrowFromCenter(checkmark), run_time=feedback_time)
                comparison_eq.add(checkmark)
            else:
                # X for mismatch
                cross = Text("✗", font_size=36, color=RED)
                cross.next_to(comparison_eq, RIGHT, buff=0.3)
                self.scene.play(FadeIn(cross, scale=0.5), run_time=feedback_time)
                comparison_eq.add(cross)
            
            self._add_temporary(comparison_eq)
            
            # Brief pause to let viewer process (15% of remaining duration)
            wait_time = (duration - cleanup_time - highlight_time - show_time - feedback_time) * 0.5
            if wait_time > 0:
                self.scene.wait(wait_time)
            
            # Fade out comparison (remaining duration)
            fade_time = duration - cleanup_time - highlight_time - show_time - feedback_time - wait_time - 0.08
            if fade_time > 0:
                self.scene.play(FadeOut(comparison_eq), run_time=fade_time)
                self.temporary_objects.remove(comparison_eq)
        else:
            # If no value, just wait
            self.scene.wait(duration - cleanup_time - highlight_time - 0.08)
        
        self.comparison_count += 1
    
    def _found(self, action: VisualAction, duration: float):
        """Indicate target found at index with celebration animation."""
        if self.array_viz is None:
            self.scene.wait(duration)
            return
        
        # Clean up temporary objects
        cleanup_time = 0.15 if self.temporary_objects else 0
        if self.temporary_objects:
            self._cleanup_temporary_objects(run_time=cleanup_time)
        
        found_index = action.data.get("index", 0)
        value = action.data.get("value", self.state.get("target"))
        
        # Clear highlights (quick)
        if self.array_viz.highlights:
            self.array_viz.clear_all_highlights(run_time=0.08)
        
        # Highlight found element with success color (25% of remaining duration)
        highlight_time = (duration - cleanup_time) * 0.25
        self.array_viz.highlight([found_index], color=GREEN, run_time=highlight_time)
        
        # Create "FOUND!" banner with emphasis (40% of remaining duration)
        found_text = Text("FOUND!", font_size=48, color=GREEN, weight=BOLD)
        found_text.next_to(self.array_viz.cells[found_index], UP, buff=0.9)
        
        # Add decorative elements
        star_left = Text("★", font_size=36, color=YELLOW)
        star_right = Text("★", font_size=36, color=YELLOW)
        star_left.next_to(found_text, LEFT, buff=0.3)
        star_right.next_to(found_text, RIGHT, buff=0.3)
        
        celebration = VGroup(star_left, found_text, star_right)
        
        celebrate_time = (duration - cleanup_time - highlight_time) * 0.4
        
        # Animate found message with scale effect
        self.scene.play(
            LaggedStart(
                GrowFromCenter(star_left),
                Write(found_text, run_time=celebrate_time * 0.6),
                GrowFromCenter(star_right),
                lag_ratio=0.2
            ),
            run_time=celebrate_time
        )
        
        self._add_temporary(celebration)
        
        # Emphasize with multiple pulses (25% of remaining duration)
        if found_index < len(self.array_viz.cells):
            pulse_time = (duration - cleanup_time - highlight_time - celebrate_time) * 0.4
            self.scene.play(
                Circumscribe(self.array_viz.cells[found_index], color=GREEN, run_time=pulse_time),
                run_time=pulse_time
            )
        
        # Wait for remaining duration
        remaining_time = duration - cleanup_time - highlight_time - celebrate_time - pulse_time - 0.08
        if remaining_time > 0:
            self.scene.wait(remaining_time)
    
    def _not_found(self, action: VisualAction, duration: float):
        """Indicate target not found in array with clear visual feedback."""
        # Clean up temporary objects
        cleanup_time = 0.15 if self.temporary_objects else 0
        if self.temporary_objects:
            self._cleanup_temporary_objects(run_time=cleanup_time)
        
        # Show "NOT FOUND" message with animation (60% for animation)
        not_found_text = Text("NOT FOUND", font_size=42, color=RED, weight=BOLD)
        not_found_text.move_to(ORIGIN)
        
        # Add X symbol
        cross = Text("✗", font_size=60, color=RED)
        cross.next_to(not_found_text, UP, buff=0.5)
        
        not_found_group = VGroup(cross, not_found_text)
        
        anim_time = (duration - cleanup_time) * 0.6
        self.scene.play(
            LaggedStart(
                GrowFromCenter(cross),
                Write(not_found_text),
                lag_ratio=0.3
            ),
            run_time=anim_time
        )
        
        self._add_temporary(not_found_group)
        
        # Wait for remaining duration (40%)
        remaining_time = duration - cleanup_time - anim_time
        if remaining_time > 0:
            self.scene.wait(remaining_time)
    
    def _show_result(self, action: VisualAction, duration: float):
        """Display search result statistics with clear lifecycle management."""
        # Clean up temporary objects including found message
        cleanup_time = 0.18 if self.temporary_objects else 0
        if self.temporary_objects:
            self._cleanup_temporary_objects(run_time=cleanup_time)
        
        comparisons = action.data.get("comparisons", self.comparison_count)
        index = action.data.get("index", -1)
        
        # Create result heading
        result_heading = Text("Search Result", font_size=32, weight=BOLD, color=WHITE)
        result_heading.to_edge(UP, buff=0.7)
        
        # Create statistics
        if index >= 0:
            index_text = Text(f"Found at Index: {index}", font_size=26, color=GREEN)
            comp_text = Text(f"Comparisons: {comparisons}", font_size=26, color=BLUE_C)
        else:
            index_text = Text("Not found in array", font_size=26, color=RED)
            comp_text = Text(f"Comparisons: {comparisons}", font_size=26, color=BLUE_C)
        
        stats_group = VGroup(index_text, comp_text)
        stats_group.arrange(DOWN, buff=0.4)
        stats_group.move_to(ORIGIN)
        
        # Animate result display with staggered appearance (60% of remaining duration)
        anim_time = (duration - cleanup_time) * 0.6
        self.scene.play(
            LaggedStart(
                FadeIn(result_heading, shift=DOWN * 0.3),
                FadeIn(index_text, shift=UP * 0.2),
                FadeIn(comp_text, shift=UP * 0.2),
                lag_ratio=0.3
            ),
            run_time=anim_time
        )
        
        result_group = VGroup(result_heading, stats_group)
        self._add_temporary(result_group)
        
        # Wait for remaining duration (40%)
        remaining_time = duration - cleanup_time - anim_time
        if remaining_time > 0:
            self.scene.wait(remaining_time)
    
    def _show_complexity(self, action: VisualAction, duration: float):
        """Display time complexity analysis with proper cleanup and animations."""
        # Clean up previous result display
        cleanup_time = 0.18 if self.temporary_objects else 0
        if self.temporary_objects:
            self._cleanup_temporary_objects(run_time=cleanup_time)
        
        best = action.data.get("best", "O(1)")
        average = action.data.get("average", "O(n)")
        worst = action.data.get("worst", "O(n)")
        
        # If single complexity value provided
        if "value" in action.data:
            complexity = action.data.get("value")
            heading = Text("Time Complexity", font_size=32, weight=BOLD)
            heading.to_edge(UP, buff=0.7)
            formula = Text(complexity, font_size=56, color=BLUE)
            formula.move_to(ORIGIN)
            
            # Animate with staggered appearance
            heading_time = (duration - cleanup_time) * 0.3
            self.scene.play(FadeIn(heading, shift=DOWN * 0.2), run_time=heading_time)
            
            formula_time = (duration - cleanup_time - heading_time) * 0.6
            self.scene.play(Write(formula), run_time=formula_time)
            
            complexity_group = VGroup(heading, formula)
            self._add_temporary(complexity_group)
            
            remaining_time = duration - cleanup_time - heading_time - formula_time
            if remaining_time > 0:
                self.scene.wait(remaining_time)
        else:
            # Show all three cases with organized layout
            heading = Text("Time Complexity Analysis", font_size=30, weight=BOLD, color=WHITE)
            heading.to_edge(UP, buff=0.7)
            
            # Create colored labels for each case
            best_label = Text("Best:", font_size=24, color=GRAY)
            best_value = Text(best, font_size=28, color=GREEN, weight=BOLD)
            best_line = VGroup(best_label, best_value)
            best_line.arrange(RIGHT, buff=0.3)
            
            avg_label = Text("Average:", font_size=24, color=GRAY)
            avg_value = Text(average, font_size=28, color=YELLOW, weight=BOLD)
            avg_line = VGroup(avg_label, avg_value)
            avg_line.arrange(RIGHT, buff=0.3)
            
            worst_label = Text("Worst:", font_size=24, color=GRAY)
            worst_value = Text(worst, font_size=28, color=RED, weight=BOLD)
            worst_line = VGroup(worst_label, worst_value)
            worst_line.arrange(RIGHT, buff=0.3)
            
            complexity_cases = VGroup(best_line, avg_line, worst_line)
            complexity_cases.arrange(DOWN, buff=0.5, aligned_edge=LEFT)
            complexity_cases.move_to(ORIGIN)
            
            # Distribute duration across animations
            heading_time = (duration - cleanup_time) * 0.2
            self.scene.play(FadeIn(heading, shift=DOWN * 0.2), run_time=heading_time)
            
            # Animate each case with stagger
            line_time = (duration - cleanup_time - heading_time) * 0.22
            self.scene.play(
                FadeIn(best_line, shift=RIGHT * 0.3),
                run_time=line_time
            )
            self.scene.play(
                FadeIn(avg_line, shift=RIGHT * 0.3),
                run_time=line_time
            )
            self.scene.play(
                FadeIn(worst_line, shift=RIGHT * 0.3),
                run_time=line_time
            )
            
            complexity_group = VGroup(heading, complexity_cases)
            self._add_temporary(complexity_group)
            
            remaining_time = duration - cleanup_time - heading_time - (3 * line_time)
            if remaining_time > 0:
                self.scene.wait(remaining_time)
    
    def _fallback_text(self, action: VisualAction, duration: float):
        """Fallback for unknown actions — show as text with proper lifecycle."""
        # Clean up temporary objects
        cleanup_time = 0.15 if self.temporary_objects else 0
        if self.temporary_objects:
            self._cleanup_temporary_objects(run_time=cleanup_time)
        
        text_content = action.data.get("text", str(action.action))
        
        text = Text(text_content, font_size=32)
        text.move_to(ORIGIN)
        
        # Use full duration properly with lifecycle
        fadein_time = (duration - cleanup_time) * 0.3
        self.scene.play(FadeIn(text, shift=UP * 0.2), run_time=fadein_time)
        
        wait_time = (duration - cleanup_time - fadein_time) * 0.5
        self.scene.wait(wait_time)
        
        fadeout_time = duration - cleanup_time - fadein_time - wait_time
        self.scene.play(FadeOut(text), run_time=fadeout_time)
