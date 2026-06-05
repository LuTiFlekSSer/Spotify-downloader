import time

from src.backend.spotidl import errors
from src.utils.config import Config


class SessionMinter:
    """Достаёт cf-turnstile-response с spotidownloader.com.

    Капча появляется только после вставки ссылки и клика по Download. Мы открываем
    сайт (Camoufox), БЛОКИРУЕМ собственный POST /session сайта (чтобы он не
    израсходовал токен), вставляем ссылку-праймер, жмём Download — сайт решает
    Turnstile и заполняет input[name=cf-turnstile-response]. Забираем значение
    СРАЗУ и закрываем браузер; обмен токена на сессионный JWT делает уже Python
    (SpotiSession через requests) — это быстрее, чем ждать сетевой round-trip сайта.

    Ранее ломалось из-за того, что сайт очищал поле со ссылкой и капча не
    появлялась — лечится повторным посимвольным вводом в _trigger_download.

    camoufox импортируется ЛЕНИВО внутри solve()."""

    def __init__(self, headless: bool | None = None, timeout: float = 120.0):
        self._headless = Config.TURNSTILE_HEADLESS if headless is None else headless
        self._timeout = timeout

    def solve(self) -> str:
        from browserforge.fingerprints import Screen
        from camoufox.sync_api import Camoufox

        with Camoufox(headless=self._headless,
                      screen=Screen(max_width=1920, max_height=1080)) as browser:
            page = browser.new_page()

            def _route(route, request):
                if request.method == 'POST' and 'api.spotidownloader.com/session' in request.url:
                    route.abort()          # не даём сайту израсходовать токен
                else:
                    route.continue_()

            page.route('**/*', _route)
            page.goto(Config.TURNSTILE_PAGE, wait_until='domcontentloaded')

            try:
                page.wait_for_selector('input', timeout=20000)
            except Exception:
                pass
            time.sleep(1.2)

            self._trigger_download(page)

            deadline = time.monotonic() + self._timeout
            last_retrigger = time.monotonic()
            challenge_seen = False
            while time.monotonic() < deadline:
                if any(f.url.startswith('https://challenges.cloudflare.com') for f in page.frames):
                    challenge_seen = True
                self._click_turnstile(page)

                token_input = page.query_selector('input[name="cf-turnstile-response"]')
                value = token_input.get_attribute('value') if token_input else None
                if value:
                    return value           # токен есть -> сразу выходим (браузер закрывается)

                # повторно жмём Download только пока капча так и не появилась (клик/поле не прошли)
                if not challenge_seen and time.monotonic() - last_retrigger > 6:
                    self._trigger_download(page)
                    last_retrigger = time.monotonic()
                time.sleep(0.4)

        raise errors.SessionError('could not obtain Turnstile token')

    def _trigger_download(self, page):
        # Сайт очищает поле со ссылкой через ~1с, а кнопка Download активна ТОЛЬКО
        # пока поле заполнено. Поэтому держим поле заполненным и жмём Download в тот
        # момент, когда она стала активной (тугой цикл, перезаполняем при очистке).
        field = page.query_selector('input[placeholder], input[type="text"], input:not([type])')
        if field is None:
            return

        deadline = time.monotonic() + 8
        while time.monotonic() < deadline:
            try:
                if not (field.input_value() or '').strip():
                    field.click()
                    field.fill(Config.SESSION_PRIMER_URL)

                button = self._download_button(page)
                if button is not None and button.is_enabled():
                    button.click(timeout=3000)
                    return
            except Exception:
                pass
            time.sleep(0.15)

    @staticmethod
    def _download_button(page):
        for button in page.query_selector_all('button'):
            try:
                if 'download' in (button.inner_text() or '').strip().lower() and button.is_visible():
                    return button
            except Exception:
                pass
        return None

    @staticmethod
    def _click_turnstile(page):
        for frame in page.frames:
            if frame.url.startswith('https://challenges.cloudflare.com'):
                try:
                    element = frame.frame_element()
                    box = element.bounding_box() if element else None
                    if box:
                        page.mouse.click(box['x'] + box['width'] / 9,
                                         box['y'] + box['height'] / 2)
                except Exception:
                    pass
