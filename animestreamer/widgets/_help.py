from rich.panel import Panel

from animestreamer.widgets import CustomWidget


class Help(CustomWidget):

    def render(self) -> Panel:
        help_list = (
            "[b]H[/b] - toggles this sidebar",
            "[b]Arrows[/b] - navigation",
            "[b]Enter[/b] - confirm",
            "[b]Esc/Tab[/b] - remove focus",
            "[b]R[/b] - reverse sorting order",
            "[b]O[/b] - toggle title parsing",
            "[b]Q[/b] - quit"
        )
        return Panel(
            "\n\n".join(help_list),
            **self.get_style()
        )
