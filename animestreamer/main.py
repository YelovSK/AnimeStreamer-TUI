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
from textual.app import App
from textual.widgets import Placeholder, ScrollView
from textual.widget import Widget
from textual.reactive import Reactive
from textual.message import Message

from textual_inputs import TextInput

streamer = AnimeStreamer()


class Help(Widget):
    border_style = Reactive(Style(color="blue"))

    def render(self) -> Panel:
        content = """
[b]h[/b] - toggles left Help sidebar
[b]f[/b] - focuses search textbox
[b]enter[/b] - search torrents if textbox in focus
[b]q[/b] - quit application
"""
        return Panel(
            content,
            style=self.border_style
        )

    def on_enter(self) -> None:
        self.set_style("green")

    def on_leave(self) -> None:
        self.set_style("blue")

    def set_style(self, color: str):
        self.border_style = Style(color=color)


class Input(TextInput):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_style("blue")

    def on_enter(self) -> None:
        self.set_style("green")

    def on_leave(self) -> None:
        self.set_style("blue")

    def set_style(self, color: str):
        self.border_style = Style(color=color)


class TorrentResults(ScrollView):
    border_style = Reactive(Style(color="blue"))

    async def update_torrents(self):
        await self.update(
            Panel(
                streamer.get_results_table(),
                title="Torrents",
                border_style=self.border_style
            )
        )

    def on_enter(self) -> None:
        self.set_style("green")

    def on_leave(self) -> None:
        self.set_style("blue")

    def set_style(self, color: str):
        self.border_style = Style(color=color)


class AnimeStreamer(App):
    show_help = Reactive(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def on_load(self, event):
        await self.bind("q", "quit")
        await self.bind("h", "toggle_help", "Toggle help")
        await self.bind("f", "focus_find")
        await self.bind("enter", "find")

    async def on_mount(self) -> None:
        self.torrent_results = TorrentResults(fluid=False)  # fluid False doesn't seem to do anything
        self.search_input = Input(
            name="Find torrents",
            placeholder="torrent name",
            title="Find torrents"
        )
        self.help_bar = Help()
        await self.view.dock(self.search_input, self.torrent_results, edge="top")
        await self.view.dock(self.help_bar, edge="left", size=40, z=1)
        self.help_bar.layout_offset_x = -40
        await self.torrent_results.update_torrents()

    async def action_find(self):
        if not self.search_input.has_focus:
            return
        streamer.search(self.search_input.value)
        streamer.sort_results(key="seeders", reverse=True)
        await self.torrent_results.update_torrents()

    def action_toggle_help(self):
        self.show_help = not self.show_help

    def watch_show_help(self, show_help: bool):
        self.help_bar.animate("layout_offset_x", 0 if show_help else -40)

    async def action_focus_find(self):
        await self.search_input.focus()


if __name__ == "__main__":
    AnimeStreamer.run()
