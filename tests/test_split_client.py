"""The client role: an agent's `tdd` on a split machine only asks the runner to act."""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import os

import pytest

from tddcli.cli import build_parser, main

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


def test_the_client_sends_its_environment_on_stdin(repo, split_client, monkeypatch):
    """sudo resets the environment, and the suites need the agent's: its `PATH`, its
    virtualenv, its `HOME`. It travels as data, to be handed back to the agent's own
    processes."""
    monkeypatch.setenv("AGENT_ONLY", "yes")

    _invoke(repo, "status")

    assert json.loads(split_client.stdin.read_text())["env"]["AGENT_ONLY"] == "yes"


#: The smallest argv that parses, for every verb that needs more than its own name.
#: Keyed by verb so an entry for one that does not exist yet is simply unused.
ARGV = {
    "plan": ["plan", "register", "x"],
    "run": ["run", "start", "--plan", "x"],
    "cycle": ["cycle", "skip", "--reason", "x"],
    "annotate": ["annotate", "--key", "k", "--value", "v"],
    "note": ["note", "x"],
    "blocker": ["blocker", "--kind", "tooling", "--detail", "x"],
    "sensitivity": ["sensitivity", "begin"],
    "target": ["target", "x"],
    "log": ["log", "render"],
    "runner": ["runner", "import", "x"],
}


def _verbs() -> list[str]:
    """Read from the parser, so a verb added later is routed on purpose or fails here."""
    subparsers = next(
        action
        for action in build_parser()._actions
        if isinstance(action, argparse._SubParsersAction)
    )
    return sorted(subparsers.choices)


def test_only_docs_and_init_stay_local(repo, split_client):
    stayed_local = set()
    for verb in _verbs():
        before = len(split_client.shim.lines())
        _invoke(repo, *ARGV.get(verb, [verb]), *(["--force"] if verb == "init" else []))
        if len(split_client.shim.lines()) == before:
            stayed_local.add(verb)

    assert stayed_local == {"docs", "init"}
