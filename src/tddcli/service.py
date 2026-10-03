"""The ledger service: the host's only writer of its ledgers, reached over unix sockets."""

from __future__ import annotations

from pathlib import Path


def load_config(path: Path | None = None):
    raise NotImplementedError


class Service:
    def __init__(self, config) -> None:
        raise NotImplementedError

    def start(self) -> None:
        raise NotImplementedError

    def stop(self) -> None:
        raise NotImplementedError

    def add_source(self, name: str, socket_path: Path, executor: str | None = None) -> None:
        raise NotImplementedError
