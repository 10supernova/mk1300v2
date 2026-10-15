"""
mk1300 - Native Linux RGB controller for Ant Esports MK1300 V2 keyboard.
"""

from .layout import KEYBOARD_LAYOUT, KEY_COUNT, MAX_KEY_INDEX, KB_WIDTH, KB_HEIGHT, Key
from .driver import HIDDriver

__all__ = [
    "KEYBOARD_LAYOUT",
    "KEY_COUNT",
    "MAX_KEY_INDEX",
    "KB_WIDTH",
    "KB_HEIGHT",
    "Key",
    "HIDDriver",
]
