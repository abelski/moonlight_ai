---
name: sdlc-feature-analyst
description: Plan a feature or bugfix before implementing it — from a confirmed brainstorm idea file or a raw request (clarified via AskUserQuestion), write a checklist plan to plans/improvements/active/ (plans/triage/active/ for a bugfix), have a cold agent review it, get user approval, implement on its own branch via the sdlc-ralph-implement loop, then write the spend report into the plan.
---

You are a feature analyst. Your job is to plan before writing any code. Follow these phases
strictly.

## Session state

The plan keeps this flow's state in a `## Session state` block, a json fence at its end. The side panel reads it, and a
clean session resumes from it. `<plugin root>` is two levels above this skill's folder. The phase names are: Phase 1
`idea`, Phases 2–3 `design`, Phase 4 `implement`, Phase 4.5 `uat`, Phase 5 `docs`, `spendreport` and `close` (by step).

- Once the plan file is written: `python3 <plugin root>/scripts/plan-state.py init <plan> --flow sdlc-feature-analyst
  --phases idea,design,implement,uat,docs,spendreport,close --done idea [--idea <idea file>]`. A plan with no
  `## UAT verification` section leaves `uat` out of `--phases`.
- At the start of each later phase: `python3 <plugin root>/scripts/plan-state.py phase <plan> <name>`. Add
  `--waiting you` while the user is asked (`design`: the approval and the confirmation), `--branch <branch>` once the
  branch exists, and `--blocked` when the implementation or the UAT loop is blocked. Going back to a phase resets every
  later phase to `pending`.
- Resume: if `$ARGUMENTS` is a plan with a `## Session state` block, read its json fence, check out its `branch`, and
  continue from the phase marked `running`, `waiting` or `blocked`. Do not redo `done` phases.

## Phase 1 — Clarify requirements

If `$ARGUMENTS` is a confirmed idea file (`plans/ideas/idea_<N>_<slug>.md`, `status: confirmed`,
written by the `sdlc-brainstorm` skill), it holds the business context (problem, scope, decisions,
precedents) — don't re-ask what it already settles. Reuse its `N` and `slug` for everything below
(plan file `plans/improvements/active/plan_<N>_<slug>.md`), read its precedent plans and mirror their structure where
they fit. Only technical ambiguities the idea and the code can't answer go to `AskUserQuestion`.
An idea file that isn't `confirmed` → stop and run `Skill(skill: "moonlight:sdlc-brainstorm", args: <path>)`
instead.

Otherwise, identify any ambiguities in the feature/bugfix request in `$ARGUMENTS`.

- If anything is unclear (scope, edge cases, affected files, data changes, UI behaviour, etc.),
  use the `AskUserQuestion` tool to ask clarifying questions. Group related questions into a
  single call (up to 4 questions).

Wait for the user to answer before proceeding. Do not guess.

- If the request is clear enough, skip directly to Phase 2.

## Phase 2 — Write the plan (in planning mode)

Call the `EnterPlanMode` tool to enter planning mode, then explore the codebase thoroughly to
understand the affected files, existing patterns, and dependencies. If the project has a codebase
research file (`documentation/codebase-research.md` or `docs/codebase-research.md`, written by
`moonlight:moonlight-init`), read it first, then verify the parts the plan depends on.

Write the plan in English, whatever language the conversation uses. Create the plan file at
`plans/improvements/active/plan_<N>_<slug>.md` (`plans/triage/active/plan_<N>_<slug>.md` for `kind: bugfix`). `N` is the
idea file's number, else the next unused number under `plans/`. Create the folder and its `implemented/` sibling if they
don't exist.

The plan MUST start with YAML frontmatter:

```yaml
---
kind: feature | bugfix
status: draft
iteration: 0
max_iterations: <N>
suggested_model: <sonnet | opus | haiku | fable>
suggested_effort: <low | medium | high | xhigh | max>
confirmed_model: null
confirmed_effort: null
---
```

- `max_iterations` = `clamp((Implementation items + Validation items) * 2, 8, 30)`.
- `suggested_model`/`suggested_effort` are your judgment call based on the nature of the work: a
  mechanical, well-patterned change (e.g. "mirror an existing file for a new one") suggests a
  cheaper/faster tier (`haiku` or `sonnet`, `low`/`medium`); something touching auth, payments,
  data migrations, or genuinely novel design suggests a stronger tier (`opus`, `high`+). State
  your one-line reason in the Context section below — `sdlc-ralph-implement` will show it to the user
  if it needs to reconcile this against their current session settings.

Then these sections, in order:

### Context
If working from an idea file, link it first (`Idea: plans/ideas/idea_<N>_<slug>.md`). Why this is
being built, current behaviour, relevant existing files/patterns found during
exploration. Include your one-line `suggested_model`/`suggested_effort` rationale here.

### Goals
Bulleted list of the explicit, user-facing outcomes this plan delivers.

### Non-Goals
Bulleted list of what's explicitly out of scope — bounds the implementer, prevents scope creep.

### Decisions
The settled answers from grilling or from stand-in agents, one line each: `- [source:confidence] question → answer`.
Source `user` for answers the user gave, `stand-in` for answers from the stand-in agents. Empty is fine if the plan
had no open questions.

### Prototype (optional)
Only for plans that change what a user sees. Step 0 of Implementation is a static mock of the changed
screen(s), saved as an HTML file in the project's scratch folder (`/tmp`, per CLAUDE.md). Copy the
surrounding UI from the real components rather than sketching it. Take screenshots at each width and
language that the Definition of Done names. Stop there for the user's approval: no product code before
it. Approved changes go back into Requirements. Skip the section for backend-only or data-only plans.

### Requirements
Functional requirements, plus a `### Standing constraints` subsection restating this project's
own non-negotiable rules from its `CLAUDE.md` (validation location, testing requirements, design
system usage, whatever applies) — copy the file's own wording rather than inventing one here.

### Implementation
A numbered checklist of every change required, ordered by dependency. Each item should name the
file(s) touched and what changes. Use GitHub-flavoured markdown checkboxes:

```markdown
## Implementation

- [ ] 1. `path/to/file.ext` — what changes and why
- [ ] 2. `path/to/other_file.ext` — what changes and why
```

### Validation
A checklist of how to verify the feature works end-to-end after implementation:

```markdown
## Validation

- [ ] Unit tests: `<test command>`
- [ ] Smoke: <manual or scripted check that the happy path works>
- [ ] Edge case: <a specific edge case named in Requirements>
```

### Definition of Done
The mechanically-verifiable subset of Validation — literal shell commands only, excluding
manual/human-only steps. These get re-run together as the final gate right before the plan is
marked done:

```markdown
## Definition of Done

​```bash
<lint/typecheck command>
<test command>
​```
```

### UAT verification (optional)
Only add this when the change has user-observable behavior worth testing black-box (a chat agent,
an API, a UI flow) *and* the project has some way to drive the running app (a CLI, an HTTP call, a
probe script). Skip it entirely for internal-only changes (a migration, a refactor, a backend job)
with nothing to black-box test.

When included, add `uat_rounds: 0` / `max_uat_rounds: 3` to the frontmatter alongside the other
keys, and a section:

```markdown
## UAT verification

**Instrument:** <the exact command/method a tester with zero codebase access can run as-is to
drive the running app — a CLI invocation, a `curl` against a local endpoint, a probe script>

**Scenarios:**
1. <scripted user input/action>
2. <next input/action>

**Acceptance criteria:** (observable behavior only — no file, constant, or function name)
- [ ] <criterion>
- [ ] <criterion>
```

### Cold review

After writing the file, spawn a **fresh** reviewer that sees none of your reasoning — only files:

```
Agent(subagent_type: "general-purpose", description: "Cold plan review", run_in_background: false,
  prompt: "Review the plan plans/improvements/active/plan_<N>_<slug>.md [against its idea file plans/ideas/idea_<N>_<slug>.md]
  and the repo rules in CLAUDE.md. Read the code the plan touches. Report, ranked: (1) requirements
  the plan misses or contradicts, (2) wrong file/function names or steps that won't work against
  the real code, (3) missing tests or Definition-of-Done checks, (4) over-engineering — anything
  simpler that does the job. Do not edit files. Be concrete: file, line, what to change.")
```

Do not pass it your conversation, summaries or reasoning — the point is a reader with no context,
who catches what the author's own context hides. Fix what's valid in the plan; note what you
rejected and why.

### Approval

Show the user the full plan content in chat plus the review findings (fixed / rejected). Run `plan-state.py init` and
`plan-state.py phase <plan> design --waiting you` (see Session state); if planning mode refuses the commands, run both
right after `ExitPlanMode` in Phase 3. Then use the `AskUserQuestion` tool to ask:

- Question: "Plan saved to `<plan path>`. Ready to proceed?"
- Options: "Approve — start implementation", "Revise — I have corrections"

If the user selects "Revise", ask a follow-up `AskUserQuestion` for their corrections, update the
plan file, show the revised plan, and ask for approval again. Repeat until approved. Stay in
planning mode throughout all revisions.

When the user selects "Approve", flip the plan file's frontmatter `status: draft` →
`status: approved` before moving to Phase 3.

## Phase 3 — Confirm implementation start

When the user approves the plan:

1. Call `ExitPlanMode` to leave planning mode.
2. Use the `AskUserQuestion` tool to confirm:
   - Question: "This will modify code via a bounded, self-correcting loop (up to
     <max_iterations> retry attempts on validation failures before the plan is marked blocked for
     review). Proceed with implementation?"
   - Options: "Yes — implement now", "No — let me reconsider"

If the user selects "No", stop and use `AskUserQuestion` to ask what they want to change.

On "Yes", create the change's own branch **before the first code edit** — never edit code on the
main branch. Idea and plan files were written on main, uncommitted; they carry into the branch:

```bash
git checkout -b feat/<N>-<slug>   # feat/<slug> without an idea number; fix/... for kind: bugfix
```

Right after the branch is created, set `started_at` in the plan's frontmatter to the current UTC time
(`date -u +%Y-%m-%dT%H:%M:%SZ`). The spend report in Phase 5 counts from it. Then run
`plan-state.py phase <plan> implement --branch <branch>`.

If main has unrelated uncommitted changes, stop and ask the user — don't carry them along. Only the
user commits, merges and pushes (this repo's hook blocks the agent from `git commit`/`git push`).

## Phase 4 — Implement via sdlc-ralph-implement

Delegate implementation entirely to the shared implementer loop:

```
Skill(skill: "moonlight:sdlc-ralph-implement", args: "<plan path>")
```

`sdlc-ralph-implement` owns all further checkbox flipping, validation retries, iteration/blocked-state
bookkeeping, and the final Definition-of-Done gate. Do not duplicate any of that logic here.

- If it reports `status: done` — proceed to Phase 4.5 if the plan has a `## UAT verification`
  section, otherwise straight to Phase 5.
- If it reports `status: blocked` — run `plan-state.py phase <plan> implement --blocked`, relay its
  `## Blocked` section to the user verbatim and stop. Do not attempt to silently finish the plan yourself.

## Phase 4.5 — Black-box UAT verification (only if the plan defines it)

Reproduction/unit tests passing is not proof the behavior is right — they were written by the same
mind that wrote the fix. This loop hands judgment to something that has never seen the code. Run `plan-state.py phase <plan> uat` first;
when `uat_rounds` runs out, `plan-state.py phase <plan> uat --blocked`.

1. Spawn a `moonlight:sdlc-uat-tester` subagent (`Agent(subagent_type: "moonlight:sdlc-uat-tester")`) with **exactly three
   things**: the plan's `Instrument`, `Scenarios`, and `Acceptance criteria` — verbatim — plus a
   verdict path (e.g. `<plan path without .md>-uat-round-<n>.md`). Never send it the plan file itself,
   the diff, the tests, or your theory of the fix; its independence is the value.
2. Read the verdict:
   - **PASS** — proceed to Phase 5.
   - **FAIL** — bump `uat_rounds` in the plan frontmatter, persist. If `uat_rounds >=
     max_uat_rounds`: set `status: blocked`, report the verdict to the user, stop. Otherwise: hand
     the tester's transcript and criteria **verbatim** (no added diagnosis of your own — you're the
     mind that got it wrong the first time) to a `moonlight:sdlc-ralph-implementer` fix pass targeting this plan
     file, then repeat step 1.
   - **INCONCLUSIVE** (the instrument itself never produced a real answer — env/quota/network) —
     doesn't consume a round; fix the environment and retry step 1.
3. Never mark the plan done on a FAIL, and never relax a criterion to force a PASS — a criterion is
   only edited when it was wrong about the desired behavior, and you say so if you do.

## Phase 5 — Wrap up

Once `sdlc-ralph-implement` reports the plan done:

1. Run `plan-state.py phase <plan> docs`. If this project maintains `specs/` (living current-behavior docs), spawn a
   `moonlight:sdlc-spec-writer` subagent (`Agent(subagent_type: "moonlight:sdlc-spec-writer")`) per touched component
   to update `specs/<component>.md` — see the `moonlight:sdlc-spec-writer` agent. Optional; skip if the project
   doesn't use this convention.
2. **Spec gate** (only if the idea file has a `## Proposed spec`). Check each proposed scenario against
   the shipped behavior as the updated spec describes it. A promised scenario that did not ship: correct
   the idea file to match what shipped, and tell the user. Something that shipped but the proposal did
   not name: add it to the idea file, tagged `New`. Do not move any file until this gate passes.
3. Spend report: run `plan-state.py phase <plan> spendreport`, then
   `python3 <plugin root>/scripts/token-report.py --plan <plan path>`. It counts the sessions in the state block from
   the plan's `started_at`, subagents included, and writes or replaces the plan's `## spendreport` section. Tell the
   user one line: the spend report is in the plan. If it fails, show its message and stop before the move.
4. Run `plan-state.py phase <plan> close`. Move the file: `plans/improvements/active/plan_<N>_<slug>.md` →
   `plans/improvements/implemented/` (`plans/triage/active/` → `plans/triage/implemented/` for a bugfix). If there's
   an idea file, move it too: `plans/ideas/idea_<N>_<slug>.md` → `plans/ideas/implemented/`.
5. If this project keeps a changelog, append a row describing what changed.
6. Any project-specific epilogue (announcing the change, notifying someone, closing a linked
   ticket) is the caller's responsibility, not this skill's — `sdlc-ralph-implement` is
   pipeline-agnostic and never publishes or notifies anything on its own.
7. Hand the branch to the user: tell them how to test it locally and give the commands to run
   once they're happy — `git add -A && git commit -m "feat(<area>): <summary> (#<N>)"`, then
   `git checkout main && git merge --no-ff feat/<N>-<slug>`. If they request changes instead, add
   them as new unchecked items to the plan, set `status: in_progress`, and re-run
   `Skill(skill: "moonlight:sdlc-ralph-implement", args: <plan path>)` on the same branch.

## Notes

- Keep solutions simple — no over-engineering.
- Follow existing code conventions in this repo.
- Do not push to git without an explicit directive from the user.
