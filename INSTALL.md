# Installing Claude Usage Clock (for Claude)

Someone asked you to install this plugin. It works on Windows 10 or later only; on any other system, stop and tell them.

## 1. Install the plugin

`/plugin` does not run in the desktop app's Code tab or the VS Code panel, so install it from the shell with the Claude Code CLI. The desktop app ships its own `claude.exe`, which may not be on PATH.

PowerShell:

```powershell
$c = (Get-Command claude -ErrorAction SilentlyContinue).Source
if (-not $c) { $c = $env:CLAUDE_CODE_EXECPATH }
if (-not $c) { $c = (Get-ChildItem "$env:LOCALAPPDATA\Claude-Data" -Recurse -Filter claude.exe -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1).FullName }
& $c plugin install token-usage-clock --marketplace octooking-byte/claude-usage-clock
```

Bash (Git Bash on Windows):

```bash
"${CLAUDE_CODE_EXECPATH:-claude}" plugin install token-usage-clock --marketplace octooking-byte/claude-usage-clock
```

It prints `Successfully installed plugin: token-usage-clock@token-usage-clock`.

## 2. Tell the person

- Start a new session. The plugin loads there.
- The first time, the clock sets itself up (about a minute) and appears on the desktop. Python is not needed.
- If it does not appear, type `/clock`. If it still does not, the reason is in `%USERPROFILE%\.claude\progress\token-panel-start.log`.

Do nothing else: no other downloads, no settings changes.
