# Implementation Friction Log: tasks/issue-114-init-skill-scaffold.md

- Run: 2
- Executor: claude-opus-5-5 (source: claimed)
- Plan blob: `c68264cafdf7229d140a82cf0a17aa0113e3dd36` (declared)
- Started: 2026-10-29T23:27:07.785911+00:00  Ended: 2026-10-30T00:08:37.808622+00:00  Outcome: complete
- Baseline failures at start: tddcli=60

## Plan fidelity

- Declared cycles: 16
- Delivered: 16   Skipped: 0
- Never reached: none
- Human interventions: 0

### Cycle 16: the hooks README shows the stanza init writes  _(standard)_
- **Target:** `tddcli::tests/test_init_skill.py::test_the_hooks_readme_shows_the_stanza_init_writes`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `3f4f9beaa` [red] test: the hooks README shows the stanza init writes (1 files)
  - `caafc9963` [green] docs: the hooks README shows tdd init --skill and its stanza (1 files)
  - `72acb1bbb` [refactor] docs: tdd init --skill in the README, harness guide, PRD and changelog (9 files)

### Cycle 15: doctor checks the driving skill's declared versions against the binary's  _(standard)_
- **Target:** `tddcli::tests/test_init_skill.py::test_doctor_checks_the_driving_skills_declared_versions`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `a51889620` [red] test: doctor names a driving skill that has drifted from the binary (1 files)
  - `675b00e95` [green] feat: doctor checks the driving skill's verb_set_version and envelope_version (2 files)

### Cycle 14: --update-skill without --skill is refused as skill_required  _(standard)_
- **Target:** `tddcli::tests/test_init_skill.py::test_update_skill_without_skill_is_refused`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `d9ee1cea6` [red] test: init refuses --update-skill without --skill (1 files)
  - `c849d0f9b` [green] feat: init refuses --update-skill without --skill (1 files)

### Cycle 13: --update-skill replaces a harness file that differs  _(standard)_
- **Target:** `tddcli::tests/test_init_skill.py::test_update_skill_replaces_a_harness_file_that_differs`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `cdf1cd8de` [red] test: init --skill --update-skill replaces a stale skill (1 files)
  - `7dfb709da` [green] feat: tdd init --update-skill (1 files)

### Cycle 12: a harness file that differs is refused as harness_files_differ, with or without --force  _(standard)_
- **Target:** `tddcli::tests/test_init_skill.py::test_a_harness_file_that_differs_is_refused_with_or_without_force`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `4f3ba7eb8` [red] test: init --skill never overwrites a customised harness file (1 files)
  - `3b42d101c` [green] feat: init --skill refuses to overwrite a harness file that differs (1 files)

### Cycle 11: a settings.json that already wires both hooks is reported as wired  _(standard)_
- **Target:** `tddcli::tests/test_init_skill.py::test_settings_that_already_wire_both_hooks_are_reported_as_wired`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `d909b47ac` [red] test: init --skill recognises settings that already wire the hooks (1 files)
  - `77a713f3c` [green] feat: init --skill reports already-wired hooks as wired (2 files)

### Cycle 10: an existing .claude/settings.json is left alone and the stanza is handed over  _(standard)_
- **Target:** `tddcli::tests/test_init_skill.py::test_an_existing_settings_file_is_left_alone_and_the_stanza_handed_over`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `0f8b70736` [red] test: init --skill never edits an existing settings.json (1 files)
  - `628344684` [green] feat: init --skill hands over the hook stanza instead of merging it (1 files)

### Cycle 9: with no .claude/settings.json, init --skill writes one that wires both hooks  _(standard)_
- **Target:** `tddcli::tests/test_init_skill.py::test_init_skill_writes_settings_that_wire_both_hooks`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `ce170ecef` [red] test: init --skill writes settings.json wiring both hooks (1 files)
  - `f19b95e21` [green] feat: init --skill writes .claude/settings.json when there is none (2 files)

### Cycle 8: with --skill an existing tdd.toml is kept, and --force still replaces it  _(standard)_
- **Target:** `tddcli::tests/test_init_skill.py::test_init_skill_keeps_an_existing_tdd_toml_unless_forced`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `93753f337` [red] test: init --skill keeps an existing tdd.toml (1 files)
  - `64a9788e3` [green] feat: init --skill keeps an existing tdd.toml unless --force (1 files)

### Cycle 7: a scaffold missing from the installation is refused as missing_from_install and nothing is written  _(standard)_
- **Target:** `tddcli::tests/test_init_skill.py::test_a_scaffold_missing_from_the_install_is_refused_and_nothing_is_written`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `7bb1a7855` [red] test: init --skill refuses when a shipped file is missing (1 files)
  - `64125c57b` [green] feat: init --skill reports a packaging fault before writing anything (1 files)

### Cycle 6: every file a harness scaffolds is carried into the wheel  _(standard)_
- **Target:** `tddcli::tests/test_init_skill.py::test_every_scaffolded_file_is_carried_into_the_wheel`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `0da16b3d1` [red] test: every scaffolded file is force-included into the wheel (1 files)
  - `af27b82aa` [green] build: ship the Claude Code hook scripts in the wheel (1 files)

### Cycle 5: tdd init --skill claude-code writes the installed Stop and Bash hooks  _(standard)_
- **Target:** `tddcli::tests/test_init_skill.py::test_init_skill_writes_the_installed_hooks`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `2d9f7965b` [red] test: tdd init --skill claude-code writes the installed hooks (1 files)
  - `313a4f07e` [green] feat: init --skill writes the Stop and Bash hooks (1 files)

### Cycle 4: an unknown harness is refused as unknown_harness and nothing is written  _(standard)_
- **Target:** `tddcli::tests/test_init_skill.py::test_an_unknown_harness_is_refused_and_nothing_is_written`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `efdb0aeb6` [red] test: init refuses an unknown harness (1 files)
  - `d8ca78a36` [green] feat: init --skill refuses an unknown harness (1 files)

### Cycle 3: tdd init --skill claude-code writes the installed driving skill  _(standard)_
- **Target:** `tddcli::tests/test_init_skill.py::test_init_skill_writes_the_installed_driving_skill`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `37ec0953e` [red] test: tdd init --skill claude-code writes the installed skill (1 files)
  - `642a1a590` [green] feat: tdd init --skill claude-code writes the driving skill (2 files)

### Cycle 2: the shipped driving skill declares the versions this binary emits  _(standard)_
- **Target:** `tddcli::tests/test_init_skill.py::test_the_shipped_skill_declares_the_versions_this_binary_emits`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `f2532cd7f` [red] test: the shipped tdd-drive skill declares its verb_set_version (1 files)
  - `c701c77c2` [green] feat: tdd-drive declares verb_set_version and envelope_version in its metadata (1 files)

### Cycle 1: extract docs.shipped(path) from Topic.resolve  _(refactor)_
- **Target:** none
- **Projects:** `tddcli`
- **Suite runs by phase:** {'CLOSE_SWEEP': 1}
- **Commits:**
  - `116f2aef5` [refactor] refactor: docs.shipped resolves any shipped file, packaged copy first (1 files)
> **note** _(during AWAITING_REFACTOR)_: run start baselined tddcli=60 failures on the split-mode runner while the same tree passes 722/722 when run locally in the guest (uv run pytest); the plan expected 0. Treating as runner-environment noise: every new test lives in the new tests/test_init_skill.py, and cycle 1's guard tests are also run locally.

## Time

- Wall clock: 41.5 min. Suite: 33.0 min (79%).

| Phase | Suite runs | Suite (min) | Average (s) |
|---|---|---|---|
| AWAITING_TEST | 15 | 0.4 | 1.4 |
| AWAITING_IMPL | 30 | 28.8 | 57.6 |
| CLOSE_SWEEP | 2 | 3.8 | 114.3 |

| Cycle | Wall (min) | Suite (min) | Suite runs |
|---|---|---|---|
| 1 | 4.8 | 2.1 | 1 |
| 2 | 2.6 | 2.3 | 3 |
| 3 | 1.8 | 1.3 | 3 |
| 4 | 2.1 | 1.9 | 3 |
| 5 | 2.3 | 2.0 | 3 |
| 6 | 2.0 | 1.7 | 3 |
| 7 | 2.1 | 1.9 | 3 |
| 8 | 2.5 | 2.0 | 3 |
| 9 | 2.5 | 2.1 | 3 |
| 10 | 2.0 | 1.7 | 3 |
| 11 | 2.6 | 2.1 | 3 |
| 12 | 2.0 | 1.8 | 3 |
| 13 | 2.2 | 2.0 | 3 |
| 14 | 2.3 | 2.1 | 3 |
| 15 | 3.0 | 2.3 | 3 |
| 16 | 4.7 | 3.8 | 4 |

## Executor narrative

_Claims from the executor, unverified by design._

> hardest cycle: 8, which needed cmd_init split into a _write_config helper so the config step could be kept under --skill while plain init's envelope stayed byte-identical. Plan got wrong: baselines expected {tddcli: 0}, but the runner baselined 60 (the suite passes 722/722 locally), and the create_stub verb was never issued for cycles 3/13 because the tool accepted JSONDecodeError as the RED. Deviations: harness.wires() also type-checks non-list event values so a malformed settings.json can never raise. Harness friction: each advance runs the ~2 min suite, ~50 min wall clock across 16 cycles.

