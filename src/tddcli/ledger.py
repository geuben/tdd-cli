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

SCHEMA_VERSION = 13


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
    # v12 -> v13 records each row's source. `run` and `plan_contract` gain the column;
    # the claims and the baseline cache are rebuilt, because their UNIQUE constraints
    # gain it too and SQLite cannot alter a constraint in place.
    12: """
ALTER TABLE run ADD COLUMN source TEXT NOT NULL DEFAULT 'local';
ALTER TABLE plan_contract ADD COLUMN source TEXT NOT NULL DEFAULT 'local';

CREATE TABLE baseline_claim_v13 (
    id INTEGER PRIMARY KEY,
    source TEXT NOT NULL DEFAULT 'local',
    worktree_path TEXT NOT NULL,
    hostname TEXT NOT NULL,
    pid INTEGER NOT NULL,
    projects_total INTEGER NOT NULL DEFAULT 0,
    projects_done INTEGER NOT NULL DEFAULT 0,
    current_project TEXT,
    started_at TEXT NOT NULL,
    UNIQUE(source, worktree_path)
);
INSERT INTO baseline_claim_v13 (id, worktree_path, hostname, pid, projects_total,
    projects_done, current_project, started_at)
    SELECT id, worktree_path, hostname, pid, projects_total, projects_done,
    current_project, started_at FROM baseline_claim;
DROP TABLE baseline_claim;
ALTER TABLE baseline_claim_v13 RENAME TO baseline_claim;

CREATE TABLE advance_claim_v13 (
    id INTEGER PRIMARY KEY,
    source TEXT NOT NULL DEFAULT 'local',
    worktree_path TEXT NOT NULL,
    hostname TEXT NOT NULL,
    pid INTEGER NOT NULL,
    started_at TEXT NOT NULL,
    UNIQUE(source, worktree_path)
);
INSERT INTO advance_claim_v13 (id, worktree_path, hostname, pid, started_at)
    SELECT id, worktree_path, hostname, pid, started_at FROM advance_claim;
DROP TABLE advance_claim;
ALTER TABLE advance_claim_v13 RENAME TO advance_claim;

CREATE TABLE baseline_cache_v13 (
    id INTEGER PRIMARY KEY,
    source TEXT NOT NULL DEFAULT 'local',
    project TEXT NOT NULL,
    tree_hash TEXT NOT NULL,
    config_sha TEXT NOT NULL,
    failing TEXT NOT NULL,
    tests TEXT NOT NULL,
    failed_files TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(source, project, tree_hash, config_sha)
);
INSERT INTO baseline_cache_v13 (id, project, tree_hash, config_sha, failing, tests,
    failed_files, created_at)
    SELECT id, project, tree_hash, config_sha, failing, tests, failed_files, created_at
    FROM baseline_cache;
DROP TABLE baseline_cache;
ALTER TABLE baseline_cache_v13 RENAME TO baseline_cache;
""",
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);

-- No index may name a `source` column: SCHEMA runs before the migrations, so on a
-- pre-v13 ledger that column does not exist yet when this script does.

CREATE TABLE IF NOT EXISTS baseline_claim (
    id INTEGER PRIMARY KEY,
    source TEXT NOT NULL DEFAULT 'local',
    worktree_path TEXT NOT NULL,
    hostname TEXT NOT NULL,
    pid INTEGER NOT NULL,
    projects_total INTEGER NOT NULL DEFAULT 0,
    projects_done INTEGER NOT NULL DEFAULT 0,
    current_project TEXT,
    started_at TEXT NOT NULL,
    UNIQUE(source, worktree_path)
);

CREATE TABLE IF NOT EXISTS advance_claim (
    id INTEGER PRIMARY KEY,
    source TEXT NOT NULL DEFAULT 'local',
    worktree_path TEXT NOT NULL,
    hostname TEXT NOT NULL,
    pid INTEGER NOT NULL,
    started_at TEXT NOT NULL,
    UNIQUE(source, worktree_path)
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
    registered_at TEXT NOT NULL,
    source TEXT NOT NULL DEFAULT 'local'
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
    start_sha TEXT,                     -- HEAD at run start; late probes and accept-failures run suites here
    source TEXT NOT NULL DEFAULT 'local' -- where the run came in from: `local`, or a ledger service's source
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
    source TEXT NOT NULL DEFAULT 'local',
    project TEXT NOT NULL,
    tree_hash TEXT NOT NULL,
    config_sha TEXT NOT NULL,
    failing TEXT NOT NULL,              -- json list
    tests TEXT NOT NULL,                -- json list
    failed_files TEXT NOT NULL,         -- json map path -> error
    created_at TEXT NOT NULL,
    UNIQUE(source, project, tree_hash, config_sha)
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


def slug(repo_path: Path | str) -> str:
    """A repository's ledger file name, without its suffix."""
    return str(repo_path).replace(os.sep, "-").strip("-")


def ledger_path(repo_path: Path) -> Path:
    return _ensured_home() / f"{slug(repo_path)}.sqlite3"


#: `meta` key written by `import_legacy`: everything up to `last_run_id` was recorded
#: while the agent's uid could still open the ledger.
PRE_SPLIT_IMPORT = "pre_split_import"

#: The source of every run recorded on this machine's own ledger: single-user mode and
#: single-machine split mode alike. A ledger service names one source per guest socket.
LOCAL_SOURCE = "local"

# -- the guest registry ----------------------------------------------------------
#
# A ledger service exposes `Ledger` methods to guests by name, so every public method
# is classified here, exactly once. A guest method that touches one run's rows names
# that run by a parameter called exactly `run_id`, `cycle_id` or `contract_id`, which
# the service checks belongs to the guest's source; one that finds rows by worktree,
# project or cache key is SOURCE_ROOTED, and filters by the ledger's own source.

#: Reads a guest may make.
GUEST_READS = frozenset(
    {
        "abandonment",
        "active_advance_claim",
        "active_claim",
        "active_run",
        "active_runs",
        "advance_claim_row",
        "advance_claims",
        "annotation_keys_of",
        "annotations",
        "baseline_claims",
        "baseline_rows",
        "baselines",
        "blocker_counts",
        "blockers",
        "cached_baseline",
        "claim_row",
        "collection",
        "commits",
        "completed_sensitivity",
        "contract",
        "contract_by_blob",
        "cycle",
        "cycle_event_kinds",
        "cycle_events",
        "cycle_has_event",
        "cycle_has_note",
        "cycle_notes",
        "cycle_times",
        "cycles",
        "event_counts",
        "event_details",
        "get_meta",
        "interventions",
        "invocations",
        "last_cycle_event_detail",
        "last_gate",
        "last_invocation_at",
        "latest_blocked_run",
        "latest_close_sweeps",
        "latest_contract",
        "latest_run",
        "max_suite_duration_ms",
        "open_cycle",
        "open_sensitivity",
        "previous_baseline",
        "regenerated_artifacts",
        "run",
        "run_events",
        "run_has_event",
        "run_notes",
        "run_target_tests",
        "runs_in",
        "suite_time_by_phase",
        "unclosed_cycle",
    }
)

#: Writes a guest may make.
GUEST_WRITES = frozenset(
    {
        "abandon_run",
        "add_annotation",
        "add_blocker",
        "add_cycle",
        "add_note",
        "amend_baseline",
        "cache_baseline",
        "claim",
        "claim_advance",
        "close_sensitivity_check",
        "end_run",
        "event",
        "mark_artifact_check",
        "mark_cycle_closed",
        "move_cycle",
        "open_sensitivity_check",
        "record_artifact_check",
        "record_baseline",
        "record_collection",
        "record_commit",
        "record_gate",
        "record_invocation",
        "record_sensitivity_mutation",
        "register_contract",
        "release_advance_claim",
        "release_claim",
        "reopen_run",
        "set_targets",
        "skip_cycle",
        "start_run",
        "update_claim",
    }
)

#: Never answered for a guest. The generic helpers would let it name any row of any
#: source.
HOST_ONLY = frozenset(
    {
        "all",
        "close",
        "insert",
        "one",
        "run_source",
        "set_meta",
        "update",
    }
)

#: Guest methods with no run, cycle or contract id: each filters by the ledger's source.
SOURCE_ROOTED = frozenset(
    {
        "active_advance_claim",
        "active_claim",
        "active_run",
        "active_runs",
        "advance_claim_row",
        "advance_claims",
        "baseline_claims",
        "cache_baseline",
        "cached_baseline",
        "claim",
        "claim_advance",
        "claim_row",
        "contract_by_blob",
        "get_meta",
        "latest_blocked_run",
        "latest_contract",
        "latest_run",
        "max_suite_duration_ms",
        "previous_baseline",
        "register_contract",
        "release_advance_claim",
        "release_claim",
        "runs_in",
        "update_claim",
    }
)


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

    def __init__(
        self, repo_path: Path, *, path: Path | None = None, source: str | None = LOCAL_SOURCE
    ):
        self.repo_path = repo_path
        # The source this ledger reads and writes as. None is the host's unscoped view
        # of every source, built only by the ledger service and by tests.
        self.source = source
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

    def close(self) -> None:
        self.db.close()

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

    # -- sources -----------------------------------------------------------

    def _scoped(self, column: str = "source") -> tuple[str, tuple]:
        """An `AND <column> = ?` clause and its parameter, empty for the unscoped view."""
        if self.source is None:
            return "", ()
        return f" AND {column} = ?", (self.source,)

    def _stamp(self) -> dict:
        """The source column for a new row; the unscoped view leaves the default."""
        return {} if self.source is None else {"source": self.source}

    # -- domain queries --------------------------------------------------

    def active_run(self, worktree: str) -> sqlite3.Row | None:
        scope, extra = self._scoped()
        return self.one(
            f"SELECT * FROM run WHERE worktree_path = ? AND ended_at IS NULL{scope}"
            " ORDER BY id DESC LIMIT 1",
            (worktree, *extra),
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
        scope, extra = self._scoped("r.source")
        row = self.one(
            "SELECT b.failing FROM baseline b JOIN run r ON b.run_id = r.id"
            f" WHERE r.worktree_path = ? AND b.project = ? AND r.id < ?{scope}"
            " ORDER BY r.id DESC LIMIT 1",
            (worktree, project, before_run_id, *extra),
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
        # Excludes other sources' runs rather than joining on this one's, so that an
        # invocation is never dropped for want of a run row it can be joined to.
        scope, extra = ("", ())
        if self.source is not None:
            scope = " AND run_id NOT IN (SELECT id FROM run WHERE source != ?)"
            extra = (self.source,)
        row = self.one(
            "SELECT MAX(duration_ms) AS m FROM invocation"
            f" WHERE project = ? AND target_test IS NULL{scope}",
            (project, *extra),
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
        # Per source: a guest that could write a cache row another guest reads could
        # hand that guest a forged baseline and hide a regression.
        self.db.execute(
            """
            INSERT INTO baseline_cache (source, project, tree_hash, config_sha, failing, tests, failed_files, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(source, project, tree_hash, config_sha) DO UPDATE SET
                failing = excluded.failing,
                tests = excluded.tests,
                failed_files = excluded.failed_files,
                created_at = excluded.created_at
            """,
            (
                LOCAL_SOURCE if self.source is None else self.source,
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
        scope, extra = self._scoped()
        if max_age_s is not None:
            cutoff = (datetime.now(timezone.utc) - timedelta(seconds=max_age_s)).isoformat()
            return self.one(
                "SELECT * FROM baseline_cache WHERE project=? AND tree_hash=? AND config_sha=?"
                f" AND created_at >= ?{scope}",
                (project, tree_hash, config_sha, cutoff, *extra),
            )
        return self.one(
            f"SELECT * FROM baseline_cache WHERE project=? AND tree_hash=? AND config_sha=?{scope}",
            (project, tree_hash, config_sha, *extra),
        )

    # -- baseline claim ----------------------------------------------------

    def claim(self, worktree: str, hostname: str, pid: int, projects_total: int) -> int | None:
        """Insert the claim row, or return None when the worktree is already claimed.

        The insert is the lock: `(source, worktree_path)` carries `UNIQUE`, so a second
        claim fails at the insert rather than racing a read-then-write check. Two
        guests commonly check out at the same path, so the lock is per source. The conflict
        is answered as None, not as `sqlite3.IntegrityError`, because no sqlite
        exception can cross a socket to a remote caller."""
        try:
            return self.insert(
                "baseline_claim",
                worktree_path=worktree,
                hostname=hostname,
                pid=pid,
                projects_total=projects_total,
                projects_done=0,
                current_project=None,
                started_at=now(),
                **self._stamp(),
            )
        except sqlite3.IntegrityError:
            return None

    def release_claim(self, worktree: str) -> None:
        scope, extra = self._scoped()
        self._write(
            f"DELETE FROM baseline_claim WHERE worktree_path = ?{scope}", (worktree, *extra)
        )

    def update_claim(self, worktree: str, projects_done: int, current_project: str) -> None:
        """Counters and progress only — no per-project timing history, that lives in
        the stderr heartbeat lines."""
        scope, extra = self._scoped()
        self._write(
            "UPDATE baseline_claim SET projects_done = ?, current_project = ?"
            f" WHERE worktree_path = ?{scope}",
            (projects_done, current_project, worktree, *extra),
        )

    def claim_advance(self, worktree: str, hostname: str, pid: int) -> int | None:
        """Insert the advance claim row, or return None when the worktree is already
        claimed. The insert is the lock, as in `claim`."""
        try:
            return self.insert(
                "advance_claim",
                worktree_path=worktree,
                hostname=hostname,
                pid=pid,
                started_at=now(),
                **self._stamp(),
            )
        except sqlite3.IntegrityError:
            return None

    def release_advance_claim(self, worktree: str) -> None:
        scope, extra = self._scoped()
        self._write(f"DELETE FROM advance_claim WHERE worktree_path = ?{scope}", (worktree, *extra))

    def active_advance_claim(self, worktree: str) -> dict | None:
        """Read-only observer — staleness computed but no row deleted."""
        row = self.advance_claim_row(worktree)
        if row is None:
            return None
        claim = dict(row)
        claim["stale"] = self._claim_is_stale(claim["hostname"], claim["pid"], claim["started_at"])
        return claim

    def active_claim(self, worktree: str) -> dict | None:
        """Read-only, per the store's append-only contract — `cmd_progress` and
        `cmd_status` call this as pure observers. Only `cmd_run_start` acts on the
        computed `stale` flag (release + reclaim); nothing here deletes a row."""
        row = self.claim_row(worktree)
        if row is None:
            return None
        claim = dict(row)
        # A pid is meaningless from another host, and reused pids would make a
        # host-crossing liveness check actively wrong. Fall back to age: a false
        # "alive" bricks the worktree, a false "dead" reopens the bug (Decisions).
        claim["stale"] = self._claim_is_stale(claim["hostname"], claim["pid"], claim["started_at"])
        return claim

    def claim_row(self, worktree: str) -> sqlite3.Row | None:
        """The raw baseline claim, with no judgement of whether its owner lives."""
        scope, extra = self._scoped()
        return self.one(
            f"SELECT * FROM baseline_claim WHERE worktree_path = ?{scope}", (worktree, *extra)
        )

    def advance_claim_row(self, worktree: str) -> sqlite3.Row | None:
        """The raw advance claim, with no judgement of whether its owner lives."""
        scope, extra = self._scoped()
        return self.one(
            f"SELECT * FROM advance_claim WHERE worktree_path = ?{scope}", (worktree, *extra)
        )

    # -- plan contracts ----------------------------------------------------

    def contract_by_blob(self, plan_path: str, blob_sha: str | None) -> sqlite3.Row | None:
        scope, extra = self._scoped()
        return self.one(
            f"SELECT * FROM plan_contract WHERE plan_path = ? AND git_blob_sha IS ?{scope}",
            (plan_path, blob_sha, *extra),
        )

    def latest_contract(self, plan_path: str) -> sqlite3.Row | None:
        scope, extra = self._scoped()
        return self.one(
            f"SELECT * FROM plan_contract WHERE plan_path = ?{scope} ORDER BY id DESC LIMIT 1",
            (plan_path, *extra),
        )

    def register_contract(
        self,
        *,
        plan_path: str,
        blob_sha: str | None,
        commit_sha: str | None,
        status: str,
        declared_cycles: str,
        annotation_keys: str,
        ancillary_files: str,
    ) -> int:
        return self.insert(
            "plan_contract",
            plan_path=plan_path,
            git_blob_sha=blob_sha,
            git_commit=commit_sha,
            status=status,
            declared_cycles=declared_cycles,
            annotation_keys=annotation_keys,
            ancillary_files=ancillary_files,
            registered_at=now(),
            **self._stamp(),
        )

    # -- runs ----------------------------------------------------------------

    def run_source(self, run_id: int) -> str | None:
        """The source a run belongs to, whatever this ledger's own; None if no such run."""
        row = self.one("SELECT source FROM run WHERE id = ?", (run_id,))
        return row["source"] if row else None

    def run(self, run_id: int) -> sqlite3.Row | None:
        return self.one("SELECT * FROM run WHERE id = ?", (run_id,))

    def latest_run(self, worktree: str) -> sqlite3.Row | None:
        scope, extra = self._scoped()
        return self.one(
            f"SELECT * FROM run WHERE worktree_path = ?{scope} ORDER BY id DESC LIMIT 1",
            (worktree, *extra),
        )

    def latest_blocked_run(self, worktree: str) -> sqlite3.Row | None:
        scope, extra = self._scoped()
        return self.one(
            f"SELECT * FROM run WHERE worktree_path = ? AND outcome = 'blocked'{scope}"
            " ORDER BY id DESC LIMIT 1",
            (worktree, *extra),
        )

    def start_run(
        self,
        contract_id: int,
        *,
        executor_model: str,
        executor_session: str | None,
        executor_source: str,
        worktree: str,
        allow_dirty: bool,
        preexisting_dirty: list[str],
        config_sha: str | None,
        start_sha: str | None,
    ) -> int:
        return self.insert(
            "run",
            plan_contract_id=contract_id,
            executor_model=executor_model,
            executor_session=executor_session,
            executor_source=executor_source,
            worktree_path=worktree,
            started_at=now(),
            allow_dirty=int(bool(allow_dirty)),
            preexisting_dirty=json.dumps(preexisting_dirty),
            config_sha=config_sha,
            start_sha=start_sha,
            **self._stamp(),
        )

    def end_run(self, run_id: int, outcome: str) -> None:
        self.update("run", run_id, ended_at=now(), outcome=outcome)

    def reopen_run(self, run_id: int, note: str) -> None:
        """`resume --unblock`: the run is live again, and a human said why."""
        self.update("run", run_id, ended_at=None, outcome=None)
        self.insert("human_intervention", run_id=run_id, note=note, at=now())

    def abandon_run(
        self,
        run_id: int,
        *,
        reason: str,
        account: str,
        executor_model: str,
        executor_source: str,
        at: str,
    ) -> None:
        """End the run as abandoned, record who did it, and free its worktree's claims."""
        run = self.run(run_id)
        self.update("run", run_id, ended_at=at, outcome="abandoned")
        self.insert(
            "abandonment",
            run_id=run_id,
            reason=reason,
            account=account,
            executor_model=executor_model,
            executor_source=executor_source,
            at=at,
        )
        self.insert("human_intervention", run_id=run_id, note=f"abandoned: {reason}", at=at)
        self.release_claim(run["worktree_path"])
        self.release_advance_claim(run["worktree_path"])

    def record_baseline(self, run_id: int, project: str, failing: list[str], source: str) -> None:
        self.insert(
            "baseline",
            run_id=run_id,
            project=project,
            failing=json.dumps(sorted(failing)),
            captured_at=now(),
            source=source,
        )

    def record_collection(
        self, run_id: int, project: str, tests: list[str], failed_files: dict
    ) -> None:
        self.insert(
            "collection_snapshot",
            run_id=run_id,
            project=project,
            tests=json.dumps(sorted(tests)),
            failed_files=json.dumps(failed_files),
            captured_at=now(),
        )

    def baseline_rows(self, run_id: int) -> list[sqlite3.Row]:
        return self.all("SELECT * FROM baseline WHERE run_id = ?", (run_id,))

    def amend_baseline(self, run_id: int, baseline_id: int, failing: list[str]) -> None:
        self._write(
            "UPDATE baseline SET failing = ? WHERE id = ? AND run_id = ?",
            (json.dumps(sorted(failing)), baseline_id, run_id),
        )

    def latest_close_sweeps(self, run_id: int) -> list[sqlite3.Row]:
        """Each project's most recent close-sweep invocation in the run."""
        return self.all(
            "SELECT project, other_failures FROM invocation WHERE id IN ("
            "  SELECT MAX(id) FROM invocation WHERE run_id = ? AND phase_at = 'CLOSE_SWEEP'"
            "  GROUP BY project)",
            (run_id,),
        )

    # -- cycles and what is said about them ---------------------------------

    def skip_cycle(self, cycle_id: int, *, from_phase: str, to_phase: str, reason: str) -> None:
        at = now()
        self._write(
            "UPDATE cycle SET phase = ?, closed_at = ?, skip_reason = ? WHERE id = ?",
            (to_phase, at, reason, cycle_id),
        )
        self.insert(
            "transition", cycle_id=cycle_id, from_phase=from_phase, to_phase=to_phase, at=at
        )

    def set_targets(self, cycle_id: int, targets: list[str]) -> None:
        self.update("cycle", cycle_id, target_tests=json.dumps(targets))

    def add_annotation(self, run_id: int, cycle_id: int | None, key: str, value: str) -> None:
        self.insert("annotation", run_id=run_id, cycle_id=cycle_id, key=key, value=value, at=now())

    def add_note(self, run_id: int, cycle_id: int | None, phase: str | None, text: str) -> None:
        self.insert("note", run_id=run_id, cycle_id=cycle_id, phase=phase, text=text, at=now())

    def add_blocker(self, run_id: int, cycle_id: int | None, kind: str, detail: str) -> None:
        self.insert("blocker", run_id=run_id, cycle_id=cycle_id, kind=kind, detail=detail, at=now())

    # -- sensitivity checks --------------------------------------------------

    def open_sensitivity_check(
        self, cycle_id: int, *, reference_diff: str, reference_untracked: str
    ) -> int:
        return self.insert(
            "sensitivity_check",
            cycle_id=cycle_id,
            reference_diff=reference_diff,
            reference_untracked=reference_untracked,
            opened_at=now(),
        )

    def record_sensitivity_mutation(
        self,
        cycle_id: int,
        check_id: int,
        *,
        mutation_diff: str,
        observed_failure: str,
        evidence_line: str,
    ) -> None:
        self._write(
            "UPDATE sensitivity_check SET mutation_diff = ?, observed_failure = ?,"
            " evidence_line = ? WHERE id = ? AND cycle_id = ?",
            (mutation_diff, observed_failure, evidence_line, check_id, cycle_id),
        )

    def close_sensitivity_check(self, cycle_id: int, check_id: int, *, restored_ok: bool) -> None:
        self._write(
            "UPDATE sensitivity_check SET restored_ok = ?, closed_at = ?"
            " WHERE id = ? AND cycle_id = ?",
            (int(restored_ok), now(), check_id, cycle_id),
        )

    # -- the state machine's records ------------------------------------------

    def contract(self, contract_id: int) -> sqlite3.Row | None:
        return self.one("SELECT * FROM plan_contract WHERE id = ?", (contract_id,))

    def cycle(self, cycle_id: int) -> sqlite3.Row | None:
        return self.one("SELECT * FROM cycle WHERE id = ?", (cycle_id,))

    def unclosed_cycle(self, run_id: int, ordinal: int) -> sqlite3.Row | None:
        return self.one(
            "SELECT * FROM cycle WHERE run_id = ? AND ordinal = ? AND closed_at IS NULL",
            (run_id, ordinal),
        )

    def add_cycle(
        self,
        run_id: int,
        *,
        ordinal: int,
        kind: str,
        projects: list[str],
        declared_tests: list[str],
        target_tests: list[str],
        phase: str,
        head_at_open: str,
        title: str | None,
    ) -> int:
        return self.insert(
            "cycle",
            run_id=run_id,
            ordinal=ordinal,
            kind=kind,
            projects=json.dumps(projects),
            declared_tests=json.dumps(declared_tests),
            target_tests=json.dumps(target_tests),
            phase=phase,
            head_at_open=head_at_open,
            title=title,
            opened_at=now(),
        )

    def move_cycle(self, cycle_id: int, *, from_phase: str, to_phase: str) -> None:
        """Record a phase transition and put the cycle in its new phase."""
        self.insert(
            "transition", cycle_id=cycle_id, from_phase=from_phase, to_phase=to_phase, at=now()
        )
        self.update("cycle", cycle_id, phase=to_phase)

    def mark_cycle_closed(self, cycle_id: int) -> None:
        self.update("cycle", cycle_id, closed_at=now())

    def run_target_tests(self, run_id: int) -> list[list[str]]:
        """Every cycle's targets in the run, one list per cycle."""
        rows = self.all("SELECT target_tests FROM cycle WHERE run_id = ?", (run_id,))
        return [json.loads(r["target_tests"]) for r in rows]

    def record_invocation(
        self,
        run_id: int,
        cycle_id: int | None,
        *,
        phase_at: str,
        project: str,
        adapter: str,
        target_test: str | None,
        target_outcome: str | None,
        target_failure: str,
        total_passed: int,
        total_failed: int,
        other_failures: list[str],
        others_observed: bool = True,
        duration_ms: int,
        retried: bool = False,
        tree_hash: str | None,
    ) -> int:
        return self.insert(
            "invocation",
            run_id=run_id,
            cycle_id=cycle_id,
            phase_at=phase_at,
            project=project,
            adapter=adapter,
            target_test=target_test,
            target_outcome=target_outcome,
            target_failure=target_failure,
            total_passed=total_passed,
            total_failed=total_failed,
            other_failures=json.dumps(other_failures),
            others_observed=int(others_observed),
            duration_ms=duration_ms,
            retried=int(retried),
            tree_hash=tree_hash,
            started_at=now(),
        )

    def last_gate(self, run_id: int, project: str, kind: str) -> sqlite3.Row | None:
        return self.one(
            "SELECT ok, tree_hash FROM gate_result"
            " WHERE run_id = ? AND project = ? AND kind = ?"
            " ORDER BY id DESC LIMIT 1",
            (run_id, project, kind),
        )

    def record_gate(
        self,
        run_id: int,
        cycle_id: int | None,
        *,
        project: str,
        kind: str,
        ok: bool,
        output: str,
        tree_hash: str | None,
        skipped: bool = False,
    ) -> None:
        self.insert(
            "gate_result",
            run_id=run_id,
            cycle_id=cycle_id,
            project=project,
            kind=kind,
            ok=int(ok),
            output=output,
            tree_hash=tree_hash,
            skipped=int(skipped),
            at=now(),
        )

    def record_artifact_check(
        self,
        run_id: int,
        cycle_id: int | None,
        *,
        artifact: str,
        stale: bool,
        regenerate_failed: bool,
    ) -> int:
        return self.insert(
            "artifact_check",
            run_id=run_id,
            cycle_id=cycle_id,
            artifact=artifact,
            stale=int(stale),
            regenerated=0,
            regenerate_failed=int(regenerate_failed),
            at=now(),
        )

    def mark_artifact_check(
        self, run_id: int, check_id: int, *, regenerated: bool = False, failed: bool = False
    ) -> None:
        """Flag an artifact check regenerated, or its regenerate hook failed."""
        cols = {}
        if regenerated:
            cols["regenerated"] = 1
        if failed:
            cols["regenerate_failed"] = 1
        sets = ", ".join(f"{k} = ?" for k in cols)
        self._write(
            f"UPDATE artifact_check SET {sets} WHERE id = ? AND run_id = ?",
            (*cols.values(), check_id, run_id),
        )

    def record_commit(
        self,
        run_id: int,
        cycle_id: int | None,
        *,
        phase: str,
        sha: str,
        message: str,
        files: list[str],
    ) -> None:
        self.insert(
            "commit_record",
            run_id=run_id,
            cycle_id=cycle_id,
            phase=phase,
            sha=sha,
            message=message,
            files=json.dumps(files),
            at=now(),
        )

    def event_details(self, run_id: int, kind: str) -> list[str]:
        """The detail of every integrity event of one kind in the run, oldest first."""
        rows = self.all(
            "SELECT detail FROM integrity_event WHERE run_id = ? AND kind = ? ORDER BY id",
            (run_id, kind),
        )
        return [r["detail"] for r in rows]

    def cycle_event_kinds(self, cycle_id: int, kinds: list[str]) -> list[str]:
        """Which of `kinds` were recorded against the cycle, one entry per event."""
        rows = self.all(
            "SELECT kind FROM integrity_event WHERE cycle_id = ? AND kind IN ({})".format(
                ",".join("?" * len(kinds))
            ),
            (cycle_id, *kinds),
        )
        return [r["kind"] for r in rows]

    def last_cycle_event_detail(self, cycle_id: int, kind: str) -> str | None:
        row = self.one(
            "SELECT detail FROM integrity_event WHERE cycle_id = ? AND kind = ?"
            " ORDER BY id DESC LIMIT 1",
            (cycle_id, kind),
        )
        return row["detail"] if row else None

    def cycle_has_event(self, cycle_id: int, kind: str) -> bool:
        return (
            self.one(
                "SELECT id FROM integrity_event WHERE cycle_id = ? AND kind = ?", (cycle_id, kind)
            )
            is not None
        )

    def run_has_event(self, run_id: int, kind: str, detail: str) -> bool:
        return (
            self.one(
                "SELECT id FROM integrity_event WHERE run_id = ? AND kind = ? AND detail = ?",
                (run_id, kind, detail),
            )
            is not None
        )

    def cycle_has_note(self, cycle_id: int) -> bool:
        return self.one("SELECT id FROM note WHERE cycle_id = ?", (cycle_id,)) is not None

    def annotation_keys_of(self, cycle_id: int) -> set[str]:
        rows = self.all("SELECT key FROM annotation WHERE cycle_id = ?", (cycle_id,))
        return {r["key"] for r in rows}

    # -- the fleet's view ------------------------------------------------------

    def active_runs(self) -> list[sqlite3.Row]:
        """Every run not yet ended, in any worktree, with its plan."""
        scope, extra = self._scoped("r.source")
        return self.all(
            "SELECT r.id, r.worktree_path, r.executor_model, r.started_at, r.source,"
            "       p.plan_path, p.declared_cycles"
            " FROM run r JOIN plan_contract p ON p.id = r.plan_contract_id"
            f" WHERE r.ended_at IS NULL{scope} ORDER BY r.id",
            extra,
        )

    def last_invocation_at(self, run_id: int) -> str | None:
        row = self.one("SELECT MAX(started_at) AS at FROM invocation WHERE run_id = ?", (run_id,))
        return row["at"] if row else None

    def baseline_claims(self) -> list[sqlite3.Row]:
        scope, extra = self._scoped()
        return self.all(f"SELECT * FROM baseline_claim WHERE 1 = 1{scope} ORDER BY id", extra)

    def advance_claims(self) -> list[sqlite3.Row]:
        scope, extra = self._scoped()
        return self.all(f"SELECT * FROM advance_claim WHERE 1 = 1{scope} ORDER BY id", extra)

    # -- projections: the friction log, progress and metrics -------------------

    def runs_in(self, worktree: str) -> list[sqlite3.Row]:
        scope, extra = self._scoped()
        return self.all(
            f"SELECT * FROM run WHERE worktree_path = ?{scope} ORDER BY id", (worktree, *extra)
        )

    def run_events(self, run_id: int) -> list[sqlite3.Row]:
        return self.all("SELECT * FROM integrity_event WHERE run_id = ? ORDER BY id", (run_id,))

    def cycle_events(self, cycle_id: int) -> list[sqlite3.Row]:
        return self.all("SELECT * FROM integrity_event WHERE cycle_id = ? ORDER BY id", (cycle_id,))

    def event_counts(self, run_id: int) -> list[sqlite3.Row]:
        """(kind, n) per integrity event kind in the run."""
        return self.all(
            "SELECT kind, COUNT(*) n FROM integrity_event WHERE run_id = ? GROUP BY kind",
            (run_id,),
        )

    def regenerated_artifacts(self, run_id: int) -> list[str]:
        rows = self.all(
            "SELECT DISTINCT artifact FROM artifact_check WHERE run_id = ? AND regenerated = 1",
            (run_id,),
        )
        return [r["artifact"] for r in rows]

    def interventions(self, run_id: int) -> list[sqlite3.Row]:
        return self.all("SELECT * FROM human_intervention WHERE run_id = ? ORDER BY id", (run_id,))

    def commits(self, cycle_id: int) -> list[sqlite3.Row]:
        return self.all("SELECT * FROM commit_record WHERE cycle_id = ? ORDER BY id", (cycle_id,))

    def annotations(self, cycle_id: int) -> list[sqlite3.Row]:
        return self.all("SELECT * FROM annotation WHERE cycle_id = ? ORDER BY id", (cycle_id,))

    def cycle_notes(self, cycle_id: int) -> list[sqlite3.Row]:
        return self.all("SELECT * FROM note WHERE cycle_id = ? ORDER BY id", (cycle_id,))

    def run_notes(self, run_id: int) -> list[sqlite3.Row]:
        """Notes about the run as a whole, recorded while no cycle was open."""
        return self.all(
            "SELECT * FROM note WHERE run_id = ? AND cycle_id IS NULL ORDER BY id", (run_id,)
        )

    def blockers(self, run_id: int) -> list[sqlite3.Row]:
        return self.all("SELECT * FROM blocker WHERE run_id = ? ORDER BY id", (run_id,))

    def blocker_counts(self, run_id: int) -> list[sqlite3.Row]:
        """(kind, n) per blocker kind in the run."""
        return self.all(
            "SELECT kind, COUNT(*) n FROM blocker WHERE run_id = ? GROUP BY kind", (run_id,)
        )

    def abandonment(self, run_id: int) -> sqlite3.Row | None:
        return self.one("SELECT * FROM abandonment WHERE run_id = ?", (run_id,))

    def suite_time_by_phase(self, run_id: int) -> list[sqlite3.Row]:
        """(phase_at, n, ms) over every invocation of the run."""
        return self.all(
            "SELECT phase_at, COUNT(*) n, SUM(duration_ms) ms FROM invocation"
            " WHERE run_id = ? GROUP BY phase_at",
            (run_id,),
        )

    def cycle_times(self, run_id: int) -> list[sqlite3.Row]:
        """(ordinal, opened_at, closed_at, n, ms) per cycle: its suite runs and their time."""
        return self.all(
            "SELECT c.ordinal, c.opened_at, c.closed_at,"
            " COUNT(i.id) n, COALESCE(SUM(i.duration_ms), 0) ms"
            " FROM cycle c LEFT JOIN invocation i ON i.cycle_id = c.id"
            " WHERE c.run_id = ? GROUP BY c.id ORDER BY c.ordinal",
            (run_id,),
        )


def open_readonly(path: Path, *, source: str | None = LOCAL_SOURCE) -> Ledger | None:
    """A reader on an existing ledger, or None when there is none yet.

    Read-only is structural: the file is opened with SQLite's `mode=ro` URI, which also
    refuses to create it, and no schema script or migration runs. A reader therefore
    cannot perturb a ledger that live agents are writing, even if this code's schema
    constant were ever to drift from the one on disk.
    """
    if not path.is_file():
        return None
    reader = Ledger.__new__(Ledger)
    reader.repo_path = None
    reader.source = source
    reader.path = path
    reader.db = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    reader.db.row_factory = sqlite3.Row
    return reader


def open_ledger(repo_path: Path):
    """The ledger of a repository. Every command opens its ledger through here.

    A runner configured with a ledger service's socket keeps no ledger of its own: it
    gets a `RemoteLedger` that reads and writes the host's.
    """
    split = _as_runner()
    if split is not None and split.ledger_socket is not None:
        from .remote import RemoteLedger

        return RemoteLedger(split.ledger_socket, repo_path)
    return Ledger(repo_path)
