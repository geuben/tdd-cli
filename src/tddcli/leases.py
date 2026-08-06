"""Machine-wide test-worker budget.

Several agents run tdd-cli concurrently on one machine, each in its own worktree.
With no coordination each had to pin its suite to `-n 1` — the only setting that
never oversubscribes the box — which serialises every suite even when the agent is
alone. This module gives each in-flight suite invocation an even share of the
machine's cores instead: a lease file per invocation in a directory shared across
worktrees, `workers = max(1, cores // live_leases)`.

Deliberate properties:

* The split is computed once, at lease acquisition. An agent that arrives mid-run
  gets the smaller share immediately; the earlier agent's share corrects on its
  next invocation. Suites are short relative to a run, so the imbalance is
  transient and never oversubscribes by more than one suite's worth.
* No lock file. Each lease is its own uniquely-named file, created before
  counting, so two simultaneous arrivals each see the other. The remaining race
  (counting before the other's create lands) costs one transiently generous
  split, not a corrupted state.
* Stale leases must not throttle a machine forever: a lease whose pid is dead is
  swept, and so is one older than STALE_AFTER_S — a suite invocation cannot
  legitimately outlive run_command's timeout, so twice that bounds a live lease.
"""

from __future__ import annotations

import contextlib
import json
import os
import time
import uuid
from collections.abc import Iterator
from pathlib import Path

LEASE_DIR_ENV = "TDD_LEASE_DIR"
CORE_BUDGET_ENV = "TDD_CORE_BUDGET"

#: run_command's timeout is 1800s; no live suite invocation can be older than that.
STALE_AFTER_S = 3600


def lease_dir() -> Path:
    env = os.environ.get(LEASE_DIR_ENV)
    if env:
        return Path(env)
    return Path.home() / ".cache" / "tdd-cli" / "leases"


def _total_cores() -> int:
    """CORE_BUDGET lets an operator reserve headroom (agents themselves need CPU)."""
    with contextlib.suppress(ValueError):
        budget = int(os.environ.get(CORE_BUDGET_ENV, "0"))
        if budget > 0:
            return budget
    return os.cpu_count() or 1


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True  # exists, owned by someone else
    return True


def _is_live(path: Path) -> bool:
    try:
        if time.time() - path.stat().st_mtime > STALE_AFTER_S:
            return False
        payload = json.loads(path.read_text())
        pid = int(payload["pid"])
    except (OSError, ValueError, KeyError, json.JSONDecodeError):
        return False
    return _pid_alive(pid)


def _live_count(directory: Path) -> int:
    """Count live leases, sweeping the rest so a crash never throttles the machine."""
    live = 0
    for path in directory.glob("*.json"):
        if _is_live(path):
            live += 1
        else:
            with contextlib.suppress(OSError):
                path.unlink()
    return live


@contextlib.contextmanager
def worker_lease(total_cores: int | None = None) -> Iterator[int]:
    """Hold a lease for one suite invocation; yields the worker count to use."""
    directory = lease_dir()
    directory.mkdir(parents=True, exist_ok=True)
    total = total_cores or _total_cores()
    mine = directory / f"{os.getpid()}-{uuid.uuid4().hex}.json"
    mine.write_text(json.dumps({"pid": os.getpid(), "started_at": time.time()}))
    try:
        yield max(1, total // max(1, _live_count(directory)))
    finally:
        with contextlib.suppress(OSError):
            mine.unlink()
