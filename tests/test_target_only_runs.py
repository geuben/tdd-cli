"""Adapter runs with `target_only=True` (#148, PRD R9.1a).

pytest runs for real in `tmp_path`: whether a node id narrows the run is a fact
about pytest, not about our parsing. vitest's command is captured instead; its
`-t` semantics were probed against vitest 4.1.11 when the plan was written.
"""

from __future__ import annotations

from tddcli import config as config_mod
from tddcli.adapters.pytest_adapter import PytestAdapter

# A path-scoped test_command is deliberate: appending a node id to it would not
# narrow the run, so the target-only path must not be built on it.
PY_TOML = """
[project.backend]
root         = "backend"
adapter      = "pytest"
test_paths   = ["tests/"]
test_command = "pytest tests/"
"""


def _pytest(tmp_path, extra=""):
    (tmp_path / "tdd.toml").write_text(PY_TOML + extra)
    tests = tmp_path / "backend" / "tests"
    tests.mkdir(parents=True)
    (tests / "test_two.py").write_text(
        "def test_a():\n    assert False\n\n\ndef test_b():\n    assert False\n"
    )
    return PytestAdapter(config_mod.load(tmp_path).project("backend"), tmp_path)


def test_a_target_only_pytest_run_executes_only_the_target(tmp_path):
    a = _pytest(tmp_path)

    v = a.run("backend::tests/test_two.py::test_a", target_only=True)

    assert sorted(v.passed + v.failed) == ["backend::tests/test_two.py::test_a"]


def test_a_target_only_pytest_run_uses_the_owning_override(tmp_path):
    a = _pytest(
        tmp_path,
        extra=(
            "\n[[project.backend.override]]\n"
            'pattern      = "tests/special/"\n'
            'test_command = "pytest tests/special/"\n'
            'env          = { FLAG = "on" }\n'
        ),
    )
    special = tmp_path / "backend" / "tests" / "special"
    special.mkdir()
    (special / "test_flag.py").write_text(
        'import os\n\n\ndef test_flag():\n    assert os.environ.get("FLAG") == "on"\n'
    )

    v = a.run("backend::tests/special/test_flag.py::test_flag", target_only=True)

    assert v.target_outcome == "passed"


def test_a_target_only_pytest_run_reports_an_uncollectable_file_as_not_collected(tmp_path):
    a = _pytest(tmp_path)
    (tmp_path / "backend" / "tests" / "test_broken.py").write_text(
        "import nosuchmod\n\n\ndef test_c():\n    pass\n"
    )

    v = a.run("backend::tests/test_broken.py::test_c", target_only=True)

    assert v.target_outcome == "not_collected"
