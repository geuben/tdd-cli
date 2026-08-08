# Claude Code handoff skill for tdd-cli

`SKILL.md` is a plan-hardening skill for [Claude Code](https://docs.anthropic.com/en/docs/claude-code):
it audits a draft implementation plan against the codebase, probes its RED paths
empirically, authors the YAML front-matter contract, and validates it with
`tdd plan register` — before the plan is handed to a lesser agent for unsupervised
execution. It is the planning-side counterpart to the driving skill in
[`../claude-code-skill/`](../claude-code-skill/): the hardener registers the plan; the
executor starts and drives the run.

## Installation

```sh
mkdir -p .claude/skills/tdd-handoff
cp SKILL.md .claude/skills/tdd-handoff/
```

Then in a session:

```
/tdd-handoff tasks/my-plan.md
```

## Why a separate skill

A minimal-GREEN executor treats the plan's named test list as the entire spec —
everything not pinned by a test is dropped, and everything declared wrongly in the
contract reopens a hole the tool would otherwise close. Registration hard-fails on a
malformed contract by design; this skill is the process that produces contracts which
register cleanly *and* mean what they say. The failure model it hardens against is
documented inline, and the contract vocabulary it emits is the one exercised by
[`../plan.md`](../plan.md).

## Adapting it

The skill emits an Execution section for the executor verbatim; deliberately, it
contains no control flow beyond `next_action` — see the harness rules in
[`docs/harness-integration.md`](../../docs/harness-integration.md). Project
conventions (where plans and friction logs live, PR workflow, extra annotation keys)
belong in the contract's `annotation_keys` and the done-criteria block, not in new
stop rules.
