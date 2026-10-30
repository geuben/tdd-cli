"""Paths git's ignore rules match are build output, tracked or not.

Issue #98: a tracked `.gradle/` a build rewrote was staged (crashing GREEN's commit),
flagged `undeclared_file_touched` on every cycle, and held by the run-close gate.
"""

from __future__ import annotations

from conftest import git, run_cli, write_plan

ONE = """---
cycles:
  - n: 1
    project: backend
    title: "adding two numbers"
    test: "tests/test_add.py::test_add_two_numbers"
    stub_expected: ["app/calc.py"]
---

# Plan
"""


def _track_ignored(repo, rel):
    """Commit `rel` under a `.gradle/` ignore line, as `git add -f` would leave it."""
    path = repo / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("v1\n")
    with (repo / ".gitignore").open("a") as f:
        f.write(".gradle/\n")
    git(repo, "add", ".gitignore")
    git(repo, "add", "-f", rel)
    git(repo, "commit", "-q", "-m", "a tracked file the ignore rules match")


def _start(repo, body):
    plan = write_plan(repo, body)
    assert run_cli(repo, "plan", "register", plan)["ok"]
    assert run_cli(repo, "run", "start", "--plan", plan)["ok"]


def _drive_one_cycle(repo, rel, content):
    """Drive the `add` cycle, writing `content` to `rel` during GREEN."""
    (repo / "backend" / "tests" / "test_add.py").write_text(
        "from app.calc import add\n\n\ndef test_add_two_numbers():\n    assert add(2, 3) == 5\n"
    )
    (repo / "backend" / "app" / "calc.py").write_text(
        "def add(a, b):\n    raise NotImplementedError\n"
    )
    red = run_cli(repo, "advance")
    (repo / rel).write_text(content)
    (repo / "backend" / "app" / "calc.py").write_text("def add(a, b):\n    return a + b\n")
    green = run_cli(repo, "advance")
    close = run_cli(repo, "advance")
    return red, green, close


def test_a_tracked_ignored_path_inside_the_cycle_project_is_left_out_of_the_green_commit(repo):
    rel = "backend/.gradle/8.0/checksums.lock"
    _track_ignored(repo, rel)
    _start(repo, ONE)

    red, green, _ = _drive_one_cycle(repo, rel, "v2\n")

    assert green["result"].get("staged") == ["backend/app/calc.py"]


def test_a_tracked_ignored_path_outside_the_cycle_project_fires_no_undeclared_event(repo):
    rel = ".gradle/8.0/checksums.lock"
    _track_ignored(repo, rel)
    _start(repo, ONE)

    _drive_one_cycle(repo, rel, "v2\n")

    events = run_cli(repo, "metrics")["result"]["runs"][0]["integrity_events"]
    assert events.get("undeclared_file_touched", 0) == 0


def test_a_tracked_ignored_path_left_dirty_does_not_block_run_close(repo):
    rel = ".gradle/8.0/checksums.lock"
    _track_ignored(repo, rel)
    _start(repo, ONE)

    _, _, close = _drive_one_cycle(repo, rel, "v2\n")

    assert close["next_action"]["verb"] == "complete"
