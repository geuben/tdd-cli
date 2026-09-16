"""The documentation that ships with the installed binary.

An agent meeting this tool in a project it has never seen has to learn the loop
from somewhere. Fetching it from GitHub is both a network dependency at the least
reliable moment and a version hazard: `main`'s skill is written against `main`'s
`verb_set_version`, which need not be the one the installed `tdd` emits. Docs
carried inside the wheel are, by construction, the docs for this binary.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

#: Where the wheel puts them (see `tool.hatch.build.targets.wheel.force-include`).
_PACKAGED = Path(__file__).parent / "_docs"

#: Where they live in a source checkout, which is what an editable install sees.
_SOURCE = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Topic:
    name: str
    #: Path relative to the repository root — and, verbatim, inside `_docs`.
    path: str
    summary: str

    def resolve(self) -> Path:
        """The readable copy, preferring the packaged one.

        A source checkout has no `_docs`; an installed wheel has no repository
        above it. Exactly one of these exists in any given installation.
        """
        packaged = _PACKAGED / self.path
        return packaged if packaged.is_file() else _SOURCE / self.path


TOPICS: tuple[Topic, ...] = (
    Topic(
        "harness",
        "docs/harness-integration.md",
        "the envelope, the verb set, and the rules a driving skill must obey",
    ),
    Topic(
        "skill",
        "examples/skills/tdd-drive/SKILL.md",
        "a complete driving skill for Claude Code — copy it into .claude/skills/",
    ),
    Topic(
        "handoff",
        "examples/skills/tdd-handoff/SKILL.md",
        "the planning-side skill: harden a draft plan and author its contract",
    ),
    Topic(
        "hooks",
        "examples/claude-code-hooks/README.md",
        "the Stop and Bash hooks that keep an agent inside the loop",
    ),
    Topic(
        "plan",
        "examples/plan.md",
        "an annotated example plan contract",
    ),
    Topic(
        "readme",
        "README.md",
        "configuration, adapters, baselines, and the full command surface",
    ),
)

BY_NAME = {topic.name: topic for topic in TOPICS}


def read(name: str) -> str:
    """The text of one topic.

    Raises `FileNotFoundError` if the installation is missing it — a packaging
    fault, not a user error, and it should read like one.
    """
    topic = BY_NAME[name]
    path = topic.resolve()
    if not path.is_file():
        raise FileNotFoundError(
            f"{topic.path} is missing from this installation of tdd-cli."
            " Read it at https://github.com/geuben/tdd-cli instead, and please"
            " report the packaging bug."
        )
    return path.read_text()
