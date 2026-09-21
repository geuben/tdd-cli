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
