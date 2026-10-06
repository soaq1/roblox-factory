# v2 forms: the large shapes Islands composes its machines from.
#
# Seen at full size, an Islands machine is not a box with a plate and small parts on it. The conveyor
# chassis runs the whole length with the body standing inside its rails; the body is two or three big
# chamfered masses (a firebox, a deck, a housing with cut-back top edges, a vault, an open frame); and the
# fittings are heavy: pipes as thick as an arm, hex stacks, louvres across a whole face, a dark console
# at the foot that sits astride the rail. Units are grid cells.
import math
import bmesh
import factorykit as fk
from factorykit import rad
from mathutils import Vector
from .kit import bx, on, chevron, arch_pts, BELT_Z

BW = 0.38        # half width of a machine body: it stands between the rails
RAIL_OUT = 0.45  # half width of the chassis at its foot
BELT_HW = 0.31   # half width of the belt

# Rail cross-section: a thick lower wall leaning in slightly, a shoulder, a thinner upper wall, a chamfer.
RAIL = [(BELT_HW, 0.0), (RAIL_OUT, 0.0), (0.44, 0.25), (0.40, 0.29), (0.40, 0.40), (0.38, 0.42), (BELT_HW, 0.42)]


def chassis(m, x0, x1, flow=1, feet=(True, True), lines=True):
    """The conveyor that everything stands on: bed, belt with arrows, heavy rails with hex bolts,
    and a flared foot under each rail end."""
    L, cx = x1 - x0, (x0 + x1) / 2
    m.box((L, BELT_HW * 2 - 0.006, 0.24), (cx, 0, 0.12), "g3")
    m.box((L, BELT_HW * 2 - 0.006, 0.06), (cx, 0, BELT_Z - 0.03), "tread")
    m.prism(RAIL, x0, x1, "X", "g2")
    m.prism([(-y, z) for y, z in RAIL], x0, x1, "X", "g2")
    if lines:
        n = max(1, round(L * 2.4))
        for i in range(n):
            chevron(m, x0 + (i + 0.5) * L / n, flow)
    n = max(1, round(L * 2))
    for i in range(n):
        for s in (-1, 1):
            m.cyl(0.034, 0.04, (x0 + (i + 0.5) * L / n, s * 0.448, 0.13), "g1", seg=6, axis="Y")
    for present, x, d in ((feet[0], x0, 1), (feet[1], x1, -1)):
        if present:
            for s in (-1, 1):
                lo, hi = sorted((s * 0.36, s * 0.498))
                a, b = sorted((x + d * 0.004, x + d * 0.24))
                bx(m, (a, b), (lo, hi), (0.0, 0.15), "g2", bevel=0.04)


def bellows(m, x, d, top=0.80, w=0.92, hole_top=0.62, n=5, t=0.046):
    """The stack of plates around a tunnel mouth. No two neighbours are the same size."""
    steps = ((0.0, 0.0), (0.08, 0.06), (0.025, 0.02), (0.09, 0.065), (0.0, 0.0), (0.07, 0.05))
    for i in range(n):
        dw, dz = steps[i % len(steps)]
        a, b = sorted((x + d * i * t, x + d * (i + 1) * t))
        m.prism(arch_pts(w - dw, top - dz, hole_top=hole_top, hw=BELT_HW, c=0.06), a, b, "X",
                "g2" if dw < 0.05 else "g3")
    return x + d * n * t


def through(m, x0=-0.5, x1=0.5, half=1.5, top=0.80, flow=1):
    """3x1 layout: one chassis the full length, a bellows at each end of the body between x0 and x1."""
    chassis(m, -half, half, flow)
    for xf, d in ((x0, -1), (x1, 1)):
        m.box((0.02, BELT_HW * 2 - 0.006, 0.32), (xf + d * 0.011, 0, BELT_Z + 0.16), "hole")
        bellows(m, xf, d, top=top)


# ============================ MASSES ============================
def mass(m, xs, ys, zs, mk="g2", c=0.05):
    """A chamfered block."""
    bx(m, xs, ys, zs, mk, bevel=c)


def frustum(m, bottom, top, z0, z1, mk):
    """A solid between two rectangles: bottom and top are each ((x0, x1), (y0, y1))."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1)
    for v in bm.verts:
        (x0, x1), (y0, y1) = top if v.co.z > 0 else bottom
        v.co = Vector((x0 if v.co.x < 0 else x1, y0 if v.co.y < 0 else y1, z1 if v.co.z > 0 else z0))
    m._add(bm, mk)


def housing(m, xs, ys, z0, z1, mk="g1", s=0.11, corner=0.03):
    """A block whose top edges are cut back by the same amount on all four sides, the way Islands
    roofs its housings. There is no plate on it: the block itself turns the corner."""
    bx(m, xs, ys, (z0, z1 - s), mk, bevel=corner)
    frustum(m, ((xs[0] + corner, xs[1] - corner), (ys[0] + corner, ys[1] - corner)),
            ((xs[0] + s, xs[1] - s), (ys[0] + s, ys[1] - s)), z1 - s - corner, z1, mk)
    return z1


def vault(m, x0, x1, r, z0, mk="g2", n=5, cy=0.0, flat=1.0):
    """A half drum lying along the belt."""
    pts = [(cy + r * math.cos(a), z0 + r * flat * math.sin(a)) for a in (i * math.pi / n for i in range(n + 1))]
    m.prism(pts, x0, x1, "X", mk)


def stack(m, x, y, z0, h, r=0.11, seg=6, glow=False, mks=("g2", "g1")):
    """A fat chimney of hex drums, flared at the foot and at the mouth."""
    m.cyl(r * 1.35, 0.07, (x, y, z0 + 0.035), "g3", seg=seg)
    n = max(2, round(h / 0.20))
    t = (h - 0.07) / n
    for i in range(n):
        m.cyl(r * (1.0, 0.82)[i % 2], t, (x, y, z0 + 0.07 + (i + 0.5) * t), mks[i % 2], seg=seg)
    m.cyl(r * 0.9, 0.10, (x, y, z0 + h + 0.05), "g3", seg=seg, r2=r * 1.3)
    m.cyl(r * 1.05, 0.012, (x, y, z0 + h + 0.102), "glow" if glow else "hole", seg=seg)
    return z0 + h + 0.10


def nut(m, x, y, z, r=0.06, mk="g1"):
    """A big hex nut on a stud, standing on a deck."""
    m.cyl(r, 0.06, (x, y, z + 0.03), mk, seg=6)
    m.cyl(r * 0.55, 0.10, (x, y, z + 0.08), "g3", seg=6)


def elbow(m, x, y, z, foot, r=0.065, mk="white", out=0.085, d=-1):
    """A thick pipe that leaves a side wall at (x, y, z), turns down and runs into the console.
    d is -1 on the south wall and +1 on the north wall."""
    m.pipe([(x, y - d * 0.03, z), (x, y + d * out, z), (x, y + d * out, foot)], r, mk, seg=8)
    m.cyl(r * 1.28, 0.035, (x, y + d * 0.012, z), mk, seg=8, axis="Y")
    m.cyl(r * 1.28, 0.04, (x, y + d * out, foot + 0.02), mk, seg=8)


def console(m, x0, x1, h=0.30, mk="g4", d=-1):
    """The dark block at the foot of a machine's side. It sits astride the rail. d picks the side."""
    y0, y1 = sorted((d * 0.5, d * 0.37))
    bx(m, (x0, x1), (y0, y1), (0.0, h), mk, bevel=0.035)


def plinth(m, d, x0=-0.53, x1=0.53, h=0.44, mk="g4"):
    """The dark foot that runs the whole length of a machine's side and swallows the rail there. It is
    a block the body stands on, not a plate stuck to the wall. d picks the side."""
    y0, y1 = sorted((d * 0.498, d * 0.365))
    bx(m, (x0, x1), (y0, y1), (0.0, h), mk, bevel=0.04)
    return h


def downpipe(m, x, d, z_top, foot=0.44, r=0.05, mk="white"):
    """A pipe that leaves a side wall high up and runs straight down the wall into the plinth."""
    y = d * BW
    m.pipe([(x, y - d * 0.03, z_top), (x, y + d * 0.045, z_top), (x, y + d * 0.075, z_top - 0.03),
            (x, y + d * 0.075, foot - 0.02)], r, mk, seg=8)
    m.cyl(r * 1.3, 0.03, (x, y + d * 0.012, z_top), mk, seg=8, axis="Y")
    m.cyl(r * 1.3, 0.04, (x, y + d * 0.075, foot + 0.02), mk, seg=8)


def louvres(m, x0, x1, z0, z1, n=4, depth=0.05, mk="g1", d=-1, y=None):
    """Slats across a whole side wall. d picks the side."""
    y = d * BW if y is None else y
    step = (z1 - z0) / n
    for i in range(n):
        m.box((x1 - x0, depth, step * 0.6), ((x0 + x1) / 2, y + d * (depth / 2 - 0.01), z0 + (i + 0.5) * step), mk,
              rot=(rad(-18 * -d), 0, 0))
    m.box((x1 - x0 + 0.04, 0.02, z1 - z0 + 0.04), ((x0 + x1) / 2, y, (z0 + z1) / 2), "g3")


def open_frame(m, xs, ys, z0, z1, bar=0.06, mk="white"):
    """A cage of square bars you can see through."""
    for x in xs:
        for y in ys:
            m.box((bar, bar, z1 - z0), (x, y, (z0 + z1) / 2), mk)
    for y in ys:
        m.box((xs[1] - xs[0] + bar, bar, bar), ((xs[0] + xs[1]) / 2, y, z1 - bar / 2 + 0.002), mk)
    for x in xs:
        m.box((bar, ys[1] - ys[0] + bar, bar), (x, (ys[0] + ys[1]) / 2, z1 - bar / 2 + 0.004), mk)


def facenut(m, r=0.045, mk="g1"):
    """A hex nut on a wall (use inside `with on(...)`)."""
    m.cyl(r, 0.05, (0, -0.01, 0), mk, seg=6, axis="Y")
    m.cyl(r * 0.5, 0.03, (0, -0.045, 0), "g3", seg=6, axis="Y")


def plate(m, w, h, mk="g1", t=0.04, frame="g3"):
    """A big raised panel with a rim (use inside `with on(...)`)."""
    m.box((w + 0.05, t, h + 0.05), (0, -t / 2 + 0.02, 0), frame)
    m.box((w, t, h), (0, -t / 2 - 0.005, 0), mk)
