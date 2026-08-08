"""SQLite ledger. One per repository (R13.3), outside every worktree, never in the repo.

Invocations, transitions and events are append-only. Nothing here accepts a phase
from a caller — phases are written only by the state machine.
"""

from __future__ import annotations

import json
import os
import socket
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

SCHEMA_VERSION = 2


class LedgerVersionError(RuntimeError):
    """The ledger on disk was written by a newer tdd-cli than this one."""


#: Forward migrations, keyed by the version they upgrade *from*. Applied in order
#: after the idempotent SCHEMA script, which already creates missing tables and
#: indexes; a migration entry therefore only needs statements SCHEMA cannot express,
#: such as ALTER TABLE on an existing table. Every released schema version must have
#: an entry here (empty string when SCHEMA alone suffices), so an old ledger is
#: upgraded rather than silently run against a shape the code no longer expects.
MIGRATIONS: dict[int, str] = {
    # v1 -> v2 added the baseline_claim table; CREATE TABLE IF NOT EXISTS covers it.
    1: "",
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);

CREATE TABLE IF NOT EXISTS baseline_claim (
    id INTEGER PRIMARY KEY,
    worktree_path TEXT NOT NULL UNIQUE,
    hostname TEXT NOT NULL,
    pid INTEGER NOT NULL,
    projects_total INTEGER NOT NULL DEFAULT 0,
    projects_done INTEGER NOT NULL DEFAULT 0,
    current_project TEXT,
    started_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS plan_contract (
    id INTEGER PRIMARY KEY,
    plan_path TEXT NOT NULL,
    git_blob_sha TEXT,
    git_commit TEXT,
    status TEXT NOT NULL,               -- declared | undeclared
    declared_cycles TEXT NOT NULL,      -- json
    annotation_keys TEXT NOT NULL,      -- json
    registered_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS run (
    id INTEGER PRIMARY KEY,
    plan_contract_id INTEGER NOT NULL REFERENCES plan_contract(id),
    executor_model TEXT NOT NULL,
    executor_session TEXT,
    executor_source TEXT NOT NULL,      -- transcript | human | unknown
    worktree_path TEXT NOT NULL,
    started_at TEXT NOT NULL,
    ended_at TEXT,
    outcome TEXT,                       -- complete | blocked | abandoned
    allow_dirty INTEGER NOT NULL DEFAULT 0,
    preexisting_dirty TEXT NOT NULL,    -- json: excluded from authorship forever (R9.21)
    config_sha TEXT                     -- tdd.toml as of run start; drift is an event
);

CREATE TABLE IF NOT EXISTS baseline (
    id INTEGER PRIMARY KEY,
    run_id INTEGER NOT NULL REFERENCES run(id),
    project TEXT NOT NULL,
    failing TEXT NOT NULL,              -- json
    captured_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS collection_snapshot (
    id INTEGER PRIMARY KEY,
    run_id INTEGER NOT NULL REFERENCES run(id),
    project TEXT NOT NULL,
    tests TEXT NOT NULL,                -- json list
    failed_files TEXT NOT NULL,         -- json map path -> error
    captured_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS cycle (
    id INTEGER PRIMARY KEY,
    run_id INTEGER NOT NULL REFERENCES run(id),
    ordinal INTEGER NOT NULL,
    kind TEXT NOT NULL,                 -- standard | pin | contract
    projects TEXT NOT NULL,             -- json list
    declared_tests TEXT NOT NULL,       -- json list
    target_tests TEXT NOT NULL,         -- json list (adopted; may differ, R8.9)
    phase TEXT NOT NULL,
    head_at_open TEXT NOT NULL,
    title TEXT,
    opened_at TEXT NOT NULL,
    closed_at TEXT,
    skip_reason TEXT
);

CREATE TABLE IF NOT EXISTS invocation (
    id INTEGER PRIMARY KEY,
    run_id INTEGER NOT NULL REFERENCES run(id),
    cycle_id INTEGER REFERENCES cycle(id),
    phase_at TEXT NOT NULL,
    project TEXT NOT NULL,
    adapter TEXT NOT NULL,
    target_test TEXT,
    target_outcome TEXT,
    target_failure TEXT,
    total_passed INTEGER NOT NULL DEFAULT 0,
    total_failed INTEGER NOT NULL DEFAULT 0,
    other_failures TEXT NOT NULL,       -- json, baseline-subtracted
    duration_ms INTEGER NOT NULL DEFAULT 0,
    retried INTEGER NOT NULL DEFAULT 0,
    tree_hash TEXT,
    started_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS gate_result (
    id INTEGER PRIMARY KEY,
    run_id INTEGER NOT NULL REFERENCES run(id),
    cycle_id INTEGER REFERENCES cycle(id),
    project TEXT NOT NULL,
    kind TEXT NOT NULL,                 -- lint | typecheck
    ok INTEGER NOT NULL,
    output TEXT,
    at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS transition (
    id INTEGER PRIMARY KEY,
    cycle_id INTEGER NOT NULL REFERENCES cycle(id),
    from_phase TEXT NOT NULL,
    to_phase TEXT NOT NULL,
    invocation_id INTEGER REFERENCES invocation(id),
    at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS annotation (
    id INTEGER PRIMARY KEY,
    run_id INTEGER NOT NULL REFERENCES run(id),
    cycle_id INTEGER REFERENCES cycle(id),
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS integrity_event (
    id INTEGER PRIMARY KEY,
    run_id INTEGER NOT NULL REFERENCES run(id),
    cycle_id INTEGER REFERENCES cycle(id),
    kind TEXT NOT NULL,
    detail TEXT,
    at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS blocker (
    id INTEGER PRIMARY KEY,
    run_id INTEGER NOT NULL REFERENCES run(id),
    cycle_id INTEGER REFERENCES cycle(id),
    kind TEXT NOT NULL,
    detail TEXT,
    at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sensitivity_check (
    id INTEGER PRIMARY KEY,
    cycle_id INTEGER NOT NULL REFERENCES cycle(id),
    reference_diff TEXT NOT NULL,
    reference_untracked TEXT NOT NULL,
    mutation_diff TEXT,
    observed_failure TEXT,
    restored_ok INTEGER,
    opened_at TEXT NOT NULL,
    closed_at TEXT
);

CREATE TABLE IF NOT EXISTS commit_record (
    id INTEGER PRIMARY KEY,
    run_id INTEGER NOT NULL REFERENCES run(id),
    cycle_id INTEGER REFERENCES cycle(id),
    phase TEXT NOT NULL,
    sha TEXT NOT NULL,
    message TEXT NOT NULL,
    files TEXT NOT NULL,
    at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS artifact_check (
    id INTEGER PRIMARY KEY,
    run_id INTEGER NOT NULL REFERENCES run(id),
    cycle_id INTEGER REFERENCES cycle(id),
    artifact TEXT NOT NULL,
    stale INTEGER NOT NULL,
    regenerated INTEGER NOT NULL DEFAULT 0,
    at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS human_intervention (
    id INTEGER PRIMARY KEY,
    run_id INTEGER NOT NULL REFERENCES run(id),
    note TEXT NOT NULL,
    at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_cycle_run ON cycle(run_id);
CREATE INDEX IF NOT EXISTS idx_inv_cycle ON invocation(cycle_id);
"""


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ledger_path(repo_path: Path) -> Path:
    base = os.environ.get("TDD_LEDGER_HOME")
    root = Path(base) if base else Path.home() / ".local" / "share" / "tdd-cli"
    slug = str(repo_path).replace(os.sep, "-").strip("-")
    root.mkdir(parents=True, exist_ok=True)
    return root / f"{slug}.sqlite3"


class Ledger:
    def __init__(self, repo_path: Path):
        self.repo_path = repo_path
        self.path = ledger_path(repo_path)
        # A generous busy timeout: two `run start` calls against one worktree open
        # separate connections and both write (claim, then run/baseline rows).
        # SQLite's default 5s timeout can be exceeded while one holds the write lock
        # through a real baseline probe (subprocess pytest/vitest calls), surfacing
        # as `sqlite3.OperationalError: database is locked` instead of the intended
        # `IntegrityError` rejection path.
        self.db = sqlite3.connect(self.path, timeout=30.0)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA foreign_keys=ON")
        stored = self._stored_version()
        if stored is not None and stored > SCHEMA_VERSION:
            self.db.close()
            raise LedgerVersionError(
                f"ledger {self.path} has schema version {stored}, but this tdd-cli"
                f" understands up to {SCHEMA_VERSION} — it was written by a newer"
                " tdd-cli. Upgrade tdd-cli; do not downgrade the ledger."
            )
        self.db.executescript(SCHEMA)
        while stored is not None and stored < SCHEMA_VERSION:
            self.db.executescript(MIGRATIONS[stored])
            stored += 1
        self.db.execute(
            "INSERT INTO meta(key, value) VALUES ('schema_version', ?)"
            " ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (str(SCHEMA_VERSION),),
        )
        self.db.commit()

    def _stored_version(self) -> int | None:
        """The schema version already on disk, or None for a fresh database."""
        try:
            row = self.db.execute(
                "SELECT value FROM meta WHERE key = 'schema_version'"
            ).fetchone()
        except sqlite3.OperationalError:  # no meta table: fresh database
            return None
        return int(row[0]) if row else None

    # -- generic helpers -------------------------------------------------

    def _write(self, sql: str, params: tuple) -> sqlite3.Cursor:
        """Every write goes through here, so none can strand the write lock.

        Python's sqlite3 module does not roll back a failed statement, so a
        constraint violation — the `baseline_claim.worktree_path` UNIQUE violation
        that *is* the claim's lock, among others — leaves this connection's implicit
        transaction open. An unrolled-back writer holds SQLite's write lock until the
        connection is garbage collected, starving concurrent writers well past any
        reasonable busy timeout. The claim mechanism is designed around failed writes
        being cheap and side-effect-free, so this must hold on every path, not just
        the one that happened to be exercised under load.
        """
        try:
            cur = self.db.execute(sql, params)
            self.db.commit()
            return cur
        except Exception:
            self.db.rollback()
            raise

    def insert(self, table: str, **cols) -> int:
        keys = ", ".join(cols)
        marks = ", ".join("?" for _ in cols)
        return self._write(
            f"INSERT INTO {table} ({keys}) VALUES ({marks})", tuple(cols.values())
        ).lastrowid

    def one(self, sql: str, params: tuple = ()) -> sqlite3.Row | None:
        return self.db.execute(sql, params).fetchone()

    def all(self, sql: str, params: tuple = ()) -> list[sqlite3.Row]:
        return self.db.execute(sql, params).fetchall()

    def update(self, table: str, row_id: int, **cols) -> None:
        sets = ", ".join(f"{k} = ?" for k in cols)
        self._write(
            f"UPDATE {table} SET {sets} WHERE id = ?", (*cols.values(), row_id)
        )

    # -- domain queries --------------------------------------------------

    def active_run(self, worktree: str) -> sqlite3.Row | None:
        return self.one(
            "SELECT * FROM run WHERE worktree_path = ? AND ended_at IS NULL"
            " ORDER BY id DESC LIMIT 1",
            (worktree,),
        )

    def open_cycle(self, run_id: int) -> sqlite3.Row | None:
        return self.one(
            "SELECT * FROM cycle WHERE run_id = ? AND closed_at IS NULL"
            " ORDER BY ordinal LIMIT 1",
            (run_id,),
        )

    def cycles(self, run_id: int) -> list[sqlite3.Row]:
        return self.all("SELECT * FROM cycle WHERE run_id = ? ORDER BY ordinal", (run_id,))

    def baselines(self, run_id: int) -> dict[str, set[str]]:
        rows = self.all("SELECT project, failing FROM baseline WHERE run_id = ?", (run_id,))
        return {r["project"]: set(json.loads(r["failing"])) for r in rows}

    def collection(self, run_id: int) -> dict[str, set[str]]:
        rows = self.all(
            "SELECT project, tests FROM collection_snapshot WHERE run_id = ?", (run_id,)
        )
        return {r["project"]: set(json.loads(r["tests"])) for r in rows}

    def invocations(self, cycle_id: int, phase: str | None = None) -> list[sqlite3.Row]:
        if phase:
            return self.all(
                "SELECT * FROM invocation WHERE cycle_id = ? AND phase_at = ? ORDER BY id",
                (cycle_id, phase),
            )
        return self.all("SELECT * FROM invocation WHERE cycle_id = ? ORDER BY id", (cycle_id,))

    def open_sensitivity(self, cycle_id: int) -> sqlite3.Row | None:
        return self.one(
            "SELECT * FROM sensitivity_check WHERE cycle_id = ? AND closed_at IS NULL"
            " ORDER BY id DESC LIMIT 1",
            (cycle_id,),
        )

    def completed_sensitivity(self, cycle_id: int) -> sqlite3.Row | None:
        return self.one(
            "SELECT * FROM sensitivity_check WHERE cycle_id = ? AND restored_ok = 1"
            " ORDER BY id DESC LIMIT 1",
            (cycle_id,),
        )

    def event(self, run_id: int, cycle_id: int | None, kind: str, detail: str = "") -> None:
        self.insert(
            "integrity_event",
            run_id=run_id,
            cycle_id=cycle_id,
            kind=kind,
            detail=detail,
            at=now(),
        )

    # -- baseline claim ----------------------------------------------------

    def claim(self, worktree: str, hostname: str, pid: int, projects_total: int) -> int:
        """Insert the claim row. The insert is the lock: `worktree_path`
        carries `UNIQUE`, so a second claim on the same worktree raises
        `sqlite3.IntegrityError` rather than racing a read-then-write check."""
        return self.insert(
            "baseline_claim",
            worktree_path=worktree,
            hostname=hostname,
            pid=pid,
            projects_total=projects_total,
            projects_done=0,
            current_project=None,
            started_at=now(),
        )

    def release_claim(self, worktree: str) -> None:
        self.db.execute("DELETE FROM baseline_claim WHERE worktree_path = ?", (worktree,))
        self.db.commit()

    def update_claim(self, worktree: str, projects_done: int, current_project: str) -> None:
        """Counters and progress only — no per-project timing history, that lives in
        the stderr heartbeat lines."""
        self.db.execute(
            "UPDATE baseline_claim SET projects_done = ?, current_project = ?"
            " WHERE worktree_path = ?",
            (projects_done, current_project, worktree),
        )
        self.db.commit()

    def active_claim(self, worktree: str) -> dict | None:
        """Read-only, per the store's append-only contract — `cmd_progress` and
        `cmd_status` call this as pure observers. Only `cmd_run_start` acts on the
        computed `stale` flag (release + reclaim); nothing here deletes a row."""
        row = self.one("SELECT * FROM baseline_claim WHERE worktree_path = ?", (worktree,))
        if row is None:
            return None
        claim = dict(row)
        if claim["hostname"] == socket.gethostname():
            try:
                os.kill(claim["pid"], 0)
                stale = False
            except ProcessLookupError:
                # Same host, pid no longer running (e.g. a `SIGKILL`ed `run start`).
                stale = True
            except PermissionError:
                # Pid exists but is owned by someone else — alive.
                stale = False
        else:
            # A pid is meaningless from another host, and reused pids would make a
            # host-crossing liveness check actively wrong. Fall back to age: a false
            # "alive" bricks the worktree, a false "dead" reopens the bug (Decisions).
            started = datetime.fromisoformat(claim["started_at"])
            if started.tzinfo is None:
                started = started.replace(tzinfo=timezone.utc)
            stale = datetime.now(timezone.utc) - started > timedelta(minutes=60)
        claim["stale"] = stale
        return claim
