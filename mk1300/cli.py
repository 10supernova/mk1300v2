"""
Command-line interface for MK1300 V2 RGB controller.

Ported from https://github.com/kickTROLL/mk1300v2_RGB (Apache-2.0)
Original work Copyright 2024 Yash (kickTROLL)
Modified: CLI implementation for mk1300-linux
"""

import argparse
import sys
import time
from typing import Optional, Tuple

from .driver import HIDDriver
from .layout import KEYBOARD_LAYOUT, KEY_COUNT, Key
from .effects import PATTERNS, PATTERNS_BY_ID, RGBColor
from .extra_effects import EXTRA_PATTERNS_BY_ID
from .categories import ALL_PATTERNS, ALL_PATTERNS_BY_ID, CATEGORIES, get_category
from .config import load_settings, save_settings


def parse_hex_color(hex_str: str) -> Tuple[int, int, int]:
    """Parse #RRGGBB or RRGGBB string into (r, g, b) tuple."""
    cleaned = hex_str.strip().lstrip("#")
    if len(cleaned) == 3:
        cleaned = "".join([c * 2 for c in cleaned])
    if len(cleaned) != 6:
        raise ValueError(f"Invalid hex color format: {hex_str}. Use #RRGGBB or RRGGBB.")
    val = int(cleaned, 16)
    return ((val >> 16) & 0xFF, (val >> 8) & 0xFF, val & 0xFF)


def hex_to_hsv(hex_str: str) -> dict:
    """Convert hex color to HSV dict {h, s, v} with 0-255 ranges matching app.js."""
    r, g, b = parse_hex_color(hex_str)
    rf, gf, bf = r / 255.0, g / 255.0, b / 255.0
    cmax = max(rf, gf, bf)
    cmin = min(rf, gf, bf)
    delta = cmax - cmin

    if delta == 0:
        h = 0.0
    elif cmax == rf:
        h = ((gf - bf) / delta + (6.0 if gf < bf else 0.0))
    elif cmax == gf:
        h = ((bf - rf) / delta + 2.0)
    else:
        h = ((rf - gf) / delta + 4.0)

    h /= 6.0
    s = 0.0 if cmax == 0 else (delta / cmax)
    v = cmax

    return {
        "h": round(h * 255.0),
        "s": round(s * 255.0),
        "v": round(v * 255.0),
    }


def find_key(target: str) -> Key:
    """Find key by name (case-insensitive) or by hardware LED index."""
    # Check if target is an integer hardware index
    try:
        idx = int(target)
        for k in KEYBOARD_LAYOUT:
            if k.index == idx:
                return k
        # If integer doesn't match an active 61 key layout, create ad-hoc Key
        return Key(index=idx, x=0, y=0, w=1, h=1, name=f"Key_{idx}")
    except ValueError:
        pass

    target_lower = target.lower()
    for k in KEYBOARD_LAYOUT:
        if k.name.lower() == target_lower:
            return k

    raise ValueError(f"Key '{target}' not found in layout. Valid names include Esc, Tab, Q, Space, etc.")


def cmd_list_patterns(args: argparse.Namespace) -> int:
    """List available static RGB patterns."""
    cat_filter = args.category.lower() if args.category else None
    search_filter = args.search.lower() if args.search else None

    print(f"{'ID':<16} {'CATEGORY':<12} {'NAME':<24} {'ICON'}")
    print("-" * 60)

    count = 0
    for p in ALL_PATTERNS:
        cat = get_category(p.id)
        if cat_filter and cat_filter != "all" and cat != cat_filter:
            continue
        if search_filter and (search_filter not in p.id.lower() and search_filter not in p.name.lower()):
            continue
        print(f"{p.id:<16} {cat:<12} {p.name:<24} {p.icon}")
        count += 1

    print("-" * 60)
    print(f"Total patterns listed: {count}")
    return 0


def cmd_apply_pattern(args: argparse.Namespace) -> int:
    """Apply a static pattern to the keyboard."""
    pat_id = args.id
    if pat_id not in ALL_PATTERNS_BY_ID:
        print(f"Error: Unknown pattern '{pat_id}'. Run 'list-patterns' to view available IDs.", file=sys.stderr)
        return 1

    p = ALL_PATTERNS_BY_ID[pat_id]
    brightness = max(10, min(100, args.brightness))
    user_mode = args.mode or 16

    print(f"Applying pattern: {p.icon} {p.name} (Brightness: {brightness}%, Mode: {user_mode})...")

    driver = HIDDriver(on_log=print)
    try:
        driver.connect()
    except Exception as e:
        print(f"Connection failed: {e}", file=sys.stderr)
        return 1

    try:
        # Step 1: activate custom userlight mode
        driver.set_hardware_animation(user_mode, 4)

        # Step 2: compute colors with brightness
        br_factor = brightness / 100.0
        colors = p.fn(KEYBOARD_LAYOUT)

        flat = [0] * (KEY_COUNT * 3)
        for i, key in enumerate(KEYBOARD_LAYOUT):
            if i < len(colors):
                c = colors[i]
                flat[key.index * 3] = round(c.r * br_factor)
                flat[key.index * 3 + 1] = round(c.g * br_factor)
                flat[key.index * 3 + 2] = round(c.b * br_factor)

        driver.set_all_key_colors(flat, KEY_COUNT)
        print(f"✓ Successfully applied '{p.name}' to keyboard!")

        # Update saved settings
        settings = load_settings()
        settings["current_pattern_id"] = pat_id
        settings["brightness"] = brightness
        settings["user_light_mode"] = user_mode
        save_settings(settings)
        return 0
    except Exception as e:
        print(f"Error applying pattern: {e}", file=sys.stderr)
        return 1
    finally:
        driver.disconnect()


def cmd_set_key(args: argparse.Namespace) -> int:
    """Set individual key color."""
    try:
        key = find_key(args.key)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    try:
        r, g, b = parse_hex_color(args.hex)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    print(f"Setting {key.name} (HW index {key.index}) to RGB({r}, {g}, {b})...")
    driver = HIDDriver(on_log=print)
    try:
        driver.connect()
        driver.set_key_color(key.index, r, g, b)
        print(f"✓ Set {key.name} to {args.hex}")
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    finally:
        driver.disconnect()


def cmd_set_all(args: argparse.Namespace) -> int:
    """Set all keys to a single solid RGB color."""
    try:
        r, g, b = parse_hex_color(args.hex)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    brightness = max(10, min(100, args.brightness))
    user_mode = args.mode or 16
    br_factor = brightness / 100.0
    r_adj = round(r * br_factor)
    g_adj = round(g * br_factor)
    b_adj = round(b * br_factor)

    print(f"Setting all 61 keys to RGB({r_adj}, {g_adj}, {b_adj}) (Brightness: {brightness}%)...")
    driver = HIDDriver(on_log=print)
    try:
        driver.connect()
        driver.set_hardware_animation(user_mode, 4)

        flat = [0] * (KEY_COUNT * 3)
        for key in KEYBOARD_LAYOUT:
            flat[key.index * 3] = r_adj
            flat[key.index * 3 + 1] = g_adj
            flat[key.index * 3 + 2] = b_adj

        driver.set_all_key_colors(flat, KEY_COUNT)
        print(f"✓ All keys set to {args.hex}!")
        return 0
    except Exception as e:
        print(f"Error setting key colors: {e}", file=sys.stderr)
        return 1
    finally:
        driver.disconnect()


def cmd_hw_animation(args: argparse.Namespace) -> int:
    """Configure onboard hardware lighting animation."""
    mode = args.mode
    brightness = max(0, min(4, args.brightness))
    speed = max(0, min(4, args.speed))
    direction = 1 if args.direction else 0

    hsv = None
    color_mode = 0
    if args.color.lower() != "multi":
        try:
            hsv = hex_to_hsv(args.color)
            color_mode = 1
        except Exception as e:
            print(f"Invalid color hex '{args.color}': {e}", file=sys.stderr)
            return 1

    print(f"Setting HW Animation: mode={mode}, brightness={brightness}, speed={speed}, colorMode={color_mode}...")
    driver = HIDDriver(on_log=print)
    try:
        driver.connect()
        driver.set_hardware_animation(mode, brightness, speed, color_mode, direction, hsv)
        print("✓ Hardware animation applied successfully!")

        settings = load_settings()
        settings["hw_mode"] = mode
        settings["hw_bright"] = brightness
        settings["hw_speed"] = speed
        settings["hw_color"] = args.color
        save_settings(settings)
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    finally:
        driver.disconnect()


def cmd_info(args: argparse.Namespace) -> int:
    """Display connected keyboard information and config."""
    driver = HIDDriver(on_log=print)
    try:
        info = driver.connect()
        print("\n--- MK1300 V2 Hardware Info ---")
        print(f"Product:       {info.get('product_name')}")
        print(f"VID / PID:     0x{info.get('vendor_id', 0):04X} / 0x{info.get('product_id', 0):04X}")
        print(f"Device Path:   {info.get('path')}")

        try:
            cfg = driver.get_keyboard_config()
            print(f"Firmware Ver:  {cfg.get('firmware')}")
            print(f"Config PID:    0x{cfg.get('pid', 0):04X}")
            print(f"Profile:       {cfg.get('profile')}")
            print(f"Battery:       {cfg.get('battery')}%")
        except Exception as e:
            print(f"Could not read keyboard config: {e}")

        try:
            light = driver.get_light_config()
            print(f"Light Mode:    {light.get('mode')}")
            print(f"Brightness:    {light.get('brightness')} / 4")
            print(f"Speed:         {light.get('speed')} / 4")
        except Exception as e:
            print(f"Could not read light config: {e}")

        return 0
    except Exception as e:
        print(f"Could not connect to device: {e}", file=sys.stderr)
        return 1
    finally:
        driver.disconnect()


def cmd_get_keymap(args: argparse.Namespace) -> int:
    """Read and display key mappings from the keyboard firmware."""
    driver = HIDDriver()
    try:
        driver.connect()
        layer = args.layer
        print(f"Reading Layer {layer} key mappings from keyboard...")
        mappings = driver.get_layout_key_mappings(layer=layer)
        from .keycodes import describe_key_tuple, get_default_mappings
        default_map = get_default_mappings(layer)
        for i, (key, tup) in enumerate(zip(KEYBOARD_LAYOUT, mappings)):
            desc = describe_key_tuple(tup)
            def_tup = default_map[i] if i < len(default_map) else (0, 0, 0, 0)
            is_mod = (tup != def_tup)
            mod_str = " [⚡ MODIFIED]" if is_mod else ""
            print(f"Key #{i:02d} [{key.name:6s}] (HW Matrix #{key.index:3d}): {desc}{mod_str}  (raw={tup})")
        return 0
    except Exception as e:
        print(f"Failed to read key mappings: {e}", file=sys.stderr)
        return 1
    finally:
        driver.disconnect()


def cmd_remap_key(args: argparse.Namespace) -> int:
    """Remap a single key on specified layer."""
    driver = HIDDriver(on_log=print)
    try:
        driver.connect()
        key_idx = None
        if args.key.isdigit():
            val = int(args.key)
            if 0 <= val < len(KEYBOARD_LAYOUT):
                key_idx = val
            else:
                # Might be hardware matrix index
                for i, k in enumerate(KEYBOARD_LAYOUT):
                    if k.index == val:
                        key_idx = i
                        break
        else:
            for i, k in enumerate(KEYBOARD_LAYOUT):
                if k.name.lower() == args.key.lower():
                    key_idx = i
                    break
        if key_idx is None or not (0 <= key_idx < len(KEYBOARD_LAYOUT)):
            print(f"Error: Unknown key '{args.key}'. Valid keys include Esc, 1..0, Q, Space, ?, Up, etc.", file=sys.stderr)
            return 1

        target_key = KEYBOARD_LAYOUT[key_idx]

        from .keycodes import ALL_ACTIONS
        action = None
        for a in ALL_ACTIONS:
            if a.name.lower() == args.action.lower():
                action = a
                break
        if not action:
            print(f"Error: Unknown action '{args.action}'.", file=sys.stderr)
            return 1

        driver.set_key_mapping(
            matrix_index=target_key.index,
            key_type=action.key_type,
            code1=action.code1,
            code2=action.code2,
            code3=action.code3,
            layer=args.layer,
        )
        print(f"✓ Successfully remapped key #{key_idx} ({target_key.name}, HW #{target_key.index}) to '{action.name}' on Layer {args.layer}!")
        return 0
    except Exception as e:
        print(f"Failed to remap key: {e}", file=sys.stderr)
        return 1
    finally:
        driver.disconnect()


def cmd_switch_num_layer(args: argparse.Namespace) -> int:
    """Switch number row (1..=) to F1..F12 (or back to numbers) for testing."""
    driver = HIDDriver(on_log=print)
    try:
        driver.connect()
        enable_f = not args.revert
        driver.switch_num_to_fn_layer(layer=args.layer, enable_f_keys=enable_f)
        mode_str = "Function Keys F1-F12" if enable_f else "Standard Numbers (1-0, -, =)"
        print(f"✓ Layer {args.layer} number row successfully switched to {mode_str}!")
        return 0
    except Exception as e:
        print(f"Failed to switch number row: {e}", file=sys.stderr)
        return 1
    finally:
        driver.disconnect()


def cmd_smoke_test(args: argparse.Namespace) -> int:
    """Run hardware verification smoke test."""
    print("Starting MK1300 V2 Smoke Test...")
    driver = HIDDriver(on_log=print)
    try:
        driver.connect()
        print("Running testSingleKey: Esc=Red, Q=Green, W=Blue...")
        driver.test_single_key()
        time.sleep(1.0)

        print("Testing static pattern: Sunset Dusk...")
        sunset = PATTERNS_BY_ID["sunset"]
        driver.set_hardware_animation(16, 4)
        colors = sunset.fn(KEYBOARD_LAYOUT)
        flat = [0] * (KEY_COUNT * 3)
        for i, key in enumerate(KEYBOARD_LAYOUT):
            flat[key.index * 3] = colors[i].r
            flat[key.index * 3 + 1] = colors[i].g
            flat[key.index * 3 + 2] = colors[i].b
        driver.set_all_key_colors(flat, KEY_COUNT)
        time.sleep(1.5)

        print("Testing hardware animation: Breath (mode 2)...")
        driver.set_hardware_animation(2, 4, 2, 0, 0, None)
        print("✓ Smoke test complete!")
        return 0
    except Exception as e:
        print(f"Smoke test failed: {e}", file=sys.stderr)
        return 1
    finally:
        driver.disconnect()


def cmd_restore_last(args: argparse.Namespace) -> int:
    """Restore the last applied pattern or hardware lighting from saved settings."""
    settings = load_settings()
    pat_id = settings.get("current_pattern_id", "sunset")
    brightness = settings.get("brightness", 100)
    user_mode = settings.get("user_light_mode", 16)
    print(f"Restoring last profile: pattern='{pat_id}', brightness={brightness}%, mode={user_mode}...")

    # Reuse apply_pattern logic
    args.id = pat_id
    args.brightness = brightness
    args.mode = user_mode
    return cmd_apply_pattern(args)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mk1300-cli",
        description="Native Linux CLI for Ant Esports MK1300 V2 per-key RGB keyboard.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # restore-last
    p_restore = subparsers.add_parser("restore-last", help="Restore last saved pattern and lighting on login")
    p_restore.set_defaults(func=cmd_restore_last)

    # list-patterns
    p_list = subparsers.add_parser("list-patterns", help="List available static RGB patterns")
    p_list.add_argument("--category", "-c", help="Filter by category (gradient, neon, heat, ice, dark, pastel, metallic, contrasty)")
    p_list.add_argument("--search", "-s", help="Filter by pattern name or id")
    p_list.set_defaults(func=cmd_list_patterns)

    # apply-pattern
    p_apply = subparsers.add_parser("apply-pattern", help="Apply a static pattern by ID")
    p_apply.add_argument("id", help="Pattern ID (e.g. sunset, cyberpunk, dracula)")
    p_apply.add_argument("--brightness", "-b", type=int, default=100, help="Brightness percentage (10-100, default 100)")
    p_apply.add_argument("--mode", "-m", type=int, default=16, choices=[16, 20], help="UserLight mode (16 standard, 20 for Rev 2.0)")
    p_apply.set_defaults(func=cmd_apply_pattern)

    # set-key
    p_set = subparsers.add_parser("set-key", help="Set RGB color for an individual key")
    p_set.add_argument("key", help="Key name (e.g. Esc, Q, Space) or hardware index")
    p_set.add_argument("hex", help="Hex color code (e.g. #ff0000 or ff0000)")
    p_set.set_defaults(func=cmd_set_key)

    # set-all
    p_set_all = subparsers.add_parser("set-all", help="Set solid RGB color for all 61 keys")
    p_set_all.add_argument("hex", help="Hex color code (e.g. #ff0000 or ff0000)")
    p_set_all.add_argument("--brightness", "-b", type=int, default=100, help="Brightness percentage (10-100, default 100)")
    p_set_all.add_argument("--mode", "-m", type=int, default=16, choices=[16, 20], help="UserLight mode (16 standard, 20 for Rev 2.0)")
    p_set_all.set_defaults(func=cmd_set_all)

    # hw-animation
    p_hw = subparsers.add_parser("hw-animation", help="Configure hardware lighting animation")
    p_hw.add_argument("--mode", "-m", type=int, required=True, help="Mode 0-16/20 (0=Off, 1=Static, 2=Breath, 3=Swing, 4=Spin, 5=Stream...)")
    p_hw.add_argument("--brightness", "-b", type=int, default=4, choices=[0, 1, 2, 3, 4], help="Brightness level (0-4, default 4)")
    p_hw.add_argument("--speed", "-s", type=int, default=2, choices=[0, 1, 2, 3, 4], help="Speed level (0-4, default 2)")
    p_hw.add_argument("--direction", "-d", type=int, default=0, choices=[0, 1], help="Direction (0 or 1)")
    p_hw.add_argument("--color", "-c", default="multi", help="Color: 'multi' for rainbow or hex color (#RRGGBB)")
    p_hw.set_defaults(func=cmd_hw_animation)

    # info
    p_info = subparsers.add_parser("info", help="Read device hardware information and config")
    p_info.set_defaults(func=cmd_info)

    # get-keymap
    p_get_km = subparsers.add_parser("get-keymap", help="Read live key mappings from keyboard firmware")
    p_get_km.add_argument("--layer", "-l", type=int, default=0, choices=[0, 1], help="Layer to read (0=Base, 1=Fn)")
    p_get_km.set_defaults(func=cmd_get_keymap)

    # remap-key
    p_remap = subparsers.add_parser("remap-key", help="Remap a key function on the keyboard")
    p_remap.add_argument("key", help="Key name (e.g. Esc, Caps, Tab, Q, Space, ?, Up) or index (0-60)")
    p_remap.add_argument("action", help="Target action name (e.g. Mute, VolUp, Esc, Enter, Play/Pause, Slash)")
    p_remap.add_argument("--layer", "-l", type=int, default=0, choices=[0, 1], help="Layer to remap (0=Base, 1=Fn)")
    p_remap.set_defaults(func=cmd_remap_key)

    # switch-num-layer
    p_switch_num = subparsers.add_parser("switch-num-layer", help="Switch number row (1..=) to F1..F12 (or revert to numbers) for testing")
    p_switch_num.add_argument("--layer", "-l", type=int, default=0, choices=[0, 1], help="Layer to switch (default 0)")
    p_switch_num.add_argument("--revert", "-r", action="store_true", help="Revert number row back to standard numbers (1-0, -, =)")
    p_switch_num.set_defaults(func=cmd_switch_num_layer)

    # smoke-test
    p_smoke = subparsers.add_parser("smoke-test", help="Run hardware verification test")
    p_smoke.set_defaults(func=cmd_smoke_test)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
