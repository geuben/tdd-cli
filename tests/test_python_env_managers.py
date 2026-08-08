"""The pytest adapter must not assume uv (§10).

The default invocation was `uv run pytest` whenever a `pyproject.toml` existed —
but Poetry, pipenv, PDM and plain-venv projects all have one, and none of them can
be run through uv. The runner prefix is now derived from the environment manager's
own marker files, checked at the project root first and the worktree root second
(uv/pnpm-style workspaces keep a single lockfile at the top). An explicit
`test_command` always wins.
"""

from __future__ import annotations

from pathlib import Path

from tddcli import adapters
from tddcli import config as config_mod


def _adapter(tmp_path: Path, root: str = "."):
    (tmp_path / "tdd.toml").write_text(
        f'[project.app]\nroot = "{root}"\nadapter = "pytest"\ntest_paths = ["tests/"]\n'
    )
    cfg = config_mod.load(tmp_path)
    return adapters.build(cfg.project("app"), tmp_path)


def test_uv_lock_selects_uv(tmp_path):
    (tmp_path / "uv.lock").write_text("")
    assert _adapter(tmp_path)._base_cmd() == "uv run pytest"


def test_poetry_lock_selects_poetry(tmp_path):
    (tmp_path / "poetry.lock").write_text("")
    (tmp_path / "pyproject.toml").write_text("[tool.poetry]\nname = 'x'\n")
    assert _adapter(tmp_path)._base_cmd() == "poetry run pytest"


def test_poetry_section_without_lock_selects_poetry(tmp_path):
    (tmp_path / "pyproject.toml").write_text("[tool.poetry]\nname = 'x'\n")
    assert _adapter(tmp_path)._base_cmd() == "poetry run pytest"


def test_pipfile_selects_pipenv(tmp_path):
    (tmp_path / "Pipfile").write_text("")
    assert _adapter(tmp_path)._base_cmd() == "pipenv run pytest"


def test_pdm_lock_selects_pdm(tmp_path):
    (tmp_path / "pdm.lock").write_text("")
    assert _adapter(tmp_path)._base_cmd() == "pdm run pytest"


def test_plain_pep621_pyproject_runs_bare_pytest(tmp_path):
    """pip + venv is the least-assuming default: the active environment's pytest."""
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'x'\n")
    assert _adapter(tmp_path)._base_cmd() == "pytest"


def test_no_markers_runs_bare_pytest(tmp_path):
    assert _adapter(tmp_path)._base_cmd() == "pytest"


def test_workspace_lockfile_covers_a_nested_project(tmp_path):
    """A uv workspace keeps one uv.lock at the top; members have only pyproject."""
    (tmp_path / "uv.lock").write_text("")
    (tmp_path / "backend").mkdir()
    (tmp_path / "backend" / "pyproject.toml").write_text("[project]\nname = 'b'\n")
    assert _adapter(tmp_path, root="backend")._base_cmd() == "uv run pytest"


def test_project_root_markers_beat_workspace_markers(tmp_path):
    (tmp_path / "uv.lock").write_text("")
    (tmp_path / "backend").mkdir()
    (tmp_path / "backend" / "Pipfile").write_text("")
    assert _adapter(tmp_path, root="backend")._base_cmd() == "pipenv run pytest"


def test_doctor_probe_uses_the_same_runner_prefix(tmp_path):
    """The pytest-json-report probe hardcoded `uv run python`, failing on any
    non-uv project even when the plugin is installed."""
    (tmp_path / "poetry.lock").write_text("")
    probe = _adapter(tmp_path).plugin_probe_cmd()
    assert probe.startswith("poetry run python")
    assert "pytest_jsonreport" in probe
