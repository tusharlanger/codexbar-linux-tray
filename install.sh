#!/usr/bin/env bash
# Installer for codexbar-linux-tray.
# Installs the script into ~/.local/bin and registers either a systemd
# user service (preferred) or a GNOME autostart .desktop entry.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="${HOME}/.local/bin"
mkdir -p "${BIN_DIR}"

# 1. codexbar CLI prerequisite
if ! command -v codexbar >/dev/null 2>&1; then
  echo "[!] codexbar CLI not found on PATH."
  echo "    Install from https://github.com/steipete/CodexBar/releases"
  echo "    Linux x86_64 example:"
  echo "      curl -L -o /tmp/codexbar.tgz \\"
  echo "        https://github.com/steipete/CodexBar/releases/latest/download/CodexBarCLI-linux-x86_64.tar.gz"
  echo "      tar -xzf /tmp/codexbar.tgz -C ${BIN_DIR}"
  exit 1
fi

# 2. Python GTK + AppIndicator bindings
if ! python3 -c "import gi; gi.require_version('AyatanaAppIndicator3','0.1'); from gi.repository import AyatanaAppIndicator3" >/dev/null 2>&1; then
  echo "[!] Missing python3-gi AppIndicator bindings."
  echo "    Ubuntu/Debian:  sudo apt install -y gir1.2-ayatanaappindicator3-0.1 python3-gi"
  echo "    Fedora:         sudo dnf install -y libayatana-appindicator-gtk3 python3-gobject"
  echo "    Arch:           sudo pacman -S libayatana-appindicator python-gobject"
  exit 1
fi

# 3. GNOME AppIndicator extension reminder (Ubuntu has it preinstalled)
if command -v gnome-extensions >/dev/null 2>&1; then
  if ! gnome-extensions list 2>/dev/null | grep -qi appindicator; then
    echo "[!] No AppIndicator GNOME extension detected."
    echo "    Install one of:  gnome-shell-extension-appindicator (Debian/Ubuntu)"
    echo "                     gnome-shell-extension-appindicator (Fedora)"
    echo "                     'AppIndicator and KStatusNotifierItem Support' from extensions.gnome.org"
  fi
fi

# 4. Install the script
install -m 755 "${SCRIPT_DIR}/codexbar-tray.py" "${BIN_DIR}/codexbar-tray.py"
echo "[+] Installed ${BIN_DIR}/codexbar-tray.py"

# 5. Choose launcher: systemd user service (preferred) or autostart .desktop
if command -v systemctl >/dev/null 2>&1; then
  UNIT_DIR="${HOME}/.config/systemd/user"
  mkdir -p "${UNIT_DIR}"
  install -m 644 "${SCRIPT_DIR}/systemd/codexbar-tray.service" "${UNIT_DIR}/codexbar-tray.service"
  systemctl --user daemon-reload
  systemctl --user enable --now codexbar-tray.service
  echo "[+] Enabled systemd user service: codexbar-tray.service"
  echo "    Manage:  systemctl --user {status,restart,stop} codexbar-tray"
else
  AUTO_DIR="${HOME}/.config/autostart"
  mkdir -p "${AUTO_DIR}"
  install -m 644 "${SCRIPT_DIR}/autostart/codexbar-tray.desktop" "${AUTO_DIR}/codexbar-tray.desktop"
  nohup python3 "${BIN_DIR}/codexbar-tray.py" >/dev/null 2>&1 &
  disown
  echo "[+] Installed autostart .desktop and launched in background"
fi

echo
echo "Done. Look for the tray icon in your top bar."
echo "If nothing appears, ensure your GNOME AppIndicator extension is enabled and log out/in."
