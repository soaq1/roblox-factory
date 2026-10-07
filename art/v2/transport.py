# v2 transport: the conveyor itself, the junctions that part and join its flow, and storage.
import math
from mathutils import Matrix
from .d import *          # noqa: F401,F403
from . import belts
from .d import through, free, run, chev, buttress, mouth, panel, lamps, hatch, neck, frame, DIRS, SECTION, RAILPOLY, BED, K

W_IN, E_OUT = ("W", "in", 0), ("E", "out", 0)


def belt(m):
    """Straight belt, 1x1. The conveyor pieces live in belts.py; these keep the catalog's names."""
    belts.straight(m)


def belt_corner(m):
    """Corner belt, 1x1: in from the west, out to the south, the whole section swept round the corner."""
    belts.corner_right(m)


def belt_ramp(m):
    """Ramp, 2x1: in low at the west, out one cell higher at the east, level at both ends, on two piers."""
    belts.ramp(m)


def junction(m, ins, outs, top=0.80):
    """The body of a junction: a block on a plinth with a mouth in each face that is used, and a well
    in its top where the belt floor and the vanes that steer the flow can be seen."""
    bx(m, (-0.50, 0.50), (-0.50, 0.50), (0.0, 0.11), T, bevel=0.035)
    bx(m, (-0.425, 0.425), (-0.425, 0.425), (0.07, top), G, bevel=0.04)
    for s in ins:
        mouth(m, s, False, tall=0.70)
    for s in outs:
        mouth(m, s, True, tall=0.70)
    for s in "WESN":                                          # a face with no mouth carries a sunk service panel
        if s not in ins + outs:
            origin, inward = DIRS[s]
            with frame(m, origin, inward):
                m.box((0.04, 0.56, 0.36), (0.063, 0, 0.44), G, bevel=0.028)
                m.box((0.012, 0.40, 0.04), (0.04, 0, 0.50), SLIT)
                m.box((0.012, 0.40, 0.04), (0.04, 0, 0.40), SLIT)
    for s in SIDES:
        bx(m, (-0.40, 0.40), tuple(sorted((s * 0.30, s * 0.40))), (top - 0.02, top + 0.06), D, bevel=0.02)
        bx(m, tuple(sorted((s * 0.30, s * 0.40))), (-0.40, 0.40), (top - 0.02, top + 0.06), D, bevel=0.02)
    m.box((0.62, 0.62, 0.02), (0, 0, top - 0.005), "h_belt")
    return top


def vane(m, x, y, ang, z, L=0.34):
    m.box((L, 0.05, 0.07), (x, y, z + 0.04), T, rot=ang)


def splitter(m):
    """Splitter: one flow in, two out. A vane on a pivot swings between the two ways out."""
    z = junction(m, "W", "ES")
    vane(m, 0.06, -0.06, rad(-22), z)
    m.cyl(0.07, 0.10, (-0.09, 0.0, z + 0.05), "h_lite", seg=8)
    chev(m, -0.18, z=z + 0.005)


def merger(m):
    """Merger: two flows in, one out. Two fixed vanes draw both into the one way out."""
    z = junction(m, "WN", "E")
    vane(m, 0.02, 0.13, rad(-28), z, L=0.36)
    vane(m, 0.02, -0.13, rad(28), z, L=0.36)
    chev(m, 0.20, z=z + 0.005)


def sorter(m):
    """Sorter: an eye on a bridge over the well reads each item, and a vane sends the chosen kind out
    the side."""
    z = junction(m, "W", "ES")
    vane(m, 0.10, -0.05, rad(-30), z, L=0.30)
    for s in SIDES:
        bx(m, (-0.20, -0.08), tuple(sorted((s * 0.30, s * 0.42))), (z + 0.04, z + 0.34), G, bevel=0.02)
    bx(m, (-0.21, -0.07), (-0.43, 0.43), (z + 0.30, z + 0.42), G, bevel=0.025)
    m.cyl(0.085, 0.05, (-0.14, 0, z + 0.28), T, seg=10)
    m.cyl(0.055, 0.02, (-0.14, 0, z + 0.25), "h_core", seg=10)


def magsep(m):
    """Magnetic separator: a horseshoe magnet hangs from a bridge over the well and pulls the iron out
    to the side."""
    z = junction(m, "W", "ES")
    for s in SIDES:
        bx(m, (-0.07, 0.07), tuple(sorted((s * 0.30, s * 0.42))), (z + 0.04, z + 0.50), G, bevel=0.02)
    bx(m, (-0.08, 0.08), (-0.43, 0.43), (z + 0.46, z + 0.58), G, bevel=0.025)
    bx(m, (-0.10, 0.10), (-0.20, 0.20), (z + 0.30, z + 0.47), "h_red", bevel=0.03)
    for s in SIDES:
        bx(m, (-0.10, 0.10), tuple(sorted((s * 0.09, s * 0.20))), (z + 0.10, z + 0.32), "h_red", bevel=0.0)
        bx(m, (-0.10, 0.10), tuple(sorted((s * 0.09, s * 0.20))), (z + 0.08, z + 0.15), "h_lite", bevel=0.0)


def pusher(m):
    """Pusher, 1x1: the belt runs straight through; a ram on the north side shoves an item off it and
    out the south side through a gap in the rail."""
    m.prism(RAILPOLY, -0.5, 0.5, "X", R)
    for a, b in ((-0.5, -0.33), (0.33, 0.5)):
        m.prism([(-y, z) for y, z in RAILPOLY], a, b, "X", R)
    m.box((1.0, 2 * BH, BED), (0, 0, BED / 2), R)
    m.box((0.66, 0.5 - BH, BED), (0, (-0.5 - BH) / 2, BED / 2), R)
    m.box((1.0, 2 * BH, 0.03), (0, 0, BZ - 0.015), "h_belt")
    m.box((0.66, 0.5 - BH, 0.03), (0, (-0.5 - BH) / 2, BZ - 0.015), "h_belt")
    chev(m, -0.30)
    chev(m, 0.32)
    with m.at((0, -0.36, 0), rad(-90)):
        chev(m, 0.0)
    bx(m, (-0.30, 0.30), (0.30, 0.50), (0.0, 0.70), G, bevel=0.04)
    m.cyl(0.11 * K, 0.10, (0, 0.27, 0.50), D, seg=8, axis="Y", rot=(0, rad(22.5), 0))
    m.cyl(0.05, 0.12, (0, 0.20, 0.50), "h_steel", seg=8, axis="Y")
    bx(m, (-0.27, 0.27), (0.10, 0.16), (0.33, 0.66), T, bevel=0.02)


def storage(m, Z):
    """Storage: a tall bin with a barred window in each side, the crates stacked inside showing through
    it, under a ribbed lid."""
    for d in SIDES:
        yp, z = panel(m, d, Z, w=0.56)
        lamps(m, d, yp, z, cols=("h_paint", "h_paint", "h_lite"))
    bx(m, (-0.46, 0.46), (-0.41, 0.41), (Z - 0.02, Z + 0.70), G, bevel=0.035)
    for d in SIDES:
        m.box((0.64, 0.012, 0.44), (0, d * 0.412, Z + 0.34), SLIT)
        for x, zz, w in ((-0.19, Z + 0.22, 0.20), (0.05, Z + 0.22, 0.22), (-0.10, Z + 0.42, 0.24), (0.19, Z + 0.44, 0.16)):
            m.box((w, 0.012, 0.18), (x, d * 0.418, zz), "h_wood_l")
        for sz in (-1, 0, 1):
            m.box((0.70, 0.03, 0.035), (0, d * 0.424, Z + 0.34 + sz * 0.22), D)
        for sx in SIDES:
            m.box((0.035, 0.03, 0.47), (sx * 0.335, d * 0.424, Z + 0.34), D)
    bx(m, (-0.42, 0.42), (-0.37, 0.37), (Z + 0.68, Z + 0.76), D, bevel=0.02)
    for x in (-0.24, 0.0, 0.24):
        bx(m, (x - 0.05, x + 0.05), (-0.39, 0.39), (Z + 0.74, Z + 0.80), G, bevel=0.015)


def packer(m, Z):
    """Packer: a carton sits on a roller bed under an arch that carries the reel of tape that seals
    it."""
    for d in SIDES:
        yp, z = panel(m, d, Z, w=0.48)
        hatch(m, d, yp, 0, z)
        bx(m, (-0.08, 0.08), tuple(sorted((d * 0.30, d * 0.42))), (Z - 0.02, Z + 0.76), G, bevel=0.025)
    neck(m, Z, 0.46, 0.40, 0.05)
    bx(m, (-0.42, 0.42), (-0.25, 0.25), (Z + 0.03, Z + 0.10), D, bevel=0.015)
    for i in range(7):
        m.cyl(0.035, 0.46, (-0.36 + i * 0.12, 0, Z + 0.12), "h_lite", seg=8, axis="Y")
    m.box((0.34, 0.34, 0.26), (0, 0, Z + 0.285), "h_wood_l", bevel=0.012)
    m.box((0.345, 0.07, 0.265), (0, 0, Z + 0.285), "h_cloth")
    bx(m, (-0.09, 0.09), (-0.43, 0.43), (Z + 0.70, Z + 0.83), G, bevel=0.03)
    m.cyl(0.15, 0.09, (0, 0, Z + 0.96), T, seg=12, axis="Y")
    m.cyl(0.06, 0.11, (0, 0, Z + 0.96), "h_lite", seg=8, axis="Y")
    for d in SIDES:
        bx(m, (-0.05, 0.05), tuple(sorted((d * 0.06, d * 0.11))), (Z + 0.81, Z + 0.98), G, bevel=0.0)


def vending(m):
    """Vending machine, 1x1: a cabinet with a glazed front showing the goods on its shelves, a coin
    panel beside the glass and a tray at the bottom."""
    bx(m, (-0.44, 0.44), (-0.36, 0.36), (0.0, 0.10), T, bevel=0.03)
    bx(m, (-0.41, 0.41), (-0.33, 0.33), (0.06, 1.55), G, bevel=0.04)
    bx(m, (-0.42, 0.42), (-0.34, 0.34), (1.36, 1.50), D, bevel=0.03)
    for s in SIDES:
        y = s * 0.332
        m.box((0.50, 0.012, 0.74), (-0.09, y, 0.92), "h_glass")
        for k in range(3):
            m.box((0.50, 0.03, 0.03), (-0.09, y, 0.70 + k * 0.22), D)
            for j, mk in enumerate(("h_red", "h_oil", "h_paint")):
                m.box((0.09, 0.02, 0.13), (-0.24 + j * 0.15, y, 0.795 + k * 0.22 - 0.22 * (k == 2) * 0 - 0.0), mk)
        for sz in SIDES:
            m.box((0.56, 0.035, 0.035), (-0.09, y + s * 0.006, 0.92 + sz * 0.385), T)
        for sx in SIDES:
            m.box((0.035, 0.035, 0.80), (-0.09 + sx * 0.265, y + s * 0.006, 0.92), T)
        m.box((0.14, 0.02, 0.46), (0.29, y + s * 0.004, 1.02), T, bevel=0.004)
        m.box((0.07, 0.012, 0.02), (0.29, y + s * 0.016, 1.12), SLIT)
        m.cyl(0.03, 0.02, (0.29, y + s * 0.014, 0.94), "h_lite", seg=8, axis="Y")
        m.box((0.60, 0.012, 0.18), (-0.04, y, 0.32), SLIT)
        m.box((0.66, 0.04, 0.035), (-0.04, y + s * 0.008, 0.215), T)


free("belt", (1, 1), belt, items=False)
free("belt_corner", (1, 1), belt_corner, items=False)
free("belt_ramp", (2, 1), belt_ramp, items=False)
free("splitter", (1, 1), splitter, ports=(W_IN, E_OUT, ("S", "out", 0)), items=False)
free("merger", (1, 1), merger, ports=(W_IN, ("N", "in", 0), E_OUT), items=False)
free("sorter", (1, 1), sorter, ports=(W_IN, E_OUT, ("S", "out", 0)), items=False)
free("magsep", (1, 1), magsep, ports=(W_IN, E_OUT, ("S", "out", 0)), items=False)
free("pusher", (1, 1), pusher, ports=(W_IN, E_OUT, ("S", "out", 0)), items=False)
through("storage", storage, foot_beams)
through("packer", packer, foot_beams)
free("vending", (1, 1), vending, items=False)
