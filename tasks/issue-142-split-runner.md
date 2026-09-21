---
closes: 142
cycles:
  - n: 1
    project: tddcli
    title: "the runner config decides the role: absent is single, own user is runner, another user is client"
    test: "tests/test_split_config.py::test_role_follows_the_runner_config"
    stub_expected: ["src/tddcli/runner.py"]
    files: ["src/tddcli/runner.py"]
    commit_red: "test: the runner config decides the role"
    commit_green: "feat: load the machine runner config and resolve the process role"
    commit_refactor: "refactor: tidy runner config loading"
  - n: 2
    project: tddcli
    title: "a runner config the caller could have forged is refused"
    test: "tests/test_split_config.py::test_an_untrusted_runner_config_is_refused"
    files: ["src/tddcli/runner.py"]
    commit_red: "test: an untrusted runner config is refused"
    commit_green: "feat: refuse a runner config not owned by root or the process, or writable by others"
    commit_refactor: "refactor: tidy the config trust check"
  - n: 3
    project: tddcli
    title: "every process the tool spawns goes through the actor"
    test: "tests/test_actor_seams.py::test_only_the_actor_spawns_processes"
    files: ["src/tddcli/actor.py", "src/tddcli/gitutil.py", "src/tddcli/adapters/base.py"]
    commit_red: "test: only the actor module may spawn processes"
    commit_green: "feat: route git and command spawns through a LocalActor"
    commit_refactor: "refactor: tidy the actor spawn seam"
  - n: 4
    project: tddcli
    title: "every write outside the tool's own state goes through the actor"
    test: "tests/test_actor_seams.py::test_only_the_actor_writes_outside_the_tools_own_state"
    files:
      - "src/tddcli/actor.py"
      - "src/tddcli/snapshot.py"
      - "src/tddcli/gitutil.py"
      - "src/tddcli/cli.py"
      - "src/tddcli/adapters/pytest_adapter.py"
      - "src/tddcli/adapters/gradle_adapter.py"
    commit_red: "test: only the actor writes outside the tool's own state"
    commit_green: "feat: route worktree and temp-dir writes through the LocalActor"
    commit_refactor: "refactor: tidy the actor file seam"
  - n: 5
    project: tddcli
    title: "a SudoActor wraps both spawn forms in sudo as the agent"
    test: "tests/test_sudo_actor.py::test_both_spawn_forms_run_through_sudo_as_the_agent"
    stub_expected: ["src/tddcli/actor.py"]
    files: ["src/tddcli/actor.py"]
    commit_red: "test: a SudoActor wraps both spawn forms in sudo as the agent"
    commit_green: "feat: SudoActor runs argv and shell commands via sudo -u <agent>"
    commit_refactor: "refactor: tidy SudoActor spawning"
  - n: 6
    project: tddcli
    title: "a spawned command sees the agent's environment plus the tool's extras, not the runner's"
    test: "tests/test_sudo_actor.py::test_spawned_environment_is_the_agents_plus_extras"
    files: ["src/tddcli/actor.py"]
    commit_red: "test: a spawned command sees the agent's environment plus extras"
    commit_green: "feat: SudoActor passes the agent's environment with sudo -E"
    commit_refactor: "refactor: tidy SudoActor environment handling"
  - n: 7
    project: tddcli
    title: "with no agent environment the SudoActor lets sudo build one"
    test: "tests/test_sudo_actor.py::test_without_an_agent_environment_sudo_builds_it"
    files: ["src/tddcli/actor.py"]
    commit_red: "test: with no agent environment sudo builds it"
    commit_green: "feat: SudoActor uses -H instead of -E when it holds no agent environment"
    commit_refactor: "refactor: tidy SudoActor flag selection"
  - n: 8
    project: tddcli
    title: "every file operation is performed by a process spawned as the agent"
    test: "tests/test_sudo_actor.py::test_file_operations_are_performed_as_the_agent"
    stub_expected: ["src/tddcli/agentfs.py"]
    files: ["src/tddcli/actor.py", "src/tddcli/agentfs.py"]
    commit_red: "test: file operations are performed as the agent"
    commit_green: "feat: SudoActor file operations run the agentfs helper as the agent"
    commit_refactor: "refactor: tidy the agentfs helper"
  - n: 9
    project: tddcli
    title: "in the runner role, run start spawns git and the suite as the agent"
    test: "tests/test_split_runner.py::test_run_start_spawns_git_and_the_suite_as_the_agent"
    files: ["src/tddcli/cli.py"]
    commit_red: "test: in the runner role run start spawns everything as the agent"
    commit_green: "feat: main installs a SudoActor for SUDO_USER in the runner role"
    commit_refactor: "refactor: tidy role wiring in main"
  - n: 10
    project: tddcli
    title: "the runner takes the agent's environment from stdin when flagged"
    test: "tests/test_split_runner.py::test_agent_context_on_stdin_reaches_spawned_commands"
    files: ["src/tddcli/cli.py"]
    commit_red: "test: the agent context on stdin reaches spawned commands"
    commit_green: "feat: --agent-context-stdin carries the agent's environment to the runner"
    commit_refactor: "refactor: tidy agent context parsing"
  - n: 11
    project: tddcli
    title: "a runner invoked with no agent refuses every verb that would spawn"
    test: "tests/test_split_runner.py::test_the_runner_without_an_agent_refuses_to_act"
    files: ["src/tddcli/cli.py"]
    commit_red: "test: the runner without an agent refuses to act"
    commit_green: "feat: the runner role refuses verbs when SUDO_USER is absent"
    commit_refactor: "refactor: tidy the no-agent refusal"
  - n: 12
    project: tddcli
    title: "an unreadable worktree is reported as a failure envelope in the runner role"
    test: "tests/test_split_runner.py::test_an_unreadable_worktree_is_a_failure_envelope"
    files: ["src/tddcli/cli.py"]
    commit_red: "test: an unreadable worktree is a failure envelope"
    commit_green: "feat: the runner reports PermissionError as worktree_unreadable"
    commit_refactor: "refactor: tidy the unreadable-worktree envelope"
  - n: 13
    project: tddcli
    title: "the client forwards the verb to the runner through sudo and relays its answer"
    test: "tests/test_split_client.py::test_the_client_forwards_the_verb_and_relays_the_answer"
    files: ["src/tddcli/cli.py", "src/tddcli/runner.py"]
    commit_red: "test: the client forwards the verb and relays the answer"
    commit_green: "feat: in the client role tdd re-executes as the runner via sudo"
    commit_refactor: "refactor: tidy client forwarding"
  - n: 14
    project: tddcli
    title: "the client sends its environment to the runner on stdin"
    test: "tests/test_split_client.py::test_the_client_sends_its_environment_on_stdin"
    files: ["src/tddcli/runner.py"]
    commit_red: "test: the client sends its environment on stdin"
    commit_green: "feat: the client writes the agent context JSON to the runner's stdin"
    commit_refactor: "refactor: tidy the agent context payload"
  - n: 15
    project: tddcli
    title: "docs and init stay local; every other verb is forwarded"
    test: "tests/test_split_client.py::test_only_docs_and_init_stay_local"
    files: ["src/tddcli/cli.py"]
    commit_red: "test: only docs and init stay local in the client role"
    commit_green: "feat: docs and init are never forwarded to the runner"
    commit_refactor: "refactor: tidy the local-verb table"
  - n: 16
    project: tddcli
    title: "the runner's ledger home comes from its config, never from the caller's TDD_LEDGER_HOME"
    test: "tests/test_split_ledger.py::test_the_runner_ignores_the_callers_ledger_home"
    files: ["src/tddcli/ledger.py"]
    commit_red: "test: the runner ignores the caller's TDD_LEDGER_HOME"
    commit_green: "feat: in the runner role the ledger home comes from the runner config"
    commit_refactor: "refactor: tidy ledger home resolution"
  - n: 17
    project: tddcli
    title: "the runner's ledger directory is private to it"
    test: "tests/test_split_ledger.py::test_the_runner_ledger_directory_is_mode_700"
    files: ["src/tddcli/ledger.py"]
    commit_red: "test: the runner's ledger directory is mode 700"
    commit_green: "feat: the runner role creates and keeps its ledger directory at mode 700"
    commit_refactor: "refactor: tidy ledger directory permissions"
  - n: 18
    project: tddcli
    title: "a run by a mapped agent records the operator-assigned model"
    test: "tests/test_split_identity.py::test_a_mapped_agent_records_the_operator_assigned_model"
    files: ["src/tddcli/identity.py", "src/tddcli/cli.py"]
    commit_red: "test: a mapped agent records the operator-assigned model"
    commit_green: "feat: the runner resolves executor identity from its [executor] map"
    commit_refactor: "refactor: tidy operator identity resolution"
  - n: 19
    project: tddcli
    title: "a run by an unmapped agent records the agent's claim, labelled claimed"
    test: "tests/test_split_identity.py::test_an_unmapped_agent_is_recorded_as_claimed"
    files: ["src/tddcli/identity.py"]
    commit_red: "test: an unmapped agent is recorded as claimed"
    commit_green: "feat: the runner resolves an unmapped executor on the agent's side and labels it claimed"
    commit_refactor: "refactor: tidy claimed identity resolution"
  - n: 20
    project: tddcli
    title: "single-mode doctor reports the mode and stops claiming the ledger is out of reach"
    test: "tests/test_split_doctor.py::test_single_mode_doctor_says_the_agent_can_reach_the_ledger"
    files: ["src/tddcli/cli.py"]
    commit_red: "test: single-mode doctor says the agent can reach the ledger"
    commit_green: "feat: doctor reports mode single and a ledger isolation notice"
    commit_refactor: "refactor: tidy the doctor mode report"
  - n: 21
    project: tddcli
    title: "split-mode doctor verifies the drop to the agent's uid and names the sudoers line when it fails"
    test: "tests/test_split_doctor.py::test_split_doctor_checks_the_drop_to_the_agent"
    files: ["src/tddcli/cli.py"]
    commit_red: "test: split doctor checks the drop to the agent's uid"
    commit_green: "feat: split doctor probes id -u as the agent"
    commit_refactor: "refactor: tidy the drop check"
  - n: 22
    project: tddcli
    title: "split-mode doctor's ledger check follows what the agent can actually read"
    test: "tests/test_split_doctor.py::test_split_doctor_ledger_check_follows_what_the_agent_can_read"
    files: ["src/tddcli/cli.py"]
    commit_red: "test: split doctor's ledger check follows what the agent can read"
    commit_green: "feat: split doctor probes ledger readability as the agent"
    commit_refactor: "refactor: tidy the ledger reach check"
  - n: 23
    project: tddcli
    title: "split-mode doctor's install check follows what the agent can actually write"
    test: "tests/test_split_doctor.py::test_split_doctor_install_check_follows_what_the_agent_can_write"
    files: ["src/tddcli/cli.py"]
    commit_red: "test: split doctor's install check follows what the agent can write"
    commit_green: "feat: split doctor probes install writability as the agent"
    commit_refactor: "refactor: tidy the install check"
  - n: 24
    project: tddcli
    title: "runner import copies a legacy ledger and marks its history pre-split"
    test: "tests/test_runner_import.py::test_import_copies_the_ledger_and_marks_it_pre_split"
    stub_expected: ["src/tddcli/cli.py"]
    files: ["src/tddcli/cli.py", "src/tddcli/ledger.py"]
    commit_red: "test: runner import copies a legacy ledger and marks it pre-split"
    commit_green: "feat: tdd runner import"
    commit_refactor: "refactor: tidy runner import"
  - n: 25
    project: tddcli
    title: "runner import refuses to overwrite a ledger the runner already holds"
    test: "tests/test_runner_import.py::test_import_refuses_to_overwrite_an_existing_ledger"
    files: ["src/tddcli/cli.py"]
    commit_red: "test: runner import refuses to overwrite an existing ledger"
    commit_green: "feat: runner import refuses when the target ledger exists"
    commit_refactor: "refactor: tidy the overwrite refusal"
  - n: 26
    project: tddcli
    title: "runner import is refused when an agent calls it"
    test: "tests/test_runner_import.py::test_import_is_refused_for_an_agent_caller"
    files: ["src/tddcli/cli.py"]
    commit_red: "test: runner import is refused for an agent caller"
    commit_green: "feat: runner import is operator-only"
    commit_refactor: "refactor: tidy the operator-only check"
  - n: 27
    project: tddcli
    title: "runner import is refused on a machine that is not split"
    test: "tests/test_runner_import.py::test_import_is_refused_in_single_mode"
    files: ["src/tddcli/cli.py"]
    commit_red: "test: runner import is refused in single mode"
    commit_green: "feat: runner import refuses with not_split outside the runner role"
    commit_refactor: "refactor: tidy the not_split refusal"
  - n: 28
    project: tddcli
    title: "metrics says which runs predate the split"
    test: "tests/test_runner_import.py::test_metrics_reports_the_pre_split_marker"
    files: ["src/tddcli/render.py"]
    commit_red: "test: metrics reports the pre-split marker"
    commit_green: "feat: metrics carries pre_split_import when the ledger was imported"
    commit_refactor: "refactor: tidy the pre-split marker"
  - n: 29
    project: tddcli
    title: "the split-runner setup guide ships with the binary"
    test: "tests/test_docs_command.py::test_the_split_topic_explains_the_sudoers_setup"
    files:
      - "src/tddcli/docs.py"
      - "pyproject.toml"
      - "docs/split-runner.md"
      - "README.md"
      - "SECURITY.md"
      - "docs/PRD.md"
      - "CHANGELOG.md"
    commit_red: "test: the split topic explains the sudoers setup"
    commit_green: "docs: split-runner guide, and stop claiming isolation in single mode"
    commit_refactor: "refactor: tidy the split-runner docs"
---

# Issue 142: split the runner from the agent

## Context

[Issue #142](https://github.com/geuben/tdd-cli/issues/142). The README says the run is recorded
"in a ledger the agent cannot reach". As built, the ledger is one SQLite file owned by the uid
that runs `tdd`, which is the agent's uid. "Cannot reach" only means "outside the worktree".

This plan adds a **split mode**. A `tdd` runner under its own uid owns a ledger directory only
it can open. The agent can only ask the runner to act, through one `sudoers` line. The runner
executes every suite, gate, hook and git command as the agent's uid, in the agent's worktree,
and observes the results from outside. Single-user installs keep working unchanged, and
`tdd doctor` says which mode a machine is in and stops claiming isolation in single mode.

Scope is one machine (confirmed by Reuben, 2026-09-21). One ledger per machine is accepted.

## Design decisions (locked)

1. **Transport is a sudo entry point, not a daemon.** *Decided by Reuben, 2026-09-21.*
   A runner under its own non-root uid cannot `setuid` to the agent, so dropping to the agent
   needs sudo in either shape. PRD R13.7 already says "No daemon". Two sudoers lines per
   machine:

       <agent>      ALL=(tdd-runner) NOPASSWD: /opt/tdd-cli/bin/tdd
       tdd-runner   ALL=(<agent>)    NOPASSWD:SETENV: ALL

   Footguns, and the setting that avoids each:
   - `sudo -E` fails with "not allowed to preserve the environment" unless the rule carries
     the `SETENV:` tag. The second line above carries it.
   - macOS sudo keeps the caller's `HOME` unless told otherwise, which would put the
     runner's default ledger home and lease directory in the agent's home. The client always
     passes `-H`.
   - Always pass `-n`. A sudo that prompts would hang an unattended agent.
   - sudo keeps the caller's cwd by default, so the runner sees the agent's cwd. No `-D`.

2. **Machine config.** `/etc/tdd-cli/runner.toml`, or the path in `TDD_RUNNER_CONFIG`.
   *Decided from evidence:* tests invoke the CLI in-process through `conftest.run_cli`, and a
   developer's machine may itself be split, so tests need an override. The override is safe
   because of decision 3.

       [runner]
       user        = "tdd-runner"            # required
       command     = "/opt/tdd-cli/bin/tdd"  # required: the path the first sudoers line names
       sudo        = "/usr/bin/sudo"         # optional, this is the default
       ledger_home = "/var/lib/tdd-cli"      # optional; default is the runner's ~/.local/share/tdd-cli

       [executor]                            # optional: agent user name -> model
       agent1 = "claude-fable-5-1"

   Role: config absent → `single`. `pwd.getpwnam(user).pw_uid == os.geteuid()` → `runner`.
   Otherwise → `client`. A `user` that does not exist is a `RunnerConfigError`.

3. **A config is trusted only if it is owned by root or by the process's own euid, and is not
   group- or world-writable.** *Decided from evidence.* An agent can point its own client at a
   forged config, which only moves its own run into a ledger nobody trusts. It cannot do the
   same to the runner: sudo's `env_reset` strips `TDD_RUNNER_CONFIG`, and if a sudoers file
   ever preserved it, the forged file is owned by the agent, not by root or the runner, so the
   runner refuses it. `RunnerConfigError` surfaces as a failure envelope from `main`, the same
   way `ConfigError` does.

4. **One actor seam for everything that touches the agent's territory.** *Decided from
   evidence:* there are exactly two spawn sites (`gitutil.git`, `adapters.base.run_command`)
   and six write sites (see cycle 4's sweep). New module `src/tddcli/actor.py`:

       class LocalActor:                      # single mode and the client's local verbs
           run_argv(argv, *, cwd=None, env=None, timeout=None, input=None) -> CompletedProcess
           run_shell(command, *, cwd, env=None, timeout=None) -> CompletedProcess
           read_text(path) -> str | None      # None when the file is missing
           write_bytes(path, data)            # creates parent directories
           unlink(path)                       # missing is not an error
           mkdtemp(prefix) -> Path
           rmtree(path)                       # errors ignored
           symlink(src, dst)                  # creates parent directories
       class SudoActor(same methods)          # runner role
       current() -> actor ; install(actor)

   `env` on the run methods is the *extra* environment (`TDD_WORKERS` and the like), exactly
   what `run_command` calls `extra_env` today. `LocalActor` merges it over `os.environ`.
   `SudoActor` merges it over the agent's environment.

   **All git runs as the agent, reads included.** Git refuses a repository owned by another
   uid ("dubious ownership"), and commits must be the agent's.

   The runner reads the worktree directly (`tdd.toml`, test-file globs, JUnit XML). Split mode
   therefore requires the worktree to be readable by the runner uid. The one exception is the
   pytest JSON report, which lives in an agent-created temp directory of mode 700: it is read
   with `actor.read_text`.

5. **SudoActor command shapes.**
   - argv: `[sudo, "-n", "-E", "-u", agent, "--", *argv]`
   - shell: the argv form of `["/bin/sh", "-c", command]`
   - with no agent environment held: `-H` replaces `-E`, and sudo builds the environment.
   - file operations: the argv form of `[sys.executable, "-m", "tddcli.agentfs", op, path, ...]`,
     with `write` data on stdin and `read` text on stdout. `agentfs` exits 3 for "missing" on
     `read`. The install must therefore be readable and executable by the agent.
   With an agent environment held, the subprocess `env` passed to sudo is
   `{**agent_env, **extra}` and nothing from the runner's own `os.environ`. With none held,
   the runner's environment is inherited unchanged plus `extra`: there is no `-E`, so real
   sudo's `env_reset` discards it and builds the agent's. (The test shim needs this too: it
   reads `SUDO_LOG` and `PATH` from whatever environment it is given.)

6. **Agent context.** The client adds a hidden top-level flag, `--agent-context-stdin`
   (`help=argparse.SUPPRESS`), and writes `{"env": {...}}` as JSON to the runner's stdin.
   The flag carries no phase, cycle number or identity, so R8.3 holds across the boundary.
   The agent is `SUDO_USER`, which sudo sets itself and a caller cannot override.
   The client captures the runner's stdout and writes it to `sys.stdout`; stderr is inherited
   so heartbeats stay live. `main` returns the runner's exit code.

7. **Verb routing in the client role.** Accepted locally: `docs`, `init` (and `--version`,
   `--help`, which argparse answers before routing). Forwarded: every other top-level verb,
   including `runner`. The client parses first, then forwards the original argv verbatim.
   Pinned by one table-driven test over the parser's own verb list (cycle 15).

8. **A runner with no `SUDO_USER` acts for nobody.** It refuses every verb except
   `runner import` with `reason: "no_agent"`. It never falls back to spawning as itself,
   because that would run the agent's code as the ledger's uid.

9. **Ledger home in the runner role** is `ledger_home` from the config, else the runner's
   `~/.local/share/tdd-cli`. `TDD_LEDGER_HOME` is ignored in the runner role. The directory is
   created at mode 700 and chmod-ed back to 700 on every open. Single and client roles are
   unchanged (`TDD_LEDGER_HOME`, mode untouched).

10. **Executor identity in the runner role.** *Decided by Reuben, 2026-09-21.*
    - `SUDO_USER` is in `[executor]` → that model, `executor_source = "operator"`.
    - Otherwise the runner runs `[sys.executable, "-m", "tddcli.identity", <worktree>]` as the
      agent (it prints the `Executor` as JSON), and records the result with
      `executor_source = "claimed"`. A result whose source is `unknown` stays `unknown`.
      `--executor` is passed through as a third argv and is a claim like any other.
    - The runner never reads `TDD_EXECUTOR_MODEL`, `CLAUDE_CODE_SESSION_ID` or the transcript
      from its own environment or home.
    `executor_source` is free text in the schema and is passed through by `render.py`, so no
    migration is needed. Update the column comment in `ledger.py`'s `run` DDL.

11. **Doctor.** `result.mode` is `"single"` or `"split"`.
    - single: a check named `ledger isolation`, `ok: true`, whose detail says the ledger is
      writable by the same uid that runs the agent and points at `tdd docs split`. It is a
      notice, not a blocker: single-user installs must keep working.
    - split, all probed live through the actor so they hold on a real install:
      - `runs as the agent`: `id -u` as the agent equals `pwd.getpwnam(SUDO_USER).pw_uid`.
        The failing detail quotes the second sudoers line from decision 1.
      - `ledger out of the agent's reach`: `test -r <ledger file>` as the agent must fail.
      - `install not writable by the agent`: `test -w <tddcli package dir>` as the agent must
        fail.
    The existing `ledger outside worktree` check stays in both modes.

12. **`tdd runner import <file>`.** *Decided by Reuben, 2026-09-21.* Runner role only, and
    only when `SUDO_UID` is unset or `"0"`: otherwise an agent could import forged history.
    - Not the runner role → `reason: "not_split"`.
    - `SUDO_UID` set and not `"0"` → `reason: "operator_only"`.
    - Target `<ledger home>/<file's basename>` exists → `reason: "ledger_exists"`. No merge.
    - Otherwise copy the file, open it with `Ledger`-style migration so it reaches the current
      schema, and write one `meta` row: key `pre_split_import`, value JSON
      `{"source": <path>, "imported_at": <iso>, "last_run_id": <max run id or null>}`.
    The command needs no worktree. `tdd metrics` adds `result.pre_split_import` (the parsed
    JSON) when the row exists, so consumers can exclude runs up to `last_run_id`.
    No schema version change: the `meta` table already exists.

13. **Referee.** `SCHEMA_VERSION` does not change, so the released 0.12.2 tool referees this
    run, per the note at the top of `tdd.toml`. It ignores `TDD_RUNNER_CONFIG`.

## Deliberate scope cuts (do not build)

- **Hash chain / tamper evidence.** Premise: *user-deferred* (Reuben, 2026-09-21). In split
  mode the agent cannot open the ledger; in single mode there is nowhere the agent cannot
  write, so a published head is forgeable.
- **Socket daemon transport.** Premise: *user-deferred* (decision 1).
- **Multi-machine shared ledger.** Premise: *user-deferred* (Reuben, 2026-09-21: "single
  machine is ok for now").
- **An automated test with a real second uid.** Premise: *unreachable*. Creating accounts and
  sudoers rules needs root, which neither the test suite nor the run has. The tests use a fake
  `sudo` (see the divergence table). The gap is covered by doctor's three live probes, which
  run against real sudo on a real install, and by the manual verification checklist in
  `docs/split-runner.md`. Re-evaluation trigger: none, the premise does not rest on run
  evidence.
- **Merging an imported ledger into an existing runner ledger.** Premise: *named non-goal* of
  decision 12; the issue asks for migration, not reconciliation.

### Fake/real divergence

| Method | Fake `sudo` shim | Real sudo | Production path left untested | Ruling |
|---|---|---|---|---|
| run argv after `--` | execs it as the same uid | execs it as the target uid | the uid change itself | acceptable: doctor's `runs as the agent` probe checks it live |
| `-n` | ignored | fails instead of prompting | the sudoers policy lookup | acceptable: doctor probe fails with the sudoers line named |
| `-E` | environment passes because nothing resets it | needs `SETENV:` | the SETENV tag | acceptable: same doctor probe uses `-E` |
| `-H` | ignored | sets `HOME` to the target's | runner `HOME` on macOS | acceptable: manual checklist item |
| cwd | inherited | inherited unless unreadable | runner cannot traverse to the worktree | acceptable: cycle 12's envelope, manual checklist item |

## Test fixtures (add to `tests/conftest.py`)

Test-path edits stage in RED automatically. Add each piece in the cycle named.

**Cycle 1** adds this autouse fixture, so a developer machine that is itself split cannot put
the suite into the client role:

    @pytest.fixture(autouse=True)
    def _single_user_mode(tmp_path, monkeypatch):
        monkeypatch.setenv("TDD_RUNNER_CONFIG", str(tmp_path / "no-runner.toml"))
        for var in ("SUDO_USER", "SUDO_UID"):
            monkeypatch.delenv(var, raising=False)

**Cycle 3** extends it with a teardown that restores the local actor, because `main` installs
an actor process-wide and the suite runs the CLI in-process:

        yield
        from tddcli import actor
        actor.install(actor.LocalActor())

**Cycle 5** adds the shim and the helpers. `deny` names commands the shim refuses with exit 1,
which is how doctor's "the agent cannot" direction is reached without a second uid:

    SHIM = """#!/bin/sh
    echo "MARK=$MARK $@" >> "$SUDO_LOG"
    while [ "$1" != "--" ]; do shift; done; shift
    case " $SUDO_DENY " in *" $(basename "$1") "*) exit 1;; esac
    exec "$@"
    """

    def current_user() -> str:
        return pwd.getpwuid(os.geteuid()).pw_name

    @pytest.fixture
    def sudo_shim(tmp_path, monkeypatch):
        shim = tmp_path / "bin" / "sudo"
        shim.parent.mkdir()
        shim.write_text(textwrap.dedent(SHIM))
        shim.chmod(0o755)
        log = tmp_path / "sudo.log"
        log.write_text("")
        monkeypatch.setenv("SUDO_LOG", str(log))
        return SimpleNamespace(path=shim, log=log, lines=lambda: log.read_text().splitlines())

Probed 2026-09-21: the shim runs `/bin/sh -c 'echo hi $FOO'` and `git -C <repo> rev-parse HEAD`
correctly and logs `MARK=m -n -E -u agent -- /bin/sh -c echo hi $FOO`.

**Cycle 9** adds the runner-role fixture. The agent is the current user, so every spawn really
executes:

    @pytest.fixture
    def split_runner(tmp_path, monkeypatch, sudo_shim):
        home = tmp_path / "runner-ledgers"
        cfg = tmp_path / "runner.toml"
        cfg.write_text(
            f'[runner]\nuser = "{current_user()}"\ncommand = "tdd"\n'
            f'sudo = "{sudo_shim.path}"\nledger_home = "{home}"\n'
        )
        monkeypatch.setenv("TDD_RUNNER_CONFIG", str(cfg))
        monkeypatch.setenv("SUDO_USER", current_user())
        monkeypatch.setenv("SUDO_UID", str(os.geteuid()))
        return SimpleNamespace(config=cfg, ledger_home=home, shim=sudo_shim)

**Cycle 13** adds the client-role fixture. `user = "root"` makes the role `client` for any
non-root test process; skip the test when `os.geteuid() == 0`. `command` is a stub that records
its argv and stdin, answers with a fixed envelope, and exits 3:

    @pytest.fixture
    def split_client(tmp_path, monkeypatch, sudo_shim):
        stub = tmp_path / "bin" / "tdd-stub"
        stub.write_text(
            "#!/bin/sh\n"
            f'echo "$@" > "{tmp_path}/stub.argv"\n'
            f'cat > "{tmp_path}/stub.stdin"\n'
            "echo '{\"ok\": true, \"stub\": true}'\n"
            "exit 3\n"
        )
        stub.chmod(0o755)
        cfg = tmp_path / "runner.toml"
        cfg.write_text(f'[runner]\nuser = "root"\ncommand = "{stub}"\nsudo = "{sudo_shim.path}"\n')
        monkeypatch.setenv("TDD_RUNNER_CONFIG", str(cfg))
        return SimpleNamespace(stub=stub, argv=tmp_path / "stub.argv",
                               stdin=tmp_path / "stub.stdin", shim=sudo_shim)

## Cycles

Every test below is a new function. Where a test file does not exist yet, create it with
`from __future__ import annotations` and imports from `conftest`, as the existing files do.

### Cycle 1: the runner config decides the role

Test: table-driven over three configs. No file at the `TDD_RUNNER_CONFIG` path →
`runner.load()` is `None`. `user = current_user()` → `.role == "runner"`. `user = "root"` →
`.role == "client"` (skip this row as root). Single assertion: the list of observed roles equals
`[None, "runner", "client"]`.
Production target: `src/tddcli/runner.py`, `load() -> RunnerConfig | None` and `RunnerConfig`
(`user`, `command`, `sudo`, `ledger_home`, `executors`, `role`).
Stub: `runner.py` with `class RunnerConfigError(RuntimeError)`, an empty `RunnerConfig`
dataclass, and `load()` raising `NotImplementedError`.
EXPECTED FAILURE: fails with `NotImplementedError` raised from `runner.load`.

### Cycle 2: an untrusted runner config is refused

Test: table-driven over three forgeries of an otherwise valid config, each expecting
`RunnerConfigError`: mode `0o666`; mode `0o664`; and a foreign owner, reached by
`monkeypatch.setattr(os, "geteuid", lambda: <real euid + 1>)` so the file's real owner is
neither root nor the process. Single assertion: all three raise.
Production target: `runner.load`.
EXPECTED FAILURE: fails with `Failed: DID NOT RAISE <class 'tddcli.runner.RunnerConfigError'>`.
Note for the foreign-owner row: `load` resolves the role with `pwd.getpwnam(user).pw_uid`
compared to `os.geteuid()`; the trust check runs first, so the patched euid never reaches it.

### Cycle 3: every process the tool spawns goes through the actor

Test: a static guard. The set of files under `src/tddcli/` whose text matches
`\bsubprocess\b|os\.(system|popen|exec\w*|spawn\w*)\(` must equal `{"actor.py"}`.
Discovery command, and its output on 2026-09-21:

    grep -rlE "subprocess|os\.(system|popen|exec|spawn)" src/tddcli
    src/tddcli/gitutil.py
    src/tddcli/adapters/base.py

Production target: new `actor.py` (`LocalActor.run_argv`, `LocalActor.run_shell`, `current`,
`install`); `gitutil.git` calls `actor.current().run_argv(["git", "-C", ...])`;
`adapters.base.run_command` calls `actor.current().run_shell(...)` and keeps its timing
heartbeat and its `(code, stdout, stderr)` return. Behaviour in single mode is unchanged: the
568 existing tests are the guard.
EXPECTED FAILURE: fails with an `AssertionError` whose left side is
`{'gitutil.py', 'adapters/base.py'}`.
Re-run the discovery command first and report any delta from the list above.

### Cycle 4: every write outside the tool's own state goes through the actor

Test: a static guard. Files under `src/tddcli/` matching
`\.write_text\(|\.write_bytes\(|\.unlink\(|rmtree\(|mkdtemp\(|TemporaryDirectory\(|symlink_to\(|\.mkdir\(`
must be a subset of `{"actor.py", "agentfs.py", "leases.py", "ledger.py"}`. Leases and the
ledger are the tool's own state and stay the runner's.
Discovery command, and the sites it found on 2026-09-21 outside that allowlist:

    grep -rnE "\.write_text\(|\.write_bytes\(|\.unlink\(|rmtree\(|mkdtemp\(|TemporaryDirectory\(|symlink_to\(|\.mkdir\(" src/tddcli

- `gitutil.temporary_worktree`: `mkdtemp`, the parent `mkdir` plus `symlink_to`, `rmtree`
- `snapshot.restore`: two `unlink`s, and `mkdir` plus `write_bytes`
- `cli.cmd_init`: `write_text` of `tdd.toml`
- `cli.cmd_log_render`: `mkdir` plus `write_text` for `--out`
- `pytest_adapter._suite_report`: `TemporaryDirectory`; replace with `mkdtemp`/`rmtree`, and
  replace the `is_file()` + `read_text()` pair with `actor.read_text` returning `None`
- `gradle_adapter._clear_results`: `unlink`

Production target: the `LocalActor` file methods from decision 4, and those six sites.
Existing coverage guards each site: `test_snapshot_and_identity.py`, `test_late_baseline.py`,
`test_init_detection.py`, `test_end_to_end.py` (`--out`), every pytest-adapter test, and
`test_gradle_adapter.py`.
EXPECTED FAILURE: fails with an `AssertionError` listing `gitutil.py`, `snapshot.py`, `cli.py`,
`adapters/pytest_adapter.py`, `adapters/gradle_adapter.py`.

### Cycle 5: a SudoActor wraps both spawn forms

Test: `SudoActor(sudo=shim.path, agent="agent-x", env=None)`. Call
`run_argv(["echo", "one"])` and `run_shell("echo two", cwd=tmp_path)`. Single assertion: the shim
log's two lines end with `-u agent-x -- echo one` and `-u agent-x -- /bin/sh -c echo two`.
Production target: `actor.SudoActor.run_argv`, `run_shell`.
Stub: add `class SudoActor` to `actor.py` with the constructor storing its arguments and every
method raising `NotImplementedError`.
EXPECTED FAILURE: fails with `NotImplementedError` from `SudoActor.run_argv`.

### Cycle 6: the spawned environment is the agent's plus extras

Test: `monkeypatch.setenv("WHO", "runner")`. `SudoActor(..., env={"WHO": "agent", "PATH":
os.environ["PATH"], "SUDO_LOG": <log>})`. `run_shell("echo $WHO $TDD_WORKERS", cwd=tmp_path,
env={"TDD_WORKERS": "4"})`. Single assertion: stdout is `agent 4\n`, and the logged flags
include `-E`.
`SUDO_LOG` must be in the agent env or the shim cannot log; that is a property of the shim, not
of the design.
EXPECTED FAILURE: fails with `AssertionError`, stdout is `runner 4` or `runner`.

### Cycle 7: with no agent environment sudo builds it

Test: `SudoActor(..., env=None)`, `run_argv(["true"])`. Single assertion: the logged flags are
exactly `-n -H -u agent-x --`.
EXPECTED FAILURE: fails with `AssertionError`, the logged flags contain `-E`.
If cycle 5's GREEN already emits `-H` for `env=None`, this pre-passes; then run the sensitivity
check and say so in `friction_note`.

### Cycle 8: file operations are performed as the agent

Test: with a `SudoActor` whose env carries `PATH` and `SUDO_LOG`, perform in order: `mkdtemp`,
`write_bytes(dir/"a/b.txt", b"x")`, `read_text(dir/"a/b.txt")`, `read_text(dir/"missing")`,
`symlink(dir/"a/b.txt", dir/"l/link")`, `unlink(dir/"a/b.txt")`, `rmtree(dir)`. Single assertion
over one tuple: the read returned `"x"`, the missing read returned `None`, the link existed
before `rmtree`, the directory is gone after, and every one of the seven log lines contains
`-m tddcli.agentfs`.
Production target: `actor.SudoActor` file methods; new `src/tddcli/agentfs.py` with
`main(argv)` and an `if __name__ == "__main__"` guard, ops `mkdtemp read write symlink unlink
rmtree`. `agentfs.py` must import nothing from `tddcli` except the standard library: it runs as
the agent.
Stub: `agentfs.py` with `main` raising `NotImplementedError`.
EXPECTED FAILURE: fails with `NotImplementedError` from `SudoActor.mkdtemp`.

### Cycle 9: in the runner role, run start spawns git and the suite as the agent

Test: with `split_runner`, commit a one-cycle plan with `conftest.write_plan`, register it, and
`run_cli(repo, "run", "start", "--plan", ...)`. Single assertion: the envelope is `ok` and the
shim log has at least one line containing `-u <current user> -- git -C` and at least one
containing `-- /bin/sh -c`.
Production target: `cli.main`: after parsing, `runner.load()`; in the runner role with
`SUDO_USER` set, `actor.install(SudoActor(sudo=cfg.sudo, agent=SUDO_USER, env=None))`; in every
other case `actor.install(LocalActor())`. Also add `runner.RunnerConfigError` to `main`'s
existing `except (ConfigError, GitError, LedgerVersionError)` tuple.
EXPECTED FAILURE: fails with `AssertionError`, the shim log is empty.

### Cycle 10: the agent context on stdin reaches spawned commands

Test: with `split_runner`, `monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps({"env":
{**os.environ, "MARK": "from-agent"}})))`, then
`run_cli(repo, "--agent-context-stdin", "doctor")`. Single assertion: some shim log line starts
with `MARK=from-agent`.
Production target: `cli.build_parser` (hidden top-level flag) and `cli.main` (parse the JSON,
pass `env` to the `SudoActor`).
EXPECTED FAILURE: argparse rejects the unknown flag, `main` returns 2 with empty stdout, and
`run_cli` fails with `json.JSONDecodeError: Expecting value`. That is a runtime failure inside
the test, not a collection error.

### Cycle 11: the runner without an agent refuses to act

Test: with `split_runner`, `monkeypatch.delenv("SUDO_USER")` and `SUDO_UID`, then
`run_cli(repo, "status")`. Single assertion: `ok` is false and `reason == "no_agent"`.
EXPECTED FAILURE: fails with `AssertionError`; the envelope is the ordinary "no active run"
failure with no `reason`.

### Cycle 12: an unreadable worktree is a failure envelope

Test: with `split_runner`, `(repo / "tdd.toml").chmod(0)` (restore in `finally`), then
`run_cli(repo, "doctor")`. Single assertion: `reason == "worktree_unreadable"` and the error
names the runner user. Skip as root.
Production target: `cli.main` catches `PermissionError` in the runner role only.
EXPECTED FAILURE (probed): `PermissionError: [Errno 13] Permission denied: '.../tdd.toml'`
propagates out of `run_cli`.

### Cycle 13: the client forwards the verb and relays the answer

Test: with `split_client`, call `main(["status"])` through a variant of `run_cli_text` that
also returns `main`'s return value. Single assertion over one tuple: the shim log line is
`... -n -H -u root -- <stub> --agent-context-stdin status`, the stub's recorded argv is
`--agent-context-stdin status`, stdout is the stub's envelope, and the return value is 3.
Production target: `runner.forward(cfg, argv) -> int` and its call in `cli.main`.
EXPECTED FAILURE: fails with `AssertionError`; stdout is the local "no active run" failure and
the shim log is empty.

### Cycle 14: the client sends its environment on stdin

Test: with `split_client`, `monkeypatch.setenv("AGENT_ONLY", "yes")`, `main(["status"])`.
Single assertion: `json.loads(stub.stdin.read_text())["env"]["AGENT_ONLY"] == "yes"`.
EXPECTED FAILURE: fails with `json.JSONDecodeError`, because cycle 13's GREEN sends no stdin.
Cycle 13's GREEN must pass `input=""` and nothing more.

### Cycle 15: only docs and init stay local

Test: with `split_client`, walk the top-level verbs from `build_parser()`'s subparser choices.
For each, call `main` with the smallest argv that parses (a fixed table in the test: `plan
register x`, `run start --plan x`, `cycle skip --reason x`, `log render`, `sensitivity begin`,
`runner import x`, and the bare verb otherwise) and record whether the shim log grew. Single
assertion: the set of verbs that did not forward equals `{"docs", "init"}`.
`runner` is not a verb until cycle 24; build the table from the parser so the test stays true
when it arrives, and keep the `runner import x` entry keyed by name so it is unused until then.
EXPECTED FAILURE: fails with `AssertionError`; the not-forwarded set is empty, because cycle 13
forwards everything.

### Cycle 16: the runner ignores the caller's TDD_LEDGER_HOME

Test: with `split_runner` (the `repo` fixture has already set `TDD_LEDGER_HOME`),
`run_cli(repo, "doctor")`. Single assertion: `split_runner.ledger_home` holds exactly one
`*.sqlite3` file and the `TDD_LEDGER_HOME` directory holds none.
Production target: `ledger.ledger_path`.
EXPECTED FAILURE: fails with `AssertionError`; the ledger is under `TDD_LEDGER_HOME`.

### Cycle 17: the runner's ledger directory is mode 700

Test: with `split_runner`, pre-create `ledger_home` at mode `0o755`, run `doctor`. Single
assertion: `stat.S_IMODE(ledger_home.stat().st_mode) == 0o700`.
EXPECTED FAILURE: fails with `AssertionError: 0o755 != 0o700`.

### Cycle 18: a mapped agent records the operator-assigned model

Test: with `split_runner`, append `[executor]\n<current user> = "model-from-operator"` to the
config, start a run. Single assertion: `result.executor_source == "operator"` and the run row's
`executor_model == "model-from-operator"`. `conftest` pins `TDD_EXECUTOR_MODEL` in the process
environment; the assertion proves the runner did not read it.
Production target: `identity.resolve` gains the runner-role branch; `cli.cmd_run_start` and
`cli.cmd_doctor` pass it the runner config and `SUDO_USER`.
EXPECTED FAILURE: fails with `AssertionError`; the source is `declared` and the model is
`pytest-executor`.

### Cycle 19: an unmapped agent is recorded as claimed

Test: with `split_runner` and the agent context on stdin carrying
`TDD_EXECUTOR_MODEL=model-the-agent-claims`, `run_cli(repo, "--agent-context-stdin", "run",
"start", "--plan", ...)`. Single assertion: source is `claimed` and the model is
`model-the-agent-claims`.
Production target: `identity.py` gains `main(argv)` printing the `Executor` as JSON, run as the
agent through `actor.current().run_argv`.
EXPECTED FAILURE: fails with `AssertionError`; the source is `declared` and the model is
`pytest-executor`.

### Cycle 20: single-mode doctor says the agent can reach the ledger

Test: `run_cli(repo, "doctor")`. Single assertion: `result.mode == "single"` and the check named
`ledger isolation` is `ok` with `"same uid"` in its detail.
EXPECTED FAILURE (probed): `KeyError: 'mode'`; doctor's result keys today are `checks`,
`healthy`, `projects`.

### Cycle 21: split doctor checks the drop to the agent

Test: two doctor runs with `split_runner`: one plain, one with `SUDO_DENY=id`. Single assertion:
the `runs as the agent` check is `[True, False]` across the two, and the failing detail
contains `NOPASSWD:SETENV`.
EXPECTED FAILURE: fails in `_check` with `AssertionError`: no check named `runs as the agent`.

### Cycle 22: split doctor's ledger check follows what the agent can read

Test: two doctor runs: plain (agent and runner are the same uid, so the ledger *is* readable),
and `SUDO_DENY=test`. Single assertion: `ledger out of the agent's reach` is `[False, True]`.
EXPECTED FAILURE: fails in `_check`: no check of that name.

### Cycle 23: split doctor's install check follows what the agent can write

Test: as cycle 22, for `install not writable by the agent`: `[False, True]`.
EXPECTED FAILURE: fails in `_check`: no check of that name.
Cycles 21 to 23 each add one `check(...)` call and nothing earlier. `SUDO_DENY=test` flips
both of the last two checks; each test reads only its own.

### Cycle 24: runner import copies the ledger and marks it pre-split

Test: in single mode create a legacy ledger with one run (start a run on `repo`). Then switch to
`split_runner`, delete `SUDO_USER` and `SUDO_UID`, and `run_cli(repo, "runner", "import",
<legacy file>)`. Single assertion: the envelope is `ok`, the copy under `ledger_home` has the
same run count, and its `meta` row `pre_split_import` parses to JSON whose `last_run_id` is that
run's id.
Production target: `cli.cmd_runner_import`, the `runner import` subparser, and a small
`Ledger.set_meta`/`get_meta` pair in `ledger.py`.
Stub (`cli.py` is in `stub_expected`): register `runner import <file>` with a handler that
returns `failure("runner import is not implemented", reason="not_implemented")`. Without it the
verb does not parse and the test dies in `json.loads("")` (probed: `invalid choice: 'runner'`).
EXPECTED FAILURE: fails with `AssertionError`: the envelope is not `ok`.
Exempt `runner import` from cycle 11's `no_agent` refusal in this cycle's GREEN.

### Cycle 25: import refuses to overwrite

Test: import twice. Single assertion: the second envelope has `reason == "ledger_exists"`.
EXPECTED FAILURE: fails with `AssertionError`; the second import succeeds.

### Cycle 26: import is refused for an agent caller

Test: with `split_runner` as built (`SUDO_UID` is the test's non-zero uid). Single assertion:
`reason == "operator_only"` and nothing was copied. Skip as root.
EXPECTED FAILURE: fails with `AssertionError`; the import succeeds.

### Cycle 27: import is refused in single mode

Test: no runner config. Single assertion: `reason == "not_split"`.
EXPECTED FAILURE: fails with `AssertionError`; the import succeeds into `TDD_LEDGER_HOME`.

### Cycle 28: metrics reports the pre-split marker

Test: after cycle 24's import, with `SUDO_USER` restored, `run_cli(repo, "metrics")`. Single
assertion: `result.pre_split_import.last_run_id` equals the legacy run's id.
Production target: `render.metrics`. This is the consumer of cycle 24's `meta` row.
EXPECTED FAILURE (probed): `KeyError: 'pre_split_import'`; metrics' result keys today are
`runs` and `note`.

### Cycle 29: the split-runner guide ships with the binary

Test: `run_cli_text(repo, "docs", "split")`. Single assertion: the text contains
`NOPASSWD:SETENV` and `tdd runner import`.
Production target: a `Topic("split", "docs/split-runner.md", ...)` in `docs.TOPICS`, the matching
`force-include` line in `pyproject.toml` (the existing `test_every_topic_is_carried_into_the_wheel`
enforces it), and the new file. `docs/split-runner.md` covers: what split mode protects against
and what it does not (a forged report file, a client-side downgrade); the two accounts; the two
sudoers lines and the four footguns from decision 1; the config file and its trust rule;
installing `tdd` where the agent cannot write it; worktree readability; the `[executor]` map and
the `operator`/`claimed` sources; `tdd runner import`; and a manual verification checklist
(`tdd doctor` healthy with all three split checks true, `sudo -u <agent> cat <ledger>` denied,
a commit made during a run is authored by the agent).
In the same GREEN, update:
- `README.md`: the intro sentence that ends "a ledger the agent cannot reach", and the
  `## Storage` section, to state the single/split distinction and link the guide.
- `SECURITY.md`: the trust model's ledger bullet.
- `docs/PRD.md`: R5.2/R5.3 (identity in split mode), R13.3 (ledger home), and a new R13.10
  describing split mode. R13.7 "No daemon" stays.
- `CHANGELOG.md`: an `### Added` entry under `## [Unreleased]`.
EXPECTED FAILURE: `docs split` is rejected as an unknown topic, so the text is the failure
envelope and the assertion fails on `NOPASSWD:SETENV`.

## Execution

This plan is executed through `tdd-cli`. **You run every command below yourself** — do not ask the
user to start the run. `tdd run start` records which model is executing, resolved from your own
session; a run started by anyone else attributes this work to the wrong agent.

    git checkout -b issue-142-split-runner      # first, before anything else
    tdd doctor                                  # must report healthy: true
    tdd run start --plan tasks/issue-142-split-runner.md

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
  green at the plan commit in a fresh worktree (568 passed, 2026-09-21); expect
  `baselines: {tddcli: 0}`.
- Verbs this plan will hit: `write_test`, `create_stub` (cycles 1, 5, 8, 24),
  `write_implementation`, `refactor_or_advance`, `run_sensitivity_check` →
  `tdd sensitivity begin|check|end` (possible on cycle 7),
  `resolve_blocker` → `tdd blocker --kind <regression|target_unfixable|bad_red|plan_defect|tooling|context_exhausted|pre_existing_failure|no_baseline_for_project> --detail '...'`,
  `confirm_cycle_applicable` on a non-existent cycle → `tdd cycle skip --reason`. This plan
  declares no annotation keys beyond the reserved `plan_defect` and `friction_note`.

**Minimal GREEN, per cycle — add this and nothing earlier:**

- cycle 1 parses the file and resolves the role. No ownership or mode check.
- cycle 2 adds the trust check, and nothing else.
- cycle 3 adds `run_argv`/`run_shell` to `LocalActor` and moves the two spawn sites. No file
  methods.
- cycle 4 adds the `LocalActor` file methods and moves the six write sites. No `SudoActor`.
- cycle 5 wraps argv and shell with `-n -E -u <agent> --`. It leaves the subprocess
  environment inherited.
- cycle 6 passes `{**agent_env, **extra}` as the subprocess environment.
- cycle 7 swaps `-E` for `-H` when the agent environment is `None`.
- cycle 8 adds the `SudoActor` file methods and `agentfs`.
- cycle 9 installs the actor in `main` from the role and `SUDO_USER`, with `env=None`.
- cycle 10 adds the flag and feeds `env` to the actor. It does not touch identity.
- cycle 11 adds the `no_agent` refusal. Cycle 12 adds the `PermissionError` envelope.
- cycle 13 forwards every verb with empty stdin. Cycle 14 adds the payload. Cycle 15 adds the
  local-verb table.
- cycle 16 changes where `ledger_path` looks. Cycle 17 adds the mode.
- cycle 18 adds the operator map only; an unmapped agent still resolves as today. Cycle 19
  adds the agent-side claim.
- cycles 20 to 23 add one doctor check each (cycle 20 also adds `result.mode`).
- cycle 24 builds the copy and the marker with no refusals. Cycles 25, 26 and 27 add one
  refusal each. Cycle 28 reads the marker in `metrics`.

## Done-criteria

**Before finishing:** run `tdd log render --out tasks/friction-logs/issue-142-split-runner-friction.md` and `tdd metrics`. Report the plan-fidelity section — declared vs delivered vs skipped — and every integrity event. Do not narrate what the ledger already records.

Then commit the friction log and raise the PR:

    git add tasks/friction-logs/issue-142-split-runner-friction.md
    git commit -m "docs: friction log for issue-142-split-runner"

Then invoke the **`raise-pr` skill** (`/raise-pr`), which runs the quality gates, pushes the
branch and opens the PR against `main`. Do not push or call the GitHub API by hand. If a gate
fails, fix it and re-run the skill — a failed gate is work, not a reason to hand back.

Docs are deliverables, not hopes — cycle 29 owns them. Each of these must be non-empty, or the
PR body says which cycle dropped it and why:

- `git diff --stat origin/main -- docs/split-runner.md`
- `git diff --stat origin/main -- README.md`
- `git diff --stat origin/main -- SECURITY.md`
- `git diff --stat origin/main -- docs/PRD.md`
- `git diff --stat origin/main -- CHANGELOG.md`

Nothing a user sees changes outside the JSON envelope and the docs, so no demo recording is
required. Quote a split-mode `tdd doctor` envelope (from the test fixture) in the PR body, and
say plainly that split mode has not been exercised with a real second uid: that is the manual
checklist in `docs/split-runner.md`.
