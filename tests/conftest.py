from __future__ import annotations

import os
import pwd
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(cwd), *args], capture_output=True, text=True, check=True
    ).stdout


@pytest.fixture(autouse=True)
def _isolated_lease_dir(tmp_path, monkeypatch):
    """Every suite invocation takes a machine-wide worker lease; keep the test
    suite's leases out of the developer's real ~/.cache/tdd-cli."""
    monkeypatch.setenv("TDD_LEASE_DIR", str(tmp_path / "worker-leases"))


@pytest.fixture(autouse=True)
def _pinned_executor_identity(monkeypatch):
    """A developer's shell resolves identity from its live Claude session; CI
    resolves nothing and every run logs executor_unknown. Pin a declared
    identity so both behave the same; the attribution tests delenv this to
    exercise the unknown paths."""
    monkeypatch.setenv("TDD_EXECUTOR_MODEL", "pytest-executor")


@pytest.fixture(autouse=True)
def _single_user_mode(tmp_path, monkeypatch):
    """A developer machine may itself be split (`/etc/tdd-cli/runner.toml`); the suite
    must never pick that up and start forwarding to a runner."""
    monkeypatch.setenv("TDD_RUNNER_CONFIG", str(tmp_path / "no-runner.toml"))
    for var in ("SUDO_USER", "SUDO_UID"):
        monkeypatch.delenv(var, raising=False)
    yield
    # `main` installs an actor process-wide and the suite drives the CLI in-process,
    # so a split-mode test would otherwise leave its actor behind for the next one.
    from tddcli import actor

    actor.install(actor.LocalActor())


#: A stand-in for sudo. It logs what it was asked, then runs the command as the same
#: uid — everything about split mode except the uid change itself. `SUDO_DENY` names
#: commands it refuses, which is how "the agent cannot" is reached without a second uid.
SUDO_SHIM = """\
#!/bin/sh
echo "MARK=$MARK $@" >> "$SUDO_LOG"
while [ "$1" != "--" ]; do shift; done; shift
case " $SUDO_DENY " in *" $(basename "$1") "*) exit 1;; esac
exec "$@"
"""


def current_user() -> str:
    return pwd.getpwuid(os.geteuid()).pw_name


@pytest.fixture
def sudo_shim(tmp_path, monkeypatch):
    shim = tmp_path / "bin" / "sudo"
    shim.parent.mkdir()
    shim.write_text(SUDO_SHIM)
    shim.chmod(0o755)
    log = tmp_path / "sudo.log"
    log.write_text("")
    monkeypatch.setenv("SUDO_LOG", str(log))
    return SimpleNamespace(path=shim, log=log, lines=lambda: log.read_text().splitlines())


@pytest.fixture
def split_runner(tmp_path, monkeypatch, sudo_shim):
    """This process is the runner, called through sudo by an agent.

    The agent is the current user, so every spawn the runner makes really executes:
    the whole split-mode path runs, short of the uid change.
    """
    home = tmp_path / "runner-ledgers"
    cfg = tmp_path / "runner.toml"
    cfg.write_text(
        f'[runner]\nuser = "{current_user()}"\ncommand = "tdd"\n'
        f'sudo = "{sudo_shim.path}"\nledger_home = "{home}"\n'
    )
    monkeypatch.setenv("TDD_RUNNER_CONFIG", str(cfg))
    monkeypatch.setenv("SUDO_USER", current_user())
    monkeypatch.setenv("SUDO_UID", str(os.geteuid()))
    return SimpleNamespace(config=cfg, ledger_home=home, shim=sudo_shim)


@pytest.fixture
def split_client(tmp_path, monkeypatch, sudo_shim):
    """This process is an agent's `tdd` on a split machine.

    `user = "root"` makes any non-root process a client. The runner's `command` is a
    stub that records what reached it, answers with a fixed envelope, and exits 3.
    """
    stub = tmp_path / "bin" / "tdd-stub"
    stub.write_text(
        "#!/bin/sh\n"
        f'echo "$@" > "{tmp_path}/stub.argv"\n'
        f'cat > "{tmp_path}/stub.stdin"\n'
        'echo \'{"ok": true, "stub": true}\'\n'
        "exit 3\n"
    )
    stub.chmod(0o755)
    cfg = tmp_path / "runner.toml"
    cfg.write_text(f'[runner]\nuser = "root"\ncommand = "{stub}"\nsudo = "{sudo_shim.path}"\n')
    monkeypatch.setenv("TDD_RUNNER_CONFIG", str(cfg))
    return SimpleNamespace(
        stub=stub,
        argv=tmp_path / "stub.argv",
        stdin=tmp_path / "stub.stdin",
        shim=sudo_shim,
    )


@pytest.fixture
def ledger_home(tmp_path, monkeypatch):
    home = tmp_path / "ledger-home"
    home.mkdir()
    monkeypatch.setenv("TDD_LEDGER_HOME", str(home))
    return home


@pytest.fixture
def repo(tmp_path, ledger_home):
    """A git repo with one Python project, wired for the pytest adapter."""
    root = tmp_path / "workspace"
    (root / "backend" / "tests").mkdir(parents=True)
    (root / "backend" / "app").mkdir(parents=True)

    (root / "tdd.toml").write_text(
        "[project.backend]\n"
        'root       = "backend"\n'
        'adapter    = "pytest"\n'
        'test_paths = ["tests/"]\n'
        "lint       = []\n"
        "typecheck  = []\n"
    )
    (root / "backend" / "app" / "__init__.py").write_text("")
    (root / "backend" / "tests" / "test_smoke.py").write_text(
        "def test_smoke():\n    assert True\n"
    )
    (root / "backend" / "conftest.py").write_text(
        "import sys, pathlib\nsys.path.insert(0, str(pathlib.Path(__file__).parent))\n"
    )
    (root / ".gitignore").write_text(
        ".pytest_cache/\n__pycache__/\n*.pyc\n.coverage\njsonreport*.json\n"
    )

    subprocess.run(["git", "init", "-q", str(root)], check=True)
    git(root, "config", "user.email", "test@example.com")
    git(root, "config", "user.name", "Test")
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "initial")
    return root


@pytest.fixture
def repo_multi(repo, ledger_home):
    """`repo` plus an empty vitest `frontend` (a `package.json`, no test files).

    Both projects are reachable from a plan that declares both, so `run start`
    probes both and reports `baselines: {backend: 0, frontend: 0}`.
    """
    (repo / "frontend").mkdir()
    (repo / "frontend" / "package.json").write_text('{"name": "frontend", "version": "1.0.0"}\n')
    (repo / "tdd.toml").write_text(
        "[project.backend]\n"
        'root       = "backend"\n'
        'adapter    = "pytest"\n'
        'test_paths = ["tests/"]\n'
        "lint       = []\n"
        "typecheck  = []\n"
        "\n"
        "[project.frontend]\n"
        'root       = "frontend"\n'
        'adapter    = "vitest"\n'
        'test_paths = ["**/*.test.ts", "**/*.test.tsx"]\n'
        "lint       = []\n"
        "typecheck  = []\n"
    )
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "add empty vitest frontend")
    return repo


@pytest.fixture
def repo_three(repo, ledger_home):
    """`repo` (backend) plus two extra pytest projects — `svc` and `other` — and an
    artifact `schema` produced_by `backend`, consumed_by `svc`.

    Under scoped baseline capture, `run start` with a plan declaring only `backend`
    probes `backend` and `svc` (reachable via the artifact edge) but skips `other`.
    """
    for name in ("svc", "other"):
        (repo / name / "tests").mkdir(parents=True)
        (repo / name / "tests" / "test_smoke.py").write_text("def test_smoke():\n    assert True\n")
    (repo / "backend" / "schema.json").write_text("{}")
    (repo / "tdd.toml").write_text(
        "[project.backend]\n"
        'root       = "backend"\n'
        'adapter    = "pytest"\n'
        'test_paths = ["tests/"]\n'
        "\n"
        "[project.svc]\n"
        'root       = "svc"\n'
        'adapter    = "pytest"\n'
        'test_paths = ["tests/"]\n'
        "\n"
        "[project.other]\n"
        'root       = "other"\n'
        'adapter    = "pytest"\n'
        'test_paths = ["tests/"]\n'
        "\n"
        "[artifact.schema]\n"
        'path        = "backend/schema.json"\n'
        'produced_by = "backend"\n'
        'consumed_by = ["svc"]\n'
        'regenerate  = "true"\n'
    )
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "add svc, other, schema artifact")
    return repo


@pytest.fixture
def repo_schema_other(repo, ledger_home):
    """`repo` (backend) plus `svc` and `other` projects; artifact `schema` produced_by
    `other`, consumed_by `svc`. Since the plan declares only `backend`, `svc` is
    un-baselined — `other` is not reachable from `backend` via the artifact graph.

    `svc` carries a pre-committed failing test; writing a file under `other/` during a
    run touches `schema`'s producer root, pulling un-baselined `svc` into the close sweep.
    """
    for name in ("svc", "other"):
        (repo / name / "tests").mkdir(parents=True)
    (repo / "svc" / "tests" / "test_svc.py").write_text("def test_svc_fails():\n    assert False\n")
    (repo / "other" / "tests" / "test_other.py").write_text("def test_other():\n    assert True\n")
    (repo / "other" / "schema.json").write_text("{}")
    (repo / "tdd.toml").write_text(
        "[project.backend]\n"
        'root       = "backend"\n'
        'adapter    = "pytest"\n'
        'test_paths = ["tests/"]\n'
        "\n"
        "[project.svc]\n"
        'root       = "svc"\n'
        'adapter    = "pytest"\n'
        'test_paths = ["tests/"]\n'
        "\n"
        "[project.other]\n"
        'root       = "other"\n'
        'adapter    = "pytest"\n'
        'test_paths = ["tests/"]\n'
        "\n"
        "[artifact.schema]\n"
        'path        = "other/schema.json"\n'
        'produced_by = "other"\n'
        'consumed_by = ["svc"]\n'
        'regenerate  = "true"\n'
    )
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "add svc, other (schema from other to svc)")
    return repo


@pytest.fixture
def repo_broken(repo, ledger_home):
    """`repo` plus a second pytest project `verify` that cannot collect.

    Mirrors a missing-dependency incident. `run start` refuses this project, so the
    fixture is only usable by doctor tests, which need no run.
    """
    (repo / "verify" / "tests").mkdir(parents=True)
    (repo / "verify" / "tests" / "test_v.py").write_text(
        "import yaml_does_not_exist\n\ndef test_v():\n    assert True\n"
    )
    (repo / "tdd.toml").write_text(
        "[project.backend]\n"
        'root       = "backend"\n'
        'adapter    = "pytest"\n'
        'test_paths = ["tests/"]\n'
        "lint       = []\n"
        "typecheck  = []\n"
        "\n"
        "[project.verify]\n"
        'root       = "verify"\n'
        'adapter    = "pytest"\n'
        'test_paths = ["tests/"]\n'
        "lint       = []\n"
        "typecheck  = []\n"
    )
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "add broken verify project")
    return repo


def write_plan(repo: Path, body: str, name: str = "tasks/plan.md") -> str:
    path = repo / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", f"plan: {name}")
    return name


def run_cli_text(repo: Path, *argv: str) -> str:
    """Invoke the CLI in-process, returning raw stdout."""
    import contextlib
    import io

    from tddcli.cli import main

    prev = os.getcwd()
    os.chdir(repo)
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            main(list(argv))
    finally:
        os.chdir(prev)
    return buf.getvalue()


def run_cli(repo: Path, *argv: str) -> dict:
    """Invoke the CLI and parse its JSON envelope."""
    import json

    return json.loads(run_cli_text(repo, *argv))
