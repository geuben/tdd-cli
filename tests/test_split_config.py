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


def test_an_untrusted_runner_config_is_refused(tmp_path, monkeypatch):
    """The three ways a caller could have forged the file the runner trusts."""
    cfg = tmp_path / "runner.toml"
    monkeypatch.setenv("TDD_RUNNER_CONFIG", str(cfg))
    real_euid = os.geteuid()

    def refused(mode: int, euid: int) -> bool:
        _write_config(cfg, _current_user())
        cfg.chmod(mode)
        monkeypatch.setattr(os, "geteuid", lambda: euid)
        try:
            runner.load()
        except runner.RunnerConfigError:
            return True
        finally:
            monkeypatch.setattr(os, "geteuid", lambda: real_euid)
        return False

    forgeries = {
        "world-writable": refused(0o666, real_euid),
        "group-writable": refused(0o664, real_euid),
        "foreign owner": refused(0o644, real_euid + 1),
    }
    assert forgeries == dict.fromkeys(forgeries, True)
