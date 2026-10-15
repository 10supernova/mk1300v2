"""
ANT Esports MK1300 V2 - 60% keyboard layout definition and key matrix mapping.

Ported from https://github.com/kickTROLL/mk1300v2_RGB (Apache-2.0)
Original work Copyright 2024 Yash (kickTROLL)
Modified: JS to Python port for mk1300-linux
"""

from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass(frozen=True)
class Key:
    index: int
    x: float
    y: float
    w: float
    h: float
    name: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "index": self.index,
            "x": self.x,
            "y": self.y,
            "w": self.w,
            "h": self.h,
            "name": self.name,
        }


# Row 0: Esc, 1-0, -, =, Backspace
# Row 1: Tab, Q-P, [, ], backslash
# Row 2: Caps, A-L, ;, ', Enter
# Row 3: LShift, Z-?, Up, RShift
# Row 4: Ctrl, Win, Alt, Space, Alt, Menu, Ctrl, Fn

KEYBOARD_LAYOUT: List[Key] = [
    # Row 0 - number row (y=0)
    # NOTE: Esc uses index 21 (the ~ slot in the firmware matrix).
    # Index 0 is reserved for a non-existent function-row key on the full keyboard.
    Key(index=21, x=0.0,   y=0.0, w=1.0,  h=1.0, name="Esc"),
    Key(index=22, x=1.0,   y=0.0, w=1.0,  h=1.0, name="1"),
    Key(index=23, x=2.0,   y=0.0, w=1.0,  h=1.0, name="2"),
    Key(index=24, x=3.0,   y=0.0, w=1.0,  h=1.0, name="3"),
    Key(index=25, x=4.0,   y=0.0, w=1.0,  h=1.0, name="4"),
    Key(index=26, x=5.0,   y=0.0, w=1.0,  h=1.0, name="5"),
    Key(index=27, x=6.0,   y=0.0, w=1.0,  h=1.0, name="6"),
    Key(index=28, x=7.0,   y=0.0, w=1.0,  h=1.0, name="7"),
    Key(index=29, x=8.0,   y=0.0, w=1.0,  h=1.0, name="8"),
    Key(index=30, x=9.0,   y=0.0, w=1.0,  h=1.0, name="9"),
    Key(index=31, x=10.0,  y=0.0, w=1.0,  h=1.0, name="0"),
    Key(index=32, x=11.0,  y=0.0, w=1.0,  h=1.0, name="-"),
    Key(index=33, x=12.0,  y=0.0, w=1.0,  h=1.0, name="="),
    Key(index=34, x=13.0,  y=0.0, w=2.0,  h=1.0, name="←"),

    # Row 1 - QWERTY (y=1)
    Key(index=42, x=0.0,   y=1.0, w=1.5,  h=1.0, name="Tab"),
    Key(index=43, x=1.5,   y=1.0, w=1.0,  h=1.0, name="Q"),
    Key(index=44, x=2.5,   y=1.0, w=1.0,  h=1.0, name="W"),
    Key(index=45, x=3.5,   y=1.0, w=1.0,  h=1.0, name="E"),
    Key(index=46, x=4.5,   y=1.0, w=1.0,  h=1.0, name="R"),
    Key(index=47, x=5.5,   y=1.0, w=1.0,  h=1.0, name="T"),
    Key(index=48, x=6.5,   y=1.0, w=1.0,  h=1.0, name="Y"),
    Key(index=49, x=7.5,   y=1.0, w=1.0,  h=1.0, name="U"),
    Key(index=50, x=8.5,   y=1.0, w=1.0,  h=1.0, name="I"),
    Key(index=51, x=9.5,   y=1.0, w=1.0,  h=1.0, name="O"),
    Key(index=52, x=10.5,  y=1.0, w=1.0,  h=1.0, name="P"),
    Key(index=53, x=11.5,  y=1.0, w=1.0,  h=1.0, name="["),
    Key(index=54, x=12.5,  y=1.0, w=1.0,  h=1.0, name="]"),
    Key(index=55, x=13.5,  y=1.0, w=1.5,  h=1.0, name="\\"),

    # Row 2 - Home row (y=2)
    Key(index=63, x=0.0,   y=2.0, w=1.75, h=1.0, name="Caps"),
    Key(index=64, x=1.75,  y=2.0, w=1.0,  h=1.0, name="A"),
    Key(index=65, x=2.75,  y=2.0, w=1.0,  h=1.0, name="S"),
    Key(index=66, x=3.75,  y=2.0, w=1.0,  h=1.0, name="D"),
    Key(index=67, x=4.75,  y=2.0, w=1.0,  h=1.0, name="F"),
    Key(index=68, x=5.75,  y=2.0, w=1.0,  h=1.0, name="G"),
    Key(index=69, x=6.75,  y=2.0, w=1.0,  h=1.0, name="H"),
    Key(index=70, x=7.75,  y=2.0, w=1.0,  h=1.0, name="J"),
    Key(index=71, x=8.75,  y=2.0, w=1.0,  h=1.0, name="K"),
    Key(index=72, x=9.75,  y=2.0, w=1.0,  h=1.0, name="L"),
    Key(index=73, x=10.75, y=2.0, w=1.0,  h=1.0, name=";"),
    Key(index=74, x=11.75, y=2.0, w=1.0,  h=1.0, name="'"),
    Key(index=76, x=12.75, y=2.0, w=2.25, h=1.0, name="Enter"),

    # Row 3 - Shift row (y=3)
    Key(index=84, x=0.0,   y=3.0, w=2.25, h=1.0, name="Shift"),
    Key(index=86, x=2.25,  y=3.0, w=1.0,  h=1.0, name="Z"),
    Key(index=87, x=3.25,  y=3.0, w=1.0,  h=1.0, name="X"),
    Key(index=88, x=4.25,  y=3.0, w=1.0,  h=1.0, name="C"),
    Key(index=89, x=5.25,  y=3.0, w=1.0,  h=1.0, name="V"),
    Key(index=90, x=6.25,  y=3.0, w=1.0,  h=1.0, name="B"),
    Key(index=91, x=7.25,  y=3.0, w=1.0,  h=1.0, name="N"),
    Key(index=92, x=8.25,  y=3.0, w=1.0,  h=1.0, name="M"),
    Key(index=93, x=9.25,  y=3.0, w=1.0,  h=1.0, name="<"),
    Key(index=94, x=10.25, y=3.0, w=1.0,  h=1.0, name=">"),
    Key(index=95, x=11.25, y=3.0, w=1.0,  h=1.0, name="?"),
    Key(index=97, x=12.25, y=3.0, w=2.75, h=1.0, name="Shift"),

    # Row 4 - Bottom row (y=4)
    Key(index=105, x=0.0,   y=4.0, w=1.25, h=1.0, name="Ctrl"),
    Key(index=106, x=1.25,  y=4.0, w=1.25, h=1.0, name="Win"),
    Key(index=107, x=2.5,   y=4.0, w=1.25, h=1.0, name="Alt"),
    Key(index=111, x=3.75,  y=4.0, w=6.25, h=1.0, name="Space"),
    Key(index=115, x=10.0,  y=4.0, w=1.25, h=1.0, name="Alt"),
    Key(index=116, x=11.25, y=4.0, w=1.0,  h=1.0, name="Menu"),
    Key(index=117, x=12.25, y=4.0, w=1.25, h=1.0, name="Ctrl"),
    Key(index=118, x=13.5,  y=4.0, w=1.5,  h=1.0, name="Fn"),
]

MAX_KEY_INDEX: int = max(k.index for k in KEYBOARD_LAYOUT)
KEY_COUNT: int = MAX_KEY_INDEX + 1
KB_WIDTH: float = 15.0   # ~15 standard key-widths
KB_HEIGHT: float = 5.0   # 5 rows
