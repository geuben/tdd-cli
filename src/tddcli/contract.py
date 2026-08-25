"""Plan contracts from YAML front-matter, hashed at the committed blob (§7.2).

The plan's *commit* is the contract, so a planning agent needs no integration with
this tool and an implementing agent cannot quietly move its own goalposts: editing
front-matter mid-run changes the blob and raises `plan_blob_changed` (R7.11).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from . import gitutil
from .config import Config

FENCE = "---"

STANDARD = "standard"
PIN = "pin"
CONTRACT = "contract"
REFACTOR = "refactor"


class ContractError(RuntimeError):
    """Malformed front-matter. Hard-fails registration (R7.10)."""


@dataclass
class DeclaredCycle:
    ordinal: int
    kind: str
    projects: list[str]
    tests: list[str]
    title: str = ""
    files: list[str] = field(default_factory=list)
    stub_expected: list[str] = field(default_factory=list)
    modifies_tests: list[str] = field(default_factory=list)
    commit_messages: dict[str, str] = field(default_factory=dict)
    meta: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "n": self.ordinal,
            "kind": self.kind,
            "projects": self.projects,
            "tests": self.tests,
            "title": self.title,
            "files": self.files,
            "stub_expected": self.stub_expected,
            "modifies_tests": self.modifies_tests,
            "commit_messages": self.commit_messages,
        }

    @staticmethod
    def from_dict(d: dict) -> "DeclaredCycle":
        return DeclaredCycle(
            ordinal=d["n"],
            kind=d["kind"],
            projects=d["projects"],
            tests=d["tests"],
            title=d.get("title", ""),
            files=d.get("files", []),
            stub_expected=d.get("stub_expected", []),
            modifies_tests=d.get("modifies_tests", []),
            commit_messages=d.get("commit_messages", {}),
        )


@dataclass
class PlanContract:
    plan_path: str
    status: str                      # declared | undeclared
    cycles: list[DeclaredCycle]
    annotation_keys: list[str]
    blob_sha: str | None = None
    commit_sha: str | None = None


def split_front_matter(text: str) -> str | None:
    """Return the raw YAML block, or None when there is no front-matter at all."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != FENCE:
        return None
    for i in range(1, len(lines)):
        if lines[i].strip() == FENCE:
            return "\n".join(lines[1:i])
    return None


def _as_list(value, field_name: str, ordinal: int) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list) and all(isinstance(v, str) for v in value):
        return list(value)
    raise ContractError(f"cycle {ordinal}: {field_name} must be a string or list of strings")


def parse_cycle(raw: dict, config: Config | None) -> DeclaredCycle:
    if not isinstance(raw, dict):
        raise ContractError(f"each cycle must be a mapping, got {type(raw).__name__}")
    if "n" not in raw:
        raise ContractError("every cycle needs an `n` ordinal")
    ordinal = raw["n"]
    if not isinstance(ordinal, int):
        raise ContractError(f"cycle ordinal must be an integer, got {ordinal!r}")

    flags = [
        name for name, key in (
            (PIN, "pin_cycle"),
            (CONTRACT, "contract_cycle"),
            (REFACTOR, "refactor_cycle"),
        ) if raw.get(key)
    ]
    if len(flags) > 1:
        raise ContractError(
            f"cycle {ordinal}: cycle kinds are exclusive, got {flags}"
        )
    kind = flags[0] if flags else STANDARD

    tests = _as_list(raw.get("tests") or raw.get("test"), "test", ordinal)
    projects = _as_list(raw.get("projects") or raw.get("project"), "project", ordinal)
    if not projects:
        raise ContractError(f"cycle {ordinal}: no project declared")

    # A refactor cycle changes structure without changing behaviour: existing tests are
    # the guard, so it has no target of its own and opens straight into refactor.
    if kind == REFACTOR and tests:
        raise ContractError(
            f"cycle {ordinal}: a refactor cycle declares no test — the existing suite"
            " is the guard. Use a pin cycle if new behaviour must be characterised first."
        )
    if kind != REFACTOR and not tests:
        raise ContractError(
            f"cycle {ordinal}: no test declared. Mark it `refactor_cycle: true` if it"
            " is behaviour-preserving with no new test."
        )

    if len(tests) > 1 and kind != CONTRACT:
        raise ContractError(
            f"cycle {ordinal}: {len(tests)} tests declared but this is not a contract cycle."
            " One behaviour per cycle (R9.8)."
        )
    if kind == CONTRACT and len(tests) < 2:
        raise ContractError(
            f"cycle {ordinal}: contract cycles must declare more than one target test"
        )

    if config is not None:
        for name in projects:
            if name not in config.projects:
                raise ContractError(
                    f"cycle {ordinal}: unknown project {name!r};"
                    f" registered: {sorted(config.projects)}"
                )

    commits = {}
    for phase_key in ("red", "green", "refactor", "pin"):
        msg = raw.get(f"commit_{phase_key}")
        if msg is not None:
            if not isinstance(msg, str):
                raise ContractError(f"cycle {ordinal}: commit_{phase_key} must be a string")
            commits[phase_key] = msg

    meta_raw = raw.get("meta")
    if meta_raw is not None and not isinstance(meta_raw, dict):
        raise ContractError(f"cycle {ordinal}: meta must be a mapping, got {type(meta_raw).__name__}")
    meta = dict(meta_raw) if meta_raw is not None else {}

    return DeclaredCycle(
        ordinal=ordinal,
        kind=kind,
        projects=projects,
        tests=tests,
        title=raw.get("title", ""),
        files=_as_list(raw.get("files"), "files", ordinal),
        stub_expected=_as_list(raw.get("stub_expected"), "stub_expected", ordinal),
        modifies_tests=_as_list(raw.get("modifies_tests"), "modifies_tests", ordinal),
        commit_messages=commits,
        meta=meta,
    )


def parse(text: str, plan_path: str, config: Config | None = None) -> PlanContract:
    """Absent front-matter is legitimate (R7.9); malformed front-matter is a defect (R7.10)."""
    block = split_front_matter(text)
    if block is None:
        return PlanContract(plan_path=plan_path, status="undeclared", cycles=[], annotation_keys=[])

    try:
        data = yaml.safe_load(block)
    except yaml.YAMLError as exc:
        raise ContractError(f"front-matter is not valid YAML: {exc}") from exc

    if not isinstance(data, dict):
        raise ContractError("front-matter must be a mapping")
    if "cycles" not in data:
        raise ContractError("front-matter present but declares no `cycles`")
    if not isinstance(data["cycles"], list) or not data["cycles"]:
        raise ContractError("`cycles` must be a non-empty list")

    cycles = [parse_cycle(c, config) for c in data["cycles"]]
    ordinals = [c.ordinal for c in cycles]
    if len(set(ordinals)) != len(ordinals):
        raise ContractError(f"duplicate cycle ordinals: {ordinals}")
    cycles.sort(key=lambda c: c.ordinal)

    keys = data.get("annotation_keys", [])
    if not isinstance(keys, list) or not all(isinstance(k, str) for k in keys):
        raise ContractError("annotation_keys must be a list of strings")

    return PlanContract(
        plan_path=plan_path,
        status="declared",
        cycles=cycles,
        annotation_keys=keys,
    )


def register(worktree: Path, plan_rel: str, config: Config | None) -> PlanContract:
    """Read the plan as committed — never the working-tree copy."""
    try:
        blob, commit = gitutil.blob_sha_at_head(worktree, plan_rel)
        text = gitutil.show_at_head(worktree, plan_rel)
    except gitutil.GitError as exc:
        raise ContractError(
            f"{plan_rel} must be committed before registration: {exc}"
        ) from exc
    contract = parse(text, plan_rel, config)
    contract.blob_sha = blob
    contract.commit_sha = commit
    return contract


def cycles_to_json(cycles: list[DeclaredCycle]) -> str:
    return json.dumps([c.to_dict() for c in cycles])


def cycles_from_json(blob: str) -> list[DeclaredCycle]:
    return [DeclaredCycle.from_dict(d) for d in json.loads(blob)]
