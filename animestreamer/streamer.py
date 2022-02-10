from __future__ import annotations
import os
import json
import appdirs
from shutil import which
from pathlib import Path

from NyaaPy import Nyaa

from rich.console import Console
from rich.table import Table
from rich.progress import track

CONFIG_DIR = Path(appdirs.user_config_dir(appname="animestreamer"))
CONFIG_DIR.mkdir(parents=True, exist_ok=True)
config = CONFIG_DIR / "config.json"
if not config.exists():
    with config.open("w") as f:
        json.dump({"download_path": ""}, f, indent=4)


class AnimeStreamer:

    def __init__(self) -> None:
        self.console = Console()
        self.results = []
        self.nyaa = Nyaa
        self.show_at_once = 10
        self.curr_page = 0
        self.pages = 4  # number of pages searched (75 results per page)
        with config.open(encoding="utf-8-sig") as f:
            self.download_path = json.load(f)["download_path"]

    @staticmethod
    def is_webtorrent_installed() -> bool:
        return which("webtorrent") is not None

    def search(self, text: str) -> None:
        self.results = []
        for page in track(range(self.pages), description="Searching..."):
            self.results.extend(self.nyaa.search(keyword=text, page=page))
        # NyaaPy gives duplicates
        ids = set()
        to_remove = []
        for r in self.results:
            if r["id"] in ids:
                to_remove.append(r)
            ids.add(r["id"])
        for r in to_remove:
            self.results.remove(r)

    def sort_results(self, key: str, reverse: bool = False) -> None:
        """keys: seeders, date, size, completed_downloads, leechers"""
        if key == "size":
            size_dict = {
                "KiB": 1,
                "MiB": 1_000,
                "GiB": 1_000_000
            }
            sort_lambda = lambda d: size_dict[d[key].split()[1]] * float(d[key].split()[0])
        elif key == "date":
            sort_lambda = lambda d: d[key]
        else:
            sort_lambda = lambda d: int(d[key])
        self.results = sorted(self.results, key=sort_lambda, reverse=reverse)

    def get_results_table(self, selected: int) -> Table:
        """Returns a table of torrents from the current page."""
        table = Table()
        if not self.results:
            return table
        table.add_column("Num", style="red")
        table.add_column("Name")
        table.add_column("Size")
        table.add_column("Seeders")
        table.add_column("Date")
        for i, res in enumerate(self.top_results()):
            num = i + 1 + (self.curr_page * self.show_at_once)
            if i + 1 == selected:
                torrent_name = f"[bold red]{res['name']}[/bold red]"
            else:
                torrent_name = res["name"]
            table.add_row(str(num), torrent_name, res["size"], res["seeders"], res["date"])
        return table

    def top_results(self) -> list:
        """Returns 'show_at_once' results from the current page"""
        return self.results[self.curr_page * self.show_at_once:self.curr_page * self.show_at_once + self.show_at_once]

    def play_torrent(self, torrent_num: int, player: str = "mpv") -> None:
        if not self.results or not self.is_webtorrent_installed():
            return
        torrent_num -= 1
        magnet_link = self.results[torrent_num]["magnet"]
        path = f"-o {self.download_path}" if self.download_path else ""
        os.system(f'webtorrent "{magnet_link}" --not-on-top --{player} {path}')

    def get_download_path(self) -> str:
        return self.download_path

    def set_download_path(self, path: str) -> bool:
        """Returns True if set, False if not set."""
        if not os.path.exists(path):
            return False
        self.download_path = path
        with config.open(encoding="utf-8-sig") as f:
            content = json.load(f)
        content["download_path"] = self.download_path
        with config.open("w") as f:
            json.dump(content, f)
        return True

    def next_page(self) -> None:
        if self.curr_page < self.get_page_count():
            self.curr_page += 1

    def prev_page(self) -> None:
        if self.curr_page > 0:
            self.curr_page -= 1

    def get_page_count(self) -> int:
        return len(self.results) // self.show_at_once
