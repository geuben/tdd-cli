---
closes: 74
cycles:
  - n: 1
    project: tddcli
    title: "TDD_EXECUTOR_MODEL resolves with source declared"
    test: "tests/test_executor_attribution.py::test_env_override_resolves_as_declared"
    files: ["src/tddcli/identity.py"]
    commit_red: "test: TDD_EXECUTOR_MODEL yields source declared"
    commit_green: "feat: harness-declared executor identity via TDD_EXECUTOR_MODEL"

  - n: 2
    project: tddcli
    title: "the declared override wins over a readable transcript"
    test: "tests/test_executor_attribution.py::test_declared_override_beats_transcript"
    files: ["src/tddcli/identity.py"]
    commit_red: "test: declared identity overrides transcript detection"
    commit_green: "feat: declared executor identity takes precedence"

  - n: 3
    project: tddcli
    title: "resolve records why detection failed: session env missing"
    test: "tests/test_executor_attribution.py::test_reason_names_the_missing_session_env"
    files: ["src/tddcli/identity.py"]
    commit_red: "test: unknown executor carries the missing-env reason"
    commit_green: "feat: Executor.reason — CLAUDE_CODE_SESSION_ID not set"

  - n: 4
    project: tddcli
    title: "resolve records why detection failed: transcript not found"
    test: "tests/test_executor_attribution.py::test_reason_names_the_missing_transcript"
    files: ["src/tddcli/identity.py"]
    commit_red: "test: unknown executor carries the no-transcript reason"
    commit_green: "feat: reason names the session whose transcript was not found"

  - n: 5
    project: tddcli
    title: "resolve records why detection failed: transcript has no model line"
    test: "tests/test_executor_attribution.py::test_reason_names_the_model_less_transcript"
    files: ["src/tddcli/identity.py"]
    commit_red: "test: unknown executor carries the no-model-record reason"
    commit_green: "feat: reason distinguishes a model-less transcript from a missing one"

  - n: 6
    project: tddcli
    title: "run start records an executor_unknown event with the reason"
    test: "tests/test_executor_attribution.py::test_run_start_records_executor_unknown_event"
    files: ["src/tddcli/cli.py"]
    commit_red: "test: an unattributed run leaves an executor_unknown event"
    commit_green: "feat: run start logs executor_unknown with the detection reason"

  - n: 7
    project: tddcli
    title: "the run start envelope surfaces the attribution warning"
    test: "tests/test_executor_attribution.py::test_run_start_envelope_carries_executor_warning"
    files: ["src/tddcli/cli.py"]
    commit_red: "test: run start result warns when the executor is unknown"
    commit_green: "feat: executor_warning in the run start envelope"

  - n: 8
    project: tddcli
    title: "doctor reports executor identity and the failure reason informationally"
    test: "tests/test_executor_attribution.py::test_doctor_reports_executor_identity"
    files: ["src/tddcli/cli.py"]
    commit_red: "test: doctor names the executor-identity diagnosis"
    commit_green: "feat: informational executor identity check in doctor"
---

# Issue #74 — transcript-based executor attribution intermittently records unknown

https://github.com/geuben/tdd-cli/issues/74
Task file: `tasks/issue-74-executor-attribution.md`

## Context

Across eight consecutive real runs, six recorded `Executor: unknown (source: unknown)`
and the failure was silent — after the fact there is no way to say which model executed
which run, which is the audit trail `executor_model`/`executor_source` exist for.
**Root cause located during planning** (read-only ledger inspection): every `unknown`
run in this repo's ledger also has an **empty `executor_session`** — `CLAUDE_CODE_SESSION_ID`
was not set in those environments — while every attributed run has one. Detection did
not regress; those launches never carried the session env at all.

This plan makes the failure diagnosable and overridable, per the issue's three bullets:
`identity.resolve` records *why* it fell back (`Executor.reason`: env missing /
transcript not found / no model line); a harness that knows the answer sets
`TDD_EXECUTOR_MODEL`, recorded with `source: declared`; and the gap is surfaced at the
moment it can still be fixed — an `executor_unknown` integrity event plus a warning in
the `run start` envelope, and an informational executor-identity line in `tdd doctor`.

## Design decisions (locked)

- **`TDD_EXECUTOR_MODEL` is the only `declared` channel** (user decision): the existing
  `run start --executor` flag keeps `source: "human"` — its help text and R5.2 define it
  as the human fallback, and the metrics keep three distinguishable trust levels:
  transcript-observed, harness-declared, human-typed.
- **Declared wins over transcript** (user decision): an explicit override overrides, and
  this also fixes the documented subagent limitation (a subagent inherits its parent's
  `CLAUDE_CODE_SESSION_ID` and would be transcript-attributed to the parent's model —
  the spawning harness knows better). The risk of a lying agent is labeled, never
  hidden: `source` says `declared`, not `transcript`. Resolution order:
  `TDD_EXECUTOR_MODEL` → transcript → `--executor` human label → unknown.
- **`Executor` gains `reason: str | None = None`** (evidence: the dataclass is consumed
  only by `cmd_run_start`, which reads `model`/`session`/`source` — an additive field
  breaks nothing). `reason` is set on every non-transcript resolution path with one of
  three messages: the session env is not set; no transcript for session `<id>` under
  `TRANSCRIPT_ROOT`; the transcript at `<path>` contains no model records.
- **The doctor check is informational — always `ok`** (evidence: `implement-issue`
  plans gate on `doctor` reporting `healthy: true`, and human-labelled or
  harness-declared runs are legitimate; a failing check would brick those machines).
  It reports `<source>: <model>` and appends the reason when the source is `unknown`.
- **The run-start warning is an integrity event plus an envelope field**, not a refusal
  (the issue says "warn"): `executor_unknown` (run-scoped, `cycle_id=None`, detail =
  the reason) and `result.executor_warning` in the success envelope. Existing plumbing
  already stores `executor.source` verbatim on the run row — no schema change.

## Verified repo facts

*Anchors are symbol names — grep for them; no line numbers in this plan.*

- **Probed live** (this session): with the session env and transcript present,
  `identity.resolve` returns `('claude-fable-5', source='transcript')`; **with
  `TDD_EXECUTOR_MODEL=harness-model` set it is ignored** (transcript still wins, and
  with the session env deleted the result is `unknown`/`unknown`); the `Executor`
  instance **has no `reason` attribute**. These are cycles 1–3's expected failures.
- **Read-only ledger inspection**: this repo's ledger holds runs 4–8 as
  `unknown|unknown` with empty `executor_session`, and runs 9–11 as
  `claude-sonnet-4-6|transcript` with sessions — the missing-env failure mode, not a
  parse regression.
- **The identity module** (`identity.py`): `resolve(project_path, human_label)` reads
  `CLAUDE_CODE_SESSION_ID`, finds the transcript via `_find_transcript` (slug-scoped
  path, then a `TRANSCRIPT_ROOT` glob), reads the last model record via
  `_model_from_transcript`, falls back to the human label, then to
  `Executor("unknown", session, "unknown")`. All harness coupling lives here (R5.1);
  the only production caller is `cmd_run_start` (`executor = identity.resolve(worktree,
  args.executor)` feeding `executor_model/session/source` into the run insert and the
  started-envelope detail).
- **Doctor structure** (`cmd_doctor`): a `checks, check = _doctor_checklist()` pair;
  `check(name, ok, detail, project=None)` appends to the envelope's `result.checks`.
  The identity check lands after the ledger checks, before the per-project loop.
- **Test harness for identity** (`tests/test_snapshot_and_identity.py`): monkeypatch
  `identity.TRANSCRIPT_ROOT` and `CLAUDE_CODE_SESSION_ID`, write
  `<root>/<slug>/<session>.jsonl` with `{"model": ...}` lines. The new unit cycles copy
  this pattern; e2e cycles use the conftest `repo` fixture + `run_cli` (in-process, so
  `monkeypatch.setattr(identity, "TRANSCRIPT_ROOT", ...)` and `delenv` reach the CLI).
  Cycles 6–8 must `delenv` both `CLAUDE_CODE_SESSION_ID` and `TDD_EXECUTOR_MODEL` and
  point `TRANSCRIPT_ROOT` at an empty directory so resolution is deterministically
  unknown regardless of the developer's environment.
- **Blast radius: empty.** Existing identity tests
  (`test_model_is_read_from_the_session_transcript`,
  `test_human_label_is_the_fallback_not_the_default`,
  `test_last_model_wins_when_a_session_switches`) do not set `TDD_EXECUTOR_MODEL`, and
  the `--executor` flag's semantics are unchanged — `modifies_tests` is empty for every
  cycle. Integrity-event readers (`render.py`, `metrics`) render new event kinds
  generically.
- **Suite is green now**: 406 passed on this branch. Expected `run start` baseline:
  `{"tddcli": 0}` — anything else means a moved branch; stop.
- **Lint is ruff-only, no typecheck**; every RED fails at runtime (assertion or
  in-test `AttributeError`), never at collection — **no cycle needs `stub_expected`**.

## Cycle detail

*Single project `tddcli`; tests in a new `tests/test_executor_attribution.py`. Unit
cycles (1–5) monkeypatch env + `TRANSCRIPT_ROOT`; e2e cycles (6–8) run on the `repo`
fixture with resolution forced unknown. Minimum GREEN throughout.*

**Cycle 1 — the env override resolves as declared.** Test (unit): `setenv
TDD_EXECUTOR_MODEL=harness-model`, `delenv CLAUDE_CODE_SESSION_ID`, `TRANSCRIPT_ROOT` →
nowhere; assert `identity.resolve(None)` has `model == "harness-model"` and
`source == "declared"`. *EXPECTED FAILURE (probed):* today the result is
`unknown`/`unknown` — `AssertionError`. *GREEN:* read `TDD_EXECUTOR_MODEL` in
`resolve`; when set, return `Executor(model=env, session=<env session or None>,
source="declared")`. Production target: `identity.resolve`.

**Cycle 2 — declared beats transcript.** Test (unit): full transcript fixture (the
`test_model_is_read_from_the_session_transcript` shape) **plus**
`TDD_EXECUTOR_MODEL=harness-model`; assert `source == "declared"` and
`model == "harness-model"`. *EXPECTED FAILURE (probed):* transcript wins today —
`source == "transcript"`. *GREEN:* the declared check moves ahead of transcript
detection (if cycle 1's minimal GREEN placed it later). Production target:
`identity.resolve`.

**Cycle 3 — reason: session env missing.** Test (unit): `delenv` both env vars,
`TRANSCRIPT_ROOT` → nowhere; `e = identity.resolve(None)`; assert
`"CLAUDE_CODE_SESSION_ID" in e.reason`. *EXPECTED FAILURE (probed):*
`AttributeError: 'Executor' object has no attribute 'reason'`. *GREEN:* add
`reason: str | None = None` to `Executor`; set the missing-env message on that path.
Production targets: `identity.Executor`, `identity.resolve`.

**Cycle 4 — reason: transcript not found.** Test (unit): session env set to
`sess-gone`, `TRANSCRIPT_ROOT` → an existing empty directory; assert `e.reason`
mentions `sess-gone` (no transcript found). *EXPECTED FAILURE:* cycle 3's minimal GREEN
sets `reason` only on the missing-env branch, so `reason is None` here —
`AssertionError` (`TypeError: argument of type 'NoneType'` counts as the same failing
test if asserted with `in`; assert `e.reason and "sess-gone" in e.reason`). *GREEN:*
set the no-transcript message when `_find_transcript` returns `None`. Production
target: `identity.resolve`.

**Cycle 5 — reason: transcript without a model record.** Test (unit): write the
session's transcript containing only model-less lines (e.g. `{"type": "user"}`); assert
`e.reason` mentions the transcript containing no model records. *EXPECTED FAILURE:*
after cycle 4 the transcript is found, so its branch sets no reason — `reason is None`.
*GREEN:* set the no-model message when `_model_from_transcript` returns `None`.
Production target: `identity.resolve`.

**Cycle 6 — run start logs `executor_unknown`.** Test (e2e): `repo` fixture; `delenv`
both env vars and point `identity.TRANSCRIPT_ROOT` at an empty tmp dir
(`monkeypatch.setattr`); register + `run start`; read
`Ledger(repo).all("SELECT detail FROM integrity_event WHERE kind = 'executor_unknown'")`
and assert one row whose detail mentions `CLAUDE_CODE_SESSION_ID`. *EXPECTED FAILURE:*
no such event kind exists — zero rows, `AssertionError`. *GREEN:* in `cmd_run_start`,
after the run insert (where `run_id` exists — the event-block landmark shared with
`plan_blob_changed`), when `executor.source == "unknown"`:
`ledger.event(run_id, None, "executor_unknown", executor.reason or "")`. Production
target: `cmd_run_start`.

**Cycle 7 — the envelope warns.** Test (e2e): same setup; assert the `run start`
envelope's `result["executor_warning"]` is truthy and mentions
`CLAUDE_CODE_SESSION_ID`. *EXPECTED FAILURE:* the key is absent —
`result.get("executor_warning")` is `None`, `AssertionError`. *GREEN:* include
`executor_warning=executor.reason` in the success envelope's result when the source is
`unknown` (omit otherwise). Production target: `cmd_run_start`.

**Cycle 8 — doctor names the diagnosis.** Test (e2e): same forced-unknown setup (no
run needed); `run_cli(repo, "doctor")`; find the check named `"executor identity"` in
`result["checks"]` and assert its detail mentions `unknown` and
`CLAUDE_CODE_SESSION_ID`, and that `result["healthy"]` is still `True`. *EXPECTED
FAILURE:* no check with that name exists — `AssertionError` (StopIteration guarded by
`next(..., None)` + assert). *GREEN:* in `cmd_doctor`, after the ledger checks:
`ex = identity.resolve(worktree)`; `check("executor identity", True, ...)` with
`f"{ex.source}: {ex.model}"`, appending ` — {ex.reason}` when the source is `unknown`.
Always `ok=True` — informational by decision. Production target: `cmd_doctor`.

## Deliberate scope cuts (do not build)

- **No e2e pin that a declared run stores `source: "declared"` on the run row.**
  Premise: `cmd_run_start` already stores `executor.model/session/source` verbatim
  (existing generic plumbing, exercised by every e2e run in the suite); cycles 1–2
  prove the resolution, and no new storage code exists to test. *Re-evaluation
  trigger:* if during execution any run-row consumer turns out to special-case source
  values, stop and add the pin rather than absorbing a fix.
- **No refusal on unknown attribution.** The issue asks to *warn*; human- and
  fallback-mode usage stays legal. A strict mode (`run start --require-attribution`)
  is a possible follow-up, not built here.
- **`--executor` semantics unchanged** (user decision): it remains the human fallback
  (`source: "human"`); no new flag is added — the env var is the harness channel.
- **No root-cause fix for the original missing-env launches** — that is a harness
  configuration matter (the launcher must export `CLAUDE_CODE_SESSION_ID` or set
  `TDD_EXECUTOR_MODEL`); this plan makes the gap visible and overridable, which is the
  issue's ask.
- **No transcript-format hardening** beyond the existing parser — the ledger evidence
  shows the failures were env-absence, not parse failures; `reason` will say so if
  that ever changes.
- **Mirrors: none** — identity resolution lives once in `identity.py` (R5.1 pins all
  harness coupling there); no `docs/INVARIANTS.md` registry exists in this repo.
- **README/PRD documentation** is a post-run doc follow-up, not a cycle (see
  Done-criteria).

## Execution

This plan is executed through `tdd-cli`. **You run every command below yourself** — do
not ask the user to start the run. `tdd run start` records which model is executing,
resolved from your own session; a run started by anyone else attributes this work to
the wrong agent.

**Referee rule:** run the *released* tdd-cli **0.8.0** at `~/.local/bin/tdd` (the
`uv tool` install), never a working-tree editable install. On this machine plain `tdd`
on PATH resolves to an editable venv importing from this working tree — check
`which tdd` and use the full path `~/.local/bin/tdd` in every command below if it is
not already first. Verify: `~/.local/bin/tdd --version` → `tdd-cli 0.8.0`. This plan
adds no ledger schema and uses only 0.8.0-supported front-matter keys. Do **not**
export `TDD_EXECUTOR_MODEL` in your own shell — your run must be transcript-attributed.

    git checkout -b feat/74-executor-attribution   # first, before anything else
    ~/.local/bin/tdd doctor                        # must report healthy: true
    ~/.local/bin/tdd run start --plan tasks/issue-74-executor-attribution.md

If the branch already exists, do not force-checkout and do not pick another name: check
it out only if it carries this plan's commit and no unrelated work, otherwise stop and
ask. If `tdd doctor` fails on *other* uncommitted `tasks/issue-*.md` files (sibling
plans), commit, stash, or gitignore them before `run start`.

Then repeat until done: read `next_action.verb`, do exactly what it says, run
`~/.local/bin/tdd advance`. Stop when `next_action.terminal` is `true`.

When `next_action.terminal` is `true`, finish the run: render the friction log, commit
it, and raise the PR — see Done-criteria below.

- `tdd advance` is the only command that changes phase; the tool stages and commits
  from the phase — do not `git add`/`git commit` yourself.
- Expected baseline for this repo: `{"tddcli": 0}` — anything else means a moved
  branch; stop.
- This plan declares **no `annotation_keys`**, so `annotate_cycle` will not appear. All
  eight cycles are standard: `write_test` → `write_code` → optional refactor. A cycle
  whose test unexpectedly passes on arrival drives `run_sensitivity_check` →
  `~/.local/bin/tdd sensitivity begin|check|end`. If blocked, `resolve_blocker` →
  `tdd blocker --kind --detail` (kinds: `plan_defect`, `tooling`, `regression`,
  `pre_existing_failure`); `confirm_cycle_applicable` on a cycle the code has
  outgrown → `tdd cycle skip --reason`.

## Done-criteria

**Before finishing:** run
`~/.local/bin/tdd log render --out tasks/friction-logs/issue-74-executor-attribution-friction.md`
(the `tasks/friction-logs/` at the **repository root**) and `~/.local/bin/tdd metrics`.
Report the plan-fidelity section — declared vs delivered vs skipped — and every
integrity event. Do not narrate what the ledger already records.

Then the documentation follow-up, committed as ordinary commits after the run is
terminal: in `docs/PRD.md` (§5.1 executor identity and the integrity-event table) and
`docs/harness-integration.md`, document `TDD_EXECUTOR_MODEL` (`source: declared`, wins
over transcript), `Executor.reason`, the `executor_unknown` event, the envelope
warning, and the doctor line.

Then commit the friction log and raise the PR:

    git add tasks/friction-logs/issue-74-executor-attribution-friction.md
    git commit -m "docs: friction log for issue-74-executor-attribution"

Then invoke the **`raise-pr` skill** (`/raise-pr`), which runs the quality gates,
pushes the branch and opens the PR against `main`. Do not push or call the GitHub API
by hand. If a gate fails, fix it and re-run the skill — a failed gate is work, not a
reason to hand back.
