# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.1] - 2026-04-17

### Changed
- Top-bar label is now just `<n>%` (was `S<n>%`) — the panel position already tells you it's the session meter.

### Added
- `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, issue + PR templates, basic CI workflow, README badges.

## [0.1.0] - 2026-04-17

### Added
- Initial release.
- GNOME AppIndicator that wraps the upstream `codexbar` Linux CLI.
- Top-bar `S<sessionPct>%` label, threshold-coloured icon (yellow ≥ 60 %, red ≥ 85 %).
- Dropdown card with Session / Weekly / Sonnet meters, monthly extras, reset countdowns, pace projection, local cost (today / 30 d) for Claude and Codex.
- `install.sh` that registers a systemd user service (preferred) or a GNOME autostart `.desktop`.
- MIT licence; credits to `steipete/CodexBar` and `ryoppippi/ccusage`.

[Unreleased]: https://github.com/tusharlanger/codexbar-linux-tray/compare/v0.1.1...HEAD
[0.1.1]: https://github.com/tusharlanger/codexbar-linux-tray/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/tusharlanger/codexbar-linux-tray/releases/tag/v0.1.0
