---
kind: feature
status: done
iteration: 2
max_iterations: 28
suggested_model: sonnet
suggested_effort: high
confirmed_model: sonnet
confirmed_effort: high
started_at: 2026-10-30T20:59:33Z
---

# Plan #8 — Check that the README describes correctly how to use the plugin

## Context

Idea: `plans/ideas/idea_8_readme-usage-check.md`.

`README.md` (265 lines) is the only user guide. Plan #7 added the panel, state-block and spend-report text, and the owner
added "Adapt it to your project" (lines 139-157). Both are now committed on `main` (HEAD `5ac3493`). The whole file was
never checked against the skills, hooks, scripts and agents it describes. This plan is a document check: read each README
claim, find the file and line that proves or disproves it, record a verdict, and fix `README.md` with the smallest edit
where the claim is wrong.

The branch starts from `main`. The only uncommitted file is the idea file, which rides into the branch. So
`git diff main -- README.md` is exactly this plan's edits, and the idea's success check 4 can be checked by that diff.

Suspects found while reading the README against the repo (each must still be checked, not assumed):

- `README.md:127` says the triage skills need "two things", but the table below it (lines 130-134) lists three keys.
- `README.md:52` says "Every flow runs these phases". The bug flow has its own steps (line 63). The feature flows number
  their phases differently: `moonlight-fast` has phases 0-8, `moonlight-calm` 0-7, `sdlc-feature-analyst` 1-5. README
  phase "4. Code review" is not a phase in any of them; it sits inside `sdlc-ralph-implement` (Step 4.5).
- `README.md:147`, the Values row: "The planner copies `## Commands` into each plan's Validation and Definition of Done."
  Only `skills/moonlight-init/SKILL.md:93` and `:125` mention `## Commands`. The planner reads `### Standing
  constraints` (`skills/sdlc-feature-analyst/SKILL.md:105-139`, `agents/sdlc-ralph-implementer.md:46`). So the Rules row is
  likely right and the second sentence of the Values row is likely wrong. Confirm both.
- `README.md:114` (`claude -p` needs `--add-dir`) appears only in the README, not in any skill.
- `moonlight-calm` and `moonlight-fast` are in the Entry points table but not in the Skills tables (lines 159-194). The
  Skills headers ("Feature pipeline", "Conversation and setup") never claim completeness; decide from the text.
- `README.md:68` says the state block is at the end of the plan; after the first spend report it is followed by
  `## spendreport` (a note from the #7 review).
- `README.md:241-242` says the plugin does not load the starter `CLAUDE.md` into its own sessions, but `CLAUDE.md` is
  loaded as project instructions when working in this repo. Check what the sentence means.
- `README.md:21` and `:214` describe the reminders hook as showing lines from `plans/reminders.md`. `hooks/reminders.py:9`
  builds its path with `parents[2]` from `hooks/reminders.py`, which is above the plugin root. The README describes the
  intended behaviour and the code looks wrong: this is a code issue for the list, and the README line is not changed.

`suggested_model: sonnet`, `suggested_effort: high`: reading and judging claims, no design, but a wrong `right` verdict is
the main risk, so effort is high.

## Goals

- A `## Claim check` section in this plan: one row per checked README claim (a command, a name, a step, a number, a link, a
  rule — not one row per sentence) with README line, claim, evidence (`file:line`) and verdict (`right`, `wrong`,
  `not verified`).
- Every `wrong` claim fixed in `README.md` with the smallest edit, or listed under `## Code issues for the owner` when the
  code is what looks wrong.
- A `## README edits` section: each edit as README line, before, after, and the claim row that justifies it.

## Non-Goals

- Changing code, skills, hooks, scripts, agents or any file other than `README.md`, this plan, and the `README.md:NNN`
  cites in `docs/codebase-research.md` (see Decisions).
- Running any command to verify a claim.
- New README sections, restructuring, rewording of text that is right.
- A spec file (document change, no new behaviour; `specs/` has no component to update).
- Rewriting the owner's "Adapt it to your project" section beyond fixing claims that are wrong.

## Decisions

- [user:high] What comes out? → report and fix: check every claim, fix `README.md` minimally, list what was checked and fixed.
- [user:high] How to check? → read only; no command is run to verify a claim; install/update from GitHub are `not verified`.
- [user:high] Which parts? → the whole file, including "Adapt it to your project".
- [user:high] README and code disagree? → README is changed; a suspected code bug is only listed, and the README line stays.
- [user:high] Non-goals and success check → as in the idea file.
- [user:high] Where does the claim list live? → in this plan file, as `## Claim check`.
- [user:high] Branch base → "carry along" was chosen while #7 was uncommitted. #7 is now merged, so nothing is left to carry: the branch starts from `main` and the idea file rides in.
- [analyst:medium] Verdict scale → `right`, `wrong`, `not verified`. A claim true only by Claude Code's own behaviour, with no repo file to check it, is `not verified`. A claim whose code is what looks wrong gets `wrong` and a row in `## Code issues for the owner`; the README is not edited for it.
- [analyst:medium] `docs/codebase-research.md` carries about ten `README.md:NNN` cites (lines 9, 11, 15, 18, 31, 37, 49, 53, 57, 63 at the time of writing). README edits can shift them, and #7's review found stale cites a real cost. So the last item updates those cites in that file, and nothing else in it. This goes slightly past the idea's scope; the owner sees it in the approval.
- [analyst:medium] Definition of Done → one scope gate (`git diff --name-only`), which checks which files changed, not any claim. It does not run the plugin.

## Requirements

- Cover every README heading: the intro and all 22 `##` and `###` headings (15 `##`, 7 `###`).
- Check names exactly: each skill, agent, hook, command, file and flag the README names exists with that spelling.
- Check every relative link, and every `#anchor` (by grepping `^#` in the README).
- Check numbers and lists against their source: the `moonlight-calm` escalation list (README lines 85-93) against
  `skills/moonlight-calm/SKILL.md` lines 52-60; the hook command list against `hooks/block-git-commit-push.sh`; the panel
  facts (144 columns, 3 s and 30 s refresh, close rule) against `hooks/panel.tsx` (the `every(3000…)` and `every(30000…)`
  timers) and `docs/panel-spike.md`; the phase and state-block text against `scripts/plan-state.py`,
  `scripts/token-report.py` and the four flow skills; the init text against `skills/moonlight-init/SKILL.md`; the adapter
  keys against `CLAUDE.md` (`## Moonlight adapters`) and the triage skills.
- Seed these as `not verified`, never `right`: `claude plugin marketplace add`, `claude plugin install`, `claude plugin
  update`, `claude plugin validate .`, `claude plugin test .`, `claude --plugin-dir .`, headless `claude -p` with
  `--add-dir`, "Claude Code may ask you once to enable it" (README line 23), "restart Claude Code after an update", the
  output-style override of `/output-style`, namespacing and the `.claude/skills/` copy claim. For each, still check it
  does not contradict a repo file.
- Edit `README.md` only with the Edit tool, one small edit per wrong claim, and log each in `## README edits`.

### Standing constraints

From `CLAUDE.md`:
- "Smallest diff that achieves the goal. No drive-by refactors, no unrequested abstractions."
- "Every change gets its own branch (`feat/<N>-<slug>`, `fix/<N>-<slug>`), created before the first code edit."
- "Keep `README.md` current as part of "done"."
- "Never commit or push to git without explicit, in-session user consent."
- "Write repo files in English."
- Specs stay current: not applicable, no behaviour changes and `specs/` has no component.

## Implementation

The branch `feat/8-readme-usage-check` is created by the flow from `main` before the first edit below. The implementer reads
with Read, Grep and Glob and edits with Edit; it does not use Bash to verify a claim.

- [x] 1. This plan — add empty `## Claim check` (header `# | README line | Claim | Evidence | Verdict`), `## README edits` and `## Code issues for the owner`, to be filled by the items below.
- [x] 2. `README.md` lines 1-38 (intro, Quick start, Install and update, namespacing): sources `.claude-plugin/marketplace.json`, `plugin.json`, `skills/moonlight-update/SKILL.md`, `hooks/`, `scripts/`, `docs/panel-spike.md`.
- [x] 3. `README.md` lines 40-95 (Entry points, phases, session state and spend report, `moonlight-calm`): sources `skills/moonlight-fast`, `moonlight-calm`, `sdlc-brainstorm`, `sdlc-feature-analyst`, `sdlc-fix-issue-from-triage`, `scripts/plan-state.py`, `scripts/token-report.py`. Includes the suspects "Every flow runs these phases" and "at the end of the plan".
- [x] 4. `README.md` lines 97-137 (Start on an existing project, Start a new project, Adapters): sources `skills/moonlight-init/SKILL.md`, `CLAUDE.md`, `skills/sdlc-triage/SKILL.md`, `skills/sdlc-fix-issue-from-triage/SKILL.md`. Includes the suspects "two things" and `--add-dir`.
- [x] 5. `README.md` lines 139-157 (Adapt it to your project): sources `skills/sdlc-feature-analyst/SKILL.md`, `skills/moonlight-init/SKILL.md`, `agents/sdlc-ralph-implementer.md`, `hooks/block-git-commit-push.sh`. Verdicts to confirm: Rules row right; second sentence of the Values row wrong.
- [x] 6. `README.md` lines 159-207 (Skills and Agents tables): each row against `skills/*/SKILL.md` and `agents/*.md` (name exists, "Only you can run it" matches `disable-model-invocation: true`, the description is true). Decide the missing `moonlight-calm` and `moonlight-fast` rows from the section text and record the reasoning.
- [x] 7. `README.md` lines 209-265 (Hooks, Side panel, Output style, Starter CLAUDE.md, Develop the plugin, Not in the plugin yet, Docs): sources `hooks/`, `hooks/panel.tsx`, `docs/panel-spike.md`, `output-styles/talk-to-user.md`, `.claude/skills/`, the Docs link targets. The `reminders.py:9` suspect goes to `## Code issues for the owner`.
- [x] 8. Whole `README.md` — check every link and anchor; confirm every heading has a row; confirm each `## README edits` entry has a justifying row and that its edits are the only changes this plan made to `README.md`.
- [x] 9. `docs/codebase-research.md` — update only the `README.md:NNN` cites that the README edits shifted. Leave a note in `## README edits` if none shifted.

## Validation

- [x] Every row of `## Claim check` has a verdict and an evidence `file:line` (or "no file; Claude Code behaviour" for `not verified`), and no row says `right` for a claim on the seeded run-needed list.
- [x] Every `wrong` row has a matching entry in `## README edits` or in `## Code issues for the owner`.
- [x] Every entry in `## README edits` names the README line, the before and after text, and its claim row.
- [x] Every one of the 22 headings and the intro has at least one row in `## Claim check`.

These four name no shell command (the idea forbids running commands to check claims); the implementer ticks each by reading its own tables with Read and Grep. The reviewer checks the three suspects with the highest impact (`two things`, the `## Commands` claim, `Every flow runs these phases`) against their evidence.

## Definition of Done

```bash
test -z "$(git diff --name-only main | grep -v -e '^README.md$' -e '^docs/codebase-research.md$' -e '^plans/')"
```

This gate checks which files changed. It verifies no claim and does not run the plugin.

## Open risks

- A `right` verdict can be wrong if a skill was misread; the reviewer re-reads the three highest-risk rows.
- Claude Code behaviour (install, update, namespacing, `--add-dir`) stays `not verified`; the README keeps those lines unless a repo file contradicts them.
- The "no Bash" rule for the implementer is prose; the agent has Bash available. The scope gate catches stray file edits, not stray commands.

## Claim check

README line numbers in every table are those of `README.md` at `HEAD` (`5ac3493`), as read before any edit. The edits below
shift later lines: edit 4 adds one line at 86, so text after it is one line lower in the edited file (edits 1 to 3 keep the
line count).

| # | README line | Claim | Evidence | Verdict |
|---|---|---|---|---|
| 1 | 1-3 (intro) | Title `moonlight` and the logo `.claude-plugin/icon.png` | `.claude-plugin/icon.png` exists | right |
| 2 | 5-6 (intro) | A Claude Code plugin with the SDLC pipeline and a few safety hooks; install once, update in place | `.claude-plugin/plugin.json:4`, `hooks/hooks.json:3-24`, `skills/moonlight-update/SKILL.md:6-8` | right |
| 3 | 8 (intro) | Repo is `github.com/abelski/moonlight_ai` | `skills/moonlight-update/SKILL.md:3,19` | right |
| 4 | 9 (intro) | License MIT, link `[LICENSE](LICENSE)` | `.claude-plugin/plugin.json:5`; `LICENSE` exists | right |
| 5 | 13-16 (Quick start) | `claude plugin marketplace add abelski/moonlight_ai` and `claude plugin install moonlight@moonlight` | Names agree: marketplace `moonlight` (`.claude-plugin/marketplace.json:2`), plugin `moonlight` (`:8`), same commands in `skills/moonlight-update/SKILL.md:19`. The commands need a run: no file; Claude Code behaviour | not verified |
| 6 | 18-19 (Quick start) | `/moonlight:moonlight-init` exists; links `#start-a-new-project` and `#entry-points` | `skills/moonlight-init/SKILL.md:2`; README headings at lines 117 and 40 | right |
| 7 | 21 (Quick start) | `jq` is needed: the git-safety hook reads its input with it | `hooks/block-git-commit-push.sh:8` | right |
| 8 | 21-22 (Quick start) | `python3` is needed: reminders hook, session state, spend report | `hooks/hooks.json:8`, `scripts/plan-state.py:1`, `scripts/token-report.py:1` | right |
| 9 | 22-23 (Quick start) | The panel is a mod on early-access function hooks, checked on Claude Code 2.1.314 | `docs/panel-spike.md:3-4`, `hooks/hooks.json:26` | right |
| 10 | 23 (Quick start) | The panel draws in the terminal only | `hooks/panel.tsx:125` (`e.surface !== 'terminal'` returns) | right |
| 11 | 23 (Quick start) | "Claude Code may ask you once to enable it" | `docs/panel-spike.md:20,31` says this could not be answered from the sources; no file; Claude Code behaviour | not verified |
| 12 | 23-24 (Quick start) | Without the panel, every flow still works | `docs/panel-spike.md:31-32`; the flows call only the scripts (`skills/moonlight-fast/SKILL.md:16-23`), the panel only reads (`hooks/panel.tsx:1-3`) | right |
| 13 | 28-30 (Install and update) | Install from GitHub: the two commands of row 5 | As row 5: no file; Claude Code behaviour | not verified |
| 14 | 31 (Install and update) | Install from a local clone: `claude plugin marketplace add /path/to/moonlight_ai`, then install | `.claude-plugin/marketplace.json:9` (`"source": "./"`) does not contradict it; the command needs a run: no file; Claude Code behaviour | not verified |
| 15 | 32 (Install and update) | Update: `claude plugin update moonlight@moonlight` | `skills/moonlight-update/SKILL.md:24-25` runs `claude plugin marketplace update moonlight` first, then this command; the README omits the refresh step. Whether it is needed is Claude Code behaviour, no file | not verified |
| 16 | 32 (Install and update) | "or ask Claude to run `moonlight-update`" | `skills/moonlight-update/SKILL.md:2-3` (name and trigger) | right |
| 17 | 34 (Install and update) | Restart Claude Code after an update | `skills/moonlight-update/SKILL.md:31` says the same, but it relays what the CLI reports: no file; Claude Code behaviour | not verified |
| 18 | 36 (Install and update) | Every skill and agent is namespaced `moonlight:<name>`, for example `moonlight:sdlc-feature-analyst` | The skills call `moonlight:sdlc-ralph-implement` (`skills/sdlc-feature-analyst/SKILL.md:235`) and `moonlight:sdlc-uat-tester` (`:252`); `skills/sdlc-feature-analyst/SKILL.md:2` exists. The namespacing is Claude Code behaviour, no file | not verified |
| 19 | 37 (Install and update) | The call forms `Skill(skill: "moonlight:<name>")` and `subagent_type: "moonlight:<name>"` | Used in `skills/sdlc-feature-analyst/SKILL.md:235,252`; `CLAUDE.md` section "Skill / command / agent authoring". The repo only shows the form in use; that it resolves is Claude Code behaviour, no file | not verified |
| 20 | 38 (Install and update) | "Bare names do not resolve" | `CLAUDE.md` section "Skill / command / agent authoring" says it too; resolution is Claude Code behaviour, no file. Two bare calls in the repo are listed under Code issues | not verified |
| 21 | 42 (Entry points) | "They run the same phases" | The flows name and order their phases differently: `skills/moonlight-fast/SKILL.md:13-14`, `skills/moonlight-calm/SKILL.md:16-17`, `skills/sdlc-feature-analyst/SKILL.md:12-13` | wrong (edit 1) |
| 22 | 44-48 (Entry points) | The three skills exist and take a requirement text or an idea | `skills/sdlc-brainstorm/SKILL.md:2,6`, `skills/moonlight-fast/SKILL.md:2,6`, `skills/moonlight-calm/SKILL.md:2,6` | right |
| 23 | 46 (Entry points) | Standard: you take part in grilling, plan review, following the implementation, acceptance | `skills/sdlc-brainstorm/SKILL.md:30-38`, `skills/sdlc-feature-analyst/SKILL.md:187-214,291-295` | right |
| 24 | 47 (Entry points) | Fast: grilling, plan review, acceptance | `skills/moonlight-fast/SKILL.md:6-8` | right |
| 25 | 48 (Entry points) | Calm: the requirement, then acceptance | `skills/moonlight-calm/SKILL.md:6-8,82-88` | right |
| 26 | 52 (The phases) | "Every flow runs these phases" (the 8-step list) | `fast`: research, idea, design, implement, accept, docs, spendreport, close (`skills/moonlight-fast/SKILL.md:13-14`); `calm`: research, design, implement, docs, accept, spendreport, close (`skills/moonlight-calm/SKILL.md:16-17`); `sdlc-feature-analyst`: idea, design, implement, uat, docs, spendreport, close, with acceptance at hand-off (`skills/sdlc-feature-analyst/SKILL.md:12-13,291-295`); the bug flow has other steps (`skills/sdlc-fix-issue-from-triage/SKILL.md:13-15`). README step 4 "Code review" is no phase in any flow: it is Step 4.5 inside `sdlc-ralph-implement` (`skills/sdlc-ralph-implement/SKILL.md:93`) | wrong (edit 2) |
| 27 | 54-56, 58-61 (The phases) | What steps 1-3 and 5-8 contain: idea, plan plus proposed spec plus plan review, TDD on a feature branch, validation and acceptance, docs and specs, spend report into `## spendreport`, close | `skills/sdlc-feature-analyst/SKILL.md:25-31,45-55,216-225,268-295`, `skills/moonlight-fast/SKILL.md:37-96`, `scripts/token-report.py:149` | right |
| 28 | 57 (The phases) | A code review step exists | `skills/sdlc-ralph-implement/SKILL.md:93-123` | right (as a step inside Implementation; see row 26) |
| 29 | 63 (The phases) | The bug flow has its own steps and writes the spend report before it resolves the issue in the tracker | `skills/sdlc-fix-issue-from-triage/SKILL.md:13-15,104-111` (Step 6 item 1 before item 2) | right |
| 30 | 68-70 (Session state and spend report) | The block holds the flow, the current phase, each phase's status (`pending`, `running`, `waiting`, `blocked`, `done`), who waits (`you` or nobody), the sessions with start times, the branch and the idea file; no token numbers | `scripts/plan-state.py:57-65,92-103` | right |
| 31 | 68 (Session state and spend report) | Suspect: "the plan file ends with a `## Session state` block" | `scripts/plan-state.py:66-67` appends the block at the end, but `scripts/token-report.py:137` appends `## spendreport` after it, so the block is no longer last once the report exists | wrong (edit 3) |
| 32 | 70-71 (Session state and spend report) | The flows write it with `scripts/plan-state.py`: `init` once the plan exists, `phase` at the start of each phase | `skills/sdlc-feature-analyst/SKILL.md:15-19`, `skills/moonlight-fast/SKILL.md:16-20`, `skills/moonlight-calm/SKILL.md:19-23`, `skills/sdlc-fix-issue-from-triage/SKILL.md:17-21` | right |
| 33 | 71-72 (Session state and spend report) | A clean session given the plan reads the block and continues from the recorded phase | `skills/sdlc-feature-analyst/SKILL.md:22-23`, `skills/moonlight-fast/SKILL.md:21-23`, `skills/moonlight-calm/SKILL.md:26-28`, `skills/sdlc-fix-issue-from-triage/SKILL.md:22-23` | right |
| 34 | 74-76 (Session state and spend report) | `scripts/token-report.py --plan <plan>` counts every session in the block from `started_at`, subagents included, and writes `## spendreport`: messages, input, cache writes, cache reads, output, billable total | `scripts/token-report.py:33-44,112-129,142-163` | right |
| 35 | 76 (Session state and spend report) | Nothing is printed to chat | `skills/moonlight-fast/SKILL.md:88` and `skills/moonlight-calm/SKILL.md:99` ("Do not print the totals"), the other flows tell the user one line (`skills/sdlc-feature-analyst/SKILL.md:282-283`); the script prints one status line to the tool output (`scripts/token-report.py:163`) | right |
| 36 | 76-77 (Session state and spend report) | The count covers everything in those sessions since `started_at`, unrelated work too | `scripts/token-report.py:151-152` | right |
| 37 | 81-83 (What `moonlight-calm` does) | `moonlight-calm` asks nothing until the end; `sdlc-stand-in-product-owner` answers open points, `sdlc-stand-in-tech-lead` reviews the plan; decisions go into `## Decisions` with source and confidence | `skills/moonlight-calm/SKILL.md:6-11,43-50`; `agents/sdlc-stand-in-product-owner.md:2-3`, `agents/sdlc-stand-in-tech-lead.md:2-3` | right (the exceptions are the escalation list, rows 38-39) |
| 38 | 85 (What `moonlight-calm` does) | "The run stops and asks you only when:" followed by the list | The Escalation section lists six cases (`skills/moonlight-calm/SKILL.md:54-61`), but Phase 0 also stops and escalates on a dirty tree (`skills/moonlight-calm/SKILL.md:32-33`), which the list lacks | wrong (edit 4) |
| 39 | 86-93 (What `moonlight-calm` does) | The list: a stand-in not confident (`low`); a flag `security`, `auth`, `data-migration`, `breaking-change` or `public-api`; more than 12 checklist items; a review asks for changes twice in a row; implementation blocked; a UAT section fails; ready for acceptance | `skills/moonlight-calm/SKILL.md:56-61` (flags at `:57`, 12 at `:58`, twice at `:59`, also `:49-50`), acceptance `:82-88` | right |
| 40 | 95 (What `moonlight-calm` does) | Commits and merges stay with the user in every flow; Claude creates the feature branch and never commits | `skills/moonlight-fast/SKILL.md:96`, `skills/moonlight-calm/SKILL.md:107`, `skills/sdlc-feature-analyst/SKILL.md:291-295`, `skills/sdlc-fix-issue-from-triage/SKILL.md:119`, `skills/sdlc-ralph-implement/SKILL.md:219` | right |
| 41 | 99-100 (Start on an existing project) | `moonlight-init` needs a git repository; without one it stops and asks you to run `git init` | `skills/moonlight-init/SKILL.md:11-12` | right |
| 42 | 100-102 (Start on an existing project) | Step 1: it surveys the code for test, lint and build commands and notes what is missing | `skills/moonlight-init/SKILL.md:17-30` | right |
| 43 | 102-105 (Start on an existing project) | Step 2: research into `docs/codebase-research.md` (or `documentation/` if that folder exists), with `file:line` references; brainstorm and planning skills read it first | `skills/moonlight-init/SKILL.md:37-38,59`; `skills/sdlc-brainstorm/SKILL.md:22-23`; `skills/sdlc-feature-analyst/SKILL.md:48-50` | right |
| 44 | 106 (Start on an existing project) | Step 3: shows one table of what it will create and asks once | `skills/moonlight-init/SKILL.md:62-64,78-79` | right |
| 45 | 107-108 (Start on an existing project) | Step 4: creates `CLAUDE.md` from the starter, the `plans/` folders, `plans/reminders.md`, `specs/`, the `.gitignore` lines for the detected stack | `skills/moonlight-init/SKILL.md:66-72,83-99` | right |
| 46 | 109-110 (Start on an existing project) | Step 5: if you choose, one spec per component under `specs/`; each spec is one agent run | `skills/moonlight-init/SKILL.md:101-111` | right |
| 47 | 112 (Start on an existing project) | Existing files are skipped; nothing is committed | `skills/moonlight-init/SKILL.md:7,85,129` | right |
| 48 | 114-115 (Start on an existing project) | Headless `claude -p` runs need `--add-dir <plugin folder>` because the starter `CLAUDE.md` is in the plugin folder; an interactive session asks once | `skills/moonlight-init/SKILL.md:86` says where the starter is and does not contradict it; nothing in the repo mentions `-p` or `--add-dir`: no file; Claude Code behaviour | not verified |
| 49 | 119-123 (Start a new project) | init is for a repo that already has code; for a new project: create the folder, `git init`, write first code, commit, run init, then an entry point; both anchors | `skills/moonlight-init/SKILL.md:3,11-13`; a clean tree is needed by the flows (`skills/moonlight-fast/SKILL.md:27-28`); README headings at lines 97 and 40 | right |
| 50 | 127 (Adapters) | Suspect: the triage skills "need two things" | Three keys: `CLAUDE.md:151-155`; `Notify on resolve` is read by `skills/sdlc-fix-issue-from-triage/SKILL.md:112-114`; the README table below lists three | wrong (edit 5) |
| 51 | 127-128 (Adapters) | The project states it in a `## Moonlight adapters` section of `CLAUDE.md`, one `Key: value` line each | `CLAUDE.md:142-148`, `skills/sdlc-triage/SKILL.md:16`, `skills/sdlc-fix-issue-from-triage/SKILL.md:7-8` | right |
| 52 | 130-134 (Adapters) | The table: `Triage source`, `Resolve in tracker` (runs only after you confirm), `Notify on resolve` and their meanings | `CLAUDE.md:151-155`; confirm gate `skills/sdlc-fix-issue-from-triage/SKILL.md:91-102`, `skills/sdlc-triage/SKILL.md:39-40` | right |
| 53 | 136 (Adapters) | A missing or `(not set)` key makes the skill ask instead of guess a command | `CLAUDE.md:144-145`, `skills/sdlc-triage/SKILL.md:19-21`, `skills/sdlc-fix-issue-from-triage/SKILL.md:109-111` (for `Notify on resolve`, a flag and no command, a missing value means "nothing is sent", `:112-114`) | right |
| 54 | 136-137 (Adapters) | Commands read secrets from the environment or `.env`; the section names variables, never values | `CLAUDE.md:156` | right |
| 55 | 141-143 (Adapt it to your project) | Skills are namespaced, so a copy in `.claude/skills/` does not replace the plugin skill, and a plugin update never reaches it | `docs/skill-authoring.md:8-11` keeps repo-local tools in `.claude/skills/` and does not contradict it; the replace and update behaviour is Claude Code's: no file; Claude Code behaviour | not verified |
| 56 | 143-150 (Adapt it to your project) | There are four layers and the first that works is used | The table holds four rows: Values, Rules, Gates, Wrappers (`README.md:145-150`) | right |
| 57 | 147 (Adapt it to your project) | Values: `## Commands` and `## Moonlight adapters` in `CLAUDE.md` hold the test, lint and build commands and the issue tracker | `skills/moonlight-init/SKILL.md:93` (writes `## Commands`), `CLAUDE.md:142-156` | right |
| 58 | 147 (Adapt it to your project) | Suspect: Values row, second sentence: "The planner copies `## Commands` into each plan's Validation and Definition of Done" | Only `skills/moonlight-init/SKILL.md:125` says it. `sdlc-feature-analyst` has only the placeholders `<test command>` and `<lint/typecheck command>` (`skills/sdlc-feature-analyst/SKILL.md:127,140`) and its CLAUDE.md read is for standing constraints (`:105-108`); `## Commands` appears in no other skill or agent (search over the repo: `skills/moonlight-init/SKILL.md:53,93,125` only) | wrong (edit 6) |
| 59 | 148 (Adapt it to your project) | Rules: the rest of `CLAUDE.md`; the planner copies them into each plan's `### Standing constraints` | `skills/sdlc-feature-analyst/SKILL.md:105-108`, `agents/sdlc-ralph-implementer.md:46`, `agents/sdlc-ralph-reviewer.md:54` | right |
| 60 | 149 (Adapt it to your project) | "A gate is code, not a sentence in `CLAUDE.md`" for "never" rules | `CLAUDE.md` section "Testing & validation" (a "must always / must never" requirement is a code gate) | right |
| 61 | 149 (Adapt it to your project) | Gates are hooks in the project's `.claude/settings.json` | `hooks/hooks.json:14-24` shows the plugin's own hook form; where a project puts its own hooks is Claude Code behaviour: no file; Claude Code behaviour | not verified |
| 62 | 150 (Adapt it to your project) | Wrappers: a project skill with its own name calls `Skill(skill: "moonlight:<name>")` and adds steps | The plugin's skills call each other that way (`skills/moonlight-fast/SKILL.md:39,58`); that a project skill can call a plugin skill is Claude Code behaviour: no file; Claude Code behaviour | not verified |
| 63 | 152-154 (Adapt it to your project) | Fixed: commit and push are always the user's, and the git-safety hook enforces it | `hooks/block-git-commit-push.sh:14-19`, `hooks/hooks.json:14-24` | right |
| 64 | 155 (Adapt it to your project) | Fixed: the layout and file names under `plans/`, which the skills read and write | `skills/sdlc-feature-analyst/SKILL.md:52-55`, `skills/sdlc-fix-issue-from-triage/SKILL.md:29`, `skills/sdlc-triage/SKILL.md:61`, `hooks/panel.tsx:11` | right |
| 65 | 157 (Adapt it to your project) | Last resort: copy a skill under another name, note the plugin version it came from, merge later changes yourself | Advice, no checkable claim; the version to note exists (`.claude-plugin/plugin.json:3`) | right |
| 66 | 159-161, 174, 181 (Skills; Feature pipeline; Bug pipeline; Conversation and setup) | Suspect: `moonlight-calm` and `moonlight-fast` have no row in the Skills tables | The headings claim no completeness: "Feature pipeline", "Bug pipeline", "Conversation and setup" (`README.md:161,174,181`). Both skills are described in Entry points and in the `moonlight-calm` section (`README.md:44-48,79-93`) and exist (`skills/moonlight-fast/SKILL.md:2`, `skills/moonlight-calm/SKILL.md:2`). Not a wrong claim; adding rows would be new text, a non-goal | right (no edit) |
| 67 | 165 (Feature pipeline) | `sdlc-brainstorm`: finds precedents, grills you, writes the idea file with a `## Proposed spec`; on confirm adds the success check to `plans/reminders.md` | `skills/sdlc-brainstorm/SKILL.md:20-38,44-64,88-89` | right |
| 68 | 166 (Feature pipeline) | `sdlc-feature-analyst`: idea or raw request into a plan; a fresh agent reviews it, you approve, it hands off to `sdlc-ralph-implement`; the spec gate runs at close-out | `skills/sdlc-feature-analyst/SKILL.md:25-43,170-201,230-239,276-279` | right |
| 69 | 167 (Feature pipeline) | `sdlc-ralph-implement`: runs a checklist plan to the end: implement, review and validate, repeat until the round is clean or the retry budget runs out; resumable | `skills/sdlc-ralph-implement/SKILL.md:11-14,78-123,125-145,166-197` | right |
| 70 | 168 (Feature pipeline) | `sdlc-tdd`: "Test-first red-green-refactor"; a bug fix starts red on the unfixed code | The skill says "TDD is the red → green loop" (`skills/sdlc-tdd/SKILL.md:8`) and "Refactoring is not part of the loop" (`:39`); the bug-fix half is right (`:37`) | wrong (edit 7) |
| 71 | 169 (Feature pipeline) | `sdlc-standards-spec-review`: reviews a diff on standards and spec in parallel sub-agents; a fork of Matt Pocock's `code-review` (MIT) | `skills/sdlc-standards-spec-review/SKILL.md:3-4,7-10,12-17`; `docs/third-party.md:1-8` | right |
| 72 | 170 (Feature pipeline) | `sdlc-diagnosing-bugs`: finds the cause of a hard bug or a performance regression before any fix | `skills/sdlc-diagnosing-bugs/SKILL.md:3,66,114` (causes in Phases 1-4, fix in Phase 5) | right |
| 73 | 171 (Feature pipeline) | `sdlc-pr`: writes a PR body | `skills/sdlc-pr/SKILL.md:3,12` | right |
| 74 | 172 (Feature pipeline) | `sdlc-update-readme`: keeps README.md in sync with real changes only | `skills/sdlc-update-readme/SKILL.md:11-17` | right |
| 75 | 178 (Bug pipeline) | `sdlc-triage`: fetches unresolved issues through `Triage source`, filters spam and test noise, drafts a bugfix plan per confirmed issue into `plans/triage/active/` | `skills/sdlc-triage/SKILL.md:16-21,28-40,58-62` | right |
| 76 | 179 (Bug pipeline) | `sdlc-fix-issue-from-triage`: reproduces the symptom, fixes through `sdlc-ralph-implement`, checks the regression test fails on the unfixed code, closes the issue through `Resolve in tracker` after you confirm | `skills/sdlc-fix-issue-from-triage/SKILL.md:45-51,53-62,75-81,91-111` | right |
| 77 | 185 (Conversation and setup) | `productivity-grilling`: interviews you, one question per turn; for a big idea it asks first: one at a time, or in rounds | `skills/productivity-grilling/SKILL.md:8,10` | right |
| 78 | 186 (Conversation and setup) | `productivity-grill-me`: alias for `productivity-grilling`; only you can run it | `skills/productivity-grill-me/SKILL.md:4,7` | right |
| 79 | 187 (Conversation and setup) | `productivity-handoff`: writes a handoff document so a fresh agent can pick up; only you can run it | `skills/productivity-handoff/SKILL.md:3,5,8` | right |
| 80 | 188 (Conversation and setup) | `productivity-research`: investigates a question against high-trust primary sources and saves findings as a Markdown file in the repo | `skills/productivity-research/SKILL.md:3,10-11` | right |
| 81 | 189 (Conversation and setup) | `productivity-retro`: runs a retrospective on a coding session; only you can run it | `skills/productivity-retro/SKILL.md:3-4,7` | right |
| 82 | 190 (Conversation and setup) | `productivity-show-me`: explains the current topic visually, diagrams and focused HTML artifacts; only you can run it | `skills/productivity-show-me/SKILL.md:3-4,118` | right |
| 83 | 191 (Conversation and setup) | `productivity-wait-what`: re-pitches the last message in plain terms; only you can run it | `skills/productivity-wait-what/SKILL.md:3-4,7` | right |
| 84 | 192 (Conversation and setup) | `productivity-writing-for-agents`: guidance for documents an agent reads: skills, `AGENTS.md`, `CLAUDE.md` | `skills/productivity-writing-for-agents/SKILL.md:3,6` | right |
| 85 | 193 (Conversation and setup) | `moonlight-init`: sets up an existing repo; link `#start-on-an-existing-project` | `skills/moonlight-init/SKILL.md:3`; README heading at line 97 | right |
| 86 | 194 (Conversation and setup) | `moonlight-update`: updates the installed plugin from its marketplace and reports the version | `skills/moonlight-update/SKILL.md:3,24-30` | right |
| 87 | 186-191 (Conversation and setup) | "Only you can run it" appears on exactly five rows | `disable-model-invocation: true` is set in exactly five skills: grill-me `:4`, retro `:4`, show-me `:4`, handoff `:5`, wait-what `:4`; no other skill sets it | right |
| 88 | 198 (Agents) | Agents run inside skills; you do not call them directly | `agents/sdlc-ralph-implementer.md:3`, `agents/sdlc-ralph-reviewer.md:3`, `agents/sdlc-spec-writer.md:3` ("Never invoke ... directly / for open-ended ..."); the stand-ins say the same | right |
| 89 | 202 (Agents) | `sdlc-ralph-implementer`: one pass of a checklist plan for `sdlc-ralph-implement`, writes the failing test first | `agents/sdlc-ralph-implementer.md:3,8-12,31-34` | right |
| 90 | 203 (Agents) | `sdlc-ralph-reviewer`: read-only review gate after each pass; checks security, dead code, over-engineering, regression tests that could not fail | `agents/sdlc-ralph-reviewer.md:3,12,77,129,199`; `skills/sdlc-ralph-implement/SKILL.md:93-100` | right |
| 91 | 204 (Agents) | `sdlc-spec-writer`: writes `specs/<component>.md`, a Gherkin description of what a component does now | `agents/sdlc-spec-writer.md:8-9,56-70` | right |
| 92 | 205 (Agents) | `sdlc-uat-tester`: black-box, no codebase access; runs only when a plan has `## UAT verification` | `agents/sdlc-uat-tester.md:3,12-20`; `skills/sdlc-feature-analyst/SKILL.md:246-252`, `skills/sdlc-fix-issue-from-triage/SKILL.md:68-70` | right |
| 93 | 206 (Agents) | `sdlc-stand-in-product-owner`: answers open questions in `moonlight-calm`; returns an answer, a confidence and flags | `agents/sdlc-stand-in-product-owner.md:3`, `skills/moonlight-calm/SKILL.md:43-45` | right |
| 94 | 207 (Agents) | `sdlc-stand-in-tech-lead`: reviews a plan in `moonlight-calm`; approves it or returns blockers | `agents/sdlc-stand-in-tech-lead.md:3`, `skills/moonlight-calm/SKILL.md:48-50` | right |
| 95 | 213 (Hooks) | `block-git-commit-push.sh` runs as PreToolUse on Bash and blocks `git commit` and `git push` | `hooks/hooks.json:14-24`, `hooks/block-git-commit-push.sh:14-19` | right |
| 96 | 213 (Hooks) | It also blocks `reset --hard`, `clean -f`, `branch -D`, `checkout .` and `restore .` | `hooks/block-git-commit-push.sh:21` | right |
| 97 | 21, 214 (Quick start; Hooks) | Suspect: `reminders.py` runs at SessionStart and shows the lines of `plans/reminders.md` due within 3 days | Event and the 3-day rule are right (`hooks/hooks.json:3-12`, `hooks/reminders.py:8,17`). The path is built with `parents[2]` (`hooks/reminders.py:9`): from `hooks/reminders.py` that is the folder above the plugin root, not the project, so the hook cannot find the project's `plans/reminders.md`. The code is what looks wrong; the README describes the intended behaviour and is not changed | wrong (code issue 1; no README edit) |
| 98 | 215 (Hooks) | `panel.tsx` is a mod (function hooks), described in the next section | `hooks/hooks.json:26`, `hooks/panel.tsx:122` | right |
| 99 | 219-220 (Side panel) | The panel opens by itself in a terminal session while a plan in `plans/improvements/active/` or `plans/triage/active/` holds a `## Session state` block; the newest such plan wins | `hooks/panel.tsx:11,54-70,125` | right |
| 100 | 220-222 (Side panel) | It shows the flow and time since `started_at`, each phase with its status, a `you` mark on the waiting phase, tokens per subagent, a total split into input, cache and output | `hooks/panel.tsx:167-187` | right |
| 101 | 222 (Side panel) | Phases redraw every few seconds; tokens every 30 seconds and when a turn ends | `hooks/panel.tsx:131-132,155-159` (3000 ms and 30000 ms timers, `turn.complete`) | right |
| 102 | 224 (Side panel) | `/moonlight-panel` hides it and brings it back; closing it with its close mark hides it too | `hooks/panel.tsx:128,137-146,149-151` | right |
| 103 | 225-226 (Side panel) | Under 144 columns Claude Code holds the pane back until there is room, or until you run `/moonlight-panel` | `docs/panel-spike.md:38-40` records the engine's rule, taken from the types and the reference, not run; no repo code applies it: no file; Claude Code behaviour | not verified |
| 104 | 227-228 (Side panel) | It closes when the plan moves to `implemented/`, or when the plan is `status: done` and its flow reached the last phase | `hooks/panel.tsx:11,43,78` (only `active/` is read; the `done` rule) | right |
| 105 | 230 (Side panel) | `docs/panel-spike.md` records what was checked about the mod API and what was not | `docs/panel-spike.md:3-4,18-32` | right |
| 106 | 234-236 (Output style) | `talk-to-user` replies in short, plain words, point first, short lines, facts exact; it keeps Claude Code's coding instructions | `output-styles/talk-to-user.md:4,8-29` shows the text and the `keep-coding-instructions: true` key (`:4`); what Claude Code does with the key is not in any repo file: no file; Claude Code behaviour | not verified |
| 107 | 235 (Output style) | It is on by default while the plugin is enabled | `output-styles/talk-to-user.md:3,5` (`force-for-plugin: true`) shows the frontmatter asks for it, as in row 108; what Claude Code does with the key is not in any repo file: no file; Claude Code behaviour | not verified |
| 108 | 235-236 (Output style) | It overrides the output style you pick with `/output-style`; disable the plugin to turn it off | The frontmatter asks for it (`output-styles/talk-to-user.md:5`); what Claude Code does with it is not in any repo file: no file; Claude Code behaviour | not verified |
| 109 | 240-241 (Starter CLAUDE.md) | `CLAUDE.md` at the plugin root holds the practices `moonlight-init` copies: planning, testing, git and deploy safety, knowledge capture | `skills/moonlight-init/SKILL.md:86`; `CLAUDE.md` sections "Before making changes", "Testing & validation", "Safety & guardrails", "Documentation & knowledge capture" | right |
| 110 | 241-242 (Starter CLAUDE.md) | Suspect: "The plugin itself does not load this file into its own sessions" | Meaning: installing the plugin does not put this file into the sessions of the projects that use it (`CLAUDE.md:3-6` calls it a template, "not a rulebook this repo itself must obey"). Whether a plugin loads a root `CLAUDE.md` is Claude Code behaviour: no file. In this repo Claude Code does load `CLAUDE.md` as the project's own instructions, which the sentence does not mean; left unedited, flagged | not verified (no edit) |
| 111 | 246 (Develop the plugin) | `claude --plugin-dir .` tests local edits without installing | No file; needs a run; Claude Code behaviour | not verified |
| 112 | 247 (Develop the plugin) | `claude plugin validate .` checks the manifests | `docs/panel-spike.md:4,9` records the author running `claude plugin validate` on a scratch copy; I ran nothing | not verified |
| 113 | 248 (Develop the plugin) | `python3 -m unittest discover -s test` runs the script tests | `test/test_plan_state.py:8,28` and `test/test_token_report.py:8,91` are `unittest.TestCase` files in `test/`; only names and layout checked; the command needs a run and I ran nothing | not verified |
| 114 | 248 (Develop the plugin) | `claude plugin test .` runs the panel test | `docs/panel-spike.md:66-71` describes the command; `test/panel.test.tsx` exists; needs a run | not verified |
| 115 | 249 (Develop the plugin) | Use the plugin in this repo too: install it from the local clone, see Install and update | Anchor `#install-and-update` exists (`README.md:26`); the install itself is row 14 | not verified |
| 116 | 253-255 (Not in the plugin yet) | `.claude/skills/helper-*` (`helper-do-in-my-chrome`, `helper-sql`) stay in this repo and are not installed by the plugin | `.claude/skills/helper-do-in-my-chrome/SKILL.md:2`, `.claude/skills/helper-sql/SKILL.md:2` exist; the plugin folders are `skills/`, `agents/`, `hooks/`, `output-styles/` (`docs/skill-authoring.md:8-11`) | right |
| 117 | 259-265 (Docs) | The five files exist and are described correctly: `CLAUDE.md`, `docs/third-party.md` (Pocock and HumanLayer, both MIT), `docs/skill-authoring.md`, `docs/patterns.md`, `docs/panel-spike.md` | `docs/third-party.md:1-14`, `docs/skill-authoring.md:1-11`, `docs/patterns.md:1-4`, `docs/panel-spike.md:3-4`; `CLAUDE.md:1-6` | right |
| 118 | 3, 9, 19, 123-124, 194, 231, 250, 262-265 (all) | Every relative link and every `#anchor` resolves | Anchors against `grep '^#'` of the README: `#start-a-new-project` (118), `#entry-points` (40), `#start-on-an-existing-project` (98), `#install-and-update` (26), all at the edited-file line numbers; files exist: `LICENSE`, `CLAUDE.md`, `docs/third-party.md`, `docs/skill-authoring.md`, `docs/patterns.md`, `docs/panel-spike.md`, `.claude-plugin/icon.png` | right |

Heading coverage (22 headings and the intro): intro rows 1-4; Quick start 5-12; Install and update 13-20; Entry points 21-25;
The phases 26-29; Session state and spend report 30-36; What `moonlight-calm` does on its own 37-40; Start on an existing
project 41-48; Start a new project 49; Adapters 50-54; Adapt it to your project 55-65; Skills 66; Feature pipeline 67-74; Bug
pipeline 75-76; Conversation and setup 77-87; Agents 88-94; Hooks 95-98; Side panel 99-105; Output style 106-108; Starter
CLAUDE.md 109-110; Develop the plugin 111-115; Not in the plugin yet 116; Docs 117. Links and anchors: row 118.

## README edits

Line numbers are those at `HEAD`. Each edit is one `Edit` on `README.md`.

| Edit | README line | Before | After | Claim row |
|---|---|---|---|---|
| 1 | 42 | `Three ways in. They run the same phases. They differ in how much you take part.` | `Three ways in. They cover the same steps. They differ in how much you take part.` | 21 |
| 2 | 52 | `Every flow runs these phases:` | `The feature flows cover these steps. Names and order differ a little per flow, and code review runs inside Implementation:` | 26 |
| 3 | 68 | `the plan file ends with a `## Session state` block` | `the plan file holds a `## Session state` block` | 31 |
| 4 | 85-86 | list starts with `- a stand-in is not confident (`low`),` | a new first bullet `- the working tree is not clean at the start,` is added above it | 38 |
| 5 | 127 | `The triage skills need two things from the project: where the issues live, and how to close one.` | `The triage skills need three things from the project: where the issues live, how to close one, and whether closing one notifies the reporter.` | 50 |
| 6 | 147 | `The test, lint and build commands, and the issue tracker. The planner copies `## Commands` into each plan's Validation and Definition of Done.` (Values row) | `The test, lint and build commands, and the issue tracker.` | 58 |
| 7 | 168 | `Test-first red-green-refactor. A bug fix starts red on the unfixed code.` | `Test-first red-green loop. A bug fix starts red on the unfixed code.` | 70 |

Check (item 8): every edit above has a justifying `wrong` row (21, 26, 31, 38, 50, 58, 70), and every `wrong` row has an edit or a
code issue (row 97 is code issue 1). The `git diff -U0 -- README.md` of the working tree shows seven changed spots, exactly
these seven edits and nothing else.

Cites in `docs/codebase-research.md` (item 9): edit 4 added one README line at 86, so the cites below it moved by one. Updated
there: `README.md:238-242` to `239-243` (line 11), `251-255` to `252-256` (line 31), `248` to `249` (tests, lines 53 and 57),
`247` to `248` (validate, lines 53 and 57), `246` to `247` (`--plugin-dir`, line 57). Unchanged, and still right:
`5-8`, `21-24`, `40-48`, `81-82`, `8`, `36-38`. Nothing else in that file changed.

Totals of `## Claim check`: 118 rows, 87 right, 8 wrong, 23 not verified.

## Code issues for the owner

Found while reading; none is changed here, and the README is not edited for them.

1. `hooks/reminders.py:9`: `pathlib.Path(__file__).resolve().parents[2] / "plans" / "reminders.md"`. From
   `hooks/reminders.py`, `parents[0]` is `hooks/`, `parents[1]` is the plugin root, `parents[2]` is the folder above it.
   The hook therefore looks for `plans/reminders.md` outside the plugin and outside the project. It should read the
   project's file (the session's working directory). README lines 21 and 214 describe the intended behaviour. Claim row 97.
2. `skills/moonlight-init/SKILL.md:125` says "The planner copies commands from `## Commands` into each plan's Validation and
   Definition of Done". `sdlc-feature-analyst` has no such step (`skills/sdlc-feature-analyst/SKILL.md:127,140` are
   placeholders). Either the planner gets the step or the init line goes. The README sentence was removed (edit 6). Claim row 58.
3. `skills/productivity-retro/SKILL.md:11` calls the skill `writing-for-agents`. That name does not exist and a bare name does
   not resolve; the skill is `moonlight:productivity-writing-for-agents`. Claim row 20.
4. `skills/sdlc-tdd/SKILL.md:26` calls the skill `codebase-design`, and `:39` points at the `code-review` skill. Neither is in
   this repo (the fork is `sdlc-standards-spec-review`). Claim row 20.
5. `skills/sdlc-ralph-implement/SKILL.md:19` lists `plans/*.md` (excluding `plans/implemented/`) when no argument is given. The
   plans live in `plans/improvements/active/` and `plans/triage/active/`, so the list finds nothing.

## Session state

```json
{
  "flow": "sdlc-feature-analyst",
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
      "started_at": "2026-10-30T20:59:19Z"
    }
  ],
  "branch": "feat/8-readme-usage-check",
  "idea": "plans/ideas/idea_8_readme-usage-check.md"
}
```

## Review

- [x] Code review passed (round 2)
- note: `README.md:52-57`, edit 2 says "code review runs inside Implementation" while the list below still shows "4. Code review" as its own step. Accurate and the smallest edit; the owner can drop the clause.
- note: `README.md:128`, the edited line is about 150 characters while the prose around it wraps at about 120.
- note: `README.md:76`, "Nothing is printed to chat" is true of the totals; the flows still tell the user one line that the spend report is in the plan.
- note: `README.md:148`, after edit 6 the Values row still lists `## Commands`; only `moonlight-init` writes that section and no skill reads it (code issue 2).
- note: plan row 2 ("update it in place") is `right` on the update skill's existence, not on how Claude Code applies the update; row 15 covers the command and is `not verified`.
- note: plan rows 99 and 102 are `right` on the module's own code; they assume the engine honours `$.ui.open` and the person's close event.

## spendreport

Counted at 2026-10-30T21:10:46Z over sessions 2e8db606-cd0e-4603-aef9-49e505c34c12: everything in those sessions since 2026-10-30T20:59:33Z, subagents included.

- messages: 86
- input tokens (new): 182
- cache writes: 320171
- cache reads: 10232017
- output tokens: 89572
- billable total (new + writes + output): 409925
