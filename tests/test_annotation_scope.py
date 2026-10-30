"""Scoped annotation keys (#76): a declared check required only on the cycles it applies to."""

from __future__ import annotations

import json

from conftest import run_cli, write_plan
from tddcli import gitutil
from tddcli.contract import parse
from tddcli.ledger import Ledger

TWO_REFACTOR = """---
cycles:
  - n: 1
    project: backend
    refactor_cycle: true
    title: "one"
  - n: 2
    project: backend
    refactor_cycle: true
    title: "two"
annotation_keys: KEYS
---
"""


def _plan(keys: str) -> str:
    return TWO_REFACTOR.replace("KEYS", keys)


def test_a_contract_stored_before_scoping_still_requires_every_key_at_close(repo):
    plan = write_plan(repo, _plan('["k"]'))
    run_cli(repo, "plan", "register", plan)
    ledger = Ledger(gitutil.repo_identity(repo))
    row = ledger.one("SELECT id, declared_cycles FROM plan_contract")
    cycles = json.loads(row["declared_cycles"])
    for c in cycles:
        c.pop("annotation_keys", None)
    ledger.db.execute(
        "UPDATE plan_contract SET declared_cycles = ? WHERE id = ?",
        (json.dumps(cycles), row["id"]),
    )
    ledger.db.commit()
    run_cli(repo, "run", "start", "--plan", plan)

    (repo / "backend" / "app" / "moved.py").write_text("VALUE = 1\n")
    out = run_cli(repo, "advance")
    assert (out["next_action"]["verb"], out["result"]["missing_annotations"]) == (
        "annotate_cycle",
        ["k"],
    )


RESOLVED = """---
cycles:
  - n: 1
    project: backend
    refactor_cycle: true
  - n: 2
    project: frontend
    refactor_cycle: true
  - n: 3
    projects: [backend, frontend]
    contract_cycle: true
    tests: ["backend::tests/test_a.py::test_a", "frontend::a.test.ts > a"]
annotation_keys:
  - plan_wide
  - {name: a, applies_to: [2, 3]}
  - {name: b, applies_to: 1}
  - {name: f, projects: frontend}
  - {name: g, projects: [backend]}
---
"""


def test_annotation_keys_resolve_onto_the_cycles_they_apply_to():
    contract = parse(RESOLVED, "p.md")
    assert (contract.annotation_keys, [c.annotation_keys for c in contract.cycles]) == (
        ["plan_wide", "a", "b", "f", "g"],
        [["plan_wide", "b", "g"], ["plan_wide", "a", "f"], ["plan_wide", "a", "f", "g"]],
    )


def test_a_scoped_key_is_required_only_on_the_cycles_it_applies_to(repo):
    plan = write_plan(repo, _plan('["plan_wide", {name: k, applies_to: [2]}]'))
    run_cli(repo, "plan", "register", plan)
    run_cli(repo, "run", "start", "--plan", plan)
    (repo / "backend" / "app" / "moved.py").write_text("VALUE = 1\n")

    first = run_cli(repo, "advance")
    run_cli(repo, "annotate", "--key", "plan_wide", "--value", "x")
    closed = run_cli(repo, "advance")
    second = run_cli(repo, "advance")
    assert (
        first["result"]["missing_annotations"],
        closed["run"]["cycle"],
        second["result"]["missing_annotations"],
    ) == (["plan_wide"], 2, ["plan_wide", "k"])
