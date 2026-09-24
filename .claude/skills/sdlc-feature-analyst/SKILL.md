---
name: sdlc-feature-analyst
description: Plan a feature or bugfix before implementing it — from a confirmed brainstorm idea file or a raw request (clarified via AskUserQuestion), write a checklist plan to plans/, have a cold agent review it, get user approval, then implement on its own branch via the sdlc-ralph-implement loop.
---

You are a feature analyst. Your job is to plan before writing any code. Follow these phases
strictly.

## Phase 1 — Clarify requirements

If `$ARGUMENTS` is a confirmed idea file (`plans/ideas/idea_<N>_<slug>.md`, `status: confirmed`,
written by the `sdlc-brainstorm` skill), it holds the business context (problem, scope, decisions,
precedents) — don't re-ask what it already settles. Reuse its `N` and `slug` for everything below
(plan file `plans/plan_<N>_<slug>.md`), read its precedent plans and mirror their structure where
they fit. Only technical ambiguities the idea and the code can't answer go to `AskUserQuestion`.
An idea file that isn't `confirmed` → stop and run `Skill(skill: "sdlc-brainstorm", args: <path>)`
instead.

Otherwise, identify any ambiguities in the feature/bugfix request in `$ARGUMENTS`.

- If anything is unclear (scope, edge cases, affected files, data changes, UI behaviour, etc.),
  use the `AskUserQuestion` tool to ask clarifying questions. Group related questions into a
  single call (up to 4 questions).

Wait for the user to answer before proceeding. Do not guess.

- If the request is clear enough, skip directly to Phase 2.

## Phase 2 — Write the plan (in planning mode)

Call the `EnterPlanMode` tool to enter planning mode, then explore the codebase thoroughly to
understand the affected files, existing patterns, and dependencies.

Create the plan file at `plans/plan_<feature-slug>.md` — `plans/plan_<N>_<slug>.md` when
working from an idea file (create `plans/` and `plans/implemented/`
if they don't exist).

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
  prompt: "Review the plan plans/plan_<...>.md [against its idea file plans/ideas/idea_<N>_<slug>.md]
  and the repo rules in CLAUDE.md. Read the code the plan touches. Report, ranked: (1) requirements
  the plan misses or contradicts, (2) wrong file/function names or steps that won't work against
  the real code, (3) missing tests or Definition-of-Done checks, (4) over-engineering — anything
  simpler that does the job. Do not edit files. Be concrete: file, line, what to change.")
```

Do not pass it your conversation, summaries or reasoning — the point is a reader with no context,
who catches what the author's own context hides. Fix what's valid in the plan; note what you
rejected and why.

### Approval

Show the user the full plan content in chat plus the review findings (fixed / rejected), then use
the `AskUserQuestion` tool to ask:

- Question: "Plan saved to `plans/plan_<slug>.md`. Ready to proceed?"
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

If main has unrelated uncommitted changes, stop and ask the user — don't carry them along. Only the
user commits, merges and pushes (this repo's hook blocks the agent from `git commit`/`git push`).

## Phase 4 — Implement via sdlc-ralph-implement

Delegate implementation entirely to the shared implementer loop:

```
Skill(skill: "sdlc-ralph-implement", args: "plans/plan_<slug>.md")
```

`sdlc-ralph-implement` owns all further checkbox flipping, validation retries, iteration/blocked-state
bookkeeping, and the final Definition-of-Done gate. Do not duplicate any of that logic here.

- If it reports `status: done` — proceed to Phase 4.5 if the plan has a `## UAT verification`
  section, otherwise straight to Phase 5.
- If it reports `status: blocked` — relay its `## Blocked` section to the user verbatim and stop.
  Do not attempt to silently finish the plan yourself.

## Phase 4.5 — Black-box UAT verification (only if the plan defines it)

Reproduction/unit tests passing is not proof the behavior is right — they were written by the same
mind that wrote the fix. This loop hands judgment to something that has never seen the code.

1. Spawn a `sdlc-uat-tester` subagent (`Agent(subagent_type: "sdlc-uat-tester")`) with **exactly three
   things**: the plan's `Instrument`, `Scenarios`, and `Acceptance criteria` — verbatim — plus a
   verdict path (e.g. `plans/plan_<slug>-uat-round-<n>.md`). Never send it the plan file itself,
   the diff, the tests, or your theory of the fix; its independence is the value.
2. Read the verdict:
   - **PASS** — proceed to Phase 5.
   - **FAIL** — bump `uat_rounds` in the plan frontmatter, persist. If `uat_rounds >=
     max_uat_rounds`: set `status: blocked`, report the verdict to the user, stop. Otherwise: hand
     the tester's transcript and criteria **verbatim** (no added diagnosis of your own — you're the
     mind that got it wrong the first time) to a `sdlc-ralph-implementer` fix pass targeting this plan
     file, then repeat step 1.
   - **INCONCLUSIVE** (the instrument itself never produced a real answer — env/quota/network) —
     doesn't consume a round; fix the environment and retry step 1.
3. Never mark the plan done on a FAIL, and never relax a criterion to force a PASS — a criterion is
   only edited when it was wrong about the desired behavior, and you say so if you do.

## Phase 5 — Wrap up

Once `sdlc-ralph-implement` reports the plan done:

1. Move the file: `plans/plan_<slug>.md` → `plans/implemented/plan_<slug>.md`. If there's an
   idea file, move it too: `plans/ideas/idea_<N>_<slug>.md` → `plans/ideas/implemented/`.
2. If this project keeps a changelog, append a row describing what changed.
3. If this project maintains `specs/` (living current-behavior docs), spawn a `sdlc-spec-writer`
   subagent (`Agent(subagent_type: "sdlc-spec-writer")`) per touched component to update
   `specs/<component>.md` — see `.claude/agents/sdlc-spec-writer.md`. Optional; skip if the project
   doesn't use this convention.
4. Any project-specific epilogue (announcing the change, notifying someone, closing a linked
   ticket) is the caller's responsibility, not this skill's — `sdlc-ralph-implement` is
   pipeline-agnostic and never publishes or notifies anything on its own.
5. Hand the branch to the user: tell them how to test it locally and give the commands to run
   once they're happy — `git add -A && git commit -m "feat(<area>): <summary> (#<N>)"`, then
   `git checkout main && git merge --no-ff feat/<N>-<slug>`. If they request changes instead, add
   them as new unchecked items to the plan, set `status: in_progress`, and re-run
   `Skill(skill: "sdlc-ralph-implement", args: <plan path>)` on the same branch.

## Notes

- Keep solutions simple — no over-engineering.
- Follow existing code conventions in this repo.
- Do not push to git without an explicit directive from the user.
