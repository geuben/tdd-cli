"""Baseline sanity gates: refuse implausible baselines, surface standing failures,
and probe live-service reachability before capture.
"""

from __future__ import annotations

import json

from conftest import git, run_cli, write_plan
from tddcli import gitutil
from tddcli.ledger import Ledger, now

PLAN = """---
cycles:
  - n: 1
    project: backend
    title: "adding two numbers"
    test: "tests/test_add.py::test_add_two_numbers"
    commit_red: "test: adding two numbers"
    commit_green: "feat: add()"
---

# Plan
"""


def _make_mostly_red_repo(repo, *, n: int = 12):
    """Replace test_smoke.py with n always-failing tests."""
    (repo / "backend" / "tests" / "test_smoke.py").unlink()
    lines = "\n".join(f"def test_fail_{i}():\n    assert False\n" for i in range(n))
    (repo / "backend" / "tests" / "test_infra.py").write_text(lines + "\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "infra: all-red suite")


def test_a_mostly_red_baseline_is_refused(repo):
    _make_mostly_red_repo(repo, n=12)
    plan = write_plan(repo, PLAN)
    run_cli(repo, "plan", "register", plan)
    out = run_cli(repo, "run", "start", "--plan", plan)

    assert out["ok"] is False, out
    assert out["result"]["reason"] == "baseline_implausible", out
    projects = {p["project"]: p for p in out["result"]["projects"]}
    assert "backend" in projects, out
    assert projects["backend"]["failing"] == 12
    assert projects["backend"]["collected"] == 12


def test_accept_baseline_overrides_the_refusal(repo):
    _make_mostly_red_repo(repo, n=12)
    plan = write_plan(repo, PLAN)
    run_cli(repo, "plan", "register", plan)
    out = run_cli(repo, "run", "start", "--plan", plan, "--accept-baseline")

    assert out["ok"] is True, out
    assert out["next_action"]["verb"] == "write_test"


def test_a_small_all_red_suite_is_not_refused(repo):
    _make_mostly_red_repo(repo, n=3)
    plan = write_plan(repo, PLAN)
    run_cli(repo, "plan", "register", plan)
    out = run_cli(repo, "run", "start", "--plan", plan)

    assert out["ok"] is True, out
    assert out["result"].get("reason") != "baseline_implausible"


def test_project_ratio_config_raises_the_threshold(repo):
    _make_mostly_red_repo(repo, n=12)
    toml = (repo / "tdd.toml").read_text()
    (repo / "tdd.toml").write_text(toml + "baseline_max_failure_ratio = 1.0\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "config: raise ratio threshold")
    plan = write_plan(repo, PLAN)
    run_cli(repo, "plan", "register", plan)
    out = run_cli(repo, "run", "start", "--plan", plan)

    assert out["ok"] is True, out


def test_accepted_implausible_baseline_records_an_event(repo):
    _make_mostly_red_repo(repo, n=12)
    plan = write_plan(repo, PLAN)
    run_cli(repo, "plan", "register", plan)
    run_cli(repo, "run", "start", "--plan", plan, "--accept-baseline")
    out = run_cli(repo, "metrics")

    events = out["result"]["runs"][0]["integrity_events"]
    assert events.get("baseline_accepted", 0) >= 1


def _make_healthy_large_repo(repo, *, passing: int = 20, failing: int = 2):
    """Replace test_smoke.py with a large mostly-passing suite."""
    (repo / "backend" / "tests" / "test_smoke.py").unlink()
    lines = "\n".join(f"def test_pass_{i}():\n    assert True\n" for i in range(passing))
    lines += "\n" + "\n".join(f"def test_fail_{i}():\n    assert False\n" for i in range(failing))
    (repo / "backend" / "tests" / "test_suite.py").write_text(lines + "\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "suite: healthy large baseline")


def test_a_healthy_baseline_is_recorded_untouched(repo):
    _make_healthy_large_repo(repo, passing=20, failing=2)
    plan = write_plan(repo, PLAN)
    run_cli(repo, "plan", "register", plan)
    out = run_cli(repo, "run", "start", "--plan", plan)

    assert out["ok"] is True, out
    assert out["result"].get("reason") != "baseline_implausible"
    metrics = run_cli(repo, "metrics")
    events = metrics["result"]["runs"][0]["integrity_events"]
    assert events.get("baseline_accepted", 0) == 0


def test_non_empty_baseline_emits_standing_delta(repo, ledger_home):
    # Seed a prior ended run with one failing test for this repo's worktree.
    ledger = Ledger(gitutil.repo_identity(repo))
    worktree_path = str(repo)
    seeded_failing_id = "backend::tests/test_infra.py::test_fail_0"

    contract_id = ledger.insert(
        "plan_contract",
        plan_path="tasks/plan.md",
        git_blob_sha=None,
        git_commit=None,
        status="declared",
        declared_cycles="[]",
        annotation_keys="[]",
        ancillary_files="[]",
        registered_at=now(),
    )
    prior_run_id = ledger.insert(
        "run",
        plan_contract_id=contract_id,
        executor_model="test-model",
        executor_source="human",
        worktree_path=worktree_path,
        started_at=now(),
        ended_at=now(),
        preexisting_dirty="[]",
    )
    ledger.insert(
        "baseline",
        run_id=prior_run_id,
        project="backend",
        failing=json.dumps([seeded_failing_id]),
        captured_at=now(),
        source="probed",
    )

    # Small suite (< MIN=10) with one inherited fail and one new fail.
    (repo / "backend" / "tests" / "test_smoke.py").unlink()
    (repo / "backend" / "tests" / "test_infra.py").write_text(
        "def test_fail_0():\n    assert False\n"  # inherited
        "\ndef test_fail_1():\n    assert False\n"  # new
        "\ndef test_pass():\n    assert True\n"
    )
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "suite: small mixed")

    plan = write_plan(repo, PLAN)
    run_cli(repo, "plan", "register", plan)
    run_cli(repo, "run", "start", "--plan", plan)

    rows = ledger.all(
        "SELECT detail FROM integrity_event WHERE kind = 'baseline_standing_delta'"
    )
    assert len(rows) == 1
    delta = json.loads(rows[0]["detail"])
    assert len(delta["new"]) == 1
    assert len(delta["inherited"]) == 1


def test_reachable_services_proceed_normally(repo):
    toml = (repo / "tdd.toml").read_text()
    (repo / "tdd.toml").write_text(toml + 'health_command = "true"\n')
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "config: passing health_command")
    plan = write_plan(repo, PLAN)
    run_cli(repo, "plan", "register", plan)
    out = run_cli(repo, "run", "start", "--plan", plan)

    assert out["ok"] is True, out
    assert out["next_action"]["verb"] == "write_test"
    assert out["result"].get("reason") != "services_unreachable"


def test_unreachable_services_refuse_before_probing(repo):
    toml = (repo / "tdd.toml").read_text()
    (repo / "tdd.toml").write_text(toml + 'health_command = "false"\n')
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "config: failing health_command")
    plan = write_plan(repo, PLAN)
    run_cli(repo, "plan", "register", plan)
    out = run_cli(repo, "run", "start", "--plan", plan)

    assert out["ok"] is False, out
    assert out["result"]["reason"] == "services_unreachable", out
    projects = {p["project"]: p for p in out["result"]["projects"]}
    assert "backend" in projects, out
    assert projects["backend"]["exit_code"] != 0


def test_first_run_reports_all_standing_failures_new(repo, ledger_home):
    # No prior run seeded — everything should be reported as new.
    ledger = Ledger(gitutil.repo_identity(repo))

    (repo / "backend" / "tests" / "test_smoke.py").unlink()
    (repo / "backend" / "tests" / "test_infra.py").write_text(
        "def test_fail_0():\n    assert False\n"
        "\ndef test_fail_1():\n    assert False\n"
        "\ndef test_pass():\n    assert True\n"
    )
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "suite: small failing")

    plan = write_plan(repo, PLAN)
    run_cli(repo, "plan", "register", plan)
    run_cli(repo, "run", "start", "--plan", plan)

    rows = ledger.all(
        "SELECT detail FROM integrity_event WHERE kind = 'baseline_standing_delta'"
    )
    assert len(rows) == 1
    delta = json.loads(rows[0]["detail"])
    assert len(delta["new"]) == 2
    assert len(delta["inherited"]) == 0
