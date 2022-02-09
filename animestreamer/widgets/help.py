from rich.panel import Panel

from animestreamer.widgets.custom_widget import CustomWidget


class Help(CustomWidget):

    def render(self) -> Panel:
        help_list = (
            "[b]H[/b] - toggles this sidebar",
            "[b]left_arrow[/b] - previous page (if results focused)",
            "[b]right_arrow[/b] - next page (if results focused)",
            "[b]up_arrow[/b] - select previous form (green)",
            "[b]down_arrow[/b] - select next form (green)",
            "[b]ENTER[/b] - focus selected form (double line)",
            "[b]TAB[/b] - remove focus from form",
            "[b]R[/b] - reverse sorting order",
            "[b]P[/b] - play selected torrent",
            "[b]Q[/b] - quit application"
        )
        return Panel(
            "\n\n".join(help_list),
            **self.get_style()
        )