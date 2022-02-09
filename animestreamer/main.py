from __future__ import annotations

from rich import box
from rich.style import Style
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from textual.app import App
from textual.widgets import Header, Footer
from textual.widget import Widget
from textual.reactive import Reactive
from textual_inputs import TextInput

# from animestreamer.streamer import AnimeStreamer  # package install
from streamer import AnimeStreamer  # running from terminal

streamer = AnimeStreamer()


def get_border_style(highlighted: bool) -> Style:
    HIGHLIGHT_STYLE = Style(color="green")
    NORMAL_STYLE = Style(color="blue")
    if highlighted:
        return HIGHLIGHT_STYLE
    return NORMAL_STYLE


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


class CustomFooter(Footer):

    def make_key_text(self) -> Text:
        """Override for styling and show only keys with description"""
        text = Text(
            style="white on rgb(98,98,98)",
            no_wrap=True,
            overflow="ellipsis",
            justify="left",
            end="",
        )
        for binding in self.app.bindings.shown_keys:
            if not binding.description:
                continue
            key_display = (
                binding.key.upper()
                if binding.key_display is None
                else binding.key_display
            )
            hovered = self.highlight_key == binding.key
            key_text = Text.assemble(
                (f" {key_display} ", "reverse" if hovered else "default on default"),
                f" {binding.description} ",
                meta={"@click": f"app.press('{binding.key}')", "key": binding.key},
            )
            text.append_text(key_text)
        return text


class CustomHeader(Header):

    def __init__(self) -> None:
        super().__init__(tall=False, style=Style(color="white", bgcolor="rgb(98,98,98)"))

    def render(self) -> Table:
        """Override for title"""
        header_table = Table.grid(padding=(0, 1), expand=True)
        header_table.add_column(justify="left", ratio=0, width=8)
        header_table.add_column("title", justify="center", ratio=1)
        header_table.add_column("clock", justify="right", width=8)
        header_table.add_row(
            "", "AnimeStreamer", self.get_clock() if self.clock else ""
        )
        return header_table


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


class Input(TextInput):
    highlighted = Reactive(False)  # highlight
    last_search = ""

    def render(self):
        self.border_style = get_border_style(highlighted=self.highlighted)
        return super(Input, self).render()

    def search(self):
        if self.last_search == self.value or not self.value:
            return
        streamer.search(self.value)
        self.last_search = self.value

    def on_enter(self) -> None:
        self.highlighted = True

    def on_leave(self) -> None:
        self.highlighted = False


class TorrentResults(CustomWidget):
    selected_torrent = Reactive(1)

    def render(self):
        if streamer.results:
            page = f"{streamer.curr_page + 1}/{streamer.get_page_count() + 1}"
        else:
            page = "No results"
        return Panel(
            streamer.get_results_table(selected=self.selected_torrent),
            title=f"Torrents [yellow][{page}][/yellow]",
            **self.get_style()
        )

    def play_torrent(self):
        if not streamer.results:
            return
        torrent_num = self.selected_torrent + (streamer.curr_page * streamer.show_at_once)
        streamer.play_torrent(torrent_num)

    def next_torrent(self):
        if self.selected_torrent < streamer.show_at_once:
            self.selected_torrent += 1

    def prev_torrent(self):
        if self.selected_torrent > 1:
            self.selected_torrent -= 1

    def next_page(self):
        streamer.next_page()
        self.refresh()

    def prev_page(self):
        streamer.prev_page()
        self.refresh()


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


class AnimeStreamer(App):
    show_help = Reactive(False)
    current_index = Reactive(0)  # index of highlighted form

    async def on_load(self, event):
        """Bind keys on startup"""
        await self.bind("q", "quit", "Quit")
        await self.bind("h", "toggle_help", "Help")
        await self.bind("enter", "enter", "Focus/Defocus form")
        await self.bind("p", "play", "Play")
        await self.bind("r", "reverse", "Reverse sort")
        await self.bind("left", "left", "Prev page")
        await self.bind("right", "right", "Next page")
        await self.bind("down", "down")
        await self.bind("up", "up")

    async def on_mount(self) -> None:
        """On startup"""
        await self.create_forms()
        await self.create_layout()
        self.forms = (self.search_input, self.sorting, self.torrent_results)
        await self.enter_current_form()

    async def on_resize(self, event) -> None:
        """Changes number of Torrents showed based on the terminal size"""
        height = event.size.height
        show = int((height - 16) // 1.5)  # todo literally random
        if show <= 0:
            show = 1
        streamer.show_at_once = show
        if self.torrent_results.selected_torrent > streamer.show_at_once:
            self.torrent_results.selected_torrent = streamer.show_at_once

    async def create_forms(self):
        """Creates forms"""
        self.torrent_results = TorrentResults()
        self.search_input = Input(
            name="Find torrents",
            placeholder="<torrent_name>",
            title="Find torrents"
        )
        self.sorting = Sort()
        self.help_bar = Help(focusable=False)

    async def create_layout(self):
        """Puts forms into layout"""
        await self.view.dock(CustomHeader(), edge="top")
        await self.view.dock(CustomFooter(), edge="bottom")
        await self.view.dock(self.search_input, self.sorting, edge="top", size=3)
        await self.view.dock(self.torrent_results, edge="top")
        help_size = 40
        await self.view.dock(self.help_bar, edge="left", size=help_size, z=1)
        self.help_bar.layout_offset_x = -help_size

    async def search(self):
        """Searches Torrents"""
        self.search_input.search()
        self.sorting.sort()
        self.torrent_results.refresh()

    async def action_enter(self):
        """Focuses form or searches Torrent"""
        if self.search_input.has_focus and self.search_input.highlighted:
            await self.set_focus(None)
            await self.search()
        else:
            highlighted_form = self.forms[self.current_index]
            if self.focused == highlighted_form:
                await self.set_focus(None)
            else:
                await highlighted_form.focus()

    async def action_toggle_help(self):
        """Toggles help shown/hidden"""
        self.show_help = not self.show_help
        self.help_bar.animate("layout_offset_x", 0 if self.show_help else -40)

    async def action_down(self) -> None:
        """Highlights next form or selects next Torrent (down arrow)"""
        if self.focused == self.torrent_results:
            self.torrent_results.next_torrent()
        else:
            self.current_index += 1
            if self.current_index == len(self.forms):
                self.current_index = 0
            await self.enter_current_form()

    async def action_up(self) -> None:
        """Highlights previous form or selects previous Torrent (up arrow)"""
        if self.focused == self.torrent_results:
            self.torrent_results.prev_torrent()
        else:
            self.current_index -= 1
            if self.current_index == -1:
                self.current_index = len(self.forms) - 1
            await self.enter_current_form()

    async def enter_current_form(self):
        """Highlights form with green outline"""
        for i, form in enumerate(self.forms):
            form.highlighted = i == self.current_index

    async def action_left(self):
        """Previous Torrent page or previous sorting (left arrow)"""
        if self.focused == self.torrent_results:
            self.torrent_results.prev_page()
        elif self.focused == self.sorting:
            self.sorting.prev_sort()
            self.torrent_results.refresh()

    async def action_right(self):
        """Next Torrent page or next sorting (right arrow)"""
        if self.focused == self.torrent_results:
            self.torrent_results.next_page()
        elif self.focused == self.sorting:
            self.sorting.next_sort()
            self.torrent_results.refresh()

    async def action_reverse(self):
        """Sorting asc/desc reverse"""
        self.sorting.reverse_sort()
        self.torrent_results.refresh()

    async def action_play(self):
        """Starts playing selected Torrent"""
        self.torrent_results.play_torrent()
        self.refresh()


def run():
    AnimeStreamer.run()


if __name__ == "__main__":
    run()
