# Claude Code skill for tdd-cli

`SKILL.md` is a complete driving skill for [Claude Code](https://docs.anthropic.com/en/docs/claude-code):
it dispatches on `next_action.verb` from each envelope, writes only tests and
implementation, and leaves suites, phase, and commits to the tool. The contract it
implements is [`docs/harness-integration.md`](../../docs/harness-integration.md).

## Installation

```sh
mkdir -p .claude/skills/tdd-drive
cp SKILL.md .claude/skills/tdd-drive/
```

Then in a session:

```
/tdd-drive tasks/my-plan.md
```

Pair it with the hooks in [`../claude-code-hooks/`](../claude-code-hooks/): the skill
deliberately contains no stopping instructions, so without a Stop hook nothing prevents
the agent from ending its turn mid-run.

## Adapting it

The skill is written against `verb_set_version: 2` and `envelope_version: 1`, and
refuses to run against anything newer — extend the verb table rather than deleting the
check. Project conventions (where plans live, what annotations mean, friction-log
destinations) belong in additions to the verb entries, not in new state or stop rules.
