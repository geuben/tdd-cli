"""tdd.toml — the project registry and artifact graph (§7.1).

Roots are declared, never discovered by scanning for marker files (R7.1): two
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


def _pattern_matches(rel_path: str, pattern: str) -> bool:
    """`test_paths`-style matching: trailing-slash directory, glob, or bare
    directory prefix."""
    if pattern.endswith("/"):
        return rel_path.startswith(pattern)
    return fnmatch(rel_path, pattern) or rel_path.startswith(pattern.rstrip("/") + "/")


@dataclass
class Override:
    """An alternate suite for the files matching `pattern` (R7.13).

    Some tests intentionally live outside the project's default runner config —
    contract tests that need a live backend being the motivating case. Widening the
    default config to satisfy collection breaks CI (the default suite suddenly makes
    real network calls) and pollutes target adoption with tests from the other suite.
    Instead the registry declares the alternate command; collection and suite runs
    union the default suite with every override suite.

    `pattern` matches paths relative to the project root, like `test_paths`.
    `env` values may reference `${VAR}`, expanded from the environment at invocation.
    """

    pattern: str
    test_command: str
    collect_command: str | None = None
    env: dict[str, str] = field(default_factory=dict)
    lease: str | None = None
    timeout: int | None = None


@dataclass
class Project:
    name: str
    root: str
    adapter: str
    test_paths: list[str] = field(default_factory=list)
    lint: list[str] = field(default_factory=list)
    typecheck: list[str] = field(default_factory=list)
    in_close_sweep: bool = True
    #: The project's own suite command. Without this the tool runs its adapter's
    #: default invocation, which can differ from what the project actually runs —
    #: parallelism, plugins, markers — so the suite under TDD is not the suite the
    #: team trusts. The adapter appends only its reporting flags.
    test_command: str | None = None
    #: Per-file collection. Must not be parallelised: collection is cheap and xdist
    #: adds startup cost per file.
    collect_command: str | None = None
    #: Environment for the default suite's runs and collection, same semantics as
    #: an override's `env`: `${VAR}` references expand from the environment at
    #: invocation, so per-checkout values (a database port) stay out of the
    #: reviewed file. An override's `env` layers on top for its own suite.
    env: dict[str, str] = field(default_factory=dict)
    #: Alternate suites for files the default command cannot reach (R7.13).
    overrides: list[Override] = field(default_factory=list)
    #: Named machine-wide exclusive lease required before running this project's suite.
    lease: str | None = None
    #: Wall-clock timeout in seconds for this project's suite invocations.
    #: Overrides the 1800 s default. Doctor warns when a known baseline exceeds it.
    timeout: int | None = None

    def override_for(self, rel_path: str) -> Override | None:
        """First declared override whose pattern matches (path relative to the
        project root), so precedence is the reviewed file's order, never dict or
        filesystem order. Patterns follow `test_paths` semantics: a glob, a
        trailing-slash directory, or a bare directory prefix."""
        for ov in self.overrides:
            if _pattern_matches(rel_path, ov.pattern):
                return ov
        return None

    @property
    def test_patterns(self) -> list[str]:
        """`test_paths` plus every override pattern. An override's files are tests by
        declaration — the pattern exists to name the command that runs them — so they
        classify as tests for staging and discovery without being repeated in
        `test_paths`."""
        return self.test_paths + [ov.pattern for ov in self.overrides]

    def owns(self, rel_path: str) -> bool:
        if self.root == ".":  # single-project repo: the root is the worktree itself
            return True
        return rel_path == self.root or rel_path.startswith(self.root.rstrip("/") + "/")

    def relative_to_root(self, rel_path: str) -> str:
        prefix = self.root.rstrip("/") + "/"
        return rel_path[len(prefix) :] if rel_path.startswith(prefix) else rel_path

    def is_test_file(self, rel_path: str) -> bool:
        """rel_path is relative to the worktree root."""
        if not self.owns(rel_path):
            return False
        inner = self.relative_to_root(rel_path)
        for pattern in self.test_patterns:
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

    def owns(self, rel_path: str) -> bool:
        p = self.path.rstrip("/")
        return rel_path == p or rel_path.startswith(p + "/")


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
            raise ConfigError(f"unknown project {name!r}; registered: {sorted(self.projects)}")
        return self.projects[name]

    def owning_project(self, rel_path: str) -> Project | None:
        # Longest root wins, so nested roots resolve deterministically; a "." root
        # counts as length zero so any nested root beats the repo-root project.
        def depth(p: Project) -> int:
            return 0 if p.root == "." else len(p.root)

        best = None
        for proj in self.projects.values():
            if proj.owns(rel_path) and (best is None or depth(proj) > depth(best)):
                best = proj
        return best

    def is_generated(self, rel_path: str) -> bool:
        """R7.7 — generated output is excluded from authorship accounting."""
        return any(art.owns(rel_path) for art in self.artifacts.values() if art.generated)

    def artifact_chain(self, art: Artifact) -> list[Artifact]:
        """`art` plus every upstream artifact its regenerate hook may refresh."""
        chain, seen = [art], {art.name}
        while (up := chain[-1].upstream_artifact) is not None and up not in seen:
            chain.append(self.artifacts[up])
            seen.add(up)
        return chain

    def reachable_projects(self, declared: list[str]) -> list[str]:
        reachable = set(declared)
        changed = True
        while changed:
            changed = False
            for art in self.artifacts.values():
                producer = art.produced_by
                if producer in reachable:
                    for consumer in art.consumed_by:
                        if consumer not in reachable:
                            reachable.add(consumer)
                            changed = True
        return sorted(reachable)

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


def _load_overrides(project: str, raw: list) -> list[Override]:
    overrides: list[Override] = []
    for i, body in enumerate(raw, start=1):
        if not isinstance(body, dict):
            raise ConfigError(
                f"project {project!r} override #{i} must be a table ([[project.<name>.override]])"
            )
        if "pattern" not in body:
            raise ConfigError(f"project {project!r} override #{i} has no pattern")
        if "test_command" not in body:
            raise ConfigError(
                f"project {project!r} override {body['pattern']!r} has no test_command"
            )
        env = body.get("env", {})
        if not isinstance(env, dict) or not all(isinstance(v, str) for v in env.values()):
            raise ConfigError(
                f"project {project!r} override {body['pattern']!r}: env must be a"
                " table of string values"
            )
        timeout = body.get("timeout")
        if timeout is not None and not isinstance(timeout, int):
            raise ConfigError(
                f"project {project!r} override {body['pattern']!r}: timeout must be an integer"
            )
        overrides.append(
            Override(
                pattern=body["pattern"],
                test_command=body["test_command"],
                collect_command=body.get("collect_command"),
                env=env,
                lease=body.get("lease"),
                timeout=timeout,
            )
        )
    return overrides


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
        env = body.get("env", {})
        if not isinstance(env, dict) or not all(isinstance(v, str) for v in env.values()):
            raise ConfigError(f"project {name!r}: env must be a table of string values")
        timeout = body.get("timeout")
        if timeout is not None and not isinstance(timeout, int):
            raise ConfigError(f"project {name!r}: timeout must be an integer")
        projects[name] = Project(
            name=name,
            root=body["root"].rstrip("/"),
            adapter=body["adapter"],
            test_paths=body.get("test_paths", []),
            lint=body.get("lint", []),
            typecheck=body.get("typecheck", []),
            in_close_sweep=body.get("in_close_sweep", True),
            test_command=body.get("test_command"),
            collect_command=body.get("collect_command"),
            env=env,
            overrides=_load_overrides(name, body.get("override", [])),
            lease=body.get("lease"),
            timeout=timeout,
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
