# Aerox 3 Wireless battery tray

A small KDE Plasma system-tray indicator for the SteelSeries Aerox 3 Wireless.
It reads the battery with `rivalcfg --battery-level`, shows the percentage as a
colored badge, and sends a notification when the battery is low.

- Green above 20%, orange at 20% or below, red at 10% or below, blue while charging
- Plugging in the cable is detected within ~2 seconds (USB ID `1038:183a`)
- Left or right click the badge for "Refresh now" and "Quit"
- Thresholds and check interval are at the top of `aerox-battery-tray.py`

## Install (CachyOS / Arch + KDE Plasma)

    git clone <your-repo-url> aerox-battery-tray
    cd aerox-battery-tray
    ./install.sh

If `./install.sh` says permission denied, run `bash install.sh` instead.

The installer:

1. installs `python-pyqt6` with pacman,
2. installs `rivalcfg` from the AUR (needs `paru` or `yay`; install with `sudo pacman -S paru`),
3. sets up rivalcfg's udev rules,
4. copies the script to `~/.local/bin/`,
5. adds a start menu entry and a login autostart entry,
6. starts the app.

It is safe to re-run.

## Uninstall

    ./uninstall.sh

This leaves `rivalcfg` and `python-pyqt6` installed.

## Notes

- The charging badge only reacts instantly when the cable is plugged into a
  computer. With a plain USB charger it updates at the next periodic check.
- If the badge doesn't appear, check the hidden-items arrow in the Plasma tray.
