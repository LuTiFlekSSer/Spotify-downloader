import msvcrt
import os
from io import IOBase
from typing import Optional

from PySide6.QtCore import QObject, Signal
from PySide6.QtNetwork import QLocalServer, QLocalSocket

from src.utils.config import Config


class InstanceLock:
    def __init__(self, lockfile: str) -> None:
        self.lockfile: str = lockfile
        self.fp: Optional[IOBase] = None

    def acquire(self) -> bool:
        try:
            self.fp = open(self.lockfile, 'w')
            msvcrt.locking(self.fp.fileno(), msvcrt.LK_NBLCK, 1)
            return True
        except OSError:
            if self.fp:
                self.fp.close()
            self.fp = None
            return False

    def release(self) -> None:
        if self.fp:
            try:
                msvcrt.locking(self.fp.fileno(), msvcrt.LK_UNLCK, 1)
            except Exception:
                pass
            try:
                self.fp.close()
            except Exception:
                pass
            try:
                os.remove(self.lockfile)
            except Exception:
                pass
            self.fp = None


class InstanceManager(QObject):
    # action, payload (например 'open', '<spotify-url>')
    sig_external_command = Signal(str, str)

    def __init__(self) -> None:
        super().__init__()
        self._server_name: str = Config.APP_NAME
        self._server: QLocalServer = QLocalServer()
        self._server.newConnection.connect(self._on_new_connection)
        self._lockfile_path: str = os.path.join(
            os.path.expanduser('~'),
            f'.{self._server_name.lower().replace(" ", "_")}_single_instance.lock',
        )
        self._lock: InstanceLock = InstanceLock(self._lockfile_path)
        self.is_primary_instance: bool = False

    def try_acquire_lock(self) -> bool:
        self.is_primary_instance = self._lock.acquire()
        return self.is_primary_instance

    def release_lock(self) -> None:
        self._lock.release()

    def send(self, action: str, payload: str) -> bool:
        socket = QLocalSocket()
        socket.connectToServer(self._server_name)

        if not socket.waitForConnected(500):
            return False

        socket.write(f'{action}|{payload}'.encode('utf-8'))
        socket.flush()
        socket.waitForBytesWritten(1000)
        socket.disconnectFromServer()
        return True

    def start_server(self) -> None:
        QLocalServer.removeServer(self._server_name)
        self._server.listen(self._server_name)

    def _on_new_connection(self) -> None:
        client = self._server.nextPendingConnection()
        if client:
            client.readyRead.connect(lambda: self._on_client_ready_read(client))

    def _on_client_ready_read(self, client: QLocalSocket) -> None:
        msg = bytes(client.readAll().data()).decode('utf-8')
        parts = msg.strip().split('|', 1)

        if len(parts) == 2:
            action, payload = parts
            self.sig_external_command.emit(action, payload)

        client.disconnectFromServer()
