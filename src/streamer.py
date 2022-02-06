from __future__ import annotations
import os
import json
import appdirs
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

    def __init__(self):
        self.console = Console()
        self.results = []
        self.nyaa = Nyaa
        self.show_at_once = 10
        self.curr_page = 0
        self.player = "vlc"
        self.pages = 3  # number of pages searched (75 results per page)
        with config.open(encoding="utf-8-sig") as f:
            self.download_path = json.load(f)["download_path"]

    def search(self, text: str) -> None:
        self.curr_page = 0
        self.results = []
        for page in track(range(self.pages), description="Searching..."):
            self.results.extend(self.nyaa.search(keyword=text, page=page))

    def sort_results(self, key: str, reverse: bool = False) -> None:
        if key == "size":
            size_lambda = lambda n, s: float(n) / 1000 if s == "KiB" else (float(n) if s == "MiB" else float(n) * 1000)
            sort_lambda = lambda d: size_lambda(d[key].split()[0], d[key].split()[1])
        else:
            conv_int = key in ["seeders", "leechers", "size", "completed_downloads"]
            sort_lambda = (lambda d: int(d[key])) if conv_int else (lambda d: d[key])
        self.results = sorted(self.results, key=sort_lambda, reverse=reverse)

    def top_results(self) -> list:
        return self.results[self.curr_page * self.show_at_once:self.curr_page * self.show_at_once + self.show_at_once]

    def list_top_results(self) -> None:
        table = Table(title="Torrents")
        table.add_column("Num", style="red")
        table.add_column("Name")
        table.add_column("Size")
        table.add_column("Seeders")
        table.add_column("Date")
        for i, res in enumerate(self.top_results()):
            num = i + 1 + (self.curr_page * self.show_at_once)
            table.add_row(str(num), res["name"], res["size"], res["seeders"], res["date"])
        self.console.print(table)
        last_page = (len(self.results) - 1) // self.show_at_once
        self.console.print(f"Page {self.curr_page + 1}/{last_page + 1}")

    def give_magnet(self, result_num: int):
        return self.results[result_num]["magnet"]

    def stream_magnet(self, magnet_link: str):
        # default location: C:\Users\username\AppData\Local\Temp\webtorrent
        path = f"-o {self.download_path}" if self.download_path else ""
        os.system(f'webtorrent "{magnet_link}" --not-on-top --{self.player} {path}')

    def set_page(self, page_num: int):
        page_num -= 1
        if page_num < 0:
            self.curr_page = 0
        elif page_num * self.show_at_once > len(self.results):
            self.curr_page = (len(self.results) - 1) // self.show_at_once
        else:
            self.curr_page = page_num

    def play_torrent(self, torrent_num: int):
        torrent_num -= 1
        if torrent_num not in range(len(self.results)):
            self.console.print(f"{torrent_num + 1} is not valid")
            return
        magnet_link = self.give_magnet(torrent_num)
        self.stream_magnet(magnet_link)

    def get_download_path(self):
        if self.download_path == "":
            return "Default (depends on the OS)"
        else:
            return self.download_path

    def set_download_path(self, path):
        self.download_path = path
        with config.open(encoding="utf-8-sig") as f:
            content = json.load(f)
        content["download_path"] = self.download_path
        with config.open("w") as f:
            json.dump(content, f)
