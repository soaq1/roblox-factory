# v2 open-bay machines: a trial of keeping the level through-conveyor (the item goes in at one mouth and
# comes out at the other) while opening the middle, so the work done on the item is in plain sight instead
# of hidden in a closed box. The mouths at each end are the same folding covers as foundation D.
import math
from . import hero as _hero
from . import pairs as _pairs
from .base import foot_anchor, foot_bin
from .d import *          # noqa: F401,F403
from .d import run, cover, frame, K


def bay(m, foot=None):
    """The conveyor, a mouth at each end, and the two pedestals the open frame stands on."""
    run(m, -1.5, 1.5, braces=(-4 / 3, -1.0, 1.0, 4 / 3))
    if foot:
        foot(m)
    for d in SIDES:
        bx(m, (-0.47, 0.47), tuple(sorted((d * 0.36, d * 0.50))), (0.0, 0.15), T, bevel=0.035)
        bx(m, (-0.44, 0.44), tuple(sorted((d * 0.33, d * 0.485))), (0.10, 0.62), G, bevel=0.04)
    cover(m, BX, 1)
    cover(m, -BX, -1)


def press_bay(m):
    """Press with an open bay: the ingot rides in under the west cover, is flattened in plain sight
    under the platen, and rides out under the east cover as a plate."""
    bay(m)
    for d in SIDES:
        m.box((0.52, 0.02, 0.24), (0, d * 0.488, 0.38), D, bevel=0.008)
        m.cyl(0.075, 0.03, (0, d * 0.50, 0.38), T, seg=10, axis="Y")
        m.cyl(0.055, 0.012, (0, d * 0.512, 0.38), "h_lite", seg=10, axis="Y")
        for sx in SIDES:
            x, y = sx * 0.31, d * 0.41
            m.cyl(0.088, 0.07, (x, y, 0.655), D, seg=6)
            m.cyl(0.055, 0.90, (x, y, 1.07), "h_lite", seg=8)
            m.cyl(0.08, 0.27, (x, y, 1.12), G, seg=8)
            m.cyl(0.082, 0.06, (x, y, 1.73), D, seg=6)
            m.cyl(0.045, 0.05, (x, y, 1.785), "h_lite", seg=6)
    bx(m, (-0.43, 0.43), (-0.485, 0.485), (1.02, 1.22), T, bevel=0.022)
    bx(m, (-0.24, 0.24), (-0.22, 0.22), (0.95, 1.03), D, bevel=0.02)
    m.cyl(0.11, 0.26, (0, 0, 1.34), "h_steel", seg=12)
    bx(m, (-0.45, 0.45), (-0.50, 0.50), (1.46, 1.70), G, bevel=0.05)
    m.cyl(0.215 * K, 0.05, (0, 0, 1.72), D, seg=8, rot=rad(22.5))
    m.cyl(0.19 * K, 0.30, (0, 0, 1.86), G, seg=8, rot=rad(22.5))
    m.cyl(0.215 * K, 0.05, (0, 0, 2.00), D, seg=8, rot=rad(22.5))
    m.cyl(0.07, 0.05, (0, 0, 2.05), "h_lite", seg=6)
    m.box((0.24, 0.13, 0.09), (-1.15, 0, 0.352), "h_steel", bevel=0.02)
    m.box((0.30, 0.26, 0.035), (0.0, 0, 0.325), "h_lite")
    m.box((0.30, 0.26, 0.035), (1.15, 0, 0.325), "h_lite")


def saw_bay(m):
    """Sawmill with an open bay: the log rides in, the blade cuts it in plain sight under its guard,
    and planks ride out."""
    bay(m)
    zc = 0.75
    for d in SIDES:
        bx(m, (-0.15, 0.15), tuple(sorted((d * 0.33, d * 0.485))), (0.58, 1.22), G, bevel=0.035)
        m.cyl(0.18, 0.04, (0, d * 0.478, zc), D, seg=12, axis="Y")
        m.cyl(0.07, 0.05, (0, d * 0.482, zc), "h_lite", seg=8, axis="Y")
    m.cyl(0.045, 0.80, (0, 0, zc), "h_lite", seg=8, axis="Y")
    _pairs.saw_blade(m, zc, 0.37)
    _pairs.saw_hood(m, zc, 0.46, 0.405, zc)
    bx(m, (-0.17, 0.17), (-0.485, 0.485), (1.19, 1.36), G, bevel=0.04)
    m.cyl(0.10, 0.50, (-1.15, 0, 0.405), "h_wood", seg=8, axis="X")
    for s in SIDES:
        m.box((0.40, 0.085, 0.16), (-0.02, s * 0.055, 0.385), "h_wood_l")
        m.box((0.48, 0.09, 0.05), (1.15, s * 0.075, 0.33), "h_wood_l")


def blast3(m):
    """Blast furnace, 3x3: a trial of a big machine in the same language. Ore and fuel come in by two
    mouths side by side on the west and iron leaves by one on the east. The furnace stands on a wide
    hall; a gallery climbs from above each input to the furnace top; a blower house stands between the
    inputs; two stoves stand behind and feed the ring main round the stack."""
    from .works import ring_pipe
    for sy in SIDES:
        with m.at((0, sy * 1.0, 0)):
            run(m, -1.5, -0.5, braces=(-4 / 3, -1.0))
            cover(m, -0.5, -1)
    run(m, 0.5, 1.5, braces=(1.0, 4 / 3))
    cover(m, 0.5, 1)
    # the hall
    bx(m, (-0.52, 0.52), (-1.49, 1.49), (0.0, 0.16), T, bevel=0.045)
    bx(m, (-0.50, 0.50), (-1.47, 1.47), (0.12, 0.90), G, bevel=0.04)
    bx(m, (-0.52, 0.52), (-1.49, 1.49), (0.84, 0.96), D, bevel=0.03)
    for sy in SIDES:                                          # end walls: a sunk door
        with frame(m, (0, sy * 1.5), (0, -sy)):
            m.box((0.04, 0.62, 0.48), (0.045, 0, 0.50), G, bevel=0.028)
            m.box((0.012, 0.012, 0.42), (0.022, 0, 0.50), SLIT)
            for s in SIDES:
                m.box((0.02, 0.03, 0.14), (0.018, s * 0.06, 0.50), T)
    # blower house between the two inputs
    bx(m, (-1.18, -0.48), (-0.40, 0.40), (0.0, 0.14), T, bevel=0.04)
    bx(m, (-1.15, -0.48), (-0.37, 0.37), (0.10, 0.76), G, bevel=0.04)
    m.cyl(0.27, 0.05, (-1.16, 0, 0.43), T, seg=12, axis="X")
    m.cyl(0.215, 0.02, (-1.166, 0, 0.43), SLIT, seg=12, axis="X")
    for i in (-1, 0, 1):
        m.box((0.03, 0.40 * (1 - abs(i) * 0.25), 0.032), (-1.176, 0, 0.43 + i * 0.11), G)
    bx(m, (-0.84, -0.46), (-0.17, 0.17), (0.72, 1.02), G, bevel=0.035)
    # the furnace on the hall
    Z = 0.94
    octa(m, 0.48, 0.48, Z, Z + 0.34, T)
    oct_ring(m, 0.51, 0.11, Z + 0.30, Z + 0.40, D)
    octa(m, 0.47, 0.30, Z + 0.36, Z + 1.50, G)
    for z in (Z + 0.74, Z + 1.12):
        a = 0.47 - (z - Z - 0.36) / 1.14 * 0.17
        octa(m, a + 0.024, a + 0.012, z - 0.03, z + 0.03, D)
    oct_ring(m, 0.34, 0.09, Z + 1.46, Z + 1.56, D)
    octa(m, 0.27, 0.14, Z + 1.52, Z + 1.68, G)
    m.pipe([(-0.30, 0, Z + 1.20), (-0.30, 0, Z + 1.78), (-0.13, 0, Z + 1.98), (0.13, 0, Z + 1.98), (0.30, 0, Z + 1.78),
            (0.30, 0, Z + 1.20)], 0.055, W, seg=8)
    for k in range(3):                                        # tuyere peepholes, lit from within
        m.box((0.012, 0.06, 0.09), (-0.49, (k - 1) * 0.13, Z + 0.15), "h_glow")
    for dz in (-0.065, 0.065):
        m.box((0.03, 0.44, 0.03), (-0.496, 0, Z + 0.15 + dz), TD)
    # hot blast: ring main, a tuyere on every flat, two stoves behind
    ring_pipe(m, 0.57, Z + 0.52, 0.055, W)
    for j in range(8):
        a = j * math.pi / 4
        m.cyl(0.034, 0.16, (math.cos(a) * 0.50, math.sin(a) * 0.50, Z + 0.52), W, seg=8, axis="X", rot=a)
    for sy in SIDES:
        with m.at((1.0, sy * 1.0, 0)):
            octa(m, 0.41, 0.41, 0.0, 0.13, T)
            octa(m, 0.36, 0.36, 0.10, 1.88, G)
            for z in (0.62, 1.30):
                octa(m, 0.378, 0.378, z - 0.03, z + 0.03, D)
            octa(m, 0.36, 0.22, 1.88, 2.08, G)
            octa(m, 0.22, 0.10, 2.08, 2.18, D)
        a = math.atan2(sy, 1)
        m.cyl(0.062, 0.56, (math.cos(a) * 0.82, math.sin(a) * 0.82, Z + 0.52), W, seg=8, axis="X", rot=a)
        m.cyl(0.085, 0.04, (math.cos(a) * 1.06, math.sin(a) * 1.06, Z + 0.52), D, seg=8, axis="X", rot=a)
    # a gallery from above each input up to the furnace top
    for s in SIDES:
        m.prism([(s * 1.22, 0.94), (s * 0.94, 0.94), (s * 0.12, Z + 1.50), (s * 0.40, Z + 1.50)], -0.15, 0.15, "X", G)
        for sx in SIDES:
            a, b = sorted((sx * 0.15, sx * 0.195))
            m.prism([(s * 1.27, 0.94), (s * 0.94, 0.94), (s * 0.12, Z + 1.50), (s * 0.45, Z + 1.50)], a, b, "X", D)
        bx(m, (-0.21, 0.21), tuple(sorted((s * 0.90, s * 1.30))), (0.92, 1.06), D, bevel=0.03)
    # the tap: iron runs down a runner into the output mouth
    m.prism([(0.46, Z + 0.10), (0.86, 0.86), (0.86, 0.78), (0.46, Z + 0.02)], -0.10, 0.10, "Y", D)
    m.prism([(0.46, Z + 0.12), (0.86, 0.88), (0.86, 0.86), (0.46, Z + 0.10)], -0.09, 0.09, "Y", "h_glow")
    for s in SIDES:
        a, b = sorted((s * 0.10, s * 0.155))
        m.prism([(0.46, Z + 0.20), (0.86, 0.96), (0.86, 0.78), (0.46, Z + 0.02)], a, b, "Y", G)


blast3.frame = {"iso": (5.2, 1.25), "side": (4.6, 1.5), "top": (3.8, 1.0), "end": (4.6, 1.5)}
_hero.HEROES["blast3"] = blast3


def lineup(m):
    """Four machines of different size at one scale, with a figure: sawmill, press, smelter, blast
    furnace."""
    with m.at((-7.0, 0, 0)):
        saw_bay(m)
    with m.at((-3.2, 0, 0)):
        press_bay(m)
    with m.at((0.6, 0, 0)):
        _hero.smelter(m)
    with m.at((5.2, 0, 0)):
        blast3(m)
    with m.at((-5.1, -1.3, 0), -0.5):                         # a Roblox character is about 5 studs: 1.67 cells
        for sx in SIDES:
            m.box((0.30, 0.30, 0.64), (sx * 0.16, 0, 0.32), "g5")
            m.box((0.28, 0.30, 0.62), (sx * 0.48, 0, 0.96), "sand")
        m.box((0.64, 0.32, 0.64), (0, 0, 0.96), "water")
        m.cyl(0.21, 0.36, (0, 0, 1.47), "sand", seg=10)


lineup.frame = {"iso": (13.5, 0.9), "side": (15.5, 1.5), "top": (15.5, 1.0), "end": (4.6, 1.5)}
_hero.HEROES["lineup"] = lineup


for name, fn in (("press_bay", press_bay), ("saw_bay", saw_bay)):
    fn.frame = {"iso": (3.3, 0.72), "side": (3.4, 0.95), "top": (3.2, 0.6), "end": (2.6, 1.0)}
    _hero.HEROES[name] = fn
_hero.press.frame = _pairs.saw.frame = {"iso": (3.3, 0.72), "side": (3.4, 0.95), "top": (3.2, 0.6), "end": (2.6, 1.0)}
