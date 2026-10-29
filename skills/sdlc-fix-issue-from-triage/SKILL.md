---
name: sdlc-fix-issue-from-triage
description: Fix a triaged issue from plans/triage/active/ — delegate the fix and tests to the sdlc-ralph-implement loop, then confirm resolution with the user before updating the tracker and moving the plan to implemented/. Companion to the sdlc-triage skill, which drafts the plan this one executes.
---

Fix a triaged issue by following its pre-written plan from `plans/triage/active/`. This skill
knows nothing about any *specific* tracker — Step 6 runs the project's `Resolve in
tracker` command from `## Moonlight adapters` in `CLAUDE.md`.

## Step 1 — Locate the plan file

If `$ARGUMENTS` is provided, treat it as an issue number (e.g. `35`) or partial filename.

- Search `plans/triage/active/` (not `implemented/` or `hold/`) for a file matching
  `issue-<number>` or the given string.
- If no match is found, list all open plan files and use `AskUserQuestion` to ask which one to fix.

`sdlc-triage` always writes plan files with `status: draft` — there's no separate approval UI for this
pipeline the way `sdlc-feature-analyst` has one; the user invoking this skill on a specific issue *is*
the approval. If the located plan's `status` is still `draft`, flip it to `approved` now, before
delegating in Step 3 (this is what lets `sdlc-ralph-implement` proceed instead of bouncing it back as
unapproved).

Then create the fix's own branch before any code edit — never fix on the main branch:
`git checkout -b fix/<N>-<slug>` (slug from the plan filename). If main has unrelated uncommitted
changes, stop and ask the user first.

## Step 2 — Reproduce the reported symptom

Before delegating, reproduce the symptom through the project's real path: call the endpoint, run the
command, or load the page, and read the output or the server log. Write what you observed as a
`Reproduced:` line under the plan's `## Root cause`. If it does not reproduce, or the real cause
differs from `## Root cause`, the plan is a hypothesis: correct it in place with a dated `CORRECTION`
note, keep the original analysis, and tell the user before implementing anything.

## Step 3 — Delegate the fix and tests

```
Skill(skill: "moonlight:sdlc-ralph-implement", args: "plans/triage/active/issue-<N>-*.md")
```

`sdlc-ralph-implement` reads the plan's `## Root cause` and `## Fix plan` checklist, applies each item,
then works through `## Tests`, running real commands and retrying failures up to the plan's
`max_iterations` before giving up. It owns all checkbox flipping, retry/iteration bookkeeping, and
the final `## Definition of Done` gate. Do not duplicate any of that logic here.

- If it reports `status: blocked` — relay its `## Blocked` section to the user verbatim and stop.
  Do not attempt to silently finish the fix yourself.
- If it reports `status: done` and the plan has a `## UAT verification` section — run the same
  Phase 4.5 black-box loop `sdlc-feature-analyst` uses (spawn `moonlight:sdlc-uat-tester`, retry via
  `moonlight:sdlc-ralph-implementer` up to `max_uat_rounds`, blocked on exhaustion) before Step 3b.
- If it reports `status: done` (no UAT section, or UAT passed) — proceed to Step 3b. The plan file
  is still in `plans/triage/active/` at this point (`sdlc-ralph-implement` never moves files — that
  stays this skill's job, see Step 6).

## Step 3b — Red check on the regression test

Once the delegation reports `status: done`, the plan's `## Tests` must include a regression test for the
reported symptom. Confirm that it can fail. Create a temporary worktree at the base commit
(`git worktree add <tmp-dir> <base>`), copy the new test into it, and run it there. It must fail for the
reported reason. Never use `git stash` or `reset` on the user's uncommitted work. A test that passes on
the unfixed code guards nothing: rewrite it, then run the delegation again. Remove the worktree afterwards.

## Step 4 — Optional smoke check

If this project has an obvious way to manually exercise the fix (a running dev server, a CLI
command, a script) and the plan or the issue names a specific page/flow to check, exercise it now
and verify the specific behavior the issue reported is now correct. Skip this step entirely if
there's no clear way to do it — it's a human-facing sanity check on top of `## Tests`, not a
replacement for it, and not worth inventing a check that doesn't already fit the project.

## Step 5 — Confirm resolution with user

Use `AskUserQuestion` to ask:
- Question: `"Issue #<N> — <one-line summary of what was fixed>. Mark as resolved?"`
- Options: `"Yes — mark resolved"`, `"No — something looks wrong"`

If the user selects **No**, ask a follow-up `AskUserQuestion`: "What still looks wrong?" and
investigate.

## Step 6 — Update the tracker and move the plan

Only if the user selected **Yes**:

1. Read the `Resolve in tracker` key under `## Moonlight adapters` in this project's `CLAUDE.md`. If the key is
   missing or `(not set)`, stop this step and ask the user how this issue gets resolved. Do not guess a command.
   Otherwise run the command with the issue id.
2. Notifications: read the `Notify on resolve` key. `yes` means the resolve command already notifies the reporter;
   say so in the report. `no`, or a missing value, means nothing is sent; say that in the report, and let the user
   decide who tells the reporter. Never send a notice from this skill.
3. Move the plan file: `plans/triage/active/issue-<N>-*.md` →
   `plans/triage/implemented/IMPLEMENTED-issue-<N>-*.md`.
4. Report: "Issue #<N> marked resolved. Plan moved to `implemented/`." plus the commands for the
   user to run — `git add -A && git commit -m "fix(<area>): <summary> (issue #<N>)"`, then
   `git checkout main && git merge --no-ff fix/<N>-<slug>`. Only the user commits and merges.

## Notes

- This skill is the pipeline-specific wrapper around `sdlc-ralph-implement`, not a reimplementation of
  it — it owns issue lookup, the optional smoke check, the human resolution gate, and the
  tracker/`implemented/` bookkeeping, exactly the parts of this flow that are unique to
  triage-sourced bugfixes. `sdlc-ralph-implement` itself never touches a tracker, never notifies anyone,
  and never moves plan files.
- Do not push to git.
- For any destructive write beyond marking the single issue resolved, ask the user to confirm
  first.
- Triage plan files live in `plans/triage/active/`. Resolved files go to
  `plans/triage/implemented/` with the `IMPLEMENTED-` prefix. On-hold files live in
  `plans/triage/hold/` (the tracker-driven hold state from `sdlc-triage`, separate from a plan's own
  `status: blocked` frontmatter field, which means the implementation loop hit its retry budget —
  check both meanings if a plan seems stuck).
