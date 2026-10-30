# Claude Code skill for tdd-cli

`SKILL.md` is a complete driving skill for [Claude Code](https://docs.anthropic.com/en/docs/claude-code):
it dispatches on `next_action.verb` from each envelope, writes only tests and
implementation, and leaves suites, phase, and commits to the tool. The contract it
implements is [`docs/harness-integration.md`](../../../docs/harness-integration.md).

## Installation

```sh
tdd init --skill claude-code
```

That writes the skill, the hooks and their wiring together, from the copies installed
with `tdd`, so the skill on disk is the one written for the binary that will drive it.
See [`../../claude-code-hooks/README.md`](../../claude-code-hooks/README.md) for what it
writes and what it leaves alone.

By hand, the skill alone:

```sh
mkdir -p .claude/skills/tdd-drive
cp SKILL.md .claude/skills/tdd-drive/
```

Then in a session:

```
/tdd-drive tasks/my-plan.md
```

Pair it with the hooks in [`../../claude-code-hooks/`](../../claude-code-hooks/): the skill
deliberately contains no stopping instructions, so without a Stop hook nothing prevents
the agent from ending its turn mid-run.

## Adapting it

The skill is written against `verb_set_version: 2` and `envelope_version: 1`, and
refuses to run against anything newer — extend the verb table rather than deleting the
check. Project conventions (where plans live, what annotations mean, friction-log
destinations) belong in additions to the verb entries, not in new state or stop rules.

Keep the `metadata.verb_set_version` and `metadata.envelope_version` front-matter when
customising: `tdd doctor` compares them with what the binary emits and names a skill that
has drifted. `tdd init --skill claude-code --update-skill` replaces it with the current
copy; re-apply your additions afterwards.
