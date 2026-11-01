---
closes: 234
cycles:
  - n: 1
    project: tddcli
    pin_cycle: true
    title: "the last cycle keeps the run-close gate, and an unblock still completes the run"
    test: "tests/test_cycle_close_gate.py::test_the_last_cycle_keeps_the_run_close_gate"
    files: ["src/tddcli/advance.py"]
    commit_pin: "test: pin — the last cycle keeps the run-close gate"
  - n: 2
    project: tddcli
    title: "a flagged path still dirty holds an earlier cycle's close"
    test: "tests/test_cycle_close_gate.py::test_a_dirty_flagged_path_holds_the_cycle_close"
    files: ["src/tddcli/machine.py", "src/tddcli/advance.py", "docs/PRD.md", "README.md", "CHANGELOG.md"]
    modifies_tests: ["tests/test_undeclared_dedup.py::test_dedup_is_per_cycle_not_per_run"]
    commit_red: "test: a dirty flagged path must hold the cycle close"
    commit_green: "fix: a flagged path still dirty holds the cycle close, not only the run close"
    commit_refactor: "refactor: share the blocked-close envelope"
  - n: 3
    project: tddcli
    pin_cycle: true
    title: "committing or discarding the held path, then unblocking, lets the next advance close the cycle"
    test: "tests/test_cycle_close_gate.py::test_committing_or_discarding_the_held_path_lets_the_cycle_close"
    files: ["src/tddcli/machine.py"]
    commit_pin: "test: pin — a committed or discarded held path lets the cycle close"
  - n: 4
    project: tddcli
    pin_cycle: true
    title: "unblocking with the path still dirty holds the close again"
    test: "tests/test_cycle_close_gate.py::test_unblocking_with_the_path_still_dirty_holds_the_close_again"
    files: ["src/tddcli/machine.py"]
    commit_pin: "test: pin — an unblock that leaves the path dirty is held again"
  - n: 5
    project: tddcli
    title: "a RED taken on a dirty tree names the paths its commit left out"
    test: "tests/test_red_on_dirty_tree.py::test_a_red_on_a_dirty_tree_names_the_paths_its_commit_left_out"
    files: ["src/tddcli/advance.py", "docs/PRD.md", "CHANGELOG.md"]
    commit_red: "test: a RED on a dirty tree must name the paths its commit left out"
    commit_green: "feat: record red_on_dirty_tree when the RED commit leaves changed paths out"
    commit_refactor: "refactor: tidy the red_on_dirty_tree emission"
---

# A flagged undeclared edit must not cross into the next cycle

## Context

[#234](https://github.com/geuben/tdd-cli/issues/234): `Engine.close_undeclared_gate`, the
run-close gate from #69, runs only when the **last** cycle closes. `_handle_refactor` in
`src/tddcli/advance.py` computes `last = not any(c.ordinal > cycle["ordinal"] for c in
engine.declared)` and calls the gate only `if last`. Between cycles, a path flagged
`undeclared_file_touched` can stay dirty and carry into the next cycle:

1. The next cycle's RED runs on the dirty tree, so its RED verdict is not a verdict on the RED
   commit.
2. If the path is inside a project the next cycle covers, `staging.paths_for_phase(GREEN, ...)`
   takes it into that cycle's GREEN commit, mixed in with the cycle's own change.

This was seen in a real run. In cycle 4 the executor reverted a production file in a project
outside cycle 4's projects. tdd flagged it `undeclared_file_touched` and left it uncommitted.
Cycle 5's RED ran on the dirty tree, and the revert landed in cycle 5's GREEN commit.

The issue proposes two things:

- **At cycle close**, the run-close gate's check over the paths flagged during that cycle. A
  path still dirty is a typed blocker, with the run-close resolutions: commit it as its own
  commit in this cycle, or discard it with a recorded justification. The run-close gate stays
  as the final backstop.
- **At RED**, when the tree has dirty paths outside the cycle's staged set, record them on the
  RED invocation, or as an event, so an auditor can tell that the RED verdict was taken on a
  tree that differs from the RED commit.

It keeps #98's rule that paths git ignores are build output: never staged, never flagged, never
a close blocker.

There is no investigation report on the issue and no `investigate/issue-234` branch. The issue
was filed and classified by automation (the `dispatch:classify` comment), and no person has
commented. Every claim below comes from reading the code and from the planning probes.

### What the planning probes found (E-2, run in a scratch worktree of `origin/main`)

| Probe | Result |
|---|---|
| Two-cycle plan. `notes.md` (outside `backend`) is written during cycle 1's GREEN and never committed. Cycle 1 is closed | Close reply `write_test`, `"Cycle 1 closed. Cycle 2 (...)"`. Metrics: `outcome: None`, `cycles_closed: 1`, `undeclared_file_touched: 1`. `git status`: `?? notes.md`. **The issue, reproduced.** |
| One-cycle plan, the same stray file, the last cycle is closed, then `resume --unblock --note ...` | Close reply `blocked`, `result: {kind: undeclared_file_uncommitted, paths: ["notes.md"], commit: null}`. The unblock replies `complete`. **Today's run-close gate. Cycle 1 pins it.** |
| Cycle 2's RED on a tree that also holds an undeclared module, `notes.md`, an ancillary path and a modified tracked file git ignores | No event names the tree. Only `implementation_during_red` and `undeclared_file_touched` fire, and neither says the verdict's tree differed from the commit. |
| A throwaway version of the whole change, in the scratch worktree: decisions 1 to 6 | Two-cycle close: `blocked`, `paths: ["notes.md"]`, metrics `outcome: blocked`, `cycles_closed: 0`, `blockers: {undeclared_file_uncommitted: 1}`. After a commit **or** a delete of `notes.md`, then `resume --unblock` (reply `refactor_or_advance`, `"Resumed at cycle 1, phase AWAITING_REFACTOR"`), the next `advance` replies `write_test`, `"Cycle 1 closed. ..."`, run cycle 2. After an unblock with `notes.md` left dirty, the next `advance` replies `blocked` again with `paths: ["notes.md"]`, and the blockers count is 2. The RED event's details were `[["backend/app/helper.py", "docs/companion.md", "notes.md"]]`. |
| The full suite against that throwaway version | `1 failed, 868 passed`. The one failure is `tests/test_undeclared_dedup.py::test_dedup_is_per_cycle_not_per_run`, which carries a dirty `shared.md` from cycle 1 into cycle 2: the very thing this issue forbids (see decision 8). `mypy` and `ruff` were clean. |

The throwaway version and the probe files were deleted with the scratch worktree.

## Design decisions (locked)

1. **The cycle-close gate holds every cycle except the last, over the paths that cycle
   flagged.** It is a new method, `Engine.cycle_undeclared_gate(cycle_row) -> list[str]`, in
   `src/tddcli/machine.py` beside `close_undeclared_gate`. The method:
   - takes the union of the JSON lists in the `detail` of this cycle's
     `undeclared_file_touched` events. It reads them with the existing
     `self.ledger.cycle_events(cycle_row["id"])`, filtered on `row["kind"]`;
   - keeps the paths in `gitutil.dirty_paths(self.worktree)`;
   - returns them sorted.

   It emits no event. `undeclared_file_dropped` and `ignored_paths_dirty` stay run-close only,
   as #69 and #98 made them.
   - *Decided by evidence.* The issue says "any path flagged `undeclared_file_touched` during
     this cycle that is still dirty", and "The run-close gate stays as the final backstop". So
     the last cycle keeps `close_undeclared_gate` unchanged, over the whole run's flags, and
     cycle 1 pins that. "Dirty" means what it means in the run-close gate:
     `gitutil.dirty_paths` lists tracked modifications and untracked files.
   - *Decided by convention.* No new `Ledger` method, so no change to `GUEST_READS` and no
     socket-mode compatibility note. `render.friction_log` reads `cycle_events` the same way,
     and `tests/test_ledger_surface.py::test_no_module_but_the_ledger_speaks_sql` forbids SQL
     outside `ledger.py`. A first throwaway version that queried `integrity_event` directly
     failed that test.

2. **Where it runs.** In `_handle_refactor`, at the point where `close_undeclared_gate` runs
   today: after the close sweep has passed, and before `engine.close_cycle`. So:
   - the annotation gate, the REFACTOR commit, the artifact checks and the sweep all come
     first, unchanged;
   - an agent-fixable failure (a sweep regression, a stale artifact) is replied before a
     person is needed. If the agent fixes such a failure by reverting the stray edit, no
     person is needed at all.

   The REFACTOR commit's `_stage_and_commit` is the cycle's last chance to flag a path. It runs
   in the same `advance`, before the gate, so the gate sees every path the cycle flagged.
   *Decided by convention:* the gate sits where the run-close gate already sits.

3. **A held close is the run-close gate's typed blocker, but the cycle stays open.** When
   `cycle_undeclared_gate` returns paths, `_handle_refactor` does all of this and does **not**
   call `close_cycle`:
   1. `engine.ledger.add_blocker(run_id, cycle_id, "undeclared_file_uncommitted",
      json.dumps(paths))`;
   2. `engine.ledger.end_run(run_id, "blocked")`;
   3. returns an `Envelope` shaped like today's run-close `BLOCKED` envelope:
      - `run`: `id`, `plan`, `cycle`, `of`, `phase: "BLOCKED"`, `executor`;
      - `result`: `{"kind": "undeclared_file_uncommitted", "paths": paths, "commit": sha}`;
      - `next_action`: `NextAction(Verb.BLOCKED, ...)`. The detail names the cycle and the
        paths, and says: commit each path in a commit of its own, or discard it (revert or
        delete it), then `tdd resume --unblock --note ...`, then `tdd advance`.

   The cycle stays in `AWAITING_REFACTOR` with `closed_at` NULL. `resume --unblock` reopens the
   run, and `ledger.open_cycle` finds that cycle again. The next `advance` re-enters
   `_handle_refactor` and checks again.
   - *Decided by evidence.* The issue says "a typed blocker. The resolutions are the same as at
     run close". The blocker kind is #69's `undeclared_file_uncommitted`, because it is the
     same check.
   - *Decided by convention.* `cmd_blocker` already writes a blocker and ends the run `blocked`
     while a cycle is open. `cmd_resume --unblock` already reopens such a run at its open
     cycle. R8.7 says a blocked run is not live, so the stop hook releases. The kind stays out
     of `BLOCKER_KINDS`, as #69 decided, because that set validates only the manual
     `tdd blocker`.
   - The detail text is not asserted. Cycle 2's projection pins the verb, `result.kind`,
     `result.paths`, the run's outcome and that no cycle closed. Do not route this envelope
     through `_reply`: a blocked run has no live phase, and the run-close envelope does not use
     `_reply` either.

4. **An unblock does not excuse the path; the next `advance` checks again.** No state records
   that a path was "already blocked". The gate's only input is the cycle's flags and the
   worktree.
   - Committing the path makes it clean, so the close proceeds.
   - Discarding it (delete an untracked file; `git checkout -- <path>` for a tracked one) also
     makes it clean, so the close proceeds. The unblock note is the recorded justification.
   - An unblock that leaves the path dirty is held again, with a second blocker row.

   *Decided by evidence:* the issue's problem is the dirty edit carrying into the next cycle
   (its points 1 and 2). An unblock that let it through would bring the bug back.

   This differs from the last cycle on purpose. There, an unblock completes the run with the
   path still dirty (cycle 1 pins this), because no later cycle can take it in. Decision 1
   keeps that unchanged.

5. **`tdd cycle skip` is not gated.** The issue asks for the gate "at cycle close", and in this
   code that is `Engine.close_cycle`, reached from `_handle_refactor`. `cmd_cycle_skip` is a
   separate path (`ledger.skip_cycle`), and #69 left it ungated too. Refusing a skip would be a
   new refusal on a verb the issue does not name. Any dirt a skipped cycle leaves is named by
   the next cycle's `red_on_dirty_tree` (decision 6) and, if it is outside that cycle's
   projects, by its `undeclared_file_touched`. *Decided by evidence* (the issue's wording), and
   by the convention that a default keeps today's behaviour.

6. **At RED: an integrity event, `red_on_dirty_tree`, not a new invocation column.** The issue
   allows either. A column on `invocation` would change an existing table's shape: a
   `SCHEMA_VERSION` bump and a frozen referee. An event kind is a new row value in the existing
   `integrity_event` table. *Decided by convention* (`.claude/plan-issue.md`: bump only when an
   existing table's shape changes). The name follows `implementation_during_red` and
   `ignored_paths_dirty`.
   - **Where:** in `advance._stage_and_commit`, inside the existing `if phase == staging.RED:`
     block. It goes after `implementation_during_red` and after `paths =
     staging.paths_for_phase(phase, classification)`, so move that line up, above the RED
     block, or compute the event after it.
   - **What:** `left = sorted(set(changed) - set(paths) - set(classification.ignored))`, where
     `changed` is the `engine.authored_changes(cycle)` set the function already computed. If
     `left` is non-empty, write one `engine.ledger.event(run_id, cycle_id,
     "red_on_dirty_tree", json.dumps(left))`.
   - **What that includes:** implementation written during RED, paths outside the cycle's
     projects, plan-declared `ancillary_files` (RED commits only tests and stubs), and
     generated paths. Each of these was in the tree the RED verdict ran on, and none is in the
     RED commit.
   - **What it excludes:**
     - paths git ignores or `tdd.toml` ignores, which are `classification.ignored`. The issue
       keeps #98's rule.
     - pre-existing dirt, which `Engine.authored_changes` already drops and `run start`
       records.
   - Nothing is written when `left` is empty, which is the normal RED. The test's clean cycle 1
     pins this.

   RED's verdict and its commit come from one `advance`, with no edit in between. So the tree
   at staging is the tree the verdict ran on. The event is not in `NUDGE_KINDS` and blocks
   nothing (P2). It is a cycle event, so the friction log renders it as a
   `- **Event — red_on_dirty_tree:** [...]` line on that cycle (`render.friction_log`), with
   no change to `render.py`.
   - *Decided by evidence:* the issue ("so an auditor can tell"). Pin commits are left alone,
     because the issue names RED only.

7. **Docs move with the behaviour. No schema bump.**
   - **Cycle 2:**
     - `docs/PRD.md` R9.16 gains the cycle-close gate.
     - `docs/PRD.md` §12's "Recorded, never blocked" line names the exception.
     - `README.md`'s "Run-close gate for undeclared file touches" section gains the cycle-close
       paragraph. Its "Enforcement boundary" sentence on the exception is widened.
     - `CHANGELOG.md` gains a `### Fixed` line under `## [Unreleased]`.
   - **Cycle 5:**
     - `docs/PRD.md`'s IntegrityEvent list gains `red_on_dirty_tree`.
     - `CHANGELOG.md` gains an `### Added` line.

   The exact text is in each cycle. `docs/`, `README.md` and `CHANGELOG.md` are in-project here
   (root `.`), so they go in `files`, not `ancillary_files`. *By convention* (#98's plan,
   `RELEASING.md`). Changing what PRD §12 lists as never blocked is what the issue asks for.
   The README already carves out the run-close exception to it.

8. **The one broken test keeps its purpose.**
   `tests/test_undeclared_dedup.py::test_dedup_is_per_cycle_not_per_run` (#55) checks that
   each cycle touching the same stray path records its own event. Today it leaves `shared.md`
   dirty across cycle 1's close, which the gate now holds. Cycle 2 changes it so the path is
   flagged in both cycles without carrying over:
   - after the GREEN `advance` of cycle 1, and before the closing `advance`, commit it with
     `git(repo, "add", "shared.md")` and `git(repo, "commit", "-q", "-m", "docs: shared
     scratch")`. This is the sanctioned resolution, done before the gate looks;
   - at the start of cycle 2, before writing `test_sub.py`, rewrite it with
     `(repo / "shared.md").write_text("shared scratch, again\n")`;
   - import `git` from `conftest`.

   Its assertion stays `== 2` and is not weakened. It was probed: the changed test passes on
   today's code and on the throwaway version.

## Not in scope (not asked for)

These are not cuts of anything the issue asks for. Rule 4 (no future-proofing) keeps them out:

- **Gating `tdd cycle skip`** (decision 5).
- **A tool-made commit of the held path.** The issue's resolutions are the run-close ones: a
  person commits or discards, then unblocks.
- **A `red_on_dirty_tree` on pin commits** (decision 6).
- **An unblock at the last cycle leaves the run with `outcome` NULL.** The planning probe saw
  it: after the run-close gate blocks, `resume --unblock` replies `complete`, but metrics
  report `outcome: None`, because `reopen_run` clears the outcome and nothing ends the run
  again. This is today's behaviour, unrelated to this issue. Cycle 1 asserts only the verbs,
  so it neither pins nor changes it.

## Fake/real divergence

None. Every test drives the real CLI in-process (`conftest.run_cli`) over a real git repository
(the `repo` fixture), with real `git status` and real commits.

## Invariant registry, mirrors

There is no `docs/INVARIANTS.md` in this repo. Nothing mirrors `advance.py` or `machine.py`.
`close_undeclared_gate` and the new `cycle_undeclared_gate` are two checks at two points, not
two copies of one: the first is run-wide and emits events, the second is cycle-scoped and emits
none.

## Cycles

**Test files.**
- Cycles 1 to 4 put their tests in a new file, `tests/test_cycle_close_gate.py`, which cycle 1
  creates. Its module docstring cites issue #234.
- Cycle 5 puts its test in a new file, `tests/test_red_on_dirty_tree.py`, with the same kind of
  docstring.

Both import only names that exist today: `from conftest import git, run_cli, write_plan`,
`json`, `shutil`, and, in cycle 5 only, `from tddcli import gitutil` and `from tddcli.ledger
import Ledger`. No cycle declares a stub. Write module-level imports only for what that file's
tests use, or ruff fails the close sweep.

**Fixture values. Every cycle uses exactly these.**

- The stray path: `notes.md`, at the repository root, outside the `backend` root. It lands in
  `Classification.outside` (`staging.classify`: `owner is None or owner.root not in roots`),
  like the real incident's path in another project's root. Its content is `"scratch notes\n"`.
- The one-cycle plan `ONE`:

  ```yaml
  cycles:
    - n: 1
      project: backend
      title: "adding two numbers"
      test: "tests/test_add.py::test_add_two_numbers"
      stub_expected: ["app/calc.py"]
  ```

- The two-cycle plan `TWO`: `ONE` plus

  ```yaml
    - n: 2
      project: backend
      title: "subtracting two numbers"
      test: "tests/test_sub.py::test_subtract_two_numbers"
      stub_expected: ["app/sub.py"]
  ```

  Each plan body is front matter followed by `# Plan`.
- Helpers in `tests/test_cycle_close_gate.py`, written in cycle 1:
  - `_start(repo, body)`: `plan = write_plan(repo, body)`, then assert that `plan register` and
    `run start --plan` are `ok`.
  - `_close_cycle_one(repo)`: drives the `add` cycle with the stray path and returns the closing
    `advance`'s envelope:
    1. write `backend/tests/test_add.py`:
       `from app.calc import add` / `def test_add_two_numbers(): assert add(2, 3) == 5`;
    2. write the stub `backend/app/calc.py`: `def add(a, b): raise NotImplementedError`;
    3. `advance` (RED);
    4. write `notes.md`;
    5. write the real `add`: `return a + b`;
    6. `advance` (GREEN), which flags `notes.md`;
    7. return `run_cli(repo, "advance")`.
- `_metrics(repo)`: `run_cli(repo, "metrics")["result"]["runs"][0]`.

### Cycle 1 (pin): the last cycle keeps the run-close gate

- **Behaviour:** decision 1's "the run-close gate stays as the final backstop". At the last
  cycle, the close still ends the run, and an unblock still completes it with the path dirty.
- **Test:** `test_the_last_cycle_keeps_the_run_close_gate`
  1. `_start(repo, ONE)`;
  2. `close = _close_cycle_one(repo)`;
  3. `resumed = run_cli(repo, "resume", "--unblock", "--note", "discarding scratch notes")`.

  Single assertion:
  `assert (close["next_action"]["verb"], resumed["next_action"]["verb"]) == ("blocked", "complete")`.
- **Why a pin:** this is today's behaviour, and it passes on arrival (probed). It guards cycle
  2. A GREEN that also held the last cycle open would make the unblock reply
  `refactor_or_advance`, and GREEN's whole-suite run would report this test.
- **Sensitivity check:** mutate `_handle_refactor` so the last cycle's blocked close returns
  before `engine.close_cycle` runs. The unblock then finds an open cycle and replies
  `refactor_or_advance`.
- **If it fails on arrival:** the branch has moved. Do not edit production code in a pin cycle.
  File `tdd blocker --kind plan_defect --detail '...'` with both verbs.

### Cycle 2: a flagged path still dirty holds an earlier cycle's close

- **Behaviour:** decisions 1 to 3.
- **Test:** `test_a_dirty_flagged_path_holds_the_cycle_close`
  1. `_start(repo, TWO)`;
  2. `close = _close_cycle_one(repo)`;
  3. `run = _metrics(repo)`.

  Single assertion:

  ```python
  assert (
      close["next_action"]["verb"],
      close["result"].get("kind"),
      close["result"].get("paths"),
      run["outcome"],
      run["cycles_closed"],
  ) == ("blocked", "undeclared_file_uncommitted", ["notes.md"], "blocked", 0)
  ```

  The expected values come from the fixture, not from production code. `cycles_closed == 0`
  pins that the cycle stays open. `outcome == "blocked"` pins that the run ended blocked, so
  the stop hook releases.
- **Production target:**
  - `Engine.cycle_undeclared_gate` in `src/tddcli/machine.py` (decision 1). `machine.py`
    already imports `gitutil` and `json`.
  - In `_handle_refactor` in `src/tddcli/advance.py`: when the cycle is not `last`, call the
    gate, and if it returns paths, do decision 3's three steps and return. The last cycle's
    path is untouched.
  - **Update `tests/test_undeclared_dedup.py::test_dedup_is_per_cycle_not_per_run`** as
    decision 8 says. It is declared in `modifies_tests`. Without the update, GREEN's
    whole-suite run fails it with `assert 1 == 2`: cycle 1's close is held, so cycle 2 never
    opens.
  - `docs/PRD.md` R9.16: after "Per P2 this does not block." (the sentence wraps across two
    lines, so search for `does not block.`), add:
    > A flagged path still dirty when its cycle closes is the exception (#234). Unless the
    > cycle is the run's last, `advance` records an `undeclared_file_uncommitted` blocker
    > naming the paths and ends the run `blocked`. The cycle stays open in `AWAITING_REFACTOR`.
    > Whoever unblocks it commits each path in a commit of its own or discards it, then
    > `tdd resume --unblock --note ...`. The next `advance` checks again. At the last cycle the
    > run-close gate decides, over every path the run flagged, and an unblock completes the
    > run.
  - `docs/PRD.md` §12: the "**Recorded, never blocked** (per P2)" list keeps "undeclared file
    touches" and adds, after the list's closing period: " A flagged path still uncommitted
    when its cycle or the run closes is the exception (R9.16)."
  - `README.md`, in "Run-close gate for undeclared file touches": after the three bullets, and
    before the ignored-paths paragraph, add:
    > Every earlier cycle gets the same check when it closes, over the paths flagged during
    > that cycle (#234). A flagged path still dirty holds the close. The `advance` reply is
    > `blocked`, with `result.kind` `undeclared_file_uncommitted` and `result.paths`. The run
    > ends `blocked` and the cycle stays open. Commit each path in a commit of its own, or
    > discard it (revert or delete it). Then run `tdd resume --unblock --note "..."` and
    > `tdd advance`. That advance checks again, so a path still dirty holds the close again. A
    > stray edit cannot carry into the next cycle's RED run or GREEN commit.
  - `README.md`, "Enforcement boundary": replace "Undeclared file touches are an exception at
    run close: see the run-close gate above." (it wraps after `run close:`) with "Undeclared file touches are an exception
    when a cycle or the run closes: see the run-close gate above."
  - `CHANGELOG.md`, under `## [Unreleased]`, a `### Fixed` entry:
    > **A flagged undeclared edit can no longer cross into the next cycle** (#234). When a
    > cycle other than the last closes with a path it flagged `undeclared_file_touched` still
    > dirty, `tdd advance` now records an `undeclared_file_uncommitted` blocker, ends the run
    > `blocked` and leaves the cycle open. Commit or discard the path, `tdd resume --unblock
    > --note ...`, then `tdd advance` again, which checks again. Before this, the edit ran in
    > the next cycle's RED and could land in its GREEN commit. The run-close gate at the last
    > cycle is unchanged.
- **EXPECTED FAILURE** (probed on `origin/main`):
  `AssertionError: assert ('write_test', None, None, None, 1) == ('blocked', 'undeclared_file_uncommitted', ['notes.md'], 'blocked', 0)`.
  Today the close opens cycle 2, and `close["result"]` is `{"commit": None, "regenerated":
  None}`.
- **Refactor (optional):** the new envelope and the run-close `BLOCKED` envelope share their
  `run` block. A helper for both is the planned refactor. No behaviour change.

### Cycle 3 (pin): committing or discarding the held path, then unblocking, lets the cycle close

- **Behaviour:** decision 4's two accepted resolutions.
- **Test:** `test_committing_or_discarding_the_held_path_lets_the_cycle_close(repo, tmp_path)`.
  It is table-driven over two copies of the fresh fixture, made with
  `shutil.copytree(repo, tmp_path / case, symlinks=True)` **before** any run starts. Each copy
  is its own repository and ledger, because the ledger is keyed by `gitutil.repo_identity`.
  For each `case` in `("commit", "discard")`, with `r` the copy:
  1. `_start(r, TWO)`; `_close_cycle_one(r)`;
  2. resolve:
     - `"commit"`: `git(r, "add", "notes.md")`, then
       `git(r, "commit", "-q", "-m", "docs: scratch notes")`;
     - `"discard"`: `(r / "notes.md").unlink()`;
  3. `run_cli(r, "resume", "--unblock", "--note", f"{case} notes.md")`;
  4. `after = run_cli(r, "advance")`;
  5. `outcomes[case] = (after["run"]["cycle"], after["next_action"]["verb"],
     after["next_action"]["detail"].startswith("Cycle 1 closed."))`.

  Single assertion:
  `assert outcomes == {"commit": (2, "write_test", True), "discard": (2, "write_test", True)}`.
- **Why a pin:** after cycle 2, the advance that follows an unblock re-enters
  `_handle_refactor`. The gate finds `notes.md` clean (committed, or gone), so the cycle
  closes. This passes on arrival (probed on the throwaway version: both cases gave cycle 2,
  `write_test`, `"Cycle 1 closed. ..."`).
- **Sensitivity check:** mutate `cycle_undeclared_gate` to return the flagged paths without
  the `dirty_paths` filter. Both cases are then held again.
- **If it fails on arrival:** cycle 2's GREEN did not follow decisions 3 and 4. For example, it
  closed the cycle before blocking, or it recorded state that outlives the unblock. Do not edit
  production code in a pin cycle. File `tdd blocker --kind plan_defect --detail '...'` with
  `outcomes`.

### Cycle 4 (pin): unblocking with the path still dirty holds the close again

- **Behaviour:** decision 4's rejected form. An unblock does not excuse the path.
- **Test:** `test_unblocking_with_the_path_still_dirty_holds_the_close_again`
  1. `_start(repo, TWO)`; `_close_cycle_one(repo)`;
  2. `run_cli(repo, "resume", "--unblock", "--note", "leaving notes.md")`;
  3. `again = run_cli(repo, "advance")`;
  4. `run = _metrics(repo)`.

  Single assertion:

  ```python
  assert (again["next_action"]["verb"], again["result"].get("paths"), run["blockers"]) == (
      "blocked",
      ["notes.md"],
      {"undeclared_file_uncommitted": 2},
  )
  ```

- **Why a pin:** cycle 2's gate has no memory of the earlier block (decision 4), so the second
  close is held the same way. This passes on arrival (probed on the throwaway version).
- **Sensitivity check:** mutate `cycle_undeclared_gate` to return `[]` once the cycle already
  has an `undeclared_file_uncommitted` blocker. The advance then closes the cycle.
- **If it fails on arrival:** the same instruction as cycle 3.

### Cycle 5: a RED taken on a dirty tree names the paths its commit left out

- **Behaviour:** decision 6. It covers what the event includes and excludes, and that a clean
  RED writes nothing.
- **Test:** `test_a_red_on_a_dirty_tree_names_the_paths_its_commit_left_out`, in
  `tests/test_red_on_dirty_tree.py`.
  1. Track a file git ignores, **before** `write_plan`, so that it is clean at `run start`:
     - write `v1\n` to `repo / ".gradle/8.0/checksums.lock"`, creating the parent directories;
     - append `.gradle/\n` to `.gitignore`;
     - `git(repo, "add", ".gitignore")`, then
       `git(repo, "add", "-f", ".gradle/8.0/checksums.lock")`;
     - `git(repo, "commit", "-q", "-m", "a tracked file the ignore rules match")`.

     (`.claude/plan-issue/git-ignored-tracked-paths.md`: only a tracked ignored file reaches
     `git status`.)
  2. Register and start this file's plan. It is `TWO` (copy the YAML into this file) plus a
     top-level `ancillary_files: ["docs/companion.md"]`.
  3. Drive cycle 1 **clean**: write `test_add.py` and the stub `calc.py` exactly as
     `_close_cycle_one` does, then `advance`. Write the real `add`, then `advance`, then
     `advance`. No stray path, so the close opens cycle 2.
  4. Before cycle 2's RED, write all of these:
     - `backend/tests/test_sub.py`:
       `from app.sub import sub` / `def test_subtract_two_numbers(): assert sub(5, 3) == 2`;
     - the stub `backend/app/sub.py`: `def sub(a, b): raise NotImplementedError`;
     - `backend/app/helper.py`: `X = 1\n` (implementation written during RED);
     - `notes.md`: `scratch notes\n` (outside);
     - `docs/companion.md`: `c\n` (ancillary), creating `docs/`;
     - `.gradle/8.0/checksums.lock`: `v2\n` (a tracked path git ignores).
  5. `run_cli(repo, "advance")` (cycle 2's RED).
  6. `run_id = run_cli(repo, "metrics")["result"]["runs"][0]["run"]`, then
     `ledger = Ledger(gitutil.repo_identity(repo))`, as `tests/test_flaky_reruns.py`'s
     `_flaky_events` does.

  Single assertion:

  ```python
  assert [json.loads(d) for d in ledger.event_details(run_id, "red_on_dirty_tree")] == [
      ["backend/app/helper.py", "docs/companion.md", "notes.md"]
  ]
  ```

  One list, so cycle 1's clean RED wrote nothing. Three paths, so implementation, outside and
  ancillary paths are all named. The ignored path and the staged test and stub are not. The
  expected list is written from the fixture, not computed by production code.
- **Production target:**
  - `advance._stage_and_commit` (decision 6).
  - `docs/PRD.md`'s IntegrityEvent typed list: add `red_on_dirty_tree` to the list, and after
    the `flaky_pre_existing` sentence add:
    > `red_on_dirty_tree` names the changed paths a RED commit left out, so the RED verdict
    > was taken on a tree that differs from the RED commit (#234). It leaves out paths git or
    > `tdd.toml` ignores, and dirt that was there before the run.
  - `CHANGELOG.md`, under `## [Unreleased]`, an `### Added` entry:
    > **`red_on_dirty_tree` integrity event** (#234). When a RED commit leaves changed paths
    > out (implementation written during RED, paths outside the cycle's projects, ancillary or
    > generated paths), `tdd advance` records them on the cycle, so the friction log shows the
    > RED verdict ran on a tree that differs from its commit. Paths git ignores are not named.
    > It blocks nothing.
- **EXPECTED FAILURE** (probed on `origin/main`):
  `AssertionError: assert [] == [['backend/app/helper.py', 'docs/companion.md', 'notes.md']]`.
  Cycle 2's RED still succeeds (`write_implementation`), with `implementation_during_red` and
  `undeclared_file_touched` events, so nothing raises before the assertion.

## Execution

This plan is executed through `tdd-cli`. **You run every command below yourself** — do not ask the
user to start the run. `tdd run start` records which model is executing, resolved from your own
session; a run started by anyone else attributes this work to the wrong agent.

    git checkout -b issue-234-cycle-close-undeclared-gate   # first, before anything else
    tdd doctor                                  # healthy, or failing only for projects this plan cannot reach
    tdd run start --plan tasks/issue-234-cycle-close-undeclared-gate.md   # captures baselines, opens cycle 1

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
  tool stages and commits, deriving the file set from the phase. (The `git` calls in this plan's
  tests run inside the tests' own temporary repositories, not in this checkout.)
- The baseline is captured at `run start` and subtracted from later verdicts. The suite is green
  at the plan's base (verified in a fresh worktree of `origin/main`: `869 passed`). Expect
  `baselines: {tddcli: 0}`.
- The referee is the released `tdd` on `PATH` (the note at the top of `tdd.toml`), never
  `uv run tdd`. It does not have this plan's gate, and every file this plan touches is inside
  the `tddcli` root `.`, so your own run is neither held nor flagged.
- Verbs this plan will hit:
  - `write_test`, `write_implementation`, `refactor_or_advance`.
  - `run_sensitivity_check` → `tdd sensitivity begin|check|end`. Every pin (cycles 1, 3 and 4)
    asks for one. Each cycle names the mutation to make. A standard RED that passes on arrival
    asks for one too: mutate what that cycle's GREEN added.
  - `annotate_cycle` → `tdd annotate --key --value`. This plan declares no keys of its own;
    `plan_defect` and `friction_note` are reserved.
  - `resolve_blocker` → `tdd blocker --kind <plan_defect|tooling|regression|pre_existing_failure> --detail '...'`.
    A pin that fails on arrival is `plan_defect`, as each pin says.
  - `confirm_cycle_applicable` on a non-existent cycle → `tdd cycle skip --reason`.
  - No cycle declares a stub: every test imports only names that exist today.

**Minimal GREEN, per cycle. Add this and nothing earlier:**

- Cycle 1 is a pin. It adds only its test and the helpers.
- Cycle 2 adds:
  - `Engine.cycle_undeclared_gate`, and the hold in `_handle_refactor`;
  - the `test_dedup_is_per_cycle_not_per_run` update;
  - the PRD R9.16 and §12 text, the two README edits, and the `### Fixed` CHANGELOG entry.

  No `red_on_dirty_tree`.
- Cycles 3 and 4 are pins. They add only their test.
- Cycle 5 adds:
  - the `red_on_dirty_tree` emission in `_stage_and_commit`;
  - the PRD IntegrityEvent entry;
  - the `### Added` CHANGELOG entry.

## Done-criteria

**Before finishing:** run `tdd log render --out tasks/friction-logs/issue-234-cycle-close-undeclared-gate-friction.md` and `tdd metrics`. Report the plan-fidelity section — declared vs delivered vs skipped — and every integrity event. Do not narrate what the ledger already records.

Then commit the friction log and raise the PR:

    git add tasks/friction-logs/issue-234-cycle-close-undeclared-gate-friction.md
    git commit -m "docs: friction log for issue-234-cycle-close-undeclared-gate"

Then invoke the **`raise-pr` skill** (`/raise-pr`), which runs the quality gates, pushes the
branch and opens the PR against `main`. Do not push or call the GitHub API by hand. If a gate
fails, fix it and re-run the skill — a failed gate is work, not a reason to hand back.

The PR body says `Closes #234`. Cycles 2 and 5 own the docs:

- `git diff --stat origin/main -- docs/PRD.md` must be non-empty, or the PR body says why.
- `git diff --stat origin/main -- README.md` must be non-empty, or the PR body says why.
- `git diff --stat origin/main -- CHANGELOG.md` must be non-empty, or the PR body says why.

The visible change is `advance`'s reply and ledger content, so no demo recording is required. In
the PR body:
- quote cycle 2's held-close envelope (`next_action` and `result`);
- say that a mid-run hold now needs a person to unblock. Harnesses that run unattended
  (geuben/dispatch's `implement-issue`) will see `blocked` at a cycle close where they used to
  see the next cycle open.
