---
name: sdlc-standards-spec-review
description: "Review the changes since a fixed point (commit, branch, tag, or merge-base) along two axes: Standards (does the code follow this repo's documented coding standards plus a Fowler smell baseline?) and Spec (does the code match what the originating plan/idea/issue asked for?). Runs both reviews in parallel sub-agents and reports them side by side. Use when the user wants to review a branch, a PR, work-in-progress changes against its plan, or asks to \"review since X\" for standards or spec compliance. For bug-hunting use the built-in /code-review instead."
license: MIT
---

Adapted from Matt Pocock's `code-review` skill
(https://github.com/mattpocock/skills, `skills/engineering/code-review`, MIT, forked at
`c55ee46`). Renamed so it doesn't shadow Claude Code's built-in `/code-review` (a bug hunter —
a different job). Re-sync by hand against that commit.

Two-axis review of the diff between `HEAD` and a fixed point:

- **Standards**: does the code conform to this repo's documented coding standards?
- **Spec**: does the code faithfully implement the originating plan / idea / issue?

Both axes run as **parallel sub-agents** so they don't pollute each other's context, then this
skill aggregates their findings.

## Process

### 1. Pin the fixed point

Parse `$ARGUMENTS`: the fixed point (a commit SHA, branch name, tag, `main`, `HEAD~5`, etc.) and
optionally a spec path. No fixed point given → ask for it.

Capture the diff command once: `git diff <fixed-point>...HEAD` (three-dot, so the comparison is
against the merge-base). Also note the commit list via `git log <fixed-point>..HEAD --oneline`.
If the user wants uncommitted work included, use `git diff <fixed-point>` (two-arg, working tree)
and list untracked files from `git status --short`.

Confirm the fixed point resolves (`git rev-parse <fixed-point>`) and the diff is non-empty. A bad
ref or empty diff fails here, not inside two parallel sub-agents.

### 2. Identify the spec source

Look in this order:

1. A path the user passed as an argument.
2. A plan under `plans/` (or `plans/implemented/`, `plans/triage/`) matching the branch's
   `<N>-<slug>`, plus its idea file under `plans/ideas/`.
3. Issue references in commit messages (`#123`, `Closes #45`) — fetch them only if the project
   has a documented way to (e.g. the `sdlc-triage` skill's tracker setup).
4. A spec file under `docs/` or `specs/` matching the branch name or feature.
5. Nothing found → ask the user. If they say there isn't one, skip the Spec sub-agent and report
   "no spec available".

### 3. Identify the standards sources

Anything in the repo documenting how code should be written: `CLAUDE.md`, `CODING_STANDARDS.md`,
`CONTRIBUTING.md`, `docs/` conventions.

On top of those, the Standards axis always carries the **smell baseline** in
[references/smells.md](references/smells.md). The repo overrides it; every smell is a judgement
call, never a hard violation.

### 4. Spawn both sub-agents in parallel

**Standards sub-agent prompt** includes:

- The diff command and commit list.
- The standards-source files from step 3, **plus the full contents of `references/smells.md`**
  pasted in.
- The brief: "Report, per file/hunk where relevant, (a) every place the diff violates a
  documented standard: cite the standard (file + the rule); and (b) any baseline smell you spot:
  name it and quote the hunk. Distinguish hard violations from judgement calls: documented-
  standard breaches can be hard, but baseline smells are always judgement calls, and a
  documented repo standard overrides the baseline. Skip anything tooling enforces. Under 400
  words. Do not invoke any review skill or spawn additional agents: perform this review
  directly."

**Spec sub-agent prompt** includes:

- The diff command and commit list.
- The path or fetched contents of the spec.
- The brief: "Report: (a) requirements the spec asked for that are missing or partial; (b)
  behaviour in the diff that wasn't asked for (scope creep); (c) requirements that look
  implemented but where the implementation looks wrong. Quote the spec line for each finding.
  Under 400 words. Do not invoke any review skill or spawn additional agents: perform this review
  directly."

Give neither sub-agent your own reasoning about the change — file paths and commands only.

### 5. Aggregate and report

Present the two reports under `## Standards` and `## Spec` headings, verbatim or lightly cleaned.
Do **not** merge or rerank findings across axes.

End with a one-line summary: total findings per axis, and the worst issue _within each axis_ (if
any). Don't pick a single winner across axes.

## Why two axes

- Code that follows every standard but implements the wrong thing → **Standards pass, Spec fail.**
- Code that does exactly what the plan asked but breaks the project's conventions → **Spec pass,
  Standards fail.**

Reporting them separately stops one axis from masking the other.

## Gotchas

- **Recursive fan-out.** Upstream's sub-agent briefs didn't forbid delegation, so sub-agents
  could rediscover the skill and spawn more agents (reports of 50+). The "do not invoke … or spawn
  additional agents" line in both briefs is the fix — keep it.
- **Run it from a fresh session**, not the one that wrote the code: same context reviewing itself
  is confirmation bias.
- **`sdlc-ralph-reviewer` can't run this skill** (subagents have no `Agent` tool). It applies the same
  two axes inline and reads `references/smells.md` directly — edit the baseline there, once.
