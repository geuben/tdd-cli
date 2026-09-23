"""Projections over the ledger: the friction log (§8.5) and metrics (§11.3).

The friction log is rendered, never composed by hand — every observable fact comes
from recorded events, and only judgement fields come from annotations.
"""

from __future__ import annotations

import json
from collections import defaultdict

from .ledger import PRE_SPLIT_IMPORT, Ledger


def _fmt_list(items) -> str:
    return ", ".join(f"`{i}`" for i in items) if items else "none"


def friction_log(ledger: Ledger, run) -> str:
    contract = ledger.one("SELECT * FROM plan_contract WHERE id = ?", (run["plan_contract_id"],))
    cycles = ledger.cycles(run["id"])
    lines: list[str] = []
    a = lines.append

    a(f"# Implementation Friction Log: {contract['plan_path']}")
    a("")
    a(f"- Run: {run['id']}")
    a(f"- Executor: {run['executor_model']} (source: {run['executor_source']})")
    a(f"- Plan blob: `{contract['git_blob_sha']}` ({contract['status']})")
    a(
        f"- Started: {run['started_at']}  Ended: {run['ended_at'] or '—'}"
        f"  Outcome: {run['outcome'] or 'live'}"
    )
    all_baseline_rows = ledger.all(
        "SELECT project, failing, source FROM baseline WHERE run_id = ?", (run["id"],)
    )
    run_start_baselines = {
        r["project"]: json.loads(r["failing"])
        for r in all_baseline_rows
        if r["source"] != "late_probe"
    }
    late_probe_rows = [r for r in all_baseline_rows if r["source"] == "late_probe"]
    a(
        "- Baseline failures at start: "
        + (", ".join(f"{k}={len(v)}" for k, v in run_start_baselines.items()) or "none")
    )
    if late_probe_rows:
        run_start_sha = run["start_sha"] or ""
        sha7 = run_start_sha[:7] if run_start_sha else "unknown"
        parts = ", ".join(
            f"{r['project']}={len(json.loads(r['failing']))}" for r in late_probe_rows
        )
        a(f"- Late baselines: {parts} (at {sha7})")
    regen_rows = ledger.all(
        "SELECT DISTINCT artifact FROM artifact_check WHERE run_id = ? AND regenerated = 1",
        (run["id"],),
    )
    if regen_rows:
        a("- Artifacts auto-regenerated: " + _fmt_list([r["artifact"] for r in regen_rows]))
    a("")

    declared = json.loads(contract["declared_cycles"])
    delivered = {c["ordinal"] for c in cycles if c["phase"] == "CLOSED"}
    skipped = {c["ordinal"] for c in cycles if c["phase"] == "SKIPPED"}
    a("## Plan fidelity")
    a("")
    a(f"- Declared cycles: {len(declared)}")
    a(f"- Delivered: {len(delivered)}   Skipped: {len(skipped)}")
    missing = sorted({d["n"] for d in declared} - delivered - skipped)
    a(f"- Never reached: {missing or 'none'}")
    interventions = ledger.all("SELECT * FROM human_intervention WHERE run_id = ?", (run["id"],))
    a(f"- Human interventions: {len(interventions)}")
    for i in interventions:
        a(f"  - {i['at']}: {i['note']}")
    amended_events = ledger.all(
        "SELECT detail FROM integrity_event WHERE run_id = ? AND kind = 'baseline_amended'",
        (run["id"],),
    )
    for ev in amended_events:
        detail = json.loads(ev["detail"])
        for project, entry in sorted(detail.items()):
            for test_id, verdict in sorted(entry.get("accepted", {}).items()):
                a(f"    - accepted: `{test_id}` ({verdict})")
            for test_id, verdict in sorted(entry.get("refused", {}).items()):
                a(f"    - refused: `{test_id}` ({verdict})")
    a("")

    events = defaultdict(list)
    for e in ledger.all("SELECT * FROM integrity_event WHERE run_id = ?", (run["id"],)):
        events[e["cycle_id"]].append(e)

    for cycle in reversed(cycles):
        a(
            f"### Cycle {cycle['ordinal']}"
            + (f": {cycle['title']}" if cycle["title"] else "")
            + f"  _({cycle['kind']})_"
        )
        if cycle["phase"] == "SKIPPED":
            a(f"- **Skipped:** {cycle['skip_reason']}")
            a("")
            continue

        targets = json.loads(cycle["target_tests"])
        a(f"- **Target:** {_fmt_list(targets)}")
        a(f"- **Projects:** {_fmt_list(json.loads(cycle['projects']))}")

        by_phase = defaultdict(list)
        for inv in ledger.invocations(cycle["id"]):
            by_phase[inv["phase_at"]].append(inv)
        attempts = {p: len(v) for p, v in by_phase.items()}
        a(f"- **Suite runs by phase:** {attempts or 'none'}")

        first_test_phase = by_phase.get("AWAITING_TEST") or by_phase.get("AWAITING_PIN")
        if first_test_phase:
            outcome = first_test_phase[0]["target_outcome"]
            expected = "passed" if cycle["kind"] == "pin" else "failed"
            verdict = "as expected" if outcome == expected else f"**{outcome}**"
            a(f"- **First run outcome:** {outcome} ({verdict})")

        sens = ledger.completed_sensitivity(cycle["id"])
        if sens:
            a("- **Sensitivity check:** verified, restore byte-identical")
            if sens["observed_failure"]:
                evidence = sens["evidence_line"]
                if evidence:
                    capped = ("…" + evidence[-160:]) if len(evidence) > 160 else evidence
                    a(f"  - observed: `{capped}`")
                elif evidence == "":
                    a("  - observed: <no assertion line captured>")
                else:
                    snippet = sens["observed_failure"].strip().splitlines()
                    a(f"  - observed: `{snippet[0][:160] if snippet else ''}`")

        commits = ledger.all(
            "SELECT * FROM commit_record WHERE cycle_id = ? ORDER BY id", (cycle["id"],)
        )
        if commits:
            a("- **Commits:**")
            for c in commits:
                files = json.loads(c["files"])
                a(f"  - `{c['sha'][:9]}` [{c['phase']}] {c['message']} ({len(files)} files)")
        else:
            a("- **Commits:** none")

        for e in events.get(cycle["id"], []):
            a(f"- **Event — {e['kind']}:** {e['detail'][:300]}")

        annotations = ledger.all(
            "SELECT * FROM annotation WHERE cycle_id = ? ORDER BY id", (cycle["id"],)
        )
        for ann in annotations:
            a(f"- **{ann['key']}:** {ann['value']}")
        notes = ledger.all("SELECT * FROM note WHERE cycle_id = ? ORDER BY id", (cycle["id"],))
        for n in notes:
            a(f"> **note** _(during {n['phase']})_: {n['text']}")
        a("")

    run_notes = ledger.all(
        "SELECT * FROM note WHERE run_id = ? AND cycle_id IS NULL ORDER BY id",
        (run["id"],),
    )
    if run_notes:
        a("## Executor narrative")
        a("")
        a("_Claims from the executor, unverified by design._")
        a("")
        for n in run_notes:
            a(f"> {n['text']}")
        a("")

    blockers = ledger.all("SELECT * FROM blocker WHERE run_id = ?", (run["id"],))
    if blockers:
        a("## Blockers")
        a("")
        for b in blockers:
            a(f"- **{b['kind']}** (cycle {b['cycle_id']}): {b['detail']}")
        a("")
    return "\n".join(lines) + "\n"


PHASE_SHORT = {
    "AWAITING_TEST": "writing test",
    "AWAITING_PIN": "writing pin",
    "AWAITING_IMPL": "implementing",
    "AWAITING_REFACTOR": "refactoring",
    "SENSITIVITY_REQUIRED": "sensitivity check",
}


def _seconds(start: str, end: str | None) -> float:
    """Seconds from `start` to `end`, or to now while `end` is unset (a live run)."""
    from datetime import datetime, timezone

    began = datetime.fromisoformat(start)
    finished = datetime.fromisoformat(end) if end else datetime.now(timezone.utc)
    return (finished - began).total_seconds()


def _elapsed(start: str, end: str | None) -> str:
    total = int(_seconds(start, end))
    hours, rem = divmod(total, 3600)
    mins, secs = divmod(rem, 60)
    return f"{hours}h{mins:02d}m" if hours else f"{mins}m{secs:02d}s"


def progress(ledger: Ledger, run) -> str:
    """A human's view of where the run is. Never consulted by an agent."""
    contract = ledger.one("SELECT * FROM plan_contract WHERE id = ?", (run["plan_contract_id"],))
    declared = json.loads(contract["declared_cycles"])
    rows = {c["ordinal"]: c for c in ledger.cycles(run["id"])}

    out: list[str] = []
    a = out.append
    name = contract["plan_path"].rsplit("/", 1)[-1].removesuffix(".md")
    state = run["outcome"] or "running"
    a(f"{name} · run {run['id']} · {run['executor_model']} ({run['executor_source']}) · {state}")
    a(f"{len(declared)} cycles · elapsed {_elapsed(run['started_at'], run['ended_at'])}")
    a("")

    closed = skipped = 0
    for decl in declared:
        ordinal = decl["n"]
        row = rows.get(ordinal)
        title = (decl.get("title") or "").strip()[:46]
        kind = decl["kind"]

        if row is None:
            a(f"    {ordinal:>2}  {kind:<8}  {title}")
            continue
        if row["phase"] == "SKIPPED":
            skipped += 1
            a(f"  ⊘ {ordinal:>2}  {kind:<8}  {title}")
            a(f"          skipped — {row['skip_reason']}")
            continue

        runs = len(ledger.invocations(row["id"]))
        commits = ledger.all(
            "SELECT phase, sha FROM commit_record WHERE cycle_id = ? ORDER BY id",
            (row["id"],),
        )
        events = ledger.all("SELECT kind FROM integrity_event WHERE cycle_id = ?", (row["id"],))
        detail = f"{runs} suite run{'' if runs == 1 else 's'}"
        if commits:
            detail += "  " + " ".join(f"{c['phase']}:{c['sha'][:7]}" for c in commits)

        if row["phase"] == "CLOSED":
            closed += 1
            a(f"  ✓ {ordinal:>2}  {kind:<8}  {title}")
        else:
            phase = PHASE_SHORT.get(row["phase"], row["phase"])
            a(f"  ▸ {ordinal:>2}  {kind:<8}  {title}")
            a(f"          NOW: {phase}")
        a(f"          {detail}")
        for e in events:
            a(f"          ! {e['kind']}")

    a("")
    total_events = ledger.all(
        "SELECT kind, COUNT(*) n FROM integrity_event WHERE run_id = ? GROUP BY kind",
        (run["id"],),
    )
    summary = f"{closed}/{len(declared)} closed"
    if skipped:
        summary += f" · {skipped} skipped"
    summary += (
        " · no integrity events"
        if not total_events
        else " · " + ", ".join(f"{e['kind']}×{e['n']}" for e in total_events)
    )
    blockers = ledger.all("SELECT kind, detail FROM blocker WHERE run_id = ?", (run["id"],))
    a(summary)
    for b in blockers:
        a(f"BLOCKED ({b['kind']}): {b['detail']}")
    return "\n".join(out) + "\n"


#: The order a cycle meets its suite runs in; any other `phase_at` sorts after these.
PHASE_ORDER = ("AWAITING_TEST", "AWAITING_PIN", "SENSITIVITY", "AWAITING_IMPL", "CLOSE_SWEEP")


def _time_summary(ledger: Ledger, run) -> dict:
    """Where a run's time went (#147): its wall clock, and the suite's share of it by
    phase. One source for `tdd metrics` and the friction log, so they cannot disagree.
    Every invocation of the run counts, so the phases sum to the suite total."""
    rows = ledger.all(
        "SELECT phase_at, COUNT(*) n, SUM(duration_ms) ms FROM invocation"
        " WHERE run_id = ? GROUP BY phase_at",
        (run["id"],),
    )
    by_phase = {r["phase_at"]: {"runs": r["n"], "suite_s": r["ms"] / 1000} for r in rows}

    def order(phase: str) -> tuple:
        return (PHASE_ORDER.index(phase), "") if phase in PHASE_ORDER else (len(PHASE_ORDER), phase)

    wall = _seconds(run["started_at"], run["ended_at"])
    suite = sum(p["suite_s"] for p in by_phase.values())
    return {
        "wall_clock_s": wall,
        "suite_s": suite,
        "suite_share": suite / wall if wall else None,
        "by_phase": {phase: by_phase[phase] for phase in sorted(by_phase, key=order)},
    }


def _time_json(summary: dict) -> dict:
    """`tdd metrics`' view: seconds to one decimal, the share to three."""
    share = summary["suite_share"]
    return {
        "wall_clock_s": round(summary["wall_clock_s"], 1),
        "suite_s": round(summary["suite_s"], 1),
        "suite_share": round(share, 3) if share is not None else None,
        "by_phase": {
            phase: {"runs": p["runs"], "suite_s": round(p["suite_s"], 1)}
            for phase, p in summary["by_phase"].items()
        },
    }


def _impl_attempts(rows) -> int:
    """GREEN attempts, as target-only rows. Every advance since R9.1e starts with a
    target-only run (`others_observed = 0`, one row per project), and a passing one
    adds a whole-suite run, which must not count twice. A cycle recorded earlier has
    no target-only GREEN rows: each of its attempts was a whole-suite run."""
    target_only = [r for r in rows if not r["others_observed"]]
    return len(target_only) if target_only else len(rows)


def metrics(ledger: Ledger, worktree: str) -> dict:
    runs = ledger.all("SELECT * FROM run WHERE worktree_path = ? ORDER BY id", (worktree,))
    out = {
        "runs": [],
        "note": (
            "Cross-plan aggregates are not comparable: cycle difficulty varies too much."
            " Compare runs of the same contract only (R11.1)."
        ),
    }
    imported = ledger.get_meta(PRE_SPLIT_IMPORT)
    if imported:
        # Runs up to `last_run_id` were recorded while the agent's uid could still open
        # the ledger. Whoever compares runs decides what that is worth; we only say so.
        out["pre_split_import"] = json.loads(imported)
    for run in runs:
        cycles = ledger.cycles(run["id"])
        # Pin cycles pass on arrival by design; refactor cycles have no test at all.
        standard = [c for c in cycles if c["kind"] not in ("pin", "refactor")]
        red_violations = ledger.all(
            "SELECT * FROM integrity_event WHERE run_id = ? AND kind = 'red_first_violation'",
            (run["id"],),
        )
        impl_attempts = [
            _impl_attempts(ledger.invocations(c["id"], "AWAITING_IMPL")) for c in cycles
        ]
        blockers = ledger.all(
            "SELECT kind, COUNT(*) n FROM blocker WHERE run_id = ? GROUP BY kind",
            (run["id"],),
        )
        by_project = defaultdict(int)
        for c in cycles:
            for p in json.loads(c["projects"]):
                by_project[p] += 1
        out["runs"].append(
            {
                "run": run["id"],
                "plan_contract": run["plan_contract_id"],
                "executor": run["executor_model"],
                "executor_source": run["executor_source"],
                "outcome": run["outcome"],
                "cycles_declared": len(
                    json.loads(
                        ledger.one(
                            "SELECT declared_cycles FROM plan_contract WHERE id = ?",
                            (run["plan_contract_id"],),
                        )["declared_cycles"]
                    )
                ),
                "cycles_closed": sum(1 for c in cycles if c["phase"] == "CLOSED"),
                "cycles_skipped": sum(1 for c in cycles if c["phase"] == "SKIPPED"),
                # R6.2 — pin cycles pass on arrival by design and are excluded.
                "red_first_violation_rate": (
                    round(len(red_violations) / len(standard), 3) if standard else None
                ),
                "impl_attempts_total": sum(impl_attempts),
                "impl_attempts_max": max(impl_attempts, default=0),
                "cycles_by_project": dict(by_project),
                "blockers": {b["kind"]: b["n"] for b in blockers},
                "human_interventions": len(
                    ledger.all("SELECT id FROM human_intervention WHERE run_id = ?", (run["id"],))
                ),
                "time": _time_json(_time_summary(ledger, run)),
                "integrity_events": {
                    r["kind"]: r["n"]
                    for r in ledger.all(
                        "SELECT kind, COUNT(*) n FROM integrity_event WHERE run_id = ?"
                        " GROUP BY kind",
                        (run["id"],),
                    )
                },
            }
        )
    return out
