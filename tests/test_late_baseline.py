"""Late-baseline probing: start sha capture, temporary worktrees, and per-test verdicts."""

from __future__ import annotations

from conftest import run_cli, write_plan
from tddcli import gitutil
from tddcli.ledger import Ledger
from test_baseline_integrity import BACKEND_ONLY_PLAN, PLAN, TEST_ADD


def _drive_to_close(repo):
    """Register BACKEND_ONLY_PLAN, start, RED, GREEN; leave cycle 1 in AWAITING_REFACTOR."""
    plan = write_plan(repo, BACKEND_ONLY_PLAN)
    run_cli(repo, "plan", "register", plan)
    out = run_cli(repo, "run", "start", "--plan", plan)
    assert out["ok"], out
    (repo / "backend" / "tests" / "test_add.py").write_text(TEST_ADD)
    (repo / "backend" / "app" / "calc.py").write_text("def add(a, b):\n    raise NotImplementedError\n")
    run_cli(repo, "advance")
    (repo / "backend" / "app" / "calc.py").write_text("def add(a, b):\n    return a + b\n")
    return out


def _pull_svc_into_the_sweep(repo):
    """Touching other/'s root pulls artifact `schema`'s consumer svc into the close sweep."""
    (repo / "other" / "generated.json").write_text("{}")


def test_run_start_records_the_start_sha_on_the_run_row(repo):
    write_plan(repo, PLAN)
    sha = gitutil.head(repo)
    run_cli(repo, "plan", "register", "tasks/plan.md")
    out = run_cli(repo, "run", "start", "--plan", "tasks/plan.md")
    assert out["ok"], out
    ledger = Ledger(gitutil.repo_identity(repo))
    run_id = out["run"]["id"]
    row = ledger.one("SELECT * FROM run WHERE id = ?", (run_id,))
    assert dict(row).get("start_sha") == sha
