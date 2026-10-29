---
closes: 190
cycles:
  - n: 1
    project: tddcli
    pin_cycle: true
    title: "a runner that keeps its own ledger ignores core_budget"
    test: "tests/test_remote_leases.py::test_core_budget_does_not_cap_a_runner_that_keeps_its_own_ledger"
    files: ["src/tddcli/leases.py"]
    commit_red: "test: pin the local lease split against runner.toml's core_budget"
    commit_refactor: "refactor: tidy the local lease path"
  - n: 2
    project: tddcli
    title: "a guest caps its lease at the CPUs it may run on"
    test: "tests/test_remote_leases.py::test_a_guest_caps_its_lease_at_the_cpus_it_may_use"
    files: ["src/tddcli/leases.py"]
    commit_red: "test: a guest caps its lease at the CPUs it may use"
    commit_green: "fix: a guest runner caps the service's lease at its own CPU affinity"
    commit_refactor: "refactor: tidy the guest lease cap"
  - n: 3
    project: tddcli
    title: "runner.toml's core_budget is the guest's budget, in place of its affinity"
    test: "tests/test_remote_leases.py::test_core_budget_is_the_guests_own_budget"
    files: ["src/tddcli/runner.py", "src/tddcli/leases.py"]
    commit_red: "test: core_budget is the guest's own budget"
    commit_green: "feat: a guest runner caps its lease at runner.toml's core_budget"
    commit_refactor: "refactor: tidy the guest budget"
  - n: 4
    project: tddcli
    title: "a guest without sched_getaffinity falls back to os.cpu_count()"
    test: "tests/test_remote_leases.py::test_a_guest_without_sched_getaffinity_falls_back_to_cpu_count"
    files: ["src/tddcli/leases.py"]
    commit_red: "test: a guest without sched_getaffinity falls back to cpu_count"
    commit_green: "fix: a guest without sched_getaffinity budgets os.cpu_count()"
    commit_refactor: "refactor: tidy the guest CPU fallback"
  - n: 5
    project: tddcli
    title: "a core_budget that is not a positive integer is refused"
    test: "tests/test_split_config.py::test_a_core_budget_that_is_not_a_positive_integer_is_refused"
    files: ["src/tddcli/runner.py"]
    commit_red: "test: a core_budget that is not a positive integer is refused"
    commit_green: "feat: runner.toml refuses a core_budget that is not a positive integer"
    commit_refactor: "refactor: tidy core_budget validation"
  - n: 6
    project: tddcli
    refactor_cycle: true
    title: "document the guest's own core budget"
    files: ["docs/split-runner.md", "README.md", "CHANGELOG.md"]
    commit_refactor: "docs: a guest caps its worker lease at its own budget"
---

# Issue 190: a guest runner caps its worker lease at its own budget

## Context

[Issue #190](https://github.com/geuben/tdd-cli/issues/190). A runner in a guest has
`ledger_socket` set in `/etc/tdd-cli/runner.toml`, and it takes each suite's worker lease from
the host's ledger service (`leases.worker_lease` → `remote.worker_lease` → `Service.take_lease`).
The service sizes the lease as `leases._total_cores() // (live + 1)`, using the **host's**
`TDD_CORE_BUDGET` or `os.cpu_count()`. The guest's own limits never come into it. On
geuben/machine the host has 10 cores, and a Linux slot VM has 6 cores, 3.9 GB of memory and no
swap. One backend suite there ran `pytest -n 10`, the OOM killer took its xdist workers, and the
baseline was refused (geuben/coparenting#1218). The same base passes with `-n 4`.

The guest cannot cap the lease itself. sudo's `env_reset` drops a `TDD_CORE_BUDGET` the agent
sets, and the socket path never reads a local budget anyway.

What the issue asks for: in a guest, the runner yields
`workers = min(service_share, local_budget)`, where `local_budget` is, in order:

1. `core_budget` in `[runner]` of runner.toml (root's file, so the operator sets it and the
   agent cannot);
2. otherwise `len(os.sched_getaffinity(0))` where that exists, or else `os.cpu_count()`.

`snapshot()` and `tdd fleet` keep showing the host's split. Only the yielded count changes.

After this ships, geuben/machine's image sets `core_budget = 4` in each Linux slot's runner.toml.
That work is outside this repo.

## Design decisions (locked)

1. **The cap is applied in the guest, in `leases.worker_lease`'s socket branch, and nowhere
   else.** The service, the wire protocol, `Service.take_lease`, `Service.lease_snapshot`,
   `leases._total_cores` and `leases.snapshot` do not change. The lease still counts as one
   live suite on the host, whatever count the guest used. *Decided by the issue* ("Only the
   yielded count changes"; "`snapshot()` / `tdd fleet` may keep showing the host's split"). It
   also has to be the guest: the service cannot see the guest's affinity.
   Do not touch `_total_cores`. The in-process service in the tests reads it, and it must stay
   the host's budget.
2. **`local_budget` = `core_budget`, else `len(os.sched_getaffinity(0))`, else
   `os.cpu_count() or 1`.** `core_budget` *replaces* the affinity. It is not combined with it:
   an operator who sets `core_budget = 10` on a 3-CPU guest gets 10, capped only by the
   service's share. A guest never reads `TDD_CORE_BUDGET`. *Decided by the issue*, which gives
   that exact order. `or 1` follows `_total_cores`'s existing `os.cpu_count() or 1`
   (*convention*).
3. **`workers = min(service_share, local_budget)`.** `core_budget` only ever lowers the share;
   it never raises it. *Decided by the issue.*
4. **`core_budget` is a new optional key in `[runner]`, parsed by `runner.load` into
   `RunnerConfig.core_budget: int | None = None`.** *Decided by the issue* (name and table).
   The field sits beside `ledger_socket` (*convention*: every `[runner]` key is a
   `RunnerConfig` field).
5. **A `core_budget` that is not a positive TOML integer is refused**, with `RunnerConfigError`
   naming the key: `0`, a negative integer, a string (`"4"`), a float (`4.5`) and a boolean
   (`true`) are all refused. An absent key is `None`. *Convention*: `runner.load` already
   refuses a malformed runner.toml (bad TOML, a missing `user`/`command`, an unknown user, both
   `ledger_socket` and `ledger_home`), and `docs/split-runner.md` says "Anything else is
   refused". A refusal surfaces as `failure(str(exc))`, which `cli.main` already does for
   `RunnerConfigError`.
   **Mechanism trap:** TOML `true` loads as Python `True`, and `isinstance(True, int)` is
   `True`. The check must exclude `bool` explicitly
   (`isinstance(v, bool) or not isinstance(v, int) or v < 1`). A refusal is raised whatever
   the runner's mode, so a bad value never sits unnoticed on a runner that ignores it.
6. **`core_budget` has no effect on a runner that keeps its own ledger (no `ledger_socket`).**
   That runner's lease path is unchanged: it splits `_total_cores()` across its lease
   directory. *Decided by the issue's scope* ("In a guest, the runner caps the lease…"). The
   bug is a guest taking a host-sized share, and a host runner's `os.cpu_count()` already is
   its own machine. Cycle 1 pins this, and the docs say it. Applying `core_budget` there too
   would be a new behaviour that the issue does not ask for.
7. **`leases.worker_lease` reads the guest's config once per lease.** It replaces
   `_ledger_socket()` with a helper that returns the guest's `RunnerConfig` (or `None`), which
   both `worker_lease` and `snapshot` use. `snapshot` still reads only `ledger_socket` from it.
   Nothing in `tests/` patches it (`grep -rn "leases\._ledger_socket\|\"_ledger_socket\"" tests/` is empty), so
   the rename breaks no test. *Convention*: `runner.load()` is already called per lease today.
8. **Existing remote-lease tests get a fixed, large guest affinity.** `tests/test_remote_leases.py`
   runs the service in-process with `TDD_CORE_BUDGET=12`, so its guest's affinity is the test
   machine's. A simulated cap on main, in a scratch worktree on a 6-core host, failed
   `test_a_lease_ends_when_its_connection_closes` and `test_a_stale_lease_is_not_counted`
   (`assert 6 == 12`). `test_the_service_counts_leases_across_sources` (`== 6`) fails on any
   host with fewer than 6 CPUs. Cycle 2's RED therefore extends that file's autouse fixture
   `_twelve_cores` with
   `monkeypatch.setattr(os, "sched_getaffinity", lambda _pid: set(range(64)), raising=False)`.
   The tests that need another value override it in their own body. No test body changes and
   no assertion count changes, so `modifies_tests` stays empty. *Decided by evidence* (the
   scratch-worktree run). `raising=False` is what lets the patch work on macOS, where
   `os.sched_getaffinity` does not exist.

## Deliberate scope cuts (do not build)

- **A memory-aware bound (MemAvailable / a per-worker estimate).** Premise: *named non-goal*.
  The issue calls it "nice to have… optional: `core_budget` covers it". It would also need a
  per-worker memory estimate that is project-specific, and nothing in the issue supplies one.
- **geuben/machine setting `core_budget = 4`, and the host service dropping its stopgap
  `TDD_CORE_BUDGET=4`.** Premise: *unreachable*. Both are in another repository (the issue's
  "Then" section).

## Fake and real divergence

| Seam | Fake behaviour | Real behaviour | Path left untested | Ruling |
|---|---|---|---|---|
| `os.sched_getaffinity` (monkeypatched) | returns a fixed set | the CPUs the kernel lets this process run on (cpuset, taskset) | the kernel call itself | acceptable: a stdlib call; `len()` of its result is the whole contract |
| `os.cpu_count` (monkeypatched, cycle 4) | returns 2 or `None` | the machine's logical CPUs, or `None` | none | acceptable |
| in-process ledger service (`ledger_service`, `split_guest`) | a thread in the test process, over a real unix socket | `tdd ledger serve` on the host, socket forwarded into the VM | the forwarding (ssh `-R`, vsock) | acceptable: unchanged by this plan, the same seam #169 uses |

## Cycles

All of cycles 1–4 live in `tests/test_remote_leases.py`, at file scope, like the file's
existing tests. They use its autouse `_twelve_cores` fixture (`TDD_CORE_BUDGET=12`, so the
in-process service's share for a lone lease is 12) and the `split_guest` / `split_runner`
fixtures from `tests/conftest.py`. Write a guest's `core_budget` with
`guest_config(split_guest.runner, split_guest.socket, "core_budget = N\n")`.
`runner.load()` re-reads the file on every call, so rewriting it between leases takes effect.

### Cycle 1 (pin): a runner that keeps its own ledger ignores `core_budget`

- **Behaviour:** a split runner with `ledger_home` (no `ledger_socket`) and `core_budget = 2`
  in its runner.toml still splits `_total_cores()`. A lone lease yields 12.
- **Test:** `test_core_budget_does_not_cap_a_runner_that_keeps_its_own_ledger(split_runner,
  monkeypatch, tmp_path)`. Set `TDD_LEASE_DIR` to `tmp_path / "leases"`, then append
  `core_budget = 2\n` to `split_runner.config`'s text. The single assertion: `with
  leases.worker_lease() as workers:` gives `workers == 12`.
- **Target:** `src/tddcli/leases.py::worker_lease` (the local branch, unchanged).
- **EXPECTED:** passes on arrival (probed on main: `12`). It stays green through every later
  cycle, which is the point. If it fails after cycle 3, the GREEN applied `core_budget`
  outside the socket branch, against decision 6.

### Cycle 2: a guest caps its lease at the CPUs it may run on

- **RED test-file edits:** add `import os`, and extend the autouse `_twelve_cores` fixture as
  decision 8 gives it (a 64-CPU affinity). This keeps
  `test_the_service_counts_leases_across_sources`, `test_a_lease_ends_when_its_connection_closes`,
  `test_a_stale_lease_is_not_counted` and `test_guest_fleet_reports_the_hosts_lease_count`
  green once the cap exists (probed: all four pass against the cycle-2 state).
- **Test:** `test_a_guest_caps_its_lease_at_the_cpus_it_may_use(split_guest, monkeypatch)`.
  Patch `os.sched_getaffinity` to `lambda _pid: {0, 1, 2}` (`raising=False`). Single
  assertion: a lone lease (service share 12) yields `3`.
- **Target:** `src/tddcli/leases.py::worker_lease`, socket branch: yield
  `min(workers, len(os.sched_getaffinity(0)))`.
- **EXPECTED FAILURE:** `assert 12 == 3` (probed on main).

### Cycle 3: `core_budget` is the guest's budget, in place of its affinity

- **Test:** `test_core_budget_is_the_guests_own_budget(split_guest, monkeypatch)`. It is
  table-driven over `(core_budget, affinity CPUs)`, with one lone lease each (service share
  12). Before each lease, patch `os.sched_getaffinity` to `set(range(cpus))` and rewrite the
  guest config with `core_budget = <budget>`. Collect `{budget: workers}`. Single assertion:
  `got == {4: 4, 64: 12, 10: 10}`. The rows mean:
  - `(4, 64)` → 4: the budget caps below the share;
  - `(64, 64)` → 12: the budget never raises the share (`min`, not replace);
  - `(10, 3)` → 10: `core_budget` replaces the affinity rather than being combined with it.
- **Target:** `src/tddcli/runner.py`: a `RunnerConfig.core_budget: int | None = None` field,
  set by `load()` from `section.get("core_budget")`. `src/tddcli/leases.py`: the guest-config
  helper of decision 7, and the local budget `split.core_budget or <affinity>`.
- **EXPECTED FAILURE** (against cycle 2's GREEN): `assert {4: 12, 64: 12, 10: 3} == {4: 4,
  64: 12, 10: 10}`. Probed on main the left side is `{4: 12, 64: 12, 10: 12}`. Cycle 2's
  GREEN turns the `10` row into `3`, and the `4` and `10` rows still differ.

### Cycle 4: a guest without `sched_getaffinity` falls back to `os.cpu_count()`

- **Test:** `test_a_guest_without_sched_getaffinity_falls_back_to_cpu_count(split_guest,
  monkeypatch)`. Call `monkeypatch.delattr(os, "sched_getaffinity", raising=False)`. That
  undoes the autouse fixture's patch and is what macOS looks like. The guest has no
  `core_budget`. For `n` in `(2, None)`, patch `os.cpu_count` to return `n` and take a lone
  lease. Single assertion: `got == {2: 2, None: 1}`.
- **Target:** `src/tddcli/leases.py`: the affinity step uses `os.sched_getaffinity` only when
  `hasattr(os, "sched_getaffinity")`, else `os.cpu_count() or 1`.
- **EXPECTED FAILURE:** `AttributeError: module 'os' has no attribute 'sched_getaffinity'`,
  raised from `leases.worker_lease` inside the test body (probed against the cycle-2 state).
  It is a failure of the code under test, not of setup: today a macOS guest would crash
  exactly there.

### Cycle 5: a `core_budget` that is not a positive integer is refused

- **Test:** `tests/test_split_config.py::test_a_core_budget_that_is_not_a_positive_integer_is_refused(tmp_path,
  monkeypatch)`, at file scope like the file's other tests. Point `TDD_RUNNER_CONFIG` at
  `tmp_path / "runner.toml"`. For each raw TOML value in `("0", "-2", '"4"', "4.5", "true")`,
  write the file with `_write_config(cfg, _current_user())` and then append
  `core_budget = <raw>\n`. Call `runner.load()`, and record whether it raised
  `runner.RunnerConfigError` with `"core_budget"` in the message. Single assertion: the
  record equals `dict.fromkeys(values, True)`, in the same shape as
  `test_an_untrusted_runner_config_is_refused`.
- **Target:** `src/tddcli/runner.py::load`: validate the value as decision 5 gives it,
  excluding `bool`. The message names the key (the test checks for `"core_budget"`), for example
  `"<path>: [runner] core_budget must be a positive integer, not '4'"`.
- **EXPECTED FAILURE:** `assert {'0': False, '-2': False, '"4"': False, '4.5': False, 'true':
  False} == {... True ...}` (probed on main, and unchanged by cycle 3's plain read).

### Cycle 6 (refactor, docs): document the guest's own budget

Behaviour is unchanged, and the existing suite guards it.

- `docs/split-runner.md`, "The guest": add `# core_budget = 4` to the guest's `[runner]`
  snippet, with a comment saying it defaults to the CPUs the runner may use. Extend the
  "**Worker leases are the host's.**" paragraph: the guest uses
  `min(the service's share, its own budget)`. Its own budget is `core_budget`, otherwise
  `len(os.sched_getaffinity(0))`, or `os.cpu_count()` where that does not exist. A value
  that is not a positive integer is refused. `core_budget` is read only by a runner with
  `ledger_socket`. `tdd fleet` still shows the host's split.
- `README.md`, the split-mode bullet ending "one history and one worker budget for every
  guest": add that each guest caps its share at its own cores (`core_budget` in its
  runner.toml).
- `CHANGELOG.md`, under `## [Unreleased]`: add a `### Fixed` entry. A guest runner caps
  the worker lease from the ledger service at its own budget, `core_budget` in
  `[runner]` or else the CPUs it may run on, so a guest smaller than its host no longer
  runs a host-sized `-n` (#190).

## Execution

This plan is executed through `tdd-cli`. **You run every command below yourself** — do not ask the
user to start the run. `tdd run start` records which model is executing, resolved from your own
session; a run started by anyone else attributes this work to the wrong agent.

    git checkout -b issue-190-guest-core-budget # first, before anything else
    tdd doctor                                  # healthy, or failing only for projects this plan cannot reach
    tdd run start --plan tasks/issue-190-guest-core-budget.md   # captures baselines, opens cycle 1

`tdd doctor` checks every project; `tdd run start` probes only the ones the plan declares and
those downstream of them through an `[artifact]`. A failing check on a project outside that set
does not stop the run: note it and go on. Any other failing check stops it.

If the branch already exists, do not force-checkout and do not pick another name: check it out
only if it carries this plan's commit and no unrelated work, otherwise stop and ask.

**Referee.** Use the released `tdd` on `PATH`, never `uv run tdd` from this tree (the note at
the top of `tdd.toml`). This plan changes no ledger table, so `SCHEMA_VERSION` does not move
and no frozen referee is needed.

Then repeat until done: read `next_action.verb`, do exactly what it says, run `tdd advance`.
Stop when `next_action.terminal` is `true`.

When `next_action.terminal` is `true`, finish the run: render the friction log, commit it, and
raise the PR — see Done-criteria below.

- `tdd advance` is the only command that changes phase. Do not `git add` or `git commit` — the
  tool stages and commits, deriving the file set from the phase.
- The baseline is captured at `run start` and subtracted from later verdicts. The suite is
  green at the plan's base (verified in a fresh worktree: `722 passed`). Expect
  `baselines: {tddcli: 0}` and no standing failures.
- Verbs this plan will hit:
  - `write_test`, `write_implementation`, `refactor_or_advance`.
  - `run_sensitivity_check` → `tdd sensitivity begin|check|end`: pin cycle 1, and any cycle
    that pre-passes.
  - `create_stub`: no cycle declares a stub (every RED imports only existing symbols), so any
    request means an undeclared import.
  - `resolve_blocker` → `tdd blocker --kind <plan_defect|environment> --detail '...'`.
  - `confirm_cycle_applicable` on a non-existent cycle → `tdd cycle skip --reason`.
  - This plan declares no annotation keys, so `annotate_cycle` should not appear.
- If cycle 1's pin fails after any later GREEN, that GREEN applied `core_budget` outside the
  socket branch. Fix the GREEN, never the pin.
- Cycle 6 is docs only. If it turns out to need a code change, raise `plan_defect`. Never
  commit a semantic change under a refactor phase.

**Minimal GREEN, per cycle: add this and nothing earlier.**

- cycle 2 yields `min(workers, len(os.sched_getaffinity(0)))` in the socket branch. It does not
  read `core_budget`, check `hasattr` or add `or 1`.
- cycle 3 adds `RunnerConfig.core_budget`, read verbatim with no validation. It also adds the
  guest-config helper (decision 7) and `core_budget` taking the affinity's place. It adds no
  `hasattr` fallback.
- cycle 4 adds the `hasattr(os, "sched_getaffinity")` fallback to `os.cpu_count() or 1`.
- cycle 5 adds the validation in `runner.load`, and nothing in `leases.py`.

## Done-criteria

**Before finishing:** run `tdd log render --out tasks/friction-logs/issue-190-guest-core-budget-friction.md` and `tdd metrics`. Report the plan-fidelity section — declared vs delivered vs skipped — and every integrity event. Do not narrate what the ledger already records.

Then commit the friction log and raise the PR:

    git add tasks/friction-logs/issue-190-guest-core-budget-friction.md
    git commit -m "docs: friction log for issue-190-guest-core-budget"

Then invoke the **`raise-pr` skill** (`/raise-pr`), which runs the quality gates, pushes the
branch and opens the PR against `main`. Do not push or call the GitHub API by hand. If a gate
fails, fix it and re-run the skill — a failed gate is work, not a reason to hand back.

The PR body says `Closes #190`.

Docs are deliverables, not hopes. Cycle 6 owns them:

- `git diff --stat origin/main -- docs/split-runner.md` must be non-empty, or the PR body says why.
- `git diff --stat origin/main -- README.md` must be non-empty, or the PR body says why.
- `git diff --stat origin/main -- CHANGELOG.md` must be non-empty, or the PR body says why.

Nothing a user *sees* changes outside the worker count a guest's suite receives, so no demo
recording is required. The real guest (a VM whose runner.toml sets `core_budget`, behind a
forwarded socket) cannot run in CI. The PR body says so.
