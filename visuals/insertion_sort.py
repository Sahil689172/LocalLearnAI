"""
LocalLearn AI - Insertion Sort Visual Renderer
------------------------------------------------
High-quality visual rendering for insertion sort algorithm.

Demonstrates the actual insertion sort mechanics:
- Select key from unsorted portion
- Compare with sorted portion
- Shift larger elements right
- Insert key into correct position
- Visual distinction between sorted/unsorted regions
"""

from manim import *
from .base import VisualRenderer, VisualAction
from .array_visualizer import ArrayVisualizer


# Language-specific labels
_LABELS = {
    "key": {
        "en": "Key",
        "hi": "कुंजी",
        "ta": "முக்கிய",
        "te": "కీ",
        "mr": "की",
    },
    "sorted": {
        "en": "Sorted",
        "hi": "क्रमबद्ध",
        "ta": "வரிசைப்படுத்தப்பட்டது",
        "te": "క్రమబద్ధీకరించబడింది",
        "mr": "क्रमवार",
    },
    "comparing": {
        "en": "Comparing",
        "hi": "तुलना",
        "ta": "ஒப்பிடுதல்",
        "te": "పోల్చడం",
        "mr": "तुलना",
    },
}


def _label(key: str, lang: str) -> str:
    return _LABELS.get(key, {}).get(lang, _LABELS[key]["en"])


class InsertionSortRenderer(VisualRenderer):
    """
    Renders insertion sort visual actions.
    
    Supported actions:
    - show_array: display initial unsorted array
    - select_key: highlight the current key element
    - compare: show comparison between key and sorted element
    - shift: animate shifting elements right
    - insert: place key into correct position
    - mark_sorted: update sorted region indicator
    - show_complexity: display O(n²) complexity
    """
    
    def __init__(self, scene, language: str = "en"):
        super().__init__(scene, language)
        self.array_viz = None
        self.sorted_bound = 0  # everything before this index is sorted
    
    def render_action(self, action: VisualAction, beat_duration: float):
        """Render an insertion sort visual action."""
        action_type = action.action
        
        if action_type == "show_array":
            self._show_array(action, beat_duration)
        elif action_type == "select_key":
            self._select_key(action, beat_duration)
        elif action_type == "compare":
            self._compare(action, beat_duration)
        elif action_type == "shift":
            self._shift(action, beat_duration)
        elif action_type == "insert":
            self._insert(action, beat_duration)
        elif action_type == "mark_sorted":
            self._mark_sorted(action, beat_duration)
        elif action_type == "show_complexity":
            self._show_complexity(action, beat_duration)
        else:
            # Unknown action — show as text explanation
            self._fallback_text(action, beat_duration)
    
    def _show_array(self, action: VisualAction, duration: float):
        """Display the initial unsorted array."""
        values = action.data.get("values", [5, 2, 8, 3, 1, 6, 4])
        
        self.array_viz = ArrayVisualizer(
            self.scene,
            values,
            position=ORIGIN + UP * 0.5,
            language=self.language
        )
        
        # Allocate time: 30% show, 70% wait
        show_time = duration * 0.3
        wait_time = duration * 0.7
        
        self.array_viz.show(run_time=show_time)
        self.scene.wait(wait_time)
        
        self.sorted_bound = 1  # first element is trivially sorted
    
    def _select_key(self, action: VisualAction, duration: float):
        """Highlight the key element to be inserted."""
        if self.array_viz is None:
            return
        
        key_index = action.data.get("index", self.sorted_bound)
        
        # Clear previous highlights
        self.array_viz.clear_all_highlights(run_time=0.2)
        
        # Allocate time: 40% highlight, 20% label, 40% wait
        highlight_time = duration * 0.4
        label_time = duration * 0.2
        wait_time = duration * 0.4
        
        # Highlight key
        self.array_viz.highlight([key_index], color=YELLOW, run_time=highlight_time)
        
        # Add "Key" label
        key_pos = self.array_viz.cells[key_index].get_top() + UP * 0.4
        self.array_viz.add_label(
            "key",
            _label("key", self.language),
            key_pos,
            run_time=label_time
        )
        
        self.scene.wait(wait_time)
        self.state["key_index"] = key_index
    
    def _compare(self, action: VisualAction, duration: float):
        """Show comparison between key and sorted elements."""
        if self.array_viz is None:
            return
        
        key_index = self.state.get("key_index", 1)
        compare_index = action.data.get("compare_with", key_index - 1)
        
        # Allocate time
        highlight_time = duration * 0.35
        wait_time = duration * 0.65
        
        # Highlight both elements being compared
        self.array_viz.clear_all_highlights(run_time=0.2)
        self.array_viz.highlight([key_index], color=YELLOW, run_time=highlight_time * 0.5)
        self.array_viz.highlight([compare_index], color=BLUE, run_time=highlight_time * 0.5)
        
        # Brief pulse to draw attention
        self.array_viz.indicate_element(compare_index, color=BLUE, run_time=highlight_time)
        
        self.scene.wait(wait_time)
    
    def _shift(self, action: VisualAction, duration: float):
        """Animate shifting elements one position to the right."""
        if self.array_viz is None:
            return
        
        indices = action.data.get("indices", [])
        if not indices:
            return
        
        # Allocate time: 70% shift animation, 30% settle
        shift_time = duration * 0.7
        settle_time = duration * 0.3
        
        # Highlight elements being shifted
        self.array_viz.clear_all_highlights(run_time=0.2)
        self.array_viz.highlight(indices, color=ORANGE, run_time=0.3)
        
        # Shift animation
        self.array_viz.shift_right(indices, run_time=shift_time)
        
        self.scene.wait(settle_time)
    
    def _insert(self, action: VisualAction, duration: float):
        """Insert the key into its correct position."""
        if self.array_viz is None:
            return
        
        insert_index = action.data.get("index", 0)
        key_value = action.data.get("value", 0)
        
        # Allocate time
        insert_time = duration * 0.5
        indicate_time = duration * 0.3
        wait_time = duration * 0.2
        
        # Clear highlights
        self.array_viz.clear_all_highlights(run_time=0.2)
        
        # Insert value
        self.array_viz.insert_at(insert_index, key_value, run_time=insert_time)
        
        # Highlight the inserted element
        self.array_viz.highlight([insert_index], color=GREEN, run_time=0.3)
        self.array_viz.indicate_element(insert_index, color=GREEN, run_time=indicate_time)
        
        # Remove key label
        self.array_viz.remove_label("key", run_time=0.2)
        
        self.scene.wait(wait_time)
    
    def _mark_sorted(self, action: VisualAction, duration: float):
        """Update the visual indicator of the sorted region."""
        if self.array_viz is None:
            return
        
        new_bound = action.data.get("sorted_until", self.sorted_bound + 1)
        
        # Clear all highlights
        self.array_viz.clear_all_highlights(run_time=0.2)
        
        # Fade unsorted portion slightly
        if new_bound < len(self.array_viz.cells):
            self.array_viz.set_opacity_range(
                new_bound,
                len(self.array_viz.cells),
                opacity=0.5,
                run_time=duration * 0.4
            )
        
        # Restore sorted portion to full opacity
        self.array_viz.set_opacity_range(
            0,
            new_bound,
            opacity=1.0,
            run_time=duration * 0.4
        )
        
        self.sorted_bound = new_bound
        self.scene.wait(duration * 0.2)
    
    def _show_complexity(self, action: VisualAction, duration: float):
        """Display time complexity."""
        complexity = action.data.get("value", "O(n²)")
        
        # Allocate time
        show_time = duration * 0.4
        wait_time = duration * 0.6
        
        # Create complexity display
        heading = Text("Time Complexity", font_size=32)
        heading.to_edge(UP, buff=0.5)
        
        formula = Text(complexity, font_size=56, color=BLUE)
        formula.move_to(ORIGIN)
        
        self.scene.play(Write(heading), run_time=show_time * 0.4)
        self.scene.play(Write(formula), run_time=show_time * 0.6)
        self.scene.wait(wait_time)
        
        self.scene.play(
            FadeOut(heading),
            FadeOut(formula),
            run_time=0.5
        )
    
    def _fallback_text(self, action: VisualAction, duration: float):
        """Fallback for unknown actions — show as text."""
        text_content = action.data.get("text", str(action.action))
        
        text = Text(text_content, font_size=32)
        text.move_to(ORIGIN)
        
        self.scene.play(FadeIn(text, shift=UP * 0.2), run_time=duration * 0.3)
        self.scene.wait(duration * 0.5)
        self.scene.play(FadeOut(text), run_time=duration * 0.2)
