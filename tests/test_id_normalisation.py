"""Tests for per-adapter target-id normalisation (issue #57).

Covers:
  - Base Adapter identity hook (pytest ids are byte-for-byte unchanged)
  - VitestAdapter separator canonicalisation
  - VitestAdapter.run() matches a target differing only by the describe/test separator
"""

from __future__ import annotations

from pathlib import Path

from tddcli import config as config_mod
from tddcli.adapters.pytest_adapter import PytestAdapter
from tddcli.adapters.vitest_adapter import VitestAdapter

PYTEST_TOML = """
[project.backend]
root       = "backend"
adapter    = "pytest"
test_paths = ["tests/"]
"""

VITEST_TOML = """
[project.frontend]
root       = "frontend"
adapter    = "vitest"
test_paths = ["**/*.test.ts"]
"""


def vitest_adapter_for(tmp_path: Path) -> VitestAdapter:
    (tmp_path / "tdd.toml").write_text(VITEST_TOML)
    (tmp_path / "frontend").mkdir()
    cfg = config_mod.load(tmp_path)
    return VitestAdapter(cfg.project("frontend"), tmp_path)


def pytest_adapter_for(tmp_path: Path) -> PytestAdapter:
    (tmp_path / "tdd.toml").write_text(PYTEST_TOML)
    (tmp_path / "backend").mkdir()
    cfg = config_mod.load(tmp_path)
    return PytestAdapter(cfg.project("backend"), tmp_path)


def test_vitest_normalise_id_collapses_describe_separator(tmp_path):
    """VitestAdapter.normalise_id folds ' > ' between nesting levels to a space."""
    adapter = vitest_adapter_for(tmp_path)

    # Primary case: ' > ' between describe and test name is collapsed to a space
    declared = "frontend::a.test.ts > someHelper > formats a value"
    canonical = "frontend::a.test.ts > someHelper formats a value"
    assert adapter.normalise_id(declared) == canonical

    # Idempotent: already-canonical (space-joined) id is returned unchanged
    assert adapter.normalise_id(canonical) == canonical

    # Multi-level: ' > ' at every nesting level all collapse
    multi = "frontend::a.test.ts > a > b > c"
    assert adapter.normalise_id(multi) == "frontend::a.test.ts > a b c"

    # No ' > ' after the file segment (unusual, file-only) — returned unchanged
    file_only = "frontend::a.test.ts"
    assert adapter.normalise_id(file_only) == file_only


def test_base_adapter_normalise_id_is_identity(tmp_path):
    """The base hook returns the id unchanged — pytest ids need no normalisation."""
    adapter = pytest_adapter_for(tmp_path)
    test_id = "backend::tests/test_x.py::test_y"
    assert adapter.normalise_id(test_id) == test_id
