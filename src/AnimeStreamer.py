from NyaaPy import Nyaa
from os import system, path
from termcolor import colored
from rich.console import Console
from rich.table import Table


class AnimeStreamer:

    def __init__(self, pages=1, player="vlc", download_path=""):
        self.console = Console()
        self.results = []
        self.nyaa = Nyaa
        self.show_at_once = 10
        self.curr_page = 0
        self.player = player
        self.download_path = download_path
        self.pages = pages  # number of pages searched (75 results per page)

    def search(self, val):
        self.results = []
        self.curr_page = 0
        for page in range(self.pages):
            self.results.extend(self.nyaa.search(keyword=val, page=page))
        # remove duplicates, something broke in NyaaPy I guess
        ids = set()
        to_remove = []
        for r in self.results:
            if r["id"] in ids:
                to_remove.append(r)
            ids.add(r["id"])
        for r in to_remove:
            self.results.remove(r)

    def sort_results(self, key, order):
        reverse = order != "asc"
        if key == "size":
            size_lambda = lambda n, s: float(n)/1000 if s == "KiB" else (float(n) if s == "MiB" else float(n)*1000)
            sort_lambda = lambda d: size_lambda(d[key].split()[0], d[key].split()[1])
        else:
            conv_int = key in ["seeders", "leechers", "size", "completed_downloads"]
            sort_lambda = (lambda d: int(d[key])) if conv_int else (lambda d: d[key])
        self.results = sorted(self.results, key=sort_lambda, reverse=reverse)
        self.list_top_results()

    def top_results(self):
        return self.results[self.curr_page*self.show_at_once:self.curr_page*self.show_at_once+self.show_at_once]

    def list_top_results(self):
        system("cls")
        table = Table(title="Torrents")
        table.add_column("Num", style="red")
        table.add_column("Name")
        table.add_column("Size")
        table.add_column("Seeders")
        table.add_column("Date")
        for i, res in enumerate(self.top_results()):
            num = i+1+(self.curr_page*self.show_at_once)
            table.add_row(str(num), res["name"], res["size"], res["seeders"], res["date"])
        self.console.print(table)

    def give_magnet(self, n):
        return self.results[int(n)]["magnet"]

    def stream_magnet(self, magnet_link):
        # default location: C:\Users\username\AppData\Local\Temp\webtorrent
        path = f"-o {self.download_path}" if self.download_path else ""
        system(f'webtorrent "{magnet_link}" --not-on-top --{self.player} {path}')

    def check_input(self, action, input):
        if not input:
            return False
        if action == "sort":
            input = input.split()
            if len(input) != 2 or (input[0] not in ("seeders", "date", "size", "completed_downloads", "leechers") or input[1] not in ("asc", "desc")):
                return False
        elif action == "select":
            if not input.isnumeric():
                return False
        elif action == "page":
            if input not in ("next", "prev") and not input.isnumeric():
                return False
        return True

    def do_input(self, action, input):
        if not self.check_input(action, input):
            return False
        if action == "search":
            self.search(input)
            self.sort_results(key="seeders", order="desc")
            self.list_top_results()
        elif action == "sort":
            self.sort_results(*(input.split()))
        elif action == "page":
            if input in ("next", "prev"):
                if input == "next":
                    self.next_page()
                elif input == "prev":
                    self.prev_page()
            else:
                page_num = input
                if page_num.isnumeric():
                    page_num = int(page_num)-1
                    if page_num < 0:
                        self.curr_page = 0
                    elif page_num*self.show_at_once > len(self.results):
                        self.curr_page = (len(self.results)-1) // self.show_at_once
                    else:
                        self.curr_page = page_num

            self.list_top_results()
        elif action == "select":
            selected_num = int(input)-1
            if selected_num not in range(self.curr_page*self.show_at_once, self.curr_page*self.show_at_once+self.show_at_once):
                print(colored(f"{selected_num+1} is not a number from the current page", "red"))
                return
            magnet_link = self.give_magnet(selected_num)
            self.stream_magnet(magnet_link)
        elif action == "path":
            if path.exists(input):
                self.download_path = input
            else:
                self.console.print("Path does not exist")
        elif action == "pages":
            if input in [str(i) for i in range(1, 21)]:
                self.pages = int(input)
            else:
                self.console.print("Must be in range from 1 to 20")
        return True

    def next_page(self):
        if (self.curr_page+1)*self.show_at_once < len(self.results):
            self.curr_page += 1

    def prev_page(self):
        if self.curr_page > 0:
            self.curr_page -= 1
            
    def show_help(self):
        table = Table(title="Functions")
        for col in ("Input", "Action", "Arguments"):
            table.add_column(col)
        table.add_row("-f", "find", "torrent name")
        table.add_row("-s", "sort", "seeders/date/size/completed_downloads/leechers + asc/desc")
        table.add_row("-p", "page", "next/prev/page_num")
        table.add_row("-c", "choose", "torrent number")
        table.add_row("-d", "set download path", "path or empty to show show current")
        table.add_row("-pg", "pages to search", "num")
        table.add_row("-r", "reset", "")
        table.add_row("-h", "shows this table", "")
        self.console.print(table)

    def reset(self):
        system("cls")
        self.curr_page = 0
        self.results = []
        self.start()

    def start(self):
        self.show_help()
        action_dict = {"-f": "search", "-s": "sort", "-p": "page", "-c": "select", "-d": "path", "-pg": "pages"}
        while True:
            user_input = input(">> ")
            if len(user_input.split()) in (2, 3):
                action, val = user_input.split()[0], " ".join(user_input.split()[1:])
                if action in action_dict:
                    if not self.do_input(action_dict[action], val):
                        system("cls")
                        if len(self.results):
                            self.list_top_results()
                else:
                    system("cls")
            elif user_input == "-h":
                self.show_help()
            elif user_input == "-r":
                self.reset()
            elif user_input == "-d":
                self.console.print("Current path:", self.download_path)
            elif len(self.results):
                self.list_top_results()
            else:
                system("cls")

        
streamer = AnimeStreamer(pages=3)
streamer.start()