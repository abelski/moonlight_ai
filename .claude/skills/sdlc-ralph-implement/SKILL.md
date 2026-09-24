---
name: sdlc-ralph-implement
description: Execute a checklist plan file (feature or bugfix) to completion via a bounded, resumable, self-correcting loop — delegates each pass to a sdlc-ralph-implementer subagent, flips checkboxes live, retries failed validation commands up to max_iterations (persisted in the plan's own frontmatter so retries survive a session restart), marks the plan blocked rather than falsely done if the budget runs out. Pipeline-agnostic — knows nothing about any caller-specific epilogue (publishing, notifying, moving files); callers own that.
---

Execute a plan file's checklist(s) to completion. This skill is deliberately pipeline-agnostic —
it works identically no matter which skill produced the plan (`sdlc-feature-analyst` or anything else
that writes the same checklist shape), and it never publishes anything or notifies anyone itself.
It reports `done` or `blocked` back to whoever invoked it; the caller decides what happens next.

It can also be invoked standalone — `/sdlc-ralph-implement <path-to-plan-file>` — to resume any
`in_progress` or `blocked` plan from a cold session. All progress lives in the plan file itself,
not in conversation memory, so a fresh invocation with zero prior context can pick up exactly
where a previous one left off.

## Step 0 — Resolve the target plan file

- If `$ARGUMENTS` is a path, use it.
- If empty: list `plans/*.md` (excluding `plans/implemented/`). If exactly one file exists, use
  it. If more than one, `AskUserQuestion` which one. If none, report there's nothing to implement
  and stop.

## Step 1 — Parse frontmatter, guard on status

Read the file. Extract the YAML frontmatter (`kind`, `status`, `iteration`, `max_iterations`,
`suggested_model`, `suggested_effort`, `confirmed_model`, `confirmed_effort`).

- **No frontmatter at all** (a legacy/hand-authored plan): this is still supported. Synthesize it
  now and write it in: count existing checklist items to compute
  `max_iterations = clamp(total_items * 2, 8, 30)`, set `iteration: 0`,
  `suggested_model`/`suggested_effort` unset (`null` — skip the reconciliation question in Step 2
  entirely when there's nothing to suggest), and treat `status` as `approved` (a plan file that
  exists under `plans/` without frontmatter was clearly already approved by whatever process
  created it).
- **`status: draft`** — stop. Tell the user this plan hasn't been approved yet; send them back to
  whichever skill authored it.
- **`status: done`** — report it's already done, stop. Idempotent no-op.
- **`approved`, `in_progress`, or `blocked`** — proceed to Step 2.

## Step 2 — Model/effort reconciliation (once per plan, only)

Only runs the first time a plan transitions `approved → in_progress` (i.e. skip this entirely on
every resume — `confirmed_model`/`confirmed_effort` being already set is exactly the signal that
this already happened, don't re-ask).

- If `suggested_model`/`suggested_effort` are `null` (legacy plan, nothing suggested): set
  `confirmed_model` to whatever model this session is currently running as, `confirmed_effort` to
  `medium`, persist, move on — no question needed, there's nothing to reconcile against.
- Otherwise compare:
  - `suggested_model` vs. the model this current session is actually running as.
  - `suggested_effort` vs. any effort level the user explicitly specified when invoking this
    skill or the plan's originating command (if none was specified, there's nothing to compare —
    treat effort as matching).
  - **If both match**: set `confirmed_model`/`confirmed_effort` to the suggested values, persist,
    proceed silently. Do not ask anything.
  - **If either differs**: ask once, via `AskUserQuestion`:
    - Question: `"This plan suggests {suggested_model}/{suggested_effort} for implementation
      ({one-line reason from the plan's Context section}). Use suggested, keep current session
      settings, or choose different ones?"`
    - Options: `"Use suggested"`, `"Use current session settings"`, `"Choose other"` (if chosen,
      follow up with which model and which effort).
  - Persist the resolved values into `confirmed_model`/`confirmed_effort` immediately. This is
    permanent for the life of this plan — every later retry and resume reads these fields and
    never asks again.

## Step 3 — Enter/resume

- `status: approved` → flip to `in_progress`, bump `iteration` from 0 to 1, persist. This marks
  "an attempt is underway," it is not itself a retry.
- `status: in_progress` or `blocked` already → this is a resume. Do not bump `iteration` here;
  bumps only happen per validation-retry attempt (Step 5).

## Step 4 — Implementation / Fix-plan fast pass

Only runs if the plan's `## Implementation` (feature) or `## Fix plan` (bugfix) section has any
remaining `- [ ]` boxes.

Spawn **one** `sdlc-ralph-implementer` subagent (`Agent(subagent_type: "sdlc-ralph-implementer", model:
confirmed_model)`) covering the *entire* remaining section in a single pass — not one subagent
per checklist item. Tell it: the plan file path, that this is an "implementation pass," and the
`confirmed_effort` level. It writes through checkbox updates to the plan file directly as it
completes each item; you don't need to re-apply anything from its report.

When it returns, re-read the plan file's checkbox state (don't trust the subagent's prose summary
as ground truth — the file is ground truth). If items remain unchecked and the subagent reported
a genuine blocker (not just "ran out of budget"), treat this the same as a validation failure
would be treated in Step 5: surface it to the user directly rather than silently retrying
indefinitely.

Once every Implementation/Fix-plan box is checked, fall straight into Step 4.5 in the same turn —
no need to wait for a new invocation.

## Step 4.5 — Code review gate

Skip if the plan already has a `## Review` section containing `- [x] Code review passed` (a
resume after the gate already passed).

Loop, starting at round 1:

1. Spawn `sdlc-ralph-reviewer` (`Agent(subagent_type: "sdlc-ralph-reviewer")`). Tell it: the plan
   file path, `confirmed_effort`, and whether this is the first round or a re-review — on a
   re-review, also the previous round's findings verbatim plus, for each one the implementer
   disputed, its stated reason. Relay **nothing else** from the implementer — not its report, its
   reasoning, or any claim that the work is done; the reviewer's independence is the point.
2. **No `blocker` and no `should-fix`** → write/replace the plan's `## Review` section with
   `- [x] Code review passed (round <N>)` followed by any `note` findings as plain bullets
   (recorded, not acted on). Go to Step 5.
3. Otherwise bump `iteration` and persist it (same budget as Step 5, same write-before-retry
   rule). At `iteration >= max_iterations` → Step 7, with the open findings as the blocking item.
   Else spawn `sdlc-ralph-implementer` for a **"review-fix pass"**, giving it the plan path,
   `confirmed_effort`, and the `blocker`/`should-fix` findings verbatim. Then loop to the next
   round as a re-review.

A `should-fix` the implementer disputes and the reviewer then drops no longer counts; one the
reviewer upholds keeps the loop going. There is no "good enough" exit short of the budget.

**Review ⇄ validation cycle.** Steps 4.5, 5 and 6 form one loop that ends only when a single round
has a clean review *and* every validation/DoD command passes with no code changed in that round —
or when `max_iterations` runs out (Step 7). If any Step 5/6 retry changed code, the reviewed diff
is stale: replace `- [x] Code review passed` with `- [ ] Code review (re-review after validation
fixes)`, return here for a re-review (tell the reviewer which findings/fixes came from
validation), and after it passes re-run **every** `## Validation`/`## Tests` command and the
`## Definition of Done` commands, not just the unchecked ones.

## Step 5 — Validation / Tests pass with bounded self-correction

For each unchecked item under `## Validation` (feature) or `## Tests` (bugfix), in order:

- **If it names a literal command**: spawn a `sdlc-ralph-implementer` subagent for a "validation
  retry" pass, telling it the plan file path, the exact command, and `confirmed_effort`.
  - It reports pass → the box is already checked (the subagent writes through) → continue to the
    next item.
  - It reports fail → before it retries again, **you** bump `iteration` in the plan frontmatter
    and persist it immediately (this write must land before the retry, so a crash mid-retry
    resumes with the correct count) → check `iteration >= max_iterations`:
    - If not yet at the cap: spawn another `sdlc-ralph-implementer` "validation retry" pass for the
      *same* command (it already has the failure context from its own last attempt if this is
      the same subagent conversation; if this is a fresh subagent call, give it the previous
      failure output so it isn't starting blind). Repeat until pass or cap reached.
    - If at the cap: go to Step 7 (Blocked). Do not mark the box done. Do not continue to later
      items. Do not fabricate success.
- **If it's a manual/human-only item** (no literal runnable command — e.g. "manual smoke test by
  user"): leave it unchecked. Do not silently check it, and do not block completion on it either
  — note it in the final report as "left for user to verify."

## Step 6 — Completion gate

Once every mechanical box across both sections is checked (manual items aside):

- Re-run **every command listed in `## Definition of Done`** together, right now, even if some
  were already exercised individually earlier — this is the final no-drift check, catching
  anything that regressed between when an individual box was checked and now.
- All must exit 0 / pass. If one fails here, treat it exactly like a Step 5 validation failure:
  diagnose, fix, retry, bounded by the same `max_iterations`, escalate to Step 7 if exhausted.
- If any retry in Step 5 or here changed code, do **not** complete: go back to Step 4.5 (see
  "Review ⇄ validation cycle"). Complete only from a round where nothing needed fixing.
- If the plan has no `## Definition of Done` section at all (legacy plan): skip this extra gate,
  note in your report that it was missing, and treat "all mechanical boxes checked" as sufficient
  for completion.
- On success: set `status: done`, persist. **Stop here.** Report completion back to whoever
  invoked this skill (or directly to the user, if invoked standalone), including: what was
  implemented, what validation passed, and any manual/human-only items still left for the user.
  Do **not** move the file, do **not** publish or notify anyone, do **not** attempt any epilogue
  — those are pipeline-specific and owned entirely by the caller.

## Step 7 — Blocked

`iteration >= max_iterations` reached with mechanical items still unchecked, open review
findings, or a review ⇄ validation round that still changed code:

- Set `status: blocked`, persist.
- Replace any existing `## Blocked` section (don't let it grow across repeated block/resume
  cycles — keep only the most recent) with:

  ```markdown
  ## Blocked (iteration <N>/<max_iterations>, <ISO timestamp>)

  **Done:**
  - [x] <currently-checked items, copied>

  **Remaining:**
  - [ ] <currently-unchecked items, copied>

  **Blocking command:** `<exact failing command>` (or, from Step 4.5, the open review blockers)

  Last failure output:
  ```
  <captured tail of stderr/stdout>
  ```

  **What was tried:** <1-3 sentence summary of the diagnose-fix-retry attempts and why none
  resolved it>

  **Suggested next step:** <short actionable note for a human>
  ```
- Report this to the user, stop. Do not proceed to Step 6. Do not run any epilogue. Never claim
  success when blocked.

## Using `/loop` + `ScheduleWakeup`

Default is inline — proceed through Steps 3-7 in the current turn without touching `/loop` at
all. Reach for it only in two specific cases:

- **Resuming across a session boundary**: at Step 1, the plan's `status` was already
  `in_progress` or `blocked` *before this invocation started* (the practical signal that an
  earlier attempt didn't finish in one sitting), and meaningful validation-retry work likely
  remains.
- **A large fresh plan**: at Step 3, the total checklist item count exceeds roughly 12, or your
  own judgment says this plan is unlikely to finish in one turn.

When used: invoke the `loop` skill with no interval (dynamic self-pacing). Each `ScheduleWakeup`
call passes the *identical* `/sdlc-ralph-implement <path>` prompt forward, sets `noop: false` with a
`reason` describing the concrete work just done (each firing here does real work, never idle
polling), and picks `delaySeconds` near the 60-second floor rather than the 20-30 minute idle
default. Call `stop: true` the instant Step 6 or Step 7 is reached.

## Notes

- Never commit or push to git — this skill (and the subagents it spawns) never does, regardless
  of what a plan implies. Progress is tracked entirely via the plan file's own checkboxes and
  frontmatter, not git history.
- `sdlc-ralph-implementer` subagents never have `Agent` tool access — they cannot recursively spawn
  further loops. All iteration/retry control lives here, in this orchestrator.
- This skill has zero knowledge of caller-specific epilogues (publishing, notifications, moving
  files). If you find yourself about to do one of those, stop — that belongs in the calling
  skill, not here.
- The Step 4.5 reviewer (`sdlc-ralph-reviewer`) applies the Standards/Spec axes of the
  `sdlc-standards-spec-review` skill inline — it can't run that skill itself, since subagents have
  no `Agent` tool. For a two-sub-agent review from a fresh session, run
  `/sdlc-standards-spec-review` by hand.
