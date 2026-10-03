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


def _contract(ledger: Ledger) -> int:
    return ledger.register_contract(
        plan_path="tasks/p.md",
        blob_sha="abc",
        commit_sha="def",
        status="declared",
        declared_cycles="[]",
        annotation_keys="[]",
        ancillary_files="[]",
    )


def _start(ledger: Ledger, contract: int, worktree: str) -> int:
    return ledger.start_run(
        contract,
        executor_model="m",
        executor_session=None,
        executor_source="human",
        worktree=worktree,
        allow_dirty=False,
        preexisting_dirty=[],
        config_sha=None,
        start_sha=None,
    )


def test_a_source_reads_only_its_own_runs_and_contracts(tmp_path, ledger_home):
    repo = tmp_path / "somerepo"
    a = Ledger(repo, source="a")
    b = Ledger(repo, source="b")
    worktree = str(tmp_path / "wt")
    run_id = _start(a, _contract(a), worktree)
    a.record_baseline(run_id, "app", ["t::x"], source="probed")
    a.record_invocation(
        run_id,
        None,
        phase_at="CLOSE_SWEEP",
        project="app",
        adapter="pytest",
        target_test=None,
        target_outcome=None,
        target_failure="",
        total_passed=1,
        total_failed=0,
        other_failures=[],
        duration_ms=500,
        tree_hash=None,
    )

    seen_by_b = {
        "active_run": b.active_run(worktree),
        "latest_contract": b.latest_contract("tasks/p.md"),
        "previous_baseline": b.previous_baseline(worktree, "app", 10**9),
        "max_suite_duration_ms": b.max_suite_duration_ms("app"),
        "latest_run": b.latest_run(worktree),
    }
    assert seen_by_b == dict.fromkeys(seen_by_b)


def test_two_sources_claim_and_cache_the_same_worktree_independently(tmp_path, ledger_home):
    repo = tmp_path / "somerepo"
    a = Ledger(repo, source="a")
    b = Ledger(repo, source="b")
    worktree = "/work/repo"
    a.claim(worktree, "h", 1, 1)
    a.cache_baseline("app", "tree", "cfg", failing=["t::x"], tests=["t::x"], failed_files={})

    assert (b.claim(worktree, "h", 2, 1) is not None, b.cached_baseline("app", "tree", "cfg")) == (
        True,
        None,
    )
