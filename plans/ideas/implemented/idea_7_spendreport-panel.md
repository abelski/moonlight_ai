---
number: 7
slug: spendreport-panel
status: confirmed
---

# Idea #7 — Spend report, session state and live panel

## Problem
The owner wants to know how many tokens a task cost, and to see the run while it goes. Today the token report
(`scripts/token-report.py`) is printed to chat once, at the end of three flows (`moonlight-calm`, `moonlight-fast`,
`sdlc-feature-analyst`). Four things are wrong:

- The numbers vanish with the chat. Nothing is kept with the task.
- The bug flow (`sdlc-fix-issue-from-triage`) has no report at all.
- The script reads only the newest session by default (`session_files`, `mains[-1:]`). A task resumed in a second
  session shows too low a total.
- Nothing shows, while a flow runs, which phase it is in, how long it took, or when it waits for the owner.

## Desired outcome
- Every closed plan carries a `## spendreport` section with the token totals of that task.
- A plan that is in progress carries a session-state block. A clean session reads it and continues from the same phase.
- A side panel, open by default during a moonlight flow, shows the phases, the time, who waits, and the tokens.

## Proposed spec
Components named here are proposals. No `specs/<component>.md` exists yet.

**Session state (plan file)**
- New: Given a plan with status `in_progress`, the plan file holds a state block with: the current phase, the status
  of each phase (done, running, waiting), who waits (`you` or none), the session ids of the task with the start time of
  each, the branch name, and the path of the idea file.
- New: When a flow moves to another phase, it updates the block before it starts the phase.
- New: Given a clean session and a plan with a state block, when the owner resumes the plan, the flow continues from
  the recorded phase and does not redo finished phases.

**Spend report**
- New: When a flow closes a plan, the plan gets a `## spendreport` section before it moves to `implemented/`. It holds
  messages counted, input, cache writes, cache reads, output and the billable total, counted from the plan's
  `started_at` over the session ids in the state block, subagent transcripts included.
- Changed: The close phase no longer prints the token totals to chat.
- New: When the bug flow closes a plan, it writes `## spendreport` the same way.
- New: Given a task run over two sessions, the spendreport counts both.

**Panel**
- New: When a moonlight flow has written its plan file with a state block, a side panel opens by itself. Every flow
  writes that file after research and idea, so those phases show as done from the start. (Corrected at close-out: the
  idea first said the panel opens when the flow starts.)
- New: The panel shows the flow's phases, each as done, running, waiting or blocked, the elapsed time, and a `you`
  mark on the phase that waits for the owner: plan review and acceptance in `moonlight-fast`, acceptance and
  escalations in `moonlight-calm`, plan approval in `sdlc-feature-analyst`, the resolution question in the bug flow.
  No `you` shows during the idea grilling of `moonlight-fast` (no plan file exists yet), and `sdlc-feature-analyst`
  has no acceptance mark (its handoff comes after the plan moves). (Corrected at close-out.)
- New: A plan whose frontmatter says `done` stays in the panel until its state reaches the last phase, because
  `sdlc-ralph-implement` sets `done` before acceptance, docs, spendreport and close.
- New: The panel shows the tokens of each subagent and a running total split into input, cache and output.
- New: A command hides the panel and brings it back.
- New: When the terminal is too narrow, the panel waits and shows when there is room.
- New: When no moonlight flow runs, the panel is closed.

## Scope
- In: `## spendreport` in the plan file, for the feature flows and the bug flow. Session-state block in the plan file.
  Counting over the session ids of the task. The side panel, terminal only. Moving the end-of-run token output from chat
  into the plan file. A script change so the report can take a list of sessions.
- Out (non-goals):
  - Cost in dollars. The model price is not known for sure, so the number could be wrong.
  - Panels for desktop, VS Code and mobile. Terminal only.
  - Counting tokens outside moonlight tasks.
  - Storing token numbers per phase in the plan file. The transcripts already hold them, and a copy can drift.
  - Printing the token report to chat at the end.

## Decisions
- **Q** What is wrong with the report today? — The owner wants a live view like a side panel, and a kept record of the cost.
- **Q** What does the panel show? — Phases with done, running, waiting; elapsed time; tokens per subagent; a running
  total with input, cache and output; a `you` mark where the owner is needed. No dollars.
- **Q** What stays at the end of the task? — Option 3, and the name is `spendreport`: a section in the plan file.
- **Q** Where does it live, and what about chat? — A `## spendreport` section inside the plan file. No chat print.
- **Q** Which flows? — The three that have the report today, plus the bug flow. Every flow that closes a plan writes it.
- **Q** Count all sessions of a task? — Yes. Superseded by the session-state block: count the session ids listed there.
- **Q** One idea or two? — One idea, one plan.
- **Q** When does the panel appear? — By itself when a flow starts, plus a command to hide and bring it back.
- **Q** Where does the panel read the phase from? — From the plan file. The in-progress plan holds a session-state block
  so a clean session can resume.
- **Q** What does the state block hold? — Phase, phase statuses, who waits, session ids with start times, branch, idea
  path. Not token numbers.
- **Q** Non-goals and success check — Confirmed as written below.

## Precedents
No past plans exist (`plans/` is new, no changelog). Code precedents:
- `scripts/token-report.py` — sums tokens from session and subagent transcripts. Reuse the counting. Its `--session`
  takes one id and its default reads the newest session only.
- `skills/moonlight-calm/SKILL.md` Phase 6, `skills/moonlight-fast/SKILL.md` Phase 7,
  `skills/sdlc-feature-analyst/SKILL.md` close-out step 6 — where the report runs today.
- `skills/sdlc-ralph-implement/SKILL.md` — already resumes from plan frontmatter and checkboxes. The state block extends
  that.

## Success check
Run one small task through `moonlight-fast`.
1. The panel shows the phases and puts `you` on plan approval and on acceptance.
2. Close the session in the middle of the task, open a clean one, and the flow continues from the recorded phase.
3. At the end the plan file has a `## spendreport`, and its total equals `scripts/token-report.py` over the same
   sessions.

## Open questions
- Can the panel mod live inside the `moonlight` plugin, which has command hooks in `hooks/hooks.json`, or does it need
  its own plugin in the same repository? Not checked.
- What per-agent token data does the engine give a mod? The `22k ctx` in the owner's reference picture is the context
  size, not the billed tokens. If the engine gives only context size, the per-subagent figure needs another source.
- A mod written in a session needs the owner's one-time consent to load. How a plugin-shipped mod is switched on is
  not checked.
- `token-report.py --session` takes one id. It must take a list, or the plan must call it once per session.
- The bug flow has its own phases. The panel needs each flow to declare its phase list.
