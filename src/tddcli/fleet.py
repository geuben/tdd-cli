"""Fleet view — every agent's progress on this repository, in one summary.

The ledger is one SQLite database per repository, shared by all worktrees, so the
data already exists in one place; this module only reads it, through a reader from
`ledger.open_readonly`. Read-only is structural, not conventional: that reader
cannot create, migrate, or mutate the ledger that live agents are writing mid-run.
That is what makes it safe to run — from any worktree, on any branch — while runs
are in flight.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

from . import leases
from .ledger import Ledger, claim_is_stale


def _age_s(iso: str | None) -> float | None:
    if not iso:
        return None
    stamp = datetime.fromisoformat(iso)
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=timezone.utc)
    return round((datetime.now(timezone.utc) - stamp).total_seconds(), 1)


def _runs(reader: Ledger) -> list[dict]:
    out = []
    for row in reader.active_runs():
        cycle = reader.open_cycle(row["id"])
        last_at = reader.last_invocation_at(row["id"])
        out.append(
            {
                "run_id": row["id"],
                "worktree": row["worktree_path"],
                "plan": row["plan_path"],
                "executor": row["executor_model"],
                "started_at": row["started_at"],
                "cycle": cycle["ordinal"] if cycle else None,
                "of": len(json.loads(row["declared_cycles"])) or None,
                "phase": cycle["phase"] if cycle else None,
                "title": cycle["title"] if cycle else None,
                # Staleness signal for a wedged agent: age of the newest suite
                # invocation, falling back to run start when none has landed yet.
                "last_activity_age_s": _age_s(last_at or row["started_at"]),
            }
        )
    return out


def _claims(reader: Ledger) -> list[dict]:
    rows = reader.baseline_claims()
    return [
        {
            "worktree": r["worktree_path"],
            "hostname": r["hostname"],
            "projects_done": r["projects_done"],
            "projects_total": r["projects_total"],
            "current_project": r["current_project"],
            "elapsed_s": _age_s(r["started_at"]),
            "pid": r["pid"],
            "stale": claim_is_stale(r["hostname"], r["pid"], r["started_at"]),
        }
        for r in rows
    ]


def _advance_claims(reader: Ledger) -> list[dict]:
    rows = reader.advance_claims()
    return [
        {
            "worktree": r["worktree_path"],
            "hostname": r["hostname"],
            "pid": r["pid"],
            "stale": claim_is_stale(r["hostname"], r["pid"], r["started_at"]),
            "elapsed_s": _age_s(r["started_at"]),
        }
        for r in rows
    ]


def summarise(reader: Ledger | None) -> dict:
    """`reader` is from `ledger.open_readonly`: None when no ledger exists yet."""
    if reader is None:
        return {"runs": [], "collecting": [], "advancing": [], "suites": leases.snapshot()}
    try:
        return {
            "runs": _runs(reader),
            "collecting": _claims(reader),
            "advancing": _advance_claims(reader),
            "suites": leases.snapshot(),
        }
    finally:
        reader.close()


def render(summary: dict) -> str:
    lines = []
    for r in summary["runs"]:
        cycle = f"cycle {r['cycle']}/{r['of']}" if r["cycle"] else "between cycles"
        title = f" ({r['title']})" if r.get("title") else ""
        lines.append(
            f"{r['worktree']}  {r['plan']}  {cycle}{title}  {r['phase'] or '-'}"
            f"  last activity {r['last_activity_age_s']}s ago"
        )
    for c in summary["collecting"]:
        line = (
            f"{c['worktree']}  collecting baseline"
            f" {c['projects_done']}/{c['projects_total']}"
            f" (current: {c['current_project'] or '-'}) — {c['elapsed_s']}s elapsed"
        )
        if c.get("stale"):
            line += f" — collector (pid {c['pid']}) is dead"
        lines.append(line)
    for a in summary["advancing"]:
        line = f"{a['worktree']}  advance in flight — {a['elapsed_s']}s elapsed"
        if a.get("stale"):
            line += f" — holder (pid {a['pid']}) is dead"
        lines.append(line)
    s = summary["suites"]
    lines.append(
        f"suites executing now: {s['active']}"
        f" — {s['workers_each']} worker(s) each of {s['total_cores']} cores"
    )
    if not summary["runs"] and not summary["collecting"] and not summary["advancing"]:
        lines.insert(0, "no active runs")
    return "\n".join(lines) + "\n"
