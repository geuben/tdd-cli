from __future__ import annotations

import os
from pathlib import Path

from .machine import Engine


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
                file_path = adapter.target_path(native)
                if file_path is None:
                    if project_name not in _scan_cache:
                        _scan_cache[project_name] = adapter.scan_target_paths()
                    scan = _scan_cache[project_name]
                    if scan is None:
                        reason = "no_path_in_id"
                    elif native not in scan:
                        reason = "not_found_in_sources"
                    elif len(scan[native]) > 1:
                        reason = "ambiguous_id"
                    else:
                        joined = os.path.normpath(os.path.join(project.root, scan[native][0]))
                        paths.append(
                            {
                                "cycle": cycle.ordinal,
                                "field": field,
                                "id": test_id,
                                "project": project_name,
                                "path": joined,
                            }
                        )
                        continue
                    unresolved.append(
                        {
                            "cycle": cycle.ordinal,
                            "field": field,
                            "id": test_id,
                            "project": project_name,
                            "reason": reason,
                        }
                    )
                else:
                    joined = os.path.normpath(os.path.join(project.root, file_path))
                    paths.append(
                        {
                            "cycle": cycle.ordinal,
                            "field": field,
                            "id": test_id,
                            "project": project_name,
                            "path": joined,
                        }
                    )

    return {"plan": contract.plan_path, "paths": paths, "unresolved": unresolved}
