import os

from rich.style import Style
from textual.reactive import Reactive
from textual_inputs import TextInput

from animestreamer import streamer


class PathInput(TextInput):
    highlighted = Reactive(False)
    path = Reactive(streamer.get_download_path())

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if streamer.get_download_path() == "":
            self.placeholder = "Default (depends on the OS)"

    def render(self):
        self.border_style = self.border_style = Style(color="green") if self.highlighted else Style(color="blue")
        return super(PathInput, self).render()

    def set_path(self) -> bool:
        """Returns if path was set"""
        if os.path.exists(self.value):
            streamer.set_download_path(self.value)
            return True
        else:
            self.set_current_path()
            return False

    def set_current_path(self):
        if self.value != streamer.get_download_path():
            self.value = streamer.get_download_path()

    def on_enter(self) -> None:
        self.highlighted = True

    def on_leave(self) -> None:
        self.highlighted = False