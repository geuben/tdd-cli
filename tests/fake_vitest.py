"""A stand-in for vitest 4.1.11, run as `<python> fake_vitest.py list|run …` from a
project root, so the vitest adapter can be driven end to end without node.

Every `*.test.ts` under the cwd declares its cases one per line:

    case: <title> > <title> = pass | fail | listed | needs <root-relative path>

`needs X` passes exactly when `<cwd>/X` exists. A `listed` case is listed and never
reported by `run`: a collect/run disagreement no real runner produces on purpose.

- `list [--json] [<rel file>…]` prints `[core] <rel> > <titles joined " > ">` per
  case — a named vitest project — or, with `--json`, vitest's JSON listing.
- `run --reporter=json [<rel file>] [-t <pattern>]` prints vitest's JSON report,
  `-t` filtering with `re.search` on the space-joined fullName; exit 1 on a failure.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

CASE = re.compile(r"^case:\s*(?P<titles>.+?)\s*=\s*(?P<status>pass|fail|listed|needs\s+\S+)\s*$")


def _cases(root: Path, only: list[str]) -> list[tuple[str, list[str], str]]:
    found = []
    for path in sorted(root.rglob("*.test.ts")):
        if "node_modules" in path.parts:
            continue
        rel = path.relative_to(root).as_posix()
        if only and rel not in only:
            continue
        for line in path.read_text().splitlines():
            match = CASE.match(line.strip())
            if match:
                titles = [t.strip() for t in match["titles"].split(" > ")]
                found.append((rel, titles, match["status"]))
    return found


def _passes(root: Path, status: str) -> bool:
    if status.startswith("needs"):
        return (root / status.split(None, 1)[1]).exists()
    return status == "pass"


def main(argv: list[str]) -> int:
    root = Path.cwd()
    command, rest = argv[0], argv[1:]
    as_json = False
    pattern = None
    files: list[str] = []
    i = 0
    while i < len(rest):
        arg = rest[i]
        if arg == "--json":
            as_json = True
        elif arg.startswith("--reporter"):
            pass
        elif arg == "-t":
            i += 1
            pattern = rest[i]
        else:
            files.append(arg)
        i += 1

    cases = _cases(root, files)
    if command == "list":
        if as_json:
            print(
                json.dumps(
                    [
                        {
                            "name": " > ".join(titles),
                            "file": str(root / rel),
                            "projectName": "core",
                        }
                        for rel, titles, _ in cases
                    ]
                )
            )
        else:
            for rel, titles, _ in cases:
                print(f"[core] {rel} > {' > '.join(titles)}")
        return 0

    suites: dict[str, list[dict]] = {}
    for rel, titles, status in cases:
        if status == "listed":
            continue
        full_name = " ".join(titles)
        if pattern is not None and not re.search(pattern, full_name):
            continue
        ok = _passes(root, status)
        suites.setdefault(rel, []).append(
            {
                "fullName": full_name,
                "status": "passed" if ok else "failed",
                "failureMessages": [] if ok else [f"AssertionError: {full_name} failed"],
            }
        )
    failed = any(t["status"] == "failed" for ts in suites.values() for t in ts)
    report = {
        "duration": 5,
        "testResults": [
            {
                "name": str(root / rel),
                "status": "failed" if any(t["status"] == "failed" for t in ts) else "passed",
                "assertionResults": ts,
            }
            for rel, ts in suites.items()
        ],
    }
    print(json.dumps(report))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
