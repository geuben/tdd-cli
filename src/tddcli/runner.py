"""The machine-level runner config, and the role this process takes from it.

Split mode (issue 142): a `tdd` runner under its own uid owns the ledger, and the
agent can only ask it to act. Which side of that boundary a process is on follows
from one file, not from anything the caller says.
"""

from __future__ import annotations

import os
import pwd
import stat
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

CONFIG_PATH = Path("/etc/tdd-cli/runner.toml")
CONFIG_ENV = "TDD_RUNNER_CONFIG"
DEFAULT_SUDO = "/usr/bin/sudo"


class RunnerConfigError(RuntimeError):
    pass


@dataclass
class RunnerConfig:
    user: str
    command: str
    role: str  # runner | client
    sudo: str = DEFAULT_SUDO
    ledger_home: Path | None = None
    executors: dict[str, str] = field(default_factory=dict)


def config_path() -> Path:
    override = os.environ.get(CONFIG_ENV)
    return Path(override) if override else CONFIG_PATH


def _require_trusted(path: Path) -> None:
    """Refuse a config the caller could have forged.

    An agent may point its own client at any file it likes: that only moves its own
    run into a ledger nobody trusts. The runner must not follow it there, so the file
    has to belong to root or to this process, and nobody else may be able to edit it.
    """
    st = path.stat()
    if st.st_uid not in (0, os.geteuid()):
        raise RunnerConfigError(
            f"{path} is owned by uid {st.st_uid}; it must be owned by root or by the"
            " user running tdd"
        )
    if st.st_mode & (stat.S_IWGRP | stat.S_IWOTH):
        raise RunnerConfigError(f"{path} is group- or world-writable; `chmod go-w` it")


def load() -> RunnerConfig | None:
    """None on a machine that is not split."""
    path = config_path()
    if not path.is_file():
        return None
    _require_trusted(path)
    try:
        raw = tomllib.loads(path.read_text())
    except tomllib.TOMLDecodeError as exc:
        raise RunnerConfigError(f"{path}: {exc}") from exc
    section = raw.get("runner") or {}
    for key in ("user", "command"):
        if not section.get(key):
            raise RunnerConfigError(f"{path}: [runner] needs `{key}`")
    try:
        runner_uid = pwd.getpwnam(section["user"]).pw_uid
    except KeyError as exc:
        raise RunnerConfigError(
            f"{path}: [runner] user {section['user']!r} does not exist"
        ) from exc
    ledger_home = section.get("ledger_home")
    return RunnerConfig(
        user=section["user"],
        command=section["command"],
        role="runner" if runner_uid == os.geteuid() else "client",
        sudo=section.get("sudo", DEFAULT_SUDO),
        ledger_home=Path(ledger_home) if ledger_home else None,
        executors=dict(raw.get("executor") or {}),
    )
