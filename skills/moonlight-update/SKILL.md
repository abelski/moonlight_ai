---
name: moonlight-update
description: Update the installed moonlight plugin from its marketplace (github.com/abelski/moonlight_ai) and report the version change. Use when the user asks to update, sync or upgrade moonlight, or wants to know whether new moonlight skills, agents or hooks are available.
---

Update the installed `moonlight` plugin. Nothing is copied into the project any more: the plugin
is installed once and updated in place, so there is no file-by-file pick-list.

## 1. Check what is installed

```bash
claude plugin list
```

Find the `moonlight@moonlight` row and note its version.

- If it is missing, stop. Ask the user before installing, because installing changes their global
  plugin configuration:
  `claude plugin marketplace add abelski/moonlight_ai` then `claude plugin install moonlight@moonlight`.

## 2. Refresh the marketplace and update

```bash
claude plugin marketplace update moonlight
claude plugin update moonlight@moonlight
```

## 3. Report

- Show the old and new version.
- Tell the user to restart Claude Code. The CLI reports that an update applies only after a restart.
- Do not `git add` or commit anything. Leave that to the user.
