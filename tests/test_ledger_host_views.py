"""One history per host: the operator reads every source's runs in one place.

Guests only ever see their own source. On the host, `tdd ledger metrics|fleet|log`
ask the ledger service, which reads every repository's ledger across all sources.
"""

from __future__ import annotations

import pytest

from conftest import guest_config, run_cli, run_cli_text, write_plan
from tddcli import gitutil
from tddcli import ledger as ledger_mod

MINIMAL_PLAN = """\
---
cycles:
  - n: 1
    project: backend
    title: "placeholder"
    test: "tests/test_smoke.py::test_smoke"
    commit_red: "test: placeholder"
    commit_green: "feat: placeholder"
---
# Minimal plan for host view tests
"""


@pytest.fixture
def two_sources(repo, split_guest, ledger_service):
    """A run as `vm-1`, then one in the same repository as `vm-2`: {source: run id}."""
    ledger_service.service.add_source("vm-2", ledger_service.dir / "vm-2.sock", executor=None)
    plan = write_plan(repo, MINIMAL_PLAN)
    runs = {}
    for source in ("vm-1", "vm-2"):
        guest_config(split_guest.runner, ledger_service.dir / f"{source}.sock")
        run_cli(repo, "plan", "register", plan)
        runs[source] = run_cli(repo, "run", "start", "--plan", plan)["run"]["id"]
    return runs


def slug(repo) -> str:
    return ledger_mod.slug(gitutil.repo_identity(repo))


def test_ledger_metrics_covers_every_source(repo, two_sources):
    out = run_cli(repo, "ledger", "metrics")

    runs = (out["result"].get("repos") or {}).get(slug(repo), {}).get("runs", [])
    assert sorted(r["source"] for r in runs) == ["vm-1", "vm-2"]


def test_ledger_fleet_lists_active_runs_of_every_source(repo, two_sources):
    out = run_cli(repo, "ledger", "fleet")

    runs = out["result"].get("runs") or []
    assert sorted((r["source"], r["run_id"]) for r in runs) == sorted(two_sources.items())


def test_ledger_log_renders_any_sources_run(repo, two_sources):
    run_id = two_sources["vm-2"]

    text = run_cli_text(repo, "ledger", "log", "--repo", slug(repo), "--run", str(run_id))
    # `render.friction_log` heads a run's log with its plan, then `- Run: <id>`.
    assert ("tasks/plan.md" in text, f"- Run: {run_id}\n" in text) == (True, True)


def single_user_ledger(repo, ledger_home):
    """A ledger with one run, from a machine with no ledger service: all of it `local`."""
    plan = write_plan(repo, MINIMAL_PLAN)
    run_cli(repo, "plan", "register", plan)
    run_cli(repo, "run", "start", "--plan", plan)
    (path,) = ledger_home.glob("*.sqlite3")
    return path


def test_ledger_import_retags_a_ledger_as_one_source(repo, ledger_home, ledger_service):
    legacy = single_user_ledger(repo, ledger_home)

    run_cli(repo, "ledger", "import", str(legacy), "--source", "legacy")
    host = ledger_mod.open_readonly(ledger_service.home / legacy.name, source=None)
    assert host is not None and [r["source"] for r in host.runs_in(None)] == ["legacy"]


def test_ledger_import_refuses_an_existing_host_ledger(repo, ledger_home, ledger_service):
    legacy = single_user_ledger(repo, ledger_home)
    run_cli(repo, "ledger", "import", str(legacy), "--source", "legacy")

    again = run_cli(repo, "ledger", "import", str(legacy), "--source", "legacy")
    assert again["result"].get("reason") == "ledger_exists"
