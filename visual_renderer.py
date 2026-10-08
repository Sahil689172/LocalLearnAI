"""
Deterministic visual renderer for LocalLearn AI.

This module consumes structured visual plans from lesson specs and generates
high-quality Manim animations using algorithm-specific renderers.
"""

from typing import Any

# Manim and visuals imports are deferred — they require the main .venv
# which has Manim installed. The .tts-venv does not have Manim.
# Imports happen inside VisualRenderService.generate_scene_file() only.


try:
    from manim import Scene, VGroup, Text, Wait
    from visuals.base import VisualRenderer, VisualAction
    from visuals.insertion_sort import InsertionSortRenderer
    from visuals.binary_search import BinarySearchRenderer
    from visuals.linear_search import LinearSearchRenderer
    from visuals.bubble_sort import BubbleSortRenderer
    from visuals.selection_sort import SelectionSortRenderer
    _MANIM_AVAILABLE = True
    _BaseScene = Scene
except ImportError:
    _MANIM_AVAILABLE = False
    _BaseScene = object  # fallback so class definition doesn't fail


class LessonScene(_BaseScene):
    """
    Main Manim scene that orchestrates beat-by-beat animation.
    
    This scene is constructed dynamically from lesson beats with visual plans
    and audio timing information.
    """
    
    def __init__(self, beats: list[dict], **kwargs):
        """
        Initialize the lesson scene.
        
        Parameters
        ----------
        beats : list[dict]
            Enriched beats with visual plans and timing data.
            Each beat must have:
            - audio_duration: duration in seconds
            - visual: {type, action, data, emphasis (optional)}
            - language: language code
        **kwargs
            Additional arguments passed to Scene.
        """
        super().__init__(**kwargs)
        self.beats = beats
        self.renderer_cache: dict[str, VisualRenderer] = {}
    
    def construct(self):
        """
        Main Manim construct method that builds the animation.
        
        This method is called by Manim to generate the scene.
        It processes beats sequentially, delegating to algorithm-specific
        renderers based on visual.type.
        
        Ensures final video duration matches total audio duration.
        """
        # Calculate total audio duration for synchronization
        total_audio_duration = sum(beat.get("audio_duration", 3.0) for beat in self.beats)
        
        print(f"[LessonScene] Starting scene construction")
        print(f"[LessonScene] Total beats: {len(self.beats)}")
        print(f"[LessonScene] Total audio duration: {total_audio_duration:.2f}s")
        
        for i, beat in enumerate(self.beats):
            beat_duration = beat.get("audio_duration", 3.0)
            print(f"[LessonScene] Rendering beat {i+1}/{len(self.beats)}: {beat.get('id', '?')} (duration: {beat_duration:.2f}s)")
            self._render_beat(beat)
        
        # CRITICAL: Add buffer at the end to ensure video doesn't cut off early
        # This addresses the issue where video (16.7s) ends before audio (27.2s)
        # The buffer ensures the video timeline matches or exceeds the audio timeline
        buffer_duration = 1.0  # 1 second buffer
        print(f"[LessonScene] Adding {buffer_duration}s buffer at end")
        self.wait(buffer_duration)
        
        actual_duration = total_audio_duration + buffer_duration
        print(f"[LessonScene] Scene construction complete")
        print(f"[LessonScene] Expected video duration: {actual_duration:.2f}s")

    
    def _render_beat(self, beat: dict) -> None:
        """
        Render a single beat with its visual plan.
        
        Parameters
        ----------
        beat : dict
            Beat with visual plan and timing.
        """
        visual = beat.get("visual")
        duration = beat.get("audio_duration", 3.0)
        language = beat.get("language", "en")
        
        if not visual:
            # No visual plan - just wait for the audio duration
            self.wait(duration)
            return
        
        visual_type = visual.get("type")
        action = visual.get("action")
        data = visual.get("data", {})
        emphasis = visual.get("emphasis", [])
        
        # Route to appropriate renderer based on visual type
        if visual_type == "array":
            self._render_array_visual(action, data, emphasis, duration, language)
        elif visual_type == "text":
            self._render_text_visual(action, data, duration, language)
        elif visual_type == "diagram":
            self._render_diagram_visual(action, data, duration, language)
        else:
            # Unknown visual type - just wait
            print(f"[LessonScene] Warning: unknown visual type '{visual_type}'")
            self.wait(duration)
    
    def _render_array_visual(
        self,
        action: str,
        data: dict,
        emphasis: list[int],
        duration: float,
        language: str
    ) -> None:
        """
        Render array-based visualizations (sorting, searching algorithms).
        
        Routes to algorithm-specific renderers based on the action type.
        """
        # Determine which algorithm renderer to use based on action
        # (insertion_sort, binary_search, bubble_sort, selection_sort)
        
        # Actions are grouped by algorithm:
        insertion_actions = {
            "show_array", "select_key", "compare", "shift", 
            "insert", "mark_sorted", "show_complexity"
        }
        binary_search_actions = {
            "show_array", "check_middle", "found", 
            "eliminate_half", "show_complexity"
        }
        linear_search_actions = {
            "show_array", "set_pointer", "move_pointer", "compare_element",
            "found", "not_found", "show_result", "show_complexity"
        }
        bubble_sort_actions = {
            "show_array", "compare_adjacent", "swap", 
            "mark_sorted", "show_complexity"
        }
        selection_sort_actions = {
            "show_array", "find_min", "swap_with_min", 
            "mark_sorted", "show_complexity"
        }
        
        # Determine renderer type
        renderer_type = None
        if action in insertion_actions:
            renderer_type = "insertion_sort"
        elif action in binary_search_actions:
            renderer_type = "binary_search"
        elif action in linear_search_actions:
            renderer_type = "linear_search"
        elif action in bubble_sort_actions:
            renderer_type = "bubble_sort"
        elif action in selection_sort_actions:
            renderer_type = "selection_sort"
        else:
            print(f"[LessonScene] Warning: unknown array action '{action}'")
            self.wait(duration)
            return
        
        # Get or create renderer
        renderer = self._get_renderer(renderer_type, language)
        
        # Execute the action
        try:
            renderer.render_action(
                VisualAction(
                    type="array",
                    action=action,
                    data=data,
                    emphasis=emphasis,
                    duration=duration,
                ),
                beat_duration=duration,
            )
        except Exception as e:
            print(f"[LessonScene] Error executing action '{action}': {e}")
            # Fallback: just wait
            self.wait(duration)
    
    def _render_text_visual(
        self,
        action: str,
        data: dict,
        duration: float,
        language: str
    ) -> None:
        """
        Render text-based visualizations (titles, explanations, labels).
        """
        text_content = data.get("text", "")
        if not text_content:
            self.wait(duration)
            return
        
        # Simple text display
        text_obj = Text(text_content, font_size=36)
        
        if action == "show":
            self.play(text_obj.animate.scale(1.0), run_time=min(1.0, duration * 0.3))
            self.wait(max(0, duration - 1.0))
            self.play(text_obj.animate.scale(0), run_time=min(1.0, duration * 0.2))
        elif action == "fade_in":
            self.play(text_obj.animate.set_opacity(1), run_time=duration)
        elif action == "fade_out":
            self.play(text_obj.animate.set_opacity(0), run_time=duration)
        else:
            # Default: show for duration
            self.add(text_obj)
            self.wait(duration)
            self.remove(text_obj)
    
    def _render_diagram_visual(
        self,
        action: str,
        data: dict,
        duration: float,
        language: str
    ) -> None:
        """
        Render diagram-based visualizations (flowcharts, trees, graphs).
        
        Not yet implemented - placeholder for future expansion.
        """
        print(f"[LessonScene] Warning: diagram visuals not yet implemented")
        self.wait(duration)
    
    def _get_renderer(self, renderer_type: str, language: str) -> VisualRenderer:
        """
        Get or create a renderer instance for the given type.
        
        Renderers are cached to maintain state across beats (e.g., array persistence).
        """
        cache_key = f"{renderer_type}_{language}"
        
        if cache_key not in self.renderer_cache:
            if renderer_type == "insertion_sort":
                self.renderer_cache[cache_key] = InsertionSortRenderer(self, language=language)
            elif renderer_type == "binary_search":
                self.renderer_cache[cache_key] = BinarySearchRenderer(self, language=language)
            elif renderer_type == "linear_search":
                self.renderer_cache[cache_key] = LinearSearchRenderer(self, language=language)
            elif renderer_type == "bubble_sort":
                self.renderer_cache[cache_key] = BubbleSortRenderer(self, language=language)
            elif renderer_type == "selection_sort":
                self.renderer_cache[cache_key] = SelectionSortRenderer(self, language=language)
            else:
                raise ValueError(f"Unknown renderer type: {renderer_type}")
        
        return self.renderer_cache[cache_key]


class VisualRenderService:
    """
    Service that generates Manim scene files from lesson beats.
    
    This is the bridge between timing service output and Manim rendering.
    """
    
    def __init__(self, output_dir: str = "."):
        """
        Initialize the visual render service.
        
        Parameters
        ----------
        output_dir : str, optional
            Directory where scene files will be written.
        """
        self.output_dir = output_dir
    
    def create_scene_class(self, beats: list[dict]) -> type[Scene]:
        """
        Create a Scene class dynamically for the given beats.
        
        Parameters
        ----------
        beats : list[dict]
            Enriched beats with visual plans and timing.
        
        Returns
        -------
        type[Scene]
            A Scene subclass ready to be rendered by Manim.
        """
        # Create a closure that captures beats
        def construct_method(self):
            scene = LessonScene(beats)
            scene.construct()
        
        # Create dynamic class
        SceneClass = type(
            "GeneratedLessonScene",
            (LessonScene,),
            {
                "__init__": lambda self, **kwargs: LessonScene.__init__(self, beats, **kwargs),
            }
        )
        
        return SceneClass
    
    def generate_scene_file(
        self,
        beats: list[dict],
        output_filename: str = "generated_scene.py"
    ) -> str:
        """
        Generate a standalone Python file with a Manim scene.
        
        This creates a .py file that can be rendered with `manim -pql file.py SceneName`.
        
        Parameters
        ----------
        beats : list[dict]
            Enriched beats with visual plans and timing.
        output_filename : str, optional
            Name of the output Python file.
        
        Returns
        -------
        str
            Path to the generated scene file.
        """
        # Deferred: only needed when actually generating a scene file
        try:
            from language_codes import LanguageCode  # noqa: F401
        except ImportError:
            pass
        import json
        from pathlib import Path
        
        output_path = Path(self.output_dir) / output_filename
        
        # Serialize beats to embed in the file
        beats_json = json.dumps(beats, indent=2)
        
        scene_code = f'''"""
Auto-generated Manim scene for LocalLearn AI.

This file was generated by visual_renderer.py and contains a complete
Manim scene with beats and visual plans embedded.

To render:
    manim -pql {output_filename} LessonScene
"""

from manim import Scene
import json

# Import visual renderers
import sys
from pathlib import Path

# Add parent directory to path to import local modules
sys.path.insert(0, str(Path(__file__).parent))

from visual_renderer import LessonScene

# Embedded lesson beats with timing and visual plans
BEATS = {beats_json}


class GeneratedLessonScene(LessonScene):
    """The main scene to render."""
    
    def __init__(self, **kwargs):
        super().__init__(beats=BEATS, **kwargs)


# For convenience, expose as LessonScene too
LessonScene = GeneratedLessonScene
'''
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(scene_code)
        
        print(f"[VisualRenderService] Generated scene file: {output_path}")
        
        return str(output_path)
    
    def validate_beats(self, beats: list[dict]) -> list[str]:
        """
        Validate that beats have required fields for rendering.
        
        Parameters
        ----------
        beats : list[dict]
            Beats to validate.
        
        Returns
        -------
        list[str]
            List of validation errors (empty if valid).
        """
        errors = []
        
        for i, beat in enumerate(beats):
            if not isinstance(beat, dict):
                errors.append(f"Beat {i} is not a dict")
                continue
            
            # Check required fields
            if "audio_duration" not in beat:
                errors.append(f"Beat {i} ({beat.get('id', '?')}) missing 'audio_duration'")
            
            # Visual plan validation
            visual = beat.get("visual")
            if visual:
                if not isinstance(visual, dict):
                    errors.append(f"Beat {i} ({beat.get('id', '?')}) visual is not a dict")
                    continue
                
                if "type" not in visual:
                    errors.append(f"Beat {i} ({beat.get('id', '?')}) visual missing 'type'")
                if "action" not in visual:
                    errors.append(f"Beat {i} ({beat.get('id', '?')}) visual missing 'action'")
                if "data" not in visual:
                    errors.append(f"Beat {i} ({beat.get('id', '?')}) visual missing 'data'")
        
        return errors


def create_visual_renderer(output_dir: str = ".") -> VisualRenderService:
    """
    Factory function to create a VisualRenderService.
    
    Parameters
    ----------
    output_dir : str, optional
        Directory for output files.
    
    Returns
    -------
    VisualRenderService
        Ready-to-use visual render service.
    """
    return VisualRenderService(output_dir=output_dir)
