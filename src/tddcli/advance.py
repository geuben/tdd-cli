"""Phase handlers for `tdd advance` — the only command that changes phase (§8.3).

Every transition here is the consequence of an observed suite run. Nothing accepts a
phase from the caller.
"""

from __future__ import annotations

import json

from . import adapters, config as config_mod, gitutil, staging
from .adapters.base import FAILED, NOT_COLLECTED, NOT_FOUND, PASSED
from .envelope import Envelope, NextAction, Verb
from .ledger import now
from .machine import (
    AWAITING_IMPL,
    AWAITING_PIN,
    AWAITING_REFACTOR,
    AWAITING_TEST,
    SENSITIVITY_REQUIRED,
    Engine,
)


def _reply(engine: Engine, cycle, verb: Verb, detail: str, **result) -> Envelope:
    fresh = engine.ledger.one("SELECT * FROM cycle WHERE id = ?", (cycle["id"],)) if cycle else None
    return Envelope(
        run=engine.run_state(fresh or cycle),
        result=result,
        next_action=NextAction(verb, detail),
    )


def _last_invocation_hash(engine: Engine, cycle) -> str | None:
    rows = engine.ledger.invocations(cycle["id"], cycle["phase"])
    return rows[-1]["tree_hash"] if rows else None


def _adopt_target(engine: Engine, cycle, missing: list[str]) -> tuple[list[str], list[str]]:
    """R8.9 — resolve the target from newly collected tests when the declared id misses."""
    projects = json.loads(cycle["projects"])
    at_start = engine.ledger.collection(engine.run["id"])
    known = {t for tests in at_start.values() for t in tests}
    existing_targets = set(json.loads(cycle["target_tests"]))

    new_tests: list[str] = []
    for name in projects:
        adapter = adapters.build(engine.config.project(name), engine.worktree)
        current = adapter.collect()
        new_tests.extend(sorted(current.tests - known - existing_targets))
    return new_tests, missing


def _stage_and_commit(engine: Engine, cycle, phase: str, declared) -> tuple[str | None, list[str], object]:
    changed = engine.authored_changes(cycle)
    classification = staging.classify(
        engine.config, changed, json.loads(cycle["projects"]), declared, engine.excluded
    )
    if phase == staging.RED and classification.implementation:
        engine.ledger.event(
            engine.run["id"], cycle["id"], "implementation_during_red",
            json.dumps(classification.implementation),
        )
    if classification.outside:
        engine.ledger.event(
            engine.run["id"], cycle["id"], "undeclared_file_touched",
            json.dumps(classification.outside),
        )
    paths = staging.paths_for_phase(phase, classification)
    message = staging.default_message(phase, declared, cycle["ordinal"])
    sha, staged = staging.commit(
        engine.worktree, paths, message, engine.trailers(cycle, phase)
    )
    if sha:
        engine.record_commit(cycle, phase, sha, message, staged)
    return sha, staged, classification


# -- handlers ------------------------------------------------------------


def _handle_test_phase(engine: Engine, cycle, retried: bool, expect_pass: bool) -> Envelope:
    """AWAITING_TEST (expect fail) and AWAITING_PIN (expect pass) share this shape."""
    declared = engine.declared_for(cycle["ordinal"])
    projects = json.loads(cycle["projects"])
    targets = json.loads(cycle["target_tests"])
    phase = cycle["phase"]

    outcomes, others, _, failure = engine.run_projects(
        projects, targets, cycle, phase, retried
    )

    missing = [t for t, o in outcomes.items() if o == NOT_FOUND]
    if missing:
        candidates, _ = _adopt_target(engine, cycle, missing)
        if len(candidates) == 1:
            engine.ledger.event(
                engine.run["id"], cycle["id"], "declared_test_mismatch",
                json.dumps({"declared": missing, "adopted": candidates}),
            )
            kept = [t for t in targets if t not in missing]
            engine.ledger.update(
                "cycle", cycle["id"], target_tests=json.dumps(kept + candidates)
            )
            cycle = engine.ledger.one("SELECT * FROM cycle WHERE id = ?", (cycle["id"],))
            return _reply(
                engine, cycle, Verb.REFACTOR_OR_ADVANCE,
                f"Adopted {candidates[0]} as the target (declared {missing[0]} was not"
                " collected). Run `tdd advance` again to evaluate it.",
                adopted=candidates,
            )
        if len(candidates) > 1:
            engine.ledger.event(
                engine.run["id"], cycle["id"], "multiple_new_tests",
                json.dumps(candidates),
            )
            return _reply(
                engine, cycle, Verb.NAME_TARGET_TEST,
                "Several new tests appeared; a cycle covers one behaviour. Name the"
                " intended target with `tdd target <id>`.",
                candidates=candidates,
            )
        return _reply(
            engine, cycle, Verb.WRITE_TEST,
            f"Target {missing[0]} was not collected and no new test was found."
            " Write the failing test.",
            missing=missing,
        )

    not_collected = [t for t, o in outcomes.items() if o == NOT_COLLECTED]
    if not_collected:
        return _reply(
            engine, cycle, Verb.CREATE_STUB,
            f"{not_collected[0]} could not be collected — the module it imports does not"
            " exist yet. Create the stub, then run `tdd advance`.",
            not_collected=not_collected, failure=failure,
        )

    if others:
        return _reply(
            engine, cycle, Verb.FIX_REGRESSION,
            f"{len(others)} test(s) outside this cycle are failing. Fix them before"
            " proceeding.",
            other_failures=others,
        )

    passed_all = all(o == PASSED for o in outcomes.values())
    failed_all = all(o == FAILED for o in outcomes.values())

    if expect_pass:
        if not passed_all:
            return _reply(
                engine, cycle, Verb.WRITE_TEST,
                "A pin cycle's test must pass on arrival — it characterises behaviour"
                " that already exists. This one does not pass.",
                outcomes=outcomes, failure=failure,
            )
        sha, staged, _ = _stage_and_commit(engine, cycle, staging.PIN, declared)
        engine.transition(cycle, SENSITIVITY_REQUIRED)
        return _reply(
            engine, cycle, Verb.RUN_SENSITIVITY_CHECK,
            "Pin recorded. Now prove it bites: `tdd sensitivity begin`, mutate the"
            " behaviour under test, `tdd sensitivity check`, then `tdd sensitivity end`.",
            commit=sha, staged=staged,
        )

    if passed_all:
        engine.ledger.event(
            engine.run["id"], cycle["id"], "red_first_violation", json.dumps(targets)
        )
        return _reply(
            engine, cycle, Verb.RUN_SENSITIVITY_CHECK,
            "The test passed before any implementation. Run a sensitivity check to prove"
            " it can fail: `tdd sensitivity begin`, mutate, `tdd sensitivity check`,"
            " `tdd sensitivity end`.",
            outcomes=outcomes,
        )

    if not failed_all:
        return _reply(
            engine, cycle, Verb.WRITE_TEST,
            "A contract cycle's targets must all fail together before implementation.",
            outcomes=outcomes,
        )

    sha, staged, classification = _stage_and_commit(engine, cycle, staging.RED, declared)
    engine.transition(cycle, AWAITING_IMPL)
    return _reply(
        engine, cycle, Verb.WRITE_IMPLEMENTATION,
        f"RED confirmed. Write the minimum code to pass {targets[0]}, then"
        " `tdd advance`.",
        commit=sha, staged=staged, failure=failure,
        implementation_during_red=classification.implementation or None,
    )


def _handle_impl(engine: Engine, cycle, retried: bool) -> Envelope:
    declared = engine.declared_for(cycle["ordinal"])
    projects = json.loads(cycle["projects"])
    targets = json.loads(cycle["target_tests"])

    outcomes, others, _, failure = engine.run_projects(
        projects, targets, cycle, AWAITING_IMPL, retried
    )

    if others:
        return _reply(
            engine, cycle, Verb.FIX_REGRESSION,
            f"The implementation broke {len(others)} test(s) elsewhere.",
            other_failures=others,
        )
    if not all(o == PASSED for o in outcomes.values()):
        return _reply(
            engine, cycle, Verb.WRITE_IMPLEMENTATION,
            "Target still failing. Adjust the implementation and `tdd advance`.",
            outcomes=outcomes, failure=failure,
        )

    sha, staged, _ = _stage_and_commit(engine, cycle, staging.GREEN, declared)
    engine.transition(cycle, AWAITING_REFACTOR)
    return _reply(
        engine, cycle, Verb.REFACTOR_OR_ADVANCE,
        "GREEN confirmed. Refactor if the plan calls for it, then `tdd advance` to close"
        " the cycle.",
        commit=sha, staged=staged,
    )


def _handle_sensitivity(engine: Engine, cycle) -> Envelope:
    done = engine.ledger.completed_sensitivity(cycle["id"])
    if done is None:
        return _reply(
            engine, cycle, Verb.RUN_SENSITIVITY_CHECK,
            "A verified sensitivity check is required before this cycle can proceed.",
        )
    engine.transition(cycle, AWAITING_REFACTOR)
    return _reply(
        engine, cycle, Verb.REFACTOR_OR_ADVANCE,
        "Sensitivity verified. Perform the planned refactor, then `tdd advance`.",
    )


def _handle_refactor(engine: Engine, cycle, retried: bool) -> Envelope:
    declared = engine.declared_for(cycle["ordinal"])
    missing = engine.missing_annotations(cycle)
    if missing:
        return _reply(
            engine, cycle, Verb.ANNOTATE_CYCLE,
            "This plan requires judgement annotations before a cycle closes: "
            + ", ".join(missing),
            missing_annotations=missing,
        )

    touched = engine.authored_changes(cycle)
    sha, staged, _ = _stage_and_commit(engine, cycle, staging.REFACTOR, declared)
    if sha:
        touched = set(staged) | touched

    regenerated = engine.check_artifacts(cycle)
    outcome = engine.sweep(cycle, touched)

    if not outcome.ok:
        if outcome.failures:
            return _reply(
                engine, cycle, Verb.FIX_REGRESSION,
                f"Close sweep found {len(outcome.failures)} failing test(s).",
                failures=outcome.failures, commit=sha,
            )
        gates = [{"project": p, "kind": k, "output": o} for p, k, o in outcome.gates]
        return _reply(
            engine, cycle, Verb.FIX_REGRESSION,
            "Close sweep is green but lint/typecheck gates failed.",
            gates=gates, commit=sha,
        )

    nxt = engine.close_cycle(cycle)
    if nxt is None:
        return Envelope(
            run={
                "id": engine.run["id"],
                "plan": engine.contract_row["plan_path"],
                "cycle": cycle["ordinal"],
                "of": len(engine.declared),
                "phase": "CLOSED",
                "executor": engine.run["executor_model"],
            },
            result={"commit": sha, "regenerated": regenerated or None},
            next_action=NextAction(
                Verb.COMPLETE, "All declared cycles are complete. Run `tdd log render`."
            ),
        )
    declared_next = engine.declared_for(nxt["ordinal"])
    verb = Verb.WRITE_TEST
    detail = (
        f"Cycle {cycle['ordinal']} closed. Cycle {nxt['ordinal']}"
        f" ({declared_next.title or 'untitled'}): write the failing test"
        f" {json.loads(nxt['target_tests'])[0]}."
    )
    if nxt["kind"] == "pin":
        detail = (
            f"Cycle {cycle['ordinal']} closed. Cycle {nxt['ordinal']} is a pin cycle:"
            " write a characterisation test that passes on arrival."
        )
    return _reply(engine, nxt, verb, detail, commit=sha, regenerated=regenerated or None)


# -- entry point ---------------------------------------------------------

HANDLERS = {
    AWAITING_TEST: lambda e, c, r: _handle_test_phase(e, c, r, expect_pass=False),
    AWAITING_PIN: lambda e, c, r: _handle_test_phase(e, c, r, expect_pass=True),
    AWAITING_IMPL: _handle_impl,
    AWAITING_REFACTOR: _handle_refactor,
    SENSITIVITY_REQUIRED: lambda e, c, r: _handle_sensitivity(e, c),
}


def _check_config_drift(engine: Engine, cycle) -> None:
    """The registry is a reviewed file, not ledger state — so pin it and watch it.

    Widening `test_paths` mid-run would reclassify implementation as tests and
    silently disable the RED-commit detection in R9.14.
    """
    pinned = engine.run["config_sha"]
    if not pinned:
        return
    current = config_mod.config_sha(engine.worktree)
    if current == pinned:
        return
    already = engine.ledger.one(
        "SELECT id FROM integrity_event WHERE run_id = ? AND kind = 'config_changed'"
        " AND detail = ?",
        (engine.run["id"], current),
    )
    if already is None:
        engine.ledger.event(
            engine.run["id"], cycle["id"], "config_changed",
            current,
        )


def advance(engine: Engine, cycle, retry: bool = False) -> Envelope:
    _check_config_drift(engine, cycle)

    if engine.ledger.open_sensitivity(cycle["id"]) is not None:
        return _reply(
            engine, cycle, Verb.RUN_SENSITIVITY_CHECK,
            "A sensitivity check is open. Close it with `tdd sensitivity end` before"
            " advancing — the tree is deliberately mutated.",
        )

    phase = cycle["phase"]
    if phase in (AWAITING_TEST, AWAITING_PIN, AWAITING_IMPL):
        current = engine.tree_hash(json.loads(cycle["projects"]))
        previous = _last_invocation_hash(engine, cycle)
        if previous == current and not retry:
            consecutive = sum(
                1 for r in engine.ledger.invocations(cycle["id"], phase)[-3:]
                if r["retried"]
            )
            if consecutive >= 3:
                return _reply(
                    engine, cycle, Verb.RESOLVE_BLOCKER,
                    "Three consecutive retries with no change to the tree. Record a"
                    " blocker with `tdd blocker` or change the code.",
                )
            return _reply(
                engine, cycle, Verb.WRITE_IMPLEMENTATION
                if phase == AWAITING_IMPL else Verb.WRITE_TEST,
                "no_change_since_last_run — nothing under this cycle's project roots has"
                " changed since the last run. Edit the code, or pass --retry to re-run"
                " anyway (flaky or environmental failures).",
            )

    handler = HANDLERS.get(phase)
    if handler is None:
        return Envelope(
            ok=False, error=f"no handler for phase {phase}",
            run=engine.run_state(cycle),
        )
    return handler(engine, cycle, retry)
