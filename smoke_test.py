#!/usr/bin/env python3
"""
Hardware smoke test for Ant Esports MK1300 V2 per-key RGB keyboard.
Tests:
1. Enumeration and vendor config interface opening (0xFF00/0x02)
2. Device config query (firmware, PID, battery, profile)
3. testSingleKey sequence: Key 0 (Esc) RED, Key 43 (Q) GREEN, Key 44 (W) BLUE
4. Static pattern write: Sunset Dusk (all keys)
5. Hardware animation: Breath mode
"""

import sys
import time
from mk1300.driver import HIDDriver
from mk1300.effects import PATTERNS_BY_ID
from mk1300.layout import KEYBOARD_LAYOUT, KEY_COUNT


def main():
    print("=" * 60)
    print("ANT ESPORTS MK1300 V2 - HARDWARE SMOKE TEST")
    print("=" * 60)

    driver = HIDDriver(on_log=print)
    dev_info = driver.find_device_info()
    if not dev_info:
        print("\n[!] Keyboard not found on vendor config interface (0xFF00/0x02).")
        print("Please check:")
        print(" 1. The keyboard is firmly connected via USB.")
        print(" 2. The udev rule is installed (sudo cp udev/99-mk1300.rules /etc/udev/rules.d/ && sudo udevadm trigger).")
        print(" 3. The official proprietary software is closed.\n")
        return 1

    print(f"\n[+] Found matching interface at {dev_info.get('path')}")
    try:
        driver.connect(dev_info)
    except Exception as e:
        print(f"[-] Connect failed: {e}")
        return 1

    try:
        # Step 1: Read keyboard config
        print("\n--- Step 1: Query Keyboard Configuration ---")
        cfg = driver.get_keyboard_config()
        print(f"Firmware Version: {cfg.get('firmware')}")
        print(f"Device PID:       0x{cfg.get('pid', 0):04X}")
        print(f"Battery:          {cfg.get('battery')}%")
        print(f"Active Profile:   {cfg.get('profile')}")

        # Step 2: testSingleKey
        print("\n--- Step 2: testSingleKey Sequence ---")
        driver.test_single_key()
        print(">> Look at your keyboard: Esc should be RED, Q should be GREEN, W should be BLUE.")
        time.sleep(2.0)

        # Step 3: Static Pattern (Sunset Dusk)
        print("\n--- Step 3: Apply Static Pattern (Sunset Dusk) ---")
        driver.set_hardware_animation(16, 4)
        sunset = PATTERNS_BY_ID["sunset"]
        colors = sunset.fn(KEYBOARD_LAYOUT)
        flat = [0] * (KEY_COUNT * 3)
        for i, key in enumerate(KEYBOARD_LAYOUT):
            flat[key.index * 3] = colors[i].r
            flat[key.index * 3 + 1] = colors[i].g
            flat[key.index * 3 + 2] = colors[i].b
        driver.set_all_key_colors(flat, KEY_COUNT)
        print(">> Look at your keyboard: 'Sunset Dusk' gradient should be shining across all keys.")
        time.sleep(2.5)

        # Step 4: Hardware Animation (Breath)
        print("\n--- Step 4: Hardware Animation (Breath, Multi-color) ---")
        driver.set_hardware_animation(mode=2, brightness=4, speed=2, color_mode=0, direction=0, hsv=None)
        print(">> Look at your keyboard: Rainbow Breath animation should be pulsing.")
        print("\n" + "=" * 60)
        print("✓ ALL HARDWARE SMOKE TESTS EXECUTED SUCCESSFULLY!")
        print("=" * 60)
        return 0

    except Exception as e:
        print(f"\n[-] Hardware test encountered an error: {e}")
        return 1
    finally:
        driver.disconnect()


if __name__ == "__main__":
    sys.exit(main())
