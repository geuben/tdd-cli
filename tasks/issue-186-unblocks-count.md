---
closes: 186
cycles:
  # -- Phase 1: the count is reported as unblocks ----------------------------------------
  - n: 1
    project: tddcli
    title: "tdd metrics reports unblocks, not human_interventions"
    test: "tests/test_unblocks_count.py::test_metrics_reports_unblocks_not_human_interventions"
    files: ["src/tddcli/render.py"]
    commit_red: "test: tdd metrics reports unblocks"
    commit_green: "feat: tdd metrics reports unblocks instead of human_interventions"
    commit_refactor: "refactor: tidy the unblocks metric"
  - n: 2
    project: tddcli
    title: "the friction log lists each unblock under Unblocks: N"
    test: "tests/test_unblocks_count.py::test_the_friction_log_lists_each_unblock_under_unblocks"
    files: ["src/tddcli/render.py"]
    modifies_tests:
      - "tests/test_late_baseline.py::test_friction_log_lists_amended_baseline_verdicts_under_human_interventions"
    commit_red: "test: the friction log lists unblocks"
    commit_green: "feat: the friction log reports Unblocks: N"
    commit_refactor: "refactor: tidy the unblocks line"
  # -- Phase 2: an abandonment is not an unblock ------------------------------------------
  - n: 3
    project: tddcli
    title: "tdd run abandon writes no human_intervention row"
    test: "tests/test_run_abandon.py::test_abandoning_records_no_unblock"
    files: ["src/tddcli/ledger.py"]
    modifies_tests:
      - "tests/test_run_abandon.py::test_abandoning_records_a_human_intervention"
    commit_red: "test: abandoning a run records no unblock"
    commit_green: "feat: tdd run abandon stops writing a human_intervention row"
    commit_refactor: "refactor: tidy abandon_run"
  - n: 4
    project: tddcli
    title: "a row a pre-change abandon wrote is not counted or listed as an unblock"
    test: "tests/test_unblocks_count.py::test_a_pre_change_abandon_row_is_not_an_unblock"
    files: ["src/tddcli/render.py"]
    commit_red: "test: a pre-change abandon row is not an unblock"
    commit_green: "feat: leave rows abandon wrote out of the unblocks"
    commit_refactor: "refactor: tidy the unblocks filter"
  - n: 5
    project: tddcli
    title: "an unblock whose note reads like an abandonment is still an unblock"
    test: "tests/test_unblocks_count.py::test_an_unblock_whose_note_reads_like_an_abandonment_is_still_counted"
    files: ["src/tddcli/render.py"]
    commit_red: "test: an unblock noted like an abandonment still counts"
    commit_green: "feat: match a pre-change abandon row on its time as well as its note"
    commit_refactor: "refactor: tidy the abandon-row match"
  - n: 6
    project: tddcli
    title: "the friction log names an abandoned run's reason on an Abandoned: line"
    test: "tests/test_run_abandon.py::test_the_friction_log_names_the_abandonment_reason"
    files: ["src/tddcli/render.py"]
    commit_red: "test: the friction log names why a run was abandoned"
    commit_green: "feat: the friction log gains an Abandoned: header line"
    commit_refactor: "refactor: tidy the Abandoned line"
  # -- Phase 3: wording ------------------------------------------------------------------
  - n: 7
    project: tddcli
    title: "resume --unblock without --note asks for a note describing the unblock"
    test: "tests/test_unblocks_count.py::test_unblock_without_a_note_asks_for_one_describing_the_unblock"
    files: ["src/tddcli/cli.py"]
    commit_red: "test: --unblock without --note names the unblock"
    commit_green: "feat: --unblock asks for a note describing the unblock"
    commit_refactor: "refactor: tidy the --note refusal"
  - n: 8
    project: tddcli
    refactor_cycle: true
    title: "docs stop calling an unblock a human intervention"
    files:
      - "docs/PRD.md"
      - "README.md"
      - "examples/skills/tdd-drive/SKILL.md"
      - "CHANGELOG.md"
      - "src/tddcli/ledger.py"
    commit_refactor: "docs: unblocks, not human interventions"
---

# Issue 186: the human-interventions count includes the agent's own unblocks

## Context

Issue #186. The friction log's "Human interventions: N" and `tdd metrics`' `human_interventions`
count every row of the `human_intervention` table (`render.friction_log`, `render.metrics`, both
through `Ledger.interventions`). `tdd resume --unblock --note` writes such a row whoever runs it
(`Ledger.reopen_run`, called from `cli.cmd_resume`). Under `claude -p` nobody is watching, and the
agent runs it itself: `/implement-issue` allows `--unblock --accept-failures` for a test that also
fails at the merge-base. So unattended runs report human interventions when no person took part.

The issue asks for a naming and reporting change, not attribution. No command takes an executor
identity (PRD R8.3), so tdd-cli cannot tell who unblocked a run.

- The friction log and `tdd metrics` report the count as unblocks ("Unblocks: N", `unblocks`),
  with each note listed as today.
- The docs stop describing `resume --unblock` as necessarily a human intervention.
- Who intervened is counted outside tdd-cli. geuben/dispatch counts a person's interventions
  across an issue's whole path (geuben/dispatch#217), and treats this count as a friction signal.

**Done when** (from the issue):

- No output of tdd-cli calls an unblock a human intervention. This covers the friction log
  (cycle 2), `tdd metrics` (cycle 1), the `--note` refusal (cycle 7) and the shipped docs
  (cycle 8, checked by the Done-criteria grep).
- Ledgers written before the change render with the new name and the same count. This holds
  for every run except an abandoned one; see decision 1.

`tdd run abandon` (#150) also writes a `human_intervention` row, `note = "abandoned: <reason>"`,
at the same `at` as the run's `abandonment` row (`Ledger.abandon_run`). Probed on today's tree:
`run abandon` gives that row, the `abandonment` row and the run's `ended_at` one identical
timestamp. So today the count covers unblocks **and** abandonments. An earlier planning run asked
which the renamed count covers
([comment](https://github.com/geuben/tdd-cli/issues/186#issuecomment-6507689259)), and the owner
answered "1 - A: Count unblocks only"
([comment](https://github.com/geuben/tdd-cli/issues/186#issuecomment-6508198421)).

## Design decisions (locked)

1. **The count covers unblocks only.** *Decided by a person*
   ([answer](https://github.com/geuben/tdd-cli/issues/186#issuecomment-6508198421) to option 1A
   of [the question](https://github.com/geuben/tdd-cli/issues/186#issuecomment-6507689259)).
   - "Unblocks: N" and `unblocks` count `resume --unblock` rows only.
   - `run abandon` stops writing a `human_intervention` row (cycle 3). Its `abandonment` row and
     `outcome = abandoned` already record the abandonment, and `tdd metrics` already reports
     `abandoned: {reason, by}`.
   - The friction log gets an `Abandoned: <reason>` header line, read from the `abandonment`
     table (cycle 6).
   - Rows that `run abandon` wrote before the change are left out of the count and the list
     (cycles 4 and 5). For runs abandoned before the change, the count is one lower than today.
     The owner accepted that departure from the issue's "same count" when they chose 1A.
   - `tests/test_run_abandon.py::test_abandoning_records_a_human_intervention` pinned #150's
     "abandoning is a human intervention". Cycle 3 replaces it.
2. **What counts as a pre-change abandon row.** *Settled by evidence* (the decision's own rule,
   and the probe above). A `human_intervention` row is left out exactly when all of these hold:
   - its run has an `abandonment` row (`Ledger.abandonment(run_id)` is not `None`);
   - its `note == f"abandoned: {abandonment['reason']}"`;
   - its `at == abandonment["at"]`.

   Every other row is an unblock. A run with `outcome = 'abandoned'` and no `abandonment` row
   (`tests/test_baseline_integrity.py` makes such runs with SQL) leaves every row in. Cycle 4
   pins the note match and cycle 5 pins the time match.
3. **The filter lives in `render.py`, not in `Ledger.interventions`.** *Settled by evidence.*
   `interventions` is in `GUEST_READS` (`src/tddcli/ledger.py`), and a guest on this release may
   reach a host service on an older one (#169). Such a host answers `interventions` unfiltered.
   Its `abandon_run` also still writes the row, because guests call `abandon_run` through the
   service and the host runs its own copy. Filtering where the count is rendered gives one
   answer whatever release the host runs. `render.friction_log` and `render.metrics` back every
   output: `tdd log render`, `tdd metrics`, and the service's `log` and `metrics`
   (`service.Service.log` and `.metrics` call `render`). Both read through one private helper,
   `render._unblocks(ledger, run_id) -> list[sqlite3.Row]`, which uses `ledger.interventions`
   and `ledger.abandonment`. Both methods are already in `GUEST_READS`.
4. **Storage is unchanged.** *Settled by convention* (`.claude/plan-issue.md`: bump only when an
   existing table's shape changes, #150). The `human_intervention` table keeps its name and
   shape. There is no `SCHEMA_VERSION` bump and no frozen referee. `Ledger.interventions` and
   `Ledger.reopen_run` keep their names: internal names, not output, and renaming a guest read
   breaks guests talking to older hosts (#169). `abandon_run`'s signature is unchanged.
5. **No `human_interventions` alias in `tdd metrics`.** *Settled by evidence* (the issue's
   done-when: "No output of tdd-cli calls an unblock a human intervention"). The key is
   replaced outright. The `CHANGELOG.md` entry goes under `### Changed`, names the old and new
   key, and says it breaks JSON readers. That follows the repo's convention (`RELEASING.md`;
   #149's metrics change was logged the same way).
6. **The friction log keeps listing each note** under the renamed line,
   `  - <at>: <note>`, as the issue asks. The `accepted:` / `refused:` baseline-amendment lines
   stay nested under it. *Settled by evidence:* the issue, and
   `tests/test_late_baseline.py`'s test, which cycle 2 renames to
   `test_friction_log_lists_amended_baseline_verdicts_under_unblocks`. That test's assertions do
   not change.
7. **The `Abandoned:` line.** *Settled by the person's decision and by convention.* It is
   `- Abandoned: <reason>`, directly after the `- Started: … Outcome: …` line, whenever
   `ledger.abandonment(run_id)` is not `None`. It reads the reason from the `abandonment` table,
   not from the old row's note, so runs from before and after the change render the same way.
   The account and executor stay in `tdd metrics`' `abandoned.by`, as today.
8. **The `--note` refusal is reworded** from "`--unblock requires --note describing the
   intervention`" to "`--unblock requires --note describing the unblock`" (`cli.cmd_resume`).
   *Settled by convention:* the refusal names the thing the count now calls it. The earlier
   planning comment listed this as settled, and nobody objected.
9. **Docs** (the issue's second bullet). *Settled by evidence:* the issue, R8.3, and the
   comment's "Already settled" list. Cycle 8 has the exact edits.
   - `docs/PRD.md` §8.3's `resume --unblock` and `run abandon` rows say what the ledger records,
     without claiming a person. They say the verbs are meant for whoever supervises the run, and
     that tdd-cli cannot tell who ran them (R8.3). The `run abandon` row drops its
     `human_intervention` event.
   - R8.8 is rewritten: unblocks per run is a friction signal, and who intervened is counted
     outside tdd-cli.
   - README's "Abandoning a run", "The friction log" and command table are reworded to match.
   - The shipped `examples/skills/tdd-drive/SKILL.md` stops saying "human intervention".
   - Released `CHANGELOG.md` entries are history and are not edited.
10. **`tdd blocker`'s `next_action` detail is left alone.** "A human can resume with `tdd resume
    --unblock`" states the intended use. It does not call an unblock a human intervention, and
    `detail` is non-authoritative (docs/harness-integration.md). *Settled by evidence.*
11. **Consumers outside this repo are named, not edited.** *Settled by convention:* this repo's
    plans edit this repo.
    - The user-level `implement-issue` skill reads the friction log's "Human interventions"
      header (its step "Read its header"). So does `raise-pr`'s Interventions section.
    - geuben/dispatch may read `human_interventions`.

    The PR body names all three for their owners. This plan's own run renders its friction log
    with the released 0.15.0 referee, which still prints "Human interventions", so these
    consumers keep working until the release that carries this change.
12. **Tests.** *Settled by convention* (`.claude/plan-issue.md`).
    - Count and list cycles go through `render.py` with a fixture ledger (`Ledger.insert` with
      fixed timestamps, under the `ledger_home` fixture).
    - End-to-end cycles go through `conftest.run_cli`.
    - The new file is `tests/test_unblocks_count.py`. Abandon behaviours stay in
      `tests/test_run_abandon.py`, beside #150's.
13. **No `.github/workflows/` change is needed.**

## Deliberate scope cuts (do not build)

None. Attribution (who unblocked) is a named non-goal of the issue ("this is a naming and
reporting change, not attribution"; R8.3). Editing `implement-issue`, `raise-pr` or
geuben/dispatch is outside this repository (decision 11).

## Fake and real divergence

| Seam | In the tests | In production | Ruling |
|---|---|---|---|
| A ledger written before the change | `Ledger.insert` of an `abandonment` row and a `human_intervention` row with `note = "abandoned: <reason>"` at the same `at` | tdd ≤ 0.15.0's `abandon_run` | acceptable: probed, the real one writes exactly that shape, with one shared timestamp |
| A host service on an older release | not tested | its `abandon_run` still writes the row, and its `interventions` answers unfiltered | acceptable: the filter is in `render` (decision 3), and cycles 4 and 5 cover the same rows |
| The run behind a fixture ledger | a `run` row with no cycles, `ended_at = 10:10` | a run started by `tdd run start` | acceptable: only the Plan-fidelity section and the metrics key are asserted, and cycle 1 checks the key end to end |

## Cycles

Every refusal asserted here is a bare `envelope.failure(error)`, with no `reason`. Cycle 7 reads
the message as `out["error"]`, at the envelope's top level (probed).

### The new test file's helpers

`tests/test_unblocks_count.py` is created in cycle 1's RED. Cycles 2, 4, 5 and 7 add to it.
Module docstring: `"""Unblocks, not human interventions (issue #186)."""`. Imports: `json`,
`sqlite3` (for the helper's return annotation), `from conftest import run_cli, write_plan`,
`from tddcli import render`, and `from tddcli.ledger import Ledger`. All of these exist today.
The end-to-end tests (cycles 1 and 7) take the `repo` fixture. The fixture-ledger tests (cycles
2, 4 and 5) take `(tmp_path, ledger_home)`.

- `PLAN`: the same one-cycle plan string as `tests/test_run_abandon.py`'s `PLAN`
  (project `backend`, test `tests/test_add.py::test_add_two_numbers`).
- `blocked_run(repo)`: does `run_cli(repo, "plan", "register", write_plan(repo, PLAN))`, then
  `run_cli(repo, "run", "start", "--plan", <plan>)` and asserts `["ok"]`. Then it runs
  `run_cli(repo, "blocker", "--kind", "plan_defect", "--detail", "x")`. Probed: the blocker
  answers `ok: true`, verb `blocked`.
- `_at(minute)`: `f"2026-09-01T10:{minute:02d}:00+00:00"`, as in `tests/test_time_report.py`.
- `fixture_ledger(tmp_path, unblocks, abandoned=None) -> tuple[Ledger, sqlite3.Row]`:
  - `ledger = Ledger(tmp_path / "somerepo")`.
  - One `plan_contract` row: `plan_path="tasks/p.md", status="declared",
    declared_cycles=json.dumps([{"n": 1}]), annotation_keys="[]", registered_at=_at(0)`.
  - One `run` row: `plan_contract_id=<contract>, executor_model="m",
    executor_source="declared", worktree_path="/wt", started_at=_at(0), ended_at=_at(10),
    preexisting_dirty="[]"`, and `outcome="abandoned" if abandoned else "complete"`.
  - For each `(minute, note)` in `unblocks`, in order: a `human_intervention` row
    `run_id=<run>, note=note, at=_at(minute)`.
  - If `abandoned` is a `(minute, reason)` pair, it writes what tdd ≤ 0.15.0's `abandon_run`
    wrote. First an `abandonment` row: `run_id=<run>, reason=reason, account="op",
    executor_model="m", executor_source="declared", at=_at(minute)`. Then a
    `human_intervention` row: `run_id=<run>, note=f"abandoned: {reason}", at=_at(minute)`.
  - Returns `(ledger, ledger.one("SELECT * FROM run WHERE id = ?", (run_id,)))`.
- `fidelity(text)`: the Plan-fidelity section. It returns
  `text.split("\n## Plan fidelity\n", 1)[1].split("\n## ", 1)[0].strip()` when that heading is
  in `text`, else `""`.
- `FIDELITY_HEAD = "- Declared cycles: 1\n- Delivered: 0   Skipped: 0\n- Never reached: [1]\n"`.
  Probed: a fixture ledger with no cycle rows renders exactly these three lines, followed by
  the count line.

### Phase 1: the count is reported as unblocks

**Cycle 1: `test_metrics_reports_unblocks_not_human_interventions`** (in
`tests/test_unblocks_count.py`).
- `blocked_run(repo)`, then `run_cli(repo, "resume", "--unblock", "--note", "fixed the fixture")`.
- `m = run_cli(repo, "metrics")["result"]["runs"][0]`.
- Single assertion: `(m.get("unblocks"), "human_interventions" in m) == (1, False)`.
- Production target: `render.metrics`. The `"human_interventions"` key becomes `"unblocks"`,
  still `len(ledger.interventions(run["id"]))`.
- EXPECTED FAILURE (probed): `AssertionError: assert (None, True) == (1, False)`.

**Cycle 2: `test_the_friction_log_lists_each_unblock_under_unblocks`** (in
`tests/test_unblocks_count.py`).
- `ledger, run = fixture_ledger(tmp_path, [(2, "fixed the fixture"), (5, "verified against main")])`.
- Single assertion: `fidelity(render.friction_log(ledger, run))` equals `FIDELITY_HEAD` +
  `"- Unblocks: 2\n  - 2026-09-01T10:02:00+00:00: fixed the fixture\n  - 2026-09-01T10:05:00+00:00: verified against main"`.
- Also in RED, rename
  `tests/test_late_baseline.py::test_friction_log_lists_amended_baseline_verdicts_under_human_interventions`
  to `test_friction_log_lists_amended_baseline_verdicts_under_unblocks`. Change only its name;
  its body and assertions stay as they are.
- Production target: `render.friction_log`. The line `- Human interventions: {n}` becomes
  `- Unblocks: {n}`.
- EXPECTED FAILURE (probed): the section has `- Human interventions: 2` where `- Unblocks: 2`
  is expected, so `AssertionError: assert '- Declared cycles: 1\n…- Human interventions: 2\n…' == '- Declared cycles: 1\n…- Unblocks: 2\n…'`.

### Phase 2: an abandonment is not an unblock

**Cycle 3: `test_abandoning_records_no_unblock`** (in `tests/test_run_abandon.py`).
- In RED, rewrite `test_abandoning_records_a_human_intervention` in place. Rename it to
  `test_abandoning_records_no_unblock` and keep its setup (`register`, `start`,
  `run abandon --reason "superseded by #145"`). Its assertion becomes
  `assert notes == []`, where `notes` is still read from `SELECT note FROM human_intervention`.
- Production target: `Ledger.abandon_run`. Delete its `self.insert("human_intervention", …)`
  line. Nothing else in `abandon_run` changes.
- EXPECTED FAILURE (probed): `AssertionError: assert ['abandoned: superseded by #145'] == []`.

**Cycle 4: `test_a_pre_change_abandon_row_is_not_an_unblock`** (in
`tests/test_unblocks_count.py`).
- `ledger, run = fixture_ledger(tmp_path, [(2, "fixed the fixture")], abandoned=(10, "superseded by #145"))`.
- Single assertion, over both outputs:
  `(render.metrics(ledger, "/wt")["runs"][0]["unblocks"], fidelity(render.friction_log(ledger, run)))`
  equals `(1, FIDELITY_HEAD + "- Unblocks: 1\n  - 2026-09-01T10:02:00+00:00: fixed the fixture")`.
- Production target: `render._unblocks(ledger, run_id)`, new, used by both `render.metrics` and
  `render.friction_log` in place of `ledger.interventions`. Decision 3 says why it lives here.
- EXPECTED FAILURE (probed: today's render lists the abandon row as the third line):
  `AssertionError: assert (2, '…- Unblocks: 2\n  - 2026-09-01T10:02:00+00:00: fixed the fixture\n  - 2026-09-01T10:10:00+00:00: abandoned: superseded by #145') == (1, '…- Unblocks: 1\n  - 2026-09-01T10:02:00+00:00: fixed the fixture')`.

**Cycle 5: `test_an_unblock_whose_note_reads_like_an_abandonment_is_still_counted`** (in
`tests/test_unblocks_count.py`).
- `ledger, run = fixture_ledger(tmp_path, [(5, "abandoned: superseded by #145")], abandoned=(10, "superseded by #145"))`.
  The 10:05 row is a real unblock whose note happens to match. Only the 10:10 row is the one
  abandon wrote.
- Single assertion, over both outputs:
  `(render.metrics(ledger, "/wt")["runs"][0]["unblocks"], fidelity(render.friction_log(ledger, run)))`
  equals `(1, FIDELITY_HEAD + "- Unblocks: 1\n  - 2026-09-01T10:05:00+00:00: abandoned: superseded by #145")`.
- Production target: `render._unblocks`. The match also requires `row["at"] == abandonment["at"]`
  (decision 2).
- EXPECTED FAILURE (derived, not probed: probing it would mean building cycle 4. After cycle 4's
  note-only match, both rows are dropped):
  `AssertionError: assert (0, '…- Unblocks: 0') == (1, '…- Unblocks: 1\n  - 2026-09-01T10:05:00+00:00: abandoned: superseded by #145')`.

**Cycle 6: `test_the_friction_log_names_the_abandonment_reason`** (in `tests/test_run_abandon.py`).
- `plan = register(repo)`, `start(repo, plan)`, then
  `run_cli(repo, "run", "abandon", "--reason", "superseded by #145")`, then
  `run_cli(repo, "log", "render", "--out", str(repo / "friction.md"))`. Read the file as `text`.
- Single assertion: `"  Outcome: abandoned\n- Abandoned: superseded by #145\n" in text`.
- Production target: `render.friction_log`. After the `- Started: … Outcome: …` line, when
  `ledger.abandonment(run["id"])` is not `None`, write `- Abandoned: {abandonment['reason']}`.
- A run with no `abandonment` row must still render. That guard is already covered:
  `tests/test_time_report.py::test_the_friction_log_carries_a_time_section` renders a `blocked`
  run with no `abandonment` row, and would raise `TypeError` on `None["reason"]`.
- EXPECTED FAILURE (probed: today the line after the `Started` line is
  `- Baseline failures at start: backend=0`): `AssertionError: assert '  Outcome: abandoned\n- Abandoned: superseded by #145\n' in '# Implementation Friction Log: tasks/plan.md\n…'`.

### Phase 3: wording

**Cycle 7: `test_unblock_without_a_note_asks_for_one_describing_the_unblock`** (in
`tests/test_unblocks_count.py`).
- `blocked_run(repo)`, then `out = run_cli(repo, "resume", "--unblock")`.
- Single assertion: `out["error"] == "--unblock requires --note describing the unblock"`.
- Production target: `cli.cmd_resume`, the `if not args.note:` refusal.
- EXPECTED FAILURE (probed):
  `AssertionError: assert '--unblock requires --note describing the intervention' == '--unblock requires --note describing the unblock'`.

**Cycle 8 (refactor): docs.** Docs only. A refactor phase never carries a behaviour change: if
one seems needed, raise `plan_defect`.
- `docs/PRD.md`, §8.3:
  - The `tdd resume --unblock --note <text>` row becomes: "For whoever supervises the run.
    Reopen a blocked run, recording an unblock (a `human_intervention` row) with the note.
    tdd-cli cannot tell who ran it (R8.3)."
  - The `tdd run abandon` row: "**human only.**" becomes "For whoever supervises the run;
    tdd-cli cannot tell who ran it (R8.3)." Drop "a `human_intervention` event," from its
    list. Everything else in the row stays.
  - R8.8 becomes: "`resume --unblock` rows in `human_intervention` are the input to unblocks per
    run, a friction signal: each is a run that stopped and was let go on. No command takes an
    executor identity (R8.3), so the count cannot say who unblocked a run. Who intervened is
    counted outside tdd-cli (geuben/dispatch#217). An abandonment is not an unblock: the rows
    `run abandon` wrote before #186 are left out of the count."
- `README.md`:
  - "Abandoning a run": drop "records a `human_intervention`," from the sentence that lists
    what abandoning does. Add a sentence: the friction log names the reason on an
    `Abandoned:` line in its header.
  - "The friction log": "(declared vs delivered vs skipped vs never-reached cycles, human
    interventions)" becomes "(declared vs delivered vs skipped vs never-reached cycles, and
    unblocks with their notes)".
  - The `tdd metrics` paragraph after it: "blockers, interventions," becomes "blockers,
    unblocks,".
  - The command table:
    - `tdd resume [--unblock --note]`'s description becomes "reconstruct position; `--unblock`
      reopens a blocked run and records an unblock".
    - `tdd run abandon`'s "human only" becomes "for whoever supervises the run".
    - `tdd metrics`' "interventions" becomes "unblocks".
- `examples/skills/tdd-drive/SKILL.md`, "Recovery": "`tdd resume` handles a run interrupted by
  a human intervention." becomes "`tdd resume` handles a run that was unblocked or otherwise
  changed from outside the session." It is shipped (`pyproject.toml` force-includes it), so it
  is tdd-cli output.
- `CHANGELOG.md`, under `## [Unreleased]`, a `### Changed` entry:
  "**Unblocks, not human interventions** (#186). The friction log's "Human interventions: N" is
  now "Unblocks: N", and `tdd metrics`' `human_interventions` key is now `unblocks` (breaking
  for JSON readers; there is no alias). tdd-cli cannot tell who ran `resume --unblock`, so it no
  longer says a person did. `tdd run abandon` no longer counts as one. It stops writing a
  `human_intervention` row, the rows it wrote before are left out of the count, and the
  friction log names the reason on a new `Abandoned:` header line. The ledger schema is
  unchanged."
- `src/tddcli/ledger.py`: `Ledger.reopen_run`'s docstring "the run is live again, and a human
  said why" becomes "the run is live again, and whoever unblocked it said why".
- Leave alone: released `CHANGELOG.md` entries, `docs/split-runner.md` ("`resume --unblock`
  still works"), and `tdd blocker`'s `next_action` detail (decision 10).

## Execution

This plan is executed through `tdd-cli`. **You run every command below yourself** — do not ask the
user to start the run. `tdd run start` records which model is executing, resolved from your own
session; a run started by anyone else attributes this work to the wrong agent.

    git checkout -b issue-186-unblocks-count    # first, before anything else
    tdd doctor                                  # healthy, or failing only for projects this plan cannot reach
    tdd run start --plan tasks/issue-186-unblocks-count.md   # captures baselines, opens cycle 1

`tdd doctor` checks every project; `tdd run start` probes only the ones the plan declares and
those downstream of them through an `[artifact]`. A failing check on a project outside that set
does not stop the run: note it and go on. Any other failing check stops it.

`tdd` is the released tool on `PATH` (0.15.0 at planning), never `uv run tdd` from this tree:
see the note at the top of `tdd.toml`. This plan changes no ledger table, so it needs no frozen
referee. The referee renders this run's own friction log, so that log still says "Human
interventions". That is expected.

If the branch already exists, do not force-checkout and do not pick another name: check it out
only if it carries this plan's commit and no unrelated work, otherwise stop and ask.

Then repeat until done: read `next_action.verb`, do exactly what it says, run `tdd advance`.
Stop when `next_action.terminal` is `true`.

When `next_action.terminal` is `true`, finish the run: render the friction log, commit it, and
raise the PR — see Done-criteria below.

- `tdd advance` is the only command that changes phase. Do not `git add` or `git commit` — the
  tool stages and commits, deriving the file set from the phase.
- The baseline is captured at `run start` and subtracted from later verdicts. The suite is green
  at the plan's base: a fresh worktree of `origin/main` with `uv run pytest -n auto` gives
  `722 passed`. Expect `baselines: {tddcli: 0}` and no standing failures.
- Verbs this plan will hit:
  - `write_test`, `write_implementation`, `refactor_or_advance`.
  - `create_stub`: no cycle declares a stub, and every symbol the tests import exists today. A
    request means an undeclared import.
  - `run_sensitivity_check` → `tdd sensitivity begin|check|end`: for any cycle that pre-passes.
  - `resolve_blocker` → `tdd blocker --kind <plan_defect|environment> --detail '...'`.
  - `confirm_cycle_applicable` on a non-existent cycle → `tdd cycle skip --reason`.
  - This plan declares no annotation keys, so `annotate_cycle` should not appear.
- Cycle 8 is docs only. A refactor phase never carries a behaviour change: if one seems
  needed, raise `plan_defect`.

**Minimal GREEN, per cycle — add this and nothing earlier:**

- cycle 1: `render.metrics`' key `human_interventions` becomes `unblocks`, still counting every
  `ledger.interventions` row. Do not touch `friction_log`.
- cycle 2: `render.friction_log`'s `- Human interventions:` line becomes `- Unblocks:`, still
  listing every `ledger.interventions` row.
- cycle 3: delete the `human_intervention` insert from `Ledger.abandon_run`. Nothing in
  `render.py`.
- cycle 4: `render._unblocks(ledger, run_id)`, which drops a row when the run has an
  `abandonment` row and the row's `note == f"abandoned: {reason}"`. **Match on the note only.**
  Both `metrics` and `friction_log` call it.
- cycle 5: `_unblocks` also requires `row["at"] == abandonment["at"]`.
- cycle 6: the `- Abandoned: <reason>` header line, when `ledger.abandonment(run["id"])` is not
  `None`.
- cycle 7: the `--note` refusal's wording in `cli.cmd_resume`.
- cycle 8: the docs listed above, and nothing in code but `reopen_run`'s docstring.

## Done-criteria

**Before finishing:** run `tdd log render --out tasks/friction-logs/issue-186-unblocks-count-friction.md` and `tdd metrics`. Report the plan-fidelity section — declared vs delivered vs skipped — and every integrity event. Do not narrate what the ledger already records.

Then commit the friction log and raise the PR:

    git add tasks/friction-logs/issue-186-unblocks-count-friction.md
    git commit -m "docs: friction log for issue-186-unblocks-count"

Then invoke the **`raise-pr` skill** (`/raise-pr`), which runs the quality gates, pushes the
branch and opens the PR against `main`. Do not push or call the GitHub API by hand. If a gate
fails, fix it and re-run the skill — a failed gate is work, not a reason to hand back.

The PR body says `Closes #186`.

The done-when "no output of tdd-cli calls an unblock a human intervention" is checked by:

    grep -rniE "human interventions?" src README.md docs examples

It must print nothing. Released `CHANGELOG.md` entries and `tasks/` are history and are not
searched. If it prints a line, fix it in a `docs:` commit or say in the PR body why it stays.

Docs are deliverables, not hopes. Cycle 8 owns them:

- `git diff --stat origin/main -- docs/PRD.md` must be non-empty, or the PR body says why.
- `git diff --stat origin/main -- README.md` must be non-empty, or the PR body says why.
- `git diff --stat origin/main -- examples/skills/tdd-drive/SKILL.md` must be non-empty, or the PR body says why.
- `git diff --stat origin/main -- CHANGELOG.md` must be non-empty, or the PR body says why.

What a user sees changes in two lines of markdown text, one JSON key and one refusal message, so
no demo recording is required. Instead, quote in the PR body:

- the Plan-fidelity section and header of a friction log for a run that was unblocked once and
  then abandoned (`tdd log render`), from this tree (`uv run tdd`, in a scratch repo);
- the matching `tdd metrics` run entry.

The PR body also names the consumers this change breaks outside the repo, for their owners
(decision 11). They are the user-level `implement-issue` skill and `raise-pr`'s Interventions
section, which read the friction log's "Human interventions" header, and geuben/dispatch, which
may read `human_interventions`.
