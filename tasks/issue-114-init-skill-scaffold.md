---
closes: 114
cycles:
  - n: 1
    project: tddcli
    refactor_cycle: true
    title: "extract docs.shipped(path) from Topic.resolve"
    files: ["src/tddcli/docs.py"]
    commit_refactor: "refactor: docs.shipped resolves any shipped file, packaged copy first"
  - n: 2
    project: tddcli
    title: "the shipped driving skill declares the versions this binary emits"
    test: "tests/test_init_skill.py::test_the_shipped_skill_declares_the_versions_this_binary_emits"
    files: ["examples/skills/tdd-drive/SKILL.md"]
    commit_red: "test: the shipped tdd-drive skill declares its verb_set_version"
    commit_green: "feat: tdd-drive declares verb_set_version and envelope_version in its metadata"
    commit_refactor: "refactor: tidy the skill front-matter"
  - n: 3
    project: tddcli
    title: "tdd init --skill claude-code writes the installed driving skill"
    test: "tests/test_init_skill.py::test_init_skill_writes_the_installed_driving_skill"
    stub_expected: ["src/tddcli/cli.py"]
    files: ["src/tddcli/cli.py", "src/tddcli/harness.py"]
    commit_red: "test: tdd init --skill claude-code writes the installed skill"
    commit_green: "feat: tdd init --skill claude-code writes the driving skill"
    commit_refactor: "refactor: tidy the harness scaffold"
  - n: 4
    project: tddcli
    title: "an unknown harness is refused as unknown_harness and nothing is written"
    test: "tests/test_init_skill.py::test_an_unknown_harness_is_refused_and_nothing_is_written"
    files: ["src/tddcli/cli.py"]
    commit_red: "test: init refuses an unknown harness"
    commit_green: "feat: init --skill refuses an unknown harness"
    commit_refactor: "refactor: tidy the harness lookup"
  - n: 5
    project: tddcli
    title: "tdd init --skill claude-code writes the installed Stop and Bash hooks"
    test: "tests/test_init_skill.py::test_init_skill_writes_the_installed_hooks"
    files: ["src/tddcli/harness.py"]
    commit_red: "test: tdd init --skill claude-code writes the installed hooks"
    commit_green: "feat: init --skill writes the Stop and Bash hooks"
    commit_refactor: "refactor: tidy the hook scaffolds"
  - n: 6
    project: tddcli
    title: "every file a harness scaffolds is carried into the wheel"
    test: "tests/test_init_skill.py::test_every_scaffolded_file_is_carried_into_the_wheel"
    files: ["pyproject.toml"]
    commit_red: "test: every scaffolded file is force-included into the wheel"
    commit_green: "build: ship the Claude Code hook scripts in the wheel"
    commit_refactor: "refactor: tidy the force-include list"
  - n: 7
    project: tddcli
    title: "a scaffold missing from the installation is refused as missing_from_install and nothing is written"
    test: "tests/test_init_skill.py::test_a_scaffold_missing_from_the_install_is_refused_and_nothing_is_written"
    files: ["src/tddcli/cli.py"]
    commit_red: "test: init --skill refuses when a shipped file is missing"
    commit_green: "feat: init --skill reports a packaging fault before writing anything"
    commit_refactor: "refactor: tidy the install preflight"
  - n: 8
    project: tddcli
    title: "with --skill an existing tdd.toml is kept, and --force still replaces it"
    test: "tests/test_init_skill.py::test_init_skill_keeps_an_existing_tdd_toml_unless_forced"
    files: ["src/tddcli/cli.py"]
    commit_red: "test: init --skill keeps an existing tdd.toml"
    commit_green: "feat: init --skill keeps an existing tdd.toml unless --force"
    commit_refactor: "refactor: tidy the config step"
  - n: 9
    project: tddcli
    title: "with no .claude/settings.json, init --skill writes one that wires both hooks"
    test: "tests/test_init_skill.py::test_init_skill_writes_settings_that_wire_both_hooks"
    files: ["src/tddcli/cli.py", "src/tddcli/harness.py"]
    commit_red: "test: init --skill writes settings.json wiring both hooks"
    commit_green: "feat: init --skill writes .claude/settings.json when there is none"
    commit_refactor: "refactor: tidy the settings stanza"
  - n: 10
    project: tddcli
    title: "an existing .claude/settings.json is left alone and the stanza is handed over"
    test: "tests/test_init_skill.py::test_an_existing_settings_file_is_left_alone_and_the_stanza_handed_over"
    files: ["src/tddcli/cli.py"]
    commit_red: "test: init --skill never edits an existing settings.json"
    commit_green: "feat: init --skill hands over the hook stanza instead of merging it"
    commit_refactor: "refactor: tidy the settings hand-over"
  - n: 11
    project: tddcli
    title: "a settings.json that already wires both hooks is reported as wired"
    test: "tests/test_init_skill.py::test_settings_that_already_wire_both_hooks_are_reported_as_wired"
    files: ["src/tddcli/cli.py", "src/tddcli/harness.py"]
    commit_red: "test: init --skill recognises settings that already wire the hooks"
    commit_green: "feat: init --skill reports already-wired hooks as wired"
    commit_refactor: "refactor: tidy the wiring check"
  - n: 12
    project: tddcli
    title: "a harness file that differs is refused as harness_files_differ, with or without --force"
    test: "tests/test_init_skill.py::test_a_harness_file_that_differs_is_refused_with_or_without_force"
    files: ["src/tddcli/cli.py"]
    commit_red: "test: init --skill never overwrites a customised harness file"
    commit_green: "feat: init --skill refuses to overwrite a harness file that differs"
    commit_refactor: "refactor: tidy the differs preflight"
  - n: 13
    project: tddcli
    title: "--update-skill replaces a harness file that differs"
    test: "tests/test_init_skill.py::test_update_skill_replaces_a_harness_file_that_differs"
    stub_expected: ["src/tddcli/cli.py"]
    files: ["src/tddcli/cli.py"]
    commit_red: "test: init --skill --update-skill replaces a stale skill"
    commit_green: "feat: tdd init --update-skill"
    commit_refactor: "refactor: tidy --update-skill"
  - n: 14
    project: tddcli
    title: "--update-skill without --skill is refused as skill_required"
    test: "tests/test_init_skill.py::test_update_skill_without_skill_is_refused"
    files: ["src/tddcli/cli.py"]
    commit_red: "test: init refuses --update-skill without --skill"
    commit_green: "feat: init refuses --update-skill without --skill"
    commit_refactor: "refactor: tidy the flag check"
  - n: 15
    project: tddcli
    title: "doctor checks the driving skill's declared versions against the binary's"
    test: "tests/test_init_skill.py::test_doctor_checks_the_driving_skills_declared_versions"
    files: ["src/tddcli/cli.py", "src/tddcli/harness.py"]
    commit_red: "test: doctor names a driving skill that has drifted from the binary"
    commit_green: "feat: doctor checks the driving skill's verb_set_version and envelope_version"
    commit_refactor: "refactor: tidy the skill version check"
  - n: 16
    project: tddcli
    title: "the hooks README shows the stanza init writes"
    test: "tests/test_init_skill.py::test_the_hooks_readme_shows_the_stanza_init_writes"
    files:
      - "examples/claude-code-hooks/README.md"
      - "examples/claude-code-hooks/stop_hook.py"
      - "examples/claude-code-hooks/bash_hook.py"
      - "examples/skills/tdd-drive/README.md"
      - "README.md"
      - "docs/harness-integration.md"
      - "docs/PRD.md"
      - "CHANGELOG.md"
      - "src/tddcli/docs.py"
      - "src/tddcli/cli.py"
    commit_red: "test: the hooks README shows the stanza init writes"
    commit_green: "docs: the hooks README shows tdd init --skill and its stanza"
    commit_refactor: "docs: tdd init --skill in the README, harness guide, PRD and changelog"
---

# Issue 114: `tdd init --skill`, scaffolding the driving skill and hooks from the installed copies

## Context

Issue #114. Since #113, `tdd docs` lets an agent read the shipped skill and hook docs from the
installed binary. Setting up a project for an agent-driven run is still manual: copy
`examples/skills/tdd-drive/SKILL.md` into `.claude/skills/tdd-drive/`, copy the two hook
scripts, and hand-write the `.claude/settings.json` stanza that wires them. Two things go wrong:

- **It gets skipped.** The skill contains no stopping instructions by design, so a project with
  the skill but no Stop hook has a loop that breaks silently.
- **It drifts.** A hand-copied `SKILL.md` stays at the `verb_set_version` it was copied at while
  `tdd` is upgraded underneath it.

The ask is `tdd init --skill claude-code`, behind a flag. It writes the skill and hooks from the
copies installed with the binary, plus whatever wires the hooks up. The issue leaves five
design questions open. This plan settles all of them below. This was an automated dispatch
run with nobody to ask, so the planner decided each one from codebase evidence and recorded
why. Out of scope, by the issue's own words: anything about *reading* the docs (#113).

Evidence gathered while planning (base `b487ce1`):

- `cmd_init` in `src/tddcli/cli.py` writes `tdd.toml` through `actor.current().write_file` and
  refuses an existing one unless `--force`. Its parser has only `--force`.
- `src/tddcli/docs.py` resolves a shipped file as `_PACKAGED / path` (the wheel's
  `tddcli/_docs`), falling back to `_SOURCE / path` (the checkout).
- `pyproject.toml` force-includes the skill and the hooks `README.md`, but **not**
  `stop_hook.py` or `bash_hook.py`. A wheel built and installed during planning had only
  `README.md` under `tddcli/_docs/examples/claude-code-hooks/`.
- `tests/test_actor_seams.py` fails any `.write_text(`, `.write_bytes(`, `.mkdir(` and similar
  call outside `actor.py`, `agentfs.py`, `leases.py`, `ledger.py` and `service.py`.
- `init` is in `LOCAL_VERBS`, so on a split machine the agent's own `tdd` answers it locally.
  Nothing about split mode changes.
- The suite is green in a fresh worktree: **722 passed**.

## Design decisions (locked)

1. **The harness is a closed set, held in a new module `src/tddcli/harness.py`.** Today it is
   `{"claude-code"}` only. Adapters use an entry-point group because they load code. A harness
   is data (files to copy, a settings stanza), with nothing to load, so a registry would be
   future-proofing. The shape, which later cycles and tests rely on by name:

   ```python
   @dataclass(frozen=True)
   class Scaffold:
       source: str  # repo-relative path of the shipped copy, and verbatim its path under `_docs`
       dest: str    # worktree-relative path init writes it to

   @dataclass(frozen=True)
   class Harness:
       name: str
       files: tuple[Scaffold, ...]
       # added by later cycles (see the increment list in Execution):
       settings_path: str  # ".claude/settings.json"                         (cycle 9)
       settings: dict      # the stanza                                       (cycle 9)
       skill: str          # dest of the driving skill, which doctor reads    (cycle 15)

   HARNESSES: dict[str, Harness]
   ```

   The `claude-code` files, in this order:

   | source | dest |
   |---|---|
   | `examples/skills/tdd-drive/SKILL.md` | `.claude/skills/tdd-drive/SKILL.md` |
   | `examples/claude-code-hooks/stop_hook.py` | `.claude/hooks/tdd_stop_hook.py` |
   | `examples/claude-code-hooks/bash_hook.py` | `.claude/hooks/tdd_bash_hook.py` |

   The `tdd_` prefix (from the issue's sketch) keeps the scripts from colliding with a
   project's own hooks. The planning-side `tdd-handoff` skill is not scaffolded: the issue asks
   for the *driving* skill and its hooks. *Decided by: planner, from the adapter registry and
   the issue's sketch.*

   **Mechanism footgun:** do not use argparse `choices=` for `--skill`. An argparse error exits
   2 with empty stdout, so no envelope reaches the caller (`conftest.run_cli` dies in
   `JSONDecodeError`). Take `--skill` as a free string and refuse an unknown one in
   `cmd_init` (cycle 4), the way `tdd docs <unknown>` names the known topics.

2. **Files are copied out, never referenced in place.** Referencing the installed package
   (`python3 /…/site-packages/tddcli/_docs/…`) writes a machine-specific path into a file
   projects commit, and it breaks when the venv moves. A copied hook can still track the binary,
   because both hooks delegate every decision to `tdd status`'s envelope. Copies are read with
   `docs.shipped(source)` (cycle 1), so an installed wheel reads its packaged copy and an
   editable install reads the checkout. That is the same resolution `tdd docs` uses.
   `pyproject.toml` force-includes both hook scripts at `tddcli/_docs/<source>` (cycle 6). The
   sdist `include` already carries `examples`. *Decided by: planner.*

3. **`.claude/settings.json` is written only when it does not exist. It is never merged into.**
   The stanza:

   ```json
   {
     "hooks": {
       "Stop": [
         {"hooks": [{"type": "command",
                     "command": "python3 \"$CLAUDE_PROJECT_DIR/.claude/hooks/tdd_stop_hook.py\""}]}
       ],
       "PreToolUse": [
         {"matcher": "Bash",
          "hooks": [{"type": "command",
                     "command": "python3 \"$CLAUDE_PROJECT_DIR/.claude/hooks/tdd_bash_hook.py\""}]}
       ]
     }
   }
   ```

   `$CLAUDE_PROJECT_DIR` (Claude Code expands it in hook commands) keeps the hooks working
   after the agent `cd`s into a subdirectory. The existing README's relative path does not.
   Written as `json.dumps(stanza, indent=2) + "\n"`.

   `result.harness.settings` is one of:
   - `"written"`: there was no settings file, so init wrote the stanza (cycle 9).
   - `"wired"`: the file exists and already wires both hooks (cycle 11). Wired means that, for
     each event in the stanza (`Stop`, `PreToolUse`), some group in `data["hooks"][event]` has
     a hook whose `command` equals the stanza's command for that event. A file that is not
     JSON, or not an object, is not wired. It is never an error.
   - `"not_written"`: the file exists and does not wire both hooks (cycle 10). The file is left
     byte-for-byte untouched. `result.harness.settings_stanza` carries the stanza, and
     `next_action.detail` gains: `".claude/settings.json already exists and does not wire the
     tdd hooks: merge result.harness.settings_stanza into it. Without the Stop hook nothing
     stops the agent ending its turn mid-run."`

   Why not merge: settings.json is the user's file and may already have Stop hooks. Rewriting it
   re-serialises their formatting, and the issue calls a silent merge into someone's hook
   config "worse" than overwriting. Why not print-only: on a fresh project that brings back the
   skipped step the issue exists to remove. Only `.claude/settings.json` is read.
   `settings.local.json` and user-level settings are not, so hooks wired only there report as
   `not_written` (a false nag, never a lost edit). *Decided by: planner, from the issue's
   option 2.*

4. **Existing harness files: identical is fine, different is refused, and `--update-skill`
   replaces.** A dest whose bytes equal the shipped copy is rewritten harmlessly, or skipped.
   Any dest that exists and differs refuses the whole command **before anything is written**
   (`tdd.toml` included), with `reason: "harness_files_differ"` and `result.differs`, the list
   of differing dests in table order. `--update-skill` overwrites them. `--force` keeps its
   one meaning, overwriting `tdd.toml`, and **does not** bypass the refusal (cycle 12 pins
   both forms). Conflating them would mean refreshing a stale skill destroys a reviewed
   `tdd.toml`, and a customised skill is lost to a flag the user passed for a different file.
   The README invites customisation, so refusing by default and naming the files is the
   non-lossy choice. *Decided by: planner, from the issue's question 3.*

5. **With `--skill`, an existing `tdd.toml` is kept, not refused.** `tdd init --skill
   claude-code` on an already-configured project scaffolds the harness and reports
   `result.config == "kept"` (no `written`/`detected`/`unmatched` keys). `--force` still
   regenerates it. Without `--skill`, `tdd init` is unchanged in every respect, including its
   envelope. *Decided by: planner.* The common case is adding the harness to a configured
   project, and requiring `--force` there would destroy the config to get the skill.

6. **Preflight order in `cmd_init`.** First match wins. Every refusal is
   `failure(message, reason=…)`, so the code lands under **`result.reason`**, never at the
   envelope's top level. Refusals write nothing.
   1. `skill_required`: `--update-skill` given without `--skill` (cycle 14);
   2. `unknown_harness`: the error names the known harnesses (cycle 4);
   3. `missing_from_install`: some `docs.shipped(source)` is not a file. The error says
      `"<source> is missing from this installation of tdd-cli … please report the packaging
      bug"`, like `docs.read` (cycle 7);
   4. `harness_files_differ`: unless `--update-skill` (cycle 12);
   5. then `tdd.toml` (written / kept / today's "already exists" refusal without `--skill`),
      then the harness files, then settings.

7. **Doctor checks the skill's declared versions. Drift is a failing check, and an undeclared
   version is a passing notice.** The shipped `SKILL.md` front-matter gains (cycle 2):

   ```yaml
   metadata:
     verb_set_version: "2"
     envelope_version: "1"
   ```

   `metadata` is the Agent Skills spec's free-form string map. Claude Code reads `name`,
   `description` and `argument-hint`, and ignores keys it does not use, so the skill still
   loads. This was not verified against a live Claude Code; see "Risk the run cannot retire" below. The
   prose rule in the skill ("If `next_action.verb_set_version` is not `2` …") stays.
   `harness.declared_versions(text) -> dict | None` returns the `metadata` mapping. It returns
   `None` when there is no front-matter (`contract.split_front_matter` returns `None`), when the
   YAML does not parse (catch `yaml.YAMLError`), when it is not a mapping, or when `metadata`
   is absent or not a mapping.

   For each harness whose `skill` dest exists in the worktree, `cmd_doctor` adds one global
   (no `project`) check named **`driving skill version`**:
   - declared `None` → `ok: True`, detail `"<dest> declares no verb_set_version, so drift
     cannot be checked; `tdd init --skill claude-code --update-skill` replaces it with this
     version's copy"`;
   - otherwise `ok` iff `str(declared.get("verb_set_version")) == str(VERB_SET_VERSION)` and
     the same for `envelope_version`, so an unquoted `2` matches. Failing detail: `"<dest> was
     written for verb_set_version <x>, envelope_version <y>; this tdd emits <V>, <E>. Run `tdd
     init --skill claude-code --update-skill` and re-apply any local additions."`

   No skill file means no check. An undeclared skill passes because every skill hand-copied
   before this release has no `metadata`, and turning every such repo unhealthy on upgrade
   would block runs that work today. A *declared* mismatch is exactly the mid-run hard stop
   the issue wants surfaced early. *Decided by: planner, from the issue's question 4.*

8. **No doctor check on hook wiring or hook-script drift.** The issue asks for the version
   check (question 4) and solves "skipped hooks" by having init write them. Hooks wired only in
   `settings.local.json` or user settings would make a wiring check a false failure. Not built,
   because nothing asks for it (TDD rule 4). It is not a scope cut. *Decided by: planner.*

9. **Writes go through `actor.current().write_file`** (it creates parent directories). Reads of
   shipped copies use `docs.shipped(source).read_bytes()`, and existing dests use
   `Path.read_bytes()`/`is_file()`. **Never** call `.write_text(`, `.write_bytes(`, `.mkdir(`
   in `harness.py` or `cli.py`: `tests/test_actor_seams.py` fails the run on them.
   `harness.py` spawns nothing.

10. **`docs.shipped(path: str) -> Path`** reads the module globals `_PACKAGED` and `_SOURCE`
    *at call time*. **Footgun:** do not bind them as default arguments. The tests monkeypatch
    `docs._PACKAGED`, and a default captured at import time ignores the patch.
    `Topic.resolve` becomes `return shipped(self.path)`.

11. **The referee is the released `tdd` on `PATH`** (0.15.0 at planning), never an editable
    install of this tree. `SCHEMA_VERSION` and `VERB_SET_VERSION` do not change.

## Deliberate scope cuts (do not build)

None. Every behaviour the issue asks for is built. Other harnesses (Cursor, Codex …) are not
cuts: the issue asks for `claude-code` and treats others as a question about the *shape*,
which decision 1 answers.

## Risk the run cannot retire

`metadata` in `SKILL.md` front-matter is assumed harmless to Claude Code's skill loader
(decision 7). If a reviewer knows otherwise, the fallback is a top-level key such as
`tdd-cli-verb-set-version`, which changes only cycle 2's file and cycle 15's reader.

## Cycles

All tests go in the **new file `tests/test_init_skill.py`**, at module scope (no classes),
driven in-process through `conftest.run_cli`. Header and helpers:

```python
"""`tdd init --skill`: the driving skill and hooks, from the copies installed with the binary."""

from __future__ import annotations

import json
import subprocess
import tomllib
from pathlib import Path

import pytest
import yaml

from conftest import run_cli
from tddcli import contract, docs
from tddcli.envelope import ENVELOPE_VERSION, VERB_SET_VERSION

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL = ".claude/skills/tdd-drive/SKILL.md"
STOP_HOOK = ".claude/hooks/tdd_stop_hook.py"
BASH_HOOK = ".claude/hooks/tdd_bash_hook.py"
SETTINGS = ".claude/settings.json"
EXPECTED_SETTINGS = {
    "hooks": {
        "Stop": [
            {"hooks": [{"type": "command",
                        "command": 'python3 "$CLAUDE_PROJECT_DIR/.claude/hooks/tdd_stop_hook.py"'}]}
        ],
        "PreToolUse": [
            {"matcher": "Bash",
             "hooks": [{"type": "command",
                        "command": 'python3 "$CLAUDE_PROJECT_DIR/.claude/hooks/tdd_bash_hook.py"'}]}
        ],
    }
}


@pytest.fixture
def bare_repo(tmp_path, ledger_home):
    root = tmp_path / "workspace"
    root.mkdir()
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    return root


@pytest.fixture
def packaged(tmp_path, monkeypatch):
    """A fake installed `_docs`: what init must copy from, not the checkout."""
    files = {
        "examples/skills/tdd-drive/SKILL.md": "packaged skill\n",
        "examples/claude-code-hooks/stop_hook.py": "packaged stop\n",
        "examples/claude-code-hooks/bash_hook.py": "packaged bash\n",
    }
    root = tmp_path / "_docs"
    for rel, text in files.items():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(text)
    monkeypatch.setattr(docs, "_PACKAGED", root)
    return files


def read(repo: Path, rel: str) -> str | None:
    path = repo / rel
    return path.read_text() if path.is_file() else None
```

`EXPECTED_SETTINGS` is written out literally in the test, independently of
`harness.HARNESSES` (E-9).

The block above is the file's **final** header. Add each import, constant, fixture and helper in
the first cycle whose test uses it, not all at once in cycle 2. The project's lint gate is
`uv run ruff check`, and F401 fails an unused import.

**Never import `tddcli.harness` at module top.** It does not exist until cycle 3's GREEN, so a
top-level import fails cycle 2's RED in collection. The tests that need it (cycles 6 and 16)
import it inside the test function.

Probe-verified at planning: today `run_cli(bare_repo, "init", "--skill", "claude-code")` raises
`json.JSONDecodeError: Expecting value: line 1 column 1 (char 0)`. argparse exits 2 on the
unknown flag. **That is why cycle 3 declares `src/tddcli/cli.py` in `stub_expected`**, and
cycle 13 does the same for `--update-skill`. With only `s.add_argument("--skill")` stubbed,
init writes `tdd.toml`, returns `ok: true`, and writes no skill (probe-verified).

### Cycle 1: extract `docs.shipped` (refactor)

- **Change:** add `def shipped(path: str) -> Path` to `src/tddcli/docs.py`, moving the body of
  `Topic.resolve` into it (decision 10), and make `Topic.resolve` delegate to it. Keep its
  docstring's "exactly one of these exists" explanation on `shipped`.
- **Guard:** `tests/test_docs_command.py`: `test_the_packaged_copy_wins_over_the_repository_one`,
  `test_a_missing_packaged_file_reports_a_packaging_fault`, `test_every_topic_is_readable`.
  No behaviour changes. A semantic change here is a blocker, not a refactor commit.

### Cycle 2: the shipped skill declares its versions

- **Behaviour:** `examples/skills/tdd-drive/SKILL.md`'s front-matter declares the
  `verb_set_version` and `envelope_version` the binary emits.
- **Test:** `test_the_shipped_skill_declares_the_versions_this_binary_emits`.
  `front = yaml.safe_load(contract.split_front_matter((REPO_ROOT / "examples/skills/tdd-drive/SKILL.md").read_text()))`;
  assert `front.get("metadata") == {"verb_set_version": str(VERB_SET_VERSION), "envelope_version": str(ENVELOPE_VERSION)}`.
- **Production target:** the `SKILL.md` front-matter: add the `metadata:` block from decision 7
  after `argument-hint`, with the values quoted.
- **EXPECTED FAILURE** (probed): `AssertionError: assert None == {'verb_set_version': '2', 'envelope_version': '1'}`.

### Cycle 3: init --skill writes the installed skill

- **Behaviour:** `tdd init --skill claude-code` writes `.claude/skills/tdd-drive/SKILL.md` with
  the bytes of the *installed* (packaged) copy.
- **Test:** `test_init_skill_writes_the_installed_driving_skill(bare_repo, packaged)`.
  `run_cli(bare_repo, "init", "--skill", "claude-code")`; assert
  `read(bare_repo, SKILL) == "packaged skill\n"`.
- **Stub (RED):** in `build_parser`, the `init` subparser gains `s.add_argument("--skill")`.
  Nothing else.
- **Production target:** new `src/tddcli/harness.py` (`Scaffold`, `Harness(name, files)`,
  `HARNESSES` with the one skill file), and `cli.cmd_init`, which, when `args.skill` is set,
  writes each `files` entry from `docs.shipped(source).read_bytes()` through the actor.
- **EXPECTED FAILURE** (probed, after the stub): `AssertionError: assert None == 'packaged skill\n'`.

### Cycle 4: unknown harness

- **Behaviour:** `--skill <unknown>` is refused with `unknown_harness`. The error names the known
  harnesses, and nothing is written, not even `tdd.toml`.
- **Test:** `test_an_unknown_harness_is_refused_and_nothing_is_written(bare_repo)`.
  `out = run_cli(bare_repo, "init", "--skill", "cursor")`; assert
  `(out["ok"], out["result"].get("reason"), "claude-code" in out.get("error", ""), (bare_repo / "tdd.toml").exists()) == (False, "unknown_harness", True, False)`.
  The reason is under `result.reason`.
- **Production target:** `cli.cmd_init`, a lookup in `harness.HARNESSES` before anything is
  written.
- **EXPECTED FAILURE:** after cycle 3's minimal GREEN, either `KeyError: 'cursor'` raised out of
  `main` (a `HARNESSES[args.skill]` lookup) or `AssertionError: assert (True, None, False, True) == (False, 'unknown_harness', True, False)`
  (a `.get` lookup). Either is a legitimate RED. A pass on arrival means cycle 3 over-built.

### Cycle 5: the hooks

- **Behaviour:** `tdd init --skill claude-code` also writes `.claude/hooks/tdd_stop_hook.py` and
  `.claude/hooks/tdd_bash_hook.py` from the installed copies of
  `examples/claude-code-hooks/stop_hook.py` and `bash_hook.py`.
- **Test:** `test_init_skill_writes_the_installed_hooks(bare_repo, packaged)`. Run init with
  `--skill claude-code`; assert
  `{STOP_HOOK: read(bare_repo, STOP_HOOK), BASH_HOOK: read(bare_repo, BASH_HOOK)} == {STOP_HOOK: "packaged stop\n", BASH_HOOK: "packaged bash\n"}`.
- **Production target:** `harness.HARNESSES["claude-code"].files` gains the two `Scaffold`s
  (decision 1's table order).
- **EXPECTED FAILURE:** `AssertionError: assert {'.claude/hooks/tdd_stop_hook.py': None, '.claude/hooks/tdd_bash_hook.py': None} == {…: 'packaged stop\n', …: 'packaged bash\n'}`.

### Cycle 6: the wheel carries every scaffold

- **Behaviour:** every `source` a harness scaffolds is force-included into the wheel at
  `tddcli/_docs/<source>`. Without this, the published wheel fails where the checkout passes.
  Planning confirmed it: a built wheel has no `stop_hook.py`.
- **Test:** `test_every_scaffolded_file_is_carried_into_the_wheel()`. Inside the function:
  `from tddcli import harness`;
  `included = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text())["tool"]["hatch"]["build"]["targets"]["wheel"]["force-include"]`;
  `sources = [f.source for h in harness.HARNESSES.values() for f in h.files]`; assert
  `{s: included.get(s) for s in sources} == {s: f"tddcli/_docs/{s}" for s in sources}`.
- **Production target:** `pyproject.toml`, adding two lines under
  `[tool.hatch.build.targets.wheel.force-include]`:
  `"examples/claude-code-hooks/stop_hook.py" = "tddcli/_docs/examples/claude-code-hooks/stop_hook.py"`
  and the same for `bash_hook.py`.
- **EXPECTED FAILURE:** `AssertionError: assert {…'examples/claude-code-hooks/stop_hook.py': None, …} == {…: 'tddcli/_docs/examples/claude-code-hooks/stop_hook.py', …}`.

### Cycle 7: a scaffold missing from the installation

- **Behaviour:** when a harness source is missing from both the packaged and the source
  location, init refuses with `missing_from_install` and writes nothing.
- **Test:** `test_a_scaffold_missing_from_the_install_is_refused_and_nothing_is_written(bare_repo, monkeypatch)`.
  `monkeypatch.setattr(docs, "_PACKAGED", Path("/nonexistent"))` and the same for `_SOURCE`;
  run init with `--skill claude-code`; assert
  `(out["ok"], out["result"].get("reason"), (bare_repo / "tdd.toml").exists(), read(bare_repo, SKILL)) == (False, "missing_from_install", False, None)`.
- **Production target:** `cli.cmd_init`, preflight step 3 (decision 6).
- **EXPECTED FAILURE:** `FileNotFoundError` raised from `read_bytes` (minimal cycles 3 and 5 read
  without checking). A legitimate failing test.

### Cycle 8: an existing tdd.toml is kept with --skill

- **Behaviour:** with `--skill`, an existing `tdd.toml` is kept and reported as
  `config: "kept"`, and `--force` still regenerates it.
- **Test:** `test_init_skill_keeps_an_existing_tdd_toml_unless_forced(bare_repo, packaged)`.
  Write `bare_repo / "tdd.toml"` = `"# mine\n"`; `kept = run_cli(bare_repo, "init", "--skill", "claude-code")`;
  record `kept_text = read(bare_repo, "tdd.toml")`; then
  `run_cli(bare_repo, "init", "--skill", "claude-code", "--force")`; assert
  `(kept["ok"], kept_text, kept["result"].get("config"), read(bare_repo, "tdd.toml").startswith("# Generated by `tdd init`")) == (True, "# mine\n", "kept", True)`.
- **Production target:** `cli.cmd_init`'s existing-config check.
- **EXPECTED FAILURE:** `AssertionError: assert (False, '# mine\n', None, True) == (True, '# mine\n', 'kept', True)`.

### Cycle 9: settings.json written when absent

- **Behaviour:** with no `.claude/settings.json`, init writes one holding exactly the stanza and
  reports `harness.settings == "written"`.
- **Test:** `test_init_skill_writes_settings_that_wire_both_hooks(bare_repo, packaged)`.
  `out = run_cli(bare_repo, "init", "--skill", "claude-code")`; assert
  `(json.loads(read(bare_repo, SETTINGS) or "null"), out["result"].get("harness", {}).get("settings")) == (EXPECTED_SETTINGS, "written")`.
- **Production target:** `Harness.settings_path` and `Harness.settings` (decision 3), and
  `cli.cmd_init`, which writes the stanza when the path is absent. Also
  `result.harness = {"name": ..., "settings": "written"}`.
- **EXPECTED FAILURE:** `AssertionError: assert (None, None) == ({'hooks': {…}}, 'written')`.

### Cycle 10: an existing settings.json is handed the stanza, not edited

- **Behaviour:** an existing `.claude/settings.json` that does not wire the hooks is left
  byte-for-byte unchanged. The envelope reports `settings: "not_written"` with
  `settings_stanza`, and the detail tells the human to merge it. This holds for a valid file and
  for one that is not JSON.
- **Test:** `test_an_existing_settings_file_is_left_alone_and_the_stanza_handed_over(tmp_path, ledger_home, packaged)`.
  For each `original` in `('{"permissions": {"allow": ["Bash(ls:*)"]}}\n', "{not json\n")`: make a
  fresh repo under `tmp_path / f"ws{i}"` (`git init -q`), write `.claude/settings.json` =
  `original`, run init with `--skill claude-code`, and collect
  `(read(repo, SETTINGS) == original, h.get("settings"), h.get("settings_stanza"), "settings_stanza" in out["next_action"]["detail"])`,
  where `h = out["result"].get("harness", {})`. Assert the list equals
  `[(True, "not_written", EXPECTED_SETTINGS, True)] * 2`.
- **Production target:** `cli.cmd_init`, the existing-file branch, using the detail sentence
  from decision 3.
- **EXPECTED FAILURE:** `AssertionError` on the list. After cycle 9's minimal GREEN the file is
  either untouched with no `settings_stanza` (`(True, None, None, False)`) or overwritten
  (`(False, 'written', None, False)`).
- **Why the malformed case is here:** cycle 11 adds JSON parsing. This row turns a
  `json.JSONDecodeError` there into a `fix_regression` instead of a crash nobody tested.

### Cycle 11: already wired

- **Behaviour:** a settings file that already wires both hooks is reported as `wired`, with no
  merge instruction.
- **Test:** `test_settings_that_already_wire_both_hooks_are_reported_as_wired(bare_repo, packaged)`.
  Run init with `--skill claude-code` twice; on the second envelope assert
  `(out["result"]["harness"]["settings"], "settings_stanza" in out["next_action"]["detail"]) == ("wired", False)`.
  The second run works because cycle 8 keeps the `tdd.toml` the first run wrote, and the
  harness files are identical to their shipped copies.
- **Production target:** a `harness` function that decides whether parsed settings wire every
  stanza hook (decision 3's definition), called by `cli.cmd_init` in the existing-file branch.
- **EXPECTED FAILURE:** `AssertionError: assert ('not_written', True) == ('wired', False)`.

### Cycle 12: a differing harness file is never overwritten without --update-skill

- **Behaviour:** if any dest exists and differs from its shipped copy, init refuses with
  `harness_files_differ`, lists it in `result.differs`, and writes nothing. That includes
  `tdd.toml`, and the same holds with `--force`.
- **Test:** `test_a_harness_file_that_differs_is_refused_with_or_without_force(bare_repo, packaged)`.
  Write `bare_repo / SKILL` = `"my skill\n"` (create its parent in the test). Run
  `plain = run_cli(bare_repo, "init", "--skill", "claude-code")` and
  `forced = run_cli(bare_repo, "init", "--skill", "claude-code", "--force")`; assert
  `([(o["ok"], o["result"].get("reason"), o["result"].get("differs")) for o in (plain, forced)], read(bare_repo, SKILL), (bare_repo / "tdd.toml").exists()) == ([(False, "harness_files_differ", [SKILL])] * 2, "my skill\n", False)`.
- **Production target:** `cli.cmd_init`, preflight step 4 (decision 6).
- **EXPECTED FAILURE:** `AssertionError`: both runs return `(True, None, None)`, the skill reads
  `'packaged skill\n'`, and `tdd.toml` exists.

### Cycle 13: --update-skill

- **Behaviour:** `--update-skill` replaces a differing harness file with the installed copy.
- **Test:** `test_update_skill_replaces_a_harness_file_that_differs(bare_repo, packaged)`.
  Write `bare_repo / SKILL` = `"my skill\n"`; run init with
  `--skill claude-code --update-skill`; assert `(out["ok"], read(bare_repo, SKILL)) == (True, "packaged skill\n")`.
- **Stub (RED):** `s.add_argument("--update-skill", action="store_true")` on the `init`
  subparser. Nothing else.
- **Production target:** `cli.cmd_init`, which skips preflight step 4 when `args.update_skill`.
- **EXPECTED FAILURE** (after the stub): `AssertionError: assert (False, 'my skill\n') == (True, 'packaged skill\n')`.
  Before the stub it is `JSONDecodeError`, as in cycle 3.

### Cycle 14: --update-skill alone

- **Behaviour:** `--update-skill` without `--skill` is refused with `skill_required`, and
  `tdd.toml` is not written. A flag that is silently ignored is the trap this guards.
- **Test:** `test_update_skill_without_skill_is_refused(bare_repo)`.
  `out = run_cli(bare_repo, "init", "--update-skill")`; assert
  `(out["ok"], out["result"].get("reason"), (bare_repo / "tdd.toml").exists()) == (False, "skill_required", False)`.
- **Production target:** `cli.cmd_init`, preflight step 1.
- **EXPECTED FAILURE:** `AssertionError: assert (True, None, True) == (False, 'skill_required', False)`.

### Cycle 15: doctor and the skill's declared versions

- **Behaviour:** when the claude-code skill exists in the worktree, `tdd doctor` reports a
  `driving skill version` check. It fails for a declared mismatch and names the refresh
  command. It passes, as a notice, when nothing is declared or the front-matter is unusable.
  With no skill there is no check.
- **Test:** `test_doctor_checks_the_driving_skills_declared_versions(repo)` (the conftest `repo`
  fixture. Its project root is `backend`, so `.claude/` is outside every project and doctor's
  cleanliness check ignores it. Doctor took 0.4 s per call at planning). Helper inside the test:

  ```python
  shipped = (REPO_ROOT / "examples/skills/tdd-drive/SKILL.md").read_text()
  v, e = f'verb_set_version: "{VERB_SET_VERSION}"', f'envelope_version: "{ENVELOPE_VERSION}"'

  def check(text):
      path = repo / SKILL
      if text is None:
          path.unlink(missing_ok=True)
      else:
          path.parent.mkdir(parents=True, exist_ok=True)
          path.write_text(text)
      found = [c for c in run_cli(repo, "doctor")["result"]["checks"]
               if c["check"] == "driving skill version"]
      return found[0] if found else None
  ```

  Assert this dict equals the expected one (both written out in the test):

  | key | text | expected |
  |---|---|---|
  | `"absent"` | `None` → `check(...)` is `None` | `None` |
  | `"current"` | `shipped` | `True` |
  | `"current, unquoted"` | `shipped.replace(v, f"verb_set_version: {VERB_SET_VERSION}")` | `True` |
  | `"older verb set"` | `shipped.replace(v, f'verb_set_version: "{VERB_SET_VERSION - 1}"')` | `False` |
  | `"older envelope"` | `shipped.replace(e, f'envelope_version: "{ENVELOPE_VERSION - 1}"')` | `False` |
  | `"no metadata"` | `"---\nname: tdd-drive\n---\nbody\n"` | `True` |
  | `"no front-matter"` | `"just prose\n"` | `True` |
  | `"malformed"` | `"---\nname: [unclosed\n---\n"` | `True` |
  | `"not a mapping"` | `"---\n- a list\n---\n"` | `True` |
  | `"remedy named"` | `"tdd init --skill claude-code --update-skill" in` the `"older verb set"` check's `detail` | `True` |

  For every row but the first and last, the value is `check(text)["ok"]`, or `None` when
  `check` returns `None`. Build the actual dict with a guard such as
  `(c or {}).get("ok")`, so a missing check reads `None` instead of raising. The `"current"`
  row consumes the real shipped skill, so it proves cycle 2's declaration and this reader agree
  (E-3).

  After-state probed at planning, in a scratch file outside the repo: a front-matter with
  decision 7's `metadata` block parses to `{'verb_set_version': '2', 'envelope_version': '1'}`,
  and the `replace` on `v` changes the text. `"---\nname: [unclosed\n---\n"` raises
  `yaml.parser.ParserError`, and `"---\n- a list\n---\n"` parses to a list. Those last two are
  why `declared_versions` must catch and type-check.
- **Production target:** `Harness.skill`, `harness.declared_versions`, and `cli.cmd_doctor` (the
  check, after the executor-identity check and before the per-project loop. Decision 7 gives
  the detail strings).
- **EXPECTED FAILURE** (probed): every row reads `None`, so `AssertionError` on the dict
  (`'current': None` vs `True` first).

### Cycle 16: the hooks README shows what init writes; the docs

- **Behaviour:** the JSON block in `examples/claude-code-hooks/README.md` (shown by
  `tdd docs hooks`) is exactly the stanza init writes. A human who sets up by hand gets the
  same wiring.
- **Test:** `test_the_hooks_readme_shows_the_stanza_init_writes()`. Inside the function:
  `from tddcli import harness`;
  `text = (REPO_ROOT / "examples/claude-code-hooks/README.md").read_text()`;
  `block = text.split("```json\n", 1)[1].split("```", 1)[0]`; assert
  `json.loads(block) == harness.HARNESSES["claude-code"].settings`. The README must keep exactly
  one ```` ```json ```` block.
- **GREEN:** rewrite `examples/claude-code-hooks/README.md`. **Installation** leads with
  `tdd init --skill claude-code` (what it writes, when it leaves `settings.json` alone,
  `--update-skill`), then a manual fallback: copy the scripts to
  `.claude/hooks/tdd_stop_hook.py` / `tdd_bash_hook.py` and use the stanza (decision 3's
  commands, `$CLAUDE_PROJECT_DIR`). Drop the "Hooks run from the workspace root … no
  configuration" sentence, which the new commands make moot.
- **EXPECTED FAILURE** (probed): `AssertionError`. The README's commands are
  `python3 .claude/hooks/stop_hook.py` / `bash_hook.py`.
- **REFACTOR (the docs, commit `docs: …`):**
  - `README.md`: under "Quick start", add `tdd init --skill claude-code   # also scaffold the
    Claude Code skill and hooks; see tdd docs hooks`. In the Commands table, change the row to
    `` `tdd init [--skill claude-code [--update-skill]]` / `tdd doctor` ``. In "Enforcement
    boundary", say the hooks are installed by `tdd init --skill claude-code`.
  - `examples/skills/tdd-drive/README.md`: **Installation** becomes `tdd init --skill
    claude-code` (skill, hooks and their wiring together, from the installed copies). The
    `mkdir`/`cp` lines become the manual fallback. Under "Adapting it", note that
    `metadata.verb_set_version` is what `tdd doctor` checks, so keep it when customising.
  - `examples/claude-code-hooks/stop_hook.py` / `bash_hook.py`: in each module docstring,
    replace "Wire it up in `.claude/settings.json` — see README.md in this directory." with
    "`tdd init --skill claude-code` installs and wires it; `tdd docs hooks` shows the manual
    setup." Docstrings only, no code.
  - `src/tddcli/docs.py`: the `skill` topic's summary becomes "a complete driving skill for
    Claude Code: `tdd init --skill claude-code` installs it", and the `hooks` summary gains
    ", installed by `tdd init --skill claude-code`".
  - `src/tddcli/cli.py`: the `LOCAL_VERBS` comment says `init` writes `tdd.toml` *and the
    harness files*. Comment only.
  - `docs/harness-integration.md`: in the intro bullets, add that `tdd init --skill
    claude-code` writes both the skill and the hooks from the installed copies, and that
    `tdd doctor` checks the skill's `metadata.verb_set_version`.
  - `docs/PRD.md`: the `tdd init` row in the command table gains `--skill <harness>` /
    `--update-skill`.
  - `CHANGELOG.md` under `## [Unreleased]`, `### Added`: **`tdd init --skill claude-code`**
    (#114). It covers what is written, the settings policy, `--update-skill`, the refusal
    reasons, the new force-included hook scripts, and the `driving skill version` doctor check.

## Behaviour census

| Promise | Test |
|---|---|
| shipped skill declares the binary's versions | cycle 2 |
| init writes the installed skill | cycle 3 |
| unknown harness refused, nothing written | cycle 4 |
| init writes the installed hooks | cycle 5 |
| hooks ship in the wheel | cycle 6, plus the wheel smoke test in Done-criteria |
| missing install file refused, nothing written | cycle 7 |
| tdd.toml kept with `--skill`; `--force` regenerates it | cycle 8 |
| settings.json written when absent, reported `written` | cycle 9 |
| existing settings.json untouched (valid or not), stanza and nag handed over | cycle 10 |
| already-wired settings reported `wired`, no nag | cycle 11 |
| differing file refused, with and without `--force`, nothing written | cycle 12 |
| `--update-skill` replaces | cycle 13 |
| `--update-skill` alone refused | cycle 14 |
| doctor: drift fails and names the remedy; undeclared/unusable passes; absent adds no check; consumes the real shipped skill | cycle 15 |
| manual-install README matches what init writes | cycle 16 |
| plain `tdd init` unchanged | existing `tests/test_init_detection.py` (4 tests), run every cycle |
| installed copies preferred over a checkout | cycles 3 and 5 (the `packaged` fixture) and cycle 1's guard tests |

Accepted multi-form surface of the new flags (E-12c): `--skill claude-code` and
`--skill=claude-code` are argparse-equivalent (not separately pinned). Unknown values are
cycle 4. `--update-skill` alone is cycle 14. `--force` with `--skill` is pinned on both of its
paths in cycles 8 and 12. `--skill` with no value exits 2 from argparse with no envelope, as
every value-taking flag in this CLI does. Not pinned.

Fake vs real (E-10):

| Seam | Fake | Real | Untested real path | Ruling |
|---|---|---|---|---|
| `docs._PACKAGED` (`packaged` fixture) | a tmp `_docs` holding three one-line files | the wheel's `tddcli/_docs` | the wheel's actual layout | acceptable: cycle 6 pins the force-include map, and Done-criteria runs `init --skill` from a built wheel |

No invariant registry exists in this repo. Mirrors: the hooks README stanza and
`Harness.settings` (parity, cycle 16), and the shipped `SKILL.md` versions and `envelope.py`
(parity, cycle 2). There are no sweeps. No existing test changes (`modifies_tests` is empty
throughout). Planning grepped for monkeypatches through `docs.` and found only
`docs._PACKAGED`/`docs._SOURCE` in `tests/test_docs_command.py`, which cycle 1 keeps working.

## Execution

This plan is executed through `tdd-cli`. **You run every command below yourself** — do not ask the
user to start the run. `tdd run start` records which model is executing, resolved from your own
session; a run started by anyone else attributes this work to the wrong agent.

    git checkout -b issue-114-init-skill-scaffold        # first, before anything else
    tdd doctor                                           # healthy, or failing only for projects this plan cannot reach
    tdd run start --plan tasks/issue-114-init-skill-scaffold.md

`tdd doctor` checks every project; `tdd run start` probes only the ones the plan declares and
those downstream of them through an `[artifact]`. A failing check on a project outside that set
does not stop the run: note it and go on. Any other failing check stops it.

If the branch already exists, do not force-checkout and do not pick another name: check it out
only if it carries this plan's commit and no unrelated work, otherwise stop and ask.

**Referee.** Use the released `tdd` on `PATH` (`tdd --version`), never an editable install of
this working tree. No schema or verb-set version changes in this plan (decision 11).

Then repeat until done: read `next_action.verb`, do exactly what it says, run `tdd advance`.
Stop when `next_action.terminal` is `true`.

When `next_action.terminal` is `true`, finish the run: render the friction log, commit it, and
raise the PR — see Done-criteria below.

- `tdd advance` is the only command that changes phase. Do not `git add` or `git commit` — the
  tool stages and commits, deriving the file set from the phase.
- The baseline is captured at `run start` and subtracted from later verdicts. The suite was
  green at the plan's base in a fresh worktree (722 passed, 2026-10-29), so expect
  `baselines: {tddcli: 0}`.
- Verbs this plan will hit:
  - `create_stub` (cycles 3 and 13: the argparse flag only), `write_test`,
    `write_implementation`, `refactor_or_advance` (cycle 1 is refactor-only);
  - `run_sensitivity_check` → `tdd sensitivity begin|check|end`, if a test passes on arrival.
    No cycle here is a pin, so a pre-pass means an earlier GREEN over-built. Say so with
    `tdd annotate --key plan_defect` or `friction_note`;
  - `resolve_blocker` → `tdd blocker --kind <plan_defect|regression|bad_red|tooling> --detail '...'`;
  - `confirm_cycle_applicable` on a non-existent cycle → `tdd cycle skip --reason`.

  This plan declares no annotation keys beyond the reserved `plan_defect` and `friction_note`.

**Minimal GREEN, per cycle. Add this and nothing earlier:**

- cycle 1: `docs.shipped`, with `Topic.resolve` delegating. No behaviour change.
- cycle 2: the `metadata` block in `SKILL.md`. No code.
- cycle 3: `harness.py` with `Scaffold`, `Harness(name, files)`, and `HARNESSES` holding the
  skill file only. `cmd_init` writes it after `tdd.toml`. No refusals, no hooks, no settings,
  no `result.harness`.
- cycle 4: `unknown_harness`, checked before `tdd.toml` is written.
- cycle 5: the two hook `Scaffold`s.
- cycle 6: the two force-include lines in `pyproject.toml`.
- cycle 7: `missing_from_install` preflight.
- cycle 8: keep an existing `tdd.toml` under `--skill` (`config: "kept"`), unless `--force`.
- cycle 9: `Harness.settings_path` / `settings`, written when absent, and `result.harness` with
  `name` and `settings: "written"`. **No** existing-file branch yet.
- cycle 10: the existing-file branch, which leaves the file alone and reports `not_written`,
  `settings_stanza` and the detail sentence. **No** JSON parsing yet.
- cycle 11: parse and detect `wired`. A parse failure or a non-object is `not_written`
  (cycle 10's malformed row holds you to this).
- cycle 12: `harness_files_differ`, before anything is written, ignoring `--force`.
- cycle 13: `--update-skill` skips cycle 12's refusal.
- cycle 14: `skill_required`, first in the preflight.
- cycle 15: `Harness.skill`, `harness.declared_versions`, and the doctor check.
- cycle 16: the hooks README (GREEN), then every other doc in REFACTOR.

## Done-criteria

**Before finishing:** run `tdd log render --out tasks/friction-logs/issue-114-init-skill-scaffold-friction.md` and `tdd metrics`. Report the plan-fidelity section — declared vs delivered vs skipped — and every integrity event. Do not narrate what the ledger already records.

**Wheel smoke test** (CI's smoke test only runs `tdd --help`, so this is the one place the
packaged path is exercised end to end). From the worktree root:

    uv build -q -o /tmp/tdd114-dist
    uv venv -q /tmp/tdd114-smoke && VIRTUAL_ENV=/tmp/tdd114-smoke uv pip install -q /tmp/tdd114-dist/*.whl
    mkdir /tmp/tdd114-scratch && cd /tmp/tdd114-scratch && git init -q
    /tmp/tdd114-smoke/bin/tdd init --skill claude-code
    ls .claude/skills/tdd-drive/SKILL.md .claude/hooks/tdd_stop_hook.py .claude/hooks/tdd_bash_hook.py .claude/settings.json

The envelope must be `ok: true` and all four files must exist. Put the envelope in the PR body,
then delete the three `/tmp/tdd114-*` paths. A failure here is work: fix it in this branch.

Then commit the friction log and raise the PR:

    git add tasks/friction-logs/issue-114-init-skill-scaffold-friction.md
    git commit -m "docs: friction log for issue-114-init-skill-scaffold"

Then invoke the **`raise-pr` skill** (`/raise-pr`), which runs the quality gates, pushes the
branch and opens the PR against `main`. Do not push or call the GitHub API by hand. If a gate
fails, fix it and re-run the skill — a failed gate is work, not a reason to hand back.

The PR body says `Closes #114`.

Docs are deliverables. Each of these must be non-empty (cycle 16), or the PR body says which
cycle dropped it and why:
- `git diff --stat origin/main -- README.md`
- `git diff --stat origin/main -- examples/claude-code-hooks/README.md`
- `git diff --stat origin/main -- examples/skills/tdd-drive/README.md`
- `git diff --stat origin/main -- docs/harness-integration.md`
- `git diff --stat origin/main -- docs/PRD.md`
- `git diff --stat origin/main -- CHANGELOG.md`

This adds a CLI flag with a JSON envelope. Nothing visual changes, so no demo recording is
required.
