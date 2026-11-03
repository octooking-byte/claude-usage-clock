# Changelog

All notable changes to this project are listed here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and versions follow [Semantic Versioning](https://semver.org/). The plugin version is in `.claude-plugin/plugin.json`; clock builds for people without Python are the `v*` releases.

## [Unreleased]

## [0.1.4] - 2026-11-04

### Added
- `THIRD-PARTY-NOTICES.txt` inside the clock zip: the licences of Python, NumPy (with OpenBLAS), Pillow and the PyInstaller bootloader that the exe redistributes.
- `SECURITY.md`, `CODE_OF_CONDUCT.md` and this changelog. Private vulnerability reporting is on.

### Changed
- Without Python, the mod downloads the v0.1.4 clock build (same clock, now with the licence notices).

## [0.1.3] - 2026-11-04

### Changed
- Without Python, the mod downloads the v0.1.2 clock build, which has the crown fix below and is built without UPX.

## [0.1.2] - 2026-11-04

### Added
- `INSTALL.md`: in the desktop app or VS Code, send Claude the repository link and ask it to install; it finds the Claude Code CLI and runs the install.

### Changed
- The clock build no longer uses UPX, which drew antivirus false positives.

### Security
- Every command the mod runs starts from the plugin's own folder, and pip runs with `-I`, so a `pip.py` or `py.exe` in the folder you opened cannot run in their place.

## [0.1.1] - 2026-11-04

### Added
- One-line install: the first time the clock cannot start, the mod sets it up by itself (pip, or the release zip checked by SHA-256).

### Fixed
- Dashboard layout: pulling the crown while an earlier compaction still waits now shakes the clock instead of doing nothing.

## [0.1.0] - 2026-11-03

### Added
- First public release.

[Unreleased]: https://github.com/octooking-byte/claude-usage-clock/compare/v0.1.4...HEAD
[0.1.4]: https://github.com/octooking-byte/claude-usage-clock/releases/tag/v0.1.4
[0.1.3]: https://github.com/octooking-byte/claude-usage-clock/commit/b5e7b6e
[0.1.2]: https://github.com/octooking-byte/claude-usage-clock/releases/tag/v0.1.2
[0.1.1]: https://github.com/octooking-byte/claude-usage-clock/commit/d318b99
[0.1.0]: https://github.com/octooking-byte/claude-usage-clock/releases/tag/v0.1.0
