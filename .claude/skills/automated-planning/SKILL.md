---
name: automated-planning
description: Plan an issue labelled needs-plan with nobody present, in a dispatch slot. Either opens a PR with a hardened plan, when every design choice can be settled from evidence, or opens nothing and comments the decisions a person must make. Use when the prompt is "/automated-planning NNN". Never use it interactively; there, use /plan-issue.
---

# automated-planning

You are planning issue **#$0** in a dispatch slot. Nobody is watching and nobody will
answer a question. The console started this run because the issue is labelled `needs-plan`,
after an investigation reproduced the bug (dispatch ADR-0006), or after classify labelled it an
enhancement (dispatch ADR-0005), when there is no investigation to read. The rules are in
geuben/dispatch's
[ADR-0007](https://github.com/geuben/dispatch/blob/main/docs/adr/0007-automated-planning-plans-or-asks-and-merge-hands-on.md);
this repo's settings for it are in `.dispatch.toml`.

Console notes (the first word is the issue number; follow the rest): $ARGUMENTS

**Planning is all or nothing.** End in exactly one of two ways:

- **Planned:** every design choice is settled. Open a PR from `plan/issue-N` that adds the
  hardened plan, then swap `needs-plan` for `plan-review`.
- **Needs a decision:** at least one product or design choice is open. Open **no** branch and
  **no** PR. Comment the decisions on the issue, then swap `needs-plan` for `needs-decision`.

The console checks which happened. A run that does neither is recorded `refused`.

## Hard rules

- Never label the issue `hardened`. Never edit the issue body. When the plan PR merges,
  dispatch's handoff adds the label and the `Task file:` line.
- Never push to `main`. Never write implementation code: the plan is the only deliverable.
- Never close the issue, and never put a closing keyword (`close`, `fix`, `resolve` and their
  forms) next to `#N` in the PR's title or body, or in a commit message. Write `Refs #N`.
- Never use `AskUserQuestion` or wait for input. Where `/plan-issue` says to ask the user, the
  choice is either yours to settle from evidence, or an open decision (step 3).
- Use `gh` for GitHub. If a hook blocks bare `gh`, use `ghx` with the same arguments.

## 1. Check the issue is still yours

```sh
gh issue view $0 --json state,labels,body,comments
gh pr list --head plan/issue-$0 --state open --json number,url
```

Stop without changing anything if any of these holds: the issue is closed, it no longer has
`needs-plan`, or a `plan/issue-$0` PR is already open. Say why in your final message.

## 2. Gather the evidence

Read the `/plan-issue` skill (`~/.claude/skills/plan-issue/SKILL.md`), and the repo's notes
for it, `.claude/plan-issue.md` and every note in `.claude/plan-issue/*.md`, which bind this plan
as they bind any other. They hold what earlier plans here learned the hard way: the referee is
the released `tdd` on `PATH`, how a RED dies through `conftest.run_cli`, where spawns must live,
when `SCHEMA_VERSION` needs a bump. You will follow its Phase 0, A (except where noted), B, D and E. **If
that skill is not installed, stop:** say so in your final message and change nothing. Without its
hardening rules a plan cannot be hardened, and the console will record the run `refused` for a
person to see.

Then read, in this order:

1. **The issue and every comment.** Two kinds of comment matter most:
   - **The investigation's report**, the comment starting `<!-- dispatch:investigate`. It has
     the root cause with file:line references, the steps to reproduce, the suggested fix, and
     the calls it left open. Verify its claims against the code; do not trust them blindly.
   - **Answers from people**, which follow an earlier `<!-- dispatch:plan needs-decision -->`
     comment of yours. **Each answer is a locked decision.** Record it as decided by a person,
     with a link to the comment, and do not re-open it.
2. **The failing test** on `investigate/issue-$0`, if that branch exists:
   `git fetch origin investigate/issue-$0 && git diff origin/main...FETCH_HEAD`.
   It is usually the first RED cycle of the plan. Carry its test into the plan; do not merge
   the branch.
3. **What is already decided.** There is no `docs/adr/` here. Read `docs/PRD.md` (the spec,
   cited by section, e.g. §6.1), `docs/split-runner.md`, `docs/harness-integration.md`, the
   README and `CONTRIBUTING.md`.
4. **Earlier plans** in `tasks/issue-*.md` that touch the same modules, and the audits in
   `tasks/friction-audits/` if there are any. A plan here is named
   `tasks/issue-$0-<kebab-slug>.md`; copy the shape of a recent one (its front matter, its
   Execution and Done-criteria blocks).

In `/plan-issue`'s Phase A, the "already planned?" question has one answer here: if the issue
already names a plan on `main`, open decision (step 3) — "re-plan, or keep the existing plan?".

## 3. Settle the decision tree (in place of Phase C)

List every design branch the plan needs, as Phase C does, then put each one into exactly one
group:

- **Settled by evidence.** The code, an ADR, the issue, a person's answer, or the
  investigation (once verified) decides it. Record the decision and cite the evidence.
- **Settled by convention.** A choice the repo already makes the same way elsewhere, or that
  a careful maintainer would not need asking about. Examples: a refusal is an
  `envelope.failure(...)` with its `reason` under `result.reason`, like every other verb's; a
  new per-project knob goes in `tdd.toml`'s project table beside its siblings, with a default
  that keeps today's behaviour; new ledger state is a new table (no `SCHEMA_VERSION` bump)
  rather than a changed one; a new spawn goes through `src/tddcli/actor.py`; a user-visible
  change gets a line under `## [Unreleased]` in `CHANGELOG.md`. Record the decision, the
  convention, and where else the repo does the same.
- **Open.** A genuine product or design choice with real trade-offs that nothing above
  settles: what a harness or a person sees or can do (a new verb, flag or output field, and
  its name), a policy (what to keep, what to refuse, who decides), a change to what
  `docs/PRD.md` specifies, a change to an existing ledger table's shape (it needs a schema
  bump and a frozen referee), or two approaches whose costs differ and that the evidence
  cannot rank.

"Needs a decision" is not a reason to cut scope, here or anywhere (`/plan-issue`'s Scope
policy). It is a reason to ask. **Stop for open decisions only.** Asking about something the
repo already answers costs a person a round trip for nothing.

If any branch is **open**, go to step 4a. Otherwise go to step 4b.

## 4a. Needs a decision: comment, swap the label, stop

Settle every branch you can first, so that the person sees the open ones in context and the
next run does not have to redo the work. Then write one comment, in this shape:

```markdown
<!-- dispatch:plan needs-decision -->
**Automated planning stopped: N decision(s) need a person before this can be planned.**

### 1. <the decision, as a question>
<why it matters, and what depends on it>

- **A. <option> (recommended)**: <what it means, and its trade-off>
- **B. <option>**: <what it means, and its trade-off>

Evidence: <file:line, ADR or comment links that bear on it>

### 2. ...

### Already settled
- <each decision you made, one line, with its evidence or convention>

**To continue:** reply with your choices (for example "1A, 2B"), then swap `needs-decision`
back to `needs-plan`. The next planning run treats the answers as decided.
```

The first line must be exactly `<!-- dispatch:plan needs-decision -->`. Post it, then swap the
labels in one edit:

```sh
gh issue comment $0 --body-file <file>
gh issue edit $0 --remove-label needs-plan --add-label needs-decision
```

Stop. Do not create a branch, a plan file or a PR.

## 4b. Planned: draft, harden, open the plan PR

1. Create the branch: `git checkout -b plan/issue-$0 origin/main`.
2. Draft the plan (`/plan-issue` Phase D) at `tasks/issue-$0-<kebab-slug>.md`, with `closes: $0` in its
   front matter. Its **Design decisions (locked)** section names, for each decision, what
   decided it: evidence, convention, or a person (linked).
3. Harden it (`/plan-issue` Phase E, every step), with these changes:
   - **E-15:** commit the plan on this branch, and register the contract. Registration must
     succeed. If it cannot, and fixing that needs a choice, the choice is an open decision
     (step 4a). Delete the branch locally; do not push it. Register with the released `tdd`
     on `PATH`, never `uv run tdd` from this tree (the note at the top of `tdd.toml`). If no
     released `tdd` is on `PATH`, that is the slot's fault, not a design choice: stop, change
     nothing, and say so in your final message.
   - **E-18:** skip it all. Do not label the issue, and do not edit its body. Dispatch's handoff
     does both when the PR merges.
   - **E-19:** the readiness report goes into the PR body, not to a user.
   - If hardening turns up an open decision, go to step 4a. Do not push the branch.
4. Push the branch and open the PR against `main`:

   ```sh
   git push -u origin plan/issue-$0
   gh pr create --base main --head plan/issue-$0 \
     --title "plan: <name> (#N)" --body-file <file>
   ```

   The body starts with the summary of the plan and its **Design decisions (locked)**, each
   with what decided it, so a reviewer can disagree with one quickly. Then comes the readiness
   report, and then `Refs #N` on its own line. Merging this PR approves the plan: dispatch's handoff
   then labels the issue `hardened`, and the fix may start unattended. Closing it unmerged
   sends the issue back to `needs-decision`.

   When any cycle's `files` or `stub_expected`, or the plan's `ancillary_files`, names a path
   under `.github/workflows/`, the body's first line is exactly:

   This plan edits `.github/workflows/`: merging this plan labels #$0 `<label>` (if you merge it yourself).

   `<label>` is the `label` in the repo's `.dispatch.toml` `[ci]` table, or `ci` when there is
   none (there is none today). A run without the console's `ci` grant cannot push such a change: GitHub rejects the
   whole push, so the run hands the change back as a patch instead (dispatch ADR-0022). Merging the
   plan adds the label when the person who merges it is in the handoff's `HANDOFF_CI_ACTORS`
   (dispatch ADR-0023); anyone else labels the issue by hand before merging.
5. Comment on the issue, and swap the labels:

   ```sh
   gh issue comment $0 --body "<!-- dispatch:plan planned -->
   Plan PR: <url>. Merge it to approve the plan; close it to send this back for a decision."
   gh issue edit $0 --remove-label needs-plan --add-label plan-review
   ```

## 5. Final message

End with one paragraph: which way the run ended, the PR or comment URL, and each decision
with how it was settled. It goes to the run's log, which a person reads when something looks
wrong.
