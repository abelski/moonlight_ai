---
name: sdlc-triage
description: Fetch unresolved user-reported issues from this project's issue tracker, filter out spam/test noise by checking each against real data, and draft a bugfix plan per confirmed issue into plans/triage/active/ — using the same frontmatter/checklist shape sdlc-ralph-implement already drives. Use when asked to triage a backlog of user-reported issues, process bug reports, or sync triage plan files with tracker state. Pairs with sdlc-fix-issue-from-triage, which executes one drafted plan.
---

Turn unresolved issues sitting in this project's tracker into verified, ready-to-implement bugfix
plans. This skill knows nothing about any *specific* tracker (no database schema, no API baked
in) — Step 1 is where the project's actual tracker gets plugged in.

## Step 1 — Determine the issue source

Create `plans/triage/active/`, `plans/triage/hold/`, and `plans/triage/implemented/` if they don't
already exist.

- If `$ARGUMENTS` names a source, query, or filter, use it as given.
- Otherwise check this project's `CLAUDE.md`/docs for a documented tracker and query. If none is
  documented, ask the user once (`AskUserQuestion` or a direct question): where do unresolved,
  user-reported issues live for this project — a database table, a GitHub/Linear/Jira query, a
  spreadsheet, a support inbox — and how should they be fetched (a query, an API call, a file to
  read)? Use their answer for this run; it isn't this skill's job to persist it.

## Step 2 — Fetch unresolved issues

Run whatever Step 1 resolved to. Print a summary: id, short description, reported date, current
status, for each issue found.

## Step 3 — Validate each issue against real data

Before planning a fix, verify each issue reflects a real, reproducible problem — not a test
submission or a fabricated report. Red flags:

- The description reads like placeholder/test text ("test", "asdf", "just checking this works").
- The data/feature/page the report references doesn't actually exist in the project.
- Near-duplicate or contradictory reports filed within a short window of each other.

To verify, inspect whatever the report actually references — grep the codebase, query the
relevant data, hit the relevant page/endpoint. If a report can't be confirmed against reality, mark
it resolved-as-invalid through the tracker (the mechanism from Step 1) and skip planning it — don't
create a plan file for it.

## Step 4 — Plan fixes in parallel

For every confirmed issue that doesn't already have a plan file (see Step 5's naming), spawn one
`Plan` agent per issue via the `Agent` tool (`subagent_type: "Plan"`), all in a single message so
they run concurrently. Each agent prompt must include:

- The issue's id, description, and any other reported details.
- Instruction to explore the codebase and identify: the affected area, likely root cause, specific
  files touched, and concrete fix steps.
- Instruction to judge a `suggested_model` (`sonnet | opus | haiku | fable`) and `suggested_effort`
  (`low | medium | high | xhigh | max`) for *implementing* the fix — a mechanical, single-file fix
  suggests a cheaper/faster tier; something spanning multiple files, an ambiguous root cause, or an
  auth/data-integrity risk suggests a stronger tier — plus a one-line reason.

Wait for all agents to return before proceeding to Step 5.

## Step 5 — Save individual plan files

Derive a short slug (3-5 words, lowercase, hyphen-separated) from each issue's description.
Filename: `plans/triage/active/issue-<id>-<slug>.md`. If a file matching `issue-<id>-*.md` already
exists in `active/` or `hold/`, skip that issue entirely.

```markdown
---
kind: bugfix
status: draft
iteration: 0
max_iterations: <N>
suggested_model: <sonnet | opus | haiku | fable>
suggested_effort: <low | medium | high | xhigh | max>
confirmed_model: null
confirmed_effort: null
---

# Issue #<id> — <short context>

**Reported:** <date>
**Status:** <tracker status>
**Description:** <description>

## Root cause
... (include the one-line suggested_model/suggested_effort reason here)

## Fix plan
- [ ] 1. `path/to/file.ext` — what changes and why
- [ ] 2. ...

## Tests
- [ ] <this project's real test command that covers the fix>
- [ ] <a test, new or existing, that reproduces the reported issue>

## Definition of Done

​```bash
<lint/typecheck command>
<test command>
​```
```

`max_iterations` = `clamp((Fix plan items + Tests items) * 2, 8, 30)`. Always write `status: draft`
here — `sdlc-fix-issue-from-triage` flips it to `approved` once a human starts working the issue; this
skill only ever produces drafts. A plan may also carry an optional `## UAT verification` section,
same convention as `sdlc-feature-analyst`, if the fix has user-observable behavior worth black-box
testing.

After saving, print the list of created file paths.

## Step 6 — Clean up stale plan files

- Any file with an `IMPLEMENTED-` prefix sitting in `active/` or `hold/` → move it to
  `implemented/`.
- A plan file whose tracker status changed → move it: on-hold → `hold/`, reopened → back to
  `active/`, resolved → add the `IMPLEMENTED-` prefix and move to `implemented/`.
- A plan file whose tracker row no longer exists → delete it.
- For plan files describing a code change, check whether that change is already present in the
  codebase (grep for the relevant function/pattern). If a fix looks implemented but the tracker
  still shows it open, note this to the user — it may need to be formally resolved.

## Notes

- This is a bulk-intake sibling to `sdlc-feature-analyst`, not a replacement for it — both produce the
  same plan frontmatter/checklist shape, which is what lets `sdlc-ralph-implement` drive either without
  caring which one wrote the file.
- Never hardcode a tracker's schema, connection string, or API shape into this file — that's
  exactly the part every project supplies for itself in Step 1.
- Do not push to git.
- Destructive tracker writes (marking something resolved, deleting a row) in Step 3 are limited to
  the validated-spam case; anything else stays a draft plan for a human to act on.
