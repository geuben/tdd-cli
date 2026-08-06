"""Fleet view — every agent's progress on this repository, in one summary.

The ledger is one SQLite database per repository, shared by all worktrees, so the
data already exists in one place; this module only reads it. Read-only is
structural, not conventional: the database is opened with SQLite's `mode=ro` URI,
so the command cannot create, migrate, or mutate the ledger that live agents are
writing mid-run. That is what makes it safe to run — from any worktree, on any
branch — while runs are in flight, even if this code's schema constant were ever
to drift from the one on disk.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from . import leases


def open_readonly(path: Path) -> sqlite3.Connection | None:
    """None when no ledger exists yet — `mode=ro` also refuses to create one."""
    if not path.is_file():
        return None
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _age_s(iso: str | None) -> float | None:
    if not iso:
        return None
    stamp = datetime.fromisoformat(iso)
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=timezone.utc)
    return round((datetime.now(timezone.utc) - stamp).total_seconds(), 1)


def _runs(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        "SELECT r.id, r.worktree_path, r.executor_model, r.started_at,"
        "       p.plan_path, p.declared_cycles"
        " FROM run r JOIN plan_contract p ON p.id = r.plan_contract_id"
        " WHERE r.ended_at IS NULL ORDER BY r.id"
    ).fetchall()
    out = []
    for row in rows:
        cycle = conn.execute(
            "SELECT ordinal, phase, title FROM cycle"
            " WHERE run_id = ? AND closed_at IS NULL ORDER BY ordinal LIMIT 1",
            (row["id"],),
        ).fetchone()
        last = conn.execute(
            "SELECT MAX(started_at) AS at FROM invocation WHERE run_id = ?",
            (row["id"],),
        ).fetchone()
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
                "last_activity_age_s": _age_s(last["at"] or row["started_at"]),
            }
        )
    return out


def _claims(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute("SELECT * FROM baseline_claim ORDER BY id").fetchall()
    return [
        {
            "worktree": r["worktree_path"],
            "hostname": r["hostname"],
            "projects_done": r["projects_done"],
            "projects_total": r["projects_total"],
            "current_project": r["current_project"],
            "elapsed_s": _age_s(r["started_at"]),
        }
        for r in rows
    ]


def summarise(ledger_db: Path) -> dict:
    conn = open_readonly(ledger_db)
    if conn is None:
        return {"runs": [], "collecting": [], "suites": leases.snapshot()}
    try:
        return {
            "runs": _runs(conn),
            "collecting": _claims(conn),
            "suites": leases.snapshot(),
        }
    finally:
        conn.close()


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
        lines.append(
            f"{c['worktree']}  collecting baseline"
            f" {c['projects_done']}/{c['projects_total']}"
            f" (current: {c['current_project'] or '-'}) — {c['elapsed_s']}s elapsed"
        )
    s = summary["suites"]
    lines.append(
        f"suites executing now: {s['active']}"
        f" — {s['workers_each']} worker(s) each of {s['total_cores']} cores"
    )
    if not summary["runs"] and not summary["collecting"]:
        lines.insert(0, "no active runs")
    return "\n".join(lines) + "\n"
