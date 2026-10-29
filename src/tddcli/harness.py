"""The agent harnesses `tdd init --skill` can scaffold.

A closed set, unlike adapters: an adapter loads code, a harness is only data —
the shipped files to copy out and where they go. Copied, never referenced in
place, so a project commits no path into somebody's site-packages.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Scaffold:
    #: Repository-relative path of the shipped copy — and, verbatim, its path under `_docs`.
    source: str
    #: Worktree-relative path init writes it to.
    dest: str


@dataclass(frozen=True)
class Harness:
    name: str
    files: tuple[Scaffold, ...]
    #: The harness's settings file, written only when it does not exist.
    settings_path: str
    #: What that file holds when init writes it: the wiring for `files`' hooks.
    settings: dict = field(hash=False)


def _hook(script: str) -> dict:
    # `$CLAUDE_PROJECT_DIR` keeps the hook reachable after the agent `cd`s.
    return {"type": "command", "command": f'python3 "$CLAUDE_PROJECT_DIR/{script}"'}


HARNESSES: dict[str, Harness] = {
    "claude-code": Harness(
        "claude-code",
        (
            Scaffold("examples/skills/tdd-drive/SKILL.md", ".claude/skills/tdd-drive/SKILL.md"),
            Scaffold("examples/claude-code-hooks/stop_hook.py", ".claude/hooks/tdd_stop_hook.py"),
            Scaffold("examples/claude-code-hooks/bash_hook.py", ".claude/hooks/tdd_bash_hook.py"),
        ),
        ".claude/settings.json",
        {
            "hooks": {
                "Stop": [{"hooks": [_hook(".claude/hooks/tdd_stop_hook.py")]}],
                "PreToolUse": [
                    {"matcher": "Bash", "hooks": [_hook(".claude/hooks/tdd_bash_hook.py")]}
                ],
            }
        },
    ),
}
