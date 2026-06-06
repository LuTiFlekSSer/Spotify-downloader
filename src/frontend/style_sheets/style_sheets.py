from enum import Enum

from qfluentwidgets import StyleSheetBase, Theme


class StyleSheet(StyleSheetBase, Enum):
    HOME_WINDOW = 'home_window'
    TRACKS_WINDOW = 'tracks_window'
    SETTINGS_WINDOW = 'settings_window'

    def path(self, theme: Theme = Theme.AUTO) -> str:
        return f'src/frontend/style_sheets/qss/{self.value}.qss'
