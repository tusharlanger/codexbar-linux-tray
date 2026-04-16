# Contributing

Thanks for your interest in `codexbar-linux-tray`! This is a small project, so contribution is informal — just keep things simple and discuss before large changes.

## Ground rules

- **One thing per PR.** A bug fix and a new feature should be two PRs.
- **Match the existing style.** Pure Python 3, no external runtime deps beyond `PyGObject` / GTK / `AyatanaAppIndicator3`. The whole point is that this stays a single drop-in script.
- **Don't break the upstream contract.** All data must come from the official `codexbar` CLI subprocess. We don't talk to provider APIs directly.
- **Keep it Linux-desktop friendly.** AppIndicator first; KDE Plasma / Hyprland / Sway / Wayland-only paths are welcome but should not regress GNOME/X11.

## Dev loop

```bash
git clone https://github.com/tusharlanger/codexbar-linux-tray.git
cd codexbar-linux-tray

# run the script directly
python3 codexbar-tray.py

# or restart the installed service after editing
systemctl --user restart codexbar-tray
journalctl --user -u codexbar-tray -f
```

## Filing issues

- **Bug reports** should include: distro + version, GNOME/desktop version, `codexbar --version`, `python3 -V`, output of `gnome-extensions list | grep -i appindicator`, any tracebacks from `journalctl --user -u codexbar-tray`.
- **Feature requests** should describe the desktop environment they target and whether the upstream `codexbar` CLI already exposes the data via `codexbar usage --json` or `codexbar cost --json`.

## Pull requests

- Open against `main`.
- Add a line to `CHANGELOG.md` under `## [Unreleased]`.
- If your change adds a config knob, document it in the README's **Configure** table.
- New providers in the dropdown should degrade gracefully when the upstream CLI returns an error or the user isn't signed in.

## Code of Conduct

By participating you agree to abide by the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md).
