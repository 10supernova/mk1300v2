#!/usr/bin/env python3
"""
Automated screenshot generator for AntRGB MK1300 controller.
Captures high-resolution screenshots of each feature tab in GTK4.
"""
import os
import sys
import time
import subprocess
import threading
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, GLib, Gdk

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mk1300.ui import AntRGBApp
from mk1300.effects import PATTERNS
from mk1300.layout import KEYBOARD_LAYOUT

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resources", "screenshots")
os.makedirs(OUTPUT_DIR, exist_ok=True)

class ScreenshotApp(AntRGBApp):
    def __init__(self):
        super().__init__()
        self.set_application_id("io.github.antrgb.MK1300Screenshot")

    def do_activate(self):
        super().do_activate()
        # Set floating and size in hyprland or GTK
        self.window.set_default_size(1280, 820)
        GLib.timeout_add(1000, self._step_1_patterns)

    def _capture(self, filename: str, callback):
        def _do_grab():
            time.sleep(0.4)
            # Find window geometry in hyprland
            out = subprocess.check_output(["hyprctl", "clients", "-j"], text=True)
            import json
            clients = json.loads(out)
            win = next((c for c in clients if "MK1300Screenshot" in c.get("class", "") or "AntRGB" in c.get("title", "")), None)
            path = os.path.join(OUTPUT_DIR, filename)
            if win:
                x, y = win["at"]
                w, h = win["size"]
                subprocess.run(["grim", "-g", f"{x},{y} {w}x{h}", path])
            else:
                subprocess.run(["grim", path])
            print(f"Captured {path}")
            GLib.idle_add(callback)

        threading.Thread(target=_do_grab, daemon=True).start()

    def _step_1_patterns(self):
        # Select Sunset Dusk or Cyberpunk
        p = next((x for x in PATTERNS if x.id == "cyberpunk"), PATTERNS[0])
        self.current_pattern = p
        self._update_preview_from_pattern()
        self.stack.set_visible_child_name("sync")
        self._capture("01-static-patterns.png", self._step_2_hardware)

    def _step_2_hardware(self):
        self.stack.set_visible_child_name("hardware")
        # Select rainbow breath or stream
        if hasattr(self, "hw_mode_combo"):
            self.hw_mode_combo.set_selected(2) # Breath mode
        self._capture("02-hardware-fx.png", self._step_3_custom)

    def _step_3_custom(self):
        self.stack.set_visible_child_name("custom")
        # Paint WASD green, Esc red, Arrows cyan
        for i, k in enumerate(KEYBOARD_LAYOUT):
            if k.name in ["W", "A", "S", "D"]:
                self.custom_colors[i] = [0, 255, 128]
            elif k.name == "Esc":
                self.custom_colors[i] = [255, 50, 50]
            elif k.name in ["I", "J", "K", "L", "Space"]:
                self.custom_colors[i] = [120, 180, 255]
            elif k.name in ["Enter", "Shift"]:
                self.custom_colors[i] = [255, 180, 0]
        if hasattr(self, "custom_kb"):
            self.custom_kb.set_colors(self.custom_colors)
            self.custom_kb.queue_draw()
        self._capture("03-custom-painter.png", self._step_4_keymap)

    def _step_4_keymap(self):
        self.stack.set_visible_child_name("keymap")
        self._capture("04-key-functions.png", self._finish)

    def _finish(self):
        print("All screenshots generated successfully!")
        self.quit()

if __name__ == "__main__":
    app = ScreenshotApp()
    sys.exit(app.run(sys.argv))
