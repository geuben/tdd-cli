---
closes: 98
cycles:
  - n: 1
    project: tddcli
    title: "a tracked path git ignores, changed inside the cycle's project, is left out of the GREEN commit"
    test: "tests/test_ignored_paths.py::test_a_tracked_ignored_path_inside_the_cycle_project_is_left_out_of_the_green_commit"
    files: ["src/tddcli/gitutil.py", "src/tddcli/staging.py", "src/tddcli/advance.py", "docs/PRD.md"]
    commit_red: "test: a tracked path git ignores must stay out of the GREEN commit"
    commit_green: "fix: paths git's ignore rules match are build output, never staged or flagged"
    commit_refactor: "refactor: tidy the git ignore lookup"
  - n: 2
    project: tddcli
    pin_cycle: true
    title: "a tracked path git ignores, changed outside the cycle's project, fires no undeclared_file_touched"
    test: "tests/test_ignored_paths.py::test_a_tracked_ignored_path_outside_the_cycle_project_fires_no_undeclared_event"
    files: ["src/tddcli/staging.py"]
    commit_pin: "test: pin — a path git ignores fires no undeclared_file_touched"
  - n: 3
    project: tddcli
    pin_cycle: true
    title: "a tracked path git ignores, left dirty, does not block run close"
    test: "tests/test_ignored_paths.py::test_a_tracked_ignored_path_left_dirty_does_not_block_run_close"
    files: ["src/tddcli/machine.py"]
    commit_pin: "test: pin — a dirty path git ignores does not block run close"
  - n: 4
    project: tddcli
    title: "run close names the dirty paths git ignores once, as ignored_paths_dirty"
    test: "tests/test_ignored_paths.py::test_dirty_ignored_paths_are_reported_once_at_run_close"
    files: ["src/tddcli/machine.py", "README.md", "docs/PRD.md", "CHANGELOG.md"]
    commit_red: "test: run close must name the dirty paths git ignores once"
    commit_green: "feat: report dirty ignored paths once at run close as ignored_paths_dirty"
    commit_refactor: "refactor: tidy the run-close ignored-path report"
---

# Paths git ignores are build output: never staged, never undeclared, never a close blocker

## Context

[#98](https://github.com/geuben/tdd-cli/issues/98): in a real run on 0.8.0, a Gradle build
during the suite rewrote 8 files under a `.gradle/` directory inside a declared project root.
The repository's `.gitignore` has `.gradle/`. All 8 paths fired `undeclared_file_touched` on
every one of the run's 9 cycles. At the terminal `advance`, the run-close gate from #69
(`Engine.close_undeclared_gate`) blocked the run with `undeclared_file_uncommitted`, and a
person had to unblock it. The issue asks for:

1. the candidates for `undeclared_file_touched` (and so for `undeclared_file_uncommitted`) to be
   filtered through git's ignore rules, falling back to `config.is_ignored`;
2. ignored-but-dirty paths to be reported, "if at all", once per run as an informational
   `ignored_paths_dirty` line, not per cycle;
3. a regression test: a project root with an ignored directory that the suite writes into gives
   zero `undeclared_file_touched` events and does not block close.

There is no investigation report on the issue and no `investigate/issue-98` branch. Every claim
below comes from the planning probes.

### What the planning probes found (E-2, run on `origin/main`)

**The issue's stated cause is not quite right, and the difference decides the fix.** The
detector already respects `.gitignore` for untracked files. `Engine.authored_changes` reads
`gitutil.changed_paths`, which is `git status --porcelain=v1 -uall`. That command never lists
an untracked ignored file. The third probe below shows it.

The only way a path git ignores can show up in `git status` is when **it is tracked at HEAD**,
for example committed before the ignore line was added, or added with `git add -f`. Git lists
changes to tracked files whatever the ignore rules say. All of the reported symptoms fit a
tracked `.gradle/` directory:

| Probe (scratch repo and the `repo` fixture, git 2.43) | Result |
|---|---|
| Untracked `.gradle/8.0/checksums.lock` under a committed `.gradle/` ignore, written during GREEN | No event. The run closes `complete`. **Already correct today.** |
| The same path, tracked at HEAD with `git add -f`, outside the cycle's project (`backend`), modified during GREEN | `undeclared_file_touched: 1`, then `undeclared_file_uncommitted` at close: `next_action.verb == "blocked"`. **The issue, reproduced.** |
| The same, with a two-cycle plan and the path dirtied in each cycle | `undeclared_file_touched: 2` (one per cycle), then blocked at close |
| Tracked `backend/.gradle/8.0/checksums.lock`, **inside** the cycle's project, modified during GREEN | GREEN's `advance` returns `ok: false`: `"git add -- backend/.gradle/8.0/checksums.lock backend/app/calc.py failed: The following paths are ignored by one of your .gitignore files: backend/.gradle ..."`. The path lands in the `implementation` bucket and `gitutil.add` raises. **Worse than the issue: GREEN cannot commit at all.** |
| `git add -- <tracked file under an ignored dir>` | Stages the file, but exits 1 with the "paths are ignored" advice. That is the executor's "git refuses ignored paths without `-f`" from the issue. |
| `git check-ignore --stdin -z` (no `--no-index`) on that tracked path | Prints nothing, exit 1. **Tracked paths are never reported by default.** |
| `git check-ignore --no-index --stdin -z` on the same path | Prints the path, exit 0 |
| `--no-index --stdin -z` with `.gradle/`, `*.lock` and `!keep.lock`, given `app/.gradle/8.0/checksums.lock`, `keep.lock` and `src/a.py` | Prints only `app/.gradle/8.0/checksums.lock`, so negation is honoured. No match at all gives exit 1 and empty output. |

So the issue's proposed `git check-ignore --stdin` would filter **nothing**. The flag that
matters is `--no-index` (decision 2).

Test blast radius: a throwaway version of the whole change (git-ignored paths routed into
`Classification.ignored`) was run against the full suite in a scratch worktree of `origin/main`.
The only failure was `tests/test_actor_seams.py::test_only_the_actor_spawns_processes`, because
the hack spawned `git` from `staging.py` directly. The locked design (decision 2) goes through
`gitutil.git`, which goes through the actor, so that guard stays green. **No existing test
changes; no cycle declares `modifies_tests`.** The hack was discarded.

## Design decisions (locked)

1. **"Ignored by git" means matched by git's ignore rules, whether or not the path is tracked.**
   A tracked path matching `.gitignore` (or `.git/info/exclude`, or `core.excludesFile`) is
   build output, exactly like a `config.is_ignored` path. *Decided by evidence:* the probes above
   show that this is the only kind of ignored path the detector can see. The issue's
   wording, "build residue that git itself would never stage", describes it.
   `Config.is_ignored` already matches patterns without asking whether a path is tracked, and
   `staging.classify` treats its matches as "build output is never authored".

2. **The lookup is a new `gitutil.ignored_paths(worktree, paths) -> set[str]`.** It runs
   `git check-ignore --no-index --stdin -z` through `gitutil.git` and feeds the paths on stdin,
   each terminated by NUL. It returns the NUL-separated paths that git printed. Details:
   - An empty `paths` returns `set()` without spawning.
   - `gitutil.git` gains an `input: str | None = None` keyword, passed to
     `actor.current().run_argv(argv, input=input)`. `Actor.run_argv` and `SudoActor.run_argv`
     already accept `input`, so `actor.py` is unchanged and the spawn guard
     (`tests/test_actor_seams.py`) stays green.
   - **Mechanism footguns, all probed:**
     - Without `--no-index`, check-ignore reports no tracked path, so the whole fix would do
       nothing.
     - check-ignore exits 1 when nothing matches, so the call is `check=False`. Otherwise
       `gitutil.git` raises on every advance with no ignored dirt.
     - Do not pass `-v`. With `-v`, negated (`!`) matches are printed too, and would read as
       ignored.

   With `check=False`, a fatal check-ignore error (exit 128, empty stdout) yields `set()`, which
   is today's behaviour. That is accepted, and gets no test of its own.

   The issue's "falls back to `config.is_ignored` for the non-git case" needs no code. tdd-cli
   refuses to run outside a git worktree (`gitutil.worktree_root`), and `config.is_ignored` keeps
   applying beside the git rules (decision 3). *Decided by evidence (the probes; the issue's
   proposal) and by convention:* every other path-list git call passes through `gitutil.git`,
   and `actor.py` is the only place that spawns.

3. **Where the filter goes: `staging.classify`, beside `config.is_ignored`, at the top of the
   loop and before every other bucket.** `classify` gains a keyword `ignored: set[str] | None =
   None`. Its first branch becomes "`config.is_ignored(rel)` **or** `rel` is in `ignored`", which
   appends to `out.ignored` and continues. `advance._stage_and_commit` computes
   `gitutil.ignored_paths(engine.worktree, sorted(changed))` and passes it in. `classify` stays
   free of git. The existing positional calls in `tests/test_config_and_staging.py` keep working
   because the new parameter defaults to `None`. Because the branch comes before every other
   bucket:
   - an ignored path is never in `implementation`, so it is never staged and GREEN cannot crash
     (cycle 1);
   - it is never in `outside`, so `undeclared_file_touched` cannot fire for it (cycle 2);
   - the run-close gate only reads `undeclared_file_touched` details, so it cannot block on it
     (cycle 3).

   This is why cycles 2 and 3 are pins. *Decided by evidence (the issue: "filter the candidate
   set … and therefore `undeclared_file_uncommitted`"; the inside-the-project crash probe) and
   by convention (the `config.is_ignored` branch already sits there).* A filter on the
   `outside` bucket alone, or in the emission block in `advance.py`, would leave GREEN crashing
   on the inside case. It is not allowed.

4. **`ignored_paths_dirty` is built, once per run, at run close.** Inside
   `Engine.close_undeclared_gate`, after the existing `undeclared_file_dropped` logic:
   - take the gate's `dirty` set (`gitutil.dirty_paths`);
   - run it through `gitutil.ignored_paths`;
   - if the result is non-empty, write **one** event of kind `ignored_paths_dirty` with
     `detail = json.dumps(sorted(paths))`.

   The gate runs once, when the last declared cycle closes, so the event is once per run. A
   blocked close reports it as well, because it is written before the blocker. It carries
   **the closing cycle's id** (`cycle_row["id"]`), not `None`. The friction log renders cycle
   events as `- **Event — <kind>:** <detail>` lines (`render.friction_log`), while run-level
   (`None`) events appear only as `kind×n` counts in the header. The issue asks for an
   informational *line*. The `undeclared_file_uncommitted` blocker written by the same close is
   also attached to the closing cycle.

   It names only paths git's ignore rules match, not `config.is_ignored`-only paths. An untracked
   `.pytest_cache/` without a `.gitignore` line would otherwise put noise in every run, and the
   issue is about `.gitignore`. Pre-existing dirt is not subtracted: the event says what is
   dirty and ignored when the run ends. It is informational: not in `NUDGE_KINDS`, not a blocker,
   and the outcome is unchanged.

   *Decided by evidence:* the issue proposes the name, the once-per-run cadence and "informational
   line". Its "if at all" is settled toward building it because of decision 3. After the fix, a
   tracked ignored file a build rewrote is neither committed nor flagged, and stays dirty when
   the run ends. Without this event nothing in the ledger says so. The Scope policy also says
   build what the issue asks for rather than trim it. *By convention:* `undeclared_file_dropped`
   is the gate's other informational event, emitted from the same method.

5. **Docs move with the behaviour, and need no `SCHEMA_VERSION` bump.**
   - In cycle 1, `docs/PRD.md` R9.16 gains the git-ignore exception.
   - In cycle 4, `docs/PRD.md`'s IntegrityEvent list gains `ignored_paths_dirty`; `README.md`'s
     "Run-close gate for undeclared file touches" section gains the ignored-path paragraph; and
     `CHANGELOG.md` gains a line under `## [Unreleased]`.

   The event is a new `kind` value in the existing `integrity_event` table, with no shape
   change, so no `SCHEMA_VERSION` bump and no frozen referee. *By convention
   (`.claude/plan-issue.md`; `RELEASING.md`).*

## Not in scope (not asked for)

These are not cuts of anything the issue asks for. They are related surfaces the issue does not
name. Rule 4 (no future-proofing) keeps them out:

- **`tdd doctor`'s "worktree clean" check, and `snapshot.authored_dirty`** (sensitivity
  fingerprints) still use `config.is_ignored` only. A tracked ignored file left dirty by one run
  would fail doctor in the *same* checkout before the next run. Doctor's own detail names it,
  and `implement-issue` runs every run in a fresh clone. A sensitivity check whose suite rewrites
  a tracked ignored file could see a fingerprint mismatch. Neither was observed or asked for.
- **`gitutil.tree_hash`** (`git add -A` into a throwaway index) still hashes tracked ignored
  files. A build that rewrites one counts as a change for `no_change_since_last_run`. That is
  the permissive direction, and nobody has reported it.

## Fake/real divergence

None. Every test drives the real CLI in-process (`conftest.run_cli`) over a real git repository
(the `repo` fixture), with a real `git check-ignore`.

## Cycles

All four tests live in a new file, `tests/test_ignored_paths.py`, which cycle 1 creates. The
module docstring cites issue #98. Import `from conftest import git, run_cli, run_cli_text,
write_plan`, and add `from tddcli import gitutil` and `from tddcli.ledger import Ledger` only if
a test needs them. None of the four does. No cycle declares a stub: every test imports only
names that exist today.

**Fixture values: all cycles use exactly these.**

- The `.gitignore` line: `.gradle/`, appended to the `repo` fixture's existing `.gitignore`.
- The path inside the project: `backend/.gradle/8.0/checksums.lock`. Used in cycle 1.
- The path outside the project: `.gradle/8.0/checksums.lock`, at the repository root, outside the
  `backend` root. Used in cycles 2, 3 and 4. The real incident's path was in a *different*
  project's root. Both land in the same `outside` bucket (`staging.classify`: `owner is None or
  owner.root not in roots`), so the repository root stands in for it.
- A helper, written in cycle 1:
  `_track_ignored(repo, rel)`
  - writes `v1\n` to `repo / rel`, creating the parent directories;
  - appends `.gradle/\n` to `.gitignore`;
  - runs `git add .gitignore`, then `git add -f <rel>`;
  - commits with the message `"a tracked file the ignore rules match"`.

  The helper is called **before** `write_plan`, so the path is clean at `run start`.
- The one-cycle plan `ONE`, used by cycles 1 to 3:

  ```yaml
  cycles:
    - n: 1
      project: backend
      title: "adding two numbers"
      test: "tests/test_add.py::test_add_two_numbers"
      stub_expected: ["app/calc.py"]
  ```

- The two-cycle plan `TWO`, used by cycle 4: `ONE` plus

  ```yaml
    - n: 2
      project: backend
      title: "subtracting two numbers"
      test: "tests/test_sub.py::test_subtract_two_numbers"
      stub_expected: ["app/sub.py"]
  ```

- A helper, written in cycle 1: `_drive_one_cycle(repo, rel, content)`. It drives one
  `add` cycle and returns `(red, green, close)`, the three envelopes:
  1. write `backend/tests/test_add.py`:
     `from app.calc import add` / `def test_add_two_numbers(): assert add(2, 3) == 5`;
  2. write the stub `backend/app/calc.py`: `def add(a, b): raise NotImplementedError`;
  3. `advance` (red);
  4. write `content` to `repo / rel`;
  5. write the real `add`: `return a + b`;
  6. `advance` (green);
  7. `advance` (close).

  The cycle 1 and cycle 3 assertions below use `_drive_one_cycle`'s return value. Cycle 2 reads
  metrics after it. Every test first runs `plan register` and `run start --plan` on its plan.

### Cycle 1: a tracked path git ignores, inside the cycle's project, stays out of the GREEN commit

- **Behaviour:** a path that git's ignore rules match is never staged, even when it is tracked
  and inside the cycle's project.
- **Test:** `test_a_tracked_ignored_path_inside_the_cycle_project_is_left_out_of_the_green_commit`
  1. `_track_ignored(repo, "backend/.gradle/8.0/checksums.lock")`;
  2. register and start `ONE`;
  3. `red, green, _ = _drive_one_cycle(repo, "backend/.gradle/8.0/checksums.lock", "v2\n")`.

  Single assertion: `assert green["result"].get("staged") == ["backend/app/calc.py"]`.
- **Production target:**
  - `gitutil.ignored_paths` and `gitutil.git`'s `input` keyword (decision 2);
  - `staging.classify`'s `ignored` keyword (decision 3);
  - `advance._stage_and_commit`, which passes the set in;
  - `docs/PRD.md` R9.16 gains one sentence: *"A path git's ignore rules match is build output
    whether or not it is tracked (`git check-ignore --no-index`). Like a `config.is_ignored`
    path, it is never staged and never recorded as `undeclared_file_touched`, so the run-close
    gate never sees it (#98)."*
- **EXPECTED FAILURE** (probed): `AssertionError: assert None == ['backend/app/calc.py']`.
  GREEN's envelope is `ok: false` with `result: {}`, because `gitutil.add` raised `git add --
  backend/.gradle/8.0/checksums.lock backend/app/calc.py failed: The following paths are ignored
  by one of your .gitignore files`. The helper's third `advance` then returns an ordinary
  `no_change_since_last_run` envelope, so the test reaches its assertion and nothing raises
  first (probed).

### Cycle 2 (pin): a tracked path git ignores, outside the project, fires no `undeclared_file_touched`

- **Behaviour:** the issue's detector clause. The 72-line flood cannot recur.
- **Test:** `test_a_tracked_ignored_path_outside_the_cycle_project_fires_no_undeclared_event`
  1. `_track_ignored(repo, ".gradle/8.0/checksums.lock")`;
  2. register and start `ONE`;
  3. `_drive_one_cycle(repo, ".gradle/8.0/checksums.lock", "v2\n")`;
  4. `events = run_cli(repo, "metrics")["result"]["runs"][0]["integrity_events"]`.

  Single assertion: `assert events.get("undeclared_file_touched", 0) == 0`.
- **Why a pin:** cycle 1's GREEN puts every path git ignores into `Classification.ignored`
  before the `outside` check (decision 3), so this passes on arrival. Before cycle 1 it fails
  with `AssertionError: assert 1 == 0` (probed with exactly this test). The after-state was
  not probed, because probing it would mean building cycle 1. It follows from the locked branch
  order.
- **If it fails on arrival:** cycle 1's GREEN did not follow decision 3. Do not edit production
  code in a pin cycle. File `tdd blocker --kind plan_defect --detail '...'` naming where cycle 1
  put the filter.

### Cycle 3 (pin): a tracked path git ignores, left dirty, does not block run close

- **Behaviour:** the issue's close-gate clause.
- **Test:** `test_a_tracked_ignored_path_left_dirty_does_not_block_run_close`
  1. `_track_ignored(repo, ".gradle/8.0/checksums.lock")`;
  2. register and start `ONE`;
  3. `_, _, close = _drive_one_cycle(repo, ".gradle/8.0/checksums.lock", "v2\n")`.

  Single assertion: `assert close["next_action"]["verb"] == "complete"`.
- **Why a pin:** `Engine.close_undeclared_gate` flags only paths named in
  `undeclared_file_touched` details. After cycles 1 and 2 there are none, so this passes on
  arrival. Before cycle 1 it fails with `AssertionError: assert 'blocked' == 'complete'`
  (probed with exactly this test). The envelope's `result` is `{"kind":
  "undeclared_file_uncommitted", "paths": [".gradle/8.0/checksums.lock"]}`.
- **If it fails on arrival:** the same instruction as cycle 2.

### Cycle 4: run close names the dirty paths git ignores, once, as `ignored_paths_dirty`

- **Behaviour:** decision 4. Once per run, not per cycle, on the closing cycle, rendered as a
  friction-log line.
- **Test:** `test_dirty_ignored_paths_are_reported_once_at_run_close`
  1. `_track_ignored(repo, ".gradle/8.0/checksums.lock")`;
  2. register and start `TWO`;
  3. `_drive_one_cycle(repo, ".gradle/8.0/checksums.lock", "v2\n")`, which closes cycle 1 and
     opens cycle 2;
  4. drive cycle 2 inline:
     1. write `backend/tests/test_sub.py`:
        `from app.sub import sub` / `def test_subtract_two_numbers(): assert sub(5, 3) == 2`;
     2. write the stub `backend/app/sub.py`: `def sub(a, b): raise NotImplementedError`;
     3. `advance`;
     4. write `v3\n` to the ignored path;
     5. write the real `sub`: `return a - b`;
     6. `advance`, then `advance`;
  5. `rendered = run_cli_text(repo, "log", "render")`.

  Single assertion:

  ```python
  assert rendered.count('- **Event — ignored_paths_dirty:** [".gradle/8.0/checksums.lock"]') == 1
  ```

  The path is dirty through both cycles. A per-cycle emission gives a count of 2, and a
  run-level (`None`) event gives 0, because `None` events render only as a header count. So the
  assertion pins the cadence and the placement as well as the paths. The expected string is
  built from the fixture path, not from production code.
- **Production target:**
  - `Engine.close_undeclared_gate` in `src/tddcli/machine.py` (decision 4); `machine.py`
    already imports `gitutil`;
  - `docs/PRD.md`: add `ignored_paths_dirty` to the IntegrityEvent typed list;
  - `README.md`, in "Run-close gate for undeclared file touches", after the three bullets, add a
    paragraph:

    > Paths git's ignore rules match are build output, tracked or not. They are never staged,
    > never fire `undeclared_file_touched`, and so never reach this gate. When the last cycle
    > closes, any of them still dirty are named once, in an `ignored_paths_dirty` event on that
    > cycle. It is an informational line in the friction log and blocks nothing.

  - `CHANGELOG.md`: under `## [Unreleased]`, a `### Fixed` entry:

    > Paths git's ignore rules match, including tracked ones such as a committed `.gradle/`,
    > are no longer staged, flagged `undeclared_file_touched` or held by the run-close gate. A
    > tracked one inside the cycle's project no longer fails GREEN's commit. Any left dirty
    > are named once at run close in a new informational `ignored_paths_dirty` event (#98).
- **EXPECTED FAILURE** (probed on `origin/main`): `assert 0 == 1`. Today the render has two
  `undeclared_file_touched` event lines and an `undeclared_file_uncommitted` blocker. After
  cycles 1 to 3 it has neither, and still no `ignored_paths_dirty` line, so cycle 4's RED still
  fails `0 == 1`.

## Execution

This plan is executed through `tdd-cli`. **You run every command below yourself** — do not ask the
user to start the run. `tdd run start` records which model is executing, resolved from your own
session; a run started by anyone else attributes this work to the wrong agent.

    git checkout -b issue-98-ignored-paths-are-build-output   # first, before anything else
    tdd doctor                                  # healthy, or failing only for projects this plan cannot reach
    tdd run start --plan tasks/issue-98-ignored-paths-are-build-output.md   # captures baselines, opens cycle 1

`tdd doctor` checks every project; `tdd run start` probes only the ones the plan declares and
those downstream of them through an `[artifact]`. A failing check on a project outside that set
does not stop the run: note it and go on. Any other failing check stops it.

If the branch already exists, do not force-checkout and do not pick another name: check it out
only if it carries this plan's commit and no unrelated work, otherwise stop and ask.

Then repeat until done: read `next_action.verb`, do exactly what it says, run `tdd advance`.
Stop when `next_action.terminal` is `true`.

When `next_action.terminal` is `true`, finish the run: render the friction log, commit it, and
raise the PR — see Done-criteria below.

- `tdd advance` is the only command that changes phase. Do not `git add` or `git commit` — the
  tool stages and commits, deriving the file set from the phase.
- The baseline is captured at `run start` and subtracted from later verdicts. The suite is green
  at the plan's base (verified in a fresh worktree of `origin/main`: `722 passed`). Expect
  `baselines: {tddcli: 0}`.
- The referee is the released `tdd` on `PATH` (the note at the top of `tdd.toml`), never
  `uv run tdd`.
- Verbs this plan will hit:
  - `write_test`, `write_implementation`, `refactor_or_advance`.
  - `run_sensitivity_check` → `tdd sensitivity begin|check|end`, if a standard RED pre-passes.
    Mutate the increment that cycle added.
  - `annotate_cycle` → `tdd annotate --key --value`. This plan declares no keys of its own;
    `plan_defect` and `friction_note` are reserved.
  - `resolve_blocker` → `tdd blocker --kind <plan_defect|environment> --detail '...'`. A pin
    (cycle 2 or 3) that fails on arrival is `plan_defect`, as each cycle says.
  - `confirm_cycle_applicable` on a non-existent cycle → `tdd cycle skip --reason`.
  - No cycle declares a stub: every test imports only names that exist today.

**Minimal GREEN, per cycle — add this and nothing earlier:**

- Cycle 1 adds:
  - `gitutil.ignored_paths`, and the `input` keyword on `gitutil.git`;
  - the `ignored` keyword on `staging.classify`, checked beside `config.is_ignored` in the
    loop's **first** branch;
  - the call in `advance._stage_and_commit`;
  - the R9.16 sentence in `docs/PRD.md`.

  Nothing in `machine.py`, and no `ignored_paths_dirty`.
- Cycles 2 and 3 are pins. They add only their test.
- Cycle 4 adds:
  - the `ignored_paths_dirty` event in `Engine.close_undeclared_gate`;
  - the PRD IntegrityEvent entry;
  - the README paragraph;
  - the CHANGELOG entry.

## Done-criteria

**Before finishing:** run `tdd log render --out tasks/friction-logs/issue-98-ignored-paths-are-build-output-friction.md` and `tdd metrics`. Report the plan-fidelity section — declared vs delivered vs skipped — and every integrity event. Do not narrate what the ledger already records.

Then commit the friction log and raise the PR:

    git add tasks/friction-logs/issue-98-ignored-paths-are-build-output-friction.md
    git commit -m "docs: friction log for issue-98-ignored-paths-are-build-output"

Then invoke the **`raise-pr` skill** (`/raise-pr`), which runs the quality gates, pushes the
branch and opens the PR against `main`. Do not push or call the GitHub API by hand. If a gate
fails, fix it and re-run the skill — a failed gate is work, not a reason to hand back.

The PR body says `Closes #98`. Cycles 1 and 4 own the docs:

- `git diff --stat origin/main -- docs/PRD.md` must be non-empty, or the PR body says why.
- `git diff --stat origin/main -- README.md` must be non-empty, or the PR body says why.
- `git diff --stat origin/main -- CHANGELOG.md` must be non-empty, or the PR body says why.

The visible change is ledger and friction-log content, so no demo recording is required. In the
PR body, quote the `- **Event — ignored_paths_dirty:** …` line from cycle 4's test render. Also
say that the root cause was **tracked** paths that the ignore rules match. That is why the fix
uses `git check-ignore --no-index`.
