# v2 open-bay machines: a trial of keeping the level through-conveyor (the item goes in at one mouth and
# comes out at the other) while opening the middle, so the work done on the item is in plain sight instead
# of hidden in a closed box. The mouths at each end are the same folding covers as foundation D.
import math
from . import hero as _hero
from . import pairs as _pairs
from .base import foot_anchor, foot_bin
from .d import *          # noqa: F401,F403
from .d import run, cover, K


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


for name, fn in (("press_bay", press_bay), ("saw_bay", saw_bay)):
    fn.frame = {"iso": (3.3, 0.72), "side": (3.4, 0.95), "top": (3.2, 0.6), "end": (2.6, 1.0)}
    _hero.HEROES[name] = fn
_hero.press.frame = _pairs.saw.frame = {"iso": (3.3, 0.72), "side": (3.4, 0.95), "top": (3.2, 0.6), "end": (2.6, 1.0)}
