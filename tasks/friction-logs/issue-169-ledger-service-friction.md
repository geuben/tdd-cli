# Implementation Friction Log: tasks/issue-169-ledger-service.md

- Run: 1
- Executor: claude-opus-5-5 (source: transcript)
- Plan blob: `6e02083cbc917277e9009daaf8a499dcb10a78e3` (declared)
- Started: 2026-10-03T00:25:37.656330+00:00  Ended: 2026-10-03T03:31:49.860055+00:00  Outcome: complete
- Baseline failures at start: tddcli=0

## Plan fidelity

- Declared cycles: 46
- Delivered: 46   Skipped: 0
- Never reached: none
- Human interventions: 0

### Cycle 46: document split mode across a VM boundary  _(refactor)_
- **Target:** none
- **Projects:** `tddcli`
- **Suite runs by phase:** {'CLOSE_SWEEP': 1}
- **Commits:**
  - `dd6a61155` [refactor] docs: split mode across a VM boundary (3 files)

### Cycle 45: ledger import refuses a ledger the host already holds  _(standard)_
- **Target:** `tddcli::tests/test_ledger_host_views.py::test_ledger_import_refuses_an_existing_host_ledger`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `83dd475fc` [red] test: ledger import never overwrites (1 files)
  - `9d2036c90` [green] feat: ledger import refuses an existing host ledger (2 files)
> **note** _(during AWAITING_REFACTOR)_: cycle 45 also touched cli.py (declared: service.py only): a service refusal reaches the CLI as reason=ledger_refused, so 'reason == ledger_exists' needed the ledger verb wrapper to report an admin refusal's own code as its reason. Done generally in _ledger_verb, so every operator verb reports its service's refusal codes (unknown_source, unknown_repo, ledger_exists) directly.

### Cycle 44: ledger import brings an existing ledger in as one named source  _(standard)_
- **Target:** `tddcli::tests/test_ledger_host_views.py::test_ledger_import_retags_a_ledger_as_one_source`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `18a99e9d3` [red] test: ledger import retags an existing ledger (1 files)
  - `5f0386a31` [green] feat: tdd ledger import (3 files)

### Cycle 43: ledger log renders any source's run on the host  _(standard)_
- **Target:** `tddcli::tests/test_ledger_host_views.py::test_ledger_log_renders_any_sources_run`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `8936fe7e5` [red] test: host log renders any source's run (1 files)
  - `24ee03b22` [green] feat: tdd ledger log (2 files)

### Cycle 42: ledger fleet on the host lists active runs of every source  _(standard)_
- **Target:** `tddcli::tests/test_ledger_host_views.py::test_ledger_fleet_lists_active_runs_of_every_source`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `392dea256` [red] test: host fleet covers every source (1 files)
  - `859f111be` [green] feat: tdd ledger fleet (3 files)

### Cycle 41: ledger metrics on the host covers every source  _(standard)_
- **Target:** `tddcli::tests/test_ledger_host_views.py::test_ledger_metrics_covers_every_source`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `c7cf65c90` [red] test: host metrics cover every source (1 files)
  - `0ebcb9a74` [green] feat: tdd ledger metrics (4 files)

### Cycle 40: a guest's fleet view reports the host's live lease count  _(standard)_
- **Target:** `tddcli::tests/test_remote_leases.py::test_guest_fleet_reports_the_hosts_lease_count`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `a85a76a06` [red] test: guest fleet shows host-wide suites (1 files)
  - `47f6dcd2d` [green] feat: a socket-mode lease snapshot comes from the service (3 files)

### Cycle 39: a lease older than the stale limit is not counted  _(standard)_
- **Target:** `tddcli::tests/test_remote_leases.py::test_a_stale_lease_is_not_counted`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `023c90b93` [red] test: stale leases do not throttle the host (1 files)
  - `104976269` [green] feat: the service ignores leases past the stale limit (1 files)

### Cycle 38: a lease ends when its connection closes  _(standard)_
- **Target:** `tddcli::tests/test_remote_leases.py::test_a_lease_ends_when_its_connection_closes`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `51e91ae95` [red] test: a closed lease connection frees its share (1 files)
  - `4d9cbdc71` [green] feat: the service forgets a lease when its connection closes (1 files)

### Cycle 37: the service counts worker leases across sources  _(standard)_
- **Target:** `tddcli::tests/test_remote_leases.py::test_the_service_counts_leases_across_sources`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `f52f6743a` [red] test: worker leases are counted across guests (1 files)
  - `aa5737883` [green] feat: a socket-mode runner takes its worker lease from the service (3 files)

### Cycle 36: ledger serve runs the service until SIGTERM and exits 0  _(standard)_
- **Target:** `tddcli::tests/test_ledger_admin.py::test_ledger_serve_runs_until_terminated`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `1485bf0fa` [red] test: ledger serve runs until SIGTERM (1 files)
  - `345a13f71` [green] feat: tdd ledger serve (2 files)
  - `b0e86aa8e` [refactor] refactor: tidy serve (1 files)

### Cycle 35: the admin socket is mode 600 and guest sockets are mode 660  _(standard)_
- **Target:** `tddcli::tests/test_ledger_admin.py::test_socket_modes`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `356c568fc` [red] test: admin and guest socket modes (1 files)
  - `38838b2f4` [green] feat: the service sets its sockets' modes (1 files)

### Cycle 34: sources and bindings survive a service restart  _(standard)_
- **Target:** `tddcli::tests/test_ledger_admin.py::test_sources_survive_a_service_restart`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `314cb3d9d` [red] test: sources survive a service restart (1 files)
  - `24b050ec2` [green] feat: the service persists its sources (1 files)

### Cycle 33: ledger remove-source closes and removes its socket  _(standard)_
- **Target:** `tddcli::tests/test_ledger_admin.py::test_remove_source_closes_its_socket`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `5ffde934b` [red] test: remove-source closes the guest socket (1 files)
  - `07e2920e0` [green] feat: tdd ledger remove-source (2 files)

### Cycle 32: ledger bind changes a source's executor for its next run  _(standard)_
- **Target:** `tddcli::tests/test_ledger_admin.py::test_bind_changes_the_executor_for_the_next_run`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `3d628b7aa` [red] test: bind changes a source's executor (1 files)
  - `029473356` [green] feat: tdd ledger bind (2 files)

### Cycle 31: ledger sources lists each source with its socket and binding  _(standard)_
- **Target:** `tddcli::tests/test_ledger_admin.py::test_sources_lists_each_source_and_its_binding`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `49d0bfb72` [red] test: ledger sources lists sources (1 files)
  - `f8ad925d5` [green] feat: tdd ledger sources (2 files)

### Cycle 30: ledger add-source opens a guest socket through the admin socket  _(standard)_
- **Target:** `tddcli::tests/test_ledger_admin.py::test_add_source_opens_a_guest_socket`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `77743fd52` [red] test: add-source opens a guest socket (1 files)
  - `f9f818cb2` [green] feat: tdd ledger add-source (2 files)

### Cycle 29: ledger verbs run locally and refuse without a service config  _(standard)_
- **Target:** `tddcli::tests/test_ledger_admin.py::test_ledger_verbs_are_never_forwarded_to_a_runner`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `023b5776d` [red] test: ledger verbs stay local and need a service config (1 files)
  - `e27e18916` [green] feat: tdd ledger verb group, answered locally (2 files)
> **note** _(during AWAITING_REFACTOR)_: cycle 29 also changed tests/test_split_client.py (not in modifies_tests): test_only_docs_and_init_stay_local pinned the local verb set to {docs, init}, and decision 16 adds ledger by design. Renamed it test_only_docs_init_and_ledger_stay_local, widened the set, and gave ledger an ARGV entry so the verb actually parses rather than staying local by failing to.

### Cycle 28: doctor on a socket-mode runner names the source it reaches  _(standard)_
- **Target:** `tddcli::tests/test_split_doctor.py::test_socket_mode_doctor_names_the_source_it_reaches`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'SENSITIVITY': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** passed (**passed**)
- **Sensitivity check:** verified, restore byte-identical
  - observed: `assert (True, False) == (True, True)`
- **Commits:**
  - `41adac5ef` [refactor] refactor: tidy socket-mode doctor (3 files)
- **Event — red_first_violation:** ["tddcli::tests/test_split_doctor.py::test_socket_mode_doctor_names_the_source_it_reaches"]
> **note** _(during AWAITING_REFACTOR)_: cycle 28 pre-passed: the plan's assertion ('vm-1' in the ledger-reachable detail) was already true because the guest socket's file name is vm-1.sock. Ran the sensitivity check against the test as written (it bites), then in the refactor phase tightened it to 'source vm-1' (fails on the old detail, which was the socket path alone) and implemented the planned GREEN: doctor pings the service and renders 'socket <path> (source <name>)', skipping the local ledger-readability probe in socket mode.

### Cycle 27: a runner config naming both ledger_socket and ledger_home is refused  _(standard)_
- **Target:** `tddcli::tests/test_split_config.py::test_ledger_socket_and_ledger_home_together_are_refused`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `a1567f3b4` [red] test: ledger_socket and ledger_home are exclusive (1 files)
  - `14f26f8c1` [green] feat: refuse a runner config naming both ledger locations (1 files)

### Cycle 26: runner import is refused on a socket-mode runner  _(standard)_
- **Target:** `tddcli::tests/test_runner_import.py::test_import_is_refused_when_the_ledger_is_on_the_host`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `82c3ecc9f` [red] test: runner import is refused when the ledger is remote (1 files)
  - `e1ecf8733` [green] feat: runner import refuses a socket-mode runner (1 files)

### Cycle 25: claim staleness is judged in the guest, not on the host  _(standard)_
- **Target:** `tddcli::tests/test_ledger_service.py::test_claim_staleness_is_judged_in_the_guest`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `f8b298245` [red] test: claim staleness is judged where the pid lives (1 files)
  - `52f1874f3` [green] feat: the remote ledger judges claim liveness locally (2 files)

### Cycle 24: a bound source stamps the abandoning executor too  _(standard)_
- **Target:** `tddcli::tests/test_ledger_service.py::test_a_bound_source_stamps_the_abandoning_executor`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2, 'CLOSE_SWEEP': 1}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `e3410288e` [red] test: abandonment records the bound executor (1 files)
  - `574cd5e33` [green] feat: the service stamps the executor on abandonment (1 files)
  - `9aa53c0f9` [refactor] refactor: tidy abandonment stamping (1 files)

### Cycle 23: an unbound source records a guest-claimed operator executor as claimed  _(standard)_
- **Target:** `tddcli::tests/test_ledger_service.py::test_an_unbound_source_downgrades_a_guest_operator_claim`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `826d5b102` [red] test: a guest cannot claim operator identity (1 files)
  - `8ec2def10` [green] feat: an unbound source records guest identity as claimed (1 files)

### Cycle 22: a bound source records the operator-assigned executor  _(standard)_
- **Target:** `tddcli::tests/test_ledger_service.py::test_a_bound_source_records_the_operator_assigned_executor`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `a62d3c1f5` [red] test: a bound source records the operator's executor (1 files)
  - `0e851b688` [green] feat: the service stamps a bound source's executor on run start (1 files)

### Cycle 21: a guest may still note a completed run  _(standard)_
- **Target:** `tddcli::tests/test_ledger_service.py::test_a_guest_may_still_note_a_completed_run`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `55fc021a4` [red] test: notes on a completed run are still accepted (1 files)
  - `058d55b94` [green] feat: appending a note is exempt from the closed-run rule (1 files)

### Cycle 20: a guest cannot write to its own completed run  _(standard)_
- **Target:** `tddcli::tests/test_ledger_service.py::test_a_guest_cannot_write_to_a_completed_run`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `1ca514029` [red] test: a completed run is closed to guest writes (1 files)
  - `ff8368bbe` [green] feat: the service refuses writes to complete or abandoned runs (1 files)

### Cycle 19: a guest repo path that is not absolute is refused  _(standard)_
- **Target:** `tddcli::tests/test_ledger_service.py::test_a_malformed_repo_path_is_refused`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `d1ba5a035` [red] test: malformed repo paths are refused (1 files)
  - `db58c5139` [green] feat: the service validates the guest's repo path (1 files)

### Cycle 18: a guest cannot call a host-only method  _(standard)_
- **Target:** `tddcli::tests/test_ledger_service.py::test_a_guest_cannot_call_a_host_only_method`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `a04d449c6` [red] test: guests cannot call host-only ledger methods (1 files)
  - `54f77258f` [green] feat: the service dispatches only guest-classified methods (2 files)
> **note** _(during AWAITING_REFACTOR)_: cycle 18 also touched ledger.py (not declared): cycle 11 had classified active_claim/active_advance_claim as HOST_ONLY, but guest commands still call them through the socket until cycle 25 composes them locally; the allow-list would have broken every guest run start. Reclassified them as SOURCE_ROOTED guest reads here; cycle 25 moves them to HOST_ONLY, which is what its expected failure assumes.

### Cycle 17: a guest naming another source's cycle or contract is refused  _(standard)_
- **Target:** `tddcli::tests/test_ledger_service.py::test_a_guest_naming_another_sources_cycle_is_refused`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `dcbd8d72c` [red] test: a guest cannot reach another source's cycle (1 files)
  - `1309371bb` [green] feat: ownership checks cover cycle and contract ids (1 files)

### Cycle 16: a guest naming another source's run is refused  _(standard)_
- **Target:** `tddcli::tests/test_ledger_service.py::test_a_guest_naming_another_sources_run_is_refused`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `98a7eb9ef` [red] test: a guest cannot reach another source's run (1 files)
  - `5796174c2` [green] feat: the service refuses run ids of other sources (4 files)

### Cycle 15: an unreachable ledger socket refuses the verb  _(standard)_
- **Target:** `tddcli::tests/test_ledger_service.py::test_an_unreachable_socket_refuses_the_verb`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `78c276d0e` [red] test: an unreachable ledger socket refuses the verb (1 files)
  - `99ea8d598` [green] feat: fail closed when the ledger service is unreachable (2 files)

### Cycle 14: a blocked guest run can still be unblocked  _(pin)_
- **Target:** `tddcli::tests/test_ledger_service.py::test_a_blocked_guest_run_can_be_unblocked`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_PIN': 1, 'SENSITIVITY': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** passed (as expected)
- **Sensitivity check:** verified, restore byte-identical
  - observed: `RuntimeError: mutated`
- **Commits:**
  - `871ed1497` [pin] test: pin a blocked guest run can still be unblocked (1 files)
> **note** _(during SENSITIVITY_REQUIRED)_: cycle 14: the plan's pin uses `tdd blocker --kind environment`, which is not in BLOCKER_KINDS; the pin uses plan_defect instead. Same path: blocker then resume --unblock.

### Cycle 13: a guest renders its own friction log through the socket  _(pin)_
- **Target:** `tddcli::tests/test_ledger_service.py::test_a_guest_renders_its_own_friction_log`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_PIN': 1, 'SENSITIVITY': 1, 'CLOSE_SWEEP': 1}
- **First run outcome:** passed (as expected)
- **Sensitivity check:** verified, restore byte-identical
  - observed: `TypeError: 'NoneType' object is not subscriptable`
- **Commits:**
  - `1a13225e3` [pin] test: pin a guest renders its own friction log through the socket (1 files)

### Cycle 12: a guest runner's run lands in the host ledger under its source  _(standard)_
- **Target:** `tddcli::tests/test_ledger_service.py::test_a_guest_run_lands_in_the_host_ledger_under_its_source`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `fd9465f41` [red] test: a guest run lands in the host ledger (2 files)
  - `baf996a46` [green] feat: a runner with ledger_socket keeps its ledger on the host (6 files)

### Cycle 11: every Ledger method is classified for guests and scoped  _(standard)_
- **Target:** `tddcli::tests/test_ledger_surface.py::test_every_ledger_method_is_classified_and_scoped`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `cfd2f5b3d` [red] test: every ledger method is classified for guests (1 files)
  - `3e94cae95` [green] feat: classify the ledger's methods for guests (1 files)

### Cycle 10: a source socket answers ping with the source's name and binding  _(standard)_
- **Target:** `tddcli::tests/test_ledger_service.py::test_a_source_socket_answers_ping_with_its_name`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 2, 'AWAITING_IMPL': 2}
- **First run outcome:** not_collected (**not_collected**)
- **Commits:**
  - `c2246568b` [red] test: a source socket answers ping (3 files)
  - `b9173ef0b` [green] feat: ledger service listens on a socket per source (3 files)
- **Event — stub_directive_issued:** ["tddcli::tests/test_ledger_service.py::test_a_source_socket_answers_ping_with_its_name"]

### Cycle 9: metrics names each run's source  _(standard)_
- **Target:** `tddcli::tests/test_ledger_sources.py::test_metrics_names_each_runs_source`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `fb5c15a4a` [red] test: metrics names each run's source (1 files)
  - `c1c4e1148` [green] feat: metrics names each run's source (1 files)

### Cycle 8: two sources claim and cache the same worktree independently  _(standard)_
- **Target:** `tddcli::tests/test_ledger_sources.py::test_two_sources_claim_and_cache_the_same_worktree_independently`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `ee6d5b5a9` [red] test: claims and baseline cache are per source (1 files)
  - `257f69f96` [green] feat: claims and the baseline cache are keyed by source (1 files)

### Cycle 7: a Ledger bound to one source never reads another source's runs or contracts  _(standard)_
- **Target:** `tddcli::tests/test_ledger_sources.py::test_a_source_reads_only_its_own_runs_and_contracts`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `6ace2773b` [red] test: a source reads only its own runs and contracts (1 files)
  - `d8accbd0b` [green] feat: source-rooted ledger reads filter by source (1 files)
> **note** _(during AWAITING_REFACTOR)_: cycle 7: the declared stub (source kwarg) was not needed as a separate step; the TypeError was accepted as RED directly. max_suite_duration_ms excludes other sources' runs with NOT IN rather than a JOIN, because tests/test_named_leases_and_timeout.py inserts invocations with no run row.

### Cycle 6: a v12 ledger migrates to v13 with every row tagged source 'local'  _(standard)_
- **Target:** `tddcli::tests/test_ledger_sources.py::test_a_v12_ledger_migrates_with_its_rows_tagged_local`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `7c191e282` [red] test: a v12 ledger migrates with its rows tagged local (1 files)
  - `656bfb87d` [green] feat: ledger schema v13 records each run's source (1 files)

### Cycle 5: no module but ledger.py speaks SQL or imports sqlite3  _(standard)_
- **Target:** `tddcli::tests/test_ledger_surface.py::test_no_module_but_the_ledger_speaks_sql`
- **Projects:** `tddcli`
- **Suite runs by phase:** {'AWAITING_TEST': 1, 'AWAITING_IMPL': 2}
- **First run outcome:** failed (as expected)
- **Commits:**
  - `3e5d56b1d` [red] test: only the ledger module speaks SQL (1 files)
  - `0c3817e26` [green] refactor: render reaches the ledger through named domain methods (2 files)

### Cycle 4: fleet reads through a read-only Ledger instead of its own sqlite connection  _(refactor)_
- **Target:** none
- **Projects:** `tddcli`
- **Suite runs by phase:** {'CLOSE_SWEEP': 1}
- **Commits:**
  - `9c55c1b43` [refactor] refactor: fleet reads through a read-only Ledger (4 files)

### Cycle 3: the final close decides the run's outcome before it ends the run  _(refactor)_
- **Target:** none
- **Projects:** `tddcli`
- **Suite runs by phase:** {'CLOSE_SWEEP': 1}
- **Commits:**
  - `ece0dce39` [refactor] refactor: the final close settles blocked-or-complete before ending the run (3 files)

### Cycle 2: machine.py and advance.py reach the ledger only through named Ledger methods  _(refactor)_
- **Target:** none
- **Projects:** `tddcli`
- **Suite runs by phase:** {'CLOSE_SWEEP': 1}
- **Commits:**
  - `c4f648b95` [refactor] refactor: the state machine reaches the ledger through named domain methods (3 files)

### Cycle 1: cli.py reaches the ledger only through named Ledger methods  _(refactor)_
- **Target:** none
- **Projects:** `tddcli`
- **Suite runs by phase:** {'CLOSE_SWEEP': 1}
- **Commits:**
  - `ec923a963` [refactor] refactor: cli reaches the ledger through named domain methods (2 files)

## Time

- Wall clock: 186.2 min. Suite: 79.8 min (43%).

| Phase | Suite runs | Suite (min) | Average (s) |
|---|---|---|---|
| AWAITING_TEST | 40 | 1.1 | 1.7 |
| AWAITING_PIN | 2 | 0.1 | 2.2 |
| SENSITIVITY | 3 | 0.1 | 2.0 |
| AWAITING_IMPL | 76 | 62.2 | 49.1 |
| CLOSE_SWEEP | 10 | 16.3 | 97.9 |

| Cycle | Wall (min) | Suite (min) | Suite runs |
|---|---|---|---|
| 1 | 5.2 | 2.0 | 1 |
| 2 | 4.7 | 1.6 | 1 |
| 3 | 2.1 | 1.5 | 1 |
| 4 | 2.3 | 1.5 | 1 |
| 5 | 4.2 | 1.5 | 3 |
| 6 | 4.2 | 1.5 | 3 |
| 7 | 4.5 | 1.5 | 3 |
| 8 | 3.8 | 1.6 | 3 |
| 9 | 3.7 | 1.6 | 3 |
| 10 | 4.3 | 1.5 | 4 |
| 11 | 3.9 | 1.6 | 3 |
| 12 | 5.4 | 1.6 | 3 |
| 13 | 2.1 | 1.6 | 3 |
| 14 | 2.0 | 1.6 | 3 |
| 15 | 3.8 | 1.6 | 3 |
| 16 | 3.8 | 1.6 | 3 |
| 17 | 5.5 | 1.7 | 3 |
| 18 | 3.9 | 1.6 | 3 |
| 19 | 3.6 | 1.6 | 3 |
| 20 | 3.7 | 1.6 | 3 |
| 21 | 3.6 | 1.7 | 3 |
| 22 | 3.7 | 1.7 | 3 |
| 23 | 5.4 | 1.6 | 3 |
| 24 | 5.3 | 3.3 | 4 |
| 25 | 4.0 | 1.6 | 3 |
| 26 | 3.7 | 1.7 | 3 |
| 27 | 3.7 | 1.7 | 3 |
| 28 | 4.5 | 1.7 | 3 |
| 29 | 6.1 | 1.7 | 3 |
| 30 | 3.9 | 1.7 | 3 |
| 31 | 3.8 | 1.7 | 3 |
| 32 | 3.6 | 1.7 | 3 |
| 33 | 3.6 | 1.7 | 3 |
| 34 | 3.9 | 1.7 | 3 |
| 35 | 3.7 | 1.7 | 3 |
| 36 | 5.7 | 3.3 | 4 |
| 37 | 4.0 | 1.7 | 3 |
| 38 | 4.7 | 1.7 | 3 |
| 39 | 3.6 | 1.7 | 3 |
| 40 | 3.9 | 1.8 | 3 |
| 41 | 4.1 | 1.8 | 3 |
| 42 | 4.1 | 1.8 | 3 |
| 43 | 4.1 | 1.8 | 3 |
| 44 | 4.2 | 1.8 | 3 |
| 45 | 3.9 | 1.8 | 3 |
| 46 | 4.3 | 1.7 | 1 |

## Executor narrative

_Claims from the executor, unverified by design._

> hardest cycle: 38, lease release on EOF: the handler thread sees EOF asynchronously, so the next guest's lease could still count a finished one; made deterministic by pruning hung-up connections with a non-blocking MSG_PEEK at take time. plan got wrong: cycle 28's assertion pre-passed (the socket file is named vm-1.sock); cycle 14 named a blocker kind (environment) that does not exist; cycles 18, 29 and 45 needed files the plan did not declare (ledger.py reclassification of active_claim until cycle 25; tests/test_split_client.py's local-verb guard; cli.py to surface ledger_exists as the reason). harness friction: the worktree guard rejects heredocs and chained git, so every multi-line edit went through a scripted exact-match replacement file; ruff format reformatted an already-committed test once and it had to be reverted to keep the cycle's file set clean.

