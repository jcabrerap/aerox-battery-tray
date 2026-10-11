#!/usr/bin/env bash
# Installs the Aerox 3 Wireless battery tray indicator (CachyOS / Arch, KDE Plasma).
# Safe to re-run: it just updates the script and desktop entries.
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
bin_dir="$HOME/.local/bin"
apps_dir="$HOME/.local/share/applications"
autostart_dir="$HOME/.config/autostart"
script="$bin_dir/aerox-battery-tray.py"

echo "==> Installing PyQt6"
sudo pacman -S --needed --noconfirm python-pyqt6

echo "==> Checking for rivalcfg"
if ! command -v rivalcfg >/dev/null 2>&1; then
    if command -v paru >/dev/null 2>&1; then
        paru -S --needed rivalcfg
    elif command -v yay >/dev/null 2>&1; then
        yay -S --needed rivalcfg
    else
        echo "rivalcfg is not installed and no AUR helper was found."
        echo "Run:  sudo pacman -S paru   then   paru -S rivalcfg   and re-run this script."
        exit 1
    fi
fi

echo "==> Setting up udev rules (so rivalcfg works without sudo)"
sudo rivalcfg --update-udev
sudo udevadm control --reload-rules
sudo udevadm trigger

echo "==> Installing the tray script"
mkdir -p "$bin_dir" "$apps_dir" "$autostart_dir"
install -m 755 "$here/aerox-battery-tray.py" "$script"

echo "==> Creating start menu and autostart entries"
cat > "$apps_dir/aerox-battery-tray.desktop" << EOF
[Desktop Entry]
Type=Application
Name=Mouse Battery Tray
Comment=Battery indicator for the Aerox 3 Wireless
Exec=python $script
Icon=battery
Terminal=false
Categories=Utility;
Actions=Quit;

[Desktop Action Quit]
Name=Quit Mouse Battery Tray
Exec=pkill -f aerox-battery-tray.py
EOF

cat > "$autostart_dir/aerox-battery-tray.desktop" << EOF
[Desktop Entry]
Type=Application
Name=Mouse Battery Tray
Exec=python $script
Icon=battery
Terminal=false
EOF

# Older manual setups used a different autostart file name; remove it to avoid two copies
rm -f "$autostart_dir/aerox-battery.desktop"

kbuildsycoca6 >/dev/null 2>&1 || true

echo "==> Starting it now"
pkill -f aerox-battery-tray.py || true
nohup python "$script" >/dev/null 2>&1 &
disown || true

echo "Done. Look for the battery badge in the system tray."
