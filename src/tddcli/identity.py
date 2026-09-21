"""Executor identity resolution (§5.1).

The harness exposes a session id but not the model, so the model is read from the
session transcript. Agents never supply identity by any path (R5.2) — the human
fallback exists for hosts where the transcript is unavailable.

Known limit: an in-process subagent inherits its parent's CLAUDE_CODE_SESSION_ID and
writes no transcript under TRANSCRIPT_ROOT, so a run it starts resolves to the
parent's model. Model comparisons require executors in top-level sessions.

All harness coupling lives in this one module (R5.1): a transcript format change
breaks here and nowhere else.
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

from . import actor, runner

TRANSCRIPT_ROOT = Path.home() / ".claude" / "projects"


@dataclass
class Executor:
    model: str
    session: str | None
    source: str  # transcript | human | declared | unknown | operator | claimed
    reason: str | None = None


def _slug(path: Path) -> str:
    return str(path).replace(os.sep, "-")


def _find_transcript(session_id: str, project_path: Path | None) -> Path | None:
    candidates: list[Path] = []
    if project_path is not None:
        scoped = TRANSCRIPT_ROOT / _slug(project_path) / f"{session_id}.jsonl"
        candidates.append(scoped)
    if TRANSCRIPT_ROOT.is_dir():
        candidates.extend(TRANSCRIPT_ROOT.glob(f"*/{session_id}.jsonl"))
    for c in candidates:
        if c.is_file():
            return c
    return None


def _model_from_transcript(path: Path) -> str | None:
    """Last model wins — a session may switch models mid-run."""
    found = None
    try:
        with path.open() as fh:
            for line in fh:
                line = line.strip()
                if not line or '"model"' not in line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                model = rec.get("model") or (rec.get("message") or {}).get("model")
                if isinstance(model, str) and model:
                    found = model
    except OSError:
        return None
    return found


def _operator_assigned(split: runner.RunnerConfig) -> Executor | None:
    """The model the runner's operator assigned to the calling account.

    It is the one identity an agent cannot write: the map lives in the runner's config,
    and the account is `SUDO_USER`, which sudo sets itself.
    """
    model = split.executors.get(os.environ.get("SUDO_USER", ""))
    return Executor(model=model, session=None, source="operator") if model else None


def _claimed(project_path: Path | None, human_label: str | None) -> Executor:
    """What the agent says it is, resolved on the agent's side and labelled as a claim.

    The session id, the transcript and `TDD_EXECUTOR_MODEL` are all the agent's to
    write, and none of them is in the runner's environment or home anyway. So the
    ordinary resolution runs as the agent, and whatever it finds is recorded as
    `claimed`: a consumer comparing models can leave it out.
    """
    argv = [sys.executable, "-m", "tddcli.identity", str(project_path or ""), human_label or ""]
    proc = actor.current().run_argv(argv)
    try:
        found = Executor(**json.loads(proc.stdout))
    except (json.JSONDecodeError, TypeError):
        return Executor(
            model="unknown",
            session=None,
            source="unknown",
            reason=f"the agent-side resolver failed: {proc.stderr.strip()[:200]}",
        )
    if found.source == "unknown":
        return found
    return Executor(
        model=found.model,
        session=found.session,
        source="claimed",
        reason=f"resolved on the agent's side via {found.source}",
    )


def resolve(project_path: Path | None = None, human_label: str | None = None) -> Executor:
    split = runner.load()
    if split is not None and split.role == "runner":
        return _operator_assigned(split) or _claimed(project_path, human_label)
    return _resolve_locally(project_path, human_label)


def _resolve_locally(project_path: Path | None, human_label: str | None) -> Executor:
    session = os.environ.get("CLAUDE_CODE_SESSION_ID")

    declared = os.environ.get("TDD_EXECUTOR_MODEL")
    if declared:
        return Executor(model=declared, session=session, source="declared")

    reason: str | None = None
    if not session:
        reason = "CLAUDE_CODE_SESSION_ID is not set"
    else:
        transcript = _find_transcript(session, project_path)
        if transcript is None:
            reason = f"no transcript for session {session} under {TRANSCRIPT_ROOT}"
        else:
            model = _model_from_transcript(transcript)
            if model:
                return Executor(model=model, session=session, source="transcript")
            reason = f"no model records in transcript {transcript}"

    if human_label:
        return Executor(model=human_label, session=session, source="human")

    return Executor(model="unknown", session=session, source="unknown", reason=reason)


def main(argv: list[str]) -> int:
    """`python -m tddcli.identity <worktree> <label>`: the runner runs this as the agent.

    It resolves locally and never consults the runner config, so it cannot recurse.
    """
    project_path = Path(argv[0]) if argv and argv[0] else None
    human_label = argv[1] if len(argv) > 1 and argv[1] else None
    sys.stdout.write(json.dumps(asdict(_resolve_locally(project_path, human_label))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
