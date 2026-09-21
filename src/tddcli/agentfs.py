"""File operations a split-mode runner performs as the agent.

The runner's uid cannot write into the agent's worktree, nor read the mode-700 temp
directories the agent's tools create, so `SudoActor` runs this module as the agent:

    python -m tddcli.agentfs <op> <path> [<path>]

It runs with the agent's privileges and no others, which is the point: it can do only
what the agent could already do. Standard library only — it must not pull the rest of
the package, and with it the ledger, into a process the agent controls.
"""

from __future__ import annotations

import base64
import shutil
import sys
import tempfile
from pathlib import Path

#: `read` of a file that is not there. Distinct from 1 so a crash is not read as "missing".
MISSING = 3


def main(argv: list[str]) -> int:
    op, args = argv[0], argv[1:]
    if op == "mkdtemp":
        sys.stdout.write(tempfile.mkdtemp(prefix=args[0]))
    elif op == "read":
        path = Path(args[0])
        if not path.is_file():
            return MISSING
        sys.stdout.write(path.read_text())
    elif op == "write":
        path = Path(args[0])
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(base64.b64decode(sys.stdin.read()))
    elif op == "unlink":
        Path(args[0]).unlink(missing_ok=True)
    elif op == "rmtree":
        shutil.rmtree(args[0], ignore_errors=True)
    elif op == "symlink":
        dst = Path(args[1])
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.symlink_to(args[0])
    else:
        sys.stderr.write(f"agentfs: unknown operation {op!r}\n")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
