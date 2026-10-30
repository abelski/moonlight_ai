# Codebase research

Read-only map of this repo. Every claim cites a file or `file:line`. `(inferred)` marks what was not read directly.

## 1. What it is

`moonlight` is a Claude Code plugin, not an application. It ships an SDLC pipeline as markdown skills and agents
(brainstorm, plan with a cold review, checklist implementation with a review gate, TDD, triage, specs, PR bodies),
two hooks, a side-panel mod, one output style and two scripts, token report and plan session state (`README.md:5-8`,
`.claude-plugin/plugin.json`). The root `CLAUDE.md` is a starter template that `moonlight-init` copies into other
projects, and the plugin does not load it into its own sessions (`README.md:238-242`, `CLAUDE.md:3-6`).

## 2. Stack and entry points

- Runtime: markdown prompts run by Claude Code. The hooks and scripts need `python3` and `jq`; the side panel is a Claude Code mod on early-access function hooks (`README.md:21-24`).
- Plugin manifest: `.claude-plugin/plugin.json:1-5` (name, version `0.1.0`). Marketplace entry: `.claude-plugin/marketplace.json:1-12`, source `./`.
- Hook wiring: `hooks/hooks.json:3-24` (SessionStart runs `hooks/reminders.py`; PreToolUse on Bash runs `hooks/block-git-commit-push.sh`).
- User entry points (skills): `skills/sdlc-brainstorm/SKILL.md`, `skills/moonlight-fast/SKILL.md`, `skills/moonlight-calm/SKILL.md` (`README.md:40-48`). Setup entry: `skills/moonlight-init/SKILL.md`.
- Only runnable code: `hooks/block-git-commit-push.sh`, `hooks/reminders.py`, `scripts/token-report.py:180` (`main`, called at `:210`), `scripts/plan-state.py:107` (`main`, called at `:132`), `hooks/panel.tsx:122` (`register`), and `skills/sdlc-diagnosing-bugs/scripts/hitl-loop.template.sh`.

## 3. Layout

- `.claude-plugin/`: plugin and marketplace manifests, icon.
- `skills/`: 22 skills, one folder each with `SKILL.md`. Prefixes: `sdlc-*` pipeline, `moonlight-*` entry and setup, `productivity-*` conversation tools.
- `agents/`: 6 subagents, all named `sdlc-*` (`agents/sdlc-ralph-implementer.md`, `-ralph-reviewer`, `-spec-writer`, `-stand-in-product-owner`, `-stand-in-tech-lead`, `-uat-tester`).
- `hooks/`: `hooks.json` plus the two hook scripts, and `panel.tsx`, the side-panel mod that `hooks.json` names under `modules`.
- `output-styles/`: `talk-to-user.md`, forced on while the plugin is enabled (`output-styles/talk-to-user.md:5`).
- `scripts/`: `token-report.py` (token totals; `--plan` writes a plan's `## spendreport`) and `plan-state.py` (a plan's `## Session state` block), called by the entry-point skills, `sdlc-feature-analyst` and `sdlc-fix-issue-from-triage`.
- `docs/`: `skill-authoring.md`, `patterns.md`, `third-party.md`, `panel-spike.md` (the mod API facts the panel relies on).
- `test/`: `test_token_report.py` and `test_plan_state.py` (`python3 -m unittest discover -s test`), `panel.test.tsx` (`claude plugin test .`).
- `.claude/skills/`: repo-local `helper-do-in-my-chrome` and `helper-sql`, not shipped (`README.md:251-255`).
- Root: `CLAUDE.md` (starter template), `README.md`, `LICENSE`, `.gitignore`.

## 4. Main flows

1. **Feature, standard**: `skills/sdlc-brainstorm/SKILL.md` → `skills/sdlc-feature-analyst/SKILL.md` → `skills/sdlc-ralph-implement/SKILL.md` (→ `agents/sdlc-ralph-implementer.md`, `agents/sdlc-ralph-reviewer.md`, `skills/sdlc-tdd/SKILL.md`) → `agents/sdlc-spec-writer.md` → `scripts/token-report.py --plan` (`skills/sdlc-feature-analyst/SKILL.md:280-281`).
2. **Feature, light or unattended**: `skills/moonlight-fast/SKILL.md` or `skills/moonlight-calm/SKILL.md`, then the same implement and review chain. `moonlight-calm` also uses `agents/sdlc-stand-in-product-owner.md` and `agents/sdlc-stand-in-tech-lead.md` (`README.md:81-82`).
3. **Bug triage**: `skills/sdlc-triage/SKILL.md` → `skills/sdlc-fix-issue-from-triage/SKILL.md` → `skills/sdlc-ralph-implement/SKILL.md`. Commands come from `## Moonlight adapters` in the project's `CLAUDE.md` (`CLAUDE.md:142-156`).
4. **Onboard a repo**: `skills/moonlight-init/SKILL.md` (Steps 1-6, `:9-127`), which copies the root `CLAUDE.md` as the starter (`:83-85`).

## 5. Data

None. No database, models, schemas or migrations. State lives in markdown files in the target project: `plans/`, `specs/`, `plans/reminders.md` (`skills/moonlight-init/SKILL.md:66-70`).

## 6. Configuration and external services

- One environment variable is read by this repo's code: `CLAUDE_CODE_SESSION_ID`, the session id fallback in `scripts/plan-state.py:71-72` (checked `hooks/reminders.py`, `scripts/token-report.py`, `scripts/plan-state.py`, `hooks/block-git-commit-push.sh`, `hooks/panel.tsx`). `${CLAUDE_PLUGIN_ROOT}`, set by Claude Code, is expanded in `hooks/hooks.json:8,20`.
- `scripts/token-report.py:28-30` reads transcripts under `~/.claude/projects/`.
- Update source: `github.com/abelski/moonlight_ai` (`README.md:8`, `skills/moonlight-update/SKILL.md`).

## 7. Tests

`test/` holds tests for `scripts/token-report.py` (`test_token_report.py`), `scripts/plan-state.py` (`test_plan_state.py`) and `hooks/panel.tsx` (`panel.test.tsx`). The README runs them with `python3 -m unittest discover -s test` and `claude plugin test .` (`README.md:248`). There is still no runner config and no CI file (no `.github/`, `.gitlab-ci.yml`, `.pre-commit-config.yaml`, `.husky/`). The README also names `claude plugin validate .` to check the manifests (`README.md:247`).

## 8. Commands

`CLAUDE.md` has no `## Commands` section (init skipped it because the file exists). The README names `claude plugin validate .` (`README.md:247`), `claude --plugin-dir .` for local edits (`README.md:246`), and the tests: `python3 -m unittest discover -s test` and `claude plugin test .` (`README.md:248`). No lint, typecheck or build command exists.

## 9. Conventions

- Skill frontmatter: `name` equals the folder, a `description` of what and when (`docs/skill-authoring.md:31-45`; example `skills/moonlight-calm/SKILL.md:1-4`).
- Agents: frontmatter with `tools` and `model` (`agents/sdlc-spec-writer.md:1-6`).
- Namespacing: skills and agents are referenced as `moonlight:<name>` (`README.md:36-38`).
- User-only skills set `disable-model-invocation: true` (`skills/productivity-handoff/SKILL.md:5`).
- Hook errors: SessionStart hook swallows failures with `2>/dev/null || true` (`hooks/hooks.json:8`).
- Known-limit shortcuts get a comment (`hooks/block-git-commit-push.sh:10-13`).

## 10. Risks and gaps

- No CI. `test/` covers `scripts/token-report.py`, `scripts/plan-state.py` and `hooks/panel.tsx`; `hooks/reminders.py` and `hooks/block-git-commit-push.sh` have no tests. The git-guard is a regex (`hooks/block-git-commit-push.sh:14,21`) and its author notes it can be bypassed (`:10-13`).
- `hooks/reminders.py:9` builds the reminders path from `parents[2]` of the script file. When the plugin runs from its install folder, that is not the project folder (inferred: the script has no use of the current directory). If so, reminders never show in a project. Not run.
- `CLAUDE.md` describes itself as a template this repo need not obey (`CLAUDE.md:3-6`), but also holds repo-specific plugin rules (`CLAUDE.md:130-140`). Mixed role.
- `CLAUDE.md:69` mentions `temp_files/screenshots/`, while `CLAUDE.md:11` says scratch goes to `/tmp`. Two scratch conventions.
- Secrets: a regex scan for key, secret and token assignments in tracked files found none.

## 11. Open questions

- Does `hooks/reminders.py` find `plans/reminders.md` when run from the plugin install folder? The code says no; not run.
- Should this repo carry its own `CLAUDE.md` for working on the plugin, apart from the starter template? The code does not say.
