import json
import time

from src.backend.spotidl import errors
from src.utils.config import Config


class SessionMinter:
    """Получает сессионный JWT spotidownloader.

    Капча Turnstile появляется только после вставки ссылки и клика по Download —
    тогда сайт сам решает капчу и делает POST /session. Мы открываем сайт
    (Camoufox), вставляем ссылку-праймер, жмём Download и ПЕРЕХВАТЫВАЕМ ответ
    /session, доставая из него token. Возвращаемся сразу же — браузер закрывается,
    не дожидаясь самой загрузки.

    Важно: НЕ блокируем /session сайта (иначе сайт сбрасывает форму и очищает поле).
    camoufox импортируется ЛЕНИВО внутри mint()."""

    def __init__(self, headless: bool | None = None, timeout: float = 120.0):
        self._headless = Config.TURNSTILE_HEADLESS if headless is None else headless
        self._timeout = timeout

    def mint(self) -> str:
        from browserforge.fingerprints import Screen
        from camoufox.sync_api import Camoufox

        captured: dict = {}
        with Camoufox(headless=self._headless,
                      screen=Screen(max_width=1920, max_height=1080)) as browser:
            page = browser.new_page()

            def _on_response(response):
                try:
                    if ('api.spotidownloader.com/session' in response.url
                            and response.request.method == 'POST'):
                        token = json.loads(response.text()).get('token')
                        if token:
                            captured['jwt'] = token
                except Exception:
                    pass

            page.on('response', _on_response)
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
                if 'jwt' in captured:
                    return captured['jwt']

                if any(f.url.startswith('https://challenges.cloudflare.com') for f in page.frames):
                    challenge_seen = True
                self._click_turnstile(page)

                # повторно жмём Download только пока капча так и не появилась (клик не прошёл)
                if not challenge_seen and time.monotonic() - last_retrigger > 6:
                    self._trigger_download(page)
                    last_retrigger = time.monotonic()
                time.sleep(0.4)

        raise errors.SessionError('could not obtain session (Turnstile)')

    def _trigger_download(self, page):
        try:
            field = page.query_selector('input[placeholder], input[type="text"], input:not([type])')
            if field and field.is_visible():
                field.click()
                field.fill(Config.SESSION_PRIMER_URL)
                time.sleep(0.4)
                # если сайт очистил поле — печатаем посимвольно (надёжнее для React-инпутов)
                if not (field.input_value() or '').strip():
                    field.click()
                    page.keyboard.type(Config.SESSION_PRIMER_URL, delay=15)
                    time.sleep(0.4)
        except Exception:
            pass

        for button in page.query_selector_all('button'):
            try:
                if 'download' in (button.inner_text() or '').strip().lower() and button.is_visible():
                    button.click()
                    return
            except Exception:
                pass

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
