from rich.panel import Panel
from textual.reactive import Reactive

from animestreamer import streamer
from animestreamer.widgets import CustomWidget


class Sort(CustomWidget):
    sorts = ("seeders", "date", "size", "completed_downloads", "leechers")
    sort_ix = Reactive(0)
    reversed = Reactive(True)

    def render(self) -> Panel:
        content = []
        for ix, sort in enumerate(self.sorts):
            if ix == self.sort_ix:
                content.append(f"[bold red]{sort}[/bold red]")
            else:
                content.append(sort)
        order = "Desc" if self.reversed else "Asc"
        return Panel(
            "   ".join(content),
            title=f"Sorting [yellow][{order}][/yellow]",
            height=3,
            **self.get_style()
        )

    def next_sort(self) -> None:
        if self.sort_ix < len(self.sorts) - 1:
            self.sort_ix += 1
            self.sort()

    def prev_sort(self) -> None:
        if self.sort_ix > 0:
            self.sort_ix -= 1
            self.sort()

    def reverse_sort(self) -> None:
        self.reversed = not self.reversed
        self.sort()

    def sort(self) -> None:
        streamer.sort_results(key=self.get_current_sort(), reverse=self.reversed)

    def get_current_sort(self) -> str:
        return self.sorts[self.sort_ix]