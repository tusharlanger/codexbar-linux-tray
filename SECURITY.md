# Security Policy

## Supported versions

Only the latest tagged release on `main` is supported.

## Reporting a vulnerability

Please **do not open a public issue** for security problems.

Email the maintainer at **tushar.langer@gmail.com** with:

- A description of the issue and its impact.
- Steps to reproduce or a minimal proof of concept.
- The version of `codexbar-linux-tray`, the upstream `codexbar` CLI, and your distro / desktop environment.

You will get an acknowledgement within 7 days. A fix and coordinated disclosure will follow as fast as the severity warrants.

## Threat model and scope

This project is a thin local front-end. It:

- Spawns the upstream `codexbar` CLI as a subprocess and parses its JSON output.
- Renders into a `Gtk.Menu` attached to an `AyatanaAppIndicator3` indicator.
- Writes nothing to disk and opens no network sockets of its own.
- Uses `xdg-open` to launch URLs (Usage Dashboard, Status Page) when the user clicks those menu items.

Vulnerabilities in the upstream `codexbar` CLI itself should be reported to https://github.com/steipete/CodexBar.
