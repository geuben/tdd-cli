# Claude Code hooks for tdd-cli

The README's "Enforcement boundary" section delegates two rules to the
harness; these hooks implement them for [Claude Code](https://docs.anthropic.com/en/docs/claude-code):

- **`stop_hook.py`** — a Stop hook that queries `tdd status` and refuses to
  let the agent stop while a run is live. A typed blocker
  (`tdd blocker --kind ... --detail ...`) releases it.
- **`bash_hook.py`** — a PreToolUse hook that denies bare `pytest`/`vitest`
  invocations while a run is live, pointing the agent at `tdd advance`.
  Collection-only commands (`--collect-only`, `vitest list`) stay allowed.

Both hooks fail open: if `tdd` is not installed or emits something
unparseable, they allow the action rather than wedging the agent.

## Installation

Copy the scripts somewhere stable (e.g. `.claude/hooks/` in your repo), make
them executable, and add to `.claude/settings.json`:

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          { "type": "command", "command": "python3 .claude/hooks/stop_hook.py" }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          { "type": "command", "command": "python3 .claude/hooks/bash_hook.py" }
        ]
      }
    ]
  }
}
```

Hooks run from the workspace root, which is where `tdd status` resolves the
worktree — no configuration is needed beyond the above.
