__all__ = [
    'Cli'
]

import MainPage
import Update
import argparse


class Cli:
    def __init__(self):
        self._main_page = MainPage.MainPage()
        self._update = Update.Update()

        parser = argparse.ArgumentParser()
        parser.add_argument('-U', type=str, help='Path to previous executable file')
        self._args = parser.parse_args()

    def start(self):
        if self._args.U is not None:
            self._update.install(self._args.U)
            return

        if self._update.start():
            return

        self._main_page.main_page()
