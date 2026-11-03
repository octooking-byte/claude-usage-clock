---
name: token-usage-clock
description: Explain or troubleshoot the Claude Usage Clock desktop clock, which shows Claude Code's 5-hour limit, weekly limit and conversation size on a mechanical clock. Use when the person asks what the clock's dials, lights or controls mean, why it does not appear, why a light stays on, or how to hide, resize, recolour or reset it.
---

# Claude Usage Clock

The mod (`hooks/register.tsx`) writes usage and status to `~/.claude/progress/token-panel.json`. A separate Python window (`window/`) reads that file and draws the clock. It calls no model and uses no network.

## Reading it

| Part | Meaning |
|---|---|
| 5H (big centre dial) | Share of the 5-hour limit used. Digits are time left until it resets; red under 30 minutes |
| WEEK | Share of the 7-day limit used |
| CHAT | Share of the context window the main session's conversation fills |
| Warning light under a dial | That value is at 80% or more |
| Big dial glows | Claude is answering in the main session, or the person is pressing a dial |
| Big dial blinks every 0.3 s | A permission prompt or question in the main session waits for the person |
| CHAT dial glows | A background task (agent, workflow, monitor) runs in the main session |
| Small screen WEEK | Time until the weekly reset |
| Small screen CHAT | Tokens in the current conversation |
| Small screen TURN | New tokens this turn (input, cache writes, output; cache reads excluded), or the last turn once it ends |

## Which session

One clock serves every open session. The **main session** is the one the person last typed in or answered a permission prompt or question in; scheduled or program input does not count. When the main session closes, an open session takes over after 10 s. 5H and WEEK are account-wide; CHAT, the lights and crown compaction belong to the main session. To switch, type once in the wanted session.

## Controls

Three stems on the right: top stem, crown (middle), bottom stem.

| Action | Effect |
|---|---|
| Right-click | Switch form: single clock ↔ dashboard (three dials) |
| Shift + right-click, or `/clock off` | Hide; `/clock` shows it again |
| Click the top stem | Black or white face |
| Scroll over the bottom stem | Size 60% to 140% |
| Grab the crown, move the mouse up or down | Glow colour |
| Pull the crown out, hold 6 s, release | Compact the main session |
| Drag the crescent down, or double-click the big dial | Open or close the small screen |
| Scroll over a dial (either direction) | The hand spins faster and faster |

## Troubleshooting

| Symptom | Check |
|---|---|
| Clock does not appear | Python 3 with `numpy` and `pillow` (`py -3 -m pip install numpy pillow`), or `%LOCALAPPDATA%\TokenClock\token-clock.exe`. Then `/clock`. Start errors are in `~/.claude/progress/token-panel-start.log` |
| No glow while Claude works | The mod loads when Claude Code starts. Fully quit (tray icon in the desktop app) and reopen |
| CHAT glows with nothing running | Read `backgroundTasks` in `token-panel.json`; the light clears after the next answer once that task ends |
| Clock off-screen | Hide it, delete `~/.claude/progress/token-panel-pos.json`, show it |
| Crown pull does nothing | Only the main session is compacted. Type once in the wanted session first |
| Other errors | `~/.claude/progress/token-panel-error.log` |

Read files only to answer. Do not delete a file without the person's yes.
