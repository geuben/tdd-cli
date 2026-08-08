"""`tdd init` adapter detection: evidence, not guesses.

A `package.json` alone used to be claimed as vitest — but a jest or mocha project
has one too, and the wrong guess wrote a config that failed on first use. Vitest
now requires a vitest config file or a declared vitest dependency; anything else
with a package.json is reported as unmatched for the human to declare.
"""

from __future__ import annotations

import json
import subprocess

import pytest

from conftest import run_cli


@pytest.fixture
def bare_repo(tmp_path, ledger_home):
    root = tmp_path / "workspace"
    root.mkdir()
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    return root


def test_a_jest_project_is_unmatched_not_claimed_as_vitest(bare_repo):
    (bare_repo / "web").mkdir()
    (bare_repo / "web" / "package.json").write_text(
        json.dumps({"name": "web", "devDependencies": {"jest": "^29.0.0"}})
    )
    out = run_cli(bare_repo, "init")
    assert out["ok"], out
    assert out["result"]["detected"] == []
    assert out["result"]["unmatched"] == ["web"]
    assert "vitest" not in (bare_repo / "tdd.toml").read_text()
    assert "web" in out["next_action"]["detail"]


def test_a_vitest_dependency_is_enough_evidence(bare_repo):
    (bare_repo / "web").mkdir()
    (bare_repo / "web" / "package.json").write_text(
        json.dumps({"name": "web", "devDependencies": {"vitest": "^2.0.0"}})
    )
    out = run_cli(bare_repo, "init")
    assert out["result"]["detected"] == ["web"]
    assert 'adapter    = "vitest"' in (bare_repo / "tdd.toml").read_text()


def test_a_vitest_config_file_is_enough_evidence(bare_repo):
    (bare_repo / "web").mkdir()
    (bare_repo / "web" / "vitest.config.js").write_text("export default {}\n")
    out = run_cli(bare_repo, "init")
    assert out["result"]["detected"] == ["web"]


def test_a_malformed_package_json_is_unmatched_not_a_crash(bare_repo):
    (bare_repo / "web").mkdir()
    (bare_repo / "web" / "package.json").write_text("{not json")
    out = run_cli(bare_repo, "init")
    assert out["ok"], out
    assert out["result"]["detected"] == []
    assert out["result"]["unmatched"] == ["web"]
