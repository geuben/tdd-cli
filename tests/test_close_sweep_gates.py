"""Close-sweep gate ordering and short-circuit (issue #129)."""

from __future__ import annotations

from pathlib import Path

from conftest import git, run_cli, write_plan
from tddcli import config as config_mod
from tddcli import gitutil
from tddcli.ledger import Ledger
from tddcli.machine import Engine

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


# ── cycle 3 ── _gate stops at the first failing command


def test_gate_stops_at_the_first_failing_command(repo):
    lint_cmds = [
        "sh -c 'echo LINT-BOOM; exit 1'",
        "sh -c 'echo SECOND-RAN; exit 1'",
    ]
    out = _drive_to_close(repo, lint_cmds=lint_cmds)
    gates = out.get("result", {}).get("gates", [])
    lint_gate = next((g for g in gates if g["kind"] == "lint"), None)
    assert lint_gate is not None
    assert "SECOND-RAN" not in lint_gate["output"]


# ── cycle 4 ── a failing lint means typecheck is never run


def test_a_failing_lint_stops_the_gate_pass_before_typecheck(repo, tmp_path):
    counter = tmp_path / "typecheck-ran"
    typecheck_cmds = [f"sh -c 'echo ran >> {counter}; exit 1'"]
    _drive_to_close(repo, lint_cmds=["sh -c 'exit 1'"], typecheck_cmds=typecheck_cmds)
    assert not counter.exists()


# ── cycle 5 ── a failing gate short-circuits the sweep before any suite runs


def test_a_failing_gate_runs_no_suite(repo):
    out = _drive_to_close(repo, lint_cmds=["sh -c 'exit 1'"])
    run_id = out["run"]["id"]
    led = Ledger(gitutil.repo_identity(repo))
    rows = led.all(
        "SELECT * FROM invocation WHERE run_id = ? AND phase_at = 'CLOSE_SWEEP'",
        (run_id,),
    )
    assert len(rows) == 0


# ── cycle 6 ── every sweep project's gates run before any project's suite

_THREE_PLAN = """\
---
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


def test_a_later_projects_failing_gate_runs_no_earlier_suite(repo_three):
    # Rewrite tdd.toml: backend has no lint, svc has a failing lint.
    (repo_three / "tdd.toml").write_text(
        "[project.backend]\n"
        'root       = "backend"\n'
        'adapter    = "pytest"\n'
        'test_paths = ["tests/"]\n'
        "\n"
        "[project.svc]\n"
        'root       = "svc"\n'
        'adapter    = "pytest"\n'
        'test_paths = ["tests/"]\n'
        "lint       = [\"sh -c 'exit 1'\"]\n"
        "typecheck  = []\n"
        "\n"
        "[project.other]\n"
        'root       = "other"\n'
        'adapter    = "pytest"\n'
        'test_paths = ["tests/"]\n'
        "\n"
        "[artifact.schema]\n"
        'path        = "backend/schema.json"\n'
        'produced_by = "backend"\n'
        'consumed_by = ["svc"]\n'
        'regenerate  = "true"\n'
    )
    git(repo_three, "add", "-A")
    git(repo_three, "commit", "-q", "-m", "configure svc lint")

    plan = write_plan(repo_three, _THREE_PLAN)
    assert run_cli(repo_three, "plan", "register", plan)["ok"]
    assert run_cli(repo_three, "run", "start", "--plan", plan)["ok"]

    # RED: test + stub
    (repo_three / "backend" / "tests" / "test_gate_probe.py").write_text(_TEST)
    (repo_three / "backend" / "app" / "probe.py").write_text(_STUB)
    adv = run_cli(repo_three, "advance")
    assert adv["next_action"]["verb"] == "write_implementation", adv

    # GREEN: real implementation
    (repo_three / "backend" / "app" / "probe.py").write_text(_IMPL)
    adv = run_cli(repo_three, "advance")
    assert adv["next_action"]["verb"] == "refactor_or_advance", adv

    # Modify backend/schema.json (dirty) → pulls svc into the close sweep
    (repo_three / "backend" / "schema.json").write_text('{"version": 2}\n')

    # Advance at AWAITING_REFACTOR → svc's lint fails → no suite runs
    out = run_cli(repo_three, "advance")

    run_id = out["run"]["id"]
    led = Ledger(gitutil.repo_identity(repo_three))
    rows = led.all(
        "SELECT * FROM invocation WHERE run_id = ? AND phase_at = 'CLOSE_SWEEP' AND project = 'backend'",
        (run_id,),
    )
    assert len(rows) == 0


# ── cycle 7 ── the gate-failure reply does not claim the sweep is green


def test_the_gate_failure_reply_does_not_claim_the_sweep_is_green(repo):
    out = _drive_to_close(repo, lint_cmds=["sh -c 'exit 1'"])
    assert out["next_action"]["detail"] == (
        "Close sweep stopped before the suite: lint/typecheck gates failed."
    )


# ── cycle 8 ── pin: a gate that failed is re-run at the same tree


def test_a_failed_gate_is_rerun_at_the_same_tree(repo, tmp_path):
    counter = tmp_path / "lint-count"
    lint_cmds = [f"sh -c 'echo x >> {counter}; exit 1'"]
    _drive_to_close(repo, lint_cmds=lint_cmds)
    # Advance again at AWAITING_REFACTOR with nothing edited (same tree) → gate re-runs
    run_cli(repo, "advance")
    assert counter.read_text().count("\n") == 2


# ── cycle 9 ── pin: a gate is re-run when its project tree changed


def test_a_gate_is_rerun_when_the_tree_changed(repo, tmp_path):
    """Lint passes but suite fails first time; tree changes; lint runs again second time."""
    counter = tmp_path / "lint-count"
    lint_cmds = [f"sh -c 'echo x >> {counter}'"]  # exits 0 (passes)

    # Set up a failing test that will be in the close sweep
    (repo / "tdd.toml").write_text(_toml(lint_cmds))
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "configure gates")

    plan = write_plan(repo, SIMPLE_PLAN)
    assert run_cli(repo, "plan", "register", plan)["ok"]
    assert run_cli(repo, "run", "start", "--plan", plan)["ok"]

    # RED
    (repo / "backend" / "tests" / "test_gate_probe.py").write_text(_TEST)
    (repo / "backend" / "app" / "probe.py").write_text(_STUB)
    adv = run_cli(repo, "advance")
    assert adv["next_action"]["verb"] == "write_implementation", adv

    # GREEN
    (repo / "backend" / "app" / "probe.py").write_text(_IMPL)
    adv = run_cli(repo, "advance")
    assert adv["next_action"]["verb"] == "refactor_or_advance", adv

    # First close: add a failing test → lint passes but suite fails
    (repo / "backend" / "tests" / "test_fail.py").write_text("def test_fail():\n    assert False\n")
    out1 = run_cli(repo, "advance")
    assert out1["next_action"]["verb"] == "fix_regression", out1

    # Fix the failing test → tree changes → second close: lint re-runs
    (repo / "backend" / "tests" / "test_fail.py").write_text("def test_fail():\n    assert True\n")
    out2 = run_cli(repo, "advance")
    assert out2["next_action"]["verb"] != "fix_regression" or out2.get("result", {}).get("gates"), (
        out2
    )

    assert counter.read_text().count("\n") == 2


# ── cycle 11 ── a gate that passed at this tree hash is not re-executed


def test_a_passing_gate_is_not_reexecuted_at_an_unchanged_tree(repo, tmp_path):
    """Lint passes first close; suite fails first close; tree unchanged for second close →
    lint should be skipped the second time."""
    counter = tmp_path / "lint-count"
    lint_cmds = [f"sh -c 'echo x >> {counter}'"]  # exits 0 (passes)

    (repo / "tdd.toml").write_text(_toml(lint_cmds))
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "configure gates")

    plan = write_plan(repo, SIMPLE_PLAN)
    assert run_cli(repo, "plan", "register", plan)["ok"]
    assert run_cli(repo, "run", "start", "--plan", plan)["ok"]

    # RED/GREEN
    (repo / "backend" / "tests" / "test_gate_probe.py").write_text(_TEST)
    (repo / "backend" / "app" / "probe.py").write_text(_STUB)
    assert run_cli(repo, "advance")["next_action"]["verb"] == "write_implementation"
    (repo / "backend" / "app" / "probe.py").write_text(_IMPL)
    assert run_cli(repo, "advance")["next_action"]["verb"] == "refactor_or_advance"

    # First close: add failing test (dirty) → lint passes, suite fails
    (repo / "backend" / "tests" / "test_fail.py").write_text("def test_fail():\n    assert False\n")
    out1 = run_cli(repo, "advance")
    assert out1["next_action"]["verb"] == "fix_regression", out1

    # Second close: no change to tree → lint should be skipped
    run_cli(repo, "advance")
    # (could be fix_regression again due to suite failure, but lint must NOT re-run)

    assert counter.read_text().count("\n") == 1


# ── cycle 12 ── a skipped gate still records a gate_result row, marked skipped


def test_a_skipped_gate_records_a_skipped_row(repo, tmp_path):
    """Same scenario as cycle 11: lint passes first close, skipped second close.
    The second gate_result row must have skipped=1."""
    counter = tmp_path / "lint-count"
    lint_cmds = [f"sh -c 'echo x >> {counter}'"]

    (repo / "tdd.toml").write_text(_toml(lint_cmds))
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "configure gates")

    plan = write_plan(repo, SIMPLE_PLAN)
    assert run_cli(repo, "plan", "register", plan)["ok"]
    assert run_cli(repo, "run", "start", "--plan", plan)["ok"]

    # RED/GREEN
    (repo / "backend" / "tests" / "test_gate_probe.py").write_text(_TEST)
    (repo / "backend" / "app" / "probe.py").write_text(_STUB)
    assert run_cli(repo, "advance")["next_action"]["verb"] == "write_implementation"
    (repo / "backend" / "app" / "probe.py").write_text(_IMPL)
    assert run_cli(repo, "advance")["next_action"]["verb"] == "refactor_or_advance"

    # First close: failing test (dirty) → lint passes
    (repo / "backend" / "tests" / "test_fail.py").write_text("def test_fail():\n    assert False\n")
    out1 = run_cli(repo, "advance")
    run_id = out1["run"]["id"]
    assert out1["next_action"]["verb"] == "fix_regression", out1

    # Second close: no tree change → lint skipped
    run_cli(repo, "advance")

    led = Ledger(gitutil.repo_identity(repo))
    rows = led.all(
        "SELECT skipped FROM gate_result WHERE run_id = ? AND project = 'backend' AND kind = 'lint' ORDER BY id",
        (run_id,),
    )
    assert [r["skipped"] for r in rows] == [0, 1]


# ── issue 146 ── a sweep that skips its own suites still runs their gates


def test_skip_own_still_runs_the_cycle_projects_gates(repo):
    (repo / "tdd.toml").write_text(_toml(["sh -c 'exit 1'"]))
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "configure gates")
    plan = write_plan(repo, SIMPLE_PLAN)
    assert run_cli(repo, "plan", "register", plan)["ok"]
    out = run_cli(repo, "run", "start", "--plan", plan)

    ledger = Ledger(gitutil.repo_identity(repo))
    run_row = ledger.one("SELECT * FROM run WHERE id = ?", (out["run"]["id"],))
    cycle_row = ledger.one(
        "SELECT * FROM cycle WHERE run_id = ? ORDER BY id ASC LIMIT 1", (run_row["id"],)
    )
    engine = Engine(ledger, config_mod.load(repo), repo, run_row)

    outcome = engine.sweep(cycle_row, set(), skip_own=True)

    assert [(p, k) for p, k, _ in outcome.gates] == [("backend", "lint")]


# ── issue 146 ── a cycle with no refactor edit skips its own close-sweep suite


def test_a_cycle_with_no_refactor_edit_skips_its_own_close_sweep_suite(repo):
    out = _drive_to_close(repo, lint_cmds=["true"])
    led = Ledger(gitutil.repo_identity(repo))
    count = led.one(
        "SELECT COUNT(*) AS n FROM invocation"
        " WHERE run_id = ? AND phase_at = 'CLOSE_SWEEP' AND project = 'backend'",
        (out["run"]["id"],),
    )["n"]
    assert (out["next_action"]["verb"], count) == ("complete", 0)
