# План перехода Spotify Downloader → PySide6 + Fluent

> Ветка: **`rewrite/pyside6-fluent`** (создана от `develop`).
> Референс архитектуры: `E:\PyCharm\Encryption_app` (PyQt5 + PyQt-Fluent-Widgets).
> Цель: полностью переписать приложение на **PySide6 + PySide6-Fluent-Widgets**, сохранив
> поведение для пользователя, но переработав код. Заложить глобальное потокобезопасное
> хранилище ключа Cloudflare с обновлением по истечении срока.

---

## 1. Что есть сейчас (итоги анализа)

**Стек:** CustomTkinter + CTkMessagebox + CTkMenuBar + Pillow, spotipy, eyed3, requests,
pyperclip, pywin32. ~5 500 строк, плоская структура пакетов в корне.

**Функциональность (сохраняем для пользователя):**
- 4 режима: **Sync** (двусторонняя синхронизация локальной папки с «любимыми»),
  **Check/Compare** (только сравнение), **Playlist** (скачать плейлист по ссылке),
  **Multiple** (скачивать отдельные треки по ссылкам по одной).
- Игнор-листы: локальный и серверный.
- Авто-переименование локальных файлов, если трек переименовали в Spotify (по id).
- Настраиваемое число потоков, автообновление приложения, выбор языка (ru/en).
- Spotify OAuth по client_id / client_secret / redirect_uri пользователя.

**Главные проблемы старого кода (НЕ переносим):**
- Везде `while thread.is_alive(): self.update(); time.sleep(0.01)` — ручная прокрутка
  Tk-цикла вместо нормальной асинхронности. Это №1 препятствие для порта.
- Общее мутабельное состояние между потоками без синхронизации (работает «на удаче» из-за GIL).
- `SettingsStorage.Settings` — не синглтон, ~14 мест создают свои sqlite-соединения к одному файлу, без блокировок.
- Баги: `compare_versions` сравнивает строки, а не числа (`'10' < '9'`); `_get_track_info`
  на ретрае подменяет `Response` на `dict` → ретраи мертвы; нет таймаутов на `requests`.
- Хранение `client_secret` и `code` открытым текстом в sqlite; auth построен на повторном
  использовании одноразового OAuth-кода (хрупко).

**API загрузки (то, что меняем на Cloudflare-API):**
- `POST https://spotymp3.app/api/download-track {url: open.spotify.com/track/<id>}` → `{file_url}` → `GET file_url` (mp3-байты). — `TrackDownloader/Downloader.py:_get_track_info`.
- `GET https://api.spotifydown.com/metadata/track/<id>` (заголовки origin/referer spotifydown) — валидация ссылки в `MtPool.add`.
- `GET https://api.spotifydown.com/trackList/playlist/<id>?offset=` — список плейлиста.
- Ни в одном из них сейчас **нет** ключа/токена/обработки 403 Cloudflare — это и есть точка интеграции нового ключа.

---

## 2. Что даёт референс (Encryption_app) — паттерны для копирования

| Паттерн референса | Файл | Применение в Spotify |
|---|---|---|
| `Singleton(type)` метакласс на `WeakValueDictionary` | `src/utils/singleton.py` | копируем 1:1 — основа всех глобалов |
| `Config(metaclass=Singleton)` — все константы/пути/URL | `src/utils/config.py` | APP_NAME, пути %APPDATA%, GitHub-релизы, эндпоинты Spotify/Cloudflare, TTL ключа |
| `SingletonStorage` — eager-init всех синглтонов в `main()` | `src/singleton_storage.py` | держит strong-ref (иначе WeakValueDict соберёт GC) |
| `MasterKeyStorage(metaclass=Singleton)` — общий секрет | `src/master_key_storage/` | **прямой шаблон для CloudflareKeyStorage** |
| `GlobalFlags(metaclass=Singleton)` c `threading.Event` | `src/global_flags.py` | `stop_event`, `is_running`/`is_syncing`, `modal_open` |
| Поллер-поток + ThreadPoolExecutor + `Events(QObject)` сигналы | `loader_thread.py`, `backend/encrypt_libs/loader.py` | **шаблон движка загрузки** |
| `MSFluentWindow` + `addSubInterface` + splash + сохранение геометрии | `src/frontend/hmi.py` | каркас главного окна |
| `find_mega_parent()` + маркер `ULTRA_MEGA_PARENT` | `src/utils/utils.py` | доступ виджетов к главному окну без импортов |
| `PagedListView` — виртуализированный список с пулом виджетов-строк | `src/frontend/paged_list_view.py` | **таблица треков** (тянет десятки тысяч строк) |
| 3-слойное окно: Window → ButtonsCard(CommandBar) → ContentCard | `passwords_window/`, `history_window/` | страница треков, история загрузок |
| `MessageBoxBase` + `validate()` + `PopupTeachingTip` | `sub_windows/` | все модалки (логин, подтверждения, ошибки) |
| `QConfig` + `ConfigItem`/валидаторы + `SettingCard`-ы | `settings_window/` | страница настроек |
| `DataBase(metaclass=Singleton)` sqlite + один Lock, `check_same_thread=False` | `src/backend/db/` | единое потокобезопасное хранилище |
| `StyleSheetBase`-enum, `FluentIconBase`-enum, JSON-локали-синглтон | `style_sheets/`, `icons/`, `locales/` | стили/иконки/локализация |
| `InstanceManager` — single-instance (`msvcrt` lock) + `QLocalServer` IPC | `src/frontend/instance_manager.py` | один экземпляр + открытие ссылок из 2-го запуска |

> ⚠️ Референс на **PyQt5**, цель — **PySide6**: меняем `from PyQt5.QtCore import QObject, pyqtSignal`
> → `from PySide6.QtCore import QObject, Signal`; `pyqtSignal(...)` → `Signal(...)`. API `QtNetwork`
> (`QLocalServer/QLocalSocket`) и qfluentwidgets идентичны. Пакет — `PySide6-Fluent-Widgets` (импорт тот же — `qfluentwidgets`).

---

## 3. Контракты совместимости — НЕ менять побайтно

Иначе сломается совместимость с уже скачанными файлами / существующими установками:

1. **Карта замены символов имени файла** (`SpotifyTracks.SpTracks.dict_for_replace`, 9 символов
   `/ \ : " * ? < > |` → Unicode-двойники, разделитель артистов `⧸` = U+29F8). Вынести в общий
   модуль констант — её читает и фетчер, и `create_download_query`.
2. **Формат имени:** `"<title> - <artist1>⧸<artist2>".mp3`; `release_date` обрезается до года (`[:4]`); `cover = images[0].url`.
3. **`Status`-enum** (OK/API_ERR/GET_ERR/JPG_ERR/NF_ERR/TAG_ERR/CANCELLED/LINK_ERR) и **ключи `pool_status`**
   (`ok/get_err/jpg_err/nf_err/tag_err/cancelled/link_err/launched/all_tracks` + `quantity/list`) — UI завязан на них.
4. **settings.db**: путь `%APPDATA%\Spotify downloader\settings.db`, таблицы `app_settings`,
   `tracks_id(name,track_id)`, `local_ignore(name)`, `server_ignore(name)`; булевы — строки `'True'/'False'`,
   `'None'` как sentinel. Нужен авто-миграционный импорт при первом запуске нового приложения.
5. **Spotify OAuth**: scope `user-library-read`, кэш-файл `%APPDATA%\Spotify downloader\.cache`.
6. **`Locales/locales.json`** (~130 ключей, ru+en) — переиспользуем как есть, ключи = контракт всего UI.
7. **GitHub releases**, версия в `Version.__version__`, схема самообновления `-U`/`-F` (двухпроцессная подмена exe).

---

## 4. Новый download-API (`spotidownloader.com`) и хранилище сессии

Старый API (`spotymp3.app` / `spotifydown.com`) заменяется на **`api.spotidownloader.com`**.
Доступ двухключевой (источники: папка `Запросы/` и проект `turnstile_bypass/`):

**Ключ №1 — Turnstile-токен Cloudflare (одноразовый).** Добывается автоматизацией браузера
**Camoufox** (undetected Firefox): открыть `https://spotidownloader.com/en`, кликнуть чекбокс Turnstile
(iframe `challenges.cloudflare.com`), считать `input[name="cf-turnstile-response"]`. Нужен только для
получения сессии (после — выбрасывается).

**Ключ №2 — сессионный JWT (живёт ~10 минут).** `POST /session {token:<turnstile>}` →
`{success, token:"<JWT>"}`. JWT = `header.payload.signature`; в payload есть `iat`/`exp` (подтверждено:
**exp − iat = 600 c**). Этот Bearer-JWT шарят все потоки загрузки, и **именно он истекает** — его обновление
и есть «логика обновления ключа». `exp` читается прямо из JWT, TTL угадывать не нужно.

**Запросы** (заголовки `origin`/`referer` = `https://spotidownloader.com/`, реалистичный `user-agent`;
все, кроме `/session` и скачивания байтов, — с `Authorization: Bearer <JWT>`):

| Назначение | Запрос | Тело | Ответ |
|---|---|---|---|
| Сессия | `POST /session` | `{token:<turnstile>}` | `{success, token:"<JWT>"}` |
| Метаданные плейлиста/трека | `POST /metadata` | `{type:"playlist"\|"track", id}` | `{artists, title, cover, releaseDate, ...}` |
| Список треков (пагинация по `offset`) | `POST /tracks` | `{type, id, offset}` | `{success, trackList:[{id,title,artists,cover,album,releaseDate}], statusCode}` |
| Ссылка на mp3 | `POST /download` | `{id}` | `{success, metadata:{...,isrc}, link, linkFlac}` |
| Сами байты | `GET <link>` | — | mp3 (подписанный tunnel-URL `*.yt-dl.click?id&exp&sig&sec&iv`, **без** авторизации) |

**Важно:** форма трека (`id, title, artists`-строка-через-запятую`, album, releaseDate, cover`) совпадает
со старой, которую уже ждёт `create_download_query` → имя файла/теги переносятся почти без изменений.
«Любимые» по-прежнему берутся из Spotify (spotipy, OAuth пользователя); spotidownloader нужен только чтобы
по track-id получить ссылку на mp3 и для метаданных/списков при вставленной ссылке.

### Структура пакета

```
src/backend/spotidl/
  turnstile.py     # TurnstileSolver(Camoufox) -> cf-turnstile-response
  session.py       # SpotiSession(metaclass=Singleton): Bearer-JWT + exp; get_token()/force_refresh()/clear()
  api_client.py    # ApiClient: metadata/tracks/download/fetch_bytes; инъекция Bearer; retry-on-401
  constants.py     # эндпоинты, заголовки, refresh-margin
```

### `SpotiSession` (это и есть «глобальное хранилище ключа»)

```python
class SpotiSession(metaclass=Singleton):
    class Events(QObject):
        sig_refreshing = Signal(); sig_refreshed = Signal(); sig_refresh_failed = Signal(str)
    events = Events()

    def __init__(self):
        self._lock = RLock()
        self._token = ''
        self._exp = 0.0            # из payload JWT (epoch); 0 == сессии нет
        self._margin = 30.0        # обновлять за 30 c до exp

    def get_token(self) -> str:    # single-flight: N потоков на истёкшей сессии -> ровно ОДИН refresh
        with self._lock:
            if not self._token or time.time() >= self._exp - self._margin:
                self._refresh_locked()
            return self._token

    def force_refresh(self):       # на 401/«expired» в ответе API
        with self._lock:
            self._refresh_locked()

    def _refresh_locked(self):
        self.events.sig_refreshing.emit()
        try:
            cf = TurnstileSolver().solve()                       # дорого: поднимает браузер
            jwt = post('/session', json={'token': cf})['token']
            self._token = jwt
            self._exp = _read_exp_from_jwt(jwt)                  # base64-decode payload -> exp
            self.events.sig_refreshed.emit()
        except Exception as e:
            self._token, self._exp = '', 0.0
            self.events.sig_refresh_failed.emit(str(e)); raise

    def clear(self):
        with self._lock: self._token, self._exp = '', 0.0
```

**Интеграция:**
- Инстанцируется один раз в `SingletonStorage` (strong-ref держит от GC).
- Каждый запрос `ApiClient` берёт `Bearer = SpotiSession().get_token()` — токен **не** передаётся через
  сигнатуры задач пула. На ответ 401/«expired» → `force_refresh()` + один повтор.
- `TurnstileSolver` (и весь сетевой код) — **только** на воркер-потоках, никогда на GUI-потоке.
- single-flight критичен: при синхронизации сотен треков (>10 мин) сессия истечёт в процессе и обновится
  прозрачно **один раз** (под `RLock`), а не каждым потоком; так избегаем шторма запусков браузера.
- Сигналы `Events` → статус-карточка на Home («Сессия: активна / обновляется / ошибка») через `InfoBar`.

### Решения по Camoufox
1. **Поставка браузера → вшить в инсталлятор.** Патченый Firefox (сотни МБ) кладём в сборку Inno Setup
   и указываем Camoufox путь к встроенному браузеру (env/конфиг Camoufox), чтобы работало оффлайн без
   `camoufox fetch`. Инсталлятор большой — это принято.
2. **Режим → headless по умолчанию.** `TurnstileSolver(headless=True)` (значение из `Config`/настройки),
   архитектурно абстрагировано, чтобы переключить на видимое окно одним флагом. Пользователь протестирует
   надёжность headless; если Turnstile в headless не решается — флипаем на видимое окно.
3. **Деградация.** Если Turnstile не решился за таймаут — `sig_refresh_failed` → `InfoBar.error` + пауза
   очереди загрузки, без падения приложения.

---

## 5. Новая модель многопоточности (вместо busy-wait)

3-слойное разделение из референса:

1. **`DownloaderPool(metaclass=Singleton)`** — владеет `ThreadPoolExecutor(max_workers=threads)`,
   одним `Lock`, очередью `set[DownloadTask]`, учётом `_running`/`_done`, и `events = Events(QObject)`.
   `DownloadTask` = uid (uuid4) + track_id + future + счётчик прогресса (под мелким локом) + статус.
2. **`DownloaderThread(threading.Thread, daemon=True)`** — единственный поллер: цикл
   `while not GlobalFlags().stop_event.is_set(): DownloaderPool().exec(); time.sleep(Config.THREAD_SLEEP)`.
   Стартует один раз в `main()` до UI.
3. **`Events(QObject)`** с сигналами `sig_download_start(uid, total)`, `sig_progress(uid, cur, total)`,
   `sig_status(uid, TrackStatus)`, `sig_update()`. UI-страница коннектится к ним; слоты бегут на GUI-потоке
   (queued connection) и только обновляют модель таблицы. `exec()` троттлит общий апдейт до ~10 Гц и
   шлёт `sig_progress` только при изменении целого процента (как `Loader.exec`).
- **Отмена/закрытие:** `GlobalFlags.stop_event` останавливает поллер; `closeEvent` главного окна
  блокирует выход, пока `is_running` (показывает `InfoBar.error`), иначе ставит `stop_event` и сохраняет геометрию.
- spotify-фетч, sync-diff, логин, апдейтер — те же воркеры/сигналы, без `self.update()`.

---

## 6. Целевая структура каталогов

```
main.py                       # bootstrap: chdir(frozen), InstanceManager-lock, SingletonStorage, поллеры, create_ui
src/
  utils/
    singleton.py              # копия из референса
    config.py                 # Config(Singleton): пути, URL, эндпоинты, TTL, тайминги
    utils.py                  # find_mega_parent, resource_path (PyInstaller _MEIPASS), get_normalized_size, compare_versions (ИСПРАВЛЕННАЯ)
  singleton_storage.py        # eager-init всех синглтонов
  global_flags.py             # stop_event / is_running / is_syncing / modal_open
  version/__init__.py         # __version__
  locales/
    locales.py                # Locales(Singleton): JSON + auto-detect языка + persist
    locales.json              # перенести существующий (ru/en, ~130 ключей)
    errors.py
  backend/
    db/
      data_base.py            # DataBase(Singleton): sqlite check_same_thread=False + Lock; settings + tracks + ignore + history
      db_records.py           # TrackRecord, TrackStatus(Enum), SyncResult(Enum)
      migration.py            # импорт старого settings.db при первом запуске
    spotify/
      session.py              # OAuth (бывш. SpotifyLogin.Login) — логика без UI, refresh-token
      tracks.py               # фетч liked-треков (бывш. SpTracks), воркер+сигналы
      constants.py            # dict_for_replace, формат имени (общий контракт)
    spotidl/                  # новый download-API spotidownloader.com (§4)
      turnstile.py            # TurnstileSolver(Camoufox) -> cf-turnstile-response
      session.py              # SpotiSession(Singleton): Bearer-JWT + exp, single-flight refresh
      api_client.py           # ApiClient: /metadata /tracks /download + GET bytes; инъекция Bearer; retry-on-401
      constants.py            # эндпоинты, заголовки, refresh-margin
    download/
      downloader.py           # одна задача загрузки (бывш. Downloader) + eyed3-тегирование (почти как есть)
      pool.py                 # DownloaderPool(Singleton) + DownloadTask
      diff.py                 # LcTracks + Comparator: чистый compute_diff() отдельно от apply_renames()
    updater/
      updater.py              # GitHub-релизы, скачивание, -U/-F подмена exe (с таймаутами, исправл. версией)
  frontend/
    instance_manager.py       # single-instance + IPC (копия, под Spotify-команды)
    hmi.py                    # MainWindow(MSFluentWindow) + create_ui()
    paged_list_view.py        # копия виртуализированного списка
    icons/icons.py            # CustomIcons(FluentIconBase): SPOTIFY/DOWNLOAD/SYNC/KEY
    style_sheets/             # StyleSheet(StyleSheetBase) + qss/*.qss
    home_window/              # дашборд: статус логина/ключа/пула, действия
    tracks_window/            # 4 режима + таблица треков + прогресс
    settings_window/          # SpotifyConfig(QConfig) + SettingCard-ы + ignore-листы
    sub_windows/
      message_box/            # generic confirm/error
      login_dialog/           # OAuth-визард (2 шага) на MessageBoxBase/QStackedWidget
      update_window/          # экран обновления
```

---

## 7. Поэтапный план работ

**Фаза 0 — Каркас (фундамент).**
`requirements.txt` (PySide6, PySide6-Fluent-Widgets, spotipy, eyed3, requests, pywin32, packaging,
camoufox, browserforge — для Turnstile-солвера, §4).
`singleton.py`, `config.py`, `global_flags.py`, `utils.py`, `version`. `main.py` с frozen-chdir и
`InstanceManager`. Пустой `MSFluentWindow` со splash, темой, сохранением геометрии. Запускается «hello world».

**Фаза 1 — Backend-хранилища.**
`DataBase` (sqlite+Lock), `db_records`, миграция старого `settings.db`. `Locales`-синглтон (+ auto-detect).
`StyleSheet`/`CustomIcons`. Никакого UI-функционала ещё.

**Фаза 2 — Spotify-аккаунт и треки.**
Перенести `Login`/`Errors` (логика без UI), **починить на refresh-token**. `tracks.py` (фетч liked,
воркер+сигналы, исправить баг прогресса >100%). `login_dialog` на `MessageBoxBase`. Дашборд Home со статусом логина.

**Фаза 3 — Движок загрузки + сессия spotidownloader (§4).**
`spotidl/`: `turnstile.py` (Camoufox-solver), `SpotiSession` (Bearer-JWT + exp + single-flight refresh),
`api_client.py` (`/metadata` `/tracks` `/download` + GET байтов, инъекция Bearer, retry-on-401, таймауты).
`downloader.py` (eyed3-тегирование почти как есть), `DownloaderPool` + `DownloaderThread` (§5),
`diff.py` (чистый compute_diff отдельно от apply_renames). Сначала автономный e2e-тест:
solve → session → tracks(плейлист) → download(id) → mp3, затем интеграция в пул.

**Фаза 4 — UI страницы.**
`tracks_window`: 4 режима (Sync/Check/Playlist/Multiple) поверх `PagedListView` + карточки-строки
(обложка/название/артисты/статус/прогресс), `CommandBar`, прогресс-бар, отмена/ретрай, редактирование
игнор-листов. `settings_window`: `SpotifyConfig(QConfig)` + карточки (потоки, папка, форматы, авто-сравнение,
автообновление, перезапись, язык, очистка данных) + игнор-листы. Все модалки/ошибки → `MessageBox`/`InfoBar`.

**Фаза 5 — Апдейтер.**
`updater.py` + `update_window`. Сохранить `-U`/`-F` и двухпроцессную подмену exe; исправить сравнение версий,
добавить таймауты/User-Agent, чистку temp, проверку размера.

**Фаза 6 — Сборка и проверка.**
Сборка (Nuitka+Inno Setup как в референсе, либо PyInstaller — см. вопрос ниже). `--add-data` для
`locales.json`, иконок, qss. Прогон 4 сценариев на реальном аккаунте. README обновить (скриншоты).

---

## 8. Решения, которые нужно подтвердить

Ниже — мои рекомендации по умолчанию; план написан под них. Если что-то поменяешь — скорректирую.

1. **Виджет таблицы треков:** виртуализированный `PagedListView` с карточками-строками (тянет 10k+ «любимых»,
   совпадает с референсом) — *рекомендую*; альтернатива — `TableWidget` (ближе к старым 3 колонкам №/Title/Status).
2. **Совместимость данных:** авто-миграция существующего `settings.db` (тот же `%APPDATA%`, импорт настроек/
   tracks_id/ignore-листов) — *рекомендую*; альтернатива — старт «с чистого листа».
3. **Spotify-авторизация:** перейти на **refresh-token** (надёжно, не зависит от одноразового кода) —
   *рекомендую*; альтернатива — точно сохранить текущую (хрупкую) схему повторного использования `code`.
4. **Сборка:** **Nuitka + Inno Setup** (как в Encryption_app) — *рекомендую*; альтернатива — оставить PyInstaller.
