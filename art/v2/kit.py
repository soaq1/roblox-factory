# v2 kit: the shared parts every v2 model is built from.
#
# The grammar follows Islands' industrial machines: a conveyor trough runs through the machine,
# ribbed plates wrap each tunnel mouth, bodies are stacked slabs rather than one box, and large
# machines stand inside an open steel frame. Units are grid cells (one cell is 3 studs).
import math
import factorykit as fk
from factorykit import PAL, EMIT, rad, SIDE_ANG
from mathutils import Vector

PAL.update({
    # machine greys, light to dark; g4 is the warm skirt colour
    "g1": "#cfd2d3", "g2": "#b3b6b7", "g3": "#969a9b", "g4": "#756f6d", "g5": "#4b4e50",
    "tread": "#2b2f2e", "treadline": "#7d8280",
    "frame": "#8fb3d1", "stripe": "#22262a",      # painted steel frame and its dark edge line
    "badge": "#e0564a", "tankc": "#e6e1d3", "tank_dark": "#cbc5b6",
    "glassb": "#8fd3e6", "lampg": "#58d07a", "lampr": "#ff4b3e", "rock": "#7c7a7d", "rock_dark": "#636165",
    "clayp": "#c08a62", "navy": "#34425e", "toolred": "#c8452f", "paper": "#3f7fd0",
})
EMIT.update({"lampg": 1.6, "lampr": 1.6})

BELT_Z = 0.30          # height of the belt surface
HALF = 0.46            # half width of a trough, rails included
SPECS2 = []
V1 = {s["key"]: s for s in fk.SPECS}

W_IN, E_OUT = ("W", "in", 0), ("E", "out", 0)


def machine2(key, size=(3, 1), ports=(), ins=None, outs=None, ko=None, fam=None, recipe=None, items=True):
    """Register a v2 model. Name, family and description come from the v1 entry with the same key."""
    def deco(fn):
        v1 = V1.get(key, {})
        SPECS2.append(dict(
            key=key, ko=ko or v1.get("ko", key), fam=fam or v1.get("fam", ""),
            recipe=v1.get("recipe", "") if recipe is None else recipe, size=size, ports=ports,
            ins=v1.get("ins", ()) if ins is None else ins, outs=v1.get("outs", ()) if outs is None else outs,
            fn=fn, items=items, v1size=v1.get("size")))
        return fn
    return deco


def bx(m, xs, ys, zs, mk, bevel=0.0, taper=1.0):
    """A box given by its extents on each axis."""
    m.box((xs[1] - xs[0], ys[1] - ys[0], zs[1] - zs[0]),
          ((xs[0] + xs[1]) / 2, (ys[0] + ys[1]) / 2, (zs[0] + zs[1]) / 2), mk, bevel=bevel, taper=taper)


FACE_ANG = {"S": 0.0, "E": math.pi / 2, "N": math.pi, "W": -math.pi / 2}


def on(m, side, x, y, z=0.0):
    """Local frame on a wall: the wall is the plane y=0, outward is -y, x runs along it, z is up."""
    return m.at((x, y, z), FACE_ANG[side])


# ============================ CONVEYOR ============================
RAILP = [(0.33, 0.0), (HALF, 0.0), (HALF, 0.24), (0.42, 0.24), (0.42, 0.39), (0.33, 0.39)]


def chevron(m, x, flow=1, z=BELT_Z + 0.003):
    """A shallow V across the belt, pointing the way items travel."""
    for s in (-1, 1):
        m.box((0.018, 0.33, 0.006), (x, s * 0.16, z), "treadline", rot=s * flow * 0.21)


def trough(m, x0, x1, feet=(True, True), flow=1, lines=True, bolts=True):
    """Conveyor bed along X from x0 to x1: bed, belt, stepped rails, hex bolts, flared feet at the ends."""
    L, cx = x1 - x0, (x0 + x1) / 2
    m.box((L, 0.70, 0.24), (cx, 0, 0.12), "g3")
    m.box((L, 0.66, 0.06), (cx, 0, BELT_Z - 0.03), "tread")
    m.prism(RAILP, x0, x1, "X", "g1")
    m.prism([(-y, z) for y, z in RAILP], x0, x1, "X", "g1")
    if lines:
        n = max(1, round(L * 3))
        for i in range(n):
            chevron(m, x0 + (i + 0.5) * L / n, flow)
    if bolts:
        n = max(1, round(L * 2))
        for i in range(n):
            for s in (-1, 1):
                m.cyl(0.028, 0.03, (x0 + (i + 0.5) * L / n, s * (HALF + 0.004), 0.145), "g3", seg=6, axis="Y")
    for present, x, d in ((feet[0], x0, 1), (feet[1], x1, -1)):
        if present:
            m.box((0.10, 1.0, 0.16), (x + d * 0.054, 0, 0.08), "g2")


def arch_pts(w, top, hole_top=0.80, hw=0.33):
    """Outline of a plate that straddles the belt, with the tunnel cut out of it."""
    return [(-w / 2, 0.0), (-w / 2, top), (w / 2, top), (w / 2, 0.0),
            (hw, 0.0), (hw, hole_top), (-hw, hole_top), (-hw, 0.0)]


def collar(m, x, d, n=3, t=0.065, w=0.98, top=0.98, shrink=0.045, mks=("g2", "g3")):
    """Ribbed plates around a tunnel mouth, n plates from x in direction d. Returns where they end."""
    for i in range(n):
        a, b = x + d * i * t, x + d * (i + 1) * t
        k = i % 2
        m.prism(arch_pts(w - k * 2 * shrink, top - k * shrink), min(a, b), max(a, b), "X", mks[k])
    return x + d * n * t


def port_arch(m, x, d, kind, w=1.0, top=1.03, double=True):
    """The coloured arch that marks a port: yellow is an input, teal is an output."""
    mk = "accent" if kind == "in" else "out"
    plates = ((0.0, 0.04, mk, 0.0), (0.04, 0.014, "stripe", 0.03), (0.054, 0.04, mk, 0.0))
    if not double:
        plates = ((0.0, 0.014, "stripe", 0.03), (0.014, 0.05, mk, 0.0))
    for a, t, k, s in plates:
        lo, hi = sorted((x + d * a, x + d * (a + t)))
        m.prism(arch_pts(w - s, top - s / 2), lo, hi, "X", k)
    return x + d * (plates[-1][0] + plates[-1][1])


def stub(m, xf, d, L, kind, n=3, top=0.98, w=0.98):
    """Conveyor leaving a body face at x=xf in direction d (+1 or -1): trough, collar, port arch."""
    xo = xf + d * L
    flow = d if kind == "out" else -d
    trough(m, min(xf, xo), max(xf, xo), feet=(d < 0, d > 0), flow=flow)
    m.box((0.02, 0.66, 0.50), (xf + d * 0.011, 0, BELT_Z + 0.25), "hole")
    xe = collar(m, xf, d, n=n, top=top, w=w)
    return port_arch(m, xe, d, kind, w=min(1.0, w + 0.02), top=top + 0.04)


def port(m, side, x, y, kind, L=1.0, **kw):
    """A stub leaving the body at (x, y) toward a compass side."""
    with m.at((x, y, 0), SIDE_ANG[side]):
        stub(m, 0, 1, L, kind, **kw)


def inline(m, x0=-0.5, x1=0.5, half=1.5, kinds=("in", "out"), **kw):
    """The usual 3x1 layout: input stub on the west, output stub on the east, body between x0 and x1."""
    if kinds[0]:
        stub(m, x0, -1, half + x0, kinds[0], **kw)
    if kinds[1]:
        stub(m, x1, 1, half - x1, kinds[1], **kw)


# ============================ WALL DETAILS (use inside `with on(...)`) ============================
def vent(m, w=0.40, h=0.26, n=4):
    m.box((w + 0.07, 0.03, h + 0.07), (0, -0.015, 0), "g1")
    m.box((w, 0.012, h), (0, -0.033, 0), "g5")
    for i in range(n):
        m.box((w - 0.03, 0.02, h / (2 * n)), (0, -0.045, -h / 2 + (i + 0.5) * h / n), "g2")


def panel(m, w=0.4, h=0.3, mk="g1", t=0.03, bolts=True):
    m.box((w, t, h), (0, -t / 2, 0), mk)
    if bolts:
        for sx in (-1, 1):
            for sz in (-1, 1):
                m.cyl(0.02, 0.02, (sx * (w / 2 - 0.045), -t - 0.006, sz * (h / 2 - 0.045)), "g3", seg=6, axis="Y")


def hexbolt(m, r=0.04, mk="g3"):
    m.cyl(r, 0.035, (0, -0.0175, 0), mk, seg=6, axis="Y")
    m.cyl(r * 0.55, 0.02, (0, -0.045, 0), "g1", seg=6, axis="Y")


def badge(m, r=0.085):
    """The small red emblem Islands puts on its heavy machines."""
    m.cyl(r, 0.03, (0, -0.015, 0), "badge", seg=5, axis="Y")
    m.cyl(r * 0.62, 0.02, (0, -0.036, 0), "g1", seg=5, axis="Y")
    m.cyl(r * 0.25, 0.02, (0, -0.05, 0), "g5", seg=5, axis="Y")


def gauge(m, r=0.09):
    m.cyl(r, 0.03, (0, -0.015, 0), "g5", seg=10, axis="Y")
    m.cyl(r * 0.76, 0.02, (0, -0.034, 0), "white", seg=10, axis="Y")
    m.box((0.014, 0.014, r * 0.7), (0.015, -0.05, 0.015), "red", rot=(0, rad(30), 0))


def buttons(m, cols=("spark", "lampg", "water", "red"), s=0.055):
    w = len(cols) * (s + 0.025) + 0.045
    m.box((w, 0.03, s + 0.09), (0, -0.015, 0), "g5")
    for i, c in enumerate(cols):
        m.box((s, 0.02, s), (-w / 2 + 0.035 + s / 2 + i * (s + 0.025), -0.038, 0), c)


def slots(m, w=0.36, h=0.22, n=4, mk="glow", vertical=True):
    """A dark opening with glowing bars behind it: a firebox door or a status display."""
    m.box((w + 0.07, 0.03, h + 0.07), (0, -0.015, 0), "g4")
    m.box((w, 0.012, h), (0, -0.033, 0), "hole")
    for i in range(n):
        if vertical:
            m.box((w / (2 * n), 0.014, h - 0.05), (-w / 2 + (i + 0.5) * w / n, -0.041, 0), mk)
        else:
            m.box((w - 0.05, 0.014, h / (2 * n)), (0, -0.041, -h / 2 + (i + 0.5) * h / n), mk)


def lamp(m, mk="lampg", r=0.035):
    m.cyl(r + 0.012, 0.02, (0, -0.01, 0), "g5", seg=8, axis="Y")
    m.cyl(r, 0.03, (0, -0.03, 0), mk, seg=8, axis="Y")


# ============================ STRUCTURE ============================
def band(m, xs, ys, z, t=0.08, mk="g4", out=0.04):
    """A trim slab that overhangs the block below it."""
    bx(m, (xs[0] - out, xs[1] + out), (ys[0] - out, ys[1] + out), (z, z + t), mk)


def chimney(m, x, y, z0, h, r=0.10, seg=6, mks=("g2", "g3"), glow=False):
    """A stack of segments of alternating width, the way Islands draws its chimneys and pistons."""
    n = max(2, round(h / 0.15))
    t = h / n
    for i in range(n):
        k = i % 2
        m.cyl(r * (1.0, 0.76)[k], t, (x, y, z0 + (i + 0.5) * t), mks[k], seg=seg)
    m.cyl(r * 1.18, 0.05, (x, y, z0 + h + 0.025), "g5", seg=seg)
    m.cyl(r * 0.8, 0.012, (x, y, z0 + h + 0.052), "glow" if glow else "hole", seg=seg)
    return z0 + h + 0.05


def frame_tower(m, xs, ys, z0, levels, post=0.055, beam=0.11, mk="frame"):
    """An open scaffold: a thin post at each corner and a ring of painted beams at each level."""
    top = max(levels)
    for x in xs:
        for y in ys:
            m.box((post, post, top - z0), (x, y, (top + z0) / 2), "g3")
    h = beam * 0.62
    for z in levels:
        for y in ys:
            bx(m, (xs[0] - beam / 2, xs[1] + beam / 2), (y - beam / 2, y + beam / 2), (z - h, z), mk)
            bx(m, (xs[0] - beam / 2 + 0.01, xs[1] + beam / 2 - 0.01), (y - beam / 2 + 0.01, y + beam / 2 - 0.01),
               (z - h - 0.016, z - h), "stripe")
        for x in xs:
            bx(m, (x - beam / 2, x + beam / 2), (ys[0] - beam / 2, ys[1] + beam / 2), (z - h, z), mk)
            bx(m, (x - beam / 2 + 0.01, x + beam / 2 - 0.01), (ys[0] - beam / 2 + 0.01, ys[1] + beam / 2 - 0.01),
               (z - h - 0.016, z - h), "stripe")


def tank(m, x, y, z0, r, h, mk="tankc", seg=10, rings=2, lip=True, rods=True):
    """An upright tank with ring bands, a rim, and thin rods down its side."""
    m.cyl(r, h, (x, y, z0 + h / 2), mk, seg=seg)
    for i in range(rings):
        m.cyl(r + 0.02, 0.05, (x, y, z0 + h * (i + 0.5) / rings), "tank_dark" if mk == "tankc" else "g3", seg=seg)
    if lip:
        m.cyl(r + 0.03, 0.07, (x, y, z0 + h + 0.035), mk, seg=seg)
        m.cyl(r - 0.03, 0.012, (x, y, z0 + h + 0.072), "g5", seg=seg)
    if rods:
        for a in (rad(-60), rad(-120)):
            m.cyl(0.016, h * 0.9, (x + math.cos(a) * (r + 0.03), y + math.sin(a) * (r + 0.03), z0 + h * 0.5), "g3", seg=6)
    return z0 + h + (0.07 if lip else 0)


def flange(m, loc, r, axis="Z", mk="g3", t=0.04):
    m.cyl(r, t, loc, mk, seg=8, axis=axis)


def hopper(m, x, y, z0, w=0.62, h=0.30, mk="g2", fill="hole", d=None):
    """A funnel that widens upward, with a dark rim."""
    d = d or w
    k = 0.6
    m.box((w * k, d * k, h), (x, y, z0 + h / 2), mk, taper=1 / k)
    bx(m, (x - w / 2 - 0.03, x + w / 2 + 0.03), (y - d / 2 - 0.03, y + d / 2 + 0.03), (z0 + h, z0 + h + 0.05), "g4")
    bx(m, (x - w / 2 + 0.04, x + w / 2 - 0.04), (y - d / 2 + 0.04, y + d / 2 - 0.04), (z0 + h + 0.03, z0 + h + 0.055), fill)
    return z0 + h + 0.05


def skirt(m, xs, y=-0.5, depth=0.05, h=0.20, mk="g4"):
    """The low block that sits at the foot of a machine's front."""
    bx(m, xs, (y, y + depth), (0.0, h), mk)


def rocks(m, pts, mk="rock", jitter=0.16):
    for x, y, z, r in pts:
        m.ico(r, (x, y, z), mk, squash=0.85, jitter=jitter)


# ============================ LAYOUTS ============================
def body(m, top=0.80, mk="g2", band_mk="g4", t=0.08, xs=(-0.5, 0.5), ys=(-0.44, 0.44), out=0.04):
    """The lower block of a machine with a trim band on it. Returns the height of the deck."""
    bx(m, xs, ys, (0.0, top), mk)
    band(m, xs, ys, top, t=t, mk=band_mk, out=out)
    return top + t


TEE_IN = (("W", "in", 0.5), ("S", "in", 0), ("E", "out", 0.5))
TEE_OUT = (("W", "in", 0.5), ("E", "out", 0.5), ("S", "out", 0))


def tee(m, s_kind="in", **kw):
    """3x2 layout: the line runs along the back row and a side stub comes out the front.
    The body belongs at x -0.5..0.5, y 0..1."""
    with m.at((0, 0.5, 0)):
        inline(m, **kw)
    port(m, "S", 0, 0.0, s_kind, L=1.0, **kw)


def tee_body(m, top=1.30, mk="g2", band_mk="g4", t=0.08):
    return body(m, top, mk, band_mk, t, xs=(-0.5, 0.5), ys=(0.04, 0.96))
