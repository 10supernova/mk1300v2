"""
GTK4 + Libadwaita native Linux desktop interface for MK1300 V2 RGB controller.
Dark Tokyo Night UI with Omarchy theme integration, live 61-key visualizer,
searchable pattern grid, hardware-animation controls, and custom preset editor.
"""

import math
import os
import sys
import threading
from typing import Dict, List, Optional, Tuple

import cairo
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, GLib, GObject, Gtk

from .categories import ALL_PATTERNS, ALL_PATTERNS_BY_ID, CATEGORIES, get_category
from .config import load_settings, save_settings
from .driver import HIDDriver
from .effects import PATTERNS, PATTERNS_BY_ID, RGBColor
from .layout import KB_HEIGHT, KB_WIDTH, KEY_COUNT, KEYBOARD_LAYOUT, Key
from .theme import generate_gtk_css, load_theme


def hex_to_rgb(hex_str: str) -> Tuple[int, int, int]:
    cleaned = hex_str.strip().lstrip("#")
    if len(cleaned) == 3:
        cleaned = "".join([c * 2 for c in cleaned])
    val = int(cleaned, 16)
    return ((val >> 16) & 0xFF, (val >> 8) & 0xFF, val & 0xFF)


def rgb_to_hex(r: int, g: int, b: int) -> str:
    return f"#{r:02x}{g:02x}{b:02x}"


def hex_to_hsv(hex_str: str) -> dict:
    r, g, b = hex_to_rgb(hex_str)
    rf, gf, bf = r / 255.0, g / 255.0, b / 255.0
    cmax = max(rf, gf, bf)
    cmin = min(rf, gf, bf)
    delta = cmax - cmin

    if delta == 0:
        h = 0.0
    elif cmax == rf:
        h = (gf - bf) / delta + (6.0 if gf < bf else 0.0)
    elif cmax == gf:
        h = (bf - rf) / delta + 2.0
    else:
        h = (rf - gf) / delta + 4.0

    h /= 6.0
    s = 0.0 if cmax == 0 else (delta / cmax)
    v = cmax

    return {
        "h": round(h * 255.0),
        "s": round(s * 255.0),
        "v": round(v * 255.0),
    }


class KeyboardWidget(Gtk.DrawingArea):
    """Visualizer and interactive painter for the 61-key keyboard layout."""

    def __init__(self, interactive: bool = False):
        super().__init__()
        self.interactive = interactive
        self.colors: List[Tuple[int, int, int]] = [(0, 0, 0)] * len(KEYBOARD_LAYOUT)
        self.paint_color: Tuple[int, int, int] = (255, 45, 120)  # Default neon pink
        self.selected_indices: set = set()
        self.on_color_changed = None  # callback(key_idx, rgb)
        self.on_color_picked = None   # callback(rgb_hex)

        self.set_draw_func(self._draw)
        self.set_hexpand(True)
        self.set_vexpand(False)
        self.set_content_height(160)
        self.set_content_width(460)

        if self.interactive:
            # Click and drag controller
            drag = Gtk.GestureDrag()
            drag.connect("drag-begin", self._on_drag_begin)
            drag.connect("drag-update", self._on_drag_update)
            drag.connect("drag-end", self._on_drag_end)
            self.add_controller(drag)

            # Secondary click (context menu / eyedropper)
            click = Gtk.GestureClick()
            click.set_button(3)  # right-click
            click.connect("pressed", self._on_right_click)
            self.add_controller(click)

    def set_colors(self, colors: List[Tuple[int, int, int]]):
        self.colors = colors
        self.queue_draw()

    def set_paint_color(self, r: int, g: int, b: int):
        self.paint_color = (r, g, b)

    def _get_key_at(self, px: float, py: float, w: float, h: float) -> Optional[int]:
        scale = min(w / KB_WIDTH, h / KB_HEIGHT) * 0.95
        ox = (w - (KB_WIDTH * scale)) / 2.0
        oy = (h - (KB_HEIGHT * scale)) / 2.0

        for i, k in enumerate(KEYBOARD_LAYOUT):
            kx = ox + k.x * scale
            ky = oy + k.y * scale
            kw = k.w * scale
            kh = k.h * scale
            if kx <= px <= kx + kw and ky <= py <= ky + kh:
                return i
        return None

    def _on_drag_begin(self, gesture, start_x, start_y):
        w = self.get_width()
        h = self.get_height()
        idx = self._get_key_at(start_x, start_y, w, h)
        if idx is not None:
            self.colors[idx] = self.paint_color
            self.queue_draw()
            if self.on_color_changed:
                self.on_color_changed(idx, self.paint_color)

    def _on_drag_update(self, gesture, offset_x, offset_y):
        start_x, start_y = gesture.get_start_point()[1:]
        cur_x = start_x + offset_x
        cur_y = start_y + offset_y
        w = self.get_width()
        h = self.get_height()
        idx = self._get_key_at(cur_x, cur_y, w, h)
        if idx is not None and self.colors[idx] != self.paint_color:
            self.colors[idx] = self.paint_color
            self.queue_draw()
            if self.on_color_changed:
                self.on_color_changed(idx, self.paint_color)

    def _on_drag_end(self, gesture, offset_x, offset_y):
        pass

    def _on_right_click(self, gesture, n_press, x, y):
        w = self.get_width()
        h = self.get_height()
        idx = self._get_key_at(x, y, w, h)
        if idx is not None and self.on_color_picked:
            r, g, b = self.colors[idx]
            self.on_color_picked(rgb_to_hex(r, g, b))

    def _draw_rounded_rect(self, cr: cairo.Context, x: float, y: float, w: float, h: float, r: float):
        cr.new_sub_path()
        cr.arc(x + w - r, y + r, r, -math.pi / 2, 0)
        cr.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
        cr.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
        cr.arc(x + r, y + r, r, math.pi, 3 * math.pi / 2)
        cr.close_path()

    def _draw(self, area, cr: cairo.Context, width: int, height: int):
        # Calculate fit
        scale = min(width / KB_WIDTH, height / KB_HEIGHT) * 0.95
        ox = (width - (KB_WIDTH * scale)) / 2.0
        oy = (height - (KB_HEIGHT * scale)) / 2.0
        margin = max(1.5, scale * 0.04)
        corner_r = max(2.5, scale * 0.12)

        # Draw keyboard backing
        cr.set_source_rgba(0.08, 0.08, 0.12, 0.95)
        self._draw_rounded_rect(cr, ox - 4, oy - 4, KB_WIDTH * scale + 8, KB_HEIGHT * scale + 8, corner_r + 4)
        cr.fill()

        # Border around plate
        cr.set_source_rgba(0.2, 0.25, 0.35, 0.4)
        cr.set_line_width(1.0)
        self._draw_rounded_rect(cr, ox - 4, oy - 4, KB_WIDTH * scale + 8, KB_HEIGHT * scale + 8, corner_r + 4)
        cr.stroke()

        # Font configuration
        cr.select_font_face("JetBrainsMono Nerd Font", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        font_size = max(7.0, scale * 0.28)
        cr.set_font_size(font_size)

        for i, key in enumerate(KEYBOARD_LAYOUT):
            kx = ox + key.x * scale + margin
            ky = oy + key.y * scale + margin
            kw = key.w * scale - margin * 2
            kh = key.h * scale - margin * 2

            r, g, b = self.colors[i] if i < len(self.colors) else (0, 0, 0)
            rf, gf, bf = r / 255.0, g / 255.0, b / 255.0
            brightness = max(r, g, b)

            # Draw outer glow if key is illuminated
            if brightness > 30:
                glow_r = corner_r + 2.0
                cr.set_source_rgba(rf, gf, bf, 0.25)
                self._draw_rounded_rect(cr, kx - 1.5, ky - 1.5, kw + 3.0, kh + 3.0, glow_r)
                cr.fill()

            # Keycap background
            # Blend RGB with keycap dark base
            cr.set_source_rgba(rf * 0.85 + 0.08, gf * 0.85 + 0.08, bf * 0.85 + 0.12, 0.95)
            self._draw_rounded_rect(cr, kx, ky, kw, kh, corner_r)
            cr.fill()

            # Keycap border
            if brightness > 40:
                cr.set_source_rgba(rf, gf, bf, 0.7)
            else:
                cr.set_source_rgba(0.25, 0.28, 0.38, 0.5)
            cr.set_line_width(1.0)
            self._draw_rounded_rect(cr, kx, ky, kw, kh, corner_r)
            cr.stroke()

            # Key label text
            # Determine contrasting font color
            text_brightness = (rf * 0.299 + gf * 0.587 + bf * 0.114)
            if text_brightness > 0.65:
                cr.set_source_rgba(0.05, 0.05, 0.08, 0.95)
            else:
                cr.set_source_rgba(0.95, 0.95, 1.0, 0.95)

            extents = cr.text_extents(key.name)
            tx = kx + (kw - extents.width) / 2.0 - extents.x_bearing
            ty = ky + (kh - extents.height) / 2.0 - extents.y_bearing
            cr.move_to(tx, ty)
            cr.show_text(key.name)


class AntRGBApp(Adw.Application):
    """AntRGB Application Controller."""

    def __init__(self):
        super().__init__(application_id="io.github.antrgb.MK1300Linux", flags=0)
        self.driver = HIDDriver(on_log=self._on_driver_log)
        self.theme = load_theme()
        self.settings = load_settings()
        self.window = None

        # State
        current_id = self.settings.get("current_pattern_id", "sunset")
        self.current_pattern = ALL_PATTERNS_BY_ID.get(current_id, ALL_PATTERNS[0])
        self.brightness = int(self.settings.get("brightness", 100))
        self.active_category = self.settings.get("active_category", "all")
        self.user_light_mode = int(self.settings.get("user_light_mode", 16))
        self.hw_mode = int(self.settings.get("hw_mode", 1))
        self.hw_speed = int(self.settings.get("hw_speed", 2))
        self.hw_bright = int(self.settings.get("hw_bright", 4))
        self.hw_color = self.settings.get("hw_color", "multi")
        self.custom_colors = [
            (c.get("r", 0), c.get("g", 0), c.get("b", 0))
            for c in self.settings.get("custom_colors", [])
        ]
        if len(self.custom_colors) < len(KEYBOARD_LAYOUT):
            self.custom_colors.extend([(0, 0, 0)] * (len(KEYBOARD_LAYOUT) - len(self.custom_colors)))
        self.custom_undo_stack: List[List[Tuple[int, int, int]]] = []

    def do_activate(self):
        if not self.window:
            self._build_ui()
        self.window.present()
        self._auto_connect_background()

    def _on_driver_log(self, msg: str):
        GLib.idle_add(self._append_log, msg)

    def _append_log(self, msg: str):
        if hasattr(self, "log_buffer"):
            end_iter = self.log_buffer.get_end_iter()
            self.log_buffer.insert(end_iter, f"> {msg}\n")
            if hasattr(self, "log_text_view"):
                self.log_text_view.scroll_to_iter(end_iter, 0.0, False, 0.0, 0.0)

    def _apply_theme_css(self):
        css_provider = Gtk.CssProvider()
        css_data = generate_gtk_css(self.theme)
        css_provider.load_from_data(css_data.encode("utf-8"))
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

    def _build_ui(self):
        self._apply_theme_css()

        self.window = Adw.ApplicationWindow(application=self)
        self.window.set_title("AntRGB - MK1300 V2")
        self.window.set_default_size(980, 720)

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.window.set_content(main_box)

        # ── Header Bar ──
        header = Adw.HeaderBar()
        main_box.append(header)

        # Title widget
        title_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        title_lbl = Gtk.Label(label="AntRGB")
        title_lbl.add_css_class("pixel-title")
        title_box.append(title_lbl)

        sub_lbl = Gtk.Label(label="MK1300 V2")
        sub_lbl.add_css_class("subtitle-label")
        title_box.append(sub_lbl)
        header.set_title_widget(title_box)

        # Connect / status controls
        status_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.status_badge = Gtk.Label(label="OFFLINE")
        self.status_badge.add_css_class("status-badge-offline")
        status_box.append(self.status_badge)

        self.connect_btn = Gtk.Button(label="Connect")
        self.connect_btn.add_css_class("primary-action")
        self.connect_btn.connect("clicked", self._on_connect_clicked)
        status_box.append(self.connect_btn)

        about_btn = Gtk.Button(icon_name="help-about-symbolic")
        about_btn.set_tooltip_text("About AntRGB")
        about_btn.connect("clicked", self._on_about_clicked)
        status_box.append(about_btn)

        header.pack_end(status_box)

        # Theme indicator in header
        theme_tag = Gtk.Label(label=f"🎨 {self.theme.source}")
        theme_tag.add_css_class("subtitle-label")
        header.pack_start(theme_tag)

        # ── Upper Section: Live Keyboard Visualizer Preview ──
        preview_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        preview_card.add_css_class("card-panel")
        preview_card.set_margin_start(16)
        preview_card.set_margin_end(16)
        preview_card.set_margin_top(12)
        preview_card.set_margin_bottom(12)

        preview_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        p_title = Gtk.Label(label="LIVE 61-KEY PREVIEW")
        p_title.add_css_class("subtitle-label")
        preview_header.append(p_title)

        self.current_pattern_lbl = Gtk.Label(label=f"{self.current_pattern.icon} {self.current_pattern.name.upper()}")
        self.current_pattern_lbl.add_css_class("accent-text")
        preview_header.append(self.current_pattern_lbl)

        preview_header.append(Gtk.Box(hexpand=True))

        # Brightness Slider
        b_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        b_lbl = Gtk.Label(label="BRIGHTNESS:")
        b_lbl.add_css_class("subtitle-label")
        b_box.append(b_lbl)

        self.brightness_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 10, 100, 5)
        self.brightness_scale.set_value(self.brightness)
        self.brightness_scale.set_size_request(140, -1)
        self.brightness_scale.connect("value-changed", self._on_brightness_changed)
        b_box.append(self.brightness_scale)

        self.brightness_val_lbl = Gtk.Label(label=f"{self.brightness}%")
        self.brightness_val_lbl.add_css_class("monospace-font")
        b_box.append(self.brightness_val_lbl)

        preview_header.append(b_box)
        preview_card.append(preview_header)

        # The Visualizer canvas
        self.preview_kb = KeyboardWidget(interactive=False)
        preview_card.append(self.preview_kb)
        main_box.append(preview_card)

        # ── Lower Section: Tabs View ──
        tabs_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        tabs_box.set_margin_start(16)
        tabs_box.set_margin_end(16)
        tabs_box.set_margin_bottom(12)
        tabs_box.set_vexpand(True)
        main_box.append(tabs_box)

        # View Stack & Switcher
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.stack.set_vexpand(True)

        switcher = Gtk.StackSwitcher()
        switcher.set_stack(self.stack)
        switcher.set_halign(Gtk.Align.CENTER)
        tabs_box.append(switcher)

        # Tab 1: Software Sync (90 Static Patterns)
        sync_tab = self._build_sync_tab()
        self.stack.add_titled(sync_tab, "sync", "Static Patterns (90)")

        # Tab 2: Hardware FX
        hw_tab = self._build_hw_tab()
        self.stack.add_titled(hw_tab, "hardware", "Hardware FX")

        # Tab 3: Custom Preset Painter
        custom_tab = self._build_custom_tab()
        self.stack.add_titled(custom_tab, "custom", "Custom Painter")

        # Tab 4: Diagnostics Log
        log_tab = self._build_log_tab()
        self.stack.add_titled(log_tab, "log", "HID Activity Log")

        tabs_box.append(self.stack)

        # Compute initial colors
        self._update_preview_from_pattern()

    def _build_sync_tab(self) -> Gtk.Widget:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_vexpand(True)

        # Filter bar: Search + Category Chips + Rev 2.0 toggle
        filter_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)

        # Search Entry
        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_placeholder_text("Search 90 patterns...")
        self.search_entry.set_size_request(220, -1)
        self.search_entry.connect("search-changed", self._on_search_changed)
        filter_bar.append(self.search_entry)

        # Category Scrollable Chips
        cat_scroll = Gtk.ScrolledWindow()
        cat_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.NEVER)
        cat_scroll.set_hexpand(True)

        cat_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        cat_scroll.set_child(cat_box)

        self.cat_buttons: Dict[str, Gtk.Button] = {}
        for cat in CATEGORIES:
            btn = Gtk.Button(label=f"{cat.icon} {cat.label}")
            btn.add_css_class("category-chip")
            if cat.id == self.active_category:
                btn.add_css_class("active")
            btn.connect("clicked", self._on_category_clicked, cat.id)
            self.cat_buttons[cat.id] = btn
            cat_box.append(btn)

        filter_bar.append(cat_scroll)

        # Rev 2.0 Checkbox
        rev_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        rev_check = Gtk.CheckButton(label="Rev 2.0 (Mode 20)")
        rev_check.set_active(self.user_light_mode == 20)
        rev_check.connect("toggled", self._on_rev_toggle)
        rev_box.append(rev_check)
        filter_bar.append(rev_box)

        box.append(filter_bar)

        # Pattern Grid Scroll
        grid_scroll = Gtk.ScrolledWindow()
        grid_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        grid_scroll.set_vexpand(True)

        self.flowbox = Gtk.FlowBox()
        self.flowbox.set_valign(Gtk.Align.START)
        self.flowbox.set_max_children_per_line(6)
        self.flowbox.set_min_children_per_line(2)
        self.flowbox.set_selection_mode(Gtk.SelectionMode.NONE)
        self.flowbox.set_row_spacing(8)
        self.flowbox.set_column_spacing(8)

        grid_scroll.set_child(self.flowbox)
        box.append(grid_scroll)

        self._populate_pattern_grid()
        return box

    def _populate_pattern_grid(self):
        # Clear existing
        while child := self.flowbox.get_first_child():
            self.flowbox.remove(child)

        search_query = self.search_entry.get_text().strip().lower() if hasattr(self, "search_entry") else ""

        for p in ALL_PATTERNS:
            cat = get_category(p.id)
            if self.active_category != "all" and cat != self.active_category:
                continue
            if search_query and (search_query not in p.id.lower() and search_query not in p.name.lower()):
                continue

            card = Gtk.Button()
            card.add_css_class("pattern-card")
            if p.id == self.current_pattern.id:
                card.add_css_class("active")

            c_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            icon_lbl = Gtk.Label(label=p.icon)
            icon_lbl.set_size_request(24, 24)
            c_box.append(icon_lbl)

            name_lbl = Gtk.Label(label=p.name)
            name_lbl.set_halign(Gtk.Align.START)
            c_box.append(name_lbl)

            card.set_child(c_box)
            card.connect("clicked", self._on_pattern_card_clicked, p)
            self.flowbox.append(card)

    def _build_hw_tab(self) -> Gtk.Widget:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        box.set_margin_top(12)
        box.set_margin_start(24)
        box.set_margin_end(24)

        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        card.add_css_class("card-panel")
        box.append(card)

        # Mode Selector
        mode_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        m_lbl = Gtk.Label(label="Effect Mode:")
        m_lbl.set_size_request(120, -1)
        m_lbl.set_halign(Gtk.Align.START)
        mode_box.append(m_lbl)

        mode_names = [
            "0: Light Off",
            "1: Static",
            "2: Breath",
            "3: Swing",
            "4: Spin",
            "5: Stream",
            "6: Bloom",
            "7: UDWawe",
            "8: Cross",
            "9: Rain",
            "10: Meteor",
            "11: TrigSpread",
            "12: TrigSpreadReverse",
            "13: TrigSingle",
            "14: Soduko",
            "15: Tide",
            f"{self.user_light_mode}: UserLight",
        ]
        self.mode_combo = Gtk.DropDown.new_from_strings(mode_names)
        self.mode_combo.set_selected(min(self.hw_mode, len(mode_names) - 1))
        self.mode_combo.set_hexpand(True)
        mode_box.append(self.mode_combo)
        card.append(mode_box)

        # Speed Slider
        speed_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        sp_lbl = Gtk.Label(label="Animation Speed:")
        sp_lbl.set_size_request(120, -1)
        sp_lbl.set_halign(Gtk.Align.START)
        speed_box.append(sp_lbl)

        self.speed_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 4, 1)
        self.speed_scale.set_value(self.hw_speed)
        self.speed_scale.set_hexpand(True)
        self.speed_scale.set_draw_value(True)
        speed_box.append(self.speed_scale)
        card.append(speed_box)

        # Brightness Slider
        bright_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        br_lbl = Gtk.Label(label="Hardware Brightness:")
        br_lbl.set_size_request(120, -1)
        br_lbl.set_halign(Gtk.Align.START)
        bright_box.append(br_lbl)

        self.hw_bright_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 4, 1)
        self.hw_bright_scale.set_value(self.hw_bright)
        self.hw_bright_scale.set_hexpand(True)
        self.hw_bright_scale.set_draw_value(True)
        bright_box.append(self.hw_bright_scale)
        card.append(bright_box)

        # Color Option
        color_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        c_lbl = Gtk.Label(label="Color Mode:")
        c_lbl.set_size_request(120, -1)
        c_lbl.set_halign(Gtk.Align.START)
        color_box.append(c_lbl)

        swatches_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        color_box.append(swatches_box)

        # Multi / Rainbow button
        self.multi_btn = Gtk.Button(label="🌈 Rainbow")
        self.multi_btn.add_css_class("color-swatch-btn")
        if self.hw_color == "multi":
            self.multi_btn.add_css_class("active")
        self.multi_btn.connect("clicked", lambda b: self._select_hw_color("multi"))
        swatches_box.append(self.multi_btn)

        # Preset palette swatches
        swatch_colors = [
            ("#ff0000", "Red"),
            ("#00ff00", "Green"),
            ("#0000ff", "Blue"),
            ("#00ffff", "Cyan"),
            ("#ff00ff", "Magenta"),
            ("#ffff00", "Yellow"),
            ("#ffffff", "White"),
        ]
        self.swatch_buttons = {}
        for hex_val, name in swatch_colors:
            btn = Gtk.Button()
            btn.add_css_class("color-swatch-btn")
            btn.set_tooltip_text(name)
            # Custom swatch color style
            rgba = hex_to_rgb(hex_val)
            provider = Gtk.CssProvider()
            provider.load_from_data(f"button {{ background-color: {hex_val}; }}".encode("utf-8"))
            btn.get_style_context().add_provider(provider, Gtk.STYLE_PROVIDER_PRIORITY_USER)
            btn.connect("clicked", lambda b, h=hex_val: self._select_hw_color(h))
            swatches_box.append(btn)
            self.swatch_buttons[hex_val] = btn

        card.append(color_box)

        # Apply Button
        btn_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        apply_btn = Gtk.Button(label="Apply Hardware FX")
        apply_btn.add_css_class("primary-action")
        apply_btn.connect("clicked", self._on_apply_hw_clicked)
        btn_row.append(apply_btn)
        card.append(btn_row)

        return box

    def _build_custom_tab(self) -> Gtk.Widget:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_vexpand(True)

        # Toolbar
        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        toolbar.add_css_class("card-panel")

        # Palette
        p_lbl = Gtk.Label(label="Paint Color:")
        p_lbl.add_css_class("subtitle-label")
        toolbar.append(p_lbl)

        paint_swatches = ["#ff0055", "#00f5ff", "#00ff88", "#ffe100", "#b24bff", "#ffffff", "#000000"]
        for hex_c in paint_swatches:
            btn = Gtk.Button()
            btn.add_css_class("color-swatch-btn")
            btn.set_tooltip_text(hex_c)
            p = Gtk.CssProvider()
            p.load_from_data(f"button {{ background-color: {hex_c}; }}".encode("utf-8"))
            btn.get_style_context().add_provider(p, Gtk.STYLE_PROVIDER_PRIORITY_USER)
            btn.connect("clicked", lambda b, c=hex_c: self._set_custom_paint_color(c))
            toolbar.append(btn)

        toolbar.append(Gtk.Box(hexpand=True))

        # Actions
        fill_btn = Gtk.Button(label="Fill All")
        fill_btn.connect("clicked", self._on_custom_fill)
        toolbar.append(fill_btn)

        import_btn = Gtk.Button(label="Import from Sync")
        import_btn.connect("clicked", self._on_custom_import_sync)
        toolbar.append(import_btn)

        clear_btn = Gtk.Button(label="Clear")
        clear_btn.connect("clicked", self._on_custom_clear)
        toolbar.append(clear_btn)

        undo_btn = Gtk.Button(label="Undo")
        undo_btn.connect("clicked", self._on_custom_undo)
        toolbar.append(undo_btn)

        push_btn = Gtk.Button(label="Push to Keyboard")
        push_btn.add_css_class("primary-action")
        push_btn.connect("clicked", self._on_custom_push)
        toolbar.append(push_btn)

        box.append(toolbar)

        # Interactive Canvas
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        card.add_css_class("card-panel")
        card.set_vexpand(True)

        c_info = Gtk.Label(label="Click or drag across keys to paint. Right-click any key to pick its color.")
        c_info.add_css_class("subtitle-label")
        card.append(c_info)

        self.custom_kb = KeyboardWidget(interactive=True)
        self.custom_kb.set_colors(self.custom_colors)
        self.custom_kb.on_color_changed = self._on_custom_key_painted
        self.custom_kb.on_color_picked = self._set_custom_paint_color
        card.append(self.custom_kb)

        box.append(card)
        return box

    def _build_log_tab(self) -> Gtk.Widget:
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scroll.set_vexpand(True)

        self.log_text_view = Gtk.TextView()
        self.log_text_view.set_editable(False)
        self.log_text_view.set_cursor_visible(False)
        self.log_text_view.add_css_class("log-view")
        self.log_buffer = self.log_text_view.get_buffer()

        scroll.set_child(self.log_text_view)
        return scroll

    def _update_preview_from_pattern(self):
        br = self.brightness / 100.0
        colors = self.current_pattern.fn(KEYBOARD_LAYOUT)
        rgb_list = [
            (round(c.r * br), round(c.g * br), round(c.b * br))
            for c in colors
        ]
        self.preview_kb.set_colors(rgb_list)
        self.current_pattern_lbl.set_label(f"{self.current_pattern.icon} {self.current_pattern.name.upper()}")

    def _on_pattern_card_clicked(self, btn: Gtk.Button, pattern):
        self.current_pattern = pattern
        self._update_preview_from_pattern()
        self._populate_pattern_grid()

        # Save setting
        self.settings["current_pattern_id"] = pattern.id
        save_settings(self.settings)

        # Send to hardware if connected
        if self.driver.connected:
            threading.Thread(target=self._send_pattern_to_hardware, daemon=True).start()

    def _send_pattern_to_hardware(self):
        try:
            self.driver.set_hardware_animation(self.user_light_mode, 4)
            br = self.brightness / 100.0
            colors = self.current_pattern.fn(KEYBOARD_LAYOUT)
            flat = [0] * (KEY_COUNT * 3)
            for i, key in enumerate(KEYBOARD_LAYOUT):
                if i < len(colors):
                    c = colors[i]
                    flat[key.index * 3] = round(c.r * br)
                    flat[key.index * 3 + 1] = round(c.g * br)
                    flat[key.index * 3 + 2] = round(c.b * br)
            self.driver.set_all_key_colors(flat, KEY_COUNT)
            self._on_driver_log(f"Applied pattern '{self.current_pattern.name}' to keyboard")
        except Exception as e:
            self._on_driver_log(f"Error applying pattern: {e}")

    def _on_brightness_changed(self, scale: Gtk.Scale):
        self.brightness = int(scale.get_value())
        self.brightness_val_lbl.set_label(f"{self.brightness}%")
        self._update_preview_from_pattern()
        self.settings["brightness"] = self.brightness
        save_settings(self.settings)

        if self.driver.connected:
            threading.Thread(target=self._send_pattern_to_hardware, daemon=True).start()

    def _on_search_changed(self, entry: Gtk.SearchEntry):
        self._populate_pattern_grid()

    def _on_category_clicked(self, btn: Gtk.Button, cat_id: str):
        self.active_category = cat_id
        for cid, b in self.cat_buttons.items():
            if cid == cat_id:
                b.add_css_class("active")
            else:
                b.remove_css_class("active")
        self.settings["active_category"] = cat_id
        save_settings(self.settings)
        self._populate_pattern_grid()

    def _on_rev_toggle(self, check: Gtk.CheckButton):
        self.user_light_mode = 20 if check.get_active() else 16
        self.settings["user_light_mode"] = self.user_light_mode
        save_settings(self.settings)
        self._on_driver_log(f"Hardware UserLight mode set to {self.user_light_mode}")

    def _select_hw_color(self, color_hex: str):
        self.hw_color = color_hex
        self.multi_btn.remove_css_class("active")
        if color_hex == "multi":
            self.multi_btn.add_css_class("active")

        for h, btn in self.swatch_buttons.items():
            if h.lower() == color_hex.lower():
                btn.add_css_class("active")
            else:
                btn.remove_css_class("active")

    def _on_apply_hw_clicked(self, btn: Gtk.Button):
        mode_idx = self.mode_combo.get_selected()
        mode = self.user_light_mode if mode_idx == 16 else mode_idx
        speed = int(self.speed_scale.get_value())
        bright = int(self.hw_bright_scale.get_value())
        color_hex = self.hw_color

        if not self.driver.connected:
            self._on_driver_log("Cannot apply HW FX: Keyboard not connected")
            return

        def _worker():
            try:
                if color_hex == "multi":
                    self.driver.set_hardware_animation(mode, bright, speed, 0, 0, None)
                else:
                    hsv = hex_to_hsv(color_hex)
                    self.driver.set_hardware_animation(mode, bright, speed, 1, 0, hsv)
                self._on_driver_log(f"Hardware animation applied: mode={mode}, bright={bright}, speed={speed}")
            except Exception as e:
                self._on_driver_log(f"Error applying hardware animation: {e}")

        threading.Thread(target=_worker, daemon=True).start()

    def _set_custom_paint_color(self, hex_color: str):
        r, g, b = hex_to_rgb(hex_color)
        self.custom_kb.set_paint_color(r, g, b)
        self._on_driver_log(f"Paint color selected: {hex_color}")

    def _on_custom_key_painted(self, idx: int, rgb: Tuple[int, int, int]):
        self.custom_colors[idx] = rgb
        if self.driver.connected:
            threading.Thread(target=self._push_custom_to_hardware, daemon=True).start()

    def _on_custom_fill(self, btn: Gtk.Button):
        self.custom_undo_stack.append(list(self.custom_colors))
        color = self.custom_kb.paint_color
        self.custom_colors = [color] * len(KEYBOARD_LAYOUT)
        self.custom_kb.set_colors(self.custom_colors)
        if self.driver.connected:
            threading.Thread(target=self._push_custom_to_hardware, daemon=True).start()

    def _on_custom_import_sync(self, btn: Gtk.Button):
        self.custom_undo_stack.append(list(self.custom_colors))
        colors = self.current_pattern.fn(KEYBOARD_LAYOUT)
        self.custom_colors = [(c.r, c.g, c.b) for c in colors]
        self.custom_kb.set_colors(self.custom_colors)
        if self.driver.connected:
            threading.Thread(target=self._push_custom_to_hardware, daemon=True).start()

    def _on_custom_clear(self, btn: Gtk.Button):
        self.custom_undo_stack.append(list(self.custom_colors))
        self.custom_colors = [(0, 0, 0)] * len(KEYBOARD_LAYOUT)
        self.custom_kb.set_colors(self.custom_colors)
        if self.driver.connected:
            threading.Thread(target=self._push_custom_to_hardware, daemon=True).start()

    def _on_custom_undo(self, btn: Gtk.Button):
        if self.custom_undo_stack:
            self.custom_colors = self.custom_undo_stack.pop()
            self.custom_kb.set_colors(self.custom_colors)
            if self.driver.connected:
                threading.Thread(target=self._push_custom_to_hardware, daemon=True).start()

    def _on_custom_push(self, btn: Gtk.Button):
        if self.driver.connected:
            threading.Thread(target=self._push_custom_to_hardware, daemon=True).start()
        else:
            self._on_driver_log("Cannot push custom preset: Keyboard not connected")

    def _push_custom_to_hardware(self):
        try:
            self.driver.set_hardware_animation(self.user_light_mode, 4)
            flat = [0] * (KEY_COUNT * 3)
            for i, key in enumerate(KEYBOARD_LAYOUT):
                if i < len(self.custom_colors):
                    r, g, b = self.custom_colors[i]
                    flat[key.index * 3] = r
                    flat[key.index * 3 + 1] = g
                    flat[key.index * 3 + 2] = b
            self.driver.set_all_key_colors(flat, KEY_COUNT)
            self._on_driver_log("Custom RGB preset pushed to keyboard")
        except Exception as e:
            self._on_driver_log(f"Error pushing custom preset: {e}")

    def _auto_connect_background(self):
        def _connect():
            try:
                info = self.driver.connect()
                GLib.idle_add(self._update_connection_ui, True, info)
                # Apply current pattern
                self._send_pattern_to_hardware()
            except Exception as e:
                GLib.idle_add(self._update_connection_ui, False, None)

        threading.Thread(target=_connect, daemon=True).start()

    def _on_connect_clicked(self, btn: Gtk.Button):
        if self.driver.connected:
            self.driver.disconnect()
            self._update_connection_ui(False, None)
        else:
            btn.set_sensitive(False)
            btn.set_label("Connecting...")

            def _connect():
                try:
                    info = self.driver.connect()
                    GLib.idle_add(self._update_connection_ui, True, info)
                    self._send_pattern_to_hardware()
                except Exception as e:
                    self._on_driver_log(f"Connection failed: {e}")
                    GLib.idle_add(self._update_connection_ui, False, None)

            threading.Thread(target=_connect, daemon=True).start()

    def _update_connection_ui(self, connected: bool, info: Optional[dict]):
        self.connect_btn.set_sensitive(True)
        if connected:
            self.status_badge.set_label("ONLINE")
            self.status_badge.remove_css_class("status-badge-offline")
            self.status_badge.add_css_class("status-badge-online")
            self.connect_btn.set_label("Disconnect")
        else:
            self.status_badge.set_label("OFFLINE")
            self.status_badge.remove_css_class("status-badge-online")
            self.status_badge.add_css_class("status-badge-offline")
            self.connect_btn.set_label("Connect")

    def _on_about_clicked(self, btn: Gtk.Button):
        about = Adw.AboutWindow(
            application_name="AntRGB",
            application_icon="io.github.antrgb.MK1300Linux",
            developer_name="AntRGB Contributors",
            version="1.0.0",
            copyright="© 2026 AntRGB Contributors\nOriginal work Copyright 2024 Yash (kickTROLL)",
            license_type=Gtk.License.APACHE_2_0,
            website="https://github.com/kickTROLL/mk1300v2_RGB",
            issue_url="https://github.com/kickTROLL/mk1300v2_RGB",
        )
        about.set_comments(
            "Native Linux RGB controller for Ant Esports MK1300 V2 60% per-key RGB keyboard.\n\n"
            "Ported 1:1 from the open-source web tool by Yash (kickTROLL):\n"
            "https://github.com/kickTROLL/mk1300v2_RGB\n\n"
            "Features 90 static patterns, hardware animations, live visualizer, "
            "and Tokyo Night / Omarchy theme integration."
        )
        about.set_transient_for(self.window)
        about.present()


def main():
    app = AntRGBApp()
    return app.run(sys.argv)


if __name__ == "__main__":
    sys.exit(main())
