---
closes: 58
cycles:
  - n: 1
    project: tddcli
    title: "parse_cycle accepts a per-cycle meta mapping onto DeclaredCycle.meta"
    test: "tests/test_contract.py::test_parse_cycle_accepts_meta_mapping"
    files: ["src/tddcli/contract.py"]
    commit_red: "test: per-cycle meta mapping parses onto DeclaredCycle"
    commit_green: "feat: DeclaredCycle.meta parsed from reserved per-cycle meta key"

  - n: 2
    project: tddcli
    title: "meta survives the cycles_to_json/cycles_from_json storage round-trip"
    test: "tests/test_contract.py::test_meta_survives_storage_round_trip"
    files: ["src/tddcli/contract.py"]
    commit_red: "test: meta round-trips through cycles_to_json/cycles_from_json"
    commit_green: "feat: round-trip meta through to_dict/from_dict"

  - n: 3
    project: tddcli
    title: "non-mapping meta hard-fails registration with a ContractError"
    test: "tests/test_contract.py::test_non_mapping_meta_raises_contract_error"
    files: ["src/tddcli/contract.py"]
    commit_red: "test: non-mapping meta is rejected"
    commit_green: "feat: validate meta shape, reject non-mapping"

  - n: 4
    project: tddcli
    title: "other unknown per-cycle keys remain silently ignored (leniency pin)"
    test: "tests/test_contract.py::test_unknown_per_cycle_keys_are_silently_ignored"
    pin_cycle: true                 # characterisation of today's tolerance; passes on arrival
    commit_pin: "test: pin the unknown per-cycle key tolerance"
---

# Issue #58 — reserved per-cycle `meta:` passthrough for authored-at-plan-time metadata

https://github.com/geuben/tdd-cli/issues/58
Task file: `tasks/issue-58-cycle-meta-passthrough.md`

## Context

The plan-contract parser is *lenient*: `parse_cycle` in `src/tddcli/contract.py` reads
only the keys it recognises, via `raw.get(...)`, so any extra per-cycle key an author
writes — `covers: [...]`, say — is silently dropped rather than hard-failed. That
tolerance is real and useful (it keeps authors from tripping over their own annotations),
but it is *write-only*: an unknown key is frozen into the plan-blob hash (the blob sha is
taken over the raw committed file bytes, R7.2), yet the parser never surfaces it. It is
not on `DeclaredCycle`, not in `to_dict`/`from_dict`, not in `cycles_to_json`/
`cycles_from_json`, and so never reaches the parsed contract, the ledger, or the friction
log. Authored intent is committed and hashed but unreadable.

This issue adds **one** reserved, documented per-cycle passthrough: a `meta:` mapping.
Its contents are opaque — no key vocabulary is enforced — but its *shape* is validated: a
non-mapping `meta` is a defect and hard-fails registration like any other malformed
front-matter (R7.10). `meta` parses into a new `DeclaredCycle.meta: dict` (default empty)
and round-trips through both storage seams, so authored metadata is *both* hash-frozen
*and* readable back out of the ledger.

`meta` is deliberately distinct from `annotation_keys`. `annotation_keys` is a top-level
list declaring the *run-time* judgement-annotation vocabulary an agent may volunteer via
`tdd annotate` — a different concept living on `PlanContract`, not on a cycle. Do not
overload it.

Ordering: cycle 1 gets `meta` off the raw mapping and onto the dataclass; cycle 2 forces
it through the JSON storage round-trip (the seam the ledger actually uses); cycle 3 adds
the shape guard; cycle 4 pins the *surrounding* leniency so the reserved key is understood
as one documented exception to a tolerance that otherwise stays exactly as it is.

## Verified repo facts

*Every fact below was read out of the codebase during hardening — none are asserted from
memory. Locators are real function names and real file paths; grep for them at execution
time.*

- **`parse_cycle(raw, config)`** (`src/tddcli/contract.py`, ~line 102) constructs and
  returns a `DeclaredCycle` reading only known keys: `n`, the kind flags (`pin_cycle`,
  `contract_cycle`, `refactor_cycle`), `tests`/`test`, `projects`/`project`, `title`,
  `files`, `stub_expected`, `modifies_tests`, and `commit_{red,green,refactor,pin}`. There
  is **no** `meta` read today, and no rejection of extra keys — an unknown key on a cycle
  is neither stored nor an error. This is the leniency cycle 4 pins.
- **`DeclaredCycle`** (dataclass, ~line 31) has fields `ordinal`, `kind`, `projects`,
  `tests`, `title`, `files`, `stub_expected`, `modifies_tests`, `commit_messages`. **No
  `meta` field exists** — so a test reading `parse(...).cycles[0].meta` today raises
  `AttributeError`. That is cycle 1's expected RED.
- **`DeclaredCycle.to_dict`** (~line 43) emits exactly `n, kind, projects, tests, title,
  files, stub_expected, modifies_tests, commit_messages` — no `meta`. **`from_dict`**
  (~line 56) reads those same keys with `d.get(...)` defaults and would ignore a `meta`
  key in the dict. Both must gain `meta` for cycle 2.
- **`cycles_to_json(cycles)`** (line 232) is `json.dumps([c.to_dict() for c in cycles])`;
  **`cycles_from_json(blob)`** (line 236) is
  `[DeclaredCycle.from_dict(d) for d in json.loads(blob)]`. They delegate straight to
  `to_dict`/`from_dict`, so once cycle 2 fixes those two the JSON seam carries `meta`
  automatically — which is exactly why cycle 2's test drives the *storage* seam
  (`cycles_from_json(cycles_to_json([...]))`) rather than `to_dict`/`from_dict` in
  isolation: one test through the real seam pins all four functions.
- **Storage round-trip is real, not hypothetical.** The parsed cycles are serialised at
  registration — `cli.py`, `declared_cycles=contract_mod.cycles_to_json(parsed.cycles)`
  — into the `plan_contract.declared_cycles` column (`ledger.py`, `TEXT NOT NULL`,
  `-- json`), and read back by `Engine.__init__` (`machine.py`,
  `self.declared = contract_mod.cycles_from_json(self.contract_row["declared_cycles"])`)
  and by `cmd_run_start` (`cli.py`). So `meta` surviving `cycles_to_json` →
  `cycles_from_json` is precisely what makes it readable off a run.
- **`ContractError`** (~line 27) is the malformed-front-matter exception; `parse_cycle`
  already raises it for other shape defects (e.g. `commit_{phase}` that is not a string,
  ~line 165: `commit_{phase_key} must be a string`). Cycle 3 follows that exact pattern
  for `meta`.
- **`parse(text, plan_path, config=None)`** (~line 181) is the public entry the tests use;
  it calls `parse_cycle` per raw cycle and sorts by ordinal. `tests/test_contract.py`
  drives everything through `parse` with inline front-matter strings — no `config` passed,
  so project names are not validated against a registry (the `config is not None` guard at
  ~line 152 is skipped). Use `project: backend` in the inline YAML as the existing tests
  do; it need not be `tddcli` inside a `parse`-only unit test.
- **`tests/test_contract.py` exists** and imports
  `from tddcli.contract import CONTRACT, PIN, STANDARD, ContractError, parse`. Its cases
  build inline `"""---\ncycles:\n ...---"""` strings and assert on
  `parse(body, "tasks/p.md").cycles[0]` (see `test_declared_front_matter_parses_cycles`,
  `test_pin_cycle_is_a_distinct_kind`, `test_cycle_without_project_hard_fails`). Match that
  style. Cycles 2 additionally needs `cycles_to_json, cycles_from_json` added to the import
  line — they are not imported yet.
- **No existing test constructs `DeclaredCycle` with positional args** in
  `tests/test_contract.py`, and `meta` is added as a keyword field with a
  `field(default_factory=dict)` default, so adding it breaks no existing construction.
  `tests/test_release_surface.py` inserts a `plan_contract` row with
  `declared_cycles="[]"` — an empty cycle list — so it is untouched by a new per-cycle
  field.
- **README** documents the per-cycle vocabulary in the `## Plan contracts` section
  (`README.md`, ~lines 186–214): a fenced YAML example listing `project`, `title`, `test`,
  `stub_expected`, `commit_red`/`commit_green`, `pin_cycle`, `contract_cycle`, `tests`, and
  top-level `annotation_keys`. This is where `meta:` and a one-line note on the
  unknown-key tolerance belong — a post-run doc follow-up, not a cycle (see Done-criteria).
- **Baseline for this repo is `{"tddcli": 0}`** — the config project name is `tddcli`.
  `run start` captures it; anything else at arrival means a moved branch — stop.

## Cycle detail

*Expected failure per cycle, grounded in the code above; minimum GREEN; resist later
cycles' behaviour.*

### Cycle 1 — parse accepts a meta mapping

**Expected RED (probe-verified):** `AttributeError: 'DeclaredCycle' object has no attribute
'meta'` — the dataclass has no such field, so reading `parse(body, ...).cycles[0].meta`
fails. Confirmed empirically during hardening: `parse(<cycle with a meta mapping>).cycles[0].meta`
raises exactly that `AttributeError` today.

Test (`test_parse_cycle_accepts_meta_mapping`): inline front-matter, one standard cycle
carrying `meta:` as a mapping, e.g.
```yaml
    meta:
      covers: ["REQ-1", "REQ-2"]
      author: "planning"
```
Assert `parse(body, "tasks/p.md").cycles[0].meta == {"covers": ["REQ-1", "REQ-2"],
"author": "planning"}`. Also assert a cycle with **no** `meta` yields `meta == {}` (the
default).

GREEN (minimal): add `meta: dict = field(default_factory=dict)` to `DeclaredCycle`, and in
`parse_cycle`'s constructor call add `meta=raw.get("meta", {})`. **Do not** validate the
shape yet and **do not** touch `to_dict`/`from_dict` — those are cycles 3 and 2. Resist.

### Cycle 2 — meta survives the storage round-trip

**Expected RED:** assertion failure — the round-tripped cycle's `meta` is empty
(`{}`), because `to_dict` does not emit `meta`, so `cycles_from_json` reconstructs the
default. The asserted non-empty mapping `!= {}`.

Test (`test_meta_survives_storage_round_trip`): parse a cycle with a non-trivial `meta`
mapping, then drive it through the real storage seam —
`restored = cycles_from_json(cycles_to_json(contract.cycles))` — and assert
`restored[0].meta == <the same mapping>`. Add `cycles_to_json, cycles_from_json` to the
module import. This one test pins all four functions (`to_dict`/`from_dict` via the JSON
seam that the ledger uses).

GREEN: add `"meta": self.meta` to `to_dict`, and `meta=d.get("meta", {})` to `from_dict`.
`cycles_to_json`/`cycles_from_json` need no change — they delegate.

### Cycle 3 — non-mapping meta is rejected

**Expected RED:** *no exception is raised* — after cycle 1, `raw.get("meta", {})` stores a
non-mapping value verbatim, so `pytest.raises(ContractError)` fails because nothing
raises. (The test asserts the raise; today's code silently accepts.)

Test (`test_non_mapping_meta_raises_contract_error`): inline front-matter with
`meta: "not a mapping"` (a string) on an otherwise valid cycle;
`with pytest.raises(ContractError, match="meta must be a mapping")`. Consider a second
assertion for a list-valued `meta` in the same test to nail "mapping, not just non-string".

GREEN: in `parse_cycle`, before constructing the cycle, read `meta = raw.get("meta", {})`
and `if not isinstance(meta, dict): raise ContractError(f"cycle {ordinal}: meta must be a
mapping")`; pass that validated `meta` into the constructor. Mirror the existing
`commit_{phase}` shape check.

### Cycle 4 — unknown per-cycle keys stay ignored (leniency pin)

**Pin cycle — passes on arrival by design.** This characterises today's tolerance so the
reserved `meta:` key is understood as the *one* documented exception, and so a future
change that starts hard-failing unknown keys must break a red test on purpose.

**Expected on arrival:** GREEN with no code change. If it is RED, the tolerance has already
changed — stop and record a `plan_defect`; do not "fix" production code to make a pin pass.

Test (`test_unknown_per_cycle_keys_are_silently_ignored`): inline front-matter with an
arbitrary unknown key on a valid cycle, e.g. `covers: ["REQ-9"]` (a bare authored key, not
under `meta`). Assert that `parse(body, ...)` succeeds, the cycle parses, and the unknown
key is *not* surfaced — neither raised nor captured in `meta` (`cycle.meta == {}`). This
distinguishes the reserved passthrough from the ambient tolerance.

**Probe-verified:** during hardening, `parse(<cycle with a bare `covers:` key>)` succeeded,
the cycle parsed (ordinal intact), and nothing was raised — the tolerance holds today, and
cycles 1–3 only add `meta` handling, which does not change how a *non-*`meta` unknown key is
treated. So this pin passes on arrival both now and after cycles 1–3.

Because a pin cycle declares a `test` and passes on arrival, `tdd advance` will route a
run-sensitivity check on it (`run_sensitivity_check`) — follow the verb, run
`tdd sensitivity begin|check|end` as instructed. The test asserts behaviour that already
holds; do not weaken it to force a RED. **Sensitivity-check hint (a leniency pin is
unusual):** the mutation that must make this test fail is to *add* the very intolerance the
pin denies — e.g. temporarily have `parse_cycle` capture the unknown key into `meta` (so
`cycle.meta != {}`) or `raise ContractError` on an unrecognised key. `tdd sensitivity begin`
snapshots, apply that mutation, `tdd sensitivity check` confirms the test now fails, then
`tdd sensitivity end` restores byte-identical. Do not leave the mutation in.

## Deliberate scope cuts (do not build)

- **No `meta` key vocabulary.** `meta` is opaque by design — only its shape (a mapping) is
  validated. Do not enforce, whitelist, or type-check any keys inside it. That is the whole
  point of a passthrough.
- **Do not surface `meta` in the friction log, ledger events, render, or fleet output.**
  This issue makes `meta` *readable back off the parsed contract*; wiring it into any
  projection is a separate concern with its own issue. `render.py` and `fleet.py` already
  read `declared_cycles` JSON directly (`render.py`; `fleet.py`) and will carry
  the extra key harmlessly — leave them be.
- **Do not touch `annotation_keys`.** It is a top-level run-time annotation vocabulary on
  `PlanContract`, a different concept. `meta` is per-cycle, authored, opaque.
- **Do not tighten the unknown-key tolerance.** Cycle 4 pins it as-is. Hard-failing unknown
  per-cycle keys is a deliberate future decision, not this issue.
- **No migration of the `declared_cycles` column.** It is untyped JSON `TEXT`; an added
  object key needs no schema change, and older rows without `meta` reconstruct the `{}`
  default via `from_dict`'s `d.get("meta", {})`.
- **README/PRD documentation** of `meta:` and the tolerance note: same PR, after the run is
  terminal, as ordinary commits — not a cycle (see Done-criteria).

## Execution

This plan is executed through `tdd-cli`. **You run every command below yourself** — do not
ask the user to start the run. `tdd run start` records which model is executing, resolved
from your own session; a run started by anyone else attributes this work to the wrong
agent.

**Referee rule:** run the *released* `tdd` **0.7.0**, never this working tree's editable
install. Do not work in a shell with this repo's `.venv` activated. Verify before starting:
`tdd --version` → **0.7.0**.

> **Environment blocker found at hardening (2026-08-23):** `~/.local/bin/tdd` is stale at
> **0.6.0**, which understands ledger schema only up to v2 and *cannot open this repo's
> v3 ledger* — `tdd doctor` fails with "written by a newer tdd-cli". Meanwhile `which tdd`
> may resolve to a `.venv` on `PATH`. Before starting you MUST have 0.7.0 as the `tdd` you
> invoke: `uv tool upgrade tdd-cli` (or reinstall) so `~/.local/bin/tdd --version` → 0.7.0,
> and confirm `which tdd` is a 0.7.0 binary that is **not** `/Volumes/SSD/repos/tdd-cli/.venv`
> (this working tree's own editable install). A separate 0.7.0 clone is fine.

The suites under test are still this working tree's code; only the controller is pinned.

The branch `feat/58-cycle-meta` already exists — it was created at hardening and carries
this plan's commit. Check it out; if it has grown unrelated work, stop and ask.

    git checkout feat/58-cycle-meta                 # exists: created at hardening, carries this plan
    tdd doctor                                      # must report healthy: true
    tdd run start --plan tasks/issue-58-cycle-meta-passthrough.md

`tdd doctor` must be green first: if it reports "worktree clean" failing on *other*
uncommitted `tasks/issue-*.md` files (sibling plans not part of this work), commit, stash,
or gitignore them before `run start`.

Then repeat until done: read `next_action.verb`, do exactly what it says, run
`tdd advance`. Stop when `next_action.terminal` is `true`.

When `next_action.terminal` is `true`, finish the run: render the friction log, commit it,
and raise the PR — see Done-criteria below.

- `tdd advance` is the only command that changes phase. Do not `git add` or `git commit` —
  the tool stages and commits, deriving the file set from the phase.
- The baseline is captured at `run start` and subtracted from later verdicts. Expected
  baseline for this repo: `{"tddcli": 0}` — anything else means a moved branch; stop.
- Verbs this plan can hit: `run_sensitivity_check` → `tdd sensitivity begin|check|end`
  (expected on the cycle-4 pin, which passes on arrival); `resolve_blocker` →
  `tdd blocker --kind --detail` (kinds: `plan_defect`, `tooling`, `regression`,
  `pre_existing_failure`); `confirm_cycle_applicable` on a cycle the codebase has outgrown
  → `tdd cycle skip --reason`. This plan declares no `annotation_keys`.

## Done-criteria

**Before finishing:** run
`tdd log render --out tasks/friction-logs/issue-58-cycle-meta-friction.md` and
`tdd metrics`. Report the plan-fidelity section — declared vs delivered vs skipped — and
every integrity event. Do not narrate what the ledger already records.

Then the documentation follow-up, committed as ordinary commits on the branch after the
run is terminal: in `README.md`'s `## Plan contracts` section, add `meta:` to the per-cycle
vocabulary (a mapping of opaque authored metadata, hash-frozen and readable back) and a
one-line note that other unknown per-cycle keys are tolerated but dropped — the documented
distinction cycle 4 pins.

Then commit the friction log and raise the PR:

    git add tasks/friction-logs/issue-58-cycle-meta-friction.md
    git commit -m "docs: friction log for issue-58-cycle-meta"

Then invoke the **`raise-pr` skill** (`/raise-pr`), which runs the quality gates, pushes
the branch and opens the PR against `main`. Do not push or call the GitHub API by hand. If
a gate fails, fix it and re-run the skill — a failed gate is work, not a reason to hand
back.
