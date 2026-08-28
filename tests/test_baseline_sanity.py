"""Baseline sanity gates: refuse implausible baselines, surface standing failures,
and probe live-service reachability before capture.
"""

from __future__ import annotations

from conftest import git, run_cli, write_plan

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
