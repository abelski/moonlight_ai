# claude_bootstrap

Reusable Claude Code setup pulled out of this machine's working repos — the parts that are
generic enough to drop into a new project instead of rebuilding from scratch each time.

## What's here

- **[CLAUDE.md](CLAUDE.md)** — a starter set of working practices (planning, testing, git/deploy
  safety, knowledge capture). Copy into a new project's `CLAUDE.md` and trim to what fits.
- **`.claude/skills/`** — flat on disk (Claude Code doesn't discover nested skill folders), grouped
  by name prefix:
  - **SDLC (`sdlc-*`)** — the idea → plan → implement → review pipeline.
    - `sdlc-brainstorm` — first step of a feature: find precedents in past plans, grill the user,
      write a confirmed `plans/ideas/idea_<N>_<slug>.md` holding the what/why, hand off to
      `sdlc-feature-analyst`.
    - `sdlc-feature-analyst` — idea file or raw request → plan → cold review by a fresh agent →
      approve → branch `feat/<N>-<slug>` → hand off to `sdlc-ralph-implement`. The user commits
      and merges.
    - `sdlc-ralph-implement` — bounded, resumable, self-correcting loop that executes a checklist
      plan: implement → review ⇄ validate, repeated until a round is clean or the budget runs out.
    - `sdlc-triage` — bulk-intake sibling to `sdlc-feature-analyst`: fetch unresolved issues from
      this project's own tracker (source left for the project to plug in), filter spam/test
      noise, draft a bugfix plan per confirmed issue into `plans/triage/active/`.
    - `sdlc-fix-issue-from-triage` — companion to `sdlc-triage`: execute one drafted plan via
      `sdlc-ralph-implement`, confirm resolution with the user, then update the tracker
      (mechanism left for the project to plug in) and move the plan to `implemented/`.
    - `sdlc-standards-spec-review` — two-axis diff review (Standards: repo conventions + Fowler
      smell baseline; Spec: does it match the plan) in parallel sub-agents. Fork of Matt Pocock's
      `code-review` (MIT), renamed to not shadow the built-in `/code-review` bug hunter.
    - `sdlc-update-readme` — keep README.md in sync with real changes only.
  - **Productivity (`productivity-*`)** — conversation tools.
    - `productivity-grilling` — relentless interview to stress-test a plan, decision, or idea;
      `productivity-grill-me` is a user-typed alias for it.
    - `productivity-handoff` — compact the conversation into a handoff doc for another agent.
    - `productivity-wait-what` — the last reply didn't land: re-pitch it.
  - **Helpers (`helper-*`)** — one-off utilities.
    - `helper-do-in-my-chrome` — drive the user's own logged-in Chrome tab.
    - `helper-sql` — ad-hoc query runner against a project's database.
- **`.claude/agents/`** — all SDLC, same `sdlc-` prefix as the skills.
  - `sdlc-ralph-implementer` — the mechanical worker `sdlc-ralph-implement` spawns per pass.
  - `sdlc-ralph-reviewer` — read-only code-review gate (security, dead code, over-engineering,
    config-vs-hardcoded, architecture fit), reporting on the same Standards/Spec axes as
    `sdlc-standards-spec-review` and reusing its smell baseline. Runs as `sdlc-ralph-implement`'s
    Step 4.5 gate after implementation, before validation; blockers go back to the implementer.
  - `sdlc-spec-writer` — maintains `specs/<component>.md`, a living current-behavior doc (Gherkin
    scenarios) written after a plan's Definition-of-Done gate passes — optional add-on, invoked
    from `sdlc-feature-analyst`'s wrap-up only if a project uses this convention.
  - `sdlc-uat-tester` — black-box PASS/FAIL/INCONCLUSIVE verifier with zero codebase access, driving
    the running app via a project-supplied instrument (CLI, HTTP call, probe script) — optional
    add-on, invoked from `sdlc-feature-analyst`'s Phase 4.5 only when a plan has a `## UAT
    verification` section.
- **`.claude/output-styles/talk-to-me.md`** — short, blunt, plain-language replies.
- **`docs/skill-authoring.md`** — the Agent Skills spec convention used across these repos.
- **`docs/patterns.md`** — heavier patterns seen elsewhere (a tiered plan-and-verify loop with
  black-box verification, a deploy-safety protocol, agent-loop design notes) that are pointers to
  their source repo, not copies — too coupled to genericize until actually needed.

## How to use it

Copy what you need into a new project's `.claude/` and `CLAUDE.md` — this repo isn't meant to be
symlinked or installed as a dependency, it's a catalog to pull from and adapt per-project.
