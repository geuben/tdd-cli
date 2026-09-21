"""`tdd doctor` says which mode a machine is in, and what that mode is worth.

On a single-user machine the ledger belongs to the uid that runs the agent, and
doctor says so instead of claiming isolation. On a split machine it probes the three
things the split rests on, live and as the agent, so they hold on the real install
rather than in a test's imagination.
"""

from __future__ import annotations

from conftest import run_cli


def _check(out: dict, name: str) -> dict:
    matches = [c for c in out["result"]["checks"] if c["check"] == name]
    assert len(matches) == 1, [c["check"] for c in out["result"]["checks"]]
    return matches[0]


def test_single_mode_doctor_says_the_agent_can_reach_the_ledger(repo):
    out = run_cli(repo, "doctor")

    isolation = _check(out, "ledger isolation")
    said = (out["result"]["mode"], isolation["ok"], "same uid" in isolation["detail"])
    assert said == ("single", True, True)


def _probe(repo, monkeypatch, name: str, deny: str) -> tuple[list[bool], str]:
    """One split-mode check across two machines: one where sudo lets the agent run
    `deny`, and one where it does not. Returns both verdicts and the second detail."""
    allowed = _check(run_cli(repo, "doctor"), name)
    monkeypatch.setenv("SUDO_DENY", deny)
    refused = _check(run_cli(repo, "doctor"), name)
    return [allowed["ok"], refused["ok"]], refused["detail"]


def test_split_doctor_checks_the_drop_to_the_agent(repo, split_runner, monkeypatch):
    """Everything else in split mode assumes the runner can become the agent. When it
    cannot, the fix is one sudoers line, so the check quotes it."""
    verdicts, detail = _probe(repo, monkeypatch, "runs as the agent", deny="id")

    assert (verdicts, "NOPASSWD:SETENV" in detail) == ([True, False], True)


def test_split_doctor_ledger_check_follows_what_the_agent_can_read(
    repo, split_runner, monkeypatch
):
    """In this suite the agent and the runner are one uid, so the agent *can* read the
    ledger and the check must say so. It passes only once `test -r`, asked as the
    agent, is refused: the check reports what is true, not what was configured."""
    verdicts, _ = _probe(repo, monkeypatch, "ledger out of the agent's reach", deny="test")

    assert verdicts == [False, True]
