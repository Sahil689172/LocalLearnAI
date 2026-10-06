"""
LocalLearn AI - Array Visualizer
----------------------------------
Reusable component for rendering array-based algorithm visualizations.
"""

from manim import *


class ArrayVisualizer:
    """
    Reusable array visualization component.
    
    Creates and maintains a visual representation of an array with:
    - Boxes for each element
    - Value labels
    - Index labels (optional)
    - Highlighting
    - State annotations (sorted/unsorted regions)
    """
    
    def __init__(
        self,
        scene,
        values: list[int],
        position: np.ndarray = ORIGIN,
        box_size: float = 0.8,
        language: str = "en",
    ):
        self.scene = scene
        self.values = list(values)
        self.position = position
        self.box_size = box_size
        self.language = language
        
        self.cells = VGroup()  # VGroup of (box, label) pairs
        self.highlights = {}  # index -> SurroundingRectangle
        self.annotations = {}  # str -> Text mobject
        
        self._build_array()
    
    def _build_array(self):
        """Build the initial array visualization."""
        for val in self.values:
            box = Square(side_length=self.box_size, stroke_width=2.5, stroke_color=WHITE)
            label = Text(str(val), font_size=28)
            label.move_to(box.get_center())
            cell = VGroup(box, label)
            self.cells.add(cell)
        
        self.cells.arrange(RIGHT, buff=0.12)
        self.cells.move_to(self.position)
    
    def show(self, run_time: float = 1.0):
        """Animate the array appearing on screen."""
        self.scene.play(
            LaggedStart(
                *[FadeIn(cell, shift=UP * 0.15) for cell in self.cells],
                lag_ratio=0.1
            ),
            run_time=run_time
        )
    
    def highlight(self, indices: list[int], color=YELLOW, run_time: float = 0.5):
        """Highlight specific array elements."""
        animations = []
        for idx in indices:
            if 0 <= idx < len(self.cells):
                if idx in self.highlights:
                    # Update existing highlight
                    rect = self.highlights[idx]
                    animations.append(rect.animate.set_color(color))
                else:
                    # Create new highlight
                    rect = SurroundingRectangle(
                        self.cells[idx],
                        color=color,
                        buff=0.06,
                        stroke_width=3
                    )
                    self.highlights[idx] = rect
                    animations.append(Create(rect))
        
        if animations:
            self.scene.play(*animations, run_time=run_time)
    
    def clear_highlight(self, index: int, run_time: float = 0.3):
        """Remove highlight from an element."""
        if index in self.highlights:
            rect = self.highlights[index]
            self.scene.play(FadeOut(rect), run_time=run_time)
            del self.highlights[index]
    
    def clear_all_highlights(self, run_time: float = 0.3):
        """Remove all highlights."""
        if self.highlights:
            self.scene.play(
                *[FadeOut(rect) for rect in self.highlights.values()],
                run_time=run_time
            )
            self.highlights = {}
    
    def swap_visual(self, i: int, j: int, run_time: float = 0.8):
        """Visually swap two elements."""
        if not (0 <= i < len(self.cells) and 0 <= j < len(self.cells)):
            return
        
        # Swap in data
        self.values[i], self.values[j] = self.values[j], self.values[i]
        
        # Animate visual swap
        cell_i = self.cells[i]
        cell_j = self.cells[j]
        
        target_i = cell_j.get_center()
        target_j = cell_i.get_center()
        
        self.scene.play(
            cell_i.animate.move_to(target_i),
            cell_j.animate.move_to(target_j),
            run_time=run_time
        )
        
        # Update internal order
        self.cells.submobjects[i], self.cells.submobjects[j] = \
            self.cells.submobjects[j], self.cells.submobjects[i]
    
    def shift_right(self, indices: list[int], run_time: float = 0.6):
        """Shift elements one position to the right."""
        if not indices:
            return
        
        animations = []
        for idx in indices:
            if 0 <= idx < len(self.cells) - 1:
                cell = self.cells[idx]
                next_pos = self.cells[idx + 1].get_center()
                animations.append(cell.animate.move_to(next_pos))
        
        if animations:
            self.scene.play(*animations, run_time=run_time)
    
    def insert_at(self, index: int, value: int, run_time: float = 0.6):
        """Insert/place a value at a specific index."""
        if not (0 <= index < len(self.cells)):
            return
        
        # Update value
        self.values[index] = value
        
        # Update label
        box, label = self.cells[index]
        new_label = Text(str(value), font_size=28)
        new_label.move_to(box.get_center())
        
        self.scene.play(
            Transform(label, new_label),
            run_time=run_time
        )
    
    def set_opacity_range(self, start: int, end: int, opacity: float, run_time: float = 0.5):
        """Set opacity for a range of elements (for showing sorted/unsorted regions)."""
        animations = []
        for i in range(start, min(end, len(self.cells))):
            if 0 <= i < len(self.cells):
                animations.append(self.cells[i].animate.set_opacity(opacity))
        
        if animations:
            self.scene.play(*animations, run_time=run_time)
    
    def indicate_element(self, index: int, color=GREEN, run_time: float = 0.8):
        """Draw attention to an element with Indicate animation."""
        if 0 <= index < len(self.cells):
            self.scene.play(
                Indicate(self.cells[index], scale_factor=1.15, color=color),
                run_time=run_time
            )
    
    def add_label(self, key: str, text: str, position, run_time: float = 0.5):
        """Add a text label (e.g., 'Sorted', 'Key', 'Target')."""
        label = Text(text, font_size=24, color=BLUE)
        label.move_to(position)
        self.annotations[key] = label
        self.scene.play(FadeIn(label, shift=UP * 0.1), run_time=run_time)
    
    def remove_label(self, key: str, run_time: float = 0.3):
        """Remove a previously added label."""
        if key in self.annotations:
            self.scene.play(FadeOut(self.annotations[key]), run_time=run_time)
            del self.annotations[key]
    
    def cleanup(self, run_time: float = 0.5):
        """Remove all visual elements from the scene."""
        mobjects_to_remove = [self.cells]
        mobjects_to_remove.extend(self.highlights.values())
        mobjects_to_remove.extend(self.annotations.values())
        
        self.scene.play(
            *[FadeOut(mob) for mob in mobjects_to_remove],
            run_time=run_time
        )
