from __future__ import annotations

import json
import socket
import struct
from threading import Event, Thread
from typing import Any, Callable

from .config import DEFAULT_TIMEOUT_SECONDS
from .protocol import PeerInfo


class NetworkError(Exception):
    pass


def _recv_exact(sock: socket.socket, size: int) -> bytes:
    data = bytearray()
    while len(data) < size:
        chunk = sock.recv(size - len(data))
        if not chunk:
            raise NetworkError("Connection closed while receiving data")
        data.extend(chunk)
    return bytes(data)


def send_framed_json(sock: socket.socket, message: dict[str, Any]) -> None:
    payload = json.dumps(message).encode("utf-8")
    header = struct.pack("!I", len(payload))
    sock.sendall(header + payload)


def recv_framed_json(sock: socket.socket) -> dict[str, Any]:
    header = _recv_exact(sock, 4)
    size = struct.unpack("!I", header)[0]
    payload = _recv_exact(sock, size)
    return json.loads(payload.decode("utf-8"))


def rpc_call(peer: PeerInfo, message: dict[str, Any], timeout: float = DEFAULT_TIMEOUT_SECONDS) -> dict[str, Any]:
    with socket.create_connection((peer.host, peer.port), timeout=timeout) as sock:
        sock.settimeout(timeout)
        send_framed_json(sock, message)
        return recv_framed_json(sock)


class PeerServer:
    def __init__(
        self,
        host: str,
        port: int,
        handler: Callable[[dict[str, Any]], dict[str, Any]],
    ) -> None:
        self.host = host
        self.port = port
        self._handler = handler
        self._stop = Event()
        self._thread: Thread | None = None
        self._socket: socket.socket | None = None

    def start(self) -> None:
        if self._thread is not None:
            return

        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((self.host, self.port))
        server_socket.listen()
        server_socket.settimeout(0.5)

        self._socket = server_socket
        self._thread = Thread(target=self._serve, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._socket is not None:
            try:
                self._socket.close()
            except OSError:
                pass
            self._socket = None
        if self._thread is not None:
            self._thread.join(timeout=1.0)
            self._thread = None

    def _serve(self) -> None:
        assert self._socket is not None
        while not self._stop.is_set():
            try:
                client, _ = self._socket.accept()
            except socket.timeout:
                continue
            except TimeoutError:
                continue
            except OSError:
                break
            worker = Thread(target=self._handle_client, args=(client,), daemon=True)
            worker.start()

    def _handle_client(self, client: socket.socket) -> None:
        with client:
            try:
                message = recv_framed_json(client)
                response = self._handler(message)
            except Exception as exc:
                response = {"status": "error", "error": str(exc)}
            send_framed_json(client, response)
