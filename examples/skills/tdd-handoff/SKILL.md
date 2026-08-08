---
name: tdd-handoff
description: Audit and harden an implementation plan before handing it to a lesser agent to execute unsupervised through tdd-cli. Emits the plan's YAML front-matter contract and validates it with tdd plan register. Use when the user says "prepare this plan for handoff", "harden this plan", "handoff review", or before dispatching any plan file to another model for autonomous implementation.
argument-hint: [<plan-path>]
---

## Purpose

Take an existing draft plan and transform it into a form that a lesser agent, executing
literally and minimally, will implement completely. Output is the revised plan — carrying
a registered front-matter contract — plus a short handoff-readiness report. No
implementation code.

This is the planning-side counterpart to the driving skill in
`examples/skills/tdd-drive/`. The hardener runs `tdd plan register`; the executor runs
`tdd doctor` and `tdd run start`. Never start a run on the executor's behalf: executor
identity is recorded from the session that runs `run start`, so a hardener-started run
attributes the work to the wrong agent.

---

## The core failure model

A minimal-GREEN TDD executor treats the plan's **named test list as the entire spec**.
Everything else is advisory and will be dropped:

- **Prose intent** ("...so the device stays logged in") with no test → not built.
- **Bundled test specs** (one RED step asserting three behaviours) → satisfied by the
  cheapest clause; the cycle looks complete.
- **Artifacts created in GREEN steps** (golden fixtures, generated clients) → committed
  but never consumed; detect nothing.
- **Unspecified guards/state machines** → guaranteed omission: minimal-GREEN *forbids*
  code no test demands.
- **Hard-to-test behaviour with no named test seam** → quietly narrowed to whatever the
  harness can express cheaply.
- **Plan/repo contradictions** → the executor follows repo convention, not the plan.
- **Unreachable numeric targets** → the executor either expands scope to chase them or
  writes the criterion off.
- **Silent friction & hidden design flaws** → the executor hacks around awkward designs
  or over-mocks to force tests green, burying architectural flaws instead of surfacing
  them.
- **Unverified setup** — a plan whose cycles were reasoned about but never executed
  ships wrong routes, unmet preconditions, and shadowed guard clauses. **The plan's own
  hedges — "if required", "if needed" — mark the exact spots this happens.**

### Failure modes the tool prevents — if the plan is declared correctly

These need no prose hardening, but the plan must still *declare* them for the tool to
catch them. Getting the declaration wrong reopens the hole:

| Failure mode | Prevented by | What the plan must still declare |
|---|---|---|
| Import-error RED counted as RED | adapter reports `not_collected`, distinct from `not_found` | `stub_expected` per cycle |
| Type-checker-blocked RED commit | staging derives the RED commit from phase | `stub_expected` (signature stubs included) |
| RED-passed-on-arrival recorded as done | cycle cannot close without a verified sensitivity check | correct cycle **kind** |
| Test deletion as conflict resolution | collection diff + `modifies_tests` | `modifies_tests` for authorised edits |
| Bulk-edit completion | one commit per phase, with `TDD-Cycle` trailers | commit messages per phase |
| Self-assessment decoupled from evidence | friction log is a projection of the ledger | `annotation_keys` for judgement fields |
| Baseline asserted from a subset | `tdd run start` measures every project | nothing — automatic |
| Line-number drift | — | still your job (step 1) |

**The tool cannot infer intent.** A cycle whose kind is wrong is worse than one with no
tool at all: a standard cycle mislabelled as a pin will accept a test that never fails,
and the violation is recorded as normal.

---

## Procedure

### 0. If the draft is not cycle-structured, decompose it first

Everything below assumes the plan is a sequence of **cycles** — each with one named
test, a GREEN scope, and commit messages. A freeform draft (prose, a task list, a PRD
excerpt) is not ready for this procedure; restructure it first:

- Decompose the work into cycles matching the body structure of `examples/plan.md` in
  the tdd-cli repository: one behaviour per cycle, in dependency order, each with a
  proposed test name, production target, and an EXPECTED FAILURE line.
- Assign each cycle a provisional kind from the table in step 7 — the probe (step 2)
  will confirm or correct it.
- Carry every promise the prose makes into either a cycle or an explicit scope-cut
  list; step 3 will audit that nothing fell between.

The decomposition does not need to be right — the rest of this procedure exists to
correct it. It needs to be *explicit*, so there is something to correct.

### 1. Read the plan AND probe the repo

Read the full plan. Then verify its claims against the codebase — do not trust the
plan's description of preconditions:

- Do the files, functions, fixtures, and helpers the plan references actually exist at
  the stated paths?
- **Do the HTTP routes, request bodies, CLI flags, and payload shapes exist as
  written?** A route string is a symbol like any other, and it is the one an
  integration test actually calls. Verify every path and body against the
  router/handler definition, not against what the endpoint is *called* in prose. A
  wrong route produces a framework 404 that an executor will misdiagnose as an
  authorization, RLS, or fixture problem and then "fix" by deleting the test.
- **Check the suite is green now.** `tdd run start` captures per-project baselines and
  subtracts them from every later verdict — do not hand-record a baseline, it will
  drift. But if the suite is red, name the failing tests in the plan and say whether
  they are the work or a blocker.
- Does the plan contradict observable repo convention (migrations, schema versioning,
  test layout, DI patterns)? Resolve every contradiction **in the plan now**. Delete
  any "where plan and code disagree, code wins" escape clause; replace with the
  specific resolved decision.
- **Search for tests that already cover the plan's target behaviour.** An
  already-failing test *is* the RED and no new test should be written; an
  already-passing one may mean the cycle is redundant — or that it is a **pin cycle**,
  not a standard one. Grep by behaviour and status code, not just by the plan's
  proposed test name.
- For each cycle, confirm the test harness can actually express the specified
  assertion (see step 9).
- **Convert all raw line numbers to stable anchors.** For every `file.py:N` reference:
  replace it with the function or test name it falls inside, or a grep pattern the
  executor runs at execution time. A line number is acceptable only as a rough hint
  alongside a named anchor, never as the sole locator.
- **Verify this mechanically before dispatch.** Run
  `grep -nE '\.(py|ts|tsx|md):[0-9]+' <plan-file>` — it must return empty. Still the
  most-violated rule in this skill; a passing grep is the only proof it was applied.

### 2. Prove the RED path empirically — do not reason about it

**This is the step that catches the defects reasoning misses.** Static reading tells
you a plan is coherent; it does not tell you whether the executor's first
`client.post(...)` reaches the code under test.

For **at least one cycle per phase**, and for **every cycle touching an endpoint,
fixture, or setup sequence the plan did not inherit verbatim from a passing test**,
write a throwaway probe, run it, record what happened, and delete it.

The probe is not a test. It asserts nothing, prints everything, and ends with
`assert False` so the output surfaces. It must live where the real test will live so
it inherits the same fixtures.

What to extract from it, and put in the plan:

- **Does the setup reach the code under test?** Any status that is not the target and
  not the expected failure means the cycle as written cannot produce a legitimate RED.
- **What is the actual failure mode?** Quote the real output in the cycle's EXPECTED
  FAILURE line.
- **Which preconditions are mandatory?** Every "if required" in a plan is an unexecuted
  assumption; resolve it or say plainly it was not verified.
- **Which guard fires first?** Confirm the intended exception is reachable rather than
  shadowed by an earlier check.
- **Does the test pass or fail on arrival?** This determines the cycle's **kind**
  (step 7) and is the single most consequential thing the probe tells you.

Delete the probe before finishing and confirm the tree is clean (`git status`). Never
commit it.

If the environment genuinely cannot run the probe, say so **in the plan, in the
cycle**, and mark that cycle's setup as unverified.

### 3. Behaviour census — prose vs. tests

List every behaviour the plan's prose promises. For each, find the named test that
pins it. Classify:

- **PINNED** — a single RED test names it. OK.
- **PROSE-ONLY** — promised but no test. Either add a RED cycle for it or move it to
  an explicit "deliberate scope cuts (do not build)" list. No third state.
- **CROSS-BOUNDARY** — pay special attention to consumption across layers: backend
  returns X → is there a test that the *frontend stores/uses* X? A regenerated client
  is not consumption. This is the most common escape.

### 4. Split bundled RED steps

Every RED step must name exactly **one** test asserting **one** behaviour. If a step's
description contains "and", "also", "plus", or a semicolon-list of assertions, split it
into separate cycles.

The tool enforces this: a cycle declaring more than one test is rejected at
registration unless marked `contract_cycle`. Do not reach for `contract_cycle` to
silence that error — it exists only for breaking contract changes where no intermediate
green state is possible (step 7).

### 5. Every cycle names its production target, not just its test file

For each RED cycle the plan must name **both** the test file the test lands in **and**
the production module + function the behaviour lands in. Then **trace the call path
yourself** to confirm the two agree. If the plan's file spec and its production target
imply different modules, one of them is wrong — resolve it before dispatch.

The production target becomes the cycle's `files` list, which is diffed against what
actually changed.

### 6. Stub-first: make every new symbol importable *and type-checkable* before RED

For each cycle that introduces a new module, class, function, **or parameter**, the
minimal stub is created before RED:

- The stub is an empty class, a function that raises `NotImplementedError`, a
  placeholder module, or — for a new argument — a **signature stub**: the parameter
  added with a default and *no reference to it in the body*.
- It must contain **no production logic**. Its only job is to let the test runner load
  the file and let the type checker pass.
- **The stub must satisfy the repo's pre-commit gates** (mypy, ruff, import ordering).

Declare every stub path in the cycle's `stub_expected`. This is load-bearing in two
directions: the RED commit stages declared stubs alongside the test, and anything else
that changed is recorded as implementation written during RED. A declared file that is
*not* a stub is how real implementation sneaks into a RED commit. Declare exactly the
files, no more.

**Deriving the list is a mechanical exercise, not a judgement call — do it for every
cycle:** read the RED test you have specified, list every `import`/`from` in it, and
mark each symbol that does not exist at the stated path *today*. Each one is a
`stub_expected` entry. This is the single most-missed field. Note what the
declaration does and does not buy: it does **not** suppress the `create_stub`
directive — that fires whenever the target is uncollectable, so a driving skill that
writes the test before the stub takes that round trip regardless. What declaring buys
is the accounting: declared files are staged into the RED commit *as stubs*, while an
undeclared file is at best adopted after a directive and at worst recorded as
implementation written during RED.

**`stub_expected` is also where non-test files the RED phase legitimately requires
go**, even when "stub" is a poor name for them: import-contract registries
(`.importlinter`), lint or coverage configs, module `__init__` exports, fixture
indexes. If a new production module cannot be *added* without an accompanying config
entry — because an existing pinned test enforces the pairing — that config file
belongs in `stub_expected` for every cycle that adds a module. Miss it and the same
file is reported as implementation-during-RED in every cycle of the run.

The tool exempts a stub it demanded itself (`create_stub` → the new file joins the RED
commit, recorded as `stub_adopted`), so a miss is recoverable rather than a violation.
**This is a safety net, not a substitute for declaring it.** The exemption covers only
*new* files in the cycle where the directive was issued; an edit to a file already at
HEAD — a config registry, exactly the `.importlinter` case — is still recorded as
implementation written during RED.

RED means "test runs and fails on an assertion." It never means "test crashes on
import" or "test could not be committed."

### 7. Assign every cycle a kind

**The most consequential decision this skill makes.** The tool's whole discipline
rests on it, and it cannot be inferred from the outcome — a standard cycle that passes
on arrival stays a violation and is never silently reclassified.

| Kind | Declare | Use when | The tool then |
|---|---|---|---|
| standard | *(default)* | the test genuinely fails before implementation | requires RED before GREEN |
| `pin_cycle: true` | one test | the test **must pass on arrival** — it characterises existing behaviour before a refactor deletes or restructures it | skips RED, makes the sensitivity check **mandatory**, excludes the cycle from the RED-first violation metric |
| `refactor_cycle: true` | **no test** | call sites move, behaviour is preserved, the existing suite is the guard | opens straight into refactor; the close sweep is the only gate |
| `contract_cycle: true` | 2+ tests, may span projects | a **breaking** contract change where no intermediate green state exists | requires all targets red together, then green together |

Rules:

- Decide the kind from the **probe** (step 2), not from the plan's prose. A preamble
  claiming "every cycle is behaviour-preserving" is not evidence;
  `EXPECTED FAILURE: stub returns None` in the cycle body is.
- **A plan may mix kinds freely, and most refactoring plans do.** Do not let one
  sentence in a preamble set the kind for every cycle — check each one.
- Additive contract changes are **two ordinary cycles**, not a `contract_cycle`.
  Reserve it for the case where both sides must move together.
- A `refactor_cycle` with no close-sweep coverage of the affected area is unguarded.
  If the existing suite does not cover the migrated call sites, add a pin cycle before
  it.

### 8. RED-passed-on-arrival protocol

For every cycle, state the **expected failure mode** ("fails with
`AssertionError: no error raised`").

The tool enforces the response — a passed-on-arrival cycle cannot close without
`tdd sensitivity begin/check/end`, and the restore is verified byte-identical. Your job
is narrower but sharper: decide whether passing on arrival is **expected**
(→ `pin_cycle`) or a **defect** (→ standard cycle, and the executor will be forced
through the check). Guessing wrong in the pin direction is the more dangerous error:
it converts a discipline failure into a sanctioned one.

### 9. Test-seam validation for hard-to-test behaviour

For each behaviour like "persists across sessions", "un-dismissable", "device-only
path": state in the plan **how** it will be tested (which seam, which mock contract,
which harness). If the current harness cannot express it, either add the seam-building
work as its own cycle, or explicitly descope. Never leave the executor to discover
untestability mid-cycle — they will downgrade the test silently.

### 10. Verify that detection claims are actually detectable

Wherever the plan claims a test *detects* something, apply this question:

> Does this test derive its expected value **independently** of the code under test?

If both sides of the comparison call the same production function, the test cannot
detect a change in it. Only an independently-pinned value detects it. Rewrite any
success criterion that overstates what its test proves.

### 11. Fakes and ports: demand the divergence table up front

When a plan introduces test doubles for a repository/port, require the plan to state,
**before execution**:

| Method | Fake behaviour | Real behaviour | Production path left untested |
|---|---|---|---|

Then rule on each row explicitly: *acceptable* (documented, low risk), or *needs an
integration pin* (a named test at the real boundary, added as its own cycle).

### 12. Fixtures and cross-implementation contracts

Any golden fixture, canonical-bytes contract, or wire format consumed by more than one
implementation:

- The fixture is **created and asserted in the same cycle's RED test** — never "commit
  the fixture" as a GREEN sub-step.
- Every consumer implementation gets its **own byte-equality test** against the same
  fixture file, as a named RED step in the consumer's cycle.
- If a consumer's cycle might be deferred, the fixture-assertion test moves to the
  producer's cycle so it can't be orphaned.

Where the artifact is generated (an OpenAPI schema, a generated client), check whether
`tdd.toml` already declares it as an `artifact` with a `check` or `regenerate` command.
If so, freshness is enforced automatically and the plan needs no manual regeneration
step — the tool regenerates and commits separately. If not, and the plan depends on
it, add the artifact edge to `tdd.toml` as part of hardening.

### 13. Guards, state machines, and negative space

Walk every new endpoint/mutation and ask: what transitions are illegal?
(re-invocation, out-of-order calls, acting on superseded resources, idempotency, size
limits). Each guard the product needs gets its own RED test. If a guard is deliberately
absent, write that in scope cuts.

### 14. Enumerate every sweep and migration step

Ban adverbial scope. "Migrate the call sites, highest-cost first", "sweep the
remaining files", "same shape as Phase 2" — each will be executed against whatever
subset the executor happens to find.

For every sweep/migration/"same as above" step:

- **Run the discovery command now** and paste the **exact enumerated file list** into
  the plan.
- Include the command itself so the executor re-derives the list and reports any delta.
- Expand every "same shape as Phase N" into its own named artifacts.
- **Validate the discovery pattern against known variants before trusting its
  output.** A pattern that looks exhaustive usually is not. Deliberately search for
  the variants your regex would exclude and reconcile the counts. An under-counted
  sweep is worse than no sweep.

**Enumerate the test-side blast radius, not just the production one.** Any change to
an exception type, signature, return shape, or status code breaks the tests asserting
the old form. For every such change the plan must:

- List the affected tests **by name and file**, derived from a validated pattern.
- **Attach each one to the cycle that breaks it**, updated in that cycle's commit —
  not a cleanup pass that will be dropped.
- Declare them in that cycle's `modifies_tests`. Without this the tool reports every
  authorised edit as test weakening, and an alarm that fires on correct work gets
  ignored — which is how the real weakening slips past.
- Forbid the cheap escape: never relax an assertion to a base class to absorb the
  change, and never delete the test.

### 15. Validate numeric targets against irreducible floors

Any target stated as a number must be decomposed: which step contributes which
portion; what the **irreducible floor** is (container startup, load-bearing sleeps,
suites not being converted, fixed I/O); and whether `target > floor`. If not, the
target is unreachable — fix the floor as its own step, or restate the target honestly.

---

## 16. Author the contract

The plan carries its own machine-readable contract in YAML front-matter. This is a
**deliverable of hardening**, not an afterthought: the front-matter is what executes,
and where it disagrees with the prose, the front-matter wins. `examples/plan.md` in
the tdd-cli repository is a complete plan exercising every cycle kind and the full
vocabulary.

```yaml
---
cycles:
  - n: 1
    project: backend                    # must exist in tdd.toml
    title: "short behaviour description"
    test: "tests/x/test_y.py::test_z"   # project-relative; namespaced automatically
    stub_expected: ["app/services/y.py"]
    files: ["app/services/y.py", "app/routers/z.py"]
    modifies_tests: ["tests/blackbox/test_j.py::test_old_shape"]
    commit_red: "test: ..."
    commit_green: "feat: ..."
    commit_refactor: "refactor: ..."
  - n: 2
    project: backend
    refactor_cycle: true
    title: "migrate the remaining call sites"
    files: ["app/routers/w.py"]
    commit_refactor: "refactor: ..."
annotation_keys: ["construction_count_after"]
---
```

Field rules:

- **`n`** — ordinals must be unique and are executed in ascending order.
- **`project`** — must name a project in `tdd.toml`. Use `projects: [a, b]` only for a
  `contract_cycle`.
- **`test`** — project-relative for pytest (`tests/x/test_y.py::test_z`). For vitest,
  worktree-relative plus the full test name
  (`frontend/services/__tests__/a.test.ts > full name here`), where the name is the
  space-joined `describe` titles plus the `it` title.
- **`stub_expected`** — every file the cycle creates as a stub before RED. See step 6.
- **`files`** — the production blast radius. Diffed against what actually changed;
  divergence is recorded, not blocked.
- **`modifies_tests`** — existing tests this cycle is authorised to change. See
  step 14.
- **`commit_*`** — one per phase the cycle has. Take them verbatim from the plan's
  COMMIT steps; the plan almost always already wrote them.
- **`annotation_keys`** — the judgement fields this plan wants recorded per cycle.
  Required before each cycle closes, so use them for the things the plan says to
  "record in the friction log". Do not add generic ones — `plan_defect` and
  `friction_note` are already reserved.

**Then validate mechanically. This is a gate, not a suggestion:**

```sh
git add <plan-file> && git commit -m "plan: <name> contract"   # the contract is the committed blob
tdd plan register <plan-file>
```

Registration **must** succeed and its reported cycle count and kind breakdown **must**
match your intent. Paste both into the readiness report. A malformed contract
hard-fails here by design — that failure is a defect in *this* skill's output, not
something to route around with `--allow-undeclared`.

Then confirm the environment: `tdd doctor` must report `healthy: true`.

## 17. Execution section, branch, and autonomy contract

Confirm:

- The plan is **committed** — the contract is hashed at the git blob, so an
  uncommitted plan cannot be registered.
- `tdd doctor` is green and `tdd plan register` succeeded.
- The Execution section opens with branch creation and closes with the PR. Both are
  the **executor's** job and both are easily forgotten: the tool owns commits but not
  branches and not the remote, so work silently piles onto whatever branch the
  executor started on — usually the default one — and ends as a pile of commits nobody
  asked to review.

**The plan MUST contain an Execution section, and it must instruct the executor to
start the run itself.** This is easy to omit — the tool owns so much of the pre-flight
that the *start* gets forgotten with it, leaving a hardened plan nobody can begin.
Required content, and nothing beyond it:

```markdown
## Execution

This plan is executed through `tdd-cli`. **You run every command below yourself** — do not ask the
user to start the run. `tdd run start` records which model is executing, resolved from your own
session; a run started by anyone else attributes this work to the wrong agent.

    git checkout -b <task-name>                 # first, before anything else
    tdd doctor                                  # must report healthy: true
    tdd run start --plan <plan-path>            # captures baselines, opens cycle 1

If the branch already exists, do not force-checkout and do not pick another name: check it out
only if it carries this plan's commit and no unrelated work, otherwise stop and ask.

Then repeat until done: read `next_action.verb`, do exactly what it says, run `tdd advance`.
Stop when `next_action.terminal` is `true`.

When `next_action.terminal` is `true`, finish the run: render the friction log, commit it, and
raise the PR — see Done-criteria below.

- `tdd advance` is the only command that changes phase. Do not `git add` or `git commit` — the
  tool stages and commits, deriving the file set from the phase.
- The baseline is captured at `run start` and subtracted from later verdicts. State the expected
  summary line so a moved branch is caught.
- Map the verbs the plan will actually hit: `run_sensitivity_check` → `tdd sensitivity
  begin|check|end`; `annotate_cycle` → `tdd annotate --key --value` (name this plan's keys);
  `resolve_blocker` → `tdd blocker --kind --detail` (list the kinds); `confirm_cycle_applicable`
  on a non-existent cycle → `tdd cycle skip --reason`.
```

**Add nothing else.** No stop condition, no phase list, no "when to hand back" clause —
`next_action` is the sole authority on control flow, and a second opinion in prose is
exactly the two-sources-of-truth conflict the no-control-flow rule (`docs/PRD.md`
R16.1) exists to prevent. The one "stop and
ask" this template contains — the branch-collision clause — does not violate that
rule: it fires *before* `tdd run start`, outside the loop `next_action` governs, as
does the PR after `terminal`. Neither is a reason to interrupt the loop itself.

**Who runs what.** The *hardener* runs `tdd plan register`; the *executor* runs
`tdd doctor` and `tdd run start`. Never register on the executor's behalf mid-run, and
never start a run on theirs: executor identity comes from the session that runs
`run start`, so a human-started or hardener-started run records the wrong model and
silently poisons every model-comparison metric the ledger exists to produce.

## 18. Done-criteria

The conformance checks are computed. Append only:

> **Before finishing:** run
> `tdd log render --out tasks/friction-logs/<task-name>-friction.md` and
> `tdd metrics`. Report the plan-fidelity section — declared vs delivered vs skipped —
> and every integrity event. Do not narrate what the ledger already records.
>
> Then commit the friction log and open the PR against the default branch, following
> this repository's contribution workflow (quality gates first, then push and PR — via
> a PR skill if the repo provides one, otherwise `gh pr create`). If a gate fails, fix
> it and re-run — a failed gate is work, not a reason to hand back.

Adjust the friction-log destination to the repo's convention if it has one; keep it
**at the worktree root**. `tdd log render` resolves a relative `--out` from the
worktree root, so the path above is correct verbatim from any directory — write it
into the plan exactly as given, and never prefix it with a project directory
(`backend/tasks/...`). Executors working inside a single project reliably get this
wrong, and audit tooling only reads one location.

## 19. Emit the readiness report

- **Contract registered**: paste the `tdd plan register` result — cycle count and kind
  breakdown — and confirm it matches intent
- **Execution section present**, instructing the executor to run `tdd doctor` and
  `tdd run start` itself, with this plan's annotation keys and blocker kinds named
- **Branch and PR bracketed**: the Execution section opens with
  `git checkout -b <task-name>` (stop-if-exists) and the done-criteria close with
  committing the friction log and opening the PR
- **Cycle kinds assigned**, with the probe evidence for each pin and each
  refactor-only cycle
- **`tdd doctor` healthy**
- **Baseline**: green, or the failing tests named and classified as work or blocker
- **RED paths probed empirically** — wrong routes corrected, unmet preconditions
  found, actual failure modes recorded, guard ordering confirmed. Name any cycle that
  could not be probed
- **Existing coverage found**, and which cycles it replaces, shortens, or converts to
  pins
- Behaviours moved from PROSE-ONLY → new cycles (with test names)
- **Test-side blast radius enumerated**, attached to breaking cycles and declared in
  `modifies_tests`
- RED steps split
- **Production targets named**, with call paths traced where test file and target
  module disagreed
- **Stubs declared** for every cycle introducing a new module/class/function/parameter
  — state the imports you walked per cycle, and name the config/registry files
  (`.importlinter` and the like) that a new module cannot be added without
- **Expected failure modes stated** per cycle
- Detection/mutation claims verified as independently-derived (or rewritten)
- Fake/real divergence table present, each row ruled
- Fixture/contract assertions relocated into RED; generated artifacts covered by an
  `artifact` edge
- Test seams specified or behaviours descoped
- Guards added
- **Sweep steps enumerated** with the discovery command and its output
- **Numeric targets validated** against irreducible floors
- Plan/repo contradictions resolved (and how)
- `grep -nE '\.(py|ts|tsx|md):[0-9]+' <plan-file>` returns empty

Then present the revised plan file for approval before any dispatch.
