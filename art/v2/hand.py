# v2 hand work: the fire, the furnace, the chest and the benches where things are made by hand. They are
# timber and stone with steel fittings, to set them apart from the machines.
import math
from .d import *          # noqa: F401,F403
from .d import free, K

WD, WL = "h_wood", "h_wood_l"


def campfire(m):
    """Campfire, 1x1: a ring of stones, crossed logs, flame."""
    for k in range(8):
        a = k * math.pi / 4
        m.box((0.20, 0.15, 0.13), (0.34 * math.cos(a), 0.34 * math.sin(a), 0.065), "h_stone", bevel=0.03, rot=a + math.pi / 2)
    for y in (-0.11, 0.11):
        m.cyl(0.065, 0.50, (0, y, 0.085), WD, seg=8, axis="X")
        m.cyl(0.065, 0.50, (y, 0, 0.20), WD, seg=8, axis="Y")
    m.cyl(0.15, 0.36, (0, 0, 0.44), "h_glow", seg=6, r2=0.0)
    m.cyl(0.09, 0.22, (0.08, 0.05, 0.37), "h_oil", seg=6, r2=0.0)
    m.cyl(0.08, 0.20, (-0.08, -0.05, 0.36), "h_oil", seg=6, r2=0.0)


def hand_furnace(m):
    """Hand furnace, 1x1: a small stone furnace, its fire set back behind bars in each side, with a
    stub of chimney."""
    bx(m, (-0.42, 0.42), (-0.40, 0.40), (0.0, 0.12), T, bevel=0.03)
    bx(m, (-0.38, 0.38), (-0.36, 0.36), (0.08, 0.74), "h_stone", bevel=0.045)
    bx(m, (-0.41, 0.41), (-0.39, 0.39), (0.70, 0.82), D, bevel=0.03)
    bx(m, (-0.15, 0.15), (-0.15, 0.15), (0.80, 1.14), "h_stone", bevel=0.03)
    bx(m, (-0.18, 0.18), (-0.18, 0.18), (1.10, 1.19), D, bevel=0.02)
    m.box((0.22, 0.22, 0.012), (0, 0, 1.192), SLIT)
    for d in SIDES:
        y = d * 0.362
        m.box((0.36, 0.012, 0.24), (0, y, 0.38), "h_glow")
        for k in range(4):
            m.box((0.025, 0.03, 0.24), (-0.12 + k * 0.08, y + d * 0.012, 0.38), TD)
        for sz in SIDES:
            m.box((0.46, 0.05, 0.05), (0, y + d * 0.012, 0.38 + sz * 0.145), D)
        for sx in SIDES:
            m.box((0.05, 0.05, 0.29), (sx * 0.205, y + d * 0.012, 0.38), D)


def chest(m):
    """Chest, 1x1: a banded timber chest with a rounded lid and a latch."""
    bx(m, (-0.42, 0.42), (-0.30, 0.30), (0.0, 0.42), WD, bevel=0.03)
    lid = [(-0.30, 0.42), (-0.30, 0.52), (-0.19, 0.64), (0.19, 0.64), (0.30, 0.52), (0.30, 0.42)]
    m.prism(lid, -0.42, 0.42, "X", WL)
    for x in (-0.27, 0.27):
        m.prism([(y * 1.05, 0.0 + (z - 0.0) * 1.0 + (0.012 if z > 0.45 else 0.0)) for y, z in
                 [(-0.30, 0.0)] + lid + [(0.30, 0.0)]], x - 0.045, x + 0.045, "X", D)
    for s in SIDES:
        m.box((0.14, 0.03, 0.16), (0, s * 0.305, 0.40), "h_lite", bevel=0.01)
        m.box((0.05, 0.02, 0.05), (0, s * 0.322, 0.37), T)


def bench(m, x0, x1, hy=0.36, top=0.70):
    """A work bench: a thick top on an apron and four stout legs, with a shelf between them."""
    bx(m, (x0, x1), (-hy, hy), (top - 0.11, top), WL, bevel=0.025)
    bx(m, (x0 + 0.05, x1 - 0.05), (-hy + 0.05, hy - 0.05), (top - 0.22, top - 0.10), WD, bevel=0.0)
    for x in (x0 + 0.10, x1 - 0.10):
        for s in SIDES:
            m.box((0.11, 0.11, top - 0.11), (x, s * (hy - 0.10), (top - 0.11) / 2), WD)
    bx(m, (x0 + 0.08, x1 - 0.08), (-hy + 0.10, hy - 0.10), (0.14, 0.20), WD, bevel=0.0)
    return top


def vise(m, x, y, z):
    bx(m, (x - 0.10, x + 0.10), (y - 0.08, y + 0.08), (z, z + 0.07), T, bevel=0.015)
    for sx in SIDES:
        bx(m, tuple(sorted((x + sx * 0.03, x + sx * 0.10))), (y - 0.10, y + 0.10), (z + 0.06, z + 0.24), T, bevel=0.02)
    m.cyl(0.025, 0.34, (x + 0.05, y, z + 0.13), "h_lite", seg=8, axis="X")
    m.cyl(0.02, 0.18, (x + 0.22, y, z + 0.13), "h_lite", seg=6, axis="Y")


def hammer(m, x, y, z, rot=0.0):
    with m.at((x, y, z), rot):
        m.cyl(0.022, 0.34, (0, 0, 0.03), WD, seg=6, axis="X")
        m.box((0.09, 0.20, 0.08), (0.16, 0, 0.04), "h_steel", bevel=0.015)


def anvil(m, x, y, z):
    with m.at((x, y, 0)):
        bx(m, (-0.11, 0.11), (-0.10, 0.10), (z, z + 0.07), T, bevel=0.015)
        bx(m, (-0.06, 0.06), (-0.07, 0.07), (z + 0.06, z + 0.17), T, bevel=0.0)
        m.prism([(-0.26, z + 0.25), (-0.13, z + 0.16), (0.16, z + 0.16), (0.16, z + 0.27), (-0.13, z + 0.27)], -0.085, 0.085, "Y", T)


def pot(m, x, y, z):
    m.cyl(0.12, 0.03, (x, y, z + 0.015), D, seg=10)
    m.cyl(0.11, 0.16, (x, y, z + 0.11), "h_steel", seg=10)
    m.cyl(0.12, 0.03, (x, y, z + 0.205), D, seg=10)
    m.cyl(0.03, 0.04, (x, y, z + 0.24), T, seg=8)


def screen(m, x, y, z, w=0.36):
    bx(m, (x - 0.07, x + 0.07), (y - 0.05, y + 0.05), (z, z + 0.08), D, bevel=0.015)
    bx(m, (x - w / 2, x + w / 2), (y - 0.04, y + 0.04), (z + 0.07, z + 0.36), D, bevel=0.02)
    for s in SIDES:
        m.box((w - 0.06, 0.012, 0.21), (x, y + s * 0.041, z + 0.215), "h_core")


def wb_basic(m):
    """Basic bench, 1x1: a small bench with a block of wood on it, a saw cut into the block and a
    hammer."""
    z = bench(m, -0.44, 0.44)
    m.box((0.30, 0.22, 0.16), (-0.10, 0.06, z + 0.08), WD, bevel=0.015)
    m.box((0.40, 0.012, 0.14), (-0.06, 0.06, z + 0.21), "h_steel", rot=(0, rad(-12), 0))
    m.box((0.12, 0.04, 0.12), (0.16, 0.06, z + 0.27), WL, bevel=0.02)
    hammer(m, 0.02, -0.22, z, rad(8))


def wb_tool(m):
    """Tool bench, 2x1: a vise on the bench, and tools hung on a board behind it."""
    z = bench(m, -0.94, 0.94)
    bx(m, (-0.90, 0.90), (0.28, 0.35), (z - 0.02, z + 0.72), WD, bevel=0.02)
    for x in (-0.84, 0.84):
        m.box((0.09, 0.09, 0.74), (x, 0.31, z + 0.35), WD)
    vise(m, -0.50, -0.04, z)
    for x, w, h, mk in ((-0.55, 0.07, 0.34, "h_steel"), (-0.30, 0.20, 0.10, "h_steel"), (0.05, 0.05, 0.40, WL),
                        (0.34, 0.30, 0.12, "h_steel"), (0.66, 0.08, 0.30, T)):
        m.box((w, 0.03, h), (x, 0.265, z + 0.44), mk, bevel=0.008)
    hammer(m, 0.30, -0.10, z, rad(-20))


def wb_part(m):
    """Parts bench, 2x1: an anvil at one end and a bench drill at the other."""
    z = bench(m, -0.94, 0.94)
    anvil(m, -0.50, 0.0, z)
    bx(m, (0.34, 0.66), (-0.14, 0.14), (z, z + 0.06), T, bevel=0.015)
    m.cyl(0.045, 0.62, (0.62, 0, z + 0.33), "h_lite", seg=8)
    bx(m, (0.30, 0.70), (-0.11, 0.11), (z + 0.50, z + 0.72), G, bevel=0.035)
    m.cyl(0.03, 0.20, (0.42, 0, z + 0.41), "h_steel", seg=8)
    m.cyl(0.015, 0.08, (0.42, 0, z + 0.27), "h_steel", seg=6, r2=0.03)
    bx(m, (0.32, 0.52), (-0.10, 0.10), (z + 0.14, z + 0.19), D, bevel=0.01)
    m.cyl(0.03, 0.14, (0.42, 0, z + 0.10), D, seg=8)


def wb_machine(m):
    """Machine bench, 2x1: a machine frame under assembly with its gear fitted, and a hoist standing
    over it."""
    z = bench(m, -0.94, 0.94)
    bx(m, (-0.52, 0.02), (-0.20, 0.20), (z, z + 0.30), "h_steel", bevel=0.035)
    gear(m, 0.15, 0.06, (-0.25, -0.225, z + 0.16), T, teeth=10)
    m.cyl(0.045, 0.09, (-0.25, -0.225, z + 0.16), "h_lite", seg=8, axis="Y")
    bx(m, (0.62, 0.74), (-0.06, 0.06), (z, z + 0.92), G, bevel=0.025)
    bx(m, (-0.30, 0.76), (-0.05, 0.05), (z + 0.84, z + 0.95), G, bevel=0.025)
    m.prism([(0.62, z + 0.55), (0.62, z + 0.66), (0.36, z + 0.86), (0.28, z + 0.86)], -0.03, 0.03, "Y", D)
    m.cyl(0.02, 0.26, (-0.24, 0, z + 0.71), "h_lite", seg=6)
    bx(m, (-0.29, -0.19), (-0.045, 0.045), (z + 0.50, z + 0.60), T, bevel=0.015)


def wb_cook(m):
    """Cooking bench, 2x1: a stove with a pot on it, a chopping board with a loaf, and a shelf of jars
    behind."""
    z = bench(m, -0.94, 0.94)
    bx(m, (-0.84, -0.20), (-0.28, 0.24), (z, z + 0.09), D, bevel=0.02)
    for x in (-0.68, -0.36):
        m.cyl(0.11, 0.02, (x, -0.02, z + 0.10), T, seg=10)
    pot(m, -0.68, -0.02, z + 0.10)
    bx(m, (0.10, 0.70), (-0.24, 0.12), (z, z + 0.04), WD, bevel=0.012)
    bx(m, (0.22, 0.54), (-0.14, 0.02), (z + 0.04, z + 0.15), "h_oil", bevel=0.035)
    m.box((0.30, 0.012, 0.10), (0.56, -0.06, z + 0.09), "h_steel", rot=(0, 0, rad(30)))
    bx(m, (-0.90, 0.90), (0.27, 0.35), (z - 0.02, z + 0.44), WD, bevel=0.02)
    bx(m, (-0.90, 0.90), (0.16, 0.35), (z + 0.40, z + 0.46), WL, bevel=0.015)
    for x, mk in ((-0.6, "h_red"), (-0.3, "h_oil"), (0.0, "h_paint"), (0.3, "h_cloth"), (0.6, "h_red")):
        m.cyl(0.07, 0.15, (x, 0.24, z + 0.535), mk, seg=8)
        m.cyl(0.055, 0.03, (x, 0.24, z + 0.625), D, seg=8)


def wb_elec(m):
    """Electrics bench, 2x1: a meter with a lit screen, a coil of copper wire, and a soldering iron in
    its stand."""
    z = bench(m, -0.94, 0.94)
    screen(m, -0.48, 0.08, z, w=0.46)
    m.cyl(0.15, 0.04, (0.20, 0.0, z + 0.02), D, seg=12)
    m.cyl(0.12, 0.16, (0.20, 0.0, z + 0.12), "h_copper", seg=12)
    m.cyl(0.15, 0.04, (0.20, 0.0, z + 0.22), D, seg=12)
    bx(m, (0.52, 0.76), (-0.10, 0.10), (z, z + 0.06), T, bevel=0.015)
    m.cyl(0.05, 0.16, (0.58, 0, z + 0.13), D, seg=8)
    m.cyl(0.022, 0.34, (0.66, 0, z + 0.20), "h_lite", seg=6, rot=(0, rad(55), 0))
    m.cyl(0.04, 0.16, (0.80, 0, z + 0.30), "h_red", seg=8, rot=(0, rad(55), 0))


def wb_furn(m):
    """Furniture bench, 2x1: a chair being made stands on the bench beside the plane and the boards
    it is being made from."""
    z = bench(m, -0.94, 0.94)
    for sx in SIDES:
        for sy in SIDES:
            m.box((0.055, 0.055, 0.30 if sy < 0 else 0.62), (-0.46 + sx * 0.13, sy * 0.13, z + (0.15 if sy < 0 else 0.31)), WL)
    bx(m, (-0.63, -0.29), (-0.17, 0.17), (z + 0.28, z + 0.34), WL, bevel=0.012)
    bx(m, (-0.62, -0.30), (0.10, 0.16), (z + 0.46, z + 0.62), WL, bevel=0.012)
    for k in range(3):
        m.box((0.60, 0.13, 0.035), (0.40, 0.06 - k * 0.012, z + 0.018 + k * 0.035), WL if k % 2 else WD)
    bx(m, (0.18, 0.44), (-0.26, -0.14), (z, z + 0.08), WD, bevel=0.015)
    m.box((0.06, 0.05, 0.10), (0.25, -0.20, z + 0.12), WD, bevel=0.015)
    m.box((0.05, 0.012, 0.09), (0.34, -0.20, z + 0.09), "h_steel", rot=(0, rad(-35), 0))


def wb_all(m):
    """All-in-one bench, 3x1: a long bench carrying a vise, an anvil, a meter and a stove with its pot,
    under a tool board."""
    z = bench(m, -1.44, 1.44)
    bx(m, (-1.40, 1.40), (0.28, 0.35), (z - 0.02, z + 0.70), WD, bevel=0.02)
    for x in (-1.34, 0.0, 1.34):
        m.box((0.09, 0.09, 0.72), (x, 0.31, z + 0.34), WD)
    for x, w, h, mk in ((-1.05, 0.07, 0.34, "h_steel"), (-0.80, 0.22, 0.10, "h_steel"), (-0.50, 0.05, 0.40, WL),
                        (0.45, 0.30, 0.12, "h_steel"), (0.78, 0.08, 0.30, T), (1.06, 0.18, 0.18, "h_steel")):
        m.box((w, 0.03, h), (x, 0.265, z + 0.44), mk, bevel=0.008)
    vise(m, -1.08, -0.04, z)
    anvil(m, -0.42, -0.02, z)
    screen(m, 0.34, 0.06, z, w=0.40)
    bx(m, (0.76, 1.34), (-0.26, 0.22), (z, z + 0.09), D, bevel=0.02)
    pot(m, 1.05, -0.02, z + 0.09)


free("campfire", (1, 1), campfire, items=False)
free("hand_furnace", (1, 1), hand_furnace, items=False)
free("chest", (1, 1), chest, items=False)
free("wb_basic", (1, 1), wb_basic, items=False)
free("wb_tool", (2, 1), wb_tool, items=False)
free("wb_part", (2, 1), wb_part, items=False)
free("wb_machine", (2, 1), wb_machine, items=False)
free("wb_cook", (2, 1), wb_cook, items=False)
free("wb_elec", (2, 1), wb_elec, items=False)
free("wb_furn", (2, 1), wb_furn, items=False)
free("wb_all", (3, 1), wb_all, items=False)
