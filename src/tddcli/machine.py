"""The state machine (§6). Phases are computed from observed test runs, never asserted.

Two cycle kinds:

* standard/contract — AWAITING_TEST → AWAITING_IMPL → AWAITING_REFACTOR → CLOSED
* pin — AWAITING_PIN → SENSITIVITY_REQUIRED → AWAITING_REFACTOR → CLOSED

A pin cycle's test passes on arrival by design (R6.2), so it is excluded from the
RED-first violation metric. A *standard* cycle that passes on arrival remains a
violation and is never reclassified as a pin (R6.4) — the kind is declared by the plan
in advance, never inferred from the outcome.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path

from . import adapters, contract as contract_mod, gitutil, staging
from .adapters.base import FAILED, NOT_COLLECTED, NOT_FOUND, PASSED
from .config import Config
from .contract import PIN, REFACTOR, DeclaredCycle
from .envelope import Verb, heartbeat
from .ledger import Ledger, now

AWAITING_TEST = "AWAITING_TEST"
AWAITING_IMPL = "AWAITING_IMPL"
AWAITING_REFACTOR = "AWAITING_REFACTOR"
AWAITING_PIN = "AWAITING_PIN"
SENSITIVITY_REQUIRED = "SENSITIVITY_REQUIRED"
CLOSED = "CLOSED"
SKIPPED = "SKIPPED"

#: A refactor cycle has no test of its own, so it opens straight into the refactor
#: phase: the existing suite plus the close sweep are its only guard.
OPENING_PHASE = {PIN: AWAITING_PIN, REFACTOR: AWAITING_REFACTOR}


@dataclass
class SweepOutcome:
    failures: list[str]
    gates: list[tuple[str, str, str]]      # (project, kind, output)

    @property
    def ok(self) -> bool:
        return not self.failures and not self.gates


class Engine:
    def __init__(self, ledger: Ledger, config: Config, worktree: Path, run_row):
        self.ledger = ledger
        self.config = config
        self.worktree = worktree
        self.run = run_row
        self.contract_row = ledger.one(
            "SELECT * FROM plan_contract WHERE id = ?", (run_row["plan_contract_id"],)
        )
        self.declared = contract_mod.cycles_from_json(self.contract_row["declared_cycles"])
        self.annotation_keys = json.loads(self.contract_row["annotation_keys"])
        self.excluded = set(json.loads(run_row["preexisting_dirty"]))

    # -- helpers ---------------------------------------------------------

    def declared_for(self, ordinal: int) -> DeclaredCycle | None:
        return next((c for c in self.declared if c.ordinal == ordinal), None)

    def roots(self, project_names: list[str]) -> list[str]:
        return [self.config.project(n).root for n in project_names]

    def tree_hash(self, project_names: list[str]) -> str:
        return gitutil.tree_hash(self.worktree, self.roots(project_names))

    def authored_changes(self, cycle_row) -> set[str]:
        return {
            p
            for p in gitutil.changed_paths(self.worktree)
            if p not in self.excluded
        }

    def trailers(self, cycle_row, phase: str) -> dict[str, str]:
        return {
            "TDD-Run": str(self.run["id"]),
            "TDD-Cycle": str(cycle_row["ordinal"]),
            "TDD-Phase": phase,
        }

    def run_state(self, cycle_row) -> dict:
        return {
            "id": self.run["id"],
            "plan": self.contract_row["plan_path"],
            "cycle": cycle_row["ordinal"] if cycle_row else None,
            "of": len(self.declared) or None,
            "kind": cycle_row["kind"] if cycle_row else None,
            "phase": cycle_row["phase"] if cycle_row else None,
            "projects": json.loads(cycle_row["projects"]) if cycle_row else [],
            "executor": self.run["executor_model"],
        }

    # -- suite execution -------------------------------------------------

    def _baselines(self) -> dict[str, set[str]]:
        return self.ledger.baselines(self.run["id"])

    def run_projects(
        self, project_names: list[str], targets: list[str], cycle_row, phase: str,
        retried: bool = False,
    ) -> tuple[dict[str, str], list[str], list, str]:
        """Run each project once. Returns (target outcomes, other failures, verdicts, failure text)."""
        baselines = self._baselines()
        outcomes: dict[str, str] = {}
        others: list[str] = []
        verdicts = []
        failure_text = ""
        tree = self.tree_hash(project_names)

        for name in project_names:
            project = self.config.project(name)
            adapter = adapters.build(project, self.worktree)
            target = next((t for t in targets if t.startswith(f"{name}::")), None)
            started = time.monotonic()
            verdict = adapter.run(target)
            elapsed = time.monotonic() - started
            verdicts.append(verdict)
            # Unconditional, not past a duration threshold — a conditional heartbeat
            # goes silent exactly when a run is slow for an unexpected reason.
            # Distinct event name from `baseline_captured`: same channel, different
            # meaning. One insertion point covers every phase, close sweeps included.
            heartbeat(
                event="project_completed", project=name, elapsed_s=round(elapsed, 2),
            )

            base = baselines.get(name, set())
            other = [f for f in verdict.failed if f not in base and f not in targets]
            others.extend(other)
            if target is not None:
                outcomes[target] = verdict.target_outcome
                if verdict.target_failure:
                    failure_text = verdict.target_failure

            self.ledger.insert(
                "invocation",
                run_id=self.run["id"],
                cycle_id=cycle_row["id"],
                phase_at=phase,
                project=name,
                adapter=adapter.name,
                target_test=target,
                target_outcome=verdict.target_outcome if target else None,
                target_failure=verdict.target_failure[:2000],
                total_passed=len(verdict.passed),
                total_failed=len(verdict.failed),
                other_failures=json.dumps(other),
                duration_ms=verdict.duration_ms,
                retried=int(retried),
                tree_hash=tree,
                started_at=now(),
            )
            if verdict.error:
                self.ledger.event(
                    self.run["id"], cycle_row["id"], "tooling_defect", verdict.error
                )
        return outcomes, others, verdicts, failure_text

    def sweep(self, cycle_row, touched: set[str], skip_own: bool = False) -> SweepOutcome:
        """R9.2 — cycle projects plus anything downstream of an artifact it touched.

        `skip_own` drops the cycle's own suites when the tree is unchanged since GREEN:
        they just passed on an identical tree. Downstream projects still run, having
        not run at all yet. Never set for a refactor cycle, where the existing suite
        is the only guard there is.
        """
        cycle_projects = json.loads(cycle_row["projects"])
        names = self.config.close_sweep_projects(cycle_projects, touched)
        if skip_own:
            names = [n for n in names if n not in cycle_projects]
        baselines = self._baselines()
        failures: list[str] = []
        gates: list[tuple[str, str, str]] = []

        for name in names:
            project = self.config.project(name)
            adapter = adapters.build(project, self.worktree)
            verdict = adapter.run(None)
            base = baselines.get(name, set())
            failures.extend(f for f in verdict.failed if f not in base)
            self.ledger.insert(
                "invocation",
                run_id=self.run["id"],
                cycle_id=cycle_row["id"],
                phase_at="CLOSE_SWEEP",
                project=name,
                adapter=adapter.name,
                target_test=None,
                target_outcome=None,
                target_failure="",
                total_passed=len(verdict.passed),
                total_failed=len(verdict.failed),
                other_failures=json.dumps(verdict.failed),
                duration_ms=verdict.duration_ms,
                tree_hash=self.tree_hash([name]),
                started_at=now(),
            )
            for kind, gate in (("lint", adapter.lint()), ("typecheck", adapter.typecheck())):
                self.ledger.insert(
                    "gate_result",
                    run_id=self.run["id"],
                    cycle_id=cycle_row["id"],
                    project=name,
                    kind=kind,
                    ok=int(gate.ok),
                    output=gate.output,
                    at=now(),
                )
                if not gate.ok:
                    gates.append((name, kind, gate.output))
        return SweepOutcome(failures=failures, gates=gates)

    # -- artifacts -------------------------------------------------------

    def check_artifacts(self, cycle_row) -> list[str]:
        """R9.12/R9.20 — the tool regenerates; the agent is informed, not asked."""
        regenerated: list[str] = []
        for art in self.config.artifacts.values():
            if not art.check and not art.regenerate:
                continue
            stale = self._artifact_stale(art)
            self.ledger.insert(
                "artifact_check",
                run_id=self.run["id"],
                cycle_id=cycle_row["id"] if cycle_row else None,
                artifact=art.name,
                stale=int(stale),
                regenerated=0,
                at=now(),
            )
            if not stale:
                continue
            self.ledger.event(
                self.run["id"], cycle_row["id"] if cycle_row else None,
                "stale_artifact", art.name,
            )
            if art.regenerate:
                adapters.base.run_command(art.regenerate, self.worktree)
                paths = [
                    p for p in gitutil.changed_paths(self.worktree)
                    if self.config.is_generated(p)
                ]
                sha, staged = staging.commit_generated(
                    self.worktree, paths, art.name,
                    self.trailers(cycle_row, "artifact") if cycle_row else {},
                )
                if sha:
                    self.ledger.insert(
                        "commit_record",
                        run_id=self.run["id"],
                        cycle_id=cycle_row["id"] if cycle_row else None,
                        phase="artifact",
                        sha=sha,
                        message=f"chore({art.name}): regenerate",
                        files=json.dumps(staged),
                        at=now(),
                    )
                regenerated.append(art.name)
        return regenerated

    def _artifact_stale(self, art) -> bool:
        if art.check:
            code, _, _ = adapters.base.run_command(art.check, self.worktree)
            return code != 0
        if not art.regenerate:
            return False
        before = gitutil.tree_hash(self.worktree, [art.path])
        adapters.base.run_command(art.regenerate, self.worktree)
        return gitutil.tree_hash(self.worktree, [art.path]) != before

    # -- cycle lifecycle -------------------------------------------------

    def open_cycle(self, ordinal: int):
        declared = self.declared_for(ordinal)
        if declared is None:
            return None
        phase = OPENING_PHASE.get(declared.kind, AWAITING_TEST)
        cycle_id = self.ledger.insert(
            "cycle",
            run_id=self.run["id"],
            ordinal=ordinal,
            kind=declared.kind,
            projects=json.dumps(declared.projects),
            declared_tests=json.dumps(
                [self._qualify(declared, t) for t in declared.tests]
            ),
            target_tests=json.dumps(
                [self._qualify(declared, t) for t in declared.tests]
            ),
            phase=phase,
            head_at_open=gitutil.head(self.worktree),
            title=declared.title,
            opened_at=now(),
        )
        return self.ledger.one("SELECT * FROM cycle WHERE id = ?", (cycle_id,))

    @staticmethod
    def _qualify(declared: DeclaredCycle, test_id: str) -> str:
        if "::" in test_id and test_id.split("::", 1)[0] in declared.projects:
            return test_id
        for project in declared.projects:
            if test_id.startswith(f"{project}/"):
                return f"{project}::{test_id[len(project) + 1:]}"
        return f"{declared.projects[0]}::{test_id}"

    def transition(self, cycle_row, to_phase: str) -> None:
        self.ledger.insert(
            "transition",
            cycle_id=cycle_row["id"],
            from_phase=cycle_row["phase"],
            to_phase=to_phase,
            at=now(),
        )
        self.ledger.update("cycle", cycle_row["id"], phase=to_phase)

    def close_cycle(self, cycle_row):
        self.transition(cycle_row, CLOSED)
        self.ledger.update("cycle", cycle_row["id"], closed_at=now())
        nxt = next(
            (c for c in self.declared if c.ordinal > cycle_row["ordinal"]), None
        )
        if nxt is None:
            self.ledger.update(
                "run", self.run["id"], ended_at=now(), outcome="complete"
            )
            return None
        return self.open_cycle(nxt.ordinal)

    def record_commit(self, cycle_row, phase: str, sha: str, message: str, files: list[str]):
        self.ledger.insert(
            "commit_record",
            run_id=self.run["id"],
            cycle_id=cycle_row["id"],
            phase=phase,
            sha=sha,
            message=message,
            files=json.dumps(files),
            at=now(),
        )

    def opening_action(self, cycle_row) -> tuple[Verb, str]:
        """What the agent must do first in a newly opened cycle, by kind."""
        ordinal = cycle_row["ordinal"]
        title = cycle_row["title"] or "untitled"
        targets = json.loads(cycle_row["target_tests"])
        if cycle_row["kind"] == REFACTOR:
            return Verb.REFACTOR_OR_ADVANCE, (
                f"Cycle {ordinal} ({title}) is behaviour-preserving: perform the"
                " migration, then `tdd advance`. The existing suite is the guard."
            )
        if cycle_row["kind"] == PIN:
            return Verb.WRITE_TEST, (
                f"Cycle {ordinal} ({title}) is a pin cycle: write a characterisation"
                " test that passes on arrival."
            )
        target = targets[0] if targets else "the declared test"
        return Verb.WRITE_TEST, (
            f"Cycle {ordinal} ({title}): write the failing test {target}."
        )

    def missing_annotations(self, cycle_row) -> list[str]:
        if not self.annotation_keys:
            return []
        present = {
            r["key"]
            for r in self.ledger.all(
                "SELECT key FROM annotation WHERE cycle_id = ?", (cycle_row["id"],)
            )
        }
        return [k for k in self.annotation_keys if k not in present]
