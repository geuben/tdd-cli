"""Command surface (§8). Transport-agnostic by construction (R13.8).

No command accepts a phase, a cycle number, or executor identity (R8.3).
"""

from __future__ import annotations

import argparse
import difflib
import json
import os
import socket
import sqlite3
import sys
import time
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path

from . import (
    __version__,
    adapters,
    fleet,
    gitutil,
    identity,
    render,
    snapshot,
)
from . import (
    config as config_mod,
)
from . import (
    contract as contract_mod,
)
from .adapters.base import FAILED, NOT_COLLECTED
from .advance import advance as do_advance
from .envelope import Envelope, NextAction, Verb, failure, heartbeat
from .ledger import Ledger, LedgerVersionError, ledger_path, now
from .machine import CLOSED, SKIPPED, Engine

BLOCKER_KINDS = {
    "regression",
    "target_unfixable",
    "bad_red",
    "plan_defect",
    "tooling",
    "context_exhausted",
    # Failing, but not caused by this run — a flake, or something the baseline missed.
    # Distinct from `regression`, which records a defect the run introduced.
    "pre_existing_failure",
}


def _worktree() -> Path:
    return gitutil.worktree_root(Path.cwd())


def _context(require_run: bool = True):
    worktree = _worktree()
    cfg = config_mod.load(worktree)
    ledger = Ledger(gitutil.repo_identity(worktree))
    run = ledger.active_run(str(worktree))
    if require_run and run is None:
        raise SystemExit(
            failure("no active run in this worktree; `tdd run start --plan <path>`").emit()
        )
    return worktree, cfg, ledger, run


def _engine(worktree, cfg, ledger, run) -> Engine:
    return Engine(ledger, cfg, worktree, run)


def _claim_elapsed_s(claim: dict) -> float:
    started = datetime.fromisoformat(claim["started_at"])
    if started.tzinfo is None:
        started = started.replace(tzinfo=timezone.utc)
    return round((datetime.now(timezone.utc) - started).total_seconds(), 2)


def _collecting_envelope(claim: dict) -> Envelope:
    """Shared by `cmd_progress` (JSON and bare) and `cmd_status`: a claim with no run
    row yet is an in-flight baseline, not "never started". `status` is
    documented as the agent's machine view; agents polled `progress` because
    `status` gave them nothing — routing them to the human command to learn machine
    state was the actual defect."""
    return Envelope(
        result={
            "status": "collecting_baseline",
            "projects_done": claim["projects_done"],
            "projects_total": claim["projects_total"],
            "current_project": claim["current_project"],
            "elapsed_s": _claim_elapsed_s(claim),
        },
        next_action=NextAction(
            Verb.AWAIT_BASELINE,
            "A baseline is being collected; poll `tdd progress` again.",
        ),
    )


# -- commands ------------------------------------------------------------


PYTHON_PROJECT_MARKERS = ("pyproject.toml", "setup.cfg", "setup.py", "pytest.ini")
VITEST_CONFIGS = ("vitest.config.ts", "vitest.config.js", "vitest.config.mts", "vitest.config.mjs")


def _detect_adapter(directory: Path) -> tuple[str, str] | None:
    """(adapter, test_paths) for a directory, or None when nothing matches.

    A `package.json` alone is not vitest evidence — a jest or mocha project has
    one too, and a wrong guess here writes a config that fails on first use.
    """
    if any((directory / marker).is_file() for marker in PYTHON_PROJECT_MARKERS):
        return "pytest", '["tests/"]'
    if any((directory / c).is_file() for c in VITEST_CONFIGS):
        return "vitest", '["**/__tests__/**", "**/*.test.ts", "**/*.test.tsx"]'
    pkg = directory / "package.json"
    if pkg.is_file():
        try:
            deps = json.loads(pkg.read_text())
        except (json.JSONDecodeError, OSError):
            return None
        combined = {**deps.get("dependencies", {}), **deps.get("devDependencies", {})}
        if "vitest" in combined:
            return "vitest", '["**/__tests__/**", "**/*.test.ts", "**/*.test.tsx"]'
    return None


def _project_key(name: str) -> str:
    """A bare TOML key: letters, digits, underscore, hyphen."""
    cleaned = "".join(c if c.isalnum() or c in "_-" else "-" for c in name)
    return cleaned or "app"


def cmd_init(args) -> Envelope:
    worktree = _worktree()
    path = worktree / config_mod.CONFIG_NAME
    if path.exists() and not args.force:
        return failure(f"{path} already exists; pass --force to overwrite")

    detected: list[tuple[str, str, str, str]] = []  # (name, root, adapter, test_paths)
    unmatched: list[str] = []

    # A single-project repo is the common case: the worktree root is the project.
    root_hit = _detect_adapter(worktree)
    if root_hit is not None:
        detected.append((_project_key(worktree.name), ".", *root_hit))

    for child in sorted(p for p in worktree.iterdir() if p.is_dir()):
        if child.name.startswith(".") or child.name == "node_modules":
            continue
        hit = _detect_adapter(child)
        if hit is not None:
            detected.append((child.name, child.name, *hit))
        elif (child / "package.json").is_file():
            unmatched.append(child.name)

    lines = [
        "# Generated by `tdd init` — review before use (roots are declared, never inferred).",
        "",
    ]
    for name, root, adapter, tests in detected:
        lines += [
            f"[project.{name}]",
            f'root       = "{root}"',
            f'adapter    = "{adapter}"',
            f"test_paths = {tests}",
            "lint       = []",
            "typecheck  = []",
            "",
        ]
    path.write_text("\n".join(lines))
    return Envelope(
        result={
            "written": str(path),
            "detected": [d[0] for d in detected],
            "unmatched": unmatched or None,
        },
        next_action=NextAction(
            Verb.CONFIRM_CYCLE_APPLICABLE,
            "Review tdd.toml: confirm roots, add lint/typecheck commands and artifact edges."
            + (
                f" No supported adapter detected for: {', '.join(unmatched)} —"
                " declare one manually (third-party adapters register under the"
                " `tddcli.adapters` entry-point group)."
                if unmatched
                else ""
            ),
        ),
    )


LEGACY_ARTIFACTS = (".pytest_report.json", ".tdd-state.json")
SKIP_DIRS = {"node_modules", ".venv", "venv", "__pycache__", ".git"}


def _legacy_artifacts(worktree: Path) -> list[Path]:
    """Find stale artifacts in *this* worktree only.

    Nested worktrees under `.claude/worktrees/` are separate checkouts with their own
    in-flight work; scanning into them reports another branch's live files as this
    worktree's problem.
    """
    found: list[Path] = []

    def walk(directory: Path, depth: int = 0) -> None:
        if depth > 8:
            return
        try:
            entries = list(directory.iterdir())
        except OSError:
            return
        for entry in entries:
            if entry.is_dir():
                if entry.name in SKIP_DIRS:
                    continue
                # A nested checkout owns its own state.
                if (entry / ".git").exists():
                    continue
                walk(entry, depth + 1)
            elif entry.name in LEGACY_ARTIFACTS:
                found.append(entry)

    walk(worktree)
    return sorted(found)


def _doctor_checklist() -> tuple[list[dict], Callable]:
    """A checks list and its recorder, which refuses a blocker it cannot explain.

    `resolve_blocker` with an empty `detail` is unfalsifiable: an agent is told to
    fix something and given nothing to fix. It re-runs doctor, reads the identical
    output, and loops. Enforcing the detail here means a check added later inherits
    the guarantee instead of relying on its author to remember.
    """
    checks: list[dict] = []

    def check(name, ok, detail="", project=None):
        if not ok and not str(detail).strip():
            raise AssertionError(
                f"doctor check {name!r} would fail silently: a failing check must name what to fix"
            )
        entry = {"check": name, "ok": bool(ok), "detail": detail}
        if project is not None:
            entry["project"] = project
        checks.append(entry)

    return checks, check


def _blocks_the_loop(rel_path: str, cfg) -> bool:
    """Whether dirt at `rel_path` is somewhere a run would actually read it."""
    if rel_path == config_mod.CONFIG_NAME:
        return True
    if cfg.owning_project(rel_path) is not None:
        return True
    return any(art.owns(rel_path) for art in cfg.artifacts.values())


def _cleanliness_detail(blocking: list[str], unrelated: list[str]) -> str:
    def listed(paths: list[str]) -> str:
        head = ", ".join(paths[:5])
        return head if len(paths) <= 5 else f"{head} (+{len(paths) - 5} more)"

    if blocking:
        return (
            f"uncommitted changes a run would observe: {listed(blocking)}."
            " Commit, stash, or gitignore them before `tdd run start`."
        )
    if unrelated:
        return (
            f"clean where a run reads; {len(unrelated)} unrelated path(s) left as-is:"
            f" {listed(unrelated)}"
        )
    return ""


def cmd_doctor(args) -> Envelope:
    worktree = _worktree()
    checks, check = _doctor_checklist()

    check("worktree resolvable", True, str(worktree))
    try:
        cfg = config_mod.load(worktree)
        check("tdd.toml valid", True, f"{len(cfg.projects)} projects")
    except config_mod.ConfigError as exc:
        check("tdd.toml valid", False, str(exc))
        return Envelope(ok=False, error="configuration invalid", result={"checks": checks})

    repo = gitutil.repo_identity(worktree)
    ledger = Ledger(repo)
    check("ledger reachable", True, str(ledger.path))
    check(
        "ledger outside worktree", not str(ledger.path).startswith(str(worktree)), str(ledger.path)
    )

    projects: dict[str, dict] = {}
    for name, project in cfg.projects.items():
        before = len(checks)
        root = worktree / project.root
        check("root exists", root.is_dir(), str(root), project=name)
        check(
            "adapter known", project.adapter in adapters.available(), project.adapter, project=name
        )
        declared = bool(project.test_paths)
        check(
            "test_paths declared",
            declared,
            ""
            if declared
            else f"add `test_paths` to [project.{name}] in tdd.toml — without it no"
            " suite can be discovered for this project",
            project=name,
        )
        if project.adapter == "pytest":
            # The probe runs in the project's own environment (uv, poetry, pipenv,
            # pdm or the active venv) — hardcoding `uv run` here failed the check
            # on any non-uv project even with the plugin installed.
            probe = adapters.build(project, worktree).plugin_probe_cmd()
            code, out, err = adapters.base.run_command(probe, root, label="doctor")
            check("pytest-json-report installed", code == 0, (err or "")[:200], project=name)

        # Run before `collectable()` so this actionable message wins over
        # vitest's stack trace: a git worktree does not inherit `node_modules`
        # (it isn't tracked), and `npx vitest` fails with a wall of noise that
        # doesn't say why.
        if project.adapter == "vitest" and not (root / "node_modules").is_dir():
            check(
                "node_modules present",
                False,
                "git worktrees do not inherit `node_modules` (it isn't tracked)."
                " Symlink it from the main checkout, e.g."
                f" `ln -s <main-checkout>/{project.root}/node_modules {root}/node_modules`.",
                project=name,
            )

        # The Gradle wrapper is not on PATH; a project that invokes `./gradlew`
        # needs the committed wrapper present at the project root, or the run
        # fails with a bare `No such file or directory` that never says why.
        # Only checked when the command actually uses the wrapper — a project on
        # a system `gradle` is not held to it.
        if project.adapter == "gradle":
            gradle_cmd = adapters.build(project, worktree)._test_cmd()
            if "gradlew" in gradle_cmd:
                wrapper = root / "gradlew"
                check(
                    "gradle wrapper present",
                    wrapper.is_file(),
                    ""
                    if wrapper.is_file()
                    else "no ./gradlew at the project root — run `gradle wrapper` to"
                    " generate it, or point test_command at a gradle on PATH",
                    project=name,
                )

        # Whole-suite `--collect-only`/`vitest list` (§10) — a single, cheap
        # probe (0.04s on a broken project) that attributes a collection failure
        # to its project. Nothing shells out to doctor today, so this is the only
        # place a `ModuleNotFoundError` like the real `pyyaml` incident surfaces.
        adapter = adapters.build(project, worktree)
        gate = adapter.collectable()
        check("collectable", gate.ok, gate.output, project=name)

        # R7.13's premise — "files the default runner config cannot reach" — is
        # a config property nothing else enforces. Probe it at preflight so the
        # overlap is named here, not discovered as an opaque mid-cycle failure.
        if project.overrides:
            gate = adapter.override_isolation()
            check(
                "default suite cannot reach override files",
                gate.ok,
                gate.output,
                project=name,
            )

        if project.timeout is not None:
            max_ms = ledger.max_suite_duration_ms(name)
            if max_ms is not None and project.timeout * 1000 < max_ms:
                check(
                    "timeout exceeds known baseline",
                    False,
                    f"timeout = {project.timeout} s but the longest recorded full-suite"
                    f" run for this project took {max_ms / 1000:.1f} s — raise timeout"
                    f" or the suite will be killed before it finishes",
                    project=name,
                )
            else:
                check("timeout exceeds known baseline", True, project=name)

        projects[name] = {"ok": all(c["ok"] for c in checks[before:])}

    for art in cfg.artifacts.values():
        # One evaluation feeds both `ok` and the detail: evaluating the condition
        # twice lets them disagree, and a passing check that still says "add a hook"
        # is the same misdirection as a failing check that says nothing.
        has_hook = bool(art.check or art.regenerate)
        check(
            f"artifact {art.name}: has check or regenerate",
            has_hook,
            ""
            if has_hook
            else f"add `check` or `regenerate` to [artifact.{art.name}] in tdd.toml —"
            " freshness cannot be verified without one",
        )

    stale = _legacy_artifacts(worktree)
    check(
        "no legacy state artifacts",
        not stale,
        f"delete these pre-ledger state files: {', '.join(str(s) for s in stale[:5])}"
        if stale
        else "",
    )

    # Only dirt a run would read can corrupt one. Blocking on everything else
    # stopped agents on unrelated notes and editor settings, and — because the
    # check named no path — gave them nothing to act on but a re-run. `is_ignored`
    # also excludes doctor's own probe residue (`.venv`, `node_modules`, caches),
    # so running doctor can no longer be what makes doctor fail.
    dirt = sorted(p for p in gitutil.dirty_paths(worktree) if not cfg.is_ignored(p))
    blocking = [p for p in dirt if _blocks_the_loop(p, cfg)]
    unrelated = [p for p in dirt if p not in set(blocking)]
    check("worktree clean", not blocking, _cleanliness_detail(blocking, unrelated))

    ok = all(c["ok"] for c in checks)
    return Envelope(
        ok=ok,
        result={"checks": checks, "projects": projects, "healthy": ok},
        next_action=NextAction(
            Verb.CONFIRM_CYCLE_APPLICABLE if ok else Verb.RESOLVE_BLOCKER,
            "Environment is ready." if ok else "Resolve the failing checks above.",
        ),
    )


def cmd_plan_register(args) -> Envelope:
    worktree = _worktree()
    cfg = config_mod.load(worktree)
    ledger = Ledger(gitutil.repo_identity(worktree))
    rel = str(Path(args.plan))
    try:
        parsed = contract_mod.register(worktree, rel, cfg)
    except contract_mod.ContractError as exc:
        # R7.10 — malformed front-matter is a planning defect and must surface.
        return failure(f"malformed plan contract: {exc}", plan=rel)

    if parsed.status == "undeclared" and not args.allow_undeclared:
        return failure(
            f"{rel} has no front-matter contract. Add one, or pass --allow-undeclared"
            " (fidelity metrics will be unavailable).",
            plan=rel,
        )

    existing = ledger.one(
        "SELECT * FROM plan_contract WHERE plan_path = ? AND git_blob_sha IS ?",
        (rel, parsed.blob_sha),
    )
    contract_id = (
        existing["id"]
        if existing
        else ledger.insert(
            "plan_contract",
            plan_path=rel,
            git_blob_sha=parsed.blob_sha,
            git_commit=parsed.commit_sha,
            status=parsed.status,
            declared_cycles=contract_mod.cycles_to_json(parsed.cycles),
            annotation_keys=json.dumps(parsed.annotation_keys),
            registered_at=now(),
        )
    )
    return Envelope(
        result={
            "contract_id": contract_id,
            "status": parsed.status,
            "blob": parsed.blob_sha,
            "cycles": len(parsed.cycles),
            "kinds": {
                k: sum(1 for c in parsed.cycles if c.kind == k)
                for k in {c.kind for c in parsed.cycles}
            },
            "reused": bool(existing),
        },
        next_action=NextAction(
            Verb.CONFIRM_CYCLE_APPLICABLE, f"Contract registered. `tdd run start --plan {rel}`."
        ),
    )


def _probe_projects(cfg, worktree, ledger, on_progress):
    """Probe every project's baseline (R9.5a): run + collect, timing each, emitting a
    `baseline_captured` heartbeat, and calling `on_progress(done, name)` — extracted
    from `cmd_run_start`, which carried claiming, timing, heartbeating and progress
    updates inline past the point of legibility. Returns `{name: (verdict, collection)}`.
    """
    probes = {}
    for done, (name, project) in enumerate(cfg.projects.items(), start=1):
        adapter = adapters.build(project, worktree)
        started = time.monotonic()
        verdict = adapter.run(None)
        ran = time.monotonic()
        collection = adapter.collect()
        elapsed = time.monotonic() - started
        probes[name] = (verdict, collection)
        # Split, not just totalled: `run` and `collect` have unrelated cost models
        # — one scales with tests, the other with files — and a single number sends
        # whoever asks "why was that slow?" out of the tool to measure by hand.
        heartbeat(
            event="baseline_captured",
            project=name,
            test_count=len(collection.tests),
            elapsed_s=round(elapsed, 2),
            run_s=round(ran - started, 2),
            collect_s=round(elapsed - (ran - started), 2),
        )
        on_progress(done, name)
    return probes


def cmd_run_start(args) -> Envelope:
    worktree = _worktree()
    cfg = config_mod.load(worktree)
    ledger = Ledger(gitutil.repo_identity(worktree))

    active = ledger.active_run(str(worktree))
    if active is not None:
        return failure(
            "a run is already active in this worktree",
            reason="run_already_active",
            run_id=active["id"],
            started_at=active["started_at"],
        )

    rel = str(Path(args.plan))
    contract_row = ledger.one(
        "SELECT * FROM plan_contract WHERE plan_path = ? ORDER BY id DESC LIMIT 1", (rel,)
    )
    if contract_row is None:
        return failure(f"{rel} is not registered; run `tdd plan register {rel}` first")

    # R7.11 — the plan blob is the contract; drift must surface.
    blob_changed = False
    try:
        current_blob, _ = gitutil.blob_sha_at_head(worktree, rel)
        blob_changed = bool(
            contract_row["git_blob_sha"] and current_blob != contract_row["git_blob_sha"]
        )
    except gitutil.GitError:
        pass

    dirty = sorted(gitutil.dirty_paths(worktree))
    if dirty and not args.allow_dirty:
        return failure(
            "working tree is dirty; commit first or pass --allow-dirty"
            " (pre-existing changes are then excluded from authorship forever)",
            dirty=dirty,
        )

    if contract_row["status"] == "undeclared" and not args.allow_undeclared:
        return failure("contract is undeclared; pass --allow-undeclared")

    # Claim the worktree before probing: two `run start` calls against
    # one worktree must not both pass the baseline window. `Ledger.claim`'s `UNIQUE`
    # insert is the lock — do not read-then-write, which is the race this
    # closes. A claim whose owner is gone (e.g. a `SIGKILL`ed `run start`)
    # is reclaimed rather than obeyed, or one dead process bricks the worktree
    # forever; `active_claim` only computes staleness, it never deletes.
    existing = ledger.active_claim(str(worktree))
    if existing is not None and existing["stale"]:
        ledger.release_claim(str(worktree))

    try:
        ledger.claim(
            str(worktree),
            hostname=socket.gethostname(),
            pid=os.getpid(),
            projects_total=len(cfg.projects),
        )
    except sqlite3.IntegrityError:
        return failure(
            "a baseline is already being collected in this worktree; do not re-run"
            " `run start` — poll `tdd progress` instead, which reports"
            " `collecting_baseline` with per-project counters until it finishes",
            reason="baseline_in_progress",
        )

    try:
        # Probe every project before the run exists (R9.5a). A baseline is subtracted
        # from every later failure set, so an untrustworthy one is worse than none: it
        # reports pre-existing failures as regressions for the life of the run.
        # Refusing here also leaves no half-started run behind to block the next
        # attempt — and must release the claim too, or the retry it invites is itself
        # refused.
        probes = _probe_projects(
            cfg,
            worktree,
            ledger,
            on_progress=lambda done, name: ledger.update_claim(
                str(worktree),
                projects_done=done,
                current_project=name,
            ),
        )
        for name, (verdict, collection) in probes.items():
            if not collection.tests and collection.failed_files:
                sample = sorted(collection.failed_files)[0]
                return failure(
                    f"{name}: no test could be collected — {len(collection.failed_files)}"
                    f" file(s) failed to collect, starting with {sample}. The baseline"
                    " would record no failures and every pre-existing failure would then"
                    " read as a regression. Fix the environment (dependencies"
                    " installed?) and retry.",
                    project=name,
                    failed_files=sorted(collection.failed_files),
                )
            if collection.tests and not verdict.passed and not verdict.failed:
                return failure(
                    f"{name}: the suite collected {len(collection.tests)} test(s) but"
                    " the baseline run executed no tests, so it observed nothing. Check"
                    " `test_command` in tdd.toml and retry.",
                    project=name,
                    collected=len(collection.tests),
                )

        executor = identity.resolve(worktree, args.executor)
        run_id = ledger.insert(
            "run",
            plan_contract_id=contract_row["id"],
            executor_model=executor.model,
            executor_session=executor.session,
            executor_source=executor.source,
            worktree_path=str(worktree),
            started_at=now(),
            allow_dirty=int(bool(args.allow_dirty)),
            preexisting_dirty=json.dumps(dirty),
            config_sha=config_mod.config_sha(worktree),
        )
        run = ledger.one("SELECT * FROM run WHERE id = ?", (run_id,))
        if blob_changed:
            ledger.event(run_id, None, "plan_blob_changed", rel)

        # Baselines and the collection snapshot, per project (R9.5, R8.9) — from the
        # probe above, so the suite is not run twice.
        for name, (verdict, collection) in probes.items():
            ledger.insert(
                "baseline",
                run_id=run_id,
                project=name,
                failing=json.dumps(sorted(verdict.failed)),
                captured_at=now(),
            )
            ledger.insert(
                "collection_snapshot",
                run_id=run_id,
                project=name,
                tests=json.dumps(sorted(collection.tests)),
                failed_files=json.dumps(collection.failed_files),
                captured_at=now(),
            )

        engine = Engine(ledger, cfg, worktree, run)
        engine.check_artifacts(None)
        first = engine.declared[0] if engine.declared else None
        if first is None:
            return failure("contract declares no cycles")
        cycle = engine.open_cycle(first.ordinal)

        verb, opening = engine.opening_action(cycle)
        detail = f"Run {run_id} started ({executor.model}, via {executor.source}). {opening}"
        return Envelope(
            run=engine.run_state(cycle),
            result={
                "baselines": {n: len(v) for n, v in ledger.baselines(run_id).items()},
                "executor_source": executor.source,
            },
            next_action=NextAction(verb, detail),
        )
    finally:
        ledger.release_claim(str(worktree))


def cmd_status(args) -> Envelope:
    worktree, cfg, ledger, run = _context(require_run=False)
    if run is None:
        claim = ledger.active_claim(str(worktree))
        if claim is not None:
            return _collecting_envelope(claim)
        return Envelope(
            result={"active": False},
            next_action=NextAction(
                Verb.CONFIRM_CYCLE_APPLICABLE, "No active run. `tdd run start --plan <path>`."
            ),
        )
    engine = _engine(worktree, cfg, ledger, run)
    cycle = ledger.open_cycle(run["id"])
    if cycle is None:
        return Envelope(
            run={"id": run["id"], "phase": CLOSED},
            next_action=NextAction(Verb.COMPLETE, "Run complete."),
        )
    attempts = len(ledger.invocations(cycle["id"], cycle["phase"]))
    return Envelope(
        run=engine.run_state(cycle),
        result={
            "attempts_in_phase": attempts,
            "targets": json.loads(cycle["target_tests"]),
            "sensitivity_open": ledger.open_sensitivity(cycle["id"]) is not None,
        },
        next_action=NextAction(
            Verb.REFACTOR_OR_ADVANCE, "Run `tdd advance` to evaluate the current phase."
        ),
    )


def cmd_advance(args) -> Envelope:
    worktree, cfg, ledger, run = _context()
    engine = _engine(worktree, cfg, ledger, run)
    cycle = ledger.open_cycle(run["id"])
    if cycle is None:
        return Envelope(
            run={"id": run["id"], "phase": CLOSED},
            next_action=NextAction(Verb.COMPLETE, "All cycles complete."),
        )
    return do_advance(engine, cycle, retry=args.retry)


def cmd_cycle_skip(args) -> Envelope:
    worktree, cfg, ledger, run = _context()
    engine = _engine(worktree, cfg, ledger, run)
    cycle = ledger.open_cycle(run["id"])
    if cycle is None:
        return failure("no open cycle")
    ledger.update("cycle", cycle["id"], phase=SKIPPED, closed_at=now(), skip_reason=args.reason)
    ledger.insert(
        "transition",
        cycle_id=cycle["id"],
        from_phase=cycle["phase"],
        to_phase=SKIPPED,
        at=now(),
    )
    nxt_declared = next((c for c in engine.declared if c.ordinal > cycle["ordinal"]), None)
    if nxt_declared is None:
        ledger.update("run", run["id"], ended_at=now(), outcome="complete")
        return Envelope(
            run={"id": run["id"], "cycle": cycle["ordinal"], "phase": SKIPPED},
            next_action=NextAction(Verb.COMPLETE, "Final cycle skipped; run complete."),
        )
    nxt = engine.open_cycle(nxt_declared.ordinal)
    verb, opening = engine.opening_action(nxt)
    return Envelope(
        run=engine.run_state(nxt),
        result={"skipped": cycle["ordinal"], "reason": args.reason},
        next_action=NextAction(verb, f"Cycle {cycle['ordinal']} skipped. {opening}"),
    )


def cmd_annotate(args) -> Envelope:
    worktree, cfg, ledger, run = _context()
    cycle = ledger.open_cycle(run["id"])
    ledger.insert(
        "annotation",
        run_id=run["id"],
        cycle_id=cycle["id"] if cycle else None,
        key=args.key,
        value=args.value,
        at=now(),
    )
    return Envelope(
        run={"id": run["id"], "cycle": cycle["ordinal"] if cycle else None},
        result={"key": args.key},
        next_action=NextAction(Verb.REFACTOR_OR_ADVANCE, "Annotation recorded. `tdd advance`."),
    )


def cmd_blocker(args) -> Envelope:
    worktree, cfg, ledger, run = _context()
    if args.kind not in BLOCKER_KINDS:
        return failure(f"unknown blocker kind {args.kind!r}; use one of {sorted(BLOCKER_KINDS)}")
    cycle = ledger.open_cycle(run["id"])
    ledger.insert(
        "blocker",
        run_id=run["id"],
        cycle_id=cycle["id"] if cycle else None,
        kind=args.kind,
        detail=args.detail,
        at=now(),
    )
    # R8.7 — a blocked run is not live, so the stop hook must release.
    ledger.update("run", run["id"], ended_at=now(), outcome="blocked")
    return Envelope(
        run={"id": run["id"], "cycle": cycle["ordinal"] if cycle else None, "phase": "BLOCKED"},
        result={"kind": args.kind, "detail": args.detail},
        next_action=NextAction(
            Verb.BLOCKED,
            f"Run blocked ({args.kind}). A human can resume with"
            " `tdd resume --unblock --note ...`.",
        ),
    )


def _accept_failures_into_baseline(ledger: Ledger, run_id: int) -> dict[str, list[str]]:
    """Fold the failures the last close sweep saw into the baseline (R9.5b).

    A run whose baseline missed a failure cannot otherwise recover: unblocking returns
    it to the phase it blocked in, and the next sweep finds the same failure. Only a
    human reaches this, only by asking, and what was accepted is recorded.
    """
    latest = ledger.all(
        "SELECT project, other_failures FROM invocation WHERE id IN ("
        "  SELECT MAX(id) FROM invocation WHERE run_id = ? AND phase_at = 'CLOSE_SWEEP'"
        "  GROUP BY project)",
        (run_id,),
    )
    rows = {
        r["project"]: r for r in ledger.all("SELECT * FROM baseline WHERE run_id = ?", (run_id,))
    }
    accepted: dict[str, list[str]] = {}
    for sweep in latest:
        row = rows.get(sweep["project"])
        if row is None:
            continue
        known = set(json.loads(row["failing"]))
        new = sorted(set(json.loads(sweep["other_failures"])) - known)
        if not new:
            continue
        ledger.update("baseline", row["id"], failing=json.dumps(sorted(known | set(new))))
        accepted[sweep["project"]] = new
    if accepted:
        ledger.event(run_id, None, "baseline_amended", json.dumps(accepted))
    return accepted


def cmd_resume(args) -> Envelope:
    worktree = _worktree()
    cfg = config_mod.load(worktree)
    ledger = Ledger(gitutil.repo_identity(worktree))
    run = ledger.active_run(str(worktree))
    accepted: dict[str, list[str]] = {}

    if args.accept_failures and not args.unblock:
        return failure("--accept-failures applies to --unblock")

    if args.unblock:
        if run is not None:
            return failure("run is already live; --unblock applies to a blocked run")
        blocked = ledger.one(
            "SELECT * FROM run WHERE worktree_path = ? AND outcome = 'blocked'"
            " ORDER BY id DESC LIMIT 1",
            (str(worktree),),
        )
        if blocked is None:
            return failure("no blocked run to unblock in this worktree")
        if not args.note:
            return failure("--unblock requires --note describing the intervention")
        ledger.update("run", blocked["id"], ended_at=None, outcome=None)
        ledger.insert("human_intervention", run_id=blocked["id"], note=args.note, at=now())
        if args.accept_failures:
            accepted = _accept_failures_into_baseline(ledger, blocked["id"])
        run = ledger.one("SELECT * FROM run WHERE id = ?", (blocked["id"],))

    if run is None:
        return failure("no active run in this worktree")

    engine = _engine(worktree, cfg, ledger, run)
    cycle = ledger.open_cycle(run["id"])
    if cycle is None:
        return Envelope(
            run={"id": run["id"], "phase": CLOSED},
            next_action=NextAction(Verb.COMPLETE, "Run complete."),
        )
    result = {"resumed": True}
    if accepted:
        result["accepted_into_baseline"] = accepted
    return Envelope(
        run=engine.run_state(cycle),
        result=result,
        next_action=NextAction(
            Verb.REFACTOR_OR_ADVANCE,
            f"Resumed at cycle {cycle['ordinal']}, phase {cycle['phase']}. Run `tdd advance`.",
        ),
    )


def cmd_sensitivity(args) -> Envelope:
    worktree, cfg, ledger, run = _context()
    cycle = ledger.open_cycle(run["id"])
    if cycle is None:
        return failure("no open cycle")

    if args.step == "begin":
        if ledger.open_sensitivity(cycle["id"]) is not None:
            return failure("a sensitivity check is already open")
        check_id = ledger.insert(
            "sensitivity_check",
            cycle_id=cycle["id"],
            reference_diff=snapshot.capture(worktree, cfg),
            reference_untracked=snapshot.fingerprint(worktree, cfg),
            opened_at=now(),
        )
        return Envelope(
            run={"id": run["id"], "cycle": cycle["ordinal"]},
            result={"check_id": check_id},
            next_action=NextAction(
                Verb.RUN_SENSITIVITY_CHECK,
                "Reference state recorded. Mutate the behaviour under test, then"
                " `tdd sensitivity check`.",
            ),
        )

    open_check = ledger.open_sensitivity(cycle["id"])
    if open_check is None:
        return failure("no open sensitivity check; run `tdd sensitivity begin` first")
    engine = _engine(worktree, cfg, ledger, run)
    targets = json.loads(cycle["target_tests"])
    projects = json.loads(cycle["projects"])

    if args.step == "check":
        outcomes, _, _, failure_text = engine.run_projects(
            projects, targets, cycle, "SENSITIVITY", False
        )
        # A mutation that breaks collection also proves the test depends on the code.
        bites = bool(outcomes) and all(o in (FAILED, NOT_COLLECTED) for o in outcomes.values())
        ledger.update(
            "sensitivity_check",
            open_check["id"],
            mutation_diff=gitutil.diff_text(worktree)[:20000],
            observed_failure=failure_text[:4000],
        )
        if not bites:
            return Envelope(
                ok=False,
                error="the mutation did not make the target fail — the test pins nothing",
                run={"id": run["id"], "cycle": cycle["ordinal"]},
                result={"outcomes": outcomes},
                next_action=NextAction(
                    Verb.RUN_SENSITIVITY_CHECK,
                    "Strengthen the mutation or the assertion, then check again.",
                ),
            )
        return Envelope(
            run={"id": run["id"], "cycle": cycle["ordinal"]},
            result={"outcomes": outcomes, "observed_failure": failure_text[:800]},
            next_action=NextAction(
                Verb.RUN_SENSITIVITY_CHECK,
                "The test fails under mutation. Restore with `tdd sensitivity end`.",
            ),
        )

    # end — restore and verify byte-identical (R8.5)
    to_restore = snapshot.restore(worktree, cfg, open_check["reference_diff"])
    restored_ok = snapshot.fingerprint(worktree, cfg) == open_check["reference_untracked"]
    ledger.update(
        "sensitivity_check",
        open_check["id"],
        restored_ok=int(restored_ok),
        closed_at=now(),
    )
    if not restored_ok:
        ledger.event(run["id"], cycle["id"], "restore_mismatch", json.dumps(to_restore))
        return Envelope(
            ok=False,
            error="restore is not byte-identical to the reference state",
            run={"id": run["id"], "cycle": cycle["ordinal"]},
            result={"restored": to_restore},
            next_action=NextAction(
                Verb.RESOLVE_BLOCKER,
                "The working tree does not match the pre-mutation state. Restore it by"
                " hand before continuing.",
            ),
        )
    return Envelope(
        run={"id": run["id"], "cycle": cycle["ordinal"]},
        result={"restored": to_restore, "restored_ok": True},
        next_action=NextAction(Verb.REFACTOR_OR_ADVANCE, "Restored and verified. `tdd advance`."),
    )


def cmd_target(args) -> Envelope:
    worktree, cfg, ledger, run = _context()
    cycle = ledger.open_cycle(run["id"])
    if cycle is None:
        return failure("no open cycle")

    # The target must be grounded in observed collection, the same way phase is
    # grounded in observed execution (#15): recording free text deferred a typo —
    # or a speculative `tdd target env` — to the next suite run, where it
    # surfaced as `not_found` against a test that never existed.
    known: set[str] = set()
    for name in json.loads(cycle["projects"]):
        adapter = adapters.build(cfg.project(name), worktree)
        known |= adapter.collect().tests
    if args.test not in known:
        close = difflib.get_close_matches(args.test, sorted(known), n=3, cutoff=0.6)
        hint = f" Closest collected ids: {', '.join(close)}." if close else ""
        return failure(
            f"{args.test} is not a collected test in this cycle's projects;"
            f" the target was not changed.{hint}"
        )

    ledger.update("cycle", cycle["id"], target_tests=json.dumps([args.test]))
    ledger.event(run["id"], cycle["id"], "target_named_by_agent", args.test)
    return Envelope(
        run={"id": run["id"], "cycle": cycle["ordinal"]},
        result={"target": args.test},
        next_action=NextAction(Verb.REFACTOR_OR_ADVANCE, "Target set. `tdd advance`."),
    )


def cmd_log_render(args) -> Envelope:
    worktree, cfg, ledger, run = _context(require_run=False)
    if run is None:
        run = ledger.one(
            "SELECT * FROM run WHERE worktree_path = ? ORDER BY id DESC LIMIT 1",
            (str(worktree),),
        )
    if run is None:
        return failure("no runs recorded for this worktree")
    text = render.friction_log(ledger, run)
    if args.out:
        # R9.15 — a relative --out is worktree-relative, never cwd-relative: the
        # command is run from wherever the agent happens to be standing, and
        # `tasks/friction-logs/` means the one at the root of the repo.
        out = Path(args.out)
        if not out.is_absolute():
            out = worktree / out
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text)
        written = str(out.relative_to(worktree)) if not Path(args.out).is_absolute() else str(out)
        return Envelope(
            result={"written": written, "path": str(out)},
            next_action=NextAction(Verb.COMPLETE, f"Friction log written to {out}."),
        )
    sys.stdout.write(text)
    return Envelope(
        result={"rendered": True},
        next_action=NextAction(Verb.COMPLETE, "Rendered."),
        silent=True,
    )


def cmd_progress(args) -> Envelope:
    """Human-readable progress. `status` remains the agent's machine view."""
    worktree, cfg, ledger, run = _context(require_run=False)
    if run is None:
        run = ledger.one(
            "SELECT * FROM run WHERE worktree_path = ? ORDER BY id DESC LIMIT 1",
            (str(worktree),),
        )
    if run is None:
        # A baseline can take minutes; a claim with no run row yet is in-flight, not
        # "never started". `ok: true` — a polling agent must not see
        # repeated exit-1, the signal that caused the re-runs in the first place.
        # Leaving the human form saying "no runs recorded" while JSON says
        # "collecting" would be the same ambiguity in a new place.
        claim = ledger.active_claim(str(worktree))
        if claim is not None:
            envelope = _collecting_envelope(claim)
            if args.json:
                return envelope
            result = envelope.result
            current = (
                f" (current: {result['current_project']})" if result["current_project"] else ""
            )
            sys.stdout.write(
                f"collecting baseline: {result['projects_done']}/{result['projects_total']}"
                f" projects{current} — {result['elapsed_s']}s elapsed\n"
            )
            envelope.silent = True
            return envelope
        return failure("no runs recorded for this worktree")
    if args.json:
        engine = _engine(worktree, cfg, ledger, run)
        cycle = ledger.open_cycle(run["id"])
        return Envelope(
            run=engine.run_state(cycle) if cycle else {"id": run["id"], "phase": CLOSED},
            result=render.metrics(ledger, str(worktree)),
            next_action=NextAction(Verb.COMPLETE, "Progress reported."),
        )
    sys.stdout.write(render.progress(ledger, run))
    return Envelope(
        result={"rendered": True},
        next_action=NextAction(Verb.COMPLETE, "Progress rendered."),
        silent=True,
    )


def cmd_fleet(args) -> Envelope:
    """Every worktree's active run against this repository, plus in-flight
    baselines and currently executing suites. Deliberately does not use
    `_context`: no tdd.toml, active run, or existing ledger is required, and the
    ledger is opened read-only so live agents cannot be perturbed."""
    worktree = _worktree()
    summary = fleet.summarise(ledger_path(gitutil.repo_identity(worktree)))
    if args.json:
        return Envelope(result=summary, next_action=NextAction(Verb.COMPLETE, "Fleet reported."))
    sys.stdout.write(fleet.render(summary))
    return Envelope(
        result=summary,
        next_action=NextAction(Verb.COMPLETE, "Fleet rendered."),
        silent=True,
    )


def cmd_metrics(args) -> Envelope:
    worktree, cfg, ledger, run = _context(require_run=False)
    return Envelope(
        result=render.metrics(ledger, str(worktree)),
        next_action=NextAction(Verb.COMPLETE, "Metrics computed."),
    )


# -- parser --------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="tdd", description=__doc__)
    p.add_argument("--version", action="version", version=f"tdd-cli {__version__}")
    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("init", help="scaffold tdd.toml for review")
    s.add_argument("--force", action="store_true")
    s.set_defaults(fn=cmd_init)

    s = sub.add_parser("doctor", help="environment preflight")
    s.set_defaults(fn=cmd_doctor)

    plan = sub.add_parser("plan", help="plan contracts").add_subparsers(
        dest="plan_command", required=True
    )
    s = plan.add_parser("register")
    s.add_argument("plan")
    s.add_argument("--allow-undeclared", action="store_true")
    s.set_defaults(fn=cmd_plan_register)

    run_p = sub.add_parser("run", help="runs").add_subparsers(dest="run_command", required=True)
    s = run_p.add_parser("start")
    s.add_argument("--plan", required=True)
    s.add_argument("--executor", help="human-supplied label; agents must not use this")
    s.add_argument("--allow-dirty", action="store_true")
    s.add_argument("--allow-undeclared", action="store_true")
    s.set_defaults(fn=cmd_run_start)

    s = sub.add_parser("status")
    s.set_defaults(fn=cmd_status)

    s = sub.add_parser("advance", help="the only command that changes phase")
    s.add_argument("--retry", action="store_true", help="re-run an unchanged tree")
    s.set_defaults(fn=cmd_advance)

    cyc = sub.add_parser("cycle").add_subparsers(dest="cycle_command", required=True)
    s = cyc.add_parser("skip")
    s.add_argument("--reason", required=True)
    s.set_defaults(fn=cmd_cycle_skip)

    s = sub.add_parser("annotate")
    s.add_argument("--key", required=True)
    s.add_argument("--value", required=True)
    s.set_defaults(fn=cmd_annotate)

    s = sub.add_parser("blocker")
    s.add_argument("--kind", required=True)
    s.add_argument("--detail", required=True)
    s.set_defaults(fn=cmd_blocker)

    s = sub.add_parser("resume")
    s.add_argument("--unblock", action="store_true")
    s.add_argument("--note")
    s.add_argument(
        "--accept-failures",
        action="store_true",
        help="fold the failures the last close sweep saw into the baseline, so a run"
        " whose baseline missed them can proceed; recorded as baseline_amended",
    )
    s.set_defaults(fn=cmd_resume)

    s = sub.add_parser("sensitivity")
    s.add_argument("step", choices=["begin", "check", "end"])
    s.set_defaults(fn=cmd_sensitivity)

    s = sub.add_parser("target", help="name the target test when several new tests appeared")
    s.add_argument("test")
    s.set_defaults(fn=cmd_target)

    log = sub.add_parser("log").add_subparsers(dest="log_command", required=True)
    s = log.add_parser("render")
    s.add_argument(
        "--out",
        help="write here instead of stdout; a relative path is resolved from the"
        " worktree root, not the current directory",
    )
    s.set_defaults(fn=cmd_log_render)

    s = sub.add_parser("progress", help="human-readable plan progress")
    s.add_argument("--json", action="store_true", help="machine output instead")
    s.set_defaults(fn=cmd_progress)

    s = sub.add_parser("fleet", help="all active runs on this repository, across every worktree")
    s.add_argument("--json", action="store_true", help="machine output instead")
    s.set_defaults(fn=cmd_fleet)

    s = sub.add_parser("metrics")
    s.set_defaults(fn=cmd_metrics)
    return p


def main(argv: list[str] | None = None) -> int:
    if os.name == "nt":
        # Worker leases, process-liveness checks, and cache paths are POSIX-only.
        # Failing here, loudly, beats corrupting a lease directory ten minutes in.
        return failure(
            "tdd-cli does not support Windows: worker leases and process-liveness"
            " checks are POSIX-only. Run it under WSL instead.",
            reason="unsupported_platform",
        ).emit()
    try:
        args = build_parser().parse_args(argv)
        envelope = args.fn(args)
    except (config_mod.ConfigError, gitutil.GitError, LedgerVersionError) as exc:
        envelope = failure(str(exc))
    except SystemExit as exc:
        return int(exc.code or 0)
    return envelope.emit()


if __name__ == "__main__":
    raise SystemExit(main())
