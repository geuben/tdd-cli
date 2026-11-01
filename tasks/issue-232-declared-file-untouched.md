---
closes: 232
cycles:
  # -- Phase 1: pin today's quiet close, which the new code must keep -----------------------
  - n: 1
    project: tddcli
    pin_cycle: true
    title: "a run that committed every declared path records no declared_file_untouched"
    test: "tests/test_declared_untouched.py::test_a_run_that_committed_every_declared_path_records_no_untouched_event"
    commit_pin: "test: pin — a run that committed every declared path records no untouched event"
  - n: 2
    project: tddcli
    pin_cycle: true
    title: "the complete reply is unchanged when every declared path was committed"
    test: "tests/test_declared_untouched.py::test_the_complete_reply_is_unchanged_when_every_declared_path_was_committed"
    commit_pin: "test: pin — the complete reply is unchanged when nothing declared is untouched"
  - n: 3
    project: tddcli
    pin_cycle: true
    title: "a run with no recorded start_sha still ends complete"
    test: "tests/test_declared_untouched.py::test_a_run_with_no_recorded_start_sha_still_ends_complete"
    commit_pin: "test: pin — a run with no recorded start_sha still ends complete"
  # -- Phase 2: the event --------------------------------------------------------------------
  - n: 4
    project: tddcli
    title: "the last close records the declared paths no commit of the run touched"
    test: "tests/test_declared_untouched.py::test_the_last_close_records_the_declared_paths_no_commit_of_the_run_touched"
    files: ["src/tddcli/gitutil.py", "src/tddcli/machine.py", "src/tddcli/advance.py"]
    commit_red: "test: the last close must record the declared paths no commit touched"
    commit_green: "feat: record declared_file_untouched when the last cycle closes"
    commit_refactor: "refactor: tidy the untouched-declared-path lookup"
  - n: 5
    project: tddcli
    pin_cycle: true
    title: "a last close that blocks still records the untouched paths"
    test: "tests/test_declared_untouched.py::test_a_last_close_that_blocks_still_records_the_untouched_paths"
    commit_pin: "test: pin — a blocked last close still records declared_file_untouched"
  - n: 6
    project: tddcli
    title: "paths committed under the project root, removed, skipped or ignored are not reported"
    test: "tests/test_declared_untouched.py::test_paths_committed_under_the_project_root_removed_skipped_or_ignored_are_not_reported"
    files: ["src/tddcli/machine.py"]
    commit_red: "test: project-relative, removed, skipped and ignored paths are not untouched"
    commit_green: "feat: resolve declared paths under their project root, drop skipped and ignored ones"
    commit_refactor: "refactor: tidy the declared-path resolution"
  - n: 7
    project: tddcli
    title: "skipping the last cycle records the untouched paths"
    test: "tests/test_declared_untouched.py::test_skipping_the_last_cycle_records_the_untouched_paths"
    files: ["src/tddcli/cli.py"]
    commit_red: "test: skipping the last cycle must record the untouched paths"
    commit_green: "feat: a final cycle skip records declared_file_untouched"
    commit_refactor: "refactor: tidy the final-skip close"
  # -- Phase 3: the executor is asked, and the friction log says it -------------------------
  - n: 8
    project: tddcli
    title: "the complete reply names the untouched paths and asks for a note"
    test: "tests/test_declared_untouched.py::test_the_complete_reply_names_the_untouched_paths_and_asks_for_a_note"
    files: ["src/tddcli/advance.py"]
    commit_red: "test: the complete reply must name the untouched paths"
    commit_green: "feat: the complete reply names untouched declared paths and asks for a note"
    commit_refactor: "refactor: tidy the untouched-path sentence"
  - n: 9
    project: tddcli
    title: "the final skip reply names the untouched paths and asks for a note"
    test: "tests/test_declared_untouched.py::test_the_final_skip_reply_names_the_untouched_paths_and_asks_for_a_note"
    files: ["src/tddcli/cli.py"]
    commit_red: "test: the final skip reply must name the untouched paths"
    commit_green: "feat: the final skip reply names untouched declared paths and asks for a note"
    commit_refactor: "refactor: tidy the final-skip reply"
  - n: 10
    project: tddcli
    title: "the friction log names untouched paths per cycle, and ancillary ones in plan fidelity"
    test: "tests/test_declared_untouched.py::test_the_friction_log_names_untouched_paths_per_cycle_and_for_ancillary_files"
    files: ["src/tddcli/render.py", "docs/PRD.md", "README.md", "CHANGELOG.md"]
    commit_red: "test: the friction log must name untouched declared paths"
    commit_green: "feat: render declared_file_untouched in the friction log's plan fidelity"
    commit_refactor: "refactor: tidy the untouched-path rendering"
---

# The friction log reports declared files that no commit of the run touched

## Context

[#232](https://github.com/geuben/tdd-cli/issues/232): the friction log reports
`undeclared_file_touched`, which lists files a run changed that the plan did not declare. It never
reports the reverse: files the plan declared that no commit of the run touched. In a real run,
four declared files were never delivered: a fuzz harness's build manifest, its fuzz target, a
packaging script and a `.gitignore` entry. A locked design decision that depended on them was
dropped with them. The run closed `complete`, the friction log said nothing, and the gap was
found weeks later.

The issue asks for this:

1. At the terminal `tdd advance`, compute the declared paths that no commit of the run touched.
   The declared paths are each cycle's `files` and `stub_expected`, and the plan's
   `ancillary_files`. A path the plan says to delete counts as touched once it is gone.
2. Record them in a run-level `declared_file_untouched` event, and render it in the friction
   log's Plan fidelity section, per cycle where the path came from a cycle.
3. Make it a nudge, not a gate. The reply asks the executor to `tdd note` why each path was not
   needed. Blocking the close until such a note exists is named as an optional follow-up.

The issue is an enhancement. There is no investigation report and no `investigate/issue-232`
branch. Every claim below comes from reading the code and from the planning probes.

### What the code does today (verified on `origin/main`, `bd57486`)

- The last cycle closes in `advance._handle_refactor`. After the close sweep passes, it computes
  `last` and calls `Engine.close_undeclared_gate(cycle)` (which may block), and then
  `Engine.close_cycle`, which ends the run. This is the one terminal `advance` path. Every cycle
  kind closes through it.
- **A run also ends `complete` a second way:** `cli.cmd_cycle_skip`, when the skipped cycle is
  the last declared one, calls `ledger.end_run(run["id"], "complete")` and replies `complete`
  with its own text ("Final cycle skipped; run complete. …").
- `run.start_sha` is HEAD at `run start`. `cmd_run_start` always sets it
  (`start_sha = start_sha or gitutil.head(worktree)`). It has been a column since schema v10
  (0.11.0). A ledger migrated from v9 has `NULL` in rows of runs started before then.
- The ledger's `commit` rows hold only the commits the tool made. README's "Run-close gate for
  undeclared file touches" tells the executor to commit a flagged file **by hand**
  (`git add <path> && git commit`), so a hand commit is a commit of the run too.
- `staging.classify` accepts a `stub_expected` entry written either from the repository root
  (`backend/app/calc.py`) or from the cycle's project root (`app/calc.py`):
  `rel in stub_set or owner.relative_to_root(rel) in stub_set`. Plans in the wild use both
  spellings: README and PRD's example front-matter use `stub_expected: ["app/exception_map.py"]`,
  and `examples/plan.md` uses `files: ["backend/app/orders/pricing.py"]`. In this repo the one
  project's root is `.`, so the two spellings are the same.
- `render.friction_log` never renders a run-level event (`cycle_id` NULL). It prints events
  only inside each cycle's block (`events.get(cycle["id"])`). `undeclared_file_dropped` is
  written run-level and appears nowhere in the friction log. It is counted only in
  `tdd metrics`' `integrity_events` and in `tdd progress`' summary line. (The #98 plan says
  run-level events "appear as `kind×n` counts in the header". That is `tdd progress`, not the
  friction log.)
- On a split-runner guest, `service._Session._closed` refuses a guest write to a run that has
  ended (`run_closed`), and `add_note` is its only exemption (`CLOSED_RUN_EXEMPT`). `event`,
  `cycles` and `event_details` are already guest-visible (`GUEST_WRITES`/`GUEST_READS`), so no
  `Ledger` method is added and no ownership change is needed.

### What the planning probes found (E-2)

All probes ran in a scratch `git worktree` of `origin/main`, which has no worktree-setup script
and needs none. The suite there is green: **`869 passed`**.

| Probe | Result |
|---|---|
| `git log --format= --name-only -z S..HEAD` over a commit with `git mv old.py renamed.py` and `git rm gone.py` | Prints `gone.py` and `renamed.py`. **`old.py` is missing**: rename detection is on by default, so the old path of a rename is never named |
| The same with `--no-renames` | Prints `gone.py`, `old.py` and `renamed.py`. A removal is always named |
| The same over an empty range (`HEAD..HEAD`) | Empty output, exit 0 |
| `git check-ignore --no-index --stdin -z` given `backend/generated/out.txt`, which does not exist, under a `generated/` ignore line | Prints the path. The lookup needs no file on disk |
| Every test in the Cycles section, written into the scratch tree and run on `origin/main` | Cycles 1–3 pass. Cycles 4–10 fail with the EXPECTED FAILURE each cycle quotes. Cycle 5 is a pin because cycle 4 makes it pass |
| A throwaway version of the whole change (decisions 2–8), in the same scratch tree | All ten tests pass. **The full suite still passes (`869 passed`)**, and `ruff check` is clean. No existing test breaks, so no cycle declares `modifies_tests` |
| The same hack, with each of cycle 6's four rules switched off in turn (spellings, `--no-renames`, the skip filter, the ignore filter), and with all four off (the state after cycle 4) | Cycle 6's test fails each time, each with the one extra path that rule removes. All four off gives `['app/calc.py', 'backend/app/never.py', 'backend/app/old.py', 'backend/app/skipped_only.py', 'backend/generated/out.txt']`. So each rule is pinned independently |
| The hack without decision 2's NULL guard, `run.start_sha` set to NULL before the last close | The close `advance` returns `ok: false` with `error: "git log --no-renames … None..HEAD failed: fatal: ambiguous argument 'None..HEAD'"` and `next_action: null` |

The hack, the probe tests and the scratch worktree were all deleted.

## Design decisions (locked)

1. **Declared paths are each delivered cycle's `files` and `stub_expected`, and the plan's
   `ancillary_files`.** `test` and `modifies_tests` ids are not included. A cycle whose ledger
   row is `SKIPPED` contributes nothing. A path it shares with a delivered cycle or with
   `ancillary_files` is still declared through those. *Decided by evidence:* the issue lists
   exactly those three fields. A skipped cycle already has its own line in the friction log
   (`- **Skipped:** <reason>`), and PRD R7.5a already treats a skipped cycle as not executed.
   The issue's case is work that disappeared without a line, and a skip is not that. A declared
   test that never appears already fails RED, so test ids need no second report.

2. **A path is touched when any commit in `run.start_sha..HEAD` names it.** This is the new
   `gitutil.paths_committed_since(worktree, sha) -> set[str]`. It runs
   `git log --no-renames --format= --name-only -z <sha>..HEAD` through `gitutil.git` and returns
   the NUL-separated names, stripped, without empties. A hand commit counts. A removal counts,
   because git names a removed path in the commit that removes it. That is the issue's "paths
   the plan says to delete count as touched once they are gone".
   - **Mechanism footgun:** without `--no-renames`, `git log` names only the new path of a
     rename, so a declared file that the run renamed away would be reported (probed).
   - When `run.start_sha` is NULL (a run started before schema v10 and still live), the method
     returns `[]` and records nothing. `git log None..HEAD` fails, so without the guard the
     last close would answer `ok: false` (probed). Cycle 3 pins it.
   - `gitutil.git` goes through the actor, so `tests/test_actor_seams.py` stays green. *Decided
     by evidence:* the issue says "no commit of the run". The ledger's `commit` rows miss the
     hand commits README tells executors to make. The probes cover the mechanism.

3. **A cycle's path may be written from the repository root or from the cycle's project
   root.** A path `p` declared by a cycle is touched when any of its forms is touched. The
   forms are `os.path.normpath(p)`, plus `os.path.normpath(os.path.join(root, p))` for each of
   the cycle's projects' `root` (`self.config.project(name).root`). An `ancillary_files` path is
   repository-relative (README) and has only the first form. Paths are reported **as the plan
   writes them**. *Decided by evidence:* `staging.classify` accepts both spellings for
   `stub_expected`, and the repo's own docs use both (Context).

4. **A path whose form git's ignore rules match is not reported.** The method passes all forms
   to the existing `gitutil.ignored_paths` (`git check-ignore --no-index`). *Decided by
   convention (#98):* paths git ignores are build output, never staged and never committed, so
   such a path could only ever be reported, and a note could never answer it.

5. **One run-level event, recorded when the last cycle closes, before the run ends.** It is a
   new `Engine.record_untouched_declared(self) -> list[str]` in `src/tddcli/machine.py`. It
   computes `untouched = sorted(p for p, forms in … if not forms & (committed | ignored))`.
   When the list is non-empty it calls
   `self.ledger.event(self.run["id"], None, "declared_file_untouched", json.dumps(untouched))`.
   It returns `untouched` either way. It is called from two places:
   - `advance._handle_refactor`:
     `untouched = engine.record_untouched_declared() if last else []`, placed immediately
     **before** `blocking = engine.close_undeclared_gate(cycle) if last else []`. So a close
     that blocks records it too (cycle 5), and it is written while the run is still live.
   - `cli.cmd_cycle_skip`, in the `nxt_declared is None` branch, **before**
     `ledger.end_run(run["id"], "complete")`. The skipped cycle's row is already `SKIPPED`
     (`ledger.skip_cycle` runs first), so decision 1 leaves out its paths.

   **Mechanism footgun:** the call must come before the run ends. On a split-runner guest, a
   write to an ended run is refused with `run_closed`. *Decided by evidence:* the issue asks
   for a run-level event that lists the paths. The `cycle skip` path is included because the
   issue's failure is "the run closed `complete`, the friction log said nothing", and
   `cmd_cycle_skip` is the other way a run closes `complete`. *By convention:*
   `undeclared_file_dropped` is a run-level event with `json.dumps(sorted(paths))` as its detail.
   The new event is not in `NUDGE_KINDS` (those are per-cycle) and is not a blocker.

6. **The `complete` reply names the paths and asks for a note. No new result field.** A new
   function in `src/tddcli/advance.py`:

   ```python
   def untouched_sentence(paths: list[str]) -> str:
       if not paths:
           return ""
       listed = ", ".join(f"`{p}`" for p in paths)
       return (
           f" Declared but untouched by any commit of this run: {listed}."
           " A plan may over-declare: say in the closing note why each was not needed."
       )
   ```

   It goes between the reply's first sentence and `' Before rendering, …'`, in both `complete`
   replies: `advance._handle_refactor`'s "All declared cycles are complete." and
   `cmd_cycle_skip`'s "Final cycle skipped; run complete.". `cli.py` imports it from
   `.advance`, beside `advance as do_advance`. With no untouched path the replies are exactly
   today's (cycle 2). The blocked reply is unchanged. *Decided by evidence:* the issue says
   "the reply asks the executor to `tdd note` why each path was not needed", and the
   `complete` reply's detail is where the closing note is already asked for. *By convention:*
   a nudge lives in `next_action.detail`, as `_note_nudge` does. Rule 4 rules out a result
   field the issue does not ask for.

7. **The friction log renders the paths in Plan fidelity.** In `render.friction_log`:
   - `untouched` is the sorted union of the paths in every `declared_file_untouched` detail of
     the run (`ledger.event_details`).
   - A cycle's declared set is `set(d.get("files") or []) | set(d.get("stub_expected") or [])`,
     taken from the raw `declared_cycles` dicts and never through `contract.cycles_from_json`
     (the `render-raw-declared-cycles` note).
   - **Per cycle:** in each rendered (non-skipped) cycle block, right after the `Commits` lines
     and before the cycle's `Event` lines, when any untouched path is in that cycle's declared
     set: ``- **Declared but untouched:** `<path>`, `<path>` `` (`_fmt_list`, in sorted order).
   - **Plan-level:** the untouched paths that no non-skipped cycle declares. Only
     `ancillary_files` can produce these. They get one line, after the
     `Declared check never ran` lines and before `- Unblocks:`:
     ``- **Declared but untouched (ancillary_files):** `<path>` ``.

   A run with no such event renders exactly as today. *Decided by evidence:* the issue asks for
   the Plan fidelity section, per cycle where the path came from a cycle. The `### Cycle`
   blocks sit under `## Plan fidelity`. *By convention:* a bold-label bullet, like
   `**Skipped:**` and `**Declared check never ran:**`. No existing line or `tdd metrics` key is
   renamed, so the friction log's outside readers are unaffected (the
   `render-friction-log-consumers` note).

8. **Docs move with the behaviour, and need no `SCHEMA_VERSION` bump.** In cycle 10:
   - `docs/PRD.md` gains R7.5b, and `declared_file_untouched` joins the IntegrityEvent typed
     list;
   - `README.md` gains a paragraph in "Run-close gate for undeclared file touches", and a
     sentence in "The friction log";
   - `CHANGELOG.md` gains an `### Added` entry under `## [Unreleased]`.

   The event is a new `kind` value in the existing `integrity_event` table, so there is no shape
   change and no frozen referee. *By convention:* `.claude/plan-issue.md`, `RELEASING.md` and
   #98's plan.

## Deliberate scope cuts (do not build)

- **Blocking the close until a note exists.** *Premise: the issue names it as a non-goal.* It
  says "It is a nudge, not a gate", and lists blocking only as an "optional follow-up". If a
  person wants the gate, it is a new issue.

## Not in scope (not asked for)

These are not cuts of anything the issue asks for. Rule 4 (no future-proofing) keeps them out.

- Rendering the other run-level events (`undeclared_file_dropped`) in the friction log. They
  are still counted in `tdd metrics` and `tdd progress`.
- `tdd metrics` gets no new key. Its existing `integrity_events` counts include the new kind
  without any code.

## Fake/real divergence

None. Every test drives the real CLI in-process (`conftest.run_cli`) over a real git repository
(the `repo` fixture), with real `git log` and `git check-ignore`. The ledger is read directly
through `Ledger`.

## Cycles

All ten tests live in a new file, `tests/test_declared_untouched.py`, which cycle 1 creates. Its
module docstring cites issue #232. It imports only names that exist today, so **no cycle
declares a stub**:

```python
from __future__ import annotations

import json
import os
import shutil

from conftest import git, run_cli, run_cli_text, write_plan

from tddcli import gitutil
from tddcli.ledger import Ledger
```

Every test drives the `repo` fixture (one pytest project, `backend`, rooted at `backend`).

### Fixture values: every cycle uses exactly these

Write these module-level constants and helpers in cycle 1, all of them, even the ones only a
later cycle uses. In each plan string, a cycle entry sits under `cycles:` at the indentation
shown, and every plan ends with `---\n\n# Plan\n`.

- `TEST_ADD = "from app.calc import add\n\n\ndef test_add_two_numbers():\n    assert add(2, 3) == 5\n"`
- `STUB_ADD = "def add(a, b):\n    raise NotImplementedError\n"`
- `REAL_ADD = "def add(a, b):\n    return a + b\n"`
- The **add cycle** `n: N`, with its `stub_expected` and `files` as each plan below gives them:

  ```yaml
    - n: N
      project: backend
      title: "adding two numbers"
      test: "tests/test_add.py::test_add_two_numbers"
      stub_expected: [<stub>]
      files: [<files>]
  ```

- The **sub cycle**, always `n: 2`, never written, only skipped:

  ```yaml
    - n: 2
      project: backend
      title: "subtracting two numbers"
      test: "tests/test_sub.py::test_subtract_two_numbers"
      files: [<files>]
  ```

- The plans:

  | Name | Cycles | `ancillary_files` |
  |---|---|---|
  | `ONE` | add `n: 1`, stub `"backend/app/calc.py"`, files `["backend/app/calc.py"]` | none |
  | `ONE_THEN_SUB` | `ONE`'s add cycle, then sub with `files: []` | none |
  | `NEVER_ONE` | add `n: 1`, stub `"backend/app/calc.py"`, files `["backend/app/calc.py", "backend/app/never.py"]` | none |
  | `NEVER_ANCILLARY` | `NEVER_ONE`'s add cycle | `["docs/never.md"]` |
  | `NEVER_THEN_SUB` | `NEVER_ONE`'s add cycle, then sub with `files: ["backend/app/sub.py"]` | none |
  | `BY_HAND` | add `n: 1`, stub `"backend/app/calc.py"`, files `["backend/app/calc.py", "backend/app/by_hand.py", "backend/app/never.py"]` | `["docs/never.md"]` |
  | `EXCLUSIONS` | see cycle 6 | none |

  `ancillary_files:` is a top-level key after the `cycles:` list, e.g.
  `ancillary_files: ["docs/never.md"]`.

- `_start(repo, body) -> int`: `plan = write_plan(repo, body)`; assert
  `run_cli(repo, "plan", "register", plan)["ok"]`; `out = run_cli(repo, "run", "start", "--plan",
  plan)`; assert `out["ok"]`; return `out["run"]["id"]`.
- `_deliver_add(repo, during_green=None, before_close=None) -> dict` drives the add cycle and
  returns the envelope of its last `advance`:
  1. write `TEST_ADD` to `backend/tests/test_add.py`, and `STUB_ADD` to `backend/app/calc.py`;
  2. `run_cli(repo, "advance")` (RED);
  3. if `during_green`, call `during_green(repo)`;
  4. write `REAL_ADD` to `backend/app/calc.py`; `run_cli(repo, "advance")` (GREEN);
  5. if `before_close`, call `before_close(repo)`;
  6. `return run_cli(repo, "advance")` (the close).
- `_untouched(repo) -> list`:
  `Ledger(gitutil.repo_identity(repo)).all("SELECT cycle_id, detail FROM integrity_event WHERE
  kind = 'declared_file_untouched' ORDER BY id")`, returned as
  `[(r["cycle_id"], json.loads(r["detail"])) for r in rows]`.
- `_both_endings(repo, tmp_path, before_end=None) -> dict[str, dict]` runs one end-to-end run per
  way a run can end, each in its own copy of the repo. For each `ending` in
  `("advance", "skip")`, it does `copy = tmp_path / ending` and
  `shutil.copytree(repo, copy, symlinks=True)` **before any run starts**. Each copy is an
  independent repo and ledger (the `testing-execution-counter-flake` note). Then:
  - `"advance"`: `run_id = _start(copy, ONE)`;
    `out["advance"] = _deliver_add(copy, before_close=...)`. The callback is
    `lambda r: before_end(r, run_id)` when `before_end` is given, otherwise `None`.
  - `"skip"`: `run_id = _start(copy, ONE_THEN_SUB)`; `_deliver_add(copy)`, which closes cycle 1
    and opens cycle 2; if `before_end`, `before_end(copy, run_id)`;
    `out["skip"] = run_cli(copy, "cycle", "skip", "--reason", "not needed")`.

  It returns `out`. Read each copy's ledger as `_untouched(tmp_path / ending)`.
- `ADVANCE_DONE` and `SKIP_DONE` are today's `complete` details, verbatim (probed):

  ```python
  ADVANCE_DONE = (
      "All declared cycles are complete."
      ' Before rendering, record a closing narrative with `tdd note "<hardest cycle and why,'
      ' plan inaccuracies, deviations>"`. Then run `tdd log render`.'
  )
  SKIP_DONE = (
      "Final cycle skipped; run complete."
      ' Before rendering, record a closing narrative with `tdd note "<hardest cycle and why,'
      ' plan inaccuracies, deviations>"`. Then run `tdd log render`.'
  )
  ```

- `UNTOUCHED = " Declared but untouched by any commit of this run: {}. A plan may over-declare:
  say in the closing note why each was not needed."` (one line in the file; `{}` takes the
  backticked, comma-joined paths). The expected strings in cycles 8 and 9 are built from
  these constants, never by calling `advance.untouched_sentence` (E-9).

### Cycle 1 (pin): a run that committed every declared path records no `declared_file_untouched`

- **Behaviour:** the negative space of decision 5. No event is written when nothing is
  untouched, whichever way the run ends. It guards against an empty `[]` event.
- **Test:** `test_a_run_that_committed_every_declared_path_records_no_untouched_event(repo,
  tmp_path)`: `_both_endings(repo, tmp_path)`. Single assertion:
  `assert {e: _untouched(tmp_path / e) for e in ("advance", "skip")} == {"advance": [], "skip": []}`.
- **Why a pin:** no code writes the kind today, so it passes on arrival (probed). After cycles 4
  and 7 it guards the `if untouched:` in decision 5.
- **If it fails on arrival:** do not edit production code in a pin cycle. File
  `tdd blocker --kind plan_defect --detail '...'`.

### Cycle 2 (pin): the `complete` reply is unchanged when every declared path was committed

- **Behaviour:** decision 6's empty case. `untouched_sentence([])` adds nothing, in both
  replies.
- **Test:** `test_the_complete_reply_is_unchanged_when_every_declared_path_was_committed(repo,
  tmp_path)`: `out = _both_endings(repo, tmp_path)`. Single assertion:
  `assert {e: o["next_action"]["detail"] for e, o in out.items()} == {"advance": ADVANCE_DONE,
  "skip": SKIP_DONE}`.
- **Why a pin:** these are today's texts, verbatim (probed: passes on arrival).
- **If it fails on arrival:** the same instruction as cycle 1.

### Cycle 3 (pin): a run with no recorded `start_sha` still ends complete

- **Behaviour:** decision 2's NULL guard, for both ways a run ends.
- **Test:** `test_a_run_with_no_recorded_start_sha_still_ends_complete(repo, tmp_path)`:
  `out = _both_endings(repo, tmp_path, before_end=_forget_start_sha)`, with a helper
  `_forget_start_sha(repo, run_id)` that does
  `Ledger(gitutil.repo_identity(repo)).update("run", run_id, start_sha=None)`. Single
  assertion:
  `assert {e: (o["next_action"] or {}).get("verb") for e, o in out.items()} == {"advance":
  "complete", "skip": "complete"}`.
- **Why a pin:** nothing reads `start_sha` at close today, so it passes on arrival (probed).
  Without the guard, cycle 4's GREEN makes the close return `ok: false` with
  `next_action: null`, and this test then fails `assert {'advance': None, …} == …` (probed).
  That is why the guard is part of cycle 4's increment.
- **If it fails on arrival:** the same instruction as cycle 1.

### Cycle 4: the last close records the declared paths no commit of the run touched

- **Behaviour:** decisions 2 and 5, for the terminal `advance`. A hand commit counts as a commit
  of the run, and `ancillary_files` are declared.
- **Test:** `test_the_last_close_records_the_declared_paths_no_commit_of_the_run_touched(repo)`
  1. `_start(repo, BY_HAND)`;
  2. `_deliver_add(repo, during_green=by_hand)`. `by_hand(r)` writes `VALUE = 1\n` to
     `backend/app/by_hand.py`, then runs `git(r, "add", "backend/app/by_hand.py")` and
     `git(r, "commit", "-q", "-m", "by hand")`.

  Single assertion:
  `assert _untouched(repo) == [(None, ["backend/app/never.py", "docs/never.md"])]`.
  The `None` pins that the event is run-level. `by_hand.py` is absent only if the hand commit
  counts. A lookup over the ledger's `commit` rows would report it.
- **Production target:**
  - `gitutil.paths_committed_since` (decision 2, with `--no-renames`);
  - `Engine.record_untouched_declared` in `src/tddcli/machine.py`, with the NULL guard
    (decision 2) and the event (decision 5);
  - the call in `advance._handle_refactor`, before `close_undeclared_gate` (decision 5).
- **EXPECTED FAILURE** (probed on `origin/main`):
  `AssertionError: assert [] == [(None, ['backend/app/never.py', 'docs/never.md'])]`. The run
  closes `complete` and GREEN stages only `backend/app/calc.py`. The hand commit sits between
  the RED and GREEN commits.

### Cycle 5 (pin): a last close that blocks still records the untouched paths

- **Behaviour:** decision 5's placement. The record comes before the undeclared gate decides to
  block.
- **Test:** `test_a_last_close_that_blocks_still_records_the_untouched_paths(repo)`
  1. `_start(repo, NEVER_ONE)`;
  2. write `scratch\n` to `repo / "notes.md"`, outside `backend`, so it is undeclared and left
     dirty;
  3. `close = _deliver_add(repo)`.

  Single assertion: `assert (close["next_action"]["verb"], _untouched(repo)) == ("blocked",
  [(None, ["backend/app/never.py"])])`.
- **Why a pin:** cycle 4 places the call before `close_undeclared_gate`, so this passes on
  arrival. On `origin/main` it fails `assert ('blocked', []) == ('blocked', [(None,
  ['backend/app/never.py'])])` (probed). The close's result is `{"kind":
  "undeclared_file_uncommitted", "paths": ["notes.md"]}`.
- **If it fails on arrival:** cycle 4's GREEN put the call somewhere other than decision 5
  says. Do not edit production code in a pin cycle. File
  `tdd blocker --kind plan_defect --detail '...'` and name where the call went.

### Cycle 6: paths committed under the project root, removed, skipped or ignored are not reported

- **Behaviour:** decisions 1, 2, 3 and 4 together. This is one richer test over one method,
  rather than four thin consecutive cycles (TDD rule 7). Each rule removes exactly one path from
  the list, and switching off any one of them fails this test (probed).
- **Test:**
  `test_paths_committed_under_the_project_root_removed_skipped_or_ignored_are_not_reported(repo)`
  1. Before the plan: write `OLD = 1\n` to `backend/app/old.py` and `GONE = 1\n` to
     `backend/app/gone.py`, and append `generated/\n` to `.gitignore`. Then
     `git(repo, "add", "-A")` and
     `git(repo, "commit", "-q", "-m", "files the plan removes, and ignored build output")`.
  2. `_start(repo, EXCLUSIONS)`, with `EXCLUSIONS` exactly:

     ```yaml
     ---
     cycles:
       - n: 1
         project: backend
         title: "a cycle that does not apply"
         test: "tests/test_mul.py::test_multiply"
         files: ["backend/app/skipped_only.py"]
       - n: 2
         project: backend
         title: "adding two numbers"
         test: "tests/test_add.py::test_add_two_numbers"
         stub_expected: ["app/calc.py"]
         files: ["app/calc.py", "backend/app/old.py", "backend/app/gone.py", "backend/generated/out.txt", "backend/app/never.py"]
     ---

     # Plan
     ```

  3. `run_cli(repo, "cycle", "skip", "--reason", "does not apply")`, which skips cycle 1 and
     opens cycle 2;
  4. `_deliver_add(repo, during_green=green)`, where `green(r)` does three things:
     - `os.rename(r / "backend/app/old.py", r / "backend/app/renamed.py")`;
     - unlinks `backend/app/gone.py`;
     - creates `backend/generated/` and writes `built\n` to `backend/generated/out.txt`.

  Single assertion: `assert _untouched(repo) == [(None, ["backend/app/never.py"])]`.
- **Production target:** `Engine.record_untouched_declared` only:
  - the project-root forms (decision 3);
  - the `SKIPPED` filter over `self.ledger.cycles(self.run["id"])` (decision 1, using
    `machine.SKIPPED`);
  - the `gitutil.ignored_paths` filter over every form (decision 4).
- **EXPECTED FAILURE** (probed against cycle 4's increment):
  `AssertionError: assert [(None, ['app/calc.py', 'backend/app/never.py', 'backend/app/old.py',
  'backend/app/skipped_only.py', 'backend/generated/out.txt'])] == [(None,
  ['backend/app/never.py'])]`.
  - `old.py` is in that list only if cycle 4 left out `--no-renames`. With decision 2 followed,
    the list has four entries and the test still fails.
  - On `origin/main` it fails `assert [] == …`.
  - GREEN stages `backend/app/calc.py`, `backend/app/gone.py` and `backend/app/renamed.py`
    (probed). The rename lands as a removal plus an addition, and the ignored file is never
    staged.

### Cycle 7: skipping the last cycle records the untouched paths

- **Behaviour:** decision 5's second call site.
- **Test:** `test_skipping_the_last_cycle_records_the_untouched_paths(repo)`
  1. `_start(repo, NEVER_THEN_SUB)`;
  2. `_deliver_add(repo)`, which closes cycle 1 and opens cycle 2;
  3. `run_cli(repo, "cycle", "skip", "--reason", "not needed")`.

  Single assertion: `assert _untouched(repo) == [(None, ["backend/app/never.py"])]`.
  `backend/app/sub.py` is absent because its cycle is skipped (decision 1).
- **Production target:** `cli.cmd_cycle_skip`'s final branch:
  `engine.record_untouched_declared()` before `ledger.end_run` (decision 5). Leave the result
  unbound here: an assigned, unread local fails ruff's `F841` in the close sweep. Cycle 9 binds
  it. Do not change the reply.
- **EXPECTED FAILURE** (probed): `AssertionError: assert [] == [(None,
  ['backend/app/never.py'])]`. The skip replies `complete` with `SKIP_DONE`.

### Cycle 8: the `complete` reply names the untouched paths and asks for a note

- **Behaviour:** decision 6, on the terminal `advance`, with two paths so the join is pinned.
- **Test:** `test_the_complete_reply_names_the_untouched_paths_and_asks_for_a_note(repo)`
  1. `_start(repo, NEVER_ANCILLARY)`;
  2. `close = _deliver_add(repo)`.

  Single assertion:

  ```python
  assert close["next_action"]["detail"] == (
      "All declared cycles are complete."
      + UNTOUCHED.format("`backend/app/never.py`, `docs/never.md`")
      + ADVANCE_DONE.removeprefix("All declared cycles are complete.")
  )
  ```

- **Production target:** `advance.untouched_sentence`, and its use in `_handle_refactor`'s
  `complete` reply (decision 6).
- **EXPECTED FAILURE** (probed): `AssertionError: assert 'All declared... log render`.' ==
  'All declared... log render`.'`. Today's detail lacks the sentence.

### Cycle 9: the final skip reply names the untouched paths and asks for a note

- **Behaviour:** decision 6, on `cmd_cycle_skip`'s `complete` reply.
- **Test:** `test_the_final_skip_reply_names_the_untouched_paths_and_asks_for_a_note(repo)`
  1. `_start(repo, NEVER_THEN_SUB)`;
  2. `_deliver_add(repo)`;
  3. `out = run_cli(repo, "cycle", "skip", "--reason", "not needed")`.

  Single assertion:

  ```python
  assert out["next_action"]["detail"] == (
      "Final cycle skipped; run complete."
      + UNTOUCHED.format("`backend/app/never.py`")
      + SKIP_DONE.removeprefix("Final cycle skipped; run complete.")
  )
  ```

- **Production target:** `cli.cmd_cycle_skip`'s final `NextAction` text, using
  `untouched_sentence` imported from `.advance` (decision 6).
- **EXPECTED FAILURE** (probed): `AssertionError: assert 'Final cycle ... log render`.' ==
  'Final cycle ... log render`.'`.

### Cycle 10: the friction log names untouched paths per cycle, and ancillary ones in plan fidelity

- **Behaviour:** decision 7, at the boundary where the event is consumed.
- **Test:** `test_the_friction_log_names_untouched_paths_per_cycle_and_for_ancillary_files(repo)`
  1. `_start(repo, NEVER_ANCILLARY)`;
  2. `_deliver_add(repo)`;
  3. `lines = run_cli_text(repo, "log", "render").splitlines()`;
  4. `picked = [ln for ln in lines if ln.startswith("### Cycle") or "Declared but untouched" in ln]`.

  Single assertion:

  ```python
  assert picked == [
      "- **Declared but untouched (ancillary_files):** `docs/never.md`",
      "### Cycle 1: adding two numbers  _(standard)_",
      "- **Declared but untouched:** `backend/app/never.py`",
  ]
  ```

  The order pins the placement. The ancillary line is in the Plan fidelity bullets, ahead of
  every cycle block, and the cycle's line is inside its block. The expected strings come from
  the fixture paths.
- **Production target:**
  - `render.friction_log` (decision 7);
  - `docs/PRD.md`: after R7.5a, add:

    > - **R7.5b** A declared file no commit touched is surfaced, not hidden (#232). When the
    >   last cycle closes, by `tdd advance` (whether the run completes or blocks) or by
    >   `tdd cycle skip`, the tool takes every declared path. These are each delivered cycle's
    >   `files` and `stub_expected`, read as written and under each of the cycle's project
    >   roots, and `ancillary_files`. It drops the paths git's ignore rules match, and those
    >   that any commit from `run.start_sha` to `HEAD` touched, a removal or rename included.
    >   What is left, as the plan writes it, is recorded in one run-level
    >   `declared_file_untouched` event. The `complete` reply names it and asks for a closing
    >   note on why each path was not needed. It blocks nothing. The friction log's Plan
    >   fidelity section carries ``- **Declared but untouched:** `<path>` `` in each cycle that
    >   declares the path, and ``- **Declared but untouched (ancillary_files):** `<path>` ``,
    >   before `Unblocks`, for a path no delivered cycle declares.

    and add `declared_file_untouched` to the end of the IntegrityEvent typed list;
  - `README.md`, in "Run-close gate for undeclared file touches", after the ignored-paths
    paragraph, add:

    > The reverse is reported too. When the last cycle closes, by `tdd advance` or by a final
    > `tdd cycle skip`, any path the plan declares that no commit since `run start` touched is
    > recorded in one `declared_file_untouched` event. The declared paths are a delivered
    > cycle's `files` or `stub_expected`, written from the repository or the project root,
    > and `ancillary_files`. A commit made by hand counts, and so does removing or renaming
    > the file. Paths git ignores are left out. The `complete` reply names the paths and asks
    > for a `tdd note` on why each was not needed. A plan may over-declare, so this blocks
    > nothing.

    and in "The friction log", after the `Declared check never ran` sentence, add:

    > It also names each declared path no commit of the run touched, in the cycle that
    > declared it (``- **Declared but untouched:** `src/x.py` ``), or, for an
    > `ancillary_files` path, on a ``- **Declared but untouched (ancillary_files):** ``
    > line.

  - `CHANGELOG.md`, under `## [Unreleased]`, an `### Added` entry:

    > - **Declared files no commit touched are reported** (#232). When the last cycle closes,
    >   by `tdd advance` or a final `tdd cycle skip`, every path the plan declares (`files`,
    >   `stub_expected`, `ancillary_files`) that no commit since `run start` touched is recorded
    >   in a new run-level `declared_file_untouched` event. Hand commits, removals and renames
    >   count as touched; skipped cycles' paths and paths git ignores are left out. The
    >   `complete` reply names them and asks for a `tdd note` on why each was not needed, and
    >   the friction log's Plan fidelity section lists them per cycle. It blocks nothing.
- **EXPECTED FAILURE** (probed): `AssertionError: assert ['### Cycle 1..._(standard)_'] ==
  ['- **Declare...pp/never.py`']`. Today only the cycle header matches.

## Execution

This plan is executed through `tdd-cli`. **You run every command below yourself** — do not ask the
user to start the run. `tdd run start` records which model is executing, resolved from your own
session; a run started by anyone else attributes this work to the wrong agent.

    git checkout -b issue-232-declared-file-untouched   # first, before anything else
    tdd doctor                                  # healthy, or failing only for projects this plan cannot reach
    tdd run start --plan tasks/issue-232-declared-file-untouched.md   # captures baselines, opens cycle 1

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
  at the plan's base (verified in a fresh worktree of `origin/main`: `869 passed`). Expect
  `baselines: {tddcli: 0}`.
- The referee is the released `tdd` on `PATH` (the note at the top of `tdd.toml`), never
  `uv run tdd`. It predates this feature, so this run's own close reports nothing new.
- Lint (`uv run ruff check`) and typecheck (`uv run mypy`, over `src` and `tests`) are close-sweep
  gates. Every stub and GREEN must pass both. `Ledger.run` and `Ledger.one` return `Row | None`.
- Verbs this plan will hit:
  - `write_test`, `write_implementation`, `refactor_or_advance`.
  - `run_sensitivity_check` → `tdd sensitivity begin|check|end`, if a standard RED pre-passes.
    Mutate the increment that cycle added.
  - `annotate_cycle` → `tdd annotate --key --value`. This plan declares no keys of its own;
    `plan_defect` and `friction_note` are reserved.
  - `resolve_blocker` → `tdd blocker --kind <plan_defect|environment> --detail '...'`. A pin
    (cycle 1, 2, 3 or 5) that fails on arrival is `plan_defect`, as each cycle says.
  - `confirm_cycle_applicable` on a non-existent cycle → `tdd cycle skip --reason`.
  - No cycle declares a stub: every test imports only names that exist today.

**Minimal GREEN, per cycle — add this and nothing earlier:**

- Cycles 1, 2 and 3 are pins. Cycle 1 creates the test file with **every** constant and helper
  from "Fixture values" and its own test. Cycles 2 and 3 add only their test (and cycle 3 its
  `_forget_start_sha` helper).
- Cycle 4 adds:
  - `gitutil.paths_committed_since`, with `--no-renames` (decision 2);
  - `Engine.record_untouched_declared`, with the NULL-`start_sha` guard. It reads cycle paths
    **as written only** (no project-root forms), takes **every** declared cycle (no skip filter)
    and applies **no** ignore filter. It writes the event only when the list is non-empty;
  - the call in `advance._handle_refactor`, before `close_undeclared_gate`.

  Nothing in `cli.py` and no reply text.
- Cycle 5 is a pin. It adds only its test.
- Cycle 6 adds, in `Engine.record_untouched_declared` only: the project-root forms, the
  `SKIPPED` filter and the `gitutil.ignored_paths` filter.
- Cycle 7 adds the call in `cmd_cycle_skip`'s final branch, before `end_run`, unbound. No reply
  text.
- Cycle 8 adds `advance.untouched_sentence` and its use in `_handle_refactor`'s `complete`
  reply. Nothing in `cli.py`.
- Cycle 9 binds `untouched` from that call and uses `untouched_sentence` in `cmd_cycle_skip`'s
  `complete` reply.
- Cycle 10 adds the render lines, the PRD R7.5b text and IntegrityEvent entry, the two README
  passages and the CHANGELOG entry.

## Done-criteria

**Before finishing:** run `tdd log render --out tasks/friction-logs/issue-232-declared-file-untouched-friction.md` and `tdd metrics`. Report the plan-fidelity section — declared vs delivered vs skipped — and every integrity event. Do not narrate what the ledger already records.

Then commit the friction log and raise the PR:

    git add tasks/friction-logs/issue-232-declared-file-untouched-friction.md
    git commit -m "docs: friction log for issue-232-declared-file-untouched"

Then invoke the **`raise-pr` skill** (`/raise-pr`), which runs the quality gates, pushes the
branch and opens the PR against `main`. Do not push or call the GitHub API by hand. If a gate
fails, fix it and re-run the skill — a failed gate is work, not a reason to hand back.

The PR body says `Closes #232`. Cycle 10 owns the docs:

- `git diff --stat origin/main -- docs/PRD.md` must be non-empty, or the PR body says why.
- `git diff --stat origin/main -- README.md` must be non-empty, or the PR body says why.
- `git diff --stat origin/main -- CHANGELOG.md` must be non-empty, or the PR body says why.

The visible change is ledger content, reply text and friction-log lines, so no demo recording is
required. In the PR body, quote cycle 10's two rendered lines and cycle 8's `complete` detail.
Say that the friction log's text gains lines and renames none, so its outside readers
(`implement-issue`, `raise-pr`) are unaffected.
