# v2 conveyor pieces, redone to the section the new machines carry (d.SECTION: rails and bed in one
# piece, hairline arrows, a pale bolt on each rail's slope). Every piece ends in that same section,
# square to the cell's edge, so any piece meets any other, and any machine's mouth, without a step.
#
#   straight   1x1   west to east
#   corner     1x1   west to south (right) or west to north (left): the whole section swept round the
#                    cell's inner corner, so rails, bed and belt turn as one
#   ramp       2x1   west, low, to east, one cell higher, on two slim trestles. An end that meets a flat
#                    belt is level there and eases into the slope; an end that meets another ramp
#                    keeps its slope, so a run of ramps is one straight climb (four variants, and one
#                    without trestles for stacking).
#   ramp down  2x1   the same going the other way: west, high, to east, one cell lower.
#
# There is no open, rail-less belt: the developer dropped it (2026-10-07).
import math
import bmesh
from mathutils import Matrix
from .d import *          # noqa: F401,F403
from .d import run, chev, SECTION, BED, K
from .base import BOLT, BOLT_AT, BOLT_LEAN, WEB

ST = "h_steel"

ARC = 12                  # facets in a quarter turn
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
    m.cyl(BOLT[0], BOLT[1], (0, BOLT_AT[0], BOLT_AT[1]), "h_lite", seg=6, axis="Y", rot=(BOLT_LEAN, 0, 0))


def straight(m):
    """Straight belt, 1x1."""
    run(m, -0.5, 0.5, braces=(-1 / 3, 0.0, 1 / 3))


SQUARE = 3.2             # how square a corner's outer rail turns: 2 is a quarter circle, larger is squarer


def corner(m, turn=-1, square=None):
    """Corner belt, 1x1: in from the west; out to the south (turn = -1, a right turn) or to the north
    (turn = +1). The section is swept round the cell's inner corner, so rails, bed and belt turn as one
    and the inner rail closes into a post. The sweep is not a quarter circle but a little squarer (a
    superellipse): the developer asked for the outer rail to be cut back less, so that the corner
    keeps some of its angle. Both ends are still the plain section, square to the cell's edge."""
    n = SQUARE if square is None else square

    def at(th, across, z):                                    # a point of the section, th degrees round from the entry
        a = rad(90 - th)
        c, s_ = abs(math.cos(a)), abs(math.sin(a))
        r = (0.5 + across) * (c ** n + s_ ** n) ** (-1.0 / n)
        return (-0.5 + r * math.cos(a), -turn * (-0.5 + r * math.sin(a)), z)

    def frame_at(th, across):                                 # where that point is, and which way the belt runs there
        x, y, _ = at(th, across, 0.0)
        x0, y0, _ = at(th - 0.5, across, 0.0)
        x1, y1, _ = at(th + 0.5, across, 0.0)
        return x, y, math.atan2(y1 - y0, x1 - x0)

    steps = [90.0 * i / ARC for i in range(ARC + 1)]
    loft(m, [[at(th, y, z) for y, z in SECTION] for th in steps], R)
    loft(m, [[at(th, y, z) for y, z in WEB] for th in steps], RD)                       # the strip in the outer rail's web
    loft(m, [[at(th, -y, z) for y, z in WEB] for th in steps], RD)                      # and in the inner rail's
    loft(m, [[at(th, y, z) for y, z in BELT] for th in steps], "h_belt")
    for th in (22.5, 67.5):                                   # arrows, turning with the belt
        x, y, head = frame_at(th, 0.0)
        with m.at((x, y, 0), head):
            chev(m, 0.0)
    for th in (20.0, 45.0, 70.0):                             # bolts in the outer rail's web, each square to it
        x, y, head = frame_at(th, BOLT_AT[0])
        with m.at((x, y, 0), head + (0.0 if turn < 0 else math.pi)):
            m.cyl(BOLT[0], BOLT[1], (0, 0, BOLT_AT[1]), "h_lite", seg=6, axis="Y")


def corner_right(m):
    corner(m, -1)


def corner_left(m):
    corner(m, 1)


RISE, EASE = 1.0, 0.30
PITCH = 3                 # pairs of arrows to a cell, as on the flat belt


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


def ramp(m, low=True, high=True, flow=1, legs=True, down=False):
    """Ramp, 2x1. Going up it runs from the west, low, to the east, one cell higher; with down=True it
    runs from the west, high, to the east, one cell lower (the same shape turned end for end, its
    arrows still pointing east). `low` and `high` say whether the low end and the high end are level
    (see ramp_profile): level against a flat belt, sloping on against another ramp.
    It stands on two slim trestles (with legs=False, on nothing: for ramps stacked one above another,
    where trestles would stand on the belt below)."""
    up_lift, up_pitch = ramp_profile(low, high)
    g = -1 if down else 1                                     # which way the high end lies
    lift_at = lambda x: up_lift(g * x)
    pitch_at = lambda x: g * up_pitch(g * x)
    n = 24
    xs = [-1.0 + 2.0 * i / n for i in range(n + 1)]
    loft(m, [[(x, y, z + lift_at(x)) for y, z in SECTION] for x in xs], R)
    for s in SIDES:
        loft(m, [[(x, s * y, z + lift_at(x)) for y, z in WEB] for x in xs], RD)
    loft(m, [[(x, y, z + lift_at(x)) for y, z in BELT] for x in xs], "h_belt")

    def on_slope(x):                                          # a frame lying on the ramp at x
        return m.stack[-1] @ Matrix.Translation((x, 0, lift_at(x))) @ Matrix.Rotation(-pitch_at(x), 4, "Y")

    # Arrows and bolts at the flat belt's own pitch (three to a cell), measured along the belt's
    # surface, with half a pitch left at each end: across a joint with a flat belt, or with another
    # ramp, the spacing stays the same, so the row of arrows does not break there.
    fine = [-1.0 + 2.0 * i / 400 for i in range(401)]
    run_ = [0.0]
    for a_, b_ in zip(fine, fine[1:]):
        run_.append(run_[-1] + math.hypot(b_ - a_, lift_at(b_) - lift_at(a_)))
    count = max(1, round(run_[-1] * PITCH))
    for k in range(count):
        want = (k + 0.5) * run_[-1] / count
        i = next(j for j in range(len(run_)) if run_[j] >= want)
        x = fine[i]
        m.stack.append(on_slope(x))
        chev(m, 0.0, flow)
        bolt(m)
        m.stack.append(m.stack[-1] @ Matrix.Rotation(math.pi, 4, "Z"))
        bolt(m)
        m.stack.pop()
        m.stack.pop()
    if not legs:
        return
    for xc in (g * 0.10, g * 0.80):                           # trestles: a slim post under each rail on a small foot, a tie
        for s in SIDES:                                       # between the two, and a knee brace from each post up to the rail
            ya, yb = sorted((s * 0.385, s * 0.435))
            m.prism([(xc - 0.028, 0.02), (xc + 0.028, 0.02), (xc + 0.028, lift_at(xc + 0.028) + 0.02), (xc - 0.028, lift_at(xc - 0.028) + 0.02)],
                    ya, yb, "Y", ST)
            ya, yb = sorted((s * 0.34, s * 0.48))
            m.prism([(xc - 0.09, 0.0), (xc + 0.09, 0.0), (xc + 0.07, 0.035), (xc - 0.07, 0.035)], ya, yb, "Y", T)
            xk, zk = xc - g * 0.24, lift_at(xc) * 0.42        # the brace: from part way up the post to the rail further down the slope
            ya, yb = sorted((s * 0.395, s * 0.425))
            m.prism([(xc - g * 0.02, zk - 0.03), (xc - g * 0.02, zk + 0.03), (xk, lift_at(xk) + 0.02), (xk - g * 0.06, lift_at(xk - g * 0.06) + 0.02)], ya, yb, "Y", ST)
        zt = lift_at(xc) * 0.62
        m.prism([(xc - 0.022, zt - 0.022), (xc + 0.022, zt - 0.022), (xc + 0.022, zt + 0.022), (xc - 0.022, zt + 0.022)], -0.40, 0.40, "Y", ST)   # tie


def ramp_start(m):
    """The first ramp of a run: level where it leaves the flat belt, sloping on at the top."""
    ramp(m, True, False)


def ramp_mid(m):
    """A ramp between two ramps: one straight slope."""
    ramp(m, False, False)


def ramp_end(m):
    """The last ramp of a run: sloping on from the ramp below, level where it meets the flat belt."""
    ramp(m, False, True)


def ramp_bare(m):
    """A ramp without trestles, level at both ends."""
    ramp(m, True, True, legs=False)


def ramp_down(m):
    """A ramp going down, on its own: level at both ends."""
    ramp(m, True, True, down=True)


def ramp_down_start(m):
    """The first of a run of ramps going down: level where it leaves the flat belt at the top."""
    ramp(m, False, True, down=True)


def ramp_down_mid(m):
    """A ramp going down between two others: one straight slope."""
    ramp(m, False, False, down=True)


def ramp_down_end(m):
    """The last of a run going down: level where it meets the flat belt at the bottom."""
    ramp(m, True, False, down=True)


def ramp_down_bare(m):
    """A ramp going down without trestles, level at both ends."""
    ramp(m, True, True, legs=False, down=True)
