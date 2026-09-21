"""The actor a split-mode runner installs: everything it does, it does as the agent.

`sudo` here is `conftest.sudo_shim`, which logs its arguments and then runs the
command as the same uid. What these tests pin is what the runner *asks* sudo for;
that sudo then changes uid is `tdd doctor`'s live probe, not something a test
without root can show.
"""

from __future__ import annotations

from tddcli.actor import SudoActor


def test_both_spawn_forms_run_through_sudo_as_the_agent(tmp_path, sudo_shim):
    actor = SudoActor(sudo=str(sudo_shim.path), agent="agent-x", env=None)

    actor.run_argv(["echo", "one"])
    actor.run_shell("echo two", cwd=tmp_path)

    tails = [line.split(" -u ", 1)[1] for line in sudo_shim.lines()]
    assert tails == ["agent-x -- echo one", "agent-x -- /bin/sh -c echo two"]
