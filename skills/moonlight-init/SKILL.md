---
name: moonlight-init
description: Set up an existing (brownfield) repo for the moonlight SDLC skills without overwriting anything. Surveys the code for its test, lint and build commands, researches the codebase into a tracked map (layout, entry points, flows, tests, risks), then creates the plans folders, reminders file, specs folder and a CLAUDE.md from the starter where they are missing. Use when the user wants to start moonlight on a project that already has code, or asks to init or onboard a repo.
---

Set up the repo in `$ARGUMENTS` (default: the current directory) so the `moonlight:` skills can run on it.
The setup is additive: nothing is overwritten, nothing is deleted, nothing is committed.

## Step 1 — Check the repo

- Run `git rev-parse --is-inside-work-tree`. If it is not a git repository, stop and ask the user to run
  `git init` first: the SDLC flow creates branches.
- Run `git status --short`. If there are uncommitted changes, list them and say that init does not touch them.
- Find the main branch: `git symbolic-ref --short refs/remotes/origin/HEAD` (drop the `origin/` prefix). If
  that fails, use `main` if it exists, else `master`. If it is still unclear, ask.

## Step 2 — Survey the code

Read these; do not guess.

- Manifests and build files: `package.json`, `pyproject.toml`, `setup.cfg`, `requirements*.txt`, `pom.xml`,
  `build.gradle*`, `go.mod`, `Cargo.toml`, `Gemfile`, `composer.json`, `Makefile`.
- Command sources: `scripts` in `package.json`, Makefile targets, CI files (`.gitlab-ci.yml`,
  `.github/workflows/*.yml`), `.pre-commit-config.yaml`, `.husky/`.
- Existing docs and layout: `README.md`, `AGENTS.md`, `CLAUDE.md`, `docs/`, `documentation/`, `specs/`,
  `CHANGELOG.md`, `plans/`.
- Secrets hygiene: whether `.gitignore` ignores `.env`.

Keep the survey in your notes: the languages found, and the test, lint, typecheck and build commands with
the file each came from. Note what is missing (for example, no test command at all).

## Step 3 — Research the codebase

Read-only. The goal is a map that a new agent can read before it greps the repo. The planner and the cold
plan reviewer use it, so every claim needs a reference.

- Research folder: `documentation/` if the project has that folder, otherwise `docs/`. The file is
  `codebase-research.md` in it.
- Small repo (roughly under 200 source files): do the research yourself with Glob, Grep and targeted reads.
- Larger repo: spawn one `Explore` subagent with "very thorough", and give it the questions of the sections
  below. Write the file from its report, then check two or three of its file references with Grep before you trust them.

Write these sections, in this order:

1. **What it is.** One paragraph, in your own words, from the README and the code.
2. **Stack and entry points.** Runtime, framework, entry files, how the app starts. Each with `file:line`.
3. **Layout.** Each top-level folder, one line each.
4. **Main flows.** Two to four user-visible flows, each as the list of files it touches, in order.
5. **Data.** Where models, schemas and migrations live, and which database engine.
6. **Configuration and external services.** Environment variable names and the code that reads them. Never
   print values, and never open `.env`.
7. **Tests.** Where they live, how to run them, which engine they use, what they cover and what they miss.
8. **Commands.** A pointer to the `## Commands` section of CLAUDE.md. Do not copy it.
9. **Conventions.** Naming, error handling, module boundaries. One example with a `file:line` for each.
10. **Risks and gaps.** Untested areas, very large files, duplicated logic, stale docs, and secrets found in
    tracked files (name the file and the key only, never the value).
11. **Open questions.** What the code could not settle.

Rules for the file: every claim cites `file` or `file:line`. Anything you inferred rather than read is marked
`(inferred)`. Describe what the code does; do not recommend changes.

## Step 4 — Propose the setup

Show one table. For each item, say whether init creates it, skips it because it exists, or leaves it to the user.

| # | Item | Action |
|---|---|---|
| 1 | `CLAUDE.md` | create from the starter if missing; otherwise leave it and list the starter sections it lacks |
| 2 | `plans/` folders: `ideas/`, `improvements/active/`, `improvements/implemented/`, `triage/active/`, `triage/implemented/`, `triage/hold/` | create each with a `.gitkeep`, if missing |
| 3 | `plans/reminders.md` | create with a one-line header, if missing |
| 4 | `specs/` | create the folder, if missing; then offer one spec per component (Step 5b) |
| 5 | `.gitignore` | add the lines that are missing: `.env`, plus the usual build-output and dependency folders for the detected stack (`node_modules/` for Node, `.venv/` and `__pycache__/` for Python, `target/` for Maven and Cargo, `dist/` or `build/` where the build writes there) |
| 6 | `documentation/codebase-research.md` or `docs/codebase-research.md` | create from Step 3, if missing |

Show a short summary of the research next to the table: the stack, the entry points, and the top three risks.

Ask once with `AskUserQuestion`: "Apply this setup?" Options: "Apply", "Pick items", "Cancel". For "Pick items",
ask in plain text which numbers to apply.

Do not create a changelog. The feature skills append to one only when the project keeps it; mention it in the report.

## Step 5 — Apply

- Never overwrite or delete. A target that exists is skipped, and the report names it.
- `CLAUDE.md`: copy the starter, which is the `CLAUDE.md` at the plugin root, two levels above this skill's
  folder (`skills/moonlight-init/` → plugin root). Then:
  - set the title to `# CLAUDE.md — <project name>`, and replace the starter's intro (the "Distilled from…"
    paragraph and the template note) with one line on what this project is, taken from the README;
  - in `## Project layout`, keep the lines that match this repo and remove the rest;
  - remove the sections that describe the template repo itself: `## Skill / command / agent authoring` and
    `## Useful patterns not copied here verbatim`;
  - add a `## Commands` section listing each command from Step 2 with its source file;
  - add the main branch name under `## Before making changes`;
  - add one line under `## Project layout` pointing to the research file.
  Tell the user to trim the rest to what fits.
- `.gitignore`: append only the lines from Step 4 row 5 that are not already there, one per line.
- Create the folders, the reminders file, `specs/` and the research file from Step 4.

## Step 5b — Specs (optional)

Run this only if `specs/` exists and the research file names components. A component is a top-level folder
that holds source files, under the source root (for example `src/*`). Skip tests, docs and config folders.

List the components with a rough file count for each. Leave out any component that already has
`specs/<component>.md`: init never rewrites an existing spec. Then ask once with `AskUserQuestion`: "Write a spec
for each component now?" Options: "All", "Pick components", "Later".

Before asking, say that each component is one `moonlight:sdlc-spec-writer` run, and that each run reads the
whole component. On a large repo, suggest "Pick components".

For each chosen component, run one `Agent(subagent_type: "moonlight:sdlc-spec-writer")` at a time. The prompt gives
the target `specs/<component>.md`, the component folder, and the plan path `none` (a baseline run, no plan). After
each run, check the file: exactly the two sections the agent defines, no `- [ ]` items, no dates, no plan references.
Then report it.

## Step 6 — Report

- List what was created, what was skipped, and what the user must decide.
- Next steps: the user reviews the research file and commits the setup (`git add -A && git commit -m "chore:
  set up moonlight"`), then runs `/moonlight:sdlc-brainstorm <first change>`. The code has no plans yet, so the
  precedent search will find nothing. That is expected.
- The planner copies commands from `## Commands` into each plan's Validation and Definition of Done.

## Rules

- Never commit, push, stash or reset.
- Never install dependencies, and never run the project's build or tests during init. The survey and the research
  read files only.
- Keep the setup minimal. The other skills create whatever else they need the first time they run.
