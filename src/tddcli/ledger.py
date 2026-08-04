"""SQLite ledger. One per repository (R13.3), outside every worktree, never in the repo.

Invocations, transitions and events are append-only. Nothing here accepts a phase
from a caller — phases are written only by the state machine (P1).
"""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

SCHEMA_VERSION = 2

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
        self.db = sqlite3.connect(self.path)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.executescript(SCHEMA)
        self.db.execute(
            "INSERT OR IGNORE INTO meta(key, value) VALUES ('schema_version', ?)",
            (str(SCHEMA_VERSION),),
        )
        self.db.commit()

    # -- generic helpers -------------------------------------------------

    def insert(self, table: str, **cols) -> int:
        keys = ", ".join(cols)
        marks = ", ".join("?" for _ in cols)
        cur = self.db.execute(
            f"INSERT INTO {table} ({keys}) VALUES ({marks})", tuple(cols.values())
        )
        self.db.commit()
        return cur.lastrowid

    def one(self, sql: str, params: tuple = ()) -> sqlite3.Row | None:
        return self.db.execute(sql, params).fetchone()

    def all(self, sql: str, params: tuple = ()) -> list[sqlite3.Row]:
        return self.db.execute(sql, params).fetchall()

    def update(self, table: str, row_id: int, **cols) -> None:
        sets = ", ".join(f"{k} = ?" for k in cols)
        self.db.execute(
            f"UPDATE {table} SET {sets} WHERE id = ?", (*cols.values(), row_id)
        )
        self.db.commit()

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
