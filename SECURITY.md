# Security policy

## Supported versions

Only the latest release gets fixes. Update with `claude plugin update token-usage-clock@token-usage-clock`, or reinstall the line in the README.

## Reporting a vulnerability

Please do not open a public issue. Use the private report form instead:
https://github.com/octooking-byte/claude-usage-clock/security/advisories/new

Include what you ran, what happened, and the Claude Code version (`claude --version`). Expect a first reply within 7 days.

## What the mod runs

The full list is in the README under "How it works". In short: the clock window, one `reg query` for the language, `/compact` when you pull the crown, and, only the first time the clock cannot start, `pip install --user numpy pillow` or a download of the release zip that is kept only if its SHA-256 matches the value in `hooks/register.tsx`. Every command runs from the plugin's own folder.
