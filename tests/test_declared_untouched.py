"""A declared file no commit of the run touched is reported (#232).

The friction log already reports `undeclared_file_touched`: files a run changed
that the plan did not declare. These tests cover the reverse. When the last
cycle closes, by `tdd advance` or by a final `tdd cycle skip`, every declared
path (`files`, `stub_expected`, `ancillary_files`) that no commit since
`run start` touched is recorded in one run-level `declared_file_untouched`
event, named in the `complete` reply and rendered in the friction log.
"""

from __future__ import annotations

import json
import shutil

from conftest import run_cli, write_plan
from tddcli import gitutil
from tddcli.ledger import Ledger

TEST_ADD = "from app.calc import add\n\n\ndef test_add_two_numbers():\n    assert add(2, 3) == 5\n"
STUB_ADD = "def add(a, b):\n    raise NotImplementedError\n"
REAL_ADD = "def add(a, b):\n    return a + b\n"


def _add_cycle(n: int, stub: str, files: list[str]) -> str:
    return (
        f"  - n: {n}\n"
        "    project: backend\n"
        '    title: "adding two numbers"\n'
        '    test: "tests/test_add.py::test_add_two_numbers"\n'
        f"    stub_expected: [{json.dumps(stub)}]\n"
        f"    files: {json.dumps(files)}\n"
    )


def _sub_cycle(files: list[str]) -> str:
    return (
        "  - n: 2\n"
        "    project: backend\n"
        '    title: "subtracting two numbers"\n'
        '    test: "tests/test_sub.py::test_subtract_two_numbers"\n'
        f"    files: {json.dumps(files)}\n"
    )


def _plan(*cycles: str, ancillary: list[str] | None = None) -> str:
    body = "---\ncycles:\n" + "".join(cycles)
    if ancillary is not None:
        body += f"ancillary_files: {json.dumps(ancillary)}\n"
    return body + "---\n\n# Plan\n"


_ADD = _add_cycle(1, "backend/app/calc.py", ["backend/app/calc.py"])
_NEVER_ADD = _add_cycle(1, "backend/app/calc.py", ["backend/app/calc.py", "backend/app/never.py"])

ONE = _plan(_ADD)
ONE_THEN_SUB = _plan(_ADD, _sub_cycle([]))
NEVER_ONE = _plan(_NEVER_ADD)
NEVER_ANCILLARY = _plan(_NEVER_ADD, ancillary=["docs/never.md"])
NEVER_THEN_SUB = _plan(_NEVER_ADD, _sub_cycle(["backend/app/sub.py"]))
BY_HAND = _plan(
    _add_cycle(
        1,
        "backend/app/calc.py",
        ["backend/app/calc.py", "backend/app/by_hand.py", "backend/app/never.py"],
    ),
    ancillary=["docs/never.md"],
)
EXCLUSIONS = (
    "---\n"
    "cycles:\n"
    "  - n: 1\n"
    "    project: backend\n"
    '    title: "a cycle that does not apply"\n'
    '    test: "tests/test_mul.py::test_multiply"\n'
    '    files: ["backend/app/skipped_only.py"]\n'
    "  - n: 2\n"
    "    project: backend\n"
    '    title: "adding two numbers"\n'
    '    test: "tests/test_add.py::test_add_two_numbers"\n'
    '    stub_expected: ["app/calc.py"]\n'
    '    files: ["app/calc.py", "backend/app/old.py", "backend/app/gone.py",'
    ' "backend/generated/out.txt", "backend/app/never.py"]\n'
    "---\n"
    "\n"
    "# Plan\n"
)

ADVANCE_DONE = (
    "All declared cycles are complete."
    ' Before rendering, record a closing narrative with `tdd note "<hardest cycle and why,'
    ' plan inaccuracies, deviations>"`. Then run `tdd log render`.'
)
SKIP_DONE = (
    "Final cycle skipped; run complete."
    ' Before rendering, record a closing narrative with `tdd note "<hardest cycle and why,'
    ' plan inaccuracies, deviations>"`. Then run `tdd log render`.'
)
UNTOUCHED = " Declared but untouched by any commit of this run: {}. A plan may over-declare: say in the closing note why each was not needed."  # noqa: E501


def _start(repo, body: str) -> int:
    plan = write_plan(repo, body)
    assert run_cli(repo, "plan", "register", plan)["ok"]
    out = run_cli(repo, "run", "start", "--plan", plan)
    assert out["ok"]
    return out["run"]["id"]


def _deliver_add(repo, during_green=None, before_close=None) -> dict:
    (repo / "backend/tests/test_add.py").write_text(TEST_ADD)
    (repo / "backend/app/calc.py").write_text(STUB_ADD)
    run_cli(repo, "advance")
    if during_green:
        during_green(repo)
    (repo / "backend/app/calc.py").write_text(REAL_ADD)
    run_cli(repo, "advance")
    if before_close:
        before_close(repo)
    return run_cli(repo, "advance")


def _untouched(repo) -> list:
    rows = Ledger(gitutil.repo_identity(repo)).all(
        "SELECT cycle_id, detail FROM integrity_event"
        " WHERE kind = 'declared_file_untouched' ORDER BY id"
    )
    return [(r["cycle_id"], json.loads(r["detail"])) for r in rows]


def _both_endings(repo, tmp_path, before_end=None) -> dict[str, dict]:
    copies = {}
    for ending in ("advance", "skip"):
        copies[ending] = tmp_path / ending
        shutil.copytree(repo, copies[ending], symlinks=True)
    out: dict[str, dict] = {}

    copy = copies["advance"]
    run_id = _start(copy, ONE)
    out["advance"] = _deliver_add(
        copy, before_close=(lambda r: before_end(r, run_id)) if before_end else None
    )

    copy = copies["skip"]
    run_id = _start(copy, ONE_THEN_SUB)
    _deliver_add(copy)
    if before_end:
        before_end(copy, run_id)
    out["skip"] = run_cli(copy, "cycle", "skip", "--reason", "not needed")
    return out


def test_a_run_that_committed_every_declared_path_records_no_untouched_event(repo, tmp_path):
    _both_endings(repo, tmp_path)
    assert {e: _untouched(tmp_path / e) for e in ("advance", "skip")} == {
        "advance": [],
        "skip": [],
    }


def test_the_complete_reply_is_unchanged_when_every_declared_path_was_committed(repo, tmp_path):
    out = _both_endings(repo, tmp_path)
    assert {e: o["next_action"]["detail"] for e, o in out.items()} == {
        "advance": ADVANCE_DONE,
        "skip": SKIP_DONE,
    }
