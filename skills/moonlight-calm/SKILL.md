---
name: moonlight-calm
description: Autonomous entry point. Takes a requirement text as the idea, makes every decision itself through stand-in agents, implements on a feature branch with TDD, reviews, validates, updates docs and specs, reports the token use and closes. It asks the user only to escalate a risk it cannot settle, and at the end for acceptance. Use when the user wants a change built unattended and reviewed at the end.
---

Run the change described in `$ARGUMENTS` without asking the user, except at the escalation points and at acceptance. If
`$ARGUMENTS` is empty, ask once for the requirement text. If it is a path to a file, read the file. The requirement text is
the idea, taken as given: there is no grilling. Write every file in English.

Every decision goes into the plan's `## Decisions` section, one line each: `- [source:confidence] question → answer`. The
source is `stand-in` or `user`. The confidence is `high`, `medium` or `low`.

## Phase 0 — Repo checks

- Git repo, clean tree, main branch (`git symbolic-ref --short refs/remotes/origin/HEAD`, else `main`). If the tree is
  dirty, stop and escalate.
- Read `CLAUDE.md` for standing constraints and the `## Moonlight adapters` keys.
- If the project has a codebase research file (`documentation/codebase-research.md` or `docs/codebase-research.md`), read it.

## Phase 1 — Research

Look at the code the requirement names, as in `moonlight-fast`. A large repo gets one `Explore` agent. No questions.

## Phase 2 — Design (stand-ins)

1. Open points: list every point the plan needs settled that the requirement does not settle. For each one, ask
   `moonlight:sdlc-stand-in-product-owner` with the point, the requirement text and the research findings. It returns an
   answer, a confidence and any flags. Record each answer in `## Decisions`.
2. Write `plans/improvements/active/plan_<N>_<slug>.md` in the format of `sdlc-feature-analyst` Phase 2, with `## Decisions`
   and `## Proposed spec` (if the project keeps `specs/`). Set `started_at: null`.
3. Ask `moonlight:sdlc-stand-in-tech-lead` to review the plan against the requirement and the research. It approves, or
   returns findings. On findings, fix the plan and ask once more. A second round of findings escalates.

## Escalation (the only other place the user is asked)

Stop the run and ask the user, with the stop reason and the exact answer needed, when any of these holds:

- a stand-in returns confidence `low`;
- a stand-in flag is in this list: `security`, `auth`, `data-migration`, `breaking-change`, `public-api`;
- the plan has more than 12 checklist items: propose how to split it, and ask which part to run first;
- the reviewer asks for changes twice in a row;
- `sdlc-ralph-implement` reports `blocked`;
- the UAT section fails (only if the plan has one).

Nothing else asks the user.

## Phase 3 — Branch and implementation (TDD)

- Create `feat/<N>-<slug>` from main, before the first code edit. Set `started_at` in the plan frontmatter to the current UTC
  time, `date -u +%Y-%m-%dT%H:%M:%SZ`.
- Run `Skill(skill: "moonlight:sdlc-ralph-implement", args: "<plan path>")`. It implements each item test-first, runs the
  reviewer gate, the validation commands and the Definition of Done.
- `status: blocked`: escalate with its `## Blocked` section.

## Phase 4 — Documentation and specs

- If the project keeps `specs/`, run `moonlight:sdlc-spec-writer` once per touched component (plan path given). Then run the
  spec gate: each `## Proposed spec` scenario must match the shipped behavior. If a promised scenario did not ship, correct the
  proposal and record the change in `## Decisions` as `stand-in`.
- Update the docs and README for what changed, with `moonlight:sdlc-update-readme` if the change needs it.

## Phase 5 — Validation and acceptance (the user accepts)

- If the plan has a `## UAT verification` section, run the black-box loop of `sdlc-feature-analyst` Phase 4.5.
- Print the decisions ledger: every `## Decisions` line, with its source and confidence.
- Tell the user how to try the change locally. Use `AskUserQuestion`: "Accept the change?" Options: "Accept", "Changes
  needed". On changes, add them as new unchecked items to the plan, set `status: in_progress`, and run phase 3 again on the
  same branch.

## Phase 6 — Check (tokens)

```bash
python3 <plugin root>/scripts/token-report.py --since <started_at from the plan> --json
```

The plugin root is two levels above this skill's folder. Show the user the totals: messages counted, input, cache writes,
cache reads, output, and the billable total.

## Phase 7 — Close

- Move the plan to `plans/improvements/implemented/` (same filename).
- If the project keeps a changelog, add a row.
- Report: the branch is ready. Give the user the commands to run: `git add -A && git commit -m "feat(<area>): <summary> (#<N>)"`,
  then `git checkout main && git merge --no-ff feat/<N>-<slug>`. Claude does not commit or merge in this flow.

## Notes

- Keep solutions simple. Do not push to git.
- If a phase cannot run (no codebase research file, no `specs/` folder, no UAT section), say so in one line and go on.
