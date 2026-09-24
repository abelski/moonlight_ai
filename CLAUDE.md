# CLAUDE.md — starter practices

Distilled from the CLAUDE.md files, skills, and agents across this machine's other repos. This is
a **template to copy into a new project and trim**, not a rulebook this repo itself must obey —
keep only what fits the project, drop the rest.

## Project layout

- Source code lives in `/src`.
- Tests live in `/test`.
- Scratch/temp files (intermediate output, one-off scripts, anything not meant to ship) go in
  `/tmp` — gitignored, never committed.
- Secrets and environment-specific config go in `.env` — gitignored, never committed, never
  hard-coded elsewhere (see the secrets rule under Safety & guardrails).

## Before making changes

- Plan before touching code, except for changes small enough that a plan would cost more than
  the change itself (a typo, a one-line fix with an obvious cause, a docstring tweak).
- If the harness has an `EnterPlanMode`/plan-mode tool, use it, then persist the approved plan to
  a repo-tracked `plans/NNNN-short-title.md` (zero-padded, incrementing) — plan-mode output alone
  often lives outside the repo and won't survive a session boundary.
- Every plan is a checklist (`- [ ] item`), not prose. Check items off (`- [x]`) live, during
  implementation — never in one batch at the end. A plan file is the source of truth for
  progress if a session is interrupted or resumed.
- Once a plan is fully done, move it to `plans/implemented/` (same filename) so active and
  finished plans don't mix.
- Keep the *what/why* of a feature (problem, scope, decisions) in its own idea file
  (`plans/ideas/`), separate from the plan's *how* — so reviewers and later sessions can check the
  plan against it.
- Have a fresh agent with none of the author's context review a plan before approval — give it
  only file paths, never a summary of your reasoning.
- Every change gets its own branch (`feat/<N>-<slug>`, `fix/<N>-<slug>`), created before the first
  code edit. Idea and plan files may be written on main; they carry into the branch.
- Ceremony should scale with the size and risk of the change, not apply uniformly. A one-file,
  no-contract-change fix doesn't need the same process as a schema migration.

## Making the change

- Smallest diff that achieves the goal. No drive-by refactors, no unrequested abstractions.
- Simple architecture: no new interface, factory, or config knob unless there's already a second
  concrete need for it.
- Ask before adding a new dependency, library, or external service.
- Extend via existing extension points (a registry, a plugin hook) instead of editing shared/core
  code for a single new case.
- Reuse existing patterns and files rather than inventing new ones — check what's already there
  before writing something new.
- Before changing a function/handler/endpoint's behavior, check who already depends on it (grep
  every caller). Prefer additive changes; if a breaking change is unavoidable, say so explicitly
  before making it.

## Testing & validation

- Write unit tests for new or modified logic.
- Add test coverage for every new feature and run the relevant suite(s) before calling it done.
- Never assert tests on exact LLM/AI-generated output text — assert on structured effects (tool
  calls, arguments, return shapes) instead; exact-text assertions break on harmless rewording.
- Post-implementation, verify end-to-end: run the tests, check logs, actually exercise the
  changed behavior — don't stop at "the diff looks right."
- Before starting a new dev server, check whether one is already running to avoid duplicate or
  stale processes.

## Safety & guardrails

- Never commit or push to git without explicit, in-session user consent — a plan calling for a
  push is not consent.
- Deploys, especially to production, are a separate, explicit, human-gated action — never bundled
  into a plan's own checklist or done on initiative because a step seemed related.
- Keep an explicit list (in this file, or a linked doc) of irreversible/costly operations that
  always need a fresh explicit request: prod deploy, IAM/permission changes, paid API calls,
  destructive deletes. Safer, reversible tiers can proceed unprompted.
- Automating a browser or external tool: connect to the user's already-authenticated session
  (e.g. an existing Chrome instance) rather than spinning up a fresh one and re-authenticating —
  and never close a browser session you didn't open.
- If automation hits a login/auth screen, stop and ask the user to log in manually. Never enter
  credentials on their behalf.
- Read-only by default against systems you don't own: never click/submit/mutate data in an
  external system via automation without being asked — stop and report instead.
- Secrets never go through ad-hoc code: read them via one dedicated module/function, never
  hard-coded, never logged, and never duplicated inline at each call site.
- A destructive local operation (deleting generated files, resetting state) always lists what
  will be affected and waits for explicit confirmation before acting.
- Output files get identifying names (date, subject, run id) — never generic names that silently
  overwrite the last run's output.

## Documentation & knowledge capture

- If a bug takes real time to diagnose, or something about the environment/API/server behaves
  non-obviously, write it down immediately in a durable knowledge file (`knowledge/`,
  `documentation/`, or similar) — don't let it get re-learned by the next session.
- Keep `README.md` current as part of "done," not a follow-up task — update it for new/removed
  setup steps, changed commands, or architecture changes; skip it for internal refactors with no
  user-facing effect.
- Research, findings, and architecture-decision records belong in a tracked folder (`documents/`,
  `documentation/`), not only in chat — future sessions can't read the conversation.
- Give features/changes a sequential number for traceability across plans, commits, and a
  changelog, if the project is long-lived enough to benefit from it.

## Skill / command / agent authoring

- Any command, skill, or agent created for this project lives in this project's own `.claude/`
  directory (`.claude/commands/`, `.claude/skills/`, `.claude/agents/`) — project scope, not the
  user's global `~/.claude/`. It ships with the repo and works for anyone who clones it.
- See [docs/skill-authoring.md](docs/skill-authoring.md) for the convention this machine's repos
  converged on (Agent Skills spec: frontmatter shape, directory layout, size limits).

## Useful patterns not copied here verbatim

See [docs/patterns.md](docs/patterns.md) — heavier architectural patterns observed elsewhere on
this machine. Not generic enough to drop in as-is; worth reading before building something
similar from scratch.
