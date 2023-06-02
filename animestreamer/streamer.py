from __future__ import annotations
import os
import json
import appdirs
import anitopy
from shutil import which
from pathlib import Path

from NyaaPy.nyaa import Nyaa

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
        self.nyaa = Nyaa()
        self.show_at_once = 10
        self.curr_page = 0
        self.pages = 6  # number of pages searched (75 results per page)
        with config.open(encoding="utf-8-sig") as f:
            conf = json.load(f)
            self.download_path = conf["download_path"]
            self.player = conf["player"]

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
            if r.id in ids:
                to_remove.append(r)
            ids.add(r.id)
        for r in to_remove:
            self.results.remove(r)

    def sort_results(self, key: str = "date", reverse: bool = False) -> None:
        """keys: seeders, date, size, completed_downloads, leechers"""
        if key == "size":
            size_dict = {
                "KiB": 1,
                "MiB": 1_000,
                "GiB": 1_000_000
            }
            sort_lambda = lambda d: size_dict[d.size.split()[1]] * float(d.size.split()[0])
        elif key == "date":
            sort_lambda = lambda d: d.date
        else:
            sort_lambda = lambda d: int(getattr(d, key))
        self.results = sorted(self.results, key=sort_lambda, reverse=reverse)

    def get_results_table(self, selected: int, parsed: bool) -> Table:
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
            title = self.parse_torrent(res.name) if parsed else res.name
            if i + 1 == selected:
                torrent_name = self.colored(title, "bold red")
            else:
                torrent_name = title
            table.add_row(str(num), torrent_name, res.size, res.seeders, res.date)
        return table

    def parse_torrent(self, name: str) -> str:
        parsed = anitopy.parse(name)
        keys = {    # key: (colour, prefix, suffix)
            "anime_title": (None, "", ""),
            "anime_season": ("yellow", "[S", "]"),
            "episode_number": ("yellow", "[E", "]"),
            "video_resolution": ("green", "[", "]"),
            "video_term": ("green", "[", "]"),
            "release_group": ("blue", "[", "]")
        }
        info = []
        for key, formatting in keys.items():
            if key not in parsed:
                continue
            colour, prefix, suffix = formatting
            value = parsed[key]
            if isinstance(value, list): # episode_number: [from, to]
                value = "-".join(value)
            value = prefix + value + suffix
            info.append(self.colored(value, colour))

        return " ".join(info)

    @staticmethod
    def colored(text: str, col: str | None = None) -> str:
        if col is None:
            return text
        return f"[{col}]{text}[/{col}]"

    def top_results(self) -> list:
        """Returns 'show_at_once' results from the current page"""
        page_start_ix = self.curr_page * self.show_at_once
        page_end_ix = page_start_ix + self.show_at_once
        return self.results[page_start_ix:page_end_ix]

    def play_torrent(self, torrent_num: int, player: str = "mpv") -> None:
        if not self.results or not self.is_webtorrent_installed():
            return
        torrent_num -= 1
        magnet_link = self.results[torrent_num].magnet
        path = f"-o {self.download_path}" if self.download_path else ""
        os.system(f'webtorrent "{magnet_link}" --not-on-top --{player} {path}')

    def get_download_path(self) -> str:
        return self.download_path

    def get_player(self) -> str:
        return self.player
    
    def set_player(self, player: str) -> None:
        self.player = player

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
