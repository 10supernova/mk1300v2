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
from .keycodes import (
    ALL_ACTIONS,
    CAT_STANDARD,
    CAT_MEDIA,
    CAT_MOUSE,
    CAT_LAYER,
    CAT_SYSTEM,
    STANDARD_ACTIONS,
    MEDIA_ACTIONS,
    MOUSE_ACTIONS,
    LAYER_ACTIONS,
    SYSTEM_ACTIONS,
    ACTION_BY_TUPLE,
    describe_key_tuple,
    get_default_mappings,
    KeyAction,
)


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

    def __init__(self, interactive: bool = False, mode: str = "paint"):
        super().__init__()
        self.interactive = interactive
        self.mode = mode  # "paint" or "select"
        self.colors: List[Tuple[int, int, int]] = [(0, 0, 0)] * len(KEYBOARD_LAYOUT)
        self.paint_color: Tuple[int, int, int] = (255, 45, 120)  # Default neon pink
        self.selected_indices: set = set()
        self.selected_key_idx: Optional[int] = None
        self.key_sublabels: Optional[List[str]] = None
        self.is_modified: Optional[List[bool]] = None
        self.zoom: float = 1.0
        self.on_color_changed = None  # callback(key_idx, rgb)
        self.on_color_picked = None   # callback(rgb_hex)
        self.on_key_clicked = None    # callback(key_idx)

        self.set_draw_func(self._draw)
        self.set_hexpand(True)
        self.set_vexpand(False)
        self.set_content_height(160)
        self.set_content_width(460)

        if self.interactive:
            if self.mode == "select":
                select_click = Gtk.GestureClick()
                select_click.set_button(1)
                select_click.connect("pressed", self._on_select_click)
                self.add_controller(select_click)
            else:
                # Click and drag controller for painting
                drag = Gtk.GestureDrag()
                drag.connect("drag-begin", self._on_drag_begin)
                drag.connect("drag-update", self._on_drag_update)
                drag.connect("drag-end", self._on_drag_end)
                self.add_controller(drag)

                # Secondary click (eyedropper)
                click = Gtk.GestureClick()
                click.set_button(3)  # right-click
                click.connect("pressed", self._on_right_click)
                self.add_controller(click)

    def set_zoom(self, zoom: float):
        """Set zoom scale (0.8x to 2.5x) and adjust layout."""
        self.zoom = max(0.8, min(2.5, zoom))
        self.set_content_width(int(580 * self.zoom))
        self.set_content_height(int(190 * self.zoom))
        self.queue_draw()

    def _on_select_click(self, gesture, n_press, x, y):
        w = self.get_width()
        h = self.get_height()
        idx = self._get_key_at(x, y, w, h)
        if idx is not None:
            self.selected_key_idx = idx
            self.queue_draw()
            if self.on_key_clicked:
                self.on_key_clicked(idx)

    def set_colors(self, colors: List[Tuple[int, int, int]]):
        self.colors = colors
        self.queue_draw()

    def set_paint_color(self, r: int, g: int, b: int):
        self.paint_color = (r, g, b)

    def _get_key_at(self, px: float, py: float, w: float, h: float) -> Optional[int]:
        base_scale = min(w / KB_WIDTH, h / KB_HEIGHT) * 0.95
        scale = base_scale * self.zoom
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
        # Calculate fit with zoom multiplier
        base_scale = min(width / KB_WIDTH, height / KB_HEIGHT) * 0.95
        scale = base_scale * self.zoom
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

            is_selected = (self.selected_key_idx == i)
            sublabel = self.key_sublabels[i] if (self.key_sublabels and i < len(self.key_sublabels)) else None
            modified = self.is_modified[i] if (self.is_modified and i < len(self.is_modified)) else False

            # Selection / Modified outer glow
            if is_selected:
                cr.set_source_rgba(0.73, 0.60, 0.97, 0.45) # Tokyo Night purple selection
                self._draw_rounded_rect(cr, kx - 3.0, ky - 3.0, kw + 6.0, kh + 6.0, corner_r + 3.0)
                cr.fill()
            elif modified:
                cr.set_source_rgba(0.49, 0.81, 1.0, 0.35) # Tokyo Night cyan glow for modified keys
                self._draw_rounded_rect(cr, kx - 2.5, ky - 2.5, kw + 5.0, kh + 5.0, corner_r + 2.5)
                cr.fill()

            r, g, b = self.colors[i] if i < len(self.colors) else (0, 0, 0)
            rf, gf, bf = r / 255.0, g / 255.0, b / 255.0
            brightness = max(r, g, b)

            # Draw outer glow if key is illuminated
            if brightness > 30 and not is_selected and not modified:
                glow_r = corner_r + 2.0
                cr.set_source_rgba(rf, gf, bf, 0.25)
                self._draw_rounded_rect(cr, kx - 1.5, ky - 1.5, kw + 3.0, kh + 3.0, glow_r)
                cr.fill()

            # Keycap background
            if is_selected:
                cr.set_source_rgba(0.20, 0.23, 0.38, 0.98)
            elif modified:
                cr.set_source_rgba(0.12, 0.22, 0.36, 0.98)
            else:
                cr.set_source_rgba(rf * 0.85 + 0.08, gf * 0.85 + 0.08, bf * 0.85 + 0.12, 0.95)
            self._draw_rounded_rect(cr, kx, ky, kw, kh, corner_r)
            cr.fill()

            # Keycap border
            if is_selected:
                cr.set_source_rgba(0.73, 0.60, 0.97, 1.0)
                cr.set_line_width(2.0)
                self._draw_rounded_rect(cr, kx, ky, kw, kh, corner_r)
                cr.stroke()
            elif modified:
                cr.set_source_rgba(0.49, 0.81, 1.0, 0.95)
                cr.set_line_width(1.8)
                self._draw_rounded_rect(cr, kx, ky, kw, kh, corner_r)
                cr.stroke()
            elif brightness > 40:
                cr.set_source_rgba(rf, gf, bf, 0.7)
                cr.set_line_width(1.0)
                self._draw_rounded_rect(cr, kx, ky, kw, kh, corner_r)
                cr.stroke()
            else:
                cr.set_source_rgba(0.25, 0.28, 0.38, 0.5)
                cr.set_line_width(1.0)
                self._draw_rounded_rect(cr, kx, ky, kw, kh, corner_r)
                cr.stroke()

            # Key label text
            if modified and sublabel:
                # Active function name displayed prominently in cyan
                cr.set_source_rgba(0.49, 0.81, 1.0, 1.0)
                cr.set_font_size(font_size * 0.82)
                disp = sublabel if len(sublabel) <= 6 else sublabel[:5] + "…"
                ext = cr.text_extents(disp)
                cr.move_to(kx + (kw - ext.width) / 2.0 - ext.x_bearing, ky + kh * 0.44)
                cr.show_text(disp)

                # Default physical legend as subscript below
                cr.set_source_rgba(0.65, 0.70, 0.85, 0.65)
                cr.set_font_size(max(5.5, font_size * 0.56))
                sub_disp = f"[{key.name}]"
                ext_sub = cr.text_extents(sub_disp)
                cr.move_to(kx + (kw - ext_sub.width) / 2.0 - ext_sub.x_bearing, ky + kh * 0.82)
                cr.show_text(sub_disp)
                cr.set_font_size(font_size)
            elif sublabel and sublabel != key.name:
                # Key name top
                cr.set_source_rgba(0.95, 0.95, 1.0, 0.95)
                cr.set_font_size(font_size * 0.78)
                ext1 = cr.text_extents(key.name)
                cr.move_to(kx + (kw - ext1.width) / 2.0 - ext1.x_bearing, ky + kh * 0.40)
                cr.show_text(key.name)
                # Sublabel bottom
                cr.set_source_rgba(0.48, 0.64, 0.97, 0.95)
                cr.set_font_size(max(5.5, font_size * 0.60))
                disp = sublabel if len(sublabel) <= 7 else sublabel[:6] + "…"
                ext2 = cr.text_extents(disp)
                cr.move_to(kx + (kw - ext2.width) / 2.0 - ext2.x_bearing, ky + kh * 0.80)
                cr.show_text(disp)
                cr.set_font_size(font_size)
            else:
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

        # Key mapping & function behavior state
        self.current_layer = 0
        self.current_profile = 0
        self.layer_mappings: Dict[int, List[Tuple[int, int, int, int]]] = {
            0: get_default_mappings(0),
            1: get_default_mappings(1),
        }
        self.selected_key_idx = 0
        self.action_categories = [CAT_STANDARD, CAT_MEDIA, CAT_MOUSE, CAT_LAYER, CAT_SYSTEM]
        self.current_cat_actions: List[KeyAction] = STANDARD_ACTIONS

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

        # Tab 4: Key Remapping & Function Behavior
        keymap_tab = self._build_keymap_tab()
        self.stack.add_titled(keymap_tab, "keymap", "Keys & Functions")

        # Tab 5: Diagnostics Log
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

    def _build_keymap_tab(self) -> Gtk.Widget:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_vexpand(True)

        # Toolbar
        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        toolbar.add_css_class("card-panel")

        # Layer selector
        l_lbl = Gtk.Label(label="Layer:")
        l_lbl.add_css_class("subtitle-label")
        toolbar.append(l_lbl)

        layer_model = Gtk.StringList.new(["Layer 0: Base / Standard", "Layer 1: Fn Function Layer"])
        self.layer_dropdown = Gtk.DropDown.new(layer_model, None)
        self.layer_dropdown.set_selected(self.current_layer)
        self.layer_dropdown.connect("notify::selected", self._on_layer_selected)
        toolbar.append(self.layer_dropdown)

        # Profile selector
        p_lbl = Gtk.Label(label="Profile:")
        p_lbl.add_css_class("subtitle-label")
        toolbar.append(p_lbl)

        profile_model = Gtk.StringList.new(["Profile 1", "Profile 2", "Profile 3"])
        self.profile_dropdown = Gtk.DropDown.new(profile_model, None)
        self.profile_dropdown.set_selected(self.current_profile)
        self.profile_dropdown.connect("notify::selected", self._on_profile_selected)
        toolbar.append(self.profile_dropdown)

        # Auto sleep
        s_lbl = Gtk.Label(label="Sleep:")
        s_lbl.add_css_class("subtitle-label")
        toolbar.append(s_lbl)

        sleep_model = Gtk.StringList.new(["Never", "2 min", "5 min", "10 min", "30 min"])
        self.sleep_dropdown = Gtk.DropDown.new(sleep_model, None)
        self.sleep_dropdown.set_selected(2)
        self.sleep_dropdown.connect("notify::selected", self._on_sleep_selected)
        toolbar.append(self.sleep_dropdown)

        # Zoom Controls
        zoom_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        z_lbl = Gtk.Label(label="Zoom:")
        z_lbl.add_css_class("subtitle-label")
        zoom_box.append(z_lbl)

        z_out = Gtk.Button(label="🔍 −")
        z_out.set_tooltip_text("Zoom out keyboard preview")
        z_out.connect("clicked", self._on_zoom_out)
        zoom_box.append(z_out)

        self.zoom_lbl = Gtk.Label(label="135%")
        self.zoom_lbl.add_css_class("monospace-font")
        zoom_box.append(self.zoom_lbl)

        z_in = Gtk.Button(label="🔍 +")
        z_in.set_tooltip_text("Zoom in keyboard preview")
        z_in.connect("clicked", self._on_zoom_in)
        zoom_box.append(z_in)
        toolbar.append(zoom_box)

        toolbar.append(Gtk.Box(hexpand=True))

        # Test helper: Switch number row to Fn layer
        swap_btn = Gtk.Button(label="⚡ Switch Num Row ↔ F1-F12 (Test)")
        swap_btn.set_tooltip_text("Toggle number row between numbers 1..= and F1..F12 on hardware for testing")
        swap_btn.connect("clicked", self._on_swap_num_fn_clicked)
        toolbar.append(swap_btn)

        # Actions
        read_btn = Gtk.Button(label="Read from Keyboard")
        read_btn.set_tooltip_text("Fetch current key mappings directly from keyboard hardware")
        read_btn.connect("clicked", self._on_read_keymap_clicked)
        toolbar.append(read_btn)

        reset_btn = Gtk.Button(label="Reset Defaults")
        reset_btn.set_tooltip_text("Reset current layer to factory default mappings")
        reset_btn.connect("clicked", self._on_reset_keymap_clicked)
        toolbar.append(reset_btn)

        apply_btn = Gtk.Button(label="Apply to Keyboard")
        apply_btn.add_css_class("primary-action")
        apply_btn.set_tooltip_text("Write all 61 key mappings for this layer to keyboard firmware")
        apply_btn.connect("clicked", self._on_apply_keymap_clicked)
        toolbar.append(apply_btn)

        box.append(toolbar)

        # Interactive Canvas Card (Zoomed in & larger)
        kb_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        kb_card.add_css_class("card-panel")
        kb_card.set_vexpand(True)

        kb_hint = Gtk.Label(label="Click any key below to select it and customize its function behavior (modified keys glow in cyan):")
        kb_hint.add_css_class("subtitle-label")
        kb_card.append(kb_hint)

        scroll_kb = Gtk.ScrolledWindow()
        scroll_kb.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scroll_kb.set_vexpand(True)
        scroll_kb.set_min_content_height(280)

        self.keymap_kb = KeyboardWidget(interactive=True, mode="select")
        self.keymap_kb.selected_key_idx = 0
        self.keymap_kb.zoom = 1.35
        self.keymap_kb.set_content_height(280)
        self.keymap_kb.set_content_width(820)
        self.keymap_kb.set_vexpand(True)
        self.keymap_kb.set_hexpand(True)
        self.keymap_kb.on_key_clicked = self._on_keymap_key_clicked
        self._update_keymap_kb_labels()

        scroll_kb.set_child(self.keymap_kb)
        kb_card.append(scroll_kb)
        box.append(kb_card)

        # Key Inspector & Remap Editor Card
        editor_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        editor_card.add_css_class("card-panel")

        ed_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        self.selected_key_title = Gtk.Label(label="SELECTED KEY: Esc (#0)")
        self.selected_key_title.add_css_class("accent-text")
        ed_header.append(self.selected_key_title)

        self.selected_key_badge = Gtk.Label(label="Current: Standard Keys: Esc")
        self.selected_key_badge.add_css_class("subtitle-label")
        ed_header.append(self.selected_key_badge)

        editor_card.append(ed_header)

        # Controls row
        ed_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)

        cat_lbl = Gtk.Label(label="Category:")
        cat_lbl.add_css_class("subtitle-label")
        ed_row.append(cat_lbl)

        cat_model = Gtk.StringList.new(self.action_categories)
        self.cat_dropdown = Gtk.DropDown.new(cat_model, None)
        self.cat_dropdown.set_selected(0)
        self.cat_dropdown.connect("notify::selected", self._on_action_cat_changed)
        ed_row.append(self.cat_dropdown)

        act_lbl = Gtk.Label(label="Function:")
        act_lbl.add_css_class("subtitle-label")
        ed_row.append(act_lbl)

        self.current_cat_actions = STANDARD_ACTIONS
        self.action_model = Gtk.StringList.new([a.name for a in self.current_cat_actions])
        self.action_dropdown = Gtk.DropDown.new(self.action_model, None)
        self.action_dropdown.set_selected(0)
        ed_row.append(self.action_dropdown)

        assign_btn = Gtk.Button(label="Assign to Key")
        assign_btn.add_css_class("primary-action")
        assign_btn.connect("clicked", self._on_assign_action_clicked)
        ed_row.append(assign_btn)

        instant_btn = Gtk.Button(label="Remap Single Key (HID)")
        instant_btn.set_tooltip_text("Immediately send remapping for this key to connected keyboard")
        instant_btn.connect("clicked", self._on_instant_remap_clicked)
        ed_row.append(instant_btn)

        editor_card.append(ed_row)
        box.append(editor_card)

        self._update_selected_key_ui()
        return box

    def _on_zoom_in(self, btn: Gtk.Button):
        new_z = round(self.keymap_kb.zoom + 0.15, 2)
        self.keymap_kb.set_zoom(new_z)
        self.zoom_lbl.set_label(f"{int(round(self.keymap_kb.zoom * 100))}%")

    def _on_zoom_out(self, btn: Gtk.Button):
        new_z = round(self.keymap_kb.zoom - 0.15, 2)
        self.keymap_kb.set_zoom(new_z)
        self.zoom_lbl.set_label(f"{int(round(self.keymap_kb.zoom * 100))}%")

    def _on_swap_num_fn_clicked(self, btn: Gtk.Button):
        if not self.driver.connected:
            self._on_driver_log("Cannot switch: Keyboard not connected")
            return

        current_map = self.layer_mappings.get(self.current_layer, [])
        is_already_fn = False
        if len(current_map) > 1:
            is_already_fn = (current_map[1][2] == 58)

        layer = self.current_layer
        target_enable_f = not is_already_fn

        def _worker():
            try:
                state_str = "Standard Numbers (1-0, -, =)" if is_already_fn else "Function Keys (F1-F12)"
                self._on_driver_log(f"Switching Layer {layer} number row to {state_str}...")
                self.driver.switch_num_to_fn_layer(layer=layer, enable_f_keys=target_enable_f)
                m = self.driver.get_layout_key_mappings(layer=layer)
                if m and len(m) == len(KEYBOARD_LAYOUT):
                    self.layer_mappings[layer] = m
                    GLib.idle_add(self._update_keymap_kb_labels)
                    GLib.idle_add(self._update_selected_key_ui)
                self._on_driver_log(f"✓ Number row successfully switched to {state_str} on hardware!")
            except Exception as e:
                self._on_driver_log(f"Error switching number row: {e}")

        threading.Thread(target=_worker, daemon=True).start()

    def _on_keymap_key_clicked(self, idx: int):
        self.selected_key_idx = idx
        self._update_selected_key_ui()

    def _update_keymap_kb_labels(self):
        if not hasattr(self, "keymap_kb"):
            return
        current_map = self.layer_mappings.get(self.current_layer, [])
        default_map = get_default_mappings(self.current_layer)
        labels = []
        modified = []
        for i in range(len(KEYBOARD_LAYOUT)):
            if i < len(current_map):
                tup = current_map[i]
                desc = describe_key_tuple(tup)
                short_desc = desc.split(":")[-1].strip()
                labels.append(short_desc)
                def_tup = default_map[i] if i < len(default_map) else (0, 0, 0, 0)
                modified.append(tup != def_tup)
            else:
                labels.append("")
                modified.append(False)
        self.keymap_kb.key_sublabels = labels
        self.keymap_kb.is_modified = modified
        self.keymap_kb.queue_draw()

    def _update_selected_key_ui(self):
        if not hasattr(self, "selected_key_title"):
            return
        idx = self.selected_key_idx
        if 0 <= idx < len(KEYBOARD_LAYOUT):
            key = KEYBOARD_LAYOUT[idx]
            self.selected_key_title.set_label(f"SELECTED KEY: {key.name} (Layout #{idx}, HW Matrix #{key.index})")
            current_map = self.layer_mappings.get(self.current_layer, [])
            default_map = get_default_mappings(self.current_layer)
            if idx < len(current_map):
                desc = describe_key_tuple(current_map[idx])
                def_tup = default_map[idx] if idx < len(default_map) else (0, 0, 0, 0)
                is_mod = (current_map[idx] != def_tup)
                mod_tag = "  [⚡ MODIFIED]" if is_mod else ""
                self.selected_key_badge.set_label(f"Assigned: {desc}{mod_tag}")
            else:
                self.selected_key_badge.set_label("Assigned: Standard")

    def _on_action_cat_changed(self, dropdown: Gtk.DropDown, param):
        idx = dropdown.get_selected()
        cat = self.action_categories[idx] if idx < len(self.action_categories) else CAT_STANDARD
        if cat == CAT_STANDARD:
            self.current_cat_actions = STANDARD_ACTIONS
        elif cat == CAT_MEDIA:
            self.current_cat_actions = MEDIA_ACTIONS
        elif cat == CAT_MOUSE:
            self.current_cat_actions = MOUSE_ACTIONS
        elif cat == CAT_LAYER:
            self.current_cat_actions = LAYER_ACTIONS
        else:
            self.current_cat_actions = SYSTEM_ACTIONS

        self.action_model = Gtk.StringList.new([a.name for a in self.current_cat_actions])
        self.action_dropdown.set_model(self.action_model)
        self.action_dropdown.set_selected(0)

    def _on_assign_action_clicked(self, btn: Gtk.Button):
        act_idx = self.action_dropdown.get_selected()
        if 0 <= act_idx < len(self.current_cat_actions):
            action = self.current_cat_actions[act_idx]
            self.layer_mappings[self.current_layer][self.selected_key_idx] = action.tuple
            self._update_keymap_kb_labels()
            self._update_selected_key_ui()
            key = KEYBOARD_LAYOUT[self.selected_key_idx]
            self._on_driver_log(f"Assigned '{action.name}' to key '{key.name}' (HW #{key.index}) on Layer {self.current_layer}")

    def _on_instant_remap_clicked(self, btn: Gtk.Button):
        if not self.driver.connected:
            self._on_driver_log("Cannot remap: Keyboard not connected")
            return
        act_idx = self.action_dropdown.get_selected()
        if not (0 <= act_idx < len(self.current_cat_actions)):
            return
        action = self.current_cat_actions[act_idx]
        self.layer_mappings[self.current_layer][self.selected_key_idx] = action.tuple
        self._update_keymap_kb_labels()
        self._update_selected_key_ui()

        matrix_idx = KEYBOARD_LAYOUT[self.selected_key_idx].index
        key_name = KEYBOARD_LAYOUT[self.selected_key_idx].name
        layer = self.current_layer

        def _worker():
            try:
                self.driver.set_key_mapping(
                    matrix_index=matrix_idx,
                    key_type=action.key_type,
                    code1=action.code1,
                    code2=action.code2,
                    code3=action.code3,
                    layer=layer,
                )
                self._on_driver_log(f"✓ Remapped hardware slot #{matrix_idx} ({key_name}) to '{action.name}' on hardware")
            except Exception as e:
                self._on_driver_log(f"Error remapping key: {e}")

        threading.Thread(target=_worker, daemon=True).start()

    def _on_apply_keymap_clicked(self, btn: Gtk.Button):
        if not self.driver.connected:
            self._on_driver_log("Cannot apply keymap: Keyboard not connected")
            return
        mappings = list(self.layer_mappings[self.current_layer])
        layer = self.current_layer

        def _worker():
            try:
                self._on_driver_log(f"Writing all 61 key mappings to Layer {layer}...")
                self.driver.set_all_key_mappings(mappings, layer=layer)
                self._on_driver_log(f"✓ All key mappings applied successfully to Layer {layer}!")
            except Exception as e:
                self._on_driver_log(f"Error applying key mappings: {e}")

        threading.Thread(target=_worker, daemon=True).start()

    def _on_read_keymap_clicked(self, btn: Gtk.Button):
        if not self.driver.connected:
            self._on_driver_log("Cannot read keymap: Keyboard not connected")
            return
        layer = self.current_layer

        def _worker():
            try:
                self._on_driver_log(f"Reading live key mappings from Layer {layer}...")
                m = self.driver.get_layout_key_mappings(layer=layer)
                if m and len(m) == len(KEYBOARD_LAYOUT):
                    self.layer_mappings[layer] = m
                    GLib.idle_add(self._update_keymap_kb_labels)
                    GLib.idle_add(self._update_selected_key_ui)
                    self._on_driver_log(f"✓ Read {len(m)} key mappings from hardware Layer {layer}")
            except Exception as e:
                self._on_driver_log(f"Error reading key mappings: {e}")

        threading.Thread(target=_worker, daemon=True).start()

    def _on_reset_keymap_clicked(self, btn: Gtk.Button):
        self.layer_mappings[self.current_layer] = get_default_mappings(self.current_layer)
        self._update_keymap_kb_labels()
        self._update_selected_key_ui()
        self._on_driver_log(f"Reset Layer {self.current_layer} to factory defaults")

    def _on_layer_selected(self, dropdown: Gtk.DropDown, param):
        self.current_layer = dropdown.get_selected()
        self._update_keymap_kb_labels()
        self._update_selected_key_ui()
        self._on_driver_log(f"Selected Layer {self.current_layer}")

    def _on_profile_selected(self, dropdown: Gtk.DropDown, param):
        self.current_profile = dropdown.get_selected()
        if self.driver.connected:
            threading.Thread(target=lambda: self.driver.set_current_profile(self.current_profile), daemon=True).start()

    def _on_sleep_selected(self, dropdown: Gtk.DropDown, param):
        idx = dropdown.get_selected()
        seconds_map = [0, 120, 300, 600, 1800]
        sec = seconds_map[idx] if idx < len(seconds_map) else 300
        if self.driver.connected:
            threading.Thread(target=lambda: self.driver.set_auto_sleep_time(sec), daemon=True).start()

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
                try:
                    m0 = self.driver.get_layout_key_mappings(layer=0)
                    m1 = self.driver.get_layout_key_mappings(layer=1)
                    if m0 and len(m0) == len(KEYBOARD_LAYOUT):
                        self.layer_mappings[0] = m0
                    if m1 and len(m1) == len(KEYBOARD_LAYOUT):
                        self.layer_mappings[1] = m1
                    GLib.idle_add(self._update_keymap_kb_labels)
                    GLib.idle_add(self._update_selected_key_ui)
                except Exception as ex:
                    self._on_driver_log(f"Keymap sync notice: {ex}")
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
                    try:
                        m0 = self.driver.get_layout_key_mappings(layer=0)
                        m1 = self.driver.get_layout_key_mappings(layer=1)
                        if m0 and len(m0) == len(KEYBOARD_LAYOUT):
                            self.layer_mappings[0] = m0
                        if m1 and len(m1) == len(KEYBOARD_LAYOUT):
                            self.layer_mappings[1] = m1
                        GLib.idle_add(self._update_keymap_kb_labels)
                        GLib.idle_add(self._update_selected_key_ui)
                    except Exception as ex:
                        self._on_driver_log(f"Keymap sync notice: {ex}")
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
