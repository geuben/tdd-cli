"""Scoped annotation keys (#76): a declared check required only on the cycles it applies to."""

from __future__ import annotations

import json

from conftest import run_cli, write_plan
from tddcli import gitutil
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
