# moonlight

Claude Code plugin with our SDLC pipeline, plus a git-safety hook and a reminders hook. Installed
once per machine or project and updated in place, instead of copying files between repos.

Repo: `github.com/abelski/moonlight_ai`. License: MIT (see [LICENSE](LICENSE)).

## Install

Requires `jq` (the git-safety hook reads its input with it) and `python3` (the reminders hook).

From GitHub:

```bash
claude plugin marketplace add abelski/moonlight_ai
claude plugin install moonlight@moonlight
```

From a local clone (what to use while developing the plugin):

```bash
claude plugin marketplace add /path/to/moonlight_ai
claude plugin install moonlight@moonlight
```

Update later with `claude plugin update moonlight@moonlight`, or ask Claude to run the
`moonlight-update` skill. Restart Claude Code after an update.

Inside the plugin, every skill and agent is namespaced `moonlight:<name>`, for example
`moonlight:sdlc-feature-analyst`. The names below are the bare names. Reference them the same way from
other skills: `Skill(skill: "moonlight:<name>")` and `subagent_type: "moonlight:<name>"`. Bare names do not resolve.

## Start on an existing project

Run `moonlight-init` once in the repo. It works in this order:

1. Surveys the code for its test, lint and build commands, and notes what is missing.
2. Researches the codebase into `docs/codebase-research.md` (or `documentation/codebase-research.md` when that
   folder exists): a map with `file:line` references, which the brainstorm and planning skills read first.
3. Shows one table of what it will create, and asks once.
4. Applies it. It creates `CLAUDE.md` from the starter, the `plans/` folders, `plans/reminders.md`, `specs/`, and
   the `.gitignore` lines for the detected stack.
5. If you pick it, writes one spec per component under `specs/` through the `sdlc-spec-writer` agent. Each spec is
   one agent run, so pick components on large repos.

Anything that already exists is skipped, and nothing is committed. Review the files, then commit them yourself.

Headless runs (`claude -p`) need `--add-dir <plugin folder>`, because the starter `CLAUDE.md` lives in the plugin
folder. An interactive session asks once instead.

## Adapters

The triage skills need to know where a project's issues live and how to close one. The project says so in a
`## Moonlight adapters` section of its `CLAUDE.md`, one `Key: value` line each:

- `Triage source`: a read-only command that prints the open issues as a JSON array.
- `Resolve in tracker`: a command that takes one issue id and marks it resolved. It runs only after you confirm.
- `Notify on resolve`: `yes` if the resolve command notifies the reporter, `no` if nothing does.

`(not set)`, or a missing key, makes the skill ask you instead of guessing a command. Commands read secrets from
the environment or `.env`: the section names variables, never values. `moonlight-init` asks for these values when a
project triages issues, and the starter carries the section with every value at `(not set)`.

## What the plugin contains

- **Skills** (`skills/`) — flat on disk, one folder per skill.
  - **SDLC (`sdlc-*`)** — the idea → plan → implement → review pipeline.
    - `sdlc-brainstorm` — first step of a feature: find precedents in past plans, grill the user, write a
      confirmed `plans/ideas/idea_<N>_<slug>.md` holding the what/why, including a `## Proposed spec` in Gherkin.
      On confirm, the success check becomes a dated line in `plans/reminders.md`. Hands off to
      `sdlc-feature-analyst`.
    - `sdlc-feature-analyst` — idea file or raw request → plan → cold review by a fresh agent → approve →
      branch `feat/<N>-<slug>` → hand off to `sdlc-ralph-implement`. Optional `## Prototype` step for plans that
      change visible UI. At close-out, a spec gate checks the shipped behavior against the idea's proposed spec.
      The user commits and merges.
    - `sdlc-ralph-implement` — bounded, resumable, self-correcting loop that executes a checklist plan:
      implement → review ⇄ validate, repeated until a round is clean or the budget runs out.
    - `sdlc-triage` — bulk-intake sibling to `sdlc-feature-analyst`: fetch unresolved issues from this
      project's own tracker (source left for the project to plug in), filter spam/test noise, draft a bugfix
      plan per confirmed issue into `plans/triage/active/`.
    - `sdlc-fix-issue-from-triage` — companion to `sdlc-triage`: reproduce the symptom before fixing, execute
      one drafted plan via `sdlc-ralph-implement`, check that the regression test fails on the unfixed code,
      confirm resolution with the user, then update the tracker (mechanism left for the project to plug in) and
      move the plan to `implemented/`.
    - `sdlc-standards-spec-review` — two-axis diff review (Standards: repo conventions + Fowler smell baseline;
      Spec: does it match the plan) in parallel sub-agents. Fork of Matt Pocock's `code-review` (MIT), renamed to
      not shadow the built-in `/code-review` bug hunter.
    - `sdlc-diagnosing-bugs` — diagnosis loop for hard bugs and perf regressions: find the cause before fixing.
    - `sdlc-tdd` — test-first red-green-refactor. A bug fix starts red on the unfixed code.
    - `sdlc-pr` — how to write a PR body.
    - `sdlc-update-readme` — keep README.md in sync with real changes only.
  - **Conversation**
    - `productivity-grilling` — interview the user about a plan, decision or idea, one question per turn.
      For a big idea it asks first whether to go one at a time or in rounds.
    - `productivity-grill-me` — user-typed alias for `productivity-grilling`.
  - **Setup and maintenance**
    - `moonlight-init` — set up an existing repo for the moonlight skills, without overwriting anything (see
      "Start on an existing project").
    - `moonlight-update` — update the installed plugin from its marketplace and report the version.
- **Agents** (`agents/`) — all SDLC, same `sdlc-` prefix as the skills.
  - `sdlc-ralph-implementer` — the mechanical worker `sdlc-ralph-implement` spawns per pass.
  - `sdlc-ralph-reviewer` — read-only code-review gate (security, dead code, over-engineering,
    config-vs-hardcoded, architecture fit, and regression tests that could not fail), reporting on the same
    Standards/Spec axes as `sdlc-standards-spec-review` and reusing its smell baseline. Runs as
    `sdlc-ralph-implement`'s Step 4.5 gate after implementation, before validation; blockers go back to the
    implementer.
  - `sdlc-spec-writer` — maintains `specs/<component>.md`, a living current-behavior doc (Gherkin scenarios).
    It runs after a plan's Definition-of-Done gate passes, from `sdlc-feature-analyst`'s wrap-up. `moonlight-init`
    also runs it as a baseline, with no plan, to write the first spec of each component.
  - `sdlc-uat-tester` — black-box PASS/FAIL/INCONCLUSIVE verifier with zero codebase access, driving the running
    app via a project-supplied instrument (CLI, HTTP call, probe script) — optional add-on, invoked from
    `sdlc-feature-analyst`'s Phase 4.5 only when a plan has a `## UAT verification` section.
- **Hooks** (`hooks/hooks.json`):
  - `block-git-commit-push.sh` (PreToolUse on Bash) — only the user commits or pushes. Also blocks
    `reset --hard`, `clean -f`, `branch -D`, `checkout .` and `restore .`.
  - `reminders.py` (SessionStart) — shows `plans/reminders.md` lines due within 3 days.
- **Starter** (`CLAUDE.md` at the plugin root) — the working practices that `moonlight-init` copies into a project.
  It is not loaded into the plugin's own sessions.

## Not in the plugin yet

These stay in this repo's `.claude/` and are not installed by the plugin:

- `.claude/skills/productivity-*` — conversation tools (handoff, retro, research,
  writing-for-agents, show-me, wait-what).
- `.claude/skills/helper-*` — one-off utilities (`helper-do-in-my-chrome`, `helper-sql`).
- `.claude/output-styles/talk-to-me.md` — short, blunt, plain-language replies.

## Develop the plugin

Test local edits without installing: `claude --plugin-dir .` from this repo. Check manifests with
`claude plugin validate .`. The plugin is developed with the plugin itself: install it from the local clone
(see Install) and use it in this repo.

## License

MIT, see [LICENSE](LICENSE). Material adapted from other MIT-licensed repos keeps their copyright lines in
`LICENSE`, and [docs/third-party.md](docs/third-party.md) lists each adaptation.

## Docs

- **[CLAUDE.md](CLAUDE.md)** — the starter set of working practices (planning, testing, git/deploy
  safety, knowledge capture). `moonlight-init` copies it into a project's `CLAUDE.md`; trim to what fits.
- **`docs/third-party.md`** — attribution for material adapted from Matt Pocock's skills and HumanLayer's `show-me` (both MIT).
- **`docs/skill-authoring.md`** — the Agent Skills spec convention, and where skills live in this repo.
- **`docs/patterns.md`** — heavier patterns seen elsewhere (a tiered plan-and-verify loop with black-box
  verification, a deploy-safety protocol, agent-loop design notes) that are pointers to their source repo, not copies.
