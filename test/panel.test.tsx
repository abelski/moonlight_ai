// Tests for hooks/panel.tsx, run with `claude plugin test .`. Nothing sits beneath the plugin: each `on` hook here
// stands for the engine (files, the token script, panes). Each state's rendered text is printed with a
// `=== panel state:` header so the owner can save and read it.
import type { On } from 'claude-code'
import { expect, mock, test } from 'claude-code/testing'
import type { Engine } from 'claude-code/testing'

const CWD = '/proj'
const ACTIVE = `${CWD}/plans/improvements/active`
const TRIAGE = `${CWD}/plans/triage/active`
const PANE = 'moonlight-panel'
const NOW = Date.parse('2026-10-30T10:12:05Z')
const FAST = 'research,idea,design,implement,accept,docs,spendreport,close'.split(',')

type Files = Record<string, { text: string; mtimeMs: number }>

function plan(opts: {
  status?: string
  flow?: string
  phase?: string
  mark?: 'running' | 'waiting' | 'blocked'
  phases?: string[]
  started?: string
  fence?: string
}): string {
  const names = opts.phases ?? FAST
  const at = names.indexOf(opts.phase ?? 'implement')
  const mark = opts.mark ?? 'running'
  const state = {
    flow: opts.flow ?? 'moonlight-fast',
    phase: names[at],
    waiting: mark === 'waiting' ? 'you' : null,
    phases: Object.fromEntries(names.map((n, i) => [n, i < at ? 'done' : i === at ? mark : 'pending'])),
    sessions: [
      { id: 's1', started_at: '2026-10-30T10:00:00Z' },
      { id: 's2', started_at: '2026-10-30T10:05:00Z' },
    ],
    branch: 'feat/1-x',
    idea: null,
  }
  return [
    '---',
    'kind: feature',
    `status: ${opts.status ?? 'in_progress'}`,
    `started_at: ${opts.started ?? '2026-10-30T10:00:00Z'}`,
    '---',
    '',
    '# Plan',
    '',
    '## Session state',
    '',
    '```json',
    opts.fence ?? JSON.stringify(state, null, 2),
    '```',
    '',
  ].join('\n')
}

const ROW = { input_tokens: 0, cache_creation_input_tokens: 0, cache_read_input_tokens: 0, output_tokens: 0 }
const REPORT = {
  messages: 12,
  input_tokens: 1200,
  cache_creation_input_tokens: 30000,
  cache_read_input_tokens: 450000,
  output_tokens: 8000,
  billable_total: 39200,
  by_agent: [
    { ...ROW, session: 's1', label: 'main', input_tokens: 1000, billable_total: 30000 },
    { ...ROW, session: 's1', label: 'moonlight:sdlc-ralph-implementer: Implementation pass', billable_total: 9200 },
    { ...ROW, session: 's2', label: 'Explore: old work', billable_total: 0 },
  ],
}

function engine(on: On, files: Files, isPlaced = true) {
  const clock = mock.clock(on, { now: NOW })
  const open = new Set<string>()
  const runs: string[][] = []
  const gate: { held: Promise<void> | null } = { held: null }
  const parent = (path: string) => path.slice(0, path.lastIndexOf('/'))
  on('session.start', (_, e) => ({ cwd: e.cwd }))
  on('command.register', (_, e) => ({ value: { command: e.name } }))
  on('fs.list', (_, e) => ({
    value: Object.entries(files)
      .filter(([path]) => parent(path) === e.path)
      .map(([path, file]) => ({
        name: path.slice(path.lastIndexOf('/') + 1),
        kind: 'file' as const,
        size: file.text.length,
        mtimeMs: file.mtimeMs,
        isLink: false,
      })),
  }))
  on('fs.read', (_, e) => {
    const file = files[e.path]
    if (!file) throw new Error(`ENOENT ${e.path}`)
    return { value: file.text }
  })
  on('process.run', async (_, e) => {
    runs.push([...e.argv])
    await gate.held
    const stdout = JSON.stringify(REPORT)
    return { value: { exitCode: 0, stdout, stderr: '', isStdoutTruncated: false, isStderrTruncated: false } }
  })
  on('ui.open', (_, e) => {
    open.add(e.id)
    return { value: { isPlaced: true as const } }
  })
  on('ui.close', (_, e) => {
    open.delete(e.id)
    return { value: undefined }
  })
  on('turn.complete', (_, e) => ({ text: e.answer }))
  on('ui.panes', () => ({
    value: [...open].map(id => ({ id, title: id, isShown: isPlaced, isFocused: false, isPlaced })),
  }))
  return { clock, open, runs, gate }
}

async function start($: Engine, clock: { settle: () => Promise<void> }) {
  await $.session.start({ cwd: CWD, surface: 'terminal', isInteractive: true })
  await clock.settle()
}

async function lines($: Engine, name: string, bodyColumns = 40) {
  const ui = await $.ui.mount({
    plugin: 'moonlight',
    surface: 'terminal',
    component: 'Pane',
    requestId: PANE,
    props: { title: 'moonlight', isFocused: false, bodyColumns, placement: 'dock', scroll: { offset: 0, bodyRows: 30 }, view: {} },
  })
  const texts = (await ui.findAll({ type: 'Text' })).map(found => found.text)
  await ui.unmount()
  console.log(`=== panel state: ${name} (${bodyColumns} columns) ===\n${texts.join('\n')}\n`)
  return texts
}

const command = {
  command: 'moonlight-panel',
  args: '',
  origin: { kind: 'composer' as const },
  presentation: { isFullscreen: true, columns: 200 },
}

test('a running plan shows its flow, time, phases and tokens', async ($, on) => {
  const { clock, open, runs } = engine(on, { [`${ACTIVE}/plan_1_x.md`]: { text: plan({}), mtimeMs: 1 } })
  await start($, clock)

  expect(open.has(PANE)).toBe(true)
  const shown = await lines($, 'populated')
  expect(shown[0]).toBe('moonlight-fast · 12m 05s')
  expect(shown).toContain('done    research')
  expect(shown).toContain('running implement')
  expect(shown).toContain('pending close')
  expect(shown.some(line => /implementer/.test(line) && line.endsWith('9.2k'))).toBe(true)
  expect(shown.some(line => /old work/.test(line))).toBe(false)
  expect(shown).toContain('total in 1.2k · cache 480.0k · out 8.0k')
  expect(runs[0]).toEqual(expect.arrayContaining(['--json', '--session', 's1', 's2', '--since', '2026-10-30T10:00:00Z']))
  expect(runs[0]).toEqual(expect.arrayContaining(['--project', CWD]))
})

test('a waiting phase carries the you mark, a blocked one says blocked', async ($, on) => {
  const files: Files = { [`${ACTIVE}/plan_1_x.md`]: { text: plan({ phase: 'design', mark: 'waiting' }), mtimeMs: 1 } }
  const { clock } = engine(on, files)
  await start($, clock)
  expect(await lines($, 'waiting you')).toContain('waiting design ← you')

  files[`${ACTIVE}/plan_1_x.md`] = { text: plan({ mark: 'blocked' }), mtimeMs: 2 }
  await clock.advance(5000)
  const shown = await lines($, 'blocked')
  expect(shown).toContain('blocked implement')
  expect(shown.some(line => line.includes('← you'))).toBe(false)
})

test('a narrow pane cuts long labels to its width', async ($, on) => {
  const { clock } = engine(on, { [`${ACTIVE}/plan_1_x.md`]: { text: plan({}), mtimeMs: 1 } })
  await start($, clock)
  const shown = await lines($, 'narrow', 24)
  expect(shown.every(line => line.length <= 24)).toBe(true)
  expect(shown).toContain('running implement')
})

test('no plan, a done plan and a corrupt fence open nothing and draw nothing', async ($, on) => {
  const files: Files = {}
  const { clock, open } = engine(on, files)
  await start($, clock)
  expect(open.size).toBe(0)
  expect(await lines($, 'empty')).toEqual([])

  files[`${ACTIVE}/plan_1_x.md`] = { text: plan({ status: 'done', phase: 'close' }), mtimeMs: 1 }
  await clock.advance(5000)
  expect(open.size).toBe(0)

  files[`${ACTIVE}/plan_1_x.md`] = { text: plan({ fence: '{ "flow": ' }), mtimeMs: 2 }
  await clock.advance(5000)
  expect(open.size).toBe(0)
  expect(await lines($, 'corrupt')).toEqual([])

  // implementation done, the flow still at acceptance: the panel stays
  files[`${ACTIVE}/plan_1_x.md`] = { text: plan({ status: 'done', phase: 'accept', mark: 'waiting' }), mtimeMs: 3 }
  await clock.advance(5000)
  expect(open.has(PANE)).toBe(true)
})

test('of two plans the newest with a state block wins', async ($, on) => {
  const bug = 'locate,reproduce,fix,red-check,confirm,spendreport,close'.split(',')
  const { clock } = engine(on, {
    [`${ACTIVE}/plan_1_x.md`]: { text: plan({}), mtimeMs: 1 },
    [`${TRIAGE}/issue-2-y.md`]: { text: plan({ flow: 'sdlc-fix-issue-from-triage', phases: bug, phase: 'fix' }), mtimeMs: 2 },
    [`${ACTIVE}/plan_1_x-uat-round-1.md`]: { text: '# UAT verdict\n', mtimeMs: 3 },
  })
  await start($, clock)
  const shown = await lines($, 'two plans')
  expect(shown[0]).toBe('sdlc-fix-issue-from-triage · 12m 05s')
  expect(shown).toContain('running fix')
})

test('the command hides the panel and brings it back', async ($, on) => {
  const { clock, open } = engine(on, { [`${ACTIVE}/plan_1_x.md`]: { text: plan({}), mtimeMs: 1 } })
  await start($, clock)
  expect(open.has(PANE)).toBe(true)

  expect((await $.command.run(command)).text).toMatch(/hidden/)
  expect(open.has(PANE)).toBe(false)
  await clock.advance(5000)
  expect(open.has(PANE)).toBe(false)

  expect((await $.command.run(command)).text).toMatch(/shown/)
  expect(open.has(PANE)).toBe(true)
})

test('on a narrow terminal the command places the waiting pane instead of hiding it', async ($, on) => {
  const { clock, open } = engine(on, { [`${ACTIVE}/plan_1_x.md`]: { text: plan({}), mtimeMs: 1 } }, false)
  await start($, clock)
  expect(open.has(PANE)).toBe(true)
  expect((await $.command.run(command)).text).toMatch(/shown/)
  expect(open.has(PANE)).toBe(true)
})

test('phases redraw from the plan and tokens refresh on the slow timer', async ($, on) => {
  const files: Files = { [`${ACTIVE}/plan_1_x.md`]: { text: plan({}), mtimeMs: 1 } }
  const { clock, runs } = engine(on, files)
  await start($, clock)
  const first = runs.length

  files[`${ACTIVE}/plan_1_x.md`] = { text: plan({ phase: 'accept', mark: 'waiting' }), mtimeMs: 2 }
  await clock.advance(5000)
  const shown = await lines($, 'after a phase call')
  expect(shown).toContain('done    implement')
  expect(shown).toContain('waiting accept ← you')
  expect(shown[0]).toBe('moonlight-fast · 12m 10s')
  expect(runs.length).toBe(first)

  await clock.advance(30000)
  expect(runs.length).toBe(first + 1)

  // a finished turn wrote to a transcript
  await $.turn.complete({ answer: '', durationMs: 1, isAborted: false, turnId: 't1', agentId: 'a1', reason: 'answer' })
  await clock.settle()
  expect(runs.length).toBe(first + 2)
})

test('a token run in flight is not stacked: turns and the timer during it start none', async ($, on) => {
  const { clock, runs, gate } = engine(on, { [`${ACTIVE}/plan_1_x.md`]: { text: plan({}), mtimeMs: 1 } })
  await start($, clock)
  const first = runs.length
  let release = () => {}
  gate.held = new Promise<void>(resolve => (release = resolve))
  const turn = { answer: '', durationMs: 1, isAborted: false, agentId: 'a1', reason: 'answer' as const }

  await $.turn.complete({ ...turn, turnId: 't1' })
  await clock.settle()
  expect(runs.length).toBe(first + 1)
  await $.turn.complete({ ...turn, turnId: 't2' })
  await $.turn.complete({ ...turn, turnId: 't3' })
  await clock.advance(30000)
  expect(runs.length).toBe(first + 1)

  // once the run ends, the next turn starts a fresh one
  gate.held = null
  release()
  await clock.settle()
  await $.turn.complete({ ...turn, turnId: 't4' })
  await clock.settle()
  expect(runs.length).toBe(first + 2)
})
