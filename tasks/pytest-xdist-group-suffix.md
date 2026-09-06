---
cycles:
  - n: 1
    project: tddcli
    title: "pytest run() matches a grouped target whose report node id carries xdist's @<group> suffix"
    test: "tests/test_pytest_xdist_group.py::test_pytest_run_matches_target_reported_with_xdist_group_suffix"
    files: ["src/tddcli/adapters/pytest_adapter.py"]
    commit_red: "test: a target reported as nodeid@group under --dist loadgroup must still be found"
    commit_green: "fix: strip xdist's @<group> suffix from pytest report node ids before matching"
  - n: 2
    project: tddcli
    title: "an @ inside a parametrised id's brackets is not mistaken for the xdist suffix"
    test: "tests/test_pytest_xdist_group.py::test_pytest_run_keeps_at_sign_inside_parametrised_id"
    files: ["src/tddcli/adapters/pytest_adapter.py"]
    commit_red: "test: a parametrised id containing @ inside [...] must survive suffix stripping"
    commit_green: "fix: only a trailing @<group> after the last bracket is xdist's suffix"
ancillary_files:
  - "CHANGELOG.md"
  - "docs/PRD.md"
annotation_keys: []
---

# pytest adapter: canonicalise xdist `--dist loadgroup` node ids

## Context

pytest-xdist's loadgroup scheduler reports a test marked
`@pytest.mark.xdist_group("<group>")` under the node id `<nodeid>@<group>`, and
pytest-json-report records that spelling. `PytestAdapter.run` matches the declared target
by exact equality against `test["nodeid"]` and qualifies passed/failed ids verbatim, so in a
project whose `addopts` carries `--dist loadgroup` every grouped target is reported missing
even though it is collected and passes. Seen 2026-09-06 in a downstream project: the
executor filed a `plan_defect` blocker for a correct test. The tracking issue could not be
filed from this session (the token cannot create issues on this repo); the PR carries the
description.

## Design decisions (locked)

- Canonicalise on the **report side**, when node ids are read from the JSON report and from
  `--collect-only` output, so `passed`, `failed`, the target match and collected ids all use
  the plain id. Declared ids stay as written; `normalise_id` (R10.8) is untouched because the
  divergence is in the runner's output, not in human spelling.
- The suffix is the last `@` **after the last `]`** (or anywhere when there is no `]`).
  pytest function names cannot contain `@`, and parametrised values live inside `[...]`, so an
  `@` outside brackets can only be xdist's. `test_x[user@example.com]` is left intact;
  `test_x[user@example.com]@group` becomes `test_x[user@example.com]`.

## Scope cuts

- No change to `normalise_id`: a planner who writes the suffixed id into a plan still gets
  `not_found`. Premise: plans are written from `--collect-only` output, which has no suffix.
- No change to other adapters.

## Cycles

### Cycle 1

`tests/test_pytest_xdist_group.py::test_pytest_run_matches_target_reported_with_xdist_group_suffix`
builds a pytest project with `project_with`-style registry text, fakes `run_command` to write a
report whose single test has `"nodeid": "tests/test_a.py::test_a@shared_db"`, calls
`adapter.run("backend::tests/test_a.py::test_a")`, and asserts `target_outcome == "passed"`
and `passed == ["backend::tests/test_a.py::test_a"]`.

Production target: `PytestAdapter.run` in `src/tddcli/adapters/pytest_adapter.py`, via a new
module-level `_strip_xdist_group(nodeid)` applied where `test["nodeid"]` is read (and in
`_nodeids`).

EXPECTED FAILURE: `AssertionError: assert 'not_found' == 'passed'`.

### Cycle 2

`tests/test_pytest_xdist_group.py::test_pytest_run_keeps_at_sign_inside_parametrised_id`
reports `"nodeid": "tests/test_a.py::test_a[user@example.com]@shared_db"` and
`"tests/test_a.py::test_b[user@example.com]"` (ungrouped), targets
`backend::tests/test_a.py::test_a[user@example.com]`, and asserts the target passed and
`passed == ["backend::tests/test_a.py::test_a[user@example.com]",
"backend::tests/test_a.py::test_b[user@example.com]"]`.

Production target: `_strip_xdist_group` — strip only when the last `@` follows the last `]`.

EXPECTED FAILURE: with cycle 1's minimal `split("@", 1)[0]`, both ids are truncated to
`tests/test_a.py::test_a[user` / `test_b[user`, so `target_outcome == "not_found"`.

## Execution

    git checkout fix/pytest-xdist-group-suffix
    tdd doctor
    tdd run start --plan tasks/pytest-xdist-group-suffix.md

Then read `next_action.verb`, do it, `tdd advance`, until `next_action.terminal` is true.
Ancillary edits (CHANGELOG `Unreleased`, PRD R10.8 note) land in cycle 2's GREEN.

## Done-criteria

`tdd log render --out tasks/friction-logs/pytest-xdist-group-suffix-friction.md`, then
`uv run pytest -q` and `uv run ruff check src tests` clean, then push and open the PR.
