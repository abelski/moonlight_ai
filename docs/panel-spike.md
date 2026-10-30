# Panel spike (plan #7, item 1)

Checked on Claude Code 2.1.314, 2026-10-30, against the `plugin-authoring` skill's `types/claude-code.d.ts` and
`reference.md`, and with `claude plugin validate` on a scratch copy of this plugin. The mod API is early access: re-check
these facts after a Claude Code update.

## One plugin or two

One. A scratch copy of the repo with `"modules": ["./panel.tsx"]` added to `hooks/hooks.json` (beside the existing
`SessionStart` and `PreToolUse` command hooks) and a stub `hooks/panel.tsx` passes `claude plugin validate`. The
validator lists the module's hooks and `$` calls and adds one note: the plugin directory (the public catalog) has its own
rules for code modules that `validate` does not apply.

- `modules` must be a list holding one path, relative to `hooks/hooks.json`. A plain string is refused
  (`expected array, received string`), and so is a second entry.
- So the panel lives in this plugin: `hooks/panel.tsx`, no second plugin and no `marketplace.json` change.

## How a plugin-shipped mod gets the owner's consent

Not answerable from the types, the reference or a command without triggering the prompt, which the spike must not do.
What the sources say:

- `reference.md` (Sharing a mod): after `claude plugin install`, a plugin that is a hooks module alone prints
  `Installed <mod>. Plugin is now active.` and its hooks run from then on. Moonlight also has skills, agents and command
  hooks; what it prints is not stated.
- `reference.md` speaks of a switch for function hooks that can be off (a `claude -p` run names a `--plugin-dir` module
  that did not load, "the switch being off included"). How the owner turns it on for an installed plugin is not written.
- Under the `allowManagedHooksOnly` setting a `user`-tier plugin loads no hooks module at all, and a higher-tier
  `plugin.register` hook can refuse the module.

The owner checks this at manual acceptance: after updating the plugin, start a session and answer any prompt that asks to
enable the module. If the module does not load, the scripts and the spendreport still work; only the panel is missing.

## A narrow window

The engine handles it; the module only calls `$.ui.open`.

- A pane the plugin opens by itself waits undrawn below 144 terminal columns (110 for an id the person once opened).
  `$.ui.open` then answers `{ isPlaced: false, reason }` and `$.ui.panes()` lists it with `isPlaced: false`.
- It is placed when the terminal widens to that floor, or when the person opens it (a command they typed), at any width.
- The fullscreen layout docks the pane beside the transcript; the main screen places it inline above the prompt.
  `e.viewport.isFullscreen` and `e.props.placement` (`dock` or `inline`) say which; the tree is sized to
  `e.props.bodyColumns`.

## The session id

- A mod: `$.session.id()` answers the session's id (the transcript file's name).
- A command hook: its stdin carries `session_id` and `transcript_path`.
- The Bash tool: `CLAUDE_CODE_SESSION_ID` is set. Not in the types; observed on 2.1.314. Inside a subagent its value is
  the main session's id, which matches the main transcript file name. So `plan-state.py phase` takes `--session`, else
  `CLAUDE_CODE_SESSION_ID`, else the newest main transcript in the project folder.

## The `$` nouns the panel needs

All declared in `CoreEngineInterface`:

- `$.fs`: `read`, `write`, `list` (`{ name, kind, size, mtimeMs, isLink }`), `exists`, `stat`, `ancestors`. A relative
  path is under the session's working directory; a read over 4 MiB rejects.
- `$.process`: `run(argv, { cwd, env, stdin, timeoutMs })` resolving `{ exitCode, stdout, stderr }` (no shell, 30 s
  default timeout), and `spawn`. CLI only.
- `$.clock`: `now`, `sleep`, `after`, `every` (timers end when the module reloads).
- `$.plugin.root`: the plugin's folder, absolute, so the panel runs `${root}/scripts/token-report.py`.
- Also used: `$.ui.open` / `close` / `panes` / `invalidate` / `resolve`, `$.command.register` with a `command.run`
  hook, and `$.state` for values a drawing reads (a hot reload loses module variables).

## Tests

`claude plugin test <dir>` runs every `*.test.ts` and `*.test.tsx` under the folder in an environment with no fs,
network or process. A test answers `fs.*`, `process.run` and `clock.*` itself with `on(...)` hooks (or `mock.clock`),
then draws the pane with `$.ui.mount({ plugin, surface, component: 'Pane', requestId, props })` and reads it with
`find` / `findAll`.
