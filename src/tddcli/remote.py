"""The guest's side of the ledger service: a ledger it can use but never holds.

A runner configured with `ledger_socket` keeps no ledger. `RemoteLedger` stands in for
`Ledger` and sends each call through the socket, by method name, to the service that
owns the host's SQLite files. The guest never sees a file, a connection or a line of
SQL: only the named methods the service is willing to answer.
"""

from __future__ import annotations

from pathlib import Path

from . import wire


class RemoteLedger:
    def __init__(self, socket_path: Path, repo_path: Path):
        self.repo_path = repo_path
        self.path = Path(socket_path)
        # One connection for the whole command: an `advance` makes hundreds of calls,
        # and over a forwarded socket each new connection is a new channel.
        self._conn = wire.Connection(self.path)
        self._conn.request("open", str(repo_path))

    def __getattr__(self, name: str):
        if name.startswith("_"):
            raise AttributeError(name)

        def call(*args, **kwargs):
            return self._conn.request(name, *args, **kwargs)

        return call

    def close(self) -> None:
        self._conn.close()
