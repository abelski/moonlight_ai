# moonlight

<img src=".claude-plugin/icon.png" alt="moonlight logo" width="160">

A Claude Code plugin with our SDLC pipeline: from an idea to a reviewed, tested branch, with a few
safety hooks. Install it once, update it in place, and stop copying files between repos.

- Repo: `github.com/abelski/moonlight_ai`
- License: MIT, see [LICENSE](LICENSE)

## Quick start

```bash
claude plugin marketplace add abelski/moonlight_ai
claude plugin install moonlight@moonlight
```

Then, in an existing project, run `/moonlight:moonlight-init` once. For a new project, see
[Start a new project](#start-a-new-project). For a new feature, pick an [entry point](#entry-points).

Requirements: `jq` (the git-safety hook reads its input with it) and `python3` (the reminders hook, the session state
and the spend report). The side panel is a Claude Code mod, built on early-access function hooks and checked on Claude
Code 2.1.314. It draws in the terminal only, and Claude Code may ask you once to enable it. Without it, every flow still
works.

## Install and update

| Task | Command |
|---|---|
| Install from GitHub | `claude plugin marketplace add abelski/moonlight_ai` and `claude plugin install moonlight@moonlight` |
| Install from a local clone | `claude plugin marketplace add /path/to/moonlight_ai` and `claude plugin install moonlight@moonlight` |
| Update | `claude plugin update moonlight@moonlight`, or ask Claude to run `moonlight-update` |

Restart Claude Code after an update.

Every skill and agent is namespaced `moonlight:<name>`, for example `moonlight:sdlc-feature-analyst`.
Reference them the same way from other skills: `Skill(skill: "moonlight:<name>")` and
`subagent_type: "moonlight:<name>"`. Bare names do not resolve.

## Entry points

Three ways in. They cover the same steps. They differ in how much you take part.

| Entry point | You take part in | Start with |
|---|---|---|
| `/moonlight:sdlc-brainstorm` (standard) | grilling of the idea, plan review, following the implementation, acceptance | an idea |
| `/moonlight:moonlight-fast <requirement>` | grilling of the idea, plan review, acceptance | a requirement text |
| `/moonlight:moonlight-calm <requirement>` | the requirement, then acceptance | a requirement text |

### The phases

The feature flows cover these steps. Names and order differ a little per flow, and code review runs inside Implementation:

1. **Idea**: what and why.
2. **Design**: the plan, the proposed spec change, and a review of the plan.
3. **Implementation**: TDD, on a feature branch.
4. **Code review**.
5. **Validation and acceptance**.
6. **Documentation and specs**.
7. **Spend report**: the token totals of the task, written into the plan as `## spendreport`.
8. **Close**.

The bug flow (`sdlc-fix-issue-from-triage`) has its own steps, and writes the spend report too, before it resolves the
issue in the tracker.

### Session state and spend report

While a flow runs, the plan file holds a `## Session state` block: a fenced `json` block with the flow, the current
phase, each phase's status (`pending`, `running`, `waiting`, `blocked`, `done`), who waits (`you` or nobody), the
session ids with their start times, the branch and the idea file. No token numbers. The flows write it with
`scripts/plan-state.py` (`init` once the plan exists, `phase` at the start of each phase). A clean session given the plan
reads the block and continues from the recorded phase.

At the end, `scripts/token-report.py --plan <plan>` counts every session in the block from the plan's `started_at`,
subagents included, and writes the plan's `## spendreport` section: messages, input, cache writes, cache reads, output
and the billable total. Nothing is printed to chat. The count covers everything in those sessions since `started_at`,
also unrelated work done in the same session.

### What `moonlight-calm` does on its own

`moonlight-calm` asks you nothing until the end. Two stand-in agents make the decisions instead:
`sdlc-stand-in-product-owner` answers open points, and `sdlc-stand-in-tech-lead` reviews the plan.
Every decision goes into the plan's `## Decisions` section, with its source and confidence.

The run stops and asks you only when:

- the working tree is not clean at the start,
- a stand-in is not confident (`low`),
- a flag is raised: `security`, `auth`, `data-migration`, `breaking-change` or `public-api`,
- the plan has more than 12 checklist items,
- a review asks for changes twice in a row,
- the implementation is blocked,
- a UAT section fails,
- or the change is ready for your acceptance.

Commits and merges stay with you in every flow. Claude creates the feature branch and never commits.

## Start on an existing project

Run `moonlight-init` once in the repo. It needs a git repository: without one, it stops and asks you to run
`git init`. It works in this order:

1. It surveys the code for the test, lint and build commands, and notes what is missing.
2. It researches the codebase into `docs/codebase-research.md` (or `documentation/codebase-research.md`
   if that folder exists). The file maps the code with `file:line` references, and the brainstorm and
   planning skills read it first.
3. It shows one table of what it will create, and asks once.
4. It applies the table. It creates `CLAUDE.md` from the starter, the `plans/` folders, `plans/reminders.md`,
   `specs/`, and the `.gitignore` lines for the detected stack.
5. If you choose, it writes one spec per component under `specs/`. Each spec is one agent run, so pick
   components on large repos.

Existing files are skipped. Nothing is committed: review the files, then commit them yourself.

Headless runs (`claude -p`) need `--add-dir <plugin folder>`, because the starter `CLAUDE.md` lives in
the plugin folder. An interactive session asks once instead.

## Start a new project

`moonlight-init` is built for a repo that already has code. For a new project:

1. Create the folder, run `git init`, and write the first code.
2. Commit it, then run `/moonlight:moonlight-init` as in [Start on an existing project](#start-on-an-existing-project).
3. Start the first feature with an [entry point](#entry-points).

## Adapters

The triage skills need three things from the project: where the issues live, how to close one, and whether closing one notifies the reporter. The
project says so in a `## Moonlight adapters` section of its `CLAUDE.md`, one `Key: value` line each:

| Key | Meaning |
|---|---|
| `Triage source` | A read-only command that prints the open issues as a JSON array. |
| `Resolve in tracker` | A command that takes one issue id and marks it resolved. It runs only after you confirm. |
| `Notify on resolve` | `yes` if the resolve command notifies the reporter, `no` if nothing does. |

If a key is missing or set to `(not set)`, the skill asks you instead of guessing a command. Commands read
secrets from the environment or `.env`. The section names variables, never values.

## Adapt it to your project

Do not copy or edit plugin files. Skills are namespaced `moonlight:<name>`, so a copy in `.claude/skills/` does not
replace the plugin skill, and a plugin update never reaches it. A project changes the plugin from its own files, in
four layers. Use the first one that works.

| Layer | Where | Use it for |
|---|---|---|
| Values | `## Commands` and `## Moonlight adapters` in `CLAUDE.md` | The test, lint and build commands, and the issue tracker. |
| Rules | the rest of `CLAUDE.md` | Rules the project never breaks, for example "UI changes are checked in RU and EN at 375px". The planner copies them into each plan's `### Standing constraints`. |
| Gates | hooks in the project's `.claude/settings.json` | "Never" rules, such as blocking a production deploy command. A gate is code, not a sentence in `CLAUDE.md`. |
| Wrappers | a project skill with its own name | A different order of steps. It calls `Skill(skill: "moonlight:<name>")` and adds steps before or after. |

Fixed, the project cannot change them:

- Commit and push are always the user's. The git-safety hook enforces it.
- The layout and file names under `plans/`. The skills read and write them.

Last resort: copy a skill under another name, note the plugin version it came from, and merge later changes yourself.

## Skills

### Feature pipeline

| Skill | What it does |
|---|---|
| `sdlc-brainstorm` | First step of a feature. Finds precedents, grills you, writes the idea file with a `## Proposed spec`. On confirm, adds the success check to `plans/reminders.md`. |
| `sdlc-feature-analyst` | Turns an idea or a raw request into a plan. A fresh agent reviews the plan, you approve it, then it hands off to `sdlc-ralph-implement`. The spec gate runs at close-out. |
| `sdlc-ralph-implement` | Runs a checklist plan to the end: implement, review and validate, repeat until the round is clean or the retry budget runs out. Resumable. |
| `sdlc-tdd` | Test-first red-green loop. A bug fix starts red on the unfixed code. |
| `sdlc-standards-spec-review` | Reviews a diff on two axes, standards and spec, in parallel sub-agents. A fork of Matt Pocock's `code-review` (MIT). |
| `sdlc-diagnosing-bugs` | Finds the cause of a hard bug or a performance regression before any fix. |
| `sdlc-pr` | Writes a PR body. |
| `sdlc-update-readme` | Keeps README.md in sync with real changes only. |

### Bug pipeline

| Skill | What it does |
|---|---|
| `sdlc-triage` | Fetches unresolved issues through `Triage source`, filters out spam and test noise, and drafts a bugfix plan per confirmed issue into `plans/triage/active/`. |
| `sdlc-fix-issue-from-triage` | Reproduces the symptom, fixes it through `sdlc-ralph-implement`, checks that the regression test fails on the unfixed code, then closes the issue through `Resolve in tracker` after you confirm. |

### Conversation and setup

| Skill | What it does |
|---|---|
| `productivity-grilling` | Interviews you about a plan, decision or idea, one question per turn. For a big idea it asks first: one at a time, or in rounds. |
| `productivity-grill-me` | Your alias for `productivity-grilling`. Only you can run it. |
| `productivity-handoff` | Writes a handoff document so a fresh agent can pick up the work. Only you can run it. |
| `productivity-research` | Investigates a question against high-trust primary sources and saves the findings as a Markdown file in the repo. |
| `productivity-retro` | Runs a retrospective on a coding session. Only you can run it. |
| `productivity-show-me` | Explains the current topic visually, with concise diagrams and focused HTML artifacts. Only you can run it. |
| `productivity-wait-what` | Re-pitches the last message in plain terms when it did not land. Only you can run it. |
| `productivity-writing-for-agents` | Guidance for writing documents that an agent reads: skills, `AGENTS.md`, `CLAUDE.md`. |
| `moonlight-init` | Sets up an existing repo. See [Start on an existing project](#start-on-an-existing-project). |
| `moonlight-update` | Updates the installed plugin from its marketplace and reports the version. |

## Agents

Agents run inside skills. You do not call them directly.

| Agent | Role |
|---|---|
| `sdlc-ralph-implementer` | Does one pass of a checklist plan for `sdlc-ralph-implement`. Writes the failing test first. |
| `sdlc-ralph-reviewer` | Read-only review gate after each implementation pass. Checks security, dead code, over-engineering and regression tests that could not fail. |
| `sdlc-spec-writer` | Writes `specs/<component>.md`, a Gherkin description of what a component does now. |
| `sdlc-uat-tester` | Black-box tester with no codebase access. Runs only when a plan has a `## UAT verification` section. |
| `sdlc-stand-in-product-owner` | Answers open questions in `moonlight-calm`. Returns an answer, a confidence and flags. |
| `sdlc-stand-in-tech-lead` | Reviews a plan in `moonlight-calm`. Approves it, or returns blockers. |

## Hooks

| Hook | Event | What it does |
|---|---|---|
| `block-git-commit-push.sh` | PreToolUse on Bash | Blocks `git commit` and `git push` from Claude, and the destructive commands `reset --hard`, `clean -f`, `branch -D`, `checkout .` and `restore .`. |
| `reminders.py` | SessionStart | Shows the lines in `plans/reminders.md` that are due within 3 days. |
| `panel.tsx` | Mod (function hooks) | The side panel, below. |

### Side panel

The panel opens by itself in a terminal session while a plan in `plans/improvements/active/` or `plans/triage/active/`
holds a `## Session state` block; the newest such plan wins. It shows the flow and the time since `started_at`, each
phase with its status, a `you` mark on the phase that waits for you, the tokens of each subagent, and a running total
split into input, cache and output. Phases redraw every few seconds; tokens every 30 seconds and when a turn ends.

- `/moonlight-panel` hides it and brings it back. Closing it with its close mark hides it too.
- On a narrow terminal (under 144 columns) Claude Code holds the pane back until there is room, or until you run
  `/moonlight-panel`.
- It closes when the plan moves to `implemented/`, or when the plan is `status: done` and its flow reached the last
  phase.

What was checked about the mod API, and what was not, is in [docs/panel-spike.md](docs/panel-spike.md).

## Output style

`talk-to-user` replies in short, plain words: the point first, short lines, and the facts kept exact. It is on by
default while the plugin is enabled, and it overrides the output style you pick with `/output-style`. Disable the
plugin to turn it off. It keeps Claude Code's coding instructions.

## Starter CLAUDE.md

`CLAUDE.md` at the plugin root holds the working practices that `moonlight-init` copies into a project:
planning, testing, git and deploy safety, and knowledge capture. Copy what fits; trim the rest. The plugin
itself does not load this file into its own sessions.

## Develop the plugin

- Test local edits without installing: `claude --plugin-dir .` from this repo.
- Check the manifests: `claude plugin validate .`.
- Run the tests: `python3 -m unittest discover -s test` (the scripts) and `claude plugin test .` (the panel).
- Use the plugin in this repo as well: install it from the local clone (see [Install and update](#install-and-update)).

## Not in the plugin yet

These stay in this repo's `.claude/` folder and are not installed by the plugin:

- `.claude/skills/helper-*`: `helper-do-in-my-chrome` and `helper-sql`.

## Docs

| File | What it is |
|---|---|
| [CLAUDE.md](CLAUDE.md) | The starter set of working practices. |
| [docs/third-party.md](docs/third-party.md) | Attribution for material adapted from Matt Pocock's skills and HumanLayer's `show-me`. Both MIT. |
| [docs/skill-authoring.md](docs/skill-authoring.md) | The Agent Skills convention, and where skills live in this repo. |
| [docs/patterns.md](docs/patterns.md) | Heavier patterns seen elsewhere, as pointers to their source. |
| [docs/panel-spike.md](docs/panel-spike.md) | What the side panel relies on in the mod API, and what is still unchecked. |
