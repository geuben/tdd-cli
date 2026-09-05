"""cargo adapter — Rust driver through `cargo test` (§10).

Test ids are `<target>::<path>`: the *target* is `lib` for unit tests compiled
into the library (`#[cfg(test)]` modules under `src/`) or the integration-test
binary name for a file under `tests/` (`tests/roundtrip.rs` → `roundtrip`); the
*path* is the test's module path exactly as cargo prints it:

    lib::layout::tests::wraps_short
    roundtrip::renders_cover_only

A targeted run composes to cargo's own selectors without translation —
`cargo test --lib -- --exact layout::tests::wraps_short` or
`cargo test --test roundtrip -- --exact renders_cover_only` — and nothing else
is appended.

Console output *is* the oracle here: `cargo test` writes no result file, but
its per-test lines (`test <path> ... ok|FAILED|ignored`) are stable, and each
target's block is preceded by a `Running unittests src/lib.rs (…)` /
`Running tests/<name>.rs (…)` header that names the target. cargo prints the
headers on stderr and the test lines on stdout, so every invocation is run with
`2>&1` to keep them interleaved in order; attribution is "the most recent
header". Doc-tests (`Doc-tests <crate>`) have no stable ids and are excluded by
running `cargo test --tests` by default.

A *compile* failure maps to `not_collected`, not `failed`. Rust has no separate
collection phase — a test naming a missing symbol fails `rustc`, not the run —
so it is treated like Python's import error and Kotlin's compile error: write a
compiling stub (a function whose body is `todo!()`), then observe the
assertion failure. The discriminator is `error: could not compile` (or an
`error[E…]` diagnostic) with no test line produced.

Only files under `test_paths` are tests for staging purposes. Declare
`tests/`, not `src/`: a `#[cfg(test)]` module lives inside a production file,
and classifying `src/` as tests would stage implementation in RED commits.
Cycle targets therefore live in `tests/*.rs`; `lib::` ids are still collected
and scored so the baseline sees them.

Config (`tdd.toml`):

    [project.kernel]
    root         = "transcript-kernel"
    adapter      = "cargo"
    test_paths   = ["tests/"]
    test_command = "cargo test --tests"      # default when omitted
"""

from __future__ import annotations

import re
import shlex
import time
from pathlib import Path

from .base import (
    FAILED,
    NOT_COLLECTED,
    PASSED,
    Adapter,
    GateResult,
    Verdict,
    clip_failure,
)

# `     Running unittests src/lib.rs (target/debug/deps/x-abc)` → target "lib"
# `     Running tests/roundtrip.rs (target/debug/deps/roundtrip-abc)` → "roundtrip"
_RUNNING_RE = re.compile(r"^\s*Running (?:unittests (\S+)|(\S+)) \(", re.MULTILINE)
_DOCTEST_RE = re.compile(r"^\s*Doc-tests ", re.MULTILINE)
# `test layout::tests::wraps_short ... ok` / `... FAILED` / `... ignored`
_TEST_LINE_RE = re.compile(r"^test (\S+) \.\.\. (ok|FAILED|ignored)\s*$", re.MULTILINE)
# `layout::tests::wraps_short: test` (from `-- --list`)
_LIST_LINE_RE = re.compile(r"^(\S+): test\s*$", re.MULTILINE)
# `---- layout::tests::wraps_short stdout ----` opens a failure block
_FAILURE_BLOCK_RE = re.compile(r"^---- (\S+) stdout ----\s*$", re.MULTILINE)
_COMPILE_ERROR_RE = re.compile(r"^error(?:\[E\d+\])?: ", re.MULTILINE)
_COULD_NOT_COMPILE_RE = re.compile(r"could not compile")
_NO_LIB_RE = re.compile(r"no library targets found")


def _target_of_header(match: re.Match) -> str | None:
    unit, path = match.group(1), match.group(2)
    if unit is not None:
        return "lib"
    if path.startswith("tests/") and path.endswith(".rs"):
        return Path(path).stem
    return None  # examples/benches: not test targets


class CargoAdapter(Adapter):
    name = "cargo"

    def stub_hint(self) -> str:
        return (
            "a compiling stub — a function whose body is `todo!()` — so the test"
            " fails on its assertion/panic rather than on `rustc`; a missing"
            " symbol is a *compile* failure (not_collected), not RED"
        )

    def lint_target_id(self, native: str) -> str | None:
        if "::" not in native:
            return (
                f"cargo target ids must be '<target>::<path>' (got {native!r}); expected"
                " shape: lib::module::tests::name or <tests-file-stem>::name"
            )
        return None

    def target_path(self, native: str) -> str | None:
        target, _, _ = native.partition("::")
        if target == "lib":
            return None
        return f"tests/{target}.rs"

    # ------------------------------------------------------------------
    # Commands
    # ------------------------------------------------------------------

    def _test_cmd(self) -> str:
        return self.project.test_command or "cargo test --tests"

    @staticmethod
    def _selector(native_id: str) -> str:
        target, _, path = native_id.partition("::")
        scope = "--lib" if target == "lib" else f"--test {shlex.quote(target)}"
        return f"{scope} -- --exact {shlex.quote(path)}"

    def _targeted_cmd(self, native_id: str) -> str:
        """`cargo test <flags…>` from the declared command, with the suite-wide
        target selector (`--tests`) dropped so the per-target scope can be set."""
        return f"{self._targeted_prefix()} {self._selector(native_id)}"

    # ------------------------------------------------------------------
    # Discovery — integration test files
    # ------------------------------------------------------------------

    def _test_files(self) -> list[Path]:
        found: set[Path] = set()
        for pattern in self.project.test_patterns or []:
            if pattern.endswith("/"):
                base = self.root / pattern
                if base.is_dir():
                    found.update(p for p in base.glob("*.rs") if p.is_file())
            else:
                found.update(p for p in self.root.glob(pattern) if p.is_file())
        return sorted(found)

    # ------------------------------------------------------------------
    # Collection — `cargo test … -- --list`, attributed by target header
    # ------------------------------------------------------------------

    def _collect_invocations(self):
        return [(f"{self._test_cmd()} -- --list", self._suite_env(None))]

    def _collect_batch(self, command, env):
        code, out, _err = self._run_suite(f"{command} 2>&1", env)
        if code != 0 or _COULD_NOT_COMPILE_RE.search(out):
            return None
        tests = self._parse_list(out)
        files = {f"tests/{t.split('::', 1)[0]}.rs" for t in tests if not t.startswith("lib::")}
        return {self.qualify(t) for t in tests}, files

    def _collect_per_file(self, rels, result):
        for rel in sorted(rels):
            stem = Path(rel).stem
            cmd = f"{self._targeted_prefix()} --test {shlex.quote(stem)} -- --list 2>&1"
            code, out, _err = self._run_suite(cmd, self._suite_env(None))
            if code != 0 or _COULD_NOT_COMPILE_RE.search(out):
                result.failed_files[rel] = clip_failure(self._errors(out))
                continue
            result.tests |= {self.qualify(t) for t in self._parse_list(out, default=stem)}
        return result

    def _targeted_prefix(self) -> str:
        parts = shlex.split(self._test_cmd())
        parts = [p for p in parts if p != "--tests"]
        if "--" in parts:
            parts = parts[: parts.index("--")]
        return shlex.join(parts)

    @staticmethod
    def _parse_list(output: str, default: str | None = None) -> set[str]:
        """Walk `--list` output, prefixing each `path: test` line with the target
        named by the most recent `Running …` header (or `default` when the
        invocation was already scoped to one target)."""
        tests: set[str] = set()
        target = default
        for line in output.splitlines():
            header = _RUNNING_RE.match(line)
            if header:
                target = _target_of_header(header)
                continue
            if _DOCTEST_RE.match(line):
                target = None
                continue
            entry = _LIST_LINE_RE.match(line)
            if entry and target is not None:
                tests.add(f"{target}::{entry.group(1)}")
        return tests

    def collectable(self) -> GateResult:
        code, out, err = self._run_suite(
            f"{self._targeted_prefix()} --no-run 2>&1", self._suite_env(None)
        )
        if code == 0:
            return GateResult(ok=True)
        return GateResult(ok=False, output=clip_failure(self._errors(out + err)))

    # ------------------------------------------------------------------
    # Results
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_run(output: str, default: str | None = None):
        """`(passed, failed, failures)` from a merged `cargo test` console."""
        passed: set[str] = set()
        failed: set[str] = set()
        failures: dict[str, str] = {}
        target = default
        # Position of each header, alongside the target it switches to — used to
        # attribute a failure block by the header most recently seen before it,
        # since two targets can share a test path (e.g. both name a test
        # `tests::it_works`) and a path-only lookup would collide between them.
        header_spans: list[tuple[int, str | None]] = []
        pos = 0
        for line in output.splitlines(keepends=True):
            header = _RUNNING_RE.match(line)
            if header:
                target = _target_of_header(header)
                header_spans.append((pos, target))
            elif _DOCTEST_RE.match(line):
                target = None
                header_spans.append((pos, target))
            else:
                entry = _TEST_LINE_RE.match(line)
                if entry and target is not None:
                    path, outcome = entry.groups()
                    tid = f"{target}::{path}"
                    if outcome == "ok":
                        passed.add(tid)
                    elif outcome == "FAILED":
                        failed.add(tid)
            pos += len(line)

        def _target_at(offset: int) -> str | None:
            current = default
            for start, tgt in header_spans:
                if start > offset:
                    break
                current = tgt
            return current

        # Failure blocks: from `---- <path> stdout ----` up to the next block or
        # the trailing `failures:` summary list.
        blocks = list(_FAILURE_BLOCK_RE.finditer(output))
        for i, m in enumerate(blocks):
            end = blocks[i + 1].start() if i + 1 < len(blocks) else len(output)
            body = output[m.end() : end]
            body = body.split("\nfailures:\n", 1)[0].strip()
            path = m.group(1)
            tid = f"{_target_at(m.start()) or 'lib'}::{path}"
            failures[tid] = clip_failure(body) if body else "test failed"
        return passed, failed, failures

    @staticmethod
    def _errors(combined: str) -> str:
        lines = [
            ln
            for ln in combined.splitlines()
            if _COMPILE_ERROR_RE.match(ln) or "-->" in ln or "could not compile" in ln
        ]
        return "\n".join(lines) if lines else combined

    def run(self, target: str | None = None) -> Verdict:
        verdict = Verdict(project=self.project.name, adapter=self.name, target=target)
        env = self._suite_env(None)

        native = self.strip(target) if target is not None else None
        if native is not None:
            cmd = self._targeted_cmd(native)
            default = native.partition("::")[0]
        else:
            cmd = self._test_cmd()
            default = None

        started = time.monotonic()
        code, out, err = self._run_suite(f"{cmd} 2>&1", env)
        verdict.duration_ms = int((time.monotonic() - started) * 1000)
        combined = out + err

        passed, failed, failures = self._parse_run(combined, default=default)
        verdict.passed = sorted(self.qualify(t) for t in passed)
        verdict.failed = sorted(self.qualify(t) for t in failed)

        if not passed and not failed:
            if _COULD_NOT_COMPILE_RE.search(combined) or (
                code != 0 and _COMPILE_ERROR_RE.search(combined)
            ):
                errors = clip_failure(self._errors(combined))
                if target is not None:
                    verdict.target_outcome = NOT_COLLECTED
                    verdict.target_failure = errors
                else:
                    verdict.error = errors
            elif target is not None and _NO_LIB_RE.search(combined):
                verdict.target_outcome = NOT_COLLECTED
                verdict.target_failure = clip_failure(combined)
            # else: filter matched nothing → NOT_FOUND; empty full run is clean
            return verdict

        if target is None or native is None:
            return verdict

        if target in verdict.passed:
            verdict.target_outcome = PASSED
        elif target in verdict.failed:
            verdict.target_outcome = FAILED
            text = failures.get(native, "test failed")
            verdict.target_failure = text
            verdict.target_evidence = next(
                (ln for ln in text.splitlines() if "panicked" in ln or "assertion" in ln),
                next((ln for ln in text.splitlines() if ln.strip()), ""),
            )
        return verdict
