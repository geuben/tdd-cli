# Driving tdd-cli from an agent harness

The tool is deliberately half of a system. It computes phase from observed test
execution, stages, commits, and records — but it cannot compel an agent to do anything.
The other half lives in the harness, in two parts:

- **A skill** (prompt, instruction file, system message — whatever your harness calls
  it) that tells the agent *how* to respond to each `next_action` the tool emits.
- **Hooks** that enforce stop conditions the skill must never contain. Ready-made
  Claude Code hooks live in [`examples/claude-code-hooks/`](../examples/claude-code-hooks/).

This document is about writing the skill. A complete, runnable Claude Code skill built
from it lives in [`examples/claude-code-skill/`](../examples/claude-code-skill/).

## The envelope

Every command prints one JSON envelope on stdout:

```json
{
  "ok": true,
  "envelope_version": 1,
  "run": {"id": 3, "plan": "tasks/plan.md", "cycle": 2, "of": 9,
          "phase": "AWAITING_IMPL", "executor": "claude-sonnet-5"},
  "result": {"commit": "80217e8ab", "staged": ["backend/tests/test_add.py"]},
  "next_action": {
    "verb": "write_implementation",
    "detail": "RED confirmed. Write the minimum code to pass ... then `tdd advance`.",
    "terminal": false,
    "verb_set_version": 2
  }
}
```

Two fields carry authority; the rest is context:

- **`next_action.verb`** — a member of a closed, versioned set. This is the single
  authority on control flow. Dispatch on it and nothing else.
- **`next_action.terminal`** — `true` only for `complete` and `blocked`. This is the
  only signal that the loop is over.

**`detail` is prose for humans and is explicitly non-authoritative.** It restates what
the verb already means, names the concrete target, and quotes the language idiom for
stubs. Show it to the agent as context; never parse it, match on it, or branch on it.

Check `envelope_version` and `verb_set_version` once at loop start. If either is newer
than the skill was written for, stop and say so — guessing at an unknown verb is worse
than halting.

## The loop

Every skill reduces to the same loop, portable to any harness that can run a command
and parse JSON:

```
envelope = run("tdd status")
while not envelope.next_action.terminal:
    act on envelope.next_action.verb        # write a test, write code, or run the named tdd command
    envelope = run("tdd advance")           # or the specific command the verb names
report(envelope)
```

The agent's entire job is the `act` line: writing tests and implementation, and
invoking the specific `tdd` subcommands some verbs name. Everything else — running
suites, deciding phase, staging, committing, recording — is the tool's job, and a
skill that duplicates any of it will fight the ledger.

## The verb set (version 2)

| verb | the tool observed | the agent must |
|---|---|---|
| `write_test` | the cycle needs its test (or the test still fails to fail correctly) | write the declared target test — for a pin cycle, a characterisation test that passes on arrival — then `tdd advance` |
| `create_stub` | the target test cannot be collected: the module it imports does not exist | create the declared stub file(s) with no logic — the `detail` quotes the language's idiom — then `tdd advance` |
| `write_implementation` | RED is confirmed and committed | write the minimum code to pass the target, then `tdd advance` |
| `fix_regression` | tests outside the cycle are failing, or the close sweep / lint / typecheck gates failed | fix them without breaking the target, then `tdd advance` |
| `run_sensitivity_check` | a test passed where proof it *can* fail is required | `tdd sensitivity begin`, mutate the behaviour under test, `tdd sensitivity check`, then `tdd sensitivity end` |
| `name_target_test` | several new tests appeared; a cycle covers one behaviour | pick the intended one: `tdd target <id>` |
| `refactor_or_advance` | GREEN is committed, or the tool simply wants `tdd advance` next | refactor only if the plan calls for it, then `tdd advance` |
| `confirm_cycle_applicable` | a judgement point outside the cycle loop: config scaffolded, no active run, doctor passed | review / register / start as the `detail` names; if a cycle no longer applies, `tdd cycle skip --reason "..."` |
| `annotate_cycle` | the plan requires judgement annotations before the cycle closes | `tdd annotate --key <k> --value "..."` for each missing key, then `tdd advance` |
| `resolve_blocker` | wedged: three unchanged retries, or failing environment checks | fix the cause, or record it: `tdd blocker --kind <kind> --detail "..."` |
| `await_baseline` | baseline collection is in flight | poll `tdd progress`; **never** re-run `tdd run start` |
| `complete` *(terminal)* | the run (or command) is finished | render the friction log if the `detail` asks, then stop |
| `blocked` *(terminal)* | a typed blocker was recorded | surface the blocker to the human and stop |

Adding a verb is a specification change and bumps `verb_set_version`.

## Volunteering judgement

`annotate_cycle` fires only for keys the plan requires. But the friction log's value to
the *next* plan depends on judgement the tool cannot observe, so the skill should tell
the agent to volunteer annotations at the moment of discovery — they attach to the open
cycle, so batching them at the end records them against the wrong one:

- `plan_defect` — the plan disagreed with the codebase: a declared test target that
  had to be adopted, behaviour already implemented, wrong file, stale line numbers.
- `friction_note` — tooling or environment cost attempts that the code did not.
- `unplanned_change` / `new_work_raised` — scope the cycle absorbed or deferred.

Run-level narrative (post-run CI failures, patterns spanning cycles) has no cycle to
attach to: append it as markdown below the rendered friction log after `tdd log render`.
Rendered sections are projections from the ledger; appended prose is unverified opinion,
and auditors should read the two accordingly.

## Rules for the skill

1. **Dispatch on the verb, never on the prose.** The `detail` string may be reworded in
   any release without a version bump; the verb set cannot.
2. **No stopping instructions.** The skill describes *how* to do work. Whether the
   agent may stop belongs to `terminal` and to a Stop hook — a skill that says "stop
   after N attempts" re-creates the self-reporting the tool exists to remove.
3. **Don't do the tool's job.** The skill must not commit, must not run
   `pytest`/`vitest` directly (the bash hook enforces this), must not reason about
   which phase the run is in, and must not edit `tdd.toml` mid-run (the change is
   recorded as `config_changed`). Suites run only through `tdd advance`.
4. **`--retry` is for the environment, not the code.** `tdd advance --retry` re-runs an
   unchanged tree; use it for flaky or environmental failures only. If nothing changed
   because the agent is stuck, the answer is `resolve_blocker`, not retries.
5. **Recover with `tdd status`, not memory.** After a crash, a compaction, or an
   inherited worktree, one `tdd status` call reconstructs the position. The skill
   should never carry its own record of where the run is.

## What not to build

The predecessor of this tool was a skill that kept its own state file: the agent wrote
a phase into a JSON file, a wrapper skill read it back, and stop conditions lived in
the prompt. Every failure class in the README's *Why* section came from that shape.
The test of a good skill is that it contains **no state, no phase names, and no stop
conditions** — only responses to verbs.
