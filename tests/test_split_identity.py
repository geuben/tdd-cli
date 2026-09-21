"""Who the runner says did the work.

Everything `identity.resolve` reads today — the session id, the transcript, the
`TDD_EXECUTOR_MODEL` override — is the agent's to write. In split mode the runner
trusts only what its operator told it, and labels everything else a claim.
"""

from __future__ import annotations

import io
import json
import os
import sys

from conftest import current_user, run_cli, write_plan
from tddcli.ledger import Ledger

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
# Minimal plan for split-mode identity tests
"""


def _start(repo, *flags: str) -> dict:
    plan = write_plan(repo, MINIMAL_PLAN)
    run_cli(repo, "plan", "register", plan)
    return run_cli(repo, *flags, "run", "start", "--plan", plan)


def _recorded(repo) -> tuple[str, str]:
    row = Ledger(repo).one("SELECT executor_model, executor_source FROM run")
    return row["executor_model"], row["executor_source"]


def test_a_mapped_agent_records_the_operator_assigned_model(repo, split_runner):
    """`conftest` pins `TDD_EXECUTOR_MODEL` in this process, which here is the runner:
    recording the operator's model proves the runner did not read its own environment."""
    with split_runner.config.open("a") as fh:
        fh.write(f'\n[executor]\n{current_user()} = "model-from-operator"\n')

    out = _start(repo)

    seen = (out["result"]["executor_source"], *_recorded(repo))
    assert seen == ("operator", "model-from-operator", "operator")


def test_an_unmapped_agent_is_recorded_as_claimed(repo, split_runner, monkeypatch):
    """The claim is resolved on the agent's side, from the agent's environment, and is
    recorded as exactly that: a consumer comparing models can leave it out."""
    agent_env = {**os.environ, "TDD_EXECUTOR_MODEL": "model-the-agent-claims"}
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps({"env": agent_env})))

    out = _start(repo, "--agent-context-stdin")

    seen = (out["result"]["executor_source"], *_recorded(repo))
    assert seen == ("claimed", "model-the-agent-claims", "claimed")


def test_the_human_label_is_a_claim_like_any_other(repo, split_runner, monkeypatch):
    """`--executor` is a human's word on a single-user machine. Through the runner it is
    whatever the caller typed, so it is carried across and recorded as a claim."""
    anonymous = {
        k: v
        for k, v in os.environ.items()
        if k not in ("TDD_EXECUTOR_MODEL", "CLAUDE_CODE_SESSION_ID")
    }
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps({"env": anonymous})))
    plan = write_plan(repo, MINIMAL_PLAN)
    run_cli(repo, "plan", "register", plan)

    run_cli(repo, "--agent-context-stdin", "run", "start", "--plan", plan, "--executor", "a-human")

    assert _recorded(repo) == ("a-human", "claimed")
