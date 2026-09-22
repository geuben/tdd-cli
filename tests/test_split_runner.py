"""The runner role: `tdd` invoked through sudo, as the uid that owns the ledger."""

from __future__ import annotations

import io
import json
import os
import sys

import pytest

from conftest import current_user, run_cli, write_plan
from tddcli import actor

MINIMAL_PLAN = """\
---
cycles:
  - n: 1
    project: backend
    title: "placeholder"
    test: "tests/test_smoke.py::test_smoke"
    commit_red: "test: placeholder"
    commit_green: "feat: placeholder"
---
# Minimal plan for split-mode tests
"""


def test_run_start_spawns_git_and_the_suite_as_the_agent(repo, split_runner):
    plan = write_plan(repo, MINIMAL_PLAN)
    run_cli(repo, "plan", "register", plan)

    out = run_cli(repo, "run", "start", "--plan", plan)

    as_agent = f"-u {current_user()} -- "
    lines = split_runner.shim.lines()
    spawned = (
        out["ok"],
        any(as_agent + "git -C" in line for line in lines),
        any(as_agent + "/bin/sh -c" in line for line in lines),
    )
    assert spawned == (True, True, True)


def _agent_context(monkeypatch, **extra: str) -> None:
    """What the client writes to the runner's stdin: the agent's environment."""
    payload = json.dumps({"env": {**os.environ, **extra}})
    monkeypatch.setattr(sys, "stdin", io.StringIO(payload))


def test_agent_context_on_stdin_reaches_spawned_commands(repo, split_runner, monkeypatch):
    _agent_context(monkeypatch, MARK="from-agent")

    run_cli(repo, "--agent-context-stdin", "doctor")

    assert any(line.startswith("MARK=from-agent ") for line in split_runner.shim.lines())


def test_the_runner_without_an_agent_refuses_to_act(repo, split_runner, monkeypatch):
    """Falling back to acting as itself would run the agent's code as the ledger's uid."""
    monkeypatch.delenv("SUDO_USER")
    monkeypatch.delenv("SUDO_UID")

    out = run_cli(repo, "status")

    assert (out["ok"], out["result"].get("reason")) == (False, "no_agent")


@pytest.mark.skipif(os.geteuid() == 0, reason="root reads a mode-000 file")
def test_an_unreadable_worktree_is_a_failure_envelope(repo, split_runner):
    """The runner reads the worktree as itself, so the agent has to let it."""
    config = repo / "tdd.toml"
    config.chmod(0)
    try:
        out = run_cli(repo, "doctor")
    finally:
        config.chmod(0o644)

    named = (out["result"].get("reason"), current_user() in out["error"])
    assert named == ("worktree_unreadable", True)


@pytest.mark.skipif(os.geteuid() == 0, reason="root reads a mode-000 file")
def test_an_unreadable_file_outside_the_runner_role_is_still_a_crash(repo):
    """Only the runner reads someone else's files. On a single-user machine an
    unreadable `tdd.toml` is a broken checkout, and a traceback is the right report."""
    config = repo / "tdd.toml"
    config.chmod(0)
    try:
        with pytest.raises(PermissionError):
            run_cli(repo, "doctor")
    finally:
        config.chmod(0o644)


def test_the_runner_never_installs_an_actor_that_acts_as_itself(repo, split_runner, monkeypatch):
    """With no caller the verb is refused before anything spawns. The actor behind that
    refusal still has to be one that cannot run the agent's code as the ledger's uid:
    if a path ever slipped past, it must fail at sudo, not succeed as the runner."""
    monkeypatch.delenv("SUDO_USER")
    monkeypatch.delenv("SUDO_UID")

    run_cli(repo, "status")

    assert isinstance(actor.current(), actor.SudoActor)
