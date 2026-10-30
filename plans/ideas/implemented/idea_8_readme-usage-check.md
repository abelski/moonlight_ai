---
number: 8
slug: readme-usage-check
status: confirmed
---

# Idea #8 — Check that the README describes correctly how to use the plugin

## Problem
The README is the only place that tells a user how to install, start and use moonlight. It has grown fast: plan #7
added a panel section, a state-block section and new phases, and the owner added "Adapt it to your project" by hand.
Nobody has checked the whole file against the skills, hooks, scripts and agents it describes. A wrong step or a
stale name sends a new user to a dead end.

## Desired outcome
A README whose usage claims match the code. The owner gets a list of every claim that was checked, with the file and
line that proves it, and a clear mark for what could not be checked by reading.

## Scope
- In: read the whole `README.md`, including "Adapt it to your project". Check each claim about how to use the plugin
  (install and update steps, entry points and their phases, `moonlight-init`, starting a new or existing project,
  adapters, skills, agents, hooks, the panel, develop and docs tables) against the repo. Fix wrong or stale text in
  `README.md` with the smallest edits. List what is wrong in the code, for the owner to decide.
- Out (non-goals):
  - Changing code, skills, hooks or scripts. A bug found in code goes to a list, not into this change.
  - Running any command, even a harmless one. The check is reading and thinking only.
  - New README sections or a new structure.
  - A spec file: this is a document change, not new behavior.

## Decisions
- **Q** What comes out? — Report and fix: check every claim, fix `README.md` with minimal edits, list what was checked and what was fixed.
- **Q** How to check? — Read only. No command is run, so install and update from GitHub cannot be confirmed and are marked "not verified".
- **Q** Which parts? — The whole file, including the owner's uncommitted section "Adapt it to your project".
- **Q** When README and code disagree? — README is changed. The code is the truth. A suspected code bug is only listed.
- **Q** Non-goals and success check — Confirmed as written here.

## Precedents
- `plans/improvements/implemented/plan_7_spendreport-panel.md` — edited the README (Check phase, panel, state block,
  prerequisites) and `docs/codebase-research.md`. Reuse: the README line anchors it changed, and its finding that
  doc cites go stale after a change.
- `docs/codebase-research.md` — a map of the code with `file:line` cites. Use it to find what the README should match.

## Success check
1. A list of checked claims exists. Each row has the file and line that proves it and a verdict: right, wrong, or not
   verified.
2. Every wrong claim is fixed in `README.md` or is in the list for the owner.
3. Everything that needs a run (install from GitHub, `claude plugin install`) is marked "not verified", never "right".
4. The `README.md` diff holds nothing except the fixes from point 2.

## Open questions
- Where the list of checked claims lives: in the plan file, or a file under `docs/`. Left for `sdlc-feature-analyst`.
- Branch base: `feat/7-spendreport-panel` is not merged yet and the working tree holds the owner's uncommitted
  README section. The README edits must not get mixed into plan #7's commit by accident.
