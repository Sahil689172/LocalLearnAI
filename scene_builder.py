"""
LocalLearn AI - Deterministic Scene Builder
--------------------------------------------
Converts a compact LessonSpec JSON into a complete Manim Python script.

Ollama decides WHAT to show.
This module decides HOW to implement it in Manim.

No LLM calls are made here — this is pure deterministic Python.
"""

# ---------------------------------------------------------------------------
# SUPPORTED SCENE TYPES
#
#   title          simple centred title + subtitle
#   definition     heading + paragraph text
#   explanation    heading + bullet points
#   array_search   animated binary search on an array
#   array_sort     animated bubble sort on an array
#   formula        heading + big formula text
#   comparison     two-column side-by-side comparison
#   complexity     heading + big complexity label + brief note
#   summary        heading + bullet points (recap style)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# CODE GENERATION HELPERS
# ---------------------------------------------------------------------------

def _scene_title(scene: dict, idx: int) -> str:
    text     = scene.get("text", "Title")
    subtitle = scene.get("subtitle", "")
    dur      = float(scene.get("duration", 4))
    wait     = max(dur - 2.0, 1.0)

    lines = [
        f"        # --- Scene {idx}: title ---",
        f"        _title = Text({repr(text)}, font_size=52)",
    ]
    if subtitle:
        lines += [
            f"        _sub = Text({repr(subtitle)}, font_size=28)",
            f"        _sub.next_to(_title, DOWN, buff=0.3)",
            f"        self.play(Write(_title), run_time=1)",
            f"        self.play(FadeIn(_sub, shift=UP*0.2), run_time=0.8)",
            f"        self.wait({wait:.1f})",
            f"        self.play(FadeOut(VGroup(_title, _sub)), run_time=0.5)",
        ]
    else:
        lines += [
            f"        self.play(Write(_title), run_time=1)",
            f"        self.wait({wait:.1f})",
            f"        self.play(FadeOut(_title), run_time=0.5)",
        ]
    return "\n".join(lines)


def _scene_definition(scene: dict, idx: int) -> str:
    heading  = scene.get("heading", "Definition")
    text     = scene.get("text", "")
    dur      = float(scene.get("duration", 6))
    wait     = max(dur - 2.5, 1.5)

    # Wrap long text across two lines if needed
    if len(text) > 60:
        mid = len(text) // 2
        # Find nearest space to split
        for offset in range(20):
            if mid + offset < len(text) and text[mid + offset] == " ":
                mid = mid + offset
                break
            if mid - offset >= 0 and text[mid - offset] == " ":
                mid = mid - offset
                break
        line1 = text[:mid].strip()
        line2 = text[mid:].strip()
        text_code = (
            f"        _t1 = Text({repr(line1)}, font_size=26)\n"
            f"        _t2 = Text({repr(line2)}, font_size=26)\n"
            f"        _t2.next_to(_t1, DOWN, buff=0.18)\n"
            f"        _body = VGroup(_t1, _t2)\n"
        )
        body_var = "_body"
    else:
        text_code = f"        _body = Text({repr(text)}, font_size=28)\n"
        body_var  = "_body"

    return (
        f"        # --- Scene {idx}: definition ---\n"
        f"        _hd = Text({repr(heading)}, font_size=36)\n"
        f"        _hd.to_edge(UP, buff=0.35)\n"
        f"        self.play(Write(_hd), run_time=0.8)\n"
        + text_code +
        f"        {body_var}.move_to(ORIGIN)\n"
        f"        self.play(FadeIn({body_var}, shift=UP*0.2), run_time=0.8)\n"
        f"        self.wait({wait:.1f})\n"
        f"        self.play(FadeOut(VGroup(_hd, {body_var})), run_time=0.5)\n"
    )


def _scene_explanation(scene: dict, idx: int) -> str:
    heading = scene.get("heading", scene.get("text", "Explanation"))
    points  = scene.get("points", [])
    dur     = float(scene.get("duration", 8))
    wait    = max(dur - len(points) * 1.0 - 1.5, 1.0)

    lines = [
        f"        # --- Scene {idx}: explanation ---",
        f"        _hd = Text({repr(heading)}, font_size=36)",
        f"        _hd.to_edge(UP, buff=0.35)",
        f"        self.play(Write(_hd), run_time=0.8)",
        f"        _pts = VGroup()",
    ]
    for i, pt in enumerate(points):
        bullet = f"• {pt}"
        lines.append(f"        _pts.add(Text({repr(bullet)}, font_size=26))")
    lines += [
        f"        _pts.arrange(DOWN, aligned_edge=LEFT, buff=0.3)",
        f"        _pts.move_to(ORIGIN)",
    ]
    for i in range(len(points)):
        lines.append(
            f"        self.play(FadeIn(_pts[{i}], shift=RIGHT*0.2), run_time=0.6)"
        )
    lines += [
        f"        self.wait({wait:.1f})",
        f"        self.play(FadeOut(VGroup(_hd, _pts)), run_time=0.5)",
    ]
    return "\n".join(lines)


def _scene_array_search(scene: dict, idx: int) -> str:
    values = scene.get("values", [10, 20, 30, 40, 50, 60, 70])
    target = scene.get("target", values[len(values) // 2])
    dur    = float(scene.get("duration", 30))

    # Build binary search steps
    steps  = _binary_search_steps(values, target)
    n      = len(values)

    lines = [
        f"        # --- Scene {idx}: array_search (binary search) ---",
        f"        _bs_vals = {values}",
        f"        _bs_tgt  = {target}",
        f"",
        f"        _hd = Text('Binary Search', font_size=36)",
        f"        _hd.to_edge(UP, buff=0.35)",
        f"        self.play(Write(_hd), run_time=0.8)",
        f"",
        f"        # Build array",
        f"        _cells = VGroup()",
        f"        for _v in _bs_vals:",
        f"            _box   = Square(side_length=0.85, stroke_width=2.5)",
        f"            _lbl   = Text(str(_v), font_size=24)",
        f"            _lbl.move_to(_box.get_center())",
        f"            _cells.add(VGroup(_box, _lbl))",
        f"        _cells.arrange(RIGHT, buff=0.12)",
        f"        _cells.scale(0.95)",
        f"        _cells.move_to(ORIGIN + UP * 0.5)",
        f"        self.play(LaggedStart(",
        f"            *[FadeIn(c, shift=UP*0.15) for c in _cells],",
        f"            lag_ratio=0.1), run_time=1.2)",
        f"",
        f"        _tgt_lbl = Text(f'Target: {{_bs_tgt}}', font_size=28)",
        f"        _tgt_lbl.to_edge(DOWN, buff=0.5)",
        f"        self.play(Write(_tgt_lbl), run_time=0.7)",
        f"        self.wait(1)",
    ]

    # Animate each binary search step
    for step_num, step in enumerate(steps):
        lo, hi, mid = step["lo"], step["hi"], step["mid"]
        mid_val     = values[mid]
        found       = (mid_val == target)

        colour = "GREEN" if found else "YELLOW"

        lines += [
            f"",
            f"        # Step {step_num + 1}: lo={lo} hi={hi} mid={mid}",
            f"        _expl_{step_num} = Text(",
            f"            f'lo={lo}  mid={mid}  hi={hi}',",
            f"            font_size=24",
            f"        )",
            f"        _expl_{step_num}.to_edge(DOWN, buff=1.1)",
            f"        self.play(FadeIn(_expl_{step_num}), run_time=0.5)",
            f"",
            f"        _rect_{step_num} = SurroundingRectangle(",
            f"            _cells[{mid}], color={colour}, buff=0.06, stroke_width=3",
            f"        )",
            f"        self.play(Create(_rect_{step_num}), run_time=0.6)",
        ]

        if found:
            lines += [
                f"        _found_lbl = Text('FOUND!', font_size=32, color=GREEN)",
                f"        _found_lbl.next_to(_cells[{mid}], UP, buff=0.4)",
                f"        self.play(Write(_found_lbl), run_time=0.6)",
                f"        self.play(Indicate(_cells[{mid}], scale_factor=1.18, color=GREEN))",
                f"        self.wait(1.5)",
                f"        self.play(FadeOut(_found_lbl), FadeOut(_rect_{step_num}),",
                f"                  FadeOut(_expl_{step_num}), run_time=0.5)",
            ]
        else:
            if mid_val < target:
                fade_range = list(range(0, mid + 1))
                direction  = "right half"
            else:
                fade_range = list(range(mid, n))
                direction  = "left half"

            lines += [
                f"        _dir_lbl = Text(",
                f"            f'{{_bs_vals[{mid}]}} vs {{_bs_tgt}} — discard {direction}',",
                f"            font_size=22",
                f"        )",
                f"        _dir_lbl.to_edge(DOWN, buff=0.15)",
                f"        self.play(Write(_dir_lbl), run_time=0.5)",
                f"        self.wait(0.8)",
                f"        self.play(",
                f"            *[_cells[i].animate.set_opacity(0.18)",
                f"              for i in {fade_range}],",
                f"            run_time=0.7)",
                f"        self.wait(0.5)",
                f"        self.play(",
                f"            FadeOut(_rect_{step_num}),",
                f"            FadeOut(_expl_{step_num}),",
                f"            FadeOut(_dir_lbl),",
                f"            run_time=0.4)",
            ]

    lines += [
        f"",
        f"        self.wait(1)",
        f"        self.play(",
        f"            FadeOut(_hd), FadeOut(_cells), FadeOut(_tgt_lbl),",
        f"            run_time=0.6)",
    ]
    return "\n".join(lines)


def _binary_search_steps(values: list, target: int) -> list:
    """Return list of dicts describing each binary search step."""
    steps = []
    lo, hi = 0, len(values) - 1
    for _ in range(20):
        if lo > hi:
            break
        mid = (lo + hi) // 2
        steps.append({"lo": lo, "hi": hi, "mid": mid})
        if values[mid] == target:
            break
        elif values[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return steps


def _scene_array_sort(scene: dict, idx: int) -> str:
    values = scene.get("values", [5, 3, 8, 1, 9, 2, 7, 4, 6])
    dur    = float(scene.get("duration", 25))

    # Limit to 8 elements to keep animation manageable
    values = values[:8]

    lines = [
        f"        # --- Scene {idx}: array_sort (bubble sort) ---",
        f"        _sort_vals = {values}",
        f"        _svals = list(_sort_vals)",
        f"",
        f"        _hd = Text('Bubble Sort', font_size=36)",
        f"        _hd.to_edge(UP, buff=0.35)",
        f"        self.play(Write(_hd), run_time=0.8)",
        f"",
        f"        def _make_cells(vals):",
        f"            cells = VGroup()",
        f"            for v in vals:",
        f"                box = Square(side_length=0.85, stroke_width=2.5)",
        f"                lbl = Text(str(v), font_size=26)",
        f"                lbl.move_to(box.get_center())",
        f"                cells.add(VGroup(box, lbl))",
        f"            cells.arrange(RIGHT, buff=0.12)",
        f"            cells.move_to(ORIGIN)",
        f"            return cells",
        f"",
        f"        _cells = _make_cells(_svals)",
        f"        self.play(LaggedStart(",
        f"            *[FadeIn(c, shift=UP*0.15) for c in _cells],",
        f"            lag_ratio=0.1), run_time=1.0)",
        f"        self.wait(0.5)",
        f"",
        f"        # Bubble sort passes (up to 3 passes shown)",
        f"        _passes = 0",
        f"        for _pass in range(len(_svals) - 1):",
        f"            if _passes >= 3:",
        f"                break",
        f"            _swapped = False",
        f"            for _j in range(len(_svals) - 1 - _pass):",
        f"                if _svals[_j] > _svals[_j + 1]:",
        f"                    _svals[_j], _svals[_j + 1] = _svals[_j + 1], _svals[_j]",
        f"                    _swapped = True",
        f"                    _new = _make_cells(_svals)",
        f"                    self.play(ReplacementTransform(_cells, _new), run_time=0.5)",
        f"                    _cells = _new",
        f"            if not _swapped:",
        f"                break",
        f"            _passes += 1",
        f"",
        f"        _done = Text('Sorted!', font_size=32, color=GREEN)",
        f"        _done.to_edge(DOWN, buff=0.5)",
        f"        self.play(Write(_done), run_time=0.6)",
        f"        self.wait(1.5)",
        f"        self.play(FadeOut(VGroup(_hd, _cells, _done)), run_time=0.6)",
    ]
    return "\n".join(lines)


def _scene_formula(scene: dict, idx: int) -> str:
    text    = scene.get("text", "")
    formula = scene.get("formula", "")
    dur     = float(scene.get("duration", 7))
    wait    = max(dur - 2.0, 2.0)

    lines = [
        f"        # --- Scene {idx}: formula ---",
    ]
    if text:
        lines += [
            f"        _ftxt = Text({repr(text)}, font_size=30)",
            f"        _ftxt.to_edge(UP, buff=1.0)",
            f"        self.play(Write(_ftxt), run_time=0.8)",
        ]
    if formula:
        lines += [
            f"        _fml = Text({repr(formula)}, font_size=56)",
            f"        _fml.move_to(ORIGIN)",
            f"        self.play(Write(_fml), run_time=1.0)",
        ]
    lines += [f"        self.wait({wait:.1f})"]
    objs = []
    if text:
        objs.append("_ftxt")
    if formula:
        objs.append("_fml")
    if objs:
        lines.append(
            f"        self.play(FadeOut(VGroup({', '.join(objs)})), run_time=0.5)"
        )
    return "\n".join(lines)


def _scene_comparison(scene: dict, idx: int) -> str:
    items = scene.get("items", [])
    dur   = float(scene.get("duration", 8))
    wait  = max(dur - 2.5, 2.0)

    lines = [
        f"        # --- Scene {idx}: comparison ---",
        f"        _cmp_groups = VGroup()",
    ]
    for item in items:
        label = item.get("label", "")
        value = item.get("value", "")
        lines += [
            f"        _ci_lbl = Text({repr(label)}, font_size=30)",
            f"        _ci_val = Text({repr(value)}, font_size=40)",
            f"        _ci_grp = VGroup(_ci_lbl, _ci_val)",
            f"        _ci_grp.arrange(DOWN, buff=0.3)",
            f"        _cmp_groups.add(_ci_grp)",
        ]
    lines += [
        f"        _cmp_groups.arrange(RIGHT, buff=2.0)",
        f"        _cmp_groups.move_to(ORIGIN)",
        f"        self.play(FadeIn(_cmp_groups, shift=UP*0.2), run_time=1.0)",
        f"        self.wait({wait:.1f})",
        f"        self.play(FadeOut(_cmp_groups), run_time=0.5)",
    ]
    return "\n".join(lines)


def _scene_complexity(scene: dict, idx: int) -> str:
    text  = scene.get("text", "Time Complexity")
    value = scene.get("value", scene.get("formula", "O(n)"))
    dur   = float(scene.get("duration", 7))
    wait  = max(dur - 2.5, 2.0)

    return (
        f"        # --- Scene {idx}: complexity ---\n"
        f"        _cx_hd  = Text({repr(text)}, font_size=34)\n"
        f"        _cx_hd.to_edge(UP, buff=0.8)\n"
        f"        _cx_val = Text({repr(value)}, font_size=64)\n"
        f"        _cx_val.move_to(ORIGIN)\n"
        f"        self.play(Write(_cx_hd), run_time=0.8)\n"
        f"        self.play(Write(_cx_val), run_time=1.0)\n"
        f"        self.wait({wait:.1f})\n"
        f"        self.play(FadeOut(VGroup(_cx_hd, _cx_val)), run_time=0.5)\n"
    )


def _scene_summary(scene: dict, idx: int) -> str:
    text   = scene.get("text", "Summary")
    points = scene.get("points", [])
    dur    = float(scene.get("duration", 8))
    wait   = max(dur - len(points) * 0.8 - 1.5, 1.5)

    lines = [
        f"        # --- Scene {idx}: summary ---",
        f"        _sm_hd = Text({repr(text)}, font_size=36)",
        f"        _sm_hd.to_edge(UP, buff=0.35)",
        f"        self.play(Write(_sm_hd), run_time=0.8)",
        f"        _sm_pts = VGroup()",
    ]
    for pt in points:
        bullet = f"• {pt}"
        lines.append(f"        _sm_pts.add(Text({repr(bullet)}, font_size=26))")
    lines += [
        f"        _sm_pts.arrange(DOWN, aligned_edge=LEFT, buff=0.3)",
        f"        _sm_pts.move_to(ORIGIN)",
    ]
    for i in range(len(points)):
        lines.append(
            f"        self.play(FadeIn(_sm_pts[{i}], shift=RIGHT*0.2), run_time=0.5)"
        )
    lines += [
        f"        self.wait({wait:.1f})",
        f"        self.play(FadeOut(VGroup(_sm_hd, _sm_pts)), run_time=0.5)",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# DISPATCH TABLE
# ---------------------------------------------------------------------------

_SCENE_BUILDERS = {
    "title":       _scene_title,
    "definition":  _scene_definition,
    "explanation": _scene_explanation,
    "array_search": _scene_array_search,
    "array_sort":  _scene_array_sort,
    "formula":     _scene_formula,
    "comparison":  _scene_comparison,
    "complexity":  _scene_complexity,
    "summary":     _scene_summary,
}

# ---------------------------------------------------------------------------
# PUBLIC API
# ---------------------------------------------------------------------------

def build_manim_code(lesson_spec: dict) -> str:
    """
    Convert a LessonSpec dict into a complete Manim Python script.

    Returns:
        Python source code as a string (no LLM call — purely deterministic).
    """
    topic    = lesson_spec.get("topic", lesson_spec.get("title", "Topic"))
    scenes   = lesson_spec.get("scenes", [])

    body_parts = []
    for idx, scene in enumerate(scenes, start=1):
        scene_type = scene.get("type", "definition")
        builder    = _SCENE_BUILDERS.get(scene_type)

        if builder is None:
            # Unknown type — fall back to definition
            fallback = dict(scene)
            fallback["type"] = "definition"
            fallback.setdefault("heading", scene.get("type", "").replace("_", " ").title())
            fallback.setdefault("text",    scene.get("text", ""))
            body_parts.append(_scene_definition(fallback, idx))
        else:
            body_parts.append(builder(scene, idx))

    body = "\n\n".join(body_parts)

    code = (
        "from manim import *\n"
        "\n"
        "\n"
        "class LocalLearnScene(Scene):\n"
        "\n"
        f"    # Generated by LocalLearn AI\n"
        f"    # Topic: {topic}\n"
        "\n"
        "    def construct(self):\n"
        "\n"
        f"{body}\n"
        "\n"
        "        # --- Outro ---\n"
        "        _outro = Text('LocalLearn AI', font_size=48)\n"
        "        _outro_sub = Text('Learn  ·  Visualize  ·  Understand', font_size=26)\n"
        "        _outro_sub.next_to(_outro, DOWN, buff=0.3)\n"
        "        self.play(Write(_outro), run_time=1.0)\n"
        "        self.play(FadeIn(_outro_sub), run_time=0.8)\n"
        "        self.wait(3)\n"
    )
    return code
