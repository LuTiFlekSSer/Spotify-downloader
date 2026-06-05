import os

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget
from qfluentwidgets import (LargeTitleLabel, SegmentedWidget, SimpleCardWidget, BodyLabel, CaptionLabel,
                            LineEdit, PushButton, PrimaryPushButton, ProgressBar, InfoBar, InfoBarPosition)

from src.backend.db.data_base import DataBase
from src.backend.db.db_records import Track, TrackStatus
from src.backend.download.pool import DownloaderPool
from src.backend.download.workers import (ScanCompareWorker, PlaylistEnumerateWorker,
                                          TrackResolveWorker, parse_spotify_id)
from src.backend.spotidl.api_client import ApiClient
from src.backend.spotidl.session import SpotiSession
from src.backend.spotify.constants import build_filename
from src.backend.spotify.session import SpotifySession
from src.backend.spotify.tracks import LikedTracksFetcher
from src.frontend.paged_list_view import PagedListView
from src.frontend.sub_windows.login_dialog.login_dialog import LoginDialog
from src.frontend.tracks_window.track_row import TrackRow
from src.global_flags import GlobalFlags
from src.locales.locales import Locales
from src.utils.config import Config
from src.utils.utils import find_mega_parent

# что докачивать при «Скачать»/«Повторить»: не трогаем уже скачанные/пропущенные.
# JPG/TAG-ошибки означают, что файл скачан (тег/обложка не критичны) -> не «провал».
_RETRYABLE = {TrackStatus.MISSING, TrackStatus.QUEUED, TrackStatus.DOWNLOAD_ERROR,
              TrackStatus.NOT_FOUND, TrackStatus.CANCELLED, TrackStatus.LINK_ERROR}
_FAILED = {TrackStatus.DOWNLOAD_ERROR, TrackStatus.NOT_FOUND,
           TrackStatus.CANCELLED, TrackStatus.LINK_ERROR}


class TracksWindow(QWidget):
    def __init__(self, name: str, parent=None):
        super().__init__(parent)
        self.setObjectName(name.replace(' ', '-'))

        self._locales = Locales()
        self._db = DataBase()
        self._session = SpotifySession()
        self._pool = DownloaderPool()
        self._spotidl = SpotiSession()
        self._api = ApiClient(self._spotidl)
        self._flags = GlobalFlags()

        self._tracks: dict[str, Track] = {}
        self._mode = 'sync'
        self._state = 'idle'          # idle | loading | loaded | downloading | done
        self._resolving = False       # multiple-режим: идёт резолв ссылки
        self._run_id = 0              # эпоха: результаты воркеров из старой эпохи игнорируются
        self._base_step = ''          # «базовый» статус (под наложение «получение токена»)
        self._workers: list = []

        self.__init_widgets()
        self._connect()
        self._select_mode('sync')

    # ---------------- UI ----------------
    def __init_widgets(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(36, 28, 36, 28)
        root.setSpacing(16)

        self._l_title = LargeTitleLabel(self._locales.get_string('tracks'))
        self._l_title.setTextColor(QColor(Config.GRAY_COLOR_900), QColor(Config.GRAY_COLOR_50))

        self._segment = SegmentedWidget(self)
        for key in ('sync', 'check', 'playlist', 'multiple'):
            self._segment.addItem(key, self._locales.get_string(f'mode_{key}'))
        self._segment.setCurrentItem('sync')

        self._input_stack = QStackedWidget(self)
        self._input_stack.setFixedHeight(56)
        self._input_stack.addWidget(self._build_hint_page())
        self._input_stack.addWidget(self._build_link_page('playlist'))
        self._input_stack.addWidget(self._build_link_page('multiple'))

        self._table = PagedListView(TrackRow, self)
        table_card = SimpleCardWidget(self)
        card_layout = QVBoxLayout(table_card)
        card_layout.setContentsMargins(8, 8, 8, 8)
        card_layout.addWidget(self._table)

        self._l_step = CaptionLabel('')
        self._progress = ProgressBar(self)
        self._progress.setFixedWidth(220)
        self._progress.hide()
        self._l_count = CaptionLabel('')
        self._stop_btn = PushButton(self._locales.get_string('stop'))
        self._stop_btn.setFixedWidth(150)
        self._stop_btn.hide()
        self._action_btn = PrimaryPushButton(self._locales.get_string('start_action'))
        self._action_btn.setFixedWidth(150)

        bottom = QHBoxLayout()
        bottom.setSpacing(12)
        bottom.addWidget(self._l_step)
        bottom.addWidget(self._progress)
        bottom.addStretch(1)
        bottom.addWidget(self._l_count)
        bottom.addWidget(self._stop_btn)
        bottom.addWidget(self._action_btn)

        root.addWidget(self._l_title)
        root.addWidget(self._segment)
        root.addWidget(self._input_stack)
        root.addWidget(table_card, 1)
        root.addLayout(bottom)

    def _build_hint_page(self) -> QWidget:
        page = QWidget()
        layout = QHBoxLayout(page)
        layout.setContentsMargins(2, 0, 2, 0)
        self._l_hint = BodyLabel(self._locales.get_string('sync_hint'))
        self._l_hint.setTextColor(QColor(Config.GRAY_COLOR_600), QColor(Config.GRAY_COLOR_300))
        layout.addWidget(self._l_hint)
        layout.addStretch(1)
        return page

    def _build_link_page(self, mode: str) -> QWidget:
        page = QWidget()
        layout = QHBoxLayout(page)
        layout.setContentsMargins(2, 0, 2, 0)
        layout.setSpacing(12)
        edit = LineEdit()
        edit.setPlaceholderText(self._locales.get_string(
            'playlist_link_ph' if mode == 'playlist' else 'track_link_ph'))
        button = PushButton(self._locales.get_string('confirm' if mode == 'playlist' else 'add'))
        button.setFixedWidth(130)
        layout.addWidget(edit, 1)
        layout.addWidget(button)
        if mode == 'playlist':
            self._playlist_edit, self._playlist_btn = edit, button
            button.clicked.connect(self._confirm_playlist)
        else:
            self._multiple_edit, self._multiple_btn = edit, button
            button.clicked.connect(self._add_track)
        return page

    def _connect(self):
        self._segment.currentItemChanged.connect(self._select_mode)
        self._action_btn.clicked.connect(self._on_action)
        self._stop_btn.clicked.connect(lambda: self._pool.stop())
        self._pool.events.sig_track_status.connect(self._on_track_status)
        self._pool.events.sig_progress.connect(self._on_progress)
        self._pool.events.sig_finished.connect(self._on_finished)
        self._spotidl.events.sig_refreshing.connect(self._on_token_refreshing)
        self._spotidl.events.sig_refreshed.connect(self._on_token_refreshed)

    def _set_step(self, text: str):
        self._base_step = text
        self._l_step.setText(text)

    def _on_token_refreshing(self):
        self._l_step.setText(self._locales.get_string('getting_token'))   # наложение поверх базового

    def _on_token_refreshed(self):
        self._l_step.setText(self._base_step)

    # ---------------- mode / state ----------------
    def open_mode(self, key: str):
        """Открыть конкретный режим (вызов с карточки на Home)."""
        if self._is_busy():
            return
        if self._segment.currentRouteKey() == key:
            self._select_mode(key)                  # сегмент уже здесь — сигнал не сработает
        else:
            self._segment.setCurrentItem(key)       # сменит сегмент -> currentItemChanged -> _select_mode

    def _is_busy(self) -> bool:
        return self._state in ('loading', 'downloading') or self._resolving

    def _select_mode(self, key: str):
        if self._is_busy():
            self._segment.setCurrentItem(self._mode)     # смена режима запрещена во время работы
            return
        self._mode = key
        self._input_stack.setCurrentIndex({'sync': 0, 'check': 0, 'playlist': 1, 'multiple': 2}[key])
        if key in ('sync', 'check'):
            self._l_hint.setText(self._locales.get_string('sync_hint' if key == 'sync' else 'check_hint'))
        self._reset()

    def _reset(self):
        self._run_id += 1                  # инвалидируем результаты идущих воркеров
        self._resolving = False
        self._tracks = {}
        self._table.set_items({})
        self._state = 'idle'
        self._set_step('')
        self._l_count.setText('')
        self._progress.hide()
        self._update_buttons()

    def _update_buttons(self):
        s = self._locales.get_string
        self._lock_navigation(self._is_busy())
        if self._state == 'downloading':
            self._action_btn.hide()
            self._stop_btn.show()
            return
        self._stop_btn.hide()
        self._action_btn.show()

        failed = any(t.status in _FAILED for t in self._tracks.values())
        has = bool(self._tracks)

        if self._mode in ('sync', 'check'):
            if self._state == 'loading':
                self._action_btn.setEnabled(False)
                return
            if self._state == 'idle':
                self._action_btn.setText(s('start_action'))
                self._action_btn.setEnabled(True)
            elif self._mode == 'check':
                self._action_btn.setText(s('refresh_action'))
                self._action_btn.setEnabled(True)
            else:  # sync loaded/done
                self._action_btn.setText(s('retry_short') if (failed and self._state == 'done') else s('download_btn'))
                self._action_btn.setEnabled(has)
        else:  # playlist / multiple
            self._action_btn.setText(s('retry_short') if (failed and self._state == 'done') else s('download_btn'))
            self._action_btn.setEnabled(has and self._state in ('loaded', 'done') and not self._resolving)

    def _on_action(self):
        if self._mode == 'sync' and self._state in ('loaded', 'done'):
            self._start_download()
        elif self._mode in ('sync', 'check'):
            self._start_sync_check()
        else:
            self._start_download()

    # ---------------- sync / check ----------------
    def _start_sync_check(self):
        if not self._require_login():
            return
        if self._mode == 'sync' and not self._require_folder():
            return
        rid = self._reset_for_load(self._locales.get_string('fetching_liked'))
        fetcher = LikedTracksFetcher(self._session)
        self._track_worker(fetcher)
        fetcher.sig_progress.connect(self._on_indeterminate_progress)
        fetcher.sig_finished.connect(lambda tracks, r=rid: self._on_liked_fetched(tracks, r))
        fetcher.sig_error.connect(lambda e, r=rid: self._fail_if('get_spotify_tracks_error', r))
        fetcher.start()

    def _on_liked_fetched(self, tracks: list, rid: int):
        if rid != self._run_id:
            return
        spotify_by_name = {build_filename(t.title, t.artists): t for t in tracks}
        directory = self._db.get_setting('download_dir')
        self._set_step(self._locales.get_string('scanning_folder'))
        worker = ScanCompareWorker(directory, spotify_by_name)
        self._track_worker(worker)
        worker.sig_finished.connect(lambda sm, lm, r=rid: self._on_compared(sm, lm, r))
        worker.sig_error.connect(lambda e, r=rid: self._fail_if('error', r))
        worker.start()

    def _on_compared(self, server_missing, local_missing, rid: int):
        if rid != self._run_id:
            return
        self._populate(local_missing)
        self._state = 'loaded'
        self._progress.hide()
        self._set_step(self._locales.get_string('no_missing') if not local_missing else '')
        self._l_count.setText(self._locales.get_string('tracks_count').format(n=len(local_missing)))
        self._update_buttons()

    # ---------------- playlist ----------------
    def _confirm_playlist(self):
        playlist_id = parse_spotify_id(self._playlist_edit.text())
        if not playlist_id:
            self._toast_error('invalid_link')
            return
        rid = self._reset_for_load(self._locales.get_string('enumerating'))
        worker = PlaylistEnumerateWorker(self._api, playlist_id)
        self._track_worker(worker)
        worker.sig_finished.connect(lambda tracks, r=rid: self._on_enumerated(tracks, r))
        worker.sig_error.connect(lambda e, r=rid: self._fail_if('link_work_error', r))
        worker.start()

    def _on_enumerated(self, tracks: list, rid: int):
        if rid != self._run_id:
            return
        self._populate(tracks)
        self._state = 'loaded'
        self._progress.hide()
        self._set_step('')
        self._l_count.setText(self._locales.get_string('tracks_count').format(n=len(tracks)))
        self._update_buttons()

    # ---------------- multiple ----------------
    def _add_track(self):
        track_id = parse_spotify_id(self._multiple_edit.text())
        if not track_id:
            self._toast_error('invalid_link')
            return
        self._resolving = True
        self._multiple_btn.setEnabled(False)
        self._set_step(self._locales.get_string('resolving_track'))
        self._update_buttons()
        rid = self._run_id
        worker = TrackResolveWorker(self._api, track_id)
        self._track_worker(worker)
        worker.sig_finished.connect(lambda track, r=rid: self._on_resolved(track, r))
        worker.sig_error.connect(lambda e, r=rid: self._after_add('invalid_link', r))
        worker.start()

    def _on_resolved(self, track: Track, rid: int):
        if rid == self._run_id and track.id not in self._tracks:
            self._tracks[track.id] = track
            self._table.add_item(track.id, track)
            self._multiple_edit.clear()
            if self._state not in ('downloading', 'done'):
                self._state = 'loaded'
            self._l_count.setText(self._locales.get_string('tracks_count').format(n=len(self._tracks)))
        self._after_add(None, rid)

    def _after_add(self, error_key, rid: int):
        self._resolving = False
        self._multiple_btn.setEnabled(True)
        self._set_step('')
        if error_key and rid == self._run_id:
            self._toast_error(error_key)
        self._update_buttons()

    # ---------------- download ----------------
    def _start_download(self):
        if not self._require_folder():
            return
        to_download = [t for t in self._tracks.values() if t.status in _RETRYABLE]
        if not to_download:
            self._toast('nothing_to_download', success=True)
            return
        directory = self._db.get_setting('download_dir')
        if not self._pool.download(to_download, directory, sync=(self._mode == 'sync')):
            self._toast_error('program_is_busy')        # пул уже занят
            return
        self._state = 'downloading'
        self._progress.show()
        self._progress.setValue(0)
        self._set_step(self._locales.get_string('tracks_downloading'))
        self._update_buttons()

    def _on_track_status(self, track_id: str, status: TrackStatus):
        track = self._tracks.get(track_id)
        if track is None:
            return
        track.status = status
        self._table.update_item(track_id)

    def _on_progress(self, done: int, total: int):
        if total:
            self._progress.setValue(int(done / total * 100))
        self._l_count.setText(self._locales.get_string('progress_count').format(done=done, total=total))

    def _on_finished(self, summary):
        if self._state != 'downloading':
            return
        self._state = 'done'
        self._progress.hide()
        self._set_step(self._locales.get_string('download_done'))
        self._update_buttons()

    # ---------------- helpers ----------------
    def _populate(self, tracks: list):
        self._tracks = {t.id: t for t in tracks}
        self._table.set_items(self._tracks)

    def _reset_for_load(self, step: str) -> int:
        self._run_id += 1
        self._resolving = False
        self._tracks = {}
        self._table.set_items({})
        self._state = 'loading'
        self._set_step(step)
        self._l_count.setText('')
        self._progress.show()
        self._progress.setValue(0)
        self._update_buttons()
        return self._run_id

    def _on_indeterminate_progress(self, done: int, total: int):
        if total:
            self._progress.setValue(int(done / total * 100))

    def _fail_if(self, key: str, rid: int):
        if rid != self._run_id:
            return
        self._state = 'idle'
        self._progress.hide()
        self._set_step('')
        self._toast_error(key)
        self._update_buttons()

    def _track_worker(self, worker):
        self._workers.append(worker)
        worker.finished.connect(lambda w=worker: self._workers.remove(w) if w in self._workers else None)

    def _require_login(self) -> bool:
        if self._session.is_authenticated():
            return True
        hmi = find_mega_parent(self)
        self._toast_error('need_login')
        self._flags.modal_open.set()
        LoginDialog(hmi).exec()
        self._flags.modal_open.clear()
        return self._session.is_authenticated()

    def _require_folder(self) -> bool:
        folder = self._db.get_setting('download_dir')
        if folder and os.path.isdir(folder):
            return True
        self._toast_error('need_folder')
        return False

    def _toast_error(self, key: str):
        self._toast(key, success=False)

    def _toast(self, key: str, success: bool):
        hmi = find_mega_parent(self)
        fn = InfoBar.success if success else InfoBar.warning
        fn(title=self._locales.get_string('check' if success else 'error'),
           content=self._locales.get_string(key), position=InfoBarPosition.BOTTOM_RIGHT,
           duration=3500, parent=hmi)

    def _lock_navigation(self, locked: bool):
        hmi = find_mega_parent(self)
        if hasattr(hmi, 'set_navigation_locked'):
            hmi.set_navigation_locked(locked)
