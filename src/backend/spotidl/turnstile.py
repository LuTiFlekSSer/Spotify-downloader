import time

from src.backend.spotidl import errors
from src.utils.config import Config


class TurnstileSolver:
    """Решает Cloudflare Turnstile на spotidownloader.com через Camoufox
    (undetected Firefox) и возвращает значение cf-turnstile-response.

    camoufox импортируется ЛЕНИВО внутри solve(), чтобы приложение и тесты
    не требовали установленного браузера до момента реальной загрузки."""

    def __init__(self, headless: bool | None = None, timeout: float = 60.0):
        self._headless = Config.TURNSTILE_HEADLESS if headless is None else headless
        self._timeout = timeout

    def solve(self) -> str:
        from browserforge.fingerprints import Screen
        from camoufox.sync_api import Camoufox

        with Camoufox(headless=self._headless,
                      screen=Screen(max_width=1920, max_height=1080)) as browser:
            page = browser.new_page()

            # блокируем собственный POST сайта на /session, чтобы он не «израсходовал» токен
            def _handle(route, request):
                if request.method == 'POST' and 'api.spotidownloader.com/session' in request.url:
                    route.abort()
                else:
                    route.continue_()

            page.route('**/*', _handle)
            page.goto(Config.TURNSTILE_PAGE)

            deadline = time.monotonic() + self._timeout
            while time.monotonic() < deadline:
                # автоклик по чекбоксу Turnstile
                for frame in page.frames:
                    if frame.url.startswith('https://challenges.cloudflare.com'):
                        element = frame.frame_element()
                        box = element.bounding_box() if element else None
                        if box:
                            page.mouse.click(box['x'] + box['width'] / 9,
                                             box['y'] + box['height'] / 2)

                token_input = page.query_selector('input[name="cf-turnstile-response"]')
                if token_input:
                    value = token_input.get_attribute('value')
                    if value:
                        return value

                time.sleep(0.5)

        raise errors.SessionError('Turnstile solve timed out')
