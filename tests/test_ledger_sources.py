"""Sources in the ledger: every run, contract, claim and cached baseline belongs to one.

A source is where a run came in from. Single-user mode and single-machine split mode
are both the source `local`; a ledger service names one source per guest socket.
"""

from __future__ import annotations

from tddcli.ledger import Ledger, now

#: The v12 shape of the tables v13 rebuilds, copied from `SCHEMA` before v13.
V12_REBUILT = """
CREATE TABLE baseline_claim (
    id INTEGER PRIMARY KEY,
    worktree_path TEXT NOT NULL UNIQUE,
    hostname TEXT NOT NULL,
    pid INTEGER NOT NULL,
    projects_total INTEGER NOT NULL DEFAULT 0,
    projects_done INTEGER NOT NULL DEFAULT 0,
    current_project TEXT,
    started_at TEXT NOT NULL
);

CREATE TABLE advance_claim (
    id INTEGER PRIMARY KEY,
    worktree_path TEXT NOT NULL UNIQUE,
    hostname TEXT NOT NULL,
    pid INTEGER NOT NULL,
    started_at TEXT NOT NULL
);

CREATE TABLE baseline_cache (
    id INTEGER PRIMARY KEY,
    project TEXT NOT NULL,
    tree_hash TEXT NOT NULL,
    config_sha TEXT NOT NULL,
    failing TEXT NOT NULL,
    tests TEXT NOT NULL,
    failed_files TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(project, tree_hash, config_sha)
);
"""


def _columns(ledger: Ledger, table: str) -> set[str]:
    return {r[1] for r in ledger.db.execute(f"PRAGMA table_info({table})").fetchall()}


def _make_v12(ledger: Ledger) -> None:
    """Put a freshly opened ledger back in its v12 shape, keeping its rows."""
    for table in ("run", "plan_contract"):
        if "source" in _columns(ledger, table):
            ledger.db.execute(f"ALTER TABLE {table} DROP COLUMN source")
    rows = [dict(r) for r in ledger.db.execute("SELECT * FROM baseline_claim").fetchall()]
    ledger.db.executescript(
        "DROP TABLE baseline_claim; DROP TABLE advance_claim; DROP TABLE baseline_cache;"
        + V12_REBUILT
    )
    for row in rows:
        row.pop("source", None)
        ledger.insert("baseline_claim", **row)
    ledger._write("UPDATE meta SET value = '12' WHERE key = 'schema_version'", ())


def test_a_v12_ledger_migrates_with_its_rows_tagged_local(tmp_path, ledger_home):
    ledger = Ledger(tmp_path / "somerepo")
    contract = ledger.insert(
        "plan_contract",
        plan_path="tasks/p.md",
        status="declared",
        declared_cycles="[]",
        annotation_keys="[]",
        registered_at=now(),
    )
    ledger.insert(
        "run",
        plan_contract_id=contract,
        executor_model="m",
        executor_source="human",
        worktree_path="/w",
        started_at=now(),
        preexisting_dirty="[]",
    )
    ledger.insert("baseline_claim", worktree_path="/w", hostname="h", pid=1, started_at=now())
    _make_v12(ledger)
    ledger.close()

    reopened = Ledger(tmp_path / "somerepo")
    sources = {
        table: dict(reopened.db.execute(f"SELECT * FROM {table}").fetchone()).get("source")
        for table in ("run", "plan_contract", "baseline_claim")
    }
    assert sources == {"run": "local", "plan_contract": "local", "baseline_claim": "local"}
