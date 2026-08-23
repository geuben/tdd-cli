"""A baseline is subtracted from every later failure set (R9.2). An empty one that
merely *looks* clean turns every pre-existing failure into a permanent regression.
"""

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
    stub_expected: ["app/calc.py"]
    commit_red: "test: adding two numbers"
    commit_green: "feat: add()"
---

# Plan
"""


TEST_ADD = """from app.calc import add


def test_add_two_numbers():
    assert add(2, 3) == 5
"""


def reach_refactor(repo):
    plan = write_plan(repo, PLAN)
    run_cli(repo, "plan", "register", plan)
    assert run_cli(repo, "run", "start", "--plan", plan)["ok"]
    (repo / "backend" / "tests" / "test_add.py").write_text(TEST_ADD)
    (repo / "backend" / "app" / "calc.py").write_text(
        "def add(a, b):\n    raise NotImplementedError\n"
    )
    run_cli(repo, "advance")
    (repo / "backend" / "app" / "calc.py").write_text("def add(a, b):\n    return a + b\n")
    out = run_cli(repo, "advance")
    assert out["run"]["phase"] == "AWAITING_REFACTOR", out


def set_test_command(repo, command: str) -> None:
    toml = (repo / "tdd.toml").read_text()
    (repo / "tdd.toml").write_text(toml + f'test_command = "{command}"\n')
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "tdd.toml")


def test_run_start_refuses_when_nothing_could_be_collected(repo):
    """The motivating failure: node_modules were absent, so every frontend test file
    failed to collect, the baseline recorded no failures, and a real pre-existing
    failure was then read as a regression at every close sweep."""
    (repo / "backend" / "tests" / "test_smoke.py").write_text(
        "import a_module_that_does_not_exist\n"
    )
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "break collection")

    plan = write_plan(repo, PLAN)
    run_cli(repo, "plan", "register", plan)
    out = run_cli(repo, "run", "start", "--plan", plan)

    assert out["ok"] is False, out
    assert "backend" in out["error"]
    assert "collect" in out["error"]


def test_run_start_refuses_a_baseline_that_ran_no_tests(repo):
    """Collection found tests, so the suite exists; the runner executed none of them.
    Whatever the cause, nothing was observed and the baseline asserts nothing."""
    set_test_command(repo, "python -m pytest tests/ -k __matches_nothing__")

    plan = write_plan(repo, PLAN)
    run_cli(repo, "plan", "register", plan)
    out = run_cli(repo, "run", "start", "--plan", plan)

    assert out["ok"] is False, out
    assert "backend" in out["error"]
    assert "no tests" in out["error"]


def test_a_project_with_no_tests_at_all_is_not_an_error(repo):
    """Nothing collected and nothing failing to collect: the project simply has no
    suite yet. That is a fact about the project, not a broken environment."""
    (repo / "backend" / "tests" / "test_smoke.py").unlink()
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "no tests")

    plan = write_plan(repo, PLAN)
    run_cli(repo, "plan", "register", plan)
    out = run_cli(repo, "run", "start", "--plan", plan)

    assert out["ok"], out
    assert out["result"]["baselines"]["backend"] == 0


def test_blocker_accepts_no_baseline_for_project_kind(repo):
    reach_refactor(repo)
    out = run_cli(repo, "blocker", "--kind", "no_baseline_for_project", "--detail", "svc has no baseline")
    assert out["ok"], out
    assert out["result"]["kind"] == "no_baseline_for_project"


def test_a_failure_the_baseline_missed_has_its_own_blocker_kind(repo):
    """Filing it as `regression` is the only option today, which mislabels the run's
    integrity record as a defect the agent caused."""
    reach_refactor(repo)
    (repo / "backend" / "tests" / "test_smoke.py").write_text(
        "def test_smoke():\n    assert False\n"
    )
    assert run_cli(repo, "advance")["next_action"]["verb"] == "fix_regression"

    out = run_cli(repo, "blocker", "--kind", "pre_existing_failure", "--detail", "flaky")
    assert out["ok"], out
    assert out["result"]["kind"] == "pre_existing_failure"


def test_unblocking_can_accept_the_failures_into_the_baseline(repo):
    """Without this the run cannot recover: unblock returns to AWAITING_REFACTOR, the
    next advance re-runs the same sweep, finds the same failure, and blocks again."""
    reach_refactor(repo)
    (repo / "backend" / "tests" / "test_smoke.py").write_text(
        "def test_smoke():\n    assert False\n"
    )
    run_cli(repo, "advance")
    run_cli(repo, "blocker", "--kind", "pre_existing_failure", "--detail", "flaky")

    resumed = run_cli(
        repo, "resume", "--unblock", "--note", "verified against main", "--accept-failures"
    )
    assert resumed["ok"], resumed
    accepted = resumed["result"]["accepted_into_baseline"]
    assert accepted == {"backend": ["backend::tests/test_smoke.py::test_smoke"]}, resumed

    closed = run_cli(repo, "advance")
    assert closed["next_action"]["verb"] == "complete", closed


def test_unblocking_without_accept_failures_leaves_the_baseline_alone(repo):
    """The escape hatch is explicit, or every unblock quietly launders a regression."""
    reach_refactor(repo)
    (repo / "backend" / "tests" / "test_smoke.py").write_text(
        "def test_smoke():\n    assert False\n"
    )
    run_cli(repo, "advance")
    run_cli(repo, "blocker", "--kind", "pre_existing_failure", "--detail", "flaky")

    resumed = run_cli(repo, "resume", "--unblock", "--note", "looking into it")
    assert resumed["ok"], resumed
    assert "accepted_into_baseline" not in resumed["result"]
    assert run_cli(repo, "advance")["next_action"]["verb"] == "fix_regression"


THREE_PROJECT_PLAN = """---
cycles:
  - n: 1
    project: backend
    title: "adding two numbers"
    test: "tests/test_add.py::test_add_two_numbers"
    stub_expected: ["app/calc.py"]
    commit_red: "test: adding two numbers"
    commit_green: "feat: add()"
---

# Plan
"""


def test_run_start_probes_only_reachable_projects(repo_three):
    plan = write_plan(repo_three, THREE_PROJECT_PLAN)
    run_cli(repo_three, "plan", "register", plan)
    out = run_cli(repo_three, "run", "start", "--plan", plan)
    assert out["ok"], out

    # only backend (declared) and svc (consumed_by via schema artifact) are probed
    assert out["result"]["baselines"] == {"backend": 0, "svc": 0}, out["result"]["baselines"]

    ledger = Ledger(gitutil.repo_identity(repo_three))
    run_id = out["run"]["id"]
    rows = ledger.all("SELECT project FROM baseline WHERE run_id = ?", (run_id,))
    probed = {r["project"] for r in rows}
    assert probed == {"backend", "svc"}, probed


def test_run_start_baseline_all_probes_every_project(repo_three):
    plan = write_plan(repo_three, THREE_PROJECT_PLAN)
    run_cli(repo_three, "plan", "register", plan)
    out = run_cli(repo_three, "run", "start", "--plan", plan, "--baseline-all")
    assert out["ok"], out
    assert out["result"]["baselines"] == {"backend": 0, "other": 0, "svc": 0}, out["result"]["baselines"]
    run_id = out["run"]["id"]
    ledger = Ledger(gitutil.repo_identity(repo_three))
    event = ledger.one(
        "SELECT detail FROM integrity_event WHERE run_id = ? AND kind = 'baseline_scoped'",
        (run_id,),
    )
    assert event is None, "baseline_scoped event must not exist when --baseline-all is used"


def test_run_start_records_baseline_scoped_event(repo_three):
    plan = write_plan(repo_three, THREE_PROJECT_PLAN)
    run_cli(repo_three, "plan", "register", plan)
    out = run_cli(repo_three, "run", "start", "--plan", plan)
    assert out["ok"], out

    run_id = out["run"]["id"]
    ledger = Ledger(gitutil.repo_identity(repo_three))
    event = ledger.one(
        "SELECT detail FROM integrity_event WHERE run_id = ? AND kind = 'baseline_scoped'",
        (run_id,),
    )
    assert event is not None, "no baseline_scoped event found"
    import json as json_mod
    skipped = json_mod.loads(event["detail"])
    assert skipped == ["other"], skipped


BACKEND_ONLY_PLAN = """---
cycles:
  - n: 1
    project: backend
    title: "adding two numbers"
    test: "tests/test_add.py::test_add_two_numbers"
    stub_expected: ["app/calc.py"]
    commit_red: "test: adding two numbers"
    commit_green: "feat: add()"
---

# Plan
"""


def reach_unbaselined_blocker(repo):
    """Drive the run to a blocked state: svc has unbaselined sweep failures."""
    plan = write_plan(repo, BACKEND_ONLY_PLAN)
    run_cli(repo, "plan", "register", plan)
    out = run_cli(repo, "run", "start", "--plan", plan)
    assert out["ok"], out
    (repo / "backend" / "tests" / "test_add.py").write_text(TEST_ADD)
    (repo / "backend" / "app" / "calc.py").write_text("def add(a, b):\n    raise NotImplementedError\n")
    run_cli(repo, "advance")
    (repo / "backend" / "app" / "calc.py").write_text("def add(a, b):\n    return a + b\n")
    (repo / "other" / "generated.json").write_text("{}")
    run_cli(repo, "advance")
    out = run_cli(repo, "advance")
    assert out["next_action"]["verb"] == "resolve_blocker", out
    return out


def test_close_sweep_with_unbaselined_failures_directs_resolve_blocker(repo_schema_other):
    out = reach_unbaselined_blocker(repo_schema_other)
    detail = out["next_action"]["detail"]
    assert "no_baseline_for_project" in detail, detail
    assert "resume --unblock --accept-failures" in detail, detail


def test_accept_failures_inserts_baseline_row_for_unbaselined_project(repo_schema_other):
    import json as json_mod
    reach_unbaselined_blocker(repo_schema_other)
    run_cli(repo_schema_other, "blocker", "--kind", "no_baseline_for_project", "--detail", "svc uncovered")
    resumed = run_cli(repo_schema_other, "resume", "--unblock", "--note", "fold svc", "--accept-failures")
    assert resumed["ok"], resumed

    ledger = Ledger(gitutil.repo_identity(repo_schema_other))
    run_id = resumed["run"]["id"]
    row = ledger.one("SELECT failing FROM baseline WHERE run_id = ? AND project = 'svc'", (run_id,))
    assert row is not None, "no baseline row created for svc"
    failing = json_mod.loads(row["failing"])
    assert any("test_svc_fails" in f for f in failing), failing

    event = ledger.one(
        "SELECT detail FROM integrity_event WHERE run_id = ? AND kind = 'baseline_amended'",
        (run_id,),
    )
    assert event is not None, "no baseline_amended event"
    amended = json_mod.loads(event["detail"])
    assert "svc" in amended, amended


def test_sweep_reports_unbaselined_failures_separately(repo_three):
    from tddcli import config as config_mod
    from tddcli.machine import Engine

    # svc has a pre-committed failing test
    (repo_three / "svc" / "tests" / "test_smoke.py").write_text(
        "def test_smoke():\n    assert False\n"
    )
    git(repo_three, "add", "-A")
    git(repo_three, "commit", "-q", "-m", "svc: failing smoke test")

    plan = write_plan(repo_three, THREE_PROJECT_PLAN)
    run_cli(repo_three, "plan", "register", plan)
    out = run_cli(repo_three, "run", "start", "--plan", plan)
    assert out["ok"], out

    run_id = out["run"]["id"]
    ledger = Ledger(gitutil.repo_identity(repo_three))
    # Delete svc's baseline to simulate an un-baselined project
    ledger.db.execute("DELETE FROM baseline WHERE run_id = ? AND project = 'svc'", (run_id,))
    ledger.db.commit()

    run_row = ledger.one("SELECT * FROM run WHERE id = ?", (run_id,))
    cycle_row = ledger.one("SELECT * FROM cycle WHERE run_id = ? ORDER BY id ASC LIMIT 1", (run_id,))
    cfg = config_mod.load(repo_three)
    engine = Engine(ledger, cfg, repo_three, run_row)

    # Touch backend/schema.json so artifact edge pulls svc into the sweep
    touched = {"backend/schema.json"}
    outcome = engine.sweep(cycle_row, touched)

    assert "svc" in outcome.unbaselined, outcome
    svc_failures = outcome.unbaselined["svc"]
    assert any("test_smoke" in f for f in svc_failures), svc_failures
    assert not outcome.failures, outcome.failures
    assert not outcome.ok


def test_reuse_baselines_populates_cache_and_default_does_not(repo_three):
    plan = write_plan(repo_three, THREE_PROJECT_PLAN)
    run_cli(repo_three, "plan", "register", plan)

    # plain run: cache stays empty
    out = run_cli(repo_three, "run", "start", "--plan", plan)
    assert out["ok"], out
    ledger = Ledger(gitutil.repo_identity(repo_three))
    assert ledger.one("SELECT COUNT(*) as n FROM baseline_cache")["n"] == 0

    # close the first run so a second run start is allowed
    from tddcli.ledger import now as ledger_now
    ledger.db.execute(
        "UPDATE run SET ended_at = ?, outcome = 'abandoned' WHERE ended_at IS NULL",
        (ledger_now(),),
    )
    ledger.db.commit()

    # with flag: populates cache for each probed project
    out2 = run_cli(repo_three, "run", "start", "--plan", plan, "--reuse-baselines", "--allow-dirty")
    assert out2["ok"], out2
    rows = ledger.all("SELECT project FROM baseline_cache")
    assert {r["project"] for r in rows} == {"backend", "svc"}
