# v2 conveyor pieces, redone to the section the new machines carry (d.SECTION: rails and bed in one
# piece, hairline arrows, a pale bolt on each rail's slope). Every piece ends in that same section,
# square to the cell's edge, so any piece meets any other, and any machine's mouth, without a step.
#
#   straight   1x1   west to east
#   corner     1x1   west to south (right) or west to north (left): the whole section swept round the
#                    cell's inner corner, so rails, bed and belt turn as one
#   ramp       2x1   west, low, to east, one cell higher: level where it meets its neighbours at both
#                    ends, easing into the slope between, carried on two portal piers
#   open       1x1   no rails: the bed's shoulders lie level with the belt so things can roll on from
#                    the side
import math
import bmesh
from mathutils import Matrix
from .d import *          # noqa: F401,F403
from .d import run, chev, SECTION, BED, K
from .base import BOLT

ST = "h_steel"

ARC = 8                   # facets in a quarter turn
BELT = [(-BH, BED), (BH, BED), (BH, BZ), (-BH, BZ)]           # the belt itself, lying on the bed


def loft(m, rings, mk):
    """One closed piece through a row of outlines (each a list of 3D points, all of one length)."""
    bm = bmesh.new()
    rows = [[bm.verts.new(p) for p in ring] for ring in rings]
    k = len(rows[0])
    for a, b in zip(rows, rows[1:]):
        for j in range(k):
            bm.faces.new((a[j], a[(j + 1) % k], b[(j + 1) % k], b[j]))
    bm.faces.new(rows[0])
    bm.faces.new(rows[-1])
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-5)     # where a corner's inner rail closes to a point
    m._add(bm, mk)


def bolt(m):
    """One pale bolt head on the slope of the rail on the left of the way the belt runs, built in a
    frame whose x runs along the belt."""
    m.cyl(BOLT[0], BOLT[1], (0, 0.4356, 0.1678), "h_lite", seg=6, axis="Y", rot=(rad(21.7), 0, 0))


def straight(m):
    """Straight belt, 1x1."""
    run(m, -0.5, 0.5, braces=(-1 / 3, 0.0, 1 / 3))


def corner(m, turn=-1):
    """Corner belt, 1x1: in from the west; out to the south (turn = -1, a right turn) or to the north
    (turn = +1). The section is swept round the cell's inner corner, so the outer rail is one curve and
    the inner rail closes into a round post."""
    def at(th, across, z):                                    # a point of the section, th degrees round from the entry
        a = rad(90 - th)
        r = 0.5 + across
        return (-0.5 + r * math.cos(a), -turn * (-0.5 + r * math.sin(a)), z)

    steps = [90.0 * i / ARC for i in range(ARC + 1)]
    loft(m, [[at(th, y, z) for y, z in SECTION] for th in steps], R)
    loft(m, [[at(th, y, z) for y, z in BELT] for th in steps], "h_belt")
    for th in (22.5, 67.5):                                   # arrows, turning with the belt
        x, y, _ = at(th, 0.0, 0.0)
        with m.at((x, y, 0), rad(turn * th)):
            chev(m, 0.0)
    for th in (22.5, 45.0, 67.5):                             # bolts on the outer rail
        x, y, _ = at(th, 0.0, 0.0)
        with m.at((x, y, 0), rad(turn * th) + (0.0 if turn < 0 else math.pi)):
            bolt(m)


def corner_right(m):
    corner(m, -1)


def corner_left(m):
    corner(m, 1)


RISE, EASE = 1.0, 0.30
SLOPE = RISE / (2.0 - EASE)


def lift_at(x):
    """How high the ramp stands at x (from -1 to 1): level at both ends, a straight slope between."""
    u = x + 1.0
    if u < EASE:
        return SLOPE * u * u / (2 * EASE)
    if u > 2.0 - EASE:
        v = 2.0 - u
        return RISE - SLOPE * v * v / (2 * EASE)
    return SLOPE * (u - EASE / 2)


def pitch_at(x):
    u = x + 1.0
    return math.atan(SLOPE * min(1.0, u / EASE, (2.0 - u) / EASE))


def ramp(m, flow=1):
    """Ramp, 2x1: from the west, low, to the east, one cell higher. Its two ends are level, so the rails
    run on from a neighbour's without a kink. It stands on two portal piers, a leg under each rail and
    a tie between them, the belt's underside open between the legs."""
    n = 24
    xs = [-1.0 + 2.0 * i / n for i in range(n + 1)]
    loft(m, [[(x, y, z + lift_at(x)) for y, z in SECTION] for x in xs], R)
    loft(m, [[(x, y, z + lift_at(x)) for y, z in BELT] for x in xs], "h_belt")

    def on_slope(x):                                          # a frame lying on the ramp at x
        return m.stack[-1] @ Matrix.Translation((x, 0, lift_at(x))) @ Matrix.Rotation(-pitch_at(x), 4, "Y")

    for x in (-0.82, -0.41, 0.0, 0.41, 0.82):
        m.stack.append(on_slope(x))
        chev(m, 0.0, flow)
        m.stack.pop()
    for x in (-0.62, -0.22, 0.42):
        m.stack.append(on_slope(x))
        bolt(m)
        m.stack.append(m.stack[-1] @ Matrix.Rotation(math.pi, 4, "Z"))
        bolt(m)
        m.stack.pop()
        m.stack.pop()
    for xc in (0.10, 0.80):                                   # piers
        for s in SIDES:
            ya, yb = sorted((s * 0.27, s * 0.47))
            m.prism([(xc - 0.17, 0.0), (xc + 0.17, 0.0), (xc + 0.10, lift_at(xc + 0.10) + 0.02), (xc - 0.10, lift_at(xc - 0.10) + 0.02)],
                    ya, yb, "Y", T)
            ya, yb = sorted((s * 0.25, s * 0.49))
            m.prism([(xc - 0.20, 0.0), (xc + 0.20, 0.0), (xc + 0.18, 0.06), (xc - 0.18, 0.06)], ya, yb, "Y", TD)   # foot
        zt = lift_at(xc) * 0.55
        m.prism([(xc - 0.05, zt - 0.05), (xc + 0.05, zt - 0.05), (xc + 0.035, zt + 0.05), (xc - 0.035, zt + 0.05)], -0.28, 0.28, "Y", ST)   # tie


OPEN_SIDE = [(BH, BZ), (0.352, BZ), (0.374, BZ - 0.022), (0.474, 0.055), (0.50, 0.055), (0.50, 0.0)]
OPEN = [(-y, z) for y, z in reversed(OPEN_SIDE)] + [(-BH, BED), (BH, BED)] + list(OPEN_SIDE)


def open_belt(m):
    """Open belt, 1x1: no rails. The bed's shoulders lie level with the belt and slope away to the same
    foot as a railed belt's, so the foot and the belt run on unbroken into a neighbour."""
    m.prism(OPEN, -0.5, 0.5, "X", R)
    m.box((1.0, BH * 2, 0.03), (0, 0, BZ - 0.015), "h_belt")
    for x in (-1 / 3, 0.0, 1 / 3):
        chev(m, x)
        with m.at((x, 0, 0)):
            bolt(m)
            with m.at((0, 0, 0), math.pi):
                bolt(m)
