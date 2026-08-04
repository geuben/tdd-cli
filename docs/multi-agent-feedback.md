# Multi-agent usage feedback

Observed during first real parallel-agent run (2026-08-04, coparenting repo, 5 simultaneous
`claude-sonnet-4-6` agents each executing an arch-review plan).

---

## 1. `tdd run start` is silent during baseline collection — agents assume it hung

**What happened:** The baseline collection phase iterates every test file with `--collect-only`
and takes 3–8 minutes on a ~1150-test suite. The command emits nothing to stdout during this
time. Agent Bash calls timed out after 2 minutes (the Claude Code default), the agent saw an
empty result, assumed the command had failed or been lost, and either re-ran it (creating
duplicate processes) or stalled waiting for guidance.

**Impact:** Several wasted runs, manual intervention via `SendMessage` to stop agents re-running
the command, and at one point two concurrent `tdd run start` processes competing on the same
worktree.

**Suggested fix:** Emit one line of JSON to stdout per project as each baseline completes, e.g.:

```json
{"event": "baseline_captured", "project": "backend", "test_count": 1147, "elapsed_s": 62}
{"event": "baseline_captured", "project": "frontend", "test_count": 84, "elapsed_s": 8}
{"event": "run_started", "run_id": "...", "plan": "tasks/arch-c3-complete-usecases.md"}
```

This gives the agent (or a human) a heartbeat to confirm progress without changing the final
JSON envelope contract.

---

## 2. `tdd progress` returns "no runs recorded" throughout baseline collection

**What happened:** `tdd progress` is the natural polling command for "is anything happening?"
but it returns `{"ok": false, "error": "no runs recorded for this worktree"}` throughout the
entire baseline phase — the same response as "nothing has been started at all". Agents cannot
distinguish "run in progress, collecting baseline" from "tdd run start was never called".

**Suggested fix:** Once `tdd run start` is invoked and the SQLite record is created, let
`tdd progress` reflect that, even before the baseline is fully captured:

```json
{
  "ok": false,
  "status": "collecting_baseline",
  "projects_done": 1,
  "projects_total": 3,
  "current_project": "frontend",
  "elapsed_s": 45
}
```

This lets agents poll safely and wait rather than retry.

---

## 3. `tdd doctor` doesn't report which project failed or why

**What happened:** `coparent-verify` had a missing `pyyaml` dependency that caused a collection
error. `tdd doctor` failed, but the error wasn't attributed to a specific project in the output.
All five concurrent agents hit this failure before one eventually diagnosed it by manually running
`pytest --collect-only` in the verify directory.

**Suggested fix:** Include a per-project result in the `tdd doctor` output:

```json
{
  "ok": false,
  "projects": {
    "backend":  {"ok": true},
    "frontend": {"ok": true},
    "verify":   {"ok": false, "error": "collection_failed", "detail": "ModuleNotFoundError: No module named 'yaml'"}
  }
}
```

R10.2 already requires adapters to report `not_collected` distinctly from `not_found` — the
same signal should be surfaced through `tdd doctor`.

---

## 4. No guard against concurrent `tdd run start` on the same worktree

**What happened:** An agent ran `tdd run start`, its Bash call timed out (see #1), the agent
assumed failure and ran it again. Two `tdd run start` processes competed on the same worktree's
SQLite ledger simultaneously.

**Suggested fix:** On startup, `tdd run start` should check whether a run is already active for
the current worktree and fail fast with a clear error:

```json
{"ok": false, "error": "run_already_active", "run_id": "...", "started_at": "..."}
```

R13.4 says concurrent runs in *separate* worktrees are supported — the converse (concurrent
runs in the *same* worktree) should be explicitly rejected.

---

## 5. `frontend/node_modules` required by `tdd doctor` even for backend-only plans

**What happened:** `tdd doctor` runs the adapter health check for all projects in `tdd.toml`,
including frontend vitest. Git worktrees don't inherit `node_modules` from the primary tree, so
any agent — even one executing a pure backend plan — fails `tdd doctor` with a vitest import
error unless the symlink is pre-created.

This is arguably correct behaviour (doctor should verify all adapters), but it was a surprise
and caused unnecessary friction across all five agents.

**Suggested fix / documentation:** Either add a note to `tdd doctor` output pointing at the
missing `node_modules` specifically, or add a check to the doctor that detects a missing
`node_modules` directory when a `vitest` adapter is configured and surfaces it as a named
actionable error rather than a raw vitest stack trace.

---

## Summary table

| # | Command | Symptom | Suggested change |
|---|---------|---------|-----------------|
| 1 | `tdd run start` | Silent for 3–8 min; agents assume hung | Per-project heartbeat lines during collection |
| 2 | `tdd progress` | `no runs recorded` during baseline | Return `collecting_baseline` status once run record exists |
| 3 | `tdd doctor` | No per-project attribution on failure | Structured per-project result with error detail |
| 4 | `tdd run start` | Concurrent invocations on same worktree | Detect and reject with `run_already_active` error |
| 5 | `tdd doctor` | Raw vitest error for missing node_modules | Named actionable error for missing adapter dependencies |
