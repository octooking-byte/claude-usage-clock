# Contributing

Issues and pull requests are welcome, in English or Korean.

## Before you start

- Bug: use the bug report form. A screenshot of the clock and `%USERPROFILE%\.claude\progress\token-panel-error.log` help most.
- macOS, Linux and Codex support are tracked as platform issues. Comment there before starting a port.
- Changes to images or dial HTML fall under [LICENSE-DESIGN.md](LICENSE-DESIGN.md). Code changes are MIT.

## Layout

| Path | Language | What it does |
|---|---|---|
| `hooks/register.tsx` | TypeScript | The Claude Code mod: reads usage and session events, writes `~/.claude/progress/token-panel.json` |
| `window/window.py` | Python | The desktop window: input, file reading, drawing loop |
| `window/gauge.py` | Python | Dashboard (three dials) behaviour: hands, springs, lights |
| `window/chrono.py` | Python | Single-clock behaviour, built on `gauge.py` |
| `window/dial.py`, `window/chrono_dial.py` | Python | Drawing each frame from the PNG layers |
| `window/morph.py` | Python | The animation between the two forms |
| `window/launch.py` | Python | Starts the window detached from Claude Code |

## Korean names in the code

Comments and most Python names are in Korean. The table below covers the names you will meet first.

| Name | Meaning | Name | Meaning |
|---|---|---|---|
| 계기 | gauge (dashboard state) | 크로노 | chronograph (single clock state) |
| 변신 | form change (morph) | 시계들 | dial table |
| 바늘 | hand | 판 | dial plate |
| 용두 | crown | 기둥 | stem (pusher) |
| 액정 | small LCD screen | 초승달 | crescent handle under the LCD |
| 빛 | glow | 붉음 | red warning amount |
| 공전 | orbit of the small dials | 태엽 | winding |
| 휠 | mouse wheel | 틱 | tick (one frame step) |
| 그림 | draw a frame | 주인 | owner (main session) |
| 주간 | weekly limit | 대화 | conversation (CHAT) |
| 다섯시간 | 5-hour limit | 덮개 | value held while compaction runs |

## Checks

```
claude plugin validate .
claude plugin test .
```

Fully quit and restart Claude Code to load a changed mod.
