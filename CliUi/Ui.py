__all__ = [
    'Cli'
]

import MainPage
import Update



class Cli:
    def __init__(self):
        self._main_page = MainPage.MainPage()

    def start(self):
        self._main_page.main_page()
