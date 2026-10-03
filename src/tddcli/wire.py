"""The ledger service's wire: newline-delimited JSON over a unix socket.

One request and one response per line. A request is `{"method", "args", "kwargs"}`;
a response is `{"ok": true, "result": ...}` or `{"ok": false, "error": <text>}`.

Results keep their shape across the socket: a ledger row is sent as
`{"$row": {"cols": [...], "vals": [...]}}` and comes back as a `Row`, which reads the
way an `sqlite3.Row` does; a set is sent as `{"$set": [...]}` and comes back a set.
"""

from __future__ import annotations

import json
import socket
from pathlib import Path


class Row:
    """A ledger row received over the wire: `row["col"]`, `row[i]`, `keys()`, `dict(row)`."""

    def __init__(self, cols: list[str], vals: list):
        self._cols = list(cols)
        self._vals = list(vals)

    def keys(self) -> list[str]:
        return list(self._cols)

    def __getitem__(self, key):
        if isinstance(key, (int, slice)):
            return self._vals[key]
        try:
            return self._vals[self._cols.index(key)]
        except ValueError:
            raise IndexError(f"No item with that key: {key!r}") from None

    def __iter__(self):
        return iter(self._vals)

    def __len__(self) -> int:
        return len(self._vals)

    def __eq__(self, other) -> bool:
        return isinstance(other, Row) and (self._cols, self._vals) == (other._cols, other._vals)

    def __repr__(self) -> str:
        return f"Row({dict(zip(self._cols, self._vals, strict=True))!r})"


def encode(value):
    """A ledger method's result, as JSON-able data."""
    if isinstance(value, dict):
        return {k: encode(v) for k, v in value.items()}
    if isinstance(value, (set, frozenset)):
        return {"$set": [encode(v) for v in sorted(value, key=repr)]}
    if isinstance(value, (list, tuple)):
        return [encode(v) for v in value]
    if hasattr(value, "keys") and hasattr(value, "__getitem__"):  # a row
        cols = list(value.keys())
        return {"$row": {"cols": cols, "vals": [value[c] for c in cols]}}
    return value


def decode(value):
    if isinstance(value, list):
        return [decode(v) for v in value]
    if isinstance(value, dict):
        if set(value) == {"$row"}:
            return Row(value["$row"]["cols"], value["$row"]["vals"])
        if set(value) == {"$set"}:
            return {decode(v) for v in value["$set"]}
        return {k: decode(v) for k, v in value.items()}
    return value


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
        if not reply.get("ok"):
            raise RuntimeError(reply.get("error") or f"the ledger service refused {method}")
        return decode(reply.get("result"))

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
