---
cycles:
  - n: 1
    project: backend
    title: "order total sums line items"
    test: "tests/orders/test_pricing.py::test_total_sums_line_items"
    stub_expected: ["app/orders/pricing.py"]
    files: ["backend/app/orders/pricing.py"]
    commit_red: "test: order total sums line items"
    commit_green: "feat: pricing.total() over line items"

  - n: 2
    project: backend
    title: "totals round half-up to whole cents"
    test: "tests/orders/test_pricing.py::test_total_rounds_half_up"
    files: ["backend/app/orders/pricing.py"]

  - n: 3
    project: backend
    pin_cycle: true
    title: "characterise the legacy bulk-discount rule before moving it"
    test: "tests/orders/test_pricing.py::test_legacy_bulk_discount_applies_over_ten_units"
    commit_pin: "test: pin the legacy bulk-discount rule"

  - n: 4
    project: backend
    refactor_cycle: true
    title: "move the discount rule from the checkout handler into pricing"
    files:
      - "backend/app/orders/pricing.py"
      - "backend/app/api/checkout.py"
    modifies_tests:
      - "tests/orders/test_checkout.py::test_checkout_applies_discount"
    commit_refactor: "refactor: discount rule lives in pricing, handler delegates"

  - n: 5
    projects: ["backend", "frontend"]
    contract_cycle: true
    title: "totals are integer cents end to end"
    tests:
      - "backend::tests/api/test_checkout_api.py::test_response_carries_total_cents"
      - "frontend::components/__tests__/OrderSummary.test.ts > renders the total from total_cents"

annotation_keys: ["legacy_discount_rule_kept"]
---

# Consolidate order pricing into one module

An example plan for `tdd-cli`, showing the full front-matter vocabulary and the body
structure that makes a plan executable by an agent without conversation context. The
front-matter above is the **contract** — hashed at the committed blob, enforced by the
tool. Everything below is **guidance** for the executor: not enforced, but the difference
between a plan that survives autonomous execution and one that doesn't.

## Context

Order totals are currently computed inline in the checkout API handler, including a
bulk-discount rule added under deadline pressure. The frontend renders a float `total`
field and has accumulated rounding workarounds. This plan extracts a `pricing` module,
pins the legacy discount behaviour before moving it, and switches the API contract to
integer cents in a single breaking change across both projects.

Why the cycles are ordered this way:

- **Cycles 1–2 (standard):** the new module first, one behaviour per cycle. Cycle 1
  declares `stub_expected` — the target test imports `app.orders.pricing`, which does
  not exist, so the tool will direct a stub and stage it with the RED commit.
- **Cycle 3 (pin):** the legacy discount rule has no test. A pin characterises it *as it
  behaves today* — the test passes on arrival by design, and the tool requires a
  sensitivity check to prove the pin can fail before it counts.
- **Cycle 4 (refactor):** behaviour-preserving move. No new test — the suite, including
  the pin from cycle 3, is the guard. `modifies_tests` declares the existing test whose
  setup legitimately changes; anything else the cycle touches is recorded as divergence.
- **Cycle 5 (contract):** a breaking change with no intermediate green state. Both
  targets are declared with project-qualified ids and must fail together, then pass
  together.

## Verified repo facts

*Probed against the codebase before dispatch — never asserted from memory. Each fact is
something the executor would otherwise have to guess, and a wrong guess mid-run becomes
a blocker. Re-verify anything cheap at execution time.*

- `app/orders/pricing.py` does not exist; cycle 1's RED will report `not_collected`
  and the tool will issue a `create_stub` directive.
- The legacy discount lives in `checkout.py` lines 41–58: 10% off subtotals of ten or
  more units, applied **before** rounding. The pin in cycle 3 must assert that order
  (discount, then round), not the mathematically equivalent one.
- `test_checkout_applies_discount` constructs the handler directly; after cycle 4 it
  must import the rule's new home. That is the one declared test modification.
- Expected RED failure, cycle 1: `ModuleNotFoundError: No module named 'app.orders.pricing'`
  at collection. Cycles 2, 5: ordinary assertion failures — state the expected message in
  each cycle's detail below.
- The frontend test id after the `>` must match vitest's `fullName` exactly: all
  `describe` titles plus the `it` title, space-joined.

## Cycle detail

*One subsection per cycle: the expected RED failure verbatim, what the test asserts, and
the minimum GREEN. An executor that knows the expected failure can tell a correct RED
from a broken environment — without it, every unexpected message looks the same.*

### Cycle 1 — total sums line items

**Expected RED:** `not_collected` (module missing) → stub directive → then the test
fails with `NotImplementedError` from the stub body.

Test: three line items, `total()` returns their sum. GREEN: the one-line sum — resist
adding rounding now; that is cycle 2's behaviour.

### Cycle 2 — round half-up to whole cents

**Expected RED:** `assert 1000 == 999` (a subtotal of 9.995 must round up).

### Cycle 3 — pin the bulk discount *(pin)*

Write the characterisation test against the handler's current behaviour; it passes on
arrival. The tool then requires `tdd sensitivity begin` → mutate the discount threshold
→ `tdd sensitivity check` → `tdd sensitivity end` to prove the pin bites.

### Cycle 4 — move the rule *(refactor)*

Move lines 41–58 into `pricing.apply_bulk_discount()`; the handler delegates. Update the
one declared test's import. The close sweep runs the full suite — the pin from cycle 3
is what makes this move safe.

**Annotate before closing:** `legacy_discount_rule_kept` — `true` if the rule moved
verbatim, or a one-line description of any intentional change. The tool refuses to close
the cycle until every key in `annotation_keys` is recorded.

### Cycle 5 — integer cents across the boundary *(contract)*

Both tests written first, both must fail together: the backend asserts the response
carries `total_cents` (int) and no `total`; the frontend asserts `OrderSummary` renders
from `total_cents`. Then one implementation pass takes both to green — there is no
deployable intermediate state, which is what `contract_cycle` declares.

## Execution

This plan is executed through `tdd-cli`. Run every command yourself — a run started by
anyone else records the wrong executor.

    git checkout -b consolidate-pricing
    tdd doctor
    tdd plan register examples/plan.md
    tdd run start --plan examples/plan.md

Then repeat until `next_action.terminal` is true: read `next_action.verb`, do exactly
what it says, run `tdd advance`.

If a cycle no longer matches the codebase, do not improvise around it:
`tdd cycle skip --reason "..."` or `tdd blocker --kind plan_codebase_conflict --detail "..."`.

## Done-criteria

    tdd log render --out tasks/friction-logs/consolidate-pricing-friction.md
    tdd metrics

Report the plan-fidelity section (declared vs delivered vs skipped) and every integrity
event. Do not narrate what the ledger already records.
