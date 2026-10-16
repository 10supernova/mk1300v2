# AntRGB (mk1300-linux)

A sleek, native Linux desktop application and CLI for controlling per-key RGB lighting on the **Ant Esports MK1300 V2** 60% mechanical keyboard, tailored for **Omarchy / Arch Linux / Hyprland / Wayland**.

Features a modern **Tokyo Night** dark theme with **automatic Omarchy theme integration**, a live 61-key visualizer canvas, 90 static patterns ported 1:1 from upstream, hardware lighting animation controls, and a custom preset painter.

---

## Upstream Credit & License Compliance

This project is a derivative work ported from the open-source web tool:
- **Upstream Project:** [kickTROLL/mk1300v2_RGB](https://github.com/kickTROLL/mk1300v2_RGB)
- **Original Author:** Yash ([@kickTROLL](https://github.com/kickTROLL))
- **License:** Apache License, Version 2.0 (see [LICENSE](LICENSE) and [NOTICE](NOTICE))

AntRGB replaces WebHID and browser requirements with a native Python + `hidapi` driver and a native GTK4 / libadwaita UI, while strictly reproducing all upstream RGB protocols and pattern mathematical formulas 1:1.

---

## Features (1:1 Port)

1. **Protocol 1:1 Fidelity:**
   - 64-byte command reports with `command-6` wrapper.
   - 56-byte chunked bulk all-key writes.
   - Single-key color writes.
   - Hardware animation configuration flow (Global Config Type 0 update + Mode Template Type 1 update).
   - Upstream byte offsets, chunk sizes, response slices, and timeouts matched 1:1.

2. **90 Static RGB Patterns:**
   - All 90 static patterns from `effects.js` ported with identical HSL conversions, normalized coordinates, and rounding math (5,490 / 5,490 key RGB values match the Node.js reference output).
   - Plus all 50 contrasty patterns from `extra-effects.js` (total 140 patterns available).
   - Grouped by categories: Gradient, Neon/Cyber, Fire/Heat, Ice/Cryo, Dark, Pastel, Metallic, and Contrasty.

3. **Hardware Animation Control:**
   - Modes: 0 (Off), 1 (Static), 2 (Breath), 3 (Swing), 4 (Spin), 5 (Stream), 6 (Bloom), 7 (UDWawe), 8 (Cross), 9 (Rain), 10 (Meteor), 11 (TrigSpread), 12 (TrigSpreadReverse), 13 (TrigSingle), 14 (Soduko), 15 (Tide), 16/20 (UserLight).
   - Controls: Speed (0-4), Brightness (0-4), Direction (0/1), Rainbow/Multi vs Custom Single Color (HSV).
   - Hardware revision toggle: Mode 16 (standard) vs Mode 20 (Rev 2.0).

4. **Accurate 61-Key Matrix Layout:**
   - Esc key mapped to matrix index 21 (quirk preserved from reference).
   - Exact physical proportions and key legends rendered with soft glows.

5. **Tokyo Night & Omarchy UI:**
   - Dark Tokyo Night palette (`#1a1b26`, `#16161e`, `#292e42`, `#c0caf5`, `#7aa2f7`, etc.).
   - Dynamically reads active colors from `~/.config/omarchy/` (`omasettings.json` and `colors.toml`) so the application matches your Omarchy system theme automatically.
   - Interactive 61-key canvas for custom preset painting with fill, clear, undo, and import.

6. **Safety First:**
   - Hardcoded block on command byte `85` (`0x55`, firmware/bootloader/flash) and sub-command `[15, 255]` (factory reset).
   - Only RGB-related commands are ever permitted. The keyboard cannot be bricked.

---

## Hardware Interface & udev Setup

The MK1300 V2 exposes its RGB configuration on a vendor-specific HID interface:
- **Usage Page:** `0xFF00`
- **Usage:** `0x02`
- **VID:** `0x36AE` / **PID:** `0xFE9C` (plus OEM clone VIDs)

Standard users require permission to access `/dev/hidraw*` without root.

### 1. Install udev rule:
```bash
sudo cp udev/99-mk1300.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules
sudo udevadm trigger
```

### 2. Verify device access:
```bash
./mk1300-cli info
```

---

## Installation & Running

### Requirements
- Arch Linux / Omarchy
- `python` (>= 3.10)
- `python-gobject`, `gtk4`, `libadwaita`
- `python-hidapi` (or `pip install --user hidapi`)

### Running Directly from Source:
```bash
# Launch GUI
./mk1300-gui

# Or run CLI commands
./mk1300-cli list-patterns
./mk1300-cli apply-pattern sunset --brightness 100
./mk1300-cli set-key Esc "#ff0000"
./mk1300-cli hw-animation --mode 2 --brightness 4 --speed 2 --color multi
```

### Building Arch Package (PKGBUILD):
```bash
makepkg -si
```

---

## CLI Reference

| Command | Arguments | Description |
|---|---|---|
| `list-patterns` | `[--category <cat>] [--search <str>]` | List all 90+ static patterns with icons |
| `apply-pattern` | `<id> [--brightness 10-100] [--mode 16\|20]` | Apply static pattern to keyboard |
| `set-key` | `<key_name\|index> <#hex>` | Set individual key RGB color |
| `set-all` | `<#hex> [--brightness 10-100]` | Set solid RGB color across all 61 keys |
| `hw-animation` | `--mode <0-16/20> [--brightness 0-4] [--speed 0-4] [--color multi\|#hex]` | Configure hardware lighting animation |
| `get-keymap` | `[--layer 0\|1]` | Read and display live key mappings from keyboard |
| `remap-key` | `<key> <action> [--layer 0\|1]` | Remap a key function on the keyboard |
| `switch-num-layer`| `[--layer 0\|1] [--revert]` | Toggle number row (1..=) between numbers and F1..F12 |
| `info` | none | Query connected keyboard PID, firmware, profile, light config |
| `restore-last` | none | Re-apply last saved pattern and brightness |
| `smoke-test` | none | Run hardware verification test (Esc red, Q green, W blue) |

---

## Official Software on Linux (Companion)

The official Windows software (`MK1300-V21-0-0.exe`) has also been extracted, patched for Linux Electron, and fixed (MK1300 VID/PID enabled, lighting protocols connected):
```bash
# Launch patched official Electron software
./mk1300-official
```

---

## Hyprland & Login Integration

To automatically restore your last applied RGB pattern when logging into Hyprland:

### Option A: Hyprland `exec-once`
Add to `~/.config/hypr/hyprland.conf`:
```ini
exec-once = /home/nova/mk1300-linux/mk1300-cli restore-last
```

### Option B: systemd user service
```bash
mkdir -p ~/.config/systemd/user/
cp systemd/mk1300-restore.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now mk1300-restore.service
```

---

## 1:1 Verification Tests

All static patterns and HID protocol packets are asserted 1:1 against the original Node.js reference driver:

```bash
# Run all test suites
./run_tests.py
```

Results:
- **Pattern Match:** 90/90 static patterns (5,490/5,490 key RGBs) match `reference/effects.js` 100%.
- **Extra Patterns:** 50/50 contrasty patterns (3,050/3,050 key RGBs) match `reference/extra-effects.js` 100%.
- **Protocol Packets:** 100% byte-for-byte packet match for single-key writes, 56-byte chunked bulk writes, hardware animation global config (Type 0), and template config (Type 1).
- **Safety Blocks:** Command 85 and Sub-command `[15, 255]` strictly blocked.

### Hardware Smoke Test:
Once your keyboard is plugged in, run:
```bash
./smoke_test.py
```
This tests:
1. Interface enumeration and config reading
2. `testSingleKey`: Esc = Red, Q = Green, W = Blue
3. Static pattern application: Sunset Dusk
4. Hardware animation: Rainbow Breath mode
