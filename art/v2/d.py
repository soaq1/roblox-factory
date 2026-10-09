# v2 shared parts for the catalog set: the conveyor, the forms a machine can take, and wall fittings.
#
# Forms (units are grid cells; x runs the way the items go):
#   through   3x1. A level conveyor runs under the body, in at the west end and out at the east
#             (base.foundation_d). A machine that takes a second material, or gives a second product,
#             also has a mouth in each side wall of the body; either side will do.
#   out       2x1. The body stands on the west cell and its product leaves along the east cell.
#   in        2x1. The mirror of it: the belt brings material in from the west.
#   junction  1x1. A low block with a mouth flush in each face that is used.
#   free      anything that does not touch a belt.
import math
from contextlib import contextmanager
from mathutils import Matrix
import factorykit as fk
from .base import (rad, G, T, TD, W, D, SLIT, R, RD, SIDES, BH, BZ, BX, BY, RAIL_D, gear, side_pipe, side_panel,
                   octa, oct_ring, bx, foundation_d, foot_beams, foot_springs, foot_hearth, foot_anchor, foot_drain,
                   foot_bin, bprism, collar, BOLT, BOLT_AT, BOLT_LEAN, WEB, offset_closed, loft_x)
from .kit import arch_pts, machine2
from .hero import sunk_frame
from .forms import frustum

fk.PAL.update({"h_water": "#5aa6c8", "h_wood": "#8f6d47", "h_wood_l": "#cfb388", "h_paint": "#2f9e94",
               "h_mix": "#8b877c", "h_stone": "#a7a399", "h_copper": "#c88748", "h_oil": "#c9a227",
               "h_cloth": "#d3c29c", "h_gem": "#58c7d4", "h_ore": "#b5683c", "h_coal": "#2c2c30",
               "h_pcb": "#2f7d54", "h_leaf": "#5f9a4a", "h_solar": "#27405f", "h_brick": "#9a5f4a",
               "h_red": "#c2483c", "h_core": "#7fe3ff", "h_glass": "#7d9cb0"})
fk.EMIT.update({"h_core": 2.2})
K = 1.0 / math.cos(math.pi / 8)
BED = BZ - 0.03
SECTION = [(-y, z) for y, z in reversed(RAIL_D)] + [(-BH, BED), (BH, BED)] + list(RAIL_D)
RAILPOLY = list(RAIL_D) + [(BH, 0.0)]
DIRS = {"W": ((-0.5, 0.0), (1, 0)), "E": ((0.5, 0.0), (-1, 0)), "S": ((0.0, -0.5), (0, 1)), "N": ((0.0, 0.5), (0, -1))}


@contextmanager
def frame(m, origin, inward):
    """Build in a port's own frame: x runs from the footprint's edge into the machine, y across the
    port. The matrix holds only 0 and +-1, so ports facing each other are exact mirror images."""
    ix, iy = inward
    m.stack.append(m.stack[-1] @ Matrix(((ix, -iy, 0, origin[0]), (iy, ix, 0, origin[1]), (0, 0, 1, 0), (0, 0, 0, 1))))
    yield
    m.stack.pop()


def chev(m, x, flow=1, z=BZ):
    """A pair of hairline chevrons on the belt, pointing the way it runs."""
    for dx in (-0.035, 0.035):
        for s in SIDES:
            m.box((0.011, 0.30, 0.004), (x + dx, s * 0.14, z + 0.002), "h_line", rot=flow * s * 0.36)


def buttress(m, x):
    """A pale bolt head on the sloping wall of each rail. (It replaced a pointed brace; the name is kept
    for the callers.) The head lies square to the wall's slope."""
    for s in SIDES:
        m.cyl(BOLT[0], BOLT[1], (x, s * BOLT_AT[0], BOLT_AT[1]), "h_lite", seg=6, axis="Y", rot=(s * BOLT_LEAN, 0, 0))


def bed(m, x0, x1):
    """Rails and bed in one piece from x0 to x1, and the darker strip let into each rail's web."""
    m.prism(SECTION, x0, x1, "X", R)
    for s in SIDES:
        m.prism([(s * y, z) for y, z in WEB], x0, x1, "X", RD)


def run(m, x0, x1, flow=1, braces=()):
    """A length of conveyor: rails and bed in one piece, the belt, its arrows, and a bolt at each place
    listed in `braces`."""
    bed(m, x0, x1)
    m.box((x1 - x0, BH * 2, 0.03), ((x0 + x1) / 2, 0, BZ - 0.015), "h_belt")
    n = max(1, round((x1 - x0) / 0.375))
    for i in range(n):
        chev(m, x0 + (i + 0.5) * (x1 - x0) / n, flow)
    for x in braces:
        buttress(m, x)


def cover(m, x0, d, sole=True, n=4, wide=False):
    """The folding cover over a tunnel mouth at the body's end x0, opening toward d. A collar hugs each
    rail behind the end frame, which stands on the rail itself; with sole=False the machine supplies
    its own. `n` is the number of folds (more folds, a deeper mouth: the developer wants every mouth,
    of whatever grade, to look as if things go deep into it). With wide=True the folds are as wide as
    the belt's rails, so that the rails run into them and nothing has to hug the rails beside them.
    Returns how far out the cover reaches."""
    x0 += d * 0.004                                           # a hair clear of the belt's own end, so no two faces share a plane there
    g = 2 * (BH - 0.305)                                      # the covers grow with the belt
    w1, w2, w3 = (0.96, 0.90, 0.988) if wide else (0.84 + g, 0.77 + g, 0.88 + g)
    folds = [(0.042, w1, 0.77, BH + 0.01, R), (0.026, w2, 0.735, BH + 0.03, RD)] * n + [(0.066, w3, 0.79, BH + 0.01, R)]
    depth = sum(f[0] for f in folds)
    if sole:
        collar(m, *sorted((x0, x0 + d * depth)))
    px = x0
    for th, w, tp, hw, mk in folds:
        a, b = sorted((px, px + d * th))
        m.prism(arch_pts(w, tp, hole_top=tp - 0.11, hw=hw, c=0.085, ci=0.035), a, b, "X", mk)
        px += d * th
    m.box((0.02, 2 * BH + 0.01, 0.694 - BZ), (x0 + d * 0.012, 0, (0.706 + BZ) / 2), SLIT)        # the dark of the tunnel, from the belt up
    return depth


def block(m, top=0.82):
    """The body block with its base course."""
    bx(m, (-BX - 0.02, BX + 0.02), (-BY - 0.02, BY + 0.02), (0.262, 0.345), G, bevel=0.03)
    bx(m, (-BX, BX), (-BY, BY), (0.30, top), G, bevel=0.028)


def stub_form(m, top=0.82, flow=1, fit=None):
    """A body with a conveyor on one side only. Drawn with the body at the origin and the belt on the
    cell to its east; `flow` is +1 when the belt carries the product away, -1 when it brings material.
    The body stands on a dark plinth. `fit(m, d, yp, z)` puts a fitting on the panel of each side wall;
    the end wall away from the belt has a sunk service door."""
    run(m, 0.2, 1.5, flow, braces=(1.0, 4 / 3))
    bx(m, (-0.50, 0.50), (-0.50, 0.50), (0.0, 0.16), T, bevel=0.045)
    bx(m, (-BX - 0.02, BX + 0.02), (-BY - 0.02, BY + 0.02), (0.13, 0.25), G, bevel=0.03)
    bx(m, (-BX, BX), (-BY, BY), (0.20, top), G, bevel=0.028)
    cover(m, BX, 1)
    for d in SIDES:
        yp = side_panel(m, d, w=0.56, h=0.34, z=top - 0.30)
        if fit:
            fit(m, d, yp, top - 0.30)
    m.box((0.04, 0.50, 0.42), (-BX - 0.012, 0, top - 0.33), G, bevel=0.028)       # service door on the end wall
    m.box((0.012, 0.012, 0.36), (-BX - 0.034, 0, top - 0.33), SLIT)
    for s in SIDES:
        m.box((0.02, 0.03, 0.12), (-BX - 0.038, s * 0.05, top - 0.33), T)
    return top


def mouth(m, side, out=False, tall=0.74):
    """A mouth flush in a face of a body whose wall stands just inside the cell's edge: a short sill
    of conveyor, an arch round the opening, darkness inside."""
    origin, inward = DIRS[side]
    with frame(m, origin, inward):
        bed(m, 0.0, 0.08)
        m.box((0.08, BH * 2, 0.03), (0.04, 0, BZ - 0.015), "h_belt")
        m.prism(arch_pts(0.82 + 2 * (BH - 0.305), tall, hole_top=tall - 0.12, hw=BH + 0.01, c=0.085, ci=0.035), 0.0, 0.075, "X", R)
        m.box((0.02, 2 * BH + 0.01, tall - 0.12 - BZ), (0.068, 0, (tall - 0.12 + BZ) / 2), SLIT)
        k = -1 if out else 1
        m.prism([(-0.07, tall - 0.085 + k * 0.03), (0.07, tall - 0.085 + k * 0.03), (0.0, tall - 0.085 - k * 0.03)],
                -0.004, 0.079, "X", "h_line")                 # an arrowhead on the arch: down is in, up is out


# ---------------------------------------- registering ----------------------------------------
def through(key, body, foot=None, sides=None, **kw):
    """Register a 3x1 through machine. `sides` is None, "in" (a second material at either side wall) or
    "out" (a second product at either side wall)."""
    ports = None
    if sides:
        ports = (("W", "in", 0), ("S", sides, 0), ("N", sides, 0), ("E", "out", 0))

    def build(m):
        Z = foundation_d(m, foot=(lambda m: None) if sides else foot)
        if sides:
            for s in "SN":
                mouth(m, s, out=(sides == "out"))
        body(m, Z)
    return machine2(key, (3, 1), ports, **kw)(build)


def stub(key, body, flow=1, top=0.82, fit=None, **kw):
    """Register a 2x1 machine with a belt on one side: flow +1 gives out to the east, -1 takes in from
    the west."""
    def build(m):
        with m.at((-0.5 * flow, 0, 0), 0.0 if flow > 0 else math.pi):
            body(m, stub_form(m, top, flow, fit))
    ports = (("E", "out", 0),) if flow > 0 else (("W", "in", 0),)
    return machine2(key, (2, 1), ports, **kw)(build)


def free(key, size, fn, ports=(), **kw):
    return machine2(key, size, ports, **kw)(fn)


# ---------------------------------------- wall fittings ----------------------------------------
def panel(m, d, Z, w=0.50, h=0.30, dz=-0.26):
    """The raised panel on a side wall. Returns its face y and its centre height."""
    return side_panel(m, d, w=w, h=h, z=Z + dz), Z + dz


def lamps(m, d, yp, z, cols=("h_paint", "h_glow", "h_lite")):
    for i, c in enumerate(cols):
        x = (i - 1) * 0.15
        m.cyl(0.058, 0.03, (x, yp + d * 0.012, z), T, seg=10, axis="Y")
        m.cyl(0.04, 0.012, (x, yp + d * 0.006, z), c, seg=10, axis="Y")


def crank(m, d, yp, x, z):
    m.cyl(0.078, 0.02, (x, yp + d * 0.008, z), T, seg=10, axis="Y")
    m.box((0.20, 0.014, 0.05), (x + 0.07, yp + d * 0.022, z), "h_lite")
    m.cyl(0.034, 0.03, (x + 0.15, yp + d * 0.017, z), D, seg=8, axis="Y")
    m.cyl(0.03, 0.03, (x, yp + d * 0.017, z), D, seg=8, axis="Y")


def hatch(m, d, yp, x, z, w=0.34, h=0.22):
    m.box((w, 0.02, h), (x, yp + d * 0.008, z), D, bevel=0.006)
    for sz in SIDES:
        m.box((0.06, 0.028, 0.04), (x - w / 2 + 0.01, yp + d * 0.012, z + sz * h * 0.28), T)
    m.box((0.04, 0.028, 0.11), (x + w / 2 - 0.05, yp + d * 0.014, z), T)


def lever(m, d, yp, x, z):
    m.box((0.28, 0.016, 0.20), (x, yp + d * 0.006, z), T, bevel=0.004)
    m.box((0.21, 0.008, 0.032), (x, yp + d * 0.015, z + 0.045), SLIT)
    m.box((0.04, 0.016, 0.18), (x + 0.045, yp + d * 0.023, z - 0.005), "h_lite", rot=(0, rad(18), 0))
    m.cyl(0.034, 0.03, (x + 0.075, yp + d * 0.017, z + 0.08), D, seg=8, axis="Y")


def drawers(m, d, yp, x, z, w=0.44):
    for sz in SIDES:
        m.box((w, 0.018, 0.11), (x, yp + d * 0.008, z + sz * 0.063), D, bevel=0.005)
        m.box((0.17, 0.016, 0.024), (x, yp + d * 0.022, z + sz * 0.063), "h_lite")


def vent_round(m, d, yp, x, z, r=0.115):
    m.cyl(r, 0.03, (x, yp + d * 0.012, z), T, seg=12, axis="Y")
    m.cyl(r * 0.78, 0.012, (x, yp + d * 0.005, z), SLIT, seg=12, axis="Y")
    for i in (-1, 0, 1):
        m.box((r * 1.5 * (1 - abs(i) * 0.28), 0.02, 0.022), (x, yp + d * 0.014, z + i * 0.05), G)


def peep(m, d, yp, x, z, r=0.105):
    m.cyl(r, 0.03, (x, yp + d * 0.012, z), T, seg=12, axis="Y")
    m.cyl(r * 0.74, 0.012, (x, yp + d * 0.004, z), "h_glow", seg=12, axis="Y")
    m.box((r * 1.5, 0.018, 0.024), (x, yp + d * 0.02, z), TD)
    m.box((0.024, 0.018, r * 1.5), (x, yp + d * 0.02, z), TD)


def strip(m, d, yp, z, mk, w=0.34, h=0.09):
    sunk_frame(m, d, yp, 0, z, w, h, mk=T)
    m.box((w, 0.008, h), (0, yp + d * 0.002, z), mk)


def neck(m, Z, hx=0.44, hy=0.38, h=0.07, mk=G):
    bx(m, (-hx, hx), (-hy, hy), (Z - 0.02, Z + h), mk, bevel=0.03)
