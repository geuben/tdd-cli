---
closes: 163
cycles:
  - n: 1
    project: tddcli
    title: "vitest batch collection builds ids from `vitest list --json`"
    test: "tests/test_vitest_adapter.py::test_batch_collection_roots_each_id_at_its_listed_file"
    files:
      - "src/tddcli/adapters/vitest_adapter.py"
      - "README.md"
      - "docs/PRD.md"
      - "CHANGELOG.md"
    modifies_tests:
      - "tests/test_batch_collection.py::test_vitest_partial_output_from_a_failed_batch_is_not_trusted"
    commit_red: "test: vitest batch collection reads each id's file from list --json"
    commit_green: "fix: build vitest batch ids from vitest list --json"
    commit_refactor: "refactor: tidy the vitest JSON listing"
  - n: 2
    project: tddcli
    title: "a vitest batch listing that is not JSON is left to the per-file loop"
    test: "tests/test_batch_collection.py::test_vitest_batch_leaves_a_text_listing_to_the_per_file_loop"
    files: ["src/tddcli/adapters/vitest_adapter.py"]
    modifies_tests:
      - "tests/test_batch_collection.py::test_vitest_batch_attributes_each_id_to_its_own_file"
    commit_red: "test: a text vitest listing is not trusted by the batch"
    commit_green: "fix: drop the text parse from vitest batch collection"
    commit_refactor: "refactor: tidy vitest batch collection"
  - n: 3
    project: tddcli
    title: "the vitest override-isolation probe reads `vitest list --json`"
    test: "tests/test_suite_overrides.py::test_vitest_isolation_probe_flags_default_reach_into_override_files"
    files: ["src/tddcli/adapters/vitest_adapter.py"]
    modifies_tests:
      - "tests/test_suite_overrides.py::test_vitest_isolation_probe_flags_default_reach_into_override_files"
    commit_red: "test: the vitest isolation probe reads list --json"
    commit_green: "fix: the vitest isolation probe reads file paths from list --json"
    commit_refactor: "refactor: share the vitest JSON listing between collection and isolation"
  - n: 4
    project: tddcli
    title: "the vitest isolation probe fails when the listing is not JSON"
    test: "tests/test_suite_overrides.py::test_vitest_isolation_probe_fails_on_a_listing_that_is_not_json"
    files:
      - "src/tddcli/adapters/vitest_adapter.py"
      - "README.md"
      - "docs/PRD.md"
      - "CHANGELOG.md"
    commit_red: "test: an unreadable vitest listing fails the isolation probe"
    commit_green: "fix: fail the vitest isolation probe on a listing that is not JSON"
    commit_refactor: "refactor: tidy the vitest isolation probe"
  - n: 5
    project: tddcli
    title: "adoption never picks a test another cycle already targets"
    test: "tests/test_advance_adoption.py::test_adoption_skips_a_test_an_earlier_cycle_targets"
    files:
      - "src/tddcli/advance.py"
      - "docs/PRD.md"
      - "CHANGELOG.md"
    commit_red: "test: adoption skips an earlier cycle's target"
    commit_green: "fix: exclude every cycle's target from adoption candidates"
    commit_refactor: "refactor: tidy adoption candidates"
  - n: 6
    project: tddcli
    title: "tdd target accepts every spelling of a collected test"
    test: "tests/test_target_validation.py::test_target_accepts_every_spelling_of_a_collected_test"
    files:
      - "src/tddcli/cli.py"
      - "docs/PRD.md"
      - "docs/harness-integration.md"
      - "CHANGELOG.md"
    commit_red: "test: tdd target accepts the plan's spelling of a test"
    commit_green: "fix: tdd target matches ids the way a plan declaration does"
    commit_refactor: "refactor: tidy tdd target matching"
  - n: 7
    project: tddcli
    pin_cycle: true
    title: "an adopted target the run did not evaluate asks for another advance"
    test: "tests/test_advance_adoption.py::test_an_adopted_target_the_run_did_not_evaluate_asks_for_another_advance"
    files: []
    commit_pin: "test: pin the unevaluated single-candidate adoption reply"
  - n: 8
    project: tddcli
    pin_cycle: true
    title: "a resolved adoption the run did not evaluate asks for another advance"
    test: "tests/test_advance_adoption.py::test_a_resolved_adoption_the_run_did_not_evaluate_asks_for_another_advance"
    files: []
    commit_pin: "test: pin the unevaluated resolved-candidate adoption reply"
  - n: 9
    project: tddcli
    refactor_cycle: true
    title: "fold the two adoption branches into one path"
    files: ["src/tddcli/advance.py"]
    commit_refactor: "refactor: one adoption path for single and resolved candidates"
  - n: 10
    project: tddcli
    title: "an adopted target the run cannot find is refused"
    test: "tests/test_advance_adoption.py::test_an_adopted_target_the_run_cannot_find_is_refused"
    files:
      - "src/tddcli/advance.py"
      - "docs/PRD.md"
      - "docs/harness-integration.md"
      - "CHANGELOG.md"
    commit_red: "test: an adoption the run cannot find is refused"
    commit_green: "fix: refuse an adopted target the run cannot find"
    commit_refactor: "refactor: tidy the refused adoption"
---

# Issue 163: vitest adoption ids

## Context

[#163](https://github.com/geuben/tdd-cli/issues/163) reports a run on tdd-cli 0.14.0 that got
stuck in cycle 2 after `tdd advance` was run before cycle 2's test existed. The run was against
a vitest project that has a named vitest project (`[core]`). The report lists four symptoms:

1. Adoption (`_adopt_target` in `src/tddcli/advance.py`) picked **cycle 1's** test for cycle 2.
   It excludes tests that existed at run start and the cycle's own targets, but not the targets
   of other cycles.
2. The adopted id was the `vitest list` spelling (`[core] file > describe > it`), which no
   verdict ever contains. The adopted test was therefore always `not_found`.
3. Every advance re-adopted a different test, so the target flipped between the two.
4. `tdd target` accepts only an exact collected id. It could not set the plan's own declared
   id, which is the one spelling that would have matched.

The probes for this plan reproduced every symptom against vitest 4.1.11 and against a fake
vitest (see cycle 5). The root causes:

- `vitest list` (text) prints `[<project name>] ` before each line whenever the vitest config
  names a project (`formatCollectedAsString` in vitest's `cli-api` chunk:
  `` (test.project.name ? `[${test.project.name}] ` : "") + fullName ``). When a vitest project
  sets its own `root`, the file path on that line is relative to **that** root. Probed:
  `packages/core/src/b.test.ts` lists as `[pkg] src/b.test.ts > …`.
- `VitestAdapter._collect_batch` takes everything before the first ` > ` as the file. That
  produces `frontend::[core] src/a.test.ts > …`, and `run()` never produces that id. Because the
  "file" `[core] src/a.test.ts` is not a real path, the batch accounts for no files. The
  per-file loop then runs too and adds the correct id, so the collected set holds **both**
  spellings of every test.
- `VitestAdapter.override_isolation` has the same parse, so for a named vitest project the
  reach check can never match an override pattern.
- `cmd_target` (`src/tddcli/cli.py`) tests `args.test in known` as an exact string.

## Design decisions (locked)

1. **Batch collection reads `vitest list --json`.** (User, Phase C.) `_collect_batch` appends
   ` --json` to each suite's collect command. It builds each id from the entry's absolute
   `file`, made relative to the adapter root exactly as `_id_for` does, and from `name` with
   its ` > ` separators rejoined by a space. That matches `run()`'s `fullName`. This handles
   both the `[name] ` prefix and per-project roots. Probed output, vitest 4.1.11 on stdout,
   with warnings on stderr:

       [
         {"name": "outer > inner > adds one", "file": "/abs/vt/src/a.test.ts", "projectName": "core"},
         {"name": "outer > inner > adds one", "file": "/abs/vt/packages/core/src/b.test.ts", "projectName": "pkg"}
       ]

   The `files` half of the batch result is the same root-relative paths, so the per-file loop
   no longer re-collects files the batch listed.
2. **`--json` is appended unconditionally**, the way `run()` appends `--reporter=json`.
   Probed: `vitest list --config x.mjs --json` works, and `vitest list --json --json` prints
   **nothing**. A collect command that already ends in `--json` therefore yields an empty
   listing. Collection then falls to the per-file loop (decision 3), and the isolation probe
   fails and names the command (decision 5). That is loud rather than silent. README says tdd
   adds the flag.
3. **A batch listing that is not a JSON array returns `None`** (the existing "leave these
   files to the loop" signal). The text parse is removed from `_collect_batch`. The per-file
   loop keeps its text parse (`_parse_list_output`), which is already correct: it pins each id
   to the path it was given and drops everything before the first ` > `, prefix included.
   Probed: `vitest list packages/core/src/b.test.ts` prints `[pkg] src/b.test.ts > …`, and
   the loop maps it to `packages/core/src/b.test.ts`.
4. **`override_isolation` reads the same JSON listing** (a shared helper is fine). Reach is
   decided from each entry's root-relative `file`.
5. **An isolation listing that is not a JSON array fails the gate.** (Evidence. The repo's
   R10.3/R10.4 rule is that a silent empty collection disables checks without any signal.)
   The `GateResult.output` names the command it ran, e.g. `npx vitest list --json`, and says
   tdd reads vitest's JSON listing. `collectable()` is unchanged: it still runs the plain
   collect command and checks only the exit code.
6. **Adoption excludes every cycle's targets in the run, compared by normalised id.** (User,
   Phase C.) `_adopt_target` drops any collected test whose `adapter.normalise_id(...)` equals
   the normalised form of any id in any `cycle.target_tests` row of this run, the current
   cycle included. The comparison must be normalised. Cycle 1's stored target is the declared
   spelling `frontend::src/add.test.ts > math > adds`, while the collected id is
   `frontend::src/add.test.ts > math adds`. A raw set difference misses the match, and the
   cycle 5 probe confirmed this. There is no per-cycle collection snapshot and no schema change.
7. **`tdd target <id>` qualifies the argument the way a plan declaration is qualified, then
   matches by normalised id, and stores the collected id.** Qualification is
   `Engine._qualify(declared, args.test)`, with `declared` from
   `_engine(...).declared_for(cycle["ordinal"])`. The stored target and the `result.target`
   are the **collected** spelling, so later raw comparisons (`_outcome_from_verdicts`) hold.
   The accepted forms are all equivalent. For collected `frontend::src/add.test.ts > math adds`:

   | form | example |
   |---|---|
   | collected, qualified | `frontend::src/add.test.ts > math adds` |
   | declared arrows, qualified | `frontend::src/add.test.ts > math > adds` |
   | plan-literal, project-relative | `src/add.test.ts > math > adds` |
   | project-relative, space-joined | `src/add.test.ts > math adds` |
   | project-name-prefixed path (`_qualify`'s strip) | `frontend/src/add.test.ts > math > adds` |

   Rejected: an id that matches no collected test in any spelling. The refusal is unchanged,
   with the same `not a collected test` error and close-match hint, and the existing
   `tests/test_target_validation.py` tests pin it. The `vitest list` text spelling
   (`[core] src/add.test.ts > …`) is rejected because collection no longer contains it
   (cycles 1–2).
8. **An adopted target that the evaluating run reports `not_found` is refused, not recorded.**
   (User, Phase C.) The adoption is evaluated **before** `target_tests` is updated. On
   `not_found`:
   - `target_tests` keeps the declared ids;
   - no `declared_test_mismatch` is recorded;
   - one `adopted_target_not_found` event is recorded, with detail
     `{"declared": missing, "adopted": [id]}`;
   - the reply is `resolve_blocker`. Its detail says that collection and execution disagree
     about the id, the declared target is unchanged, and the agent should file
     `tdd blocker --kind tooling --detail '...'`. `result` carries `adopted` and `declared`.

   This applies to the single-candidate branch and the resolved multi-candidate branch alike.
   Cycle 9 folds those into one path, so cycle 10's guard covers both.
9. **The two adoption branches become one path before the guard lands** (cycles 7–9). Their
   success paths are guarded by existing tests. Probing showed their "run did not evaluate it"
   return (`adopted_outcome is None`) was guarded by nothing, which is why cycles 7 and 8 pin it
   first. That return is reachable: in a contract cycle whose first target is missing and whose
   second target is in the same project, `Engine.run_projects` runs only one target per project.
   `declared_test_mismatch` details keep their current shapes: `{"declared", "adopted"}` for a
   single candidate, and `{"declared", "adopted", "all_candidates"}` for a resolved one.
10. **An end-to-end vitest harness is built as test code** in cycle 5's RED:
    `tests/fake_vitest.py` plus a `repo_vitest` fixture in `tests/conftest.py` (contract under
    cycle 5). The adapter-level cycles (1–4) keep monkeypatching `run_command` with the
    verbatim probed output, because that is more faithful than any fake.

### Fake vs. real vitest (the `tests/fake_vitest.py` seam)

| Behaviour | Fake | Real vitest 4.1.11 | Left untested | Ruling |
|---|---|---|---|---|
| `list` (text) | `[core] <rel> > a > b` | same | per-project `root` paths (fake has one project at the root) | acceptable: cycle 1 pins per-project roots with verbatim real JSON |
| `list --json` | `[{name: "a > b", file: abs, projectName: "core"}]` | same shape (+ `location`) | `location` | acceptable, unused |
| `list <file>` | filters to that root-relative file | same | — | acceptable |
| `run --reporter=json [file] [-t re]` | `testResults[].name` abs, `assertionResults[].fullName` space-joined, exit 1 on any failure | same shape | other report keys | acceptable, unused by the adapter |
| `-t` | Python `re.search` | JS regex, unanchored | JS-only syntax | acceptable: tdd anchors and escapes only JS metacharacters, which Python reads the same way |
| `listed` case | listed, never reported by `run` | no direct analogue | — | acceptable: a synthetic collect/run mismatch is exactly the seam cycle 10 needs |

## Deliberate scope cuts (do not build)

None. Two findings from probing are **not part of #163** and are not built here. They are
reported in the PR body for the user to file:

- `Engine.run_projects` runs only the first target per project. A contract cycle with two
  targets in one project therefore never evaluates the second.
- The reporter's already-blocked run is recovered with `tdd run abandon` (0.14.0), not with
  code in this plan.

## Cycles

Every test id is project-relative (`tddcli` root is `.`). A refusal's `reason` would sit under
`result.reason`, but no cycle here asserts one.

### Cycle 1: batch collection reads `vitest list --json`

- **Test:** `tests/test_vitest_adapter.py::test_batch_collection_roots_each_id_at_its_listed_file`.
  Use the file's `TOML`. Create empty files `frontend/src/a.test.ts` and
  `frontend/packages/core/src/b.test.ts`. Monkeypatch
  `adapters.vitest_adapter.run_command` (import `from tddcli import adapters`) with a fake:
  - a command containing `--json` returns `(0, <listing>, "")`, where the listing is
    `json.dumps([...], indent=2)` of the two entries from decision 1, with `file` =
    `str(tmp_path / "frontend" / "src/a.test.ts")` and
    `str(tmp_path / "frontend" / "packages/core/src/b.test.ts")`, and `projectName` `core`
    and `pkg`;
  - exactly `npx vitest list` returns the prefixed text
    `[core] src/a.test.ts > outer > inner > adds one\n[pkg] src/b.test.ts > outer > inner > adds one\n`;
  - anything else (the per-file loop) returns `f"{command.rsplit(' ', 1)[1]} > from the loop\n"`.

  One assertion: `adapter.collect().tests == {"frontend::src/a.test.ts > outer inner adds one",
  "frontend::packages/core/src/b.test.ts > outer inner adds one"}`. This fails if the batch
  runs without `--json`, keeps a prefixed id, or leaves the files to the loop.
- **Target:** `VitestAdapter._collect_batch`.
- **EXPECTED FAILURE:** `AssertionError: assert {'frontend::[...rom the loop'} == {...}`. The
  extra items are `frontend::[core] src/a.test.ts > outer inner adds one`,
  `frontend::[pkg] src/b.test.ts > outer inner adds one` and two `> from the loop` ids.
- **Breaks:** `tests/test_batch_collection.py::test_vitest_partial_output_from_a_failed_batch_is_not_trusted`.
  Its fake keys the whole-suite call on `command.endswith("list")`. With `--json` the batch
  command reaches the per-file branch instead and yields `frontend::--json > rescued`. Change
  the condition to `command.endswith("list --json")` and nothing else. Probed: that is the
  only existing test cycle 1 breaks.
- **Refactor phase:** README's override paragraph (the one ending "…refused at `tdd run start`,
  not mid-cycle.") says tdd appends `--json` to each vitest collect command for the
  whole-suite listing, so a collect command must not carry `--json` itself. PRD R10.7 says
  collection's whole-suite vitest listing is `vitest list --json`. CHANGELOG `## [Unreleased]`
  gets `### Fixed` with a bullet for vitest ids from named vitest projects (#163).

### Cycle 2: a text listing is not trusted by the batch

- **Test:** `tests/test_batch_collection.py::test_vitest_batch_leaves_a_text_listing_to_the_per_file_loop`.
  Use `repo_multi` and create empty `frontend/a.test.ts` and `frontend/b.test.ts`. The fake:
  - a command ending in `list --json` returns `(0, "[core] a.test.ts > alpha\n[core] b.test.ts > beta\n", "")`,
    a runner that ignored `--json`;
  - anything else returns `(0, f"{command.rsplit(' ', 1)[1]} > rescued\n", "")`.

  One assertion: `_adapter(repo_multi, "frontend").collect().tests ==
  {"frontend::a.test.ts > rescued", "frontend::b.test.ts > rescued"}`.
- **Target:** `VitestAdapter._collect_batch`. Delete its text parse and return `None` for
  anything that is not a JSON array.
- **EXPECTED FAILURE** (after cycle 1): the extra items are
  `'frontend::[core] a.test.ts > alpha'` and `'frontend::[core] b.test.ts > beta'`.
- **Breaks:** `tests/test_batch_collection.py::test_vitest_batch_attributes_each_id_to_its_own_file`.
  Its fake returns text for every command. Make it return, for a command containing `--json`,
  a JSON array with `{"name": "alpha", "file": str(repo_multi / "frontend" / "a.test.ts")}`
  and the same for `beta`/`b.test.ts`. Keep its assertion and update its docstring to say the
  listing is JSON. Probed: that is the only existing test cycle 2 breaks.

### Cycle 3: the isolation probe reads `vitest list --json`

- **Test:** rewrite the existing
  `tests/test_suite_overrides.py::test_vitest_isolation_probe_flags_default_reach_into_override_files`.
  Keep its `project_with(..., adapter="vitest")` override block. Its fake records the command
  and returns `(0, json.dumps([...]), "")` with two entries:
  - `{"name": "adds", "file": str(tmp_path / "backend" / "src/__tests__/a.test.ts"), "projectName": "core"}`;
  - `{"name": "pings", "file": str(tmp_path / "backend" / "contract/api.test.ts"), "projectName": "core"}`.

  Its assertions stay in their current order: `gate.ok is False`, `"contract/api.test.ts" in
  gate.output`, and `seen == ["npx vitest list --json"]`.
- **Target:** `VitestAdapter.override_isolation`. **Minimal GREEN:** read the JSON listing and
  keep today's text read for output that is not JSON. Cycle 4 removes it.
- **EXPECTED FAILURE:** `AssertionError: assert True is False` (`GateResult(ok=True, output='')`).

### Cycle 4: a listing that is not JSON fails the isolation probe

- **Test:** `tests/test_suite_overrides.py::test_vitest_isolation_probe_fails_on_a_listing_that_is_not_json`.
  Use the same override project as cycle 3. The fake returns
  `(0, "src/__tests__/a.test.ts > adds\n", "")` for every command. One assertion:
  `(gate.ok, "npx vitest list --json" in gate.output) == (False, True)`.
- **Target:** `VitestAdapter.override_isolation` (decision 5).
- **EXPECTED FAILURE:** `assert (True, False) == (False, True)`.
- **Refactor phase:** the README override paragraph says an unreadable listing fails
  `tdd doctor`. PRD: the isolation probe reads `vitest list --json`. CHANGELOG: a bullet under
  the same `### Fixed`.

### Cycle 5: adoption skips an earlier cycle's target

**Harness, written in this cycle's RED** (test code, staged with the test):

- `tests/fake_vitest.py` is a script run as `<python> tests/fake_vitest.py list|run …`, with
  cwd = the project root. It reads every `*.test.ts` under cwd, where each line is
  `case: <title> > <title> = pass|fail|listed|needs <root-relative path>`.
  - `list [--json] [<rel file>…]` prints either `[core] <rel> > <titles joined " > ">` per
    case, or with `--json` a JSON array of
    `{"name": <titles joined " > ">, "file": <absolute>, "projectName": "core"}`.
  - `run --reporter=json [<rel file>] [-t <pattern>]` prints
    `{"duration": 5, "testResults": [{"name": <absolute>, "status": …, "assertionResults":
    [{"fullName": <titles joined " ">, "status": "passed"|"failed", "failureMessages": […]}]}]}`.
    `-t` filters with `re.search` on `fullName`. `listed` cases are never reported.
    `needs X` passes if and only if `<cwd>/X` exists. The exit code is 1 if any case failed.
- The `repo_vitest` fixture in `tests/conftest.py` is modelled on `repo`: a workspace with
  `tdd.toml` holding
  `[project.frontend]` with `root = "frontend"`, `adapter = "vitest"`,
  `test_paths = ["**/*.test.ts"]`, and
  `test_command = "<shlex-quoted sys.executable> <shlex-quoted fake path> run"`. The
  `collect_command` is the same with `list`. It also sets `lint = []` and `typecheck = []`.
  Add `frontend/src/smoke.test.ts` containing `case: smoke > works = pass`, then `git init`,
  set the user config, and commit.

**Test:** `tests/test_advance_adoption.py::test_adoption_skips_a_test_an_earlier_cycle_targets`.
The plan has two cycles in project `frontend`: `src/add.test.ts > math > adds` and
`src/sub.test.ts > math > subtracts`, each with `commit_red`/`commit_green`. Register it and
start the run. Then:

1. Write `frontend/src/add.test.ts` with `case: math > adds = needs src/add.ts` and advance.
   This is RED.
2. Write `frontend/src/add.ts` with `export {}` and advance. This is GREEN.
3. Advance to close cycle 1.
4. Advance again **without writing cycle 2's test**.

One assertion: that last reply's `next_action.verb == "write_test"`.
- **Target:** `_adopt_target` (decision 6).
- **EXPECTED FAILURE** (after cycles 1–4): `AssertionError: assert 'run_sensitivity_check' == 'write_test'`.
  Cycle 1's test is adopted and passes on arrival. Before cycles 1–2 the reply was
  `name_target_test` with both spellings of cycle 1's test, which is the issue exactly.
- **Refactor phase:** PRD R8.9: adoption diffs `collect()` against the run's start and never
  offers a test that another cycle of the run targets. CHANGELOG bullet.

### Cycle 6: `tdd target` accepts every spelling

- **Test:** `tests/test_target_validation.py::test_target_accepts_every_spelling_of_a_collected_test`.
  Use `repo_vitest` and a one-cycle plan declaring `src/add.test.ts > math > adds`. Start the
  run and write `frontend/src/add.test.ts` with `case: math > adds = needs src/add.ts`. Run
  `run_cli(repo, "target", form)` for each of the five forms in decision 7's table, in table
  order, and collect `out.get("result", {}).get("target")`. One assertion: the list equals
  `["frontend::src/add.test.ts > math adds"] * 5`.
- **Target:** `cmd_target` in `src/tddcli/cli.py`.
- **EXPECTED FAILURE:** `AssertionError: … At index 1 diff: None != 'frontend::src/add.test.ts > math adds'`.
  Only the collected form is accepted today.
- **Refactor phase:** in `docs/harness-integration.md`, the `name_target_test` row says
  `tdd target` accepts the plan's spelling. PRD: the same, where R8.9 names `tdd target`.
  CHANGELOG bullet.

### Cycle 7 (pin): an unevaluated single-candidate adoption asks for another advance

- **Test:** `tests/test_advance_adoption.py::test_an_adopted_target_the_run_did_not_evaluate_asks_for_another_advance`.
  Use `repo` (pytest) and one `contract_cycle: true` in project `backend` with
  `tests: ["tests/test_add.py::test_add_two_numbers", "tests/test_smoke.py::test_smoke"]`,
  **missing target first**. Start the run and write `backend/tests/test_new.py` with
  `def test_new():\n    assert False\n`. One assertion on the first advance:
  `(out["next_action"]["verb"], out["result"]["adopted"]) == ("refactor_or_advance", ["backend::tests/test_new.py::test_new"])`.
- **Kind: pin.** Probed as passing on arrival: the reply is "Adopted … Run `tdd advance` again
  to evaluate it." Change no production code. The sensitivity check mutates the
  `adopted_outcome is None` return in the single-candidate branch.

### Cycle 8 (pin): an unevaluated resolved adoption asks for another advance

- **Test:** `tests/test_advance_adoption.py::test_a_resolved_adoption_the_run_did_not_evaluate_asks_for_another_advance`.
  Use the same plan as cycle 7. Write `backend/tests/test_add.py` with
  `def test_adding():\n    assert False\n` and `backend/tests/test_other.py` with
  `def test_other():\n    assert True\n`. The candidate in the declared file is resolved. One
  assertion: `(verb, adopted) == ("refactor_or_advance", ["backend::tests/test_add.py::test_adding"])`.
- **Kind: pin.** Probed as passing on arrival. Change no production code. The sensitivity
  check mutates the resolved branch's `adopted_outcome is None` return.

### Cycle 9 (refactor): one adoption path

Fold the single-candidate branch and the resolved branch of `_handle_test_phase` into one
helper. After a branch has chosen `adopted` and built the `declared_test_mismatch` detail, the
helper does the rest: record the event, update `target_tests`, call `_evaluate_adopted`, and
either return the `refactor_or_advance` reply or hand back `targets`/`outcomes`/`failure`/`others`.
Behaviour is preserved verbatim, including both detail shapes (decision 9). The guards are the
existing tests below and the cycle 7 and 8 pins:
- `tests/test_advance_adoption.py::test_single_new_test_is_adopted_and_evaluated_in_one_advance`
- `tests/test_advance_adoption.py::test_adopted_passing_test_demands_sensitivity_in_one_advance`
- `tests/test_advance_adoption.py::test_unique_same_file_candidate_is_adopted_and_evaluated`
- `tests/test_suite_scope.py::test_an_adopted_target_is_evaluated_in_the_same_advance`
- `tests/test_suite_scope.py::test_an_adopted_targets_failure_comes_from_its_own_run`

If the fold needs any change in behaviour, raise a `plan_defect` blocker. Do not commit it
under refactor.

### Cycle 10: an adoption the run cannot find is refused

- **Test:** `tests/test_advance_adoption.py::test_an_adopted_target_the_run_cannot_find_is_refused`.
  Use `repo_vitest` and a one-cycle plan declaring `src/add.test.ts > math > adds`. Start the
  run and write `frontend/src/ghost.test.ts` with `case: ghost > only listed = listed`, then
  advance. Read the ledger with `Ledger(repo)` (from `tddcli.ledger`): `target_tests` of the
  cycle row, and `[r["kind"] for r in ledger.all("SELECT kind FROM integrity_event ORDER BY id")]`.
  One assertion:
  `(out["next_action"]["verb"], json.loads(target_tests), kinds) == ("resolve_blocker", ["frontend::src/add.test.ts > math > adds"], ["adopted_target_not_found"])`.
- **Target:** the helper from cycle 9 (decision 8).
- **EXPECTED FAILURE:** the verb is `write_test`, from the misleading "A contract cycle's
  targets must all fail together" reply. `target_tests` is
  `["frontend::src/ghost.test.ts > ghost only listed"]` and the kinds are
  `["declared_test_mismatch"]`.
- **Refactor phase:** in `docs/harness-integration.md`, the `resolve_blocker` row adds "or an
  adopted target the run cannot find". PRD R8.9 gets a bullet for the refusal. CHANGELOG
  bullet.

## Behaviour census

| Promised behaviour | Test |
|---|---|
| batch ids from `list --json`, rooted at each entry's file | cycle 1 |
| batch never trusts a text listing | cycle 2 |
| isolation reads `list --json` | cycle 3 |
| isolation fails on a listing that is not JSON, naming the command | cycle 4 |
| adoption excludes every cycle's targets, normalised | cycle 5 |
| `tdd target`: five equivalent spellings stored as the collected id | cycle 6 |
| `tdd target` refuses an uncollected id | existing `test_target_refuses_a_name_that_is_not_a_collected_test` |
| unevaluated adoption asks for another advance (both branches) | cycles 7, 8 |
| an adoption the run cannot find is refused: verb, target kept, event | cycle 10 |
| per-file loop unchanged | existing `tests/test_vitest_adapter.py` parsing tests |

## Execution

This plan is executed through `tdd-cli`. **You run every command below yourself** — do not ask the
user to start the run. `tdd run start` records which model is executing, resolved from your own
session; a run started by anyone else attributes this work to the wrong agent.

    git checkout -b issue-163-vitest-adoption-ids     # first, before anything else
    tdd doctor                                        # must report healthy: true
    tdd run start --plan tasks/issue-163-vitest-adoption-ids.md

If the branch already exists, do not force-checkout and do not pick another name: check it out
only if it carries this plan's commit and no unrelated work, otherwise stop and ask.

**Referee.** Use the released `tdd` on `PATH` (`tdd --version`), never an editable install of
this working tree. This plan changes no ledger schema.

Then repeat until done: read `next_action.verb`, do exactly what it says, run `tdd advance`.
Stop when `next_action.terminal` is `true`.

When `next_action.terminal` is `true`, finish the run: render the friction log, commit it, and
raise the PR — see Done-criteria below.

- `tdd advance` is the only command that changes phase. Do not `git add` or `git commit` — the
  tool stages and commits, deriving the file set from the phase.
- The baseline is captured at `run start` and subtracted from later verdicts. The suite is
  green at the plan's base in a fresh worktree (656 passed, 2026-09-25); expect
  `baselines: {tddcli: 0}`.
- Verbs this plan will hit:
  - `write_test`, `write_implementation`, `refactor_or_advance`;
  - `run_sensitivity_check` → `tdd sensitivity begin|check|end`. Cycles 7 and 8 are pins and
    will ask for it.
  - `resolve_blocker` → `tdd blocker --kind <plan_defect|regression|bad_red|tooling>
    --detail '...'`;
  - `confirm_cycle_applicable` on a non-existent cycle → `tdd cycle skip --reason`.

  This plan declares no annotation keys beyond the reserved `plan_defect` and
  `friction_note`.

**Minimal GREEN, per cycle — add this and nothing earlier:**

- cycle 1: `--json` on the batch command, and the JSON-array branch in `_collect_batch`.
  **Keep today's text parse as the fallback.** Cycle 2 removes it.
- cycle 2: delete the text parse; a listing that is not JSON returns `None`.
- cycle 3: the JSON read in `override_isolation`. **Keep today's text read as the fallback.**
  Cycle 4 removes it.
- cycle 4: output that is not JSON fails the gate and names the command.
- cycle 5: the normalised exclusion of every cycle's targets in `_adopt_target`. The harness
  is test code in RED.
- cycle 6: `_qualify` + normalised match in `cmd_target`, storing the collected id.
- cycles 7, 8: pins. Write the test and change no production code.
- cycle 9: the fold only.
- cycle 10: evaluate before recording; on `not_found`, refuse (decision 8).

## Done-criteria

**Before finishing:** run `tdd log render --out tasks/friction-logs/issue-163-vitest-adoption-ids-friction.md` and `tdd metrics`. Report the plan-fidelity section — declared vs delivered vs skipped — and every integrity event. Do not narrate what the ledger already records.

Then commit the friction log and raise the PR:

    git add tasks/friction-logs/issue-163-vitest-adoption-ids-friction.md
    git commit -m "docs: friction log for issue-163-vitest-adoption-ids"

Then invoke the **`raise-pr` skill** (`/raise-pr`), which runs the quality gates, pushes the
branch and opens the PR against `main`. Do not push or call the GitHub API by hand. If a gate
fails, fix it and re-run the skill — a failed gate is work, not a reason to hand back.

The PR body says `Closes #163` and lists the two findings under "Deliberate scope cuts" for
the user to file.

Docs are deliverables. Each of these must be non-empty, or the PR body says which cycle
dropped it and why:
- `git diff --stat origin/main -- README.md` (cycles 1, 4)
- `git diff --stat origin/main -- docs/PRD.md` (cycles 1, 4, 5, 6, 10)
- `git diff --stat origin/main -- docs/harness-integration.md` (cycles 6, 10)
- `git diff --stat origin/main -- CHANGELOG.md` (cycles 1, 4, 5, 6, 10)

Nothing visual changes (CLI JSON envelopes only), so no demo recording is required.
