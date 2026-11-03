import { atom, read, update } from 'claude-code'
import type { Register } from 'claude-code'

import type { Limit, Meter, Turn } from '../types'

// AI를 부르는 코드가 없다. 앱이 건네주는 값만 그린다.
const PANE = 'token-panel'
const EMPTY: Turn = { total: 0, fresh: 0, requests: 0, subRequests: 0 }

// 패널 글은 컴퓨터 언어를 따른다. TOKEN_PANEL_LANG=ko|en이 먼저고, 없으면 윈도우 지역 설정(LocaleName)을 본다
let korean = false
export async function language($: any) {
  const set = String((await $.env.get('TOKEN_PANEL_LANG')) ?? '').toLowerCase()
  if (set === 'ko' || set === 'en') return set === 'ko'
  try {
    const { stdout } = await $.process.run(['reg', 'query', 'HKCU\\Control Panel\\International', '/v', 'LocaleName'], { timeoutMs: 3000 })
    return /\bko-/i.test(String(stdout ?? ''))
  } catch {
    return false
  }
}

const KO = {
  title: '토큰 사용량', five: '5시간 한도', week: '주간 한도', turn: '이번 턴', last: '지난 턴', size: '지금 대화 크기',
  later: '다음 답 뒤에 나옵니다', none: '아직 없습니다', fresh: '새로 쓴 양', total: '총량', requests: (n: number) => `요청 ${n}번`,
  sub: (n: number) => `서브에이전트 요청 ${n}번 포함`,
}
const EN: typeof KO = {
  title: 'Token usage', five: '5-hour limit', week: 'Weekly limit', turn: 'This turn', last: 'Last turn', size: 'Conversation size',
  later: 'Shown after the next answer', none: 'Nothing yet', fresh: 'New tokens', total: 'Total', requests: (n: number) => `${n} requests`,
  sub: (n: number) => `incl. ${n} subagent requests`,
}
const say = () => (korean ? KO : EN)

const meter = atom({ plugin: 'token-usage-clock', key: 'meter' } as const, { limits: [], contextWindow: 0 } as Meter, { shape: 'meter-1' })
const current = atom({ plugin: 'token-usage-clock', key: 'current' } as const, EMPTY, { shape: 'turn-1' })
const last = atom({ plugin: 'token-usage-clock', key: 'last' } as const, EMPTY, { shape: 'turn-1' })

const tokens = (n: number) =>
  korean
    ? n < 10000 ? n.toLocaleString('en-US') : `${(n / 10000).toFixed(1)}만`
    : n < 1000 ? String(n) : `${(n / 1000).toFixed(n < 100000 ? 1 : 0)}k`

const left = (at: string | undefined, now: number) => {
  if (!at) return ''
  const minutes = Math.max(0, Math.round((Date.parse(at) - now) / 60000))
  const d = Math.floor(minutes / 1440), h = Math.floor((minutes % 1440) / 60), m = minutes % 60
  if (korean) {
    if (minutes < 60) return `${m}분 뒤 초기화`
    if (minutes < 1440) return `${h}시간 ${m}분 뒤 초기화`
    return `${d}일 ${h}시간 뒤 초기화`
  }
  if (minutes < 60) return `resets in ${m} min`
  if (minutes < 1440) return `resets in ${h} h ${m} min`
  return `resets in ${d} d ${h} h`
}

const bar = (percent: number) => {
  const filled = Math.max(0, Math.min(10, Math.round(percent / 10)))
  return '█'.repeat(filled) + '░'.repeat(10 - filled)
}

const toLimits = (list: readonly { kind: string; percentUsed: number; resetsAt?: string }[]): Limit[] =>
  list.map(one => ({ kind: one.kind, percent: one.percentUsed, resetsAt: one.resetsAt }))

const progress = async ($: any) => {
  const home = String((await $.env.get('USERPROFILE')) ?? (await $.env.get('HOME')) ?? '').replaceAll('\\', '/')
  return `${home}/.claude/progress`
}

// `claude -p` 같은 자동 실행은 시계에 쓰지 않는다. 데스크톱 앱도 SDK로 돌아서 isInteractive로는 가릴 수 없다.
let headless = false

// 엔진이 이 모듈을 불러온 시각. 고친 모드가 앱에 실렸는지 상태 파일만 보고 알 수 있게 함께 적는다
const LOADED = Date.now()

// 시계 메인 바늘의 빛: working(클로드가 답을 만드는 중) · waiting(허락 창이나 질문 창이 사용자 손을 기다림) · idle(턴이 끝남)
type Activity = 'working' | 'waiting' | 'idle'
let activity: Activity = 'idle'
// 진행 중인 백그라운드 작업(셸 · 서브에이전트 · 모니터) 수. CHAT 바늘(1번)에 빛을 켠다
let background = 0
// 센 작업들의 종류·상태·설명. 불이 왜 켜졌는지 상태 파일에서 바로 보이게 남긴다
let backgroundTasks: string[] = []
let shared = 0
// 일하는 동안 이만큼마다 살아 있다고 다시 적는다. 시계는 오래 소식이 없으면 쉼으로 본다
const BEAT = 5000
const WAITING_TOOLS = ['AskUserQuestion', 'ExitPlanMode']
// 띄우는 순간 뒤에서 도는 도구. 엔진은 턴이 끝날 때만 작업 목록을 넘기므로, 띄우자마자 CHAT 빛을 먼저 켠다
const LAUNCHERS = ['Agent', 'Workflow', 'Monitor']
// 엔진 안에서는 컴퓨터 언어를 믿고 알 길이 없어, 사람에게 보이는 글은 영어 · 한국어를 함께 쓴다
const NO_CLOCK = 'Token clock could not start. Install Python 3, run py -3 -m pip install numpy pillow, then type /clock. · 시계를 띄우지 못했습니다. 위 명령으로 설치한 뒤 /clock을 입력하세요.'

// 사람이 아닌 입력. 이 입력은 시계 주인을 바꾸지 않는다.
const NOT_PERSON = ['task-notification', 'scheduled-trigger', 'peer', 'peer-send-message', 'projects-relay', 'channel', 'plugin', 'coordinator', 'observer', 'observer-activity', 'unclassified', 'sdk', 'auto-continuation']

// 시계 쪽 일은 실패해도 앱의 일을 막지 않는다. 처리기가 던지면 엔진이 그 사건을 거부한다
const quietly = async (work: () => Promise<unknown>) => {
  try {
    await work()
  } catch {
    // 다음 사건에서 다시 쓴다
  }
}

// 사용자가 마지막으로 말을 건 세션이 시계의 주인이다. 대화 크기와 용두는 세션마다 다르기 때문이다.
const ownerPath = async ($: any) => `${await progress($)}/token-panel-owner.json`

export async function owner($: any) {
  const path = await ownerPath($)
  if (!(await $.fs.exists(path))) return undefined
  try {
    const session = JSON.parse(await $.fs.read(path)).session
    return typeof session === 'string' ? session : undefined
  } catch {
    return undefined
  }
}

export const claim = async ($: any, session: unknown) => $.fs.write(await ownerPath($), JSON.stringify({ session }))

export const isPerson = (e: any) => !e.isMeta && !NOT_PERSON.includes(e.origin?.kind)

// 주인이 없을 때 다른 세션이 시계를 이어받기까지 기다리는 시간
const HANDOVER = 10000

const previous = async ($: any, path: string) => {
  try {
    return JSON.parse(await $.fs.read(path))
  } catch {
    return undefined
  }
}

// 버그를 찾을 때 되짚는 상태 기록(블랙박스). 환경 변수 TOKEN_PANEL_HISTORY=1인 컴퓨터에서만 켜지고, 기본은 꺼져 있어 아무것도 쓰지 않는다.
// 주인·빛·백그라운드·대기가 바뀔 때만 한 줄을 더하고 최근 500줄만 남긴다.
// 여러 세션이 같은 파일에 쓰므로 쓸 때마다 파일을 새로 읽어 덧붙인다(들고 있던 줄로 통째 쓰면 다른 세션의 줄을 지운다)
let history: boolean | undefined
let historyLast = ''
const HISTORY_LIMIT = 500

async function remember($: any, data: any) {
  if (history === undefined) history = (await $.env.get('TOKEN_PANEL_HISTORY')) === '1'
  if (!history) return
  const line = [String(data.session).slice(0, 8), data.activity, data.background ? 'CHAT빛' : '-', (data.backgroundTasks ?? []).join('|') || '-', (data.waits ?? []).join('|') || '-'].join(' ')
  if (line === historyLast) return
  historyLast = line
  const path = `${await progress($)}/token-panel-history.log`
  let lines: string[] = []
  try {
    lines = (await $.fs.read(path)).split('\n').filter(Boolean)
  } catch {
    // 처음 쓰는 파일
  }
  const at = new Date(data.at), two = (n: number) => String(n).padStart(2, '0')
  lines.push(`${two(at.getHours())}:${two(at.getMinutes())}:${two(at.getSeconds())}.${String(at.getMilliseconds()).padStart(3, '0')} ${line}`)
  await $.fs.write(path, lines.slice(-HISTORY_LIMIT).join('\n') + '\n')
}

// 앱 밖의 작은 창(window/window.py)이 이 파일을 읽어 그린다. 주인이 있으면 주인만 쓴다.
export async function share($: any) {
  if (headless) return
  const session = await $.session.id()
  const master = await owner($)
  if (master && master !== session) {
    shared = await $.clock.now()  // 주인이 아니면 쓰지 않는다. 박동도 5초에 한 번만 다시 본다
    return
  }
  const path = `${await progress($)}/token-panel.json`
  const before = await previous($, path)
  const now = await $.clock.now()
  // 주인이 없으면 지금 시계에 보이는 세션이 이어 쓴다. 여러 세션이 번갈아 덮어 값이 튀지 않게 한다
  if (!master && typeof before?.session === 'string' && before.session !== session && now - Number(before.at) < HANDOVER) return
  const seen = await read($, meter)
  // 한도는 계정에 하나다. 첫 측정 전 빈 목록이면 직전 값을 지켜 가짜 초기화 연출을 막는다
  const fresh = Array.isArray(seen.limits) ? seen.limits : []
  const limits = fresh.length || !Array.isArray(before?.meter?.limits) ? fresh : before.meter.limits
  const data = { session, meter: { ...seen, limits }, current: await read($, current), last: await read($, last), activity, background: background > 0, backgroundTasks, waits: [...waits.keys()].map(k => k.split(':').slice(0, 3).join(':')), loaded: LOADED, at: now }
  await $.fs.write(path, JSON.stringify(data))
  shared = now
  await quietly(() => remember($, data))
}

// 메인 턴이 도는가, 그리고 사람 손을 기다리는 호출이 남아 있는가. 빛은 이 둘로만 정한다
let turning = false
// 이번 턴의 마무리 상자에 사용자에게 묻는 질문이 있었는가
let boxAsk = false
// 기다리는 호출: 허락 창은 「perm:누구:도구:입력」, 질문 · 승인 창은 「id:호출번호」. 값은 들어온 시각
const waits = new Map<string, number>()
// 허락 창 대기마다 그 창이 넘겨준 도구 입력. 끝난 호출에는 엔진이 붙인 칸(턴 정보 따위)이 더 있어서, 이 입력의 칸만 골라 비교한다
const asked = new Map<string, { who: string; tool: unknown; input: Record<string, unknown>; call?: string }>()
// 허락을 묻기로 정해진 호출(번호 → 누구 · 도구 · 판정 때 입력). 허락 창이 뜨면 입력이 같은 호출과 짝지어,
// 그 호출이 끝날 때만 그 창의 대기를 지운다. 자동 모드가 창 없이 정한 호출은 짝이 없어 남의 창을 지우지 못한다
const askedCalls = new Map<string, { who: string; tool: unknown; input: unknown; linked: boolean }>()
// 짝을 못 찾은 대기가 영원히 깜빡이지 않게 이만큼 지나면 버린다
const PENDING_LIMIT = 30 * 60000

const stable = (value: unknown) =>
  JSON.stringify(value, (_k, x) => (x && typeof x === 'object' && !Array.isArray(x) ? Object.fromEntries(Object.entries(x).sort(([a], [b]) => (a < b ? -1 : 1))) : x))
const permKey = (who: unknown, tool: unknown, input: unknown) => `perm:${who ?? 'main'}:${tool}:${stable(input)}`
const forget = (prefix: string) => {
  for (const key of [...waits.keys()]) if (key.startsWith(prefix)) { waits.delete(key); asked.delete(key) }
}

// 턴이나 서브에이전트가 끝날 때 엔진이 진행 중인 백그라운드 작업 목록을 건넨다. 작업이 끝나면 알림이 새 턴을 열고 그 끝에서 다시 센다.
// 엔진은 $를 받는 함수를 파일 맨 위에 선언된 것만 허락한다(register 안의 화살표 함수면 모듈 전체를 싣지 않는다)
async function countBackground($: any, e: any) {
  // 아티팩트를 발행하면 엔진이 「바뀌면 알려 주는 구독」을 monitor 작업으로 세션 내내 걸어 둔다. 일이 아니라 듣기만 하므로 세지 않는다
  const list = (Array.isArray(e?.background_tasks) ? e.background_tasks : []).filter(
    (t: any) => !(t?.type === 'monitor' && String(t?.description ?? '').startsWith('live updates for artifact')),
  )
  const count = list.length
  backgroundTasks = list.map((t: any) => `${t?.type}:${t?.status}:${String(t?.description ?? '').slice(0, 60)}`)
  if (count === background) return
  background = count
  await quietly(() => share($))
}

const refresh = async ($: any) => {
  const now = await $.clock.now()
  for (const [key, at] of waits) if (now - at > PENDING_LIMIT) waits.delete(key)
  const next: Activity = waits.size ? 'waiting' : turning ? 'working' : 'idle'
  if (activity === next) return
  activity = next
  await quietly(() => share($))
}

// 사용자가 끈 시계는 세션이 시작돼도 다시 띄우지 않는다. /clock 으로만 켠다.
const clockPath = async ($: any) => `${await progress($)}/token-panel-clock.json`

export async function wanted($: any) {
  const path = await clockPath($)
  if (!(await $.fs.exists(path))) return true
  try {
    return JSON.parse(await $.fs.read(path)).on !== false
  } catch {
    return true
  }
}

// 시계를 띄운다. 이미 떠 있으면 시계가 스스로 끝나므로 세션마다 불러도 하나만 뜬다.
// 파이썬이 먼저다. 모드와 같은 판의 시계 코드가 돌기 때문이다. 파이썬이나 numpy · Pillow가 없으면 Releases의 실행 파일판을 쓴다
export async function summon($: any) {
  const launcher = `${$.plugin.root}/window/launch.py`
  const local = String((await $.env.get('LOCALAPPDATA')) ?? '').replaceAll('\\', '/')
  const tries = [['py', '-3', launcher], ['python3', launcher], ['python', launcher]]
  if (local) tries.push([`${local}/TokenClock/token-clock.exe`])
  for (const command of tries) {
    try {
      if ((await $.process.run(command, { timeoutMs: 10000 })).exitCode === 0) return true
    } catch {
      // 이 이름의 실행기가 없다. 다음을 본다.
    }
  }
  return false
}

// 주인은 1초마다 요청을 본다. 이만큼 아무도 받지 않으면 받을 세션이 없는 것이다
const ASK_LIMIT = 15000
// 압축이 끝났다는 소식이 이만큼 없으면 그 압축은 잊고 새 요청을 받는다
const RUN_LIMIT = 30 * 60000
let checking = false
let pending: number | undefined

const command = async ($: any) => {
  const path = `${await progress($)}/token-panel-cmd.json`
  if (!(await $.fs.exists(path))) return { path, asked: undefined }
  return { path, asked: JSON.parse(await $.fs.read(path)) }
}

// 그사이 새 요청이 들어왔으면 덮어쓰지 않는다.
const settle = async ($: any, asked: any, state: string, why?: string) => {
  const { path, asked: latest } = await command($)
  if (latest?.at === asked.at) await $.fs.write(path, JSON.stringify({ ...asked, state, why }))
}

// 데스크톱 앱은 SDK라 $.session.compact가 막혀 있다. /compact를 사람이 친 것처럼 넣으면 세션이 한가해질 때 돈다.
// 턴이 길면 그만큼 줄을 서므로, 기다리는 동안은 queued로 알려 시계가 실패로 보지 않게 한다.
const compact = async ($: any, asked: any) => {
  let state = 'done'
  let why: string | undefined
  try {
    await $.command.run({ command: 'compact' })
  } catch (error) {
    state = 'failed'
    why = String(error)
  }
  pending = undefined
  await settle($, asked, state, why)
  if (state !== 'done') return
  const usage = await $.session.usage()
  await update($, meter, one => ({ ...one, contextTokens: usage.context.tokens, contextWindow: usage.context.window }))
  await share($)
}

// 시계의 용두 신호를 받아 대화를 압축한다. 사용자가 마지막으로 말을 건 세션(주인)만 응한다.
export async function watch($: any) {
  if (checking) return
  checking = true
  try {
    const { asked } = await command($)
    if (asked?.state !== 'asked') return
    const at = Number(asked.at)
    const now = await $.clock.now()
    if (!(at > 0) || now - at > ASK_LIMIT) {
      await settle($, asked, 'failed', 'expired')
      return
    }
    // 주인이 없거나 주인이 아닌 세션을 향한 요청은 사용자가 고른 세션이 아니다. 되돌릴 수 없으니 바로 거절한다
    if (asked.session !== (await owner($))) {
      await settle($, asked, 'failed', 'not-owner')
      return
    }
    if (asked.session !== (await $.session.id())) return
    if (pending !== undefined && now - pending < RUN_LIMIT) {
      await settle($, asked, 'failed', 'busy')
      return
    }
    pending = at
    await settle($, asked, 'queued')
    void compact($, asked).catch(() => undefined)
  } catch {
    // 쓰는 도중의 파일이다. 다음 초에 다시 본다.
  } finally {
    checking = false
  }
}

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    await quietly(async () => {
      korean = await language($)
    })
    await quietly(async () => {
      headless = String((await $.env.get('CLAUDE_CODE_ENTRYPOINT')) ?? '').startsWith('sdk')
      if (!headless) {
        $.clock.every(1000, async () => {
          await watch($)
          await quietly(() => refresh($))  // 오래 남은 대기(30분)는 쉬는 동안에도 버린다
          if ((activity !== 'idle' || background > 0) && (await $.clock.now()) - shared > BEAT) await quietly(() => share($))
        })
        // 처음 설치한 컴퓨터에 Python이나 numpy · Pillow가 없으면 시계가 뜨지 않는다. 조용히 끝나지 않게 한 번 알린다
        if (await wanted($)) {
          void summon($).then(ok => {
            if (!ok) $.ui.toast(NO_CLOCK)
          })
        }
      }
    })
    await quietly(() => $.command.register({ name: 'tokens', description: 'Open the token usage pane · 토큰 사용량 패널' }))
    await quietly(() => $.command.register({ name: 'clock', description: 'Show the desktop token clock (/clock off hides it) · 토큰 계기판 시계' }))
    // 사용량은 바탕화면 시계로 본다. 앱 안 패널은 세션이 시작될 때 열지 않고, 열려 있던 것도 닫는다. /tokens 로만 연다
    void quietly(() => $.ui.close({ id: PANE }))
    await quietly(async () => {
      const usage = await $.session.usage()
      await update($, meter, () => ({
        limits: toLimits(usage.rateLimits),
        contextTokens: usage.context.tokens,
        contextWindow: usage.context.window,
      }))
      await share($)
    })

    return next(e)
  })

  on('command.run', { command: 'clock' }, async ($, e) => {
    const off = ['off', '끄기'].includes(String(e.args ?? '').trim())
    await $.fs.write(await clockPath($), JSON.stringify({ on: !off }))
    if (off) return { text: 'Clock hidden. /clock shows it again. · 시계를 껐습니다.' }

    return { text: (await summon($)) ? 'Clock shown. · 시계를 켰습니다.' : NO_CLOCK }
  })

  on('command.run', { command: 'tokens' }, async $ => {
    await $.ui.open({ id: PANE, title: say().title })

    return { text: 'Token pane opened. · 토큰 사용량 패널을 열었습니다.' }
  })

  on('session.measure', async ($, e, next) => {
    await quietly(async () => {
      await update($, meter, () => ({
        limits: toLimits(e.rateLimits),
        contextTokens: e.context.tokens,
        contextWindow: e.context.window,
      }))
      await share($)
    })

    return next(e)
  })

  on('turn.start', async ($, e, next) => {
    if (!e.agentId) {
      turning = true
      waits.delete('box')  // 상자에 답했거나 새 턴이 시작됐다
      activity = waits.size ? 'waiting' : 'working'
      await quietly(async () => {
        const finished = await read($, current)
        if (finished.requests > 0) await update($, last, () => finished)
        await update($, current, () => EMPTY)
        await share($)
      })
    }

    return next(e)
  })

  on('classic.Stop', async ($, e, next) => {
    await countBackground($, e)

    return next(e)
  })
  on('classic.SubagentStop', async ($, e, next) => {
    await countBackground($, e)
    if (e?.agent_id) forget(`perm:${e.agent_id}:`)
    await refresh($)

    return next(e)
  })

  // 메인 턴이 끝나면 쉼이다. 서브에이전트의 끝은 메인 턴을 끝내지 않는다. 메인이 남긴 대기도 함께 닫는다
  on('turn.complete', async ($, e, next) => {
    if (!e.agentId) {
      turning = false
      forget('perm:main:')
      forget('id:')
      if (boxAsk) waits.set('box', await $.clock.now())
      boxAsk = false
      await refresh($)
    }

    return next(e)
  })

  // 허락 창이 사람에게 뜰 때만 깜빡인다. tool.check의 ask는 자동 모드가 사람 대신 정하기도 해서 쓰지 않는다.
  // 메인이 쉬는 동안 백그라운드 서브에이전트가 묻는 창도 사람을 기다리므로 깜빡인다
  on('classic.PermissionRequest', async ($, e, next) => {
    const key = permKey(e?.agent_id, e?.tool_name, e?.tool_input)
    const who = e?.agent_id ?? 'main'
    waits.set(key, await $.clock.now())
    // 이 창을 띄운 호출을 찾는다: 판정 때 입력이 같은 것, 없으면 같은 쪽 같은 도구의 가장 최근 것
    const open = [...askedCalls].filter(([, c]) => !c.linked && c.who === who && c.tool === e?.tool_name)
    const call = open.find(([, c]) => stable(c.input) === stable(e?.tool_input)) ?? open[open.length - 1]
    if (call) call[1].linked = true
    asked.set(key, { who, tool: e?.tool_name, input: e?.tool_input && typeof e.tool_input === 'object' ? e.tool_input : {}, call: call?.[0] })
    await refresh($)

    return next(e)
  })

  // 허락을 묻기로 정해진 호출을 적어 둔다. 자동 모드가 대신 정하면 허락 창(PermissionRequest)이 뜨지 않아 대기도 생기지 않는다
  on('tool.check', async ($, e, next) => {
    const verdict = await next(e)
    if ((verdict as any)?.decision === 'ask' && typeof e?.tool_use_id === 'string') {
      askedCalls.set(e.tool_use_id, { who: (e as any).agentId ?? 'main', tool: e.tool, input: e.input, linked: false })
    }

    return verdict
  })

  // 질문 창과 계획 승인 창은 도구가 끝날 때까지 사용자를 기다린다. 끝난 호출은 자기 대기만 지운다
  on('tool.call', async ($, e, next) => {
    const { tool, tool_use_id: id, agentId, origin, ...input } = e as any
    if (WAITING_TOOLS.includes(tool)) {
      waits.set(`id:${id}`, await $.clock.now())
      await refresh($)
    }
    let answered = false
    try {
      const result: any = await next(e)
      const ok = !result?.deny && !result?.isError
      // 턴 끝 마무리 상자에 질문(버튼)이 실제로 떴으면, 턴이 끝난 뒤에도 사용자 답을 기다리므로 깜빡인다(훅에 막힌 상자는 세지 않는다)
      if (!agentId && String(tool).endsWith('wrap_up') && ok) boxAsk = typeof input.ask === 'string' && input.ask.trim() !== ''
      // 사람이 답한 질문 창만 주인을 바꾼다. 훅이나 오류로 막힌 창은 사람이 본 적이 없다
      if (!agentId && WAITING_TOOLS.includes(tool) && ok) answered = true
      // 뒤에서 도는 것이 실제로 시작됐을 때만 CHAT 빛을 먼저 켠다. 앞에서 끝난 서브에이전트는 켜지 않는다
      const launched = tool === 'Agent' ? ['async_launched', 'remote_launched'].includes(result?.result?.status) : LAUNCHERS.includes(tool) || input.run_in_background === true
      if (!agentId && ok && launched && background === 0) {
        background = 1
        backgroundTasks = [`launch:${tool}`]
        await quietly(() => share($))
      }
      return result
    } finally {
      if (WAITING_TOOLS.includes(tool)) waits.delete(`id:${id}`)
      // 이 호출이 띄운 허락 창의 대기를 지운다. 짝이 없으면 입력이 꼭 맞는 대기만 지운다
      const who = agentId ?? 'main'
      const same = [...asked].filter(([, one]) => one.who === who && one.tool === tool)
      if (typeof id === 'string') askedCalls.delete(id)
      const hit = same.find(([, one]) => one.call === id) ?? same.find(([, one]) => !one.call && Object.keys(one.input).every(k => stable(input[k]) === stable(one.input[k])))
      if (hit) {
        waits.delete(hit[0])
        asked.delete(hit[0])
        answered = true
      }
      // 허락 창이나 질문 창에 답했다면 사용자가 지금 이 세션을 보고 있다. 말을 걸지 않아도 시계를 이 세션으로 가져온다
      if (answered && !headless) await quietly(async () => claim($, await $.session.id()))
      await refresh($)
      if (answered) await quietly(() => share($))
    }
  })

  on('prompt.submit', async ($, e, next) => {
    if (!headless && isPerson(e)) {
      await quietly(async () => {
        await claim($, await $.session.id())
        await share($)
      })
    }

    return next(e)
  })

  on('session.end', async ($, e, next) => {
    // 이 세션을 기다리는 요청이 있으면 시계가 기다리지 않게 바로 알리고, 주인 자리를 비운다. 하나가 틀려도 다른 하나는 한다.
    let session: unknown
    await quietly(async () => {
      session = await $.session.id()
      const { asked } = await command($)
      if (['asked', 'queued'].includes(asked?.state) && asked.session === session) await settle($, asked, 'failed', 'ended')
    })
    turning = false
    waits.clear()
    // 닫히는 세션의 백그라운드 작업은 함께 끝난다. 빛을 끈 값을 먼저 적고 주인 자리를 비운다
    background = 0
    backgroundTasks = []
    await refresh($)
    await quietly(() => share($))
    await quietly(async () => {
      if (session && (await owner($)) === session) await claim($, null)
    })

    return next(e)
  })

  on('turn.step', async function* ($, e, next) {
    const response = yield* next(e)
    const used = response.usage
    if (used) {
      const fresh = used.input_tokens + (used.cache_creation_input_tokens ?? 0) + used.output_tokens
      const total = fresh + (used.cache_read_input_tokens ?? 0)
      await quietly(async () => {
        await update($, current, turn => ({
          total: turn.total + total,
          fresh: turn.fresh + fresh,
          requests: turn.requests + 1,
          subRequests: turn.subRequests + (e.agentId ? 1 : 0),
        }))
        await share($)
      })
    }

    return response
  })

  on('ui.render', { component: 'Pane', requestId: PANE }, async ($, e) => {
    const { Box, Text } = $.ui.resolve(e)
    const now = await $.clock.now()
    const seen = await read($, meter)
    const turn = await read($, current)
    const before = await read($, last)
    const five = seen.limits.find(one => one.kind === 'five_hour')
    const week = seen.limits.find(one => one.kind === 'seven_day')

    const w = say()

    const limit = (name: string, one: Limit | undefined) => (
      <Box flexDirection="column" marginBottom={1}>
        <Text bold>{name}</Text>
        {one ? <Text>{bar(one.percent)} {one.percent}%</Text> : <Text dimColor>{w.later}</Text>}
        {one?.resetsAt && <Text dimColor>{left(one.resetsAt, now)}</Text>}
      </Box>
    )

    const spent = (name: string, one: Turn) => (
      <Box flexDirection="column" marginBottom={1}>
        <Text bold>{name}</Text>
        {one.requests === 0 && <Text dimColor>{w.none}</Text>}
        {one.requests > 0 && <Text>{w.fresh} {tokens(one.fresh)}</Text>}
        {one.requests > 0 && <Text dimColor>{w.total} {tokens(one.total)} · {w.requests(one.requests)}</Text>}
        {one.subRequests > 0 && <Text dimColor>{w.sub(one.subRequests)}</Text>}
      </Box>
    )

    return (
      <Box flexDirection="column">
        {limit(w.five, five)}
        {limit(w.week, week)}
        {spent(w.turn, turn)}
        {spent(w.last, before)}
        <Text bold>{w.size}</Text>
        <Text>{seen.contextTokens === undefined ? w.later : `${tokens(seen.contextTokens)} / ${tokens(seen.contextWindow)}`}</Text>
      </Box>
    )
  })
}
