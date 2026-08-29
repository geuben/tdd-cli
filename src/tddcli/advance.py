"""Phase handlers for `tdd advance` — the only command that changes phase (§8.3).

Every transition here is the consequence of an observed suite run. Nothing accepts a
phase from the caller.
"""

from __future__ import annotations

import json

from . import adapters, gitutil, staging
from . import config as config_mod
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

NUDGE_KINDS = {"red_first_violation", "undeclared_file_touched", "implementation_during_red"}


def _note_nudge(engine: Engine, cycle) -> str:
    if cycle is None:
        return ""
    events = engine.ledger.all(
        "SELECT kind FROM integrity_event WHERE cycle_id = ? AND kind IN ({})".format(
            ",".join("?" * len(NUDGE_KINDS))
        ),
        (cycle["id"], *NUDGE_KINDS),
    )
    if not events:
        return ""
    existing_note = engine.ledger.one(
        "SELECT id FROM note WHERE cycle_id = ?", (cycle["id"],)
    )
    if existing_note is not None:
        return ""
    return ' An integrity event was recorded on this cycle — consider `tdd note "<why>"` while the reason is fresh.'


def _reply(engine: Engine, cycle, verb: Verb, detail: str, **result) -> Envelope:
    fresh = engine.ledger.one("SELECT * FROM cycle WHERE id = ?", (cycle["id"],)) if cycle else None
    nudge = _note_nudge(engine, fresh or cycle)
    return Envelope(
        run=engine.run_state(fresh or cycle),
        result=result,
        next_action=NextAction(verb, detail + nudge),
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


def _stub_directive_issued(engine: Engine, cycle) -> bool:
    return engine.ledger.one(
        "SELECT id FROM integrity_event WHERE cycle_id = ? AND kind = 'stub_directive_issued'",
        (cycle["id"],),
    ) is not None


def _last_outside_emitted(engine: Engine, cycle) -> str | None:
    row = engine.ledger.one(
        "SELECT detail FROM integrity_event"
        " WHERE cycle_id = ? AND kind = 'undeclared_file_touched'"
        " ORDER BY id DESC LIMIT 1",
        (cycle["id"],),
    )
    return row["detail"] if row else None


def _sanctioned_stubs(engine: Engine, cycle, implementation: list[str]) -> list[str]:
    """The files that answer a `create_stub` directive the tool itself issued.

    Only *new* files qualify: an uncollectable import is satisfied by a module that
    did not exist, so a change to a file already at HEAD is implementation however
    the cycle arrived here.
    """
    if not implementation or not _stub_directive_issued(engine, cycle):
        return []
    at_head = gitutil.tracked_at_head(engine.worktree, implementation)
    return [p for p in implementation if p not in at_head]


def _stage_and_commit(engine: Engine, cycle, phase: str, declared) -> tuple[str | None, list[str], object]:
    changed = engine.authored_changes(cycle)
    classification = staging.classify(
        engine.config, changed, json.loads(cycle["projects"]), declared, engine.excluded,
        ancillary=set(engine.ancillary_files),
    )
    if phase == staging.RED:
        adopted = _sanctioned_stubs(engine, cycle, classification.implementation)
        if adopted:
            classification.adopt_stubs(adopted)
            engine.ledger.event(
                engine.run["id"], cycle["id"], "stub_adopted", json.dumps(adopted),
            )
        if classification.implementation:
            engine.ledger.event(
                engine.run["id"], cycle["id"], "implementation_during_red",
                json.dumps(classification.implementation),
            )
    if classification.outside:
        _detail = json.dumps(classification.outside)
        if _last_outside_emitted(engine, cycle) != _detail:
            engine.ledger.event(
                engine.run["id"], cycle["id"], "undeclared_file_touched",
                _detail,
            )
    paths = staging.paths_for_phase(phase, classification)
    message = staging.default_message(phase, declared, cycle["ordinal"])
    sha, staged = staging.commit(
        engine.worktree, paths, message, engine.trailers(cycle, phase)
    )
    if sha:
        engine.record_commit(cycle, phase, sha, message, staged)
    return sha, staged, classification


def _disambiguate(candidates: list[str], declared: str, adapter) -> str | None:
    norm_declared = adapter.normalise_id(declared)
    matches = [c for c in candidates if adapter.normalise_id(c) == norm_declared]
    if len(matches) == 1:
        return matches[0]
    declared_file = declared.split("::", 1)[-1].split("::")[0].split(" > ")[0]
    same_file = [c for c in candidates if c.split("::", 1)[-1].split("::")[0].split(" > ")[0] == declared_file]
    if len(same_file) == 1:
        return same_file[0]
    return None


def _outcome_from_verdicts(verdicts, test_id: str) -> str | None:
    for v in verdicts:
        if test_id in v.failed:
            return FAILED
        if test_id in v.passed:
            return PASSED
    return None


# -- handlers ------------------------------------------------------------


def _handle_test_phase(engine: Engine, cycle, retried: bool, expect_pass: bool) -> Envelope:
    """AWAITING_TEST (expect fail) and AWAITING_PIN (expect pass) share this shape."""
    declared = engine.declared_for(cycle["ordinal"])
    projects = json.loads(cycle["projects"])
    targets = json.loads(cycle["target_tests"])
    phase = cycle["phase"]

    outcomes, others, verdicts, failure = engine.run_projects(
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
            adopted_outcome = _outcome_from_verdicts(verdicts, candidates[0])
            if adopted_outcome is None:
                return _reply(
                    engine, cycle, Verb.REFACTOR_OR_ADVANCE,
                    f"Adopted {candidates[0]} as the target (declared {missing[0]} was not"
                    " collected). Run `tdd advance` again to evaluate it.",
                    adopted=candidates,
                )
            targets = kept + candidates
            outcomes = {candidates[0]: adopted_outcome}
            others = [t for t in others if t != candidates[0]]
        elif len(candidates) > 1:
            owner = missing[0].split("::", 1)[0]
            adapter = adapters.build(engine.config.project(owner), engine.worktree)
            resolved = _disambiguate(candidates, missing[0], adapter)
            if resolved is not None:
                engine.ledger.event(
                    engine.run["id"], cycle["id"], "declared_test_mismatch",
                    json.dumps({"declared": missing, "adopted": [resolved], "all_candidates": candidates}),
                )
                kept = [t for t in targets if t not in missing]
                engine.ledger.update(
                    "cycle", cycle["id"], target_tests=json.dumps(kept + [resolved])
                )
                cycle = engine.ledger.one("SELECT * FROM cycle WHERE id = ?", (cycle["id"],))
                adopted_outcome = _outcome_from_verdicts(verdicts, resolved)
                if adopted_outcome is None:
                    return _reply(
                        engine, cycle, Verb.REFACTOR_OR_ADVANCE,
                        f"Adopted {resolved} as the target (declared {missing[0]} was not"
                        " collected). Run `tdd advance` again to evaluate it.",
                        adopted=[resolved],
                    )
                targets = kept + [resolved]
                outcomes = {resolved: adopted_outcome}
                others = [t for t in others if t != resolved]
            else:
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
        else:
            return _reply(
                engine, cycle, Verb.WRITE_TEST,
                f"Target {missing[0]} was not collected and no new test was found."
                " Write the failing test.",
                missing=missing,
            )

    not_collected = [t for t, o in outcomes.items() if o == NOT_COLLECTED]
    if not_collected:
        if not _stub_directive_issued(engine, cycle):
            engine.ledger.event(
                engine.run["id"], cycle["id"], "stub_directive_issued",
                json.dumps(not_collected),
            )
        owner = not_collected[0].split("::", 1)[0]
        hint = adapters.build(engine.config.project(owner), engine.worktree).stub_hint()
        return _reply(
            engine, cycle, Verb.CREATE_STUB,
            f"{not_collected[0]} could not be collected — the module it imports does not"
            " exist yet. Create the stub and nothing else: no logic, no behaviour, just"
            f" enough for the import and the type checker ({hint})."
            " It is staged with the test in the RED commit, not counted as"
            " implementation. Then run `tdd advance`.",
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
        # The phase must move, or the verified check is never read: _handle_sensitivity
        # is reachable only from SENSITIVITY_REQUIRED, so staying here asks forever.
        engine.transition(cycle, SENSITIVITY_REQUIRED)
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

    # §6.1 — when nothing changed since GREEN, the cycle's own suites just passed on an
    # identical tree. A refactor cycle never skips: its suite is the only guard.
    prior = engine.ledger.invocations(cycle["id"], AWAITING_IMPL)
    skip_own = bool(
        cycle["kind"] != "refactor"
        and sha is None
        and prior
        and prior[-1]["tree_hash"] == engine.tree_hash(json.loads(cycle["projects"]))
    )
    outcome = engine.sweep(cycle, touched, skip_own=skip_own)

    if not outcome.ok:
        if outcome.unbaselined:
            projects_list = ", ".join(sorted(outcome.unbaselined))
            return _reply(
                engine, cycle, Verb.RESOLVE_BLOCKER,
                f"Close sweep found failures in un-baselined project(s): {projects_list}. "
                "These are unattributable — no baseline exists to subtract. "
                "File: tdd blocker --kind no_baseline_for_project --detail '...', "
                "then resume --unblock --accept-failures to fold them into the baseline.",
                unbaselined=outcome.unbaselined, commit=sha,
            )
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
        blocking = engine.close_undeclared_gate(cycle)
        if blocking:
            engine.ledger.insert(
                "blocker",
                run_id=engine.run["id"],
                cycle_id=cycle["id"],
                kind="undeclared_file_uncommitted",
                detail=json.dumps(blocking),
                at=now(),
            )
            engine.ledger.update("run", engine.run["id"], outcome="blocked")
            return Envelope(
                run={
                    "id": engine.run["id"],
                    "plan": engine.contract_row["plan_path"],
                    "cycle": cycle["ordinal"],
                    "of": len(engine.declared),
                    "phase": "BLOCKED",
                    "executor": engine.run["executor_model"],
                },
                result={
                    "kind": "undeclared_file_uncommitted",
                    "paths": blocking,
                    "commit": sha,
                },
                next_action=NextAction(
                    Verb.BLOCKED,
                    f"Run reached its last cycle but {len(blocking)} flagged file(s) are"
                    f" uncommitted: {blocking}. Commit them, or"
                    " `tdd resume --unblock --note ...` to discard.",
                ),
            )
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
                Verb.COMPLETE,
                "All declared cycles are complete."
                " Before rendering, record a closing narrative with `tdd note \"<hardest cycle and why, plan inaccuracies, deviations>\"`."
                " Then run `tdd log render`.",
            ),
        )
    verb, opening = engine.opening_action(nxt)
    return _reply(
        engine, nxt, verb, f"Cycle {cycle['ordinal']} closed. {opening}",
        commit=sha, regenerated=regenerated or None,
    )


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
