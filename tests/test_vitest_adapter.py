"""vitest adapter parsing, pinned against real vitest 4.1.0 output.

Found live: `vitest list` ignores `--reporter=json` and emits plain text, so
collection returned zero tests for a 45-suite project — and because the exit code
was 0, nothing was recorded as failed. A silent empty collection disables target
adoption and test-weakening detection without any signal.
"""

from __future__ import annotations

from pathlib import Path

from tddcli import config as config_mod
from tddcli.adapters.vitest_adapter import VitestAdapter

TOML = """
[project.frontend]
root       = "frontend"
adapter    = "vitest"
test_paths = ["**/*.test.ts", "**/*.test.tsx"]
"""

# Verbatim from `npx vitest list contexts/__tests__/AuthContext.test.tsx`
LIST_OUTPUT = """\
contexts/__tests__/AuthContext.test.tsx > initial load — no stored token > starts loading then becomes unauthenticated
contexts/__tests__/AuthContext.test.tsx > initial load — valid stored token > restores session from stored token
contexts/__tests__/AuthContext.test.tsx > logout > clears the stored token
"""


def adapter_for(tmp_path: Path) -> VitestAdapter:
    (tmp_path / "tdd.toml").write_text(TOML)
    (tmp_path / "frontend").mkdir()
    cfg = config_mod.load(tmp_path)
    return VitestAdapter(cfg.project("frontend"), tmp_path)


def test_list_output_is_parsed_into_ids(tmp_path):
    adapter = adapter_for(tmp_path)
    path = tmp_path / "frontend" / "contexts" / "__tests__" / "AuthContext.test.tsx"
    ids = adapter._parse_list_output(LIST_OUTPUT, path)
    assert len(ids) == 3


def test_parsed_ids_match_the_form_run_produces(tmp_path):
    """`list` joins with ' > '; `run` joins with a space. They must agree."""
    adapter = adapter_for(tmp_path)
    path = tmp_path / "frontend" / "contexts" / "__tests__" / "AuthContext.test.tsx"

    from_list = adapter._parse_list_output(LIST_OUTPUT, path)
    # The id `run()` builds for the same test, from vitest's fullName.
    from_run = adapter._id_for(
        str(path),
        "initial load — no stored token starts loading then becomes unauthenticated",
    )
    assert from_run in from_list, sorted(from_list)


def test_ids_are_project_namespaced_and_worktree_relative(tmp_path):
    adapter = adapter_for(tmp_path)
    path = tmp_path / "frontend" / "contexts" / "__tests__" / "AuthContext.test.tsx"
    one = next(iter(adapter._parse_list_output(LIST_OUTPUT, path)))
    assert one.startswith("frontend::frontend/contexts/__tests__/AuthContext.test.tsx > ")


def test_arrows_are_not_left_in_the_name(tmp_path):
    adapter = adapter_for(tmp_path)
    path = tmp_path / "frontend" / "a.test.ts"
    for one in adapter._parse_list_output(LIST_OUTPUT, path):
        _, _, name = one.partition(" > ")
        assert " > " not in name, one


def test_lines_without_a_separator_are_ignored(tmp_path):
    adapter = adapter_for(tmp_path)
    path = tmp_path / "frontend" / "a.test.ts"
    noise = "RUN v4.1.0\n\nsome banner text\n" + LIST_OUTPUT
    assert len(adapter._parse_list_output(noise, path)) == 3
