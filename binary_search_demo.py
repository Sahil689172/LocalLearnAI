from manim import *


class BinarySearchExplainer(Scene):

    # ============================================================
    # HELPER FUNCTIONS
    # ============================================================

    def create_array(self, numbers):
        """
        Create an array where every number is grouped
        with its own box.

        Example:

        VGroup(
            VGroup(box1, label1),
            VGroup(box2, label2),
            ...
        )
        """

        cells = VGroup()

        for number in numbers:

            box = RoundedRectangle(
                width=1.15,
                height=0.95,
                corner_radius=0.12,
                stroke_width=3,
            )

            label = Text(
                str(number),
                font_size=28
            )

            # Put number INSIDE its own box
            label.move_to(box.get_center())

            # Very important:
            # box + label are one object
            cell = VGroup(box, label)

            cells.add(cell)

        # Arrange COMPLETE CELLS
        cells.arrange(
            RIGHT,
            buff=0.18
        )

        return cells

    def create_pointer(self, text, target, direction=DOWN):
        """
        Creates a label and arrow pointing toward a target.
        """

        label = Text(
            text,
            font_size=22
        )

        label.next_to(
            target,
            direction,
            buff=0.45
        )

        arrow = Arrow(
            start=label.get_top(),
            end=target.get_bottom(),
            buff=0.08,
            stroke_width=3,
            max_tip_length_to_length_ratio=0.15
        )

        return VGroup(label, arrow)

    # ============================================================
    # MAIN SCENE
    # ============================================================

    def construct(self):

        # ========================================================
        # 1. TITLE
        # ========================================================

        title = Text(
            "Binary Search",
            font_size=52
        )

        subtitle = Text(
            "How can we find an element efficiently?",
            font_size=28
        )

        subtitle.next_to(
            title,
            DOWN,
            buff=0.25
        )

        title_group = VGroup(
            title,
            subtitle
        )

        self.play(
            Write(title),
            FadeIn(subtitle, shift=UP * 0.2)
        )

        self.wait(2)

        self.play(
            FadeOut(title_group)
        )

        # ========================================================
        # 2. INTRODUCTION
        # ========================================================

        heading = Text(
            "Binary Search works on sorted data",
            font_size=34
        )

        heading.to_edge(
            UP,
            buff=0.35
        )

        self.play(
            Write(heading)
        )

        numbers = [
            10,
            20,
            30,
            40,
            50,
            60,
            70
        ]

        array = self.create_array(numbers)

        # Keep array comfortably inside screen
        array.scale(0.95)

        array.move_to(
            ORIGIN + DOWN * 0.25
        )

        self.play(
            LaggedStart(
                *[
                    FadeIn(
                        cell,
                        shift=UP * 0.2
                    )
                    for cell in array
                ],
                lag_ratio=0.12
            )
        )

        explanation = Text(
            "The values are arranged from smallest to largest.",
            font_size=25
        )

        explanation.to_edge(
            DOWN,
            buff=0.35
        )

        self.play(
            Write(explanation)
        )

        self.wait(3)

        self.play(
            FadeOut(heading),
            FadeOut(explanation)
        )

        # ========================================================
        # 3. TARGET
        # ========================================================

        heading = Text(
            "Our target is 60",
            font_size=36
        )

        heading.to_edge(
            UP,
            buff=0.35
        )

        self.play(
            Write(heading)
        )

        target_label = Text(
            "TARGET = 60",
            font_size=30
        )

        target_label.to_edge(
            DOWN,
            buff=0.35
        )

        self.play(
            Write(target_label)
        )

        target_box = SurroundingRectangle(
            array[5],
            color=YELLOW,
            buff=0.10,
            stroke_width=4
        )

        self.play(
            Create(target_box)
        )

        self.wait(3)

        self.play(
            FadeOut(heading),
            FadeOut(target_label),
            FadeOut(target_box)
        )

        # ========================================================
        # 4. LOW MID HIGH
        # ========================================================

        heading = Text(
            "Step 1: Check the middle",
            font_size=36
        )

        heading.to_edge(
            UP,
            buff=0.35
        )

        self.play(
            Write(heading)
        )

        low_pointer = self.create_pointer(
            "LOW",
            array[0]
        )

        mid_pointer = self.create_pointer(
            "MID",
            array[3]
        )

        high_pointer = self.create_pointer(
            "HIGH",
            array[6]
        )

        # Position pointer groups separately
        low_pointer.next_to(
            array[0],
            DOWN,
            buff=0.35
        )

        mid_pointer.next_to(
            array[3],
            DOWN,
            buff=0.35
        )

        high_pointer.next_to(
            array[6],
            DOWN,
            buff=0.35
        )

        # Scale slightly so they remain compact
        low_pointer.scale(0.85)
        mid_pointer.scale(0.85)
        high_pointer.scale(0.85)

        self.play(
            FadeIn(low_pointer),
            FadeIn(mid_pointer),
            FadeIn(high_pointer)
        )

        self.wait(2)

        # Highlight middle
        mid_highlight = SurroundingRectangle(
            array[3],
            color=YELLOW,
            buff=0.10,
            stroke_width=4
        )

        self.play(
            Create(mid_highlight)
        )

        comparison = Text(
            "Middle value = 40",
            font_size=30
        )

        comparison.to_edge(
            DOWN,
            buff=0.35
        )

        self.play(
            Write(comparison)
        )

        self.wait(3)

        # ========================================================
        # 5. COMPARE TARGET
        # ========================================================

        self.play(
            FadeOut(comparison)
        )

        comparison2 = Text(
            "60 is greater than 40",
            font_size=30
        )

        comparison2.to_edge(
            DOWN,
            buff=0.35
        )

        self.play(
            Write(comparison2)
        )

        self.wait(3)

        # ========================================================
        # 6. DISCARD LEFT HALF
        # ========================================================

        self.play(
            FadeOut(
                low_pointer
            ),
            FadeOut(
                mid_pointer
            ),
            FadeOut(
                high_pointer
            ),
            FadeOut(
                mid_highlight
            ),
            FadeOut(
                comparison2
            )
        )

        heading2 = Text(
            "The left half can be discarded",
            font_size=34
        )

        heading2.to_edge(
            UP,
            buff=0.35
        )

        self.play(
            Transform(
                heading,
                heading2
            )
        )

        # Fade the eliminated cells
        self.play(
            *[
                cell.animate.set_opacity(0.18)
                for cell in array[:4]
            ]
        )

        discard_text = Text(
            "No need to check these values again",
            font_size=27
        )

        discard_text.to_edge(
            DOWN,
            buff=0.35
        )

        self.play(
            Write(discard_text)
        )

        self.wait(3)

        self.play(
            FadeOut(discard_text)
        )

        # ========================================================
        # 7. SECOND SEARCH
        # ========================================================

        heading3 = Text(
            "Step 2: Search the remaining half",
            font_size=34
        )

        heading3.to_edge(
            UP,
            buff=0.35
        )

        self.play(
            Transform(
                heading,
                heading3
            )
        )

        low_pointer2 = self.create_pointer(
            "LOW",
            array[4]
        )

        mid_pointer2 = self.create_pointer(
            "MID",
            array[5]
        )

        high_pointer2 = self.create_pointer(
            "HIGH",
            array[6]
        )

        low_pointer2.scale(0.82)
        mid_pointer2.scale(0.82)
        high_pointer2.scale(0.82)

        # Position carefully
        low_pointer2.next_to(
            array[4],
            DOWN,
            buff=0.35
        )

        mid_pointer2.next_to(
            array[5],
            DOWN,
            buff=0.35
        )

        high_pointer2.next_to(
            array[6],
            DOWN,
            buff=0.35
        )

        self.play(
            FadeIn(low_pointer2),
            FadeIn(mid_pointer2),
            FadeIn(high_pointer2)
        )

        self.wait(2)

        # ========================================================
        # 8. FIND TARGET
        # ========================================================

        second_highlight = SurroundingRectangle(
            array[5],
            color=GREEN,
            buff=0.10,
            stroke_width=4
        )

        self.play(
            Create(second_highlight)
        )

        comparison3 = Text(
            "60 = 60",
            font_size=32
        )

        comparison3.to_edge(
            DOWN,
            buff=0.35
        )

        self.play(
            Write(comparison3)
        )

        self.wait(2)

        found_text = Text(
            "TARGET FOUND!",
            font_size=38,
            color=GREEN
        )

        found_text.to_edge(
            DOWN,
            buff=0.35
        )

        self.play(
            FadeOut(comparison3),
            Write(found_text)
        )

        self.play(
            Indicate(
                array[5],
                scale_factor=1.15,
                color=GREEN
            )
        )

        self.wait(3)

        # ========================================================
        # 9. CLEAR SEARCH VISUALIZATION
        # ========================================================

        self.play(
            FadeOut(heading),
            FadeOut(low_pointer2),
            FadeOut(mid_pointer2),
            FadeOut(high_pointer2),
            FadeOut(second_highlight),
            FadeOut(found_text)
        )

        # Restore faded cells
        self.play(
            *[
                cell.animate.set_opacity(1)
                for cell in array
            ]
        )

        # ========================================================
        # 10. WHY BINARY SEARCH IS FAST
        # ========================================================

        speed_title = Text(
            "Why is Binary Search so fast?",
            font_size=38
        )

        speed_title.to_edge(
            UP,
            buff=0.35
        )

        self.play(
            Write(speed_title)
        )

        # Move array upward
        self.play(
            array.animate.shift(UP * 1.0)
        )

        step1 = Text(
            "7 elements",
            font_size=28
        )

        step2 = Text(
            "↓",
            font_size=32
        )

        step3 = Text(
            "3 elements",
            font_size=28
        )

        step4 = Text(
            "↓",
            font_size=32
        )

        step5 = Text(
            "1 element",
            font_size=28
        )

        reduction = VGroup(
            step1,
            step2,
            step3,
            step4,
            step5
        )

        reduction.arrange(
            DOWN,
            buff=0.15
        )

        reduction.move_to(
            DOWN * 1.2
        )

        self.play(
            Write(step1)
        )

        self.play(
            Write(step2),
            Write(step3)
        )

        self.play(
            Write(step4),
            Write(step5)
        )

        self.wait(3)

        # ========================================================
        # 11. COMPLEXITY
        # ========================================================

        complexity = Text(
            "Time Complexity: O(log n)",
            font_size=34
        )

        complexity.to_edge(
            DOWN,
            buff=0.35
        )

        self.play(
            Write(complexity)
        )

        self.wait(4)

        self.play(
            FadeOut(speed_title),
            FadeOut(reduction),
            FadeOut(complexity),
            FadeOut(array)
        )

        # ========================================================
        # 12. LINEAR SEARCH COMPARISON
        # ========================================================

        comparison_title = Text(
            "Binary Search vs Linear Search",
            font_size=38
        )

        comparison_title.to_edge(
            UP,
            buff=0.35
        )

        self.play(
            Write(comparison_title)
        )

        linear_title = Text(
            "Linear Search",
            font_size=30
        )

        binary_title = Text(
            "Binary Search",
            font_size=30
        )

        linear_complexity = Text(
            "O(n)",
            font_size=40
        )

        binary_complexity = Text(
            "O(log n)",
            font_size=40
        )

        linear_group = VGroup(
            linear_title,
            linear_complexity
        )

        binary_group = VGroup(
            binary_title,
            binary_complexity
        )

        linear_group.arrange(
            DOWN,
            buff=0.4
        )

        binary_group.arrange(
            DOWN,
            buff=0.4
        )

        comparison = VGroup(
            linear_group,
            binary_group
        )

        comparison.arrange(
            RIGHT,
            buff=2.5
        )

        comparison.move_to(
            ORIGIN
        )

        self.play(
            FadeIn(
                linear_group,
                shift=LEFT
            ),
            FadeIn(
                binary_group,
                shift=RIGHT
            )
        )

        self.wait(4)

        # ========================================================
        # 13. SUMMARY
        # ========================================================

        self.play(
            FadeOut(comparison_title),
            FadeOut(comparison)
        )

        summary_title = Text(
            "Binary Search: The Four Steps",
            font_size=38
        )

        summary_title.to_edge(
            UP,
            buff=0.35
        )

        self.play(
            Write(summary_title)
        )

        point1 = Text(
            "1. Start with sorted data",
            font_size=27
        )

        point2 = Text(
            "2. Check the middle element",
            font_size=27
        )

        point3 = Text(
            "3. Eliminate half of the search space",
            font_size=27
        )

        point4 = Text(
            "4. Repeat until the target is found",
            font_size=27
        )

        points = VGroup(
            point1,
            point2,
            point3,
            point4
        )

        points.arrange(
            DOWN,
            aligned_edge=LEFT,
            buff=0.35
        )

        points.move_to(
            ORIGIN
        )

        for point in points:
            self.play(
                FadeIn(
                    point,
                    shift=RIGHT * 0.25
                )
            )

        self.wait(3)

        # ========================================================
        # 14. FINAL
        # ========================================================

        self.play(
            FadeOut(summary_title),
            FadeOut(points)
        )

        final_title = Text(
            "LocalLearn AI",
            font_size=54
        )

        final_subtitle = Text(
            "Learn • Visualize • Understand",
            font_size=28
        )

        final_subtitle.next_to(
            final_title,
            DOWN,
            buff=0.3
        )

        final_group = VGroup(
            final_title,
            final_subtitle
        )

        self.play(
            Write(final_title)
        )

        self.play(
            FadeIn(final_subtitle)
        )

        self.wait(4)