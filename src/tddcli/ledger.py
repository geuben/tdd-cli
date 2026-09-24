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

from . import runner

SCHEMA_VERSION = 12


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
    # v2 -> v3 added the advance_claim table; CREATE TABLE IF NOT EXISTS covers it.
    2: "",
    # v3 -> v4 added the baseline_cache table; CREATE TABLE IF NOT EXISTS covers it.
    3: "",
    # v4 -> v5 added source column to baseline; ALTER TABLE covers old ledgers.
    4: "ALTER TABLE baseline ADD COLUMN source TEXT NOT NULL DEFAULT 'probed';",
    # v5 -> v6 added ancillary_files column to plan_contract; ALTER TABLE covers old ledgers.
    5: "ALTER TABLE plan_contract ADD COLUMN ancillary_files TEXT NOT NULL DEFAULT '[]';",
    # v6 -> v7 added evidence_line column to sensitivity_check; ALTER TABLE covers old ledgers.
    6: "ALTER TABLE sensitivity_check ADD COLUMN evidence_line TEXT;",
    # v7 -> v8 added the note table; CREATE TABLE IF NOT EXISTS covers it.
    7: "",
    # v8 -> v9 added regenerate_failed column to artifact_check; ALTER TABLE covers old ledgers.
    8: "ALTER TABLE artifact_check ADD COLUMN regenerate_failed INTEGER NOT NULL DEFAULT 0;",
    # v9 -> v10 added start_sha column to run; ALTER TABLE covers old ledgers.
    9: "ALTER TABLE run ADD COLUMN start_sha TEXT;",
    # v10 -> v11 added tree_hash and skipped columns to gate_result; ALTER TABLE covers old ledgers.
    10: (
        "ALTER TABLE gate_result ADD COLUMN tree_hash TEXT;"
        " ALTER TABLE gate_result ADD COLUMN skipped INTEGER NOT NULL DEFAULT 0;"
    ),
    # v11 -> v12 added others_observed column to invocation; ALTER TABLE covers old ledgers.
    11: "ALTER TABLE invocation ADD COLUMN others_observed INTEGER NOT NULL DEFAULT 1;",
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

CREATE TABLE IF NOT EXISTS advance_claim (
    id INTEGER PRIMARY KEY,
    worktree_path TEXT NOT NULL UNIQUE,
    hostname TEXT NOT NULL,
    pid INTEGER NOT NULL,
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
    ancillary_files TEXT NOT NULL DEFAULT '[]',  -- json
    registered_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS run (
    id INTEGER PRIMARY KEY,
    plan_contract_id INTEGER NOT NULL REFERENCES plan_contract(id),
    executor_model TEXT NOT NULL,
    executor_session TEXT,
    executor_source TEXT NOT NULL,      -- transcript | human | declared | unknown; split mode: operator | claimed
    worktree_path TEXT NOT NULL,
    started_at TEXT NOT NULL,
    ended_at TEXT,
    outcome TEXT,                       -- complete | blocked | abandoned
    allow_dirty INTEGER NOT NULL DEFAULT 0,
    preexisting_dirty TEXT NOT NULL,    -- json: excluded from authorship forever (R9.21)
    config_sha TEXT,                    -- tdd.toml as of run start; drift is an event
    start_sha TEXT                      -- HEAD at run start; late probes and accept-failures run suites here
);

CREATE TABLE IF NOT EXISTS baseline (
    id INTEGER PRIMARY KEY,
    run_id INTEGER NOT NULL REFERENCES run(id),
    project TEXT NOT NULL,
    failing TEXT NOT NULL,              -- json
    captured_at TEXT NOT NULL,
    source TEXT NOT NULL DEFAULT 'probed'
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
    others_observed INTEGER NOT NULL DEFAULT 1,  -- 0: a target-only run saw nothing else
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
    tree_hash TEXT,
    skipped INTEGER NOT NULL DEFAULT 0,
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

CREATE TABLE IF NOT EXISTS note (
    id INTEGER PRIMARY KEY,
    run_id INTEGER NOT NULL REFERENCES run(id),
    cycle_id INTEGER REFERENCES cycle(id),
    phase TEXT,
    text TEXT NOT NULL,
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
    evidence_line TEXT,
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
    regenerate_failed INTEGER NOT NULL DEFAULT 0,
    at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS human_intervention (
    id INTEGER PRIMARY KEY,
    run_id INTEGER NOT NULL REFERENCES run(id),
    note TEXT NOT NULL,
    at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS abandonment (
    id INTEGER PRIMARY KEY,
    run_id INTEGER NOT NULL UNIQUE REFERENCES run(id),
    reason TEXT NOT NULL,
    account TEXT NOT NULL,
    executor_model TEXT NOT NULL,
    executor_source TEXT NOT NULL,
    at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS baseline_cache (
    id INTEGER PRIMARY KEY,
    project TEXT NOT NULL,
    tree_hash TEXT NOT NULL,
    config_sha TEXT NOT NULL,
    failing TEXT NOT NULL,              -- json list
    tests TEXT NOT NULL,                -- json list
    failed_files TEXT NOT NULL,         -- json map path -> error
    created_at TEXT NOT NULL,
    UNIQUE(project, tree_hash, config_sha)
);

CREATE INDEX IF NOT EXISTS idx_cycle_run ON cycle(run_id);
CREATE INDEX IF NOT EXISTS idx_inv_cycle ON invocation(cycle_id);
"""


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ledger_home() -> Path:
    """The directory the ledgers live in.

    `TDD_LEDGER_HOME` is the caller's to set, so a split-mode runner never reads it:
    following it would put the ledger wherever the agent chose. The runner's home
    comes from its own config, else from its own home directory.
    """
    split = _as_runner()
    if split is not None:
        return split.ledger_home or _default_home()
    base = os.environ.get("TDD_LEDGER_HOME")
    return Path(base) if base else _default_home()


def _as_runner() -> runner.RunnerConfig | None:
    """The machine's runner config, when this process is that runner."""
    split = runner.load()
    return split if split is not None and split.role == "runner" else None


def _default_home() -> Path:
    return Path.home() / ".local" / "share" / "tdd-cli"


def _ensured_home() -> Path:
    root = ledger_home()
    root.mkdir(parents=True, exist_ok=True)
    if _as_runner() is not None:
        # Tightened on every open, not only at creation: a directory an operator made
        # by hand would otherwise stay readable by the agent for good.
        root.chmod(0o700)
    return root


def ledger_path(repo_path: Path) -> Path:
    slug = str(repo_path).replace(os.sep, "-").strip("-")
    return _ensured_home() / f"{slug}.sqlite3"


#: `meta` key written by `import_legacy`: everything up to `last_run_id` was recorded
#: while the agent's uid could still open the ledger.
PRE_SPLIT_IMPORT = "pre_split_import"


def import_legacy(source: Path) -> tuple[Path, dict]:
    """Bring a single-user ledger under the runner, marked as pre-split history.

    Copied with SQLite's backup API rather than as a file: a ledger in WAL mode keeps
    its newest rows in a sidecar, and a plain copy of the main file would drop them.
    Returns where it landed and the marker written into it.
    """
    target = _ensured_home() / source.name
    src = sqlite3.connect(f"file:{source}?mode=ro", uri=True)
    dst = sqlite3.connect(target)
    try:
        src.backup(dst)
    finally:
        src.close()
        dst.close()
    imported = Ledger(target.parent, path=target)  # opening it migrates it forward
    # MAX over no rows is one row holding NULL: an empty ledger imports with `None`.
    last = imported.db.execute("SELECT MAX(id) FROM run").fetchone()[0]
    marker = {"source": str(source), "imported_at": now(), "last_run_id": last}
    imported.set_meta(PRE_SPLIT_IMPORT, json.dumps(marker))
    return target, marker


def claim_is_stale(hostname: str, pid: int, started_at: str) -> bool:
    """Staleness rule shared by all claim kinds.

    Same host → liveness via os.kill(pid, 0). Cross-host → age > 60 min
    (a pid is meaningless from another host; reused pids would make a
    liveness check actively wrong, so we fall back to age).
    """
    if hostname == socket.gethostname():
        try:
            os.kill(pid, 0)
            return False
        except ProcessLookupError:
            # Same host, pid no longer running.
            return True
        except PermissionError:
            # Pid exists but owned by someone else — alive.
            return False
    started = datetime.fromisoformat(started_at)
    if started.tzinfo is None:
        started = started.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) - started > timedelta(minutes=60)


class Ledger:
    _claim_is_stale = staticmethod(claim_is_stale)

    def __init__(self, repo_path: Path, *, path: Path | None = None):
        self.repo_path = repo_path
        # `path` is for a ledger that is not found by its repository: an imported one.
        self.path = path or ledger_path(repo_path)
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
            migration = MIGRATIONS[stored]
            if migration:
                try:
                    self.db.executescript(migration)
                except sqlite3.OperationalError as exc:
                    # ALTER TABLE ... ADD COLUMN is idempotent in intent; if the
                    # column already exists (only possible when a ledger's stored
                    # version was manually set below its actual schema version),
                    # ignore the error rather than refusing to open the ledger.
                    if "duplicate column name" not in str(exc).lower():
                        raise
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
            row = self.db.execute("SELECT value FROM meta WHERE key = 'schema_version'").fetchone()
        except sqlite3.OperationalError:  # no meta table: fresh database
            return None
        return int(row[0]) if row else None

    def get_meta(self, key: str) -> str | None:
        row = self.db.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
        return row[0] if row else None

    def set_meta(self, key: str, value: str) -> None:
        self.db.execute(
            "INSERT INTO meta(key, value) VALUES (?, ?)"
            " ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )
        self.db.commit()

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
        self._write(f"UPDATE {table} SET {sets} WHERE id = ?", (*cols.values(), row_id))

    # -- domain queries --------------------------------------------------

    def active_run(self, worktree: str) -> sqlite3.Row | None:
        return self.one(
            "SELECT * FROM run WHERE worktree_path = ? AND ended_at IS NULL"
            " ORDER BY id DESC LIMIT 1",
            (worktree,),
        )

    def open_cycle(self, run_id: int) -> sqlite3.Row | None:
        return self.one(
            "SELECT * FROM cycle WHERE run_id = ? AND closed_at IS NULL ORDER BY ordinal LIMIT 1",
            (run_id,),
        )

    def cycles(self, run_id: int) -> list[sqlite3.Row]:
        return self.all("SELECT * FROM cycle WHERE run_id = ? ORDER BY ordinal", (run_id,))

    def baselines(self, run_id: int) -> dict[str, set[str]]:
        rows = self.all("SELECT project, failing FROM baseline WHERE run_id = ?", (run_id,))
        return {r["project"]: set(json.loads(r["failing"])) for r in rows}

    def previous_baseline(self, worktree: str, project: str, before_run_id: int) -> set[str] | None:
        row = self.one(
            "SELECT b.failing FROM baseline b JOIN run r ON b.run_id = r.id"
            " WHERE r.worktree_path = ? AND b.project = ? AND r.id < ?"
            " ORDER BY r.id DESC LIMIT 1",
            (worktree, project, before_run_id),
        )
        if row is None:
            return None
        return set(json.loads(row["failing"]))

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

    def max_suite_duration_ms(self, project: str) -> int | None:
        """Maximum full-suite invocation duration for `project` across all known runs.

        Returns None when no invocations exist yet (first run), so callers can
        skip the timeout doctor check rather than emitting a false alarm.
        Full-suite runs have `target_test IS NULL`.
        """
        row = self.one(
            "SELECT MAX(duration_ms) AS m FROM invocation"
            " WHERE project = ? AND target_test IS NULL",
            (project,),
        )
        return None if row is None or row["m"] is None else int(row["m"])

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

    # -- baseline cache ----------------------------------------------------

    def cache_baseline(
        self,
        project: str,
        tree_hash: str,
        config_sha: str,
        *,
        failing: list[str],
        tests: list[str],
        failed_files: dict,
    ) -> None:
        self.db.execute(
            """
            INSERT INTO baseline_cache (project, tree_hash, config_sha, failing, tests, failed_files, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(project, tree_hash, config_sha) DO UPDATE SET
                failing = excluded.failing,
                tests = excluded.tests,
                failed_files = excluded.failed_files,
                created_at = excluded.created_at
            """,
            (
                project,
                tree_hash,
                config_sha,
                json.dumps(failing),
                json.dumps(tests),
                json.dumps(failed_files),
                now(),
            ),
        )
        self.db.commit()

    def cached_baseline(
        self,
        project: str,
        tree_hash: str,
        config_sha: str,
        max_age_s: float | None = None,
    ) -> sqlite3.Row | None:
        if max_age_s is not None:
            cutoff = (datetime.now(timezone.utc) - timedelta(seconds=max_age_s)).isoformat()
            return self.one(
                "SELECT * FROM baseline_cache WHERE project=? AND tree_hash=? AND config_sha=? AND created_at >= ?",
                (project, tree_hash, config_sha, cutoff),
            )
        return self.one(
            "SELECT * FROM baseline_cache WHERE project=? AND tree_hash=? AND config_sha=?",
            (project, tree_hash, config_sha),
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

    def claim_advance(self, worktree: str, hostname: str, pid: int) -> int:
        """Insert the advance claim row. The insert is the lock: `worktree_path`
        carries `UNIQUE`, so a second claim on the same worktree raises
        `sqlite3.IntegrityError` rather than racing a read-then-write check."""
        return self.insert(
            "advance_claim",
            worktree_path=worktree,
            hostname=hostname,
            pid=pid,
            started_at=now(),
        )

    def release_advance_claim(self, worktree: str) -> None:
        self.db.execute("DELETE FROM advance_claim WHERE worktree_path = ?", (worktree,))
        self.db.commit()

    def active_advance_claim(self, worktree: str) -> dict | None:
        """Read-only observer — staleness computed but no row deleted."""
        row = self.one("SELECT * FROM advance_claim WHERE worktree_path = ?", (worktree,))
        if row is None:
            return None
        claim = dict(row)
        claim["stale"] = self._claim_is_stale(claim["hostname"], claim["pid"], claim["started_at"])
        return claim

    def active_claim(self, worktree: str) -> dict | None:
        """Read-only, per the store's append-only contract — `cmd_progress` and
        `cmd_status` call this as pure observers. Only `cmd_run_start` acts on the
        computed `stale` flag (release + reclaim); nothing here deletes a row."""
        row = self.one("SELECT * FROM baseline_claim WHERE worktree_path = ?", (worktree,))
        if row is None:
            return None
        claim = dict(row)
        # A pid is meaningless from another host, and reused pids would make a
        # host-crossing liveness check actively wrong. Fall back to age: a false
        # "alive" bricks the worktree, a false "dead" reopens the bug (Decisions).
        claim["stale"] = self._claim_is_stale(claim["hostname"], claim["pid"], claim["started_at"])
        return claim
