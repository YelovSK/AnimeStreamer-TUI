from NyaaPy import Nyaa
from os import system
from termcolor import colored


class AnimeStreamer:

    def __init__(self, pages=1, player="vlc", download_path=""):
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

    def sort_results(self, key, order):
        reverse = order != "asc"
        if key == "size":
            size_lambda = lambda n, s: float(n)/1000 if s == "KiB" else (float(n) if s == "MiB" else float(n)*1000)
            sort_lambda = lambda d: size_lambda(d[key].split()[0], d[key].split()[1])
        else:
            convInt = key in ["seeders", "leechers", "size", "completed_downloads"]
            sort_lambda = (lambda d: int(d[key])) if convInt else (lambda d: d[key])
        self.results = sorted(self.results, key=sort_lambda, reverse=reverse)
        self.list_top_results()

    def top_results(self):
        return self.results[self.curr_page*self.show_at_once:self.curr_page*self.show_at_once+self.show_at_once]

    def list_top_results(self):
        system("cls")
        print(colored("-"*80, "red"))
        for i, res in enumerate(self.top_results()):
            num = i+1+(self.curr_page*self.show_at_once)
            anime_col = "yellow" if i % 2 else "green"
            print(
                colored(f'{num: }', "red", attrs=["bold", "blink"]),
                colored(f'{res["name"] }', anime_col, attrs=["bold"]),
                colored(f'[{res["size"]}] ', "white"),
                colored(f'[{res["seeders"]} seeders] ', "white"),
                colored(f'[{res["date"]}]', "white")
            )
        print(colored("-"*80, "red"))

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
        return True

    def next_page(self):
        if (self.curr_page+1)*self.show_at_once < len(self.results):
            self.curr_page += 1

    def prev_page(self):
        if self.curr_page > 0:
            self.curr_page -= 1

    def reset(self):
        system("cls")
        self.curr_page = 0
        self.results = []
        self.start(False)

    def start(self):
        action_dict = {"-f": "search", "-s": "sort", "-p": "page", "-c": "select"}
        while True:
            print("""find: -f [query]
sort: -s [seeders/date/size/completed_downloads/leechers] [asc/desc]
page: -p [next/prev/page_num]
choose: -c [torrent_num]""")
            user_input = input(">> ")
            if len(user_input.split()) in (2, 3):
                action, val = user_input.split()[0], " ".join(user_input.split()[1:])
                if action in action_dict and (action == "-f" or self.results):
                    if not self.do_input(action_dict[action], val):
                        system("cls")
                        if len(self.results):
                            self.list_top_results()
                else:
                    system("cls")
            elif len(self.results):
                self.list_top_results()
            else:
                system("cls")
            
        
streamer = AnimeStreamer(pages=2)
streamer.start()