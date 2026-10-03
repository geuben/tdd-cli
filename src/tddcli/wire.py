"""The ledger service's wire: newline-delimited JSON over a unix socket.

One request and one response per line. A response is `{"ok": true, "result": ...}`
or `{"ok": false, "refusal": <code>, "error": <text>}`.
"""

from __future__ import annotations

import json
import socket
from pathlib import Path


def send(stream, message: dict) -> None:
    stream.write(json.dumps(message).encode() + b"\n")
    stream.flush()


def receive(stream) -> dict | None:
    """The next message on the stream, or None once the other end has closed it."""
    line = stream.readline()
    return json.loads(line) if line else None


class Connection:
    """One persistent connection to a ledger service socket."""

    def __init__(self, socket_path: Path):
        self.socket_path = Path(socket_path)
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.connect(str(self.socket_path))
        self.stream = self.sock.makefile("rwb")

    def request(self, method: str, *args, **kwargs):
        send(self.stream, {"method": method, "args": list(args), "kwargs": kwargs})
        reply = receive(self.stream)
        return reply["result"]

    def close(self) -> None:
        self.stream.close()
        self.sock.close()


def call(socket_path: Path, method: str, *args, **kwargs):
    """One request on a connection of its own."""
    conn = Connection(socket_path)
    try:
        return conn.request(method, *args, **kwargs)
    finally:
        conn.close()
