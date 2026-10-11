#!/usr/bin/env bash
# Removes the tray indicator. Does not remove rivalcfg or PyQt6.
set -u

pkill -f aerox-battery-tray.py || true
rm -f "$HOME/.local/bin/aerox-battery-tray.py"
rm -f "$HOME/.local/share/applications/aerox-battery-tray.desktop"
rm -f "$HOME/.config/autostart/aerox-battery-tray.desktop"
rm -f "$HOME/.config/autostart/aerox-battery.desktop"
kbuildsycoca6 >/dev/null 2>&1 || true
echo "Removed."
