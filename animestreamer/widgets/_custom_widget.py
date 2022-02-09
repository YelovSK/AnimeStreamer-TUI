from rich import box
from rich.style import Style
from textual.reactive import Reactive
from textual.widget import Widget


class CustomWidget(Widget):
    """Add custom highlighting"""
    highlighted = Reactive(False)
    focused = Reactive(False)

    def __init__(self, focusable: bool = True):
        super().__init__()
        self.focusable = focusable  # eg Help sidebar shouldn't be focusable

    def get_style(self) -> dict[str, Style]:
        """Style kwargs for render() method"""
        return {
            "border_style": Style(color="green") if self.highlighted else Style(color="blue"),
            "box": box.DOUBLE if self.focused else box.SQUARE
        }

    def on_enter(self) -> None:
        if self.focusable:
            self.highlighted = True

    def on_leave(self) -> None:
        self.highlighted = False

    def on_focus(self) -> None:
        if self.focusable:
            self.focused = True

    def on_blur(self) -> None:
        self.focused = False
