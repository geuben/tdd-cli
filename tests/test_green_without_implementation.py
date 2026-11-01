"""A GREEN whose staged set is only test files is flagged, not silently accepted (#235)."""

from __future__ import annotations

import json
import shutil

from conftest import run_cli, run_cli_text, write_plan
from tddcli import gitutil
from tddcli.ledger import Ledger

EXPECTED = "backend/tests/expected/out.txt"

GOLDEN_TEST = """import pathlib


def test_output_matches_golden():
    expected = (pathlib.Path(__file__).parent / "expected" / "out.txt").read_text()
    assert expected == "42\\n"
"""

PLAN_GOLDEN = """---
cycles:
  - n: 1
    project: backend
    title: "output matches the golden file"
    test: "tests/test_golden.py::test_output_matches_golden"
---

# Plan
"""

PLAN_STUB = """---
cycles:
  - n: 1
    project: backend
    title: "adding two numbers"
    test: "tests/test_add.py::test_add_two_numbers"
    stub_expected: ["app/calc.py"]
---

# Plan
"""

PLAN_VALUE = """---
cycles:
  - n: 1
    project: backend
    title: "the package exposes VALUE"
    test: "tests/test_value.py::test_value"
---

# Plan
"""

PLAN_NOTES = """---
cycles:
  - n: 1
    project: backend
    title: "the notes say 42"
    test: "tests/test_notes.py::test_notes"
ancillary_files: ["docs/notes.md"]
---

# Plan
"""

PLAN_FLAKY = """---
cycles:
  - n: 1
    project: backend
    title: "flaky"
    test: "tests/test_flaky.py::test_flaky"
---

# Plan
"""


def _start(repo, plan_text):
    plan = write_plan(repo, plan_text)
    assert run_cli(repo, "plan", "register", plan)["ok"]
    started = run_cli(repo, "run", "start", "--plan", plan)
    assert started["ok"], started
    return started["run"]["id"]


def _advance_to_impl(repo):
    red = run_cli(repo, "advance")
    assert red["next_action"]["verb"] == "write_implementation", red


def _golden_red(repo):
    (repo / "backend" / "tests" / "expected").mkdir(parents=True)
    (repo / EXPECTED).write_text("")
    (repo / "backend" / "tests" / "test_golden.py").write_text(GOLDEN_TEST)
    _advance_to_impl(repo)


def _tests_only(repo, scratch):
    run_id = _start(repo, PLAN_GOLDEN)
    _golden_red(repo)
    (repo / EXPECTED).write_text("42\n")
    return run_id, run_cli(repo, "advance")


def _tests_and_implementation(repo, scratch):
    run_id = _start(repo, PLAN_GOLDEN)
    _golden_red(repo)
    (repo / EXPECTED).write_text("42\n")
    (repo / "backend" / "app" / "__init__.py").write_text("VALUE = 1\n")
    return run_id, run_cli(repo, "advance")


def _stub_filled(repo, scratch):
    run_id = _start(repo, PLAN_STUB)
    (repo / "backend" / "tests" / "test_add.py").write_text(
        "from app.calc import add\n\n\ndef test_add_two_numbers():\n    assert add(2, 3) == 5\n"
    )
    (repo / "backend" / "app" / "calc.py").write_text(
        "def add(a, b):\n    raise NotImplementedError\n"
    )
    _advance_to_impl(repo)
    (repo / "backend" / "app" / "calc.py").write_text("def add(a, b):\n    return a + b\n")
    return run_id, run_cli(repo, "advance")


def _implementation(repo, scratch):
    run_id = _start(repo, PLAN_VALUE)
    (repo / "backend" / "tests" / "test_value.py").write_text(
        'import app\n\n\ndef test_value():\n    assert getattr(app, "VALUE", None) == 1\n'
    )
    _advance_to_impl(repo)
    (repo / "backend" / "app" / "__init__.py").write_text("VALUE = 1\n")
    return run_id, run_cli(repo, "advance")


def _ancillary_only(repo, scratch):
    run_id = _start(repo, PLAN_NOTES)
    (repo / "backend" / "tests" / "test_notes.py").write_text(
        "import pathlib\n\n\n"
        "def test_notes():\n"
        '    notes = pathlib.Path(__file__).parents[2] / "docs" / "notes.md"\n'
        '    text = notes.read_text() if notes.exists() else ""\n'
        '    assert text == "42\\n"\n'
    )
    _advance_to_impl(repo)
    (repo / "docs").mkdir()
    (repo / "docs" / "notes.md").write_text("42\n")
    return run_id, run_cli(repo, "advance")


def _nothing_staged(repo, scratch):
    run_id = _start(repo, PLAN_FLAKY)
    counter = scratch / "flaky-count"
    (repo / "backend" / "tests" / "test_flaky.py").write_text(
        "import pathlib\n\n"
        f"COUNTER = pathlib.Path({str(counter)!r})\n\n\n"
        "def test_flaky():\n"
        "    n = int(COUNTER.read_text()) + 1 if COUNTER.exists() else 1\n"
        "    COUNTER.write_text(str(n))\n"
        "    assert n > 1\n"
    )
    _advance_to_impl(repo)
    return run_id, run_cli(repo, "advance")


CASES = {
    "tests_only": _tests_only,
    "tests_and_implementation": _tests_and_implementation,
    "stub_filled": _stub_filled,
    "implementation": _implementation,
    "ancillary_only": _ancillary_only,
    "nothing_staged": _nothing_staged,
}


def test_green_without_implementation_fires_only_when_every_staged_path_is_a_test(repo, tmp_path):
    seen = {}
    for name, case in CASES.items():
        copy = tmp_path / name
        shutil.copytree(repo, copy, symlinks=True)
        scratch = tmp_path / f"{name}-scratch"
        scratch.mkdir()
        run_id, green = case(copy, scratch)
        details = Ledger(gitutil.repo_identity(copy)).event_details(
            run_id, "green_without_implementation"
        )
        seen[name] = (green["next_action"]["verb"], [json.loads(d) for d in details])
    assert seen == {
        "tests_only": ("refactor_or_advance", [[EXPECTED]]),
        "tests_and_implementation": ("refactor_or_advance", []),
        "stub_filled": ("refactor_or_advance", []),
        "implementation": ("refactor_or_advance", []),
        "ancillary_only": ("refactor_or_advance", []),
        "nothing_staged": ("refactor_or_advance", []),
    }


def test_a_green_of_only_test_files_asks_for_a_note(repo, tmp_path):
    _, green = _tests_only(repo, tmp_path)
    assert "tdd note" in green["next_action"]["detail"]


def test_the_friction_log_shows_green_without_implementation_in_the_cycle_section(repo, tmp_path):
    _tests_only(repo, tmp_path)
    run_cli(repo, "advance")
    text = run_cli_text(repo, "log", "render")
    section = text.split("### Cycle 1", 1)[1].split("\n## ", 1)[0]
    assert f'- **Event — green_without_implementation:** ["{EXPECTED}"]' in section
