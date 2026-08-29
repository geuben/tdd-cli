"""Executor-narrative channel: tdd note command and rendering (issue #77)."""

from __future__ import annotations

from conftest import git, run_cli, write_plan
from tddcli import gitutil
from tddcli.ledger import Ledger

PLAN = """---
cycles:
  - n: 1
    project: backend
    title: "adding two numbers"
    test: "tests/test_add.py::test_add_two_numbers"
    commit_red: "test: add"
    commit_green: "feat: add()"
---

# Plan
"""

TEST_ADD = """from app.calc import add


def test_add_two_numbers():
    assert add(2, 3) == 5
"""

CALC_WORKING = "def add(a, b):\n    return a + b\n"
CALC_MUTATED = "def add(a, b):\n    return 0\n"


def _start(repo):
    (repo / "backend" / "app" / "calc.py").write_text(CALC_WORKING)
    (repo / "backend" / "tests" / "test_add.py").write_text(TEST_ADD)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "add calc.py and test")
    plan = write_plan(repo, PLAN)
    reg = run_cli(repo, "plan", "register", plan)
    assert reg["ok"], reg
    started = run_cli(repo, "run", "start", "--plan", plan)
    assert started["ok"], started
    return started


def test_note_attaches_to_the_open_cycle_with_its_phase(repo):
    started = _start(repo)
    run_id = started["run"]["id"]

    out = run_cli(repo, "note", "the fixture assumption was wrong")
    assert out["ok"], out

    led = Ledger(gitutil.repo_identity(repo))
    rows = led.all("SELECT * FROM note ORDER BY id")
    assert len(rows) == 1
    row = rows[0]
    assert row["run_id"] == run_id
    assert row["cycle_id"] is not None
    assert row["phase"] == "AWAITING_TEST"
    assert row["text"] == "the fixture assumption was wrong"


def test_v7_ledger_is_upgraded_in_place_to_v8(ledger_home, tmp_path):
    led = Ledger(tmp_path / "somerepo")
    led.db.execute("UPDATE meta SET value='7' WHERE key='schema_version'")
    led.db.execute("DROP TABLE note")
    led.db.commit()
    led.db.close()

    led2 = Ledger(tmp_path / "somerepo")
    rows = led2.all("SELECT * FROM note")
    assert rows == []
    version = led2.one("SELECT value FROM meta WHERE key='schema_version'")
    assert version["value"] == "8"


def test_note_after_run_end_is_run_level_on_the_latest_run(repo):
    started = _start(repo)
    run_id = started["run"]["id"]

    skipped = run_cli(repo, "cycle", "skip", "--reason", "probe")
    assert skipped["next_action"]["terminal"] is True

    out = run_cli(repo, "note", "closing narrative")
    assert out["ok"], out

    led = Ledger(gitutil.repo_identity(repo))
    rows = led.all("SELECT * FROM note WHERE run_id = ?", (run_id,))
    assert len(rows) == 1
    row = rows[0]
    assert row["cycle_id"] is None


def test_cycle_notes_render_as_blockquotes_in_their_cycle(repo, tmp_path):
    started = _start(repo)
    run_id = started["run"]["id"]

    led = Ledger(gitutil.repo_identity(repo))
    cycle = led.open_cycle(run_id)
    led.insert(
        "note",
        run_id=run_id,
        cycle_id=cycle["id"],
        phase="AWAITING_TEST",
        text="the plan's route name was stale",
        at=led.one("SELECT datetime('now')")[0],
    )

    out_path = tmp_path / "friction.md"
    result = run_cli(repo, "log", "render", "--out", str(out_path))
    assert result["ok"], result
    content = out_path.read_text()
    assert "> **note** _(during AWAITING_TEST)_: the plan's route name was stale" in content


def test_run_level_notes_render_in_the_executor_narrative_section(repo, tmp_path):
    started = _start(repo)
    run_id = started["run"]["id"]

    led = Ledger(gitutil.repo_identity(repo))
    led.insert(
        "note",
        run_id=run_id,
        cycle_id=None,
        phase=None,
        text="hardest part was the fixture",
        at=led.one("SELECT datetime('now')")[0],
    )

    out_path = tmp_path / "friction.md"
    result = run_cli(repo, "log", "render", "--out", str(out_path))
    assert result["ok"], result
    content = out_path.read_text()
    assert "## Executor narrative" in content
    assert "_Claims from the executor, unverified by design._" in content
    assert "> hardest part was the fixture" in content


def test_no_narrative_section_without_run_level_notes(repo, tmp_path):
    _start(repo)

    out_path = tmp_path / "friction.md"
    result = run_cli(repo, "log", "render", "--out", str(out_path))
    assert result["ok"], result
    content = out_path.read_text()
    assert "Executor narrative" not in content


def test_integrity_event_envelope_nudges_for_a_note(repo):
    (repo / "backend" / "app" / "calc.py").write_text(CALC_WORKING)
    (repo / "backend" / "tests" / "test_add.py").write_text(TEST_ADD)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "add calc.py and test")
    plan = write_plan(repo, PLAN)
    reg = run_cli(repo, "plan", "register", plan)
    assert reg["ok"], reg
    run_cli(repo, "run", "start", "--plan", plan)

    out = run_cli(repo, "advance")
    assert out["run"]["phase"] == "SENSITIVITY_REQUIRED", out
    assert "tdd note" in out["next_action"]["detail"]
