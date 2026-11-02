"""A RED taken on a dirty tree names the paths its commit left out (issue #234).

RED's verdict runs on the working tree, but its commit holds only tests and stubs.
`red_on_dirty_tree` names the changed paths the commit left out, so an auditor can
tell the verdict was taken on a tree that differs from the RED commit.
"""

from __future__ import annotations

import json

from conftest import git, run_cli, write_plan
from tddcli import gitutil
from tddcli.ledger import Ledger

PLAN = """---
ancillary_files: ["docs/companion.md"]
cycles:
  - n: 1
    project: backend
    title: "adding two numbers"
    test: "tests/test_add.py::test_add_two_numbers"
    stub_expected: ["app/calc.py"]
  - n: 2
    project: backend
    title: "subtracting two numbers"
    test: "tests/test_sub.py::test_subtract_two_numbers"
    stub_expected: ["app/sub.py"]
---

# Plan
"""

TEST_ADD = """from app.calc import add


def test_add_two_numbers():
    assert add(2, 3) == 5
"""

TEST_SUB = """from app.sub import sub


def test_subtract_two_numbers():
    assert sub(5, 3) == 2
"""


def test_a_red_on_a_dirty_tree_names_the_paths_its_commit_left_out(repo):
    """Implementation, outside and ancillary paths are named; ignored ones are not."""
    lock = repo / ".gradle" / "8.0" / "checksums.lock"
    lock.parent.mkdir(parents=True)
    lock.write_text("v1\n")
    with (repo / ".gitignore").open("a") as f:
        f.write(".gradle/\n")
    git(repo, "add", ".gitignore")
    git(repo, "add", "-f", ".gradle/8.0/checksums.lock")
    git(repo, "commit", "-q", "-m", "a tracked file the ignore rules match")

    plan = write_plan(repo, PLAN)
    assert run_cli(repo, "plan", "register", plan)["ok"]
    assert run_cli(repo, "run", "start", "--plan", plan)["ok"]

    # Cycle 1, clean: no event.
    (repo / "backend" / "tests" / "test_add.py").write_text(TEST_ADD)
    (repo / "backend" / "app" / "calc.py").write_text(
        "def add(a, b):\n    raise NotImplementedError\n"
    )
    run_cli(repo, "advance")
    (repo / "backend" / "app" / "calc.py").write_text("def add(a, b):\n    return a + b\n")
    run_cli(repo, "advance")
    run_cli(repo, "advance")

    # Cycle 2's RED, on a tree carrying more than its commit will.
    (repo / "backend" / "tests" / "test_sub.py").write_text(TEST_SUB)
    (repo / "backend" / "app" / "sub.py").write_text(
        "def sub(a, b):\n    raise NotImplementedError\n"
    )
    (repo / "backend" / "app" / "helper.py").write_text("X = 1\n")
    (repo / "notes.md").write_text("scratch notes\n")
    (repo / "docs").mkdir(exist_ok=True)
    (repo / "docs" / "companion.md").write_text("c\n")
    lock.write_text("v2\n")
    run_cli(repo, "advance")

    run_id = run_cli(repo, "metrics")["result"]["runs"][0]["run"]
    ledger = Ledger(gitutil.repo_identity(repo))

    assert [json.loads(d) for d in ledger.event_details(run_id, "red_on_dirty_tree")] == [
        ["backend/app/helper.py", "docs/companion.md", "notes.md"]
    ]
