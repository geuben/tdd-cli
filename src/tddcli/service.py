"""The ledger service: the host's only writer of its ledgers, reached over unix sockets.

When agents run in disposable guests, the runner has to be in the guest, because that
is where the suites run. Its ledger must not be: it would vanish with the guest, and
guest root could rewrite it. So the runner keeps none, and reads and writes the host's
through a socket the host forwards into the guest.

The service listens on one socket per source, plus an admin socket for the operator.
A connection's source is the listener it arrived on, never anything the client sends:
the protocol has no source field at all.
"""

from __future__ import annotations

import contextlib
import os
import socketserver
import threading
import tomllib
from dataclasses import dataclass
from pathlib import Path

from . import runner, wire

CONFIG_PATH = Path("/etc/tdd-cli/ledger.toml")
CONFIG_ENV = "TDD_LEDGER_SERVICE_CONFIG"


class ServiceConfigError(RuntimeError):
    pass


@dataclass
class ServiceConfig:
    admin_socket: Path
    home: Path


def config_path() -> Path:
    override = os.environ.get(CONFIG_ENV)
    return Path(override) if override else CONFIG_PATH


def load_config(path: Path | None = None) -> ServiceConfig:
    """The service's config, held to the same trust rule as the runner's."""
    path = path or config_path()
    try:
        runner._require_trusted(path)
        raw = tomllib.loads(path.read_text())
    except runner.RunnerConfigError as exc:
        raise ServiceConfigError(str(exc)) from exc
    except tomllib.TOMLDecodeError as exc:
        raise ServiceConfigError(f"{path}: {exc}") from exc
    section = raw.get("service") or {}
    if not section.get("admin_socket"):
        raise ServiceConfigError(f"{path}: [service] needs `admin_socket`")
    home = section.get("home")
    return ServiceConfig(
        admin_socket=Path(section["admin_socket"]),
        home=Path(home) if home else Path.home() / ".local" / "share" / "tdd-cli",
    )


class _Handler(socketserver.StreamRequestHandler):
    """One connection: requests answered in order until the client closes it."""

    def handle(self) -> None:
        listener: _Listener = self.server  # type: ignore[assignment]
        while (request := wire.receive(self.rfile)) is not None:
            wire.send(self.wfile, listener.service.answer(listener.source, request))


class _Listener(socketserver.ThreadingUnixStreamServer):
    # Both, or `shutdown()` hangs while a client connection is still open.
    daemon_threads = True
    block_on_close = False

    def __init__(self, path: Path, service: Service, source: str | None):
        self.path = path
        self.service = service
        self.source = source
        # A socket file left by a service that died is not a listener: replace it.
        with contextlib.suppress(FileNotFoundError):
            path.unlink()
        super().__init__(str(path), _Handler)
        self.thread = threading.Thread(target=self.serve_forever, daemon=True)
        self.thread.start()

    def close(self) -> None:
        self.shutdown()
        self.server_close()
        with contextlib.suppress(FileNotFoundError):
            self.path.unlink()


class Service:
    def __init__(self, config: ServiceConfig) -> None:
        self.config = config
        self.listeners: dict[str | None, _Listener] = {}
        self.executors: dict[str, str | None] = {}

    def start(self) -> None:
        self.config.home.mkdir(parents=True, exist_ok=True)
        self.listeners[None] = _Listener(self.config.admin_socket, self, None)

    def stop(self) -> None:
        for listener in list(self.listeners.values()):
            listener.close()
        self.listeners.clear()

    def add_source(self, name: str, socket_path: Path, executor: str | None = None) -> None:
        self.executors[name] = executor
        self.listeners[name] = _Listener(Path(socket_path), self, name)

    def answer(self, source: str | None, request: dict) -> dict:
        if request.get("method") == "ping":
            return {
                "ok": True,
                "result": {"source": source, "executor": self.executors.get(source)},
            }
        return {"ok": False, "refusal": "method_not_allowed", "error": "unknown method"}
