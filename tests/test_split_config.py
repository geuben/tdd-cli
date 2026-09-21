"""The machine-level runner config, and the role a process takes from it (issue 142)."""

from __future__ import annotations

import os
import pwd

from tddcli import runner


def _current_user() -> str:
    return pwd.getpwuid(os.geteuid()).pw_name


def _write_config(path, user: str) -> None:
    path.write_text(f'[runner]\nuser = "{user}"\ncommand = "/opt/tdd-cli/bin/tdd"\n')


def test_role_follows_the_runner_config(tmp_path, monkeypatch):
    cfg = tmp_path / "runner.toml"
    monkeypatch.setenv("TDD_RUNNER_CONFIG", str(cfg))

    roles = []
    absent = runner.load()
    roles.append(None if absent is None else absent.role)
    users = [_current_user()] + (["root"] if os.geteuid() != 0 else [])
    for user in users:
        _write_config(cfg, user)
        roles.append(runner.load().role)

    expected = [None, "runner"] + (["client"] if os.geteuid() != 0 else [])
    assert roles == expected
