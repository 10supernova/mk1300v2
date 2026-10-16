"""
Key definitions, categories, and USB HID/Consumer/Mouse mappings for Ant Esports MK1300 V2.
Extracted and matched with official Windows MK1300-V21-0-0 firmware protocol.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

@dataclass(frozen=True)
class KeyAction:
    name: str
    category: str
    key_type: int
    code1: int
    code2: int
    code3: int = 0
    description: str = ""

    @property
    def tuple(self) -> Tuple[int, int, int, int]:
        return (self.key_type, self.code1, self.code2, self.code3)


# Categories
CAT_STANDARD = "Standard Keys"
CAT_MEDIA = "Media & Volume"
CAT_MOUSE = "Mouse Actions"
CAT_LAYER = "Layer & Fn"
CAT_SYSTEM = "System & Special"

STANDARD_ACTIONS: List[KeyAction] = [
    # Letters
    KeyAction("A", CAT_STANDARD, 32, 0, 4),
    KeyAction("B", CAT_STANDARD, 32, 0, 5),
    KeyAction("C", CAT_STANDARD, 32, 0, 6),
    KeyAction("D", CAT_STANDARD, 32, 0, 7),
    KeyAction("E", CAT_STANDARD, 32, 0, 8),
    KeyAction("F", CAT_STANDARD, 32, 0, 9),
    KeyAction("G", CAT_STANDARD, 32, 0, 10),
    KeyAction("H", CAT_STANDARD, 32, 0, 11),
    KeyAction("I", CAT_STANDARD, 32, 0, 12),
    KeyAction("J", CAT_STANDARD, 32, 0, 13),
    KeyAction("K", CAT_STANDARD, 32, 0, 14),
    KeyAction("L", CAT_STANDARD, 32, 0, 15),
    KeyAction("M", CAT_STANDARD, 32, 0, 16),
    KeyAction("N", CAT_STANDARD, 32, 0, 17),
    KeyAction("O", CAT_STANDARD, 32, 0, 18),
    KeyAction("P", CAT_STANDARD, 32, 0, 19),
    KeyAction("Q", CAT_STANDARD, 32, 0, 20),
    KeyAction("R", CAT_STANDARD, 32, 0, 21),
    KeyAction("S", CAT_STANDARD, 32, 0, 22),
    KeyAction("T", CAT_STANDARD, 32, 0, 23),
    KeyAction("U", CAT_STANDARD, 32, 0, 24),
    KeyAction("V", CAT_STANDARD, 32, 0, 25),
    KeyAction("W", CAT_STANDARD, 32, 0, 26),
    KeyAction("X", CAT_STANDARD, 32, 0, 27),
    KeyAction("Y", CAT_STANDARD, 32, 0, 28),
    KeyAction("Z", CAT_STANDARD, 32, 0, 29),

    # Numbers
    KeyAction("1", CAT_STANDARD, 32, 0, 30),
    KeyAction("2", CAT_STANDARD, 32, 0, 31),
    KeyAction("3", CAT_STANDARD, 32, 0, 32),
    KeyAction("4", CAT_STANDARD, 32, 0, 33),
    KeyAction("5", CAT_STANDARD, 32, 0, 34),
    KeyAction("6", CAT_STANDARD, 32, 0, 35),
    KeyAction("7", CAT_STANDARD, 32, 0, 36),
    KeyAction("8", CAT_STANDARD, 32, 0, 37),
    KeyAction("9", CAT_STANDARD, 32, 0, 38),
    KeyAction("0", CAT_STANDARD, 32, 0, 39),

    # Function Keys
    KeyAction("F1", CAT_STANDARD, 32, 0, 58),
    KeyAction("F2", CAT_STANDARD, 32, 0, 59),
    KeyAction("F3", CAT_STANDARD, 32, 0, 60),
    KeyAction("F4", CAT_STANDARD, 32, 0, 61),
    KeyAction("F5", CAT_STANDARD, 32, 0, 62),
    KeyAction("F6", CAT_STANDARD, 32, 0, 63),
    KeyAction("F7", CAT_STANDARD, 32, 0, 64),
    KeyAction("F8", CAT_STANDARD, 32, 0, 65),
    KeyAction("F9", CAT_STANDARD, 32, 0, 66),
    KeyAction("F10", CAT_STANDARD, 32, 0, 67),
    KeyAction("F11", CAT_STANDARD, 32, 0, 68),
    KeyAction("F12", CAT_STANDARD, 32, 0, 69),

    # Modifiers & Controls
    KeyAction("Enter", CAT_STANDARD, 32, 0, 40),
    KeyAction("Esc", CAT_STANDARD, 32, 0, 41),
    KeyAction("Backspace", CAT_STANDARD, 32, 0, 42),
    KeyAction("Tab", CAT_STANDARD, 32, 0, 43),
    KeyAction("Space", CAT_STANDARD, 32, 0, 44),
    KeyAction("Minus (-)", CAT_STANDARD, 32, 0, 45),
    KeyAction("Equal (=)", CAT_STANDARD, 32, 0, 46),
    KeyAction("Bracket Left ([)", CAT_STANDARD, 32, 0, 47),
    KeyAction("Bracket Right (])", CAT_STANDARD, 32, 0, 48),
    KeyAction("Backslash (\\)", CAT_STANDARD, 32, 0, 49),
    KeyAction("Semicolon (;)", CAT_STANDARD, 32, 0, 51),
    KeyAction("Quote (')", CAT_STANDARD, 32, 0, 52),
    KeyAction("Grave Accent (`)", CAT_STANDARD, 32, 0, 53),
    KeyAction("Comma (,)", CAT_STANDARD, 32, 0, 54),
    KeyAction("Period (.)", CAT_STANDARD, 32, 0, 55),
    KeyAction("Slash (/)", CAT_STANDARD, 32, 0, 56),
    KeyAction("CapsLock", CAT_STANDARD, 32, 0, 57),

    KeyAction("Left Ctrl", CAT_STANDARD, 32, 0, 224),
    KeyAction("Left Shift", CAT_STANDARD, 32, 0, 225),
    KeyAction("Left Alt", CAT_STANDARD, 32, 0, 226),
    KeyAction("Left Win", CAT_STANDARD, 32, 0, 227),
    KeyAction("Right Ctrl", CAT_STANDARD, 32, 0, 228),
    KeyAction("Right Shift", CAT_STANDARD, 32, 0, 229),
    KeyAction("Right Alt", CAT_STANDARD, 32, 0, 230),
    KeyAction("Right Win", CAT_STANDARD, 32, 0, 231),

    # Navigation
    KeyAction("PrintScreen", CAT_STANDARD, 32, 0, 70),
    KeyAction("ScrollLock", CAT_STANDARD, 32, 0, 71),
    KeyAction("Pause", CAT_STANDARD, 32, 0, 72),
    KeyAction("Insert", CAT_STANDARD, 32, 0, 73),
    KeyAction("Home", CAT_STANDARD, 32, 0, 74),
    KeyAction("PageUp", CAT_STANDARD, 32, 0, 75),
    KeyAction("Delete", CAT_STANDARD, 32, 0, 76),
    KeyAction("End", CAT_STANDARD, 32, 0, 77),
    KeyAction("PageDown", CAT_STANDARD, 32, 0, 78),
    KeyAction("Right Arrow", CAT_STANDARD, 32, 0, 79),
    KeyAction("Left Arrow", CAT_STANDARD, 32, 0, 80),
    KeyAction("Down Arrow", CAT_STANDARD, 32, 0, 81),
    KeyAction("Up Arrow", CAT_STANDARD, 32, 0, 82),
]

MEDIA_ACTIONS: List[KeyAction] = [
    KeyAction("Mute", CAT_MEDIA, 48, 226, 0),
    KeyAction("Volume Up", CAT_MEDIA, 48, 233, 0),
    KeyAction("Volume Down", CAT_MEDIA, 48, 234, 0),
    KeyAction("Play / Pause", CAT_MEDIA, 48, 205, 0),
    KeyAction("Next Track", CAT_MEDIA, 48, 181, 0),
    KeyAction("Previous Track", CAT_MEDIA, 48, 182, 0),
    KeyAction("Stop", CAT_MEDIA, 48, 183, 0),
    KeyAction("Media Player", CAT_MEDIA, 48, 131, 1),
    KeyAction("Calculator", CAT_MEDIA, 48, 146, 1),
    KeyAction("Browser Home", CAT_MEDIA, 48, 35, 2),
    KeyAction("Browser Refresh", CAT_MEDIA, 48, 39, 2),
    KeyAction("Browser Back", CAT_MEDIA, 48, 36, 2),
    KeyAction("Browser Forward", CAT_MEDIA, 48, 37, 2),
    KeyAction("Search", CAT_MEDIA, 48, 33, 2),
    KeyAction("Email", CAT_MEDIA, 48, 138, 1),
]

MOUSE_ACTIONS: List[KeyAction] = [
    KeyAction("Mouse Left Click", CAT_MOUSE, 17, 1, 0),
    KeyAction("Mouse Right Click", CAT_MOUSE, 17, 2, 0),
    KeyAction("Mouse Middle Click", CAT_MOUSE, 17, 4, 0),
    KeyAction("Mouse Wheel Up", CAT_MOUSE, 17, 0, 1),
    KeyAction("Mouse Wheel Down", CAT_MOUSE, 17, 0, 255),
]

LAYER_ACTIONS: List[KeyAction] = [
    KeyAction("Fn (Layer Switch)", CAT_LAYER, 19, 0, 0),
    KeyAction("Layer 0 Toggle", CAT_LAYER, 19, 1, 0),
    KeyAction("Layer 1 Toggle", CAT_LAYER, 19, 2, 0),
]

SYSTEM_ACTIONS: List[KeyAction] = [
    KeyAction("Disabled / None", CAT_SYSTEM, 0, 0, 0),
]

ALL_ACTIONS: List[KeyAction] = (
    STANDARD_ACTIONS + MEDIA_ACTIONS + MOUSE_ACTIONS + LAYER_ACTIONS + SYSTEM_ACTIONS
)

ACTION_BY_TUPLE: Dict[Tuple[int, int, int, int], KeyAction] = {
    a.tuple: a for a in ALL_ACTIONS
}

def describe_key_tuple(t: Tuple[int, int, int, int]) -> str:
    """Human-readable description of a 4-byte key mapping tuple."""
    if t in ACTION_BY_TUPLE:
        return f"{ACTION_BY_TUPLE[t].category}: {ACTION_BY_TUPLE[t].name}"
    
    key_type, c1, c2, c3 = t
    if key_type == 0:
        return "Disabled"
    if key_type == 32:
        return f"Standard (code={c2})"
    if key_type == 48:
        return f"Media (code1={c1}, code2={c2})"
    if key_type == 17:
        return f"Mouse (code1={c1}, code2={c2})"
    if key_type == 19:
        return f"Layer (val={c1})"
    return f"Custom (type={key_type}, {c1}, {c2}, {c3})"


def get_default_mappings(layer: int = 0) -> List[Tuple[int, int, int, int]]:
    """Return factory default 61-key tuples for layer 0 (base) or layer 1 (Fn)."""
    if layer == 0:
        # Standard QWERTY ANSI 60%
        return [
            (32, 0, 41, 0),  # Esc
            (32, 0, 30, 0),  # 1
            (32, 0, 31, 0),  # 2
            (32, 0, 32, 0),  # 3
            (32, 0, 33, 0),  # 4
            (32, 0, 34, 0),  # 5
            (32, 0, 35, 0),  # 6
            (32, 0, 36, 0),  # 7
            (32, 0, 37, 0),  # 8
            (32, 0, 38, 0),  # 9
            (32, 0, 39, 0),  # 0
            (32, 0, 45, 0),  # -
            (32, 0, 46, 0),  # =
            (32, 0, 42, 0),  # Backspace
            (32, 0, 43, 0),  # Tab
            (32, 0, 20, 0),  # Q
            (32, 0, 26, 0),  # W
            (32, 0, 8, 0),   # E
            (32, 0, 21, 0),  # R
            (32, 0, 23, 0),  # T
            (32, 0, 28, 0),  # Y
            (32, 0, 24, 0),  # U
            (32, 0, 12, 0),  # I
            (32, 0, 18, 0),  # O
            (32, 0, 19, 0),  # P
            (32, 0, 47, 0),  # [
            (32, 0, 48, 0),  # ]
            (32, 0, 49, 0),  # \
            (32, 0, 57, 0),  # Caps
            (32, 0, 4, 0),   # A
            (32, 0, 22, 0),  # S
            (32, 0, 7, 0),   # D
            (32, 0, 9, 0),   # F
            (32, 0, 10, 0),  # G
            (32, 0, 11, 0),  # H
            (32, 0, 13, 0),  # J
            (32, 0, 14, 0),  # K
            (32, 0, 15, 0),  # L
            (32, 0, 51, 0),  # ;
            (32, 0, 52, 0),  # '
            (32, 0, 40, 0),  # Enter
            (32, 0, 225, 0), # LShift
            (32, 0, 29, 0),  # Z
            (32, 0, 27, 0),  # X
            (32, 0, 6, 0),   # C
            (32, 0, 25, 0),  # V
            (32, 0, 5, 0),   # B
            (32, 0, 17, 0),  # N
            (32, 0, 16, 0),  # M
            (32, 0, 54, 0),  # <
            (32, 0, 55, 0),  # >
            (32, 0, 56, 0),  # ?
            (32, 0, 229, 0), # RShift
            (32, 0, 224, 0), # LCtrl
            (32, 0, 227, 0), # LWin
            (32, 0, 226, 0), # LAlt
            (32, 0, 44, 0),  # Space
            (32, 0, 230, 0), # RAlt
            (32, 0, 101, 0), # Menu
            (32, 0, 228, 0), # RCtrl
            (19, 0, 0, 0),   # Fn
        ]
    else:
        # Layer 1: Ant Esports MK1300 Factory Fn Layer
        return [
            (32, 0, 53, 0),   # ` (Grave)
            (48, 131, 1, 0),  # Media Player
            (48, 234, 0, 0),  # VolDown
            (48, 233, 0, 0),  # VolUp
            (48, 226, 0, 0),  # Mute
            (48, 182, 0, 0),  # Prev Track
            (48, 181, 0, 0),  # Next Track
            (48, 205, 0, 0),  # Play/Pause
            (48, 183, 0, 0),  # Stop
            (48, 35, 2, 0),   # Web Home
            (48, 138, 1, 0),  # Email
            (48, 39, 2, 0),   # Web Refresh
            (48, 146, 1, 0),  # Calculator
            (32, 0, 76, 0),   # Del
            (32, 0, 43, 0),   # Tab
            (32, 0, 20, 0),   # Q
            (32, 0, 26, 0),   # W
            (32, 0, 8, 0),    # E
            (32, 0, 21, 0),   # R
            (32, 0, 23, 0),   # T
            (32, 0, 28, 0),   # Y
            (32, 0, 70, 0),   # PrintScreen
            (32, 0, 82, 0),   # Up
            (32, 0, 71, 0),   # ScrollLock
            (32, 0, 72, 0),   # Pause
            (32, 0, 74, 0),   # Home
            (32, 0, 77, 0),   # End
            (32, 0, 49, 0),   # \
            (32, 0, 57, 0),   # Caps
            (32, 0, 4, 0),    # A
            (32, 0, 22, 0),   # S
            (32, 0, 7, 0),    # D
            (32, 0, 9, 0),    # F
            (32, 0, 10, 0),   # G
            (32, 0, 11, 0),   # H
            (32, 0, 80, 0),   # Left
            (32, 0, 81, 0),   # Down
            (32, 0, 79, 0),   # Right
            (32, 0, 75, 0),   # PageUp
            (32, 0, 78, 0),   # PageDown
            (32, 0, 40, 0),   # Enter
            (32, 0, 225, 0),  # LShift
            (32, 0, 29, 0),   # Z
            (32, 0, 27, 0),   # X
            (32, 0, 6, 0),    # C
            (32, 0, 25, 0),   # V
            (32, 0, 5, 0),    # B
            (32, 0, 17, 0),   # N
            (32, 0, 16, 0),   # M
            (32, 0, 54, 0),   # <
            (32, 0, 55, 0),   # >
            (32, 0, 76, 0),   # Delete
            (32, 0, 229, 0),  # RShift
            (32, 0, 224, 0),  # LCtrl
            (32, 0, 227, 0),  # LWin
            (32, 0, 226, 0),  # LAlt
            (32, 0, 44, 0),   # Space
            (32, 0, 230, 0),  # RAlt
            (32, 0, 101, 0),  # Menu
            (32, 0, 228, 0),  # RCtrl
            (19, 0, 0, 0),    # Fn
        ]
