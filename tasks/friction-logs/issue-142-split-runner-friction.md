# Implementation Friction Log: tasks/issue-142-split-runner.md

- Run: 1
- Executor: claude-fable-5-1 (source: transcript)
- Plan blob: `71e250ad5fb5fb623a311492a75bd6b739359a19` (declared)
- Started: 2026-09-21T21:26:15.154411+00:00  Ended: 2026-09-21T22:38:13.291823+00:00  Outcome: complete
- Baseline failures at start: tddcli=0

## Plan fidelity

- Declared cycles: 29
- Delivered: 29   Skipped: 0
- Never reached: none
- Human interventions: 0

### Cycle 29: the split-runner setup guide ships with the binary  _(standard)_
- **Target:** `tddcli::tests/test_docs_command.py::test_the_split_topic_explains_the_sudoers_setup`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `ec6d3b17f` [red] test: the split topic explains the sudoers setup (1 files)
  - `557ff8c4e` [green] docs: split-runner guide, and stop claiming isolation in single mode (7 files)
  - `a6db4bd40` [refactor] refactor: tidy the split-runner docs (2 files)

### Cycle 28: metrics says which runs predate the split  _(standard)_
- **Target:** `tddcli::tests/test_runner_import.py::test_metrics_reports_the_pre_split_marker`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `9657b85c9` [red] test: metrics reports the pre-split marker (1 files)
  - `cd9691b02` [green] feat: metrics carries pre_split_import when the ledger was imported (1 files)

### Cycle 27: runner import is refused on a machine that is not split  _(standard)_
- **Target:** `tddcli::tests/test_runner_import.py::test_import_is_refused_in_single_mode`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `937afb789` [red] test: runner import is refused in single mode (1 files)
  - `1629bcaf2` [green] feat: runner import refuses with not_split outside the runner role (1 files)

### Cycle 26: runner import is refused when an agent calls it  _(standard)_
- **Target:** `tddcli::tests/test_runner_import.py::test_import_is_refused_for_an_agent_caller`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `75c70c8ef` [red] test: runner import is refused for an agent caller (1 files)
  - `906bf1918` [green] feat: runner import is operator-only (1 files)

### Cycle 25: runner import refuses to overwrite a ledger the runner already holds  _(standard)_
- **Target:** `tddcli::tests/test_runner_import.py::test_import_refuses_to_overwrite_an_existing_ledger`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `d18ca8950` [red] test: runner import refuses to overwrite an existing ledger (1 files)
  - `3333e0fae` [green] feat: runner import refuses when the target ledger exists (1 files)

### Cycle 24: runner import copies a legacy ledger and marks its history pre-split  _(standard)_
- **Target:** `tddcli::tests/test_runner_import.py::test_import_copies_the_ledger_and_marks_it_pre_split`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `8d79f2cc7` [red] test: runner import copies a legacy ledger and marks it pre-split (2 files)
  - `1fee41685` [green] feat: tdd runner import (4 files)

### Cycle 23: split-mode doctor's install check follows what the agent can actually write  _(standard)_
- **Target:** `tddcli::tests/test_split_doctor.py::test_split_doctor_install_check_follows_what_the_agent_can_write`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `9800545e5` [red] test: split doctor's install check follows what the agent can write (1 files)
  - `0a53ba153` [green] feat: split doctor probes install writability as the agent (1 files)

### Cycle 22: split-mode doctor's ledger check follows what the agent can actually read  _(standard)_
- **Target:** `tddcli::tests/test_split_doctor.py::test_split_doctor_ledger_check_follows_what_the_agent_can_read`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `9b637c059` [red] test: split doctor's ledger check follows what the agent can read (1 files)
  - `e336ea934` [green] feat: split doctor probes ledger readability as the agent (1 files)

### Cycle 21: split-mode doctor verifies the drop to the agent's uid and names the sudoers line when it fails  _(standard)_
- **Target:** `tddcli::tests/test_split_doctor.py::test_split_doctor_checks_the_drop_to_the_agent`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `867ec2360` [red] test: split doctor checks the drop to the agent's uid (1 files)
  - `f46d6b81b` [green] feat: split doctor probes id -u as the agent (1 files)

### Cycle 20: single-mode doctor reports the mode and stops claiming the ledger is out of reach  _(standard)_
- **Target:** `tddcli::tests/test_split_doctor.py::test_single_mode_doctor_says_the_agent_can_reach_the_ledger`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `a7f1f7822` [red] test: single-mode doctor says the agent can reach the ledger (1 files)
  - `3574c588e` [green] feat: doctor reports mode single and a ledger isolation notice (1 files)

### Cycle 19: a run by an unmapped agent records the agent's claim, labelled claimed  _(standard)_
- **Target:** `tddcli::tests/test_split_identity.py::test_an_unmapped_agent_is_recorded_as_claimed`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `3b320f4fd` [red] test: an unmapped agent is recorded as claimed (1 files)
  - `f8fb6aefc` [green] feat: the runner resolves an unmapped executor on the agent's side and labels it claimed (1 files)

### Cycle 18: a run by a mapped agent records the operator-assigned model  _(standard)_
- **Target:** `tddcli::tests/test_split_identity.py::test_a_mapped_agent_records_the_operator_assigned_model`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `67cc22ab7` [red] test: a mapped agent records the operator-assigned model (1 files)
  - `5baad3d45` [green] feat: the runner resolves executor identity from its [executor] map (1 files)

### Cycle 17: the runner's ledger directory is private to it  _(standard)_
- **Target:** `tddcli::tests/test_split_ledger.py::test_the_runner_ledger_directory_is_mode_700`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `7aca3bddb` [red] test: the runner's ledger directory is mode 700 (1 files)
  - `425ccb2ab` [green] feat: the runner role creates and keeps its ledger directory at mode 700 (1 files)
  - `148723f9f` [refactor] refactor: tidy ledger directory permissions (1 files)

### Cycle 16: the runner's ledger home comes from its config, never from the caller's TDD_LEDGER_HOME  _(standard)_
- **Target:** `tddcli::tests/test_split_ledger.py::test_the_runner_ignores_the_callers_ledger_home`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `ba0aef8ad` [red] test: the runner ignores the caller's TDD_LEDGER_HOME (1 files)
  - `9404c7bda` [green] feat: in the runner role the ledger home comes from the runner config (1 files)

### Cycle 15: docs and init stay local; every other verb is forwarded  _(standard)_
- **Target:** `tddcli::tests/test_split_client.py::test_only_docs_and_init_stay_local`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `ef58f3961` [red] test: only docs and init stay local in the client role (1 files)
  - `cf0e95e36` [green] feat: docs and init are never forwarded to the runner (1 files)

### Cycle 14: the client sends its environment to the runner on stdin  _(standard)_
- **Target:** `tddcli::tests/test_split_client.py::test_the_client_sends_its_environment_on_stdin`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `d2db478b7` [red] test: the client sends its environment on stdin (1 files)
  - `985971435` [green] feat: the client writes the agent context JSON to the runner's stdin (1 files)

### Cycle 13: the client forwards the verb to the runner through sudo and relays its answer  _(standard)_
- **Target:** `tddcli::tests/test_split_client.py::test_the_client_forwards_the_verb_and_relays_the_answer`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `dd5138077` [red] test: the client forwards the verb and relays the answer (2 files)
  - `371737d22` [green] feat: in the client role tdd re-executes as the runner via sudo (3 files)
> **note** _(during AWAITING_IMPL)_: cycle 13: touched src/tddcli/actor.py, which the plan's files list for this cycle omits. The client's sudo call is a spawn, and cycle 3's guard allows spawns only in actor.py; it also needs stdout captured with stderr inherited, which run_argv does not do. Added LocalActor.relay for it.

### Cycle 12: an unreadable worktree is reported as a failure envelope in the runner role  _(standard)_
- **Target:** `tddcli::tests/test_split_runner.py::test_an_unreadable_worktree_is_a_failure_envelope`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `2fcd7f1ab` [red] test: an unreadable worktree is a failure envelope (1 files)
  - `3a8b6e306` [green] feat: the runner reports PermissionError as worktree_unreadable (1 files)
  - `1193e652f` [refactor] refactor: tidy the unreadable-worktree envelope (2 files)

### Cycle 11: a runner invoked with no agent refuses every verb that would spawn  _(standard)_
- **Target:** `tddcli::tests/test_split_runner.py::test_the_runner_without_an_agent_refuses_to_act`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `fbb5dc55b` [red] test: the runner without an agent refuses to act (1 files)
  - `e0321684a` [green] feat: the runner role refuses verbs when SUDO_USER is absent (2 files)
> **note** _(during AWAITING_IMPL)_: cycle 11: my RED test read the envelope's top-level 'reason'; failure() puts reason under result, like every other refusal. The first GREEN attempt failed for that reason alone. Corrected the test to read result.reason; the behaviour asserted is unchanged. Cycles 12 and 24-27 will read result.reason too.

### Cycle 10: the runner takes the agent's environment from stdin when flagged  _(standard)_
- **Target:** `tddcli::tests/test_split_runner.py::test_agent_context_on_stdin_reaches_spawned_commands`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `9e1e3e684` [red] test: the agent context on stdin reaches spawned commands (1 files)
  - `e4d9ca985` [green] feat: --agent-context-stdin carries the agent's environment to the runner (1 files)

### Cycle 9: in the runner role, run start spawns git and the suite as the agent  _(standard)_
- **Target:** `tddcli::tests/test_split_runner.py::test_run_start_spawns_git_and_the_suite_as_the_agent`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `329190fb4` [red] test: in the runner role run start spawns everything as the agent (2 files)
  - `be0ec9ae7` [green] feat: main installs a SudoActor for SUDO_USER in the runner role (1 files)

### Cycle 8: every file operation is performed by a process spawned as the agent  _(standard)_
- **Target:** `tddcli::tests/test_sudo_actor.py::test_file_operations_are_performed_as_the_agent`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `a16dc6139` [red] test: file operations are performed as the agent (2 files)
  - `92a124b99` [green] feat: SudoActor file operations run the agentfs helper as the agent (2 files)

### Cycle 7: with no agent environment the SudoActor lets sudo build one  _(standard)_
- **Target:** `tddcli::tests/test_sudo_actor.py::test_without_an_agent_environment_sudo_builds_it`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `5e01f90c5` [red] test: with no agent environment sudo builds it (1 files)
  - `41f7074ab` [green] feat: SudoActor uses -H instead of -E when it holds no agent environment (1 files)

### Cycle 6: a spawned command sees the agent's environment plus the tool's extras, not the runner's  _(standard)_
- **Target:** `tddcli::tests/test_sudo_actor.py::test_spawned_environment_is_the_agents_plus_extras`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `5da027cdb` [red] test: a spawned command sees the agent's environment plus extras (1 files)
  - `0b29e10f5` [green] feat: SudoActor passes the agent's environment with sudo -E (1 files)

### Cycle 5: a SudoActor wraps both spawn forms in sudo as the agent  _(standard)_
- **Target:** `tddcli::tests/test_sudo_actor.py::test_both_spawn_forms_run_through_sudo_as_the_agent`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `d44c784fe` [red] test: a SudoActor wraps both spawn forms in sudo as the agent (3 files)
  - `59e7c90ee` [green] feat: SudoActor runs argv and shell commands via sudo -u <agent> (1 files)

### Cycle 4: every write outside the tool's own state goes through the actor  _(standard)_
- **Target:** `tddcli::tests/test_actor_seams.py::test_only_the_actor_writes_outside_the_tools_own_state`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `f393fb3cb` [red] test: only the actor writes outside the tool's own state (1 files)
  - `97b17307f` [green] feat: route worktree and temp-dir writes through the LocalActor (7 files)
> **note** _(during AWAITING_IMPL)_: cycle 4: two plan defects. (1) tests/test_project_commands.py::test_only_reporting_flags_are_appended patches adapters.pytest_adapter.tempfile, which the move removes; the plan listed no modifies_tests. Repointed the patch at actor.tempfile; assertions unchanged. (2) the guard regex matches the actor's own method names at call sites (.unlink( .mkdtemp( rmtree(), so the API in decision 4 could never satisfy it. Kept the committed RED test and renamed the file methods: write_file, remove_file, make_temp_dir, remove_tree, link.

### Cycle 3: every process the tool spawns goes through the actor  _(standard)_
- **Target:** `tddcli::tests/test_actor_seams.py::test_only_the_actor_spawns_processes`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `3a070b502` [red] test: only the actor module may spawn processes (1 files)
  - `95aeb53f1` [green] feat: route git and command spawns through a LocalActor (3 files)
> **note** _(during AWAITING_IMPL)_: cycle 3: the plan's guard regex (bare word 'subprocess') also matches comments in ledger.py and exec_adapter.py; the discovery re-run showed the delta. Narrowed the regex to import/attribute use. Also deferred the conftest actor-restore teardown to the first cycle where actor.py exists, since importing it in cycle 3's RED would break every test.

### Cycle 2: a runner config the caller could have forged is refused  _(standard)_
- **Target:** `tddcli::tests/test_split_config.py::test_an_untrusted_runner_config_is_refused`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `0b9d06d0f` [red] test: an untrusted runner config is refused (1 files)
  - `56e977f5e` [green] feat: refuse a runner config not owned by root or the process, or writable by others (1 files)

### Cycle 1: the runner config decides the role: absent is single, own user is runner, another user is client  _(standard)_
- **Target:** `tddcli::tests/test_split_config.py::test_role_follows_the_runner_config`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `5c3fe7e2e` [red] test: the runner config decides the role (3 files)
  - `9e0bb0c5d` [green] feat: load the machine runner config and resolve the process role (1 files)

## Executor narrative

_Claims from the executor, unverified by design._

> closing: all 29 cycles delivered, no blockers, no sensitivity checks, no accepted failures. Hardest cycle: 4, where the plan's guard regex collided with the actor API the same plan specified, and an existing test patched a module attribute the move removed. Plan inaccuracies: cycle 3's regex matched comments; cycle 4 missed a modifies_tests entry and named an unsatisfiable API; cycle 13 omitted actor.py from files; the plan never said refusal reasons live under result.reason, and my cycle 11 test read the wrong key at first. Deviations: actor file methods are write_file/remove_file/make_temp_dir/remove_tree/link; identity resolves the operator map inside identity.py, so cli.py was not touched in cycle 18; added LocalActor.relay for the client's sudo call. Harness friction: a worktree-isolated session refuses heredocs and python -c edits, so every file change went through the editor tools. Not verified anywhere: split mode against a real second uid.

