"""Projections over the ledger: the friction log (§8.5) and metrics (§11.3).

The friction log is rendered, never composed by hand — every observable fact comes
from recorded events, and only judgement fields come from annotations.
"""

from __future__ import annotations

import json
from collections import defaultdict

from .ledger import Ledger

OBSERVED_HEADING = "Observed"
JUDGEMENT_HEADING = "Judgement"


def _fmt_list(items) -> str:
    return ", ".join(f"`{i}`" for i in items) if items else "none"


def friction_log(ledger: Ledger, run) -> str:
    contract = ledger.one(
        "SELECT * FROM plan_contract WHERE id = ?", (run["plan_contract_id"],)
    )
    cycles = ledger.cycles(run["id"])
    lines: list[str] = []
    a = lines.append

    a(f"# Implementation Friction Log: {contract['plan_path']}")
    a("")
    a(f"- Run: {run['id']}")
    a(f"- Executor: {run['executor_model']} (source: {run['executor_source']})")
    a(f"- Plan blob: `{contract['git_blob_sha']}` ({contract['status']})")
    a(f"- Started: {run['started_at']}  Ended: {run['ended_at'] or '—'}"
      f"  Outcome: {run['outcome'] or 'live'}")
    baselines = ledger.baselines(run["id"])
    a(f"- Baseline failures at start: "
      + (", ".join(f"{k}={len(v)}" for k, v in baselines.items()) or "none"))
    a("")

    declared = json.loads(contract["declared_cycles"])
    delivered = {c["ordinal"] for c in cycles if c["phase"] == "CLOSED"}
    skipped = {c["ordinal"] for c in cycles if c["phase"] == "SKIPPED"}
    a("## Plan fidelity")
    a("")
    a(f"- Declared cycles: {len(declared)}")
    a(f"- Delivered: {len(delivered)}   Skipped: {len(skipped)}")
    missing = sorted({d['n'] for d in declared} - delivered - skipped)
    a(f"- Never reached: {missing or 'none'}")
    interventions = ledger.all(
        "SELECT * FROM human_intervention WHERE run_id = ?", (run["id"],)
    )
    a(f"- Human interventions: {len(interventions)}")
    for i in interventions:
        a(f"  - {i['at']}: {i['note']}")
    a("")

    events = defaultdict(list)
    for e in ledger.all("SELECT * FROM integrity_event WHERE run_id = ?", (run["id"],)):
        events[e["cycle_id"]].append(e)

    for cycle in reversed(cycles):
        a(f"### Cycle {cycle['ordinal']}"
          + (f": {cycle['title']}" if cycle["title"] else "")
          + f"  _({cycle['kind']})_")
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
            a(f"- **Sensitivity check:** verified, restore byte-identical")
            if sens["observed_failure"]:
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
        a("")

    blockers = ledger.all("SELECT * FROM blocker WHERE run_id = ?", (run["id"],))
    if blockers:
        a("## Blockers")
        a("")
        for b in blockers:
            a(f"- **{b['kind']}** (cycle {b['cycle_id']}): {b['detail']}")
        a("")
    return "\n".join(lines) + "\n"


def metrics(ledger: Ledger, worktree: str) -> dict:
    runs = ledger.all(
        "SELECT * FROM run WHERE worktree_path = ? ORDER BY id", (worktree,)
    )
    out = {"runs": [], "note": (
        "Cross-plan aggregates are not comparable: cycle difficulty varies too much."
        " Compare runs of the same contract only (R11.1)."
    )}
    for run in runs:
        cycles = ledger.cycles(run["id"])
        # Pin cycles pass on arrival by design; refactor cycles have no test at all.
        standard = [c for c in cycles if c["kind"] not in ("pin", "refactor")]
        red_violations = ledger.all(
            "SELECT * FROM integrity_event WHERE run_id = ? AND kind = 'red_first_violation'",
            (run["id"],),
        )
        impl_attempts = [
            len(ledger.invocations(c["id"], "AWAITING_IMPL")) for c in cycles
        ]
        blockers = ledger.all(
            "SELECT kind, COUNT(*) n FROM blocker WHERE run_id = ? GROUP BY kind",
            (run["id"],),
        )
        by_project = defaultdict(int)
        for c in cycles:
            for p in json.loads(c["projects"]):
                by_project[p] += 1
        out["runs"].append({
            "run": run["id"],
            "plan_contract": run["plan_contract_id"],
            "executor": run["executor_model"],
            "executor_source": run["executor_source"],
            "outcome": run["outcome"],
            "cycles_declared": len(json.loads(
                ledger.one("SELECT declared_cycles FROM plan_contract WHERE id = ?",
                           (run["plan_contract_id"],))["declared_cycles"]
            )),
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
            "human_interventions": len(ledger.all(
                "SELECT id FROM human_intervention WHERE run_id = ?", (run["id"],)
            )),
            "integrity_events": {
                r["kind"]: r["n"] for r in ledger.all(
                    "SELECT kind, COUNT(*) n FROM integrity_event WHERE run_id = ?"
                    " GROUP BY kind", (run["id"],)
                )
            },
        })
    return out
