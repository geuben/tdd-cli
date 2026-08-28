
import pytest

from tddcli import config as config_mod
from tddcli import staging
from tddcli.contract import DeclaredCycle

TOML = """
[project.backend]
root       = "backend"
adapter    = "pytest"
test_paths = ["tests/"]

[project.frontend]
root       = "frontend"
adapter    = "vitest"
test_paths = ["**/__tests__/**", "**/*.test.ts"]

[project.e2e]
root           = "frontend"
adapter        = "vitest"
test_paths     = ["e2e/"]
in_close_sweep = false

[artifact.openapi]
path        = "schema/openapi.json"
produced_by = "backend"
regenerate  = "true"
consumed_by = ["frontend"]

[artifact.api_client]
path        = "frontend/generated"
produced_by = "artifact.openapi"
regenerate  = "true"
consumed_by = ["frontend"]
generated   = true
"""


@pytest.fixture
def cfg(tmp_path):
    (tmp_path / "tdd.toml").write_text(TOML)
    return config_mod.load(tmp_path)


def test_projects_and_roots_are_declared_not_scanned(cfg):
    assert sorted(cfg.projects) == ["backend", "e2e", "frontend"]
    assert cfg.project("backend").root == "backend"


def test_is_test_file_uses_declared_paths(cfg):
    backend = cfg.project("backend")
    assert backend.is_test_file("backend/tests/test_x.py")
    assert not backend.is_test_file("backend/app/thing.py")
    frontend = cfg.project("frontend")
    assert frontend.is_test_file("frontend/services/__tests__/a.ts")
    assert frontend.is_test_file("frontend/services/a.test.ts")
    assert not frontend.is_test_file("frontend/services/a.ts")


def test_generated_paths_are_excluded_from_authorship(cfg):
    assert cfg.is_generated("frontend/generated/api.ts")
    assert not cfg.is_generated("frontend/services/api.ts")


def test_close_sweep_includes_downstream_of_touched_artifact(cfg):
    # Touching backend makes openapi stale, which frontend consumes.
    sweep = cfg.close_sweep_projects(["backend"], {"backend/app/routes.py"})
    assert sweep == ["backend", "frontend"]


def test_close_sweep_excludes_projects_opted_out(cfg):
    sweep = cfg.close_sweep_projects(["backend", "e2e"], set())
    assert "e2e" not in sweep


def test_close_sweep_skips_unrelated_projects(cfg):
    sweep = cfg.close_sweep_projects(["frontend"], {"frontend/services/a.ts"})
    assert sweep == ["frontend"]


def test_artifact_referencing_unknown_project_is_rejected(tmp_path):
    (tmp_path / "tdd.toml").write_text(
        '[project.a]\nroot="a"\nadapter="pytest"\n'
        '[artifact.x]\npath="p"\nproduced_by="nope"\n'
    )
    with pytest.raises(config_mod.ConfigError, match="unknown project"):
        config_mod.load(tmp_path)


# -- reachable_projects ----------------------------------------------------


def test_reachable_projects_returns_declared_when_no_artifacts(tmp_path):
    (tmp_path / "tdd.toml").write_text(
        "[project.a]\nroot='a'\nadapter='pytest'\ntest_paths=['tests/']\n"
        "[project.b]\nroot='b'\nadapter='pytest'\ntest_paths=['tests/']\n"
    )
    cfg_no_arts = config_mod.load(tmp_path)
    assert cfg_no_arts.reachable_projects(["b"]) == ["b"]


TRANSITIVE_TOML = """
[project.p1]
root = "p1"
adapter = "pytest"
test_paths = ["tests/"]

[project.p2]
root = "p2"
adapter = "pytest"
test_paths = ["tests/"]

[project.p3]
root = "p3"
adapter = "pytest"
test_paths = ["tests/"]

[artifact.x]
path = "p1/x.json"
produced_by = "p1"
consumed_by = ["p2"]

[artifact.y]
path = "p2/y.json"
produced_by = "p2"
consumed_by = ["p3"]
"""


def test_reachable_projects_includes_transitive_consumers(tmp_path):
    (tmp_path / "tdd.toml").write_text(TRANSITIVE_TOML)
    cfg_t = config_mod.load(tmp_path)
    assert cfg_t.reachable_projects(["p1"]) == ["p1", "p2", "p3"]


ARTIFACT_CHAIN_TOML = """
[project.prod]
root = "prod"
adapter = "pytest"
test_paths = ["tests/"]

[project.consumer]
root = "consumer"
adapter = "pytest"
test_paths = ["tests/"]

[artifact.base]
path = "prod/base.json"
produced_by = "prod"

[artifact.derived]
path = "prod/derived.json"
produced_by = "artifact.base"
consumed_by = ["consumer"]
"""


def test_reachable_projects_resolves_artifact_upstream_chain(tmp_path):
    (tmp_path / "tdd.toml").write_text(ARTIFACT_CHAIN_TOML)
    cfg_c = config_mod.load(tmp_path)
    # consumer is only reachable via prod -> artifact.base -> artifact.derived -> consumer
    assert cfg_c.reachable_projects(["prod"]) == ["consumer", "prod"]


SWEEP_OPT_OUT_TOML = """
[project.p1]
root = "p1"
adapter = "pytest"
test_paths = ["tests/"]

[project.p2]
root = "p2"
adapter = "pytest"
test_paths = ["tests/"]
in_close_sweep = false

[artifact.x]
path = "p1/x.json"
produced_by = "p1"
consumed_by = ["p2"]
"""


def test_reachable_projects_excludes_downstream_not_in_close_sweep(tmp_path):
    (tmp_path / "tdd.toml").write_text(SWEEP_OPT_OUT_TOML)
    cfg_o = config_mod.load(tmp_path)
    # p2 opted out of close sweep → not added via artifact closure
    assert cfg_o.reachable_projects(["p1"]) == ["p1"]
    # but p2 declared explicitly always wins
    assert cfg_o.reachable_projects(["p2"]) == ["p2"]


# -- staging ---------------------------------------------------------------


def declared(**kw):
    base = dict(ordinal=1, kind="standard", projects=["backend"], tests=["backend::t"])
    base.update(kw)
    return DeclaredCycle(**base)


def test_red_stages_tests_and_stubs_but_never_implementation(cfg):
    changed = {
        "backend/tests/test_x.py",
        "backend/app/new_module.py",
        "backend/app/existing.py",
    }
    c = staging.classify(
        cfg, changed, ["backend"],
        declared(stub_expected=["app/new_module.py"]), set(),
    )
    assert c.tests == ["backend/tests/test_x.py"]
    assert c.stubs == ["backend/app/new_module.py"]
    assert c.implementation == ["backend/app/existing.py"]

    red = staging.paths_for_phase(staging.RED, c)
    assert "backend/app/existing.py" not in red
    assert set(red) == {"backend/tests/test_x.py", "backend/app/new_module.py"}


def test_green_stages_everything_authored_in_the_cycle(cfg):
    c = staging.classify(
        cfg, {"backend/tests/test_x.py", "backend/app/existing.py"},
        ["backend"], declared(), set(),
    )
    assert set(staging.paths_for_phase(staging.GREEN, c)) == {
        "backend/tests/test_x.py", "backend/app/existing.py"
    }


def test_generated_output_is_never_attributed_to_the_agent(cfg):
    c = staging.classify(
        cfg, {"frontend/generated/api.ts", "frontend/services/a.ts"},
        ["frontend"], declared(projects=["frontend"]), set(),
    )
    assert c.generated == ["frontend/generated/api.ts"]
    assert "frontend/generated/api.ts" not in staging.paths_for_phase(staging.GREEN, c)


def test_files_outside_cycle_projects_are_flagged_not_staged(cfg):
    c = staging.classify(
        cfg, {"backend/app/x.py", "tasks/plan.md"}, ["backend"], declared(), set()
    )
    assert c.outside == ["tasks/plan.md"]
    assert "tasks/plan.md" not in staging.paths_for_phase(staging.GREEN, c)


def test_preexisting_dirt_is_excluded_forever(cfg):
    c = staging.classify(
        cfg, {"backend/app/x.py", "backend/app/dirty.py"}, ["backend"],
        declared(), {"backend/app/dirty.py"},
    )
    assert c.excluded == ["backend/app/dirty.py"]
    assert "backend/app/dirty.py" not in staging.paths_for_phase(staging.GREEN, c)


def test_pin_phase_stages_only_the_characterisation_test(cfg):
    c = staging.classify(
        cfg, {"backend/tests/test_pin.py", "backend/app/x.py"}, ["backend"],
        declared(kind="pin"), set(),
    )
    assert staging.paths_for_phase(staging.PIN, c) == ["backend/tests/test_pin.py"]


def test_commit_message_prefers_the_plan(cfg):
    d = declared(commit_messages={"red": "test: from the plan"})
    assert staging.default_message(staging.RED, d, 1) == "test: from the plan"
    assert staging.default_message(staging.GREEN, d, 1).startswith("feat:")


def test_upstream_producer_roots_includes_self_and_upstream_producers(cfg):
    assert cfg.upstream_producer_roots("frontend") == ["backend", "frontend"]
    assert cfg.upstream_producer_roots("backend") == ["backend"]


def test_declared_ancillary_file_is_bucketed_and_staged(cfg):
    c = staging.classify(
        cfg, {"backend/app/x.py", "tasks/plan.md"}, ["backend"],
        declared(), set(), ancillary={"tasks/plan.md"},
    )
    assert c.ancillary == ["tasks/plan.md"]
    assert c.outside == []
    assert "tasks/plan.md" in staging.paths_for_phase(staging.GREEN, c)


def test_health_command_parses_onto_project(tmp_path):
    (tmp_path / "tdd.toml").write_text(
        '[project.backend]\n'
        'root         = "backend"\n'
        'adapter      = "pytest"\n'
        'test_paths   = ["tests/"]\n'
        'health_command = "true"\n'
    )
    cfg = config_mod.load(tmp_path)
    assert cfg.projects["backend"].health_command == "true"

    (tmp_path / "tdd.toml").write_text(
        '[project.backend]\n'
        'root           = "backend"\n'
        'adapter        = "pytest"\n'
        'test_paths     = ["tests/"]\n'
        'health_command = 5\n'
    )
    with pytest.raises(config_mod.ConfigError):
        config_mod.load(tmp_path)
