"""The client role: an agent's `tdd` on a split machine only asks the runner to act."""

from __future__ import annotations

import contextlib
import io
import os

import pytest

from tddcli.cli import main

pytestmark = pytest.mark.skipif(os.geteuid() == 0, reason="root is never a client of root")


def _invoke(repo, *argv: str) -> tuple[int, str]:
    """`main`'s return value and what it printed, from inside the agent's worktree."""
    prev = os.getcwd()
    os.chdir(repo)
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            code = main(list(argv))
    finally:
        os.chdir(prev)
    return code, buf.getvalue()


def test_the_client_forwards_the_verb_and_relays_the_answer(repo, split_client):
    code, printed = _invoke(repo, "status")

    asked = split_client.shim.lines()[0].split(" ", 1)[1]
    relayed = (
        asked,
        split_client.argv.read_text().strip(),
        printed.strip(),
        code,
    )
    assert relayed == (
        f"-n -H -u root -- {split_client.stub} --agent-context-stdin status",
        "--agent-context-stdin status",
        '{"ok": true, "stub": true}',
        3,
    )
