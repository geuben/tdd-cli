"""The ledger service's wire: newline-delimited JSON over a unix socket."""

from __future__ import annotations

from pathlib import Path


def call(socket_path: Path, method: str, *args, **kwargs):
    raise NotImplementedError
