from __future__ import annotations
import os

import rich.box
from rich.align import Align
from rich.console import Console
# from animestreamer.streamer import AnimeStreamer
from rich.pretty import Pretty

from streamer import AnimeStreamer
import rich
from rich.style import Style
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from textual.app import App
from textual.widgets import Placeholder, ScrollView, Header, Footer
from textual.widget import Widget
from textual.reactive import Reactive
from textual.message import Message

from textual_inputs import TextInput

streamer = AnimeStreamer()


class CustomFooter(Footer):
    """Override the default Footer for Styling"""

    def make_key_text(self) -> Text:
        """Create text containing all the keys."""
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
    """Override the default Header for Styling"""

    def __init__(self) -> None:
        super().__init__(tall=False, style=Style(color="white", bgcolor="rgb(98,98,98)"))

    def render(self) -> Table:
        header_table = Table.grid(padding=(0, 1), expand=True)
        header_table.add_column(justify="left", ratio=0, width=8)
        header_table.add_column("title", justify="center", ratio=1)
        header_table.add_column("clock", justify="right", width=8)
        header_table.add_row(
            "", "AnimeStreamer", self.get_clock() if self.clock else ""
        )
        return header_table


class Help(Widget):
    entered = Reactive(False)

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
            border_style=Style(color="green") if self.entered else Style(color="blue")
        )

    def on_enter(self) -> None:
        self.entered = True

    def on_leave(self) -> None:
        self.entered = False


class Input(TextInput):
    entered = Reactive(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def on_enter(self) -> None:
        self.enter()

    def on_leave(self) -> None:
        self.leave()

    def enter(self):
        self.entered = True
        self.set_style()

    def leave(self):
        self.entered = False
        self.set_style()

    def set_style(self):
        self.border_style = Style(color="green") if self.entered else Style(color="blue")


class TorrentResults(Widget):
    has_focus = Reactive(False)
    entered = Reactive(False)
    border_style = Reactive(Style(color="blue"))
    selected_torrent = 1

    def render(self):
        return Panel(
            streamer.get_results_table(selected=self.selected_torrent),
            title="Torrents",
            border_style=self.border_style,
            box=rich.box.DOUBLE if self.has_focus else rich.box.SQUARE,
        )

    def next_torrent(self):
        if self.selected_torrent < streamer.show_at_once:
            self.selected_torrent += 1

    def prev_torrent(self):
        if self.selected_torrent > 1:
            self.selected_torrent -= 1

    def on_enter(self) -> None:
        self.enter()

    def on_leave(self) -> None:
        self.leave()

    def enter(self):
        self.entered = True
        self.set_style()

    def leave(self):
        self.entered = False
        self.set_style()

    def set_style(self):
        self.border_style = Style(color="green") if self.entered else Style(color="blue")

    def on_focus(self) -> None:
        self.has_focus = True

    def on_blur(self) -> None:
        self.has_focus = False


class Sort(Widget):
    has_focus = Reactive(False)
    entered = Reactive(False)
    border_style = Reactive(Style(color="blue"))
    sorts = ("seeders", "date", "size", "completed_downloads", "leechers")
    sort_ix = Reactive(0)
    reversed = Reactive(True)

    def render(self):
        content = []
        for ix, sort in enumerate(self.sorts):
            if ix == self.sort_ix:
                content.append(f"[bold red]{sort}[/bold red]")
            else:
                content.append(sort)
        return Panel(
            "   ".join(content),
            title="Sorting",
            border_style=self.border_style,
            box=rich.box.DOUBLE if self.has_focus else rich.box.SQUARE,
        )

    def next_sort(self):
        if self.sort_ix < len(self.sorts) - 1:
            self.sort_ix += 1
            self.sort()

    def prev_sort(self):
        if self.sort_ix > 0:
            self.sort_ix -= 1
            self.sort()

    def reverse_sort(self):
        self.reversed = not self.reversed
        self.sort()

    def sort(self):
        streamer.sort_results(key=self.sorts[self.sort_ix], reverse=self.reversed)

    def on_enter(self) -> None:
        self.enter()

    def on_leave(self) -> None:
        self.leave()

    def enter(self):
        self.entered = True
        self.set_style()

    def leave(self):
        self.entered = False
        self.set_style()

    def set_style(self):
        self.border_style = Style(color="green") if self.entered else Style(color="blue")

    def on_focus(self) -> None:
        self.has_focus = True

    def on_blur(self) -> None:
        self.has_focus = False


class AnimeStreamer(App):
    show_help = Reactive(False)
    current_index = 0

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def on_key(self, event):
        pass

    async def on_load(self, event):
        await self.bind("q", "quit", "Quit")
        await self.bind("h", "toggle_help", "Help")
        await self.bind("down", "next_tab_index")
        await self.bind("up", "previous_tab_index")
        await self.bind("left", "prev_page", "Prev page")
        await self.bind("right", "next_page", "Next page")
        await self.bind("ctrl+i", "defocus", "Remove focus")  # tab
        await self.bind("r", "reverse", "Reverse sort")
        await self.bind("p", "play", "Play")
        await self.bind("enter", "enter", "Focus form")

    async def on_mount(self) -> None:
        self.torrent_results = TorrentResults()
        self.search_input = Input(
            name="Find torrents",
            placeholder="torrent name",
            title="Find torrents"
        )
        self.sorting = Sort()
        self.help_bar = Help()
        await self.view.dock(CustomHeader(), edge="top")
        await self.view.dock(CustomFooter(), edge="bottom")
        await self.view.dock(self.search_input, self.sorting, edge="top", size=3)
        await self.view.dock(self.torrent_results, edge="top")
        help_size = 40
        await self.view.dock(self.help_bar, edge="left", size=help_size, z=1)
        self.help_bar.layout_offset_x = -help_size

        self.tab_index = [self.search_input, self.sorting, self.torrent_results]
        self.enter_current_form()

    async def search(self):
        streamer.search(self.search_input.value)
        streamer.sort_results(key="seeders", reverse=True)
        self.torrent_results.refresh()

    async def action_enter(self):
        if self.search_input.has_focus and self.search_input.border_style == Style(color="green"):
            await self.search()
            # await self.torrent_results.update_torrents()
        else:
            await self.tab_index[self.current_index].focus()
            # await getattr(self, self.tab_index[self.current_index]).focus()

    def action_toggle_help(self):
        self.show_help = not self.show_help

    def watch_show_help(self, show_help: bool):
        self.help_bar.animate("layout_offset_x", 0 if show_help else -40)

    async def action_next_tab_index(self) -> None:
        """Changes the focus to the next form field"""
        if self.focused == self.torrent_results:
            self.torrent_results.next_torrent()
            self.torrent_results.refresh()
        else:
            self.current_index += 1
            if self.current_index == len(self.tab_index):
                self.current_index = 0
            self.enter_current_form()

    async def action_previous_tab_index(self) -> None:
        """Changes the focus to the previous form field"""
        if self.focused == self.torrent_results:
            self.torrent_results.prev_torrent()
            self.torrent_results.refresh()
        else:
            self.current_index -= 1
            if self.current_index == -1:
                self.current_index = len(self.tab_index) - 1
            self.enter_current_form()

    async def action_prev_page(self):
        if self.focused == self.torrent_results:
            streamer.prev_page()
        elif self.focused == self.sorting:
            self.sorting.prev_sort()
        self.torrent_results.refresh()

    async def action_next_page(self):
        if self.focused == self.torrent_results:
            streamer.next_page()
        elif self.focused == self.sorting:
            self.sorting.next_sort()
        self.torrent_results.refresh()

    def enter_current_form(self):
        for i, form in enumerate(self.tab_index):
            if i == self.current_index:
                form.enter()
            else:
                form.leave()

    async def action_defocus(self):
        await self.set_focus(None)

    async def action_reverse(self):
        self.sorting.reverse_sort()
        self.torrent_results.refresh()

    async def action_play(self):
        if not streamer.results:
            return
        torrent_num = self.torrent_results.selected_torrent
        torrent_num += streamer.curr_page * streamer.show_at_once
        streamer.play_torrent(torrent_num)
        self.refresh()


if __name__ == "__main__":
    AnimeStreamer.run()
