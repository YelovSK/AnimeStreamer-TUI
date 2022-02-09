from rich.style import Style
from rich.table import Table
from textual.widgets import Header

from animestreamer.globals import streamer


class CustomHeader(Header):

    def __init__(self) -> None:
        super().__init__(tall=False, style=Style(color="white", bgcolor="rgb(40,40,40)"))

    def render(self) -> Table:
        """Override for title"""
        title = "AnimeStreamer"
        if not streamer.is_webtorrent_installed():
            title += " [red]<WebTorrent was not found>[/red]"
        header_table = Table.grid(padding=(0, 1), expand=True)
        header_table.add_column(justify="left", ratio=0, width=8)
        header_table.add_column("title", justify="center", ratio=1)
        header_table.add_column("clock", justify="right", width=8)
        header_table.add_row(
            "", title, self.get_clock() if self.clock else ""
        )
        return header_table