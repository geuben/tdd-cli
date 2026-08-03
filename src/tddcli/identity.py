"""Executor identity resolution (§5.1).

The harness exposes a session id but not the model, so the model is read from the
session transcript. Agents never supply identity by any path (R5.2) — the human
fallback exists for hosts where the transcript is unavailable.

All harness coupling lives in this one module (R5.1): a transcript format change
breaks here and nowhere else.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

TRANSCRIPT_ROOT = Path.home() / ".claude" / "projects"


@dataclass
class Executor:
    model: str
    session: str | None
    source: str          # transcript | human | unknown


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


def resolve(project_path: Path | None = None, human_label: str | None = None) -> Executor:
    session = os.environ.get("CLAUDE_CODE_SESSION_ID")
    if session:
        transcript = _find_transcript(session, project_path)
        if transcript is not None:
            model = _model_from_transcript(transcript)
            if model:
                return Executor(model=model, session=session, source="transcript")

    if human_label:
        return Executor(model=human_label, session=session, source="human")

    return Executor(model="unknown", session=session, source="unknown")
