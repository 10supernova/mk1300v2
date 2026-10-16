"""
mk1300-win.py  —  Windows entry point for MK1300 V2 CLI controller.

This launcher provides the full CLI experience on Windows using the
bundled Python runtime (no GTK4 GUI on Windows — the full native GUI
runs on Linux only).

Usage (after install or from extracted folder):
    mk1300-win.exe list-patterns
    mk1300-win.exe apply-pattern sunset --brightness 80
    mk1300-win.exe set-key Esc #ff0000
    mk1300-win.exe hw-animation --mode 2 --speed 2 --brightness 4 --color multi
    mk1300-win.exe info
"""

import sys
import os

# Ensure the bundled mk1300 package is found when running as a frozen .exe
if getattr(sys, "frozen", False):
    _base = sys._MEIPASS  # type: ignore[attr-defined]
else:
    _base = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, _base)

from mk1300.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
