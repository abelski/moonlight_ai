---
kind: feature
status: done
iteration: 4
max_iterations: 30
suggested_model: opus
suggested_effort: high
confirmed_model: opus
confirmed_effort: high
started_at: 2026-10-30T20:07:19Z
---

# Plan #7 — Spend report, session state and live panel

## Context

Idea: `plans/ideas/idea_7_spendreport-panel.md`.

Today `scripts/token-report.py` prints token totals to chat in three flows: `skills/moonlight-fast/SKILL.md` Phase 7,
`skills/moonlight-calm/SKILL.md` Phase 6, `skills/sdlc-feature-analyst/SKILL.md` Phase 5 step 6. The bug flow
(`skills/sdlc-fix-issue-from-triage/SKILL.md`) has no report, and its plans (`sdlc-triage`) have no `started_at` key.
`session_files` (`scripts/token-report.py:26`) reads only the newest session unless `--all-sessions`. Nothing records the
phase of a running flow, and nothing shows a live view.

Facts found while exploring:

- `~/.claude/projects/<encoded>/<session-id>.jsonl` is one session. Its subagents sit in
  `<session-id>/subagents/agent-<id>.jsonl` with an `agent-<id>.meta.json` holding `agentType`, `description`, `finished`.
  So per-subagent names and tokens come from files, not from the engine API (this settles the idea's open question).
- `token-report.py` hard-codes `~/.claude/projects` (line 23) and its file name has a hyphen, so tests run it as a
  subprocess with `HOME` pointed at a temp dir.
- The current session is the newest main transcript in the project folder (the rule `token-report.py` already uses).
- A mod is a plugin with `hooks/hooks.json` naming `modules`, exporting `register(on, options)`. It opens a pane with
  `$.ui.open`, draws it in a `ui.render` hook on `Pane`, and can use `$.fs`, `$.process`, `$.clock` and `$.plugin.root`.
  Whether one plugin can hold both command hooks and a `modules` entry is unknown: item 1 settles it.
- Plan files live in `plans/improvements/active/` (feature) and `plans/triage/active/` (bug), per `CLAUDE.md` and the
  entry-point skills. `sdlc-feature-analyst` still says `plans/plan_<slug>.md` in many places; item 8 fixes them, or the
  panel cannot find its plans.
- `specs/` is empty and the repo has no source-root components, so no `specs/<component>.md` is written. The spec gate
  checks the idea's `## Proposed spec` against the shipped skill text, scripts and README.
- Every flow creates its plan file late (fast Phase 3, calm Phase 2, feature-analyst Phase 2). So the panel opens when the
  plan file exists, not at the very first step. `init` marks the earlier phases `done`. This differs from the idea's
  "opens when a flow starts"; the spec gate corrects the idea at close-out.

`suggested_model: opus`, `suggested_effort: high`: the panel uses an early-access mod API that moves between releases
and needs real design; the scripts and skill edits are mechanical.

## Goals

- Every closed plan carries `## spendreport`, counted over the sessions of that task.
- An in-progress plan carries a `## Session state` block. A clean session resumes from it.
- A side panel shows phases, time, who waits, tokens per subagent and a running total.
- The bug flow gets all of the above.

## Non-Goals

- Cost in dollars. Panels for desktop, VS Code, mobile. Tokens outside moonlight tasks.
- Token numbers per phase stored in the plan. Printing token totals to chat at the end.
- A version bump of the plugin and any commit or merge (the owner does these).
- Touching `skills/sdlc-ralph-implement/SKILL.md` (pipeline-agnostic; its stale `plans/*.md` path in Step 0 is a known gap).
- A reminder to re-check the mod API (the owner declined dated reminders for this idea).

## Decisions

- [user:high] What does the panel show? → phases with done/running/waiting, elapsed time, tokens per subagent, running total split input/cache/output, a `you` mark. No dollars.
- [user:high] What stays at the end? → a `## spendreport` section in the plan file; no chat print.
- [user:high] Which flows? → the three that have the report today, plus the bug flow.
- [user:high] Count which sessions? → the session ids in the state block, from `started_at`.
- [user:high] One idea or two? → one idea, one plan.
- [user:high] When does the panel appear? → by itself, plus a command to hide and bring it back.
- [user:high] Phase source? → the plan file's `## Session state` block.
- [user:high] State block contents? → phase, phase statuses, who waits, session ids with start times, branch, idea path. No token numbers.
- [user:high] Non-goals and success check → as in the idea file.
- [stand-in:medium] State block format → a fenced `json` block under `## Session state`, at the end of the plan. One writer and one reader, so JSON beats YAML.
- [stand-in:medium] Current session id → newest main transcript in the project folder; `phase` also takes `--session ID` as an override. Wrong only if two sessions run in one project at once. Item 1 checks whether the engine hands the id to a hook or the Bash env.
- [stand-in:medium] Per-subagent tokens → `by_agent` in `token-report.py --json`, labelled from `.meta.json`; the panel runs the script and does not recount.
- [stand-in:medium] The spendreport writer lives in `token-report.py` (`--plan PLAN`), not in a second script. `plan-state.py` has `init` and `phase` only.
- [stand-in:medium] Phase list is fixed at `init`, so a flow with no UAT section leaves `uat` out. No `--skip` flag, no `show` command: a skill reads the JSON fence itself to resume.
- [stand-in:medium] A `phase` call resets every later phase to `pending` (flows loop back on "Changes needed" or a UAT FAIL). A blocked implementation sets the running phase to `blocked`.
- [stand-in:medium] `sdlc-ralph-implement` stays untouched.
- [stand-in:medium] The plan is persisted to `plans/improvements/active/plan_7_spendreport-panel.md` right after approval, before any code (this file is in the harness plan folder only because plan mode allows no other write).
- [spike:high] Panel location → same plugin: `claude plugin validate` passes with `"modules": ["./panel.tsx"]` beside the command hooks in `hooks/hooks.json` (a list of one path; a string is refused). The module is `hooks/panel.tsx`, its test `test/panel.test.tsx`; `claude plugin test .`. No `marketplace.json` change. Details in `docs/panel-spike.md`.
- [spike:medium] Session id → the Bash tool has `CLAUDE_CODE_SESSION_ID` (the main session's id, also inside a subagent), so `phase` takes `--session`, else that variable, else the newest main transcript. Consent for a plugin-shipped mod is not answerable without triggering the prompt; the owner checks it at manual acceptance.
- [implementer:medium] Panel close rule → `sdlc-ralph-implement` sets `status: done` when implementation ends, before accept, docs, spendreport and close. So the panel hides a `done` plan only once its state's `phase` is the last phase; otherwise `you` at acceptance would never show. The move to `implemented/` closes it as before.

## Requirements

**Token report (`scripts/token-report.py`)**

- `--session` is repeatable (`action="append"`; `session_files` takes a list). If `--session` is given, `--all-sessions` is ignored, as now.
- `--json` gains `by_agent`: one entry per transcript with `session`, label (`main`, or the `.meta.json` `agentType` and `description`; a missing meta file gives the file stem), the four token fields and the billable total. The entries sum to the top-level totals. `totals()` keeps the owning file with each message id.
- `--plan PLAN`: reads the session ids and `started_at` from the plan, counts, and writes or replaces `## spendreport` (messages, input, cache writes, cache reads, output, billable total, one line saying the count covers everything in those sessions since `started_at`, at the moment of writing). It fails with a clear message, and writes nothing, if there is no state block, no sessions, or `started_at` is `null`.
- Existing flags and text output keep working.

**Plan state (`scripts/plan-state.py`, stdlib only)**

- `init PLAN --flow NAME --phases a,b,c [--done a,b] [--idea PATH]`: adds `## Session state` if missing. Never overwrites. Handles a plan with no frontmatter.
- `phase PLAN NAME [--waiting you] [--blocked] [--branch B] [--session ID]`: earlier phases become `done`, later ones `pending`, NAME becomes `running` (`waiting` with `--waiting you`, `blocked` with `--blocked`). Registers the current session id with its first-seen UTC time if absent.
- Statuses: `pending`, `running`, `waiting`, `blocked`, `done`. The block sits beside `## Blocked` and `## Review` sections that other skills rewrite; the script touches only its own section.

**Flows** (each calls the scripts as `python3 <plugin root>/scripts/…`, the plugin root being two levels above the skill's folder)

- `init` right after the plan file is written, then `phase` at the start of every phase, with `--waiting you` where the user is asked. Phase lists mirror each flow's headings:
  - fast: `research, idea, design, implement, accept, docs, spendreport, close`. Waiting: `idea` (grilling), `design` (plan review), `accept`.
  - calm: `research, design, implement, docs, accept, spendreport, close`. Waiting: `accept`, and any phase at an escalation (the list in the skill).
  - feature-analyst: `idea, design, implement, uat, docs, spendreport, close`. Waiting: `design` (approval), `accept` via the handoff.
  - bug: `locate, reproduce, fix, red-check, confirm, spendreport, close`. Waiting: `confirm`.
- Resume rule in each flow: if the plan already has a state block, read it and continue from the `running`, `waiting` or `blocked` phase; do not redo `done` ones.
- The check phase runs `token-report.py --plan <plan>` and tells the user one line: the report is in the plan. It runs before the plan moves to `implemented/`. In the bug flow it runs before the `Resolve in tracker` command, so a failure cannot leave the tracker resolved and the plan unmoved.
- The bug flow adds `started_at` to the plan frontmatter when it creates the branch (`date -u +%Y-%m-%dT%H:%M:%SZ`).
- Skill frontmatter descriptions that say "reports the token use" are reworded.

**Panel**

- Opens when a plan with a state block exists and its frontmatter `status` is not `done`; closes otherwise. Terminal only.
- Finds the plan by scanning `plans/improvements/active/` and `plans/triage/active/`; the newest file wins. A corrupt JSON fence shows nothing and does not crash.
- Phases and elapsed time redraw every few seconds from the plan. Tokens refresh about every 30 seconds, or when a transcript changes, by running `token-report.py --json` (located with `$.plugin.root`).
- Shows: flow and elapsed time since `started_at`; phases as done / running / waiting / blocked / pending; a `you` mark on a waiting phase; tokens per subagent and a running total (input, cache, output).
- A slash command hides and restores it.

### Standing constraints

From `CLAUDE.md`:
- "Smallest diff that achieves the goal. No drive-by refactors, no unrequested abstractions."
- "Ask before adding a new dependency, library, or external service." None added: Python stdlib only.
- "Write unit tests for new or modified logic." Tests live in `/test`.
- "Keep `README.md` current as part of "done"."
- "Never commit or push to git without explicit, in-session user consent."
- "Write repo files in English."
- Knowledge capture: a non-obvious environment fact goes into `docs/`, not only the plan.

## Implementation

The branch `feat/7-spendreport-panel` is created by the flow before the first edit below.

- [x] 1. Spike, in `/tmp` only: copy the plugin folder, add a `modules` entry and a stub module to its `hooks/hooks.json`, run `claude plugin validate`. Also check: how a plugin-shipped mod gets the owner's one-time consent; what the engine does in a narrow window; whether a session id reaches a hook or the Bash env; that `$.fs`, `$.process`, `$.clock`, `$.plugin.root` exist in the types. Record the answers in `docs/panel-spike.md` and under `## Decisions`. Same plugin if it validates, else the panel goes in its own folder (`mods/moonlight-panel/`) as a second plugin in `.claude-plugin/marketplace.json`. Items 10-12 use the winning path only.
- [x] 2. `test/test_token_report.py` — failing tests first: repeated `--session`, `--since` filter, `by_agent` labels and missing meta, dedup by message id, `by_agent` sums equal the totals, `--plan` writes then replaces the section, `--plan` error cases. Fixtures are built in a temp dir, `HOME` set to it, the script run as a subprocess.
- [x] 3. `scripts/token-report.py` — repeatable `--session`, `by_agent`, `--plan`; make the tests pass.
- [x] 4. `test/test_plan_state.py` — failing tests first: `init` idempotent and with no frontmatter, `phase` ordering and reset of later phases, `--waiting you`, `--blocked`, session registration (twice is one entry), neighbouring `## Blocked` and `## Review` sections untouched.
- [x] 5. `scripts/plan-state.py` — `init` and `phase`; make the tests pass.
- [x] 6. `skills/moonlight-fast/SKILL.md` — state calls, resume rule, Phase 7 writes the spendreport instead of printing, description reworded.
- [x] 7. `skills/moonlight-calm/SKILL.md` — same, with its phases and escalation points.
- [x] 8. `skills/sdlc-feature-analyst/SKILL.md` — state calls in Phases 2–5; every `plans/plan_<slug>.md` becomes `plans/improvements/active/plan_<N>_<slug>.md` (bugfix kind: `plans/triage/active/`); Phase 5 step 6 (spendreport) moves ahead of step 3 (the move to `implemented/`); description reworded.
- [x] 9. `skills/sdlc-fix-issue-from-triage/SKILL.md` — add `started_at` at the branch, state calls per step, spendreport before the `Resolve in tracker` command in Step 6.
- [x] 10. Panel module (path from item 1) — plan finder, state reader, drawing, timers, `$.process` call to `token-report.py`.
- [x] 11. Panel command to hide and restore, in the same module.
- [x] 12. Panel test (`*.test.tsx`, after the `plugin-authoring` `pane.test.tsx` example) — fixture plan renders phases, `you` mark and tokens; no plan, a `done` plan and a corrupt fence render nothing; two plans, the newest wins. Save the rendered text of the empty, populated, waiting-`you`, blocked and narrow states to `/tmp` for the owner to look at.
- [x] 13. `README.md` (the `Check` phase at line 57 and the phase list, Hooks/panel section, state block, spendreport, panel prerequisites next to Requirements at line 21) and `docs/codebase-research.md` (line 28 and the layout lines that name the new files).

## Validation

- [x] Unit tests: `python3 -m unittest discover -s test`
- [x] Plugin check: `claude plugin validate .` (and the panel plugin folder if it is separate)
- [x] Panel test: `claude plugin test <panel plugin folder>`
- [x] Smoke: build a frozen fixture session (a finished transcript in a temp `HOME`), run `plan-state.py init`, two `phase` calls and `token-report.py --plan`; the section appears and its numbers equal `token-report.py --session <id> --since <started_at> --json` on the same fixture.
- [x] Edge: a plan with two session ids sums both; `--plan` on a plan with `started_at: null` fails with a message and writes nothing.

## Manual acceptance (owner, not part of the loop)

Run a small task through `moonlight-fast`. The panel shows the phases and `you` at plan review and acceptance. Close the session mid-task, open a clean one, and the flow continues from the recorded phase. At the end the plan has `## spendreport`. This is the idea's success check.

## Definition of Done

```bash
python3 -m unittest discover -s test
claude plugin validate .
claude plugin test <panel plugin folder>   # path fixed by item 1
```

## Open risks

- The mod API is early access; a release can change it. The panel is isolated, so the scripts and the spendreport still ship if it breaks.
- The current-session rule can pick the wrong session if two sessions run in one project at the same time.
- Tokens counted since `started_at` in a listed session include any unrelated work done in that same session.

## Review

- [x] Code review passed (round 4)
- note: the `## Session state` fence regex and the frontmatter reader are written three times (twice in Python, once in TypeScript); a change to the writer could blank the panel silently.
- note: `hooks/panel.tsx` does not clear `tokens` when a different plan becomes the newest one; the old rows stay up to 30 s.
- note: the panel finds plan folders from the session's start directory; a session started in a subdirectory finds no plans.
- note: README and skills say the state block is "at the end of the plan"; after the first spend report it is followed by `## spendreport`. Nothing breaks, the readers match the heading.
- note: in the fast flow `you` cannot show during `idea` grilling, because no plan file exists yet. The plan's Context already says the panel opens late.
- note: round 4's last finding (skill count 21, really 22 in `docs/codebase-research.md:24`) was fixed by the orchestrator in place, without a further review round.

## Session state

```json
{
  "flow": "feature-analyst",
  "phase": "close",
  "waiting": null,
  "phases": {
    "idea": "done",
    "design": "done",
    "implement": "done",
    "docs": "done",
    "spendreport": "done",
    "close": "running"
  },
  "sessions": [
    {
      "id": "2e8db606-cd0e-4603-aef9-49e505c34c12",
      "started_at": "2026-10-30T20:42:13Z"
    }
  ],
  "branch": "feat/7-spendreport-panel",
  "idea": "plans/ideas/idea_7_spendreport-panel.md"
}
```

## spendreport

Counted at 2026-10-30T20:42:31Z over sessions 2e8db606-cd0e-4603-aef9-49e505c34c12: everything in those sessions since 2026-10-30T20:07:19Z, subagents included.

- messages: 209
- input tokens (new): 438
- cache writes: 602995
- cache reads: 24730620
- output tokens: 197968
- billable total (new + writes + output): 801401
