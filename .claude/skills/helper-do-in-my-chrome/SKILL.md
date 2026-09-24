---
name: helper-do-in-my-chrome
description: Drive the user's own Chrome browser, headed, attached to their real running tab so cookies/logins carry over — never a fresh or switched profile. Use for any one-off task that needs to read or act on a live webpage the user is (or should be) logged into — check a page, click through a flow, scrape something, verify a live state — when no more specific skill already covers that site. Not for a project's own automated browser-test suite — that stays headless and isolated. Works in any project, not tied to this one.
---

Generalized Chrome automation. No project-specific logic belongs here — that lives in whichever skill or task needs it.

## Why this isn't a CDP debug-port script

The obvious approach — launch Chrome with `--remote-debugging-port=9222`, connect a Playwright script over CDP — **does not work on current Chrome** (136+). Chrome silently ignores that flag on the default profile; it's a deliberate Google security fix (any local process could otherwise drain cookies/sessions from a debuggable default profile), not a bug or a missing flag. Confirmed live against Chrome 150: process launches fine with the flag on its command line, port never opens. There is no flag workaround — the only sanctioned ways are (a) a completely separate `--user-data-dir`, which means a new profile and no reused session, or (b) the extension bridge below. This skill uses (b), because "never a new profile" is the whole point.

## The mechanism: Playwright's browser-extension bridge

This is a feature of the `@playwright/mcp` server, exposed as MCP tools (`mcp__<server-name>__browser_*`) — not a script you write and run. It attaches to a tab the user hands over from their actual, already-logged-in Chrome.

**One-time setup (do this before the first real use, check don't assume it's done):**

1. **MCP server registered in extension mode.** Check with `claude mcp list`. If nothing runs `@playwright/mcp ... --extension`, register one at user scope (works across all projects, not just this one):
   ```bash
   claude mcp add playwright-extension -s user -- npx -y @playwright/mcp@latest --extension
   ```
   A server added or changed this way only takes effect in a *new* Claude Code session — tell the user to restart/reconnect, then confirm the tools now appear as `mcp__playwright-extension__browser_*` before continuing.

2. **The Chrome extension is installed** — [Playwright Extension](https://chromewebstore.google.com/detail/playwright-extension/mmlmfjhmonkocbjadbfplnigmagldckm), id `mmlmfjhmonkocbjadbfplnigmagldckm`. Check without guessing:
   ```bash
   ls "$HOME/Library/Application Support/Google/Chrome/Default/Extensions/" 2>/dev/null | grep -i mmlmfjhmonkocbjadbfplnigmagldckm
   ```
   (Different Chrome profile → adjust `Default` to that profile's folder name.) If it's missing, tell the user to install it from the link above — don't try to install a Chrome extension for them unattended.

3. **A tab is actually handed over.** The user must click the extension's icon on the tab they want automated, in their real Chrome window, for *this* task. This is a live, per-use action — nothing on disk proves it happened. If a `browser_*` tool call fails or hangs with no attached tab, that's the most likely reason: ask the user to click the extension icon on the tab they mean, then retry.

## Doing the actual task

Once attached, just call the MCP tools directly — `browser_navigate`, `browser_click`, `browser_type`, `browser_snapshot`, `browser_take_screenshot`, `browser_evaluate`, etc. No script file needed for ordinary tasks; this is the point of the bridge over the old CDP-script approach.

Reuse the tab that was handed over — don't open new tabs/windows unless the task genuinely needs one (ask first).

`target` on click/type/etc. wants the raw `ref` value from a `browser_snapshot` (e.g. `f1e40`), not a role/name selector string — a role string throws a CSS-parsing error.

**Only if a task needs custom, reusable, multi-step logic** beyond what the tool calls cover directly (e.g. a non-trivial `browser_evaluate` payload worth inspecting or rerunning), write it to `chrome-automation-scratch/<task-slug>.js` at the repo root instead of composing it inline every time. Before writing there:
```bash
git check-ignore -q chrome-automation-scratch/probe || echo NOT_IGNORED
```
If `NOT_IGNORED`, add `chrome-automation-scratch/` to `.gitignore` first. Check what's already in that folder before adding to it — if old scripts from an unrelated task are sitting there, ask the user: keep or clean? Cleanup any time: `rm -rf chrome-automation-scratch`.

## Logins

If a page shows a sign-in/login wall, stop. Tell the user which site needs it and ask them to log in manually in that Chrome window (it's their real browser and real tab, so this persists normally). Never fill in or ask for a password, never try to script past auth.

## When unsure, ask

Ambiguous target ("that page" — which page?), a selector that doesn't match, a destructive-looking click (submit/delete/pay) — stop and ask rather than guessing. This skill has no fixed selectors or URLs of its own; every task's specifics come from the request or the calling skill.

## Screenshots

If a task needs one, save to `chrome-automation-scratch/screenshots/<short-task-name>/`.
