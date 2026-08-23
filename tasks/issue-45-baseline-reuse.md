---
closes: 45
cycles:
  - n: 1
    project: tddcli
    title: "upstream_producer_roots returns a project's own root plus its upstream artifact producers' roots"
    test: "tests/test_config_and_staging.py::test_upstream_producer_roots_includes_self_and_upstream_producers"
    files: ["src/tddcli/config.py"]
    commit_red: "test: upstream_producer_roots resolves self plus upstream producer roots"
    commit_green: "feat: Config.upstream_producer_roots for baseline cache keys"

  - n: 2
    project: tddcli
    title: "baseline_cache persists and looks up a probe result keyed by (project, tree_hash, config_sha)"
    test: "tests/test_snapshot_and_identity.py::test_baseline_cache_round_trips_by_content_key"
    files: ["src/tddcli/ledger.py"]
    commit_red: "test: baseline_cache round-trips a probe by content key"
    commit_green: "feat: baseline_cache table with cache_baseline/cached_baseline (schema v4)"

  - n: 3
    project: tddcli
    title: "--reuse-baselines populates the cache on probe; default writes nothing"
    test: "tests/test_baseline_integrity.py::test_reuse_baselines_populates_cache_and_default_does_not"
    files: ["src/tddcli/cli.py", "tests/conftest.py"]
    commit_red: "test: --reuse-baselines writes cache rows, default leaves cache empty"
    commit_green: "feat: --reuse-baselines flag populates baseline_cache after each probe"

  - n: 4
    project: tddcli
    title: "a second --reuse-baselines run reuses the cached probe and skips the suite"
    test: "tests/test_baseline_integrity.py::test_second_reuse_run_reuses_cached_baseline"
    files: ["src/tddcli/cli.py"]
    commit_red: "test: identical reuse run emits baseline_reused, not baseline_captured"
    commit_green: "feat: reuse cached failing set + collection snapshot, skipping the probe"

  - n: 5
    project: tddcli
    title: "a reused baseline row records its provenance and a baseline_reused event"
    test: "tests/test_baseline_integrity.py::test_reused_baseline_records_provenance_and_event"
    files: ["src/tddcli/cli.py", "src/tddcli/ledger.py"]
    commit_red: "test: reused baseline row is marked reused and logs a baseline_reused event"
    commit_green: "feat: baseline.source provenance column and baseline_reused event (schema v5)"

  - n: 6
    project: tddcli
    title: "a cache entry older than --reuse-max-age is ignored and re-probed"
    test: "tests/test_snapshot_and_identity.py::test_cached_baseline_respects_max_age"
    files: ["src/tddcli/ledger.py", "src/tddcli/cli.py"]
    commit_red: "test: cached_baseline filters entries past a max age"
    commit_green: "feat: --reuse-max-age TTL on cached_baseline lookup"

  - n: 7
    project: tddcli
    pin_cycle: true
    title: "a stale reused baseline still recovers via resume --unblock --accept-failures"
    test: "tests/test_baseline_integrity.py::test_stale_reused_baseline_recovers_via_accept_failures"
    files: ["tests/test_baseline_integrity.py"]
    commit_pin: "test: pin that accept-failures folds a drifted failure into a reused baseline"
---

# Issue #45 — reuse baselines across runs keyed by tree hash (opt-in)

https://github.com/geuben/tdd-cli/issues/45
Task file: `tasks/issue-45-baseline-reuse.md`

## Context

`run start` probes every plan-reachable project to capture its baseline — it runs the
full suite (`adapter.run(None)`) and collects it (`adapter.collect()`) in
`_probe_projects` (R9.5a). Issue #44 (merged, R9.5c) already scopes *which* projects are
probed to the plan-reachable set; this issue decides, for each of those, whether the
probe can be **skipped** because the project's inputs are byte-for-byte identical to a
previous run's. On a repo with frequent runs and mostly-quiescent projects, re-running an
unchanged suite recomputes an answer that cannot have changed.

The baseline is a content function of the project's own source and of anything upstream
that can regenerate into it: the failing set and collection snapshot depend on the
project root **and** the roots of every artifact producer it consumes (a producer edit
regenerates an artifact the project reads, R9.2). So the cache key is
`(project, tree_hash(project root ∪ upstream producer roots), config_sha)` →
`(failing set, collection snapshot)`. `tree_hash` already hashes tracked + untracked
content under a set of roots (it backs `no_change_since_last_run`, §6); `config_sha`
already pins `tdd.toml` per run. Reuse threads both through a new content-addressed
cache table.

The residual hazard is real: a test outcome can drift for reasons the key cannot see —
a dependency upgrade outside the repo, a toolchain or OS change. A quietly smaller or
wrong baseline is worse than a slow one, because R9.6 subtracts it from every later
failure set for the life of the run. Three guards keep reuse honest: it is **opt-in**
(`--reuse-baselines`, default OFF — no lookup, no writes, byte-identical current
behavior); it is **loud** (a `baseline_reused` heartbeat on stderr and a
`baseline_reused` integrity event + `source` provenance on the baseline row, never a
silent skip); and it is **recoverable** — a reused baseline row is an ordinary baseline
row, so the existing R9.5b path (`resume --unblock --accept-failures`) folds a drifted
failure back in. An optional TTL (`--reuse-max-age`) bounds how stale an entry may be.

Ordering: cycle 1 builds the pure key-root resolution in `config.py`; cycle 2 the
content-addressed cache in `ledger.py`; cycles 3–5 wire opt-in population, the reuse
path, and its auditability into `cmd_run_start`; cycle 6 adds the TTL; cycle 7 proves
recovery composes.

## Verified repo facts

*Every fact below was read from the codebase or confirmed by grep during hardening —
none are asserted from memory. Locators are function/symbol names; grep for them at
execution time.*

- **`gitutil.tree_hash(worktree: Path, roots: list[str]) -> str`** (`gitutil.py`)
  hashes, per root, the `git ls-files -s` tree entries, the working-tree diff, and every
  untracked file's bytes. It takes a **list of root path strings** and sorts them
  internally — so the cache key must feed it a set of *roots*, not project names.
  `Engine.tree_hash(project_names)` (`machine.py`) is the name→root wrapper
  (`gitutil.tree_hash(self.worktree, self.roots(project_names))`); the probe path in
  `cli.py` has no Engine yet (the run row does not exist), so it must call
  `gitutil.tree_hash` directly with roots from cycle 1's helper.
- **`config_mod.config_sha(worktree) -> str`** (`config.py`) is `sha256` of
  `tdd.toml`'s bytes (empty string if absent). In `cmd_run_start` it is currently computed
  inline **at the `run`-row insert, which happens *after* `_probe_projects`** — so the
  cache key (needed *during* probing, before the run row exists) must call
  `config_mod.config_sha(worktree)` itself rather than read `run.config_sha`. It is the
  same pure function, so the key and the stored `run.config_sha` agree; a `tdd.toml` edit
  invalidates every cached entry.
- **`Config.reachable_projects` / `Config._root_project`** (`config.py`)
  already exist from #44. `_root_project(produced_by)` resolves a project name or an
  `artifact.<name>` chain (via each artifact's `upstream_artifact`, `config.py`) to a
  root project. `reachable_projects` walks *downstream* (producer → `consumed_by`);
  cycle 1's `upstream_producer_roots` walks the **reverse** — a consumer up to the roots
  of the artifacts it consumes — reusing `_root_project` for the chain resolution.
- **Confirmed absent (grep, whole tree):** `upstream_producer_roots`, `baseline_cache`,
  `cache_baseline`/`cached_baseline`, `reuse_baselines`/`--reuse-baselines`, and
  `baseline_reused` do not exist anywhere in `src/`. The `baseline` table
  (`ledger.py`) has columns `id, run_id, project, failing, captured_at` only — **no
  provenance column** (the one `source` hit in `ledger.py` is `run.executor_source`).
- **`_probe_projects(projects, worktree, ledger, on_progress)`** (`cli.py`) iterates
  `projects.items()`, builds an adapter, runs `adapter.run(None)` then `adapter.collect()`,
  stores `probes[name] = (verdict, collection)`, emits a `baseline_captured` heartbeat,
  and calls `on_progress(done, name)`. **Its only caller is `cmd_run_start`**
  (`cli.py`) — grep confirms no test calls it directly — so its signature may widen
  (add `cfg`, `config_sha`, reuse options) without touching any test.
- **Probe result shapes** (`adapters/base.py`): `Verdict` is a dataclass
  requiring `project` and `adapter` positional args, with `passed: list[str]` and
  `failed: list[str]` defaulting empty; `Collection` has `tests: set[str]` and
  `failed_files: dict[str, str]`. A reuse hit reconstructs real instances from the cache
  row — `Verdict(project=name, adapter=adapter.name, failed=cached_failing)` and
  `Collection(tests=set(cached_tests), failed_files=cached_failed_files)` — so the
  downstream row-insert code (`cli.py`) is unchanged.
- **The R9.5a guards must be skipped for reused entries.** After probing, `cmd_run_start`
  loops over `probes` and refuses on two conditions (`cli.py`): "no test could be
  collected" (`not collection.tests and collection.failed_files`) and "collected but ran
  nothing" (`collection.tests and not verdict.passed and not verdict.failed`). The cache
  never stores `passed`, so a reused all-passing suite (`tests` non-empty, `passed` and
  `failed` both empty) would trip the second guard. A cached entry only got written
  because it passed these guards when first probed, so the guard loop must skip reused
  names. Track them (return a `reused` set/dict from `_probe_projects`) and `continue`
  past both guards for those names.
- **`cmd_run_start` insertion order** (`cli.py`): the `run` row is inserted first
  (carrying `config_sha`), then `plan_blob_changed` / `baseline_scoped` events, then one
  `baseline` + one `collection_snapshot` row per `probes` entry. Cycle 5's provenance and
  `baseline_reused` event slot in beside `baseline_scoped` (event) and into the
  `baseline` insert (`source` column). Do **not** run the suite twice — the row inserts
  read from the `probes` mapping the probe already produced.
- **Ledger schema/migration mechanism** (`ledger.py`): `SCHEMA_VERSION`
  is `3`. `SCHEMA` is idempotent `CREATE TABLE IF NOT EXISTS`, run first on every open;
  `MIGRATIONS[from_version]` runs only for an *existing* older ledger and need only carry
  statements `SCHEMA` cannot express (e.g. `ALTER TABLE`). A fresh DB (`_stored_version()`
  is `None`) skips the migration loop entirely. So: a **new table** needs only a `SCHEMA`
  addition + a `MIGRATIONS` entry of `""` (cycle 2, v3→v4); a **new column on an existing
  table** needs the column added to `SCHEMA`'s `CREATE` *and* an `ALTER TABLE ... ADD
  COLUMN` in `MIGRATIONS` for old ledgers (cycle 5, v4→v5). SQLite permits `ADD COLUMN`
  with a constant `NOT NULL DEFAULT`.
- **`Ledger.insert(table, **cols)`** (`ledger.py`), **`Ledger.event(run_id, cycle_id,
  kind, detail)`** (`ledger.py`), **`Ledger.baselines(run_id)`** (`ledger.py`),
  and **`Ledger.all/one`** exist and are the vocabulary for cycle 2's cache methods and
  cycle 5's event. `now()` (`ledger.py`) is the ISO-8601 UTC timestamp used
  throughout; TTL (cycle 6) compares `created_at` against it.
- **`heartbeat(**fields)`** (`envelope.py`) prints one JSON line to **stderr** with
  `flush=True`. `baseline_captured` is emitted in `_probe_projects`; `baseline_reused`
  is its reuse-path twin (same channel, distinct `event` name — the pattern
  `project_completed` vs `baseline_captured` already establishes this). Heartbeat tests
  in `tests/test_heartbeat.py` capture stderr with `capsys` and parse lines via the local
  `_heartbeat_lines` helper (`test_heartbeat.py`).
- **The `repo_three` fixture** (`tests/conftest.py`) is exactly the multi-project /
  cross-artifact repo this plan needs: `backend` (declared) + `svc` + `other`, artifact
  `schema` `produced_by = "backend"`, `consumed_by = ["svc"]`, all committed. With
  `THREE_PROJECT_PLAN` (`test_baseline_integrity.py`, declares only `backend`) a
  scoped `run start` probes `{backend, svc}` and reports
  `baselines == {"backend": 0, "svc": 0}` (asserted today by
  `test_run_start_probes_only_reachable_projects`). Cycles 3–6 reuse this
  fixture; a reuse run's cache key for `svc` covers `svc` **and** `backend` (its upstream
  producer), so a `backend` edit correctly invalidates `svc`'s cached baseline.
- **The `cfg` fixture** (`tests/test_config_and_staging.py`) declares `backend`
  (root `backend`), `frontend` (root `frontend`), `e2e` (root `frontend`,
  `in_close_sweep = false`), artifact `openapi` (`produced_by = "backend"`,
  `consumed_by = ["frontend"]`) and `api_client` (`produced_by = "artifact.openapi"`,
  `consumed_by = ["frontend"]`). So cycle 1 can assert
  `upstream_producer_roots("frontend") == ["backend", "frontend"]` (self + backend via
  both artifacts, deduped and sorted) and `upstream_producer_roots("backend") ==
  ["backend"]`. It sits beside the existing `close_sweep_projects` tests — write the new
  test in that style.
- **Recovery path already exists** (`cli.py`, `_accept_failures_into_baseline`, and
  `test_baseline_integrity.py`): `resume --unblock --accept-failures` reads
  the last CLOSE_SWEEP invocation per project and folds `other_failures` into the
  baseline row (`baseline_amended` event), inserting a fresh row when none exists. A
  reused baseline row is an ordinary row, so cycle 7 is a **characterization** test that
  the reuse path composes with this — no production change is expected beyond what
  cycles 3–5 add; if RED does not appear, see cycle 7's note.

## Cycle detail

*Expected failure per cycle, grounded in the code read above; minimum GREEN; resist
future cycles' behavior.*

### Cycle 1 — cache-key roots (pure)

**Expected RED:** `AttributeError: 'Config' object has no attribute
'upstream_producer_roots'`.

Test (in `test_config_and_staging.py`, using the shared `cfg` fixture):
`cfg.upstream_producer_roots("frontend") == ["backend", "frontend"]` and
`cfg.upstream_producer_roots("backend") == ["backend"]`. GREEN: fixpoint over
`self.artifacts` — seed a project-name set with `{project}`; for any artifact whose
consumer list intersects the set, add `self._root_project(art.produced_by)` (skip
`None`); repeat until stable; return `sorted({self.project(n).root for n in sources})`.
Deduping by root matters (`frontend` and `e2e` share root `frontend`). Reuse
`_root_project` — do not re-implement chain resolution.

### Cycle 2 — content-addressed cache (ledger)

**Expected RED:** `sqlite3.OperationalError: no such table: baseline_cache` (or
`AttributeError` on `ledger.cache_baseline`, depending on which line runs first).

Test (in `test_snapshot_and_identity.py`, ledger-only — construct a `Ledger` against a
`tmp_path` ledger home like the existing ledger tests): `cache_baseline("svc", "treeA",
"cfgA", failing=["svc::t::a"], tests=["svc::t::a", "svc::t::b"], failed_files={})` then
`cached_baseline("svc", "treeA", "cfgA")` returns a row whose `failing`, `tests`,
`failed_files` round-trip; `cached_baseline("svc", "treeB", "cfgA")` and
`cached_baseline("svc", "treeA", "cfgB")` return `None` (a changed tree or config misses).

GREEN: bump `SCHEMA_VERSION` to `4`; add to `SCHEMA` a `baseline_cache` table —
`id, project, tree_hash, config_sha, failing (json), tests (json), failed_files (json),
created_at`, with `UNIQUE(project, tree_hash, config_sha)`; add `MIGRATIONS[3] = ""`
(the `CREATE TABLE IF NOT EXISTS` covers old ledgers). Add `cache_baseline(...)` as an
upsert (`INSERT ... ON CONFLICT(project, tree_hash, config_sha) DO UPDATE` refreshing the
payload and `created_at`) and `cached_baseline(project, tree_hash, config_sha) ->
sqlite3.Row | None`. Store lists/dicts as `json.dumps`; the caller deserializes.

### Cycle 3 — opt-in population (default OFF)

**Expected RED:** argparse rejects the flag — `unrecognized arguments: --reuse-baselines`
surfaces as `run_cli` raising `SystemExit`. Write the RED around the *default* behavior
inverted: assert that after a plain `run start` (no flag) `baseline_cache` is empty, and
that `run start --reuse-baselines` writes one row per probed project — the second call
dies on argparse before the assertion.

Test (in `test_baseline_integrity.py`, `repo_three` + `THREE_PROJECT_PLAN`): a plain
`run start` leaves `SELECT COUNT(*) FROM baseline_cache` at `0`; a fresh
`run start --reuse-baselines` (new worktree/ledger, or after the first run ends) writes
a `baseline_cache` row for exactly `{backend, svc}` (the reachable set), each keyed by
`gitutil.tree_hash(worktree, cfg.upstream_producer_roots(name))` and the run's
`config_sha`.

GREEN: add `--reuse-baselines` (`store_true`) to the `run start` subparser (beside
`--baseline-all`, `cli.py`). Thread `args.reuse_baselines`, `cfg`, and the
`config_sha` into `_probe_projects`. When the flag is set, **after** a fresh probe of a
project, call `ledger.cache_baseline(name, tree_hash, config_sha, failing=verdict.failed,
tests=sorted(collection.tests), failed_files=collection.failed_files)`. When the flag is
off, do nothing new — no lookup, no write. The whole feature is flag-gated so the default
path is byte-identical to today.

### Cycle 4 — reuse path skips the probe

**Expected RED:** the second run re-probes — its stderr carries a `baseline_captured`
line for `svc` and no `baseline_reused` line — so the assertion for a `baseline_reused`
line (and no `baseline_captured`) for `svc` fails.

Test (in `test_baseline_integrity.py`, `repo_three`, `capsys`): run
`run start --reuse-baselines` once (populates), end it (or use a second worktree sharing
the ledger — the cache is repo-scoped, not worktree-scoped), discard stderr, then a
second identical `run start --reuse-baselines` on an unchanged tree. Assert the second
run's `baselines` still equals `{"backend": 0, "svc": 0}`, its stderr has a
`baseline_reused` line for each reused project and **no** `baseline_captured` line for
them, and the new run's `baseline`/`collection_snapshot` rows carry the cached failing
set and tests. (On a quiescent identical tree a fresh probe would produce the same data,
so the *heartbeat* is the load-bearing proof that the suite was skipped.)

GREEN: in `_probe_projects`, when the flag is set, compute the key and
`ledger.cached_baseline(...)` **before** building/running the adapter. On a hit,
reconstruct `Verdict(project=name, adapter=adapter.name, failed=json.loads(row["failing"]))`
and `Collection(tests=set(json.loads(row["tests"])),
failed_files=json.loads(row["failed_files"]))`, emit a `baseline_reused` heartbeat
(fields: `event`, `project`, `test_count`, short `tree_hash`) instead of
`baseline_captured`, record the name in the returned `reused` set, and skip
`adapter.run`/`adapter.collect`. On a miss, probe and populate as in cycle 3. In
`cmd_run_start`, skip the two R9.5a guards for names in `reused` (a cached entry already
passed them).

### Cycle 5 — provenance and event

**Expected RED:** `sqlite3.OperationalError: no such column: source` on the `baseline`
insert (the column does not exist), or an assertion that no `baseline_reused` event was
recorded.

Test (in `test_baseline_integrity.py`): after the reuse run of cycle 4, the reused
project's `baseline` row has `source == "reused"` while a freshly probed project's row
has `source == "probed"`, and a `baseline_reused` integrity event exists on the run whose
detail JSON lists the reused projects (sorted).

GREEN: bump `SCHEMA_VERSION` to `5`; add `source TEXT NOT NULL DEFAULT 'probed'` to the
`baseline` `CREATE TABLE` in `SCHEMA` and `MIGRATIONS[4] = "ALTER TABLE baseline ADD
COLUMN source TEXT NOT NULL DEFAULT 'probed';"`. In `cmd_run_start`'s `baseline` insert,
pass `source="reused" if name in reused else "probed"`. Beside the `baseline_scoped`
emission (`cli.py`), when `reused` is non-empty emit
`ledger.event(run_id, None, "baseline_reused", json.dumps(sorted(reused)))`. Reuse must
be loud: this is the ledger-visible twin of the stderr heartbeat.

### Cycle 6 — TTL (opt-in bound on staleness)

**Expected RED:** `TypeError: cached_baseline() got an unexpected keyword argument
'max_age_s'` — the parameter does not exist until this cycle's GREEN adds it, so the test
that passes `max_age_s=60` errors at the call. (Write the assertion for the intended
behaviour — the old entry is filtered out — around that call; the error is what the tool
records as RED. The test file collects fine, so this is a failing test, not a collection
error.)

Test (in `test_snapshot_and_identity.py`, ledger-only): insert a cache row, then
back-date its `created_at` (direct `UPDATE`, or `cache_baseline` then rewrite the
timestamp) to well in the past; `cached_baseline("svc", "treeA", "cfgA",
max_age_s=60)` returns `None`, while `max_age_s=None` (default) still returns it.

GREEN: give `cached_baseline` an optional `max_age_s: float | None = None`; when set,
add `AND created_at >= ?` with the cutoff (`now()` minus the age, compared as ISO-8601
strings — lexicographic order matches chronological order for UTC ISO timestamps). Add
`--reuse-max-age` (`type=float`, default `None`) to the `run start` subparser and thread
it to the lookup. Default (`None`) preserves cycle 4's behavior. No dedicated
`cmd_run_start` test — the ledger unit test pins the filter; the CLI wiring is a single
argument pass-through.

### Cycle 7 — recovery on a stale reused baseline (`pin_cycle`)

**This is a pin cycle — the test must PASS on arrival.** It characterises behaviour that
already ships: `_accept_failures_into_baseline` folds a close sweep's `other_failures`
into the *existing* baseline row via its `else`/amend branch, and a reused baseline row is
structurally an ordinary row (only its `source` column differs, which that function never
reads). Cycles 3–5 add the *creation* of a reused row; they do not touch the recovery
logic, so recovery composes for free. The pin exists so a future refactor of the cache
cannot silently break that compose.

The tool skips RED for a pin cycle and makes the **sensitivity check mandatory** — so
after the test passes on arrival you will be sent `run_sensitivity_check`: temporarily
break the amend path (`_accept_failures_into_baseline`'s `else` branch — e.g. make it a
no-op), confirm the test now fails, then `tdd sensitivity end` restores it byte-identical.
This is expected and correct here, not a discipline failure.

Test (in `test_baseline_integrity.py`, no production change): populate a cache entry for a
project via a first `--reuse-baselines` run; then, *without changing the project's tree*
(so the key still hits), arrange for its suite to fail on a later close sweep — the same
shape as `test_unblocking_can_accept_the_failures_into_the_baseline`: reach a close sweep
whose verdict includes a failure absent from the reused baseline, `blocker --kind
pre_existing_failure`, then `resume --unblock --accept-failures --note ...`. Assert the
failure is now in the baseline and the next `advance` reaches `complete`.

**If the test genuinely FAILS on arrival, do not force it green** — a pin that cannot pass
means the compose is actually broken (e.g. the reused row's `source` interferes with the
amend). Surface it via `tdd blocker --kind plan_defect`: the pin's premise (recovery
already composes) was wrong and needs a real fix in `_accept_failures_into_baseline`, which
this plan did not budget for. Do not silently downgrade it to a standard cycle.

*Note: this cycle could not be dynamically probed during hardening — it depends on cycles
3–5, which do not exist yet. The pin kind rests on the pinned behaviour already being
shipped and covered (`test_unblocking_can_accept_the_failures_into_the_baseline`), not on a
probe of this exact test.*

## Deliberate scope cuts (do not build)

- **Parallel probing (#46).** Orthogonal. Reuse composes with a bounded worker pool for
  free — a reused project simply does no work, so it costs one cache lookup and returns
  immediately — but this plan builds **no** pool, no concurrency, no worker leases.
  Assume #46 may land first; the reuse path is a per-project decision inside whatever
  iteration `_probe_projects` uses, serial or pooled.
- **Cache eviction / garbage collection.** The `baseline_cache` table grows unbounded
  across runs. A stale entry is harmless (it is either re-validated by an identical key
  or missed by a changed one), and the TTL bounds *use*, not *size*. A `tdd cache prune`
  command is a separate issue; do not add one.
- **Caching without the flag.** Default `run start` neither reads nor writes the cache.
  Populating unconditionally would make reuse "available immediately" but writes
  behavior-affecting state for users who never opted in; opt-in on both read and write
  keeps the default byte-identical and the feature auditable. First `--reuse-baselines`
  run is cold by design.
- **Reusing across a `config_sha` change or a producer edit.** Both are in the key
  precisely so they miss. Do not add heuristics to reuse "close enough" trees — the whole
  safety argument rests on the key being exact and the flag being opt-in.
- **A `--no-reuse` inverse or per-project reuse control.** One flag, whole-run, default
  OFF. Finer control is unmotivated here.
- **PRD/README documentation** of `--reuse-baselines`, the cache, and the
  `baseline_reused` event: same PR, after the run completes, not a cycle (see
  Done-criteria).

## Execution

This plan is executed through `tdd-cli`. **You run every command below yourself** — do
not ask the user to start the run. `tdd run start` records which model is executing,
resolved from your own session; a run started by anyone else attributes this work to the
wrong agent.

**Referee rule:** run the *released* `tdd` **0.7.0**, never this working tree's editable
install. Do not work in a shell with this repo's `.venv` activated. Verify before
starting: `tdd --version` → **0.7.0**.

> **Environment blocker found at hardening (2026-08-23):** `~/.local/bin/tdd` is stale at
> **0.6.0**, which understands ledger schema only up to v2 and *cannot open this repo's
> v3 ledger* — `tdd doctor` fails with "written by a newer tdd-cli". Meanwhile `which tdd`
> may resolve to a `.venv` on `PATH`. Before starting you MUST have 0.7.0 as the `tdd` you
> invoke: `uv tool upgrade tdd-cli` (or reinstall) so `~/.local/bin/tdd --version` → 0.7.0,
> and confirm `which tdd` points at a 0.7.0 binary that is **not** `/Volumes/SSD/repos/tdd-cli/.venv`
> (this working tree's own editable install). A separate 0.7.0 clone is fine.

The suites under test are still this working tree's code; only the controller is pinned.
(This matters more than usual here: cycles 2 and 5 change the ledger schema. The released
`tdd` opens its own ledger for *this* repo's run at its own schema version; your edits to
`SCHEMA_VERSION` live only in the suites the run executes. If the released controller and
the edited code ever disagree on a ledger, stop.)

The branch `feat/45-baseline-reuse` already exists — it was created at hardening and
carries this plan's commit. Check it out; if it has grown unrelated work, stop and ask.

    git checkout feat/45-baseline-reuse           # exists: created at hardening, carries this plan
    tdd doctor                                    # must report healthy: true
    tdd run start --plan tasks/issue-45-baseline-reuse.md

The plan file is already committed on this branch — registration reads the committed blob,
not the working tree. `tdd doctor` must be green first: if it reports "worktree clean"
failing on *other* uncommitted `tasks/issue-*.md` files (sibling plans not part of this
work), commit, stash, or gitignore them before `run start` — they are unrelated to this
plan.

Then repeat until done: read `next_action.verb`, do exactly what it says, run
`tdd advance`. Stop when `next_action.terminal` is `true`.

When `next_action.terminal` is `true`, finish the run: render the friction log, commit
it, and raise the PR — see Done-criteria below.

- `tdd advance` is the only command that changes phase. Do not `git add` or `git commit`
  cycle work — the tool stages and commits, deriving the file set from the phase.
- The baseline is captured at `run start` and subtracted from later verdicts. Expected
  baseline for this repo: `{"tddcli": 0}` — anything else means a moved branch; stop.
- Verbs this plan can hit: `run_sensitivity_check` → `tdd sensitivity begin|check|end`
  (**expected on cycle 7**, the pin cycle — the tool makes it mandatory there; not
  expected on cycles 1–6, which are standard and should produce a real RED);
  `resolve_blocker` → `tdd blocker --kind --detail` (kinds: `plan_defect`, `tooling`,
  `regression`, `pre_existing_failure`); `confirm_cycle_applicable` on a cycle the
  codebase has outgrown → `tdd cycle skip --reason`. This plan declares no
  `annotation_keys`.
- Cycle 7 is a **pin cycle**: its test must pass on arrival, then the tool sends
  `run_sensitivity_check` — follow it (break the amend branch, confirm failure, restore).
  If instead the test fails on arrival, that is a real broken compose → `tdd blocker
  --kind plan_defect` (see cycle 7's detail), not a standard-cycle RED to force.

## Done-criteria

**Before finishing:** run
`tdd log render --out tasks/friction-logs/issue-45-baseline-reuse-friction.md` and
`tdd metrics`. Report the plan-fidelity section — declared vs delivered vs skipped — and
every integrity event. Do not narrate what the ledger already records. Note explicitly
whether cycle 7 required a code change or landed GREEN.

Then the documentation follow-up, committed as ordinary commits on the branch after the
run is terminal: PRD R9.5 family (add an R9.5e for opt-in cross-run baseline reuse — the
`(project, tree_hash, config_sha)` key over the project root ∪ upstream producer roots,
the `--reuse-baselines` / `--reuse-max-age` flags, the `baseline_reused` heartbeat +
event + `source` provenance, and the loud-not-silent invariant) and the README's
`run start` section.

Then commit the friction log and raise the PR:

    git add tasks/friction-logs/issue-45-baseline-reuse-friction.md
    git commit -m "docs: friction log for issue-45-baseline-reuse"

Then invoke the **`raise-pr` skill** (`/raise-pr`), which runs the quality gates, pushes
the branch and opens the PR against `main`. Do not push or call the GitHub API by hand.
If a gate fails, fix it and re-run the skill — a failed gate is work, not a reason to
hand back.
