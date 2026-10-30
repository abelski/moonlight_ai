---
name: moonlight-fast
description: Light entry point for a small or clear change. Takes a requirement text, grills the user on the idea, writes a plan the user reviews, implements it on a feature branch with TDD, reviews and validates it, updates docs and specs, reports the token use and closes. The user takes part in the idea grilling, the plan review and the acceptance. Use when the user wants a change done without the full brainstorm step.
---

Run the change described in `$ARGUMENTS`. If `$ARGUMENTS` is empty, ask once for the requirement text. If it is a path to a
file, read the file. The user takes part at three points: the idea grilling (phase 2), the plan review (phase 3), and the
acceptance (phase 5). Everything else runs without questions. Write every file in English.

## Phase 0 — Repo checks

- Git repo, clean tree, main branch (`git symbolic-ref --short refs/remotes/origin/HEAD`, else `main`). If the tree is
  dirty, stop and ask.
- Read `CLAUDE.md` for standing constraints and the `## Moonlight adapters` keys.
- If the project has a codebase research file (`documentation/codebase-research.md` or `docs/codebase-research.md`), read it.

## Phase 1 — Research

Look at the code the requirement names: grep, targeted reads. A large repo gets one `Explore` agent with the requirement and
the question "which files and patterns does this touch". The findings go into the plan's `## Context`.

## Phase 2 — Idea (the user grills)

Run `Skill(skill: "moonlight:productivity-grilling", args: <requirement text + research findings>)`. The user answers. Each
settled answer is one line in the plan's `## Decisions` with source `user`. Stop when the idea is settled: the problem, the
outcome, the scope and non-goals, the edge cases, and how we will know it works. No idea file is written.

## Phase 3 — Design (the user reviews the plan)

Write `plans/improvements/active/plan_<N>_<slug>.md` in the format of `sdlc-feature-analyst` Phase 2 (frontmatter, Context,
Goals, Non-Goals, Requirements, Implementation, Validation, Definition of Done). Add `## Decisions` (from phase 2) and
`## Proposed spec` (the Gherkin scenarios this change adds or changes, tagged New, Changed or Removed, if the project keeps
`specs/`). Set `started_at: null` in the frontmatter.

Show the file in chat and ask the user to review it in the editor. Use `AskUserQuestion`: "Plan saved to `<path>`. Approve?"
Options: "Approve", "Revise". On revise, update the file and ask again.

## Phase 4 — Implementation (TDD, on a branch)

- Create `feat/<N>-<slug>` from main, before the first code edit. Set `started_at` in the plan frontmatter to the current UTC
  time, `date -u +%Y-%m-%dT%H:%M:%SZ`.
- Run `Skill(skill: "moonlight:sdlc-ralph-implement", args: "<plan path>")`. It implements each item test-first, runs the
  reviewer gate, the validation commands and the Definition of Done.
- `status: blocked`: relay its `## Blocked` section to the user and stop.
- `status: done`: go on to phase 5.

## Phase 5 — Validation and acceptance (the user accepts)

- If the plan has a `## UAT verification` section, run the black-box loop of `sdlc-feature-analyst` Phase 4.5.
- Tell the user how to try the change locally and what to look at. Use `AskUserQuestion`: "Accept the change?" Options:
  "Accept", "Changes needed". On changes, add them as new unchecked items to the plan, set `status: in_progress`, and run
  phase 4 again on the same branch.

## Phase 6 — Documentation and specs

- If the project keeps `specs/`, run `moonlight:sdlc-spec-writer` once per touched component (plan path given). Then run the
  spec gate: each `## Proposed spec` scenario must match the shipped behavior. Correct the plan's proposal if something did not
  ship, and tell the user.
- Update the docs and README for what changed, with `moonlight:sdlc-update-readme` if the change needs it.

## Phase 7 — Check (tokens)

Run the token report for this run:

```bash
python3 <plugin root>/scripts/token-report.py --since <started_at from the plan> --json
```

The plugin root is two levels above this skill's folder. Show the user the totals: messages counted, input, cache writes,
cache reads, output, and the billable total.

## Phase 8 — Close

- Move the plan to `plans/improvements/implemented/` (same filename).
- If the project keeps a changelog, add a row.
- Report: the branch is ready. Give the user the commands to run: `git add -A && git commit -m "feat(<area>): <summary> (#<N>)"`,
  then `git checkout main && git merge --no-ff feat/<N>-<slug>`. Claude does not commit or merge in this flow.

## Notes

- Keep solutions simple. Do not push to git.
- If a phase cannot run (no codebase research file, no `specs/` folder, no UAT section), say so in one line and go on.
