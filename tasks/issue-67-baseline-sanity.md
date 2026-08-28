---
closes: 67
cycles:
  - n: 1
    project: tddcli
    title: "a large, mostly-red baseline is refused as implausible"
    test: "tests/test_baseline_sanity.py::test_a_mostly_red_baseline_is_refused"
    files: ["src/tddcli/cli.py"]
    commit_red: "test: run start refuses an implausible mostly-red baseline"
    commit_green: "feat: refuse a baseline whose failing ratio exceeds the threshold"

  - n: 2
    project: tddcli
    title: "--accept-baseline overrides the implausibility refusal"
    test: "tests/test_baseline_sanity.py::test_accept_baseline_overrides_the_refusal"
    files: ["src/tddcli/cli.py"]
    commit_red: "test: --accept-baseline lets an implausible baseline through"
    commit_green: "feat: --accept-baseline bypasses the implausibility gate"

  - n: 3
    project: tddcli
    pin_cycle: true
    title: "a small all-red suite is exempt from the gate"
    test: "tests/test_baseline_sanity.py::test_a_small_all_red_suite_is_not_refused"
    commit_pin: "test: pin the small-suite exemption from the baseline gate"

  - n: 4
    project: tddcli
    title: "per-project baseline_max_failure_ratio overrides the default"
    test: "tests/test_baseline_sanity.py::test_project_ratio_config_raises_the_threshold"
    files: ["src/tddcli/config.py", "src/tddcli/cli.py"]
    commit_red: "test: a project's baseline_max_failure_ratio suppresses the refusal"
    commit_green: "feat: honour per-project baseline_max_failure_ratio from tdd.toml"

  - n: 5
    project: tddcli
    title: "an accepted implausible baseline records an audit event"
    test: "tests/test_baseline_sanity.py::test_accepted_implausible_baseline_records_an_event"
    files: ["src/tddcli/cli.py"]
    commit_red: "test: an accepted implausible baseline logs baseline_accepted"
    commit_green: "feat: emit a baseline_accepted integrity event on override"

  - n: 6
    project: tddcli
    pin_cycle: true
    title: "a healthy large baseline is recorded without refusal or event"
    test: "tests/test_baseline_sanity.py::test_a_healthy_baseline_is_recorded_untouched"
    commit_pin: "test: pin that a healthy baseline is untouched by the gate"

  - n: 7
    project: tddcli
    title: "Ledger.previous_baseline returns the prior run's failing set for a project"
    test: "tests/test_snapshot_and_identity.py::test_previous_baseline_returns_prior_runs_failing_set"
    files: ["src/tddcli/ledger.py"]
    commit_red: "test: previous_baseline reads the last earlier run's failing set"
    commit_green: "feat: Ledger.previous_baseline joins baseline to run by worktree"

  - n: 8
    project: tddcli
    title: "run start emits a standing-failure delta against the previous run"
    test: "tests/test_baseline_sanity.py::test_non_empty_baseline_emits_standing_delta"
    files: ["src/tddcli/cli.py"]
    commit_red: "test: a non-empty baseline logs new-vs-inherited standing failures"
    commit_green: "feat: emit baseline_standing_delta partitioning new vs inherited"

  - n: 9
    project: tddcli
    pin_cycle: true
    title: "a first run with no prior baseline reports every failure as new"
    test: "tests/test_baseline_sanity.py::test_first_run_reports_all_standing_failures_new"
    commit_pin: "test: pin the no-prior-baseline delta path"

  - n: 10
    project: tddcli
    title: "health_command parses onto a project from tdd.toml"
    test: "tests/test_config_and_staging.py::test_health_command_parses_onto_project"
    files: ["src/tddcli/config.py"]
    commit_red: "test: a project's health_command parses onto Project"
    commit_green: "feat: Project.health_command parsed and validated from tdd.toml"

  - n: 11
    project: tddcli
    title: "run start refuses when a project's health_command fails"
    test: "tests/test_baseline_sanity.py::test_unreachable_services_refuse_before_probing"
    files: ["src/tddcli/cli.py"]
    commit_red: "test: a failing health_command refuses with services_unreachable"
    commit_green: "feat: probe health_command before baseline capture, refuse if down"

  - n: 12
    project: tddcli
    pin_cycle: true
    title: "a passing health_command lets the run proceed normally"
    test: "tests/test_baseline_sanity.py::test_reachable_services_proceed_normally"
    commit_pin: "test: pin that a passing health_command does not block the run"
---

# Issue #67 — `run start` records environment-broken baselines as legitimate

https://github.com/geuben/tdd-cli/issues/67
Task file: `tasks/issue-67-baseline-sanity.md`

## Context

`run start` records whatever the suites report as the baseline, with no check on whether
the *environment* is healthy. Observed across a week of real agent-driven runs: one
project's baseline swung `0 → ~1005 → 6 → 58 → ~1007` failures across five days. The
four-digit baselines were an integration suite whose backing services were down —
recorded as a legitimate baseline. Because baseline subtraction (R9.6) removes every
pre-existing failure from later verdicts, a run that starts from a ~1005-failure baseline
has **essentially no regression protection**: any newly broken test is subtracted away as
"pre-existing," and the run reports success. A second failure mode from the same incident:
a small set of contract tests requiring a live stack sat red in *every* run's baseline for
a week, growing quietly — because baseline subtraction normalises them, nobody is forced
to look.

`#44`/`#45`/`#46` optimised *how* baselines are captured; none asks whether the captured
baseline is *believable*, nor surfaces a standing-red set as a trend. This plan implements
**all three parts of #67**:

- **Part 1 — the infra-down gate** (cycles 1–6): refuse (with an `--accept-baseline`
  override) a baseline that is implausible on a relative heuristic — for a suite large
  enough to matter, more than a threshold *fraction* of collected tests failing. The
  incident separates cleanly under any ratio from ~10–90% (`6/1010 ≈ 0.6%`,
  `58/1010 ≈ 5.7%` vs `1005/1010 ≈ 99.5%`), so a relative gate self-tunes where an absolute
  failure count would need per-project calibration. This is the safety-critical piece.
- **Part 2 — the standing-failure delta** (cycles 7–9): when a captured baseline is
  non-empty, emit a `baseline_standing_delta` event partitioning the current standing
  failures into *new* (absent from the previous run's baseline for that project) and
  *inherited*, so a permanently-red or growing set is visible as a trend. `#45`'s per-run
  `baseline` rows already store enough to make this a single query.
- **Part 3 — environment-dependent suite classes** (cycles 10–12): let a project declare a
  `health_command` in `tdd.toml`; before probing that project, `run start` runs it and, on a
  non-zero exit, refuses with a distinct `services_unreachable` condition instead of folding
  service-down failures into the baseline. Presence of `health_command` *is* the "requires
  live services" marker — no separate bool.

### The three parts are ordered and complementary

Part 3 runs **before** the probe: a project whose declared stack is down never reaches part
1's ratio computation — it refuses as `services_unreachable`, the precise diagnosis, not the
generic `baseline_implausible`. Part 1 is the backstop for a project with *no* declared
`health_command` that still comes up mostly-red. Part 2 runs **after** a believable baseline
is captured, on whatever standing failures remain.

### One deliberate scope cut carried from part 1

The issue's alternative part-1 signal — a failure *set dominated by connection/setup errors*
rather than assertions — is **not** built. The pytest adapter collapses pytest `failed` and
`error` outcomes into one `Verdict.failed` list, so distinguishing them needs a new
failure-kind field threaded through every adapter — its own change. The relative-ratio gate
already catches the observed stack-down blowouts, and part 3 catches the declared-service
case directly. See scope cuts.

## Verified repo facts

*Read out of the codebase during hardening. Cycle 1's pre-gate state and the absence of the
new symbols were confirmed **empirically** with a throwaway probe (noted inline); the rest
were read directly. Anchors are symbol names and code landmarks — grep for them.*

### Shared

- **Single-project repo.** `tdd.toml` declares `[project.tddcli]`, `root = "."`,
  `adapter = "pytest"`, `lint = ["uv run ruff check"]`, **no typecheck gate** — so a RED
  commit must pass `ruff check` only; a test that references a not-yet-existing method or
  flag is a clean runtime RED (ruff does not flag attribute access on a defined name), which
  is why no cycle here needs a `stub_expected`. Cycles run against the synthetic `repo`
  fixture in `tests/conftest.py` (one pytest project `backend`, `lint = []`,
  `typecheck = []`, a passing `test_smoke.py`) via the `write_plan` / `run_cli` /
  `git` helpers — the harness `tests/test_baseline_integrity.py` uses (`PLAN`, `reach_refactor`
  there are the templates). `run start` baseline for *this* repo is `{"tddcli": 0}` — any
  other value at arrival means a moved branch; stop.
- **The probe returns Verdicts and Collections.** `_probe_projects(...)` (in `cli.py`)
  returns `(probes, reused)` where `probes` maps `name -> (Verdict, Collection)` and `reused`
  is the set of project names served from the `#45` cache. `Verdict.failed: list[str]` and
  `Collection.tests: list[str]` are dataclass fields in `adapters/base.py`. Per project:
  `failing = len(verdict.failed)`, `collected = len(collection.tests)`.
- **State in `cmd_run_start`.** The whole probe-and-refuse-and-create-run body is wrapped in
  a `try:` whose `finally:` calls `ledger.release_claim(str(worktree))` — so **any**
  `return failure(...)` added inside that body releases the baseline claim automatically; no
  new refusal needs its own claim handling. Landmarks inside `cmd_run_start`, in order:
  1. the `--baseline-all` scoping block that assigns `probe_projects` (a `dict[str, Project]`);
  2. the `ledger.claim(...)` call (guarded by `try/except sqlite3.IntegrityError`);
  3. `_probe_projects(...)` → `probes, reused`;
  4. the **refusal loop** `for name, (verdict, collection) in probes.items():` holding the two
     existing `return failure(...)` checks (it `continue`s on `name in reused`);
  5. `run_id = ledger.insert("run", ...)` then `run = ledger.one("SELECT * FROM run WHERE id
     = ?", (run_id,))`;
  6. the **event block** right after (5): `ledger.event(run_id, None, "baseline_scoped"|
     "baseline_reused", ...)`;
  7. the **baseline-insert loop** `for name, (verdict, collection) in probes.items():
     ledger.insert("baseline", ...)`;
  8. `Engine(...)`, `open_cycle`, and the success `Envelope`.
  After (5) these names are in scope: `run_id` (int), `run` (row), `worktree` (a `Path`,
  stored on the run row as `worktree_path=str(worktree)`), `ledger`, `cfg`, `probes`,
  `reused`.
- **Refusal / event patterns.** `failure(error, **result)` (`envelope.py`) →
  `Envelope(ok=False)`, with any extra kwarg (e.g. `reason=...`, `project=...`) landing in
  `result`. `Ledger.event(run_id, cycle_id, kind, detail="")` inserts a run-scoped
  `integrity_event` with `cycle_id=None`. The metrics readout
  `run_cli(repo, "metrics")["result"]["runs"][0]["integrity_events"]` is a `{kind: count}`
  dict; an event's *detail* is read in a test via
  `Ledger(...).all("SELECT detail FROM integrity_event WHERE kind = ?", (kind,))`.

### Part 1 (gate)

- **Insertion point.** The gate is a third check after the refusal loop (landmark 4). It
  runs a **separate pass over `probes.items()`, not skipping `reused`** (an implausible
  *reused* baseline is as dangerous as a fresh one), computing `implausible = [{"project":
  name, "failing": len(v.failed), "collected": len(c.tests), "ratio": len(v.failed)/len(c.tests),
  "threshold": <effective>} for name,(v,c) in probes.items() if len(c.tests) >=
  BASELINE_MIN_COLLECTED and len(v.failed)/len(c.tests) > <effective threshold>]`. The `>=
  MIN` guard makes `collected == 0` exempt and cannot divide by zero.
- **Accept flag.** `--baseline-all`/`--reuse-baselines`/`--baseline-jobs` are added on the
  `run start` subparser (`sub.add_parser("start")` under the `run` subparser) as `store_true`
  / typed args and read as `args.baseline_all` etc. `--accept-baseline` follows the
  `--baseline-all` `store_true` pattern, read as `args.accept_baseline`.
- **The refusal precedes run creation; the accept *event* follows it.** The `implausible`
  computation and the `return failure(...)` sit at landmark 4 (before `run_id` exists — a
  refusal creates no run). But `baseline_accepted` (cycle 5) is an `integrity_event` needing
  `run_id`, so it is emitted at the **event block** (landmark 6), reusing the `implausible`
  list computed at landmark 4. Compute `implausible` once, use it in both places.
- **Empirically confirmed pre-gate state.** A probe (single-project `repo`, `test_smoke.py`
  removed, one `test_infra.py` of 12 `assert False` tests, a one-cycle plan) ran `run start`
  and observed `ok: True`, `result.baselines == {"backend": 12}`, `next_action.verb ==
  "write_test"` — the exact state cycle 1 turns into a refusal. The same probe with 3 failing
  tests also observed `ok: True` (cycle 3's premise). Probe deleted; tree clean.
- **Zero-collected safety.** `test_a_project_with_no_tests_at_all_is_not_an_error` (in
  `tests/test_baseline_integrity.py`) registers a 0-collected project and asserts `ok`; the
  `>= BASELINE_MIN_COLLECTED` guard keeps it exempt.
- **Blast radius (checked).** The gate is default-on; the min-collected guard is what keeps it
  off the existing tiny fixtures. Every baseline fixture in `tests/` collects a handful of
  tests (well under `MIN = 10`), and the full suite is green today (406 passed) — so no
  existing test builds a `collected >= MIN`, high-ratio baseline. The executor must re-run the
  full suite after cycle 1 and confirm no pre-existing test regressed; if one does, it is a
  signal to revisit `MIN`/the default, never a test to edit.

### Part 2 (standing-failure delta)

- **Schemas.** The `run` `CREATE TABLE` has a `worktree_path TEXT NOT NULL` column; the
  `baseline` `CREATE TABLE` has `run_id`, `project`, `failing` (a JSON sorted list of ids),
  `captured_at`, `source`. A baseline reaches its worktree only by joining to `run` on
  `run_id`.
- **No existing prior-baseline query.** `Ledger.baselines(run_id)` is keyed by `run_id` only.
  `Ledger.active_run(worktree)` (`SELECT * FROM run WHERE worktree_path = ? AND ended_at IS
  NULL ORDER BY id DESC LIMIT 1`) is the model for a worktree-scoped lookup. Part 2 adds
  `previous_baseline(self, worktree: str, project: str, before_run_id: int) -> set[str] |
  None` — `SELECT b.failing FROM baseline b JOIN run r ON b.run_id = r.id WHERE
  r.worktree_path = ? AND b.project = ? AND r.id < ? ORDER BY r.id DESC LIMIT 1`, returning
  `set(json.loads(row["failing"]))` or `None`. Called as `ledger.previous_baseline(
  str(worktree), name, run_id)` at the delta site; `r.id < run_id` excludes the current run's
  just-inserted baseline rows.
- **Delta site.** Emit after the baseline-insert loop (landmark 7): for each project whose
  captured `verdict.failed` is non-empty, `prev = ledger.previous_baseline(str(worktree),
  name, run_id) or set()`; `new = failing - prev`; `inherited = failing & prev`; `resolved =
  prev - failing`; `ledger.event(run_id, None, "baseline_standing_delta", json.dumps({
  "project": name, "new": sorted(new), "inherited": sorted(inherited), "resolved":
  sorted(resolved)}))`. A fully-green baseline (empty `failed`) emits nothing.
- **Ledger unit-test harness.** `tests/test_snapshot_and_identity.py` builds a `Ledger`
  directly (`Ledger(tmp_path / "repo")` under `TDD_LEDGER_HOME`, set via `monkeypatch.setenv`)
  and reaches into `ledger.db` freely for setup — see `test_cached_baseline_respects_max_age`.
  Cycle 7's test seeds, via `ledger.insert(...)`, a `plan_contract` row (the `run` FK target),
  a prior *ended* `run` row for a worktree `W` (columns `plan_contract_id`, `executor_model`,
  `executor_source`, `worktree_path=W`, `started_at`, `ended_at`, `preexisting_dirty="[]"`),
  and its `baseline` row (`run_id`, `project`, `failing=json.dumps([...])`, `captured_at`,
  `source="probed"`); then asserts `previous_baseline(W, project, before_run_id=<a larger id>)`
  equals the seeded set, and that a query before any earlier run returns `None`. Confirm the
  exact NOT-NULL column set of `run`/`plan_contract` from their `CREATE TABLE` at execution
  time (the `run` table also has `executor_session` nullable, `outcome` nullable).

### Part 3 (live-service reachability)

- **Subprocess choke point.** `run_command(command, cwd, timeout=1800, extra_env=None,
  label=None) -> (rc, stdout, stderr)` in `adapters/base.py`, `shell=True`. `cli.py` already
  calls it as `adapters.base.run_command(probe, root, label="doctor")` in the doctor code, so
  the module path is in scope. Health probe: `adapters.base.run_command(project.health_command,
  worktree / project.root, label="health")`.
- **Per-project root.** `Project.root` is a worktree-relative string (`.rstrip("/")` at load;
  `"."` = the worktree root). The command cwd is `worktree / project.root` — the same join the
  doctor code uses (`root = worktree / project.root`) and that `Adapter.__init__` uses for
  `self.root`.
- **Config field.** The `Project` dataclass has optional scalars with defaults
  (`test_command: str | None = None`, `timeout: int | None = None`); add `health_command:
  str | None = None` and `baseline_max_failure_ratio: float | None = None` beside them.
  `load()` reads each project's fields with `body.get(...)` and **ignores unknown keys**
  (no rejection), and type-checks like `if timeout is not None and not isinstance(timeout,
  int): raise ConfigError(...)`. Add, in the same place: `health_command` must be `str` if
  present; `baseline_max_failure_ratio` must be a number in `(0, 1]` if present. Wire both
  into the `Project(...)` construction with `body.get(...)`. `ConfigError` is defined in
  `config.py`. Adding fields changes `config_sha` — intended drift detection; no ledger/schema
  change.
- **Reachability slot.** Immediately after the `--baseline-all` block assigns `probe_projects`,
  and **before** the `ledger.claim(...)` guard: `for name, project in probe_projects.items()`
  with `project.health_command`, run the probe; collect non-zero exits into `unreachable = [{
  "project": name, "exit_code": rc, "output": (out + err)[-4000:]}]`; if any, `return failure(
  "services unreachable for {names} — fix the stack or drop them from this run",
  reason="services_unreachable", projects=unreachable)`. Running this before the claim means a
  down stack never touches the claim. `tests/test_config_and_staging.py` exercises config +
  `run start` together and is where cycle 10's config test lands.

## Design summary

**Constants (part 1)** — module-level in `cli.py`: `BASELINE_MAX_FAILURE_RATIO_DEFAULT = 0.5`
(more than half a suite failing at baseline is implausible) and `BASELINE_MIN_COLLECTED = 10`
(suites smaller than this are exempt — a 2-of-3-red baseline is normal pre-existing-failure
territory, which baseline subtraction exists to handle; the gate targets stack-down blowouts,
and the guard also makes `collected == 0` safe). *These two values are the one genuinely
tunable design choice; they are defended above but a reviewer may still move them — they are
isolated as named constants precisely so that is a one-line change.* Effective threshold per
project = `project.baseline_max_failure_ratio or BASELINE_MAX_FAILURE_RATIO_DEFAULT`.

**Part 2** — after a believable baseline is captured, for each project with a non-empty
captured failing set, emit `baseline_standing_delta` partitioning into `new` / `inherited` /
`resolved` against `previous_baseline`. Empty failing set → no event.

**Part 3** — for each probe project declaring `health_command`, run it in the project root
before probing; any non-zero exit → refuse `services_unreachable`. There is deliberately **no**
override (unlike part 1): a down stack yields no believable baseline; the fix is to repair it
or drop the project.

## Cycle detail

*Each RED genuinely fails given the previous GREEN (cycle 1 empirically confirmed); minimum
GREEN; resist later cycles. A "mostly-red" project = one `test_infra.py` of 12 `def test_k():
assert False` tests with `test_smoke.py` removed (collected 12 ≥ MIN, ratio 1.0); a "small
all-red" project = 3 such tests. Register a one-cycle plan (the `PLAN` shape from
`test_baseline_integrity.py`, target `tests/test_add.py::test_add_two_numbers`, which need not
exist at `run start`).*

### Part 1 — the infra-down gate

**Cycle 1 — a large, mostly-red baseline is refused.** *EXPECTED FAILURE (probed):* with no
gate `run start` returns `ok: True`, `baselines == {"backend": 12}`, `verb == "write_test"`;
the test asserts `ok is False` and fails. Test (`test_a_mostly_red_baseline_is_refused`): 12
always-failing tests, register, `run start`; assert `ok is False`, `result["reason"] ==
"baseline_implausible"`, and `result["projects"]` names `backend` with `failing == 12`,
`collected == 12`. *GREEN:* add the two constants; after the refusal loop compute `implausible`
(separate pass, not skipping `reused`) and, if non-empty, `return failure(..., reason=
"baseline_implausible", projects=implausible)`. Use a per-project `threshold` variable set to
the default here. No flag, config, or event yet.

**Cycle 2 — `--accept-baseline` overrides.** *EXPECTED FAILURE:* the flag is unknown to the
parser, so `run start ... --accept-baseline` errors (argparse `SystemExit`/unrecognized-args)
instead of proceeding; the test asserts the run proceeds. Test
(`test_accept_baseline_overrides_the_refusal`): same 12-red project, `run start ...
--accept-baseline`; assert `ok is True` and `next_action["verb"] == "write_test"`. *GREEN:*
add `--accept-baseline` (`store_true`) to the `run start` subparser; refuse only `if
implausible and not args.accept_baseline`. No event yet.

**Cycle 3 (pin) — a small all-red suite is exempt.** Locks the `BASELINE_MIN_COLLECTED`
exemption from cycle 1 (empirically, a 3-red suite currently returns `ok: True`). Test
(`test_a_small_all_red_suite_is_not_refused`): 3 always-failing tests, `run start`, no flag;
assert `ok is True`, no `baseline_implausible`. Passes against cycle 1's code — a genuine pin;
the sensitivity check the tool then requires breaks the `>= MIN` guard (temporarily gate small
suites too) and confirms the test flips to failing, then restores.

**Cycle 4 — per-project `baseline_max_failure_ratio`.** *EXPECTED FAILURE:* the key is present
in `tdd.toml` but ignored by `load()`, so the 12-red project is still refused as
`baseline_implausible`; the test asserts `ok is True`. Test
(`test_project_ratio_config_raises_the_threshold`): 12-red project, `baseline_max_failure_ratio
= 1.0` on `[project.backend]`, `run start` (no flag); assert `ok is True` (`1.0` is not
`> 1.0`). *GREEN:* add the field to `Project`, parse + range-validate `(0, 1]` in `load()`
(model on `timeout`), and in the gate take `threshold = project.baseline_max_failure_ratio or
BASELINE_MAX_FAILURE_RATIO_DEFAULT`.

**Cycle 5 — accepted implausible baseline records an audit event.** *EXPECTED FAILURE:*
`--accept-baseline` proceeds (cycle 2) but writes no event; the test asserts the event exists.
Test (`test_accepted_implausible_baseline_records_an_event`): 12-red project,
`--accept-baseline`; assert `run_cli(repo, "metrics")["result"]["runs"][0]["integrity_events"]
.get("baseline_accepted", 0) >= 1`. *GREEN:* at the event block (landmark 6), when
`implausible` is non-empty (the run only reaches here when accepted), `ledger.event(run_id,
None, "baseline_accepted", json.dumps(implausible))`.

**Cycle 6 (pin) — a healthy large baseline is untouched.** Test
(`test_a_healthy_baseline_is_recorded_untouched`): ~20 passing tests + 2 failing (ratio ~0.1,
collected ≥ MIN), `run start`; assert `ok is True`, no `baseline_implausible`,
`integrity_events.get("baseline_accepted", 0) == 0`. Pin (runs before part 2, so no
`baseline_standing_delta` yet; the test never asserts on that event). Sensitivity check:
temporarily force the ratio comparison to fire on this project, confirm the test flips.

### Part 2 — the standing-failure delta

**Cycle 7 — `Ledger.previous_baseline`.** *EXPECTED FAILURE:* the method does not exist —
confirmed `not hasattr(Ledger, "previous_baseline")`; the test's call raises `AttributeError`.
Test (`test_previous_baseline_returns_prior_runs_failing_set`, in
`tests/test_snapshot_and_identity.py`): seed a `plan_contract` row, a prior ended `run` for
worktree `W`, and its `baseline` row with `failing = ["backend::t::a", "backend::t::b"]`;
assert `previous_baseline(W, "backend", before_run_id=<larger id>) == {"backend::t::a",
"backend::t::b"}`, and `previous_baseline(W, "backend", before_run_id=<smallest id>) is None`.
*GREEN:* add the method with the join query above.

**Cycle 8 — run start emits the delta.** *EXPECTED FAILURE:* no `baseline_standing_delta` event
is written; the test asserts it exists with the right partition. Test
(`test_non_empty_baseline_emits_standing_delta`): open a `Ledger` under the test's
`TDD_LEDGER_HOME` and seed a prior ended `run` + `baseline` for the fixture worktree whose
`failing` is `["backend::tests/test_infra.py::test_fail_0"]`; write a small suite (< MIN, to
keep part 1 out of the way) that fails on two tests, one whose id equals the seeded id
(inherited) and one new (new); `run start`; read the `baseline_standing_delta` detail via
`Ledger(...).all("SELECT detail FROM integrity_event WHERE kind = 'baseline_standing_delta'")`
and assert `len(json.loads(detail)["new"]) == 1` and `len(...["inherited"]) == 1`. *GREEN:*
emit the event at the delta site (landmark 7) as in the design summary. (Confirm the fixture
worktree path used for `worktree_path` matches what `run start` records — `str(worktree)` —
by reading it back from the `run` row if needed.)

**Cycle 9 (pin) — first run, no prior baseline.** Locks the `... or set()` path. Test
(`test_first_run_reports_all_standing_failures_new`): no seeded prior run; a small suite fails
2 tests; `run start`; read the `baseline_standing_delta` detail and assert `len(new) == 2`,
`len(inherited) == 0`; no crash. Passes against cycle 8's code — a pin. Sensitivity: break the
`or set()` fallback (let `prev` stay `None`) and confirm the emit raises / the test fails.

### Part 3 — environment-dependent suite classes

**Cycle 10 — `health_command` parses onto a project.** *EXPECTED FAILURE:* `Project` has no
such field — confirmed absent from `dataclasses.fields(Project)`; the test's attribute access
raises `AttributeError`. Test (`test_health_command_parses_onto_project`, in
`tests/test_config_and_staging.py`): write `tdd.toml` with `health_command = "true"` on a
project, `config.load(worktree)`, assert `cfg.projects[name].health_command == "true"`; and a
non-string value (`health_command = 5`) raises `ConfigError`. *GREEN:* add the field to
`Project`, parse + type-validate in `load()`.

**Cycle 11 — run start refuses on a failing health command.** *EXPECTED FAILURE:* nothing runs
the command, so a project whose services are "down" still probes and returns `ok: True`; the
test asserts `ok is False`. Test (`test_unreachable_services_refuse_before_probing`): set
`health_command = "false"` (exit 1) on `[project.backend]`, `run start`; assert `ok is False`,
`result["reason"] == "services_unreachable"`, and `result["projects"]` names `backend` with a
non-zero `exit_code`. *GREEN:* add the reachability loop right after `probe_projects` is
assigned and before the claim, `return failure(..., reason="services_unreachable",
projects=unreachable)` on any non-zero exit.

**Cycle 12 (pin) — a passing health command proceeds.** Locks that a zero-exit command is
transparent. Test (`test_reachable_services_proceed_normally`): `health_command = "true"` (exit
0) on `[project.backend]` (its real suite is green), `run start`; assert `ok is True`,
`next_action["verb"] == "write_test"`, no `services_unreachable`. Passes against cycle 11's
code — a pin. Sensitivity: invert the exit-code test (refuse on zero) and confirm the test
flips.

## Deliberate scope cuts (do not build)

- **No failure-kind classification (assertion vs connection/setup).** Needs the pytest adapter
  to stop collapsing `failed`/`error` and a new `Verdict` field through every adapter — own
  change. The ratio gate and `health_command` cover the observed failure modes.
- **No override for `services_unreachable`.** A down stack yields no believable baseline; the
  resolution is to fix it or drop the project, not force it through. A `--skip-unreachable`
  that drops only the down projects is a possible follow-up.
- **`requires_live_services` is folded into `health_command` presence** — a declared health
  command *is* the marker; a separate bool would be redundant.
- **No suite-level (`Override`) `health_command`** — the marker lives on the project only.
- **No absolute failure-count threshold** (ratio + min-collected is the whole part-1 gate),
  **no new ledger column or schema bump** (reuse `integrity_event` and the existing baseline
  write; `--accept-baseline` gets no `baseline.source` value — the `baseline_accepted` event is
  the trail), and **the gate and delta apply to reused baselines too** — do not special-case
  `--reuse-baselines`.
- **Mirrors:** the baseline gate lives only in `cmd_run_start`; there is no offline/second
  implementation of baseline capture to keep in parity (no `docs/INVARIANTS.md` registry in
  this repo either). No parity cycle needed.
- **README/PRD documentation** is a post-run doc follow-up, not a cycle (see Done-criteria).

## Execution

This plan is executed through `tdd-cli`. **You run every command below yourself** — do not ask
the user to start the run. `tdd run start` records which model is executing, resolved from your
own session; a run started by anyone else attributes this work to the wrong agent.

**Referee rule:** run the *released* `tdd` **0.8.0**, never this working tree's editable
install. Verify: `tdd --version` → **0.8.0**, and `which tdd` is **not**
`/Volumes/SSD/repos/tdd-cli/.venv/bin/tdd`. This plan adds no ledger schema and uses only
0.8.0-supported front-matter keys.

    git checkout -b feat/67-baseline-sanity     # first, before anything else
    tdd doctor                                  # must report healthy: true
    tdd run start --plan tasks/issue-67-baseline-sanity.md

If the branch already exists, do not force-checkout and do not pick another name: check it out
only if it carries this plan's commit and no unrelated work, otherwise stop and ask. If
`tdd doctor` fails on *other* uncommitted `tasks/issue-*.md` files (sibling plans), commit,
stash, or gitignore them before `run start`.

Then repeat until done: read `next_action.verb`, do exactly what it says, run `tdd advance`.
Stop when `next_action.terminal` is `true`.

- `tdd advance` is the only command that changes phase; the tool stages and commits from the
  phase — do not `git add`/`git commit` yourself.
- Expected baseline for this repo: `{"tddcli": 0}` — anything else means a moved branch; stop.
- This plan declares **no `annotation_keys`**, so `annotate_cycle` will not appear. Verbs it
  will hit: standard cycles (1, 2, 4, 5, 7, 8, 10, 11) drive `write_test` → `write_code` →
  optional refactor; **pins (3, 6, 9, 12)** pass on arrival and drive `run_sensitivity_check`
  → `tdd sensitivity begin|check|end` (each pin body names what to break). If blocked,
  `resolve_blocker` → `tdd blocker --kind --detail` (kinds: `plan_defect`, `tooling`,
  `regression`, `pre_existing_failure`); `confirm_cycle_applicable` on a cycle the code has
  outgrown → `tdd cycle skip --reason`.
- Your own run trips none of the new conditions: this repo's suite is green (ratio ≈ 0), the
  `tddcli` project declares no `health_command`, and part 2 emits at most an empty-set delta
  (i.e. nothing, since the failing set is empty).

## Done-criteria

**Before finishing:** run
`tdd log render --out tasks/friction-logs/issue-67-baseline-sanity-friction.md` (the
`tasks/friction-logs/` at the **repository root**) and `tdd metrics`. Report the plan-fidelity
section — declared vs delivered vs skipped — and every integrity event. Do not narrate what the
ledger already records.

Then the documentation follow-up, committed as ordinary commits after the run is terminal: in
`README.md` and `docs/PRD.md` (its integrity-event table and the `run start` section), document
the baseline-implausibility gate and `--accept-baseline` flag; the `baseline_implausible` and
`services_unreachable` refusals (`reason`); the `baseline_accepted` and `baseline_standing_delta`
integrity events; and the per-project `baseline_max_failure_ratio` and `health_command` config
keys.

Then commit the friction log and raise the PR:

    git add tasks/friction-logs/issue-67-baseline-sanity-friction.md
    git commit -m "docs: friction log for issue-67-baseline-sanity"

Then invoke the **`raise-pr` skill** (`/raise-pr`), which runs the quality gates, pushes the
branch and opens the PR against `main`. Do not push or call the GitHub API by hand. If a gate
fails, fix it and re-run the skill — a failed gate is work, not a reason to hand back.
