"""Output envelope and the closed next_action verb set (R8.3a).

`verb` is the authority on control flow. `detail` is human-readable and explicitly
non-authoritative — skills and hooks dispatch on the verb, never on the prose.
Adding a verb is a specification change.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from enum import Enum

VERB_SET_VERSION = 1


class Verb(str, Enum):
    WRITE_TEST = "write_test"
    WRITE_IMPLEMENTATION = "write_implementation"
    CREATE_STUB = "create_stub"
    FIX_REGRESSION = "fix_regression"
    RUN_SENSITIVITY_CHECK = "run_sensitivity_check"
    NAME_TARGET_TEST = "name_target_test"
    REFACTOR_OR_ADVANCE = "refactor_or_advance"
    CONFIRM_CYCLE_APPLICABLE = "confirm_cycle_applicable"
    ANNOTATE_CYCLE = "annotate_cycle"
    RESOLVE_BLOCKER = "resolve_blocker"
    COMPLETE = "complete"
    BLOCKED = "blocked"


TERMINAL_VERBS = {Verb.COMPLETE, Verb.BLOCKED}


@dataclass
class NextAction:
    verb: Verb
    detail: str

    @property
    def terminal(self) -> bool:
        return self.verb in TERMINAL_VERBS

    def to_dict(self) -> dict:
        return {
            "verb": self.verb.value,
            "detail": self.detail,
            "terminal": self.terminal,
            "verb_set_version": VERB_SET_VERSION,
        }


@dataclass
class Envelope:
    ok: bool = True
    run: dict | None = None
    result: dict = field(default_factory=dict)
    next_action: NextAction | None = None
    error: str | None = None

    def to_dict(self) -> dict:
        out: dict = {"ok": self.ok}
        if self.error is not None:
            out["error"] = self.error
        out["run"] = self.run
        out["result"] = self.result
        out["next_action"] = self.next_action.to_dict() if self.next_action else None
        return out

    def emit(self) -> int:
        json.dump(self.to_dict(), sys.stdout, indent=2, default=str)
        sys.stdout.write("\n")
        return 0 if self.ok else 1


def failure(error: str, **result) -> Envelope:
    return Envelope(ok=False, error=error, result=result)
