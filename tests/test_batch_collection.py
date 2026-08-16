"""Collection asks the runner once, not once per file (issue #27).

Measured on a real repo: 313 per-file subprocesses cost 402s, 77% of a whole
`run start`, while *running* all the tests cost 117s. The floor per invocation
was 1.08s — the environment manager resolving plus the runner booting, paid
again per file. A single file's tests enumerate in milliseconds.

Both adapters already had a whole-suite probe (`collectable()`); collection now
uses that shape and keeps the per-file loop for the case it exists to serve.

The rule that makes this safe: **a file the batch does not account for gets
exactly the old per-file treatment.** Batch fails, batch is empty, batch skips a
file the registry declares — each falls through to the loop, so the collected set
can only match or improve on the old one, never silently shrink (R10.3/R10.4).
"""

from __future__ import annotations

from pathlib import Path

from conftest import run_cli, write_plan
from tddcli import adapters
from tddcli import config as config_mod


def _adapter(repo: Path, project: str = "backend"):
    return adapters.build(config_mod.load(repo).project(project), repo)


def _counting(monkeypatch, module=None):
    """Wrap the real `run_command`, recording every command it is asked to run."""
    seen: list[str] = []
    real = adapters.base.run_command

    def wrapper(command, cwd, timeout=1800, extra_env=None, label=None):
        seen.append(command)
        return real(command, cwd, timeout=timeout, extra_env=extra_env, label=label)

    monkeypatch.setattr(module or adapters.base, "run_command", wrapper)
    return seen


def _write_tests(repo: Path, n: int) -> None:
    for i in range(n):
        (repo / "backend" / "tests" / f"test_gen{i}.py").write_text(
            f"def test_gen{i}():\n    assert True\n"
        )


def test_a_healthy_project_is_collected_in_one_invocation(repo, monkeypatch):
    """The whole point: cost stops scaling with file count."""
    _write_tests(repo, 6)
    seen = _counting(monkeypatch, adapters.pytest_adapter)

    collected = _adapter(repo).collect()

    assert len(seen) == 1, seen
    assert len(collected.tests) == 7, collected.tests   # 6 generated + test_smoke
    assert collected.failed_files == {}


def test_the_batch_finds_the_same_tests_the_per_file_loop_would(repo, monkeypatch):
    """Equivalence is the whole risk of this change: batch enumeration uses the
    runner's own discovery, the per-file loop uses `test_paths` globs."""
    _write_tests(repo, 4)
    adapter = _adapter(repo)

    batched = adapter.collect().tests
    per_file = adapter._collect_per_file(
        {str(p.relative_to(adapter.root)) for p in adapter._test_files()},
        adapters.base.Collection(),
    ).tests

    assert batched == per_file, batched ^ per_file


def test_a_file_the_batch_never_reported_is_collected_individually(repo, monkeypatch):
    """A file matching `test_paths` that the runner's config excludes must not
    vanish from the set — a quietly smaller baseline is worse than a slow one."""
    _write_tests(repo, 3)
    adapter = _adapter(repo)
    real = adapters.base.run_command
    seen: list[str] = []

    def hide_one(command, cwd, timeout=1800, extra_env=None, label=None):
        seen.append(command)
        code, out, err = real(command, cwd, timeout=timeout, extra_env=extra_env, label=label)
        if "test_gen1.py" not in command:      # the batch "forgets" this file
            out = "\n".join(
                line for line in out.splitlines() if "test_gen1.py" not in line
            )
        return code, out, err

    monkeypatch.setattr(adapters.pytest_adapter, "run_command", hide_one)
    collected = adapter.collect()

    assert any("test_gen1.py" in t for t in collected.tests), collected.tests
    # Exactly one rescue invocation, naming that file — not a whole re-sweep.
    per_file = [c for c in seen if "test_gen1.py" in c]
    assert len(per_file) == 1, seen


def test_a_failing_batch_falls_back_to_per_file_attribution(repo_broken):
    """R10.3's purpose, preserved: one uncollectable module must not destroy the
    set, and the failure must name the file it came from."""
    adapter = _adapter(repo_broken, "verify")
    collected = adapter.collect()

    assert collected.failed_files, "a broken module must be attributed"
    assert any("test_v.py" in name for name in collected.failed_files), collected.failed_files


def test_one_broken_file_does_not_lose_its_healthy_neighbours(repo_broken):
    """The batch fails wholesale, so the fallback has to recover everything else."""
    (repo_broken / "verify" / "tests" / "test_ok.py").write_text(
        "def test_ok():\n    assert True\n"
    )
    collected = _adapter(repo_broken, "verify").collect()

    assert any("test_ok.py" in t for t in collected.tests), collected.tests
    assert any("test_v.py" in f for f in collected.failed_files), collected.failed_files


def test_override_files_are_collected_by_their_own_suite(repo, monkeypatch):
    """R7.13: an override's files are enumerated with the override's command and
    env, so batching must stay one invocation *per declared suite*."""
    (repo / "backend" / "contract").mkdir()
    (repo / "backend" / "contract" / "test_api.py").write_text(
        "def test_ping():\n    assert True\n"
    )
    (repo / "tdd.toml").write_text(
        "[project.backend]\n"
        'root       = "backend"\n'
        'adapter    = "pytest"\n'
        'test_paths = ["tests/"]\n'
        'test_command = "pytest tests"\n'
        "[[project.backend.override]]\n"
        'pattern      = "contract/"\n'
        'test_command = "pytest contract"\n'
    )
    seen = _counting(monkeypatch, adapters.pytest_adapter)

    collected = _adapter(repo).collect()

    assert len(seen) == 2, seen          # default suite + override suite, no per-file
    assert any("contract/test_api.py" in t for t in collected.tests), collected.tests


def test_partial_output_from_a_failed_batch_is_not_trusted(repo, monkeypatch):
    """A runner that aborts mid-collection still prints what it reached. Accepting
    that would take a file's *incomplete* test list as final — and reconciliation
    could not save it, because the file was mentioned. Every file is re-collected
    instead, which is the old cost only in the case that was already broken."""
    _write_tests(repo, 3)
    adapter = _adapter(repo)
    real = adapters.base.run_command
    seen: list[str] = []

    def failing_batch(command, cwd, timeout=1800, extra_env=None, label=None):
        seen.append(command)
        if "test_gen" not in command and "test_smoke" not in command:
            # whole-suite invocation: aborts, having reached one file
            return 1, "tests/test_gen0.py::test_gen0\n", "INTERNALERROR"
        return real(command, cwd, timeout=timeout, extra_env=extra_env, label=label)

    monkeypatch.setattr(adapters.pytest_adapter, "run_command", failing_batch)
    collected = adapter.collect()

    assert any("test_gen0.py" in c for c in seen[1:]), seen
    assert len(collected.tests) == 4, collected.tests   # 3 generated + test_smoke


def test_vitest_partial_output_from_a_failed_batch_is_not_trusted(repo_multi, monkeypatch):
    """Same rule for the vitest adapter, whose listing has no exit-code-free way to
    tell a complete run from an aborted one."""
    (repo_multi / "frontend" / "a.test.ts").write_text("")
    (repo_multi / "frontend" / "b.test.ts").write_text("")
    adapter = _adapter(repo_multi, "frontend")
    seen: list[str] = []

    def failing_batch(command, cwd, timeout=1800, extra_env=None, label=None):
        seen.append(command)
        if command.endswith("list"):                       # whole-suite invocation
            return 1, "a.test.ts > alpha\n", "crashed"
        return 0, f"{command.rsplit(' ', 1)[1]} > rescued", ""

    monkeypatch.setattr(adapters.vitest_adapter, "run_command", failing_batch)
    collected = adapter.collect()

    assert collected.tests == {
        "frontend::a.test.ts > rescued", "frontend::b.test.ts > rescued",
    }, collected.tests


def test_vitest_batch_attributes_each_id_to_its_own_file(repo_multi, monkeypatch):
    """`_parse_list_output` pinned every id to one path, which is right per-file
    and wrong for a whole-suite listing."""
    (repo_multi / "frontend" / "a.test.ts").write_text(
        "import {test, expect} from 'vitest'\ntest('alpha', () => expect(1).toBe(1))\n"
    )
    (repo_multi / "frontend" / "b.test.ts").write_text(
        "import {test, expect} from 'vitest'\ntest('beta', () => expect(1).toBe(1))\n"
    )
    adapter = _adapter(repo_multi, "frontend")
    monkeypatch.setattr(
        adapters.vitest_adapter, "run_command",
        lambda command, cwd, timeout=1800, extra_env=None, label=None: (
            0, "a.test.ts > alpha\nb.test.ts > beta\n", ""
        ),
    )
    collected = adapter.collect()

    assert collected.tests == {"frontend::a.test.ts > alpha", "frontend::b.test.ts > beta"}


def test_run_start_still_reports_the_same_baseline(repo, monkeypatch):
    """End to end, through the command that pays for this."""
    _write_tests(repo, 3)
    plan = write_plan(repo, """---
cycles:
  - n: 1
    project: backend
    title: "adding two numbers"
    test: "tests/test_add.py::test_add_two_numbers"
    commit_red: "test: adding"
    commit_green: "feat: add"
---
# Plan
""")
    assert run_cli(repo, "plan", "register", plan)["ok"]
    out = run_cli(repo, "run", "start", "--plan", plan)
    assert out["ok"], out
    assert out["result"]["baselines"] == {"backend": 0}, out["result"]
