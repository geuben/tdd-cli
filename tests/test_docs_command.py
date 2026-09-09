"""`tdd docs` — the documentation an agent can reach without a network.

The point of the command is that the docs it prints are the docs for *this*
binary. So these tests care less about the prose than about two invariants: every
topic resolves to a file that exists, and every topic is actually carried into the
wheel. A topic that only resolves in a source checkout is worse than no topic —
it works for every contributor and fails for every user.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

from conftest import run_cli, run_cli_text
from tddcli import docs

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_bare_docs_lists_every_topic_machine_readably(repo):
    envelope = run_cli(repo, "docs")
    assert envelope["ok"] is True
    listed = {t["name"] for t in envelope["result"]["topics"]}
    assert listed == {t.name for t in docs.TOPICS}
    assert all(t["summary"] for t in envelope["result"]["topics"])


def test_the_index_points_at_the_protocol_spec(repo):
    # The one topic an agent must read before driving a run.
    detail = run_cli(repo, "docs")["next_action"]["detail"]
    assert "tdd docs harness" in detail


def test_a_topic_prints_the_shipped_file_verbatim(repo):
    out = run_cli_text(repo, "docs", "harness")
    assert out == (REPO_ROOT / "docs" / "harness-integration.md").read_text()


def test_a_topic_prints_prose_not_an_envelope(repo):
    # An agent piping this to a reader must not have JSON stapled to the end.
    assert not run_cli_text(repo, "docs", "skill").rstrip().endswith("}")


def test_every_topic_is_readable(repo):
    for topic in docs.TOPICS:
        assert run_cli_text(repo, "docs", topic.name).strip(), topic.name


def test_an_unknown_topic_names_the_known_ones(repo):
    envelope = run_cli(repo, "docs", "nonsense")
    assert envelope["ok"] is False
    assert "'nonsense'" in envelope["error"]
    for topic in docs.TOPICS:
        assert topic.name in envelope["error"]


def test_every_topic_is_carried_into_the_wheel():
    """The drift guard: adding a topic without a force-include ships a broken command.

    Nothing else catches it — a source checkout resolves the file happily, so the
    whole suite passes while the published wheel raises FileNotFoundError.
    """
    pyproject = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text())
    included = pyproject["tool"]["hatch"]["build"]["targets"]["wheel"]["force-include"]
    for topic in docs.TOPICS:
        assert topic.path in included, f"{topic.name} is not force-included into the wheel"
        assert included[topic.path] == f"tddcli/_docs/{topic.path}"


def test_topic_paths_exist_in_the_repository():
    for topic in docs.TOPICS:
        assert (REPO_ROOT / topic.path).is_file(), topic.path


def test_the_packaged_copy_wins_over_the_repository_one(repo, monkeypatch, tmp_path):
    """An installed wheel must never read a checkout that happens to sit above it.

    Only the packaged copy is guaranteed to match the binary — which is the whole
    reason the docs are shipped rather than fetched.
    """
    packaged = tmp_path / "_docs" / "docs"
    packaged.mkdir(parents=True)
    (packaged / "harness-integration.md").write_text("packaged copy\n")
    monkeypatch.setattr(docs, "_PACKAGED", tmp_path / "_docs")

    assert run_cli_text(repo, "docs", "harness") == "packaged copy\n"


def test_a_missing_packaged_file_reports_a_packaging_fault(repo, monkeypatch):
    """Not a user error: there is no flag they could have passed instead."""
    monkeypatch.setattr(docs, "_SOURCE", Path("/nonexistent"))
    monkeypatch.setattr(docs, "_PACKAGED", Path("/nonexistent"))
    envelope = run_cli(repo, "docs", "harness")
    assert envelope["ok"] is False
    assert "packaging bug" in envelope["error"]


def test_help_points_at_the_docs_command(repo):
    # The discovery hop. An agent reads --help; it will not guess `tdd docs` exists.
    out = run_cli_text(repo, "--help")
    assert "tdd docs" in out
