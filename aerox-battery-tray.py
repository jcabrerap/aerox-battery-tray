#!/usr/bin/env python3
"""Tray battery indicator for a SteelSeries mouse, using `rivalcfg --battery-level`.

Shows the battery percentage in the system tray (works on KDE Plasma) and sends
a desktop notification when the battery is low.

Requires: python-pyqt6 (sudo pacman -S python-pyqt6) and rivalcfg.
"""

import glob
import os
import re
import shutil
import signal
import subprocess
import sys

from PyQt6.QtCore import QRect, Qt, QTimer
from PyQt6.QtGui import QAction, QColor, QCursor, QFont, QIcon, QPainter, QPixmap
from PyQt6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

# ---- Settings you may want to change -------------------------------------
CHECK_EVERY_MINUTES = 5   # how often to ask the mouse for its battery level
LOW_PERCENT = 20          # first warning at or below this level
CRITICAL_PERCENT = 10     # second, more urgent warning at or below this level
MOUSE_NAME = "SteelSeries Aerox 3 Wireless"  # shown in the menu and tooltip
CABLE_USB_ID = ("1038", "183a")  # Aerox 3 Wireless USB ID when the cable is plugged in
CABLE_WATCH_SECONDS = 2   # how often to look for the cable (cheap, doesn't call rivalcfg)
# ---------------------------------------------------------------------------

GREEN = "#2e9e4f"
ORANGE = "#e08a00"
RED = "#d33a3a"
BLUE = "#2a7fd4"
GREY = "#6b6b6b"


def make_icon(text, color):
    """Draw a small rounded badge with the given text, as a tray icon."""
    pm = QPixmap(64, 64)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor(color))
    p.drawRoundedRect(2, 10, 60, 44, 10, 10)
    font = QFont()
    font.setBold(True)
    font.setPixelSize(34 if len(text) < 3 else 26)
    p.setFont(font)
    p.setPen(QColor("white"))
    p.drawText(QRect(2, 10, 60, 44), Qt.AlignmentFlag.AlignCenter, text)
    p.end()
    return QIcon(pm)


def read_battery():
    """Return (percent, charging) or None if the mouse could not be read."""
    exe = shutil.which("rivalcfg")
    if not exe:
        return None
    try:
        out = subprocess.run(
            [exe, "--battery-level"], capture_output=True, text=True, timeout=10
        )
    except (subprocess.TimeoutExpired, OSError):
        return None
    text = (out.stdout or "") + (out.stderr or "")
    match = re.search(r"(\d+)\s*%", text)
    if out.returncode != 0 or not match:
        return None
    charging = "charging" in text.lower() and "discharging" not in text.lower()
    return int(match.group(1)), charging


def cable_connected():
    """True if the mouse shows up as a wired-mode USB device (cable plugged into the PC)."""
    vendor, product = CABLE_USB_ID
    for dev in glob.glob("/sys/bus/usb/devices/*"):
        try:
            with open(os.path.join(dev, "idVendor")) as f:
                if f.read().strip() != vendor:
                    continue
            with open(os.path.join(dev, "idProduct")) as f:
                if f.read().strip() == product:
                    return True
        except OSError:
            continue
    return False


class BatteryTray:
    def __init__(self, app):
        self.app = app
        self.last_percent = None
        self.cable = cable_connected()
        self.warned_low = False
        self.warned_critical = False

        self.tray = QSystemTrayIcon()
        self.tray.setIcon(make_icon("?", GREY))
        self.tray.setToolTip("Mouse battery: checking...")

        menu = QMenu()
        title_action = QAction(MOUSE_NAME, menu)
        title_action.setEnabled(False)
        menu.addAction(title_action)
        self.status_action = QAction("Checking...")
        self.status_action.setEnabled(False)
        menu.addAction(self.status_action)
        menu.addSeparator()
        refresh = QAction("Refresh now", menu)
        refresh.triggered.connect(self.check)
        menu.addAction(refresh)
        quit_action = QAction("Quit", menu)
        quit_action.triggered.connect(app.quit)
        menu.addAction(quit_action)
        self.menu = menu  # keep a reference so it is not garbage collected
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self.on_activated)
        self.tray.show()

        self.timer = QTimer()
        self.timer.timeout.connect(self.check)
        self.timer.start(CHECK_EVERY_MINUTES * 60 * 1000)

        self.cable_timer = QTimer()
        self.cable_timer.timeout.connect(self.watch_cable)
        self.cable_timer.start(CABLE_WATCH_SECONDS * 1000)
        self.check()

    def on_activated(self, reason):
        # Left click: show the same menu as right click
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.menu.popup(QCursor.pos())

    def set_state(self, label, tooltip, color):
        self.tray.setIcon(make_icon(label, color))
        self.tray.setToolTip(f"{MOUSE_NAME}\n{tooltip}")
        self.status_action.setText(tooltip)

    def watch_cable(self):
        now = cable_connected()
        if now == self.cable:
            return
        self.cable = now
        if now:
            # Instant feedback; the exact level follows once the mouse has settled
            label = str(self.last_percent) if self.last_percent is not None else "USB"
            self.set_state(label, "Mouse connected by cable (charging)", BLUE)
            QTimer.singleShot(3000, self.check)
        else:
            QTimer.singleShot(1500, self.check)

    def check(self):
        result = read_battery()
        if result is None:
            if self.cable:
                label = str(self.last_percent) if self.last_percent is not None else "USB"
                self.set_state(label, "Mouse connected by cable (charging)", BLUE)
            else:
                self.set_state(
                    "?",
                    "Mouse not reachable (asleep, unplugged or rivalcfg missing)",
                    GREY,
                )
            return

        percent, charging = result
        self.last_percent = percent
        charging = charging or self.cable
        if charging:
            self.set_state(str(percent), f"Mouse battery: {percent}% (charging)", BLUE)
            self.warned_low = False
            self.warned_critical = False
            return

        if percent <= CRITICAL_PERCENT:
            color = RED
        elif percent <= LOW_PERCENT:
            color = ORANGE
        else:
            color = GREEN
        self.set_state(str(percent), f"Mouse battery: {percent}%", color)

        # Reset the warnings once the battery has recovered
        if percent > LOW_PERCENT:
            self.warned_low = False
            self.warned_critical = False

        if percent <= CRITICAL_PERCENT and not self.warned_critical:
            self.warned_critical = True
            self.warned_low = True
            self.tray.showMessage(
                "Mouse battery critical",
                f"Only {percent}% left. Plug it in now.",
                QSystemTrayIcon.MessageIcon.Critical,
                15000,
            )
        elif percent <= LOW_PERCENT and not self.warned_low:
            self.warned_low = True
            self.tray.showMessage(
                "Mouse battery low",
                f"{percent}% left. Time to charge it.",
                QSystemTrayIcon.MessageIcon.Warning,
                10000,
            )


def main():
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    if not QSystemTrayIcon.isSystemTrayAvailable():
        print("No system tray available.", file=sys.stderr)
        return 1
    _tray = BatteryTray(app)  # noqa: F841 (must stay alive)
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
