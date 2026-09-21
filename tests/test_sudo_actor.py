"""The actor a split-mode runner installs: everything it does, it does as the agent.

`sudo` here is `conftest.sudo_shim`, which logs its arguments and then runs the
command as the same uid. What these tests pin is what the runner *asks* sudo for;
that sudo then changes uid is `tdd doctor`'s live probe, not something a test
without root can show.
"""

from __future__ import annotations

import os

from tddcli.actor import SudoActor


def test_both_spawn_forms_run_through_sudo_as_the_agent(tmp_path, sudo_shim):
    actor = SudoActor(sudo=str(sudo_shim.path), agent="agent-x", env=None)

    actor.run_argv(["echo", "one"])
    actor.run_shell("echo two", cwd=tmp_path)

    tails = [line.split(" -u ", 1)[1] for line in sudo_shim.lines()]
    assert tails == ["agent-x -- echo one", "agent-x -- /bin/sh -c echo two"]


def _agent_env(sudo_shim, **extra: str) -> dict[str, str]:
    """What a client would send: the shim itself needs `PATH` and `SUDO_LOG` from it."""
    return {"PATH": os.environ["PATH"], "SUDO_LOG": str(sudo_shim.log), **extra}


def test_spawned_environment_is_the_agents_plus_extras(tmp_path, monkeypatch, sudo_shim):
    monkeypatch.setenv("WHO", "runner")
    actor = SudoActor(
        sudo=str(sudo_shim.path), agent="agent-x", env=_agent_env(sudo_shim, WHO="agent")
    )

    proc = actor.run_shell("echo $WHO $TDD_WORKERS", cwd=tmp_path, env={"TDD_WORKERS": "4"})

    flags = sudo_shim.lines()[0].split(" -u ", 1)[0].split()[1:]
    assert (proc.stdout, "-E" in flags) == ("agent 4\n", True)


def test_without_an_agent_environment_sudo_builds_it(sudo_shim):
    """No `-E`, so a real sudo resets the environment to the agent's own; `-H` because
    macOS sudo would otherwise leave `HOME` pointing at the runner's."""
    SudoActor(sudo=str(sudo_shim.path), agent="agent-x", env=None).run_argv(["true"])

    asked = sudo_shim.lines()[0].split(" ", 1)[1]
    assert asked == "-n -H -u agent-x -- true"
