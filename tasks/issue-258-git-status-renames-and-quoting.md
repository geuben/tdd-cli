---
closes: 258
cycles:
  - n: 1
    project: tddcli
    title: "a renamed ancillary file is classified as its two paths, so no undeclared_file_touched fires"
    test: "tests/test_status_paths.py::test_a_renamed_ancillary_file_fires_no_undeclared_event"
    files: ["src/tddcli/gitutil.py", "docs/PRD.md", "CHANGELOG.md"]
    commit_red: "test: a renamed ancillary file must not be flagged as one undeclared path"
    commit_green: "fix: read git status without rename detection, so a rename is its two paths"
    commit_refactor: "refactor: tidy status_porcelain"
  - n: 2
    project: tddcli
    pin_cycle: true
    title: "every rename and copy form git status prints reaches dirty_paths as two paths"
    test: "tests/test_status_paths.py::test_every_rename_and_copy_form_is_two_dirty_paths"
    files: ["src/tddcli/gitutil.py"]
    commit_pin: "test: pin that every rename and copy form is two dirty paths"
  - n: 3
    project: tddcli
    title: "a git mv inside the cycle's root commits at GREEN, and staged names both paths"
    test: "tests/test_status_paths.py::test_a_git_mv_inside_the_cycle_root_stages_both_paths"
    files: ["src/tddcli/gitutil.py", "CHANGELOG.md"]
    commit_red: "test: a git mv at GREEN must commit and report both paths"
    commit_green: "fix: staged_paths names both paths of a rename"
    commit_refactor: "refactor: tidy staged_paths"
  - n: 4
    project: tddcli
    title: "paths with a space or a non-ASCII character are staged verbatim, never C-quoted"
    test: "tests/test_status_paths.py::test_paths_with_a_space_or_non_ascii_are_staged_verbatim"
    files: ["src/tddcli/gitutil.py", "docs/PRD.md", "CHANGELOG.md"]
    commit_red: "test: unusual path names must be staged verbatim"
    commit_green: "fix: read git status and the staged list with -z, so paths are never C-quoted"
    commit_refactor: "refactor: tidy the -z parsing"
---

# Issue 258: a staged rename reaches staging and classification as one `old -> new` path

## Context

[#258](https://github.com/geuben/tdd-cli/issues/258). `gitutil.status_porcelain` runs
`git status --porcelain=v1 -uall` and returns `line[3:].strip()` as each entry's path. For a
staged rename git prints `R  old -> new`, so the "path" is the string `old -> new`. Every
consumer of `dirty_paths` / `changed_paths` passes it on:

- **Staging.** `advance._stage_and_commit` classifies it with `staging.classify`. Inside a
  project root, `old -> new` is owned by that project (it starts with the root) and is not a
  test, so it is implementation. GREEN's `staging.commit` hands it to `git add` as one pathspec
  and the `advance` fails (geuben/coparenting#1528).
- **Classification.** Outside every project root (an ancillary doc, say), `old -> new` is
  neither declared nor owned, so `classify` puts it in `outside` and
  `undeclared_file_touched` fires on one bogus path. The rename stays uncommitted and lands in
  a later commit (geuben/coparenting#444).

The issue also notes that porcelain v1 C-quotes some paths: one with a space or a non-ASCII
character comes back wrapped in double quotes. The workaround today is `git reset -q`, then
`tdd advance --retry`, and coparenting's planner notes tell executors to move files with plain
`mv` (geuben/coparenting#1912).

**Done when** (from the issue): a `git mv` of a tracked file inside a cycle's root, then
`advance`, commits the rename (cycle 3) and fires no `undeclared_file_touched` event (cycle 1,
over the case where today's code does fire it). Renames and copies reach classification and
staging as their two paths (cycles 1 to 3); unusual path names are no longer quoted (cycle 4).

There is no investigation report on the issue and no `investigate/issue-258` branch: the issue
was classified straight to `needs-plan` (the `dispatch:classify` comment), and no person has
commented. Every claim below comes from the code and from the planning probes.

### What the planning probes found (E-2, git 2.43, scratch worktrees of `origin/main`)

| Probe | Result |
|---|---|
| The suite in a fresh worktree of `origin/main` | `902 passed`. No setup script needed. |
| `git mv backend/app/old.py backend/app/new.py` during GREEN, in the `repo` fixture | `status_porcelain` returns `[('R ', 'backend/app/old.py -> backend/app/new.py')]`. GREEN's `advance` replies `ok: false`, `error: "git add -- backend/app/calc.py backend/app/old.py -> backend/app/new.py failed: fatal: pathspec 'backend/app/old.py -> backend/app/new.py' did not match any files"`, `result: {}`. **Staging, reproduced.** |
| `git mv docs/old.md docs/new.md` during GREEN, both paths declared in `ancillary_files` | GREEN succeeds, `staged: ["backend/app/calc.py"]`, and metrics count `undeclared_file_touched: 1`. **Classification, reproduced.** |
| New untracked `backend/app/a b.py` and `backend/app/é.py` written during GREEN | GREEN succeeds but `staged: ["backend/app/calc.py"]`: status returned `"backend/app/a b.py"` and `"backend/app/\303\251.py"` with their quotes, which no project root owns, so both were classified `outside`, flagged and left out of the commit. |
| The four rename/copy forms, today | staged rename `R  old -> new`; renamed then edited `RM old -> new`; intent-to-add rename (`mv`, then `git add -N new`) ` R old -> new`; copy with `status.renames=copies` `C  old -> copy` plus `M  old`. `dirty_paths` returns the arrow string for each. |
| The same four with `git status --porcelain=v1 -z -uall --no-renames` | `A  new\0D  old\0`, `AM new\0D  old\0`, ` A new\0 D old\0`, `A  copy\0M  old\0`. Every rename is the old path's deletion and the new path's addition; no entry carries a second path. |
| `git diff --cached --name-only` after a staged rename | names only `new.py`. With `--no-renames` it names `new.py` and `old.py`. Without `-z` it prints `"\303\251.py"` quoted (but `a b.py` bare); with `-z` both are verbatim. |
| A throwaway version of each step, applied in order in a scratch worktree | After decision 1's `--no-renames` alone: cycle 1's test passes, cycle 2's table passes, cycle 3's test fails `assert ['backend/app/calc.py', 'backend/app/new.py'] == [..., 'backend/app/old.py']`, cycle 4's fails `assert ['backend/app/calc.py'] == [...]`. After decision 2's `--no-renames` on `staged_paths`: cycle 3 passes, cycle 4 still fails. After decision 3's `-z` on `status_porcelain` alone, cycle 4 fails at index 2 on `'"backend/app/\\303\\251.py"'`; with `-z` on `staged_paths` as well it passes. |
| The full suite, `ruff` and `mypy` against the whole throwaway change | `902 passed`; ruff and mypy clean. No existing test breaks. |

The throwaway versions and probe files were deleted with their scratch worktrees.

## Design decisions (locked)

1. **`status_porcelain` turns rename detection off: `git status --porcelain=v1 -z -uall
   --no-renames`.** With rename detection off, git prints a rename (staged, edited after, or a
   worktree-column rename of an intent-to-add file) and a copy (when the user's
   `status.renames` is `copies`) as plain `A`/`D`/`M` entries, one path each. So a rename
   reaches every consumer as "the deletion of `old` and the addition of `new`", which is what the
   issue asks for, and no entry ever carries a second path to parse.
   - *Decided by evidence:* the probe table above (all four forms), and the issue ("Return both
     paths, the deletion of `old` and the addition of `new`"). The issue offers `-z` with
     two-field parsing as "one way". `--no-renames` gives the same result with nothing to parse,
     and ignores a user's `status.renames` setting. `-z` is still needed for quoting
     (decision 3).
   - *Decided by convention:* `gitutil.paths_committed_since` already passes `--no-renames` for
     the same reason (#232, `.claude/plan-issue/gitutil-log-renames.md`).
   - `git status --no-renames` needs git 2.18 or later (2018). Nothing in this repo states a
     minimum git; CI runs `ubuntu-latest` and `macos-latest`.
   - **Footgun:** keep `--porcelain=v1`, never plain `--porcelain` with a `status.*` config
     that could change it, and never add `-b`/`--branch` (it adds a `##` header entry).
2. **`staged_paths` names both paths too: `git diff --cached --name-only --no-renames -z`.**
   `staging.commit` reads the staged list back from the index the commit is made from, and
   returns it as `advance`'s `result.staged` and the ledger's commit `files`. With rename
   detection on, a rename shows only its new path, so the deletion would be invisible in both.
   *Decided by evidence* (the probe) *and convention* (decision 1, #232).
3. **Both read NUL-separated output, verbatim.** `status_porcelain` splits on `"\0"`, drops
   empty fields, and takes `entry[:2]` as the code and `entry[3:]` as the path, with **no
   `.strip()`**. A path may begin or end with a space, and `-z` output is never quoted. The
   same goes for `staged_paths`: split on `"\0"`, drop empty fields. *Decided by evidence:* the
   issue ("`-z` also fixes paths that porcelain v1 currently C-quotes") and the probe. **Footgun:**
   `out.splitlines()` on `-z` output is wrong (it yields one line), and so is stripping each
   field.
4. **`status_porcelain`'s return shape is unchanged: `list[tuple[str, str]]`, `(code, path)`.**
   Its only callers (`is_dirty`, `dirty_paths`, and `changed_paths` through `dirty_paths`) read
   only the path. A rename's old path now carries `D ` or ` D`, and its new path `A `, `AM` or
   ` A`, which is git's own code for each. *Decided by evidence* (the call sites, below) and by
   the rule that a refactor nobody needs is not part of a fix.
5. **Every consumer of `dirty_paths`/`changed_paths` gets the fix with no change of its own.**
   Discovery command, run at plan time:
   `grep -rn "dirty_paths\|changed_paths\|is_dirty\|status_porcelain\|staged_paths" src/`. Callers
   outside `gitutil.py`:
   - `src/tddcli/snapshot.py`: `authored_dirty` (sensitivity snapshots);
   - `src/tddcli/machine.py`: `Engine.authored_changes` (classification and staging), the
     artifact commit's path list in `check_artifacts`, `close_undeclared_gate`,
     `cycle_undeclared_gate`;
   - `src/tddcli/cli.py`: `doctor`'s "worktree clean" check, and `run start`'s dirty-tree refusal
     and its `--allow-dirty` exclusion list;
   - `src/tddcli/staging.py`: `commit` calls `gitutil.add` and `gitutil.staged_paths`.

   A rename made with plain `mv` already reaches all of these today as ` D old` plus `?? new`.
   After the fix, a `git mv` reaches them in exactly that shape, so none of them meets a new
   kind of entry. Cycles 1, 3 and 4 test the two consumers the issue names (classification and
   staging) end to end. *Decided by evidence.* The executor reruns the discovery command and
   stops with a `plan_defect` blocker if a caller outside this list appears.
6. **Docs move with the behaviour. No schema change.** No ledger table or column changes, so
   `SCHEMA_VERSION` stays and no frozen referee is needed. No new `Ledger` method, so nothing
   changes for split-runner guests. `CHANGELOG.md` gets one `### Fixed` entry under
   `## [Unreleased]`, built up by cycles 1, 3 and 4. `docs/PRD.md` R9.13 gets one sentence in
   cycle 1 and one in cycle 4. `docs/`, `CHANGELOG.md` are inside the `tddcli` root `.`, so
   they go in `files` (`.claude/plan-issue.md`). *Decided by convention* (#234's and #249's
   plans, `RELEASING.md`).
7. **The tests live in one new file, `tests/test_status_paths.py`, and drive the real CLI over
   real git.** End to end through `conftest.run_cli` in the `repo` fixture, like
   `tests/test_ignored_paths.py` (#98, the closest precedent: another `git status` path that
   broke staging). Cycle 2's table calls `gitutil.dirty_paths` directly on copies of the
   fixture, like `tests/test_git_lookups.py`. *Decided by convention.*
8. **The issue's one "Test" sentence becomes two cycles.** It asks that a `git mv` inside a
   cycle's root commits the rename and fires no `undeclared_file_touched`. Inside a root, today's
   code never fires that event (the arrow string is owned by the root, so it is implementation,
   and staging crashes before anything else). The event fires only for a rename outside every
   project root. So cycle 1 asserts the event over a renamed ancillary file, where it really
   fires today, and cycle 3 asserts the commit over a rename inside the root. *Decided by
   evidence* (the probes) and by one behaviour per cycle.

## Not in scope (not asked for)

These are not cuts of anything the issue asks for. Rule 4 (no future-proofing) keeps them out:

- **`gitutil.committed_since`** (`git diff --name-only base HEAD`, used by
  `Engine.touched_reference_paths` for R7.11a) also names only the new path of a committed
  rename, and quotes non-ASCII paths. A reference path renamed away by a hand commit would not
  be noticed. The issue is about `status_porcelain`, so this stays as it is. A person may want
  to file it separately.
- **`gitutil.temporary_worktree`'s `ls-files -o -i --directory` listing** is not `-z` either.
  It only links ignored top-level entries into a probe worktree. Not asked.
- **Snapshot restore of a staged rename made during a sensitivity mutation.** `snapshot.restore`
  checks the paths out of the index, so a rename staged with `git mv` mid-mutation is not undone,
  before or after this fix. Not asked.

## Fake/real divergence

None. Every test runs real `git` in the `repo` fixture's temporary repository, and cycles 1, 3
and 4 drive the real CLI in-process.

## Invariant registry, mirrors

There is no `docs/INVARIANTS.md` in this repo. Nothing mirrors `gitutil.py`: every git call in
`src/` goes through `gitutil.git`, and the only other `git status` parsing is in tests.

## Test-side blast radius

**None.** The throwaway full change (decisions 1 to 3) ran against the whole suite in a scratch
worktree: `902 passed`, `ruff check` "All checks passed!", `mypy` "no issues found in 123 source
files". No existing test asserts an arrow string or a quoted path (`grep -rn "status_porcelain\|dirty_paths\|changed_paths" tests/`
is empty), so no cycle declares `modifies_tests`. If GREEN's whole-suite run reports an existing
test anyway, that is a `plan_defect` blocker, not a test to edit.

## Cycles

**Test file.** All four cycles put their test in a new file, `tests/test_status_paths.py`, which
cycle 1 creates. Its module docstring:

> Paths `git status` reports reach classification and staging as git's own paths (#258): a rename
> or copy is two paths, never `old -> new`, and no path is C-quoted.

Imports: `from conftest import git, run_cli, write_plan` in cycle 1; cycle 2 adds `import shutil`
and `from tddcli import gitutil`. Add an import only in the cycle whose test uses it, or ruff's
unused-import check fails that cycle's close sweep. No cycle declares a stub: every test imports
only names that exist today.

**Fixture values. Every cycle uses exactly these.**

- The plan `ONE`, front matter followed by `# Plan` (copied from `tests/test_ignored_paths.py`):

  ```yaml
  cycles:
    - n: 1
      project: backend
      title: "adding two numbers"
      test: "tests/test_add.py::test_add_two_numbers"
      stub_expected: ["app/calc.py"]
  ```

- The plan `ANCILLARY`: `ONE` plus a top-level `ancillary_files: ["docs/old.md", "docs/new.md"]`.
- Helpers, written in cycle 1:
  - `_commit(repo, rel, text)`: write `text` to `repo / rel` (creating parent directories), then
    `git(repo, "add", rel)` and `git(repo, "commit", "-q", "-m", f"add {rel}")`.
  - `_start(repo, body)`: `plan = write_plan(repo, body)`, then assert that `plan register` and
    `run start --plan` are `ok`.
  - `_red(repo)`: write `backend/tests/test_add.py`
    (`from app.calc import add` / `def test_add_two_numbers(): assert add(2, 3) == 5`) and the stub
    `backend/app/calc.py` (`def add(a, b): raise NotImplementedError`), then
    `run_cli(repo, "advance")`.
  - `_green(repo)`: write the real `backend/app/calc.py` (`def add(a, b): return a + b`), then
    return `run_cli(repo, "advance")`.

  (Cycle 1 writes `_commit`, `_start`, `_red` and `_green` because its test uses all four.)

### Cycle 1: a renamed ancillary file fires no `undeclared_file_touched`

- **Behaviour:** decision 1, at the classification consumer.
- **Test:** `test_a_renamed_ancillary_file_fires_no_undeclared_event(repo)`
  1. `_commit(repo, "docs/old.md", "companion notes\n")`;
  2. `_start(repo, ANCILLARY)`; `_red(repo)`;
  3. `git(repo, "mv", "docs/old.md", "docs/new.md")`;
  4. `_green(repo)`;
  5. `events = run_cli(repo, "metrics")["result"]["runs"][0]["integrity_events"]`.

  Single assertion: `assert events.get("undeclared_file_touched", 0) == 0`.
- **Production target:** `gitutil.status_porcelain` in `src/tddcli/gitutil.py`: add
  `"--no-renames"` to its `git status` argv. **Only that.** No `-z` yet (cycle 4), and
  `staged_paths` is untouched (cycle 3).
  - `docs/PRD.md` R9.13: after the "**REFACTOR commit** — as GREEN; skipped without error if
    nothing changed." bullet, add a line at the bullet list's indent:
    > A rename or copy is two paths here, the old path's removal and the new path's addition,
    > each classified on its own: the tool reads `git status` with rename detection off (#258).
  - `CHANGELOG.md`, under `## [Unreleased]`, a `### Fixed` section with:
    > - **A `git mv` reaches staging and classification as its two paths** (#258). A staged
    >   rename used to reach tdd as one path, `old -> new`. Inside a project root a phase commit
    >   handed it to `git add` and the `advance` failed; outside every root it was flagged
    >   `undeclared_file_touched` as one undeclared path. tdd now reads `git status` with rename
    >   detection off, so a rename or copy is the old path's removal and the new path's
    >   addition, each classified and staged on its own. The `git reset -q` and `tdd advance
    >   --retry` workaround is no longer needed.
- **EXPECTED FAILURE** (probed on `origin/main`):
  `AssertionError: assert 1 == 0`, where `1 = {'undeclared_file_touched': 1}.get(...)`. GREEN
  itself succeeds today (`staged: ["backend/app/calc.py"]`), because an `outside` path is never
  staged, so nothing raises before the assertion.

### Cycle 2 (pin): every rename and copy form is two dirty paths

- **Behaviour:** decision 1's multi-form surface (E-12c). Each form `git status` can print with
  a second path reaches `dirty_paths` as its two paths.
- **Test:** `test_every_rename_and_copy_form_is_two_dirty_paths(repo, tmp_path)`.
  1. `_commit(repo, "backend/app/old.py", "X = 1\n")`.
  2. For each `case` below, copy the fixture with
     `r = tmp_path / case.replace(" ", "-")` and `shutil.copytree(repo, r, symlinks=True)`, make
     the change in `r`, then record `found[case] = gitutil.dirty_paths(r)`:
     - `"staged rename"`: `git(r, "mv", "backend/app/old.py", "backend/app/new.py")`;
     - `"renamed then edited"`: the same `git mv`, then write `"X = 2\n"` to
       `backend/app/new.py`;
     - `"intent-to-add rename"`: `(r / "backend/app/old.py").rename(r / "backend/app/new.py")`,
       then `git(r, "add", "-N", "backend/app/new.py")`;
     - `"staged copy"`: `git(r, "config", "status.renames", "copies")`, then
       `shutil.copy(r / "backend/app/old.py", r / "backend/app/copy.py")`, then write
       `"X = 1\nY = 2\n"` to `backend/app/old.py` (git detects a copy only from a modified
       source), then `git(r, "add", "-A")`.

  Single assertion:

  ```python
  assert found == {
      "staged rename": {"backend/app/old.py", "backend/app/new.py"},
      "renamed then edited": {"backend/app/old.py", "backend/app/new.py"},
      "intent-to-add rename": {"backend/app/old.py", "backend/app/new.py"},
      "staged copy": {"backend/app/old.py", "backend/app/copy.py"},
  }
  ```

  The expected sets are written from the fixture, not computed by production code. On today's
  code the probe saw `R `, `RM`, ` R` and `C ` respectively, each returned as one arrow string.
- **Why a pin:** cycle 1's `--no-renames` already makes all four forms plain entries, so this
  passes on arrival (probed on the throwaway step). It pins the forms cycle 1's test does not
  reach. A later change that turned rename detection back on, or parsed only the index column,
  would fail it.
- **Sensitivity check:** remove `"--no-renames"` from `status_porcelain`'s argv. All four cases
  then return the arrow string. Restore it.
- **If it fails on arrival:** cycle 1's GREEN did not follow decision 1. Do not edit production
  code in a pin cycle. File `tdd blocker --kind plan_defect --detail '...'` with `found`.

### Cycle 3: a `git mv` inside the cycle's root commits at GREEN, and `staged` names both paths

- **Behaviour:** decision 2, at the staging consumer. The issue's own test.
- **Test:** `test_a_git_mv_inside_the_cycle_root_stages_both_paths(repo)`
  1. `_commit(repo, "backend/app/old.py", "X = 1\n")`;
  2. `_start(repo, ONE)`; `_red(repo)`;
  3. `git(repo, "mv", "backend/app/old.py", "backend/app/new.py")`;
  4. `green = _green(repo)`.

  Single assertion:
  `assert green["result"].get("staged") == ["backend/app/calc.py", "backend/app/new.py", "backend/app/old.py"]`.

  `staged` is read back from the index the GREEN commit is made from (`staging.commit`), so a
  list naming `old.py` means the commit holds its removal, and `new.py` its addition: the rename.
  `.get` keeps today's failure an assertion: the error envelope's `result` is `{}`.
- **Production target:** `gitutil.staged_paths` in `src/tddcli/gitutil.py`: add `"--no-renames"`
  to its `git diff --cached --name-only` argv. **Only that.** No `-z` (cycle 4).
  - `CHANGELOG.md`: append to cycle 1's entry, as its last sentence:
    > `advance`'s `result.staged`, and the files the ledger records for the commit, name both
    > paths of a rename.
- **EXPECTED FAILURE** (probed on the throwaway cycle-1 step):
  `AssertionError: assert ['backend/app/calc.py', 'backend/app/new.py'] == ['backend/app/calc.py', 'backend/app/new.py', 'backend/app/old.py']`
  (pytest may shorten the lists). The GREEN commit already holds the rename once cycle 1 is in,
  but `git diff --cached --name-only` names only the new path. On `origin/main` itself the failure
  would instead be `assert None == [...]`, because GREEN's `git add` crashes.

### Cycle 4: paths with a space or a non-ASCII character are staged verbatim

- **Behaviour:** decision 3. No path is C-quoted, in classification or in the staged list.
- **Test:** `test_paths_with_a_space_or_non_ascii_are_staged_verbatim(repo)`
  1. `_start(repo, ONE)`; `_red(repo)`;
  2. write `"A = 1\n"` to `backend/app/a b.py` and `"E = 1\n"` to `backend/app/é.py` (new,
     untracked);
  3. `green = _green(repo)`.

  Single assertion:
  `assert green["result"].get("staged") == ["backend/app/a b.py", "backend/app/calc.py", "backend/app/é.py"]`.

  `é` is written as the literal character in the test source (NFC). On macOS, `git init` sets
  `core.precomposeunicode`, so git reports it NFC too.
- **Production target:** in `src/tddcli/gitutil.py`, both:
  - `status_porcelain`: add `"-z"`, replace the `splitlines()` loop with a split on `"\0"`, and
    drop the `.strip()` (decision 3);
  - `staged_paths`: add `"-z"` and split on `"\0"`.

  Both are needed: with `-z` on `status_porcelain` alone the probe still failed, at index 2, on
  `'"backend/app/\\303\\251.py"'` from the staged list.
  - `docs/PRD.md` R9.13: append to cycle 1's sentence:
    > Paths are read NUL-separated (`-z`), so none is C-quoted.
  - `CHANGELOG.md`: append to the entry:
    > A path with a space or a non-ASCII character is no longer C-quoted. It used to be taken
    > for a path outside every project, flagged `undeclared_file_touched` and left out of the
    > commit.
- **EXPECTED FAILURE** (probed on `origin/main` and on the throwaway cycle-3 step):
  `AssertionError: assert ['backend/app/calc.py'] == ['backend/app/a b.py', 'backend/app/calc.py', 'backend/app/é.py']`.
  GREEN succeeds: both quoted paths are classified `outside`, flagged, and not staged.

## Execution

This plan is executed through `tdd-cli`. **You run every command below yourself** — do not ask the
user to start the run. `tdd run start` records which model is executing, resolved from your own
session; a run started by anyone else attributes this work to the wrong agent.

    git checkout -b issue-258-git-status-renames-and-quoting   # first, before anything else
    tdd doctor                                  # healthy, or failing only for projects this plan cannot reach
    tdd run start --plan tasks/issue-258-git-status-renames-and-quoting.md   # captures baselines, opens cycle 1

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
  tests run inside the tests' own temporary repositories, not in this checkout. Do not `git mv`
  anything in this checkout: the referee is the released tool, which still has this bug.)
- The baseline is captured at `run start` and subtracted from later verdicts. The suite is green
  at the plan's base (verified in a fresh worktree of `origin/main` on 2026-11-15: `902 passed`).
  Expect `baselines: {tddcli: 0}`.
- The referee is the released `tdd` on `PATH` (the note at the top of `tdd.toml`), never
  `uv run tdd`. It is 0.19.0 and has none of this plan's behaviour. `SCHEMA_VERSION` does not
  change.
- Every RED, GREEN and REFACTOR edit must pass `uv run ruff check` and `uv run mypy` (the close
  sweep's gates).
- Before cycle 1's GREEN, rerun decision 5's discovery command,
  `grep -rn "dirty_paths\|changed_paths\|is_dirty\|status_porcelain\|staged_paths" src/`. If it
  names a caller outside decision 5's list, stop with `tdd blocker --kind plan_defect`.
- Verbs this plan will hit:
  - `write_test`, `write_implementation`, `refactor_or_advance`.
  - `run_sensitivity_check` → `tdd sensitivity begin|check|end`. Cycle 2 is a pin and will ask
    for it: use the mutation it names, then restore it. Any standard RED that pre-passes also
    asks: mutate the increment that cycle's GREEN was to add.
  - `annotate_cycle` → `tdd annotate --key --value`. This plan declares no keys of its own;
    `plan_defect` and `friction_note` are reserved.
  - `resolve_blocker` → `tdd blocker --kind <plan_defect|regression|tooling|pre_existing_failure> --detail '...'`.
    A pin that fails on arrival (cycle 2) is `plan_defect`.
  - `confirm_cycle_applicable` on a non-existent cycle → `tdd cycle skip --reason`.

**Minimal GREEN, per cycle. Add this and nothing earlier:**

- **Cycle 1:** `"--no-renames"` in `status_porcelain`'s argv; the PRD R9.13 sentence; the
  `### Fixed` CHANGELOG entry. Not `-z`, and not `staged_paths`.
- **Cycle 2:** a pin. Only its test (and the `shutil` and `gitutil` imports).
- **Cycle 3:** `"--no-renames"` in `staged_paths`' argv; the CHANGELOG sentence. Not `-z`.
- **Cycle 4:** `"-z"` and the NUL split in both `status_porcelain` and `staged_paths`, with no
  `.strip()`; the PRD and CHANGELOG sentences.

## Done-criteria

**Before finishing:** run `tdd log render --out tasks/friction-logs/issue-258-git-status-renames-and-quoting-friction.md` and `tdd metrics`. Report the plan-fidelity section — declared vs delivered vs skipped — and every integrity event. Do not narrate what the ledger already records.

Then commit the friction log and raise the PR:

    git add tasks/friction-logs/issue-258-git-status-renames-and-quoting-friction.md
    git commit -m "docs: friction log for issue-258-git-status-renames-and-quoting"

Then invoke the **`raise-pr` skill** (`/raise-pr`), which runs the quality gates, pushes the
branch and opens the PR against `main`. Do not push or call the GitHub API by hand. If a gate
fails, fix it and re-run the skill — a failed gate is work, not a reason to hand back.

The PR body says `Closes #258`. Cycles 1, 3 and 4 own the docs:

- `git diff --stat origin/main -- docs/PRD.md` must be non-empty, or the PR body says why.
- `git diff --stat origin/main -- CHANGELOG.md` must be non-empty, or the PR body says why.
- `git diff origin/main -- src/tddcli/ledger.py | grep -c SCHEMA_VERSION` must print `0`
  (decision 6).

The visible change is `advance`'s `result.staged` and which paths are classified, so no demo
recording is required. In the PR body:

- paste cycle 3's GREEN `staged` list;
- say that `result.staged` and the ledger's commit files now name a rename's old path too, for
  harnesses that read them (geuben/dispatch's `implement-issue`, `raise-pr`);
- say that geuben/coparenting's planner note telling executors to use plain `mv` instead of
  `git mv` (geuben/coparenting#1912) can be dropped once a release carrying this is installed;
  a release is a separate step.
