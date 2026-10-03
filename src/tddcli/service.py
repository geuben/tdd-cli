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
import json
import os
import signal
import socket
import socketserver
import threading
import time
import tomllib
from dataclasses import dataclass
from pathlib import Path

from . import leases, runner, wire
from . import ledger as ledger_mod

CONFIG_PATH = Path("/etc/tdd-cli/ledger.toml")
CONFIG_ENV = "TDD_LEDGER_SERVICE_CONFIG"

#: Where the service keeps its sources, under its home, so a restart listens on them again.
SOURCES_FILE = "sources.json"

#: The admin socket is the service account's alone; a guest's is shared with the group
#: the operator forwards it through.
ADMIN_MODE = 0o600
GUEST_MODE = 0o660

#: A run with one of these outcomes takes no more writes from a guest.
CLOSED_OUTCOMES = ("complete", "abandoned")

#: The one write a closed run still takes: `tdd note` after the run is documented use,
#: and is how an executor leaves its closing narrative.
CLOSED_RUN_EXEMPT = frozenset({"add_note"})

#: Writes that record who executed a run: the service sets the executor on them.
STAMPED = frozenset({"start_run", "abandon_run"})


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


def serve(config: ServiceConfig) -> Service:
    """Run the service until SIGTERM or SIGINT, then close every socket and return it."""
    svc = Service(config)
    svc.start()
    stopped = threading.Event()
    previous = {
        sig: signal.signal(sig, lambda *_: stopped.set()) for sig in (signal.SIGTERM, signal.SIGINT)
    }
    try:
        # A timed wait, so the main thread returns to the interpreter to run the handler.
        while not stopped.wait(0.5):
            pass
    finally:
        for sig, handler in previous.items():
            signal.signal(sig, handler)
        svc.stop()
    return svc


class _Session:
    """One client connection, and the ledger it opened.

    Each connection opens its own `Ledger`, in its own handler thread: an SQLite
    connection must not cross threads.
    """

    def __init__(self, service: Service, source: str | None, conn: socket.socket | None = None):
        self.service = service
        self.source = source
        self.conn = conn
        self.ledger: ledger_mod.Ledger | None = None

    def answer(self, request: dict) -> dict:
        method = request.get("method")
        args = request.get("args") or []
        kwargs = request.get("kwargs") or {}
        if method == "ping":
            return _ok({"source": self.source, "executor": self.service.executors.get(self.source)})
        if self.source is None:
            # The admin socket: the operator's verbs, never a ledger method.
            return self.service.admin(method, args, kwargs)
        if method == "lease":
            return _ok({"workers": self.service.take_lease(self, self.conn)})
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
        if method in STAMPED:
            kwargs = self._stamp_executor(bound.arguments, set(bound.signature.parameters))
            args = []
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

    def _stamp_executor(self, arguments: dict, params: set[str]) -> dict:
        """The call's arguments, with the executor the operator bound to this source.

        A guest's own identity is guest root's to edit, so when the operator has said
        which model a source runs, that is what the run records. With no binding, the
        guest's word passes through, except that it cannot speak for the operator.
        """
        stamped = dict(arguments)
        binding = self.service.executors.get(self.source)
        if binding is not None:
            stamped.update(executor_model=binding, executor_source="operator")
            if "executor_session" in params:
                stamped["executor_session"] = None
        elif stamped.get("executor_source") == "operator":
            stamped["executor_source"] = "claimed"
        return stamped

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
        self.service.drop_lease(self)
        if self.ledger is not None:
            self.ledger.close()


def _hung_up(conn: socket.socket | None) -> bool:
    """Whether the other end of a connection has closed it. Reads nothing."""
    if conn is None:
        return False
    try:
        return conn.recv(1, socket.MSG_PEEK | socket.MSG_DONTWAIT) == b""
    except BlockingIOError:
        return False
    except OSError:
        return True


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
        session = _Session(listener.service, listener.source, self.request)
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
        # A socket's mode follows the umask unless it is set.
        path.chmod(ADMIN_MODE if source is None else GUEST_MODE)
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
        # Worker leases held by guests, across every source: one budget per host. A
        # lease is its connection, held open for as long as the suite runs.
        self.lock = threading.Lock()
        self.leases: dict[_Session, tuple[socket.socket | None, float]] = {}

    def start(self) -> None:
        self.config.home.mkdir(parents=True, exist_ok=True)
        self.listeners[None] = _Listener(self.config.admin_socket, self, None)
        for name, entry in sorted(self._saved().items()):
            self.add_source(name, Path(entry["socket"]), entry.get("executor"))

    def _saved(self) -> dict:
        path = self.config.home / SOURCES_FILE
        return json.loads(path.read_text()) if path.is_file() else {}

    def _save(self) -> None:
        """Persist every source, replacing the file whole so a crash never halves it."""
        path = self.config.home / SOURCES_FILE
        sources = {
            name: {"socket": str(self.listeners[name].path), "executor": executor}
            for name, executor in sorted(self.executors.items())
        }
        partial = path.with_name(path.name + ".partial")
        partial.write_text(json.dumps(sources, indent=2) + "\n")
        partial.replace(path)

    def stop(self) -> None:
        for listener in list(self.listeners.values()):
            listener.close()
        self.listeners.clear()

    def add_source(self, name: str, socket_path: Path, executor: str | None = None) -> None:
        self.executors[name] = executor
        self.listeners[name] = _Listener(Path(socket_path), self, name)
        self._save()

    def bind(self, name: str, executor: str) -> None:
        self.executors[name] = executor
        self._save()

    def take_lease(self, holder: _Session, conn: socket.socket | None) -> int:
        """Count one more suite running on this host; the worker count it should use.

        A lease whose connection has already hung up is forgotten first, so a guest
        that just finished never counts against the next, however its handler thread
        is scheduled. One older than `leases.STALE_AFTER_S` is not counted: no suite
        runs that long, and a guest whose VM froze must not throttle the host forever.
        """
        now = time.monotonic()
        with self.lock:
            for other, (other_conn, _) in list(self.leases.items()):
                if _hung_up(other_conn):
                    del self.leases[other]
            live = sum(
                1 for _, taken in self.leases.values() if now - taken <= leases.STALE_AFTER_S
            )
            self.leases[holder] = (conn, now)
            return max(1, leases._total_cores() // (live + 1))

    def drop_lease(self, holder: _Session) -> None:
        """Forget a lease: its connection reached EOF. There is no release message."""
        with self.lock:
            self.leases.pop(holder, None)

    def remove_source(self, name: str) -> None:
        """Close the source's socket. Its runs stay in the host's ledgers."""
        self.listeners.pop(name).close()
        del self.executors[name]
        self._save()

    def sources(self) -> list[dict]:
        """Every source, by name: the socket it listens on and the executor bound to it."""
        return [
            {"name": name, "socket": str(self.listeners[name].path), "executor": executor}
            for name, executor in sorted(self.executors.items())
        ]

    def admin(self, method: str, args: list, kwargs: dict) -> dict:
        """An operator's request, from the admin socket."""
        if method == "sources":
            return _ok(self.sources())
        if method == "bind":
            name, executor = args
            if name not in self.executors:
                return _refusal("unknown_source", f"no source named {name!r}")
            self.bind(name, executor)
            return _ok({"name": name, "executor": executor})
        if method == "remove_source":
            (name,) = args
            if name not in self.executors:
                return _refusal("unknown_source", f"no source named {name!r}")
            self.remove_source(name)
            return _ok({"name": name})
        if method == "add_source":
            name, socket_path = args
            self.add_source(name, Path(socket_path), executor=kwargs.get("executor"))
            return _ok({"name": name, "socket": str(socket_path), "executor": self.executors[name]})
        return _refusal("method_not_allowed", f"{method} is not an admin request")
