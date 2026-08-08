"""examples/plan.md is documentation with a parser: it must register cleanly, forever.

The example exists to show the full front-matter vocabulary, so these assertions pin
that vocabulary — a contract change that breaks the example must break here, not in a
user's first five minutes.
"""

from __future__ import annotations

from pathlib import Path

from tddcli import config as config_mod
from tddcli import contract

EXAMPLE = Path(__file__).parent.parent / "examples" / "plan.md"

TOML = """
[project.backend]
root       = "backend"
adapter    = "pytest"
test_paths = ["tests/"]

[project.frontend]
root       = "frontend"
adapter    = "vitest"
test_paths = ["**/*.test.ts"]
"""


def _parsed(tmp_path):
    (tmp_path / "tdd.toml").write_text(TOML)
    (tmp_path / "backend").mkdir()
    (tmp_path / "frontend").mkdir()
    cfg = config_mod.load(tmp_path)
    return contract.parse(EXAMPLE.read_text(), "examples/plan.md", cfg)


def test_example_plan_is_a_declared_contract(tmp_path):
    parsed = _parsed(tmp_path)
    assert parsed.status == "declared"
    assert [c.ordinal for c in parsed.cycles] == [1, 2, 3, 4, 5]


def test_example_plan_shows_every_cycle_kind(tmp_path):
    kinds = [c.kind for c in _parsed(tmp_path).cycles]
    assert kinds == ["standard", "standard", "pin", "refactor", "contract"]


def test_example_plan_exercises_the_full_vocabulary(tmp_path):
    cycles = {c.ordinal: c for c in _parsed(tmp_path).cycles}

    assert cycles[1].stub_expected == ["app/orders/pricing.py"]
    assert cycles[1].commit_messages == {
        "red": "test: order total sums line items",
        "green": "feat: pricing.total() over line items",
    }
    assert cycles[3].commit_messages == {"pin": "test: pin the legacy bulk-discount rule"}
    assert cycles[4].tests == []
    assert cycles[4].modifies_tests, "the refactor cycle must declare its test modification"
    assert cycles[4].commit_messages == {
        "refactor": "refactor: discount rule lives in pricing, handler delegates"
    }
    assert cycles[5].projects == ["backend", "frontend"]
    assert len(cycles[5].tests) == 2
    assert all("::" in t or " > " in t for t in cycles[5].tests)


def test_example_plan_requires_the_annotation_it_documents(tmp_path):
    assert _parsed(tmp_path).annotation_keys == ["legacy_discount_rule_kept"]
