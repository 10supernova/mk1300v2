"""
Tokyo Night & Omarchy Theme integration for native Linux GTK4 UI.
"""

import os
import json
from dataclasses import dataclass
from typing import Dict, Optional

try:
    import tomllib  # Python 3.11+ standard library
except ImportError:
    import tomli as tomllib  # fallback if needed


@dataclass
class ThemeColors:
    bg: str = "#1a1b26"
    panels: str = "#16161e"
    raised: str = "#292e42"
    text: str = "#c0caf5"
    muted: str = "#565f89"
    blue: str = "#7aa2f7"
    cyan: str = "#7dcfff"
    purple: str = "#bb9af7"
    green: str = "#9ece6a"
    orange: str = "#ff9e64"
    yellow: str = "#e0af68"
    red: str = "#f7768e"
    accent: str = "#7aa2f7"
    border: str = "#292e42"
    source: str = "Tokyo Night (Built-in)"


def load_theme() -> ThemeColors:
    """
    Load theme colors from Omarchy configuration if present (~/.config/omarchy/),
    falling back to standard Tokyo Night palette.
    """
    omarchy_dir = os.path.expanduser("~/.config/omarchy")
    settings_file = os.path.join(omarchy_dir, "omasettings.json")

    if not os.path.exists(settings_file):
        return ThemeColors()

    try:
        with open(settings_file, "r", encoding="utf-8") as f:
            settings = json.load(f)

        theme_name = settings.get("written", {}).get("theme", "")
        if not theme_name:
            theme_name = settings.get("theme", "")

        if not theme_name:
            return ThemeColors()

        # Slugify theme name for directory lookup (e.g. "Ghost Pastel" -> "ghost-pastel")
        slug = theme_name.lower().replace(" ", "-")
        theme_dir = os.path.join(omarchy_dir, "themes", slug)
        if not os.path.exists(theme_dir):
            # Try finding directory case-insensitively
            themes_root = os.path.join(omarchy_dir, "themes")
            if os.path.exists(themes_root):
                for entry in os.listdir(themes_root):
                    if entry.lower() in (slug, theme_name.lower()):
                        theme_dir = os.path.join(themes_root, entry)
                        break

        colors_file = os.path.join(theme_dir, "colors.toml")
        if not os.path.exists(colors_file):
            return ThemeColors()

        with open(colors_file, "rb") as f:
            cfg = tomllib.load(f)

        bg = cfg.get("background", "#1a1b26")
        fg = cfg.get("foreground", "#c0caf5")
        accent = cfg.get("accent", "#7aa2f7")
        border = cfg.get("active_border_color", "#292e42")

        return ThemeColors(
            bg=bg,
            panels=cfg.get("color0", "#16161e"),
            raised=cfg.get("selection_background", "#292e42"),
            text=fg,
            muted=cfg.get("color8", "#565f89"),
            blue=cfg.get("color4", "#7aa2f7"),
            cyan=cfg.get("color6", "#7dcfff"),
            purple=cfg.get("color5", "#bb9af7"),
            green=cfg.get("color2", "#9ece6a"),
            orange=cfg.get("color3", "#ff9e64"),
            yellow=cfg.get("color11", "#e0af68"),
            red=cfg.get("color1", "#f7768e"),
            accent=accent,
            border=border,
            source=f"Omarchy ({theme_name})",
        )
    except Exception:
        return ThemeColors()


def generate_gtk_css(theme: Optional[ThemeColors] = None) -> str:
    """Generate modern Tokyo Night / Omarchy GTK4 stylesheet with rounded corners and glow."""
    t = theme or load_theme()

    return f"""
/* AntRGB - Tokyo Night / Omarchy Native Stylesheet */

@define-color window_bg_color {t.bg};
@define-color window_fg_color {t.text};
@define-color view_bg_color {t.panels};
@define-color view_fg_color {t.text};
@define-color card_bg_color {t.panels};
@define-color card_fg_color {t.text};
@define-color headerbar_bg_color {t.bg};
@define-color headerbar_fg_color {t.text};
@define-color accent_color {t.accent};
@define-color accent_bg_color {t.accent};
@define-color accent_fg_color {t.bg};

window {{
    background-color: {t.bg};
    color: {t.text};
    font-family: system-ui, -apple-system, sans-serif;
}}

/* Typography */
.monospace-font {{
    font-family: 'JetBrainsMono Nerd Font', 'JetBrains Mono', 'Fira Code', monospace;
}}

.pixel-title {{
    font-weight: 800;
    font-size: 18px;
    letter-spacing: 1px;
    color: {t.cyan};
}}

.subtitle-label {{
    color: {t.muted};
    font-size: 12px;
}}

.accent-text {{
    color: {t.accent};
    font-weight: bold;
}}

/* Panels and Containers */
.card-panel {{
    background-color: {t.panels};
    border-radius: 12px;
    border: 1px solid rgba(255, 255, 255, 0.06);
    padding: 12px;
}}

.card-panel-raised {{
    background-color: {t.raised};
    border-radius: 12px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    padding: 12px;
}}

/* Status Badge */
.status-badge-online {{
    background-color: rgba(158, 206, 106, 0.2);
    color: {t.green};
    border: 1px solid {t.green};
    border-radius: 9999px;
    padding: 2px 10px;
    font-weight: bold;
    font-size: 11px;
}}

.status-badge-offline {{
    background-color: rgba(247, 118, 142, 0.2);
    color: {t.red};
    border: 1px solid {t.red};
    border-radius: 9999px;
    padding: 2px 10px;
    font-weight: bold;
    font-size: 11px;
}}

/* Interactive Buttons */
button {{
    border-radius: 10px;
    transition: all 150ms ease-in-out;
    padding: 6px 12px;
}}

button.primary-action {{
    background-color: {t.accent};
    color: {t.bg};
    font-weight: bold;
    border: none;
}}

button.primary-action:hover {{
    background-color: {t.cyan};
    box-shadow: 0 0 12px rgba(122, 162, 247, 0.4);
}}

button.category-chip {{
    background-color: {t.panels};
    color: {t.muted};
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 9999px;
    padding: 4px 12px;
    font-size: 12px;
    font-weight: 500;
}}

button.category-chip:checked, button.category-chip.active {{
    background-color: {t.raised};
    color: {t.accent};
    border: 1px solid {t.accent};
    box-shadow: 0 0 8px rgba(122, 162, 247, 0.25);
}}

button.category-chip:hover {{
    background-color: {t.raised};
    color: {t.text};
}}

/* Pattern Cards */
.pattern-card {{
    background-color: {t.panels};
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 10px;
    padding: 8px 10px;
    transition: all 120ms ease;
}}

.pattern-card:hover {{
    background-color: {t.raised};
    border-color: rgba(255, 255, 255, 0.15);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
}}

.pattern-card.active {{
    background-color: {t.raised};
    border-color: {t.accent};
    box-shadow: 0 0 10px rgba(122, 162, 247, 0.35);
}}

/* Sliders */
scale {{
    padding: 4px 0;
}}

scale trough {{
    background-color: {t.raised};
    border-radius: 6px;
    min-height: 8px;
}}

scale highlight {{
    background-color: {t.accent};
    border-radius: 6px;
}}

scale slider {{
    background-color: {t.text};
    border: 2px solid {t.accent};
    border-radius: 50%;
    min-width: 18px;
    min-height: 18px;
    box-shadow: 0 0 8px rgba(0, 0, 0, 0.5);
}}

/* Log View */
.log-view {{
    background-color: #0f1017;
    color: {t.green};
    font-family: 'JetBrainsMono Nerd Font', 'JetBrains Mono', 'Fira Code', monospace;
    font-size: 11px;
    border-radius: 8px;
    border: 1px solid rgba(255, 255, 255, 0.05);
    padding: 8px;
}}

/* Color Swatches */
.color-swatch-btn {{
    min-width: 28px;
    min-height: 28px;
    border-radius: 8px;
    border: 2px solid rgba(255, 255, 255, 0.15);
    padding: 0;
}}

.color-swatch-btn:hover {{
    border-color: #ffffff;
    box-shadow: 0 0 8px rgba(255, 255, 255, 0.3);
}}

.color-swatch-btn.active {{
    border-color: #ffffff;
    box-shadow: 0 0 10px {t.accent};
}}
"""
