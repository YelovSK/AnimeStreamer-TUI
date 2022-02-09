from rich.style import Style
from textual.reactive import Reactive
from textual_inputs import TextInput

from animestreamer.globals import streamer


class TorrentInput(TextInput):
    highlighted = Reactive(False)
    last_search = ""

    def render(self):
        self.border_style = Style(color="green") if self.highlighted else Style(color="blue")
        return super(TorrentInput, self).render()

    def search(self):
        if self.last_search == self.value or not self.value:
            return
        streamer.search(self.value)
        self.last_search = self.value

    def on_enter(self) -> None:
        self.highlighted = True

    def on_leave(self) -> None:
        self.highlighted = False