"""
90 Static RGB Patterns for Ant Esports MK1300 V2 60% keyboard.

Ported from https://github.com/kickTROLL/mk1300v2_RGB (Apache-2.0)
Original work Copyright 2024 Yash (kickTROLL)
Modified: JS to Python port for mk1300-linux
"""

import math
from dataclasses import dataclass
from typing import Callable, Dict, List, Tuple
from .layout import KEYBOARD_LAYOUT, KB_WIDTH, KB_HEIGHT, Key


@dataclass(frozen=True)
class RGBColor:
    r: int
    g: int
    b: int

    def to_dict(self) -> Dict[str, int]:
        return {"r": self.r, "g": self.g, "b": self.b}

    def to_tuple(self) -> Tuple[int, int, int]:
        return (self.r, self.g, self.b)

    def to_hex(self) -> str:
        return f"#{self.r:02x}{self.g:02x}{self.b:02x}"


@dataclass(frozen=True)
class Pattern:
    id: str
    name: str
    icon: str
    fn: Callable[[List[Key]], List[RGBColor]]


def js_round(x: float) -> int:
    """Emulate JavaScript Math.round (half rounds towards +infinity)."""
    return math.floor(x + 0.5)


def hsl(h: float, s: float, l: float) -> RGBColor:
    """Convert HSL color to RGB, matching reference effects.js implementation."""
    h = ((h % 360) + 360) % 360
    s = max(0.0, min(1.0, s))
    l = max(0.0, min(1.0, l))
    c = (1.0 - abs(2.0 * l - 1.0)) * s
    x = c * (1.0 - abs(((h / 60.0) % 2.0) - 1.0))
    m = l - c / 2.0

    if h < 60:
        r, g, b = c, x, 0.0
    elif h < 120:
        r, g, b = x, c, 0.0
    elif h < 180:
        r, g, b = 0.0, c, x
    elif h < 240:
        r, g, b = 0.0, x, c
    elif h < 300:
        r, g, b = x, 0.0, c
    else:
        r, g, b = c, 0.0, x

    return RGBColor(
        r=js_round((r + m) * 255.0),
        g=js_round((g + m) * 255.0),
        b=js_round((b + m) * 255.0),
    )


def rgb(r: int, g: int, b: int) -> RGBColor:
    return RGBColor(r=r, g=g, b=b)


OFF = RGBColor(0, 0, 0)


def nx(k: Key) -> float:
    """Normalised key centre X (0-1 range)."""
    return (k.x + k.w / 2.0) / KB_WIDTH


def ny(k: Key) -> float:
    """Normalised key centre Y (0-1 range)."""
    return (k.y + k.h / 2.0) / KB_HEIGHT


def row(k: Key) -> int:
    """Row of key (0-4)."""
    return js_round(k.y)


def zone(k: Key) -> str:
    """Classify key zone: 'mod', 'num', or 'alpha'."""
    n = k.name
    if n in ("Esc", "Tab", "Caps", "Shift", "Ctrl", "Win", "Alt", "Menu", "Fn", "←", "Enter", "Space"):
        return "mod"
    if n in ("1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "-", "="):
        return "num"
    return "alpha"


def heatColor(heat: float, scale: str) -> RGBColor:
    """Helper: map a 0-1 heat value to a colour on a given scale."""
    heat = max(0.0, min(1.0, heat))
    if scale == "ir":
        # Classic infrared: black -> red -> orange -> yellow -> white
        if heat < 0.25:
            return hsl(0, 1, heat * 2)
        if heat < 0.55:
            return hsl(0 + (heat - 0.25) * 100, 1, 0.50)
        if heat < 0.80:
            return hsl(30 + (heat - 0.55) * 120, 1, 0.55)
        return hsl(60, 1, 0.55 + (heat - 0.80) * 2.25)
    if scale == "cryo":
        # Cryo: black -> deep blue -> cyan -> white
        if heat < 0.30:
            return hsl(240, 1, heat * 1.5)
        if heat < 0.65:
            return hsl(200, 1, 0.35 + (heat - 0.30) * 0.6)
        return hsl(200, 0.30 - (heat - 0.65) * 0.9, 0.75 + (heat - 0.65) * 0.7)
    if scale == "teal":
        # Teal thermal: black -> teal -> green -> white
        if heat < 0.35:
            return hsl(170, 1, heat * 1.4)
        if heat < 0.70:
            return hsl(140, 1, 0.38 + (heat - 0.35) * 0.5)
        return hsl(100, 0.6, 0.62 + (heat - 0.70) * 1.2)
    if scale == "plasma":
        # Plasma: black -> violet -> magenta -> white
        if heat < 0.30:
            return hsl(270, 1, heat * 1.6)
        if heat < 0.65:
            return hsl(300, 1, 0.38 + (heat - 0.30) * 0.5)
        return hsl(320, 0.40, 0.62 + (heat - 0.65) * 1.1)
    return hsl(0, 0, heat)


# ── Original 20 Patterns ──────────────────────────────────────────────────────

# 1. Sunset Dusk
def sunsetDusk(keys: List[Key]) -> List[RGBColor]:
    return [hsl(0.0 + nx(k) * 50.0, 1.0, 0.48) for k in keys]

# 2. Northern Lights
def northernLights(keys: List[Key]) -> List[RGBColor]:
    return [hsl(260.0 - ny(k) * 80.0, 1.0, 0.45 + ny(k) * 0.05) for k in keys]

# 3. Cyberpunk
def cyberpunk(keys: List[Key]) -> List[RGBColor]:
    res = []
    for k in keys:
        z = zone(k)
        if z == "mod":
            res.append(hsl(300, 1, 0.50))
        elif z == "num":
            res.append(hsl(55, 1, 0.50))
        else:
            res.append(hsl(186, 1, 0.50))
    return res

# 4. Ocean Deep
def oceanDeep(keys: List[Key]) -> List[RGBColor]:
    return [hsl(200.0 + (1.0 - ny(k)) * 20.0, 1.0, 0.12 + (1.0 - ny(k)) * 0.42) for k in keys]

# 5. Rose Gold
def roseGold(keys: List[Key]) -> List[RGBColor]:
    return [hsl(340.0 - nx(k) * 20.0, 0.80, 0.44 + nx(k) * 0.08) for k in keys]

# 6. Dracula
def dracula(keys: List[Key]) -> List[RGBColor]:
    res = []
    for k in keys:
        if k.name in ("Enter", "Esc"):
            res.append(hsl(135, 1, 0.45))
        elif zone(k) == "mod":
            res.append(hsl(326, 1, 0.62))
        else:
            res.append(hsl(265.0 + nx(k) * 15.0, 0.60, 0.38))
    return res

# 7. Arctic Ice
def arcticIce(keys: List[Key]) -> List[RGBColor]:
    res = []
    for k in keys:
        cx = abs(nx(k) - 0.5) * 2.0
        h = 200.0
        l = 0.85 - cx * 0.40
        s = 0.30 + cx * 0.70
        res.append(hsl(h, s, l))
    return res

# 8. Ember
def ember(keys: List[Key]) -> List[RGBColor]:
    res = []
    for k in keys:
        if zone(k) == "mod":
            res.append(hsl(30, 1, 0.50))
        else:
            res.append(hsl(0.0 + nx(k) * 15.0, 0.95, 0.40))
    return res

# 9. Matrix Green
def matrixGreen(keys: List[Key]) -> List[RGBColor]:
    res = []
    for k in keys:
        t = nx(k)
        l = 0.25 + abs(math.sin(t * 12.0)) * 0.30
        res.append(hsl(120.0 + t * 20.0, 1.0, l))
    return res

# 10. Pastel Rainbow
def pastelRainbow(keys: List[Key]) -> List[RGBColor]:
    return [hsl((nx(k) * 300.0) % 360.0, 0.70, 0.68) for k in keys]

# 11. Royal Amethyst
def royalAmethyst(keys: List[Key]) -> List[RGBColor]:
    res = []
    for k in keys:
        if zone(k) == "mod":
            res.append(hsl(45, 1, 0.52))
        else:
            res.append(hsl(270.0 - nx(k) * 20.0, 0.75, 0.40))
    return res

# 12. Monochrome Silver
def monochromesilver(keys: List[Key]) -> List[RGBColor]:
    return [hsl(210.0, 0.15, 0.90 - ny(k) * 0.35) for k in keys]

# 13. WASD Gaming
WASD_IDX = {44, 64, 65, 66}
def wasdGaming(keys: List[Key]) -> List[RGBColor]:
    res = []
    for k in keys:
        if k.index in WASD_IDX:
            res.append(hsl(186, 1, 0.55))
        elif k.name == "Space":
            res.append(hsl(186, 0.6, 0.30))
        else:
            res.append(hsl(220.0, 0.50, 0.08 + ny(k) * 0.05))
    return res

# 14. Cherry Blossom
def cherryBlossom(keys: List[Key]) -> List[RGBColor]:
    res = []
    for k in keys:
        t = nx(k)
        h = 340.0 + math.sin(t * math.pi) * 10.0
        l = 0.70 + math.cos(ny(k) * math.pi * 0.5) * 0.10
        res.append(hsl(h, 0.75, l))
    return res

# 15. Neon Noir
NOIR_ACCENTS = {21, 34, 76, 84, 97, 111}
def neonNoir(keys: List[Key]) -> List[RGBColor]:
    res = []
    for k in keys:
        if k.index in NOIR_ACCENTS:
            res.append(hsl(300, 1, 0.55))
        elif zone(k) == "alpha":
            res.append(hsl(220, 0.40, 0.08))
        else:
            res.append(OFF)
    return res

# 16. Blood Moon
def bloodMoon(keys: List[Key]) -> List[RGBColor]:
    res = []
    for k in keys:
        t = ny(k)
        h = 5.0 - t * 5.0
        l = 0.48 - t * 0.36
        res.append(hsl(h, 1.0, max(0.04, l)))
    return res

# 17. Vaporwave
def vaporwave(keys: List[Key]) -> List[RGBColor]:
    return [hsl(310.0 - (nx(k) * 0.5 + ny(k) * 0.5) * 60.0, 0.85, 0.55) for k in keys]

# 18. Forest Depth
def forestDepth(keys: List[Key]) -> List[RGBColor]:
    return [hsl(95.0 - ny(k) * 20.0, 0.80, max(0.15, 0.48 - ny(k) * 0.22)) for k in keys]

# 19. Home Row Hero
HOMEROW = {64, 65, 66, 67, 68, 69, 70, 71, 72, 73}
def homeRowHero(keys: List[Key]) -> List[RGBColor]:
    res = []
    for k in keys:
        if k.index in HOMEROW:
            res.append(hsl(45, 1, 0.55))
        elif k.index == 111:
            res.append(hsl(45, 0.5, 0.20))
        else:
            res.append(hsl(220, 0.30, 0.06))
    return res

# 20. Synthwave
def synthwave(keys: List[Key]) -> List[RGBColor]:
    res = []
    for k in keys:
        t = ny(k)
        if t < 0.3:
            h = 200.0
        elif t < 0.6:
            h = 270.0
        else:
            h = 330.0
        l = 0.42 + (1.0 - t) * 0.08
        res.append(hsl(h, 1.0, l))
    return res


# ── New 30 Patterns ───────────────────────────────────────────────────────────

# 21. Galaxy
def galaxy(keys: List[Key]) -> List[RGBColor]:
    res = []
    for i, k in enumerate(keys):
        star = abs(math.sin(i * 127.1 + k.index * 73.5)) > 0.82
        if star:
            res.append(hsl(220, 0.20, 0.92))
        else:
            t = nx(k) * 0.4 + ny(k) * 0.6
            res.append(hsl(260.0 + t * 30.0, 0.55, 0.08 + t * 0.06))
    return res

# 22. Lava
def lava(keys: List[Key]) -> List[RGBColor]:
    res = []
    for k in keys:
        wave = math.sin(nx(k) * 8.0) * 0.5 + math.cos(ny(k) * 5.0) * 0.5
        t = (wave + 1.0) / 2.0
        h = t * 35.0
        l = 0.15 + t * 0.38
        res.append(hsl(h, 1.0, l))
    return res

# 23. Peacock
def peacock(keys: List[Key]) -> List[RGBColor]:
    res = []
    for k in keys:
        if zone(k) == "mod":
            res.append(hsl(220, 1, 0.50))
        else:
            t = nx(k)
            res.append(hsl(165.0 + t * 25.0, 1.0, 0.38 + t * 0.08))
    return res

# 24. Toxic
def toxic(keys: List[Key]) -> List[RGBColor]:
    res = []
    for k in keys:
        t = nx(k)
        l = 0.30 + abs(math.sin(t * 6.0 + ny(k) * 4.0)) * 0.22
        res.append(hsl(80.0 + t * 20.0, 1.0, l))
    return res

# 25. Cotton Candy
def cottonCandy(keys: List[Key]) -> List[RGBColor]:
    res = []
    for k in keys:
        col = math.floor(k.x + k.w / 2.0)
        res.append(hsl(340, 0.80, 0.75) if col % 2 == 0 else hsl(200, 0.70, 0.72))
    return res

# 26. Deep Space
SPACE_ACCENTS = {21, 76, 111, 84, 97}
def deepSpace(keys: List[Key]) -> List[RGBColor]:
    res = []
    for k in keys:
        if k.index in SPACE_ACCENTS:
            res.append(hsl(190, 1, 0.55))
        else:
            t = nx(k) * 0.3 + ny(k) * 0.7
            res.append(hsl(230.0 + t * 20.0, 0.60, 0.04 + t * 0.07))
    return res

# 27. Infrared
def infrared(keys: List[Key]) -> List[RGBColor]:
    res = []
    for k in keys:
        cx = 1.0 - abs(nx(k) - 0.5) * 2.0
        cy = 1.0 - abs(ny(k) - 0.5) * 2.0
        heat = (cx + cy) / 2.0
        if heat > 0.75:
            res.append(hsl(60, 1, 0.90))
        elif heat > 0.50:
            res.append(hsl(30, 1, 0.55))
        else:
            res.append(hsl(0, 1, heat * 0.50))
    return res

# 28. Electric Storm
LIGHTNING = {21, 22, 34, 42, 63, 84, 97, 111, 76}
def electricStorm(keys: List[Key]) -> List[RGBColor]:
    res = []
    for k in keys:
        if k.index in LIGHTNING:
            res.append(hsl(55, 1, 0.70))
        elif zone(k) == "alpha":
            res.append(hsl(240, 0.40, 0.07))
        else:
            res.append(hsl(240, 0.30, 0.04))
    return res

# 29. Jade
def jade(keys: List[Key]) -> List[RGBColor]:
    res = []
    for k in keys:
        cx = abs(nx(k) - 0.5) * 2.0
        l = 0.32 + (1.0 - cx) * 0.15
        res.append(hsl(150.0 + cx * 10.0, 0.70, l))
    return res

# 30. Copper Circuit
def copperCircuit(keys: List[Key]) -> List[RGBColor]:
    return [hsl(20.0 + nx(k) * 15.0, 0.70, 0.35 + ny(k) * 0.10) for k in keys]

# 31. Holographic
def holographic(keys: List[Key]) -> List[RGBColor]:
    return [hsl(((nx(k) * 0.6 + ny(k) * 0.4) * 360.0) % 360.0, 1.0, 0.52) for k in keys]

# 32. Ultraviolet
def ultraviolet(keys: List[Key]) -> List[RGBColor]:
    res = []
    for k in keys:
        if zone(k) == "mod":
            res.append(hsl(290, 1, 0.62))
        else:
            t = nx(k)
            res.append(hsl(270.0 + t * 10.0, 0.80, 0.22))
    return res

# 33. Caribbean
def caribbean(keys: List[Key]) -> List[RGBColor]:
    res = []
    for k in keys:
        t = nx(k)
        h = 180.0 - t * 160.0
        l = 0.50 - abs(t - 0.5) * 0.05
        res.append(hsl(h, 0.90, l))
    return res

# 34. Neon Sign
def neonSign(keys: List[Key]) -> List[RGBColor]:
    rowColors = [
        hsl(55, 1, 0.55),
        hsl(120, 1, 0.48),
        hsl(186, 1, 0.52),
        hsl(300, 1, 0.52),
        hsl(15, 1, 0.55),
    ]
    return [rowColors[js_round(k.y)] if 0 <= js_round(k.y) < len(rowColors) else rowColors[0] for k in keys]

# 35. Obsidian
def obsidian(keys: List[Key]) -> List[RGBColor]:
    res = []
    for k in keys:
        t = nx(k)
        l = 0.06 + abs(math.sin(t * 9.0 + ny(k) * 5.0)) * 0.08
        res.append(hsl(10, 0.70, l))
    return res

# 36. Golden Hour
def goldenHour(keys: List[Key]) -> List[RGBColor]:
    return [hsl(50.0 - nx(k) * 30.0, 1.0, 0.50 - nx(k) * 0.05) for k in keys]

# 37. Winter Frost
def winterFrost(keys: List[Key]) -> List[RGBColor]:
    return [hsl(205.0, 0.55, 0.88 - ny(k) * 0.30) for k in keys]

# 38. Aurora
def aurora(keys: List[Key]) -> List[RGBColor]:
    res = []
    for k in keys:
        wave = math.sin(nx(k) * math.pi * 3.0) * 0.5 + 0.5
        h = 140.0 + wave * 140.0
        l = 0.38 + wave * 0.12
        res.append(hsl(h, 1.0, l))
    return res

# 39. Warm Hearth
def warmHearth(keys: List[Key]) -> List[RGBColor]:
    res = []
    for k in keys:
        cx = abs(nx(k) - 0.5) * 2.0
        cy = abs(ny(k) - 0.5) * 2.0
        dist = math.sqrt(cx * cx + cy * cy) / math.sqrt(2.0)
        h = 45.0 - dist * 30.0
        l = 0.60 - dist * 0.42
        res.append(hsl(h, 1.0, max(0.05, l)))
    return res

# 40. Deep Teal
def deepTeal(keys: List[Key]) -> List[RGBColor]:
    return [hsl(185.0, 1.0, 0.14 + (1.0 - ny(k)) * 0.18) for k in keys]

# 41. Hot Pink
def hotPink(keys: List[Key]) -> List[RGBColor]:
    return [hsl(320.0 + (nx(k) * 0.5 + ny(k) * 0.5) * 20.0, 1.0, 0.50 - (nx(k) * 0.5 + ny(k) * 0.5) * 0.10) for k in keys]

# 42. Lime Punch
def limePunch(keys: List[Key]) -> List[RGBColor]:
    res = []
    for k in keys:
        z = zone(k)
        if z == "mod":
            res.append(hsl(80, 1, 0.52))
        elif z == "num":
            res.append(hsl(95, 0.90, 0.42))
        else:
            res.append(hsl(100, 0.55, 0.22))
    return res

# 43. Midnight Sakura
def midnightSakura(keys: List[Key]) -> List[RGBColor]:
    res = []
    for k in keys:
        z = zone(k)
        if z == "alpha":
            res.append(hsl(340, 0.75, 0.55))
        elif z == "num":
            res.append(hsl(340, 0.40, 0.25))
        else:
            res.append(hsl(270, 0.30, 0.06))
    return res

# 44. Titanium
def titanium(keys: List[Key]) -> List[RGBColor]:
    return [hsl(215.0, 0.20, 0.55 - (nx(k) * 0.4 + ny(k) * 0.6) * 0.20) for k in keys]

# 45. Molten Gold
def moltenGold(keys: List[Key]) -> List[RGBColor]:
    res = []
    for k in keys:
        cy = abs(ny(k) - 0.5) * 2.0
        h = 44.0 - cy * 15.0
        l = 0.52 - cy * 0.22
        res.append(hsl(h, 1.0, max(0.15, l)))
    return res

# 46. Coral Reef
def coralReef(keys: List[Key]) -> List[RGBColor]:
    return [hsl(15.0 + ny(k) * 190.0, 0.90, max(0.15, 0.55 - ny(k) * 0.25)) for k in keys]

# 47. Candy Stripes
def candyStripes(keys: List[Key]) -> List[RGBColor]:
    res = []
    for k in keys:
        col = math.floor(k.x + k.w / 2.0)
        stripe = col % 3
        if stripe == 0:
            res.append(hsl(0, 0.90, 0.55))
        elif stripe == 1:
            res.append(hsl(210, 0.80, 0.60))
        else:
            res.append(hsl(0, 0, 0.90))
    return res

# 48. Frozen Ocean
def frozenOcean(keys: List[Key]) -> List[RGBColor]:
    return [hsl(210.0, 0.80 - nx(k) * 0.50, 0.15 + nx(k) * 0.70) for k in keys]

# 49. Volcanic Ash
def volcanicAsh(keys: List[Key]) -> List[RGBColor]:
    res = []
    for k in keys:
        if zone(k) == "mod":
            res.append(hsl(25, 1, 0.48))
        else:
            t = nx(k) * ny(k)
            res.append(hsl(20, 0.15, 0.12 + t * 0.08))
    return res

# 50. Retrograde
def retrograde(keys: List[Key]) -> List[RGBColor]:
    return [hsl((1.0 - nx(k)) * 270.0, 0.65, 0.62) for k in keys]


# ── 10 Infrared-style Radial Patterns ─────────────────────────────────────────

# 51. Heat Source Left
def irLeft(keys: List[Key]) -> List[RGBColor]:
    return [heatColor(1.0 - nx(k), "ir") for k in keys]

# 52. Cryo Core
def cryoCore(keys: List[Key]) -> List[RGBColor]:
    res = []
    for k in keys:
        cx = abs(nx(k) - 0.5) * 2.0
        cy = abs(ny(k) - 0.5) * 2.0
        heat = math.sqrt(cx * cx + cy * cy) / math.sqrt(2.0)
        res.append(heatColor(heat * 0.9, "cryo"))
    return res

# 53. Thermal Teal
def thermalTeal(keys: List[Key]) -> List[RGBColor]:
    res = []
    for k in keys:
        cx = 1.0 - abs(nx(k) - 0.5) * 2.0
        cy = 1.0 - abs(ny(k) - 0.5) * 2.0
        res.append(heatColor((cx + cy) / 2.0, "teal"))
    return res

# 54. Dual Heat
def dualHeat(keys: List[Key]) -> List[RGBColor]:
    res = []
    for k in keys:
        d1 = math.sqrt(nx(k) ** 2 + ny(k) ** 2) / math.sqrt(2.0)
        d2 = math.sqrt((1.0 - nx(k)) ** 2 + (1.0 - ny(k)) ** 2) / math.sqrt(2.0)
        heat = 1.0 - min(d1, d2)
        res.append(heatColor(heat * 0.95, "ir"))
    return res

# 55. Vertical Burn
def verticalBurn(keys: List[Key]) -> List[RGBColor]:
    return [heatColor(1.0 - ny(k), "ir") for k in keys]

# 56. Solar Core
def solarCore(keys: List[Key]) -> List[RGBColor]:
    res = []
    for k in keys:
        cx = 1.0 - abs(nx(k) - 0.5) * 2.0
        cy = 1.0 - abs(ny(k) - 0.5) * 2.0
        heat = ((cx + cy) / 2.0) ** 0.6
        res.append(heatColor(heat, "ir"))
    return res

# 57. Plasma Radial
def plasmaRadial(keys: List[Key]) -> List[RGBColor]:
    res = []
    for k in keys:
        cx = 1.0 - abs(nx(k) - 0.5) * 2.0
        cy = 1.0 - abs(ny(k) - 0.5) * 2.0
        res.append(heatColor((cx + cy) / 2.0 * 0.98, "plasma"))
    return res

# 58. Corner Blaze
def cornerBlaze(keys: List[Key]) -> List[RGBColor]:
    res = []
    for k in keys:
        d = math.sqrt(nx(k) ** 2 + ny(k) ** 2) / math.sqrt(2.0)
        res.append(heatColor(1.0 - d, "ir"))
    return res

# 59. Cold Wave
def coldWave(keys: List[Key]) -> List[RGBColor]:
    return [heatColor(nx(k), "cryo") for k in keys]

# 60. Atomic Glow
def atomicGlow(keys: List[Key]) -> List[RGBColor]:
    res = []
    for k in keys:
        cx = 1.0 - abs(nx(k) - 0.5) * 2.0
        cy = 1.0 - abs(ny(k) - 0.5) * 2.0
        res.append(heatColor((cx + cy) / 2.0, "teal"))
    return res


# ── 30 More Patterns ──────────────────────────────────────────────────────────

# 61. Tri-Zone
def triZone(keys: List[Key]) -> List[RGBColor]:
    res = []
    for k in keys:
        t = nx(k)
        if t < 0.33:
            res.append(hsl(200, 1, 0.50))
        elif t < 0.66:
            res.append(hsl(270, 1, 0.50))
        else:
            res.append(hsl(340, 1, 0.52))
    return res

# 62. Flame Tips
def flameTips(keys: List[Key]) -> List[RGBColor]:
    return [hsl(20.0 + ny(k) * 15.0, 1.0, 0.08 + ny(k) * 0.45) for k in keys]

# 63. Nordic
def nordic(keys: List[Key]) -> List[RGBColor]:
    res = []
    for k in keys:
        if zone(k) == "mod":
            res.append(hsl(42, 0.90, 0.50))
        else:
            res.append(hsl(210, 0.60, 0.15 + ny(k) * 0.08))
    return res

# 64. Peach Fuzz
def peachFuzz(keys: List[Key]) -> List[RGBColor]:
    return [hsl(22.0 + (nx(k) * 0.3 + ny(k) * 0.7) * 10.0, 0.85, 0.62 - (nx(k) * 0.3 + ny(k) * 0.7) * 0.10) for k in keys]

# 65. Radioactive
def radioactive(keys: List[Key]) -> List[RGBColor]:
    res = []
    for k in keys:
        cx = 1.0 - abs(nx(k) - 0.5) * 2.0
        cy = 1.0 - abs(ny(k) - 0.5) * 2.0
        heat = (cx + cy) / 2.0
        res.append(hsl(100.0 + heat * 20.0, 1.0, 0.04 + heat * 0.50))
    return res

# 66. Spectral
def spectral(keys: List[Key]) -> List[RGBColor]:
    n = len(keys)
    return [hsl((i / n) * 360.0, 0.90, 0.50) for i, k in enumerate(keys)]

# 67. Denim Blue
def denimBlue(keys: List[Key]) -> List[RGBColor]:
    return [hsl(215.0, 0.65, 0.32 - ny(k) * 0.12) for k in keys]

# 68. Bronze Age
def bronzeAge(keys: List[Key]) -> List[RGBColor]:
    return [hsl(30.0 + (nx(k) * 0.5 + ny(k) * 0.5) * 10.0, 0.65, 0.30 + (nx(k) * 0.5 + ny(k) * 0.5) * 0.12) for k in keys]

# 69. Purple Haze
def purpleHaze(keys: List[Key]) -> List[RGBColor]:
    return [hsl(280.0 - nx(k) * 30.0, 0.70, 0.40 + nx(k) * 0.08) for k in keys]

# 70. Night Sky
STARS = {22, 29, 45, 50, 65, 71, 88, 92, 106}
def nightSky(keys: List[Key]) -> List[RGBColor]:
    res = []
    for k in keys:
        if k.index in STARS:
            res.append(hsl(220, 0.15, 0.92))
        else:
            res.append(hsl(240, 0.40, 0.04 + ny(k) * 0.03))
    return res

# 71. High Contrast
def highContrast(keys: List[Key]) -> List[RGBColor]:
    res = []
    for k in keys:
        r = js_round(k.y)
        res.append(hsl(210, 0.10, 0.92) if r % 2 == 0 else hsl(225, 0.60, 0.14))
    return res

# 72. Blueprint
def blueprint(keys: List[Key]) -> List[RGBColor]:
    res = []
    for k in keys:
        if zone(k) == "mod":
            res.append(hsl(210, 1, 0.60))
        else:
            res.append(hsl(220, 0.80, 0.12))
    return res

# 73. Mint Fresh
def mintFresh(keys: List[Key]) -> List[RGBColor]:
    res = []
    for k in keys:
        t = ny(k)
        h = 155.0
        l = 0.52 + t * 0.32
        s = 0.75 - t * 0.55
        res.append(hsl(h, s, l))
    return res

# 74. Cyberdeck
def cyberdeck(keys: List[Key]) -> List[RGBColor]:
    res = []
    for k in keys:
        r = js_round(k.y)
        if r == 0:
            res.append(hsl(186, 1, 0.55))
        elif r == 4:
            res.append(hsl(25, 1, 0.52))
        else:
            res.append(hsl(185, 0.65, 0.18 + r * 0.02))
    return res

# 75. Deep Wine
def deepWine(keys: List[Key]) -> List[RGBColor]:
    return [hsl(340.0, 0.75, 0.22 + (nx(k) * 0.4 + ny(k) * 0.6) * 0.08) for k in keys]

# 76. Copper & Gold
def copperGold(keys: List[Key]) -> List[RGBColor]:
    res = []
    for k in keys:
        col = math.floor(k.x + k.w / 2.0)
        res.append(hsl(30, 0.80, 0.42) if col % 2 == 0 else hsl(48, 0.90, 0.52))
    return res

# 77. Seafoam
def seafoam(keys: List[Key]) -> List[RGBColor]:
    return [hsl(168.0, 0.70, 0.62 - ny(k) * 0.20) for k in keys]

# 78. Orchid
def orchid(keys: List[Key]) -> List[RGBColor]:
    return [hsl(300.0 + nx(k) * 15.0, 0.55, 0.50 + nx(k) * 0.06) for k in keys]

# 79. Neon Blue
def neonBlue(keys: List[Key]) -> List[RGBColor]:
    return [hsl(210.0, 1.0, 0.58 - ny(k) * 0.20) for k in keys]

# 80. Sandstone
def sandstone(keys: List[Key]) -> List[RGBColor]:
    return [hsl(38.0 + ny(k) * 8.0, 0.55, 0.55 - ny(k) * 0.15) for k in keys]

# 81. Lavender
def lavender(keys: List[Key]) -> List[RGBColor]:
    return [hsl(255.0, 0.60, 0.68 - ny(k) * 0.22) for k in keys]

# 82. Candy Apple
def candyApple(keys: List[Key]) -> List[RGBColor]:
    res = []
    for k in keys:
        if k.name == "Space":
            res.append(hsl(0, 0, 0.92))
        elif zone(k) == "mod":
            res.append(hsl(22, 1, 0.52))
        else:
            res.append(hsl(0, 1, 0.48))
    return res

# 83. Aqua Dream
def aquaDream(keys: List[Key]) -> List[RGBColor]:
    res = []
    for k in keys:
        if zone(k) == "mod":
            res.append(hsl(185, 1, 0.32))
        else:
            res.append(hsl(178.0 + nx(k) * 12.0, 1.0, 0.48 - nx(k) * 0.05))
    return res

# 84. Solarized
def solarized(keys: List[Key]) -> List[RGBColor]:
    res = []
    for k in keys:
        z = zone(k)
        if z == "mod":
            res.append(hsl(175, 0.80, 0.38))
        elif z == "num":
            res.append(hsl(45, 0.90, 0.52))
        else:
            res.append(hsl(205.0 + nx(k) * 10.0, 0.55, 0.28))
    return res

# 85. Magma Chamber
MAGMA_HOT = {21, 34, 76, 111, 84, 97, 105, 118}
def magmaChamber(keys: List[Key]) -> List[RGBColor]:
    res = []
    for k in keys:
        if k.index in MAGMA_HOT:
            res.append(hsl(10, 1, 0.55))
        else:
            t = nx(k) * ny(k)
            res.append(hsl(5, 0.80, 0.04 + t * 0.12))
    return res

# 86. Carbon Fiber
def carbonFiber(keys: List[Key]) -> List[RGBColor]:
    res = []
    for k in keys:
        col = math.floor(k.x + k.w / 2.0)
        l = 0.10 if col % 2 == 0 else 0.07
        res.append(hsl(220, 0.10, l))
    return res

# 87. Sundown
def sundown(keys: List[Key]) -> List[RGBColor]:
    res = []
    for k in keys:
        d = nx(k) * 0.3 + ny(k) * 0.7
        h = 20.0 + d * 240.0
        l = 0.55 - d * 0.40
        res.append(hsl(h, 1.0, max(0.08, l)))
    return res

# 88. Neon Mint
def neonMint(keys: List[Key]) -> List[RGBColor]:
    res = []
    for k in keys:
        cx = 1.0 - abs(nx(k) - 0.5) * 2.0
        res.append(hsl(155, 1, 0.30 + cx * 0.25))
    return res

# 89. Deep Indigo
def deepIndigo(keys: List[Key]) -> List[RGBColor]:
    return [hsl(245.0 + nx(k) * 10.0, 0.80, 0.20 + nx(k) * 0.08) for k in keys]

# 90. Storm Cloud
def stormCloud(keys: List[Key]) -> List[RGBColor]:
    res = []
    for k in keys:
        r = js_round(k.y)
        if r <= 1:
            res.append(hsl(220, 0.20, 0.80 - r * 0.15))
        else:
            res.append(hsl(225, 0.30, 0.12 + r * 0.02))
    return res


# ── Registry ──────────────────────────────────────────────────────────────────

PATTERNS: List[Pattern] = [
    # Original 20
    Pattern(id="sunset", name="Sunset Dusk", icon="🌅", fn=sunsetDusk),
    Pattern(id="northern", name="Northern Lights", icon="🌌", fn=northernLights),
    Pattern(id="cyberpunk", name="Cyberpunk", icon="⚡", fn=cyberpunk),
    Pattern(id="ocean", name="Ocean Deep", icon="🌊", fn=oceanDeep),
    Pattern(id="rosegold", name="Rose Gold", icon="🌸", fn=roseGold),
    Pattern(id="dracula", name="Dracula", icon="🧛", fn=dracula),
    Pattern(id="arctic", name="Arctic Ice", icon="❄️", fn=arcticIce),
    Pattern(id="ember", name="Ember", icon="🔥", fn=ember),
    Pattern(id="matrix", name="Matrix Green", icon="💚", fn=matrixGreen),
    Pattern(id="pastel", name="Pastel Rainbow", icon="🎨", fn=pastelRainbow),
    Pattern(id="amethyst", name="Royal Amethyst", icon="💜", fn=royalAmethyst),
    Pattern(id="silver", name="Monochrome Silver", icon="⚪", fn=monochromesilver),
    Pattern(id="wasd", name="WASD Gaming", icon="🎮", fn=wasdGaming),
    Pattern(id="cherry", name="Cherry Blossom", icon="🌺", fn=cherryBlossom),
    Pattern(id="noir", name="Neon Noir", icon="🖤", fn=neonNoir),
    Pattern(id="blood", name="Blood Moon", icon="🌑", fn=bloodMoon),
    Pattern(id="vaporwave", name="Vaporwave", icon="🌈", fn=vaporwave),
    Pattern(id="forest", name="Forest Depth", icon="🌿", fn=forestDepth),
    Pattern(id="homerow", name="Home Row Hero", icon="🏠", fn=homeRowHero),
    Pattern(id="synthwave", name="Synthwave", icon="🎹", fn=synthwave),

    # New 30
    Pattern(id="galaxy", name="Galaxy", icon="🌠", fn=galaxy),
    Pattern(id="lava", name="Lava", icon="🌋", fn=lava),
    Pattern(id="peacock", name="Peacock", icon="🦚", fn=peacock),
    Pattern(id="toxic", name="Toxic", icon="☢️", fn=toxic),
    Pattern(id="cotton", name="Cotton Candy", icon="🍬", fn=cottonCandy),
    Pattern(id="deepspace", name="Deep Space", icon="🛸", fn=deepSpace),
    Pattern(id="infrared", name="Infrared", icon="🌡️", fn=infrared),
    Pattern(id="storm", name="Electric Storm", icon="🌩️", fn=electricStorm),
    Pattern(id="jade", name="Jade", icon="🪨", fn=jade),
    Pattern(id="copper", name="Copper Circuit", icon="🔧", fn=copperCircuit),
    Pattern(id="holo", name="Holographic", icon="💿", fn=holographic),
    Pattern(id="uv", name="Ultraviolet", icon="🔮", fn=ultraviolet),
    Pattern(id="caribbean", name="Caribbean", icon="🏖️", fn=caribbean),
    Pattern(id="neonsign", name="Neon Sign", icon="💡", fn=neonSign),
    Pattern(id="obsidian", name="Obsidian", icon="🖤", fn=obsidian),
    Pattern(id="golden", name="Golden Hour", icon="🌻", fn=goldenHour),
    Pattern(id="frost", name="Winter Frost", icon="🧊", fn=winterFrost),
    Pattern(id="aurora", name="Aurora", icon="🎇", fn=aurora),
    Pattern(id="hearth", name="Warm Hearth", icon="🕯️", fn=warmHearth),
    Pattern(id="deepteal", name="Deep Teal", icon="🌿", fn=deepTeal),
    Pattern(id="hotpink", name="Hot Pink", icon="💗", fn=hotPink),
    Pattern(id="lime", name="Lime Punch", icon="🍏", fn=limePunch),
    Pattern(id="sakura", name="Midnight Sakura", icon="🌙", fn=midnightSakura),
    Pattern(id="titanium", name="Titanium", icon="🔩", fn=titanium),
    Pattern(id="moltengold", name="Molten Gold", icon="🏆", fn=moltenGold),
    Pattern(id="coral", name="Coral Reef", icon="🪸", fn=coralReef),
    Pattern(id="candy", name="Candy Stripes", icon="🍭", fn=candyStripes),
    Pattern(id="frozen", name="Frozen Ocean", icon="🌊", fn=frozenOcean),
    Pattern(id="volcanic", name="Volcanic Ash", icon="💨", fn=volcanicAsh),
    Pattern(id="retrograde", name="Retrograde", icon="🔄", fn=retrograde),

    # 10 Infrared-style radial heat maps
    Pattern(id="ir_left", name="Heat Source Left", icon="🌡", fn=irLeft),
    Pattern(id="ir_cold", name="Cryo Core", icon="🥶", fn=cryoCore),
    Pattern(id="ir_teal", name="Thermal Teal", icon="🌿", fn=thermalTeal),
    Pattern(id="ir_dual", name="Dual Heat", icon="♨️", fn=dualHeat),
    Pattern(id="ir_vert", name="Vertical Burn", icon="🔆", fn=verticalBurn),
    Pattern(id="ir_solar", name="Solar Core", icon="☀️", fn=solarCore),
    Pattern(id="ir_plasma", name="Plasma Radial", icon="⚛️", fn=plasmaRadial),
    Pattern(id="ir_corner", name="Corner Blaze", icon="🔱", fn=cornerBlaze),
    Pattern(id="ir_coldwave", name="Cold Wave", icon="🌊", fn=coldWave),
    Pattern(id="ir_atomic", name="Atomic Glow", icon="☢️", fn=atomicGlow),

    # 30 More patterns
    Pattern(id="trizone", name="Tri-Zone", icon="🎯", fn=triZone),
    Pattern(id="flamtips", name="Flame Tips", icon="🕯", fn=flameTips),
    Pattern(id="nordic", name="Nordic", icon="🏔️", fn=nordic),
    Pattern(id="peachfuzz", name="Peach Fuzz", icon="🍑", fn=peachFuzz),
    Pattern(id="radioact", name="Radioactive", icon="☣️", fn=radioactive),
    Pattern(id="spectral", name="Spectral", icon="🌈", fn=spectral),
    Pattern(id="denim", name="Denim Blue", icon="👖", fn=denimBlue),
    Pattern(id="bronzeage", name="Bronze Age", icon="🏺", fn=bronzeAge),
    Pattern(id="purplehaze", name="Purple Haze", icon="💜", fn=purpleHaze),
    Pattern(id="nightsky2", name="Night Sky", icon="🌃", fn=nightSky),
    Pattern(id="highcontrast", name="High Contrast", icon="⬛", fn=highContrast),
    Pattern(id="blueprint", name="Blueprint", icon="📐", fn=blueprint),
    Pattern(id="mintfresh", name="Mint Fresh", icon="🌱", fn=mintFresh),
    Pattern(id="cyberdeck", name="Cyberdeck", icon="🖥️", fn=cyberdeck),
    Pattern(id="deepwine", name="Deep Wine", icon="🍷", fn=deepWine),
    Pattern(id="coppergold", name="Copper & Gold", icon="🪙", fn=copperGold),
    Pattern(id="seafoam", name="Seafoam", icon="🫧", fn=seafoam),
    Pattern(id="orchid", name="Orchid", icon="🌷", fn=orchid),
    Pattern(id="neonblue", name="Neon Blue", icon="💙", fn=neonBlue),
    Pattern(id="sandstone", name="Sandstone", icon="🏜️", fn=sandstone),
    Pattern(id="lavender", name="Lavender", icon="💐", fn=lavender),
    Pattern(id="candyapple", name="Candy Apple", icon="🍎", fn=candyApple),
    Pattern(id="aquadream", name="Aqua Dream", icon="💎", fn=aquaDream),
    Pattern(id="solarized", name="Solarized", icon="🌤️", fn=solarized),
    Pattern(id="magmachamber", name="Magma Chamber", icon="🌋", fn=magmaChamber),
    Pattern(id="carbon", name="Carbon Fiber", icon="🖤", fn=carbonFiber),
    Pattern(id="sundown", name="Sundown", icon="🌇", fn=sundown),
    Pattern(id="neonmint", name="Neon Mint", icon="🍃", fn=neonMint),
    Pattern(id="deepindigo", name="Deep Indigo", icon="🌀", fn=deepIndigo),
    Pattern(id="stormcloud", name="Storm Cloud", icon="⛈️", fn=stormCloud),
]

PATTERNS_BY_ID: Dict[str, Pattern] = {p.id: p for p in PATTERNS}
