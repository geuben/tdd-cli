"""cargo adapter — pinned against real `cargo test` console output.

All tests run without a Rust toolchain: they exercise console parsing, id
namespacing and command construction against output captured from cargo
1.98 (2026-09-05), exactly as test_gradle_adapter.py does for Gradle.
`_run_suite` is mocked.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from tddcli import config as config_mod
from tddcli.adapters import available
from tddcli.adapters.base import FAILED, NOT_COLLECTED, NOT_FOUND, PASSED, Collection
from tddcli.adapters.cargo_adapter import CargoAdapter

TOML = """
[project.kernel]
root       = "kernel"
adapter    = "cargo"
test_paths = ["tests/"]
"""

TOML_WITH_ENV = """
[project.kernel]
root       = "kernel"
adapter    = "cargo"
test_paths = ["tests/"]
env        = { CARGO_HOME = "/opt/cargo" }
"""

TOML_CUSTOM_CMD = """
[project.kernel]
root         = "kernel"
adapter      = "cargo"
test_paths   = ["tests/"]
test_command = "cargo test --tests --features fuzzing"
"""

# `cargo test --tests 2>&1` — one lib unit test fails, one integration test passes.
FULL_RUN = """\
   Compiling probe_kernel v0.1.0 (/work/kernel)
    Finished `test` profile [unoptimized + debuginfo] target(s) in 0.49s
     Running unittests src/lib.rs (/work/target/debug/deps/probe_kernel-f0a2d29d7c4f02a1)

running 3 tests
test layout::tests::fails_on_purpose ... FAILED
test tests::version_is_one ... ok
test layout::tests::wraps_short ... ok

failures:

---- layout::tests::fails_on_purpose stdout ----

thread 'layout::tests::fails_on_purpose' (173172849) panicked at src/lib.rs:7:41:
assertion `left == right` failed: expected width mismatch
  left: 2
 right: 3
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace


failures:
    layout::tests::fails_on_purpose

test result: FAILED. 2 passed; 1 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s

error: test failed, to rerun pass `--lib`
     Running tests/roundtrip.rs (/work/target/debug/deps/roundtrip-1d2c3b4a5f6e7d8c)

running 1 test
test renders_cover_only ... ok

test result: ok. 1 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s

"""

# Two targets each fail a test at the same bare path (`tests::it_works`) — the
# panic text must attribute to the target whose header preceded each block,
# not collide on the shared path.
COLLIDING_PATHS_RUN = """\
     Running unittests src/lib.rs (/work/target/debug/deps/probe_kernel-aaaa)

running 1 test
test tests::it_works ... FAILED

failures:

---- tests::it_works stdout ----

thread 'tests::it_works' panicked at src/lib.rs:3:5:
lib assertion failed


failures:
    tests::it_works

test result: FAILED. 0 passed; 1 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s

error: test failed, to rerun pass `--lib`
     Running tests/roundtrip.rs (/work/target/debug/deps/roundtrip-bbbb)

running 1 test
test tests::it_works ... FAILED

failures:

---- tests::it_works stdout ----

thread 'tests::it_works' panicked at tests/roundtrip.rs:5:5:
roundtrip assertion failed


failures:
    tests::it_works

test result: FAILED. 0 passed; 1 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s

"""

# `cargo test --tests -- --list 2>&1`
LIST_OUTPUT = """\
    Finished `test` profile [unoptimized + debuginfo] target(s) in 0.02s
     Running unittests src/lib.rs (/work/target/debug/deps/probe_kernel-f0a2d29d7c4f02a1)
layout::tests::fails_on_purpose: test
layout::tests::wraps_short: test
tests::version_is_one: test

3 tests, 0 benchmarks
     Running tests/roundtrip.rs (/work/target/debug/deps/roundtrip-1d2c3b4a5f6e7d8c)
renders_cover_only: test

1 test, 0 benchmarks
   Doc-tests probe_kernel
some_doc_example: test

1 test, 0 benchmarks
"""

# `cargo test --test roundtrip -- --exact renders_cover_only 2>&1`
TARGETED_PASS = """\
    Finished `test` profile [unoptimized + debuginfo] target(s) in 0.02s
     Running tests/roundtrip.rs (/work/target/debug/deps/roundtrip-1d2c3b4a5f6e7d8c)

running 1 test
test renders_cover_only ... ok

test result: ok. 1 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s

"""

# `cargo test --lib -- --exact layout::tests::nope 2>&1` — filter matched nothing.
TARGETED_NOT_FOUND = """\
    Finished `test` profile [unoptimized + debuginfo] target(s) in 0.02s
     Running unittests src/lib.rs (/work/target/debug/deps/probe_kernel-f0a2d29d7c4f02a1)

running 0 tests

test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 3 filtered out; finished in 0.00s

"""

# A type error in the crate: nothing ran.
COMPILE_ERROR = """\
   Compiling probe_kernel v0.1.0 (/work/kernel)
error[E0308]: mismatched types
  --> src/lib.rs:12:28
   |
12 | fn broken() { let x: u32 = "s"; }
   |                      ---   ^^^ expected `u32`, found `&str`
   |                      |
   |                      expected due to this

For more information about this error, try `rustc --explain E0308`.
error: could not compile `probe_kernel` (lib test) due to 1 previous error
"""

NO_LIB = "error: no library targets found in package `probe_bin`\n"

LIB_FAIL = "kernel::lib::layout::tests::fails_on_purpose"
LIB_PASS = "kernel::lib::layout::tests::wraps_short"
INT_PASS = "kernel::roundtrip::renders_cover_only"


def make_adapter(tmp_path: Path, toml: str = TOML) -> CargoAdapter:
    (tmp_path / "tdd.toml").write_text(toml)
    (tmp_path / "kernel" / "tests").mkdir(parents=True)
    (tmp_path / "kernel" / "tests" / "roundtrip.rs").write_text(
        "#[test] fn renders_cover_only() {}\n"
    )
    cfg = config_mod.load(tmp_path)
    return CargoAdapter(cfg.project("kernel"), tmp_path)


# ---------------------------------------------------------------------------
# Registration and ids
# ---------------------------------------------------------------------------


def test_cargo_is_a_builtin_adapter():
    assert "cargo" in available()


def test_target_id_lint_requires_target_separator(tmp_path):
    a = make_adapter(tmp_path)
    assert a.lint_target_id("renders_cover_only") is not None
    assert a.lint_target_id("roundtrip::renders_cover_only") is None
    assert a.lint_target_id("lib::layout::tests::wraps_short") is None


def test_target_path_maps_integration_target_to_its_file(tmp_path):
    a = make_adapter(tmp_path)
    assert a.target_path("roundtrip::renders_cover_only") == "tests/roundtrip.rs"
    assert a.target_path("lib::layout::tests::wraps_short") is None


# ---------------------------------------------------------------------------
# Command construction
# ---------------------------------------------------------------------------


def test_targeted_command_scopes_to_the_target_and_uses_exact(tmp_path):
    a = make_adapter(tmp_path)
    assert a._targeted_cmd("roundtrip::renders_cover_only") == (
        "cargo test --test roundtrip -- --exact renders_cover_only"
    )
    assert a._targeted_cmd("lib::layout::tests::wraps_short") == (
        "cargo test --lib -- --exact layout::tests::wraps_short"
    )


def test_targeted_command_keeps_declared_flags_but_drops_tests_selector(tmp_path):
    a = make_adapter(tmp_path, TOML_CUSTOM_CMD)
    assert a._targeted_cmd("roundtrip::renders_cover_only") == (
        "cargo test --features fuzzing --test roundtrip -- --exact renders_cover_only"
    )


def test_run_merges_stderr_into_stdout(tmp_path):
    a = make_adapter(tmp_path)
    with patch.object(CargoAdapter, "_run_suite", return_value=(0, TARGETED_PASS, "")) as rs:
        a.run(INT_PASS)
    cmd = rs.call_args.args[0]
    assert cmd.endswith("2>&1"), cmd


def test_a_run_with_a_target_but_not_target_only_runs_the_whole_suite(tmp_path):
    """GREEN (R9.1b): the target is read from the whole run, not narrowed to."""
    a = make_adapter(tmp_path)
    with patch.object(CargoAdapter, "_run_suite", return_value=(101, FULL_RUN, "")) as rs:
        a.run(INT_PASS)
    assert "--exact" not in rs.call_args.args[0]


# ---------------------------------------------------------------------------
# Suite run parsing
# ---------------------------------------------------------------------------


def test_full_run_attributes_tests_to_targets_by_header(tmp_path):
    a = make_adapter(tmp_path)
    with patch.object(CargoAdapter, "_run_suite", return_value=(101, FULL_RUN, "")):
        v = a.run()
    assert v.error is None
    assert set(v.passed) == {LIB_PASS, "kernel::lib::tests::version_is_one", INT_PASS}
    assert v.failed == [LIB_FAIL]


def test_full_run_does_not_collide_failures_sharing_a_bare_path(tmp_path):
    a = make_adapter(tmp_path)
    with patch.object(CargoAdapter, "_run_suite", return_value=(101, COLLIDING_PATHS_RUN, "")):
        v = a.run()
    assert set(v.failed) == {"kernel::lib::tests::it_works", "kernel::roundtrip::tests::it_works"}


def test_targeted_run_attributes_the_right_target_when_paths_collide(tmp_path):
    a = make_adapter(tmp_path)
    with patch.object(CargoAdapter, "_run_suite", return_value=(101, COLLIDING_PATHS_RUN, "")):
        lib_v = a.run("kernel::lib::tests::it_works")
    with patch.object(CargoAdapter, "_run_suite", return_value=(101, COLLIDING_PATHS_RUN, "")):
        int_v = a.run("kernel::roundtrip::tests::it_works")
    assert lib_v.target_outcome == FAILED
    assert "lib assertion failed" in lib_v.target_failure
    assert int_v.target_outcome == FAILED
    assert "roundtrip assertion failed" in int_v.target_failure


def test_targeted_pass(tmp_path):
    a = make_adapter(tmp_path)
    with patch.object(CargoAdapter, "_run_suite", return_value=(0, TARGETED_PASS, "")):
        v = a.run(INT_PASS)
    assert v.target_outcome == PASSED


def test_targeted_failure_carries_panic_message_as_evidence(tmp_path):
    a = make_adapter(tmp_path)
    # A targeted lib run prints the same shape as the full run's lib block.
    with patch.object(CargoAdapter, "_run_suite", return_value=(101, FULL_RUN, "")):
        v = a.run(LIB_FAIL)
    assert v.target_outcome == FAILED
    assert "expected width mismatch" in v.target_failure
    assert "panicked at src/lib.rs:7:41" in v.target_evidence
    # The trailing `failures:` summary list is not part of the failure text.
    assert "    layout::tests::fails_on_purpose" not in v.target_failure


def test_targeted_filter_matching_nothing_is_not_found(tmp_path):
    a = make_adapter(tmp_path)
    with patch.object(CargoAdapter, "_run_suite", return_value=(0, TARGETED_NOT_FOUND, "")):
        v = a.run("kernel::lib::layout::tests::nope")
    assert v.target_outcome == NOT_FOUND
    assert v.target_failure == ""


def test_compile_error_is_not_collected_for_a_target(tmp_path):
    a = make_adapter(tmp_path)
    with patch.object(CargoAdapter, "_run_suite", return_value=(101, COMPILE_ERROR, "")):
        v = a.run(LIB_PASS)
    assert v.target_outcome == NOT_COLLECTED
    assert "error[E0308]: mismatched types" in v.target_failure
    assert "src/lib.rs:12:28" in v.target_failure


def test_compile_error_is_a_suite_error_for_a_full_run(tmp_path):
    a = make_adapter(tmp_path)
    with patch.object(CargoAdapter, "_run_suite", return_value=(101, COMPILE_ERROR, "")):
        v = a.run()
    assert v.error is not None and "could not compile" in v.error
    assert v.passed == [] and v.failed == []


def test_missing_lib_target_is_not_collected(tmp_path):
    a = make_adapter(tmp_path)
    with patch.object(CargoAdapter, "_run_suite", return_value=(101, NO_LIB, "")):
        v = a.run(LIB_PASS)
    assert v.target_outcome == NOT_COLLECTED


# ---------------------------------------------------------------------------
# Collection
# ---------------------------------------------------------------------------


def test_batch_collection_prefixes_ids_and_skips_doctests(tmp_path):
    a = make_adapter(tmp_path)
    with patch.object(CargoAdapter, "_run_suite", return_value=(0, LIST_OUTPUT, "")):
        c = a.collect()
    assert c.tests == {
        LIB_FAIL,
        LIB_PASS,
        "kernel::lib::tests::version_is_one",
        INT_PASS,
    }
    assert c.failed_files == {}


def test_batch_collection_command_lists_with_merged_streams(tmp_path):
    a = make_adapter(tmp_path)
    with patch.object(CargoAdapter, "_run_suite", return_value=(0, LIST_OUTPUT, "")) as rs:
        a.collect()
    assert rs.call_args_list[0].args[0] == "cargo test --tests -- --list 2>&1"


def test_per_file_collection_records_compile_failure_against_its_file(tmp_path):
    a = make_adapter(tmp_path)
    (tmp_path / "kernel" / "tests" / "broken.rs").write_text("fn nope( {}\n")

    def side_effect(cmd, env=None, timeout=None):
        if cmd.startswith("cargo test --tests -- --list"):
            return (101, COMPILE_ERROR, "")  # batch fails → per-file loop
        if "--test broken" in cmd:
            return (101, COMPILE_ERROR, "")
        if "--test roundtrip" in cmd:
            return (0, "renders_cover_only: test\n\n1 test, 0 benchmarks\n", "")
        raise AssertionError(cmd)

    with patch.object(CargoAdapter, "_run_suite", side_effect=side_effect):
        c = a.collect()
    assert INT_PASS in c.tests
    assert "tests/broken.rs" in c.failed_files
    assert "could not compile" in c.failed_files["tests/broken.rs"]


def test_collectable_is_a_no_run_build(tmp_path):
    a = make_adapter(tmp_path)
    with patch.object(CargoAdapter, "_run_suite", return_value=(0, "", "")) as rs:
        assert a.collectable().ok
    assert rs.call_args.args[0] == "cargo test --no-run 2>&1"
    with patch.object(CargoAdapter, "_run_suite", return_value=(101, COMPILE_ERROR, "")):
        g = a.collectable()
    assert not g.ok and "E0308" in g.output


def test_every_invocation_carries_the_project_env(tmp_path):
    """`env` is how a repo points at a toolchain outside PATH (e.g. an external-disk
    rustup); the doctor gate, collection and runs must all see it."""
    a = make_adapter(tmp_path, TOML_WITH_ENV)
    with patch.object(CargoAdapter, "_run_suite", return_value=(0, LIST_OUTPUT, "")) as rs:
        a.collectable()
        a.collect()
        a.run(INT_PASS)
    for call in rs.call_args_list:
        env = call.args[1] if len(call.args) > 1 else call.kwargs.get("extra_env")
        assert env == {"CARGO_HOME": "/opt/cargo"}, call


# ---------------------------------------------------------------------------
# A crate whose test binary is not named after its file
#
# `autotests = false` plus a `[[test]]` entry compiles every file under tests/
# into one binary with a name of its own. The target is then unrelated to the
# file it was built from, and in a workspace every crate's header reads
# `Running tests/main.rs` — only the artifact tells them apart.
# ---------------------------------------------------------------------------

CONSOLIDATED_LIST = """
     Running tests/main.rs (/work/target/debug/deps/bridge_tests-541f4f38a741dff0)

adapter_config::poll_config_parses_targets_and_maps: test
adapter_webhook_config::webhook_table_parses_listen_token_and_maps: test

2 tests, 0 benchmarks
"""

WORKSPACE_LIST = """
     Running tests/main.rs (/work/target/debug/deps/bridge_tests-541f4f38a741dff0)

adapter_config::poll_config_parses_targets_and_maps: test

     Running tests/main.rs (/work/target/debug/deps/core_tests-9f1e2d3c4b5a6879)

attention_clear::clear_removes_the_alert: test

2 tests, 0 benchmarks
"""


def make_consolidated_adapter(tmp_path: Path) -> CargoAdapter:
    """A workspace of two crates, each compiling tests/main.rs under its own name."""
    (tmp_path / "tdd.toml").write_text(
        "\n".join(
            [
                "[project.ws]",
                'root       = "."',
                'adapter    = "cargo"',
                'test_paths = ["crates/*/tests/"]',
                "",
            ]
        )
    )
    for crate, target in (("dd-bridge", "bridge_tests"), ("dd-core", "core_tests")):
        tests = tmp_path / "crates" / crate / "tests"
        tests.mkdir(parents=True)
        (tests / "main.rs").write_text("mod adapter_config;\n")
        (tmp_path / "crates" / crate / "Cargo.toml").write_text(
            "\n".join(
                [
                    "[package]",
                    f'name = "{crate}"',
                    "autotests = false",
                    "",
                    "[[test]]",
                    f'name = "{target}"',
                    'path = "tests/main.rs"',
                    "",
                ]
            )
        )
    cfg = config_mod.load(tmp_path)
    return CargoAdapter(cfg.project("ws"), tmp_path)


def test_ids_use_the_binary_name_not_the_file_stem(tmp_path):
    a = make_consolidated_adapter(tmp_path)
    assert a._parse_list(CONSOLIDATED_LIST) == {
        "bridge_tests::adapter_config::poll_config_parses_targets_and_maps",
        "bridge_tests::adapter_webhook_config::webhook_table_parses_listen_token_and_maps",
    }


def test_identically_pathed_files_are_told_apart_by_their_artifact(tmp_path):
    a = make_consolidated_adapter(tmp_path)
    assert a._parse_list(WORKSPACE_LIST) == {
        "bridge_tests::adapter_config::poll_config_parses_targets_and_maps",
        "core_tests::attention_clear::clear_removes_the_alert",
    }


def test_targeted_command_scopes_to_the_declared_binary(tmp_path):
    a = make_consolidated_adapter(tmp_path)
    assert a._targeted_cmd("bridge_tests::adapter_config::parses") == (
        "cargo test --test bridge_tests -- --exact adapter_config::parses"
    )


def test_target_path_maps_a_declared_binary_to_the_file_it_is_built_from(tmp_path):
    a = make_consolidated_adapter(tmp_path)
    assert a.target_path("bridge_tests::adapter_config::parses") == (
        "crates/dd-bridge/tests/main.rs"
    )
    assert a.target_path("core_tests::attention_clear::clears") == ("crates/dd-core/tests/main.rs")


def test_per_file_collection_scopes_to_the_files_binary(tmp_path):
    a = make_consolidated_adapter(tmp_path)
    seen: list[str] = []

    def record(cmd, env):
        seen.append(cmd)
        return 0, CONSOLIDATED_LIST, ""

    with patch.object(CargoAdapter, "_run_suite", side_effect=record):
        a._collect_per_file({"crates/dd-bridge/tests/main.rs"}, Collection())
    assert "--test bridge_tests" in seen[0]
    assert "--test main" not in seen[0]


def test_a_dashed_binary_name_is_run_under_its_declared_spelling(tmp_path):
    """cargo writes `-` as `_` in the artifact, but `--test` wants the manifest's spelling."""
    (tmp_path / "tdd.toml").write_text(
        '[project.ws]\nroot = "."\nadapter = "cargo"\ntest_paths = ["tests/"]\n'
    )
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "main.rs").write_text("mod a;\n")
    (tmp_path / "Cargo.toml").write_text(
        '[package]\nname = "w"\nautotests = false\n\n'
        '[[test]]\nname = "my-tests"\npath = "tests/main.rs"\n'
    )
    cfg = config_mod.load(tmp_path)
    a = CargoAdapter(cfg.project("ws"), tmp_path)
    assert a._targeted_cmd("my_tests::a::works") == (
        "cargo test --test my-tests -- --exact a::works"
    )


def test_collection_reports_the_file_each_target_was_built_from(tmp_path):
    """The set of covered files is the manifest's, not `tests/<target>.rs`."""
    a = make_consolidated_adapter(tmp_path)
    with patch.object(CargoAdapter, "_run_suite", return_value=(0, WORKSPACE_LIST, "")):
        tests, files = a._collect_batch("cargo test --tests -- --list", {})
    assert files == {"crates/dd-bridge/tests/main.rs", "crates/dd-core/tests/main.rs"}
    assert "ws::bridge_tests::adapter_config::poll_config_parses_targets_and_maps" in tests


def test_a_malformed_artifact_falls_back_to_the_file_stem(tmp_path):
    """Nothing usable in the parentheses: the file stem is still cargo's default."""
    a = make_adapter(tmp_path)
    output = (
        "     Running tests/roundtrip.rs (/work/target/debug/deps/-1d2c3b4a)\n"
        "\nrenders_cover_only: test\n"
    )
    assert a._parse_list(output) == {"roundtrip::renders_cover_only"}


def test_a_test_entry_without_a_path_resolves_through_cargos_default(tmp_path):
    """`[[test]] name = "x"` with no `path` means `tests/x.rs`; no mapping needed."""
    (tmp_path / "tdd.toml").write_text(
        '[project.ws]\nroot = "."\nadapter = "cargo"\ntest_paths = ["tests/"]\n'
    )
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "roundtrip.rs").write_text("#[test] fn t() {}\n")
    (tmp_path / "Cargo.toml").write_text('[package]\nname = "w"\n\n[[test]]\nname = "roundtrip"\n')
    cfg = config_mod.load(tmp_path)
    a = CargoAdapter(cfg.project("ws"), tmp_path)
    assert a._manifest_targets() == {}
    assert a.target_path("roundtrip::t") == "tests/roundtrip.rs"
    assert a._targeted_cmd("roundtrip::t") == ("cargo test --test roundtrip -- --exact t")


def test_a_file_shaped_test_path_still_finds_the_manifest(tmp_path):
    """`test_paths` may name files (`tests/*.rs`), not only directories."""
    (tmp_path / "tdd.toml").write_text(
        '[project.ws]\nroot = "."\nadapter = "cargo"\ntest_paths = ["tests/*.rs"]\n'
    )
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "main.rs").write_text("mod a;\n")
    (tmp_path / "Cargo.toml").write_text(
        '[package]\nname = "w"\nautotests = false\n\n'
        '[[test]]\nname = "w_tests"\npath = "tests/main.rs"\n'
    )
    cfg = config_mod.load(tmp_path)
    a = CargoAdapter(cfg.project("ws"), tmp_path)
    assert a._manifest_targets() == {"w_tests": "tests/main.rs"}


def test_a_crate_with_no_manifest_keeps_cargos_default_mapping(tmp_path):
    """No Cargo.toml above the tests dir: the walk stops at the root, nothing is claimed."""
    a = make_adapter(tmp_path)  # kernel/tests/roundtrip.rs, no Cargo.toml anywhere
    assert a._manifest_targets() == {}
    assert a.target_path("roundtrip::renders_cover_only") == "tests/roundtrip.rs"
    assert a._target_of_file("tests/roundtrip.rs") == "roundtrip"


def test_test_files_expands_a_wildcard_directory_pattern(tmp_path):
    """`self.root / "crates/*/tests/"` is a literal path and never resolves."""
    a = make_consolidated_adapter(tmp_path)
    rels = sorted(str(p.relative_to(tmp_path)) for p in a._test_files())
    assert rels == ["crates/dd-bridge/tests/main.rs", "crates/dd-core/tests/main.rs"]
