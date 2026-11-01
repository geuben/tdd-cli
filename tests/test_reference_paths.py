"""A plan's reference_paths are read-only to its run: changing one blocks it (#235)."""

from __future__ import annotations

from tddcli.contract import ContractError, parse


def _contract_text(value: str | None) -> str:
    line = "" if value is None else f"reference_paths: {value}\n"
    return (
        "---\n"
        'cycles: [{n: 1, project: backend, test: "tests/test_a.py::test_a"}]\n'
        f"{line}"
        "---\n\n# Plan\n"
    )


def test_reference_paths_parse_as_a_list_of_strings_or_fail():
    cases = {
        "absent": None,
        "list": '["backend/tests/expected/out.txt", "docs/ref.bin"]',
        "string": '"docs/ref.bin"',
        "number": "[1]",
        "mapping": "{a: b}",
    }
    seen: dict[str, object] = {}
    for name, value in cases.items():
        try:
            seen[name] = parse(_contract_text(value), "tasks/plan.md").reference_paths
        except ContractError as exc:
            seen[name] = str(exc)
    assert seen == {
        "absent": [],
        "list": ["backend/tests/expected/out.txt", "docs/ref.bin"],
        "string": "reference_paths must be a list of strings",
        "number": "reference_paths must be a list of strings",
        "mapping": "reference_paths must be a list of strings",
    }
