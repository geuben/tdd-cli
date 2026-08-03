"""tdd.toml — the project registry and artifact graph (§7.1).

Roots are declared, never discovered by scanning for marker files (P5, R7.1): two
projects in one repo can share a marker, and directory-listing order must not decide
which suite runs.
"""

from __future__ import annotations

import hashlib
import tomllib
from dataclasses import dataclass, field
from fnmatch import fnmatch
from pathlib import Path

CONFIG_NAME = "tdd.toml"

#: Build output the tool must never author, regardless of the repository's .gitignore.
#: Without this, a run in a repo lacking a .gitignore commits __pycache__ alongside
#: the test it was asked to commit.
DEFAULT_IGNORES = (
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "node_modules",
    ".venv",
    "venv",
    "dist",
    "build",
    ".coverage",
    "htmlcov",
    ".DS_Store",
    ".tox",
    "*.pyc",
    "*.pyo",
    "*.egg-info",
)


class ConfigError(RuntimeError):
    pass


@dataclass
class Project:
    name: str
    root: str
    adapter: str
    test_paths: list[str] = field(default_factory=list)
    lint: list[str] = field(default_factory=list)
    typecheck: list[str] = field(default_factory=list)
    in_close_sweep: bool = True

    def owns(self, rel_path: str) -> bool:
        return rel_path == self.root or rel_path.startswith(self.root.rstrip("/") + "/")

    def relative_to_root(self, rel_path: str) -> str:
        prefix = self.root.rstrip("/") + "/"
        return rel_path[len(prefix):] if rel_path.startswith(prefix) else rel_path

    def is_test_file(self, rel_path: str) -> bool:
        """rel_path is relative to the worktree root."""
        if not self.owns(rel_path):
            return False
        inner = self.relative_to_root(rel_path)
        for pattern in self.test_paths:
            if pattern.endswith("/"):
                if inner.startswith(pattern):
                    return True
            elif fnmatch(inner, pattern) or fnmatch(rel_path, pattern):
                return True
            elif inner.startswith(pattern.rstrip("/") + "/"):
                return True
        return False


@dataclass
class Artifact:
    name: str
    path: str
    produced_by: str
    regenerate: str | None = None
    check: str | None = None
    consumed_by: list[str] = field(default_factory=list)
    generated: bool = False

    @property
    def upstream_artifact(self) -> str | None:
        if self.produced_by.startswith("artifact."):
            return self.produced_by.split(".", 1)[1]
        return None


@dataclass
class Config:
    worktree: Path
    projects: dict[str, Project]
    artifacts: dict[str, Artifact]
    ignores: tuple[str, ...] = DEFAULT_IGNORES

    def is_ignored(self, rel_path: str) -> bool:
        parts = Path(rel_path).parts
        for pattern in self.ignores:
            if any(fnmatch(part, pattern) for part in parts):
                return True
            if fnmatch(rel_path, pattern):
                return True
        return False

    def project(self, name: str) -> Project:
        if name not in self.projects:
            raise ConfigError(
                f"unknown project {name!r}; registered: {sorted(self.projects)}"
            )
        return self.projects[name]

    def owning_project(self, rel_path: str) -> Project | None:
        # Longest root wins, so nested roots resolve deterministically.
        best = None
        for proj in self.projects.values():
            if proj.owns(rel_path) and (best is None or len(proj.root) > len(best.root)):
                best = proj
        return best

    def is_generated(self, rel_path: str) -> bool:
        """R7.7 — generated output is excluded from authorship accounting."""
        for art in self.artifacts.values():
            if not art.generated:
                continue
            p = art.path.rstrip("/")
            if rel_path == p or rel_path.startswith(p + "/"):
                return True
        return False

    def close_sweep_projects(self, cycle_projects: list[str], touched: set[str]) -> list[str]:
        """R9.2 — the cycle's own projects, plus anything downstream of an artifact it touched."""
        names = {n for n in cycle_projects}
        for art in self.artifacts.values():
            if self._artifact_touched(art, touched):
                names.update(art.consumed_by)
        return [n for n in sorted(names) if self.projects[n].in_close_sweep]

    def _artifact_touched(self, art: Artifact, touched: set[str]) -> bool:
        producer = art.produced_by
        if producer.startswith("artifact."):
            upstream = self.artifacts.get(producer.split(".", 1)[1])
            return bool(upstream and self._artifact_touched(upstream, touched))
        proj = self.projects.get(producer)
        if proj is None:
            return False
        return any(proj.owns(p) for p in touched)

    def full_sweep_projects(self) -> list[str]:
        return sorted(self.projects)


def config_sha(worktree: Path) -> str:
    """Hash of tdd.toml as it stands in the working tree.

    The registry is deliberately a reviewed, branch-scoped file rather than ledger
    state — but that makes it editable mid-run, and one edit is load-bearing:
    widening `test_paths` to match implementation files would silently disable the
    RED-commit classification that detects implementation written during RED. The
    ledger pins this hash at run start so the drift surfaces.
    """
    path = worktree / CONFIG_NAME
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else ""


def find_config(start: Path) -> Path | None:
    cur = start.resolve()
    for candidate in [cur, *cur.parents]:
        if (candidate / CONFIG_NAME).is_file():
            return candidate / CONFIG_NAME
    return None


def load(worktree: Path) -> Config:
    path = worktree / CONFIG_NAME
    if not path.is_file():
        raise ConfigError(f"no {CONFIG_NAME} at {worktree}")
    raw = tomllib.loads(path.read_text())

    projects: dict[str, Project] = {}
    for name, body in (raw.get("project") or {}).items():
        if "root" not in body:
            raise ConfigError(f"project {name!r} has no root")
        if "adapter" not in body:
            raise ConfigError(f"project {name!r} has no adapter")
        projects[name] = Project(
            name=name,
            root=body["root"].rstrip("/"),
            adapter=body["adapter"],
            test_paths=body.get("test_paths", []),
            lint=body.get("lint", []),
            typecheck=body.get("typecheck", []),
            in_close_sweep=body.get("in_close_sweep", True),
        )

    artifacts: dict[str, Artifact] = {}
    for name, body in (raw.get("artifact") or {}).items():
        artifacts[name] = Artifact(
            name=name,
            path=body["path"],
            produced_by=body["produced_by"],
            regenerate=body.get("regenerate"),
            check=body.get("check"),
            consumed_by=body.get("consumed_by", []),
            generated=body.get("generated", False),
        )

    for art in artifacts.values():
        up = art.upstream_artifact
        if up is not None and up not in artifacts:
            raise ConfigError(f"artifact {art.name!r} names unknown upstream artifact {up!r}")
        if up is None and art.produced_by not in projects:
            raise ConfigError(
                f"artifact {art.name!r} produced_by unknown project {art.produced_by!r}"
            )
        for c in art.consumed_by:
            if c not in projects:
                raise ConfigError(f"artifact {art.name!r} consumed_by unknown project {c!r}")

    if not projects:
        raise ConfigError("no projects registered")
    extra = tuple(raw.get("ignore", []))
    return Config(
        worktree=worktree,
        projects=projects,
        artifacts=artifacts,
        ignores=DEFAULT_IGNORES + extra,
    )
