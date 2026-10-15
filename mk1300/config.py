"""
Settings persistence for mk1300-linux.
"""

import json
import os
from typing import Any, Dict, List
from .layout import KEYBOARD_LAYOUT


CONFIG_DIR = os.path.expanduser("~/.config/mk1300-linux")
CONFIG_PATH = os.path.join(CONFIG_DIR, "settings.json")


DEFAULT_SETTINGS: Dict[str, Any] = {
    "current_tab": "software",
    "active_category": "all",
    "current_pattern_id": "sunset",
    "brightness": 100,
    "hw_mode": 1,
    "hw_speed": 2,
    "hw_bright": 4,
    "hw_color": "multi",
    "user_light_mode": 16,
    "custom_colors": [{"r": 0, "g": 0, "b": 0} for _ in range(len(KEYBOARD_LAYOUT))],
    "custom_brightness": 100,
    "custom_autopush": True,
}


def load_settings() -> Dict[str, Any]:
    """Load settings from ~/.config/mk1300-linux/settings.json."""
    if not os.path.exists(CONFIG_PATH):
        return dict(DEFAULT_SETTINGS)

    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        settings = dict(DEFAULT_SETTINGS)
        settings.update(data)
        # Ensure custom_colors is the right length
        colors = settings.get("custom_colors", [])
        if len(colors) < len(KEYBOARD_LAYOUT):
            colors.extend([{"r": 0, "g": 0, "b": 0} for _ in range(len(KEYBOARD_LAYOUT) - len(colors))])
            settings["custom_colors"] = colors
        return settings
    except Exception:
        return dict(DEFAULT_SETTINGS)


def save_settings(settings: Dict[str, Any]) -> None:
    """Save settings to ~/.config/mk1300-linux/settings.json."""
    os.makedirs(CONFIG_DIR, exist_ok=True)
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)
    except Exception as e:
        print(f"Warning: Failed to save settings: {e}")
