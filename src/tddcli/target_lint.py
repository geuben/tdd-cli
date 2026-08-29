"""Static lint of declared targets: grammar and root-prefix rules."""
from __future__ import annotations

from pathlib import Path

from . import adapters
from .machine import Engine


def lint_cycles(cycles, cfg, worktree: Path) -> list[dict]:
    """Return findings for any cycle whose declared targets fail static lint.

    Grammar rule: each adapter's `lint_target_id` returns a problem string when the
    native id can never match a collected id (e.g. pytest target missing '::').

    Root-prefix rule: when a project's root != '.' and the target's path portion
    starts with '<root>/', flag it — unless the actual nested path (or its parent
    directory) exists in the worktree, which signals a genuine nested root layout.
    """
    findings = []
    for cycle in cycles:
        if cycle.kind == "refactor":
            continue
        for test_id in cycle.tests:
            qualified = Engine._qualify(cycle, test_id)
            project_name, native = qualified.split("::", 1)
            try:
                project = cfg.project(project_name)
            except Exception:
                continue
            adapter = adapters.build(project, worktree)

            lint_fn = getattr(adapter, "lint_target_id", lambda n: None)
            problem = lint_fn(native)
            if problem:
                findings.append({"cycle": cycle.ordinal, "project": project_name, "test": test_id, "problem": problem})
                continue

            path_fn = getattr(adapter, "target_path", lambda n: None)
            path_part = path_fn(native)
            if path_part is not None and project.root != ".":
                root_prefix = project.root + "/"
                if path_part.startswith(root_prefix):
                    stripped = path_part[len(root_prefix):]
                    nested = worktree / project.root / path_part
                    if not nested.exists() and not nested.parent.exists():
                        suffix = native[len(path_part):]
                        suggestion = stripped + suffix
                        findings.append({
                            "cycle": cycle.ordinal,
                            "project": project_name,
                            "test": test_id,
                            "problem": (
                                f"target path {path_part!r} duplicates the project root {project.root!r}; "
                                f"the collected id would be {stripped + suffix!r}. "
                                f"To register a genuinely nested path, create the directory first."
                            ),
                            "suggestion": suggestion,
                        })

    return findings
