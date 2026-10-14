"""The ledger service's wire: rows keep their shape, and a dropped connection fails closed."""

from __future__ import annotations

import shutil
import socket
import tempfile
import threading
from pathlib import Path

import pytest

from tddcli import wire


def test_a_row_reads_like_an_sqlite_row():
    row = wire.decode(wire.encode([{"$row": {"cols": ["id", "source"], "vals": [7, "vm-1"]}}]))[0]
    with pytest.raises(IndexError):
        row["absent"]

    assert (row["source"], row[0], row.keys(), dict(row)) == (
        "vm-1",
        7,
        ["id", "source"],
        {"id": 7, "source": "vm-1"},
    )


def test_sets_and_nested_rows_survive_the_round_trip():
    sent = {"failing": {"t::b", "t::a"}, "rows": [], "n": 3}

    assert wire.decode(wire.encode(sent)) == {"failing": {"t::a", "t::b"}, "rows": [], "n": 3}


@pytest.fixture
def socket_dir():
    # Under /tmp, not tmp_path: a socket path under tmp_path is longer than AF_UNIX allows.
    path = Path(tempfile.mkdtemp(dir="/tmp", prefix="tdd-"))
    yield path
    shutil.rmtree(path, ignore_errors=True)


def _server(path: Path, behave) -> threading.Thread:
    """A one-connection server that does `behave(conn)` and then hangs up."""
    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    listener.bind(str(path))
    listener.listen(1)

    def serve():
        conn, _ = listener.accept()
        try:
            behave(conn)
        finally:
            conn.close()
            listener.close()

    thread = threading.Thread(target=serve, daemon=True)
    thread.start()
    return thread


def test_a_service_that_hangs_up_before_answering_is_unreachable(socket_dir):
    path = socket_dir / "s.sock"
    _server(path, lambda conn: conn.makefile("rb").readline())

    with pytest.raises(wire.LedgerUnreachable, match="closed the connection"):
        wire.call(path, "ping")


def test_a_service_that_is_gone_before_the_request_is_unreachable(socket_dir):
    path = socket_dir / "s.sock"
    _server(path, lambda conn: None)
    conn = wire.Connection(path)
    # Blocks until the server's end has closed, so the request meets a broken pipe.
    assert conn.sock.recv(1, socket.MSG_PEEK) == b""
    try:
        with pytest.raises(wire.LedgerUnreachable, match="dropped the connection"):
            conn.request("ping")
    finally:
        conn.close()
