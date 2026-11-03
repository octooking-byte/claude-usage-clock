import { expect, test } from 'claude-code/testing'

const PANE = {
  plugin: 'token-usage-clock',
  component: 'Pane',
  requestId: 'token-panel',
  props: {
    title: 'Token usage',
    isFocused: false,
    bodyColumns: 40,
    placement: 'dock',
    scroll: { offset: 0, bodyRows: 20 },
    view: {},
  },
} as const

// 한국어 윈도우가 아니면 패널은 영어로 그린다. 시험 환경도 그쪽이다
test('값이 오기 전에도 네 칸이 모든 화면에 그려진다', async ($, on) => {
  on('clock.now', () => ({ value: 0 }))

  for (const surface of ['terminal', 'desktop', 'vscode', 'mobile'] as const) {
    const ui = await $.ui.mount({ ...PANE, surface })
    expect((await ui.find({ type: 'Text', text: /5-hour limit/ }))?.text).toBe('5-hour limit')
    expect((await ui.find({ type: 'Text', text: /Weekly limit/ }))?.text).toBe('Weekly limit')
    expect((await ui.find({ type: 'Text', text: /This turn/ }))?.text).toBe('This turn')
    expect((await ui.find({ type: 'Text', text: /Conversation size/ }))?.text).toBe('Conversation size')
    await ui.unmount()
  }
})
