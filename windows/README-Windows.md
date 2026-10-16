# MK1300 RGB Controller — Windows

> **CLI-only on Windows.** The full native GTK4 GUI runs on Linux (Arch/Omarchy).
> On Windows you get the complete CLI: apply patterns, set per-key colours,
> configure hardware animations, and query device info.

---

## Installing (Windows)

### Option A — Download the installer (recommended)

Download **`mk1300-win-setup-1.0.0.exe`** from the
[Releases page](https://github.com/supernova10/mk1300-linux/releases) and run it.

The installer:
- Installs `mk1300-win.exe` to `%ProgramFiles%\MK1300RGB\`
- Optionally adds it to your `PATH`
- Creates a Start Menu entry

No Python or GTK required — everything is bundled.

### Option B — Standalone portable exe

Download **`mk1300-win.exe`** from Releases and place it anywhere.
Run from Command Prompt or PowerShell.

---

## Usage

Open **Command Prompt** or **PowerShell**:

```cmd
mk1300-win info
mk1300-win list-patterns
mk1300-win apply-pattern sunset --brightness 80
mk1300-win set-key Esc #ff0000
mk1300-win set-all #00ffff
mk1300-win hw-animation --mode 2 --speed 2 --brightness 4 --color multi
mk1300-win restore-last
```

---

## Building from Source (Windows)

Requirements: Python 3.10+, Inno Setup 6 (optional, for the installer).

```cmd
git clone https://github.com/supernova10/mk1300-linux.git
cd mk1300-linux
windows\build-windows.bat
```

This produces `dist\mk1300-win.exe` and (if Inno Setup is installed)
`dist\mk1300-win-setup-1.0.0.exe`.

---

## HID Driver Note

Windows ships a built-in HID driver that `hidapi` uses directly.
**No extra driver installation is needed.**

If the keyboard isn't detected, check Device Manager to confirm
it appears under **Human Interface Devices** with VID `36AE`.

---

## Reporting Issues

[Open an issue on GitHub](https://github.com/supernova10/mk1300-linux/issues)
