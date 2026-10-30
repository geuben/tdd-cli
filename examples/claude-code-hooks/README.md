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

From the root of your repository:

```sh
tdd init --skill claude-code
```

It copies the `tdd-drive` skill and both hooks out of the installed `tdd`, so the
harness on disk matches the binary that will drive it:

- `.claude/skills/tdd-drive/SKILL.md`
- `.claude/hooks/tdd_stop_hook.py` and `.claude/hooks/tdd_bash_hook.py` (the
  `tdd_` prefix keeps them clear of your own hooks)
- `.claude/settings.json`, wiring both hooks, but **only if the file does not
  exist yet**. An existing one is never edited. If it does not already wire the
  hooks, init reports `harness.settings: "not_written"` and hands you the stanza
  in `result.harness.settings_stanza` to merge yourself.

It also writes `tdd.toml` when there is none, and keeps an existing one unless
you pass `--force`.

A harness file that differs from this version's copy (an older skill, or one you
customised) is never overwritten: init refuses with `harness_files_differ` and
names it. `tdd init --skill claude-code --update-skill` replaces it; re-apply any
local additions afterwards. `--force` only ever means `tdd.toml`.

### By hand

Copy `stop_hook.py` and `bash_hook.py` to `.claude/hooks/tdd_stop_hook.py` and
`.claude/hooks/tdd_bash_hook.py`, and add to `.claude/settings.json`:

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"$CLAUDE_PROJECT_DIR/.claude/hooks/tdd_stop_hook.py\""
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"$CLAUDE_PROJECT_DIR/.claude/hooks/tdd_bash_hook.py\""
          }
        ]
      }
    ]
  }
}
```

`$CLAUDE_PROJECT_DIR` keeps the hooks reachable after the agent `cd`s into a
subdirectory.
