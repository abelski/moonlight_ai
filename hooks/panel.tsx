// The moonlight side panel (terminal only): the newest in-progress plan's flow, elapsed time, phases, and tokens per
// subagent with a running total. Phases come from the plan's `## Session state` block (scripts/plan-state.py writes
// it); tokens from scripts/token-report.py. `/moonlight-panel` hides and restores it. Facts: docs/panel-spike.md.
import type { EngineInterface, Register } from 'claude-code'

type Status = 'pending' | 'running' | 'waiting' | 'blocked' | 'done'
type Plan = { flow: string; started: string | null; waiting: string | null; phases: [string, Status][]; sessions: string[] }
type Tokens = { input: number; cache: number; output: number; agents: { label: string; total: number }[] }

const PANE = 'moonlight-panel'
const DIRS = ['plans/improvements/active', 'plans/triage/active']
const COLORS: Record<Status, string | undefined> = {
  running: 'claude',
  waiting: 'warning',
  blocked: 'error',
  done: undefined,
  pending: undefined,
}

// shortcut: module values (not $.state) are lost on a hot reload, as the timers are; the panel then needs a new
// session. Move them to $.state, declared in a types contract in plugin.json, if that bites.
let cwd: string | undefined
let hidden = false
let plan: Plan | null = null
let tokens: Tokens | null = null
let refreshing = false

// The plan's state, or null: no block, a corrupt fence, or a done plan whose flow reached its last phase. A done plan
// before that is still shown, as sdlc-ralph-implement sets `status: done` before acceptance and close.
function parse(text: string): Plan | null {
  const front = /^---\n([\s\S]*?)\n---\n/.exec(text)?.[1] ?? ''
  const field = (key: string) =>
    new RegExp(`^${key}:[ \\t]*(.*?)[ \\t]*$`, 'm').exec(front)?.[1]?.replace(/^['"]|['"]$/g, '')
  const fence = /^## Session state[ \t]*\n\s*```json\n([\s\S]*?)\n```/m.exec(text)
  let state
  try {
    state = JSON.parse(fence?.[1] ?? '')
  } catch {
    return null
  }
  if (typeof state?.phases !== 'object' || state.phases === null) return null
  const phases = Object.entries(state.phases) as [string, Status][]
  if (field('status') === 'done' && state.phase === phases.at(-1)?.[0]) return null
  const started = field('started_at')
  return {
    flow: String(state.flow ?? 'moonlight'),
    started: started && started !== 'null' ? started : null,
    waiting: state.waiting ?? null,
    phases,
    sessions: Array.isArray(state.sessions) ? state.sessions.map((s: { id?: string }) => s?.id).filter(Boolean) : [],
  }
}

// The newest plan file holding a `## Session state` heading wins; a file without one (a UAT verdict) is skipped.
async function find($: EngineInterface, root: string): Promise<Plan | null> {
  const files: { path: string; mtimeMs: number }[] = []
  for (const dir of DIRS) {
    for (const entry of await $.fs.list(`${root}/${dir}`).catch(() => [])) {
      if (entry.kind === 'file' && entry.name.endsWith('.md')) {
        files.push({ path: `${root}/${dir}/${entry.name}`, mtimeMs: entry.mtimeMs })
      }
    }
  }
  files.sort((a, b) => b.mtimeMs - a.mtimeMs)
  for (const file of files) {
    const text = String(await $.fs.read(file.path).catch(() => ''))
    if (/^## Session state[ \t]*$/m.test(text)) return parse(text)
  }
  return null
}

async function refreshPlan($: EngineInterface, root: string) {
  plan = await find($, root)
  if (!plan) tokens = null
  $.ui.invalidate('ui.render')
  const isOpen = (await $.ui.panes()).some(pane => pane.id === PANE)
  if (plan && !hidden && !isOpen) await $.ui.open({ id: PANE, title: 'moonlight' })
  if ((!plan || hidden) && isOpen) await $.ui.close({ id: PANE })
  return plan
}

// One run at a time: every finished turn (subagents too) and the 30 s timer ask for one, and each rereads every
// transcript. A request during a run is dropped; the next turn or tick catches up.
async function refreshTokens($: EngineInterface, root: string) {
  if (refreshing || !plan || plan.sessions.length === 0) return
  refreshing = true
  try {
    const argv = ['python3', `${$.plugin.root}/scripts/token-report.py`, '--project', root, '--json']
    for (const id of plan.sessions) argv.push('--session', id)
    if (plan.started) argv.push('--since', plan.started)
    const ran = await $.process.run(argv)
    if (ran.exitCode !== 0) return
    const report = JSON.parse(ran.stdout)
    tokens = {
      input: report.input_tokens,
      cache: report.cache_creation_input_tokens + report.cache_read_input_tokens,
      output: report.output_tokens,
      agents: report.by_agent
        .filter((row: { billable_total: number }) => row.billable_total > 0)
        .map((row: { label: string; billable_total: number }) => ({ label: row.label, total: row.billable_total })),
    }
    $.ui.invalidate('ui.render')
  } finally {
    refreshing = false
  }
}

function background($: EngineInterface, work: Promise<unknown>) {
  void work.catch(error => $.ui.log(`moonlight panel: ${error}`, { to: 'debug' }))
}

const fmt = (n: number) => (n >= 1e6 ? `${(n / 1e6).toFixed(1)}M` : n >= 1e3 ? `${(n / 1e3).toFixed(1)}k` : String(n))

function elapsed(started: string | null, now: number) {
  const from = Date.parse(started ?? '')
  if (Number.isNaN(from)) return 'not started'
  const s = Math.max(0, Math.floor((now - from) / 1000))
  const two = (n: number) => String(n).padStart(2, '0')
  return s >= 3600 ? `${Math.floor(s / 3600)}h ${two(Math.floor(s / 60) % 60)}m` : `${Math.floor(s / 60)}m ${two(s % 60)}s`
}

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    const started = await next(e)
    if (!e.isInteractive || e.surface !== 'terminal') return started
    cwd = e.cwd
    const root = e.cwd
    await $.command.register({ name: 'moonlight-panel', description: 'Hide or show the moonlight panel' })
    await refreshPlan($, root)
    background($, refreshTokens($, root))
    $.clock.every(3000, () => background($, refreshPlan($, root)))
    $.clock.every(30000, () => background($, refreshTokens($, root)))
    return started
  })

  // A drawn pane hides; a hidden one, or one waiting undrawn on a narrow terminal, is shown (asked, so at any width).
  on('command.run', { command: 'moonlight-panel' }, async $ => {
    hidden = (await $.ui.panes()).some(pane => pane.id === PANE && pane.isPlaced)
    if (hidden) {
      await $.ui.close({ id: PANE })
      return { text: 'Moonlight panel hidden. Run /moonlight-panel again to bring it back.' }
    }
    const shown = cwd ? await refreshPlan($, cwd) : null
    if (shown) await $.ui.open({ id: PANE, title: 'moonlight' })
    return { text: shown ? 'Moonlight panel shown.' : 'Moonlight panel shown once a plan is in progress.' }
  })

  // The person's own close counts as hiding, so the timer does not reopen the pane.
  on('ui.close', { id: PANE }, ($, e, next) => {
    if (e.origin.kind === 'person') hidden = true
    return next(e)
  }).catch(($, e, next) => next(e))

  // A finished turn (main or subagent) has written to a transcript.
  on('turn.complete', async ($, e, next) => {
    const done = await next(e)
    if (cwd) background($, refreshTokens($, cwd))
    return done
  })

  on('ui.render', { component: 'Pane', requestId: PANE }, async ($, e) => {
    const { Box, Text } = $.ui.resolve(e)
    const shown = plan
    if (!shown) return <Box />
    const width = Math.max(10, e.props.bodyColumns)
    const cut = (text: string, room = width) => (text.length > room ? `${text.slice(0, room - 1)}…` : text)
    const totals = tokens ? [`in ${fmt(tokens.input)}`, `cache ${fmt(tokens.cache)}`, `out ${fmt(tokens.output)}`] : []
    const totalLine = `total ${totals.join(' · ')}`
    const totalRows = !tokens ? [] : totalLine.length <= width ? [totalLine] : ['total', ...totals.map(p => `  ${p}`)]

    return (
      <Box flexDirection="column">
        <Text weight="bold">{cut(`${shown.flow} · ${elapsed(shown.started, await $.clock.now())}`)}</Text>
        {shown.phases.map(([name, status]) => (
          <Text color={COLORS[status]} dimColor={status === 'done' || status === 'pending'}>
            {cut(`${status.padEnd(7)} ${name}${status === 'waiting' && shown.waiting === 'you' ? ' ← you' : ''}`)}
          </Text>
        ))}
        {tokens && <Text weight="bold">tokens</Text>}
        {tokens?.agents.map(agent => {
          const n = fmt(agent.total)
          const room = width - n.length - 1
          return <Text>{`${cut(agent.label, room).padEnd(room)} ${n}`}</Text>
        })}
        {totalRows.map(row => (
          <Text>{row}</Text>
        ))}
      </Box>
    )
  })
}
