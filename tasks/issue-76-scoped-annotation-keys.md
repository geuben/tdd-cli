---
closes: 76
cycles:
  - n: 1
    project: tddcli
    pin_cycle: true                 # characterises today's gate; passes on arrival by design
    title: "a contract stored before scoping still requires every key at close"
    test: "tests/test_annotation_scope.py::test_a_contract_stored_before_scoping_still_requires_every_key_at_close"
    commit_pin: "test: pin the annotation gate for contracts stored before scoping"
  - n: 2
    project: tddcli
    title: "annotation_keys entries resolve onto the cycles they apply to"
    test: "tests/test_annotation_scope.py::test_annotation_keys_resolve_onto_the_cycles_they_apply_to"
    files: ["src/tddcli/contract.py"]
    commit_red: "test: scoped annotation keys must resolve onto their cycles"
    commit_green: "feat: annotation_keys entries may be scoped by applies_to or projects"
    commit_refactor: "refactor: tidy annotation key resolution"
  - n: 3
    project: tddcli
    title: "a scoped key is required only on the cycles it applies to"
    test: "tests/test_annotation_scope.py::test_a_scoped_key_is_required_only_on_the_cycles_it_applies_to"
    files:
      - "src/tddcli/contract.py"
      - "src/tddcli/machine.py"
      - "README.md"
      - "docs/PRD.md"
      - "examples/skills/tdd-handoff/SKILL.md"
    commit_red: "test: a scoped annotation key must not be demanded outside its scope"
    commit_green: "feat: the close gate demands each annotation key only where it applies"
    commit_refactor: "refactor: tidy the annotation close gate"
  - n: 4
    project: tddcli
    title: "malformed annotation_keys entries hard-fail registration"
    test: "tests/test_annotation_scope.py::test_malformed_annotation_key_entries_hard_fail"
    files: ["src/tddcli/contract.py"]
    commit_red: "test: malformed annotation key entries must hard-fail"
    commit_green: "feat: refuse malformed annotation key scopes at registration"
    commit_refactor: "refactor: tidy annotation key validation"
  - n: 5
    project: tddcli
    title: "the friction log warns of a declared check no delivered cycle carried"
    test: "tests/test_annotation_scope.py::test_the_friction_log_warns_of_a_scoped_key_no_delivered_cycle_carried"
    files:
      - "src/tddcli/render.py"
      - "README.md"
      - "docs/PRD.md"
      - "CHANGELOG.md"
    commit_red: "test: the friction log must warn of a declared check that never ran"
    commit_green: "feat: the friction log warns when a declared check never ran"
    commit_refactor: "refactor: tidy the never-ran warning"
  - n: 6
    project: tddcli
    pin_cycle: true                 # passes on arrival once cycle 5 lands: the rule is uniform by design
    title: "a plain key warns too when the run delivered no cycle"
    test: "tests/test_annotation_scope.py::test_the_friction_log_warns_of_a_plain_key_when_no_cycle_was_delivered"
    commit_pin: "test: pin the never-ran warning for plain keys"
---

# Scope declared per-cycle checks to the cycles they apply to

## Context

[#76](https://github.com/geuben/tdd-cli/issues/76) reports a friction-log run in which a plan
declared a check that mattered only to cycles exercising one output format. The tool demanded it
on all 19 cycles, so the log carries 19 lines of `…_status: n/a (<runner> cycle)`. The one cycle
where the check would have mattered cannot be told apart from the noise. The check never actually
ran against a real artifact, and the `n/a` lines hid that.

The issue asks for two things:

1. Let the contract scope a declared check to a subset of cycles (its example:
   `applies_to: [12, 19]`, or `projects: [device-suite]`), and render it only on those cycles.
2. When a check applies to zero executed cycles, say so in the run summary ("declared check
   never ran") instead of writing `n/a` lines.

In tdd-cli, a plan-declared per-cycle check is an **`annotation_keys`** entry (PRD §7.2, R7.5).
`Engine.missing_annotations` (`src/tddcli/machine.py`) returns every contract key that the cycle
has not annotated yet. `_handle_refactor` (`src/tddcli/advance.py`) refuses to close the cycle
with `annotate_cycle` until that list is empty. So the executor has to write a value on every
cycle, and on the cycles where the check does not apply, that value is `n/a`. The friction log
(`render.friction_log`) prints each recorded annotation under its cycle. Nothing in the tool
records which cycles a key was meant for.

### What the planning probes found (E-2, run on `origin/main` in a scratch worktree)

The base suite is green: `722 passed` (fresh `git worktree` of `origin/main`, `uv run pytest -n auto`).

| Probe | Today |
|---|---|
| plan with two refactor cycles and `annotation_keys: ["k"]`, advance on cycle 1 | `next_action.verb == "annotate_cycle"`, `result.missing_annotations == ["k"]`, run still on cycle 1 |
| the same, after removing `annotation_keys` from every stored cycle dict in `plan_contract.declared_cycles` | identical (today the dicts have no such field, so removing it changes nothing) |
| `parse()` of `annotation_keys: ["plan_wide", {name: a, applies_to: [2]}, {name: b, applies_to: 1}]` | `ContractError: annotation_keys must be a list of strings` |
| two refactor cycles, both keys annotated on cycle 1, advance, then `tdd cycle skip` on cycle 2 | the run completes and `run.cycle` is 2 after the close. The friction log's Plan fidelity section reads `- Declared cycles: 2`, `- Delivered: 1   Skipped: 1`, `- Never reached: none`, `- Human interventions: 0`, then a blank line. There is no warning line. |
| two refactor cycles, both skipped | the same section with `- Delivered: 0   Skipped: 2`, `- Never reached: none`, then `- Human interventions: 0` |

`tests/test_time_report.py` builds a fixture ledger whose `declared_cycles` is
`[{"n": 1}, {"n": 2}]`, with no `kind` and no `projects`, and renders a friction log from it.
`contract.cycles_from_json` raises `KeyError` on dicts like these, which drives decision 9.

No existing test exercises the `annotate_cycle` gate end to end. The only tests that mention
`annotation_keys` (`tests/test_contract.py`, `tests/test_example_plan.py`) assert the parsed
list of names, which this plan keeps unchanged.

## Design decisions (locked)

1. **The check is an `annotation_keys` entry, and scoping extends that field.** There is no new
   top-level `checks:` key. The `n/a` lines the issue quotes are annotation values, and
   `annotation_keys` is the only plan-declared requirement the tool enforces per cycle. Adding a
   second list that declares the same thing would split one concept in two. Other fields here
   already accept more than one form (`project`/`projects`, `test`/`tests`, and `_as_list`'s
   string-or-list), so widening this one follows the same pattern. *Decided by evidence
   (`Engine.missing_annotations`, PRD R7.5) and convention.*
2. **Each entry is a plain string or a mapping.**
   - `"k"`: required on every declared cycle, exactly as today.
   - `{name: k, applies_to: [12, 19]}`: required only on the cycles with those ordinals.
   - `{name: k, projects: [device-suite]}`: required only on the cycles in those projects.

   The field names `name`, `applies_to` and `projects` come from the issue's own example.
   `PlanContract.annotation_keys` stays a `list[str]` of names in declaration order, and that
   list is what `cmd_plan_register` stores in the `plan_contract.annotation_keys` column, as
   today. *Decided by evidence (the issue).*
3. **The issue's third mechanism, a per-cycle boolean, is not built.** The issue offers three
   alternatives joined by "or": a cycle list, a project, or a per-cycle boolean. Its example
   spells out the first two. A per-cycle boolean selects exactly the same cycles as
   `applies_to`, only written on the cycle instead of on the key, so building it would add a
   second spelling with nothing new to express. `projects` is built because it selects
   differently: it follows the plan's projects, not its numbering. *Decided by evidence (the
   issue's wording and example).* This is a choice between the issue's alternatives, not a
   scope cut.
4. **`applies_to` and `projects` are exclusive on one entry.** Giving both hard-fails, the same
   way the cycle-kind flags do (`parse_cycle`: "cycle kinds are exclusive"). That leaves no
   union-or-intersection rule to define. *Decided by convention.*
5. **A contract cycle is in a `projects` scope when any of its projects is listed.** A contract
   cycle runs in every project it spans (PRD R9.1), so a check on any of those projects concerns
   it. *Decided by evidence (R9.1).*
6. **Scalar forms are accepted.** `applies_to: 12` means `[12]`, and `projects: device-suite`
   means `["device-suite"]`, the same way `_as_list` treats `project`, `test` and `files`.
   Cycle 2's test pins both scalar forms beside the list forms. *Decided by convention.*
7. **Malformed entries hard-fail registration (R7.10), with these exact messages, checked in
   this order.** `parse` raises `ContractError`, and `cmd_plan_register` turns it into its
   existing `malformed plan contract: …` failure.
   1. `annotation_keys` is not a list, or one of its entries is neither a string nor a mapping:
      `annotation_keys must be a list of strings or mappings`.
   2. A mapping whose `name` is missing or is not a non-empty string:
      ``every annotation key mapping needs a string `name` ``.
   3. A name that appears twice, plain or mapped: `annotation key 'k' is declared twice`.
   4. Both `applies_to` and `projects` given:
      `annotation key 'k': applies_to and projects are exclusive`.
   5. Neither given, or the one given is an empty list:
      `annotation key 'k' names no scope: give applies_to or projects, or use the plain string form`.
      This is also what catches a typo such as `applies-to`.
   6. An `applies_to` member that is not an `int`, or is a `bool`:
      `annotation key 'k': applies_to must be a cycle ordinal or a list of them`.
      **Footgun:** `bool` is a subclass of `int` in Python, and YAML `true` would otherwise
      select cycle 1. Test `isinstance(v, bool)` first.
   7. A `projects` member that is not a string:
      `annotation key 'k': projects must be a project name or a list of them`.
   8. An `applies_to` ordinal that the plan does not declare:
      `annotation key 'k': applies_to names cycle 7, which the plan does not declare`.
   9. A `projects` name that no declared cycle uses:
      `annotation key 'k': projects names 'frontend', which no declared cycle uses`.
      This needs no `Config`. Every cycle's projects have already been checked against
      `tdd.toml` when a config is given, so a name outside `tdd.toml` fails here too.

   Rules 8 and 9 mean every scope selects at least one declared cycle, so a key cannot be
   scoped to nothing at plan time. Duplicate names are refused the same way duplicate ordinals
   already are. *Decided by convention (R7.10, `parse`'s duplicate-ordinal and exclusive-kind
   refusals).*
8. **Storage: each declared cycle carries its resolved keys. No ledger shape changes, so no
   `SCHEMA_VERSION` bump.**
   - `DeclaredCycle` gains `annotation_keys: list[str] | None = None`.
   - `parse` sets it on every cycle to the keys that apply there, in declaration order: plain
     keys and in-scope mapped keys interleaved as declared.
   - `to_dict` writes it. `from_dict` reads it with `d.get("annotation_keys")`, so a cycle
     stored before this change reads back `None`.
   - `None` means "every key in the contract's `annotation_keys` column": the contract was
     registered before scoping existed, and its runs keep today's gate. Cycle 1 pins this.

   The `plan_contract.annotation_keys` column stays a JSON list of strings, so an older `tdd`
   reading a newer contract still parses it. It ignores the new per-cycle field (`from_dict`
   builds only the fields it knows) and falls back to requiring every key. That is today's
   behaviour, and it does not crash. #58's `meta` was added to the same JSON without a bump.
   *Decided by convention (the repo note on schema bumps, #58).*
9. **One helper decides what a cycle requires.** `required_annotation_keys(cycle_keys:
   list[str] | None, contract_keys: list[str]) -> list[str]` in `src/tddcli/contract.py`
   returns `list(contract_keys)` when `cycle_keys` is `None`, and `list(cycle_keys)` otherwise.
   - `Engine.missing_annotations` calls it with
     `self.declared_for(cycle_row["ordinal"]).annotation_keys`, or `None` when `declared_for`
     returns `None`.
   - `render.friction_log` calls it per stored cycle dict with `d.get("annotation_keys")`.

   **Footgun:** render must read the raw dicts from `json.loads(contract["declared_cycles"])`,
   never `cycles_from_json`. That function raises `KeyError` on the bare `{"n": 1}` dicts that
   `tests/test_time_report.py`'s fixture ledger stores. *Decided by evidence (both consumers,
   that fixture).*
10. **The warning lives in the friction log's Plan fidelity section.** The friction log is the
    run's rendered summary (PRD §8.5), and its Plan fidelity section is what every plan's
    Done-criteria tell the executor to report.
    - The test: for each name in the contract's `annotation_keys` column, in order, the key's
      scope is the declared ordinals whose `required_annotation_keys` contains it. When no
      cycle in that scope has phase `CLOSED`, the key never ran.
    - Each such key gets a line placed directly after `- Never reached: …`:
      ``- **Declared check never ran:** `<key>` (applies to cycles <n>, <n>)``, with the
      ordinals ascending and joined by `", "`.
    - The rule is the same for every key. A plain key's scope is every declared cycle, so it
      warns only when the run delivered no cycle at all (cycle 6). Skipped and never-reached
      cycles count as not executed.
    - No `tdd metrics` field and no envelope field are added: the issue asks for the run
      summary only.

    *Decided by evidence (the issue, PRD §8.5).*
11. **`tdd annotate` is unchanged.** It still records any key on the open cycle, and the
    friction log still prints exactly the annotations that were recorded
    (`ledger.annotations(cycle["id"])`). The `n/a` lines go away because the gate stops
    demanding them (cycle 3), not because rendering filters anything out. *Decided by evidence
    (`cmd_annotate`, `friction_log`).*
12. **Docs.** Each doc change lands in the cycle that makes its behaviour live:
    - **Cycle 3:**
      - PRD R7.5 gains the mapping form, the exclusivity rule, the any-project rule for
        contract cycles, and the registration refusals.
      - README's "Top-level keys" paragraph for `annotation_keys` says the same.
      - The `annotation_keys` bullet in `examples/skills/tdd-handoff/SKILL.md` (shipped as
        `tdd docs handoff`) tells planners to scope a key that only some cycles concern, because
        an every-cycle key invites `n/a` filler.
    - **Cycle 5:**
      - A new PRD R7.5a states the never-ran warning (decision 10).
      - README's friction-log section says the same, in one sentence.
      - `CHANGELOG.md` gets an `### Added` entry under `## [Unreleased]` that names #76.

    *Decided by convention (`RELEASING.md`, and every earlier plan's docs cycle).*

## Deliberate scope cuts (do not build)

None. Decision 3 picks between the issue's alternatives. It does not defer any part of the issue.

## Fake/real divergence

There are no fakes. Every end-to-end test drives the real CLI in-process (`conftest.run_cli`)
against the `repo` fixture's real pytest project. Cycle 1 rewrites one ledger row through
`Ledger.db`, the way `tests/test_baseline_integrity.py` simulates a run that predates
`start_sha`. That stands in for a contract registered by the released tool. It is
*acceptable*: the rewritten value is exactly the shape the released 0.15.0 stores (probed).

## Mirrors, invariants, guards

- No mirrored implementation: contract parsing exists only in `src/tddcli/contract.py`. The
  split-mode runner and the ledger service carry `declared_cycles` as opaque JSON text.
- No `docs/INVARIANTS.md` in this repo.
- No guard test pins the files in scope. `tests/test_actor_seams.py` is unaffected (no spawn,
  no worktree write).
- Test-side blast radius: none. No existing test asserts the old
  `annotation_keys must be a list of strings` message. `test_declared_front_matter_parses_cycles`
  and `test_example_plan.py` assert the list of names, which stays the same (decision 2).
  `test_meta_survives_storage_round_trip` asserts `meta` only. The time-report fixture has
  `annotation_keys="[]"`, so the warning loop does nothing there. `modifies_tests` is empty.

## Cycles

Every test lives in a new file, `tests/test_annotation_scope.py`, created in cycle 1. Later cycles
add imports as they need them (the lint gate is `ruff check`: no unused imports). It starts with
this module docstring and these helpers:

```python
"""Scoped annotation keys (#76): a declared check required only on the cycles it applies to."""

from __future__ import annotations

import json

from conftest import run_cli, write_plan
from tddcli import gitutil
from tddcli.ledger import Ledger

TWO_REFACTOR = """---
cycles:
  - n: 1
    project: backend
    refactor_cycle: true
    title: "one"
  - n: 2
    project: backend
    refactor_cycle: true
    title: "two"
annotation_keys: KEYS
---
"""


def _plan(keys: str) -> str:
    return TWO_REFACTOR.replace("KEYS", keys)
```

Refactor cycles open straight into `AWAITING_REFACTOR`, and `_handle_refactor` checks for missing
annotations before it stages anything. That makes them the cheapest way to reach the close gate.
Where a cycle must close, the test first writes `(repo / "backend" / "app" / "moved.py")
.write_text("VALUE = 1\n")`, as `test_refactor_cycle_closes_when_the_existing_suite_stays_green`
does.

**Cycle 1 (pin): `test_a_contract_stored_before_scoping_still_requires_every_key_at_close`.**

- **Setup:** fixture `repo`. `plan = write_plan(repo, _plan('["k"]'))`, then
  `run_cli(repo, "plan", "register", plan)`. Open `ledger = Ledger(gitutil.repo_identity(repo))`
  and read `row = ledger.one("SELECT id, declared_cycles FROM plan_contract")`. Load
  `row["declared_cycles"]` as JSON and call `c.pop("annotation_keys", None)` on every dict. Write
  it back with `ledger.db.execute("UPDATE plan_contract SET declared_cycles = ? WHERE id = ?",
  (json.dumps(cycles), row["id"]))` and `ledger.db.commit()`. Then
  `run_cli(repo, "run", "start", "--plan", plan)`, write `moved.py`, and
  `out = run_cli(repo, "advance")`.
- **Single assertion:** `(out["next_action"]["verb"], out["result"]["missing_annotations"]) ==
  ("annotate_cycle", ["k"])`.
- **Why a pin:** today the stored dicts have no `annotation_keys`, so removing it changes nothing
  and the test passes on arrival (probed). Once cycle 3 lands, it is the guard that a stored
  `None` still means "every key" (decision 8). A `from_dict` that defaults to `[]` turns this
  test red in cycle 3's close sweep.
- **Production:** none.

**Cycle 2: `test_annotation_keys_resolve_onto_the_cycles_they_apply_to`.**

- **Setup:** add `from tddcli.contract import parse`. Parse this body with
  `contract = parse(body, "p.md")` (no config, so `frontend` need not exist in any `tdd.toml`):

  ```yaml
  ---
  cycles:
    - n: 1
      project: backend
      refactor_cycle: true
    - n: 2
      project: frontend
      refactor_cycle: true
    - n: 3
      projects: [backend, frontend]
      contract_cycle: true
      tests: ["backend::tests/test_a.py::test_a", "frontend::a.test.ts > a"]
  annotation_keys:
    - plan_wide
    - {name: a, applies_to: [2, 3]}
    - {name: b, applies_to: 1}
    - {name: f, projects: frontend}
    - {name: g, projects: [backend]}
  ---
  ```

- **Single assertion:**

  ```python
  (contract.annotation_keys, [c.annotation_keys for c in contract.cycles]) == (
      ["plan_wide", "a", "b", "f", "g"],
      [["plan_wide", "b", "g"], ["plan_wide", "a", "f"], ["plan_wide", "a", "f", "g"]],
  )
  ```

  This one assertion covers plain keys on every cycle, list and scalar `applies_to`, string and
  list `projects`, the any-project rule for the contract cycle (decision 5), and declaration
  order.
- **Production:** `src/tddcli/contract.py`. Add the `DeclaredCycle.annotation_keys` field
  (decision 8, but not `to_dict`/`from_dict` yet). In `parse`, replace the list-of-strings check
  with resolution: plain names apply everywhere, mapped names to the cycles their scope
  selects. `PlanContract.annotation_keys` becomes the list of names.
- **EXPECTED FAILURE:** `tddcli.contract.ContractError: annotation_keys must be a list of
  strings`, raised by `parse` (probed).

**Cycle 3: `test_a_scoped_key_is_required_only_on_the_cycles_it_applies_to`.**

- **Setup:** fixture `repo`.
  1. `plan = write_plan(repo, _plan('["plan_wide", {name: k, applies_to: [2]}]'))`.
  2. Register the plan, `run start`, and write `moved.py`.
  3. `first = run_cli(repo, "advance")`.
  4. `run_cli(repo, "annotate", "--key", "plan_wide", "--value", "x")`.
  5. `closed = run_cli(repo, "advance")`.
  6. `second = run_cli(repo, "advance")`.
- **Single assertion:**

  ```python
  (
      first["result"]["missing_annotations"],
      closed["run"]["cycle"],
      second["result"]["missing_annotations"],
  ) == (["plan_wide"], 2, ["plan_wide", "k"])
  ```

  On cycle 1, the plain key is demanded and the scoped key is not. Cycle 1 then closes. On
  cycle 2, both are demanded. This is where the parsed scope is consumed (E-3): the value has to
  survive the ledger's JSON round trip and reach the gate.
- **Production:**
  - `src/tddcli/contract.py`: `to_dict` and `from_dict` carry `annotation_keys`, with
    `d.get(...)` so a missing field reads as `None`. Add `required_annotation_keys`
    (decision 9).
  - `src/tddcli/machine.py`: `Engine.missing_annotations` uses that helper. Keep its early
    return when the contract declares no keys.
  - Docs per decision 12, cycle-3 items: PRD R7.5, README's "Top-level keys", and
    `examples/skills/tdd-handoff/SKILL.md`.
- **EXPECTED FAILURE:** `AssertionError: assert (['plan_wide', 'k'], 1, ['k']) == (['plan_wide'],
  2, ['plan_wide', 'k'])`. After cycle 2, registration works, but the gate still demands every
  name in the contract column on every cycle, in contract order. The first probe row shows this.

**Cycle 4: `test_malformed_annotation_key_entries_hard_fail`.**

- **Setup:** add `import re`, `import pytest` and `ContractError` to the `tddcli.contract` import.
  The test is one table, a module-level `REJECTED: list[tuple[str, str]]` of
  `(keys_yaml, message)` rows in this order:

  | `keys_yaml` (substituted for `KEYS` by `_plan`) | message (decision 7) |
  |---|---|
  | `[{name: k, applies_to: [7]}]` | `annotation key 'k': applies_to names cycle 7, which the plan does not declare` |
  | `[{name: k, projects: [frontend]}]` | `annotation key 'k': projects names 'frontend', which no declared cycle uses` |
  | `[{name: k, applies_to: [1], projects: [backend]}]` | `annotation key 'k': applies_to and projects are exclusive` |
  | `[{name: k}]` | `annotation key 'k' names no scope: give applies_to or projects, or use the plain string form` |
  | `[{name: k, applies_to: []}]` | the same as the row above |
  | `[{name: k, projects: []}]` | the same as the row above |
  | `[{applies_to: [1]}]` | ``every annotation key mapping needs a string `name` `` |
  | `[{name: 3, applies_to: [1]}]` | the same as the row above |
  | `[{name: k, applies_to: [true]}]` | `annotation key 'k': applies_to must be a cycle ordinal or a list of them` |
  | `[{name: k, applies_to: ["1"]}]` | the same as the row above |
  | `[{name: k, projects: [3]}]` | `annotation key 'k': projects must be a project name or a list of them` |
  | `["k", {name: k, applies_to: [1]}]` | `annotation key 'k' is declared twice` |
  | `[3]` | `annotation_keys must be a list of strings or mappings` |
  | `k` | the same as the row above |

  The body loops: `for keys, message in REJECTED: with pytest.raises(ContractError,
  match=re.escape(message)): parse(_plan(keys), "p.md")`. Write the messages out in full in
  `REJECTED`, not as "same as above". Every row is one rejected form of one rule ("a malformed
  entry hard-fails", R7.10). The table is E-12c's "each rejected form pinned", kept to one test
  id because the tool cannot target a parametrized test.
- **Production:** `src/tddcli/contract.py`. Add the refusals in decision 7's order, so that each
  row trips exactly its own rule. For example, `[{name: k, applies_to: []}]` must reach rule 5
  before any membership check.
- **EXPECTED FAILURE:** `Failed: DID NOT RAISE <class 'tddcli.contract.ContractError'>` on the
  first row. After cycle 2, an undeclared ordinal simply selects no cycle. If cycle 2 happened to
  refuse it already, the first row it does not refuse fails the same way, or with a `Regex
  pattern did not match` naming the message it expected.

**Cycle 5: `test_the_friction_log_warns_of_a_scoped_key_no_delivered_cycle_carried`.**

- **Setup:** fixture `repo`. Add `run_cli_text` to the `conftest` import.
  1. `plan = write_plan(repo, _plan('["plan_wide", {name: delivered_k, applies_to: [1]},
     {name: skipped_k, applies_to: [2]}]'))`.
  2. Register the plan, `run start`, and write `moved.py`.
  3. Annotate `plan_wide` (`x`) and `delivered_k` (`y`), then `run_cli(repo, "advance")`.
  4. `run_cli(repo, "cycle", "skip", "--reason", "not applicable")`. This completes the run
     (probed).
  5. `lines = run_cli_text(repo, "log", "render").splitlines()` and
     `at = lines.index("- Never reached: none")`.
- **Single assertion:**

  ```python
  lines[at + 1 : at + 3] == [
      "- **Declared check never ran:** `skipped_k` (applies to cycles 2)",
      "- Human interventions: 0",
  ]
  ```

  This pins the line's text, its place in Plan fidelity, and that `plan_wide` and `delivered_k`
  (both carried by the delivered cycle 1) get no line.
- **Production:**
  - `src/tddcli/render.py`, `friction_log`: after the `Never reached` line, apply decision 10.
    Loop over **every** name in `json.loads(contract["annotation_keys"])`, not only mapped ones,
    and use `required_annotation_keys` on the raw stored dicts (decision 9's footgun).
  - Docs per decision 12, cycle-5 items: PRD R7.5a, README's friction-log section, and the
    `CHANGELOG.md` entry.
- **EXPECTED FAILURE:** `AssertionError: assert ['- Human interventions: 0', ''] == ['- **Declared
  check never ran:** ...', '- Human interventions: 0']` (probed: today the line after
  `Never reached` is `Human interventions`, then a blank line).

**Cycle 6 (pin): `test_the_friction_log_warns_of_a_plain_key_when_no_cycle_was_delivered`.**

- **Setup:** fixture `repo`.
  1. `plan = write_plan(repo, _plan('["plan_wide"]'))`. Register it and `run start`.
  2. `run_cli(repo, "cycle", "skip", "--reason", "na")` twice. The run completes (probed).
  3. Build `lines` and `at` as in cycle 5.
- **Single assertion:** `lines[at + 1 : at + 3] == ["- **Declared check never ran:** `plan_wide`
  (applies to cycles 1, 2)", "- Human interventions: 0"]`.
- **Why a pin:** decision 10's rule covers every key, and cycle 5's production loops over every
  name through the shared helper. Under that design this test passes on arrival. It pins that a
  plain key is not exempt. This after-state was reasoned from the design, not probed: probing it
  would mean building cycle 5. If the test fails on arrival, cycle 5 special-cased mapped keys
  against decision 10. Raise `tdd blocker --kind plan_defect` and do not edit the test.
- **Production:** none.

## Execution

This plan is executed through `tdd-cli`. **You run every command below yourself** — do not ask the
user to start the run. `tdd run start` records which model is executing, resolved from your own
session; a run started by anyone else attributes this work to the wrong agent.

    git checkout -b issue-76-scoped-annotation-keys   # first, before anything else
    tdd doctor                                  # healthy, or failing only for projects this plan cannot reach
    tdd run start --plan tasks/issue-76-scoped-annotation-keys.md   # captures baselines, opens cycle 1

`tdd doctor` checks every project; `tdd run start` probes only the ones the plan declares and
those downstream of them through an `[artifact]`. A failing check on a project outside that set
does not stop the run: note it and go on. Any other failing check stops it.

If the branch already exists, do not force-checkout and do not pick another name: check it out
only if it carries this plan's commit and no unrelated work, otherwise stop and ask.

Then repeat until done: read `next_action.verb`, do exactly what it says, run `tdd advance`.
Stop when `next_action.terminal` is `true`.

When `next_action.terminal` is `true`, finish the run: render the friction log, commit it, and
raise the PR — see Done-criteria below.

- `tdd advance` is the only command that changes phase. Do not `git add` or `git commit` — the
  tool stages and commits, deriving the file set from the phase.
- The baseline is captured at `run start` and subtracted from later verdicts. The suite is green at
  the plan's base (verified in a fresh worktree of `origin/main`: `722 passed`). Expect
  `baselines: {tddcli: 0}`.
- The referee is the released `tdd` on `PATH` (the note at the top of `tdd.toml`), never
  `uv run tdd`. This plan changes how the tool reads contracts, but the released referee parses
  this plan's own front matter, which uses only plain forms.
- Verbs this plan will hit:
  - `write_test` (cycles 2–5), `write_test` for a pin (cycles 1 and 6), `write_implementation`,
    `refactor_or_advance`.
  - `run_sensitivity_check` → `tdd sensitivity begin|check|end`, if a RED pre-passes. Mutate the
    increment that cycle added.
  - `annotate_cycle` → `tdd annotate --key --value`. This plan declares no keys of its own;
    `plan_defect` and `friction_note` are reserved.
  - `resolve_blocker` → `tdd blocker --kind <plan_defect|environment> --detail '...'`.
  - `confirm_cycle_applicable` on a non-existent cycle → `tdd cycle skip --reason`.
  - No cycle declares a stub: every test imports only names that exist today (`parse`,
    `ContractError`, `Ledger`, `gitutil`, and the `conftest` helpers).

**Minimal GREEN, per cycle — add this and nothing earlier:**

- cycle 1 is a pin: no production change.
- cycle 2 adds the `DeclaredCycle.annotation_keys` field and resolution in `parse`, and nothing
  else. No `to_dict`/`from_dict` change, no helper, no refusals beyond what resolution needs.
- cycle 3 adds the field to `to_dict`/`from_dict`, adds `required_annotation_keys`, and uses it
  in `Engine.missing_annotations`. It also makes the cycle-3 doc edits. No render change.
- cycle 4 adds decision 7's refusals, and nothing else.
- cycle 5 adds the warning in `friction_log` and the cycle-5 doc edits.
- cycle 6 is a pin: no production change.

## Done-criteria

**Before finishing:** run `tdd log render --out tasks/friction-logs/issue-76-scoped-annotation-keys-friction.md` and `tdd metrics`. Report the plan-fidelity section — declared vs delivered vs skipped — and every integrity event. Do not narrate what the ledger already records.

Then commit the friction log and raise the PR:

    git add tasks/friction-logs/issue-76-scoped-annotation-keys-friction.md
    git commit -m "docs: friction log for issue-76-scoped-annotation-keys"

Then invoke the **`raise-pr` skill** (`/raise-pr`), which runs the quality gates, pushes the
branch and opens the PR against `main`. Do not push or call the GitHub API by hand. If a gate
fails, fix it and re-run the skill — a failed gate is work, not a reason to hand back.

The PR body says `Closes #76`. Cycles 3 and 5 own the docs:

- `git diff --stat origin/main -- docs/PRD.md` must be non-empty, or the PR body says why.
- `git diff --stat origin/main -- README.md` must be non-empty, or the PR body says why.
- `git diff --stat origin/main -- examples/skills/tdd-handoff/SKILL.md` must be non-empty, or the
  PR body says why.
- `git diff --stat origin/main -- CHANGELOG.md` must be non-empty, or the PR body says why.

The visible change is contract syntax and one friction-log line, so no demo recording is
required. In the PR body, quote one scoped `annotation_keys` entry and the friction-log line it
produces when its only cycle is skipped.
