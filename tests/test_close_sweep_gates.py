"""Close-sweep gate ordering and short-circuit (issue #129)."""

from __future__ import annotations

from pathlib import Path

from conftest import git, run_cli, write_plan
from tddcli import gitutil
from tddcli.ledger import Ledger

# ── inner plan used by every test to reach the close sweep ────────────────────

SIMPLE_PLAN = """---
cycles:
  - n: 1
    project: backend
    title: "basic pass"
    test: "tests/test_gate_probe.py::test_gate_probe"
    stub_expected: ["app/probe.py"]
    commit_red: "test: gate probe"
    commit_green: "feat: gate probe"
---
"""

_TEST = """\
from app.probe import probe


def test_gate_probe():
    assert probe() == 42
"""

_STUB = "def probe():\n    raise NotImplementedError\n"
_IMPL = "def probe():\n    return 42\n"


def _toml(lint_cmds: list[str], typecheck_cmds: list[str] | None = None) -> str:
    tc = typecheck_cmds if typecheck_cmds is not None else []
    return (
        "[project.backend]\n"
        'root       = "backend"\n'
        'adapter    = "pytest"\n'
        'test_paths = ["tests/"]\n'
        f"lint       = {lint_cmds!r}\n"
        f"typecheck  = {tc!r}\n"
    )


def _drive_to_close(
    repo: Path,
    lint_cmds: list[str] | None = None,
    typecheck_cmds: list[str] | None = None,
    project: str = "backend",
) -> dict:
    """Drive a single-cycle inner plan through RED → GREEN and return the
    close-sweep envelope (the advance at AWAITING_REFACTOR)."""
    lint = lint_cmds if lint_cmds is not None else []
    (repo / "tdd.toml").write_text(_toml(lint, typecheck_cmds))
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "configure gates")

    plan = write_plan(repo, SIMPLE_PLAN)
    assert run_cli(repo, "plan", "register", plan)["ok"]
    assert run_cli(repo, "run", "start", "--plan", plan)["ok"]

    # RED: write test + stub so the test collects but fails
    (repo / project / "tests" / "test_gate_probe.py").write_text(_TEST)
    (repo / project / "app" / "probe.py").write_text(_STUB)
    adv = run_cli(repo, "advance")
    assert adv["next_action"]["verb"] == "write_implementation", adv

    # GREEN: write real implementation
    (repo / project / "app" / "probe.py").write_text(_IMPL)
    adv = run_cli(repo, "advance")
    assert adv["next_action"]["verb"] == "refactor_or_advance", adv

    # Advance at AWAITING_REFACTOR → triggers the close sweep
    return run_cli(repo, "advance")


# ── cycle 1 ── pin: a failing gate replies fix_regression with that gate's entry



def test_failing_lint_replies_fix_regression_with_the_lint_gate(repo):
    out = _drive_to_close(repo, lint_cmds=["sh -c 'exit 1'"])
    verb = out["next_action"]["verb"]
    gates = out.get("result", {}).get("gates", [])
    assert (verb, [(g["project"], g["kind"]) for g in gates]) == (
        "fix_regression",
        [("backend", "lint")],
    )


# ── cycle 2 ── pin: a gate that ran records a gate_result row


def test_a_failing_lint_records_its_gate_result_row(repo):
    out = _drive_to_close(repo, lint_cmds=["sh -c 'exit 1'"])
    run_id = out["run"]["id"]
    led = Ledger(gitutil.repo_identity(repo))
    rows = led.all(
        "SELECT * FROM gate_result WHERE run_id = ? AND project = 'backend' AND kind = 'lint'",
        (run_id,),
    )
    assert any(r["ok"] == 0 for r in rows)
