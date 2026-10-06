# v2 works: machines built as buildings, a trial of a second port grammar.
#
# The hero machines so far are all one shape of thing: a body astride a conveyor three cells long. A works
# is a building on a footprint of its own. Items enter and leave through ports on its edges, each exactly
# one cell wide and cut square at the footprint's boundary, so a belt in the next cell joins it. The
# building between the ports can then be any shape the process calls for. Units are grid cells.
import math
import bmesh
from contextlib import contextmanager
from mathutils import Matrix, Vector
from .base import rad, G, T, TD, W, D, SLIT, R, RD, SIDES, BH, BZ, RAIL_D, octa, oct_ring, bx
from .kit import arch_pts
from .hero import hero


@contextmanager
def frame(m, origin, inward):
    """Build in a port's own frame: x runs from the footprint's edge into the building, y across the
    port. `inward` is one of the four axis directions, so the matrix holds only 0 and +-1 and ports
    facing each other are exact mirror images."""
    ix, iy = inward
    mx = Matrix(((ix, -iy, 0, origin[0]), (iy, ix, 0, origin[1]), (0, 0, 1, 0), (0, 0, 0, 1)))
    m.stack.append(m.stack[-1] @ mx)
    yield
    m.stack.pop()


def port_belt(m, depth, out):
    """The conveyor stub of a port: rails, bed and belt from the edge to `depth`, and one arrow."""
    bed_top = BZ - 0.03
    section = [(-y, z) for y, z in reversed(RAIL_D)] + [(-BH, bed_top), (BH, bed_top)] + list(RAIL_D)
    m.prism(section, 0.0, depth, "X", R)
    m.box((depth, BH * 2, 0.03), (depth / 2, 0, BZ - 0.015), "h_belt")
    k = -1 if out else 1                                     # the arrow points the way the items go
    for dx in (-0.035, 0.035):
        for s in SIDES:
            m.box((0.011, 0.26, 0.004), (0.10 + dx, s * 0.12, BZ + 0.002), "h_line", rot=k * s * 0.36)


def port_folds(m, out=False):
    """A port with the folding cover of foundation D: an end frame, three folds, on a sill."""
    port_belt(m, 0.50, out)
    for s in SIDES:
        bx(m, (0.20, 0.48), tuple(sorted((s * 0.34, s * 0.458))), (0.0, 0.31), R, bevel=0.03)
    px = 0.20
    folds = [(0.042, 0.84, 0.77, 0.315, R), (0.026, 0.77, 0.735, 0.335, RD)] * 3
    for th, w, tp, hw, mk in [(0.066, 0.88, 0.79, 0.315, R)] + folds:
        m.prism(arch_pts(w, tp, hole_top=tp - 0.11, hw=hw, c=0.085, ci=0.035), px, px + th, "X", mk)
        px += th
    m.box((0.02, 0.62, 0.40), (px - 0.012, 0, 0.50), SLIT)
    return px


def port_house(m, depth=0.60, top=0.92, out=False):
    """A port that is the mouth of a house: a heavy frame, then one deep vaulted block."""
    port_belt(m, depth, out)
    m.prism(arch_pts(0.98, top + 0.03, hole_top=0.66, hw=0.315, c=0.11, ci=0.035), 0.12, 0.20, "X", D)
    m.prism(arch_pts(0.92, top, hole_top=0.64, hw=0.315, c=0.10, ci=0.035), 0.20, depth, "X", G)
    m.box((0.02, 0.62, 0.40), (depth - 0.03, 0, 0.50), SLIT)


def ring_pipe(m, a, z, r, mk, seg=8):
    """A round pipe bent into an eight-sided ring at height z, its flats facing along and across the
    building. `a` is the distance from the centre to the middle of a flat. Corners are mitred."""
    k = 1.0 / math.cos(math.pi / 8)
    bm = bmesh.new()
    rings = []
    for j in range(8):
        t = math.pi / 8 + j * math.pi / 4
        radial = Vector((math.cos(t), math.sin(t), 0.0))
        centre = radial * (a * k) + Vector((0, 0, z))
        rings.append([bm.verts.new(centre + radial * (r * k * math.cos(2 * math.pi * i / seg))
                                   + Vector((0, 0, r * math.sin(2 * math.pi * i / seg)))) for i in range(seg)])
    for j in range(8):
        p, q = rings[j], rings[(j + 1) % 8]
        for i in range(seg):
            bm.faces.new((p[i], p[(i + 1) % seg], q[(i + 1) % seg], q[i]))
    m._add(bm, mk)


def stove(m, x, y, z0, r=0.27, h=1.12):
    """A hot-blast stove: an eight-sided shell with two bands and a domed head."""
    k = 1.0 / math.cos(math.pi / 8)
    m.cyl(r * k * 1.08, 0.10, (x, y, z0 + 0.05), D, seg=8, rot=rad(22.5))
    m.cyl(r * k, h, (x, y, z0 + h / 2), G, seg=8, rot=rad(22.5))
    for zz in (0.36, 0.86):
        m.cyl(r * k * 1.05, 0.05, (x, y, z0 + zz), D, seg=8, rot=rad(22.5))
    m.cyl(r * k, 0.16, (x, y, z0 + h + 0.08), G, seg=8, r2=r * k * 0.62, rot=rad(22.5))
    m.cyl(r * k * 0.62, 0.07, (x, y, z0 + h + 0.195), D, seg=8, r2=r * k * 0.30, rot=rad(22.5))


@hero
def blast(m):
    """Blast furnace, 3 x 3 cells, two inputs and one output. Ore comes in at one side and fuel at the
    other; each is hauled up a skip bridge to the furnace top. Two stoves behind the furnace feed hot
    blast through the ring main round the bosh. Iron runs out of the tap hole down a runner to the output."""
    F = 0.24                                                  # floor level
    bx(m, (-1.46, 1.46), (-1.46, 1.46), (0.0, 0.18), T, bevel=0.05)
    bx(m, (-1.40, 1.40), (-1.40, 1.40), (0.16, F), G, bevel=0.03)

    # the furnace: dark hearth, bosh flaring out, stack tapering in, throat ring, top house, uptake
    octa(m, 0.58, 0.58, F - 0.02, 0.62, T)
    octa(m, 0.58, 0.70, 0.62, 0.90, G)
    oct_ring(m, 0.76, 0.16, 0.86, 0.94, D)
    octa(m, 0.70, 0.46, 0.90, 1.62, G)
    for zz in (1.12, 1.38):
        a = 0.70 - (zz - 0.90) / 0.72 * 0.24
        octa(m, a + 0.028, a + 0.012, zz - 0.025, zz + 0.025, D)
    oct_ring(m, 0.53, 0.11, 1.60, 1.72, D)
    bx(m, (-0.42, 0.42), (-0.39, 0.39), (1.66, 1.98), G, bevel=0.05)
    octa(m, 0.30, 0.17, 1.97, 2.11, D)
    m.cyl(0.12, 0.17, (0, 0, 2.19), G, seg=8, rot=rad(22.5))
    m.cyl(0.11, 0.07, (0, 0, 2.31), D, seg=8, r2=0.155, rot=rad(22.5))
    m.cyl(0.125, 0.012, (0, 0, 2.336), SLIT, seg=8, rot=rad(22.5))

    # hot blast: a ring main round the bosh, a tuyere into the furnace on every flat, two stoves behind
    ring_pipe(m, 0.80, 0.74, 0.06, W)
    for j in range(8):
        t = j * math.pi / 4
        m.cyl(0.036, 0.16, (math.cos(t) * 0.70, math.sin(t) * 0.70, 0.74), W, seg=8, axis="X", rot=t)
    for sy in SIDES:                                          # behind the furnace, clear of the cast floor
        stove(m, 0.96, sy * 0.96, F, r=0.31, h=1.30)
        t = math.atan2(sy, 1)
        m.cyl(0.055, 0.34, (math.cos(t) * 0.93, math.sin(t) * 0.93, 0.74), W, seg=8, axis="X", rot=t)
        m.cyl(0.078, 0.035, (math.cos(t) * 1.045, math.sin(t) * 1.045, 0.74), D, seg=8, axis="X", rot=t)

    # inputs: a house at each side, and a skip bridge from its roof up to the top house
    for s in SIDES:
        with frame(m, (0, s * 1.5), (0, -s)):
            port_house(m)
        m.prism([(s * 1.24, 0.84), (s * 1.24, 1.00), (s * 0.34, 1.88), (s * 0.34, 1.72)], -0.16, 0.16, "X", G)
        for sx in SIDES:
            xs = sorted((sx * 0.16, sx * 0.205))
            m.prism([(s * 1.26, 0.82), (s * 1.26, 1.07), (s * 0.34, 1.97), (s * 0.34, 1.72)], xs[0], xs[1], "X", D)
        m.prism([(s * 0.88, 1.352), (s * 0.88, 1.482), (s * 0.70, 1.658), (s * 0.70, 1.528)], -0.115, 0.115, "X", T)

    # output: the tap hole in the hearth, a runner of molten iron, and the port it runs into
    with frame(m, (-1.5, 0), (1, 0)):
        back = port_folds(m, out=True)
    x0, x1 = -1.5 + back - 0.01, -0.56
    for s in SIDES:
        bx(m, (x0, x1), tuple(sorted((s * 0.09, s * 0.18))), (F - 0.02, 0.50), G, bevel=0.02)
    m.box((x1 - x0, 0.18, 0.16), ((x0 + x1) / 2, 0, 0.32), D)
    m.box((x1 - x0, 0.18, 0.02), ((x0 + x1) / 2, 0, 0.41), "h_glow")
    m.prism(arch_pts(0.50, 0.64, hole_top=0.54, hw=0.15, c=0.06, ci=0.03), -0.65, -0.575, "X", D)
    m.box((0.02, 0.30, 0.30), (-0.588, 0, 0.39), "h_glow")


blast.frame = {"iso": (4.1, 0.80), "side": (4.3, 1.15), "top": (3.7, 1.0), "end": (4.3, 1.15)}
