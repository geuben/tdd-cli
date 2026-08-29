---
name: tdd-drive
description: Drive a tdd-cli run to completion. Dispatches on next_action.verb from each JSON envelope, writes only tests and implementation, and lets the tool run suites, decide phase, and commit.
argument-hint: [<plan-path>]
---

You are driving a `tdd-cli` run. The tool decides everything about process state; you
write tests and code. Full contract: `docs/harness-integration.md` in the tdd-cli
repository.

## Hard rules

- Never run `pytest`, `vitest`, or any test command directly — suites run only through
  `tdd advance`.
- Never commit; the tool commits.
- Never edit `tdd.toml` or the plan file while a run is live.
- Act only on `next_action.verb`. Read `detail` for context (it names the concrete
  target and, for stubs, the language idiom) but never branch on its wording.
- If `next_action.verb_set_version` is not `2` or `envelope_version` is not `1`,
  stop and report that this skill predates the installed tdd-cli.

## Loop

1. Run `tdd status` and parse the JSON envelope.
   - If there is no active run and a plan path was given:
     `tdd plan register <plan>` then `tdd run start --plan <plan>`.
   - If `run start` is slow, run it in the background — a baseline probe can take
     minutes, and re-running it is refused with `baseline_in_progress`.
2. Act on `next_action.verb` (table below).
3. Run `tdd advance` (or the specific command the verb names) and parse the new
   envelope.
4. Repeat from 2 until `next_action.terminal` is true, then report the final envelope.

## Verbs

- **write_test** — write the target test named in `run`/`result`. One behaviour, in the
  declared test file. For a pin cycle, write a characterisation test of *existing*
  behaviour; it should pass as written. Then `tdd advance`.
- **create_stub** — the test imports a module that does not exist. Create exactly the
  declared stub file(s) with no logic, using the idiom quoted in `detail`. Then
  `tdd advance`.
- **write_implementation** — write the minimum code to pass the target test. Resist
  generalising past the test. Then `tdd advance`.
- **fix_regression** — `result` lists failing tests outside this cycle (or failing
  lint/typecheck gates). Fix them without weakening the target. Then `tdd advance`.
- **run_sensitivity_check** — `tdd sensitivity begin`; make one small mutation to the
  behaviour under test; `tdd sensitivity check`; then `tdd sensitivity end` (it
  verifies the restore is byte-identical).
- **name_target_test** — several new tests appeared; `result.candidates` lists them.
  Pick the one this cycle is about: `tdd target <id>`.
- **refactor_or_advance** — refactor only if the plan's cycle calls for one; otherwise
  just `tdd advance`.
- **confirm_cycle_applicable** — a judgement point: do what `detail` names (review
  config, register a plan, start a run). If the current cycle no longer applies to the
  codebase, `tdd cycle skip --reason "<why>"`.
- **annotate_cycle** — for each key in `result.missing_annotations`:
  `tdd annotate --key <k> --value "<your judgement>"`. Then `tdd advance`.
- **resolve_blocker** — you are wedged. If you can see the cause, fix it; otherwise
  `tdd blocker --kind <kind> --detail "<what and why>"` and report it.
- **await_baseline** — poll `tdd progress` until the baseline completes. Never re-run
  `tdd run start`.
- **complete** / **blocked** — terminal. Report the outcome; if `detail` asks for it,
  run `tdd log render` first.

## Judgement annotations — volunteer these

Annotations attach to the **open** cycle: record them the moment you notice, not at the
end of the run.

- The plan disagreed with the codebase (target adopted, behaviour already implemented,
  wrong file or stale line numbers): `tdd annotate --key plan_defect --value "..."`.
- Tooling or environment cost you attempts the code didn't:
  `tdd annotate --key friction_note --value "..."`.
- The cycle absorbed undeclared scope, or surfaced follow-up work:
  `--key unplanned_change` / `--key new_work_raised`.

To capture *why* something happened — a plan assumption that proved wrong, the reason an
integrity event fired — use `tdd note "<text>"` at the moment you know. A note written
during an open cycle is stamped with that cycle and phase and appears in the friction log
as a blockquote alongside the cycle's telemetry. After the run ends, `tdd note` attaches
at run level and renders in a dedicated **Executor narrative** section. Notes are unverified
by design; write them as claims, not measurements.

Narrative that spans cycles or happened after the run (CI failures, patterns) goes as
`tdd note` after the run ends, or as markdown appended below the rendered friction log
after `tdd log render` — never into a cycle annotation it doesn't belong to.

## When a suite run changes nothing

`no_change_since_last_run` in an envelope means the tree is identical to the last run.
Change the code, or — only for a flaky or environmental failure — `tdd advance --retry`.
Three unchanged retries produce `resolve_blocker`; do not try to outlast it.

## Recovery

After any interruption (crash, compaction, inherited worktree): `tdd status`, then
re-enter the loop at step 2. Never reconstruct position from conversation memory —
the ledger's answer is the only true one. `tdd resume` handles a run interrupted by a
human intervention.
