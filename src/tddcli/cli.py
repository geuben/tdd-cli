"""Command surface (§8). Transport-agnostic by construction (R13.8).

No command accepts a phase, a cycle number, or executor identity (R8.3).
"""

from __future__ import annotations

import argparse
import concurrent.futures
import difflib
import json
import os
import pwd
import socket
import sys
import time
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import (
    __version__,
    actor,
    adapters,
    fleet,
    gitutil,
    harness,
    identity,
    render,
    snapshot,
    wire,
)
from . import (
    config as config_mod,
)
from . import (
    contract as contract_mod,
)
from . import (
    docs as docs_mod,
)
from . import ledger as ledger_mod
from . import runner as runner_mod
from . import service as service_mod
from . import target_lint as target_lint_mod
from .adapters.base import FAILED, NOT_COLLECTED
from .advance import advance as do_advance
from .envelope import (
    ENVELOPE_VERSION,
    VERB_SET_VERSION,
    Envelope,
    NextAction,
    Verb,
    failure,
    heartbeat,
)
from .ledger import Ledger, LedgerVersionError, ledger_path, now, open_ledger
from .machine import CLOSED, SKIPPED, Engine
from .remote import RemoteLedger

BASELINE_MAX_FAILURE_RATIO_DEFAULT = 0.5
BASELINE_MIN_COLLECTED = 10

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
    # Failing in a project that was never baselined — not attributable as a regression
    # (no baseline to subtract) vs. `pre_existing_failure` (baseline exists but missed it).
    "no_baseline_for_project",
}


def _worktree() -> Path:
    return gitutil.worktree_root(Path.cwd())


def _locate() -> tuple[Path, Path]:
    """The worktree and the repository identity that keys its ledger."""
    return gitutil.locate(Path.cwd())


def _context(require_run: bool = True):
    worktree, repo = _locate()
    cfg = config_mod.load(worktree)
    ledger = open_ledger(repo)
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
    state was the actual defect.

    When the claim is stale (collector pid is dead), emits `confirm_cycle_applicable`
    with recovery instructions rather than `await_baseline` — both `cmd_status` and
    `cmd_progress` go through this seam, so neither can return the wrong verb.
    """
    result = {
        "status": "collecting_baseline",
        "projects_done": claim["projects_done"],
        "projects_total": claim["projects_total"],
        "current_project": claim["current_project"],
        "elapsed_s": _claim_elapsed_s(claim),
        "stale": claim["stale"],
        "pid": claim["pid"],
    }
    if claim["stale"]:
        return Envelope(
            result=result,
            next_action=NextAction(
                Verb.CONFIRM_CYCLE_APPLICABLE,
                "Baseline collector (pid {}) is dead; re-run `tdd run start --plan <path>` to recover.".format(
                    claim["pid"]
                ),
            ),
        )
    return Envelope(
        result=result,
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
    if args.update_skill and not args.skill:
        return failure(
            "--update-skill replaces a harness's files: name the harness with --skill",
            reason="skill_required",
        )
    chosen = None
    if args.skill:
        chosen = harness.HARNESSES.get(args.skill)
        if chosen is None:
            return failure(
                f"unknown harness {args.skill!r}; known: {', '.join(sorted(harness.HARNESSES))}",
                reason="unknown_harness",
            )
        for scaffold in chosen.files:
            if not docs_mod.shipped(scaffold.source).is_file():
                return failure(
                    f"{scaffold.source} is missing from this installation of tdd-cli;"
                    " nothing was written. Please report the packaging bug.",
                    reason="missing_from_install",
                )
        # A dest that differs may be a local customisation; --force is for tdd.toml only.
        differs = [
            scaffold.dest
            for scaffold in chosen.files
            if (worktree / scaffold.dest).is_file()
            and (worktree / scaffold.dest).read_bytes()
            != docs_mod.shipped(scaffold.source).read_bytes()
        ]
        if differs and not args.update_skill:
            return failure(
                f"{', '.join(differs)} differ from this version's copies; nothing was written."
                " Pass --update-skill to replace them (re-apply any local additions after).",
                reason="harness_files_differ",
                differs=differs,
            )
    path = worktree / config_mod.CONFIG_NAME
    if path.exists() and not args.force:
        if chosen is None:
            return failure(f"{path} already exists; pass --force to overwrite")
        # Adding the harness to a configured project must not cost its config.
        result: dict = {"config": "kept"}
        detail = "Kept the existing tdd.toml."
    else:
        result, detail = _write_config(worktree, path)
    if chosen is not None:
        for scaffold in chosen.files:
            actor.current().write_file(
                worktree / scaffold.dest, docs_mod.shipped(scaffold.source).read_bytes()
            )
        settings = worktree / chosen.settings_path
        if not settings.exists():
            actor.current().write_file(
                settings, (json.dumps(chosen.settings, indent=2) + "\n").encode()
            )
            result["harness"] = {"name": chosen.name, "settings": "written"}
        elif harness.wires(chosen, settings.read_text(errors="replace")):
            result["harness"] = {"name": chosen.name, "settings": "wired"}
        else:
            # Never merged into: it is the user's file, and may already hold hooks.
            result["harness"] = {
                "name": chosen.name,
                "settings": "not_written",
                "settings_stanza": chosen.settings,
            }
            detail += (
                f" {chosen.settings_path} already exists and does not wire the tdd hooks:"
                " merge result.harness.settings_stanza into it. Without the Stop hook"
                " nothing stops the agent ending its turn mid-run."
            )
    return Envelope(result=result, next_action=NextAction(Verb.CONFIRM_CYCLE_APPLICABLE, detail))


def _write_config(worktree: Path, path: Path) -> tuple[dict, str]:
    """Detect the worktree's projects and write `tdd.toml` for review."""
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
    actor.current().write_file(path, "\n".join(lines).encode())
    result = {
        "written": str(path),
        "detected": [d[0] for d in detected],
        "unmatched": unmatched or None,
    }
    detail = (
        "Review tdd.toml: confirm roots, add lint/typecheck commands and artifact edges."
        " Then read `tdd docs harness` before driving a run."
        + (
            f" No supported adapter detected for: {', '.join(unmatched)} —"
            " declare one manually (third-party adapters register under the"
            " `tddcli.adapters` entry-point group)."
            if unmatched
            else ""
        )
    )
    return result, detail


def _skill_version(h: harness.Harness, text: str) -> tuple[bool, str]:
    """A declared mismatch fails; a skill that declares nothing passes, as a notice."""
    remedy = f"`tdd init --skill {h.name} --update-skill`"
    declared = harness.declared_versions(text)
    if declared is None:
        return True, (
            f"{h.skill} declares no verb_set_version, so drift cannot be checked;"
            f" {remedy} replaces it with this version's copy"
        )
    verb_set, envelope = declared.get("verb_set_version"), declared.get("envelope_version")
    if str(verb_set) == str(VERB_SET_VERSION) and str(envelope) == str(ENVELOPE_VERSION):
        return True, f"verb_set_version {verb_set}, envelope_version {envelope}"
    return False, (
        f"{h.skill} was written for verb_set_version {verb_set}, envelope_version {envelope};"
        f" this tdd emits {VERB_SET_VERSION}, {ENVELOPE_VERSION}. Run {remedy} and re-apply"
        " any local additions."
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


def _drop_to_the_agent(split: runner_mod.RunnerConfig) -> tuple[bool, str]:
    """Whether the runner can act as the agent, and if not, what fixes it.

    Probed before anything else doctor asks of the actor: everything else goes through
    the same sudo hop, and a refused hop would otherwise surface as whichever of them
    ran first. From `/`, so it cannot fail for a reason in the worktree.
    """
    agent = os.environ.get("SUDO_USER", "")
    asked = actor.current().run_argv(["id", "-u"], cwd=Path("/"))
    try:
        dropped = int(asked.stdout.strip()) == pwd.getpwnam(agent).pw_uid
    except (ValueError, KeyError):
        dropped = False
    if dropped:
        return True, ""
    said = asked.stderr.strip()
    return False, (
        f"the runner could not run `id -u` as {agent!r}. Add to sudoers:"
        f" `{split.user} ALL=({agent}) NOPASSWD:SETENV: ALL`"
        + (f" (sudo said: {said})" if said else "")
    )


def _split_checks(
    check: Callable,
    split: runner_mod.RunnerConfig,
    ledger_file: Path | None,
    dropped: tuple[bool, str],
) -> None:
    """What split mode rests on, probed live and as the agent.

    Each probe goes through the installed actor, so on a real machine it is answered
    by the real sudo and the real accounts: that is the one place the uid change
    itself is ever verified. `dropped` is `_drop_to_the_agent`'s answer, asked before
    anything else. `ledger_file` is None when the ledger is on the host's ledger
    service: there is then no file here for the agent to reach.
    """
    agent = os.environ.get("SUDO_USER", "")
    check("runs as the agent", *dropped)

    if ledger_file is not None:
        readable = actor.current().run_argv(["test", "-r", str(ledger_file)]).returncode == 0
        check(
            "ledger out of the agent's reach",
            not readable,
            f"{agent!r} can read {ledger_file}. Its directory must belong to {split.user}"
            " alone, at mode 700, somewhere the agent's account cannot otherwise reach"
            if readable
            else "",
        )

    # A runner whose code the agent can edit is the agent.
    install = Path(__file__).resolve().parent
    writable = actor.current().run_argv(["test", "-w", str(install)]).returncode == 0
    check(
        "install not writable by the agent",
        not writable,
        f"{agent!r} can write {install}. Install tdd-cli for the runner where the agent's"
        " account has no write access (for example under /opt, owned by root)"
        if writable
        else "",
    )


def cmd_doctor(args) -> Envelope:
    checks, check = _doctor_checklist()
    split = runner_mod.load()
    dropped = (True, "") if split is None else _drop_to_the_agent(split)
    if not dropped[0]:
        check("runs as the agent", *dropped)
        return Envelope(
            ok=False,
            error="the runner cannot act as the agent",
            result={"checks": checks, "projects": {}, "healthy": False, "mode": "split"},
            next_action=NextAction(Verb.RESOLVE_BLOCKER, "Resolve the failing checks above."),
        )
    worktree, repo = _locate()

    check("worktree resolvable", True, str(worktree))
    try:
        cfg = config_mod.load(worktree)
        check("tdd.toml valid", True, f"{len(cfg.projects)} projects")
    except config_mod.ConfigError as exc:
        check("tdd.toml valid", False, str(exc))
        return Envelope(ok=False, error="configuration invalid", result={"checks": checks})

    ledger = open_ledger(repo)
    remote = isinstance(ledger, RemoteLedger)
    if remote:
        # Reaching the service is not enough: say which source it records this guest as.
        check("ledger reachable", True, f"socket {ledger.path} (source {ledger.ping()['source']})")
    else:
        check("ledger reachable", True, str(ledger.path))
    check(
        "ledger outside worktree", not str(ledger.path).startswith(str(worktree)), str(ledger.path)
    )
    mode = "single" if split is None else "split"
    if split is None:
        # A notice, never a blocker: single-user installs must keep working. What it
        # must not do is let "outside the worktree" pass for "out of reach".
        check(
            "ledger isolation",
            True,
            "single-user mode: the ledger is owned by the same uid that runs the agent,"
            " which can open and edit it. `tdd docs split` sets up a runner the agent"
            " cannot reach.",
        )
    else:
        _split_checks(check, split, None if remote else ledger.path, dropped)

    ex = identity.resolve(worktree)
    ex_detail = f"{ex.source}: {ex.model}"
    if ex.source == "unknown":
        ex_detail += f" — {ex.reason}"
    check("executor identity", True, ex_detail)

    # Issue #99 — a notice, never a blocker: a VIRTUAL_ENV leaked from the launching
    # harness makes a runner that honours it use another environment's packages. The
    # agent's environment, not a split runner's: that is the one the suites run with.
    venv = actor.current().environ().get("VIRTUAL_ENV")
    if venv:
        try:
            rel = Path(venv).resolve().relative_to(worktree.resolve())
            owner = cfg.owning_project(rel.as_posix())
        except ValueError:
            owner = None
        if owner is not None:
            check("VIRTUAL_ENV", True, f"VIRTUAL_ENV={venv} is inside project {owner.name}'s root")
        else:
            check(
                "VIRTUAL_ENV",
                True,
                f"VIRTUAL_ENV={venv} is outside every project root in tdd.toml, so it was"
                " inherited from whatever launched this shell. A suite runner that honours"
                " VIRTUAL_ENV runs in that environment instead of the project's own, where the"
                " reporter or the dependencies may be missing. Unset it before `tdd run start`.",
            )

    for h in harness.HARNESSES.values():
        skill = worktree / h.skill
        if skill.is_file():
            check("driving skill version", *_skill_version(h, skill.read_text(errors="replace")))

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
            adapter = adapters.build(project, worktree)
            assert isinstance(adapter, adapters.PytestAdapter)
            probe = adapter.plugin_probe_cmd()
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
        detail = gate.output
        provenance = actor.current().provenance()
        if not gate.ok and provenance:
            detail = f"{detail}\n{provenance}"
        check("collectable", gate.ok, detail, project=name)

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
        result={"checks": checks, "projects": projects, "healthy": ok, "mode": mode},
        next_action=NextAction(
            Verb.CONFIRM_CYCLE_APPLICABLE if ok else Verb.RESOLVE_BLOCKER,
            "Environment is ready." if ok else "Resolve the failing checks above.",
        ),
    )


def cmd_plan_register(args) -> Envelope:
    worktree, repo = _locate()
    cfg = config_mod.load(worktree)
    ledger = open_ledger(repo)
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

    if parsed.cycles:
        lint_findings = target_lint_mod.lint_cycles(parsed.cycles, cfg, worktree)
        if lint_findings:
            return failure(
                "declared targets failed lint",
                reason="target_lint",
                findings=lint_findings,
            )

    existing = ledger.contract_by_blob(rel, parsed.blob_sha)
    contract_id = (
        existing["id"]
        if existing
        else ledger.register_contract(
            plan_path=rel,
            blob_sha=parsed.blob_sha,
            commit_sha=parsed.commit_sha,
            status=parsed.status,
            declared_cycles=contract_mod.cycles_to_json(parsed.cycles),
            annotation_keys=json.dumps(parsed.annotation_keys),
            ancillary_files=json.dumps(parsed.ancillary_files),
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


def cmd_plan_paths(args) -> Envelope:
    from . import plan_paths as plan_paths_mod

    worktree = _worktree()
    cfg = config_mod.load(worktree)
    plan_file = Path(args.plan)
    try:
        text = plan_file.read_text()
    except OSError as exc:
        return failure(f"malformed plan contract: {exc}", plan=str(args.plan))
    try:
        contract = contract_mod.parse(text, str(args.plan), cfg)
    except contract_mod.ContractError as exc:
        return failure(f"malformed plan contract: {exc}", plan=str(args.plan))
    result = plan_paths_mod.resolve(contract, cfg, worktree)
    if args.json:
        return Envelope(result=result, next_action=NextAction(Verb.COMPLETE, "Paths resolved."))
    sys.stdout.write(plan_paths_mod.render(result))
    return Envelope(
        result=result,
        next_action=NextAction(Verb.COMPLETE, "Paths rendered."),
        silent=True,
    )


def _baseline_captured(name, collection, *, elapsed_s, run_s, collect_s) -> None:
    """The `baseline_captured` heartbeat, shared by the serial and parallel probes.

    Split, not just totalled: `run` and `collect` have unrelated cost models — one
    scales with tests, the other with files — and a single number sends whoever asks
    "why was that slow?" out of the tool to measure by hand. `per_file_collects` is
    the files that fell to the per-file loop, one runner start each (issue #168).
    """
    heartbeat(
        event="baseline_captured",
        project=name,
        test_count=len(collection.tests),
        elapsed_s=elapsed_s,
        run_s=run_s,
        collect_s=collect_s,
        per_file_collects=collection.per_file_collects,
    )


def _probe_projects(
    projects,
    worktree,
    ledger,
    on_progress,
    cfg=None,
    config_sha=None,
    reuse_baselines=False,
    reuse_max_age=None,
    jobs: int = 1,
):
    """Probe a mapping of projects' baselines (R9.5a): run + collect, timing each,
    emitting a `baseline_captured` heartbeat, and calling `on_progress(done, name)`.
    Returns `({name: (verdict, collection)}, reused_set)`.
    """
    probes = {}
    reused = set()

    if jobs <= 1:
        for done, (name, project) in enumerate(projects.items(), start=1):
            adapter = adapters.build(project, worktree)
            if reuse_baselines and cfg is not None and config_sha is not None:
                roots = cfg.upstream_producer_roots(name)
                tree_hash = gitutil.tree_hash(worktree, roots)
                cached = ledger.cached_baseline(
                    name, tree_hash, config_sha, max_age_s=reuse_max_age
                )
                if cached is not None:
                    verdict = adapters.base.Verdict(
                        project=name, adapter=adapter.name, failed=json.loads(cached["failing"])
                    )
                    collection = adapters.base.Collection(
                        tests=set(json.loads(cached["tests"])),
                        failed_files=json.loads(cached["failed_files"]),
                    )
                    probes[name] = (verdict, collection)
                    reused.add(name)
                    heartbeat(
                        event="baseline_reused",
                        project=name,
                        test_count=len(collection.tests),
                        tree_hash=tree_hash[:8],
                    )
                    on_progress(done, name)
                    continue
            started = time.monotonic()
            verdict = adapter.run(None)
            ran = time.monotonic()
            collection = adapter.collect()
            elapsed = time.monotonic() - started
            probes[name] = (verdict, collection)
            _baseline_captured(
                name,
                collection,
                elapsed_s=round(elapsed, 2),
                run_s=round(ran - started, 2),
                collect_s=round(elapsed - (ran - started), 2),
            )
            if reuse_baselines and cfg is not None and config_sha is not None and not verdict.error:
                ledger.cache_baseline(
                    name,
                    tree_hash,
                    config_sha,
                    failing=sorted(verdict.failed),
                    tests=sorted(collection.tests),
                    failed_files=collection.failed_files,
                )
            on_progress(done, name)
        return probes, reused

    def _worker(name, project):
        adapter = adapters.build(project, worktree)
        started = time.monotonic()
        verdict = adapter.run(None)
        ran = time.monotonic()
        collection = adapter.collect()
        elapsed = time.monotonic() - started
        return (
            name,
            verdict,
            collection,
            round(ran - started, 2),
            round(elapsed - (ran - started), 2),
            round(elapsed, 2),
        )

    futures = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=jobs) as pool:
        for name, project in projects.items():
            futures[pool.submit(_worker, name, project)] = name
        for done, future in enumerate(concurrent.futures.as_completed(futures), start=1):
            proj_name = futures[future]
            try:
                name, verdict, collection, run_s, collect_s, elapsed_s = future.result()
            except Exception as exc:
                raise RuntimeError(f"{proj_name}: baseline probe failed: {exc}") from exc
            probes[name] = (verdict, collection)
            _baseline_captured(
                name, collection, elapsed_s=elapsed_s, run_s=run_s, collect_s=collect_s
            )
            on_progress(done, name)
    return probes, reused


def cmd_run_start(args) -> Envelope:
    worktree, repo = _locate()
    cfg = config_mod.load(worktree)
    ledger = open_ledger(repo)

    active = ledger.active_run(str(worktree))
    if active is not None:
        return failure(
            "a run is already active in this worktree",
            reason="run_already_active",
            run_id=active["id"],
            started_at=active["started_at"],
        )

    rel = str(Path(args.plan))
    contract_row = ledger.latest_contract(rel)
    if contract_row is None:
        return failure(f"{rel} is not registered; run `tdd plan register {rel}` first")

    delivered = ledger.delivered_run(rel)
    if delivered is not None:
        return failure(
            f"{rel} was delivered by run {delivered['id']} (ended {delivered['ended_at']});"
            " a delivered plan is not run again. To deliver it again, copy it to a new path,"
            " commit it, and run `tdd plan register <new path>`.",
            reason="plan_already_delivered",
            prior_run_id=delivered["id"],
            ended_at=delivered["ended_at"],
        )

    # R7.11 — the plan blob is the contract; drift must surface.
    blob_changed = False
    start_sha = None
    try:
        current_blob, start_sha = gitutil.blob_sha_at_head(worktree, rel)
        blob_changed = bool(
            contract_row["git_blob_sha"] and current_blob != contract_row["git_blob_sha"]
        )
    except gitutil.GitError:
        pass

    dirty = sorted(gitutil.dirty_paths(worktree))
    start_sha = start_sha or gitutil.head(worktree)
    if dirty and not args.allow_dirty:
        return failure(
            "working tree is dirty; commit first or pass --allow-dirty"
            " (pre-existing changes are then excluded from authorship forever)",
            dirty=dirty,
        )

    if contract_row["status"] == "undeclared" and not args.allow_undeclared:
        return failure("contract is undeclared; pass --allow-undeclared")

    if args.baseline_jobs < 1:
        return failure("--baseline-jobs must be >= 1")

    # R9.5c — scope baseline capture to plan-reachable projects unless opted out.
    declared_cycles = contract_mod.cycles_from_json(contract_row["declared_cycles"])

    if declared_cycles:
        lint_findings = target_lint_mod.lint_cycles(declared_cycles, cfg, worktree)
        if lint_findings:
            return failure(
                "declared targets failed lint",
                reason="target_lint",
                findings=lint_findings,
            )

    if declared_cycles and not args.baseline_all:
        declared_names = [p for c in declared_cycles for p in c.projects]
        reachable_names = cfg.reachable_projects(declared_names)
        probe_projects = {n: cfg.projects[n] for n in reachable_names if n in cfg.projects}
    else:
        probe_projects = cfg.projects

    unreachable: list[dict[str, Any]] = []
    for name, project in probe_projects.items():
        if not project.health_command:
            continue
        rc, out, err = adapters.base.run_command(
            project.health_command, worktree / project.root, label="health"
        )
        if rc != 0:
            unreachable.append({"project": name, "exit_code": rc, "output": (out + err)[-4000:]})
    if unreachable:
        names = ", ".join(u["project"] for u in unreachable)
        return failure(
            f"services unreachable for {names} — fix the stack or drop them from this run",
            reason="services_unreachable",
            projects=unreachable,
        )

    # Claim the worktree before probing: two `run start` calls against
    # one worktree must not both pass the baseline window. `Ledger.claim`'s `UNIQUE`
    # insert is the lock — do not read-then-write, which is the race this
    # closes. A claim whose owner is gone (e.g. a `SIGKILL`ed `run start`)
    # is reclaimed rather than obeyed, or one dead process bricks the worktree
    # forever; `active_claim` only computes staleness, it never deletes.
    existing = ledger.active_claim(str(worktree))
    if existing is not None and existing["stale"]:
        ledger.release_claim(str(worktree))

    claimed = ledger.claim(
        str(worktree),
        hostname=socket.gethostname(),
        pid=os.getpid(),
        projects_total=len(probe_projects),
    )
    if claimed is None:
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
        _cfg_sha = config_mod.config_sha(worktree)
        try:
            probes, reused = _probe_projects(
                probe_projects,
                worktree,
                ledger,
                on_progress=lambda done, name: ledger.update_claim(
                    str(worktree),
                    projects_done=done,
                    current_project=name,
                ),
                cfg=cfg,
                config_sha=_cfg_sha,
                reuse_baselines=args.reuse_baselines,
                reuse_max_age=args.reuse_max_age,
                jobs=args.baseline_jobs,
            )
        except RuntimeError as exc:
            return failure(str(exc))
        # R9.5j — a report the tool could not read observed nothing, so no ratio applies.
        # A project with no suite yet is exempt, as in R9.5a.
        unreadable = [
            {"project": n, "defect": v.error}
            for n, (v, c) in probes.items()
            if n not in reused and v.error and (c.tests or c.failed_files)
        ]
        if unreadable:
            return failure(
                "\n".join(
                    f"{u['project']}: the baseline run produced no report the tool could read"
                    f" — {u['defect']}"
                    for u in unreadable
                )
                + "\nA baseline that cannot be read observed nothing, whatever its failure count,"
                " so --accept-baseline does not apply. Fix the environment (`tdd doctor` notes"
                " a foreign VIRTUAL_ENV) and retry.",
                reason="baseline_unreadable",
                projects=unreadable,
            )
        for name, (verdict, collection) in probes.items():
            if name in reused:
                continue
            if not collection.tests and collection.failed_files:
                sample = sorted(collection.failed_files)[0]
                message = (
                    f"{name}: no test could be collected — {len(collection.failed_files)}"
                    f" file(s) failed to collect, starting with {sample}. The baseline"
                    " would record no failures and every pre-existing failure would then"
                    " read as a regression. Fix the environment (dependencies"
                    " installed?) and retry."
                    f"\n{sample}: {collection.failed_files[sample]}"
                )
                provenance = actor.current().provenance()
                if provenance:
                    message = f"{message}\n{provenance}"
                return failure(
                    message,
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

        implausible = []
        for name, (v, c) in probes.items():
            probed = probe_projects.get(name)
            threshold = (
                probed.baseline_max_failure_ratio
                if probed and probed.baseline_max_failure_ratio is not None
                else BASELINE_MAX_FAILURE_RATIO_DEFAULT
            )
            if len(c.tests) >= BASELINE_MIN_COLLECTED and len(v.failed) / len(c.tests) > threshold:
                implausible.append(
                    {
                        "project": name,
                        "failing": len(v.failed),
                        "collected": len(c.tests),
                        "ratio": len(v.failed) / len(c.tests),
                        "threshold": threshold,
                    }
                )
        if implausible and not args.accept_baseline:
            return failure(
                "baseline is implausible — more than half the suite is failing;"
                " the environment may be broken. Fix the stack or pass --accept-baseline.",
                reason="baseline_implausible",
                projects=implausible,
            )

        executor = identity.resolve(worktree, args.executor)
        run_id = ledger.start_run(
            contract_row["id"],
            executor_model=executor.model,
            executor_session=executor.session,
            executor_source=executor.source,
            worktree=str(worktree),
            allow_dirty=bool(args.allow_dirty),
            preexisting_dirty=dirty,
            config_sha=config_mod.config_sha(worktree),
            start_sha=start_sha,
        )
        run = ledger.run(run_id)
        if blob_changed:
            ledger.event(run_id, None, "plan_blob_changed", rel)
        skipped = sorted(set(cfg.projects) - set(probe_projects))
        if skipped:
            ledger.event(run_id, None, "baseline_scoped", json.dumps(skipped))
        if reused:
            ledger.event(run_id, None, "baseline_reused", json.dumps(sorted(reused)))
        if implausible:
            ledger.event(run_id, None, "baseline_accepted", json.dumps(implausible))
        if executor.source == "unknown":
            ledger.event(run_id, None, "executor_unknown", executor.reason or "")

        # Baselines and the collection snapshot, per project (R9.5, R8.9) — from the
        # probe above, so the suite is not run twice.
        for name, (verdict, collection) in probes.items():
            ledger.record_baseline(
                run_id,
                name,
                sorted(verdict.failed),
                source="reused" if name in reused else "probed",
            )
            ledger.record_collection(
                run_id, name, sorted(collection.tests), collection.failed_files
            )

        for name, (verdict, _collection) in probes.items():
            if not verdict.failed:
                continue
            failing = set(verdict.failed)
            prev = ledger.previous_baseline(str(worktree), name, run_id) or set()
            new_ids = failing - prev
            inherited = failing & prev
            resolved = prev - failing
            ledger.event(
                run_id,
                None,
                "baseline_standing_delta",
                json.dumps(
                    {
                        "project": name,
                        "new": sorted(new_ids),
                        "inherited": sorted(inherited),
                        "resolved": sorted(resolved),
                    }
                ),
            )

        engine = Engine(ledger, cfg, worktree, run)
        artifact_outcome = engine.check_artifacts(None)
        if artifact_outcome.failed:
            f = artifact_outcome.failed[0]
            stderr_tail = (f.get("stderr") or "").strip()[-200:]
            ledger.end_run(run_id, "refused")
            return failure(
                f"artifact {f['artifact']}: regenerate hook exited {f['code']}"
                + (f" — {stderr_tail}" if stderr_tail else "")
                + ". The artifact cannot be kept fresh on this machine;"
                " fix the hook or the toolchain and retry.",
                reason="artifact_regenerate_failed",
                artifacts=artifact_outcome.failed,
            )
        if artifact_outcome.stale:
            names = ", ".join(artifact_outcome.stale)
            ledger.end_run(run_id, "refused")
            return failure(
                f"artifact(s) stale and not regenerated: {names}. A stale contract gives a green"
                " wrong answer; rebuild and commit the artifact (or fix its regenerate hook) so"
                " its check passes, then retry.",
                reason="stale_artifact",
                stale_artifacts=artifact_outcome.stale,
            )
        first = engine.declared[0] if engine.declared else None
        if first is None:
            return failure("contract declares no cycles")
        cycle = engine.open_cycle(first.ordinal)

        verb, opening = engine.opening_action(cycle)
        detail = f"Run {run_id} started ({executor.model}, via {executor.source}). {opening}"
        result: dict = {
            "baselines": {n: len(v) for n, v in ledger.baselines(run_id).items()},
            "executor_source": executor.source,
        }
        if executor.source == "unknown":
            result["executor_warning"] = executor.reason or ""
        return Envelope(
            run=engine.run_state(cycle),
            result=result,
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
    existing_advance = ledger.active_advance_claim(str(worktree))
    if existing_advance is not None and existing_advance["stale"]:
        ledger.release_advance_claim(str(worktree))

    claimed = ledger.claim_advance(str(worktree), hostname=socket.gethostname(), pid=os.getpid())
    if claimed is None:
        held = ledger.advance_claim_row(str(worktree))
        started = datetime.fromisoformat(held["started_at"])
        if started.tzinfo is None:
            started = started.replace(tzinfo=timezone.utc)
        elapsed_s = int((datetime.now(timezone.utc) - started).total_seconds())
        return failure(
            "an advance is already in flight for this worktree; do not re-run or kill it"
            " — wait for its envelope, then run `tdd status` to see where the run stands",
            reason="advance_in_flight",
            pid=held["pid"],
            started_at=held["started_at"],
            elapsed_s=elapsed_s,
        )
    try:
        result = do_advance(engine, cycle, retry=args.retry)
    finally:
        ledger.release_advance_claim(str(worktree))
    return result


def cmd_cycle_skip(args) -> Envelope:
    worktree, cfg, ledger, run = _context()
    engine = _engine(worktree, cfg, ledger, run)
    cycle = ledger.open_cycle(run["id"])
    if cycle is None:
        return failure("no open cycle")
    ledger.skip_cycle(cycle["id"], from_phase=cycle["phase"], to_phase=SKIPPED, reason=args.reason)
    nxt_declared = next((c for c in engine.declared if c.ordinal > cycle["ordinal"]), None)
    if nxt_declared is None:
        ledger.end_run(run["id"], "complete")
        return Envelope(
            run={"id": run["id"], "cycle": cycle["ordinal"], "phase": SKIPPED},
            next_action=NextAction(
                Verb.COMPLETE,
                "Final cycle skipped; run complete."
                ' Before rendering, record a closing narrative with `tdd note "<hardest cycle and why, plan inaccuracies, deviations>"`.'
                " Then run `tdd log render`.",
            ),
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
    ledger.add_annotation(run["id"], cycle["id"] if cycle else None, args.key, args.value)
    return Envelope(
        run={"id": run["id"], "cycle": cycle["ordinal"] if cycle else None},
        result={"key": args.key},
        next_action=NextAction(Verb.REFACTOR_OR_ADVANCE, "Annotation recorded. `tdd advance`."),
    )


def cmd_note(args) -> Envelope:
    worktree, cfg, ledger, run = _context(require_run=False)
    if run is None:
        run = ledger.latest_run(str(worktree))
    if run is None:
        return failure("no runs recorded for this worktree; `tdd run start --plan <path>`")
    cycle = ledger.open_cycle(run["id"])
    ledger.add_note(
        run["id"],
        cycle["id"] if cycle else None,
        cycle["phase"] if cycle else None,
        args.text,
    )
    if cycle is not None:
        next_action = NextAction(
            Verb.REFACTOR_OR_ADVANCE, "Note recorded. Resume the phase in progress."
        )
    else:
        next_action = NextAction(Verb.COMPLETE, "Note recorded. Run `tdd log render`.")
    return Envelope(
        run={"id": run["id"], "cycle": cycle["ordinal"] if cycle else None},
        result={"noted": True},
        next_action=next_action,
    )


def cmd_blocker(args) -> Envelope:
    worktree, cfg, ledger, run = _context()
    if args.kind not in BLOCKER_KINDS:
        return failure(f"unknown blocker kind {args.kind!r}; use one of {sorted(BLOCKER_KINDS)}")
    cycle = ledger.open_cycle(run["id"])
    ledger.add_blocker(run["id"], cycle["id"] if cycle else None, args.kind, args.detail)
    # R8.7 — a blocked run is not live, so the stop hook must release.
    ledger.end_run(run["id"], "blocked")
    return Envelope(
        run={"id": run["id"], "cycle": cycle["ordinal"] if cycle else None, "phase": "BLOCKED"},
        result={"kind": args.kind, "detail": args.detail},
        next_action=NextAction(
            Verb.BLOCKED,
            f"Run blocked ({args.kind}). A human can resume with"
            " `tdd resume --unblock --note ...`.",
        ),
    )


def _accept_failures_into_baseline(
    engine, ledger: Ledger, run_id: int
) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    """Fold pre-existing failures into the baseline (R9.5b).

    Probes each project at run.start_sha; only accepts candidates that fail there.
    A test that passes at start_sha is refused — it is a run-introduced regression.
    Returns (accepted, refused).
    """
    latest = ledger.latest_close_sweeps(run_id)
    rows = {r["project"]: r for r in ledger.baseline_rows(run_id)}
    accepted: dict[str, list[str]] = {}
    refused: dict[str, list[str]] = {}
    for sweep in latest:
        project = sweep["project"]
        row = rows.get(project)
        sweep_failed = sorted(json.loads(sweep["other_failures"]))
        if row is None:
            if not sweep_failed:
                continue
            engine.probe_at_start_sha(project)
            refused[project] = sweep_failed
        else:
            known = set(json.loads(row["failing"]))
            new = sorted(set(sweep_failed) - known)
            if not new:
                continue
            probe = engine.probe_at_start_sha(project)
            if probe.observed:
                acc = [f for f in new if f in probe.failing]
                ref = [f for f in new if f not in probe.failing]
            else:
                acc = []
                ref = list(new)
            if acc:
                ledger.amend_baseline(run_id, row["id"], sorted(known | set(acc)))
                accepted[project] = acc
            if ref:
                refused[project] = ref
    run_row = ledger.run(run_id)
    start_sha = run_row["start_sha"] if run_row else None
    verdicts: dict[str, dict] = {}
    for project in set(list(accepted.keys()) + list(refused.keys())):
        entry: dict = {
            "start_sha": start_sha,
            "accepted": {t: "fails at start sha" for t in accepted.get(project, [])},
        }
        if project in refused:
            entry["refused"] = {t: "passes at start sha" for t in refused[project]}
        verdicts[project] = entry
    if verdicts:
        ledger.event(run_id, None, "baseline_amended", json.dumps(verdicts))
    return accepted, refused


def cmd_resume(args) -> Envelope:
    worktree, repo = _locate()
    cfg = config_mod.load(worktree)
    ledger = open_ledger(repo)
    run = ledger.active_run(str(worktree))
    accepted: dict[str, list[str]] = {}
    refused_from_baseline: dict[str, list[str]] = {}

    if args.accept_failures and not args.unblock:
        return failure("--accept-failures applies to --unblock")

    if args.unblock:
        if run is not None:
            return failure("run is already live; --unblock applies to a blocked run")
        blocked = ledger.latest_blocked_run(str(worktree))
        if blocked is None:
            return failure("no blocked run to unblock in this worktree")
        if not args.note:
            return failure("--unblock requires --note describing the unblock")
        ledger.reopen_run(blocked["id"], args.note)
        run = ledger.run(blocked["id"])
        if args.accept_failures:
            _eng = _engine(worktree, cfg, ledger, run)
            accepted, refused_from_baseline = _accept_failures_into_baseline(
                _eng, ledger, blocked["id"]
            )

    if run is None:
        return failure("no active run in this worktree")

    engine = _engine(worktree, cfg, ledger, run)
    cycle = ledger.open_cycle(run["id"])
    if cycle is None:
        return Envelope(
            run={"id": run["id"], "phase": CLOSED},
            next_action=NextAction(Verb.COMPLETE, "Run complete."),
        )
    result: dict[str, object] = {"resumed": True}
    if accepted:
        result["accepted_into_baseline"] = accepted
    if refused_from_baseline:
        result["refused_from_baseline"] = refused_from_baseline
    return Envelope(
        run=engine.run_state(cycle),
        result=result,
        next_action=NextAction(
            Verb.REFACTOR_OR_ADVANCE,
            f"Resumed at cycle {cycle['ordinal']}, phase {cycle['phase']}. Run `tdd advance`.",
        ),
    )


def _calling_account() -> str:
    """The account that asked. On a split runner that is the agent behind sudo, which
    sets `SUDO_USER` itself; elsewhere the effective uid. Never `getpass.getuser()`: it
    trusts `LOGNAME`/`USER`, which the caller controls."""
    split = runner_mod.load()
    if split is not None and split.role == "runner" and os.environ.get("SUDO_USER"):
        return os.environ["SUDO_USER"]
    return pwd.getpwuid(os.geteuid()).pw_name


def cmd_run_abandon(args) -> Envelope:
    if not args.reason.strip():
        return failure("--reason must say why the run is abandoned", reason="reason_required")
    worktree, repo = _locate()
    ledger = open_ledger(repo)
    if args.run is not None:
        run = ledger.run(args.run)
        if run is None:
            return failure(f"no run {args.run} in this ledger", reason="run_not_found")
        if run["ended_at"] is not None and run["outcome"] != "blocked":
            return failure(f"run {args.run} already ended {run['outcome']}", reason="run_ended")
        # By id only when the worktree is gone or is the caller's own: on a split runner
        # every agent reaches the same ledger, and one must not end another's live run.
        if run["worktree_path"] != str(worktree) and Path(run["worktree_path"]).exists():
            return failure(
                f"run {args.run}'s worktree {run['worktree_path']} still exists;"
                " abandon it from there",
                reason="worktree_exists",
            )
    else:
        run = ledger.active_run(str(worktree)) or ledger.latest_blocked_run(str(worktree))
        if run is None:
            return failure("no live or blocked run in this worktree", reason="no_run")
    # A stale claim is released below, not obeyed; a live one means an advance is mid-flight.
    claim = ledger.active_advance_claim(run["worktree_path"])
    if claim is not None and not claim["stale"]:
        return failure(
            f"an advance is in flight (pid {claim['pid']}); stop it first",
            reason="advance_in_flight",
            pid=claim["pid"],
        )
    executor = identity.resolve(worktree)
    ledger.abandon_run(
        run["id"],
        reason=args.reason,
        account=_calling_account(),
        executor_model=executor.model,
        executor_source=executor.source,
        at=now(),
    )
    return Envelope(
        result={"run_id": run["id"]},
        next_action=NextAction(Verb.COMPLETE, f"Run {run['id']} abandoned."),
    )


def cmd_sensitivity(args) -> Envelope:
    worktree, cfg, ledger, run = _context()
    cycle = ledger.open_cycle(run["id"])
    if cycle is None:
        return failure("no open cycle")

    if args.step == "begin":
        if ledger.open_sensitivity(cycle["id"]) is not None:
            return failure("a sensitivity check is already open")
        check_id = ledger.open_sensitivity_check(
            cycle["id"],
            reference_diff=snapshot.capture(worktree, cfg),
            reference_untracked=snapshot.fingerprint(worktree, cfg),
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
        outcomes, _, verdicts, failure_text = engine.run_projects(
            projects, targets, cycle, "SENSITIVITY", False, target_only=True
        )
        # A mutation that breaks collection also proves the test depends on the code.
        bites = bool(outcomes) and all(o in (FAILED, NOT_COLLECTED) for o in outcomes.values())
        evidence = next((v.target_evidence for v in verdicts if v.target_evidence), "")
        ledger.record_sensitivity_mutation(
            cycle["id"],
            open_check["id"],
            mutation_diff=gitutil.diff_text(worktree)[:20000],
            observed_failure=failure_text[:4000],
            evidence_line=evidence,
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
    ledger.close_sensitivity_check(cycle["id"], open_check["id"], restored_ok=restored_ok)
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
    #
    # The argument is qualified and matched the way a plan declaration is (#163), so
    # the plan's own spelling names the test it collected as; the collected id is what
    # is stored, because outcome lookups compare against verdicts verbatim.
    declared = _engine(worktree, cfg, ledger, run).declared_for(cycle["ordinal"])
    wanted = Engine._qualify(declared, args.test) if declared else args.test
    known: set[str] = set()
    target: str | None = None
    for name in json.loads(cycle["projects"]):
        adapter = adapters.build(cfg.project(name), worktree)
        collected = adapter.collect().tests
        known |= collected
        norm = adapter.normalise_id(wanted)
        target = target or next(
            (t for t in sorted(collected) if adapter.normalise_id(t) == norm), None
        )
    if target is None:
        close = difflib.get_close_matches(args.test, sorted(known), n=3, cutoff=0.6)
        hint = f" Closest collected ids: {', '.join(close)}." if close else ""
        return failure(
            f"{args.test} is not a collected test in this cycle's projects;"
            f" the target was not changed.{hint}"
        )

    ledger.set_targets(cycle["id"], [target])
    ledger.event(run["id"], cycle["id"], "target_named_by_agent", target)
    return Envelope(
        run={"id": run["id"], "cycle": cycle["ordinal"]},
        result={"target": target},
        next_action=NextAction(Verb.REFACTOR_OR_ADVANCE, "Target set. `tdd advance`."),
    )


def cmd_invocation_show(args) -> Envelope:
    """One suite invocation's recorded failures (#105), looked up across the whole
    repository's ledger: a finished run's invocations are what an audit asks about."""
    worktree, cfg, ledger, run = _context(require_run=False)
    invocation = ledger.invocation(args.id)
    if invocation is None:
        return failure(
            f"no invocation {args.id} in this repository's ledger", reason="unknown_invocation"
        )
    return Envelope(
        result={
            "invocation": invocation["id"],
            "phase": invocation["phase_at"],
            "project": invocation["project"],
            "failures": [
                {
                    "test": d["test_id"],
                    "phase": d["phase"],
                    "message": d["message"],
                    "detail": d["detail"],
                }
                for d in ledger.failure_details(invocation["id"])
            ],
        },
        next_action=NextAction(
            Verb.REFACTOR_OR_ADVANCE, "Read-only. Resume the phase in progress."
        ),
    )


def cmd_log_render(args) -> Envelope:
    worktree, cfg, ledger, run = _context(require_run=False)
    if run is None:
        run = ledger.latest_run(str(worktree))
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
        actor.current().write_file(out, text.encode())
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
        run = ledger.latest_run(str(worktree))
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
            if result["stale"]:
                sys.stdout.write(
                    f"baseline collector (pid {result['pid']}) is dead —"
                    " run `tdd run start --plan <path>` to recover\n"
                )
            else:
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
    worktree, repo = _locate()
    split = runner_mod.load()
    if split is not None and split.role == "runner" and split.ledger_socket is not None:
        # The ledger is on the host: read this source's view of it through the socket.
        reader = open_ledger(repo)
    else:
        reader = ledger_mod.open_readonly(ledger_path(repo))
    summary = fleet.summarise(reader)
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


def cmd_runner_import(args) -> Envelope:
    """Needs no worktree: it is an operator's command, run as the runner, about a file."""
    split = runner_mod.load()
    if split is None or split.role != "runner":
        # With no runner there is nowhere out of reach to import into: the copy would
        # land back in the caller's own ledger home.
        return failure(
            "this machine is not split, or this is not its runner: `tdd docs split` sets one up",
            reason="not_split",
        )
    if split.ledger_socket is not None:
        # This runner keeps no ledger: it is the host's, behind the socket.
        return failure(
            "this runner keeps its ledger on the host's ledger service: import there, with"
            " `tdd ledger import <file> --source <name>`",
            reason="ledger_remote",
        )
    # sudo sets SUDO_UID itself. Unset means someone logged in as the runner; "0" means
    # root. Anything else reached us the way an agent does, and an agent that could
    # import could hand the runner a history it wrote itself.
    if os.environ.get("SUDO_UID") not in (None, "0"):
        return failure(
            "`tdd runner import` is for the machine's operator: run it as root, or"
            " logged in as the runner",
            reason="operator_only",
        )
    source = Path(args.ledger).resolve()
    if not source.is_file():
        return failure(f"{source} is not a file")
    held = ledger_mod.ledger_home() / source.name
    if held.exists():
        # No merge, by design: the runner's copy may hold runs recorded out of the
        # agent's reach, and a second import would trade them for ones that were not.
        return failure(
            f"the runner already holds {held}; importing again would overwrite it",
            reason="ledger_exists",
        )
    target, marker = ledger_mod.import_legacy(source)
    return Envelope(
        result={"imported": str(target), "pre_split_import": marker},
        next_action=NextAction(
            Verb.COMPLETE,
            f"Imported to {target}. Runs up to {marker['last_run_id']} predate the"
            " split and are marked as such.",
        ),
    )


# -- the ledger service: the operator's verbs ----------------------------------------


def _ledger_verb(answer: Callable) -> Callable:
    """A `tdd ledger` handler: it needs this machine's ledger service config first.

    These verbs are the host operator's. They are answered here, never by a runner,
    and only on a machine that runs a ledger service.
    """

    def handler(args) -> Envelope:
        path = service_mod.config_path()
        if not path.is_file():
            return failure(
                f"no ledger service is configured on this machine ({path} is absent):"
                " `tdd docs split` describes one",
                reason="no_service",
            )
        try:
            return answer(args, service_mod.load_config(path))
        except wire.LedgerRefused as exc:
            # The operator's own service said no: its code is the reason.
            return failure(exc.error, reason=exc.refusal)

    return handler


def _not_implemented(args, cfg) -> Envelope:
    return failure("not implemented", reason="not_implemented")


def _ledger_serve(args, cfg) -> Envelope:
    heartbeat(event="ledger_service_listening", admin_socket=str(cfg.admin_socket))
    service_mod.serve(cfg)
    return Envelope(
        result={"stopped": True},
        next_action=NextAction(Verb.COMPLETE, "The ledger service stopped."),
    )


def _ledger_read(cfg, method: str, *args, **kwargs):
    """A read, on the admin socket, or on the report socket when the admin socket
    cannot be opened: the dashboard's account is let into the report socket alone.

    Only a failed connect falls back. A connection that was made and then dropped is
    never retried on the other socket.
    """
    try:
        conn = wire.Connection(cfg.admin_socket)
    except wire.LedgerUnreachable:
        if cfg.report_socket is None:
            raise
        conn = wire.Connection(cfg.report_socket)
    try:
        return conn.request(method, *args, **kwargs)
    finally:
        conn.close()


def _ledger_fleet(args, cfg) -> Envelope:
    return Envelope(
        result=_ledger_read(cfg, "fleet"),
        next_action=NextAction(Verb.COMPLETE, "Fleet reported across every source."),
    )


def _ledger_log(args, cfg) -> Envelope:
    rendered = _ledger_read(cfg, "log", args.repo, args.run)
    if args.out:
        out = Path(args.out)
        actor.current().write_file(out, rendered["text"].encode())
        return Envelope(
            result={"written": str(out), "source": rendered["source"]},
            next_action=NextAction(Verb.COMPLETE, f"Friction log written to {out}."),
        )
    sys.stdout.write(rendered["text"])
    return Envelope(
        result={"rendered": True, "source": rendered["source"]},
        next_action=NextAction(Verb.COMPLETE, "Rendered."),
        silent=True,
    )


def _ledger_import(args, cfg) -> Envelope:
    source = Path(args.file).resolve()
    if not source.is_file():
        return failure(f"{source} is not a file")
    imported = wire.call(cfg.admin_socket, "import", str(source), args.source)
    return Envelope(
        result=imported,
        next_action=NextAction(
            Verb.COMPLETE,
            f"Imported to {imported['imported']} as source {args.source}. Runs up to"
            f" {imported['pre_split_import']['last_run_id']} were recorded where the agent"
            " could reach the ledger, and are marked as such.",
        ),
    )


def _ledger_metrics(args, cfg) -> Envelope:
    return Envelope(
        result=_ledger_read(cfg, "metrics", args.repo, since=args.since),
        next_action=NextAction(Verb.COMPLETE, "Metrics computed over every source."),
    )


def _ledger_sources(args, cfg) -> Envelope:
    sources = wire.call(cfg.admin_socket, "sources")
    return Envelope(
        result={"sources": sources},
        next_action=NextAction(Verb.COMPLETE, f"{len(sources)} source(s)."),
    )


def _bind_call(args, cfg, method: str, *call_args):
    """A `bind` or `unbind`, on the socket the operator named, or else the admin socket.

    An admin socket this account cannot open falls back to the bind socket, when there
    is one. Only a failed connect does: a request the admin socket took is never resent.
    """
    if args.socket:
        return wire.call(Path(args.socket), method, *call_args)
    try:
        conn = wire.Connection(cfg.admin_socket)
    except wire.LedgerUnreachable:
        if cfg.bind_socket is None:
            raise
        conn = wire.Connection(cfg.bind_socket)
    try:
        return conn.request(method, *call_args)
    finally:
        conn.close()


def _ledger_bind(args, cfg) -> Envelope:
    bound = _bind_call(args, cfg, "bind", args.name, args.executor)
    return Envelope(
        result=bound,
        next_action=NextAction(
            Verb.COMPLETE,
            f"Source {args.name}'s next runs record {args.executor}, as said by the operator.",
        ),
    )


def _ledger_unbind(args, cfg) -> Envelope:
    unbound = _bind_call(args, cfg, "unbind", args.name)
    return Envelope(
        result=unbound,
        next_action=NextAction(
            Verb.COMPLETE, f"Source {args.name}'s next runs record the guest's own claim."
        ),
    )


def _ledger_remove_source(args, cfg) -> Envelope:
    removed = wire.call(cfg.admin_socket, "remove_source", args.name)
    return Envelope(
        result=removed,
        next_action=NextAction(
            Verb.COMPLETE, f"Source {args.name}'s socket is closed; its runs stay recorded."
        ),
    )


def _ledger_add_source(args, cfg) -> Envelope:
    added = wire.call(
        cfg.admin_socket, "add_source", args.name, args.socket, executor=args.executor
    )
    return Envelope(
        result=added,
        next_action=NextAction(
            Verb.COMPLETE,
            f"Source {args.name} listens on {args.socket}. Forward that socket into the"
            " guest and name it as the guest runner's `ledger_socket`.",
        ),
    )


def cmd_docs(args) -> Envelope:
    """The shipped documentation, printed. No network, and versioned with the binary.

    With no topic this is a machine-readable index — an agent that has just met
    `tdd` needs to know what it can read before it reads any of it.
    """
    if args.topic is None:
        return Envelope(
            result={
                "topics": [
                    {"name": t.name, "summary": t.summary, "path": t.path} for t in docs_mod.TOPICS
                ]
            },
            next_action=NextAction(
                Verb.CONFIRM_CYCLE_APPLICABLE,
                "Read `tdd docs harness` before driving a run: it specifies the envelope,"
                " the verb set, and the rules a driving skill must obey.",
            ),
        )
    if args.topic not in docs_mod.BY_NAME:
        known = ", ".join(t.name for t in docs_mod.TOPICS)
        return failure(f"unknown docs topic {args.topic!r}; known topics: {known}")
    try:
        sys.stdout.write(docs_mod.read(args.topic))
    except FileNotFoundError as exc:
        return failure(str(exc))
    return Envelope(
        result={"topic": args.topic},
        next_action=NextAction(Verb.COMPLETE, "Documentation rendered."),
        silent=True,
    )


# -- parser --------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="tdd",
        description=__doc__,
        # An agent reads --help unprompted and will never guess `tdd docs` exists.
        # This line is the whole discovery hop to the shipped protocol spec.
        epilog=(
            "Driving this tool from an agent? Run `tdd docs` for the shipped"
            " documentation — `tdd docs harness` specifies the envelope and verb set."
        ),
    )
    p.add_argument("--version", action="version", version=f"tdd-cli {__version__}")
    # Split mode's client adds this when it re-executes as the runner. It carries the
    # agent's environment and nothing else: no phase, cycle number or identity (R8.3).
    p.add_argument("--agent-context-stdin", action="store_true", help=argparse.SUPPRESS)
    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("docs", help="print the documentation shipped with this version")
    s.add_argument("topic", nargs="?", help="omit to list the available topics")
    s.set_defaults(fn=cmd_docs)

    s = sub.add_parser("init", help="scaffold tdd.toml for review")
    s.add_argument("--force", action="store_true")
    s.add_argument("--skill", help="also scaffold the driving skill and hooks for this harness")
    s.add_argument(
        "--update-skill",
        action="store_true",
        help="replace harness files that differ from this version's copies",
    )
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

    s = plan.add_parser("paths")
    s.add_argument("plan")
    s.add_argument("--json", action="store_true")
    s.set_defaults(fn=cmd_plan_paths)

    run_p = sub.add_parser("run", help="runs").add_subparsers(dest="run_command", required=True)
    s = run_p.add_parser("start")
    s.add_argument("--plan", required=True)
    s.add_argument("--executor", help="human-supplied label; agents must not use this")
    s.add_argument("--allow-dirty", action="store_true")
    s.add_argument("--allow-undeclared", action="store_true")
    s.add_argument(
        "--baseline-all",
        action="store_true",
        help="probe all projects, skipping reachability scoping",
    )
    s.add_argument(
        "--reuse-baselines",
        action="store_true",
        help="cache and reuse baseline probe results keyed by content hash",
    )
    s.add_argument(
        "--reuse-max-age",
        type=float,
        default=None,
        help="max age in seconds for a cached baseline entry",
    )
    s.add_argument(
        "--baseline-jobs",
        type=int,
        default=1,
        help="number of parallel baseline probes (default: 1, serial)",
    )
    s.add_argument(
        "--accept-baseline",
        action="store_true",
        help="override the implausibility gate and record the baseline anyway",
    )
    s.set_defaults(fn=cmd_run_start)

    s = run_p.add_parser("abandon", help="end a run that will not be finished; human only")
    s.add_argument("--reason", required=True)
    s.add_argument("--run", type=int, default=None, help="a run whose worktree is gone")
    s.set_defaults(fn=cmd_run_abandon)

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

    s = sub.add_parser("note", help="attach a narrative note to the current cycle or run")
    s.add_argument("text")
    s.set_defaults(fn=cmd_note)

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
        help="fold pre-existing failures into the baseline: accepts only tests that also fail"
        " at run.start_sha; tests that pass there are refused; never inserts a new row;"
        " recorded as baseline_amended",
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

    inv = sub.add_parser(
        "invocation", help="one suite invocation's recorded failures"
    ).add_subparsers(dest="invocation_command", required=True)
    s = inv.add_parser("show")
    s.add_argument("id", type=int)
    s.set_defaults(fn=cmd_invocation_show)

    s = sub.add_parser("progress", help="human-readable plan progress")
    s.add_argument("--json", action="store_true", help="machine output instead")
    s.set_defaults(fn=cmd_progress)

    s = sub.add_parser("fleet", help="all active runs on this repository, across every worktree")
    s.add_argument("--json", action="store_true", help="machine output instead")
    s.set_defaults(fn=cmd_fleet)

    s = sub.add_parser("metrics")
    s.set_defaults(fn=cmd_metrics)

    runner_p = sub.add_parser("runner", help="split-mode runner administration").add_subparsers(
        dest="runner_command", required=True
    )
    s = runner_p.add_parser("import")
    s.add_argument("ledger")
    s.set_defaults(fn=cmd_runner_import)

    ledger_p = sub.add_parser(
        "ledger", help="the host's ledger service: its sources and every source's history"
    ).add_subparsers(dest="ledger_command", required=True)
    s = ledger_p.add_parser("serve", help="run the ledger service until SIGTERM")
    s.set_defaults(fn=_ledger_verb(_ledger_serve))
    s = ledger_p.add_parser("sources", help="every source, its socket and its executor")
    s.set_defaults(fn=_ledger_verb(_ledger_sources))
    s = ledger_p.add_parser("add-source", help="open a socket for a new guest")
    s.add_argument("name")
    s.add_argument("--socket", required=True)
    s.add_argument("--executor", help="the model this source runs, recorded on its runs")
    s.set_defaults(fn=_ledger_verb(_ledger_add_source))
    s = ledger_p.add_parser("remove-source", help="close a guest's socket")
    s.add_argument("name")
    s.set_defaults(fn=_ledger_verb(_ledger_remove_source))
    s = ledger_p.add_parser("bind", help="set the executor a source's next runs record")
    s.add_argument("name")
    s.add_argument("--executor", required=True)
    s.add_argument("--socket", help="the socket to bind through: the admin or the bind socket")
    s.set_defaults(fn=_ledger_verb(_ledger_bind))
    s = ledger_p.add_parser("unbind", help="clear the executor a source's next runs record")
    s.add_argument("name")
    s.add_argument("--socket", help="the socket to unbind through: the admin or the bind socket")
    s.set_defaults(fn=_ledger_verb(_ledger_unbind))
    s = ledger_p.add_parser("fleet", help="active runs of every source")
    s.set_defaults(fn=_ledger_verb(_ledger_fleet))
    s = ledger_p.add_parser("metrics", help="metrics over every source's runs")
    s.add_argument("--repo", help="one repository's ledger, by its slug")
    s.add_argument(
        "--since",
        help="only runs still open, or ended at or after this ISO 8601 time with a UTC offset",
    )
    s.set_defaults(fn=_ledger_verb(_ledger_metrics))
    s = ledger_p.add_parser("log", help="render any source's run as a friction log")
    s.add_argument("--repo", required=True, help="the repository's slug")
    s.add_argument("--run", type=int, required=True)
    s.add_argument("--out")
    s.set_defaults(fn=_ledger_verb(_ledger_log))
    s = ledger_p.add_parser("import", help="bring an existing ledger in as one source")
    s.add_argument("file")
    s.add_argument("--source", required=True)
    s.set_defaults(fn=_ledger_verb(_ledger_import))
    return p


#: Verbs an agent's own `tdd` answers on a split machine. `docs` prints what shipped
#: with the binary, and `init` writes `tdd.toml` and the harness files into the agent's
#: own worktree; neither
#: touches the ledger. `ledger` is the host operator's, and talks to the ledger service
#: on this machine. Everything else is the runner's to do.
LOCAL_VERBS = {"docs", "init", "ledger"}


def _actor_for(
    split: runner_mod.RunnerConfig | None,
    agent_env: dict[str, str] | None,
    agent_umask: int | None = None,
) -> actor.LocalActor:
    """Who acts in the agent's territory for this invocation.

    The agent is `SUDO_USER`: sudo sets it itself, so a caller cannot name someone
    else. Installed on every invocation, because the suite drives `main` in-process.

    The runner never gets a `LocalActor`, even with no caller to act for. `_refusal`
    stops such an invocation before it spawns anything; if one ever got past it, a
    `sudo -u ""` that fails is the right outcome, and the agent's code running as the
    ledger's uid is the wrong one.
    """
    if split is not None and split.role == "runner":
        agent = os.environ.get("SUDO_USER", "")
        return actor.SudoActor(sudo=split.sudo, agent=agent, env=agent_env, umask=agent_umask)
    return actor.LocalActor()


def _refusal(split: runner_mod.RunnerConfig | None, args) -> Envelope | None:
    """A runner that was not called through sudo acts for nobody.

    It must not fall back to acting as itself: that would run the agent's suites, and
    the agent's git hooks, as the uid that owns the ledger. `runner` verbs are the
    exception, and so are `ledger` verbs: they are the operator's, touch no worktree
    and spawn nothing.
    """
    if split is None or split.role != "runner" or os.environ.get("SUDO_USER"):
        return None
    if args.command in ("runner", "ledger"):
        return None
    return failure(
        f"this is the split-mode runner ({split.user}) and no agent called it: run `tdd`"
        " from the agent's account, which reaches the runner through sudo",
        reason="no_agent",
    )


def _agent_context(args) -> tuple[dict[str, str] | None, int | None]:
    """The environment and umask the client sent. They only ever reach processes
    spawned as the agent, so nothing in them is trusted and nothing needs to be. A
    umask that is not a mode is ignored, as an older client's missing one is."""
    if not args.agent_context_stdin:
        return None, None
    context = json.loads(sys.stdin.read() or "{}")
    env = context.get("env")
    umask = context.get("umask")
    valid = type(umask) is int and 0 <= umask <= 0o777
    return (
        {str(k): str(v) for k, v in env.items()} if isinstance(env, dict) else None,
        umask if valid else None,
    )


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
        split = None
        args = build_parser().parse_args(argv)
        split = runner_mod.load()
        if split is not None and split.role == "client" and args.command not in LOCAL_VERBS:
            # Parsed first, so `--help`, `--version` and a mistyped verb never cost a
            # round trip; forwarded verbatim, so the runner parses exactly what we did.
            return runner_mod.forward(split, list(sys.argv[1:] if argv is None else argv))
        actor.install(_actor_for(split, *_agent_context(args)))
        envelope = _refusal(split, args) or args.fn(args)
    except PermissionError as exc:
        # Only the runner reads someone else's files. Anywhere else this is a bug, and
        # a traceback is the right report for one.
        if split is None or split.role != "runner":
            raise
        envelope = failure(
            f"the runner ({split.user}) cannot read {exc.filename}: split mode needs the"
            " worktree readable by that user (`chmod -R go+rX` it, or share a group)",
            reason="worktree_unreadable",
        )
    except wire.LedgerRefused as exc:
        envelope = failure(exc.error, reason="ledger_refused", refusal=exc.refusal)
    except wire.LedgerUnreachable as exc:
        # Fail closed: a guest whose ledger service is gone refuses the verb, and never
        # falls back to a ledger of its own.
        envelope = failure(str(exc), reason="ledger_unreachable")
    except (
        config_mod.ConfigError,
        gitutil.GitError,
        LedgerVersionError,
        runner_mod.RunnerConfigError,
        service_mod.ServiceConfigError,
    ) as exc:
        envelope = failure(str(exc))
    except SystemExit as exc:
        return int(exc.code or 0)
    return envelope.emit()


if __name__ == "__main__":
    raise SystemExit(main())
