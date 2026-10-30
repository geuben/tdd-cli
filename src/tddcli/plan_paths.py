from __future__ import annotations

import os
from pathlib import Path

from .machine import Engine


def locate(adapter, project, native: str, scan_cache: dict) -> tuple[str | None, str]:
    """R7.14 — the repository-relative file of one native test id: `(path, "")`, or
    `(None, reason)` when it cannot be placed in exactly one file."""
    file_path = adapter.target_path(native)
    if file_path is None:
        if project.name not in scan_cache:
            scan_cache[project.name] = adapter.scan_target_paths()
        scan = scan_cache[project.name]
        if scan is None:
            return None, "no_path_in_id"
        if native not in scan:
            return None, "not_found_in_sources"
        if len(scan[native]) > 1:
            return None, "ambiguous_id"
        file_path = scan[native][0]
    return os.path.normpath(os.path.join(project.root, file_path)), ""


def resolve(contract, cfg, worktree: Path) -> dict:
    from . import adapters

    paths = []
    unresolved = []
    _scan_cache: dict[str, dict[str, list[str]] | None] = {}

    for cycle in contract.cycles:
        for field, ids in (("test", cycle.tests), ("modifies_tests", cycle.modifies_tests)):
            for test_id in ids:
                qualified = Engine._qualify(cycle, test_id)
                project_name, native = qualified.split("::", 1)
                project = cfg.project(project_name)
                adapter = adapters.build(project, worktree)
                path, reason = locate(adapter, project, native, _scan_cache)
                entry = {"cycle": cycle.ordinal, "field": field, "id": test_id}
                if path is None:
                    unresolved.append({**entry, "project": project_name, "reason": reason})
                else:
                    paths.append({**entry, "project": project_name, "path": path})

    return {"plan": contract.plan_path, "paths": paths, "unresolved": unresolved}


def render(result: dict) -> str:
    paths = result.get("paths", [])
    unresolved = result.get("unresolved", [])
    total = len(paths) + len(unresolved)
    lines = ["cycle  field  project  path"]
    for row in paths:
        lines.append(f"{row['cycle']}  {row['field']}  {row['project']}  {row['path']}")
    for row in unresolved:
        lines.append(f"— unresolved ({row['reason']}): {row['id']}")
    lines.append(f"{total} ids · {len(paths)} resolved · {len(unresolved)} unresolved")
    return "\n".join(lines) + "\n"
