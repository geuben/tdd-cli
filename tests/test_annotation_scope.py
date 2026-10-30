"""Scoped annotation keys (#76): a declared check required only on the cycles it applies to."""

from __future__ import annotations

import json
import re

import pytest

from conftest import run_cli, run_cli_text, write_plan
from tddcli import gitutil
from tddcli.contract import ContractError, parse
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


REJECTED: list[tuple[str, str]] = [
    (
        "[{name: k, applies_to: [7]}]",
        "annotation key 'k': applies_to names cycle 7, which the plan does not declare",
    ),
    (
        "[{name: k, projects: [frontend]}]",
        "annotation key 'k': projects names 'frontend', which no declared cycle uses",
    ),
    (
        "[{name: k, applies_to: [1], projects: [backend]}]",
        "annotation key 'k': applies_to and projects are exclusive",
    ),
    (
        "[{name: k}]",
        "annotation key 'k' names no scope: give applies_to or projects, or use the plain string form",
    ),
    (
        "[{name: k, applies_to: []}]",
        "annotation key 'k' names no scope: give applies_to or projects, or use the plain string form",
    ),
    (
        "[{name: k, projects: []}]",
        "annotation key 'k' names no scope: give applies_to or projects, or use the plain string form",
    ),
    ("[{applies_to: [1]}]", "every annotation key mapping needs a string `name`"),
    ("[{name: 3, applies_to: [1]}]", "every annotation key mapping needs a string `name`"),
    (
        "[{name: k, applies_to: [true]}]",
        "annotation key 'k': applies_to must be a cycle ordinal or a list of them",
    ),
    (
        '[{name: k, applies_to: ["1"]}]',
        "annotation key 'k': applies_to must be a cycle ordinal or a list of them",
    ),
    (
        "[{name: k, projects: [3]}]",
        "annotation key 'k': projects must be a project name or a list of them",
    ),
    ('["k", {name: k, applies_to: [1]}]', "annotation key 'k' is declared twice"),
    ("[3]", "annotation_keys must be a list of strings or mappings"),
    ("k", "annotation_keys must be a list of strings or mappings"),
]


def test_malformed_annotation_key_entries_hard_fail():
    for keys, message in REJECTED:
        with pytest.raises(ContractError, match=re.escape(message)):
            parse(_plan(keys), "p.md")


def test_the_friction_log_warns_of_a_scoped_key_no_delivered_cycle_carried(repo):
    plan = write_plan(
        repo,
        _plan(
            '["plan_wide", {name: delivered_k, applies_to: [1]},'
            " {name: skipped_k, applies_to: [2]}]"
        ),
    )
    run_cli(repo, "plan", "register", plan)
    run_cli(repo, "run", "start", "--plan", plan)
    (repo / "backend" / "app" / "moved.py").write_text("VALUE = 1\n")
    run_cli(repo, "annotate", "--key", "plan_wide", "--value", "x")
    run_cli(repo, "annotate", "--key", "delivered_k", "--value", "y")
    run_cli(repo, "advance")
    run_cli(repo, "cycle", "skip", "--reason", "not applicable")

    lines = run_cli_text(repo, "log", "render").splitlines()
    at = lines.index("- Never reached: none")
    assert lines[at + 1 : at + 3] == [
        "- **Declared check never ran:** `skipped_k` (applies to cycles 2)",
        "- Human interventions: 0",
    ]


def test_the_friction_log_warns_of_a_plain_key_when_no_cycle_was_delivered(repo):
    plan = write_plan(repo, _plan('["plan_wide"]'))
    run_cli(repo, "plan", "register", plan)
    run_cli(repo, "run", "start", "--plan", plan)
    run_cli(repo, "cycle", "skip", "--reason", "na")
    run_cli(repo, "cycle", "skip", "--reason", "na")

    lines = run_cli_text(repo, "log", "render").splitlines()
    at = lines.index("- Never reached: none")
    assert lines[at + 1 : at + 3] == [
        "- **Declared check never ran:** `plan_wide` (applies to cycles 1, 2)",
        "- Human interventions: 0",
    ]
