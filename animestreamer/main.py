from __future__ import annotations

from textual.app import App
from textual.reactive import Reactive

from animestreamer.widgets import CustomHeader, Help, PathInput, Sort, TorrentInput, TorrentResults, CustomFooter
from animestreamer import streamer


class AnimeStreamer(App):
    show_help = Reactive(False)
    current_index = Reactive(0)  # index of highlighted form

    def on_key(self, event):
        pass

    async def on_load(self, event):
        """Bind keys on startup"""
        await self.bind("q", "quit", "Quit")
        await self.bind("h", "toggle_help", "Help")
        await self.bind("enter", "enter", "Focus form / Confirm")
        await self.bind("escape", "escape", "Defocus")
        await self.bind("r", "reverse", "Reverse sort")
        await self.bind("o", "parse", "Toggle parsed Torrents")
        await self.bind("left", "left")
        await self.bind("right", "right")
        await self.bind("down", "down")
        await self.bind("up", "up")

    async def on_mount(self) -> None:
        """On startup"""
        await self.create_forms()
        await self.create_layout()
        self.forms = (self.search_input, self.sorting, self.path_input, self.torrent_results)
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
        self.search_input = TorrentInput(
            name="Find torrents",
            placeholder="<torrent_name>",
            title="Find torrents"
        )
        self.path_input = PathInput(
            name="Download path",
            value=streamer.get_download_path(),
            title="Download path"
        )
        self.sorting = Sort()
        self.help_bar = Help(focusable=False)

    async def create_layout(self):
        """Puts forms into layout"""
        await self.view.dock(CustomHeader(), edge="top")
        await self.view.dock(CustomFooter(), edge="bottom")
        await self.view.dock(self.search_input, self.sorting, self.path_input, edge="top", size=3)
        await self.view.dock(self.torrent_results, edge="top")
        help_size = 40
        await self.view.dock(self.help_bar, edge="left", size=help_size, z=1)
        self.help_bar.layout_offset_x = -help_size

    async def search(self):
        """Searches Torrents"""
        self.search_input.search()
        self.sorting.sort()
        self.torrent_results.refresh()
        self.refresh()

    async def action_enter(self):
        """Focuses form or searches Torrent"""
        if self.search_input.has_focus and self.search_input.highlighted:
            await self.search()
        elif self.path_input.has_focus and self.path_input.highlighted:
            if not self.path_input.set_path():
                await self.action_bell()
        elif self.torrent_results.focused:
            await self.play()
        elif self.sorting.focused:
            await self.action_reverse()
        elif self.focused is None:
            highlighted_form = self.forms[self.current_index]
            await highlighted_form.focus()

    async def action_toggle_help(self):
        """Toggles help shown/hidden"""
        self.show_help = not self.show_help
        self.help_bar.animate("layout_offset_x", 0 if self.show_help else -40)

    async def action_down(self) -> None:
        """Highlights next form or selects next Torrent (down arrow)"""
        if self.focused == self.torrent_results:
            self.torrent_results.next_torrent()
        elif self.focused is None:
            self.current_index += 1
            if self.current_index == len(self.forms):
                self.current_index = 0
            await self.enter_current_form()

    async def action_up(self) -> None:
        """Highlights previous form or selects previous Torrent (up arrow)"""
        if self.focused == self.torrent_results:
            self.torrent_results.prev_torrent()
        elif self.focused is None:
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

    async def play(self):
        """Starts playing selected Torrent"""
        if not streamer.is_webtorrent_installed():
            await self.action_bell()
            return
        self.torrent_results.play_torrent()
        self.refresh()

    async def action_escape(self):
        self.search_input.set_current_search()
        self.path_input.set_current_path()
        await self.set_focus(None)

    async def action_parse(self):
        self.torrent_results.toggle_parse()


def run():
    AnimeStreamer.run()


if __name__ == "__main__":
    run()
