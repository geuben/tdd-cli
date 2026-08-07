#!/usr/bin/env python3
"""Claude Code Stop hook: refuse to let the agent stop while a tdd run is live.

The CLI cannot compel an agent to keep going — only the harness can (README,
"Enforcement boundary"). This hook closes that loop: when the agent tries to
stop, it asks `tdd status`, and blocks the stop unless the run is complete or
blocked (a typed blocker is the sanctioned way to release this hook).

Wire it up in `.claude/settings.json` — see README.md in this directory.
"""

import json
import subprocess
import sys


def main() -> int:
    json.load(sys.stdin)  # hook payload; unused, but consume it

    proc = subprocess.run(
        ["tdd", "status"], capture_output=True, text=True, timeout=120
    )
    try:
        envelope = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return 0  # no tdd here (or a broken install) — never wedge the agent

    next_action = envelope.get("next_action") or {}
    if next_action.get("terminal", True):
        return 0  # complete or blocked: the run is not live, stopping is fine

    run = envelope.get("run") or {}
    print(json.dumps({
        "decision": "block",
        "reason": (
            f"A tdd run is live (cycle {run.get('cycle')}, phase {run.get('phase')})."
            f" Next action: {next_action.get('verb')} — {next_action.get('detail')}"
            " If you are genuinely stuck, record it with"
            " `tdd blocker --kind <kind> --detail <why>`, which releases this hook."
        ),
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
