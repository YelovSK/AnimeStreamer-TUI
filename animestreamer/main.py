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
from textual.app import App
from textual.widgets import Placeholder, ScrollView
from textual.widget import Widget
from textual.reactive import Reactive
from textual.message import Message

from textual_inputs import TextInput

streamer = AnimeStreamer()


class Help(Widget):
    entered = Reactive(False)

    def render(self) -> Panel:
        help_list = (
            "[b]h[/b] - toggles this sidebar",
            "[b]left_arrow[/b] - previous page",
            "[b]right_arrow[/b] - next page",
            "[b]enter[/b] - focus form or search torrents if textbox in focus",
            "[b]tab[/b] - remove focus from form",
            "[b]q[/b] - quit application"
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

    def render(self):
        return Panel(
            streamer.get_results_table(),
            title="Torrents",
            border_style=self.border_style,
            box=rich.box.DOUBLE if self.has_focus else rich.box.SQUARE,
        )

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

    def render(self):
        content = ""
        for ix, sort in enumerate(self.sorts):
            if ix == self.sort_ix:
                content += f"[bold red]{sort}[/bold red]"
            else:
                content += sort
        return Panel(
            content,
            title="Sorting",
            border_style=self.border_style,
            box=rich.box.DOUBLE if self.has_focus else rich.box.SQUARE,
        )

    def next_sort(self):
        if self.sort_ix < len(self.sorts) - 1:
            self.sort_ix += 1
            streamer.sort_results(key=self.sorts[self.sort_ix])

    def prev_sort(self):
        if self.sort_ix > 0:
            self.sort_ix -= 1
            streamer.sort_results(key=self.sorts[self.sort_ix])

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
        await self.bind("h", "toggle_help", "Toggle help")
        await self.bind("down", "next_tab_index")
        await self.bind("up", "previous_tab_index")
        await self.bind("left", "prev_page")
        await self.bind("right", "next_page")
        await self.bind("ctrl+i", "defocus")  # tab
        await self.bind("enter", "enter", "Find torrent")

    async def on_mount(self) -> None:
        self.torrent_results = TorrentResults()
        self.search_input = Input(
            name="Find torrents",
            placeholder="torrent name",
            title="Find torrents"
        )
        self.sorting = Sort()
        self.help_bar = Help()
        await self.view.dock(self.search_input, self.sorting, edge="top", size=3)
        await self.view.dock(self.torrent_results, edge="bottom")
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
        self.current_index += 1
        if self.current_index == len(self.tab_index):
            self.current_index = 0
        self.enter_current_form()

    async def action_previous_tab_index(self) -> None:
        """Changes the focus to the previous form field"""
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
        for form in self.tab_index:
            form.leave()
        await self.set_focus(None)


if __name__ == "__main__":
    AnimeStreamer.run()
