"""
Categories and pattern organization for MK1300 V2.

Ported from https://github.com/kickTROLL/mk1300v2_RGB (Apache-2.0)
Original work Copyright 2024 Yash (kickTROLL)
Modified: JS to Python port for mk1300-linux
"""

from dataclasses import dataclass
from typing import Dict, List
from .effects import PATTERNS, Pattern
from .extra_effects import EXTRA_PATTERNS


@dataclass(frozen=True)
class Category:
    id: str
    label: str
    icon: str


CATEGORIES: List[Category] = [
    Category(id="all", label="ALL", icon="◈"),
    Category(id="gradient", label="GRADIENT", icon="🌈"),
    Category(id="neon", label="NEON/CYBER", icon="💜"),
    Category(id="heat", label="FIRE/HEAT", icon="🔥"),
    Category(id="ice", label="ICE/CRYO", icon="❄️"),
    Category(id="dark", label="DARK", icon="🌑"),
    Category(id="pastel", label="PASTEL", icon="🌸"),
    Category(id="metallic", label="METALLIC", icon="🏆"),
    Category(id="contrasty", label="CONTRASTY", icon="⚡"),
]

PATTERN_CAT: Dict[str, str] = {
    # ── Original 90 patterns ──
    "sunset": "gradient",
    "northern": "gradient",
    "ocean": "gradient",
    "vaporwave": "gradient",
    "forest": "gradient",
    "synthwave": "gradient",
    "caribbean": "gradient",
    "golden": "gradient",
    "frost": "gradient",
    "aurora": "gradient",
    "coral": "gradient",
    "frozen": "gradient",
    "retrograde": "gradient",
    "sundown": "gradient",
    "purplehaze": "gradient",
    "deepindigo": "gradient",
    "trizone": "gradient",
    "candy": "gradient",
    "seafoam": "gradient",
    "mintfresh": "gradient",
    "jade": "gradient",
    "candystripes": "gradient",
    "flamtips": "heat",

    "cyberpunk": "neon",
    "matrix": "neon",
    "storm": "neon",
    "neonsign": "neon",
    "holo": "neon",
    "uv": "neon",
    "neonblue": "neon",
    "neonmint": "neon",
    "toxic": "neon",
    "radioact": "neon",
    "lime": "neon",
    "cyberdeck": "neon",
    "blueprint": "neon",
    "spectral": "neon",
    "ir_atomic": "neon",

    "ember": "heat",
    "blood": "heat",
    "ir_left": "heat",
    "ir_vert": "heat",
    "ir_solar": "heat",
    "ir_corner": "heat",
    "ir_dual": "heat",
    "lava": "heat",
    "hearth": "heat",
    "volcanic": "heat",
    "magmachamber": "heat",
    "candyapple": "heat",

    "arctic": "ice",
    "deepspace": "ice",
    "ir_cold": "ice",
    "ir_coldwave": "ice",
    "ir_teal": "ice",
    "ir_plasma": "ice",
    "deepteal": "ice",
    "denim": "ice",
    "stormcloud": "ice",
    "aquadream": "ice",
    "peacock": "ice",
    "frozenOcean": "ice",

    "dracula": "dark",
    "noir": "dark",
    "obsidian": "dark",
    "nightsky2": "dark",
    "carbon": "dark",
    "highcontrast": "dark",
    "deepwine": "dark",
    "galaxy": "dark",
    "nordic": "dark",
    "solarized": "dark",
    "wasd": "dark",
    "blueprnt": "dark",

    "cherry": "pastel",
    "pastel": "pastel",
    "cotton": "pastel",
    "peachfuzz": "pastel",
    "silver": "pastel",
    "lavender": "pastel",
    "orchid": "pastel",
    "titanium": "pastel",
    "sakura": "pastel",
    "hotpink": "pastel",
    "sandstone": "pastel",
    "homerow": "pastel",

    "rosegold": "metallic",
    "amethyst": "metallic",
    "moltengold": "metallic",
    "copper": "metallic",
    "bronzeage": "metallic",
    "coppergold": "metallic",

    # ── Extra contrasty patterns ──
    "checkerboard": "contrasty",
    "cyberstripes": "contrasty",
    "yinyang": "contrasty",
    "typeglow": "contrasty",
    "rowneon": "contrasty",
    "bullseye": "contrasty",
    "policelight": "contrasty",
    "phantom": "dark",
    "binary": "contrasty",
    "rave": "contrasty",
    "disco": "contrasty",
    "vampire": "heat",
    "stainedglass": "contrasty",
    "lasergrid": "neon",
    "diagstripes": "contrasty",
    "flamerow": "heat",
    "voidportal": "dark",
    "sunrisefire": "heat",
    "neobluprint": "neon",
    "cherrybomb": "heat",
    "toxicrain": "neon",
    "pinstripe": "contrasty",
    "glitch": "dark",
    "heatzone": "heat",
    "icespike": "ice",
    "acidwash": "neon",
    "neontetris": "contrasty",
    "camo": "dark",
    "deepmagma": "heat",
    "frozentundra": "ice",
    "rowcheck": "contrasty",
    "neoncross": "neon",
    "horror": "dark",
    "neonstrip2": "contrasty",
    "goldrush": "metallic",
    "rainbowdiag": "contrasty",
    "acidcheck": "contrasty",
    "spotlightesc": "dark",
    "neonrowalt": "contrasty",
    "emberwaves": "heat",
    "neonblocks": "contrasty",
    "uwistripe": "contrasty",
    "midnightfire": "heat",
    "lavacheck": "heat",
    "frostbite": "ice",
    "hotspots": "heat",
    "pixelflag": "contrasty",
    "spectrumcross": "contrasty",
    "deepcherry": "pastel",
    "elecfence": "contrasty",
}


def get_category(pattern_id: str) -> str:
    """Return category ID for a given pattern ID."""
    return PATTERN_CAT.get(pattern_id, "gradient")


ALL_PATTERNS: List[Pattern] = PATTERNS + EXTRA_PATTERNS
ALL_PATTERNS_BY_ID: Dict[str, Pattern] = {p.id: p for p in ALL_PATTERNS}
