from conftest import run_cli, write_plan
from tddcli import gitutil
from tddcli.ledger import Ledger

TWO_CYCLE_PLAN = """---
cycles:
  - n: 1
    project: backend
    title: "cycle one"
    test: "tests/test_a.py::test_a"
    commit_red: "test: a"
    commit_green: "feat: a"
  - n: 2
    project: backend
    title: "cycle two"
    test: "tests/test_b.py::test_b"
    commit_red: "test: b"
    commit_green: "feat: b"
---
"""


def test_close_cycle_is_idempotent_when_the_row_is_already_closed(repo):
    from tddcli import config as config_mod
    from tddcli.machine import Engine

    plan = write_plan(repo, TWO_CYCLE_PLAN)
    run_cli(repo, "plan", "register", plan)
    out = run_cli(repo, "run", "start", "--plan", plan)
    assert out["ok"], out

    run_id = out["run"]["id"]
    ledger = Ledger(gitutil.repo_identity(repo))
    run_row = ledger.one("SELECT * FROM run WHERE id = ?", (run_id,))
    cycle_row = ledger.one(
        "SELECT * FROM cycle WHERE run_id = ? ORDER BY id ASC LIMIT 1", (run_id,)
    )
    cfg = config_mod.load(repo)
    engine = Engine(ledger, cfg, repo, run_row)

    closed_at_after_first = None

    engine.close_cycle(cycle_row)

    closed_at_after_first = ledger.one(
        "SELECT closed_at FROM cycle WHERE id = ?", (cycle_row["id"],)
    )["closed_at"]

    engine.close_cycle(cycle_row)

    open_rows = ledger.all(
        "SELECT * FROM cycle WHERE run_id = ? AND closed_at IS NULL", (run_id,)
    )
    assert len(open_rows) == 1

    transitions = ledger.all(
        "SELECT * FROM transition WHERE cycle_id = ? AND to_phase = 'CLOSED'",
        (cycle_row["id"],),
    )
    assert len(transitions) == 1

    ordinal_2_rows = ledger.all(
        "SELECT * FROM cycle WHERE run_id = ? AND ordinal = 2", (run_id,)
    )
    assert len(ordinal_2_rows) == 1

    closed_at_after_second = ledger.one(
        "SELECT closed_at FROM cycle WHERE id = ?", (cycle_row["id"],)
    )["closed_at"]
    assert closed_at_after_second == closed_at_after_first


def test_open_cycle_returns_the_existing_open_row_for_an_ordinal(repo):
    from tddcli import config as config_mod
    from tddcli.machine import Engine

    plan = write_plan(repo, TWO_CYCLE_PLAN)
    run_cli(repo, "plan", "register", plan)
    out = run_cli(repo, "run", "start", "--plan", plan)
    assert out["ok"], out

    run_id = out["run"]["id"]
    ledger = Ledger(gitutil.repo_identity(repo))
    run_row = ledger.one("SELECT * FROM run WHERE id = ?", (run_id,))
    cfg = config_mod.load(repo)
    engine = Engine(ledger, cfg, repo, run_row)

    a = engine.open_cycle(2)
    b = engine.open_cycle(2)

    assert a["id"] == b["id"]

    ordinal_2_rows = ledger.all(
        "SELECT * FROM cycle WHERE run_id = ? AND ordinal = 2", (run_id,)
    )
    assert len(ordinal_2_rows) == 1
