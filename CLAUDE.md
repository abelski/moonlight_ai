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
  a repo-tracked `plans/improvements/active/plan_<N>_<slug>.md` (bugfixes: `plans/triage/active/`) —
  plan-mode output alone often lives outside the repo and won't survive a session boundary.
- Every plan is a checklist (`- [ ] item`), not prose. Check items off (`- [x]`) live, during
  implementation — never in one batch at the end. A plan file is the source of truth for
  progress if a session is interrupted or resumed.
- Once a plan is fully done, move it to `plans/improvements/implemented/` (same filename; bugfixes go
  to `plans/triage/implemented/`) so active and finished plans don't mix.
- Finding a new issue or improvement mid-work is not a reason to fold it in silently or go quiet:
  stop and ask whether it becomes a new plan or extends the current one.
- Dated follow-ups ("check back in 2 weeks", manual rollout step) go in `plans/reminders.md` as
  `- YYYY-MM-DD — what to do`. The moonlight SessionStart hook surfaces lines due within 3 days —
  mention them to the user, delete a line when done.
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
- Say where tests differ from production (database engine, data, config). When a change touches
  constraints, foreign keys or queries, test on the production engine, or state the gap in the plan.
- Judge data-heavy work (queries, imports) by database round trips, not by local wall time.
- A "must always / must never X" requirement for an AI agent is a code gate (callback, validator),
  not a sentence in the prompt. Prose owns wording and tone; code owns invariants. Try prose at
  most once — if a check still fails, convert it to a guard.
- Any change a user sees ships with evidence screenshots (every state: empty, populated, error;
  desktop and 375px; every language) — drive them with Playwright against a local server with the
  API mocked, look at them yourself, and save under `temp_files/screenshots/<plan-name>/`. Mock any
  endpoint whose value differs locally from production.
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
- A production write that needs credentials is the user's step: hand over an import file or script,
  and do not run it yourself.
- Anything a person must judge by their senses (audio, how a screen feels) goes to the user: play or
  show the candidates and ask. Never claim that something sounds or looks right.
- An operation that runs longer than about a minute reports progress as it goes (counts), not one line
  when it ends.

## Documentation & knowledge capture

- If a bug takes real time to diagnose, or something about the environment/API/server behaves
  non-obviously, write it down immediately in a durable knowledge file (`knowledge/`,
  `documentation/`, or similar) — don't let it get re-learned by the next session.
- Document architecture decisions too, not just gotchas: when you pick one approach over a
  plausible alternative for a non-obvious reason (tradeoff, hosting/DB/auth constraint, rejected
  simpler option), write the decision and its "why" next to the related feature.
- Specs stay current: a change in behavior updates the matching `specs/<component>.md` in the same
  change. A spec that lags the code is a bug.
- When a change costs money (paid API, bigger instance, new managed service), say so before making
  it — with an estimate and the cheaper alternative. Never let a service bill while idle.
- Keep `README.md` current as part of "done," not a follow-up task — update it for new/removed
  setup steps, changed commands, or architecture changes; skip it for internal refactors with no
  user-facing effect.
- Write repo files in English — plans, ideas, specs, docs, changelog, reminders — even when the
  conversation is in another language. Use another language only for project content that needs it:
  UI copy, data files, translated articles.
- Research, findings, and architecture-decision records belong in a tracked folder (`documents/`,
  `documentation/`), not only in chat — future sessions can't read the conversation.
- Give features/changes a sequential number for traceability across plans, commits, and a
  changelog, if the project is long-lived enough to benefit from it.

## Skill / command / agent authoring

- Skills, agents and hooks shipped by this repo live in the moonlight plugin folders at the root:
  `skills/<name>/SKILL.md`, `agents/<name>.md`, `hooks/hooks.json`. They ship with the plugin and are
  namespaced `moonlight:<name>`, so reference them that way: `Skill(skill: "moonlight:<name>")` and
  `subagent_type: "moonlight:<name>"`. Bare names do not resolve.
- Personal conversation tools that are not in the plugin yet stay in `.claude/skills/` (repo-local).
- Plugin manifests live in `.claude-plugin/`. Check a change with `claude plugin validate .` and
  `claude --plugin-dir .`.
- See [docs/skill-authoring.md](docs/skill-authoring.md) for the convention this machine's repos
  converged on (Agent Skills spec: frontmatter shape, directory layout, size limits).

## Moonlight adapters

Project-specific commands for the triage skills. One `Key: value` line each. A key that is missing or
`(not set)` makes the skill stop and ask. Never guess a command.

- Triage source: (not set)
- Resolve in tracker: (not set)
- Notify on resolve: (not set)

- `Triage source`: a read-only command that prints the open issues as a JSON array. Each item has `id`,
  `title`, `description`, `reported_at` and `status`.
- `Resolve in tracker`: a command that takes one issue id and marks it resolved. It runs only after the user
  confirms.
- `Notify on resolve`: `yes` if the resolve command already notifies the reporter, `no` if nothing does.
- Commands read secrets from the environment or `.env`. Write variable names here, never values.

## Useful patterns not copied here verbatim

See [docs/patterns.md](docs/patterns.md) — heavier architectural patterns observed elsewhere on
this machine. Not generic enough to drop in as-is; worth reading before building something
similar from scratch.
