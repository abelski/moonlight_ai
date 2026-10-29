---
name: sdlc-update-readme
description: Update README.md after key decisions or architecture changes in this project.
---

Review recent changes and update README.md to reflect them.

1. **Identify what changed** — read the current README.md and the files affected by the recent
   change to understand what is now out of date or missing.

2. **Determine if an update is warranted** — only update for:
   - New or removed setup steps
   - Changed commands (script names, flags, paths)
   - Architecture changes (new files, new environments, new workflow)
   - Key decisions that affect how someone would use the project

   Do NOT update for: minor wording tweaks, internal refactors with no user-facing impact, or
   changes already reflected accurately in the README.

3. **Edit README.md** — make the minimum change needed. Keep the README concise and user-facing.
   Do not add implementation details that belong in CLAUDE.md or a design doc.

4. **Report** — briefly summarise what was updated and why.
