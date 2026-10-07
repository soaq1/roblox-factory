# v2 conveyor pieces, redone to the section the new machines carry (d.SECTION: rails and bed in one
# piece, hairline arrows, a pale bolt on each rail's slope). Every piece ends in that same section,
# square to the cell's edge, so any piece meets any other, and any machine's mouth, without a step.
#
#   straight   1x1   west to east
#   corner     1x1   west to south (right) or west to north (left): the whole section swept round the
#                    cell's inner corner, so rails, bed and belt turn as one
#   ramp       2x1   west, low, to east, one cell higher, carried on two portal piers. An end that meets
#                    a flat belt is level there and eases into the slope; an end that meets another
#                    ramp keeps its slope, so a run of ramps is one straight climb (four variants).
#
# There is no open, rail-less belt: the developer dropped it (2026-10-07).
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


def ramp_profile(low, high):
    """How a ramp rises from x = -1 to x = 1: (height at x, pitch at x). An end marked True starts or
    finishes level, to meet a flat belt; an end marked False keeps its slope, to meet another ramp, so
    a run of ramps climbs in one straight line instead of rising and levelling at every joint."""
    e0, e1 = (EASE if low else 0.0), (EASE if high else 0.0)
    slope = RISE / (2.0 - (e0 + e1) / 2)

    def lift(x):
        u = x + 1.0
        if u < e0:
            return slope * u * u / (2 * e0)
        if u > 2.0 - e1:
            v = 2.0 - u
            return RISE - slope * v * v / (2 * e1)
        return slope * (u - e0 / 2)

    def pitch(x):
        u, f = x + 1.0, 1.0
        if e0 and u < e0:
            f = u / e0
        if e1 and u > 2.0 - e1:
            f = (2.0 - u) / e1
        return math.atan(slope * f)

    return lift, pitch


def ramp(m, low=True, high=True, flow=1):
    """Ramp, 2x1: from the west, low, to the east, one cell higher. Which ends are level depends on
    what it meets (see ramp_profile): level against a flat belt, sloping on against another ramp.
    It stands on two portal piers, a leg under each rail and a tie between them, the belt's underside
    open between the legs."""
    lift_at, pitch_at = ramp_profile(low, high)
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
            m.prism([(xc - 0.17, 0.02), (xc + 0.17, 0.02), (xc + 0.10, lift_at(xc + 0.10) + 0.02), (xc - 0.10, lift_at(xc - 0.10) + 0.02)],
                    ya, yb, "Y", T)
            ya, yb = sorted((s * 0.25, s * 0.49))
            m.prism([(xc - 0.20, 0.0), (xc + 0.20, 0.0), (xc + 0.18, 0.06), (xc - 0.18, 0.06)], ya, yb, "Y", TD)   # foot
        zt = lift_at(xc) * 0.55
        m.prism([(xc - 0.05, zt - 0.05), (xc + 0.05, zt - 0.05), (xc + 0.035, zt + 0.05), (xc - 0.035, zt + 0.05)], -0.28, 0.28, "Y", ST)   # tie


def ramp_start(m):
    """The first ramp of a run: level where it leaves the flat belt, sloping on at the top."""
    ramp(m, True, False)


def ramp_mid(m):
    """A ramp between two ramps: one straight slope."""
    ramp(m, False, False)


def ramp_end(m):
    """The last ramp of a run: sloping on from the ramp below, level where it meets the flat belt."""
    ramp(m, False, True)
