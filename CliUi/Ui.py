__all__ = [
    'Cli'
]

import MainPage
import Update


class Cli:
    def __init__(self):
        self._main_page = MainPage.MainPage()
        self._update = Update.Update()

    def start(self):
        self._update.start()

        self._main_page.main_page()
