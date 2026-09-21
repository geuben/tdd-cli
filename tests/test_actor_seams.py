"""Everything the tool does in the agent's territory goes through one module.

Split mode (issue 142) runs `tdd` as a uid that must never execute the agent's code
as itself, nor write into the agent's worktree as itself. That holds only if there
is exactly one place that spawns and one place that writes, so these guards read the
source rather than exercise it: a call site added later fails here, not on the first
machine that is actually split.
"""

from __future__ import annotations

import re
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src" / "tddcli"

#: Code that spawns, not prose that mentions it: two modules say "subprocess" in a comment.
SPAWNS = re.compile(
    r"^\s*(import|from)\s+subprocess\b|\bsubprocess\.|\bos\.(system|popen|exec\w*|spawn\w*)\(",
    re.MULTILINE,
)


def _modules_matching(pattern: re.Pattern[str]) -> set[str]:
    return {
        str(path.relative_to(SRC))
        for path in SRC.rglob("*.py")
        if pattern.search(path.read_text())
    }


def test_only_the_actor_spawns_processes():
    assert _modules_matching(SPAWNS) == {"actor.py"}


WRITES = re.compile(
    r"\.write_text\(|\.write_bytes\(|\.unlink\(|rmtree\(|mkdtemp\(|TemporaryDirectory\("
    r"|symlink_to\(|\.mkdir\("
)

#: Leases and the ledger are the tool's own state: they stay the runner's.
OWN_STATE = {"actor.py", "agentfs.py", "leases.py", "ledger.py"}


def test_only_the_actor_writes_outside_the_tools_own_state():
    assert _modules_matching(WRITES) - OWN_STATE == set()
