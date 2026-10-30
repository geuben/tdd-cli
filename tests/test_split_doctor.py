"""`tdd doctor` says which mode a machine is in, and what that mode is worth.

On a single-user machine the ledger belongs to the uid that runs the agent, and
doctor says so instead of claiming isolation. On a split machine it probes the three
things the split rests on, live and as the agent, so they hold on the real install
rather than in a test's imagination.
"""

from __future__ import annotations

import os

import pytest

from conftest import ABSENT, agent_context, run_cli


def _check(out: dict, name: str) -> dict:
    matches = [c for c in out["result"]["checks"] if c["check"] == name]
    assert len(matches) == 1, [c["check"] for c in out["result"]["checks"]]
    return matches[0]


def test_single_mode_doctor_says_the_agent_can_reach_the_ledger(repo):
    out = run_cli(repo, "doctor")

    isolation = _check(out, "ledger isolation")
    probed = any(c["check"] == "runs as the agent" for c in out["result"]["checks"])
    said = (out["result"]["mode"], isolation["ok"], "same uid" in isolation["detail"], probed)
    assert said == ("single", True, True, False)


def test_a_split_runner_that_can_act_reports_its_checks_once_and_in_order(
    repo, split_runner, monkeypatch
):
    """Probing the drop to the agent first must not change what a healthy runner's
    doctor says: the same checks, in the same order, with `id -u` asked once."""
    # `uv run pytest` exports one; its informational check is not under test here.
    monkeypatch.delenv("VIRTUAL_ENV", raising=False)
    agent_context(monkeypatch, umask=0o022)

    out = run_cli(repo, "--agent-context-stdin", "doctor")

    names = [c["check"] for c in out["result"]["checks"] if "project" not in c]
    asked = sum(line.endswith(" id -u") for line in split_runner.shim.lines())
    assert (names, asked) == (
        [
            "worktree resolvable",
            "tdd.toml valid",
            "ledger reachable",
            "ledger outside worktree",
            "runs as the agent",
            "ledger out of the agent's reach",
            "install not writable by the agent",
            "executor identity",
            "no legacy state artifacts",
            "worktree clean",
        ],
        1,
    )


#: An older client sends no umask, so the runner spawns each command as it is. A
#: current one sends its own, and the runner wraps each command to apply it. Both are
#: in the field, so each split check is probed through both spawn forms.
CLIENTS = pytest.mark.parametrize("umask", [ABSENT, 0o022], ids=["older-client", "current-client"])


def _refuse_sudo(split_runner, tmp_path) -> dict[str, str]:
    """No sudoers line for the hop: sudo refuses every command, whatever it is."""
    split_runner.shim.refuse()
    return {}


def _refuse_test(split_runner, tmp_path) -> dict[str, str]:
    """The filesystem says no to the agent: a `test` that fails, first on the `PATH`
    the agent's processes get. Doctor names `test` bare, so it is found there."""
    stub = tmp_path / "agent-bin"
    stub.mkdir()
    (stub / "test").write_text("#!/bin/sh\nexit 1\n")
    (stub / "test").chmod(0o755)
    return {"PATH": f"{stub}{os.pathsep}{os.environ['PATH']}"}


def _probe(
    repo, monkeypatch, split_runner, tmp_path, name: str, refuse, umask
) -> tuple[list[bool], dict, bool]:
    """One split-mode check across two machines: one where the agent may do what the
    check asks, and one where `refuse` says it may not. Returns both verdicts, the
    second doctor's whole answer, and whether the runner wrapped its commands to apply
    a umask."""
    agent_context(monkeypatch, umask=umask)
    allowed = _check(run_cli(repo, "--agent-context-stdin", "doctor"), name)
    wrapped = any(" -c umask " in line for line in split_runner.shim.lines())
    agent_context(monkeypatch, umask=umask, **refuse(split_runner, tmp_path))
    refused = run_cli(repo, "--agent-context-stdin", "doctor")
    return [allowed["ok"], _check(refused, name)["ok"]], refused, wrapped


@CLIENTS
def test_split_doctor_checks_the_drop_to_the_agent(
    repo, split_runner, monkeypatch, tmp_path, umask
):
    """Everything else in split mode assumes the runner can become the agent, so when
    sudo refuses the hop that is the one thing doctor reports: the sudoers line that
    fixes it, and what sudo itself said."""
    verdicts, refused, wrapped = _probe(
        repo, monkeypatch, split_runner, tmp_path, "runs as the agent", _refuse_sudo, umask
    )

    detail = _check(refused, "runs as the agent")["detail"]
    said = (
        verdicts,
        len(refused["result"]["checks"]),
        "NOPASSWD:SETENV" in detail,
        "a password is required" in detail,
        wrapped,
    )
    assert said == ([True, False], 1, True, True, umask is not ABSENT)


@CLIENTS
def test_split_doctor_ledger_check_follows_what_the_agent_can_read(
    repo, split_runner, monkeypatch, tmp_path, umask
):
    """In this suite the agent and the runner are one uid, so the agent *can* read the
    ledger and the check must say so. It passes only once `test -r`, asked as the
    agent, is refused: the check reports what is true, not what was configured."""
    verdicts, _, wrapped = _probe(
        repo,
        monkeypatch,
        split_runner,
        tmp_path,
        "ledger out of the agent's reach",
        _refuse_test,
        umask,
    )

    assert (verdicts, wrapped) == ([False, True], umask is not ABSENT)


@CLIENTS
def test_split_doctor_install_check_follows_what_the_agent_can_write(
    repo, split_runner, monkeypatch, tmp_path, umask
):
    """A runner whose code the agent can edit is the agent. This suite runs from a
    checkout its own uid owns, so the check must fail here until `test -w` is refused."""
    verdicts, _, wrapped = _probe(
        repo,
        monkeypatch,
        split_runner,
        tmp_path,
        "install not writable by the agent",
        _refuse_test,
        umask,
    )

    assert (verdicts, wrapped) == ([False, True], umask is not ABSENT)


def test_socket_mode_doctor_names_the_source_it_reaches(repo, split_guest):
    reachable = _check(run_cli(repo, "doctor"), "ledger reachable")

    # `source vm-1`, not just `vm-1`: the socket's own file name already says that.
    assert (reachable["ok"], "source vm-1" in reachable["detail"]) == (True, True)


def test_a_split_runner_notes_the_agents_virtual_env_not_its_own(
    repo, split_runner, monkeypatch, tmp_path
):
    """Issue #99 — sudo resets the runner's environment, but the suites run with the
    agent's, so the agent's VIRTUAL_ENV is the one that can leak into them."""
    outside = tmp_path / "some-other-repo" / ".venv"
    monkeypatch.delenv("VIRTUAL_ENV", raising=False)
    agent_context(monkeypatch, umask=0o022, VIRTUAL_ENV=str(outside))

    out = run_cli(repo, "--agent-context-stdin", "doctor")

    assert _check(out, "VIRTUAL_ENV")["detail"].startswith(
        f"VIRTUAL_ENV={outside} is outside every project root"
    )
