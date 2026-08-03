import pytest

from tddcli.contract import CONTRACT, PIN, STANDARD, ContractError, parse

DECLARED = """---
cycles:
  - n: 1
    project: backend
    test: "tests/test_x.py::test_one"
    stub_expected: ["app/thing.py"]
    commit_red: "test: one"
annotation_keys: ["plan_defect"]
---

# Plan body
"""


def test_absent_front_matter_is_undeclared_not_an_error():
    contract = parse("# Just a plan\n", "tasks/p.md")
    assert contract.status == "undeclared"
    assert contract.cycles == []


def test_declared_front_matter_parses_cycles():
    contract = parse(DECLARED, "tasks/p.md")
    assert contract.status == "declared"
    assert len(contract.cycles) == 1
    cycle = contract.cycles[0]
    assert cycle.kind == STANDARD
    assert cycle.projects == ["backend"]
    assert cycle.stub_expected == ["app/thing.py"]
    assert cycle.commit_messages["red"] == "test: one"
    assert contract.annotation_keys == ["plan_defect"]


def test_malformed_yaml_hard_fails():
    with pytest.raises(ContractError, match="not valid YAML"):
        parse("---\ncycles: [ unclosed\n---\n", "tasks/p.md")


def test_front_matter_without_cycles_hard_fails():
    with pytest.raises(ContractError, match="declares no `cycles`"):
        parse("---\ntitle: nope\n---\n", "tasks/p.md")


def test_two_tests_require_a_contract_cycle():
    body = """---
cycles:
  - n: 1
    project: backend
    tests: ["a::test_x", "b::test_y"]
---
"""
    with pytest.raises(ContractError, match="not a contract cycle"):
        parse(body, "tasks/p.md")


def test_contract_cycle_allows_multiple_targets_across_projects():
    body = """---
cycles:
  - n: 1
    projects: ["backend", "frontend"]
    contract_cycle: true
    tests: ["backend::tests/a.py::test_x", "frontend::b.test.ts > y"]
---
"""
    cycle = parse(body, "tasks/p.md").cycles[0]
    assert cycle.kind == CONTRACT
    assert cycle.projects == ["backend", "frontend"]
    assert len(cycle.tests) == 2


def test_contract_cycle_needs_more_than_one_target():
    body = """---
cycles:
  - n: 1
    project: backend
    contract_cycle: true
    test: "a::test_x"
---
"""
    with pytest.raises(ContractError, match="more than one target"):
        parse(body, "tasks/p.md")


def test_pin_cycle_is_a_distinct_kind():
    body = """---
cycles:
  - n: 1
    project: backend
    pin_cycle: true
    test: "tests/a.py::test_pin"
---
"""
    assert parse(body, "tasks/p.md").cycles[0].kind == PIN


def test_a_cycle_cannot_be_both_pin_and_contract():
    body = """---
cycles:
  - n: 1
    project: backend
    pin_cycle: true
    contract_cycle: true
    tests: ["a::x", "b::y"]
---
"""
    with pytest.raises(ContractError, match="kinds are exclusive"):
        parse(body, "tasks/p.md")


def test_duplicate_ordinals_hard_fail():
    body = """---
cycles:
  - n: 1
    project: backend
    test: "a::x"
  - n: 1
    project: backend
    test: "a::y"
---
"""
    with pytest.raises(ContractError, match="duplicate cycle ordinals"):
        parse(body, "tasks/p.md")


def test_cycle_without_project_hard_fails():
    with pytest.raises(ContractError, match="no project declared"):
        parse('---\ncycles:\n  - n: 1\n    test: "a::x"\n---\n', "tasks/p.md")
