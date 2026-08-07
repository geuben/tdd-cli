#!/usr/bin/env python3
"""Claude Code PreToolUse hook: route bare test-runner invocations through tdd.

While a tdd run is live, phase transitions must come from observed execution
via `tdd advance` — a bare `pytest` or `vitest` run is invisible to the ledger
and tempts the agent into asserting progress. This hook denies those commands
and points at `tdd advance` instead.

Only plain runs are denied. Collection and listing (`--collect-only`,
`vitest list`) stay allowed: they observe nothing and agents legitimately use
them to name targets.

Wire it up in `.claude/settings.json` — see README.md in this directory.
"""

import json
import re
import subprocess
import sys

BARE_RUNNER = re.compile(
    r"(?:^|&&|;|\|)\s*"                       # start of a shell command
    r"(?:uv\s+run\s+|npx\s+|pnpm\s+|yarn\s+)?"  # common launchers
    r"(?:python\s+-m\s+)?"
    r"(pytest|vitest)\b(?![\w-])"
)
ALLOWED_MARKERS = ("--collect-only", "--co", "vitest list")


def run_is_live() -> bool:
    try:
        proc = subprocess.run(
            ["tdd", "status"], capture_output=True, text=True, timeout=120
        )
        envelope = json.loads(proc.stdout)
    except Exception:
        return False  # no tdd here — stay out of the way
    next_action = envelope.get("next_action") or {}
    return not next_action.get("terminal", True)


def main() -> int:
    payload = json.load(sys.stdin)
    command = (payload.get("tool_input") or {}).get("command", "")

    if not BARE_RUNNER.search(command):
        return 0
    if any(marker in command for marker in ALLOWED_MARKERS):
        return 0
    if not run_is_live():
        return 0

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                "A tdd run is live: run suites through `tdd advance`, not bare"
                " pytest/vitest. The ledger derives phase from observed execution,"
                " and a bare run observes nothing it can record."
            ),
        }
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
