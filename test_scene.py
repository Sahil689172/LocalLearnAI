from manim import *


class BinarySearchDemo(Scene):
    def construct(self):

        title = Text("Binary Search")
        title.to_edge(UP)

        numbers = [10, 20, 30, 40, 50, 60, 70]

        boxes = VGroup()
        labels = VGroup()

        for number in numbers:
            box = Square(side_length=0.8)
            label = Text(str(number), font_size=24)

            label.move_to(box.get_center())

            boxes.add(box)
            labels.add(label)

        group = VGroup(boxes, labels)
        group.arrange(RIGHT, buff=0.1)

        self.play(Write(title))
        self.play(Create(boxes))
        self.play(Write(labels))

        # Highlight middle element
        self.play(
            boxes[3].animate.set_fill(
                opacity=0.5
            )
        )

        self.wait(2)