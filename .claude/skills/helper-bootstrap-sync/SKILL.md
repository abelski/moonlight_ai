---
name: helper-bootstrap-sync
description: Check github.com/abelski/moonlight_ai for skills, agents, hooks, and output-styles, then let the user pick which ones to pull into this project's .claude/ directory. Use when the user asks to sync/update/pull from moonlight_ai (formerly claude_bootstrap), or wants to check for new bootstrap skills/agents/workflows.
---

Pull selected parts of `https://github.com/abelski/moonlight_ai` into this repo's `.claude/`.
Runs fresh every time — the source repo changes over time, so never rely on a cached list.

## 1. Fetch the current source tree

```bash
DEFAULT_BRANCH=$(curl -sL https://api.github.com/repos/abelski/moonlight_ai | python3 -c "import sys,json; print(json.load(sys.stdin)['default_branch'])")
curl -sL "https://api.github.com/repos/abelski/moonlight_ai/git/trees/$DEFAULT_BRANCH?recursive=1"
```

Keep only blobs under these prefixes — these are the pullable categories:

| Prefix | Category | Local target |
|---|---|---|
| `.claude/agents/*.md` | Agent | `.claude/agents/<file>` |
| `.claude/skills/<name>/SKILL.md` (+ sibling files in that skill dir) | Skill | `.claude/skills/<name>/` |
| `.claude/hooks/*` | Hook | `.claude/hooks/<file>` (keep executable bit) |
| `.claude/output-styles/*.md` | Output style | `.claude/output-styles/<file>` |
| `.claude/commands/*.md` | Command | `.claude/commands/<file>` |

Ignore `.claude/settings.json`, root `CLAUDE.md`, `README.md`, and `docs/*` — those are the
template repo's own config/docs, not things to drop into a downstream project. If the user
specifically asks about one of those, handle it separately by hand; don't include it in the pull list.

## 2. Build the pick-list

For each candidate file, fetch its raw content to get a one-line description:

```bash
curl -s "https://raw.githubusercontent.com/abelski/moonlight_ai/$DEFAULT_BRANCH/<path>"
```

- Skill/agent/output-style files: read the frontmatter `description:` field.
- Hooks (shell scripts): first comment line, or just the filename if there isn't one.
- Commands (plain `.md`, no frontmatter): first non-empty line.

Check whether each local target path already exists in this repo, and mark it accordingly.

**Local copies may be adapted.** If a local file differs from the template, it may carry
project-specific edits — diff the template's own changes and port them by hand rather than
overwriting wholesale.

Print a numbered list grouped by category, e.g.:

```
Agents
  1. ralph-reviewer — <description>  [new]
  2. spec-writer — <description>  [new]

Skills
  3. update-readme — <description>  [new]
  4. triage — <description>  [already present locally — pulling will overwrite]

Hooks
  5. block-git-commit-push.sh — <description>  [new]

Output styles
  6. talk-to-me.md — <description>  [already present locally, identical content]
```

Skip printing (or clearly de-emphasize) any item whose content is byte-identical to what's
already local — nothing to pull there.

## 3. Ask the user what to pull

The item count is unbounded, so don't force this through `AskUserQuestion`'s 4-option cap.
Just ask in plain text: "Which numbers do you want to pull? (comma-separated, `all`, or `none`)"

## 4. Pull the selected items

For each selected item:
- Fetch raw content from `raw.githubusercontent.com/abelski/moonlight_ai/$DEFAULT_BRANCH/<path>`.
- For a skill directory, also fetch any sibling files under that same `.claude/skills/<name>/` prefix
  from the tree (not just `SKILL.md`) so bundled resources come along.
- If the local target already exists and differs, show a short diff and confirm before overwriting
  (one confirmation covering all conflicting items is fine — don't ask per file).
- Write the file(s). For hooks, `chmod +x` the written file.

Never touch `.claude/settings.json` automatically — if the source repo's hook/permission config
looks relevant, print the relevant snippet and tell the user to merge it by hand (this project's
settings.json has project-specific permissions that a blind overwrite would clobber).

## 5. Report

List what was written or updated. Don't `git add` or commit — leave that to the user, per this
project's rule of never committing without an explicit ask.
