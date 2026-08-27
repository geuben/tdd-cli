---
closes: 70
cycles:
  - n: 1
    project: tddcli
    title: "top-level ancillary_files parses onto PlanContract.ancillary_files"
    test: "tests/test_contract.py::test_ancillary_files_parse_onto_plan_contract"
    files: ["src/tddcli/contract.py"]
    commit_red: "test: top-level ancillary_files parses onto PlanContract"
    commit_green: "feat: PlanContract.ancillary_files from top-level front-matter key"

  - n: 2
    project: tddcli
    title: "non-list / non-string ancillary_files hard-fails registration"
    test: "tests/test_contract.py::test_non_list_ancillary_files_raises_contract_error"
    files: ["src/tddcli/contract.py"]
    commit_red: "test: non-list ancillary_files is rejected"
    commit_green: "feat: validate ancillary_files is a list of strings"

  - n: 3
    project: tddcli
    title: "plan_contract carries an ancillary_files column, migrated on old ledgers"
    test: "tests/test_release_surface.py::test_plan_contract_gains_ancillary_files_column"
    files: ["src/tddcli/ledger.py"]
    commit_red: "test: plan_contract carries an ancillary_files column"
    commit_green: "feat: ancillary_files column with a v5->v6 migration"

  - n: 4
    project: tddcli
    title: "plan register persists declared ancillary_files into the ledger row"
    test: "tests/test_ancillary_files.py::test_plan_register_persists_ancillary_files"
    files: ["src/tddcli/cli.py"]
    commit_red: "test: plan register persists declared ancillary_files"
    commit_green: "feat: cmd_plan_register writes ancillary_files to the ledger"

  - n: 5
    project: tddcli
    title: "staging.classify routes a declared ancillary path to its own bucket and stages it"
    test: "tests/test_config_and_staging.py::test_declared_ancillary_file_is_bucketed_and_staged"
    stub_expected: ["src/tddcli/staging.py"]      # signature stub: the new `ancillary` param + empty bucket, inert in RED
    files: ["src/tddcli/staging.py"]
    commit_red: "test: a declared ancillary path is bucketed out of outside and staged"
    commit_green: "feat: staging.classify routes declared ancillary files to their own bucket"

  - n: 6
    project: tddcli
    title: "a declared ancillary file is committed and fires no undeclared_file_touched"
    test: "tests/test_ancillary_files.py::test_declared_ancillary_file_is_committed_and_not_flagged"
    files: ["src/tddcli/machine.py", "src/tddcli/advance.py"]
    commit_red: "test: a declared ancillary file is committed and fires no undeclared_file_touched"
    commit_green: "feat: Engine loads ancillary_files and advance stages them"
---

# Issue #70 — allow plans to declare ancillary / cross-project files

https://github.com/geuben/tdd-cli/issues/70
Task file: `tasks/issue-70-ancillary-files.md`

## Context

A cycle's `files:` list is the only vocabulary for what a cycle may touch, and it is
scoped to the cycle's project roots. Two recurring cases have no home: a **cross-project
ripple** (a backend change whose regenerated client type-breaks a frontend import the plan
already anticipates) and a **companion document** read by a test at runtime (an invariants
registry, a glossary). The plan *knows* the path, but cannot declare it, so every phase of
every cycle re-fires `undeclared_file_touched` for the same known file — and, worse, the
tool never stages that file, so the working-tree edit is silently dropped between run close
and the PR (the enforcement half of that drop is issue #69, out of scope here).

This issue adds a **plan-level** `ancillary_files:` list to the contract. A touched path
that matches the list is classified as *declared* — not `outside`, so no
`undeclared_file_touched` — and is staged into the phase commit rather than left to rot in
the working tree. Paths are repo-root-relative and may point outside any registered
project. Like everything else in the front-matter they are hash-frozen with the plan blob
(R7.2): an ancillary file touched that is *not* listed still fires the event exactly as
today, so `undeclared_file_touched` keeps meaning *genuinely* unplanned drift.

**Plan-level, not per-cycle (deliberate).** Both observed cases are plan-wide — the same
4–5-file list repeated across a whole run. The issue offers "plan-level and/or per-cycle";
this plan builds only the plan-level list. A per-cycle `ancillary_files` override is a
clean additive follow-up and is listed under scope cuts.

`ancillary_files` is deliberately distinct from `annotation_keys` (a top-level *run-time*
judgement-annotation vocabulary) and from per-cycle `files`/`stub_expected` (project-scoped
authorship). Do not overload any of them.

Ordering is a dependency chain: cycle 1 parses the list onto the contract; cycle 2 guards
its shape; cycle 3 gives the ledger a column to store it; cycle 4 writes the column at
registration; cycle 5 teaches `staging.classify` to bucket and stage a matched path; cycle
6 wires the stored list through the `Engine` into `_stage_and_commit` so the end-to-end
behaviour — committed, not flagged — holds. Cycles 4 and 6 depend on 3; cycle 6 depends on
1–5.

## Verified repo facts

*Every fact below was read out of the codebase during hardening — none are asserted from
memory. Locators are real names and paths; grep for them at execution time.*

- **This repo is a single project.** `tdd.toml` declares exactly `[project.tddcli]` with
  `root = "."`, `adapter = "pytest"`, `test_paths = ["tests/"]`. So the project root *is*
  the repo root: every `test`, `files`, and `stub_expected` path in this plan's front-matter
  is repo-root-relative (`tests/test_contract.py::...`, `src/tddcli/staging.py`). Because
  root is `.`, `owning_project` claims every path under the repo — nothing in *this* repo is
  ever `outside`. The integration cycles (4, 6) therefore run against the **synthetic**
  fixtures in `tests/conftest.py`, not against tdd-cli itself.
- **`PlanContract`** (`src/tddcli/contract.py`, dataclass ~line 74) has fields `plan_path`,
  `status`, `cycles`, `annotation_keys`, `blob_sha`, `commit_sha`. **No `ancillary_files`
  field exists** — so reading `parse(...).ancillary_files` today raises `AttributeError`.
  That is cycle 1's expected RED.
- **`parse(text, plan_path, config=None)`** (~line 190) is the public entry the tests use.
  It reads top-level keys off `data`: it requires `cycles`, and reads `annotation_keys` with
  `data.get("annotation_keys", [])`, validating it via
  `if not isinstance(keys, list) or not all(isinstance(k, str) for k in keys): raise
  ContractError("annotation_keys must be a list of strings")` (~lines 214–216). **This is the
  exact pattern cycles 1–2 mirror for `ancillary_files`** — a sibling top-level key, read and
  shape-checked the same way. There is no `ancillary_files` read today.
- **`ContractError`** (~line 27) is the malformed-front-matter exception; `parse` and
  `parse_cycle` already raise it for shape defects. Cycle 2 follows the `annotation_keys`
  precedent verbatim.
- **`_as_list(value, field_name, ordinal)`** (~line 95) coerces a str-or-list-of-str and
  raises `ContractError` otherwise, but it takes a per-*cycle* `ordinal` and is used only
  inside `parse_cycle`. Do **not** reuse it for the plan-level key — mirror the inline
  `annotation_keys` isinstance check instead (no ordinal in scope at the top level). A
  plan-level list of strings, not a str-or-list; `ancillary_files: ["a", "b"]`.
- **`plan_contract` table** (`src/tddcli/ledger.py`, SCHEMA ~line 62) has columns `id,
  plan_path, git_blob_sha, git_commit, status, declared_cycles TEXT (json),
  annotation_keys TEXT (json), registered_at`. **No `ancillary_files` column.** Cycle 3 adds
  one.
- **Migration mechanism** (`src/tddcli/ledger.py`): `SCHEMA_VERSION = 5` (line 16) and
  `MIGRATIONS: dict[int, str]` (line 29) keyed by the version upgraded *from*. `__init__`
  (line 258) runs `executescript(SCHEMA)` (idempotent `CREATE TABLE IF NOT EXISTS`) then,
  while `stored < SCHEMA_VERSION`, applies `MIGRATIONS[stored]` (line 281). The precedent is
  exact: entry `4: "ALTER TABLE baseline ADD COLUMN source TEXT NOT NULL DEFAULT 'probed';"`
  (line 37) added a defaulted column to an existing table. **Cycle 3 does the identical thing
  for `plan_contract`**: bump `SCHEMA_VERSION` to 6, add the column to the `CREATE TABLE`
  body with `DEFAULT '[]'`, and add `5: "ALTER TABLE plan_contract ADD COLUMN
  ancillary_files TEXT NOT NULL DEFAULT '[]';"`. Every released version must have a
  `MIGRATIONS` entry or the while-loop `KeyError`s — so adding entry 5 is mandatory, not
  optional.
- **The `DEFAULT '[]'` matters for two existing callers.** `tests/test_release_surface.py`
  (~line 73) and `test_newer_ledger_is_refused` insert a `plan_contract` row *without*
  `ancillary_files`; the default keeps those inserts valid. `test_older_ledger_is_migrated_forward`
  (line 59) forces a v1 ledger and asserts it reaches `SCHEMA_VERSION`; after cycle 3 it walks
  1→…→6 applying entry 5, and still passes because it asserts against the *constant*. None of
  these need editing — do not add them to `modifies_tests`.
- **`cmd_plan_register`** (`src/tddcli/cli.py`, ~line 442) parses via `contract_mod.register`,
  then `ledger.insert("plan_contract", ..., declared_cycles=..., annotation_keys=json.dumps(
  parsed.annotation_keys), registered_at=now())` (~lines 467–476) on the not-`existing` path.
  Cycle 4 adds `ancillary_files=json.dumps(parsed.ancillary_files)` to that insert, beside
  `annotation_keys`.
- **`Engine.__init__`** (`src/tddcli/machine.py`, ~line 53) loads
  `self.contract_row = ledger.one("SELECT * FROM plan_contract WHERE id = ?", ...)`,
  `self.declared = contract_mod.cycles_from_json(self.contract_row["declared_cycles"])`, and
  `self.annotation_keys = json.loads(self.contract_row["annotation_keys"])` (~line 62).
  Cycle 6 adds `self.ancillary_files = json.loads(self.contract_row["ancillary_files"])`
  right beside it. (The `SELECT *` already returns the new column once cycle 3 lands.)
- **`staging.classify(config, changed, cycle_projects, declared, excluded)`**
  (`src/tddcli/staging.py`, line 51) is a pure function with a positional signature. For each
  changed path: ignored → excluded → generated → then `owner = config.owning_project(rel)`;
  `if owner is None or owner.root not in roots: out.outside.append(rel); continue` (lines
  72–75). **The ancillary check goes immediately before that `outside` branch.** Cycle 5 adds
  a 6th parameter `ancillary: set[str] | None = None` (defaulted, so the 8 existing test
  callers and the single production caller keep working) and a new
  `Classification.ancillary: list[str] = field(default_factory=list)` bucket.
- **`Classification`** (line 25) has buckets `tests, stubs, implementation, generated,
  outside, excluded, ignored`. **`paths_for_phase(phase, classification)`** (line 85):
  RED → `tests + stubs`; PIN → `tests`; GREEN/REFACTOR → `tests + stubs + implementation`.
  Cycle 5 adds `classification.ancillary` to the **GREEN/REFACTOR** return (beside
  `implementation`), *not* to RED/PIN — a declared ancillary file is staged when authored
  work lands, and RED stays pure (tests + stubs only). A companion doc read at runtime is
  already on disk during RED (uncommitted files are readable by the suite), so it need not be
  in the RED commit to be readable — only present at run close, which the GREEN staging
  guarantees.
- **`classify` has one production caller:** the `staging.classify(...)` call inside
  `_stage_and_commit` in `advance.py`. Cycle 6 changes that call to pass
  `ancillary=set(engine.ancillary_files)`. The `undeclared_file_touched` emission is the
  block right below it in `_stage_and_commit`, gated on `if classification.outside:`; because
  cycle 5 routes declared paths out of `outside`, the event simply stops firing for them — no
  change to the emission code itself is required.
- **`authored_changes(cycle_row)`** (`src/tddcli/machine.py`, ~line 76) is diff-based, which
  is why a declared ancillary file self-heals across phases: once cycle 5/6 stage it in the
  first GREEN, it is at HEAD and no longer appears in `changed` for the REFACTOR phase — so it
  is committed exactly once, no dedup logic needed (contrast #55's `_last_outside_emitted`,
  which existed only because `outside` files are *never* staged and thus persist).
- **Integration seam.** `tests/conftest.py` provides `write_plan(repo, body)`,
  `run_cli(repo, *argv)` (returns the parsed envelope dict), and a `repo` fixture that is a
  single-project synthetic repo rooted at `backend` — so a file written at the repo root
  (e.g. `notes.md`) is genuinely `outside` the `backend` root. `tests/test_undeclared_dedup.py`
  (`test_unchanged_outside_file_is_flagged_once_per_cycle`, line 42) is the exact template
  for cycle 6: register → run start → write an outside file → advance RED/GREEN/REFACTOR →
  read `run_cli(repo, "metrics")["result"]["runs"][0]["integrity_events"]`. Cycles 4 and 6
  reuse this harness.
- **classify unit seam.** `tests/test_config_and_staging.py` has a `cfg` fixture (backend +
  frontend projects) and `test_files_outside_cycle_projects_are_flagged_not_staged` (line
  241): `staging.classify(cfg, {"backend/app/x.py", "tasks/plan.md"}, ["backend"],
  declared(), set())` asserts `c.outside == ["tasks/plan.md"]`. Cycle 5's test is the mirror,
  passing `ancillary={"tasks/plan.md"}` and asserting it lands in `c.ancillary` and in
  `paths_for_phase(GREEN, c)`, not in `c.outside`.
- **Baseline for this repo is `{"tddcli": 0}`** — the suite is fully green today
  (373–381 passed across the recent PRs). `run start` captures it; anything else at arrival
  means a moved branch — stop.

## Cycle detail

*Expected failure per cycle, grounded in the code above; minimum GREEN; resist later
cycles' behaviour.*

### Cycle 1 — parse accepts a top-level ancillary_files list

**Expected RED:** `AttributeError: 'PlanContract' object has no attribute 'ancillary_files'`
— the dataclass has no such field, so reading `parse(body, ...).ancillary_files` fails.
(Same shape as #58 cycle 1's `.meta` AttributeError, which was accepted as a legitimate
RED — `parse` itself runs fine; the behaviour "expose ancillary_files" is simply absent.)

Test (`test_ancillary_files_parse_onto_plan_contract`, in `tests/test_contract.py`): inline
front-matter with one valid standard cycle plus a top-level
```yaml
ancillary_files:
  - frontend/src/api/registerClient.ts
  - docs/INVARIANTS.md
```
Assert `parse(body, "tasks/p.md").ancillary_files == ["frontend/src/api/registerClient.ts",
"docs/INVARIANTS.md"]`. Also assert a plan with **no** `ancillary_files` yields `[]` (the
default).

GREEN (minimal): add `ancillary_files: list[str] = field(default_factory=list)` to
`PlanContract`, and in `parse` read `data.get("ancillary_files", [])` and pass it to the
`PlanContract(...)` constructor. **Do not validate the shape yet** (that is cycle 2) and do
not touch the ledger, cli, or staging.

### Cycle 2 — malformed ancillary_files is rejected

**Expected RED:** *no exception is raised* — after cycle 1, `data.get("ancillary_files", [])`
stores whatever is there verbatim, so `pytest.raises(ContractError)` fails because nothing
raises.

Test (`test_non_list_ancillary_files_raises_contract_error`): inline front-matter with
`ancillary_files: "docs/INVARIANTS.md"` (a bare string, not a list) on an otherwise valid
plan; `with pytest.raises(ContractError, match="ancillary_files must be a list of strings")`.
Add a second assertion for a list containing a non-string (`ancillary_files: [1, 2]`) in the
same test, to nail "list *of strings*".

GREEN: in `parse`, before constructing the `PlanContract`, mirror the `annotation_keys`
guard exactly — `anc = data.get("ancillary_files", [])`; `if not isinstance(anc, list) or not
all(isinstance(p, str) for p in anc): raise ContractError("ancillary_files must be a list of
strings")` — and pass the validated `anc`.

### Cycle 3 — the ledger stores it

**Expected RED:** the `plan_contract` table has no `ancillary_files` column, so the
assertion that it does fails. Write the test to open a ledger and inspect the schema rather
than to insert-with-the-column (an insert would raise `OperationalError`, a crash rather than
a clean assertion): `cols = {r[1] for r in ledger.db.execute("PRAGMA
table_info(plan_contract)").fetchall()}; assert "ancillary_files" in cols`. Confirm the
`PRAGMA table_info` row shape (`r[1]` is the column name) at execution time.

Test (`test_plan_contract_gains_ancillary_files_column`, in `tests/test_release_surface.py`
beside the other schema tests): build a v5 ledger, force it back a version the way
`test_older_ledger_is_migrated_forward` does (`ledger._write("UPDATE meta SET value = '5'
WHERE key = 'schema_version'", ())`, then close and reopen), and assert the reopened ledger
has the column — proving both the fresh-`CREATE TABLE` path *and* the migration path land the
column. Keep the import line's `SCHEMA_VERSION, Ledger` (already imported there).

GREEN: bump `SCHEMA_VERSION` to `6`; add `ancillary_files TEXT NOT NULL DEFAULT '[]',` to the
`plan_contract` `CREATE TABLE` body in `SCHEMA`; add `5: "ALTER TABLE plan_contract ADD
COLUMN ancillary_files TEXT NOT NULL DEFAULT '[]';"` to `MIGRATIONS`. Nothing else.

**Referee note (read this):** bumping `SCHEMA_VERSION` in the working tree does **not**
break the released **0.7.0** referee running this cycle. The referee owns its own run ledger
(created at v5, outside the worktree) and never opens a working-tree-created ledger; the
pytest suite the referee runs creates its own v6 ledgers in `tmp_path`/`ledger_home`
fixtures, isolated from the run ledger. This is a trodden path — the v4→v5 `source` column
landed the same way under an older referee. Do not "fix" this by reverting the bump.

### Cycle 4 — plan register writes the column

**Expected RED:** assertion failure — the stored `ancillary_files` is `'[]'` (the column
default), because `cmd_plan_register` does not write it. The asserted declared value
`!= []`.

Test (`test_plan_register_persists_ancillary_files`, in a new `tests/test_ancillary_files.py`):
`write_plan` a plan whose front-matter declares `ancillary_files: ["notes.md"]`; commit and
`run_cli(repo, "plan", "register", plan)` (assert `["ok"]`); then read the row directly —
`Ledger(gitutil.repo_identity(repo))` (mirror the `repo`/`ledger_home` access other tests
use, e.g. `test_newer_ledger_surfaces_as_a_failure_envelope_not_a_traceback` in
`test_release_surface.py`), `SELECT ancillary_files FROM plan_contract ORDER BY id DESC LIMIT
1`, and assert `json.loads(...) == ["notes.md"]`.

GREEN: add `ancillary_files=json.dumps(parsed.ancillary_files)` to the `ledger.insert(
"plan_contract", ...)` call in `cmd_plan_register`, beside `annotation_keys`. (Depends on
cycles 1 and 3.)

### Cycle 5 — classify buckets and stages a declared ancillary path

Introduces the new `ancillary` parameter on `classify`. Because a call passing an unknown
keyword would raise `TypeError` (a signature crash, not an assertion), the **pre-RED stub**
adds the parameter and the empty bucket *inert*: `classify(..., ancillary: set[str] | None =
None)` accepted but unused in the body, and `Classification.ancillary: list[str] =
field(default_factory=list)`. Declare `src/tddcli/staging.py` in `stub_expected` so the RED
commit carries that signature stub without recording it as implementation-during-RED (per the
handoff rule that a signature stub is pre-RED scaffolding).

**Expected RED (with the stub in place):** `assert c.ancillary == ["tasks/plan.md"]` fails —
the body still routes the path to `outside`, so `c.ancillary` is the empty default `[]` and
`c.outside == ["tasks/plan.md"]`.

Test (`test_declared_ancillary_file_is_bucketed_and_staged`, in
`tests/test_config_and_staging.py`, mirroring
`test_files_outside_cycle_projects_are_flagged_not_staged`):
```python
c = staging.classify(
    cfg, {"backend/app/x.py", "tasks/plan.md"}, ["backend"],
    declared(), set(), ancillary={"tasks/plan.md"},
)
assert c.ancillary == ["tasks/plan.md"]
assert c.outside == []
assert "tasks/plan.md" in staging.paths_for_phase(staging.GREEN, c)
```

GREEN: in `classify`, immediately before the `outside` branch, add `if rel in (ancillary or
set()): out.ancillary.append(rel); continue`. In `paths_for_phase`, add
`classification.ancillary` to the GREEN/REFACTOR return (beside `implementation`) — **not**
to RED or PIN. Keep the parameter defaulted so existing callers are untouched.

### Cycle 6 — end to end: committed, not flagged

**Expected RED:** with the stored list unread and unpassed, the declared file is still
`outside`: `undeclared_file_touched` fires (count `== 1`) and the file is never committed.
The test asserts count `== 0` and the file committed — both fail.

Test (`test_declared_ancillary_file_is_committed_and_not_flagged`, in
`tests/test_ancillary_files.py`, template =
`test_undeclared_dedup.py::test_unchanged_outside_file_is_flagged_once_per_cycle`): a single-cycle
plan for the synthetic `backend` project declaring `ancillary_files: ["notes.md"]`; register,
run start, write `notes.md` at the repo root, write the RED test + a stub, then advance
RED → GREEN → REFACTOR. Assert:
- `run_cli(repo, "metrics")["result"]["runs"][0]["integrity_events"].get(
  "undeclared_file_touched", 0) == 0`, and
- `notes.md` is committed on the branch — e.g. it appears in `git log --name-only`, or is
  tracked at HEAD (`git ls-files notes.md` non-empty). Use the conftest `git`/`run_cli`
  helpers; confirm the exact accessor at execution time.

GREEN: in `Engine.__init__`, add `self.ancillary_files = json.loads(
self.contract_row["ancillary_files"])` beside `self.annotation_keys`. In
`_stage_and_commit` (`advance.py`), pass `ancillary=set(engine.ancillary_files)` to the
`staging.classify(...)` call. No change to the `undeclared_file_touched` emission block is
needed — the path simply stops being `outside`.

## Deliberate scope cuts (do not build)

- **No per-cycle `ancillary_files`.** Plan-level only. A per-cycle override is a clean
  additive follow-up (it would ride `declared_cycles` JSON like `meta` did, no new column) —
  out of scope here.
- **No dedicated `[ancillary]` commit.** Declared ancillary files ride the phase's GREEN /
  REFACTOR commit. A separate `chore(ancillary): ...` commit (mirroring `commit_generated`)
  to keep cross-project files out of a project-scoped commit is a reasonable refinement, but
  it adds a second commit, a phase label for `record_commit`, and render/metrics handling —
  its own issue. The issue explicitly frames the separate commit as optional ("*or* a
  dedicated `[ancillary]` commit if cross-project staging is undesirable").
- **No run-close enforcement.** Detecting an ancillary path that *should* have been declared
  but was not, and hard-gating it at run close, is issue **#69** (`undeclared_file_uncommitted`).
  This plan only stops *declared* paths from firing the event and from being dropped. A path
  not on the list still fires `undeclared_file_touched` exactly as today.
- **Do not touch the `undeclared_file_touched` emission or its per-cycle dedup** (`advance.py`
  `_last_outside_emitted`, from #55). Cycle 5 routes declared paths out of `outside`; the
  emission code is correct as-is and keeps firing for genuinely undeclared drift.
- **Do not stage ancillary files in RED or PIN.** GREEN/REFACTOR only. A pin- or
  refactor-only cycle that must touch an ancillary file is an edge case for the follow-up;
  the two observed cases (companion doc, cross-project type-fix) land in GREEN/REFACTOR.
- **Do not touch `annotation_keys` or per-cycle `files`/`stub_expected` semantics.**
- **README/PRD documentation** of `ancillary_files:` is a post-run doc follow-up committed as
  ordinary commits on the branch, not a cycle (see Done-criteria).

## Execution

This plan is executed through `tdd-cli`. **You run every command below yourself** — do not
ask the user to start the run. `tdd run start` records which model is executing, resolved
from your own session; a run started by anyone else attributes this work to the wrong agent.

**Referee rule:** run the *released* `tdd` **0.7.0**, never this working tree's editable
install — the controller being edited mid-cycle cannot also enforce the cycle. Do not work
in a shell with this repo's `.venv` activated. Verify before starting: `tdd --version` →
**0.7.0**. If `~/.local/bin/tdd` is older, `uv tool upgrade tdd-cli` (or reinstall) until it
reports 0.7.0, and confirm `which tdd` is **not** `/Volumes/SSD/repos/tdd-cli/.venv`. The
suites under test are still this working tree's code; only the controller is pinned. This
plan uses only 0.7.0-supported front-matter keys (`n, project, title, test, files,
stub_expected, commit_red, commit_green`) — no dependency on any unreleased contract feature.

    git checkout -b feat/70-ancillary-files       # first, before anything else
    tdd doctor                                     # must report healthy: true
    tdd run start --plan tasks/issue-70-ancillary-files.md

If the branch already exists, do not force-checkout and do not pick another name: check it
out only if it carries this plan's commit and no unrelated work, otherwise stop and ask.
`tdd doctor` must be green first: if it fails on *other* uncommitted `tasks/issue-*.md`
files (sibling plans not part of this work), commit, stash, or gitignore them before
`run start`.

Then repeat until done: read `next_action.verb`, do exactly what it says, run `tdd advance`.
Stop when `next_action.terminal` is `true`.

When `next_action.terminal` is `true`, finish the run: render the friction log, commit it,
and raise the PR — see Done-criteria below.

- `tdd advance` is the only command that changes phase. Do not `git add` or `git commit` —
  the tool stages and commits, deriving the file set from the phase.
- The baseline is captured at `run start` and subtracted from later verdicts. Expected
  baseline for this repo: `{"tddcli": 0}` — anything else means a moved branch; stop.
- Verbs this plan can hit: `create_stub` on cycle 5 (the signature stub is declared in
  `stub_expected`, so the tool stages it into RED — follow the verb if it asks);
  `resolve_blocker` → `tdd blocker --kind --detail` (kinds: `plan_defect`, `tooling`,
  `regression`, `pre_existing_failure`); `confirm_cycle_applicable` on a cycle the codebase
  has outgrown → `tdd cycle skip --reason`. All six cycles are **standard** — every RED
  fails before implementation, so no `run_sensitivity_check` is expected. This plan declares
  no `annotation_keys`.

## Done-criteria

**Before finishing:** run
`tdd log render --out tasks/friction-logs/issue-70-ancillary-files-friction.md` and
`tdd metrics`. Report the plan-fidelity section — declared vs delivered vs skipped — and
every integrity event. Do not narrate what the ledger already records.

**Check for a dropped doc edit:** if the run log shows any `undeclared_file_touched` event
naming a `docs/...` or `README`/PRD file you edited, that file was staged outside the tool
and may have been dropped — verify it is committed on the branch before the PR, and commit
it manually if not.

Then the documentation follow-up, committed as ordinary commits after the run is terminal:
in `README.md`'s `## Plan contracts` section, document the top-level `ancillary_files:` list
— repo-root-relative paths, may point outside any project, classified as declared (no
`undeclared_file_touched`) and staged into the phase commit, hash-frozen with the plan. Note
it is plan-level only and distinct from per-cycle `files`.

Then commit the friction log and raise the PR:

    git add tasks/friction-logs/issue-70-ancillary-files-friction.md
    git commit -m "docs: friction log for issue-70-ancillary-files"

Then invoke the **`raise-pr` skill** (`/raise-pr`), which runs the quality gates, pushes the
branch and opens the PR against `main`. Do not push or call the GitHub API by hand. If a
gate fails, fix it and re-run the skill — a failed gate is work, not a reason to hand back.
