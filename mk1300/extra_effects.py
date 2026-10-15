"""
50 Contrasty, non-gradient patterns for MK1300 V2 60% keyboard.

Ported from https://github.com/kickTROLL/mk1300v2_RGB (Apache-2.0)
Original work Copyright 2024 Yash (kickTROLL)
Modified: JS to Python port for mk1300-linux
"""

import math
from typing import Callable, Dict, List
from .layout import KEYBOARD_LAYOUT, Key
from .effects import RGBColor, Pattern, hsl, js_round, heatColor, nx, ny, zone, OFF


def col(k: Key) -> int:
    return math.floor(k.x + k.w / 2.0)


def hash_k(k: Key) -> float:
    return abs(math.sin(k.index * 137.508 + 42.0))


# ── 50 Contrasty Patterns ─────────────────────────────────────────────────────

def checkerboard(keys: List[Key]) -> List[RGBColor]:
    return [
        hsl(300, 1, 0.52) if (js_round(k.y) + col(k)) % 2 == 0 else hsl(270, 0.35, 0.07)
        for k in keys
    ]

def cyberStripes(keys: List[Key]) -> List[RGBColor]:
    res = []
    for k in keys:
        c = col(k) % 3
        if c == 0:
            res.append(hsl(300, 1, 0.52))
        elif c == 1:
            res.append(hsl(186, 1, 0.52))
        else:
            res.append(hsl(270, 0.25, 0.06))
    return res

def yinYang(keys: List[Key]) -> List[RGBColor]:
    return [hsl(300, 1, 0.52) if nx(k) < 0.5 else hsl(186, 1, 0.52) for k in keys]

def typeGlow(keys: List[Key]) -> List[RGBColor]:
    res = []
    for k in keys:
        z = zone(k)
        if z == "alpha":
            res.append(hsl(210, 0.08, 0.92))
        elif z == "num":
            res.append(hsl(210, 0.20, 0.55))
        else:
            res.append(hsl(220, 0.50, 0.06))
    return res

def rowNeon(keys: List[Key]) -> List[RGBColor]:
    hues = [0, 60, 120, 200, 280]
    return [hsl(hues[js_round(k.y)] if 0 <= js_round(k.y) < len(hues) else 0, 1, 0.52) for k in keys]

def bullsEye(keys: List[Key]) -> List[RGBColor]:
    H = [0, 60, 186, 300]
    return [
        hsl(H[math.floor((abs(nx(k) - 0.5) + abs(ny(k) - 0.5)) * 5.0) % 4], 1, 0.52)
        for k in keys
    ]

def policeLights(keys: List[Key]) -> List[RGBColor]:
    return [
        hsl(0, 0, 0.92) if js_round(k.y) == 0 else (hsl(0, 1, 0.52) if nx(k) < 0.5 else hsl(220, 1, 0.52))
        for k in keys
    ]

def phantomKeys(keys: List[Key]) -> List[RGBColor]:
    return [hsl(hash_k(k) * 360.0, 1, 0.55) if hash_k(k) > 0.72 else OFF for k in keys]

def binary(keys: List[Key]) -> List[RGBColor]:
    return [hsl(120, 1, 0.50) if k.index % 2 == 0 else hsl(240, 0.30, 0.05) for k in keys]

def rave(keys: List[Key]) -> List[RGBColor]:
    return [hsl(hash_k(k) * 360.0, 1, 0.52) for k in keys]

def disco(keys: List[Key]) -> List[RGBColor]:
    return [hsl(((js_round(k.y) * 5 + col(k)) * 23) % 360, 0.95, 0.50) for k in keys]

def vampire(keys: List[Key]) -> List[RGBColor]:
    return [hsl(0, 1, 0.50) if col(k) % 2 == 0 else hsl(5, 0.70, 0.14) for k in keys]

def stainedGlass(keys: List[Key]) -> List[RGBColor]:
    return [
        hsl(((js_round(k.y) * 3 + math.floor(col(k) / 3.0)) * 47) % 360, 0.90, 0.48)
        for k in keys
    ]

def laserGrid(keys: List[Key]) -> List[RGBColor]:
    res = []
    for k in keys:
        r = js_round(k.y)
        c = col(k)
        if r == 0 or r == 4 or c == 0 or c >= 13:
            res.append(hsl(186, 1, 0.60))
        else:
            res.append(hsl(186, 0.30, 0.04))
    return res

def diagonalStripes(keys: List[Key]) -> List[RGBColor]:
    H = [0, 55, 186, 300]
    return [hsl(H[(js_round(k.y) + col(k)) % 4], 1, 0.52) for k in keys]

def flameRow(keys: List[Key]) -> List[RGBColor]:
    lut = [{"h": 50, "l": 0.85}, {"h": 30, "l": 0.58}, {"h": 10, "l": 0.42}, {"h": 0, "l": 0.25}, {"h": 0, "l": 0.08}]
    res = []
    for k in keys:
        idx = 4 - js_round(k.y)
        e = lut[idx] if 0 <= idx < len(lut) else lut[4]
        res.append(hsl(e["h"], 1, e["l"]))
    return res

def voidPortal(keys: List[Key]) -> List[RGBColor]:
    res = []
    for k in keys:
        d = (1.0 - abs(nx(k) - 0.5) * 2.0 + 1.0 - abs(ny(k) - 0.5) * 2.0) / 2.0
        if d > 0.70:
            res.append(hsl(300, 1, 0.65))
        elif d > 0.45:
            res.append(hsl(186, 1, 0.52))
        elif d > 0.25:
            res.append(hsl(270, 0.60, 0.15))
        else:
            res.append(hsl(270, 0.30, 0.04))
    return res

def sunriseFire(keys: List[Key]) -> List[RGBColor]:
    lut = [{"h": 55, "l": 0.90}, {"h": 50, "l": 0.58}, {"h": 25, "l": 0.50}, {"h": 5, "l": 0.38}, {"h": 0, "l": 0.12}]
    return [hsl(lut[js_round(k.y)]["h"], 1, lut[js_round(k.y)]["l"]) for k in keys]

def neonBlueprint(keys: List[Key]) -> List[RGBColor]:
    res = []
    for k in keys:
        z = zone(k)
        if z == "mod":
            res.append(hsl(186, 1, 0.55))
        elif z == "alpha":
            res.append(hsl(210, 0.08, 0.88))
        else:
            res.append(hsl(220, 0.80, 0.18))
    return res

CHERRY_BOMBS = {21, 76, 84, 97, 111}
def cherryBomb(keys: List[Key]) -> List[RGBColor]:
    res = []
    for k in keys:
        if k.index in CHERRY_BOMBS:
            res.append(hsl(0, 1, 0.55))
        elif zone(k) == "alpha":
            res.append(hsl(340, 0.55, 0.22))
        else:
            res.append(hsl(0, 0.40, 0.06))
    return res

def toxicRain(keys: List[Key]) -> List[RGBColor]:
    res = []
    for k in keys:
        c = col(k)
        peak = (c * 73 + 11) % 5
        d = abs(js_round(k.y) - peak)
        res.append(hsl(100 + c * 3, 1, max(0.04, 0.55 - d * 0.12)))
    return res

def pinstripe(keys: List[Key]) -> List[RGBColor]:
    return [hsl(180, 0.05, 0.88) if col(k) % 2 == 0 else hsl(220, 0.40, 0.06) for k in keys]

def glitch(keys: List[Key]) -> List[RGBColor]:
    H = [180, 300, 55, 120, 200]
    return [OFF if hash_k(k) > 0.88 else hsl(H[js_round(k.y)], 1, 0.50) for k in keys]

def heatZone(keys: List[Key]) -> List[RGBColor]:
    res = []
    for k in keys:
        z = zone(k)
        if z == "alpha":
            res.append(hsl(30.0 + nx(k) * 20.0, 1, 0.62))
        elif z == "num":
            res.append(hsl(15, 1, 0.48))
        else:
            res.append(hsl(0, 0.30, 0.06))
    return res

def iceSpike(keys: List[Key]) -> List[RGBColor]:
    res = []
    for k in keys:
        r = js_round(k.y)
        if r == 0:
            res.append(hsl(200, 0.15, 0.92))
        else:
            res.append(hsl(205, 0.80, max(0.08, 0.45 - r * 0.06)))
    return res

def acidWash(keys: List[Key]) -> List[RGBColor]:
    res = []
    for k in keys:
        if zone(k) == "mod":
            res.append(hsl(80, 0.30, 0.05))
        else:
            w = math.sin(nx(k) * 10.0 + ny(k) * 6.0) * 0.5 + 0.5
            res.append(hsl(75.0 + w * 20.0, 1, 0.30 + w * 0.22))
    return res

def neonTetris(keys: List[Key]) -> List[RGBColor]:
    C = [hsl(186, 1, 0.52), hsl(45, 1, 0.52), hsl(270, 1, 0.52), hsl(120, 1, 0.45), hsl(0, 1, 0.52)]
    return [C[js_round(k.y)] if 0 <= js_round(k.y) < len(C) else C[0] for k in keys]

def camo(keys: List[Key]) -> List[RGBColor]:
    res = []
    for k in keys:
        h = hash_k(k)
        if h > 0.65:
            res.append(hsl(90, 0.50, 0.22))
        elif h > 0.35:
            res.append(hsl(35, 0.45, 0.18))
        else:
            res.append(hsl(110, 0.25, 0.08))
    return res

def deepMagma(keys: List[Key]) -> List[RGBColor]:
    return [
        heatColor(1.0 - math.sqrt((1.0 - nx(k)) ** 2 + (1.0 - ny(k)) ** 2) / math.sqrt(2.0) * 0.95, "ir")
        for k in keys
    ]

def frozenTundra(keys: List[Key]) -> List[RGBColor]:
    return [
        heatColor(1.0 - math.sqrt(nx(k) ** 2 + ny(k) ** 2) / math.sqrt(2.0) * 0.90, "cryo")
        for k in keys
    ]

def rowCheckerboard(keys: List[Key]) -> List[RGBColor]:
    H = [300, 186, 55, 120, 270]
    return [
        hsl(H[js_round(k.y)], 1, 0.52) if col(k) % 2 == 0 else hsl(H[js_round(k.y)], 0.30, 0.08)
        for k in keys
    ]

def neonCross(keys: List[Key]) -> List[RGBColor]:
    res = []
    for k in keys:
        r = js_round(k.y)
        c = col(k)
        isCR = (r == 2)
        isCL = (6 <= c <= 8)
        if isCR and isCL:
            res.append(hsl(186, 0.20, 0.92))
        elif isCR or isCL:
            res.append(hsl(186, 1, 0.52))
        else:
            res.append(hsl(220, 0.40, 0.06))
    return res

def horror(keys: List[Key]) -> List[RGBColor]:
    return [
        hsl(0, 1, 0.30) if (js_round(k.y) + col(k)) % 2 == 0 else hsl(0, 0.40, 0.04)
        for k in keys
    ]

def neonGradientStripe(keys: List[Key]) -> List[RGBColor]:
    return [
        hsl(300 if col(k) % 2 == 0 else 55, 1, 0.45 + (1.0 - ny(k)) * 0.10)
        for k in keys
    ]

def goldRush(keys: List[Key]) -> List[RGBColor]:
    res = []
    for k in keys:
        if zone(k) == "mod":
            res.append(hsl(44, 1, 0.52))
        else:
            res.append(hsl(30, 0.50, 0.06 + hash_k(k) * 0.06))
    return res

def rainbowDiagonal(keys: List[Key]) -> List[RGBColor]:
    return [hsl(((nx(k) + ny(k)) / 2.0) * 360.0, 1, 0.50) for k in keys]

def acidCheckerboard(keys: List[Key]) -> List[RGBColor]:
    return [
        hsl(100, 1, 0.52) if (js_round(k.y) + col(k)) % 2 == 0 else hsl(320, 1, 0.52)
        for k in keys
    ]

SPOT_ESC = 21
def spotlightEsc(keys: List[Key]) -> List[RGBColor]:
    res = []
    for k in keys:
        if k.index == SPOT_ESC:
            res.append(hsl(55, 1, 0.92))
        else:
            dist = math.sqrt(nx(k) ** 2 + ny(k) ** 2)
            res.append(hsl(50, 0.50, max(0.0, 0.20 - dist * 0.18)))
    return res

def neonRowsAlt(keys: List[Key]) -> List[RGBColor]:
    return [
        hsl(300, 1, 0.55) if js_round(k.y) % 2 == 0 else hsl(270, 0.30, 0.06)
        for k in keys
    ]

def emberWaves(keys: List[Key]) -> List[RGBColor]:
    res = []
    for k in keys:
        w = math.sin(nx(k) * math.pi * 4.0 + ny(k) * math.pi * 2.0) * 0.5 + 0.5
        res.append(hsl(10.0 + w * 30.0, 1, 0.15 + w * 0.40))
    return res

def neonBlocks(keys: List[Key]) -> List[RGBColor]:
    return [
        hsl(((math.floor(col(k) / 3.0) * 3 + math.floor(js_round(k.y) / 2.0)) * 61) % 360, 1, 0.50)
        for k in keys
    ]

def ultrawideStripe(keys: List[Key]) -> List[RGBColor]:
    H = [0, 186, 270]
    return [hsl(H[min(2, math.floor(col(k) / 5.0))], 1, 0.52) for k in keys]

def midnightFire(keys: List[Key]) -> List[RGBColor]:
    res = []
    for k in keys:
        r = js_round(k.y)
        if r == 0:
            res.append(hsl(35, 1, 0.60))
        elif r == 1:
            res.append(hsl(10, 1, 0.42))
        else:
            res.append(hsl(270, 0.60, 0.08 + (1.0 - ny(k)) * 0.04))
    return res

def lavaCheckerboard(keys: List[Key]) -> List[RGBColor]:
    return [
        hsl(20, 1, 0.52) if (js_round(k.y) + col(k)) % 2 == 0 else hsl(10, 0.50, 0.07)
        for k in keys
    ]

FROSTBITE_SET = {111}
def frostbite(keys: List[Key]) -> List[RGBColor]:
    res = []
    for k in keys:
        if k.index in FROSTBITE_SET:
            res.append(hsl(200, 0.10, 0.92))
        elif zone(k) == "alpha":
            res.append(hsl(200, 1, 0.55))
        elif zone(k) == "num":
            res.append(hsl(205, 0.80, 0.35))
        else:
            res.append(hsl(220, 0.60, 0.10))
    return res

def hotSpots(keys: List[Key]) -> List[RGBColor]:
    res = []
    for k in keys:
        x = nx(k)
        y = ny(k)
        d = max(
            1.0 - math.sqrt(x ** 2 + y ** 2) / math.sqrt(2.0),
            1.0 - math.sqrt((1.0 - x) ** 2 + (1.0 - y) ** 2) / math.sqrt(2.0),
            1.0 - math.sqrt((x - 0.5) ** 2 + (y - 0.5) ** 2) / (math.sqrt(2.0) / 2.0),
        )
        res.append(heatColor(d * 0.95, "ir"))
    return res

def pixelFlag(keys: List[Key]) -> List[RGBColor]:
    res = []
    for k in keys:
        x = nx(k)
        if x < 0.33:
            res.append(hsl(0, 1, 0.50))
        elif x < 0.66:
            res.append(hsl(0, 0, 0.90))
        else:
            res.append(hsl(220, 1, 0.45))
    return res

def spectrumCross(keys: List[Key]) -> List[RGBColor]:
    res = []
    for k in keys:
        r = js_round(k.y)
        c = col(k)
        isCR = (r == 2)
        isCL = (6 <= c <= 8)
        if isCR and isCL:
            res.append(hsl(0, 0, 0.96))
        elif isCR:
            res.append(hsl(ny(k) * 240.0, 1, 0.52))
        elif isCL:
            res.append(hsl(nx(k) * 360.0, 1, 0.52))
        else:
            res.append(hsl(220, 0.30, 0.06))
    return res

DEEP_CHERRY = {21, 76, 84, 97, 111, 105, 117}
def deepCherry(keys: List[Key]) -> List[RGBColor]:
    res = []
    for k in keys:
        if k.index in DEEP_CHERRY:
            res.append(hsl(348, 1, 0.55))
        elif zone(k) == "alpha":
            res.append(hsl(340, 0.65, 0.18))
        else:
            res.append(hsl(345, 0.40, 0.06))
    return res

def electricFence(keys: List[Key]) -> List[RGBColor]:
    return [
        hsl(186, 1, 0.55) if math.floor(col(k) / 2.0) % 2 == 0 else hsl(220, 0.30, 0.05)
        for k in keys
    ]


EXTRA_PATTERNS: List[Pattern] = [
    Pattern(id="checkerboard", name="Checkerboard", icon="♟️", fn=checkerboard),
    Pattern(id="cyberstripes", name="Cyber Stripes", icon="⚡", fn=cyberStripes),
    Pattern(id="yinyang", name="Yin Yang", icon="☯️", fn=yinYang),
    Pattern(id="typeglow", name="Type Glow", icon="⌨️", fn=typeGlow),
    Pattern(id="rowneon", name="Row Neon", icon="📊", fn=rowNeon),
    Pattern(id="bullseye", name="Bull's Eye", icon="🎯", fn=bullsEye),
    Pattern(id="policelight", name="Police Lights", icon="🚔", fn=policeLights),
    Pattern(id="phantom", name="Phantom Keys", icon="👻", fn=phantomKeys),
    Pattern(id="binary", name="Binary", icon="💻", fn=binary),
    Pattern(id="rave", name="Rave", icon="🎉", fn=rave),
    Pattern(id="disco", name="Disco Floor", icon="🪩", fn=disco),
    Pattern(id="vampire", name="Vampire", icon="🧛", fn=vampire),
    Pattern(id="stainedglass", name="Stained Glass", icon="🪟", fn=stainedGlass),
    Pattern(id="lasergrid", name="Laser Grid", icon="🔴", fn=laserGrid),
    Pattern(id="diagstripes", name="Diagonal Stripes", icon="↗️", fn=diagonalStripes),
    Pattern(id="flamerow", name="Flame Row", icon="🔥", fn=flameRow),
    Pattern(id="voidportal", name="Void Portal", icon="🌀", fn=voidPortal),
    Pattern(id="sunrisefire", name="Sunrise Fire", icon="🌄", fn=sunriseFire),
    Pattern(id="neobluprint", name="Neon Blueprint", icon="📐", fn=neonBlueprint),
    Pattern(id="cherrybomb", name="Cherry Bomb", icon="💣", fn=cherryBomb),
    Pattern(id="toxicrain", name="Toxic Rain", icon="☣️", fn=toxicRain),
    Pattern(id="pinstripe", name="Pinstripe", icon="👔", fn=pinstripe),
    Pattern(id="glitch", name="Glitch", icon="📺", fn=glitch),
    Pattern(id="heatzone", name="Heat Zone", icon="♨️", fn=heatZone),
    Pattern(id="icespike", name="Ice Spike", icon="🧊", fn=iceSpike),
    Pattern(id="acidwash", name="Acid Wash", icon="🧪", fn=acidWash),
    Pattern(id="neontetris", name="Neon Tetris", icon="🟦", fn=neonTetris),
    Pattern(id="camo", name="Camo", icon="🫙", fn=camo),
    Pattern(id="deepmagma", name="Deep Magma", icon="🌋", fn=deepMagma),
    Pattern(id="frozentundra", name="Frozen Tundra", icon="🏔️", fn=frozenTundra),
    Pattern(id="rowcheck", name="Row Checkerboard", icon="🎲", fn=rowCheckerboard),
    Pattern(id="neoncross", name="Neon Cross", icon="➕", fn=neonCross),
    Pattern(id="horror", name="Horror", icon="💀", fn=horror),
    Pattern(id="neonstrip2", name="Neon Gradient Strip", icon="🌈", fn=neonGradientStripe),
    Pattern(id="goldrush", name="Gold Rush", icon="💰", fn=goldRush),
    Pattern(id="rainbowdiag", name="Rainbow Diagonal", icon="🌈", fn=rainbowDiagonal),
    Pattern(id="acidcheck", name="Acid Checkerboard", icon="☢️", fn=acidCheckerboard),
    Pattern(id="spotlightesc", name="Spotlight: Esc", icon="🔦", fn=spotlightEsc),
    Pattern(id="neonrowalt", name="Neon Row Alt", icon="📶", fn=neonRowsAlt),
    Pattern(id="emberwaves", name="Ember Waves", icon="🔥", fn=emberWaves),
    Pattern(id="neonblocks", name="Neon Blocks", icon="🟧", fn=neonBlocks),
    Pattern(id="uwistripe", name="Ultrawide Stripe", icon="🎌", fn=ultrawideStripe),
    Pattern(id="midnightfire", name="Midnight Fire", icon="🌙", fn=midnightFire),
    Pattern(id="lavacheck", name="Lava Checkerboard", icon="🌋", fn=lavaCheckerboard),
    Pattern(id="frostbite", name="Frostbite", icon="🥶", fn=frostbite),
    Pattern(id="hotspots", name="Hot Spots", icon="🌡️", fn=hotSpots),
    Pattern(id="pixelflag", name="Pixel Flag", icon="🏁", fn=pixelFlag),
    Pattern(id="spectrumcross", name="Spectrum Cross", icon="✚", fn=spectrumCross),
    Pattern(id="deepcherry", name="Deep Cherry", icon="🍒", fn=deepCherry),
    Pattern(id="elecfence", name="Electric Fence", icon="⚡", fn=electricFence),
]

EXTRA_PATTERNS_BY_ID: Dict[str, Pattern] = {p.id: p for p in EXTRA_PATTERNS}
