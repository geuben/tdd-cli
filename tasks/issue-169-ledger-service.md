---
closes: 169
cycles:
  # -- Phase 1: one domain query layer (behaviour-preserving) -------------------------------
  - n: 1
    project: tddcli
    refactor_cycle: true
    title: "cli.py reaches the ledger only through named Ledger methods"
    files: ["src/tddcli/cli.py", "src/tddcli/ledger.py"]
    commit_refactor: "refactor: cli reaches the ledger through named domain methods"
  - n: 2
    project: tddcli
    refactor_cycle: true
    title: "machine.py and advance.py reach the ledger only through named Ledger methods"
    files: ["src/tddcli/machine.py", "src/tddcli/advance.py", "src/tddcli/ledger.py"]
    commit_refactor: "refactor: the state machine reaches the ledger through named domain methods"
  - n: 3
    project: tddcli
    refactor_cycle: true
    title: "the final close decides the run's outcome before it ends the run"
    files: ["src/tddcli/machine.py", "src/tddcli/advance.py", "src/tddcli/ledger.py"]
    commit_refactor: "refactor: the final close settles blocked-or-complete before ending the run"
  - n: 4
    project: tddcli
    refactor_cycle: true
    title: "fleet reads through a read-only Ledger instead of its own sqlite connection"
    files: ["src/tddcli/fleet.py", "src/tddcli/ledger.py", "src/tddcli/cli.py"]
    modifies_tests:
      - "tests/test_fleet.py::test_open_readonly_cannot_write"
      - "tests/test_fleet.py::test_open_readonly_returns_none_for_missing_db"
    commit_refactor: "refactor: fleet reads through a read-only Ledger"
  - n: 5
    project: tddcli
    title: "no module but ledger.py speaks SQL or imports sqlite3"
    test: "tests/test_ledger_surface.py::test_no_module_but_the_ledger_speaks_sql"
    files: ["src/tddcli/render.py", "src/tddcli/ledger.py"]
    commit_red: "test: only the ledger module speaks SQL"
    commit_green: "refactor: render reaches the ledger through named domain methods"
    commit_refactor: "refactor: tidy the ledger's domain methods"
  # -- Phase 2: sources in the schema (v13) --------------------------------------------------
  - n: 6
    project: tddcli
    title: "a v12 ledger migrates to v13 with every row tagged source 'local'"
    test: "tests/test_ledger_sources.py::test_a_v12_ledger_migrates_with_its_rows_tagged_local"
    files: ["src/tddcli/ledger.py"]
    commit_red: "test: a v12 ledger migrates with its rows tagged local"
    commit_green: "feat: ledger schema v13 records each run's source"
    commit_refactor: "refactor: tidy the v13 migration"
  - n: 7
    project: tddcli
    title: "a Ledger bound to one source never reads another source's runs or contracts"
    test: "tests/test_ledger_sources.py::test_a_source_reads_only_its_own_runs_and_contracts"
    stub_expected: ["src/tddcli/ledger.py"]
    files: ["src/tddcli/ledger.py"]
    commit_red: "test: a source reads only its own runs and contracts"
    commit_green: "feat: source-rooted ledger reads filter by source"
    commit_refactor: "refactor: tidy source filtering"
  - n: 8
    project: tddcli
    title: "two sources claim and cache the same worktree independently"
    test: "tests/test_ledger_sources.py::test_two_sources_claim_and_cache_the_same_worktree_independently"
    files: ["src/tddcli/ledger.py"]
    commit_red: "test: claims and baseline cache are per source"
    commit_green: "feat: claims and the baseline cache are keyed by source"
    commit_refactor: "refactor: tidy per-source claims"
  - n: 9
    project: tddcli
    title: "metrics names each run's source"
    test: "tests/test_ledger_sources.py::test_metrics_names_each_runs_source"
    files: ["src/tddcli/render.py"]
    commit_red: "test: metrics names each run's source"
    commit_green: "feat: metrics names each run's source"
    commit_refactor: "refactor: tidy metrics source field"
  # -- Phase 3: the service and the remote ledger ------------------------------------------
  - n: 10
    project: tddcli
    title: "a source socket answers ping with the source's name and binding"
    test: "tests/test_ledger_service.py::test_a_source_socket_answers_ping_with_its_name"
    stub_expected: ["src/tddcli/service.py", "src/tddcli/wire.py"]
    files: ["src/tddcli/service.py", "src/tddcli/wire.py"]
    modifies_tests: ["tests/test_actor_seams.py::test_only_the_actor_writes_outside_the_tools_own_state"]
    commit_red: "test: a source socket answers ping"
    commit_green: "feat: ledger service listens on a socket per source"
    commit_refactor: "refactor: tidy the service listener"
  - n: 11
    project: tddcli
    title: "every Ledger method is classified for guests and scoped"
    test: "tests/test_ledger_surface.py::test_every_ledger_method_is_classified_and_scoped"
    files: ["src/tddcli/ledger.py"]
    commit_red: "test: every ledger method is classified for guests"
    commit_green: "feat: classify the ledger's methods for guests"
    commit_refactor: "refactor: tidy the guest method registry"
  - n: 12
    project: tddcli
    title: "a guest runner's run lands in the host ledger under its source"
    test: "tests/test_ledger_service.py::test_a_guest_run_lands_in_the_host_ledger_under_its_source"
    files: ["src/tddcli/remote.py", "src/tddcli/runner.py", "src/tddcli/ledger.py", "src/tddcli/service.py", "src/tddcli/wire.py", "src/tddcli/cli.py"]
    commit_red: "test: a guest run lands in the host ledger"
    commit_green: "feat: a runner with ledger_socket keeps its ledger on the host"
    commit_refactor: "refactor: tidy the remote ledger"
  - n: 13
    project: tddcli
    pin_cycle: true
    title: "a guest renders its own friction log through the socket"
    test: "tests/test_ledger_service.py::test_a_guest_renders_its_own_friction_log"
    files: ["src/tddcli/remote.py"]
    commit_red: "test: pin a guest rendering its friction log through the socket"
    commit_refactor: "refactor: tidy remote reads"
  - n: 14
    project: tddcli
    pin_cycle: true
    title: "a blocked guest run can still be unblocked"
    test: "tests/test_ledger_service.py::test_a_blocked_guest_run_can_be_unblocked"
    files: ["src/tddcli/service.py"]
    commit_red: "test: pin unblocking a guest run through the socket"
    commit_refactor: "refactor: tidy remote writes"
  - n: 15
    project: tddcli
    title: "an unreachable ledger socket refuses the verb"
    test: "tests/test_ledger_service.py::test_an_unreachable_socket_refuses_the_verb"
    files: ["src/tddcli/remote.py", "src/tddcli/wire.py", "src/tddcli/cli.py"]
    commit_red: "test: an unreachable ledger socket refuses the verb"
    commit_green: "feat: fail closed when the ledger service is unreachable"
    commit_refactor: "refactor: tidy unreachable handling"
  - n: 16
    project: tddcli
    title: "a guest naming another source's run is refused"
    test: "tests/test_ledger_service.py::test_a_guest_naming_another_sources_run_is_refused"
    files: ["src/tddcli/service.py", "src/tddcli/wire.py", "src/tddcli/remote.py", "src/tddcli/cli.py"]
    commit_red: "test: a guest cannot reach another source's run"
    commit_green: "feat: the service refuses run ids of other sources"
    commit_refactor: "refactor: tidy ownership checks"
  - n: 17
    project: tddcli
    title: "a guest naming another source's cycle or contract is refused"
    test: "tests/test_ledger_service.py::test_a_guest_naming_another_sources_cycle_is_refused"
    files: ["src/tddcli/service.py"]
    commit_red: "test: a guest cannot reach another source's cycle"
    commit_green: "feat: ownership checks cover cycle and contract ids"
    commit_refactor: "refactor: tidy ownership resolution"
  - n: 18
    project: tddcli
    title: "a guest cannot call a host-only method"
    test: "tests/test_ledger_service.py::test_a_guest_cannot_call_a_host_only_method"
    files: ["src/tddcli/service.py"]
    commit_red: "test: guests cannot call host-only ledger methods"
    commit_green: "feat: the service dispatches only guest-classified methods"
    commit_refactor: "refactor: tidy dispatch"
  - n: 19
    project: tddcli
    title: "a guest repo path that is not absolute is refused"
    test: "tests/test_ledger_service.py::test_a_malformed_repo_path_is_refused"
    files: ["src/tddcli/service.py"]
    commit_red: "test: malformed repo paths are refused"
    commit_green: "feat: the service validates the guest's repo path"
    commit_refactor: "refactor: tidy repo validation"
  - n: 20
    project: tddcli
    title: "a guest cannot write to its own completed run"
    test: "tests/test_ledger_service.py::test_a_guest_cannot_write_to_a_completed_run"
    files: ["src/tddcli/service.py"]
    commit_red: "test: a completed run is closed to guest writes"
    commit_green: "feat: the service refuses writes to complete or abandoned runs"
    commit_refactor: "refactor: tidy the closed-run rule"
  - n: 21
    project: tddcli
    title: "a guest may still note a completed run"
    test: "tests/test_ledger_service.py::test_a_guest_may_still_note_a_completed_run"
    files: ["src/tddcli/service.py", "src/tddcli/ledger.py"]
    commit_red: "test: notes on a completed run are still accepted"
    commit_green: "feat: appending a note is exempt from the closed-run rule"
    commit_refactor: "refactor: tidy the note exemption"
  - n: 22
    project: tddcli
    title: "a bound source records the operator-assigned executor"
    test: "tests/test_ledger_service.py::test_a_bound_source_records_the_operator_assigned_executor"
    files: ["src/tddcli/service.py"]
    commit_red: "test: a bound source records the operator's executor"
    commit_green: "feat: the service stamps a bound source's executor on run start"
    commit_refactor: "refactor: tidy executor stamping"
  - n: 23
    project: tddcli
    title: "an unbound source records a guest-claimed operator executor as claimed"
    test: "tests/test_ledger_service.py::test_an_unbound_source_downgrades_a_guest_operator_claim"
    files: ["src/tddcli/service.py"]
    commit_red: "test: a guest cannot claim operator identity"
    commit_green: "feat: an unbound source records guest identity as claimed"
    commit_refactor: "refactor: tidy identity downgrade"
  - n: 24
    project: tddcli
    title: "a bound source stamps the abandoning executor too"
    test: "tests/test_ledger_service.py::test_a_bound_source_stamps_the_abandoning_executor"
    files: ["src/tddcli/service.py"]
    commit_red: "test: abandonment records the bound executor"
    commit_green: "feat: the service stamps the executor on abandonment"
    commit_refactor: "refactor: tidy abandonment stamping"
  - n: 25
    project: tddcli
    title: "claim staleness is judged in the guest, not on the host"
    test: "tests/test_ledger_service.py::test_claim_staleness_is_judged_in_the_guest"
    files: ["src/tddcli/remote.py", "src/tddcli/ledger.py"]
    commit_red: "test: claim staleness is judged where the pid lives"
    commit_green: "feat: the remote ledger judges claim liveness locally"
    commit_refactor: "refactor: tidy claim liveness"
  - n: 26
    project: tddcli
    title: "runner import is refused on a socket-mode runner"
    test: "tests/test_runner_import.py::test_import_is_refused_when_the_ledger_is_on_the_host"
    files: ["src/tddcli/cli.py"]
    commit_red: "test: runner import is refused when the ledger is remote"
    commit_green: "feat: runner import refuses a socket-mode runner"
    commit_refactor: "refactor: tidy runner import refusals"
  - n: 27
    project: tddcli
    title: "a runner config naming both ledger_socket and ledger_home is refused"
    test: "tests/test_split_config.py::test_ledger_socket_and_ledger_home_together_are_refused"
    files: ["src/tddcli/runner.py"]
    commit_red: "test: ledger_socket and ledger_home are exclusive"
    commit_green: "feat: refuse a runner config naming both ledger locations"
    commit_refactor: "refactor: tidy runner config validation"
  - n: 28
    project: tddcli
    title: "doctor on a socket-mode runner names the source it reaches"
    test: "tests/test_split_doctor.py::test_socket_mode_doctor_names_the_source_it_reaches"
    files: ["src/tddcli/cli.py", "src/tddcli/remote.py"]
    commit_red: "test: doctor names the ledger service's source"
    commit_green: "feat: doctor pings the ledger service and names the source"
    commit_refactor: "refactor: tidy socket-mode doctor"
  # -- Phase 4: operator verbs over the admin socket ---------------------------------------
  - n: 29
    project: tddcli
    title: "ledger verbs run locally and refuse without a service config"
    test: "tests/test_ledger_admin.py::test_ledger_verbs_are_never_forwarded_to_a_runner"
    stub_expected: ["src/tddcli/cli.py"]
    files: ["src/tddcli/cli.py", "src/tddcli/service.py"]
    commit_red: "test: ledger verbs stay local and need a service config"
    commit_green: "feat: tdd ledger verb group, answered locally"
    commit_refactor: "refactor: tidy the ledger verb group"
  - n: 30
    project: tddcli
    title: "ledger add-source opens a guest socket through the admin socket"
    test: "tests/test_ledger_admin.py::test_add_source_opens_a_guest_socket"
    files: ["src/tddcli/cli.py", "src/tddcli/service.py", "src/tddcli/wire.py"]
    commit_red: "test: add-source opens a guest socket"
    commit_green: "feat: tdd ledger add-source"
    commit_refactor: "refactor: tidy the admin client"
  - n: 31
    project: tddcli
    title: "ledger sources lists each source with its socket and binding"
    test: "tests/test_ledger_admin.py::test_sources_lists_each_source_and_its_binding"
    files: ["src/tddcli/cli.py", "src/tddcli/service.py"]
    commit_red: "test: ledger sources lists sources"
    commit_green: "feat: tdd ledger sources"
    commit_refactor: "refactor: tidy source listing"
  - n: 32
    project: tddcli
    title: "ledger bind changes a source's executor for its next run"
    test: "tests/test_ledger_admin.py::test_bind_changes_the_executor_for_the_next_run"
    files: ["src/tddcli/cli.py", "src/tddcli/service.py"]
    commit_red: "test: bind changes a source's executor"
    commit_green: "feat: tdd ledger bind"
    commit_refactor: "refactor: tidy binding"
  - n: 33
    project: tddcli
    title: "ledger remove-source closes and removes its socket"
    test: "tests/test_ledger_admin.py::test_remove_source_closes_its_socket"
    files: ["src/tddcli/cli.py", "src/tddcli/service.py"]
    commit_red: "test: remove-source closes the guest socket"
    commit_green: "feat: tdd ledger remove-source"
    commit_refactor: "refactor: tidy source removal"
  - n: 34
    project: tddcli
    title: "sources and bindings survive a service restart"
    test: "tests/test_ledger_admin.py::test_sources_survive_a_service_restart"
    files: ["src/tddcli/service.py"]
    commit_red: "test: sources survive a service restart"
    commit_green: "feat: the service persists its sources"
    commit_refactor: "refactor: tidy source persistence"
  - n: 35
    project: tddcli
    title: "the admin socket is mode 600 and guest sockets are mode 660"
    test: "tests/test_ledger_admin.py::test_socket_modes"
    files: ["src/tddcli/service.py"]
    commit_red: "test: admin and guest socket modes"
    commit_green: "feat: the service sets its sockets' modes"
    commit_refactor: "refactor: tidy socket modes"
  - n: 36
    project: tddcli
    title: "ledger serve runs the service until SIGTERM and exits 0"
    test: "tests/test_ledger_admin.py::test_ledger_serve_runs_until_terminated"
    files: ["src/tddcli/cli.py", "src/tddcli/service.py"]
    commit_red: "test: ledger serve runs until SIGTERM"
    commit_green: "feat: tdd ledger serve"
    commit_refactor: "refactor: tidy serve"
  # -- Phase 5: one worker budget for every guest ------------------------------------------
  - n: 37
    project: tddcli
    title: "the service counts worker leases across sources"
    test: "tests/test_remote_leases.py::test_the_service_counts_leases_across_sources"
    files: ["src/tddcli/leases.py", "src/tddcli/remote.py", "src/tddcli/service.py"]
    commit_red: "test: worker leases are counted across guests"
    commit_green: "feat: a socket-mode runner takes its worker lease from the service"
    commit_refactor: "refactor: tidy remote leases"
  - n: 38
    project: tddcli
    title: "a lease ends when its connection closes"
    test: "tests/test_remote_leases.py::test_a_lease_ends_when_its_connection_closes"
    files: ["src/tddcli/service.py"]
    commit_red: "test: a closed lease connection frees its share"
    commit_green: "feat: the service forgets a lease when its connection closes"
    commit_refactor: "refactor: tidy lease release"
  - n: 39
    project: tddcli
    title: "a lease older than the stale limit is not counted"
    test: "tests/test_remote_leases.py::test_a_stale_lease_is_not_counted"
    files: ["src/tddcli/service.py"]
    commit_red: "test: stale leases do not throttle the host"
    commit_green: "feat: the service ignores leases past the stale limit"
    commit_refactor: "refactor: tidy lease staleness"
  - n: 40
    project: tddcli
    title: "a guest's fleet view reports the host's live lease count"
    test: "tests/test_remote_leases.py::test_guest_fleet_reports_the_hosts_lease_count"
    files: ["src/tddcli/leases.py", "src/tddcli/remote.py", "src/tddcli/service.py"]
    commit_red: "test: guest fleet shows host-wide suites"
    commit_green: "feat: a socket-mode lease snapshot comes from the service"
    commit_refactor: "refactor: tidy lease snapshot"
  # -- Phase 6: one history per host ------------------------------------------------------
  - n: 41
    project: tddcli
    title: "ledger metrics on the host covers every source"
    test: "tests/test_ledger_host_views.py::test_ledger_metrics_covers_every_source"
    files: ["src/tddcli/cli.py", "src/tddcli/service.py", "src/tddcli/render.py", "src/tddcli/ledger.py"]
    commit_red: "test: host metrics cover every source"
    commit_green: "feat: tdd ledger metrics"
    commit_refactor: "refactor: tidy host metrics"
  - n: 42
    project: tddcli
    title: "ledger fleet on the host lists active runs of every source"
    test: "tests/test_ledger_host_views.py::test_ledger_fleet_lists_active_runs_of_every_source"
    files: ["src/tddcli/cli.py", "src/tddcli/service.py", "src/tddcli/fleet.py", "src/tddcli/ledger.py"]
    commit_red: "test: host fleet covers every source"
    commit_green: "feat: tdd ledger fleet"
    commit_refactor: "refactor: tidy host fleet"
  - n: 43
    project: tddcli
    title: "ledger log renders any source's run on the host"
    test: "tests/test_ledger_host_views.py::test_ledger_log_renders_any_sources_run"
    files: ["src/tddcli/cli.py", "src/tddcli/service.py"]
    commit_red: "test: host log renders any source's run"
    commit_green: "feat: tdd ledger log"
    commit_refactor: "refactor: tidy host log"
  - n: 44
    project: tddcli
    title: "ledger import brings an existing ledger in as one named source"
    test: "tests/test_ledger_host_views.py::test_ledger_import_retags_a_ledger_as_one_source"
    files: ["src/tddcli/cli.py", "src/tddcli/service.py", "src/tddcli/ledger.py"]
    commit_red: "test: ledger import retags an existing ledger"
    commit_green: "feat: tdd ledger import"
    commit_refactor: "refactor: tidy ledger import"
  - n: 45
    project: tddcli
    title: "ledger import refuses a ledger the host already holds"
    test: "tests/test_ledger_host_views.py::test_ledger_import_refuses_an_existing_host_ledger"
    files: ["src/tddcli/service.py"]
    commit_red: "test: ledger import never overwrites"
    commit_green: "feat: ledger import refuses an existing host ledger"
    commit_refactor: "refactor: tidy import refusal"
  # -- Phase 7: docs -------------------------------------------------------------------------
  - n: 46
    project: tddcli
    refactor_cycle: true
    title: "document split mode across a VM boundary"
    files: ["docs/split-runner.md", "README.md", "CHANGELOG.md"]
    commit_refactor: "docs: split mode across a VM boundary"
---

# Issue 169: split mode across a VM boundary, with the ledger in a host service

## Context

[#169](https://github.com/geuben/tdd-cli/issues/169) follows #142. Split mode today keeps the
ledger with a runner account on the agent's machine. Once agents run in disposable VMs or
containers, the runner has to sit in the guest, because that is where the suites run. A
ledger there disappears with the guest, can never be merged, and is within reach of a guest
agent that is often root-equivalent.

The issue asks for a **ledger service on the host** that owns the SQLite files and is their
only writer. The runner in the guest keeps running suites, gates and git as the agent,
exactly as now, but reads and writes the ledger through a unix socket the host forwards into
the guest. The six properties it wants, and where this plan delivers each one:

| # | Property | Delivered by |
|---|---|---|
| 1 | The ledger never exists in the guest | cycles 12, 15 |
| 2 | A run's source comes from the socket it arrived on | cycles 6–8, 10, 12 |
| 3 | A guest writes only its own runs, never another source's, never its own closed runs | cycles 7, 8, 11, 16–21 |
| 4 | The executor is bound on the host | cycles 22–24, 32 |
| 5 | Fail closed | cycle 15, plus `ledger_refused` in 16 |
| 6 | One history per host, and optionally one worker budget | cycles 37–45 |

## Design decisions (locked)

1. **Domain RPC over one query layer** (user, Phase C). Every ledger access in the codebase
   becomes a named method on `Ledger` (cycles 1–5). The service exposes those methods by name,
   so there is exactly one query layer and the wire carries `{method, args, kwargs}`. No SQL
   ever crosses the socket. Generic `one`/`all`/`insert`/`update`/`db` stay on `Ledger` for
   tests and for host code. They are `HOST_ONLY`, and no module except `ledger.py` calls them
   (guard: cycle 5).
2. **Naming rule for domain methods** (planner; cycles 1–5 must follow it). A method that
   touches rows belonging to one run takes that run as a parameter **named exactly** `run_id`,
   `cycle_id` (a cycle's run) or `contract_id` (a `plan_contract` row). A method that finds
   rows by worktree, project or cache key filters by `self.source` and is listed in
   `SOURCE_ROOTED`. The service's ownership check binds arguments with
   `inspect.signature(method).bind(*args, **kwargs)`, so positional and keyword spellings are
   equivalent. An `id` parameter under any other name is invisible to the check, which is why
   the name is the contract.
3. **Methods later cycles depend on, by name** (planner). Cycle 1 creates `open_ledger(repo)`,
   a module-level factory. It is not `open`, which would shadow the builtin inside
   `ledger.py`. Every `Ledger(...)` construction in `cli.py` goes through it. Cycle 1 also
   creates `start_run(..., executor_model, executor_session, executor_source, ...)`, which
   returns the new run's id, `abandon_run(run_id, *, reason, account, executor_model,
   executor_source, at)` and `reopen_run(run_id, note)`. `abandon_run` does the update, both
   inserts and both claim releases that `cmd_run_abandon` does today, as **one** method.
   `reopen_run` is `resume --unblock`'s update plus its `human_intervention` insert.
   `claim(...)` and `claim_advance(...)` **return `None` when the worktree is already
   claimed** instead of raising `sqlite3.IntegrityError`, because no sqlite exception can
   cross a socket. Their callers in `cli.py` test for `None`. `cmd_note`'s insert becomes
   `add_note(run_id, ...)`, which cycle 21 exempts by name.
4. **Rows keep their shape** (planner). Local methods go on returning `sqlite3.Row`. The wire
   encodes a row as `{"$row": {"cols": [...], "vals": [...]}}` and a set as
   `{"$set": [...]}`. The client decodes them into `wire.Row` and `set`. `wire.Row` supports
   `row["col"]`, `row[i]`, `keys()` and `dict(row)`, so no caller and no test changes.
5. **Sources live in the schema: v13** (user, Phase C). The `MIGRATIONS[12]` entry does this:
   - `run` and `plan_contract` gain `source TEXT NOT NULL DEFAULT 'local'` by `ALTER TABLE`.
   - `baseline_claim`, `advance_claim` and `baseline_cache` are **rebuilt**: new table with
     `source TEXT NOT NULL DEFAULT 'local'`, then copy, drop and rename. Their `UNIQUE`
     becomes `(source, worktree_path)` and `(source, project, tree_hash, config_sha)`.
     SQLite cannot alter a `UNIQUE` constraint in place.
   - Footgun: `SCHEMA` runs **before** the migrations on every open, so it must not put an
     index on any `source` column. On an old ledger that column does not exist yet when
     `SCHEMA` runs. Create no index for `source` at all.

   Single-user mode and #142's single-machine split both use `LOCAL_SOURCE = "local"`.
   `Ledger(repo, source=LOCAL_SOURCE)` is the default. `source=None` is the host's unscoped
   view and is only ever built by the service's admin path and by tests. A
   `SCHEMA_VERSION` bump means the frozen-snapshot referee (Execution).
6. **Why the baseline cache and the claims are per source** (planner). A guest that could
   write a cache row another guest reads could hand that guest a forged baseline and hide a
   regression. Two guests also commonly check out at the same path (`/work/repo`), so a
   claim keyed by worktree alone would let one VM's `run start` block another's.
7. **One daemon, one socket per source, one admin socket** (user, Phase C).
   - `tdd ledger serve` reads `/etc/tdd-cli/ledger.toml`, or `TDD_LEDGER_SERVICE_CONFIG`.
     The trust rule is `runner._require_trusted`: owned by root or the reader, and not group-
     or world-writable. The file has `[service] admin_socket` (required) and `home` (default:
     the service account's `~/.local/share/tdd-cli`).
   - Host ledgers are `<home>/<slug>.sqlite3`, where the slug is the guest's repo path with
     `os.sep` replaced as `ledger_path` does today. Factor that into `ledger.slug(path)`.
   - Sources are added and removed at runtime over the admin socket and persisted in
     `<home>/sources.json`, so a restart re-listens on all of them.
   - A source's identity is the listener the connection arrived on, never anything the
     client sends. The protocol has no `source` field.
8. **Socket mechanics** (planner, from the E-2 probes).
   - Use `socketserver.ThreadingUnixStreamServer` with `daemon_threads = True` **and**
     `block_on_close = False`. Without both, `shutdown()` hangs while a client connection is
     open (probed: the probe hung until killed).
   - Each handler thread opens its own `Ledger`, because a sqlite connection must not cross
     threads.
   - The socket's mode follows the umask (probed: `0o140755`), so `chmod` it explicitly
     after `bind`: admin `0o600`, guest sockets `0o660`. Unlink a stale socket file before
     `bind`.
   - Wire format: newline-delimited JSON, one request and one response per line, over **one
     persistent connection per `RemoteLedger`**. One connection per request would pay an
     ssh-forwarded channel open on each of the hundreds of calls an `advance` makes.
   - The first request on a ledger connection is `{"method": "open", "args": [repo_path]}`.
     `ping`, `lease` and `lease_snapshot` need no `open`.
9. **Refusal vocabulary** (planner).
   - The service answers `{"ok": false, "refusal": <code>, "error": <text>}` with one of
     these codes:
     - `method_not_allowed`: not in `GUEST_READS | GUEST_WRITES`.
     - `foreign_run`: the run, cycle or contract belongs to another source, **or does not
       exist**, so existence never leaks.
     - `run_closed`.
     - `bad_repo`.
   - The client raises `wire.LedgerRefused(refusal, error)`. `cli.main` turns it into
     `failure(error, reason="ledger_refused", refusal=<code>)`, which is under `result`.
   - A connection failure raises `wire.LedgerUnreachable`, and `main` turns it into
     `failure(..., reason="ledger_unreachable")`.
   - Nothing on the guest side ever falls back to `ledger_home()`.
10. **The guest registry** (planner). `ledger.py` declares four frozensets of method names:
    `GUEST_READS`, `GUEST_WRITES`, `HOST_ONLY` and `SOURCE_ROOTED`.
    - Every public `Ledger` method is in exactly one of the first three.
    - Every guest method has a `run_id`/`cycle_id`/`contract_id` parameter or is in
      `SOURCE_ROOTED`.
    - `get_meta` is a guest read, because `metrics` reads the import marker. `set_meta` is
      host-only.
11. **Closed means `outcome IN ('complete', 'abandoned')`, judged before the method runs**
    (planner, from the E-2 probe below). `blocked` is not closed: `resume --unblock` and
    `resume --accept-failures` write to blocked runs by design. `add_note` is the single
    exemption, because `tdd note` after completion is documented behaviour. `cmd_note` says
    "Note recorded. Run `tdd log render`."
12. **Executor identity is stamped by the service** (planner, issue property 4).
    - For `start_run` and `abandon_run` from a source with a binding, the service replaces
      the executor arguments with `(model=<binding>, session=None, source="operator")`.
    - With no binding, a guest-sent `executor_source == "operator"` becomes `"claimed"`.
      Everything else passes through. A guest's own `[executor]` table is guest root's to
      edit.
    - No guest method writes executor columns otherwise.
    - The guest's `executor_unknown` event and its local resolution are unchanged.
13. **Claim liveness is judged where the pid lives** (planner). `active_claim` and
    `active_advance_claim` are composed on the caller's side: a guest read of the raw row
    (`claim_row` / `advance_claim_row`, `SOURCE_ROOTED`) plus the module-level
    `claim_is_stale`. `RemoteLedger` defines those two methods itself and does not proxy
    them. On the host the guest's hostname differs, so `claim_is_stale` would fall back to 60
    minutes of age.
14. **Leases** (user: build now). In socket mode `leases.worker_lease()` opens its own
    connection to the source socket and sends `{"method": "lease"}`.
    - The service counts open lease connections across **all** sources and answers
      `{"workers": max(1, cores // live)}`. `cores` is `leases._total_cores()` in the
      service's process.
    - There is **no release message**: a lease ends when its connection closes, which is
      what a dead VM does. A lease older than `leases.STALE_AFTER_S` is not counted.
    - `leases.snapshot()` in socket mode asks the service (`lease_snapshot`).
    - `named_lease` stays guest-local (evidence: it guards exclusive use of a resource the
      suite runs against, and in a guest that resource is the guest's own).
15. **Socket-mode runner config** (planner). `[runner] ledger_socket = "<path>"`. It is
    mutually exclusive with `ledger_home`; both together raise `RunnerConfigError`. The
    `[runner]` user/sudo split is unchanged.
16. **Operator verbs: `tdd ledger …`** (planner).
    - The verbs are `serve`, `sources`, `add-source <name> --socket <path> [--executor M]`,
      `remove-source <name>`, `bind <name> --executor M`, `fleet`, `metrics [--repo SLUG]`,
      `log --repo SLUG --run N [--out FILE]` and `import <file> --source <name>`.
    - All but `serve` are admin-socket requests.
    - `ledger` joins `LOCAL_VERBS`, so it is never forwarded to a runner. `_refusal` exempts
      it the way it exempts `runner`.
    - With no service config, every `ledger` verb fails with `reason: "no_service"`.
17. **Host views read through the daemon** (planner, follows from 7 and 14).
    - The daemon holds the lease counts, so `tdd ledger fleet|metrics|log` are admin
      requests.
    - The daemon opens each `<home>/*.sqlite3` with `source=None`: read-only
      (`ledger.open_readonly`) for `fleet`, and `metrics`/`log` against the host view.
    - Each run entry carries `source`. Results are keyed by repo slug.
18. **`runner import` in socket mode is refused** with `reason: "ledger_remote"`, checked
    after `not_split` and before `operator_only`. The host's `tdd ledger import` replaces it.
    That import copies the file to `<home>/<name>` with `import_legacy`'s backup-API copy,
    migrates it, retags every `local` row of `run`/`plan_contract` to the named source,
    clears the copied claim tables and writes the `pre_split_import` marker. It refuses an
    existing target with `reason: "ledger_exists"`. There is no merge (issue: "There is no
    merge").
19. **New modules** (planner).
    - `wire.py`: codec, client connection, `Row`, `LedgerRefused`, `LedgerUnreachable`.
    - `remote.py`: `RemoteLedger` and the lease client.
    - `service.py`: the daemon, dispatch, policy, leases, admin, persistence and config.
    - `service.py` writes socket files and `sources.json`, which is the tool's own state, so
      cycle 10 adds it to `OWN_STATE` in `tests/test_actor_seams.py`.
    - None of the three imports `sqlite3`: cycle 5's guard holds for them too.

## Deliberate scope cuts (do not build)

- **Path-independent repository identity.** Host ledgers are keyed by the guest's repo path.
  Two guests checking out *different* repositories at the same path share a host file, kept
  apart only by source. Premise: **named non-goal**. #169 asks for one history per host keyed
  as today, and #142's planning recorded a path-independent key as a possible later step,
  not part of this line of work.
- **Socket forwarding itself** (ssh `-R`, vsock, bind mounts). Premise: **unreachable**. The
  run has no VM or ssh pair to forward through. Cycle 46 documents the setups. The service's
  side of the boundary (a socket per source, its mode, identity by listener) is built and
  tested.
- **Unbinding an executor** (`bind --clear`). Premise: **named non-goal**. The issue asks
  only that the operator can bind one, and a disposable guest gets a fresh source.

## Fake and real divergence

| Seam | Fake behaviour | Real behaviour | Untested production path | Ruling |
|---|---|---|---|---|
| `ledger_service` fixture | `service.Service` in a thread of the test process | `tdd ledger serve` as its own process | process lifecycle, signals | needs an integration pin: cycle 36 runs the real verb in a subprocess |
| `sudo_shim` | runs the command as the same uid | real sudo drops to the agent | uid change | acceptable: #142's doctor checks cover it on real machines |
| guest and host in one process | share `socket.gethostname()` and env | different hosts | hostname-based claim staleness | acceptable: cycle 25 uses the `Ledger._claim_is_stale` seam to tell host-side from guest-side judgement |
| socket path | `/tmp/tdd-*/vm-1.sock` | a forwarded socket | the forwarding transport | acceptable: scope cut above |

## Cycles

Shared seams are written in the RED of the cycle that first needs them, in
`tests/conftest.py` (test code, staged in RED):

- **`ledger_service`** (first used by cycle 12; cycle 10 builds its service inline):
  - The socket directory is `Path(tempfile.mkdtemp(dir="/tmp", prefix="tdd-"))`, never
    `tmp_path`. Probed: a socket under `tmp_path` is 112 bytes and `bind` fails with
    `OSError: AF_UNIX path too long`; macOS allows 104.
  - It writes `ledger.toml` with `home = tmp_path / "host-ledgers"` and
    `admin_socket = <dir>/admin.sock`, and sets `TDD_LEDGER_SERVICE_CONFIG`.
  - It starts `service.Service` in a thread, stops it in teardown and removes the directory.
  - It exposes `.service`, `.home`, `.dir` and `.config`.
- **`split_guest`**:
  - It builds on `split_runner`'s environment (`SUDO_USER`, `SUDO_UID`, the shim). It adds
    source `vm-1` through `ledger_service.service.add_source("vm-1", <dir>/vm-1.sock,
    executor=None)`.
  - It writes a runner.toml with `ledger_socket` and **no** `ledger_home`.
  - It sets `HOME` to `tmp_path / "guest-home"`. Before cycle 12 the runner falls back to
    `Path.home()/.local/share/tdd-cli`, and that must never be the developer's real home.
  - It exposes `.socket`, `.config` and `.guest_home`.

To switch a test's guest to a second source, rewrite the runner config's `ledger_socket`.
`runner.load()` reads the file on every call.

### Phase 1: one domain query layer

**Cycle 1 (refactor): cli.py through named Ledger methods.**
- Every SQL string and every `ledger.one/all/insert/update` call in `src/tddcli/cli.py`
  becomes a named method in `ledger.py`, following decisions 2 and 3.
- Every `Ledger(...)` in `cli.py` becomes `ledger_mod.open_ledger(...)`.
- `cli.py` stops importing `sqlite3`: claims return `None` on conflict.
- Behaviour is preserved and the existing suite is the guard: `tests/test_run_abandon.py`,
  `tests/test_concurrent_advance.py`, `tests/test_run_claim.py` and
  `tests/test_split_identity.py` cover the changed paths.
- Discovery: `grep -nE 'ledger\.(one|all|insert|update)\(|"(SELECT|UPDATE|INSERT|DELETE)' src/tddcli/cli.py`
  (today: 12 inserts, 10 updates, 11 `one`, 2 `all`, plus 2 `IntegrityError` handlers).

**Cycle 2 (refactor): machine.py and advance.py through named methods.**
- Same rule for `src/tddcli/machine.py` (11 inserts, 5 updates, 5 `one`, 2 `all`) and
  `src/tddcli/advance.py` (1 insert, 2 updates, 6 `one`, 2 `all`).
- Discovery: `grep -nE '(self|engine)\.ledger\.(one|all|insert|update)\(' src/tddcli/machine.py src/tddcli/advance.py`.

**Cycle 3 (refactor): the final close decides the outcome before ending the run.**
- Today `_handle_refactor` calls `engine.close_cycle(cycle)`, which sets the run
  `outcome='complete'`. Only then does it run `close_undeclared_gate`, insert the
  `undeclared_file_uncommitted` blocker and flip the run to `blocked`, which writes to a
  completed run.
- Restructure: when the cycle is the last declared one, evaluate the gate (and its
  `undeclared_file_dropped` event) first. Insert the blocker if needed. Then close the cycle
  and end the run with `outcome='blocked'` or `'complete'` directly.
- The end state is identical: cycle closed, run `ended_at` set, the same outcome and rows.
- Guards: `tests/test_undeclared_close_gate.py::test_uncommitted_flagged_file_blocks_at_close`
  and `::test_a_vanished_flagged_file_is_reported_not_blocked`.
- If any existing test fails because the end state differs, that is a blocker
  (`plan_defect`), not a refactor commit.

**Cycle 4 (refactor): fleet through a read-only Ledger.**
- `fleet.open_readonly` moves to `ledger.open_readonly(path) -> Ledger | None`. It opens
  `file:<path>?mode=ro`, never runs `SCHEMA` or migrations, and returns `None` for a missing
  file.
- `fleet.summarise` takes that reader, which may be `None`, and calls named methods for its
  three queries. `cmd_fleet` passes `open_readonly(ledger_path(...))`.
- `fleet.py` stops importing `sqlite3`.
- Update the two tests in `modifies_tests` to call `ledger.open_readonly`. The write attempt
  goes through `reader.db.execute(...)` and still expects `sqlite3.OperationalError`. Do not
  weaken either assertion.

**Cycle 5: `test_no_module_but_the_ledger_speaks_sql`.**
- New file `tests/test_ledger_surface.py`. For every `src/tddcli/**/*.py` except `ledger.py`,
  it walks the AST and collects:
  - any `import sqlite3` / `from sqlite3`;
  - any string constant matching
    `^\s*(SELECT|INSERT\s+INTO|UPDATE\s+\w+\s+SET|DELETE\s+FROM|CREATE\s+(TABLE|INDEX)|ALTER\s+TABLE|PRAGMA)\b`;
  - any attribute `one|all|insert|update|db|_write` whose receiver's name (a `Name` id, or
    an `Attribute`'s `attr`) is `ledger`.
- Single assertion: the offender map is `{}`.
- Probed on today's tree (scratch copy): it flags exactly `advance.py`, `cli.py`,
  `fleet.py`, `machine.py` and `render.py`, with no false positives in `snapshot.py`,
  `gitutil.py`, `config.py` or `adapters/`.
- GREEN moves `render.py`'s 25 reads into named methods.
- EXPECTED FAILURE: ``AssertionError`` whose diff names only `render.py`, after cycles 1–4.

### Phase 2: sources in the schema

**Cycle 6: `test_a_v12_ledger_migrates_with_its_rows_tagged_local`.**
- Follow `tests/test_release_surface.py::test_invocation_gains_others_observed_column`'s
  pattern:
  1. Create a fresh ledger and insert a `plan_contract`, a `run` and a `baseline_claim` row.
  2. Set `schema_version` to `'12'`.
  3. If they exist, `ALTER TABLE … DROP COLUMN source` on `run`/`plan_contract`, and
     rebuild the three claim/cache tables in their v12 DDL (copied from `SCHEMA` at HEAD).
  4. Close and reopen.
- Single assertion: `{"run": ..., "plan_contract": ..., "baseline_claim": ...}` built from
  `dict(row).get("source")` equals `{"run": "local", "plan_contract": "local",
  "baseline_claim": "local"}`.
- GREEN:
  - `SCHEMA_VERSION = 13`.
  - The new columns in `SCHEMA`'s DDL.
  - `MIGRATIONS[12]` as in decision 5.
  - No reads change.
- EXPECTED FAILURE: `AssertionError: {'run': None, 'plan_contract': None, 'baseline_claim': None} != {...}`
  (probed: today's rows have no `source` key).

**Cycle 7: `test_a_source_reads_only_its_own_runs_and_contracts`.**
- Two `Ledger(repo, source="a")` / `Ledger(repo, source="b")` objects on one file.
- Through A's named methods: register a contract, start a run at worktree W, record a
  baseline and a full-suite invocation.
- Single assertion: B's view, as a dict of these, equals all-empty:
  - the active run at W (`active_run`);
  - the latest contract for that plan path;
  - `previous_baseline(W, project, big_id)`;
  - `max_suite_duration_ms(project)`;
  - the latest run at W.
- `stub_expected: src/tddcli/ledger.py`: add `source: str | None = LOCAL_SOURCE` to
  `Ledger.__init__`, unreferenced. Probed: without it the test dies with `TypeError:
  Ledger.__init__() got an unexpected keyword argument 'source'`.
- GREEN: inserts of `run`/`plan_contract` stamp `self.source`. Every `SOURCE_ROOTED` read
  adds `AND source = ?` when `self.source is not None`.
- EXPECTED FAILURE: `AssertionError`: B sees A's run, contract, baseline and duration.

**Cycle 8: `test_two_sources_claim_and_cache_the_same_worktree_independently`.**
- A claims W and caches a baseline for `(project, tree, config)`.
- Single assertion: `(B.claim(W, ...) is not None, B.cached_baseline(project, tree, config))
  == (True, None)`.
- GREEN: claims and the cache stamp and filter `source`. Their `UNIQUE` already includes it
  from cycle 6.
- EXPECTED FAILURE: `AssertionError: (True, <Row>) != (True, None)` or `(False, …)`. The
  claim conflict is caught as `None` per decision 3, and the cache row is shared.
  Probed today: `IntegrityError: UNIQUE constraint failed: baseline_claim.worktree_path`. That
  raises only before cycle 1's `None` conversion and cycle 6's rebuild.

**Cycle 9: `test_metrics_names_each_runs_source`.**
- Single-mode repo, one `run start` via `run_cli`.
- Single assertion: `[r.get("source") for r in run_cli(repo, "metrics")["result"]["runs"]] == ["local"]`.
- GREEN adds `"source": run["source"]` to `render.metrics`' per-run dict.
- EXPECTED FAILURE: `AssertionError: [None] != ['local']`.

### Phase 3: the service and the remote ledger

**Cycle 10: `test_a_source_socket_answers_ping_with_its_name`.**
- New file `tests/test_ledger_service.py`. The service is built **in the test body**: the
  fixture comes in cycle 12, and a fixture error is not a RED.
- The test uses a `/tmp` short dir, `service.load_config(<toml>)`, `svc = Service(cfg)`,
  `svc.start()`, then `svc.add_source("vm-1", <dir>/vm-1.sock, executor=None)`, then
  `wire.call(<dir>/vm-1.sock, "ping")`. It stops the service in `finally`.
- Single assertion: the reply equals `{"source": "vm-1", "executor": None}`.
- Stubs:
  - `service.py`: `load_config`, `Service.__init__/start/stop/add_source` raising
    `NotImplementedError`.
  - `wire.py`: `call(socket_path, method, *args, **kwargs)` raising `NotImplementedError`.
- GREEN:
  - The admin socket and the per-source listeners use the decision-8 mechanics.
  - `ping` is answered from the listener's own source.
  - Add `"service.py"` to `OWN_STATE` in `tests/test_actor_seams.py`: the service unlinks a
    stale socket and makes its home, which is its own state.
- EXPECTED FAILURE: `NotImplementedError` from `Service.start`.

**Cycle 11: `test_every_ledger_method_is_classified_and_scoped`.**
- In `tests/test_ledger_surface.py`, read the four sets with
  `getattr(ledger, NAME, frozenset())`, so their absence is an assertion and not an
  `AttributeError`.
- Single assertion: a list of problems is `[]`. The problems are:
  - each public `Ledger` method (callable, no leading `_`, defined on the class) not in
    exactly one of READS/WRITES/HOST_ONLY;
  - each guest method with no `run_id|cycle_id|contract_id` parameter that is not in
    `SOURCE_ROOTED`.
- GREEN declares the sets in `ledger.py`, per decisions 2, 10 and 13.
- EXPECTED FAILURE: `AssertionError` listing every public method as unclassified.

**Cycle 12: `test_a_guest_run_lands_in_the_host_ledger_under_its_source`.**
- Uses the fixtures `repo`, `split_guest` and `ledger_service` (written here). `run_cli(repo,
  "run", "start", "--plan", <plan>)`, then
  `reader = ledger.open_readonly(ledger_service.home / f"{ledger.slug(repo)}.sqlite3")`.
- Single assertion: `reader is not None and [r["source"] for r in <its runs>] == ["vm-1"]`.
- GREEN:
  - `RunnerConfig.ledger_socket`.
  - `ledger.open_ledger(repo)` returns `remote.RemoteLedger(socket, repo)` for a runner with
    a socket.
  - `RemoteLedger` proxies attribute calls through `wire`.
  - The service handles `open` and dispatches **any** `Ledger` method by name on a
    `Ledger(repo, source=<listener's>, path=<home>/<slug>.sqlite3)`.
  - `RemoteLedger.path` is the socket path only. Cycle 28 adds the source.
  - `cmd_fleet` and doctor use `open_ledger`/the reader rather than `ledger_path` when a
    socket is configured.
- EXPECTED FAILURE: `AssertionError` with `reader` `None`. The guest wrote to
  `<guest-home>/.local/share/tdd-cli`, because the unknown `ledger_socket` key is ignored
  today.

**Cycle 13 (pin): `test_a_guest_renders_its_own_friction_log`.**
- After a guest `run start`, `run_cli_text(repo, "log", "render")` contains the plan path.
- Expected to pass on arrival: every read `render` makes is classified (cycle 11) and
  proxied (cycle 12). This is what Done-criteria rely on inside a guest.
- If it fails, a read is misclassified. Fix the classification as a blocker
  (`plan_defect`), not here.

**Cycle 14 (pin): `test_a_blocked_guest_run_can_be_unblocked`.**
- Guest `run start`, `tdd blocker --kind environment --detail x`, then
  `tdd resume --unblock --note fixed`.
- Single assertion: `result.resumed is True`.
- It passes on arrival, because there is no closed-run rule yet. It must stay green through
  cycle 20, whose rule exempts `blocked` (decision 11).

**Cycle 15: `test_an_unreachable_socket_refuses_the_verb`.**
- `split_guest` with `ledger_socket` rewritten to `<dir>/absent.sock`, then
  `run_cli(repo, "run", "start", "--plan", …)`.
- Single assertion: `out["result"]["reason"] == "ledger_unreachable"`. The guest home also
  holds no `*.sqlite3`; assert that inside the same dict comparison
  `{"reason": …, "local_ledgers": []}`.
- GREEN: `wire` raises `LedgerUnreachable` on `FileNotFoundError` / `ConnectionRefusedError`
  / a closed connection, and `main` catches it.
- EXPECTED FAILURE: `FileNotFoundError: [Errno 2] No such file or directory`, raised out of
  `main` through `run_cli`. The in-process CLI does not catch it today.

**Cycle 16: `test_a_guest_naming_another_sources_run_is_refused`.**
- Add source `vm-2`. Guest `vm-1` starts a run. Switch the guest config to `vm-2`, then
  `run_cli(repo, "run", "abandon", "--run", <id>, "--reason", "x")`.
- Single assertion: `{k: out["result"].get(k) for k in ("reason", "refusal")} ==
  {"reason": "ledger_refused", "refusal": "foreign_run"}`.
- GREEN: ownership check for `run_id` parameters only, the `LedgerRefused` round trip, and
  `main`'s `ledger_refused`.
- EXPECTED FAILURE: `AssertionError`. Today `vm-2` reads `vm-1`'s run, and the worktree
  matches, so it abandons it with `ok: true`.

**Cycle 17: `test_a_guest_naming_another_sources_cycle_is_refused`.**
- After a `vm-1` run start, a `wire` connection on `vm-2` sends `open(repo)` and then any
  `GUEST_READS` method with a `cycle_id` parameter, using `vm-1`'s open cycle id. Read that
  id from the host file.
- Single assertion: the raised `LedgerRefused.refusal == "foreign_run"`, caught with
  `pytest.raises` and its value compared.
- GREEN extends the check to `cycle_id` and `contract_id`.
- EXPECTED FAILURE: `Failed: DID NOT RAISE`.

**Cycle 18: `test_a_guest_cannot_call_a_host_only_method`.**
- `wire` on `vm-1`: `open(repo)`, then `insert` with `"run"` and any columns.
- Single assertion: `refusal == "method_not_allowed"`.
- GREEN: dispatch only `GUEST_READS | GUEST_WRITES`.
- EXPECTED FAILURE: `Failed: DID NOT RAISE` (cycle 12 dispatches anything).

**Cycle 19: `test_a_malformed_repo_path_is_refused`.**
- For each of `["relative/repo", "", "/a\x00b", "/a\nb"]`, open a fresh `wire` connection to
  `vm-1`, call `open(path)` and collect the refusal code, or `"accepted"`.
- Single assertion: the list is `["bad_repo"] * 4`.
- Accepted form: an absolute path with no NUL or newline (every other test). Rejected forms:
  exactly these four.
- EXPECTED FAILURE: `AssertionError` with `"accepted"` entries, or a sqlite error for the NUL
  case surfaced as a non-`bad_repo` refusal.

**Cycle 20: `test_a_guest_cannot_write_to_a_completed_run`.**
- After a `vm-1` run start, mark it complete through a host view:
  `Ledger(…, source=None, path=<host file>).update("run", id, ended_at=now(),
  outcome="complete")`.
- `wire` on `vm-1` then calls `event(run_id, None, "x", "")`.
- Single assertion: `refusal == "run_closed"`.
- GREEN: for `GUEST_WRITES` with an ownership parameter, resolve the run and refuse when its
  outcome is `complete` or `abandoned`. That rule exactly, not `ended_at IS NOT NULL`:
  cycle 14's pin must stay green.
- EXPECTED FAILURE: `Failed: DID NOT RAISE`.

**Cycle 21: `test_a_guest_may_still_note_a_completed_run`.**
- Same arrangement, then `run_cli(repo, "note", "after the fact")`.
- Single assertion: `out["result"]["noted"] is True`.
- GREEN exempts `add_note` by name, and nothing else.
- E-2 evidence: simulating the closed-run rule on today's code failed 16 tests, all from
  three paths. `run abandon` writes after it ends the run (fixed by decision 3's
  `abandon_run`). The final close flips a completed run to blocked (fixed by cycle 3).
  `tdd note` after completion (this exemption).
- EXPECTED FAILURE: `KeyError: 'noted'`. The result is a `ledger_refused` failure; assert
  with `.get("noted")` to keep it an `AssertionError`.

**Cycle 22: `test_a_bound_source_records_the_operator_assigned_executor`.**
- `add_source("vm-b", …, executor="model-x")`, the guest on `vm-b`, `run start`.
- Single assertion: the host row's `(executor_model, executor_source) == ("model-x",
  "operator")`.
- EXPECTED FAILURE: `AssertionError: ('pytest-executor', 'claimed') != ('model-x', 'operator')`.
  `TDD_EXECUTOR_MODEL` is pinned by conftest, and the split runner labels it `claimed`.

**Cycle 23: `test_an_unbound_source_downgrades_a_guest_operator_claim`.**
- The guest runner.toml also has `[executor]` mapping `current_user()` to `"guest-says"`.
  Run start on unbound `vm-1`.
- Single assertion: the host row is `("guest-says", "claimed")`.
- EXPECTED FAILURE: `AssertionError: ('guest-says', 'operator') != ('guest-says', 'claimed')`.

**Cycle 24: `test_a_bound_source_stamps_the_abandoning_executor`.**
- Bound `vm-b`, run start, `tdd run abandon --reason x`.
- Single assertion: the host `abandonment` row's `(executor_model, executor_source) ==
  ("model-x", "operator")`.
- EXPECTED FAILURE: `AssertionError` with `('pytest-executor', 'claimed')`.

**Cycle 25: `test_claim_staleness_is_judged_in_the_guest`.**
- Monkeypatch `ledger.Ledger._claim_is_stale` to `staticmethod(lambda *a: False)`. That
  stands for "the host cannot tell". The module-level `ledger.claim_is_stale` stays real.
- Insert a `baseline_claim` for the repo worktree into the host file with `source="vm-1"`,
  this hostname and a dead pid. Use the dead-pid helper pattern from
  `tests/test_fleet.py::test_fleet_and_progress_agree_on_a_dead_collector`.
- Then guest `run_cli(repo, "progress", "--json")`.
- Single assertion: `out["result"]["stale"] is True`.
- EXPECTED FAILURE: `AssertionError`. The service evaluates `active_claim` with the patched
  method and says `False`.

**Cycle 26: `test_import_is_refused_when_the_ledger_is_on_the_host`.**
- In `tests/test_runner_import.py`: `split_guest`, then `delenv` `SUDO_USER`/`SUDO_UID`
  (logged in as the runner), then `run_cli(repo, "runner", "import", <a legacy file>)`.
- Single assertion: `out["result"]["reason"] == "ledger_remote"`.
- EXPECTED FAILURE: `AssertionError: None != 'ledger_remote'`. Today it imports into the
  guest home.

**Cycle 27: `test_ledger_socket_and_ledger_home_together_are_refused`.**
- In `tests/test_split_config.py`, follow `test_an_untrusted_runner_config_is_refused`: a
  config with both keys, then `pytest.raises(RunnerConfigError, match="ledger_socket")`
  around `runner.load()`.
- EXPECTED FAILURE: `Failed: DID NOT RAISE`.

**Cycle 28: `test_socket_mode_doctor_names_the_source_it_reaches`.**
- `split_guest`, then `run_cli(repo, "doctor")`.
- Single assertion: the `ledger reachable` check is `ok` and its detail contains `"vm-1"`.
- GREEN: in socket mode, doctor pings and renders `socket <path> (source <name>)`.
- EXPECTED FAILURE: `AssertionError` (detail is the socket path alone).

### Phase 4: operator verbs

New file `tests/test_ledger_admin.py`. Each test drives `run_cli(repo, "ledger", …)` with the
`ledger_service` fixture, except cycle 29.

**Cycle 29: `test_ledger_verbs_are_never_forwarded_to_a_runner`.**
- Fixture `split_client` (forwarding stub), no service config: `TDD_LEDGER_SERVICE_CONFIG`
  points at a missing file.
- Single assertion: `out.get("result", {}).get("reason") == "no_service"`. The stub would
  have answered `{"ok": true, "stub": true}`.
- `stub_expected: src/tddcli/cli.py`: the whole `ledger` subparser group (`serve`,
  `sources`, `add-source`, `remove-source`, `bind`, `fleet`, `metrics`, `log`, `import`),
  each with a handler returning `failure("not implemented", reason="not_implemented")`.
  That handler is the repo's stub convention.
- GREEN: `ledger` in `LOCAL_VERBS`, `_refusal` exempts it, and every `ledger` handler first
  loads the service config, failing `no_service` when it is absent.
- EXPECTED FAILURE: `AssertionError: None != 'no_service'` (the stub answered).

**Cycle 30: `test_add_source_opens_a_guest_socket`.**
- `run_cli(repo, "ledger", "add-source", "vm-2", "--socket", <dir>/vm-2.sock)`, then
  `wire.call(<dir>/vm-2.sock, "ping")`.
- Single assertion: the reply is `{"source": "vm-2", "executor": None}`.
- EXPECTED FAILURE: `wire.LedgerUnreachable`: the verb answered `not_implemented`, so no
  socket exists.

**Cycle 31: `test_sources_lists_each_source_and_its_binding`.**
- Single assertion: `result.sources == [{"name": "vm-1", "socket": …, "executor": None},
  {"name": "vm-2", "socket": …, "executor": "m"}]`, sorted by name.
- EXPECTED FAILURE: `KeyError: 'sources'`. Read it with `.get` so it is an
  `AssertionError: None != [...]`.

**Cycle 32: `test_bind_changes_the_executor_for_the_next_run`.**
- `ledger bind vm-1 --executor m2`, then `ping` on `vm-1`.
- Single assertion: `executor == "m2"`.
- EXPECTED FAILURE: `AssertionError: None != 'm2'`.

**Cycle 33: `test_remove_source_closes_its_socket`.**
- `ledger remove-source vm-1`.
- Single assertion: `(socket_path.exists(), <wire.call raises LedgerUnreachable>) ==
  (False, True)`.
- EXPECTED FAILURE: `AssertionError: (True, False) != (False, True)`.

**Cycle 34: `test_sources_survive_a_service_restart`.**
- `add_source("vm-1", …, executor="m")`, `stop()`, then a new `Service(same config).start()`
  and `ping` on `vm-1`.
- Single assertion: the reply is `{"source": "vm-1", "executor": "m"}`.
- EXPECTED FAILURE: `wire.LedgerUnreachable`; assert via a helper that returns the refusal
  name, to keep it an `AssertionError`.

**Cycle 35: `test_socket_modes`.**
- Single assertion: `{"admin": stat.S_IMODE(...), "vm-1": ...} == {"admin": 0o600,
  "vm-1": 0o660}`.
- EXPECTED FAILURE: `AssertionError` with `0o755`. Probed: the mode follows the umask unless
  set. Cycle 10 might already chmod. If this test passes on arrival, the tool runs the
  sensitivity check; let it.

**Cycle 36: `test_ledger_serve_runs_until_terminated`.**
- `subprocess.Popen([sys.executable, "-c", "import sys; from tddcli.cli import main; sys.exit(main(sys.argv[1:]))", "ledger", "serve"], env={…, "TDD_LEDGER_SERVICE_CONFIG": cfg})`.
  There is no `python -m tddcli` entry point.
- Poll `wire.call(admin, "ping")` for up to 10 s, then `send_signal(SIGTERM)` and
  `wait(timeout=10)`.
- Single assertion: `(answered_ping, returncode) == (True, 0)`.
- GREEN: `serve` builds the `Service`, installs a SIGTERM handler that stops it, and blocks
  until stopped.
- EXPECTED FAILURE: `AssertionError: (False, 1) != (True, 0)`. The stub's
  `not_implemented` exits 1 at once.

### Phase 5: one worker budget

New file `tests/test_remote_leases.py`, with `monkeypatch.setenv("TDD_CORE_BUDGET", "12")`.
The service runs in-process, so it sees the same variable.

**Cycle 37: `test_the_service_counts_leases_across_sources`.**
- Hold `leases.worker_lease()` as guest `vm-1` (`split_guest`).
- Then point `TDD_LEASE_DIR` at a **different** directory, so two guests share no filesystem.
  Without this, local leases would count each other and the test would pass on arrival.
- Rewrite the guest config to `vm-2` and take a second `worker_lease()`.
- Single assertion: the second yields `6`.
- GREEN: in socket mode `worker_lease` holds a lease connection. The service counts open
  lease connections, and **only increments**. Release is cycle 38.
- EXPECTED FAILURE: `AssertionError: 12 != 6`.

**Cycle 38: `test_a_lease_ends_when_its_connection_closes`.**
- Take and leave a lease on `vm-1`, then take one on `vm-2`.
- Single assertion: it yields `12`.
- GREEN: the service drops a lease when its connection reaches EOF. There is no release
  message (decision 14).
- EXPECTED FAILURE: `AssertionError: 6 != 12`.

**Cycle 39: `test_a_stale_lease_is_not_counted`.**
- Hold a lease on `vm-1`, then `monkeypatch.setattr(leases, "STALE_AFTER_S", 0)` and take one
  on `vm-2`.
- Single assertion: it yields `12`.
- EXPECTED FAILURE: `AssertionError: 6 != 12`.

**Cycle 40: `test_guest_fleet_reports_the_hosts_lease_count`.**
- Hold a lease on `vm-2` from its own lease dir, then guest `vm-1` runs
  `run_cli(repo, "fleet", "--json")`.
- Single assertion: `result.suites.active == 1`.
- EXPECTED FAILURE: `AssertionError: 0 != 1` (the snapshot is local).

### Phase 6: one history per host

New file `tests/test_ledger_host_views.py`. Two guest runs are made by `run start` as `vm-1`,
then a rewrite of the guest config to `vm-2` and a second `run start` in the same repo.
Cycle 7 makes that legal.

**Cycle 41: `test_ledger_metrics_covers_every_source`.**
- `run_cli(repo, "ledger", "metrics")`.
- Single assertion: `sorted(r["source"] for r in result["repos"][slug]["runs"]) ==
  ["vm-1", "vm-2"]`.
- GREEN: the admin `metrics` method calls `render.metrics(<host view>, worktree=None)`, where
  `None` means every worktree, for every `<home>/*.sqlite3` (or `--repo`).
- EXPECTED FAILURE: `AssertionError` / `KeyError` on `repos`. Read with `.get` so it is an
  `AssertionError`.

**Cycle 42: `test_ledger_fleet_lists_active_runs_of_every_source`.**
- Single assertion: `sorted((r["source"], r["run_id"]) for r in result["runs"])` lists both
  runs.
- GREEN: fleet run entries carry `source`, plus the admin `fleet` method over every host
  file, with the daemon's lease snapshot.
- EXPECTED FAILURE: `AssertionError: [] != [...]`.

**Cycle 43: `test_ledger_log_renders_any_sources_run`.**
- `run_cli_text(repo, "ledger", "log", "--repo", slug, "--run", str(vm2_run_id))`.
- Single assertion: the text contains the plan path and `vm-2`'s run id header.
- Check the exact header with `render.friction_log` before writing the assertion. Name the
  string in the test.
- EXPECTED FAILURE: `AssertionError`; the text is the `not_implemented` envelope.

**Cycle 44: `test_ledger_import_retags_a_ledger_as_one_source`.**
- A single-mode ledger with one run, made by `run_cli` in a plain `repo` under
  `ledger_home`. Then `run_cli(repo, "ledger", "import", <that file>, "--source", "legacy")`.
- Single assertion: the host file's run sources are `["legacy"]`.
- EXPECTED FAILURE: `AssertionError` (the host file does not exist).

**Cycle 45: `test_ledger_import_refuses_an_existing_host_ledger`.**
- Import twice.
- Single assertion: the second gives `result.reason == "ledger_exists"`.
- EXPECTED FAILURE: `AssertionError`. Cycle 44's minimal GREEN overwrites. That is the
  increment this cycle adds, and nothing earlier.

### Phase 7: docs

**Cycle 46 (refactor): docs.**
- `docs/split-runner.md` gets a new section, "Across a VM boundary". It covers:
  - the service config;
  - `tdd ledger serve` under a dedicated account (with a systemd unit example);
  - `add-source` / `bind` / `remove-source` per guest;
  - forwarding the socket: ssh `-R` with `StreamLocalBindMask`/`StreamLocalBindUnlink`, a
    docker bind mount, and vsock as a pointer;
  - the guest's `ledger_socket`;
  - what is and is not protected (a guest writes its own source's open runs, and nothing
    else);
  - host views and `tdd ledger import`;
  - socket modes;
  - the fact that a guest's `[executor]` table is a claim.
- `README.md`'s split-mode bullets gain one bullet pointing at it.
- `CHANGELOG.md` `## [Unreleased]`: an `### Added` entry for the service, the host verbs and
  host-wide leases, and a `### Changed` entry for ledger schema v13 (per-source claims and
  cache).
- `tdd docs split` serves `docs/split-runner.md` already, so no new topic is needed.

## Execution

This plan is executed through `tdd-cli`. **You run every command below yourself** — do not ask the
user to start the run. `tdd run start` records which model is executing, resolved from your own
session; a run started by anyone else attributes this work to the wrong agent.

    git checkout -b issue-169-ledger-service    # first, before anything else
    tdd doctor                                  # must report healthy: true
    tdd run start --plan tasks/issue-169-ledger-service.md   # captures baselines, opens cycle 1

If the branch already exists, do not force-checkout and do not pick another name: check it out
only if it carries this plan's commit and no unrelated work, otherwise stop and ask.

**Referee.** Cycle 6 raises `src/tddcli/ledger.py`'s `SCHEMA_VERSION` to 13. Build the frozen
snapshot referee from the plan commit *before the first cycle edit* and never rebuild it
mid-run:

    uv venv /tmp/tdd-referee-169
    uv pip install --python /tmp/tdd-referee-169/bin/python .
    /tmp/tdd-referee-169/bin/tdd doctor

Use that binary as `tdd` for every command in this plan, including the three above.

Then repeat until done: read `next_action.verb`, do exactly what it says, run `tdd advance`.
Stop when `next_action.terminal` is `true`.

When `next_action.terminal` is `true`, finish the run: render the friction log, commit it, and
raise the PR — see Done-criteria below.

- `tdd advance` is the only command that changes phase. Do not `git add` or `git commit` — the
  tool stages and commits, deriving the file set from the phase.
- The baseline is captured at `run start` and subtracted from later verdicts. The suite is
  green at the plan commit (verified in a fresh worktree: `666 passed`). Expect
  `baselines: {tddcli: 0}` and no standing failures.
- Verbs this plan will hit:
  - `write_test`, `write_implementation`, `refactor_or_advance`.
  - `create_stub`: cycles 7, 10 and 29 declare stubs; any other request means an undeclared
    import.
  - `run_sensitivity_check` → `tdd sensitivity begin|check|end`: pins 13 and 14, and any
    cycle that pre-passes.
  - `resolve_blocker` → `tdd blocker --kind <plan_defect|environment|no_baseline_for_project>
    --detail '...'`.
  - `confirm_cycle_applicable` on a non-existent cycle → `tdd cycle skip --reason`.
  - This plan declares no annotation keys, so `annotate_cycle` should not appear.
- Cycle 3 changes when a state is written, not what is written. If the end state differs, raise
  `plan_defect`; never commit a semantic change under a refactor phase.

**Minimal GREEN, per cycle — add this and nothing earlier:**

- cycle 12 dispatches any `Ledger` method by name and sets `RemoteLedger.path` to the socket path
  alone: no ownership check, no allow-list, no closed-run rule, no stamping.
- cycle 15 maps connection failures to `ledger_unreachable`, and nothing about refusals.
- cycle 16 checks `run_id` parameters only, and adds the `LedgerRefused` round trip.
- cycle 17 adds `cycle_id` and `contract_id`.
- cycle 18 adds the `GUEST_READS | GUEST_WRITES` allow-list.
- cycle 19 adds repo-path validation.
- cycle 20 refuses guest writes to `complete`/`abandoned` runs, with no exemption.
- cycle 21 exempts `add_note`, and nothing else.
- cycle 22 stamps a bound executor on `start_run` only.
- cycle 23 downgrades an unbound `operator` claim on `start_run`.
- cycle 24 extends both rules to `abandon_run`.
- cycle 29 makes every `ledger` verb load the service config; the verbs stay `not_implemented`.
- cycles 30–33 implement one admin verb each (`add-source`, `sources`, `bind`,
  `remove-source`); cycle 34 adds persistence; cycle 36 adds `serve`.
- cycle 37 counts lease connections and never forgets one.
- cycle 38 forgets a lease on EOF.
- cycle 39 adds the stale limit.
- cycle 40 moves the snapshot.
- cycle 44 imports and retags, overwriting freely; cycle 45 adds the `ledger_exists` refusal.

## Done-criteria

**Before finishing:** run `tdd log render --out tasks/friction-logs/issue-169-ledger-service-friction.md` and `tdd metrics`. Report the plan-fidelity section — declared vs delivered vs skipped — and every integrity event. Do not narrate what the ledger already records.

Then commit the friction log and raise the PR:

    git add tasks/friction-logs/issue-169-ledger-service-friction.md
    git commit -m "docs: friction log for issue-169-ledger-service"

Then invoke the **`raise-pr` skill** (`/raise-pr`), which runs the quality gates, pushes the
branch and opens the PR against `main`. Do not push or call the GitHub API by hand. If a gate
fails, fix it and re-run the skill — a failed gate is work, not a reason to hand back.

The PR body says `Closes #169`.

Docs are deliverables, not hopes. Cycle 46 owns them:

- `git diff --stat origin/main -- docs/split-runner.md` must be non-empty, or the PR body says why.
- `git diff --stat origin/main -- README.md` must be non-empty, or the PR body says why.
- `git diff --stat origin/main -- CHANGELOG.md` must be non-empty, or the PR body says why.

Nothing a user *sees* changes outside JSON envelopes and new operator verbs, so no demo
recording is required. Quote one `tdd ledger metrics` envelope covering two sources in the PR
body instead. The real socket forwarding (ssh `-R` into a VM) cannot run in CI. The PR body
says so and names the scope cut.
