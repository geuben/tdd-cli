---
closes: 253
cycles:
  - n: 1
    project: tddcli
    title: "tdd doctor lists only the failing checks by default; --all lists every check"
    test: "tests/test_doctor_output.py::test_doctor_lists_only_the_failing_checks_by_default"
    stub_expected: ["src/tddcli/cli.py"]
    files: ["src/tddcli/cli.py"]
    modifies_tests:
      - "tests/test_doctor_attribution.py::test_doctor_does_not_check_node_modules_for_a_pytest_project"
      - "tests/test_doctor_attribution.py::test_doctor_passes_gradle_wrapper_check_when_present"
      - "tests/test_doctor_attribution.py::test_doctor_does_not_check_wrapper_for_a_pytest_project"
      - "tests/test_doctor_attribution.py::test_doctor_flags_a_default_suite_that_reaches_override_files"
      - "tests/test_doctor_blockers.py::test_dirt_outside_every_declared_root_does_not_block"
      - "tests/test_doctor_blockers.py::test_doctors_own_probe_residue_does_not_block"
      - "tests/test_doctor_blockers.py::test_an_artifact_needs_only_one_of_check_or_regenerate"
      - "tests/test_doctor_blockers.py::test_doctor_notes_a_virtual_env_outside_every_project_root"
      - "tests/test_executor_attribution.py::test_doctor_reports_executor_identity"
      - "tests/test_init_skill.py::test_doctor_checks_the_driving_skills_declared_versions"
      - "tests/test_named_leases_and_timeout.py::test_doctor_timeout_check_passes_when_timeout_is_sufficient"
      - "tests/test_end_to_end.py::test_doctor_ignores_nested_checkouts"
      - "tests/test_split_doctor.py::test_single_mode_doctor_says_the_agent_can_reach_the_ledger"
      - "tests/test_split_doctor.py::test_a_split_runner_that_can_act_reports_its_checks_once_and_in_order"
      - "tests/test_split_doctor.py::test_split_doctor_checks_the_drop_to_the_agent"
      - "tests/test_split_doctor.py::test_split_doctor_ledger_check_follows_what_the_agent_can_read"
      - "tests/test_split_doctor.py::test_split_doctor_install_check_follows_what_the_agent_can_write"
      - "tests/test_split_doctor.py::test_a_split_runner_notes_the_agents_virtual_env_not_its_own"
      - "tests/test_split_doctor.py::test_socket_mode_doctor_names_the_source_it_reaches"
    commit_red: "test: tdd doctor must list only the failing checks unless --all"
    commit_green: "feat(doctor): list only the failing checks by default; --all lists every check"
    commit_refactor: "refactor(doctor): tidy the failing-checks filter"
  - n: 2
    project: tddcli
    title: "a split runner that cannot act as the agent counts the one check it ran"
    test: "tests/test_split_doctor.py::test_a_runner_that_cannot_act_counts_the_one_check_it_ran"
    files: ["src/tddcli/cli.py"]
    commit_red: "test: doctor's refused-hop reply must carry checks_run"
    commit_green: "feat(doctor): checks_run on the runner's refused-hop reply"
    commit_refactor: "refactor(doctor): tidy the refused-hop reply"
  - n: 3
    project: tddcli
    title: "tdd doctor counts every check it ran, filtered or not"
    test: "tests/test_doctor_output.py::test_doctor_counts_every_check_it_ran_in_both_modes"
    files: ["src/tddcli/cli.py", "docs/PRD.md", "README.md", "docs/harness-integration.md", "docs/split-runner.md", "CHANGELOG.md"]
    commit_red: "test: tdd doctor must count every check it ran"
    commit_green: "feat(doctor): result.checks_run counts every check doctor ran"
    commit_refactor: "docs: doctor's failing-checks default, --all and checks_run in the PRD, README, guides and changelog"
  - n: 4
    project: tddcli
    pin_cycle: true
    title: "tdd doctor writes no command_timing line unless TDD_TIMING is set, with or without --all"
    test: "tests/test_timing_visibility.py::test_doctor_writes_no_command_timing_unless_asked_for"
    files: []
    commit_pin: "test: pin that doctor writes no command_timing unless TDD_TIMING is set"
---

# Issue 253: `tdd doctor` lists only the failing checks by default

## Context

Issue #253. `tdd doctor` prints every check it ran, passing or failing. On a repo with
several projects a healthy run is a few thousand tokens, and the line an agent needs
(which check failed, and why) is a small part of it. Agents re-run doctor through
`| tail`, `| grep` or an inline `python3 -c` to find it, which repeats every probe,
including the slow collection ones, and costs a turn.

The issue asks for:

- by default, only each failing check, with its `detail` and `project`, plus the overall
  `healthy` verdict and `next_action` (cycle 1);
- on a healthy repo, the verdict and a count of the checks run (cycle 3; cycle 2 counts
  them on the split runner's early return);
- the full report behind a flag (cycle 1, through the 19 tests it moves to the flag);
- no `command_timing` lines in `tdd doctor 2>&1` unless the verbose mode is on (cycle 4,
  a pin: it already holds).

Everything lands in `cmd_doctor` and `build_parser` in `src/tddcli/cli.py`.
`_doctor_checklist`'s recorder is unchanged. It keeps recording every check, and the filter
applies to what is returned.

`cmd_doctor` has three returns, and the plan covers each:

| Return | When | `result` today | Filter | `checks_run` |
|---|---|---|---|---|
| the refused hop | split runner, `_drop_to_the_agent` failed | `checks` (only `runs as the agent`, failing), `projects: {}`, `healthy: false`, `mode: "split"` | nothing to drop (its one check fails) | cycle 2 |
| invalid config | `config_mod.ConfigError` from `config_mod.load` | `checks` only (`worktree resolvable` passing, `tdd.toml valid` failing); `next_action` is `null` | cycle 1 | cycle 3 |
| the final return | everything else | `checks`, `projects`, `healthy`, `mode` | cycle 1 | cycle 3 |

## Design decisions (locked)

1. **The flag is `tdd doctor --all`; the count is `result.checks_run`.** *Decided by a person:*
   the owner's answer "1A, 2B" ([comment](https://github.com/geuben/tdd-cli/issues/253#issuecomment-6782297475))
   to the questions in [the needs-decision comment](https://github.com/geuben/tdd-cli/issues/253#issuecomment-6782127619).
   `checks_run` is the number of checks doctor recorded (`len(checks)` before filtering), in
   both modes and at all three returns.

2. **By default only checks with `ok: false` are listed. Every passing check, notices
   included, appears only with `--all`.** *Decided by a person* (same answer, option 2B).
   That includes the always-passing notices: `executor identity` (even when its source is
   `unknown`), `VIRTUAL_ENV` (even a foreign one), `ledger isolation`, a `driving skill
   version` that declares nothing, and a passing `worktree clean` that lists unrelated paths.
   No `notice` field is added, and no notice becomes a failure. The PRD, README and guides
   that promise these notices are reworded to say "with `--all`" (cycle 3's refactor
   phase).

3. **The output shape is unchanged apart from the filter and the new key.** *Settled by the
   issue* ("The JSON shape of what is printed can stay the same, with the passing checks
   left out") *and by R8.4*, which keeps stdout a single JSON envelope. So "a single line
   saying so" in the issue is a short envelope with `checks: []`, not plain text. Each listed
   check keeps its keys (`check`, `ok`, `detail`, `project` when set). `ok`, `healthy`,
   `mode`, `projects` (the per-project `ok` map, computed from every check), the exit code
   and `next_action` are unchanged. The invalid-config return keeps `next_action: null` and
   gains no `healthy`/`mode`/`projects`: the issue does not ask for that, and adding it is
   not part of this plan.

4. **One filter, at every return that has a passing check to drop.** *Settled by
   convention.* The rule is `[c for c in checks if not c["ok"]]` unless `args.all`. Cycle 1's
   test covers both the final return and the invalid-config return, so neither is left to
   chance. The refused-hop return has only its one failing check, so nothing changes there.
   `projects` and `ok` are computed from the **unfiltered** list, as today.

5. **`checks_run` counts the unfiltered list, at every return.** *Settled by convention*
   (one rule for every return, as decision 4). The value is `len(checks)` taken before the
   filter. Cycles 2 and 3 test it at each return, each against an independently observed
   number: 1 (the one check the refused hop records), and the length of the `--all`
   listing of the same repo.

6. **`command_timing` stays where it is: off unless `TDD_TIMING=1`, and `--all` does not
   turn it on.** *Settled by evidence.* `run_command` in `src/tddcli/adapters/base.py` emits
   `command_timing` only under `TIMING_ENV` (PRD R8.4, §8's timing paragraph). Run here,
   the released `tdd` 0.19.0's `tdd doctor` wrote 0 bytes to stderr. The acceptance
   criterion already holds, so cycle 4 pins it, for both `doctor` and `doctor --all`. R8.4
   makes `TDD_TIMING` the only switch, and
   `tests/test_timing_visibility.py::test_doctor_probes_are_labelled_as_doctor` keeps
   covering doctor's timing when it is on.

7. **The flag's mechanism: `s.add_argument("--all", action="store_true", help=...)` on
   the `doctor` subparser.** *Settled by convention:* every verb flag in `build_parser` is
   declared on its subparser this way (`init --force`, `plan paths --json`).
   - **Accepted:** `tdd doctor --all`.
   - **Also accepted, as for every flag in this parser:** argparse's prefix abbreviation
     (`--al`). This is argparse's default (`allow_abbrev`), not something this plan adds,
     and it is not pinned.
   - **Rejected:** `tdd --all doctor`, because the top-level parser has no `--all`. argparse
     exits 2 with empty stdout, as for any verb flag placed before its verb. This is not
     pinned either: it is loud, and it is argparse's behaviour, not this plan's.
   - **The trap:** argparse names the attribute after the flag, `args.all`. Read it as
     `args.all`, never through `getattr(args, "all", False)`. Every caller of `cmd_doctor`
     goes through the `doctor` subparser, so the attribute always exists. A `getattr` with
     a default would hide a typo in the flag's name.

8. **Split mode needs no forwarding change.** *Settled by evidence.* `main` parses argv on
   the client first, then `runner_mod.forward` passes it to the runner verbatim, so the
   runner parses `--all` itself. A runner whose install is older than the client's rejects
   the unknown flag (argparse exits 2). The CHANGELOG entry therefore carries an "upgrade
   the runner's install with or before the agent's" line. *Settled by convention:* 0.17.0
   and 0.18.0 carried the same kind of line for the ledger service. A ledger-service guest
   runs doctor locally and makes no new ledger read, so `GUEST_READS` and `service.py` are
   untouched.

9. **The test-side blast radius is 19 test functions (22 test ids with parameters) in 7
   files. Each one moves to `--all`, and no assertion changes.** *Settled by evidence:* a
   simulation in a scratch worktree of `origin/main`. Filtering the final return and the
   invalid-config return broke exactly these 22 and nothing else (880 others passed). Each
   one reads a passing check by name. Adding `"--all"` to every `run_cli(..., "doctor")`
   call inside those functions, and inside `test_split_doctor.py`'s `_probe` helper (used by
   the three `CLIENTS`-parametrised tests), made all 22 pass again with the filter in place.
   No other test needed a change. The list is cycle 1's `modifies_tests`. Re-derive it with
   the command in cycle 1.

10. **Docs move with the code, in cycle 3's refactor phase.** *Settled by convention:*
    #249 and #231 put docs and the CHANGELOG in their last standard cycle. `CHANGELOG.md` is
    hand-edited under `## [Unreleased]` (`RELEASING.md`). The repo's root is the `tddcli`
    project root, so every doc is a cycle `files` entry, not an `ancillary_files` entry
    (`.claude/plan-issue.md`). The exact sites are listed under cycle 3.
    `examples/skills/tdd-handoff/SKILL.md` and `examples/plan.md` only read
    `healthy: true` or run plain `tdd doctor`, and `examples/skills/tdd-drive/README.md`
    describes the skill-drift *failure*, which is still listed. None of them changes.

11. **No schema, envelope or verb-set change.** *Settled by evidence.* Nothing touches the
    ledger, so `SCHEMA_VERSION` is unchanged and the referee needs no freezing. `result`'s
    contents are per-verb, so `envelope_version` and `verb_set_version` are unchanged.
    Nothing under `.github/workflows/` is touched (no workflow runs `tdd doctor`).

12. **Consumers outside this repo.** *Settled by convention*
    (`.claude/plan-issue/render-friction-log-consumers.md`). The user-level
    `implement-issue` and `plan-issue` skills read `healthy` and the failing checks, which
    keep their shape. The PR body names geuben/dispatch so its owner can check whether it
    parses passing checks, which would then need `--all`.

## Deliberate scope cuts (do not build)

- **Cutting a release.** Premise: *the run cannot reach it*. Per `RELEASING.md` a release
  is its own PR, then a tag and a GitHub Release. This run delivers the change and its
  `## [Unreleased]` entry.

No other cut. Every acceptance criterion in the issue has a cycle:

| Acceptance criterion | Cycle |
|---|---|
| healthy repo: the verdict and a pass count, not every check | 3 (`checks == []` and `checks_run`), with the verdict unchanged (decision 3) |
| failing check: its name, project and detail, and `next_action`, without the passing checks | 1 |
| `tdd doctor --all` prints today's full report | 1, through the 22 test ids moved to `--all` (for example `test_a_split_runner_that_can_act_reports_its_checks_once_and_in_order` asserts the full ordered list) |
| `tdd doctor 2>&1` has no `command_timing` lines unless the verbose mode is on | 4 (pin) |

## Cycles

### Cycle 1: by default doctor lists only the failing checks; `--all` lists every check

**Behaviour.** Without `--all`, `result.checks` holds only the checks with `ok: false`, at
the final return and at the invalid-config return. With `--all` it holds every check, as
today.

**Stub (`stub_expected: src/tddcli/cli.py`), in RED.** In `build_parser`, on the `doctor`
subparser, before `s.set_defaults(fn=cmd_doctor)`:

```python
s.add_argument("--all", action="store_true", help="also list the checks that passed")
```

Do not read it in `cmd_doctor` yet. This is a signature stub. Without it, every
`doctor --all` call in the moved tests exits 2 with empty stdout. `conftest.run_cli` would
then die in `json.JSONDecodeError`, and so would the RED.

**Test, a new file `tests/test_doctor_output.py`.** Give it a module docstring saying what
it guards: doctor's default output lists only what an agent must act on, and `--all` lists
the rest (issue #253). Put a module-level helper in it, which cycle 3 reuses:

```python
def _copy(repo: Path, tmp_path: Path, name: str, edit=None) -> Path:
    """An independent copy of `repo` (the ledger is keyed by path), with `edit` applied
    to its tdd.toml and committed, so `worktree clean` stays out of the answer."""
    root = Path(shutil.copytree(repo, tmp_path / name, symlinks=True))
    if edit is not None:
        toml = root / "tdd.toml"
        toml.write_text(edit(toml.read_text()))
        git(root, "commit", "-qam", name)
    return root
```

(`shutil`, `Path`, and `git, run_cli` from `conftest`.)

`test_doctor_lists_only_the_failing_checks_by_default(repo, tmp_path)` makes two copies,
both before any doctor call:

- `"no test_paths"`: `lambda t: t.replace('test_paths = ["tests/"]\n', "")`. The project
  then fails exactly one check, `test_paths declared`, and passes every other.
- `"bad timeout"`: `lambda t: t + 'timeout    = "slow"\n'`. `config_mod.load` raises
  `ConfigError` (`project 'backend': timeout must be an integer`), so doctor takes the
  invalid-config return.

For each, run `run_cli(root, "doctor")` and record
`([(c["check"], c.get("project"), c["detail"]) for c in out["result"]["checks"]], (out["next_action"] or {}).get("verb"))`.
Then make one assertion:

```python
assert said == {
    "no test_paths": (
        [("test_paths declared", "backend",
          "add `test_paths` to [project.backend] in tdd.toml — without it no suite can be"
          " discovered for this project")],
        "resolve_blocker",
    ),
    "bad timeout": (
        [("tdd.toml valid", None, "project 'backend': timeout must be an integer")],
        None,
    ),
}
```

The expected details are the literal strings `cmd_doctor` and `config.load` produce today
(probed). They are not derived from the code under test.

**Moving the 22 test ids to `--all`, in RED, alongside the new test.** In each function in
`modifies_tests`, change every `run_cli(<repo>, "doctor")` call to
`run_cli(<repo>, "doctor", "--all")`, and `run_cli(repo, "--agent-context-stdin", "doctor")`
to `run_cli(repo, "--agent-context-stdin", "doctor", "--all")`. Do the same for both calls in
`_probe` in `tests/test_split_doctor.py`, which the three `CLIENTS`-parametrised tests in
the list go through. Change nothing else: no assertion, no helper's logic, no other test.
They keep passing in RED, because the stub accepts the flag and ignores it. Re-derive the
list before editing, and report any difference as a `tdd note`:

    rg -n '"doctor"' tests/ | rg -v 'test_doctor_output|test_timing_visibility'

The expected hits are in the 19 functions listed, plus calls in tests that are **not**
moved because they read a *failing* check (it stays listed). For example,
`test_doctor_blockers.py`'s `test_dirt_inside_a_project_root_blocks_and_names_the_path`,
and `test_doctor_attribution.py`'s `repo_broken` tests. Leave those as they are.

**Production target.** `cmd_doctor` in `src/tddcli/cli.py`:

- At the final return, list `checks` filtered to `not c["ok"]` unless `args.all`, after
  `ok = all(c["ok"] for c in checks)`. `projects` is filled earlier from the unfiltered
  list, so it is unchanged.
- At the invalid-config return, apply the same filter to its `checks`.

Not `checks_run`, and not the refused-hop return.

**EXPECTED FAILURE** (probed with the stub in place): ``AssertionError: assert {'no test_pat...ger")], None)} == {...}``,
where the differing items show every passing check listed. For `"no test_paths"` that is
`('worktree resolvable', None, '<tmp>/no-test-paths')`, `('tdd.toml valid', None, '1 projects')`, ... `('worktree clean', None, '')`.
For `"bad timeout"` it is `('worktree resolvable', None, '<tmp>/bad-timeout')` ahead of the failing
`tdd.toml valid`.

### Cycle 2: the split runner's refused-hop reply carries `checks_run`

**Behaviour.** When a split runner cannot act as the agent, `cmd_doctor` returns early with
its one failing check, and `result.checks_run` is `1`.

**Test,** appended to `tests/test_split_doctor.py` (it reuses that file's `_refuse_sudo`,
`agent_context` and `run_cli`):

```python
def test_a_runner_that_cannot_act_counts_the_one_check_it_ran(
    repo, split_runner, monkeypatch, tmp_path
):
    """A refused hop stops doctor before anything else is probed: one check ran."""
    agent_context(monkeypatch, umask=0o022, **_refuse_sudo(split_runner, tmp_path))
    result = run_cli(repo, "--agent-context-stdin", "doctor")["result"]
    said = ([c["check"] for c in result["checks"]], result.get("checks_run"))
    assert said == (["runs as the agent"], 1)
```

`1` is not derived from the code. It is the one check this path records:
`_drop_to_the_agent` runs before anything else, and `test_split_doctor_checks_the_drop_to_the_agent`
already asserts `len(refused["result"]["checks"]) == 1`.

**Production target.** `cmd_doctor`'s refused-hop return: add `"checks_run": len(checks)`
to its `result`. Add it **there only**. Not at the invalid-config return or the final
return: cycle 3 adds those, and its test must fail first.

**EXPECTED FAILURE** (probed): ``AssertionError: assert (['runs as the agent'], None) == (['runs as the agent'], 1)``.

### Cycle 3: doctor counts every check it ran, filtered or not

**Behaviour.** At the final return and the invalid-config return, `result.checks_run` is the
number of checks doctor ran. That is the length of the `--all` listing, with or without
`--all`. On a healthy repo the default `result.checks` is `[]`.

**Test,** in `tests/test_doctor_output.py` (reusing `_copy`):

```python
def test_doctor_counts_every_check_it_ran_in_both_modes(repo, tmp_path):
    roots = {
        "healthy": _copy(repo, tmp_path, "healthy"),
        "bad timeout": _copy(repo, tmp_path, "bad-timeout", lambda t: t + 'timeout    = "slow"\n'),
    }
    failing = {"healthy": 0, "bad timeout": 1}
    said, expected = {}, {}
    for name, root in roots.items():
        short = run_cli(root, "doctor")["result"]
        full = run_cli(root, "doctor", "--all")["result"]
        said[name] = (len(short["checks"]), short.get("checks_run"), full.get("checks_run"))
        expected[name] = (failing[name], len(full["checks"]), len(full["checks"]))
    assert said == expected
```

The expected count is the length of the `--all` list, observed from the output, not
computed by the code under test. A `checks_run` taken after the filter gives 0 and 1 by
default, and fails. The healthy copy is the `repo` fixture untouched, which doctor reports
healthy. Under `uv run`, `VIRTUAL_ENV` is set and its notice is one of the counted checks:
14 checks in the probe. The test does not hard-code that number.

**Production target.** `cmd_doctor`: `"checks_run": len(checks)` at the invalid-config
return and at the final return, taken from the unfiltered list (before cycle 1's filter).
The refactor phase may fold the three returns' filter-and-count into one small helper if
that reads better. It must not change behaviour: the suite, including cycles 1 and 2's
tests, is the guard.

**EXPECTED FAILURE** (probed before cycle 1 as `{'healthy': (14, None, None)} != {'healthy': (0, 14, 14)}`
and `{'bad timeout': (2, None, None)} != {'bad timeout': (1, 2, 2)}`). After cycle 1's GREEN,
the first element becomes `0` and `1`, and the run fails on the `None`s:
``AssertionError: assert {'healthy': (0, None, None), 'bad timeout': (1, None, None)} == {'healthy': (0, N, N), 'bad timeout': (1, 2, 2)}``.
Here `N` is the `--all` count. The full-suite simulation after cycle 1's change showed this
test failing, but did not print its message, so the `0`/`1` are inferred from the filter.

**Refactor phase: the docs and the CHANGELOG** (no production code beyond the optional
helper above). Each site, by anchor:

- `docs/PRD.md`
  - §5, the paragraph starting "`tdd doctor` reports an informational `executor identity`
    check": it is listed by `tdd doctor --all`. Plain `tdd doctor` lists failing checks only
    (#253).
  - §8.1's `tdd doctor` table row: name `[--all]`. Say that by default `result.checks`
    lists only the failing checks (each with `detail` and `project`), and that `--all`
    lists every check. Say that `result.checks_run` counts the checks run, in both modes.
    Say that `healthy`, `mode`, `projects`, `ok`, the exit code and `next_action` are
    unchanged, and that `--all` does not turn on `command_timing` (R8.4: `TDD_TIMING` is
    the switch).
  - §8.1's "Clean enough" paragraph: "Dirt anywhere else is named in the passing check's
    `detail`" becomes "... visible with `--all`".
  - §8.1's `VIRTUAL_ENV` paragraph: the check is listed with `--all`.
  - R13.3a: "`tdd doctor` must say so (`mode: single`, the `ledger isolation` notice)".
    `mode` is in every reply. The notice is listed with `--all`.
- `README.md`
  - The Commands table row `` `tdd init [...]` / `tdd doctor` ``: becomes
    `` `tdd doctor [--all]` ``, "environment preflight: failing checks only; `--all` lists
    every check".
  - The "Unreadable baseline (R9.5j)" paragraph: "`tdd doctor` notes a foreign
    `VIRTUAL_ENV`" becomes "`tdd doctor --all`".
  - The ledger section's "`tdd doctor` reports `mode: single` and says so": the saying is
    the `ledger isolation` check, listed with `--all`.
- `docs/harness-integration.md`: "`tdd doctor` always reports an informational `executor
  identity` check" becomes "`tdd doctor --all` always lists ...".
- `docs/split-runner.md`
  - The opening paragraph's "says so in its `ledger isolation` check": listed by
    `tdd doctor --all`.
  - "Verify it" step 1: `tdd doctor --all` (the three checks are `ok`, so plain `doctor`
    lists none of them).
  - The ledger-socket section's "`tdd doctor`'s `ledger reachable` check": `tdd doctor --all`.
- `CHANGELOG.md`: under `## [Unreleased]`, a `### Changed` heading, then this entry:

  > - **`tdd doctor` lists only the failing checks by default** (#253). `result.checks` now
  >   holds only checks with `ok: false`, each with its `detail` and `project`. On a healthy
  >   repo it is `[]`. A new `result.checks_run` counts every check doctor ran.
  >   `healthy`, `mode`, `projects`, `ok`, the exit code and `next_action` are unchanged.
  >   `tdd doctor --all` lists every check, as before. That includes the notices that always
  >   pass (`executor identity`, `VIRTUAL_ENV`, `ledger isolation`, `driving skill
  >   version`), so anything that reads a passing check needs `--all`. `command_timing`
  >   stays off unless `TDD_TIMING=1`, with or without `--all`. In split mode, upgrade the
  >   runner's install with or before the agent's: an older runner rejects `--all`.

### Cycle 4 (pin): doctor writes no `command_timing` line unless `TDD_TIMING` is set

**Behaviour.** Without `TDD_TIMING`, neither `tdd doctor` nor `tdd doctor --all` writes a
`command_timing` line to stderr. This already holds (decision 6), so this is a pin: the
test **must pass on arrival**.

**Test,** appended to `tests/test_timing_visibility.py` (reusing its `_lines`, `base` and
`run_cli`):

```python
def test_doctor_writes_no_command_timing_unless_asked_for(repo, capsys, monkeypatch):
    """Issue #253: `tdd doctor 2>&1` stays short. Neither mode turns timing on."""
    monkeypatch.delenv(base.TIMING_ENV, raising=False)
    oks = [run_cli(repo, "doctor")["ok"], run_cli(repo, "doctor", "--all")["ok"]]
    assert (oks, _lines(capsys.readouterr().err, "command_timing")) == ([True, True], [])
```

**Production target:** none (`files: []`). It guards `run_command` in
`src/tddcli/adapters/base.py` and `cmd_doctor`.

**Probe:** it passed on arrival with the `--all` stub in place, so it is a pin.

**Sensitivity check** (the tool asks for one): in `run_command`, change
`if os.environ.get(TIMING_ENV):` to `if True:`. The test must fail, listing the
`command_timing` lines. Then restore the line.

## Fakes and seams

There are no new fakes. Split mode goes through the existing `split_runner` fixture
(`conftest.sudo_shim`) and its `refuse()`, as in `test_split_doctor_checks_the_drop_to_the_agent`.
Each repo copy is an independent repo and ledger (`.claude/plan-issue/testing-execution-counter-flake.md`).

| Double | Fake behaviour | Real behaviour | Untested production path |
|---|---|---|---|
| `sudo_shim` (`refuse()`) | refuses every command, without changing uid | sudo refusing the hop | the uid change itself. *Acceptable:* it is the existing seam, and `docs/split-runner.md`'s "Verify it" covers the real sudo |

## Execution

This plan is executed through `tdd-cli`. **You run every command below yourself** — do not ask the
user to start the run. `tdd run start` records which model is executing, resolved from your own
session; a run started by anyone else attributes this work to the wrong agent.

    git checkout -b issue-253-doctor-failing-checks-only   # first, before anything else
    tdd doctor                                  # healthy, or failing only for projects this plan cannot reach
    tdd run start --plan tasks/issue-253-doctor-failing-checks-only.md   # captures baselines, opens cycle 1

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
  at the plan's base: 902 passed in a fresh worktree of `origin/main` on 2026-11-10. Expect
  `baselines: {tddcli: 0}`.
- The referee is the released `tdd` on `PATH` (the note at the top of `tdd.toml`), never
  `uv run tdd`. It is 0.19.0 and has none of this plan's behaviour, so the `tdd doctor`
  above prints the full report. `SCHEMA_VERSION` does not change.
- Every RED, GREEN and REFACTOR edit must pass `uv run ruff check` and `uv run mypy` (the
  close sweep's gates). Annotate `_copy` as shown (`edit` may stay unannotated or be
  `Callable[[str], str] | None`).
- Verbs this plan will hit:
  - `write_test`, `write_implementation`, `refactor_or_advance`.
  - `run_sensitivity_check` → `tdd sensitivity begin|check|end`. Cycle 4 is a pin and will
    ask for it: use the mutation the cycle names, then restore it. A standard RED that
    pre-passes (most likely cycle 3, if cycle 2's GREEN put `checks_run` on every return)
    also asks: mutate the increment that cycle added. Then record the pre-pass with
    `tdd note`.
  - `annotate_cycle` → `tdd annotate --key --value`. This plan declares no keys of its own;
    `plan_defect` and `friction_note` are reserved.
  - `resolve_blocker` → `tdd blocker --kind <plan_defect|regression|tooling> --detail '...'`.
    A pin that fails on arrival (cycle 4) is `plan_defect`. So is a test outside cycle 1's
    `modifies_tests` that breaks under the filter: stop, do not edit it.
  - `confirm_cycle_applicable` on a non-existent cycle → `tdd cycle skip --reason`.

**Minimal GREEN, per cycle — add this and nothing earlier:**

- **Cycle 1:**
  - RED: the `--all` stub, and the 22 test ids moved to `--all`;
  - GREEN: the filter at the final return and the invalid-config return, honouring
    `args.all`.

  Not `checks_run`.
- **Cycle 2:** `"checks_run": len(checks)` at the refused-hop return only.
- **Cycle 3:** `checks_run` at the invalid-config and final returns, from the unfiltered
  list. Its refactor phase carries the docs and the CHANGELOG.
- **Cycle 4:** a pin. Only its test.

## Done-criteria

**Before finishing:** run `tdd log render --out tasks/friction-logs/issue-253-doctor-failing-checks-only-friction.md` and `tdd metrics`. Report the plan-fidelity section — declared vs delivered vs skipped — and every integrity event. Do not narrate what the ledger already records.

Then commit the friction log and raise the PR:

    git add tasks/friction-logs/issue-253-doctor-failing-checks-only-friction.md
    git commit -m "docs: friction log for issue-253-doctor-failing-checks-only"

Then invoke the **`raise-pr` skill** (`/raise-pr`), which runs the quality gates, pushes the
branch and opens the PR against `main`. Do not push or call the GitHub API by hand. If a gate
fails, fix it and re-run the skill — a failed gate is work, not a reason to hand back.

The PR body says `Closes #253`. Cycle 3's refactor phase owns the docs:

- `git diff --stat origin/main -- docs/PRD.md` must be non-empty, or the PR body says why.
- `git diff --stat origin/main -- README.md` must be non-empty, or the PR body says why.
- `git diff --stat origin/main -- docs/harness-integration.md` must be non-empty, or the PR body says why.
- `git diff --stat origin/main -- docs/split-runner.md` must be non-empty, or the PR body says why.
- `git diff --stat origin/main -- CHANGELOG.md` must be non-empty, or the PR body says why.
- `git diff origin/main -- src/tddcli/ledger.py` must be empty (decision 11).

The visible change is JSON output, so no demo recording is required. In the PR body:

- paste `uv run tdd doctor` and `uv run tdd doctor --all` from this checkout. Use the
  working tree's build here, not the referee, because the referee is 0.19.0. Trim the
  `--all` one to its first few checks.
- name the readers outside this repo: geuben/dispatch, which should check whether it
  parses passing checks and, if so, add `--all`. The `implement-issue` and `plan-issue`
  skills read only `healthy` and failing checks (decision 12).
- repeat the split-mode upgrade note from the CHANGELOG.
