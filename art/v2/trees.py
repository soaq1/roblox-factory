# Trees, redone at the developer's word (2026-10-09). He showed the oak he remembered and said ours
# should have that feeling: a slim dark trunk that forks, and a few big flat-faced masses of leaves
# in one dark green, each tree with an outline of its own. What stood here before (the game's
# TreeGen, as drawn in scene_island.py) was an umbrella of many round lumps in three bright greens.
#
# These are looks to judge, not yet the game's trees: the game grows its trees in code, and that code
# is to follow whichever of these is chosen.
#
#   oak_a   broad: two big crowns on a fork, two small ones low on side twigs
#   oak_b   tall: a long bare trunk, the crowns stacked high, a pointed one on top
#   oak_c   spreading: a leaning trunk, wide flat crowns in layers
#   oaks    the three side by side with a figure as tall as a character
#
# One unit is a cell (three studs); a character is 1.67 cells tall.
import math
import random
import bmesh
from mathutils import Vector
import factorykit as fk
from . import hero as _hero

fk.PAL.update({"t_bark": "#5d3b30", "t_leaf": "#1f5a23", "t_leaf_d": "#1a4d1f", "t_leaf_l": "#27672a"})
BARK = "t_bark"


def limb(m, pts, r0, r1, sides=6):
    """A limb through the points given, its radius running from r0 at the first to r1 at the last."""
    bm = bmesh.new()
    pts = [Vector(p) for p in pts]
    n = len(pts)
    rings = []
    for k, p in enumerate(pts):
        d = (pts[min(k + 1, n - 1)] - pts[max(k - 1, 0)]).normalized()
        ref = Vector((1, 0, 0)) if abs(d.x) < 0.9 else Vector((0, 1, 0))
        a = (ref - d * ref.dot(d)).normalized()
        b = d.cross(a)
        r = r0 + (r1 - r0) * k / (n - 1)
        rings.append([bm.verts.new(p + (a * math.cos(t) + b * math.sin(t)) * r) for t in (2 * math.pi * j / sides + 0.3 for j in range(sides))])
    for a_, b_ in zip(rings, rings[1:]):
        for j in range(sides):
            bm.faces.new((a_[j], a_[(j + 1) % sides], b_[(j + 1) % sides], b_[j]))
    bm.faces.new(rings[0][::-1])
    bm.faces.new(rings[-1])
    m._add(bm, BARK)


def crown(m, at, size, seed, mk="t_leaf", flat=0.42, peak=0.0):
    """A mass of leaves: the hull of a handful of points scattered over a squashed ball, so that it is
    made of a few big flat faces. Its underside is cut off flat-ish (at `flat` of its half-height
    below the middle); `peak` draws its top up to a blunt point."""
    rnd = random.Random(seed)
    bm = bmesh.new()
    sx, sy, sz = size[0] / 2, size[1] / 2, size[2] / 2
    for k in range(30):
        u, v = rnd.uniform(-1, 1), rnd.uniform(0, 2 * math.pi)
        w = math.sqrt(1 - u * u)
        rr = rnd.uniform(0.9, 1.0)
        x, y, z = w * math.cos(v) * rr, w * math.sin(v) * rr, u * rr
        z = max(z, -flat)
        if peak and z > 0.25:
            x, y, z = x * (1 - peak * z), y * (1 - peak * z), z * (1 + peak * 0.5)
        bm.verts.new((at[0] + x * sx, at[1] + y * sy, at[2] + z * sz))
    got = bmesh.ops.convex_hull(bm, input=bm.verts[:])
    junk = list({g for g in got.get("geom_interior", []) + got.get("geom_unused", []) if isinstance(g, bmesh.types.BMVert)})
    if junk:
        bmesh.ops.delete(bm, geom=junk, context="VERTS")
    m._add(bm, mk)


def oak_a(m, seed=11):
    """Broad: the trunk forks a little under half its height into two limbs, a big crown on each; two
    twigs lower down each carry a small crown."""
    limb(m, [(0, 0, 0), (0.02, 0.0, 0.55), (-0.02, 0.03, 1.15), (0.02, 0.05, 1.75)], 0.13, 0.085)
    limb(m, [(0.02, 0.05, 1.75), (-0.22, 0.02, 2.25), (-0.42, 0.0, 2.85)], 0.075, 0.045, 5)
    limb(m, [(0.02, 0.05, 1.75), (0.30, 0.08, 2.15), (0.62, 0.10, 2.55)], 0.07, 0.04, 5)
    limb(m, [(0.0, 0.01, 0.85), (-0.30, 0.0, 1.10), (-0.62, -0.02, 1.38)], 0.05, 0.03, 5)
    limb(m, [(0.0, 0.03, 1.20), (0.28, 0.02, 1.38), (0.55, 0.0, 1.55)], 0.045, 0.028, 5)
    crown(m, (-0.50, 0.0, 3.30), (2.35, 2.05, 2.30), seed)         # the crowns are big and run into one another: the top of the
    crown(m, (0.78, 0.10, 3.00), (2.45, 2.05, 2.00), seed + 1, "t_leaf_d")   # tree is full (the developer: the leaves looked empty)
    crown(m, (0.10, 0.35, 3.75), (1.90, 1.75, 1.55), seed + 4, "t_leaf_l")
    crown(m, (-0.85, -0.02, 1.60), (1.25, 1.10, 0.85), seed + 2, "t_leaf_l")
    crown(m, (0.72, 0.0, 1.66), (1.15, 1.00, 1.00), seed + 3)


def oak_b(m, seed=21):
    """Tall: a long bare trunk, slightly bowed, with the crowns stacked on its upper half and a pointed
    one at the very top."""
    limb(m, [(0, 0, 0), (0.05, 0.0, 0.9), (0.10, 0.02, 1.9), (0.06, 0.0, 2.9), (0.02, 0.0, 4.2), (0.04, 0.0, 5.5)], 0.14, 0.03)
    limb(m, [(0.08, 0.0, 2.6), (0.32, 0.02, 2.85), (0.52, 0.0, 3.05)], 0.045, 0.028, 5)
    crown(m, (0.12, 0.0, 2.90), (2.05, 1.90, 1.35), seed)
    crown(m, (0.66, 0.0, 3.30), (1.15, 1.05, 0.85), seed + 1, "t_leaf_l")
    crown(m, (-0.38, 0.0, 3.90), (1.75, 1.65, 1.65), seed + 2, "t_leaf_d")
    crown(m, (0.48, 0.08, 4.05), (1.85, 1.65, 1.65), seed + 3)
    crown(m, (0.00, 0.25, 4.75), (1.65, 1.55, 1.25), seed + 5, "t_leaf_l")
    crown(m, (0.05, 0.0, 5.40), (1.75, 1.65, 1.35), seed + 4, "t_leaf", peak=0.55)


def oak_c(m, seed=31):
    """Spreading: the trunk leans and forks low; wide flat crowns lie in layers, the widest on top."""
    limb(m, [(0, 0, 0), (-0.04, 0.0, 0.5), (-0.12, 0.02, 1.0), (-0.16, 0.03, 1.45)], 0.14, 0.09)
    limb(m, [(-0.16, 0.03, 1.45), (-0.30, 0.02, 2.0), (-0.38, 0.0, 2.6)], 0.075, 0.04, 5)
    limb(m, [(-0.16, 0.03, 1.45), (0.12, 0.05, 1.95), (0.45, 0.08, 2.45), (0.60, 0.05, 2.95)], 0.07, 0.035, 5)
    limb(m, [(-0.06, 0.01, 1.05), (0.22, -0.05, 1.35), (0.45, -0.12, 1.55)], 0.045, 0.028, 5)
    crown(m, (0.25, 0.0, 3.35), (3.05, 2.55, 1.45), seed, "t_leaf", flat=0.35)
    crown(m, (-0.95, 0.0, 2.60), (2.05, 1.75, 1.15), seed + 1, "t_leaf_l", flat=0.35)
    crown(m, (1.05, 0.15, 2.45), (2.45, 2.05, 1.30), seed + 2, "t_leaf_d", flat=0.35)
    crown(m, (0.00, 0.40, 2.90), (2.05, 1.85, 1.15), seed + 4, "t_leaf", flat=0.35)
    crown(m, (0.55, -0.15, 1.75), (1.15, 1.00, 0.60), seed + 3)


def figure(m):
    """A blocky figure as tall as a character (1.67 cells), to measure by."""
    m.box((0.26, 0.16, 0.66), (0, 0, 0.33), "h_taupe_d")
    m.box((0.36, 0.18, 0.64), (0, 0, 0.98), "h_white")
    m.box((0.22, 0.22, 0.36), (0, 0, 1.49), "h_lite")


def oaks(m):
    with m.at((-3.4, 0, 0)):
        oak_a(m)
    with m.at((0.0, 0.6, 0)):
        oak_b(m)
    with m.at((3.4, 0, 0)):
        oak_c(m)
    with m.at((1.5, 0.3, 0)):
        figure(m)


for _name, _fn, _frame in (("oak_a", oak_a, {"iso": (6.4, 2.3)}), ("oak_b", oak_b, {"iso": (8.4, 3.0)}), ("oak_c", oak_c, {"iso": (6.4, 2.1)}),
                           ("oaks", oaks, {"iso": (10.8, 3.1)})):
    _fn.frame, _fn.shadow, _fn.res = dict(_frame, side=_frame["iso"], top=_frame["iso"], end=_frame["iso"]), True, 1800
    _hero.HEROES[_name] = _fn
