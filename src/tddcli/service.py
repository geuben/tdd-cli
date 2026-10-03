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
import inspect
import os
import socketserver
import threading
import tomllib
from dataclasses import dataclass
from pathlib import Path

from . import ledger as ledger_mod
from . import runner, wire

CONFIG_PATH = Path("/etc/tdd-cli/ledger.toml")

#: A run with one of these outcomes takes no more writes from a guest.
CLOSED_OUTCOMES = ("complete", "abandoned")

#: The one write a closed run still takes: `tdd note` after the run is documented use,
#: and is how an executor leaves its closing narrative.
CLOSED_RUN_EXEMPT = frozenset({"add_note"})
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


class _Session:
    """One client connection, and the ledger it opened.

    Each connection opens its own `Ledger`, in its own handler thread: an SQLite
    connection must not cross threads.
    """

    def __init__(self, service: Service, source: str | None):
        self.service = service
        self.source = source
        self.ledger: ledger_mod.Ledger | None = None

    def answer(self, request: dict) -> dict:
        method = request.get("method")
        args = request.get("args") or []
        kwargs = request.get("kwargs") or {}
        if method == "ping":
            return _ok({"source": self.source, "executor": self.service.executors.get(self.source)})
        if method == "open":
            repo = args[0] if args else None
            if not _well_formed_repo(repo):
                return _refusal("bad_repo", f"{repo!r} is not an absolute repository path")
            self.ledger = ledger_mod.Ledger(
                Path(repo),
                source=self.source,
                path=self.service.config.home / f"{ledger_mod.slug(repo)}.sqlite3",
            )
            return _ok(None)
        if self.ledger is None:
            return {"ok": False, "error": "no ledger is open on this connection: send `open`"}
        if method not in ledger_mod.GUEST_READS | ledger_mod.GUEST_WRITES:
            return _refusal("method_not_allowed", f"{method} is not answered for a guest")
        fn = getattr(self.ledger, method)
        try:
            bound = inspect.signature(fn).bind(*args, **kwargs)
        except TypeError as exc:
            return {"ok": False, "error": f"{method}: {exc}"}
        refused = self._foreign(bound.arguments)
        if refused is None and method in ledger_mod.GUEST_WRITES - CLOSED_RUN_EXEMPT:
            refused = self._closed(bound.arguments)
        if refused is not None:
            return refused
        try:
            return _ok(fn(*args, **kwargs))
        except Exception as exc:  # the client gets the reason, the service keeps serving
            return {"ok": False, "error": f"{method}: {exc}"}

    def _foreign(self, arguments: dict) -> dict | None:
        """A refusal when the call names a run, cycle or contract of another source.

        One that does not exist is refused the same way, so that a guest cannot learn
        which ids exist in other sources by probing for them.
        """
        owners = (
            ("run_id", "run", self.ledger.run_source),
            ("cycle_id", "cycle", self._cycle_source),
            ("contract_id", "plan contract", self._contract_source),
        )
        for param, noun, source_of in owners:
            value = arguments.get(param)
            if value is not None and source_of(value) != self.source:
                return _refusal("foreign_run", f"{noun} {value} is not this source's")
        return None

    def _closed(self, arguments: dict) -> dict | None:
        """A refusal when the call writes to a run that is complete or abandoned.

        Judged before the method runs. `blocked` is not closed: `resume --unblock` and
        `--accept-failures` write to a blocked run by design.
        """
        run_id = arguments.get("run_id")
        if run_id is None and arguments.get("cycle_id") is not None:
            cycle = self.ledger.cycle(arguments["cycle_id"])
            run_id = cycle["run_id"] if cycle else None
        run = self.ledger.run(run_id) if run_id is not None else None
        if run is not None and run["outcome"] in CLOSED_OUTCOMES:
            return _refusal("run_closed", f"run {run_id} is {run['outcome']}: it takes no writes")
        return None

    def _cycle_source(self, cycle_id: int) -> str | None:
        cycle = self.ledger.cycle(cycle_id)
        return None if cycle is None else self.ledger.run_source(cycle["run_id"])

    def _contract_source(self, contract_id: int) -> str | None:
        contract = self.ledger.contract(contract_id)
        return None if contract is None else contract["source"]

    def close(self) -> None:
        if self.ledger is not None:
            self.ledger.close()


def _well_formed_repo(repo) -> bool:
    """An absolute path with no NUL or newline: it names the host's ledger file."""
    return (
        isinstance(repo, str)
        and Path(repo).is_absolute()
        and "\x00" not in repo
        and "\n" not in repo
    )


def _ok(result) -> dict:
    return {"ok": True, "result": wire.encode(result)}


def _refusal(code: str, error: str) -> dict:
    return {"ok": False, "refusal": code, "error": error}


class _Handler(socketserver.StreamRequestHandler):
    """One connection: requests answered in order until the client closes it."""

    def handle(self) -> None:
        listener: _Listener = self.server  # type: ignore[assignment]
        session = _Session(listener.service, listener.source)
        try:
            while (request := wire.receive(self.rfile)) is not None:
                wire.send(self.wfile, session.answer(request))
        finally:
            session.close()


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
