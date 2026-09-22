---
closes: 146
cycles:
  - n: 1
    project: tddcli
    title: "a sweep that skips the cycle's own suites still runs that project's lint/typecheck gates"
    test: "tests/test_close_sweep_gates.py::test_skip_own_still_runs_the_cycle_projects_gates"
    files: ["src/tddcli/machine.py"]
    commit_red: "test: a close sweep that skips its own suites still runs their gates"
    commit_green: "fix: skip_own drops the cycle's own suites, not its lint/typecheck gates"
    commit_refactor: "refactor: tidy the close-sweep project selection"
  - n: 2
    project: tddcli
    pin_cycle: true
    title: "deleting a tracked file changes the tree hash"
    test: "tests/test_tree_hash.py::test_deleting_a_tracked_file_changes_the_hash"
    files: []
    commit_pin: "test: pin that deleting a tracked file changes tree_hash"
  - n: 3
    project: tddcli
    pin_cycle: true
    title: "editing an untracked, non-ignored file changes the tree hash"
    test: "tests/test_tree_hash.py::test_editing_an_untracked_file_changes_the_hash"
    files: []
    commit_pin: "test: pin that untracked file content is part of tree_hash"
  - n: 4
    project: tddcli
    pin_cycle: true
    title: "an ignored file does not change the tree hash"
    test: "tests/test_tree_hash.py::test_an_ignored_file_does_not_change_the_hash"
    files: []
    commit_pin: "test: pin that ignored files stay out of tree_hash"
  - n: 5
    project: tddcli
    pin_cycle: true
    title: "a change outside the hashed roots does not change the tree hash"
    test: "tests/test_tree_hash.py::test_a_change_outside_the_roots_does_not_change_the_hash"
    files: []
    commit_pin: "test: pin that tree_hash is scoped to its roots"
  - n: 6
    project: tddcli
    pin_cycle: true
    title: "hashing leaves the real index untouched"
    test: "tests/test_tree_hash.py::test_hashing_leaves_the_index_untouched"
    files: []
    commit_pin: "test: pin that tree_hash stages nothing"
  - n: 7
    project: tddcli
    pin_cycle: true
    title: "a root that exists neither on disk nor in the index hashes without error"
    test: "tests/test_tree_hash.py::test_a_missing_root_hashes_without_error"
    files: []
    commit_pin: "test: pin that tree_hash accepts a root that does not exist yet"
  - n: 8
    project: tddcli
    title: "the same content hashes the same unstaged, staged and committed"
    test: "tests/test_tree_hash.py::test_the_same_content_hashes_the_same_unstaged_staged_and_committed"
    files: ["src/tddcli/gitutil.py", "CHANGELOG.md"]
    modifies_tests:
      - "tests/test_heartbeat.py::test_close_sweep_emits_a_project_completed_line"
      - "tests/test_late_baseline.py::test_accept_failures_accepts_a_test_that_fails_at_the_start_sha"
    commit_red: "test: tree_hash is independent of index and commit state"
    commit_green: "fix: tree_hash hashes working-tree content, not git state"
    commit_refactor: "refactor: tidy tree_hash"
  - n: 9
    project: tddcli
    pin_cycle: true
    title: "a cycle with no refactor edit skips its own close-sweep suite"
    test: "tests/test_close_sweep_gates.py::test_a_cycle_with_no_refactor_edit_skips_its_own_close_sweep_suite"
    files: []
    commit_pin: "test: pin that a cycle with no refactor edit skips its close-sweep suite"
---

# Issue 146 — `tree_hash` hashes content, not git state

## Context

Issue #146 (part of #145): the close sweep's "same tree as the passing GREEN run" skip never
fires. `gitutil.tree_hash` hashes `git ls-files -s` (index entries) plus `git diff` (unstaged
diff) per root. The GREEN suite run happens *before* the GREEN commit (dirty tree, old index);
the close sweep happens *after* it (clean tree, new index). Same content, different hash. In
run 1 of this repo's ledger all 29 `CLOSE_SWEEP` invocations had a different `tree_hash` from
the passing `AWAITING_IMPL` invocation before them, about 14 of 49 suite minutes.

**Done when** (from the issue): a cycle with no refactor edit skips its close sweep (cycle 9),
and a test pins that the same content before and after the GREEN commit hashes the same
(cycle 8).

Consumers of `tree_hash` (all in `src/tddcli/`), each of which now keys on content:

| Consumer | Where | Effect of the fix |
|---|---|---|
| §6.1 close-sweep skip (`skip_own`) | `advance.py`, the `prior[-1]["tree_hash"] == engine.tree_hash(...)` comparison in the AWAITING_REFACTOR handler | starts firing — the point of the issue |
| `no_change_since_last_run` | `advance.py`, `advance()` | staging alone is no longer a "change" (correct) |
| gate-result reuse | `machine.py`, `Engine.sweep` gate loop | unchanged in practice |
| baseline cache key | `cli.py`, `--reuse-baselines` path in `run start` | old cache rows miss once and are re-probed; no schema change |
| artifact staleness (regenerate) | `machine.py`, `Engine._artifact_stale` | still detects content changes; a root that does not exist yet must not raise (cycle 7) |
| invocation `tree_hash` column | `machine.py`, `Engine.run_projects` and `Engine.sweep` | values change; nothing reads them as literals |

### A latent bug the fix would expose (found in planning)

`Engine.sweep(skip_own=True)` filters the cycle's own projects out of `names` **before** the
lint/typecheck gate loop, so when the skip fires the cycle's own gates never run. Lint is run
nowhere else. The skip has never fired, so this was never observed. Fixing `tree_hash` alone
would silently turn lint off for every cycle with no refactor edit. Probed: a sweep called with
`skip_own=True` and a failing lint returns `gates == []` and `ok == True`. `docs/PRD.md` (the
AWAITING_REFACTOR row) says only the *suites* are skipped. Cycle 1 fixes this before cycle 8
makes the path live.

## Design decisions (locked)

1. **Gates before skip (cycle 1).** In `Engine.sweep`, `skip_own` removes the cycle's own
   projects from the *suite* loop only. The gate loop still runs over every sweep project,
   including the cycle's own. Decided by: `docs/PRD.md` AWAITING_REFACTOR row ("lint/typecheck
   clean and the close sweep green … the cycle's own **suites** are skipped") and the probe
   above. Update the `sweep` docstring to say gates still run.

2. **Content hash via a throwaway index (cycle 8).** `tree_hash` builds a temporary index from
   the working tree and hashes its entries:
   - copy the real index (`git rev-parse --path-format=absolute --git-path index`; this works in
     linked worktrees) into a `tempfile.TemporaryDirectory()`. When the real index does not
     exist, start from no file. The copy seeds git's stat cache, so unchanged files are not
     re-hashed;
   - run `git add -A` (no pathspec) with `GIT_INDEX_FILE=<absolute temp path>`;
   - for each root in `sorted(roots)`: `h.update(root.encode())` then
     `h.update(git ls-files -s -- <root>` output, read through the same temp index`)`.

   This covers modified, deleted, mode-changed and untracked-not-ignored files in one place, and
   ignored files stay out, as they do today. Decided by: the issue's proposed fix. The
   alternative, `git hash-object` per path, needs separate handling for deletions, modes and
   symlinks.

   **Mechanism footguns. Name them in the code:**
   - `GIT_INDEX_FILE` **must be absolute**. `gitutil.git` runs `git -C <worktree>`, so a
     relative path resolves somewhere unintended. Add an optional `env: dict[str, str] | None`
     parameter to `gitutil.git`, merged over `os.environ` (`{**os.environ, **env}`). Never
     replace the environment.
   - **No pathspec on `git add -A`.** `git add -A -- <root>` fails with "pathspec did not match
     any files" when the root exists neither on disk nor in the index. `_artifact_stale` hashes
     an artifact path before `regenerate` may have created it. Cycle 7 pins this.
   - **Never touch the real index.** `staging.py` derives commits from it. Cycle 6 pins this.
   - Keep the function signature `tree_hash(worktree: Path, roots: list[str]) -> str`.
     Rewrite the docstring to say it hashes working-tree content, independent of index or
     commit state.

3. **No ledger schema change.** Hash values change meaning but not type. Old `baseline_cache`
   rows simply stop matching and are re-probed on the next `--reuse-baselines` run. Record
   this in `CHANGELOG.md`. Decided by: `ledger.py` stores `tree_hash TEXT` everywhere and
   nothing compares it with a literal.

4. **Test blast radius (cycle 8).** Once the skip fires, two existing tests that close a cycle
   with no refactor edit and rely on the cycle's own suite running at close will fail. Both
   are in cycle 8's `modifies_tests`. The only authorised change to each is to make a **content
   edit** before the close-sweep `advance`, so the sweep still runs. Append a comment line to
   `backend/app/calc.py`, e.g. `(repo / "backend" / "app" / "calc.py").write_text("def add(a,
   b):\n    return a + b\n# refactor\n")`. Do not change any assertion.
   - `tests/test_heartbeat.py::test_close_sweep_emits_a_project_completed_line`: edit before
     the "the close sweep itself" advance.
   - `tests/test_late_baseline.py::test_accept_failures_accepts_a_test_that_fails_at_the_start_sha`:
     edit after the `UPDATE baseline …` commit, before the first `run_cli(repo, "advance")`.

   Found by simulating a firing skip in a scratch worktree (discarded). The simulation also
   failed three `tests/test_baseline_integrity.py` tests
   (`test_unblocking_can_accept_the_failures_into_the_baseline`,
   `test_unblocking_without_accept_failures_leaves_the_baseline_alone`,
   `test_stale_reused_baseline_recovers_via_accept_failures`), but it over-approximated. Those
   tests edit `test_smoke.py` after GREEN, so a real content hash differs from GREEN's and
   they keep passing. **Re-evaluation trigger:** if any test outside `modifies_tests` fails at
   cycle 8's GREEN, stop and raise `tdd blocker --kind plan_defect`. Do not edit it.

5. **Where the tests live.** Unit tests for `tree_hash` go in a new
   `tests/test_tree_hash.py`, created by cycle 2. The two sweep tests go in the existing
   `tests/test_close_sweep_gates.py`, which already has `_drive_to_close`, `_toml`,
   `SIMPLE_PLAN`, and `git`/`run_cli`/`write_plan` from `conftest`.

## Deliberate scope cuts (do not build)

None. The issue's other framing (#145: RED confirmation re-runs the whole suite) is a separate
issue, not asked for here.

## Cycles

Shared fixture for `tests/test_tree_hash.py`. Cycle 2 writes it and later cycles reuse it:

```python
from conftest import git
from tddcli import gitutil


def _repo(tmp_path):
    """A committed repo with two roots, `p` and `q`, and `*.log` ignored."""
    r = tmp_path / "r"
    r.mkdir()
    git(r, "init", "-q")
    git(r, "config", "user.email", "t@example.com")
    git(r, "config", "user.name", "T")
    (r / "p").mkdir()
    (r / "q").mkdir()
    (r / "p" / "a.py").write_text("x = 1\n")
    (r / "q" / "b.py").write_text("y = 1\n")
    (r / ".gitignore").write_text("*.log\n")
    git(r, "add", "-A")
    git(r, "commit", "-q", "-m", "init")
    return r
```

`conftest.git` uses `check=True`, and `r` is under `tmp_path`, so nothing touches this
repository.

### Cycle 1 — gates still run when the cycle's own suites are skipped

- **Behaviour:** `Engine.sweep(cycle, set(), skip_own=True)` still runs the cycle project's
  lint gate.
- **Test** `tests/test_close_sweep_gates.py::test_skip_own_still_runs_the_cycle_projects_gates`:
  write `_toml(["sh -c 'exit 1'"])` to `tdd.toml` and commit it, register `SIMPLE_PLAN`, and
  `run start`. Build an `Engine` the same way `tests/test_concurrent_advance.py` does:
  `Ledger(gitutil.repo_identity(repo))`, the run row, the first cycle row,
  `config.load(repo)`, and `Engine(ledger, cfg, repo, run_row)`. Call
  `engine.sweep(cycle_row, set(), skip_own=True)`. Single assertion:
  `[(p, k) for p, k, _ in outcome.gates] == [("backend", "lint")]`.
- **Production target:** `src/tddcli/machine.py`, `Engine.sweep`. Apply the `skip_own` filter
  to the suite loop's project list, not before the gate loop. Update the docstring.
- **EXPECTED FAILURE** (probed): `AssertionError: assert [] == [('backend', 'lint')]`.

### Cycles 2–7 — pin what `tree_hash` already gets right (all probed passing today)

These characterise the current `tree_hash` before cycle 8 rewrites it. Each must pass on
arrival. If one fails on arrival, stop and raise `tdd blocker --kind plan_defect`. Each test
has one assertion.

- **Cycle 2** `test_deleting_a_tracked_file_changes_the_hash`: `h0 = tree_hash(r, ["p"])`,
  unlink `p/a.py`, `assert tree_hash(r, ["p"]) != h0`. Creates the file with the `_repo`
  helper above.
- **Cycle 3** `test_editing_an_untracked_file_changes_the_hash`: write untracked `p/new.py`
  as `"1"`, hash, rewrite it as `"2"`, and assert the hash differs.
- **Cycle 4** `test_an_ignored_file_does_not_change_the_hash`: `h0`, write `p/x.log`, and
  assert the hash equals `h0`.
- **Cycle 5** `test_a_change_outside_the_roots_does_not_change_the_hash`: `h0` of `["p"]`,
  rewrite `q/b.py`, and assert the hash of `["p"]` equals `h0`.
- **Cycle 6** `test_hashing_leaves_the_index_untouched`: rewrite `p/a.py` and write untracked
  `p/new.py`, call `tree_hash(r, ["p"])`, and assert
  `git(r, "diff", "--cached", "--name-only") == ""`.
- **Cycle 7** `test_a_missing_root_hashes_without_error`:
  `assert isinstance(gitutil.tree_hash(r, ["nope"]), str)`. Here `nope` exists neither on
  disk nor in the index. It pins decision 2's "no pathspec on `git add -A`" footgun.

### Cycle 8 — the same content hashes the same, whatever the git state

- **Behaviour:** the hash depends only on working-tree content under the roots.
- **Test**
  `tests/test_tree_hash.py::test_the_same_content_hashes_the_same_unstaged_staged_and_committed`:
  `r = _repo(tmp_path)`. Rewrite `p/a.py` as `"x = 2\n"` and take `unstaged`. Run
  `git(r, "add", "-A")` and take `staged`. Run `git(r, "commit", "-q", "-m", "g")` and take
  `committed`. Single assertion: `len({unstaged, staged, committed}) == 1`.
- **Production target:** `src/tddcli/gitutil.py`: `tree_hash` (decision 2) plus the optional
  `env` parameter on `git`. `CHANGELOG.md`: add a `### Fixed` entry under `## [Unreleased]`.
  It says the close-sweep skip now fires (#146), and that a skipped sweep still runs the cycle
  project's lint/typecheck gates. It notes that `--reuse-baselines` cache entries from earlier
  versions miss once.
- **Tests this cycle modifies:** see decision 4. The only change allowed is a content edit
  before the close-sweep advance.
- **EXPECTED FAILURE** (probed: `staged == committed` but `unstaged` differs):
  `AssertionError: assert 2 == 1`.
- **Sensitivity:** cycles 2–7 must stay green through this GREEN. They are the guard on the
  rewrite.

### Cycle 9 — pin: a cycle with no refactor edit skips its own close-sweep suite

- **Behaviour:** this is the issue's done-when, observed where `tree_hash` is consumed
  (`advance.py`, the §6.1 skip) and not only where it is computed.
- **Test**
  `tests/test_close_sweep_gates.py::test_a_cycle_with_no_refactor_edit_skips_its_own_close_sweep_suite`:
  `out = _drive_to_close(repo, lint_cmds=["true"])`. Pass `lint_cmds` because `_drive_to_close`
  commits `tdd.toml`, and the fixture's default `lint = []` leaves nothing to commit, so
  `git commit` exits 1. Count
  `SELECT COUNT(*) FROM invocation WHERE run_id = ? AND phase_at = 'CLOSE_SWEEP' AND project = 'backend'`.
  Single assertion: `(out["next_action"]["verb"], count) == ("complete", 0)`.
- **Kind: pin.** It passes on arrival because of cycles 1 and 8. Probed before the fix:
  `verb == "complete"` with **one** backend `CLOSE_SWEEP` invocation, whose `tree_hash`
  differed from the `AWAITING_IMPL` one. After-state: `git status --porcelain` is empty after
  the GREEN commit (probed), so the content at close equals the content GREEN ran against. If
  it fails on arrival, stop and raise `tdd blocker --kind plan_defect`.
- Lint still running on a skipped sweep is already covered end to end by the existing
  `test_failing_lint_replies_fix_regression_with_the_lint_gate` and its siblings in this file.
  Once cycle 8 lands they reach the skip path. The scratch simulation showed all six fail
  without cycle 1 and pass with it.

### Behaviour census

| Promise | Test |
|---|---|
| gates run when own suites are skipped | cycle 1; end to end by the existing `test_close_sweep_gates.py` gate tests |
| deletion / untracked / ignored / root-scoped / index untouched / missing root | cycles 2–7 |
| same content hashes the same across staging and commit | cycle 8 |
| no-refactor cycle skips its own close-sweep suite | cycle 9 |
| `no_change_since_last_run` still refuses an unchanged tree | existing `tests/test_end_to_end.py::test_no_change_since_last_run_is_refused_but_retry_is_allowed` |
| a refactor cycle never skips | existing `tests/test_refactor_cycles.py` (the `kind != "refactor"` guard is untouched) |

There are no fakes or ports, no mirrors (`tree_hash` has one implementation), no
`docs/INVARIANTS.md`, no generated artifacts, and no numeric target. The issue's "~14 minutes"
is an observation, not a target.

## Execution

This plan is executed through `tdd-cli`. **You run every command below yourself** — do not ask the
user to start the run. `tdd run start` records which model is executing, resolved from your own
session; a run started by anyone else attributes this work to the wrong agent.

    git checkout -b issue-146-content-tree-hash      # first, before anything else
    tdd doctor                                       # must report healthy: true
    tdd run start --plan tasks/issue-146-content-tree-hash.md

If the branch already exists, do not force-checkout and do not pick another name: check it out
only if it carries this plan's commit and no unrelated work, otherwise stop and ask.

**Referee.** Use the released `tdd` 0.12.2 on `PATH` (`tdd --version`), never an editable
install of this working tree. `SCHEMA_VERSION` does not change in this plan.

Then repeat until done: read `next_action.verb`, do exactly what it says, run `tdd advance`.
Stop when `next_action.terminal` is `true`.

When `next_action.terminal` is `true`, finish the run: render the friction log, commit it, and
raise the PR — see Done-criteria below.

- `tdd advance` is the only command that changes phase. Do not `git add` or `git commit` — the
  tool stages and commits, deriving the file set from the phase.
- The baseline is captured at `run start` and subtracted from later verdicts. The suite is
  green at the plan commit in a fresh worktree (568 passed, 2026-09-22); expect
  `baselines: {tddcli: 0}`.
- Verbs this plan will hit: `write_test`, `write_implementation`, `refactor_or_advance`,
  `run_sensitivity_check` → `tdd sensitivity begin|check|end`,
  `resolve_blocker` → `tdd blocker --kind <regression|target_unfixable|bad_red|plan_defect|tooling|context_exhausted|pre_existing_failure|no_baseline_for_project> --detail '...'`,
  `confirm_cycle_applicable` on a non-existent cycle → `tdd cycle skip --reason`. This plan
  declares no annotation keys beyond the reserved `plan_defect` and `friction_note`.

**Minimal GREEN, per cycle — add this and nothing earlier:**

- cycle 1 moves the `skip_own` filter below the gate loop in `Engine.sweep`. It does not touch
  `gitutil`.
- cycles 2–7 are pins: write the test, and change no production code.
- cycle 8 rewrites `tree_hash` and adds `env` to `git`, then makes the content edit in the two
  `modifies_tests`. It does not touch `advance.py` or `machine.py`.
- cycle 9 is a pin: write the test, and change no production code.

## Done-criteria

**Before finishing:** run `tdd log render --out tasks/friction-logs/issue-146-content-tree-hash-friction.md` and `tdd metrics`. Report the plan-fidelity section — declared vs delivered vs skipped — and every integrity event. Do not narrate what the ledger already records.

Then commit the friction log and raise the PR:

    git add tasks/friction-logs/issue-146-content-tree-hash-friction.md
    git commit -m "docs: friction log for issue-146-content-tree-hash"

Then invoke the **`raise-pr` skill** (`/raise-pr`), which runs the quality gates, pushes the
branch and opens the PR against `main`. Do not push or call the GitHub API by hand. If a gate
fails, fix it and re-run the skill — a failed gate is work, not a reason to hand back.

Docs are deliverables: `git diff --stat origin/main -- CHANGELOG.md` must be non-empty (cycle
8), or the PR body says which cycle dropped it and why.

The run itself is refereed by the released 0.12.2, which still has the bug, so this run's own
close sweeps will **not** skip. Do not cite this run's ledger as evidence of the fix. Cycle 9
is the evidence. Nothing a user sees changes outside the JSON envelope, so no demo recording is
required.
