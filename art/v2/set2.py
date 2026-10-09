# v2 second set: four more machines in the manner of the big furnace the developer picked (bay.blast3x with
# grey accents): light walls, a dark deck, dark steel for frames and vessels, the big plain faces broken
# up by buttresses, bands, staves and windows, the same conveyor and folding-cover mouths, and rendered
# with soft shadows.
import math
import factorykit as fk
from .base import loft_x
from . import hero as _hero
from . import pairs as _pairs
from .base import foot_hearth, foot_drain
from .supply import crystal
from .d import *          # noqa: F401,F403
from .d import run, cover, block, frame, stub_form, strip, frustum, K
from .d import SECTION, chev, buttress, bed

ST, LT = "h_steel", "h_lite"
F31 = {"iso": (3.3, 0.72), "side": (3.4, 0.95), "top": (3.2, 0.6), "end": (2.6, 1.0)}
F33 = {"iso": (5.0, 1.0), "side": (4.6, 1.3), "top": (3.8, 1.0), "end": (4.6, 1.3)}
F21 = {"iso": (3.0, 0.80), "side": (3.2, 0.95), "top": (3.0, 0.6), "end": (2.6, 1.0)}


def through_base(m, top, foot):
    """A 3x1 through machine's lower half: conveyor, foot, light body with corner buttresses, a mouth at
    each end, and a dark deck. Returns the height of the deck."""
    run(m, -1.5, 1.5, braces=(-4 / 3, -1.0, 1.0, 4 / 3))
    foot(m)
    block(m, top)
    cover(m, BX, 1)
    cover(m, -BX, -1)
    for d in SIDES:
        for sx in SIDES:
            bx(m, tuple(sorted((sx * 0.33, sx * 0.45))), tuple(sorted((d * BY, d * (BY + 0.04)))), (0.30, top - 0.02), D, bevel=0.015)
    bx(m, (-0.49, 0.49), (-0.45, 0.45), (top - 0.04, top + 0.08), TD, bevel=0.03)
    return top + 0.08


def smelter2(m):
    """Smelter: a dark steel shaft with light bands on a dark deck, the melt glowing inside its rim, a
    flue up each end, and a barred fire mouth in each side wall."""
    Z = through_base(m, 0.78, foot_hearth)
    for d in SIDES:
        yp = d * BY + d * 0.004
        fz, fw, fh, ft = 0.53, 0.26, 0.17, 0.04
        for sz in SIDES:
            m.box((fw + 2 * ft, 0.05, ft), (0, yp + d * 0.02, fz + sz * (fh + ft) / 2), T)
        for sx in SIDES:
            m.box((ft, 0.05, fh), (sx * (fw + ft) / 2, yp + d * 0.02, fz), T)
        m.box((fw, 0.008, fh), (0, yp + d * 0.004, fz), "h_glow")
        for i in range(4):
            m.box((0.024, 0.018, fh), (-0.078 + i * 0.052, yp + d * 0.03, fz), TD)
    octa(m, 0.41, 0.41, Z - 0.02, Z + 0.10, T)
    octa(m, 0.37, 0.29, Z + 0.08, Z + 0.66, ST)
    for z, a in ((Z + 0.24, 0.348), (Z + 0.43, 0.322)):
        octa(m, a + 0.014, a + 0.008, z, z + 0.05, LT)
    oct_ring(m, 0.345, 0.08, Z + 0.64, Z + 0.76, TD)
    octa(m, 0.262, 0.262, Z + 0.66, Z + 0.695, "h_glow")
    for sx in SIDES:
        x = sx * 0.405
        m.cyl(0.085, 0.05, (x, 0, Z + 0.025), TD, seg=8)
        m.cyl(0.062, 0.92, (x, 0, Z + 0.46), ST, seg=8)
        m.cyl(0.058, 0.10, (x, 0, Z + 0.97), TD, seg=8, r2=0.09)
        m.cyl(0.07, 0.01, (x, 0, Z + 1.022), SLIT, seg=8)
        for z, inner in ((Z + 0.28, 0.33), (Z + 0.50, 0.30)):
            bx(m, tuple(sorted((sx * inner, x))), (-0.07, 0.07), (z, z + 0.055), D, bevel=0.0)


def washer2(m):
    """Washer: a dark steel tub of water as wide as the body, staved and rimmed, with a paddle wheel
    turning in it, and a porthole in each side wall."""
    Z = through_base(m, 0.72, foot_drain)
    for d in SIDES:
        y = d * (BY + 0.012)
        m.cyl(0.125, 0.05, (0, y, 0.50), T, seg=12, axis="Y")
        m.cyl(0.092, 0.012, (0, y + d * 0.012, 0.50), "h_water", seg=12, axis="Y")
    oct_ring(m, 0.45, 0.075, Z - 0.01, Z + 0.40, ST)
    octa(m, 0.40, 0.40, Z - 0.01, Z + 0.05, TD)
    octa(m, 0.376, 0.376, Z + 0.05, Z + 0.30, "h_water")
    oct_ring(m, 0.475, 0.11, Z + 0.37, Z + 0.45, TD)
    for j in range(8):
        with m.at((0, 0, 0), j * math.pi / 4):
            m.box((0.022, 0.13, 0.34), (0.458, 0, Z + 0.18), LT)
    gear(m, 0.25, 0.40, (0, 0, Z + 0.43), T, teeth=8, root=0.52, base=0.30, tip=0.16)
    m.cyl(0.115, 0.44, (0, 0, Z + 0.43), TD, seg=8, axis="Y")
    m.cyl(0.05, 0.86, (0, 0, Z + 0.43), LT, seg=8, axis="Y")
    for d in SIDES:
        m.box((0.20, 0.10, 0.16), (0, d * 0.41, Z + 0.46), G, bevel=0.025)


def extractor2(m):
    """Extractor, 2x1: four dark steel pylons lean in over a lit socket in the deck and hold a vein core
    in the air between them, under a halo ring."""
    with m.at((-0.5, 0, 0)):
        stub_form(m, 0.82, 1, fit=lambda m, d, yp, z: strip(m, d, yp, z, "h_core"))
        for d in SIDES:
            for sx in SIDES:
                bx(m, tuple(sorted((sx * 0.36, sx * 0.46))), tuple(sorted((d * BY, d * (BY + 0.04)))), (0.22, 0.80), D, bevel=0.015)
        bx(m, (-0.49, 0.49), (-0.45, 0.45), (0.78, 0.90), TD, bevel=0.03)
        Z = 0.90
        oct_ring(m, 0.30, 0.10, Z - 0.01, Z + 0.08, T)
        octa(m, 0.20, 0.20, Z - 0.01, Z + 0.035, "h_core")
        for sx in SIDES:
            for sy in SIDES:
                b = (tuple(sorted((sx * 0.25, sx * 0.44))), tuple(sorted((sy * 0.23, sy * 0.41))))
                t = (tuple(sorted((sx * 0.14, sx * 0.25))), tuple(sorted((sy * 0.13, sy * 0.23))))
                frustum(m, b, t, Z - 0.01, Z + 0.74, ST)
                for k in (0.30, 0.62):
                    cx, cy = 0.345 + (0.195 - 0.345) * k, 0.32 + (0.18 - 0.32) * k
                    w = 0.19 + (0.11 - 0.19) * k + 0.03
                    m.box((w, w, 0.05), (sx * cx, sy * cy, Z + 0.74 * k), LT)
                m.box((0.15, 0.14, 0.07), (sx * 0.195, sy * 0.18, Z + 0.765), TD, bevel=0.015)
        crystal(m, 0, 0, Z + 0.24, 0.19, "h_ore")


def big_arm(m, d, base, elbow, wrist, k=1.6):
    yb, zb = base
    m.cyl(0.13 * K * k, 0.10 * k, (0, d * yb, zb + 0.05 * k), TD, seg=8, rot=rad(22.5))
    m.box((0.14 * k, 0.16 * k, 0.14 * k), (0, d * yb, zb + 0.15 * k), G, bevel=0.02)
    sh = (yb, zb + 0.21 * k)
    m.cyl(0.095 * k, 0.21 * k, (0, d * yb, sh[1]), T, seg=8, axis="X")
    _pairs.link(m, d, sh, elbow, 0.055 * k, 0.07 * k, LT)
    m.cyl(0.08 * k, 0.19 * k, (0, d * elbow[0], elbow[1]), T, seg=8, axis="X")
    _pairs.link(m, d, elbow, wrist, 0.042 * k, 0.052 * k, LT)
    m.cyl(0.058 * k, 0.15 * k, (0, d * wrist[0], wrist[1]), T, seg=8, axis="X")
    m.box((0.11 * k, 0.04 * k, 0.14 * k), (0, d * (wrist[0] - 0.03 * k), wrist[1] - 0.105 * k), TD)


def assembler3(m):
    """Assembler, 3x3, first version: the lower works with the plain upper works."""
    _asm_lower(m)
    _asm_upper_v1(m)


def corrugated(m, x0, x1, y0, y1, z0, z1, faces, mk, pitch=0.15, depth=0.045):
    """A cabinet whose walls are themselves folded into ribs (like a transformer's tank), instead of bars
    stuck onto a flat wall. `faces` names the walls to fold: any of "ymin", "ymax", "xmax"."""
    def wave(a, b, n):
        (ax, ay), (bx_, by_) = a, b
        L = math.hypot(bx_ - ax, by_ - ay)
        tx, ty = (bx_ - ax) / L, (by_ - ay) / L
        k = max(1, int((L - 0.10) / pitch))
        gap = (L - k * pitch) / 2
        pts = []
        for i in range(k):
            s0 = gap + i * pitch + pitch * 0.22
            for s, dd in ((s0, 0.0), (s0 + pitch * 0.14, depth), (s0 + pitch * 0.42, depth), (s0 + pitch * 0.56, 0.0)):
                pts.append((ax + tx * s + n[0] * dd, ay + ty * s + n[1] * dd))
        return pts
    c = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    pts = [c[0]] + (wave(c[0], c[1], (0, -1)) if "ymin" in faces else []) + [c[1]]
    pts += (wave(c[1], c[2], (1, 0)) if "xmax" in faces else []) + [c[2]]
    pts += (wave(c[2], c[3], (0, 1)) if "ymax" in faces else []) + [c[3]]
    m.prism(pts, z0, z1, "Z", mk)


def cut_to(hx, hy, ref, off):
    """The corner cut for a block of half-sizes hx, hy stacked on (or under) the block ref = (hx, hy, cut),
    so that its cut corners stand `off` outside ref's cut corners (inside, when negative). Two stacked
    blocks whose corners are cut by unrelated amounts overhang evenly along the sides but not at the
    corners, where the lower one pokes out from under the upper."""
    return (hx + hy) - (ref[0] + ref[1]) + ref[2] - math.sqrt(2) * off


HALL = (0.50, 1.49, 0.035)                                   # the assembler's hall: half-sizes and corner cut
DECK_C = cut_to(0.53, 1.50, HALL, 0.02)                      # its deck's corners stand as far outside the hall's as its sides do


def _asm_lower(m):
    """Assembler, 3x3: two inputs side by side, one output. The hall, the mouths, a control cabin
    between the inputs and a power cabinet with folded walls at each back corner. Nothing small sticks
    out of it: doors and windows are sunk or framed in one piece, and no part overhangs another's edge."""
    from mathutils import Matrix
    for sy in SIDES:
        with m.at((0, sy * 1.0, 0)):
            run(m, -1.5, -0.5, braces=(-4 / 3, -1.0))
            cover(m, -0.5, -1)
    run(m, 0.5, 1.5, braces=(1.0, 4 / 3))
    cover(m, 0.5, 1)
    slab(m, 0.485, 1.475, 0.0, 0.18, cut_to(0.485, 1.475, HALL, -0.015), T, bevel=0.012)   # a dark kick strip, set back under the wall
    slab(m, 0.50, 1.49, 0.14, 0.86, HALL[2], G, bevel=0.02)
    slab(m, 0.53, 1.50, 0.82, 0.96, DECK_C, TD, bevel=0.025)
    for sy in SIDES:
        with frame(m, (0, sy * 1.5), (0, -sy)):               # x runs in from the cell's edge; the wall is at 0.01
            m.box((0.03, 0.50, 0.40), (0.02, 0, 0.42), G, bevel=0.012)                  # door, standing a little proud
            m.box((0.012, 0.012, 0.36), (0.006, 0, 0.42), SLIT)                          # the gap between its leaves
            for s in SIDES:
                m.box((0.012, 0.022, 0.13), (0.006, s * 0.055, 0.42), SLIT)              # grip slots, cut in
            m.box((0.012, 0.62, 0.09), (0.014, 0, 0.72), "h_glass")
            m.stack.append(m.stack[-1] @ Matrix(((0, 0, -1, 0.012), (-1, 0, 0, 0), (0, 1, 0, 0.72), (0, 0, 0, 1))))
            ring(m, 0.335, 0.07, [(0.0, 0.0), (0.008, 0.012), (0.022, 0.012), (0.03, 0.0)], D)
            m.stack.pop()
    # control cabin between the inputs, with a bezelled screen
    x0 = -1.15
    with m.at((-0.815, 0, 0)):
        cab = (0.335, 0.37, 0.04)
        slab(m, 0.345, 0.385, 0.0, 0.16, cut_to(0.345, 0.385, cab, 0.0125), T, bevel=0.012)
        slab(m, *cab[:2], 0.12, 0.90, cab[2], G, bevel=0.02)
        slab(m, 0.36, 0.395, 0.86, 0.97, cut_to(0.36, 0.395, cab, 0.025), TD, bevel=0.012)   # the chamfer is smaller than the overhang, so a flat soffit shows
    m.box((0.012, 0.50, 0.26), (x0 - 0.002, 0, 0.56), SLIT)
    m.stack.append(m.stack[-1] @ Matrix(((0, 0, -1, x0), (-1, 0, 0, 0), (0, 1, 0, 0.56), (0, 0, 0, 1))))
    ring(m, 0.315, 0.195, [(0.0, -0.002), (0.012, 0.034), (0.051, 0.034), (0.065, -0.002)], T)
    m.stack.pop()
    for i, w in enumerate((0.38, 0.24, 0.30)):
        m.box((0.008, w, 0.03), (x0 - 0.01, 0, 0.56 + (1 - i) * 0.07), "h_core")
    # a power cabinet at each back corner, lower than the deck: folded walls, and a ridge along its cap
    for sy in SIDES:
        y0, y1 = sorted((sy * 0.68, sy * 1.36))
        with m.at((0.98, sy * 1.02, 0)):
            slab(m, 0.41, 0.40, 0.0, 0.16, 0.04, T, bevel=0.012)
        corrugated(m, 0.60, 1.36, y0, y1, 0.12, 0.78, ("ymin" if sy < 0 else "ymax", "xmax"), ST)
        with m.at((0.98, sy * 1.02, 0)):
            slab(m, 0.42, 0.41, 0.74, 0.86, 0.07, TD, bevel=0.022)
        m.prism([(0.74, 0.85), (1.22, 0.85), (1.16, 0.93), (0.80, 0.93)], *sorted((sy * 0.82, sy * 1.22)), "Y", T)
        bx(m, (0.46, 0.64), tuple(sorted((sy * 0.88, sy * 1.16))), (0.44, 0.66), ST, bevel=0.035)


def _asm_upper_v1(m):
    """The first upper works: plain arches, plain arms. Kept for comparison."""
    Z = 0.96
    octa(m, 0.36, 0.36, Z - 0.01, Z + 0.08, T)
    octa(m, 0.29, 0.29, Z + 0.08, Z + 0.12, LT)
    m.box((0.34, 0.30, 0.20), (0, 0, Z + 0.22), ST, bevel=0.02)
    m.box((0.16, 0.12, 0.08), (0, 0, Z + 0.36), LT)
    for d in SIDES:
        big_arm(m, d, (0.80, Z - 0.01), (0.64, Z + 0.86), (0.17, Z + 0.56))
        bx(m, (-0.42, -0.08), tuple(sorted((d * 0.82, d * 1.18))), (Z - 0.01, Z + 0.10), T, bevel=0.02)
        m.box((0.12, 0.12, 0.10), (-0.33, d * 0.92, Z + 0.15), ST, bevel=0.015)
        m.box((0.12, 0.12, 0.10), (-0.17, d * 1.06, Z + 0.15), "h_copper", bevel=0.015)
    # two arches over the deck, tied by a spine
    with m.at((0, 0, 0.90)):
        for x in (-0.34, 0.34):
            m.prism(arch_pts(2.88, 1.32, hole_top=1.10, hw=1.22, c=0.36, ci=0.27), x - 0.075, x + 0.075, "X", ST)
            for s in SIDES:
                for y, z in ((s * 1.33, 0.30), (s * 1.33, 0.72)):
                    m.box((0.19, 0.25, 0.06), (x, y, z), LT)
    bx(m, (-0.44, 0.44), (-0.13, 0.13), (2.16, 2.32), TD, bevel=0.035)
    bx(m, (-0.10, 0.10), (-0.10, 0.10), (1.90, 2.18), T, bevel=0.03)
    m.cyl(0.09, 0.03, (0, 0, 1.885), "h_core", seg=10)
    # the finished frame slides down a chute into the output mouth
    m.prism([(0.33, Z + 0.07), (0.86, 0.86), (0.86, 0.78), (0.33, Z - 0.01)], -0.17, 0.17, "Y", T)
    for s in SIDES:
        a, b = sorted((s * 0.17, s * 0.225))
        m.prism([(0.33, Z + 0.17), (0.86, 0.96), (0.86, 0.78), (0.33, Z - 0.01)], a, b, "Y", G)


# ---- upper works built the way the mouths are: every member has a section, every joint a transition ----
def h_portal(m, x, w, top, leg, depth=0.20, web=0.07, c=0.34):
    """A portal frame of H section standing on z = 0: a thin web between an outer and an inner flange,
    the knees cut off at an angle, each leg on a tapered base. Build it inside m.at() to stand it on a deck."""
    hw, ht, ci = w / 2 - leg, top - leg, c - leg * 0.45
    f = 0.05                                                  # flange thickness
    m.prism(arch_pts(w - 2 * f, top - f, hole_top=ht + f, hw=hw + f, c=c - f * 0.4, ci=ci + f * 0.4), x - web / 2, x + web / 2, "X", TD)
    m.prism(arch_pts(w, top, hole_top=top - f, hw=w / 2 - f, c=c, ci=c - f * 0.45), x - depth / 2, x + depth / 2, "X", ST)
    m.prism(arch_pts(2 * (hw + f), ht + f, hole_top=ht, hw=hw, c=ci + f * 0.45, ci=ci), x - depth / 2, x + depth / 2, "X", ST)
    for s in SIDES:
        yc = s * (w / 2 - leg / 2)
        m.box((depth + 0.12, leg + 0.12, 0.09), (x, yc, 0.035), T, bevel=0.012, taper=0.80)


def offset_line(pts, f):
    """The polyline moved f to the right of its direction of travel, corners mitred."""
    out = []
    for i, (y, z) in enumerate(pts):
        ns = []
        for a, b in ((i - 1, i), (i, i + 1)):
            if 0 <= a and b < len(pts):
                dy, dz = pts[b][0] - pts[a][0], pts[b][1] - pts[a][1]
                L = math.hypot(dy, dz)
                ns.append((dz / L, -dy / L))
        ny, nz = sum(n[0] for n in ns) / len(ns), sum(n[1] for n in ns) / len(ns)
        L = math.hypot(ny, nz)
        k = f / (L * L) if len(ns) == 2 else f                # mitre: longer at a sharp corner
        out.append((y + ny * k, z + nz * k))
    return out


def sweep(m, x, line, section, mk):
    """Carry a cross-section along a polyline lying in the plane at x, mitring every corner. `section`
    lists (dx, t): dx along the belt, t the distance to the right of the line's direction of travel.
    Being lofted from quads, it has no joint lines and no stuck-together pieces."""
    import bmesh
    bm = bmesh.new()
    lines = {tt: offset_line(line, tt) for tt in {s[1] for s in section}}
    rows = [[bm.verts.new((x + dx, lines[tt][i][0], lines[tt][i][1])) for dx, tt in section] for i in range(len(line))]
    k = len(section)
    for a, b in zip(rows, rows[1:]):
        for j in range(k):
            bm.faces.new((a[j], a[(j + 1) % k], b[(j + 1) % k], b[j]))
    bm.faces.new(rows[0])
    bm.faces.new(rows[-1])
    m._add(bm, mk)


def plan(hx, hy, c):
    """A rectangle's outline with its four corners cut off by c, counter-clockwise."""
    return [(hx, -(hy - c)), (hx, hy - c), (hx - c, hy), (-(hx - c), hy), (-hx, hy - c), (-hx, -(hy - c)), (-(hx - c), -hy), (hx - c, -hy)]


def slab(m, hx, hy, z0, z1, c, mk, bevel=0.02):
    """A block whose four upright corners are cut off, and whose every edge is chamfered: no corner of
    it turns through a right angle."""
    bprism(m, plan(hx, hy, c), z0, z1, "Z", mk, bevel)


def ring(m, hx, hy, profile, mk, c=0.0):
    """A rim running round a rectangle (half-sizes hx, hy, corners cut off by c) in one piece, mitred at
    every corner. `profile` lists (u, z): u is the distance in from the rectangle's edge."""
    import bmesh
    bm = bmesh.new()
    base = plan(hx, hy, c) if c else [(hx, -hy), (hx, hy), (-hx, hy), (-hx, -hy)]
    lines = [offset_closed(base, u) for u, _ in profile]
    rows = [[bm.verts.new((lines[j][i][0], lines[j][i][1], profile[j][1])) for j in range(len(profile))] for i in range(len(base))]
    k = len(profile)
    for i in range(len(base)):
        a, b = rows[i], rows[(i + 1) % len(base)]
        for j in range(k):
            bm.faces.new((a[j], a[(j + 1) % k], b[(j + 1) % k], b[j]))
    m._add(bm, mk)


def portal2(m, x, depth=0.22):
    """A portal frame standing on z = 0, shaped rather than extruded square: its legs splay toward the
    foot, its knees turn in two cuts, its beam deepens toward the knees and rises to a crown. The
    section is an H (a dark web between two flanges) and every edge of the flanges is chamfered. Each
    leg stands on a low tapered base."""
    ky = 0.935                                                # the feet stand clear inside the deck's kerb
    r_out = [(y * ky, z) for y, z in ((0.0, 1.36), (0.55, 1.34), (1.06, 1.26), (1.26, 1.10), (1.36, 0.86), (1.44, 0.10), (1.44, 0.0))]
    r_in = [(y * ky, z) for y, z in ((1.14, 0.0), (1.10, 0.84), (0.92, 1.02), (0.60, 1.12), (0.0, 1.16))]
    P = [(-y, z) for y, z in reversed(r_out[1:])] + r_out     # left foot, over the crown, right foot
    Q = r_in + [(-y, z) for y, z in reversed(r_in[:-1])]      # right foot, under the beam, left foot
    f = 0.055
    m.prism(offset_line(P, 0.02) + offset_line(Q, 0.02), x - 0.035, x + 0.035, "X", TD)   # web, set back inside both flanges
    h, c = depth / 2, 0.022                                   # flange section: its two outer edges chamfered
    flange = [(-h, c), (-h + c, 0.0), (h - c, 0.0), (h, c), (h, f), (-h, f)]
    sweep(m, x, P, flange, ST)
    sweep(m, x, Q, flange, ST)
    for s in SIDES:                                           # a low tapered base under each foot, no wider than it must be
        m.box((depth + 0.07, 0.36, 0.07), (x, s * 1.206, 0.03), T, bevel=0.014, taper=0.82)


def taper_link(m, d, p, q, h0, h1, xh, mk):
    """A link that is deeper at p than at q."""
    (y0, z0), (y1, z1) = p, q
    L = math.hypot(y1 - y0, z1 - z0)
    ny, nz = -(z1 - z0) / L, (y1 - y0) / L
    m.prism([(d * (y0 + ny * h0), z0 + nz * h0), (d * (y1 + ny * h1), z1 + nz * h1), (d * (y1 - ny * h1), z1 - nz * h1),
             (d * (y0 - ny * h0), z0 - nz * h0)], -xh, xh, "X", mk)


def joint(m, d, y, z, r, xh):
    """A joint: a dark drum between the link's cheeks, with a lighter domed cap on each end."""
    m.cyl(r, 2 * xh + 0.05, (0, d * y, z), T, seg=10, axis="X")
    for sx in SIDES:
        m.cyl(r * 0.66, 0.035, (sx * (xh + 0.04), d * y, z), LT, seg=8, axis="X", r2=r * 0.40) if sx > 0 else \
            m.cyl(r * 0.40, 0.035, (sx * (xh + 0.04), d * y, z), LT, seg=8, axis="X", r2=r * 0.66)


def strut(m, x0, x1, y, z, r=0.05, mk=ST):
    """An eight-sided tie running along the belt between two frames, its ends buried in their webs."""
    m.cyl(r * K, x1 - x0, ((x0 + x1) / 2, y, z), mk, seg=8, axis="X", rot=(rad(22.5), 0, 0))


def arm4(m, d, yb, zb, elbow, wrist):
    """An arm on a stepped turret: yoke, a tapered upper link, a tapered forearm, a hand whose two
    fingers narrow toward their tips."""
    with m.at((0, d * yb, 0)):
        octa(m, 0.25, 0.25, zb - 0.01, zb + 0.07, T)
        octa(m, 0.20, 0.16, zb + 0.07, zb + 0.22, G)
        oct_ring(m, 0.22, 0.05, zb + 0.06, zb + 0.10, ST)
    sh = (yb, zb + 0.42)
    for sx in SIDES:                                          # yoke cheeks, cut back toward the top
        xs = sorted((sx * 0.095, sx * 0.16))
        m.prism([(d * yb - 0.12, zb + 0.20), (d * yb + 0.12, zb + 0.20), (d * yb + 0.07, zb + 0.52), (d * yb - 0.07, zb + 0.52)],
                xs[0], xs[1], "X", G)
    joint(m, d, sh[0], sh[1], 0.14, 0.095)
    taper_link(m, d, sh, elbow, 0.12, 0.085, 0.085, LT)
    ey, ez = elbow[0] - sh[0], elbow[1] - sh[1]               # a darker spine down the middle of the link, short of its ends
    taper_link(m, d, (sh[0] + ey * 0.04, sh[1] + ez * 0.04), (elbow[0] - ey * 0.04, elbow[1] - ez * 0.04), 0.065, 0.045, 0.097, ST)
    joint(m, d, elbow[0], elbow[1], 0.115, 0.085)
    taper_link(m, d, elbow, wrist, 0.08, 0.055, 0.068, LT)
    joint(m, d, wrist[0], wrist[1], 0.08, 0.068)
    wy, wz = wrist
    m.prism([(d * (wy - 0.075), wz - 0.05), (d * (wy + 0.045), wz - 0.05), (d * (wy + 0.03), wz - 0.17), (d * (wy - 0.06), wz - 0.17)],
            -0.085, 0.085, "X", TD)
    for sx in SIDES:
        xs = sorted((sx * 0.045, sx * 0.08))
        m.prism([(d * (wy - 0.05), wz - 0.16), (d * (wy + 0.02), wz - 0.16), (d * (wy - 0.002), wz - 0.31), (d * (wy - 0.03), wz - 0.31)],
                xs[0], xs[1], "X", LT)


def bin4(m, x, y, z, w=0.34, l=0.25, h=0.15):
    """An open parts bin: a wall that flares toward its rim, in one mitred piece, round a real hollow
    with a dark floor."""
    with m.at((x, y, 0)):
        ring(m, w * 0.6, l * 0.6, [(0.028, z - 0.005), (0.0, z + h - 0.005), (0.03, z + h - 0.005), (0.045, z + 0.045)], ST, c=0.02)
        m.box((w * 1.2 - 0.08, l * 1.2 - 0.08, 0.05), (0, 0, z + 0.02), SLIT)


def assembler4(m):
    """Assembler, 3x3, second version: the same lower works, with the upper works built like the mouths.
    Two H-section portals on tapered bases, tied by eight-sided struts, with a hoist rail and a work lamp under their crowns;
    the deck has a sloped kerb and seams; two tapered arms on stepped turrets work on the frame clamped
    to a rimmed turntable, each fed from a flared bin. The finished piece goes down through the hall to
    the output belt, as in every other machine; nothing carries it outside the body."""
    _asm_lower(m)
    Z = 0.96
    # deck: a kerb with a sloped inner face, running round the edge in one mitred piece; seams across the floor
    ring(m, 0.53, 1.50, [(0.0, Z - 0.02), (0.0, Z + 0.035), (0.025, Z + 0.06), (0.055, Z + 0.06), (0.10, Z - 0.02)], ST, c=DECK_C)
    for y in (-0.5, 0.5):                                     # the outer pair ran under the bins and showed at both sides of them
        m.box((0.82, 0.014, 0.006), (0, y, Z + 0.003), ST)
    # portals, tied by struts; a hoist rail with a work lamp hangs under their crowns
    with m.at((0, 0, Z)):
        for x in (-0.29, 0.29):
            portal2(m, x)
    for s in SIDES:
        strut(m, -0.29, 0.29, s * 1.19, Z + 0.62)
        strut(m, -0.29, 0.29, s * 0.75, Z + 1.20)
    m.prism([(-0.045, Z + 1.16), (0.045, Z + 1.16), (0.07, Z + 1.09), (-0.07, Z + 1.09)], -0.44, 0.44, "X", ST)
    bx(m, (-0.11, 0.11), (-0.13, 0.13), (Z + 0.97, Z + 1.10), G, bevel=0.035)
    m.cyl(0.075, 0.30, (0, 0, Z + 0.98), T, seg=8, axis="Y")
    m.cyl(0.085, 0.03, (0, 0, Z + 0.90), "h_core", seg=10)
    # turntable with the frame clamped to it
    octa(m, 0.40, 0.40, Z - 0.01, Z + 0.07, T)
    octa(m, 0.34, 0.31, Z + 0.07, Z + 0.14, ST)
    oct_ring(m, 0.36, 0.055, Z + 0.10, Z + 0.155, LT)
    m.box((0.44, 0.36, 0.20), (0, 0, Z + 0.23), G, bevel=0.035, taper=0.86)
    m.box((0.28, 0.20, 0.012), (0, 0, Z + 0.334), TD)
    m.box((0.16, 0.12, 0.08), (0, 0, Z + 0.375), "h_copper", bevel=0.02, taper=0.8)
    for d in SIDES:
        arm4(m, d, 0.70, Z, (0.56, Z + 1.04), (0.20, Z + 0.72))
        bin4(m, 0.0, d * 0.99, Z, w=0.25, l=0.22)
        m.box((0.10, 0.09, 0.08), (0.0, d * 0.99, Z + 0.08), "h_copper", bevel=0.018)      # a part lying on the bin's floor


from contextlib import contextmanager


@contextmanager
def on_side(m, d, y, zc, xc=0.0):
    """Build on a side wall: local x runs along the wall, local y up it, local z out of it. The frame is
    a proper rotation on both sides of the belt, so what is built is mirrored exactly."""
    from mathutils import Matrix
    m.stack.append(m.stack[-1] @ Matrix(((-d, 0, 0, xc), (0, 0, d, y), (0, 1, 0, zc), (0, 0, 0, 1))))
    yield
    m.stack.pop()


def smelter3(m):
    """Smelter, 3x1. Concept: ore goes into the fire and comes out as an ingot; the machine is a fire
    with a pot of melting metal on it.
    It is built as one assembled machine, not as things set on one another. One dark chassis grips both
    rails from one mouth's end frame to the other's; the mouths' folds and the firebox stand on
    it. The firebox rises into a hood whose sides slope in to a flat crown; the pot is seated on the
    crown by its own flared foot, and so is the uptake at each side of it; nothing lies on anything as a
    plate. The pot's belly swells and draws in to a thick rim with the melt glowing inside. Each side
    wall has one fire mouth, the fire set back behind bars inside a one-piece frame."""
    run(m, -1.5, 1.5, braces=(-4 / 3, -1.0, 1.0, 4 / 3))
    cover(m, BX, 1, sole=False)
    cover(m, -BX, -1, sole=False)
    collar(m, -BX - 0.318, BX + 0.318, mk=T)                  # the chassis, ending just behind each end frame
    hy = 0.40
    slab(m, BX, hy, 0.37, 0.70, 0.022, G, bevel=0.02)         # firebox, its foot inside the chassis
    # the hood: the firebox's own top, sloping in from both side walls to a flat crown
    bprism(m, [(-hy, 0.70), (-hy, 0.74), (-0.30, 0.90), (0.30, 0.90), (hy, 0.74), (hy, 0.70)], -BX, BX, "X", TD, bevel=0.016)
    for d in SIDES:                                           # fire mouth: glow at the back, bars on it, the frame round them
        with on_side(m, d, d * hy, 0.543):
            m.box((0.27, 0.15, 0.008), (0, 0, 0.002), "h_glow")
            for k in range(4):                                # bars of a tapered section, their ends set into the frame
                x = -0.09 + k * 0.06
                m.prism([(x - 0.016, 0.004), (x + 0.016, 0.004), (x + 0.008, 0.021), (x - 0.008, 0.021)], -0.10, 0.10, "Y", TD)
            ring(m, 0.185, 0.125, [(0.0, -0.004), (0.012, 0.034), (0.036, 0.034), (0.05, -0.004)], T, c=0.04)
    P = 0.90                                                  # the crown
    octa(m, 0.24, 0.19, P, P + 0.08, T)                       # the pot's flared foot, seated on the crown
    octa(m, 0.19, 0.235, P + 0.08, P + 0.24, ST)
    octa(m, 0.235, 0.25, P + 0.24, P + 0.29, LT)
    octa(m, 0.25, 0.235, P + 0.29, P + 0.34, LT)
    octa(m, 0.235, 0.19, P + 0.34, P + 0.52, ST)
    octa(m, 0.19, 0.23, P + 0.52, P + 0.58, TD)
    oct_ring(m, 0.23, 0.06, P + 0.58, P + 0.64, TD)
    octa(m, 0.168, 0.168, P + 0.58, P + 0.61, "h_glow")
    for sx in SIDES:                                          # an uptake each side, on its own flared foot, clear of the pot
        with m.at((sx * 0.37, 0, 0)):
            octa(m, 0.095, 0.072, P, P + 0.08, T)
            octa(m, 0.072, 0.058, P + 0.08, P + 0.72, ST)
            octa(m, 0.058, 0.10, P + 0.72, P + 0.78, TD)       # the cap flares, then a rim stands on it round a real hollow
            oct_ring(m, 0.10, 0.028, P + 0.78, P + 0.82, TD)
            octa(m, 0.076, 0.076, P + 0.75, P + 0.785, SLIT)   # the dark of the flue, down inside the rim


def shell(m, stations, mk):
    """One closed piece through a loop of rectangular outlines: `stations` lists (hx, hy, corner cut, z)
    going up the outside, across the rim and down the inside, so a vessel's wall, rim and hollow are a
    single mitred piece. Like `ring`, but each station has its own half-sizes."""
    import bmesh
    bm = bmesh.new()
    rows = [[bm.verts.new((x, y, z)) for x, y in plan(hx, hy, c)] for hx, hy, c, z in stations]
    n, k = len(rows), len(rows[0])
    for i in range(n):
        a, b = rows[i], rows[(i + 1) % n]
        for j in range(k):
            bm.faces.new((a[j], a[(j + 1) % k], b[(j + 1) % k], b[j]))
    m._add(bm, mk)


def crusher3(m):
    """Crusher, 3x1. Concept: stone and ore drop between two toothed rolls turning into each other and
    come out broken small; the machine is an open hopper with the rolls turning in it.
    A dark chassis grips both rails. The crush box on it leans in toward a waist. From the waist rises
    one dark piece: the roll housing, upright, then the hopper spreading wide above the mouths, over a
    lip and a rim and down inside as a funnel to the throat, a real hollow. Two long toothed rolls lie
    across the throat, a tooth of one in a gap of the other, with ore lying in the nip. Each roll's
    shaft runs into the housing's side walls, and where it does the wall carries a bearing housing with
    its cap, the same on both sides."""
    run(m, -1.5, 1.5, braces=(-4 / 3, -1.0, 1.0, 4 / 3))
    cover(m, BX, 1, sole=False)
    cover(m, -BX, -1, sole=False)
    collar(m, -BX - 0.318, BX + 0.318, mk=T)                  # the chassis
    # crush box: leans in from the chassis to a waist
    bprism(m, [(-0.40, 0.37), (0.40, 0.37), (0.37, 0.66), (-0.37, 0.66)], -BX, BX, "X", G, bevel=0.02)
    # roll housing and hopper in one: out from the waist, up, spreading, over the lip and rim, down the funnel to the throat
    shell(m, [(BX, 0.37, 0.004, 0.66), (BX, 0.40, 0.025, 0.70), (BX, 0.40, 0.025, 1.03), (0.60, 0.49, 0.06, 1.21),
              (0.60, 0.49, 0.06, 1.25), (0.58, 0.47, 0.055, 1.27), (0.55, 0.44, 0.05, 1.27),
              (0.30, 0.25, 0.02, 0.92), (0.30, 0.25, 0.02, 0.76)], TD)
    slab(m, 0.31, 0.26, 0.66, 0.765, 0.02, SLIT, bevel=0.004)  # the dark of the throat, at the bottom of the hollow
    zr, xr, rr = 0.93, 0.135, 0.14
    for sx in SIDES:                                          # the rolls: a tooth of one lies in a gap of the other
        gear(m, rr, 0.43, (sx * xr, 0, zr), LT, teeth=12, half_step=sx > 0)
        m.cyl(0.038 * K, 0.78, (sx * xr, 0, zr), T, seg=8, axis="Y", rot=(0, rad(22.5), 0))    # shaft, its ends inside the walls
        for d in SIDES:                                       # bearing housing and cap where the shaft meets the wall
            big, small = (0.10 * K, 0.08 * K), (0.05 * K, 0.038 * K)
            for (r_in, r_out), y, depth, mk in ((big, 0.415, 0.04, ST), (small, 0.44, 0.014, LT)):
                r1, r2 = (r_in, r_out) if d > 0 else (r_out, r_in)
                m.cyl(r1, depth, (sx * xr, d * y, zr), mk, seg=8, axis="Y", r2=r2, rot=(0, rad(22.5), 0))
    for x, y, r in ((0.0, -0.10, 0.055), (0.012, 0.08, 0.045), (-0.006, -0.005, 0.036)):    # ore lying in the nip between the rolls
        m.ico(r, (x, y, zr + math.sqrt((rr + r) ** 2 - xr ** 2) + 0.004), "h_ore", squash=0.85, jitter=0.12)


crusher3.frame, crusher3.shadow = F31, True
_hero.HEROES["crusher3"] = crusher3

smelter3.frame, smelter3.shadow = F31, True
_hero.HEROES["smelter3"] = smelter3


def smelter4(m):
    """Smelter, 3x1, grade 2 (hitbox 3x1x2). Concept: ore goes into the fire, melts, and sets into an
    ingot on its way out; the machine is a fire with a pot of melting metal on it, and the melt can be
    followed from the pot to the mould.
    One dark chassis grips both rails. The firebox on it has a pier at each end and a wall set back
    between them, where the fire mouth sits behind its bars in a one-piece frame. The firebox rises
    into a hood. On the hood's crown, from the end the ore comes in to the end the ingot leaves: the
    stack, on its flared foot; the pot, its belly swelling and drawing in to a rim round the glowing
    melt; a spout running down from the pot's neck; and the mould box the spout pours into, a real
    hollow with the melt lying in it. The two sides of the belt are the same."""
    run(m, -1.5, 1.5, braces=(-4 / 3, -1.0, 1.0, 4 / 3))
    cover(m, BX, 1, sole=False)
    cover(m, -BX, -1, sole=False)
    collar(m, -BX - 0.318, BX + 0.318, mk=T)                  # the chassis
    hy, hc, xp = 0.40, 0.355, 0.30                            # pier face, the wall set back between the piers, where a pier begins
    bprism(m, [(-xp, -hc), (xp, -hc), (xp, hc), (-xp, hc)], 0.37, 0.70, "Z", G, bevel=0.012)    # fire wall
    for sx in SIDES:                                          # a pier at each end, beside the mouth's folds
        with m.at((sx * (xp + BX) / 2, 0, 0)):
            slab(m, (BX - xp) / 2, hy, 0.37, 0.70, 0.02, G, bevel=0.018)
    # the hood: the firebox's own top, sloping in from both side walls to a flat crown
    bprism(m, [(-hy, 0.70), (-hy, 0.74), (-0.30, 0.90), (0.30, 0.90), (hy, 0.74), (hy, 0.70)], -BX, BX, "X", TD, bevel=0.016)
    for d in SIDES:                                           # fire mouth, set in between the piers
        with on_side(m, d, d * hc, 0.535):
            m.box((0.27, 0.15, 0.008), (0, 0, 0.002), "h_glow")
            for k in range(4):                                # bars of a tapered section, their ends set into the frame
                x = -0.09 + k * 0.06
                m.prism([(x - 0.016, 0.004), (x + 0.016, 0.004), (x + 0.008, 0.019), (x - 0.008, 0.019)], -0.10, 0.10, "Y", TD)
            ring(m, 0.185, 0.125, [(0.0, -0.004), (0.012, 0.03), (0.036, 0.03), (0.05, -0.004)], T, c=0.04)
    P = 0.90                                                  # the crown
    xs, xq, xb = -0.36, -0.02, 0.385                          # stack, pot, mould box
    with m.at((xs, 0, 0)):                                    # the stack, at the end the ore comes in
        octa(m, 0.105, 0.085, P, P + 0.08, T)
        octa(m, 0.085, 0.068, P + 0.08, P + 0.78, ST)
        octa(m, 0.068, 0.105, P + 0.78, P + 0.86, TD)         # the cap flares, then a rim stands on it round a real hollow
        oct_ring(m, 0.105, 0.03, P + 0.86, P + 0.90, TD)
        octa(m, 0.078, 0.078, P + 0.83, P + 0.865, SLIT)
    with m.at((xq, 0, 0)):                                    # the pot
        octa(m, 0.21, 0.17, P, P + 0.08, T)
        octa(m, 0.17, 0.215, P + 0.08, P + 0.24, ST)
        octa(m, 0.215, 0.23, P + 0.24, P + 0.29, LT)
        octa(m, 0.23, 0.215, P + 0.29, P + 0.34, LT)
        octa(m, 0.215, 0.175, P + 0.34, P + 0.50, ST)
        octa(m, 0.175, 0.21, P + 0.50, P + 0.56, TD)
        oct_ring(m, 0.21, 0.055, P + 0.56, P + 0.62, TD)
        octa(m, 0.152, 0.152, P + 0.555, P + 0.59, "h_glow")
    # the spout: a channel from the pot's neck down to over the mould box, the melt running in it
    with m.at((0, 0, 0), rz=rad(90)):                         # in here the channel runs along local -y, and local x is across the belt
        lo, hi = (-xb, P + 0.27), (-(xq + 0.185), P + 0.545)   # from over the middle of the mould box up to the pot's neck
        sweep(m, 0, [lo, hi], [(-0.05, 0.0), (-0.035, 0.0), (-0.035, 0.03), (0.035, 0.03), (0.035, 0.0), (0.05, 0.0),
                               (0.05, 0.03), (0.035, 0.045), (-0.035, 0.045), (-0.05, 0.03)], TD)
        sweep(m, 0, [(lo[0] + 0.006, lo[1] + 0.008), hi], [(-0.037, 0.016), (0.037, 0.016), (0.037, 0.036), (-0.037, 0.036)], "h_glow")
    with m.at((xb, 0, 0)):                                    # the mould box: the melt lies in it and sets
        shell(m, [(0.066, 0.14, 0.02, P), (0.078, 0.152, 0.022, P + 0.20), (0.066, 0.14, 0.02, P + 0.225),
                  (0.05, 0.124, 0.015, P + 0.225), (0.04, 0.115, 0.012, P + 0.15), (0.04, 0.115, 0.012, P + 0.02)], T)
        slab(m, 0.045, 0.12, P + 0.02, P + 0.17, 0.012, "h_glow", bevel=0.003)


smelter4.frame, smelter4.shadow = F31, True
_hero.HEROES["smelter4"] = smelter4


# ---- square-cut trials of the smelter's upper works (the developer found the octagonal pot weak) ----
def tower(m, stations, mk):
    """A solid through rectangular outlines with cut corners: `stations` lists (hx, hy, corner cut, z)
    going up. Lofted, with a cap at each end."""
    import bmesh
    bm = bmesh.new()
    rows = [[bm.verts.new((x, y, z)) for x, y in plan(hx, hy, c)] for hx, hy, c, z in stations]
    k = len(rows[0])
    for a, b in zip(rows, rows[1:]):
        for j in range(k):
            bm.faces.new((a[j], a[(j + 1) % k], b[(j + 1) % k], b[j]))
    bm.faces.new(rows[0])
    bm.faces.new(rows[-1])
    m._add(bm, mk)


def _smelt_lower(m):
    """The smelter below the crown: chassis, firebox with end piers, fire mouths, hood. Returns the crown's height.
    The firebox's blocks run up a little way into the hood and the hood's eave stands out past them, so
    the joint under the eave is one clean line. (With the blocks stopping flush under a hood no wider
    than they were, each cut corner of a pier showed a dark chip of the hood's underside.)"""
    run(m, -1.5, 1.5, braces=(-4 / 3, -1.0, 1.0, 4 / 3))
    cover(m, BX, 1, sole=False)
    cover(m, -BX, -1, sole=False)
    collar(m, -BX - 0.318, BX + 0.318, mk=T)
    hy, hc, xp, he, top = 0.40, 0.355, 0.30, 0.408, 0.712
    bprism(m, [(-xp, -hc), (xp, -hc), (xp, hc), (-xp, hc)], 0.37, top, "Z", G, bevel=0.012)
    for sx in SIDES:
        x0, x1 = sorted((sx * xp, sx * BX))
        bprism(m, [(x0, -hy), (x1, -hy), (x1, hy), (x0, hy)], 0.37, top, "Z", G, bevel=0.012)
    bprism(m, [(-he, 0.70), (-he, 0.74), (-0.30, 0.90), (0.30, 0.90), (he, 0.74), (he, 0.70)], -BX, BX, "X", TD, bevel=0.016)
    for d in SIDES:
        with on_side(m, d, d * hc, 0.535):
            m.box((0.27, 0.15, 0.008), (0, 0, 0.002), "h_glow")
            for k in range(4):
                x = -0.09 + k * 0.06
                m.prism([(x - 0.016, 0.004), (x + 0.016, 0.004), (x + 0.008, 0.019), (x - 0.008, 0.019)], -0.10, 0.10, "Y", TD)
            ring(m, 0.185, 0.125, [(0.0, -0.004), (0.012, 0.03), (0.036, 0.03), (0.05, -0.004)], T, c=0.04)
    return 0.90


def sq_stack(m, x, z0, top):
    """A square stack with cut corners on a flared foot, its cap a rim round a real hollow."""
    with m.at((x, 0, 0)):
        tower(m, [(0.105, 0.105, 0.03, z0), (0.085, 0.085, 0.025, z0 + 0.08)], T)
        tower(m, [(0.085, 0.085, 0.025, z0 + 0.08), (0.066, 0.066, 0.02, top - 0.13)], ST)
        tower(m, [(0.066, 0.066, 0.02, top - 0.13), (0.10, 0.10, 0.03, top - 0.05)], TD)
        shell(m, [(0.10, 0.10, 0.03, top - 0.05), (0.10, 0.10, 0.03, top), (0.076, 0.076, 0.022, top), (0.07, 0.07, 0.02, top - 0.045)], TD)
        tower(m, [(0.073, 0.073, 0.02, top - 0.07), (0.073, 0.073, 0.02, top - 0.04)], SLIT)


def pour(m, hi, xb, P):
    """A spout from the point hi = (x, z) down to over the middle of the mould box at xb, and the box."""
    with m.at((0, 0, 0), rz=rad(90)):
        lo, up = (-xb, P + 0.27), (-hi[0], hi[1])
        sweep(m, 0, [lo, up], [(-0.05, 0.0), (-0.035, 0.0), (-0.035, 0.03), (0.035, 0.03), (0.035, 0.0), (0.05, 0.0),
                               (0.05, 0.03), (0.035, 0.045), (-0.035, 0.045), (-0.05, 0.03)], TD)
        sweep(m, 0, [(lo[0] + 0.006, lo[1] + 0.004), up], [(-0.037, 0.016), (0.037, 0.016), (0.037, 0.036), (-0.037, 0.036)], "h_glow")
    with m.at((xb, 0, 0)):
        shell(m, [(0.066, 0.14, 0.02, P), (0.078, 0.152, 0.022, P + 0.20), (0.066, 0.14, 0.02, P + 0.225),
                  (0.05, 0.124, 0.015, P + 0.225), (0.04, 0.115, 0.012, P + 0.15), (0.04, 0.115, 0.012, P + 0.02)], T)
        slab(m, 0.045, 0.12, P + 0.02, P + 0.17, 0.012, "h_glow", bevel=0.003)


def smelter5a(m):
    """Trial A: the pot made square. A flared square crucible on a foot, a dark rim round the melt."""
    P = _smelt_lower(m)
    xs, xq, xb = -0.36, -0.03, 0.385
    sq_stack(m, xs, P, P + 0.90)
    with m.at((xq, 0, 0)):
        tower(m, [(0.20, 0.19, 0.04, P), (0.165, 0.155, 0.035, P + 0.07)], T)
        shell(m, [(0.165, 0.155, 0.035, P + 0.07), (0.225, 0.21, 0.045, P + 0.30), (0.225, 0.21, 0.045, P + 0.40),
                  (0.16, 0.145, 0.03, P + 0.40), (0.15, 0.135, 0.025, P + 0.12)], ST)
        shell(m, [(0.24, 0.225, 0.05, P + 0.40), (0.24, 0.225, 0.05, P + 0.45), (0.225, 0.21, 0.045, P + 0.47),
                  (0.185, 0.17, 0.035, P + 0.47), (0.168, 0.153, 0.03, P + 0.40)], TD)
        tower(m, [(0.156, 0.141, 0.026, P + 0.09), (0.156, 0.141, 0.026, P + 0.425)], "h_glow")
    pour(m, (xq + 0.215, P + 0.395), xb, P)


def smelter5b(m):
    """Trial B: no open vessel. A square furnace head on the hood with an eight-sided sight port glowing on
    each side, a dark cap, the stack on the cap, and a tap spout from its end to the mould box."""
    P = _smelt_lower(m)
    xh, xb = -0.07, 0.385
    head = (0.29, 0.235, 0.04)
    with m.at((xh, 0, 0)):
        slab(m, head[0], head[1], P, P + 0.40, head[2], G, bevel=0.02)
        slab(m, 0.31, 0.255, P + 0.40, P + 0.47, cut_to(0.31, 0.255, head, 0.02), TD, bevel=0.014)
    for d in SIDES:
        with on_side(m, d, d * head[1], P + 0.20, xc=xh):
            octa(m, 0.105, 0.105, -0.002, 0.008, "h_glow")
            oct_ring(m, 0.14, 0.04, -0.004, 0.03, T)
    sq_stack(m, xh, P + 0.47, P + 0.97)
    pour(m, (xh + head[0] - 0.02, P + 0.34), xb, P)


def smelter5c(m):
    """Trial C: a ladle hung on trunnions. A flared square ladle between two brackets, a pin each side
    with its cap, the melt glowing inside a dark rim; the spout runs from its lip to the mould box."""
    P = _smelt_lower(m)
    xs, xq, xb = -0.36, -0.03, 0.385
    sq_stack(m, xs, P, P + 0.90)
    zp = P + 0.31                                             # the trunnions' height
    for d in SIDES:
        ys = sorted((d * 0.225, d * 0.275))
        bprism(m, [(xq - 0.11, P), (xq + 0.11, P), (xq + 0.05, P + 0.42), (xq - 0.05, P + 0.42)], ys[0], ys[1], "Y", T, bevel=0.012)
        m.cyl(0.036 * K, 0.14, (xq, d * 0.225, zp), ST, seg=8, axis="Y", rot=(0, rad(22.5), 0))
        r1, r2 = (0.052 * K, 0.04 * K) if d > 0 else (0.04 * K, 0.052 * K)
        m.cyl(r1, 0.016, (xq, d * 0.283, zp), LT, seg=8, axis="Y", r2=r2, rot=(0, rad(22.5), 0))
    with m.at((xq, 0, 0)):
        tower(m, [(0.105, 0.095, 0.03, P + 0.08), (0.13, 0.12, 0.03, P + 0.11)], ST)
        shell(m, [(0.13, 0.12, 0.03, P + 0.11), (0.20, 0.17, 0.04, P + 0.34), (0.20, 0.17, 0.04, P + 0.42),
                  (0.15, 0.12, 0.03, P + 0.42), (0.125, 0.10, 0.02, P + 0.17)], ST)
        shell(m, [(0.215, 0.185, 0.045, P + 0.42), (0.215, 0.185, 0.045, P + 0.46), (0.20, 0.17, 0.04, P + 0.48),
                  (0.165, 0.135, 0.03, P + 0.48), (0.155, 0.125, 0.03, P + 0.42)], TD)
        tower(m, [(0.13, 0.105, 0.022, P + 0.14), (0.14, 0.11, 0.025, P + 0.44)], "h_glow")
    pour(m, (xq + 0.19, P + 0.415), xb, P)


@contextmanager
def on_end(m, sx, x, y, z):
    """Build on a face that looks along the belt: local z runs out of it (toward sx), local y is up."""
    from mathutils import Matrix
    m.stack.append(m.stack[-1] @ Matrix(((0, 0, sx, x), (sx, 0, 0, y), (0, 1, 0, z), (0, 0, 0, 1))))
    yield
    m.stack.pop()


def smelter6(m):
    """Smelter, 3x1, grade 2 (hitbox 3x1x2). The developer dropped the pot and asked for something with
    more presence: it may be lopsided, and it should have pipes.
    Concept as before: ore goes into the fire, melts, and sets into an ingot on its way out. On the
    hood's crown stand, not in a row but as a group: a square steel melting chamber on a flared foot
    under a dark cap, a glowing eight-sided sight port in its front; a tall square stack at the back
    corner, fed from the chamber's cap by a duct that rises, turns and runs into it; a blower at the
    front corner, a drum with a rimmed intake at one end and its motor at the other, whose air pipe
    runs out over the eave, down the wall and into the firebox's pier; and at the far end the tap
    spout running down from the chamber into the mould box. Every pipe carries something and is joined
    at both ends through a flange."""
    P = _smelt_lower(m)
    xh, yh = 0.045, 0.08                                      # melting chamber: upright below, its shoulders drawing in to the cap
    head, neck = (0.20, 0.19, 0.04), (0.15, 0.14, 0.035)
    with m.at((xh, yh, 0)):
        tower(m, [(0.225, 0.215, 0.05, P), (head[0], head[1], head[2], P + 0.06)], T)
        tower(m, [(head[0], head[1], head[2], P + 0.06), (head[0], head[1], head[2], P + 0.34), (neck[0], neck[1], neck[2], P + 0.46)], ST)
        slab(m, 0.17, 0.16, P + 0.46, P + 0.53, cut_to(0.17, 0.16, neck, 0.02), TD, bevel=0.014)
    with on_side(m, -1, yh - head[1], P + 0.20, xc=xh):       # sight port in the front
        octa(m, 0.09, 0.09, -0.002, 0.008, "h_glow")
        oct_ring(m, 0.125, 0.04, -0.004, 0.03, T)
    # stack at the back corner, and the duct that feeds it from the chamber's cap
    xs, ys, top = -0.345, 0.185, 1.92
    with m.at((0, ys, 0)):
        sq_stack(m, xs, P, top)
    xd, zd, rd = -0.02, P + 0.68, 0.05                        # where the duct leaves the cap, the height it runs at, its radius
    with m.at((0, 0, 0), rz=rad(90)):                         # in here local x is across the belt and the duct runs along local +y
        side_pipe(m, ys, [(-xd, P + 0.50), (-xd, zd - 0.045), (-xd + 0.045, zd), (-xs - 0.03, zd)], rd, ST)
    m.cyl(rd * 1.36, 0.03, (xd, ys, P + 0.545), T, seg=8)                                     # flange on the cap
    m.cyl(rd * 1.36, 0.03, (xs + 0.085, ys, zd), T, seg=8, axis="X")                         # flange on the stack
    # blower at the front corner: drum, rimmed intake, motor, and the air pipe into the firebox's pier
    xw, yw, zw, rw = -0.325, -0.185, P + 0.13, 0.108
    with m.at((xw, yw, 0)):
        tower(m, [(0.085, 0.09, 0.025, P), (0.065, 0.07, 0.02, P + 0.06)], T)
    m.cyl(rw * K, 0.19, (xw, yw, zw), ST, seg=8, axis="X", rot=(rad(22.5), 0, 0))
    with on_end(m, -1, xw - 0.095, yw, zw):                   # intake: a rim round a real hollow
        oct_ring(m, rw, 0.036, 0.0, 0.03, T)
        octa(m, 0.075, 0.075, -0.02, 0.004, SLIT)
    with on_end(m, 1, xw + 0.095, yw, zw):                    # the fan's hub, on the end away from the intake
        octa(m, 0.05, 0.04, 0.0, 0.022, LT)
    xa, ya, ra, za = -0.36, -0.455, 0.035, 0.555              # the air pipe: its plane, the wall run, its radius, where it enters the pier
    side_pipe(m, xa, [(yw - 0.03, zw), (ya + 0.045, zw), (ya, zw - 0.045), (ya, za + 0.045), (ya + 0.045, za), (-0.385, za)], ra, ST)
    m.cyl(ra * 1.4, 0.028, (xa, yw - rw - 0.012, zw), T, seg=8, axis="Y")                   # flange on the drum
    m.cyl(ra * 1.4, 0.028, (xa, -0.412, za), T, seg=8, axis="Y")                             # flange on the pier
    # tap: the spout from the chamber's far end down into the mould box
    pour(m, (xh + head[0] - 0.02, P + 0.36), 0.385, P)


smelter6.frame, smelter6.shadow = F31, True
_hero.HEROES["smelter6"] = smelter6

def smelter7(m):
    """Smelter, 3x1, grade 2 (hitbox 3x1x2). The developer found the upright chamber of smelter6 the
    weak part and asked for something lying wide instead.
    On the hood's crown lies a long, low melting chamber: a flared foot, a short upright wall with two
    glowing eight-sided sight ports, shoulders drawing in to a long dark cap. The stack rises from the
    cap at the end the ore comes in. In front of the chamber lies the blower, a drum with a rimmed
    intake, whose air pipe runs out over the eave, down the wall and into the firebox's pier. At the
    far end the tap spout runs from under the cap into the mould box."""
    P = _smelt_lower(m)
    xh, yh = -0.06, 0.10
    wall, neck = (0.31, 0.17, 0.04), (0.26, 0.115, 0.035)
    with m.at((xh, yh, 0)):
        tower(m, [(0.335, 0.195, 0.05, P), (wall[0], wall[1], wall[2], P + 0.05)], T)
        tower(m, [(wall[0], wall[1], wall[2], P + 0.05), (wall[0], wall[1], wall[2], P + 0.24), (neck[0], neck[1], neck[2], P + 0.33)], ST)
        slab(m, 0.275, 0.13, P + 0.33, P + 0.385, cut_to(0.275, 0.13, neck, 0.015), TD, bevel=0.012)
    for x in (-0.03, 0.125):                                  # sight ports in the front, clear of the blower
        with on_side(m, -1, yh - wall[1], P + 0.145, xc=x):
            octa(m, 0.042, 0.042, -0.002, 0.008, "h_glow")
            oct_ring(m, 0.068, 0.03, -0.004, 0.026, T)
    with m.at((0, yh, 0)):                                    # the stack, standing on the cap at the end the ore comes in
        sq_stack(m, -0.21, P + 0.385, 1.92)
    # blower in front of the chamber: drum, rimmed intake, hub, and the air pipe into the firebox's pier
    xw, yw, zw, rw = -0.28, -0.20, P + 0.115, 0.09
    with m.at((xw, yw, 0)):
        tower(m, [(0.085, 0.08, 0.025, P), (0.065, 0.06, 0.02, P + 0.055)], T)
    m.cyl(rw * K, 0.20, (xw, yw, zw), ST, seg=8, axis="X", rot=(rad(22.5), 0, 0))
    with on_end(m, -1, xw - 0.10, yw, zw):
        oct_ring(m, rw, 0.032, 0.0, 0.03, T)
        octa(m, 0.062, 0.062, -0.02, 0.004, SLIT)
    with on_end(m, 1, xw + 0.10, yw, zw):
        octa(m, 0.045, 0.036, 0.0, 0.022, LT)
    xa, ya, ra, za = -0.34, -0.455, 0.035, 0.555
    side_pipe(m, xa, [(yw - 0.03, zw), (ya + 0.045, zw), (ya, zw - 0.045), (ya, za + 0.045), (ya + 0.045, za), (-0.385, za)], ra, ST)
    m.cyl(ra * 1.4, 0.028, (xa, yw - rw - 0.012, zw), T, seg=8, axis="Y")
    m.cyl(ra * 1.4, 0.028, (xa, -0.412, za), T, seg=8, axis="Y")
    with m.at((0, 0.06, 0)):                                  # tap spout and mould box at the far end
        pour(m, (xh + neck[0], P + 0.35), 0.39, P)


smelter7.frame, smelter7.shadow = F31, True
_hero.HEROES["smelter7"] = smelter7

def smelter8(m):
    """Smelter, 3x1, grade 2 (hitbox 3x1x2). After the upright vessels failed, the developer pointed to
    the Islands smelter as a guide to the kind of thing wanted, not to be copied: there the star is a
    wide box open at the top, the fire seen through a grate, with pipes and small works set about it.
    Ours keeps its own body (chassis, piered firebox with its fire mouth, sloped hood) and puts on the
    crown a wide hearth box that spreads toward its rim: a flared foot, light walls leaning out, a dark
    rim round a real hollow where the fire lies under a row of bars, and a glowing tap port in its far
    end. At the far end's front corner stands the blower, a square fan casing whose open top is its intake.
    One air pipe runs from it the length of the hearth, sends two branches square into its wall, then
    turns out over the eave and drops into a boot on the near pier; a second crosses the far end, turns
    over the back eave and drops into a boot on the far pier, so neither side is bare. (A tap spout and mould box stood at the far end; the developer asked what they
    were, and they are gone. The ingot leaves by the belt like everything else.)"""
    P = _smelt_lower(m)
    xt, yt = -0.07, 0.03                                      # the hearth box
    with m.at((xt, yt, 0)):
        tower(m, [(0.325, 0.225, 0.05, P), (0.30, 0.20, 0.045, P + 0.05)], T)
        tower(m, [(0.30, 0.20, 0.045, P + 0.05), (0.34, 0.24, 0.05, P + 0.40), (0.34, 0.24, 0.05, P + 0.412)], G)   # the wall runs a little way up into the rim
        shell(m, [(0.355, 0.255, 0.055, P + 0.40), (0.355, 0.255, 0.055, P + 0.445), (0.34, 0.24, 0.05, P + 0.46),
                  (0.295, 0.195, 0.035, P + 0.46), (0.285, 0.185, 0.03, P + 0.40)], TD)
        tower(m, [(0.292, 0.192, 0.03, P + 0.395), (0.292, 0.192, 0.03, P + 0.415)], "h_glow")
        for k in range(7):                                    # bars across the hearth, their ends set into the rim
            x = -0.24 + k * 0.08
            m.prism([(x - 0.02, P + 0.41), (x + 0.02, P + 0.41), (x + 0.011, P + 0.44), (x - 0.011, P + 0.44)], -0.20, 0.20, "Y", TD)
    # blower at the front corner of the far end: a square fan casing on a foot under a dark cap, its rimmed intake facing out
    xw, yw, zw, rw = 0.385, -0.19, P + 0.14, 0.07
    case = (0.08, 0.10, 0.025)
    with m.at((xw, yw, 0)):
        tower(m, [(0.085, 0.11, 0.03, P), (case[0], case[1], case[2], P + 0.04)], T)
        slab(m, case[0], case[1], P + 0.04, P + 0.25, case[2], ST, bevel=0.01)
        # the intake is the casing's open top: a rim round a real hollow, dark inside, two bars across it.
        # (It was an eight-sided ring on the front wall with its dark middle buried in the wall, so it read as a doughnut stuck on.)
        cc = cut_to(0.088, 0.108, case, 0.008)
        shell(m, [(0.088, 0.108, cc, P + 0.24), (0.088, 0.108, cc, P + 0.275), (0.078, 0.098, cc, P + 0.29),
                  (0.06, 0.08, 0.016, P + 0.29), (0.054, 0.074, 0.014, P + 0.24)], TD)
        tower(m, [(0.058, 0.078, 0.015, P + 0.235), (0.058, 0.078, 0.015, P + 0.258)], SLIT)
        for y in (-0.028, 0.028):
            m.prism([(y - 0.012, P + 0.255), (y + 0.012, P + 0.255), (y + 0.007, P + 0.278), (y - 0.007, P + 0.278)], -0.064, 0.064, "X", ST)
    # Air pipes. Each leaves the casing square through a flange, turns only in open air, and ends by running
    # straight down through a flange into a boot on a pier: no bend lies inside a flange, and no pipe meets a wall at a slant.
    zp, ra, rf, yo, zt = P + 0.10, 0.03, 0.038, 0.447, 0.58   # run height, pipe and flange radius, where the wall run stands, a boot's top

    def boot(x, d):
        """A boot on the pier wall at side d: the pipe drops into its top, and the turn into the wall is inside it."""
        bprism(m, [(d * 0.39, zt - 0.15), (d * 0.39, zt), (d * 0.492, zt), (d * 0.492, zt - 0.06), (d * 0.44, zt - 0.15)],
               x - 0.042, x + 0.042, "X", T, bevel=0.008)
        m.cyl(rf, 0.022, (x, d * yo, zt + 0.011), TD, seg=8)

    ya, xa = -0.25, -0.345                                    # the long run along the front of the hearth, and the pier it ends at
    m.pipe([(xw - 0.05, ya, zp), (xa + 0.045, ya, zp), (xa, ya - 0.045, zp), (xa, -yo + 0.045, zp), (xa, -yo, zp - 0.045),
            (xa, -yo, zt - 0.02)], ra, ST)
    m.cyl(rf, 0.024, (xw - case[0] - 0.012, ya, zp), TD, seg=8, axis="X", rot=(rad(22.5), 0, 0))
    boot(xa, -1)
    for x in (-0.20, 0.02):                                   # two branches, square into the hearth's wall, each through a collar
        m.pipe([(x, ya, zp), (x, yt - 0.17, zp)], 0.022, ST)
        m.cyl(0.031, 0.018, (x, yt - 0.213, zp), TD, seg=8, axis="Y")
    # the second pipe: from the casing's back, across the far end, over the back eave and down into the far pier
    m.pipe([(xw, yw + case[1] - 0.03, zp), (xw, yo - 0.045, zp), (xw, yo, zp - 0.045), (xw, yo, zt - 0.02)], ra, ST)
    m.cyl(rf, 0.024, (xw, yw + case[1] + 0.012, zp), TD, seg=8, axis="Y")
    boot(xw, 1)
    # tap port in the hearth's far end, above the pipe
    with on_end(m, 1, xt + 0.332, yt, P + 0.25):              # the wall leans, so the port stands on it as a boss, its back buried
        octa(m, 0.05, 0.05, -0.006, 0.006, "h_glow")
        oct_ring(m, 0.078, 0.03, -0.022, 0.022, T)


smelter8.frame, smelter8.shadow = F31, True
_hero.HEROES["smelter8"] = smelter8

def ring_round(m, r_out, r_in, z0, z1, mk, seg=16):
    """A round ring about the local z axis, from z0 to z1: a wheel's rim, for instance."""
    import bmesh
    bm = bmesh.new()
    loops = []
    for r, z in ((r_out, z0), (r_out, z1), (r_in, z1), (r_in, z0)):
        loops.append([bm.verts.new((r * math.cos(2 * math.pi * i / seg), r * math.sin(2 * math.pi * i / seg), z)) for i in range(seg)])
    for a, b in zip(loops, loops[1:] + loops[:1]):
        for i in range(seg):
            bm.faces.new((a[i], a[(i + 1) % seg], b[(i + 1) % seg], b[i]))
    m._add(bm, mk)


def press5(m):
    """Press, 3x1, grade 2 (hitbox 3x1x2). Concept: an ingot lies under the platen and is flattened to a
    plate by the blow that comes down on it; the pressing is in plain sight.
    A dark chassis grips both rails between the two mouths, and the bay between them is open: the belt
    runs through it with the work lying on it. Four steel columns rise from the chassis on flared feet
    and carry a dark crown. The platen, a light block whose shoulders draw in above a dark die, hangs
    between the columns on a round ram that runs up through a gland into the crown. On the crown lies
    the crank housing, a bearing at each end; its shaft carries a heavy flywheel on one side and a gear
    on the other, driven by a pinion from the motor box that stands beside it. The two sides differ on
    purpose: wheel on one, gears on the other."""
    run(m, -1.5, 1.5, braces=(-4 / 3, -1.0, 1.0, 4 / 3))
    cover(m, BX, 1, sole=False)
    cover(m, -BX, -1, sole=False)
    collar(m, -BX - 0.318, BX + 0.318, mk=T)                  # the chassis
    m.box((0.30, 0.24, 0.03), (0, 0, BZ + 0.016), LT, bevel=0.008)                            # the work: a plate on the belt, under the platen
    xc, yc, zc = 0.375, 0.375, 1.18                           # where a column stands, and the crown's underside
    for sx in SIDES:
        for sy in SIDES:
            with m.at((sx * xc, sy * yc, 0)):
                tower(m, [(0.092, 0.036, 0.012, 0.355), (0.078, 0.032, 0.01, 0.46)], T)
                tower(m, [(0.078, 0.032, 0.01, 0.46), (0.064, 0.032, 0.01, zc + 0.02)], ST)   # broad, narrowing upward; runs a little way up into the crown
    crown = (0.455, 0.42, 0.05)
    slab(m, crown[0], crown[1], zc, zc + 0.22, crown[2], TD, bevel=0.02)
    tower(m, [(0.12, 0.12, 0.03, zc - 0.07), (0.155, 0.155, 0.035, zc + 0.01)], T)            # the gland the ram runs through
    # platen: a dark die under a light block whose shoulders draw in to the ram
    tower(m, [(0.27, 0.27, 0.03, 0.63), (0.29, 0.29, 0.03, 0.70)], TD)
    tower(m, [(0.31, 0.31, 0.04, 0.695), (0.31, 0.31, 0.04, 0.82), (0.17, 0.17, 0.03, 0.94)], G)
    m.cyl(0.065, zc - 0.03 - 0.93, (0, 0, (zc - 0.03 + 0.93) / 2), LT, seg=12)                # the ram
    # on the crown: crank housing with a bearing at each end, and the shaft through it
    zs, top = zc + 0.31, zc + 0.22                            # the shaft's height, the crown's top
    tower(m, [(0.16, 0.30, 0.04, top - 0.01), (0.16, 0.30, 0.04, top + 0.16), (0.11, 0.25, 0.035, top + 0.24)], ST)
    for d in SIDES:
        with on_side(m, d, d * 0.30, zs):
            octa(m, 0.075, 0.058, -0.004, 0.032, T)
    m.cyl(0.036 * K, 0.90, (0, 0.0, zs), LT, seg=8, axis="Y", rot=(0, rad(22.5), 0))
    # the flywheel, on the side the catalog looks from: a heavy rim round a set-back web, and its hub
    with on_side(m, -1, -0.455, zs):
        ring_round(m, 0.23, 0.185, -0.025, 0.025, TD)
        m.cyl(0.19, 0.022, (0, 0, 0), ST, seg=16)
        m.cyl(0.062, 0.062, (0, 0, 0), T, seg=10)
        m.cyl(0.034, 0.012, (0, 0, 0.036), LT, seg=10)
    # the other side: a gear on the shaft, a pinion in mesh with it, and the motor box the pinion runs from
    gear(m, 0.16, 0.04, (0, 0.445, zs), T, teeth=12)
    m.cyl(0.05, 0.052, (0, 0.445, zs), LT, seg=10, axis="Y")
    xm = 0.218
    gear(m, 0.07, 0.04, (xm, 0.445, zs), ST, teeth=6)
    m.cyl(0.026, 0.084, (xm, 0.43, zs), LT, seg=8, axis="Y")
    motor = (0.085, 0.10, 0.02)
    with m.at((xm + 0.045, 0.30, 0)):
        tower(m, [(0.095, 0.11, 0.025, top - 0.01), (motor[0], motor[1], motor[2], top + 0.03)], T)
        slab(m, motor[0], motor[1], top + 0.03, top + 0.17, motor[2], G, bevel=0.01)
        slab(m, 0.093, 0.108, top + 0.16, top + 0.20, cut_to(0.093, 0.108, motor, 0.008), TD, bevel=0.008)


press5.frame, press5.shadow = {"iso": (3.3, 0.85), "side": (3.4, 0.95), "top": (3.2, 0.6), "end": (2.6, 1.0)}, True
_hero.HEROES["press5"] = press5

def press6(m):
    """Press, 3x1, grade 2 (hitbox 3x1x2). Concept: an ingot lies under the platen and is flattened to a
    plate by the blow that comes down on it; the pressing is in plain sight.
    press5 stood tall on four thin columns with the platen hanging in an empty frame. After looking at
    how Satisfactory's Constructor does the same job (short thick columns, one heavy block riding on
    them), the developer chose that build: low, wide and heavy.
    A dark chassis grips both rails. On it, along each side of the open bay, runs a light bed. Four
    short round columns stand on the beds, and one thick steel head rides on them, a bushing where each
    column passes through; the columns' capped ends show above it. Under the head hangs the dark die,
    over the work lying on the belt. On the head lies the drive: a housing with a bearing at each end,
    a heavy flywheel on one end of its shaft and a gear on the other."""
    run(m, -1.5, 1.5, braces=(-4 / 3, -1.0, 1.0, 4 / 3))
    cover(m, BX, 1, sole=False)
    cover(m, -BX, -1, sole=False)
    collar(m, -BX - 0.318, BX + 0.318, mk=T)                  # the chassis
    m.box((0.30, 0.24, 0.03), (0, 0, BZ + 0.016), LT, bevel=0.008)                            # the work: a plate on the belt
    for d in SIDES:                                           # a bed along each side of the bay
        bprism(m, [(d * 0.32, 0.35), (d * 0.43, 0.35), (d * 0.43, 0.545), (d * 0.42, 0.56), (d * 0.33, 0.56), (d * 0.32, 0.545)],
               -BX, BX, "X", G, bevel=0.012)
    xc, yc, rc = 0.36, 0.375, 0.042                           # where a column stands, and its radius
    z0, z1 = 0.82, 1.06                                       # the head, at the top of its stroke
    for sx in SIDES:
        for sy in SIDES:
            with m.at((sx * xc, sy * yc, 0)):
                octa(m, 0.05, 0.044, 0.555, 0.60, T)          # foot
                m.cyl(rc, 0.66, (0, 0, 0.87), LT, seg=12)     # the column, from inside the bed to above the head
                octa(m, 0.058, 0.05, z0 - 0.03, z0 + 0.005, T)        # bushing under the head
                octa(m, 0.05, 0.058, z1 - 0.005, z1 + 0.03, T)        # bushing on the head
                octa(m, 0.05, 0.04, 1.195, 1.225, T)          # the column's cap
    head = (0.43, 0.44, 0.04)
    slab(m, head[0], head[1], z0, z1, head[2], TD, bevel=0.02)                              # dark, so the heavy head is what the eye finds
    tower(m, [(0.26, 0.24, 0.03, z0 - 0.16), (0.29, 0.27, 0.03, z0 + 0.01)], ST)              # the die, its top a little way up into the head
    # the drive, lying on the head
    zs = z1 + 0.19
    tower(m, [(0.17, 0.27, 0.035, z1 - 0.01), (0.17, 0.27, 0.035, z1 + 0.16), (0.12, 0.22, 0.03, z1 + 0.24)], G)
    for d in SIDES:
        with on_side(m, d, d * 0.27, zs - 0.07):
            octa(m, 0.07, 0.055, -0.004, 0.03, T)
    m.cyl(0.034 * K, 0.80, (0, 0.0, zs - 0.07), LT, seg=8, axis="Y", rot=(0, rad(22.5), 0))
    with on_side(m, -1, -0.365, zs - 0.07):                   # flywheel: a heavy rim round a set-back web, and its hub
        ring_round(m, 0.17, 0.13, -0.026, 0.026, ST)
        m.cyl(0.135, 0.024, (0, 0, 0), T, seg=16)
        m.cyl(0.055, 0.064, (0, 0, 0), T, seg=10)
        m.cyl(0.03, 0.012, (0, 0, 0.037), LT, seg=10)
    gear(m, 0.13, 0.045, (0, 0.365, zs - 0.07), T, teeth=10)                                  # a gear on the other end
    m.cyl(0.045, 0.06, (0, 0.365, zs - 0.07), LT, seg=10, axis="Y")


press6.frame, press6.shadow = F31, True
_hero.HEROES["press6"] = press6

def press7(m):
    """Press, 3x1, grade 2 (hitbox 3x1x2). The developer asked for this one to follow Satisfactory's
    Constructor, as the assembler followed that game's look: a closed body, four short thick columns,
    and a heavy head riding on them whose plan swells into a lobe round each column.
    Ours keeps its own conveyor, mouths, chassis and grey palette, and its own proportions.
    A dark chassis grips both rails. The body on it is closed, a louvred vent in a one-piece frame on
    each side, under a dark deck. On the deck stand the anvil and four thick round columns on collared
    feet. The head rides on the columns: a dark block with an eight-sided lobe round each column, a
    light band round each lobe; under it hangs the die, over the plate lying on the anvil. On the head
    lie a shouldered cap, a small motor box, and a ringed exhaust pipe standing off-centre."""
    run(m, -1.5, 1.5, braces=(-4 / 3, -1.0, 1.0, 4 / 3))
    cover(m, BX, 1, sole=False)
    cover(m, -BX, -1, sole=False)
    collar(m, -BX - 0.318, BX + 0.318, mk=T)                  # the chassis
    hy, zd = 0.40, 0.80                                       # the body's half width, the deck's underside
    bprism(m, [(-BX, -hy), (BX, -hy), (BX, hy), (-BX, hy)], 0.37, zd + 0.012, "Z", G, bevel=0.012)      # body, running a little way up into the deck
    slab(m, BX, hy + 0.015, zd, zd + 0.07, 0.03, TD, bevel=0.016)                                        # deck, its eave past the body
    for d in SIDES:                                           # louvred vent: dark behind, slats set into a one-piece frame
        with on_side(m, d, d * hy, 0.585):
            m.box((0.40, 0.20, 0.008), (0, 0, 0.002), SLIT)
            for k in range(4):
                y = -0.075 + k * 0.05
                m.prism([(y - 0.02, 0.004), (y + 0.012, 0.004), (y + 0.02, 0.024), (y + 0.006, 0.024)], -0.215, 0.215, "X", ST)
            ring(m, 0.25, 0.14, [(0.0, -0.004), (0.012, 0.03), (0.036, 0.03), (0.05, -0.004)], T, c=0.04)
    Z = zd + 0.07                                             # the deck's top
    tower(m, [(0.27, 0.22, 0.035, Z - 0.01), (0.24, 0.19, 0.03, Z + 0.045)], ST)                         # the anvil
    m.box((0.30, 0.22, 0.02), (0, 0, Z + 0.052), LT, bevel=0.006)                                        # the work: a plate on the anvil
    xc, yc, rc = 0.33, 0.30, 0.062                            # where a column stands, and its radius
    z0, z1 = Z + 0.17, Z + 0.43                               # the head, at the top of its stroke
    head = (0.31, 0.27, 0.05)
    slab(m, head[0], head[1], z0, z1, head[2], TD, bevel=0.018)
    tower(m, [(0.22, 0.18, 0.03, z0 - 0.09), (0.26, 0.21, 0.03, z0 + 0.01)], ST)                         # the die
    for sx in SIDES:
        for sy in SIDES:
            with m.at((sx * xc, sy * yc, 0)):
                octa(m, 0.085, 0.07, Z - 0.005, Z + 0.035, T)                                            # collared foot
                m.cyl(rc, z1 + 0.14 - Z, (0, 0, (z1 + 0.14 + Z) / 2), LT, seg=14)                        # the column
                octa(m, 0.115, 0.115, z0 - 0.012, z0 + 0.085, TD)                                                # the head's lobe round it,
                octa(m, 0.123, 0.123, z0 + 0.085, z1 - 0.085, LT)                                        # with a light band
                octa(m, 0.115, 0.115, z1 - 0.085, z1 + 0.012, TD)
                octa(m, 0.072, 0.058, z1 + 0.135, z1 + 0.17, T)                                          # the column's cap
    # on the head: a shouldered cap, a motor box, and a ringed exhaust pipe standing off-centre
    tower(m, [(0.20, 0.16, 0.03, z1 - 0.01), (0.20, 0.16, 0.03, z1 + 0.04), (0.16, 0.12, 0.025, z1 + 0.08)], ST)
    motor = (0.07, 0.06, 0.015)
    with m.at((0.08, -0.03, 0)):
        slab(m, motor[0], motor[1], z1 + 0.07, z1 + 0.17, motor[2], G, bevel=0.008)
        slab(m, 0.078, 0.068, z1 + 0.16, z1 + 0.19, cut_to(0.078, 0.068, motor, 0.008), TD, bevel=0.006)
    with m.at((-0.09, 0.04, 0)):
        octa(m, 0.045, 0.036, z1 + 0.07, z1 + 0.10, T)
        m.cyl(0.028, 0.30, (0, 0, z1 + 0.23), ST, seg=10)
        for k in range(3):
            octa(m, 0.04, 0.04, z1 + 0.15 + k * 0.06, z1 + 0.175 + k * 0.06, TD)
        oct_ring(m, 0.04, 0.014, z1 + 0.36, z1 + 0.39, TD)
        octa(m, 0.029, 0.029, z1 + 0.34, z1 + 0.375, SLIT)


press7.frame, press7.shadow = F31, True
_hero.HEROES["press7"] = press7

def vent(m, hx=0.25, hy=0.14):
    """A louvred vent, to be built inside on_side: dark behind, slats set into a one-piece frame."""
    m.box((2 * hx - 0.10, 2 * hy - 0.08, 0.008), (0, 0, 0.002), SLIT)
    n = max(2, round((2 * hy - 0.08) / 0.05))
    for k in range(n):
        y = -(n - 1) * 0.025 + k * 0.05
        m.prism([(y - 0.02, 0.004), (y + 0.012, 0.004), (y + 0.02, 0.024), (y + 0.006, 0.024)], -(hx - 0.035), hx - 0.035, "X", ST)
    ring(m, hx, hy, [(0.0, -0.004), (0.012, 0.03), (0.036, 0.03), (0.05, -0.004)], T, c=0.04)


def mould(m, z):
    """A mould: a thick dark plate standing on edge, its top corners drawn in, a light grip on top."""
    tower(m, [(0.028, 0.15, 0.01, z), (0.028, 0.15, 0.01, z + 0.22), (0.02, 0.12, 0.008, z + 0.26)], TD)
    tower(m, [(0.014, 0.05, 0.006, z + 0.255), (0.014, 0.04, 0.006, z + 0.285)], LT)


def former1(m):
    """Former, 3x2 (hitbox 3x2x2). The developer's decision: not a press and a roller and so on, but one
    big machine that does whatever the mould put into it says, in the manner of Satisfactory's
    Constructor and of the Islands press with its moulds.
    The belt runs along the front row. Astride it stands the press: a closed body with a louvred vent
    under a dark deck, an anvil and four thick round columns on the deck, and a dark head riding on
    the columns, swelling into a banded lobe round each. Along the back row runs a long hall, taller
    than the press's deck. On its roof, from one end to the other: the power pack, a square casing
    whose open top is its intake, with a pipe that runs along the roof and drops into a boot on the
    press's deck; the slot at the roof's edge beside the press, where the working mould goes, and over it
    the arm on its stepped turret, lowering a mould in; and the rack,
    a trough with the other moulds standing in it. The hall has a screen in its front wall beside the
    belt, a door and two vents in its back wall, and a ribbed panel in each end wall."""
    yb = -0.5                                                 # the belt's row
    with m.at((0, yb, 0)):
        run(m, -1.5, 1.5, braces=(-4 / 3, -1.0, 1.0, 4 / 3))
        cover(m, BX, 1, sole=False)
        cover(m, -BX, -1, sole=False)
        collar(m, -BX - 0.318, BX + 0.318, mk=T)
    # the press's body: from the front wall back to the hall, a little way up into its deck
    hy, zd = 0.40, 0.80
    bprism(m, [(-BX, yb - hy), (BX, yb - hy), (BX, 0.02), (-BX, 0.02)], 0.37, zd + 0.012, "Z", G, bevel=0.012)
    with m.at((0, (yb - hy - 0.015 + 0.0) / 2, 0)):
        slab(m, BX, (0.0 - (yb - hy - 0.015)) / 2, zd, zd + 0.07, 0.03, TD, bevel=0.016)
    with on_side(m, -1, yb - hy, 0.585):
        vent(m)
    Z = zd + 0.07
    with m.at((0, yb, 0)):
        tower(m, [(0.27, 0.22, 0.035, Z - 0.01), (0.24, 0.19, 0.03, Z + 0.045)], ST)                     # the anvil
        m.box((0.30, 0.22, 0.02), (0, 0, Z + 0.052), LT, bevel=0.006)                                    # the work
        xc, yc, rc = 0.33, 0.30, 0.062
        z0, z1 = Z + 0.17, Z + 0.43
        m.box((0.62, 0.54, z1 - z0), (0, 0, (z0 + z1) / 2), TD, bevel=0.018)                             # the head, its corners buried in the lobes
        tower(m, [(0.22, 0.18, 0.03, z0 - 0.09), (0.26, 0.21, 0.03, z0 + 0.01)], ST)                     # the die
        for sx in SIDES:
            for sy in SIDES:
                with m.at((sx * xc, sy * yc, 0)):
                    octa(m, 0.085, 0.07, Z - 0.005, Z + 0.035, T)
                    m.cyl(rc, z1 + 0.14 - Z, (0, 0, (z1 + 0.14 + Z) / 2), LT, seg=14)
                    octa(m, 0.115, 0.115, z0 - 0.012, z0 + 0.085, TD)
                    octa(m, 0.123, 0.123, z0 + 0.085, z1 - 0.085, LT)
                    octa(m, 0.115, 0.115, z1 - 0.085, z1 + 0.012, TD)
                    octa(m, 0.072, 0.058, z1 + 0.135, z1 + 0.17, T)
        tower(m, [(0.20, 0.16, 0.03, z1 - 0.01), (0.20, 0.16, 0.03, z1 + 0.04), (0.16, 0.12, 0.025, z1 + 0.08)], ST)
    # the hall along the back row
    hx, y0, y1, zr = 1.44, 0.015, 0.95, 0.90                  # half length, front and back walls, the roof's underside
    yc_, hyh = (y0 + y1) / 2, (y1 - y0) / 2
    with m.at((0, yc_, 0)):
        slab(m, hx + 0.005, hyh + 0.005, 0.0, 0.16, 0.03, T, bevel=0.012)                                # kick plinth
    bprism(m, [(-hx, y0), (hx, y0), (hx, y1), (-hx, y1)], 0.12, zr + 0.012, "Z", G, bevel=0.014)
    with m.at((0, yc_, 0)):
        slab(m, hx + 0.015, hyh + 0.015, zr, zr + 0.06, 0.04, TD, bevel=0.018)                           # roof, its eave past the walls
    R_ = zr + 0.06                                            # the roof's top
    with on_side(m, -1, y0, 0.63, xc=-1.11):                  # screen in the front wall, clear of the mouth and above the rail
        m.box((0.44, 0.26, 0.008), (0, 0, 0.002), SLIT)
        for i, w in enumerate((0.34, 0.22, 0.28)):
            m.box((w, 0.03, 0.006), (0, (1 - i) * 0.07, 0.008), "h_core")
        ring(m, 0.29, 0.195, [(0.0, -0.004), (0.012, 0.034), (0.051, 0.034), (0.065, -0.004)], T, c=0.04)
    with on_side(m, -1, y0, 0.63, xc=1.11):
        vent(m, 0.28, 0.16)
    for sx in SIDES:                                          # each end wall: a ribbed panel between two pilasters
        with on_end(m, sx, sx * hx, yc_, 0.53):
            for k in range(5):
                x = -0.20 + k * 0.10
                m.prism([(x - 0.032, -0.004), (x + 0.032, -0.004), (x + 0.018, 0.03), (x - 0.018, 0.03)], -0.27, 0.27, "Y", ST)
            ring(m, 0.31, 0.33, [(0.0, -0.004), (0.012, 0.04), (0.04, 0.04), (0.055, -0.004)], T, c=0.04)
    for x in (-0.92, 0.92):                                   # the back wall: a vent each side of a double door
        with on_side(m, 1, y1, 0.52, xc=x):
            vent(m, 0.30, 0.16)
    with on_side(m, 1, y1, 0.44, xc=0):
        m.box((0.44, 0.52, 0.02), (0, 0, 0.008), G, bevel=0.01)
        m.box((0.012, 0.48, 0.012), (0, 0, 0.016), SLIT)
        for sx in SIDES:
            m.box((0.022, 0.13, 0.012), (sx * 0.05, 0, 0.016), SLIT)
        ring(m, 0.27, 0.31, [(0.0, -0.004), (0.01, 0.03), (0.03, 0.03), (0.042, -0.004)], T, c=0.03)
    # on the roof, at one end: the power pack, its open top the intake
    xp, yp = -1.02, 0.50
    case = (0.24, 0.26, 0.04)
    with m.at((xp, yp, 0)):
        tower(m, [(0.265, 0.285, 0.05, R_ - 0.01), (case[0], case[1], case[2], R_ + 0.05)], T)
        slab(m, case[0], case[1], R_ + 0.05, R_ + 0.32, case[2], G, bevel=0.016)
        cc = cut_to(0.25, 0.27, case, 0.01)
        shell(m, [(0.25, 0.27, cc, R_ + 0.31), (0.25, 0.27, cc, R_ + 0.36), (0.235, 0.255, cc, R_ + 0.38),
                  (0.19, 0.21, 0.03, R_ + 0.38), (0.18, 0.20, 0.026, R_ + 0.31)], TD)
        tower(m, [(0.186, 0.206, 0.028, R_ + 0.305), (0.186, 0.206, 0.028, R_ + 0.335)], SLIT)
        for y in (-0.10, 0.0, 0.10):
            m.prism([(y - 0.018, R_ + 0.33), (y + 0.018, R_ + 0.33), (y + 0.01, R_ + 0.365), (y - 0.01, R_ + 0.365)], -0.20, 0.20, "X", ST)
    # its pipe: square out of the casing through a flange, along the roof, down into a boot on the press's deck
    zp, ra, rf, xq, yq = R_ + 0.14, 0.03, 0.04, -0.14, -0.05
    m.pipe([(xp + case[0] - 0.03, 0.34, zp), (xq - 0.045, 0.34, zp), (xq, 0.295, zp), (xq, yq + 0.045, zp), (xq, yq, zp - 0.045),
            (xq, yq, Z + 0.07)], ra, ST)
    m.cyl(rf, 0.024, (xp + case[0] + 0.012, 0.34, zp), TD, seg=8, axis="X", rot=(rad(22.5), 0, 0))
    with m.at((xq, yq, 0)):
        tower(m, [(0.052, 0.036, 0.012, Z - 0.01), (0.044, 0.034, 0.01, Z + 0.09)], T)                   # the boot
        m.cyl(rf * 0.82, 0.02, (0, 0, Z + 0.10), TD, seg=8)
    # the slot the working mould drops into, at the roof's edge beside the press, and the arm lowering a mould into it
    xa, ys = 0.24, 0.20
    with m.at((xa, ys, 0)):
        shell(m, [(0.062, 0.185, 0.02, R_ - 0.01), (0.068, 0.19, 0.022, R_ + 0.045), (0.058, 0.18, 0.018, R_ + 0.06),
                  (0.04, 0.162, 0.012, R_ + 0.06), (0.036, 0.158, 0.01, R_ + 0.01)], T)
        tower(m, [(0.039, 0.161, 0.011, R_ - 0.005), (0.039, 0.161, 0.011, R_ + 0.015)], SLIT)
        mould(m, R_ + 0.08)
    with m.at((xa, 0, 0)):
        arm4(m, 1, 0.66, R_, (0.82, R_ + 0.78), (ys + 0.015, R_ + 0.67))
    # the rack: a trough with the other moulds standing in it
    xr, yr = 1.0, 0.52
    with m.at((xr, yr, 0)):
        shell(m, [(0.36, 0.20, 0.03, R_ - 0.01), (0.37, 0.21, 0.035, R_ + 0.09), (0.355, 0.195, 0.03, R_ + 0.105),
                  (0.33, 0.17, 0.02, R_ + 0.105), (0.32, 0.16, 0.018, R_ + 0.03)], ST)
        tower(m, [(0.325, 0.165, 0.02, R_ - 0.005), (0.325, 0.165, 0.02, R_ + 0.035)], SLIT)
        for k in range(4):
            with m.at((-0.24 + k * 0.16, 0, 0)):
                mould(m, R_ + 0.03)


former1.frame, former1.shadow = {"iso": (4.5, 0.85), "side": (4.4, 1.0), "top": (3.9, 0.6), "end": (3.6, 1.0)}, True
_hero.HEROES["former1"] = former1

def former2(m):
    """Former, 3x2 (hitbox 3x2x2). The developer asked for it to be modelled like Satisfactory's
    Constructor, so its masses follow that machine: one tall closed body; a thick framed mouth with a
    sloped hood at one side of each end face and a tall vent beside it; four fat steel columns out of
    the body's top; a big light head on them whose plan swells round each column, a dark band round
    its top edge and bolts in its flanks; an open frame over the head; a ringed exhaust stack up
    through the head's waist; a low dark platform with bent outrigger legs.
    It is a grade 2 machine, and grade 2 is a chimney-and-pipe factory: no screen and no robot arm
    (those begin at grade 3). On the platform stand what a person would work: the rack of moulds, the
    receiver on the body's wall with the mould in use standing in it, and the drive, a heavy flywheel.
    The belt runs along the far row (y = +0.5); the platform is the near strip."""
    yb = 0.5
    with m.at((0, yb, 0)):
        bed(m, -1.5, 1.5)                   # the conveyor, as d.run lays it, but with its arrows placed by hand:
        m.box((3.0, BH * 2, 0.03), (0, 0, BZ - 0.015), "h_belt")
        for x in (-1.28, 1.28):                               # one whole pair on each open stretch; none under the mouth's frame, where the
            chev(m, x)                                        # jamb and the dark of the tunnel would cut it off
        for x in (-4 / 3, 4 / 3):
            buttress(m, x)
        collar(m, -1.0, 1.0, mk=T)                            # the chassis under the body, gripping both rails
    X, y0, y1, zt = 0.86, -0.44, 0.94, 1.0                    # the body: half length, near and far walls, top
    yc, hy = (y0 + y1) / 2, (y1 - y0) / 2
    # platform: the near row, and out past both ends of the body
    with m.at((0, -0.485, 0)):
        slab(m, 1.08, 0.485, 0.0, 0.12, 0.05, TD, bevel=0.016)
    bprism(m, [(-X - 0.012, y0 - 0.012), (X + 0.012, y0 - 0.012), (X + 0.012, 0.02), (-X - 0.012, 0.02)], 0.10, 0.385, "Z", T, bevel=0.012)   # the body's dark foot on the platform
    with m.at((0, yc, 0)):
        slab(m, X, hy, 0.37, zt, 0.05, G, bevel=0.028)        # the body
    for sx in SIDES:                                          # outrigger legs: a bent strut down to a pad
        pts = [(1.00, 0.08), (1.00, 0.30), (1.12, 0.30), (1.40, 0.09), (1.28, 0.05)]
        m.prism([(sx * x, z) for x, z in pts], -0.80, -0.66, "Y", ST)
        with m.at((sx * 1.36, -0.73, 0)):
            slab(m, 0.10, 0.11, 0.0, 0.065, 0.03, T, bevel=0.012)
    # each end face: the mouth in its thick frame under a sloped hood, and a tall vent beside it
    for sx in SIDES:
        a, b = sorted((sx * (X - 0.01), sx * (X + 0.15)))
        with m.at((0, yb, 0)):
            m.prism(arch_pts(0.96, 0.84, hole_top=0.705, hw=BH + 0.01, c=0.11, ci=0.05), a, b, "X", T)
            a2, b2 = sorted((sx * (X + 0.15), sx * (X + 0.185)))
            m.prism(arch_pts(0.86, 0.775, hole_top=0.705, hw=BH + 0.01, c=0.085, ci=0.05), a2, b2, "X", LT)
            m.box((0.02, 2 * BH + 0.01, 0.694 - BZ), (sx * (X + 0.02), 0, (0.706 + BZ) / 2), SLIT)
            m.prism([(sx * x, z) for x, z in ((X - 0.03, 0.83), (X - 0.03, 0.985), (X + 0.03, 0.985), (X + 0.14, 0.87), (X + 0.14, 0.83))],
                    -0.34, 0.34, "Y", ST)                     # the hood
        with on_end(m, sx, sx * X, -0.20, 0.66):
            m.box((0.24, 0.42, 0.008), (0, 0, 0.002), SLIT)
            for k in range(4):                                # upright slats set into a one-piece frame
                x = -0.09 + k * 0.06
                m.prism([(x - 0.022, 0.004), (x + 0.014, 0.004), (x + 0.022, 0.026), (x + 0.006, 0.026)], -0.215, 0.215, "Y", ST)
            ring(m, 0.16, 0.25, [(0.0, -0.004), (0.012, 0.032), (0.04, 0.032), (0.055, -0.004)], T, c=0.04)
    # the far wall: a raised light panel bolted on between two vents
    with on_side(m, 1, y1, 0.69, xc=0):
        m.box((0.56, 0.40, 0.03), (0, 0, 0.01), LT, bevel=0.012)
        for sx in SIDES:
            for sz in SIDES:
                m.cyl(0.022, 0.012, (sx * 0.23, sz * 0.15, 0.03), TD, seg=6)
    for x in (-0.55, 0.55):
        with on_side(m, 1, y1, 0.69, xc=x):
            vent(m, 0.20, 0.17)
    # the near wall, behind the platform: a bolted panel over the rack
    with on_side(m, -1, y0, 0.72, xc=-0.60):
        m.box((0.46, 0.30, 0.03), (0, 0, 0.01), LT, bevel=0.012)
        for sx in SIDES:
            for sz in SIDES:
                m.cyl(0.02, 0.012, (sx * 0.185, sz * 0.105, 0.03), TD, seg=6)
    # out of the body's top: four fat columns and the ram between them
    cx, cy, rc = 0.50, 0.42, 0.10
    z0, z1 = 1.22, 1.50                                       # the head, at the top of its stroke
    with m.at((0, yc, 0)):
        octa(m, 0.31, 0.27, zt - 0.01, zt + 0.045, T)
        octa(m, 0.23, 0.23, zt + 0.03, z0 + 0.02, ST)         # the ram
        slab(m, 0.56, 0.50, z0 + 0.015, z1 - 0.055, 0.06, LT, bevel=0.02)                                # the head
        slab(m, 0.568, 0.508, z1 - 0.06, z1, 0.06, TD, bevel=0.014)                                      # the dark band round its top edge
        for sx in SIDES:
            for sy in SIDES:
                with m.at((sx * cx, sy * cy, 0)):
                    octa(m, 0.145, 0.125, zt - 0.01, zt + 0.05, T)                                       # collared foot
                    m.cyl(rc, z1 + 0.10 - zt, (0, 0, (z1 + 0.10 + zt) / 2), ST, seg=16)                  # the column
                    octa(m, 0.20, 0.20, z0, z1 - 0.075, LT)                                              # the head swelling round it
                    octa(m, 0.208, 0.208, z1 - 0.08, z1 + 0.012, TD)
                    m.cyl(rc + 0.02, 0.03, (0, 0, z1 + 0.075), T, seg=16)                                # the nut under the lid
                    for u in (-0.07, 0.07):                   # two bolts in each outward flank
                        m.cyl(0.024, 0.02, (u, sy * 0.205, z0 + 0.10), TD, seg=6, axis="Y")
                        m.cyl(0.024, 0.02, (sx * 0.205, u, z0 + 0.10), TD, seg=6, axis="X")
        # over the head, carried on the columns: an open frame, the head's hatch showing through it
        za = z1 + 0.085
        ring(m, 0.61, 0.53, [(0.0, za), (0.0, za + 0.028), (0.012, za + 0.04), (0.208, za + 0.04), (0.22, za + 0.028), (0.22, za)], ST, c=0.13)
        ring(m, 0.27, 0.21, [(0.0, z1 - 0.004), (0.01, z1 + 0.03), (0.04, z1 + 0.03), (0.05, z1 - 0.004)], T, c=0.05)
        m.box((0.44, 0.32, 0.01), (0, 0, z1 + 0.003), SLIT)
        for k in range(3):
            m.prism([(-0.105 + k * 0.105 - 0.024, z1 + 0.004), (-0.105 + k * 0.105 + 0.024, z1 + 0.004),
                     (-0.105 + k * 0.105 + 0.014, z1 + 0.024), (-0.105 + k * 0.105 - 0.014, z1 + 0.024)], -0.235, 0.235, "X", ST)
        # the exhaust stack, up through the head's waist at the outlet end
        with m.at((0.70, 0, 0)):
            octa(m, 0.09, 0.07, zt - 0.01, zt + 0.045, T)
            m.cyl(0.05, 0.92, (0, 0, zt + 0.46), ST, seg=12)
            for k in range(3):
                octa(m, 0.068, 0.068, 1.68 + k * 0.068, 1.715 + k * 0.068, TD)
            oct_ring(m, 0.068, 0.022, 1.90, 1.94, TD)
            octa(m, 0.047, 0.047, 1.89, 1.925, SLIT)
    # on the platform: the mould receiver on the body's wall, the drive, and the rack
    with m.at((0.0, y0 - 0.085, 0), rad(90)):                 # the receiver: an open-topped box against the wall
        shell(m, [(0.085, 0.20, 0.02, 0.11), (0.09, 0.205, 0.022, 0.30), (0.078, 0.193, 0.018, 0.315),
                  (0.05, 0.168, 0.012, 0.315), (0.046, 0.164, 0.01, 0.20)], T)
        tower(m, [(0.049, 0.167, 0.011, 0.115), (0.049, 0.167, 0.011, 0.205)], SLIT)
        mould(m, 0.19)
    # the drive: a heavy flywheel on a shaft out of the wall, its outer end in a bearing on a pedestal
    with on_side(m, -1, y0, 0.60, xc=0.52):
        m.cyl(0.115, 0.04, (0, 0, 0.012), T, seg=8)
        m.cyl(0.05, 0.31, (0, 0, 0.145), ST, seg=10)
        ring_round(m, 0.30, 0.235, 0.08, 0.17, TD, seg=20)
        for k in range(3):
            m.box((0.50, 0.06, 0.035), (0, 0, 0.125), LT, rot=k * math.pi / 3)
        m.cyl(0.09, 0.11, (0, 0, 0.125), T, seg=8)
        m.prism([(-0.17, -0.49), (0.17, -0.49), (0.07, 0.08), (-0.07, 0.08)], 0.215, 0.285, "Z", T)
        m.cyl(0.085, 0.09, (0, 0, 0.25), TD, seg=8)
    with m.at((-0.60, -0.70, 0)):                             # the rack: a trough with the other moulds standing in it
        shell(m, [(0.33, 0.20, 0.03, 0.11), (0.34, 0.21, 0.035, 0.21), (0.325, 0.195, 0.03, 0.225),
                  (0.30, 0.17, 0.02, 0.225), (0.29, 0.16, 0.018, 0.15)], ST)
        tower(m, [(0.295, 0.165, 0.02, 0.115), (0.295, 0.165, 0.02, 0.155)], SLIT)
        for k in range(4):
            with m.at((-0.215 + k * 0.143, 0, 0)):
                mould(m, 0.15)


former2.frame, former2.shadow = {"iso": (4.5, 1.0), "side": (4.4, 1.1), "top": (3.9, 0.6), "end": (3.6, 1.1)}, True
_hero.HEROES["former2"] = former2

def lineup1(m):
    """Not a machine: the smelter, the former and the assembler side by side, to judge whether they
    belong to one set. Nearest the usual camera is the smallest."""
    for fn, y in ((smelter8, -3.5), (former2, -1.0), (assembler4, 2.5)):
        with m.at((0, y, 0)):
            fn(m)


lineup1.frame, lineup1.shadow = {"iso": (9.6, 1.0), "side": (4.6, 1.3), "top": (9.0, 1.0), "end": (9.0, 1.3)}, True
_hero.HEROES["lineup1"] = lineup1

def belt_stub(m, x0, x1, arrow, bolt):
    """A stub of conveyor from x0 to x1, as d.run lays it, but with one whole pair of arrows at `arrow`
    (so none is cut off under a mouth's cover) and a bolt at `bolt`."""
    bed(m, x0, x1)
    m.box((x1 - x0, BH * 2, 0.03), ((x0 + x1) / 2, 0, BZ - 0.015), "h_belt")
    chev(m, arrow)
    buttress(m, bolt)


def fire_window(m, bars=4, hx=0.17, hy=0.10):
    """A glowing window in a furnace wall, to be built inside on_side or on_end: the glow, bars set into
    a one-piece frame, the frame's back buried in the wall (which may lean)."""
    m.box((2 * hx - 0.08, 2 * hy - 0.08, 0.02), (0, 0, -0.004), "h_glow")
    step = (2 * hx - 0.09) / bars                             # the bars stand across the whole opening
    for k in range(bars):
        x = -(bars - 1) * step / 2 + k * step
        m.prism([(x - 0.014, 0.0), (x + 0.014, 0.0), (x + 0.008, 0.022), (x - 0.008, 0.022)], -(hy - 0.03), hy - 0.03, "Y", TD)
    ring(m, hx, hy, [(0.0, -0.03), (0.012, 0.03), (0.034, 0.03), (0.045, -0.03)], T, c=0.03)


def blast4(m):
    """Steel mill, 3x3, grade 3 (hitbox 3x3x4). Iron and coal are carried up to the top of a tall
    furnace, melt together in a blast of hot air, and run out as steel.
    Grade 3, but a furnace: a chimney-and-pipe machine with one screen, not a laboratory.
    A wide low hall carries everything: two inputs side by side at one end, the output at the other,
    buttresses and vents along its sides. On its deck stands the furnace, a square shaft that narrows
    as it rises, hooped in steel, on a dark hearth with a glowing window in three faces (the one over
    the output is the tap), under a dark cap with an open charging hopper. Round the shaft runs the
    blast main, a ring of pipe with two short branches into each face. Between the two inputs stands
    the hoist house, and from its roof an inclined hoist climbs to the hopper, a loaded skip on its
    rails. At one back corner stands a tall square stack, at the other the blower house with the
    machine's one screen; each feeds the ring through a short straight pipe."""
    X, Y, Z = 0.85, 1.46, 1.0
    for sy in SIDES:
        with m.at((0, sy * 1.0, 0)):
            belt_stub(m, -1.5, -X, -1.345, -1.43)
            cover(m, -X, -1)
    belt_stub(m, X, 1.5, 1.345, 1.43)
    cover(m, X, 1)
    wall = (X, Y, 0.03)
    slab(m, X - 0.012, Y - 0.012, 0.0, 0.18, 0.03, T, bevel=0.012)
    slab(m, X, Y, 0.14, Z - 0.07, wall[2], G, bevel=0.02)
    slab(m, X + 0.03, Y + 0.03, Z - 0.10, Z, cut_to(X + 0.03, Y + 0.03, wall, 0.03), TD, bevel=0.025)
    for d in SIDES:                                           # each long wall: three steel buttresses, a vent between each pair
        for x in (-0.60, 0.0, 0.60):
            with on_side(m, d, d * Y, 0.52, xc=x):
                m.box((0.13, 0.78, 0.032), (0, 0, 0.01), ST, bevel=0.012)
        for x in (-0.30, 0.30):
            with on_side(m, d, d * Y, 0.54, xc=x):
                vent(m, 0.19, 0.17)
    for sy in SIDES:                                          # the outlet end: a bolted panel each side of the mouth
        with on_end(m, 1, X, sy * 0.96, 0.52):
            m.box((0.46, 0.42, 0.03), (0, 0, 0.01), LT, bevel=0.012)
            for a in SIDES:
                for b in SIDES:
                    m.cyl(0.022, 0.012, (a * 0.185, b * 0.165, 0.03), TD, seg=6)
    # the hoist house between the two inputs, and the inclined hoist from its roof to the hopper
    pit = (0.30, 0.40, 0.05)
    with m.at((-1.14, 0, 0)):
        slab(m, pit[0], pit[1], 0.0, 0.60, pit[2], G, bevel=0.02)
        slab(m, 0.32, 0.42, 0.57, 0.66, cut_to(0.32, 0.42, pit, 0.02), TD, bevel=0.02)
    with on_end(m, -1, -1.44, 0, 0.32):
        vent(m, 0.24, 0.16)
    p0, p1 = (-1.30, 0.64), (-0.38, 3.02)
    L = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
    ux, uz = (p1[0] - p0[0]) / L, (p1[1] - p0[1]) / L

    def along(s, off):                                        # a point s up the incline and `off` above the rails' underside
        return (p0[0] + ux * s - uz * off, p0[1] + uz * s + ux * off)

    for sy in SIDES:
        ya, yb_ = sorted((sy * 0.14, sy * 0.21))
        m.prism([along(0, 0), along(L, 0), along(L, 0.075), along(0, 0.075)], ya, yb_, "Y", ST)                 # rails
        xa, xb = -0.875, -0.815                               # a post from the deck's edge up into each rail
        zr = lambda x: p0[1] + (x - p0[0]) * uz / ux
        m.prism([(xa, Z - 0.01), (xb, Z - 0.01), (xb, zr(xb) + 0.012), (xa, zr(xa) + 0.012)], ya, yb_, "Y", ST)
    m.box((0.05, 0.30, 0.05), (-0.845, 0, 1.38), T)
    for k in range(6):                                        # ties, their ends let into the rails
        s0 = 0.22 + k * 0.42
        m.prism([along(s0, 0.014), along(s0 + 0.05, 0.014), along(s0 + 0.05, 0.052), along(s0, 0.052)], -0.15, 0.15, "Y", T)
    s0 = 1.22                                                 # the skip, loaded, part of the way up
    m.prism([along(s0, 0.105), along(s0 + 0.30, 0.105), along(s0 + 0.34, 0.27), along(s0 - 0.04, 0.27)], -0.125, 0.125, "Y", TD)
    m.prism([along(s0 + 0.0, 0.262), along(s0 + 0.30, 0.262), along(s0 + 0.22, 0.31), along(s0 + 0.08, 0.31)], -0.09, 0.09, "Y", "h_copper")
    for q in (0.06, 0.24):
        x, z = along(s0 + q, 0.115)
        for sy in SIDES:
            m.cyl(0.042, 0.05, (x, sy * 0.175, z), T, seg=10, axis="Y")
    m.prism([(-0.45, 2.95), (-0.30, 2.95), (-0.30, 3.07), (-0.45, 3.07)], -0.25, 0.25, "Y", T)                  # the tipping head, on the hopper's lip
    # the furnace
    tower(m, [(0.68, 0.68, 0.12, Z - 0.01), (0.62, 0.62, 0.11, Z + 0.30)], T)                                    # hearth
    zb0, zb1 = Z + 0.29, Z + 1.62
    half = lambda z: 0.60 - 0.17 * (z - zb0) / (zb1 - zb0)
    cutc = lambda z: 0.11 - 0.03 * (z - zb0) / (zb1 - zb0)
    tower(m, [(0.60, 0.60, 0.11, zb0), (0.43, 0.43, 0.08, zb1)], G)                                              # the shaft, narrowing as it rises
    for z in (Z + 0.80, Z + 1.22):                            # steel hoops
        tower(m, [(half(z) + 0.016, half(z) + 0.016, cutc(z) + 0.004, z), (half(z + 0.07) + 0.016, half(z + 0.07) + 0.016, cutc(z + 0.07) + 0.004, z + 0.07)], ST)
    tower(m, [(0.47, 0.47, 0.09, Z + 1.60), (0.47, 0.47, 0.09, Z + 1.70), (0.36, 0.36, 0.07, Z + 1.82)], TD)     # cap
    shell(m, [(0.26, 0.26, 0.05, Z + 1.80), (0.33, 0.33, 0.06, Z + 2.0), (0.31, 0.31, 0.055, Z + 2.02),
              (0.27, 0.27, 0.05, Z + 2.02), (0.21, 0.21, 0.04, Z + 1.86)], ST)                                   # charging hopper, open
    tower(m, [(0.215, 0.215, 0.041, Z + 1.84), (0.215, 0.215, 0.041, Z + 1.875)], SLIT)
    for d in SIDES:                                           # a glowing window in each side face of the hearth,
        with on_side(m, d, d * 0.655, Z + 0.15):
            fire_window(m)
    with on_end(m, 1, 0.655, 0, Z + 0.15):                    # and the tap over the outlet, with a lip under it
        fire_window(m, bars=2, hx=0.20)
        m.prism([(-0.15, -0.154), (0.15, -0.154), (0.11, -0.085), (-0.11, -0.085)], -0.02, 0.085, "Z", TD)
    # the blast main: a ring of pipe round the shaft, two branches square into each face
    a_, cut, zr_, rr = 0.74, 0.20, Z + 0.50, 0.05
    loop = [(a_, 0), (a_, a_ - cut), (a_ - cut, a_), (-(a_ - cut), a_), (-a_, a_ - cut), (-a_, -(a_ - cut)), (-(a_ - cut), -a_),
            (a_ - cut, -a_), (a_, -(a_ - cut)), (a_, 0)]
    m.pipe([(x, y, zr_) for x, y in loop], rr, ST, seg=8)
    hw = half(zr_)
    for s in SIDES:
        m.cyl(rr + 0.016, 0.05, (s * a_, 0, zr_), TD, seg=8, axis="Y", rot=(0, rad(22.5), 0))                    # a flange in the middle of each run
        m.cyl(rr + 0.016, 0.05, (0, s * a_, zr_), TD, seg=8, axis="X", rot=(rad(22.5), 0, 0))
        for u in (-0.30, 0.30):
            m.cyl(0.03, a_ - hw + 0.02, (s * (a_ + hw - 0.02) / 2, u, zr_), ST, seg=8, axis="X")
            m.cyl(0.046, 0.024, (s * (hw + 0.006), u, zr_), TD, seg=8, axis="X", rot=(rad(22.5), 0, 0))
            m.cyl(0.03, a_ - hw + 0.02, (u, s * (a_ + hw - 0.02) / 2, zr_), ST, seg=8, axis="Y")
            m.cyl(0.046, 0.024, (u, s * (hw + 0.006), zr_), TD, seg=8, axis="Y", rot=(0, rad(22.5), 0))
    # one back corner: the stack
    xs, ys = 0.45, 1.10
    with m.at((xs, ys, 0)):
        tower(m, [(0.21, 0.21, 0.04, Z - 0.01), (0.17, 0.17, 0.035, Z + 0.22)], T)
        zs0, zs1 = Z + 0.21, 3.30
        sh = lambda z: 0.165 - 0.045 * (z - zs0) / (zs1 - zs0)
        tower(m, [(0.165, 0.165, 0.035, zs0), (0.12, 0.12, 0.03, zs1)], G)
        for z in (1.95, 2.65):
            tower(m, [(sh(z) + 0.012, sh(z) + 0.012, 0.035, z), (sh(z + 0.06) + 0.012, sh(z + 0.06) + 0.012, 0.035, z + 0.06)], ST)
        shell(m, [(0.125, 0.125, 0.03, 3.28), (0.165, 0.165, 0.035, 3.38), (0.165, 0.165, 0.035, 3.43), (0.15, 0.15, 0.03, 3.45),
                  (0.105, 0.105, 0.022, 3.45), (0.095, 0.095, 0.02, 3.33)], TD)
        tower(m, [(0.10, 0.10, 0.021, 3.32), (0.10, 0.10, 0.021, 3.36)], SLIT)
    yf = ys - sh(zr_)                                         # its pipe to the ring: straight, a flange where it leaves the stack
    m.cyl(0.042, yf - a_ + 0.02, (xs, (yf + a_) / 2, zr_), ST, seg=8, axis="Y")
    m.cyl(0.06, 0.024, (xs, yf - 0.006, zr_), TD, seg=8, axis="Y", rot=(0, rad(22.5), 0))
    # the other back corner: the blower house, with the screen
    xb_, yb2 = 0.45, -1.10
    bl = (0.27, 0.25, 0.04)
    with m.at((xb_, yb2, 0)):
        slab(m, 0.28, 0.26, Z - 0.01, Z + 0.08, cut_to(0.28, 0.26, bl, 0.01), T, bevel=0.012)
        slab(m, bl[0], bl[1], Z + 0.06, Z + 0.70, bl[2], G, bevel=0.018)
        slab(m, 0.29, 0.27, Z + 0.67, Z + 0.76, cut_to(0.29, 0.27, bl, 0.02), TD, bevel=0.018)
        octa(m, 0.13, 0.11, Z + 0.75, Z + 0.81, ST)
        oct_ring(m, 0.115, 0.03, Z + 0.80, Z + 0.84, T)
        octa(m, 0.086, 0.086, Z + 0.79, Z + 0.825, SLIT)
    with on_side(m, -1, yb2 - bl[1], Z + 0.38, xc=xb_):
        vent(m, 0.19, 0.16)
    with on_end(m, 1, xb_ + bl[0], yb2, Z + 0.40):
        m.box((0.30, 0.20, 0.008), (0, 0, 0.002), SLIT)
        for i, w in enumerate((0.22, 0.14, 0.18)):
            m.box((w, 0.026, 0.006), (0, (1 - i) * 0.055, 0.008), "h_core")
        ring(m, 0.19, 0.14, [(0.0, -0.004), (0.012, 0.03), (0.038, 0.03), (0.05, -0.004)], T, c=0.035)
    yg = yb2 + bl[1]
    m.cyl(0.042, -a_ - yg + 0.02, (xb_, (yg - a_) / 2, zr_), ST, seg=8, axis="Y")
    m.cyl(0.06, 0.024, (xb_, yg + 0.006, zr_), TD, seg=8, axis="Y", rot=(0, rad(22.5), 0))


blast4.frame, blast4.shadow = {"iso": (6.2, 1.6), "side": (5.0, 1.9), "top": (3.9, 1.0), "end": (5.0, 1.9)}, True
_hero.HEROES["blast4"] = blast4

def bolted(m, w, h, mk=LT, r=0.022):
    """A plate bolted on at its four corners, to be built inside on_side or on_end."""
    m.box((w, h, 0.03), (0, 0, 0.01), mk, bevel=0.012)
    for a_ in SIDES:
        for b_ in SIDES:
            m.cyl(r, 0.012, (a_ * (w / 2 - 0.05), b_ * (h / 2 - 0.05), 0.03), TD, seg=6)


def blast5(m):
    """Steel mill, 3x3, grade 3 (hitbox 3x3x4), second attempt. The developer found the first poorer than
    the grade 2 machines: a plain box under a plain shaft, its parts thin and far apart. This one
    follows the build of Satisfactory's Foundry, mass for mass, as the former followed the
    Constructor, and takes its parts from the chimney-and-pipe kit.
    A long hall with sloped shoulders stands between two dark end walls and a rib. In the inlet wall
    are the two mouths, each in a thick frame under a sloped hood, and between them a pier with a tall
    vent, a hatch and the machine's one screen. On the hall's deck, toward the outlet, rises the
    furnace: a dark hearth with glowing windows (the one over the outlet is the tap), a light upper
    block banded in steel under a dark cap, two ringed stacks on the cap. Against the furnace's front
    stands the hoist shaft, taller than the furnace, a ladder of light slats between dark stiles, and
    beside it the blower, whose fat pipe rises, turns once and runs square into the furnace."""
    X, Y = 0.90, 1.44
    for sy in SIDES:
        with m.at((0, sy * 1.0, 0)):
            belt_stub(m, -1.5, -X + 0.06, -1.29, -1.42)
            collar(m, -(X + 0.19), -(X - 0.05), mk=T)
    belt_stub(m, X - 0.06, 1.5, 1.29, 1.42)
    collar(m, X - 0.05, X + 0.19, mk=T)
    slab(m, X + 0.025, Y + 0.03, 0.0, 0.14, 0.04, TD, bevel=0.014)                                               # plinth
    sh0, sh1, zt = 0.92, 0.30, 1.25                           # the shoulder: where it starts, how far it leans in, the roof
    m.prism([(-Y, 0.12), (-Y, sh0), (-(Y - sh1), zt), (Y - sh1, zt), (Y, sh0), (Y, 0.12)], -(X - 0.10), X - 0.10, "X", G)   # the hall
    rib = [(-Y - 0.035, 0.10), (-Y - 0.035, sh0 + 0.015), (-(Y - sh1) - 0.016, zt + 0.035), (Y - sh1 + 0.016, zt + 0.035),
           (Y + 0.035, sh0 + 0.015), (Y + 0.035, 0.10)]
    for x0, x1 in ((-X, -X + 0.13), (-0.065, 0.065), (X - 0.13, X)):                                             # two end walls and a rib
        bprism(m, rib, x0, x1, "X", T, bevel=0.014)
    slab(m, 0.80, Y - sh1 - 0.06, zt - 0.01, zt + 0.045, 0.04, TD, bevel=0.012)                                  # deck
    Z = zt + 0.045
    for sy in SIDES:                                          # outrigger legs at the outlet end
        m.prism([(0.88, 0.08), (0.88, 0.34), (1.03, 0.34), (1.36, 0.09), (1.24, 0.05)], *sorted((sy * 0.93, sy * 1.07)), "Y", ST)
        with m.at((1.33, sy * 1.0, 0)):
            slab(m, 0.10, 0.11, 0.0, 0.065, 0.03, T, bevel=0.012)

    def mouth(sx, y):                                         # a thick frame round the belt, a liner, the dark of the tunnel, a hood
        with m.at((0, y, 0)):
            a_, b_ = sorted((sx * (X - 0.01), sx * (X + 0.15)))
            m.prism(arch_pts(0.96, 0.86, hole_top=0.705, hw=BH + 0.01, c=0.11, ci=0.05), a_, b_, "X", G)
            a_, b_ = sorted((sx * (X + 0.15), sx * (X + 0.185)))
            m.prism(arch_pts(0.86, 0.79, hole_top=0.705, hw=BH + 0.01, c=0.085, ci=0.05), a_, b_, "X", LT)
            m.box((0.02, 2 * BH + 0.01, 0.694 - BZ), (sx * (X + 0.02), 0, (0.706 + BZ) / 2), SLIT)
            m.prism([(sx * x, z) for x, z in ((X - 0.03, 0.85), (X - 0.03, 1.02), (X + 0.03, 1.02), (X + 0.14, 0.895), (X + 0.14, 0.85))],
                    -0.36, 0.36, "Y", ST)

    for sy in SIDES:
        mouth(-1, sy * 1.0)
    mouth(1, 0.0)
    with on_end(m, -1, -X, 0, 0.62):                          # the pier between the inlets
        m.box((0.60, 0.92, 0.05), (0, 0, 0.02), G, bevel=0.014)
        with m.at((0, 0, 0.045)):
            with m.at((0.15, -0.04, 0)):                      # a tall vent, its slats upright in a one-piece frame
                m.box((0.18, 0.62, 0.008), (0, 0, 0.002), SLIT)
                for k in range(3):
                    x = -0.05 + k * 0.05
                    m.prism([(x - 0.02, 0.004), (x + 0.012, 0.004), (x + 0.02, 0.024), (x + 0.006, 0.024)], -0.32, 0.32, "Y", ST)
                ring(m, 0.13, 0.35, [(0.0, -0.004), (0.012, 0.03), (0.036, 0.03), (0.05, -0.004)], T, c=0.035)
            with m.at((-0.14, 0.22, 0)):                      # the screen
                m.box((0.20, 0.15, 0.008), (0, 0, 0.002), SLIT)
                for i, w in enumerate((0.15, 0.09, 0.12)):
                    m.box((w, 0.022, 0.006), (0, (1 - i) * 0.044, 0.008), "h_core")
                ring(m, 0.135, 0.11, [(0.0, -0.004), (0.01, 0.026), (0.03, 0.026), (0.04, -0.004)], T, c=0.03)
            with m.at((-0.14, -0.20, 0)):                     # a hatch
                bolted(m, 0.24, 0.36, LT, r=0.016)
    for sy in SIDES:                                          # the outlet wall: a bolted panel each side of the mouth
        with on_end(m, 1, X, sy * 0.97, 0.52):
            bolted(m, 0.44, 0.44, G)
    for d in SIDES:                                           # each long wall: a vent in one bay, a bolted panel in the other
        with on_side(m, d, d * Y, 0.52, xc=-0.42):
            vent(m, 0.27, 0.19)
        with on_side(m, d, d * Y, 0.52, xc=0.42):
            bolted(m, 0.52, 0.46)
    # the furnace, on the deck toward the outlet
    xt, fx, fy = 0.37, 0.46, 0.72
    with m.at((xt, 0, 0)):
        tower(m, [(fx + 0.045, fy + 0.045, 0.11, Z - 0.02), (fx + 0.012, fy + 0.012, 0.10, Z + 0.52)], T)       # hearth
        slab(m, fx, fy, Z + 0.50, Z + 1.62, 0.10, LT, bevel=0.03)                                                # upper block
        slab(m, fx + 0.014, fy + 0.014, Z + 0.98, Z + 1.07, 0.104, ST, bevel=0.012)                              # steel band
        tower(m, [(fx + 0.03, fy + 0.03, 0.11, Z + 1.60), (fx + 0.03, fy + 0.03, 0.11, Z + 1.70), (fx - 0.06, fy - 0.06, 0.09, Z + 1.80)], TD)   # cap
        for sy in SIDES:                                      # two ringed stacks on the cap
            with m.at((0.12, sy * 0.36, 0)):
                octa(m, 0.14, 0.12, Z + 1.79, Z + 1.86, T)
                octa(m, 0.095, 0.085, Z + 1.85, Z + 2.42, ST)
                for k in range(3):
                    octa(m, 0.108, 0.108, Z + 2.12 + k * 0.085, Z + 2.16 + k * 0.085, TD)
                oct_ring(m, 0.108, 0.03, Z + 2.40, Z + 2.45, TD)
                octa(m, 0.079, 0.079, Z + 2.39, Z + 2.43, SLIT)
    yh = fy + 0.03                                            # the hearth's faces, at the windows' height
    for d in SIDES:
        for x in (xt - 0.21, xt + 0.21):
            with on_side(m, d, d * yh, Z + 0.25, xc=x):
                fire_window(m, bars=3, hx=0.15, hy=0.12)
        with on_side(m, d, d * fy, Z + 1.34, xc=xt):          # upper block: a vent over the band, a bolted panel under it
            vent(m, 0.27, 0.16)
        with on_side(m, d, d * fy, Z + 0.75, xc=xt):
            bolted(m, 0.50, 0.30, G)
    with on_end(m, 1, xt + fx + 0.03, 0, Z + 0.25):           # the tap, over the outlet, with a lip under it
        fire_window(m, bars=4, hx=0.26, hy=0.13)
        m.prism([(-0.20, -0.21), (0.20, -0.21), (0.15, -0.115), (-0.15, -0.115)], -0.02, 0.09, "Z", TD)
    with on_end(m, 1, xt + fx, 0, Z + 1.34):
        vent(m, 0.30, 0.16)
    # against the furnace's front: the hoist shaft, taller than the furnace
    x0, x1, ys_, top = -0.44, xt - fx + 0.02, -0.34, Z + 2.06
    with m.at(((x0 + x1) / 2, ys_, 0)):
        tower(m, [((x1 - x0) / 2, 0.19, 0.0, Z - 0.02), ((x1 - x0) / 2, 0.19, 0.0, top)], T)
        slab(m, (x1 - x0) / 2 + 0.03, 0.235, top - 0.02, top + 0.10, 0.03, TD, bevel=0.016)
        m.prism([(-0.16, top + 0.09), (0.16, top + 0.09), (0.09, top + 0.17), (-0.09, top + 0.17)], -0.17, 0.17, "Y", T)
    for sy in SIDES:                                          # stiles, and between them a ladder of slats let into them
        m.box((0.07, 0.055, top - Z + 0.03), (x0 - 0.02, ys_ + sy * 0.185, (Z + top) / 2 + 0.005), ST, bevel=0.01)
    n = 15
    for k in range(n):
        z0 = Z + 0.12 + k * (top - Z - 0.30) / (n - 1)
        m.prism([(x0 + 0.004, z0), (x0 - 0.04, z0 + 0.018), (x0 - 0.04, z0 + 0.05), (x0 + 0.004, z0 + 0.07)], ys_ - 0.17, ys_ + 0.17, "Y", LT)
    # beside it: the blower, and its pipe into the furnace
    xb_, yb_ = -0.50, 0.44
    bl = (0.25, 0.28, 0.04)
    with m.at((xb_, yb_, 0)):
        slab(m, bl[0], bl[1], Z - 0.02, Z + 0.36, bl[2], G, bevel=0.018)
        slab(m, bl[0] + 0.02, bl[1] + 0.02, Z + 0.33, Z + 0.42, cut_to(bl[0] + 0.02, bl[1] + 0.02, bl, 0.02), TD, bevel=0.018)
        octa(m, 0.12, 0.105, Z + 0.41, Z + 0.47, T)
    with on_end(m, -1, xb_ - bl[0], yb_, Z + 0.17):
        vent(m, 0.21, 0.12)
    zp, rp = Z + 0.92, 0.075
    m.pipe([(xb_, yb_, Z + 0.45), (xb_, yb_, zp - 0.09), (xb_ + 0.09, yb_, zp), (xt - fx + 0.02, yb_, zp)], rp, ST, seg=10)
    m.cyl(rp + 0.022, 0.03, (xb_, yb_, Z + 0.56), TD, seg=8)
    m.cyl(rp + 0.022, 0.03, (xt - fx - 0.012, yb_, zp), TD, seg=8, axis="X", rot=(rad(22.5), 0, 0))


blast5.frame, blast5.shadow = {"iso": (6.4, 1.8), "side": (5.0, 2.0), "top": (3.9, 1.0), "end": (5.0, 2.0)}, True
_hero.HEROES["blast5"] = blast5

from . import belts as _belts


def belts_demo(m):
    """Not a machine: every conveyor piece laid end to end, with a machine in the line, to judge the
    joints. Far row: three straights, the smelter, a straight, one ramp on its own, a straight on a
    block. Near row: two straights, a right turn, a straight, a left turn, a straight, then two ramps
    in a run (one straight climb of two cells) and a straight on a block two cells up, then down again in a run of two ramps. Nearest: a ramp going down on its own."""
    OX, OY = -2.5, 1.5                                        # to bring the middle of the layout to the middle of the picture

    def put(fn, x, y, rz=0.0, z=0.0):
        with m.at((x + OX, y + OY, z), rz):
            fn(m)

    def block(x, y, h, x1=None):
        x1 = x if x1 is None else x1
        with m.at(((x + x1) / 2 + OX, y + OY, 0)):
            slab(m, (x1 - x) / 2 + 0.5, 0.5, 0.0, h, 0.0, "h_stone", bevel=0.01)

    for x in (-4, -3, -2):
        put(_belts.straight, x, 2)
    put(smelter8, 0, 2)
    put(_belts.straight, 2, 2)
    put(_belts.ramp, 3.5, 2)
    put(_belts.straight, 5, 2, 0.0, 1.0)
    block(5, 2, 1.0)
    put(_belts.straight, -4, -1)
    put(_belts.straight, -3, -1)
    put(_belts.corner_right, -2, -1)
    put(_belts.straight, -2, -2, rad(-90))
    put(_belts.corner_left, -2, -3, rad(-90))
    put(_belts.straight, -1, -3)
    put(_belts.ramp_start, 0.5, -3)
    put(_belts.ramp_end, 2.5, -3, 0.0, 1.0)
    block(2, -3, 1.0, 3)
    put(_belts.straight, 4, -3, 0.0, 2.0)
    block(4, -3, 2.0)
    put(_belts.ramp_down_start, 5.5, -3, 0.0, 1.0)            # and down again in a run of two
    block(5, -3, 1.0, 6)
    put(_belts.ramp_down_end, 7.5, -3)
    put(_belts.straight, 9, -3)
    put(_belts.straight, -4, -5.5, 0.0, 1.0)                  # one ramp going down on its own
    block(-4, -5.5, 1.0)
    put(_belts.ramp_down, -2.5, -5.5)
    put(_belts.straight, -1, -5.5)


belts_demo.frame, belts_demo.shadow = {"iso": (16.5, 0.9), "side": (7.0, 1.0), "top": (7.4, 0.6), "end": (6.0, 1.0)}, True
_hero.HEROES["belts_demo"] = belts_demo
def belts_all(m):
    """Not a machine: every conveyor piece in ONE unbroken line, to judge each joint. From the start:
    two straights, a ramp up on its own, a straight, a ramp down on its own, a straight, a right turn,
    a straight, a left turn, a straight, a run of three ramps up (first, middle, last), a straight, a
    left turn, three straights, a left turn, a straight, a run of three ramps down, two straights, a
    right turn, a straight. Raised pieces stand on nothing, and the ramps above the ground have no
    trestles: what carries a raised belt is not designed yet."""
    OX, OY = -2.5, -0.5
    R90 = rad(90)

    def put(fn, x, y, rz=0.0, z=0.0):
        with m.at((x + OX, y + OY, z), rz):
            fn(m)

    def ramp(low, high, down=False, legs=True):
        return lambda mm: _belts.ramp(mm, low, high, legs=legs, down=down)

    for x in (-6, -5):
        put(_belts.straight, x, 0)
    put(ramp(True, True), -3.5, 0)
    put(_belts.straight, -2, 0, 0.0, 1.0)
    put(ramp(True, True, down=True), -0.5, 0)
    put(_belts.straight, 1, 0)
    put(_belts.corner_right, 2, 0)
    put(_belts.straight, 2, -1, -R90)
    put(_belts.corner_left, 2, -2, -R90)
    put(_belts.straight, 3, -2)
    put(ramp(True, False), 4.5, -2)
    put(ramp(False, False, legs=False), 6.5, -2, 0.0, 1.0)
    put(ramp(False, True, legs=False), 8.5, -2, 0.0, 2.0)
    put(_belts.straight, 10, -2, 0.0, 3.0)
    put(_belts.corner_left, 11, -2, 0.0, 3.0)
    for y in (-1, 0, 1):
        put(_belts.straight, 11, y, R90, 3.0)
    put(_belts.corner_left, 11, 2, R90, 3.0)
    put(_belts.straight, 10, 2, 2 * R90, 3.0)
    put(ramp(False, True, down=True, legs=False), 8.5, 2, 2 * R90, 2.0)
    put(ramp(False, False, down=True, legs=False), 6.5, 2, 2 * R90, 1.0)
    put(ramp(True, False, down=True), 4.5, 2, 2 * R90)
    for x in (3, 2):
        put(_belts.straight, x, 2, 2 * R90)
    put(_belts.corner_right, 1, 2, 2 * R90)
    put(_belts.straight, 1, 3, R90)


belts_all.frame, belts_all.shadow = {"iso": (21.0, 1.6), "side": (19.5, 1.8), "top": (19.5, 0.6), "end": (9.0, 1.8)}, True
belts_all.res = 3200                      # wide, and the joints must be seen closely
_hero.HEROES["belts_all"] = belts_all


def _factory(m, formers):
    """Not a machine: a small factory, to see the machines and belts as one thing. Two lines run side
    by side, each ore -> smelter -> former; the far line runs straight into one of the assembler's
    inputs, the near line turns left and right to reach the other; the assembler's output runs on.
    `formers` gives the former for the far line and for the near line."""
    OX, OY = 2.0, 1.5
    R90 = rad(90)

    def put(fn, x, y, rz=0.0, z=0.0):
        with m.at((x + OX, y + OY, z), rz):
            fn(m)

    def thing(x, y, kind):                                    # something riding the belt
        with m.at((x + OX, y + OY, BZ + 0.006)):       # just clear of the arrows painted on the belt
            if kind == "ore":
                m.box((0.26, 0.24, 0.18), (0, 0, 0.09), "h_ore", bevel=0.05)
            elif kind == "ingot":
                m.box((0.30, 0.16, 0.10), (0, 0, 0.05), "h_steel", bevel=0.03, taper=0.8)
            else:
                m.box((0.30, 0.26, 0.04), (0, 0, 0.02), "h_lite", bevel=0.012)

    for y, former in zip((1, -3), formers):                   # the two lines
        for x in (-10, -9):
            put(_belts.straight, x, y)
        put(smelter9, -6.5, y - 0.5)
        put(_belts.straight, -4, y)
        put(former, -2, y - 0.5)
        put(_belts.straight, 0, y)
        thing(-10.1, y, "ore")
        thing(-9.2, y, "ore")
        thing(-4.0, y, "ingot")
        thing(0.0, y, "plate")
    put(_belts.straight, 1, 1)                                # the far line: straight in
    put(_belts.corner_left, 1, -3)                            # the near line: up two cells, then in
    put(_belts.straight, 1, -2, R90)
    put(_belts.corner_right, 1, -1, R90)
    thing(1.0, -2.0, "plate")
    put(assembler4, 3, 0)
    for x in (5, 6):
        put(_belts.straight, x, 0)


def factory1(m):
    """The small factory with the former made after Satisfactory in both lines."""
    _factory(m, (former2, former2))


def factory3(m):
    """The same factory with our own rough, busy former (former4) in the near line."""
    _factory(m, (former2, former4))


def factory2(m):
    """The same factory with the former made after Islands (former3) in the near line, for comparison."""
    _factory(m, (former2, former3))


factory1.frame, factory1.shadow = {"iso": (20.0, 1.2), "side": (18.0, 1.6), "top": (18.5, 0.6), "end": (9.0, 1.6)}, True
factory1.res = 3200
_hero.HEROES["factory1"] = factory1
factory2.frame, factory2.shadow, factory2.res = factory1.frame, True, 3200
_hero.HEROES["factory2"] = factory2
factory3.frame, factory3.shadow, factory3.res = factory1.frame, True, 3200
_hero.HEROES["factory3"] = factory3


fk.PAL.update({"h_py": "#d3a62b"})          # a painted frame: the works' own colour on a grey machine
PY = "h_py"


def hex_stack(m, x, y, z0, z1, r=0.085):
    """A fat eight-sided stack built in lengths, a collar at each joint, on a flared foot, its top a rim
    round a real hollow."""
    with m.at((x, y, 0)):
        octa(m, r + 0.045, r + 0.02, z0 - 0.01, z0 + 0.07, G)
        octa(m, r, r, z0 + 0.06, z1 - 0.05, LT)
        n = max(1, round((z1 - z0 - 0.2) / 0.24))
        for k in range(1, n + 1):
            zc = z0 + 0.06 + k * (z1 - z0 - 0.17) / (n + 1)
            octa(m, r + 0.018, r + 0.018, zc - 0.03, zc + 0.03, G)
        octa(m, r + 0.01, r + 0.03, z1 - 0.06, z1 - 0.01, G)
        oct_ring(m, r + 0.03, 0.035, z1 - 0.012, z1 + 0.03, G)
        octa(m, r - 0.004, r - 0.004, z1 - 0.03, z1 + 0.012, SLIT)


def frame_ring(m, hx, hy, z0, z1, w, mk):
    """A square frame of beams, open in the middle, every edge chamfered, in one mitred piece."""
    c = 0.014
    ring(m, hx, hy, [(0.0, z0 + c), (0.0, z1 - c), (c, z1), (w - c, z1), (w, z1 - c), (w, z0 + c), (w - c, z0), (c, z0)], mk)


def former3(m):
    """Former, 3x2 (hitbox 3x2x3), in the manner of the original game's factory machines rather than
    Satisfactory's: the developer found ours had become a laboratory ("너무 연구소 느낌") beside
    Islands' "오리지널한 공장 느낌". Side by side the differences were a painted frame, a skeleton left
    open to view, fat stacks and pipes, and big plain masses; this takes all four, following the build
    of Islands' steel press mass for mass, in our own parts.
    The belt runs along the far row, open to the sky. Over it stands the press: four pairs of slim
    posts on a dark chassis, two painted square frames round them (one half way up, one at the top),
    and between the frames the painted head, hung from two cross beams, its ram and die over the work
    on the belt. In the near row stands the works' house: a grey cabinet with doors and vents, a
    painted body on it, and on the body's roof three fat stacks, a row of three small ones, and the
    fat pipe that comes over from the head. Beside the house a low platform carries the mould rack."""
    yb = 0.5
    with m.at((0, yb, 0)):
        run(m, -1.5, 1.5, braces=(-4 / 3, -1.0, 1.0, 4 / 3))
        collar(m, -0.56, 0.56, mk=T)                          # the chassis the press stands on
        Zc = 0.385
        for sx in SIDES:                                      # posts: a pair at each corner, on a shoe
            for sy in SIDES:
                m.box((0.17, 0.07, 0.05), (sx * 0.435, sy * 0.414, Zc + 0.02), G, bevel=0.012)
                for x in (0.40, 0.47):
                    m.box((0.038, 0.038, 2.42 - Zc), (sx * x, sy * 0.414, (2.42 + Zc) / 2), LT, bevel=0.008)
        frame_ring(m, 0.53, 0.49, 1.22, 1.35, 0.13, PY)       # the frame half way up
        frame_ring(m, 0.525, 0.485, 1.196, 1.224, 0.12, TD)   # and the dark line under it
        frame_ring(m, 0.53, 0.49, 2.40, 2.53, 0.13, PY)       # the frame at the top
        frame_ring(m, 0.525, 0.485, 2.376, 2.404, 0.12, TD)
        for y in (-0.2, 0.2):                                 # cross beams under the top frame; the head hangs from them
            m.prism([(y - 0.05, 2.30), (y + 0.05, 2.30), (y + 0.035, 2.385), (y - 0.035, 2.385)], -0.50, 0.50, "X", G)
        slab(m, 0.33, 0.30, 1.50, 2.31, 0.05, PY, bevel=0.025)                                           # the head
        octa(m, 0.21, 0.21, 0.86, 1.52, ST)                                                              # the ram
        slab(m, 0.27, 0.25, 0.70, 0.87, 0.035, TD, bevel=0.016)                                          # the die
        m.box((0.32, 0.26, 0.022), (0, 0, BZ + 0.017), LT, bevel=0.006)                                  # the work, on the belt
        with on_end(m, -1, -0.33, 0, 2.02):                   # the head's end: a slatted panel over two dials
            vent(m, 0.20, 0.13)
        for y in (-0.11, 0.11):
            with on_end(m, -1, -0.33, y, 1.68):
                m.cyl(0.075, 0.03, (0, 0, 0.012), G, seg=6)
                m.cyl(0.05, 0.012, (0, 0, 0.03), "h_white", seg=6)
                m.box((0.012, 0.05, 0.008), (0.012, 0.012, 0.038), "h_red", rot=0.6)
    # the near row: a low platform with the mould rack, and the works' house
    with m.at((-0.86, -0.5, 0)):
        slab(m, 0.56, 0.47, 0.0, 0.14, 0.04, T, bevel=0.014)
        shell(m, [(0.33, 0.20, 0.03, 0.13), (0.34, 0.21, 0.035, 0.23), (0.325, 0.195, 0.03, 0.245),
                  (0.30, 0.17, 0.02, 0.245), (0.29, 0.16, 0.018, 0.17)], ST)
        tower(m, [(0.295, 0.165, 0.02, 0.135), (0.295, 0.165, 0.02, 0.175)], SLIT)
        for k in range(4):
            with m.at((-0.215 + k * 0.143, 0, 0)):
                mould(m, 0.17)
    hx0, hx1 = -0.30, 1.42
    xc, hx = (hx0 + hx1) / 2, (hx1 - hx0) / 2
    with m.at((xc, -0.5, 0)):
        slab(m, hx - 0.01, 0.46, 0.0, 0.16, 0.03, T, bevel=0.012)
        slab(m, hx, 0.47, 0.12, 0.645, 0.035, G, bevel=0.02)                                             # cabinet
        body = (hx - 0.08, 0.39, 0.045)
        slab(m, body[0], body[1], 0.635, 1.04, body[2], PY, bevel=0.022)                                 # the painted body
    yf, ye = -0.97, hx1
    for x, w, h in ((0.02, 0.36, 0.38), (0.48, 0.30, 0.38)):                                             # cabinet front: two doors and a vent
        with on_side(m, -1, yf, 0.39, xc=x):
            bolted(m, w, h, LT, r=0.016)
    with on_side(m, -1, yf, 0.39, xc=1.02):
        vent(m, 0.24, 0.16)
    for y in (-0.72, -0.28):                                  # cabinet end: two vents
        with on_end(m, 1, ye, y, 0.39):
            vent(m, 0.17, 0.16)
    for x in (hx0 + 0.07, hx1 - 0.07):                        # a bolt at each front corner, top and bottom
        for z in (0.21, 0.57):
            with on_side(m, -1, yf, z, xc=x):
                m.cyl(0.024, 0.016, (0, 0, 0.006), LT, seg=6)
    yp = -0.5 - 0.39                                          # the painted body's front: let-in grey panels and a badge
    for x, w in ((0.0, 0.20), (0.33, 0.30), (0.66, 0.16), (0.88, 0.16)):
        with on_side(m, -1, yp, 0.84, xc=x):
            m.box((w, 0.24, 0.02), (0, 0, 0.006), G, bevel=0.008)
            m.box((w - 0.07, 0.17, 0.008), (0, 0, 0.018), LT)
    with on_side(m, -1, yp, 0.84, xc=1.14):
        m.cyl(0.075, 0.02, (0, 0, 0.008), "h_red", seg=6)
        m.cyl(0.04, 0.01, (0, 0, 0.022), "h_white", seg=6)
    Zr = 1.04                                                 # on the body's roof
    hex_stack(m, 0.16, -0.56, Zr, 2.12, 0.095)
    hex_stack(m, 0.58, -0.36, Zr, 1.80, 0.095)
    hex_stack(m, 0.92, -0.62, Zr, 2.34, 0.095)
    for k, top in enumerate((1.50, 1.42, 1.56)):
        hex_stack(m, 1.22, -0.26 - k * 0.19, Zr, top, 0.05)
    # the fat pipe from the head over to the body: square out of the head through a flange, one turn in the open, down through a flange
    xp, zp, rp = -0.06, 1.98, 0.075
    m.pipe([(xp, yb - 0.31, zp), (xp, -0.21, zp), (xp, -0.30, zp - 0.09), (xp, -0.30, Zr + 0.04)], rp, LT, seg=8)
    m.cyl(rp + 0.022, 0.03, (xp, yb - 0.315, zp), G, seg=8, axis="Y", rot=(0, rad(22.5), 0))
    for y in (0.0, -0.13):
        m.cyl(rp + 0.016, 0.05, (xp, y, zp), G, seg=8, axis="Y", rot=(0, rad(22.5), 0))
    for z in (1.62, 1.34):
        with m.at((xp, -0.30, 0)):
            octa(m, rp + 0.014, rp + 0.014, z - 0.025, z + 0.025, G)
    with m.at((xp, -0.30, 0)):
        octa(m, rp + 0.05, rp + 0.03, Zr - 0.01, Zr + 0.06, G)


former3.frame, former3.shadow = {"iso": (4.6, 1.3), "side": (4.4, 1.5), "top": (3.9, 0.6), "end": (3.6, 1.5)}, True
_hero.HEROES["former3"] = former3


fk.PAL.update({"h_pr": "#a9543f"})          # oxide red: the paint on former4's crown and guards
PR = "h_pr"


def hull2(c0, r0, c1, r1, n=10):
    """The outline that wraps two circles in a plane (a belt round two pulleys): points, counter-clockwise."""
    pts = [(c[0] + r * math.cos(2 * math.pi * k / (2 * n)), c[1] + r * math.sin(2 * math.pi * k / (2 * n)))
           for c, r in ((c0, r0), (c1, r1)) for k in range(2 * n)]
    pts = sorted(set(pts))
    def half(seq):
        out = []
        for q in seq:
            while len(out) >= 2 and (out[-1][0] - out[-2][0]) * (q[1] - out[-2][1]) - (out[-1][1] - out[-2][1]) * (q[0] - out[-2][0]) <= 0:
                out.pop()
            out.append(q)
        return out
    lo, hi = half(pts), half(reversed(pts))
    return lo[:-1] + hi[:-1]


def bolt_row(m, n, span, y, r=0.02):
    """A row of n bolt heads across a face, to be built inside on_side or on_end."""
    for k in range(n):
        m.cyl(r, 0.014, (-span / 2 + k * span / (n - 1), y, 0.005), LT, seg=6)


def former4(m):
    """Former, 3x2 (hitbox 3x2x3). The developer on former3: less futuristic and rougher, but too like
    Islands and "너무 단순하게 생겨서 공장 맛이 안 난다": it wants roughness AND complexity. So this is
    our own machine, a mechanical press with its works on show: heavy iron, and many parts each doing
    a job.
    The belt runs along the far row, open. Over it stands the press: four tapered iron columns on
    bolted feet, tied by rails and braced with a cross on the far side, carrying a deep painted crown
    riveted along its edges. Out of the crown's near face comes the crankshaft with a big spoked
    flywheel; a finned motor on the crown's top drives it through a guarded belt. Under the crown the
    slide runs between gibs on the columns, the ram and die below it over the work on the belt.
    The near row stands on one platform: the mould rack; an oil drum lying on two saddles, banded,
    with a manhole and two pipes that climb to the crown; and the control stand with its sloped desk,
    two levers and a handwheel."""
    yb = 0.5
    with m.at((0, yb, 0)):
        run(m, -1.5, 1.5, braces=(-4 / 3, -1.0, 1.0, 4 / 3))
        collar(m, -0.78, 0.78, mk=T)
    Zc, zk0, zk1 = 0.385, 1.76, 2.22                          # the chassis' top, the crown's underside and top
    cx, cy = 0.52, 0.42
    for sx in SIDES:
        for sy in SIDES:
            with m.at((sx * cx, yb + sy * cy, 0)):
                slab(m, 0.135, 0.072, Zc - 0.005, Zc + 0.045, 0.02, G, bevel=0.012)                      # bolted foot
                for u in (-0.095, 0.095):
                    m.cyl(0.02, 0.014, (u, 0, Zc + 0.05), LT, seg=6)
                tower(m, [(0.10, 0.068, 0.02, Zc + 0.04), (0.082, 0.06, 0.018, 1.0), (0.072, 0.056, 0.016, zk0 + 0.012)], T)   # column
            xa, xb = sorted((sx * (cx - 0.07), sx * (cx - 0.26)))                                        # gusset under the crown
            m.prism([(sx * (cx - 0.06), zk0 + 0.01), (sx * (cx - 0.06), zk0 - 0.24), (sx * (cx - 0.27), zk0 + 0.01)],
                    *sorted((yb + sy * (cy - 0.03), yb + sy * (cy + 0.03))), "Y", G)
            m.box((0.03, 0.05, 0.86), (sx * (cx - 0.105), yb + sy * 0.31, 1.33), LT, bevel=0.008)        # gib the slide runs on
    for sy in SIDES:                                          # a rail tying each pair of columns
        m.box((2 * cx, 0.055, 0.09), (0, yb + sy * cy, 1.02), G, bevel=0.012)
    for k, (a_, b_) in enumerate((((-cx, 1.07), (cx, zk0)), ((-cx, zk0), (cx, 1.07)))):                 # the cross brace, on the far side
        dx, dz = b_[0] - a_[0], b_[1] - a_[1]
        L = math.hypot(dx, dz)
        nx, nz = -dz / L * 0.025, dx / L * 0.025
        m.prism([(a_[0] + nx, a_[1] + nz), (b_[0] + nx, b_[1] + nz), (b_[0] - nx, b_[1] - nz), (a_[0] - nx, a_[1] - nz)],
                yb + cy + 0.03 - k * 0.012, yb + cy + 0.055 - k * 0.012, "Y", ST)       # one bar lies a little behind the other where they cross
    crown = (0.66, 0.47, 0.05)
    with m.at((0, yb, 0)):
        slab(m, crown[0], crown[1], zk0, zk1, crown[2], PR, bevel=0.03)                                  # the crown
        slab(m, 0.62, 0.43, zk1 - 0.012, zk1 + 0.05, cut_to(0.62, 0.43, crown, -0.04), TD, bevel=0.016)
        slab(m, 0.30, 0.29, 1.22, zk0 + 0.012, 0.04, G, bevel=0.02)                                      # the slide
        octa(m, 0.15, 0.15, 0.94, 1.235, ST)                                                             # the ram
        slab(m, 0.27, 0.25, 0.78, 0.95, 0.035, TD, bevel=0.016)                                          # the die
        m.box((0.32, 0.26, 0.022), (0, 0, BZ + 0.017), LT, bevel=0.006)                                  # the work, on the belt
    for sx in SIDES:                                          # rivets along the crown's ends, and along its far face
        with on_end(m, sx, sx * crown[0], yb, (zk0 + zk1) / 2):
            bolt_row(m, 6, 0.66, 0.16)
            bolt_row(m, 6, 0.66, -0.16)
    with on_side(m, 1, yb + crown[1], (zk0 + zk1) / 2):
        bolt_row(m, 8, 1.02, 0.16)
        bolt_row(m, 8, 1.02, -0.16)
    # the drive: crankshaft and flywheel out of the crown's near face, a finned motor on top, a guarded belt between
    zs, yw = 1.99, yb - crown[1]
    with on_side(m, -1, yw, zs):
        m.cyl(0.13, 0.05, (0, 0, 0.018), T, seg=8)            # bearing
        m.cyl(0.06, 0.24, (0, 0, 0.11), ST, seg=10)           # crankshaft
        ring_round(m, 0.40, 0.325, 0.05, 0.135, TD, seg=24)   # flywheel rim
        for k in range(3):
            m.box((0.70, 0.065, 0.04), (0, 0, 0.0925), LT, rot=k * math.pi / 3)
        m.cyl(0.115, 0.10, (0, 0, 0.0925), T, seg=8)          # hub
    xm, zm = 0.36, zk1 + 0.20                                 # the motor
    with m.at((xm, yb + 0.06, 0)):
        slab(m, 0.16, 0.20, zk1 + 0.04, zk1 + 0.085, 0.03, T, bevel=0.012)
        m.cyl(0.13, 0.42, (0, 0, zm), ST, seg=12, axis="Y")
        for k in range(5):
            m.cyl(0.146, 0.035, (0, -0.15 + k * 0.075, zm), TD, seg=12, axis="Y")
        m.cyl(0.085, 0.05, (0, 0.235, zm), T, seg=10, axis="Y")
    yg0, yg1 = yw - 0.215, yw - 0.155                         # the belt guard, outside the flywheel
    m.cyl(0.032, yb + 0.06 - 0.21 - yg1 + 0.02, (xm, (yb + 0.06 - 0.21 + yg1) / 2, zm), ST, seg=8, axis="Y")   # motor shaft
    m.prism(hull2((0.0, zs), 0.17, (xm, zm), 0.10), yg0, yg1, "Y", PR)
    for (x, z) in ((0.0, zs), (xm, zm)):
        m.cyl(0.05, 0.016, (x, yg0 - 0.008, z), LT, seg=6, axis="Y")
    # the near row, on one platform
    with m.at((0, -0.5, 0)):
        slab(m, 1.42, 0.47, 0.0, 0.12, 0.04, T, bevel=0.014)
    Zp = 0.12
    with m.at((-0.98, -0.5, 0)):                              # the mould rack
        shell(m, [(0.33, 0.20, 0.03, Zp - 0.01), (0.34, 0.21, 0.035, Zp + 0.09), (0.325, 0.195, 0.03, Zp + 0.105),
                  (0.30, 0.17, 0.02, Zp + 0.105), (0.29, 0.16, 0.018, Zp + 0.03)], ST)
        tower(m, [(0.295, 0.165, 0.02, Zp - 0.005), (0.295, 0.165, 0.02, Zp + 0.035)], SLIT)
        for k in range(4):
            with m.at((-0.215 + k * 0.143, 0, 0)):
                mould(m, Zp + 0.03)
    xt, yt, rt, zt = 0.10, -0.58, 0.26, Zp + 0.09 + 0.26       # the oil drum, lying on two saddles
    m.cyl(rt, 0.92, (xt, yt, zt), G, seg=14, axis="X")
    for sx in SIDES:
        m.cyl(rt, 0.07, (xt + sx * 0.495, yt, zt), G, seg=14, axis="X", r2=rt * 0.72) if sx > 0 else \
            m.cyl(rt * 0.72, 0.07, (xt + sx * 0.495, yt, zt), G, seg=14, axis="X", r2=rt)
        m.prism([(yt - 0.24, Zp - 0.005), (yt + 0.24, Zp - 0.005), (yt + 0.19, zt - 0.06), (yt - 0.19, zt - 0.06)],
                *sorted((xt + sx * 0.30 - 0.05, xt + sx * 0.30 + 0.05)), "X", T)
    for x in (-0.36, 0.0, 0.36):
        m.cyl(rt + 0.012, 0.045, (xt + x, yt, zt), TD, seg=14, axis="X")
    with m.at((xt - 0.20, yt, 0)):                            # manhole
        octa(m, 0.105, 0.105, zt + rt - 0.03, zt + rt + 0.04, T)
        octa(m, 0.075, 0.06, zt + rt + 0.04, zt + rt + 0.075, ST)
    zpip, rp = 1.93, 0.045                                    # two pipes from the drum up to the crown
    for x in (0.47, 0.585):
        m.pipe([(x, yt, zt + rt - 0.03), (x, yt, zpip - 0.10), (x, yt + 0.10, zpip), (x, yw + 0.02, zpip)], rp, ST, seg=8)
        with m.at((x, yt, 0)):
            octa(m, rp + 0.03, rp + 0.018, zt + rt - 0.035, zt + rt + 0.03, T)
            octa(m, rp + 0.014, rp + 0.014, 1.20, 1.245, TD)
        m.cyl(rp + 0.016, 0.026, (x, yw - 0.012, zpip), TD, seg=8, axis="Y", rot=(0, rad(22.5), 0))
    xs = 1.10                                                 # the control stand
    stand = (0.24, 0.34, 0.035)
    with m.at((xs, -0.5, 0)):
        slab(m, stand[0], stand[1], Zp - 0.005, 0.74, stand[2], G, bevel=0.018)
        m.prism([(-0.36, 0.73), (0.36, 0.73), (0.36, 0.80), (-0.36, 0.90)], -0.26, 0.26, "X", TD)       # sloped desk, toward the near side
        for x in (-0.11, 0.09):                               # two levers in the desk
            m.box((0.022, 0.022, 0.20), (x, 0.12, 0.95), ST)
            m.ico(0.035, (x, 0.12, 1.06), PR) if hasattr(m, "ico") else None
    with on_side(m, -1, -0.5 - stand[1], 0.46, xc=xs):        # handwheel on its front
        m.cyl(0.03, 0.09, (0, 0, 0.04), ST, seg=8)
        ring_round(m, 0.14, 0.105, 0.065, 0.10, PR, seg=16)
        for k in range(2):
            m.box((0.24, 0.03, 0.022), (0, 0, 0.082), ST, rot=k * math.pi / 2)
    with on_end(m, 1, xs + stand[0], -0.5, 0.44):
        vent(m, 0.22, 0.17)


former4.frame, former4.shadow = {"iso": (4.6, 1.4), "side": (4.4, 1.5), "top": (3.9, 0.6), "end": (3.6, 1.5)}, True
_hero.HEROES["former4"] = former4


def fat_stack(m, x, y, z0, z1, r=0.115, foot=0.05):
    """A fat eight-sided stack built of short lengths, alternately wide and narrow and alternately pale and
    grey, on a flared foot, under a flared head with a real hollow in it."""
    with m.at((x, y, 0)):
        octa(m, r + foot, r + 0.02, z0 - 0.01, z0 + 0.09, G)
        n = max(2, round((z1 - z0 - 0.22) / 0.17))
        h = (z1 - z0 - 0.22) / n
        for k in range(n):
            za = z0 + 0.08 + k * h
            wide = k % 2 == 0
            octa(m, r if wide else r * 0.84, r if wide else r * 0.84, za, za + h + 0.004, LT if wide else G)
        octa(m, r * 0.9, r + 0.035, z1 - 0.15, z1 - 0.06, G)
        octa(m, r + 0.035, r + 0.035, z1 - 0.062, z1 - 0.02, G)
        oct_ring(m, r + 0.042, 0.047, z1 - 0.022, z1 + 0.02, LT)
        octa(m, r - 0.008, r - 0.008, z1 - 0.05, z1 + 0.002, SLIT)


def framed(m, w, h, inner="h_dark"):
    """A let-in panel in a raised frame, to be built inside on_side or on_end."""
    m.box((w - 0.05, h - 0.05, 0.008), (0, 0, 0.004), inner)
    ring(m, w / 2, h / 2, [(0.0, -0.004), (0.008, 0.024), (0.028, 0.024), (0.036, -0.004)], G, c=0.028)   # the cut must be more than 0.6 of the
                                                              # rim's width, or the corner folds over itself and shows as a dark sliver


def former5(m, paint=None):
    """Former, 3x2 (hitbox 3x2x3). The developer put former3 beside Islands' steel press and said ours is
    simply too simple: make it much more complicated and impressive, but rough. So this is former3's
    kind of machine with its masses fattened and its surfaces filled: the open press has three painted
    frames instead of two, three rods at each corner, a bigger head with a slatted panel, a dark band
    and a bolted plate, dials on the middle frame, and a fat duct that climbs out of its top, turns
    through a box, crosses to the works' house, turns through another box and drops into its roof.
    The house is a grey cabinet with framed doors, big louvres, heavy corner bolts and a sloped hood
    at its end, under a painted body with a row of framed panels and a badge; on the body's roof stand
    a plenum that the duct runs into, and out of the plenum three fat stacks in a
    row, each taller than the last. Beside it a low platform
    carries the mould rack and a pump with its pipe into the press's chassis."""
    paint = paint or PY
    yb = 0.5
    with m.at((0, yb, 0)):
        run(m, -1.5, 1.5, braces=(-4 / 3, -1.0, 1.0, 4 / 3))
        # The press's seat on the belt, in two courses, each wide enough to carry what stands on it and each
        # sloping down at its ends: a dark sill over each rail, and on it a grey bed whose flat top the rods
        # stand on (they used to stand on small shoes that hung over the edge of a belt collar).
        Zc = 0.385
        low = [(0.356, 0.04), (0.494, 0.04), (0.494, 0.245), (0.468, 0.29), (0.356, 0.29)]
        low_end = [(0.356, 0.04), (0.494, 0.04), (0.494, 0.215), (0.468, 0.245), (0.356, 0.245)]
        up = [(0.348, 0.27), (0.49, 0.27), (0.49, 0.357), (0.466, Zc), (0.348, Zc)]
        up_end = [(0.348, 0.27), (0.49, 0.27), (0.49, 0.295), (0.466, 0.30), (0.348, 0.30)]
        for sy in SIDES:
            loft_x(m, [(x, [(sy * y, z) for y, z in o]) for x, o in ((-0.70, low_end), (-0.66, low), (0.66, low), (0.70, low_end))], T)
            loft_x(m, [(x, [(sy * y, z) for y, z in o]) for x, o in ((-0.64, up_end), (-0.585, up), (0.585, up), (0.64, up_end))], G)
        fz = ((0.92, 1.07), (1.58, 1.73), (2.46, 2.61))       # the three frames
        RX, RY = 0.475, 0.44                                  # the corner rod; the two others stand in from it, one each way
        for sx in SIDES:
            for sy in SIDES:
                for dx, dy in ((0.0, 0.0), (-0.075, 0.0), (0.0, -0.068)):                                # three rods to a corner, all inside the frames' beams
                    m.box((0.044, 0.044, fz[2][0] + 0.02 - Zc), (sx * (RX + dx), sy * (RY + dy), (fz[2][0] + 0.02 + Zc) / 2), LT, bevel=0.008)
        for z0, z1 in fz:
            frame_ring(m, 0.545, 0.49, z0, z1, 0.17, paint)
            frame_ring(m, 0.538, 0.483, z0 - 0.03, z0 + 0.004, 0.15, TD)
        for y in (-0.2, 0.2):                                 # cross beams under the top frame; the head hangs from them
            m.prism([(y - 0.055, 2.385), (y + 0.055, 2.385), (y + 0.04, 2.465), (y - 0.04, 2.465)], -0.50, 0.50, "X", G)
        slab(m, 0.37, 0.335, 1.76, 2.395, 0.05, paint, bevel=0.025)                                         # the head
        slab(m, 0.30, 0.28, 1.28, 1.59, 0.04, G, bevel=0.02)                                             # the guide under the middle frame
        octa(m, 0.18, 0.18, 1.01, 1.29, ST)                                                              # the ram
        slab(m, 0.27, 0.25, 0.85, 1.02, 0.035, TD, bevel=0.016)                                          # the die, inside the lowest frame
        m.box((0.32, 0.26, 0.022), (0, 0, BZ + 0.017), LT, bevel=0.006)                                  # the work, on the belt
        with on_end(m, -1, -0.37, 0, 2.225):                  # the head's end: a louvre, and under it the instrument panel
            vent(m, 0.25, 0.115)
        with on_end(m, -1, -0.37, 0, 1.925):                  # the panel: a raised outline round a dark field, and let into the
            m.box((0.46, 0.15, 0.008), (0, 0, 0.004), TD)     # field two dials, each a raised rim round a white face
            ring(m, 0.26, 0.105, [(0.0, -0.004), (0.008, 0.03), (0.03, 0.03), (0.038, -0.004)], G, c=0.03)
            for y, turn in ((-0.125, 0.75), (0.125, -1.15)):  # each needle runs out from its dial's centre, the two at different readings
                with m.at((y, 0, 0)):
                    ring_round(m, 0.056, 0.042, 0.006, 0.026, LT, seg=12)
                    m.cyl(0.043, 0.008, (0, 0, 0.012), "h_white", seg=12)
                    m.box((0.009, 0.034, 0.005), (-0.016 * math.sin(turn), 0.016 * math.cos(turn), 0.0185), "h_red", rot=turn)
                    m.cyl(0.011, 0.009, (0, 0, 0.0215), TD, seg=8)
        with on_side(m, -1, -0.335, 2.08):                    # and its near face
            bolted(m, 0.46, 0.42, G)
        # (the frames' corners carried bolts, on one face and then on both; the developer asked for them all off)
    # the fat duct: up out of the head, through a box, across, through a box, down into the house's roof
    rd, zd, yd = 0.105, 2.80, -0.62
    with m.at((0, yb, 0)):
        octa(m, rd + 0.02, rd + 0.005, 2.385, 2.47, G)                                                   # clear of the cross beams either side
        octa(m, rd, rd, 2.46, zd - 0.12, LT)
        slab(m, 0.14, 0.14, zd - 0.14, zd + 0.14, 0.03, G, bevel=0.02)
    m.cyl(rd * K, yb - yd - 0.26, (0, (yb + yd) / 2, zd), LT, seg=8, axis="Y", rot=(0, rad(22.5), 0))
    for y in (0.20, -0.06, -0.32):
        m.cyl((rd + 0.022) * K, 0.07, (0, y, zd), G, seg=8, axis="Y", rot=(0, rad(22.5), 0))
    with m.at((0, yd, 0)):
        slab(m, 0.14, 0.14, zd - 0.14, zd + 0.14, 0.03, G, bevel=0.02)
    # the near row: a low platform with the mould rack and a pump, and the works' house
    with m.at((-0.86, -0.5, 0)):
        slab(m, 0.56, 0.47, 0.0, 0.14, 0.04, T, bevel=0.014)
    with m.at((-0.98, -0.68, 0)):
        shell(m, [(0.33, 0.20, 0.03, 0.13), (0.34, 0.21, 0.035, 0.23), (0.325, 0.195, 0.03, 0.245),
                  (0.30, 0.17, 0.02, 0.245), (0.29, 0.16, 0.018, 0.17)], ST)
        tower(m, [(0.295, 0.165, 0.02, 0.135), (0.295, 0.165, 0.02, 0.175)], SLIT)
        for k in range(4):
            with m.at((-0.215 + k * 0.143, 0, 0)):
                mould(m, 0.17)
    pump = (0.17, 0.15, 0.03)
    xq = -0.56                                                # beside the press's sill, so that its pipe goes into the sill
    with m.at((xq, -0.24, 0)):
        slab(m, pump[0], pump[1], 0.13, 0.50, pump[2], G, bevel=0.016)
        slab(m, pump[0] + 0.02, pump[1] + 0.02, 0.48, 0.55, cut_to(pump[0] + 0.02, pump[1] + 0.02, pump, 0.02), TD, bevel=0.014)
        octa(m, 0.07, 0.07, 0.54, 0.62, ST)
    with on_side(m, -1, -0.24 - pump[1], 0.31, xc=xq):
        bolted(m, 0.22, 0.20, LT, r=0.014)
    m.cyl(0.045, 0.14, (xq, -0.03, 0.19), LT, seg=8, axis="Y", rot=(0, rad(22.5), 0))
    m.cyl(0.06, 0.03, (xq, -0.035, 0.19), G, seg=8, axis="Y", rot=(0, rad(22.5), 0))
    hx0, hx1 = -0.30, 1.42
    xc, hx = (hx0 + hx1) / 2, (hx1 - hx0) / 2
    body = (hx - 0.05, 0.39, 0.045)
    with m.at((xc, -0.5, 0)):
        slab(m, hx - 0.01, 0.46, 0.0, 0.16, 0.03, T, bevel=0.012)
        slab(m, hx, 0.47, 0.12, 0.665, 0.035, G, bevel=0.02)                                             # cabinet
        slab(m, body[0], body[1], 0.655, 1.10, body[2], paint, bevel=0.022)                                 # the painted body
    yf, ye = -0.97, hx1
    # Nothing on a wall touches or overlaps its neighbour: bolts, doors, louvres and panels each keep at least
    # 0.05 of bare wall between them (the developer: bolts and joints must not run into other trim).
    for x in (0.03, 0.43):                                    # cabinet front: two framed doors with handles, a big louvre
        with on_side(m, -1, yf, 0.40, xc=x):
            framed(m, 0.34, 0.42, LT)
            m.box((0.022, 0.11, 0.022), (0.10, 0, 0.02), TD)
    with on_side(m, -1, yf, 0.40, xc=0.98):
        vent(m, 0.29, 0.21)
    for y in (-0.71, -0.29):                                  # cabinet end: two louvres (a sloped hood stood over them; the
        with on_end(m, 1, ye, y, 0.39):                       # developer asked what it was for, and it is gone)
            vent(m, 0.18, 0.19)
    for x in (hx0 + 0.068, hx1 - 0.068):                      # heavy bolts at the cabinet's corners
        for z in (0.21, 0.59):
            with on_side(m, -1, yf, z, xc=x):
                m.cyl(0.028, 0.02, (0, 0, 0.008), LT, seg=6)
    yp = -0.5 - body[1]                                       # the painted body's front: a row of framed panels, a badge
    for x, w in ((0.02, 0.18), (0.30, 0.26), (0.555, 0.13), (0.745, 0.13), (0.935, 0.13)):
        with on_side(m, -1, yp, 0.88, xc=x):
            framed(m, w, 0.26)
    with on_side(m, -1, yp, 0.88, xc=1.14):
        m.cyl(0.075, 0.022, (0, 0, 0.008), "h_red", seg=6)
        m.cyl(0.04, 0.012, (0, 0, 0.024), "h_white", seg=6)
    for x in (hx0 + 0.13, hx1 - 0.13):                      # in the wall's own corners, clear of the panels and the badge
        for z in (0.72, 1.04):
            with on_side(m, -1, yp, z, xc=x):
                m.cyl(0.026, 0.016, (0, 0, 0.006), G, seg=6)
    # On the body's roof, one system instead of things planted side by side: the duct comes down into a box
    # elbow and runs into the end of a plenum; out of the plenum rise three fat stacks in a row, each taller
    # than the last; a handwheel and a hatch on the plenum, a hatch in the roof.
    Zr, yl = 1.10, yd                                         # the roof, and the line everything stands on
    zq = Zr + 0.145                                           # the height of the pipe that runs along the roof
    with m.at((0, yl, 0)):
        slab(m, 0.14, 0.14, Zr - 0.01, Zr + 0.29, 0.03, G, bevel=0.02)                                   # the lower box elbow, on the roof
        n = 7
        h = (zd - 0.14 - Zr - 0.28) / n
        for k in range(n):
            za = Zr + 0.28 + k * h
            wide = k % 2 == 0
            octa(m, rd if wide else rd * 0.84, rd if wide else rd * 0.84, za, za + h + 0.004, LT if wide else G)
    # The plenum stands taller than the pipe, so the pipe goes into its plain end wall, under the rim, with
    # wall showing all round it (it used to cut into the rim, right under the first stack's foot). The one
    # collar sits half way along the pipe, touching neither the elbow nor the plenum, and the stacks' feet
    # stand in from the plenum's ends.
    px0, px1, ph, pz = 0.385, 1.335, 0.19, Zr + 0.36          # the plenum: its ends, half width, top
    xj = (0.14 + px0) / 2
    m.cyl(rd * K, px0 - 0.13 + 0.02, ((px0 + 0.13) / 2 + 0.005, yl, zq), LT, seg=8, axis="X", rot=(rad(22.5), 0, 0))
    m.cyl((rd + 0.022) * K, 0.06, (xj, yl, zq), G, seg=8, axis="X", rot=(rad(22.5), 0, 0))
    with m.at(((px0 + px1) / 2, yl, 0)):
        slab(m, (px1 - px0) / 2, ph, Zr - 0.01, pz, 0.04, G, bevel=0.02)
        slab(m, (px1 - px0) / 2 + 0.012, ph + 0.012, pz - 0.05, pz + 0.012, cut_to((px1 - px0) / 2 + 0.012, ph + 0.012, ((px1 - px0) / 2, ph, 0.04), 0.012), LT, bevel=0.012)
    tops = (2.10, 2.40, 2.70)
    xs_ = (0.58, 0.86, 1.14)                                  # their feet stand side by side on the plenum, 0.06 in from its ends
    for x, top in zip(xs_, tops):                             # (a rail clamped the three together; the developer asked for it gone)
        fat_stack(m, x, yl, pz, top, 0.10, foot=0.035)
    with on_side(m, -1, yl - ph, Zr + 0.155, xc=0.70):       # on the plenum's near face, below its rim: a hatch and a handwheel
        bolted(m, 0.28, 0.15, LT, r=0.014)
    with on_side(m, -1, yl - ph, Zr + 0.155, xc=1.10):
        m.cyl(0.024, 0.07, (0, 0, 0.03), ST, seg=8)
        ring_round(m, 0.075, 0.052, 0.05, 0.078, paint, seg=14)
        for k in range(2):
            m.box((0.125, 0.02, 0.018), (0, 0, 0.064), ST, rot=k * math.pi / 2)
    m.box((0.46, 0.20, 0.03), (0.74, -0.26, Zr + 0.01), LT, bevel=0.012)                                 # a hatch in the roof behind
    for sx in SIDES:
        for sy in SIDES:
            m.cyl(0.02, 0.012, (0.74 + sx * 0.19, -0.26 + sy * 0.065, Zr + 0.03), TD, seg=6)


former5.frame, former5.shadow, former5.res = {"iso": (4.7, 1.45), "side": (4.4, 1.5), "top": (3.9, 0.6), "end": (3.6, 1.5)}, True, 1600
_hero.HEROES["former5"] = former5


def smelter11(m, e=0.20, hh=0.14, w=0.0):
    """Smelter, 3x1: smelter8, the one the developer liked best ("이 느낌 되게 좋았었음"), made taller at
    his word ("지루하지 않게 높이를 좀 키워보자"). Nothing is added from the big machines' look: it is
    the same body astride the belt, the same wide hearth open to the fire, the same blower and slim
    pipes. Three things can grow: the firebox (by e, its fire mouth with it), the hearth's walls (by
    hh), and, with w, a waist between the hood and the hearth, a narrower shaft with a fire slit in
    each long side, on which the hearth stands like a cup on its stem. The blower's casing grows to
    stay beside the hearth, and the pipes have further to drop."""
    # below the crown: as _smelt_lower, the firebox e taller
    run(m, -1.5, 1.5, braces=(-4 / 3, -1.0, 1.0, 4 / 3))
    cover(m, BX, 1, sole=False)
    cover(m, -BX, -1, sole=False)
    collar(m, -BX - 0.318, BX + 0.318, mk=T)
    hy, hc, xp, he, top = 0.40, 0.355, 0.30, 0.408, 0.712 + e
    bprism(m, [(-xp, -hc), (xp, -hc), (xp, hc), (-xp, hc)], 0.37, top, "Z", G, bevel=0.012)
    for sx in SIDES:
        x0, x1 = sorted((sx * xp, sx * BX))
        bprism(m, [(x0, -hy), (x1, -hy), (x1, hy), (x0, hy)], 0.37, top, "Z", G, bevel=0.012)
    bprism(m, [(-he, 0.70 + e), (-he, 0.74 + e), (-0.30, 0.90 + e), (0.30, 0.90 + e), (he, 0.74 + e), (he, 0.70 + e)], -BX, BX, "X", TD, bevel=0.016)
    for d in SIDES:                                           # the fire mouths, taller with the firebox
        with on_side(m, d, d * hc, 0.535 + e / 2):
            m.box((0.27, 0.15 + e, 0.008), (0, 0, 0.002), "h_glow")
            for k in range(4):
                x = -0.09 + k * 0.06
                m.prism([(x - 0.016, 0.004), (x + 0.016, 0.004), (x + 0.008, 0.019), (x - 0.008, 0.019)], -0.10 - e / 2, 0.10 + e / 2, "Y", TD)
            ring(m, 0.185, 0.125 + e / 2, [(0.0, -0.004), (0.012, 0.03), (0.036, 0.03), (0.05, -0.004)], T, c=0.04)
    P = 0.90 + e
    Ph = P + w                                                # where the hearth stands
    xt, yt = -0.07, 0.03
    if w:                                                     # the waist: a flared foot, a shaft with a fire slit each side, a collar
        with m.at((xt, yt, 0)):
            tower(m, [(0.315, 0.215, 0.05, P), (0.25, 0.16, 0.04, P + 0.06)], T)
            tower(m, [(0.25, 0.16, 0.04, P + 0.06), (0.25, 0.16, 0.04, Ph - 0.045)], G)
            tower(m, [(0.25, 0.16, 0.04, Ph - 0.045), (0.325, 0.225, 0.05, Ph)], TD)
        for d in SIDES:
            with on_side(m, d, yt + d * 0.16, (P + 0.06 + Ph - 0.045) / 2, xc=xt):
                fire_window(m, bars=5, hx=0.16, hy=(w - 0.105) / 2 - 0.03)
    H = 0.40 + hh                                             # the hearth's walls
    with m.at((xt, yt, 0)):
        tower(m, [(0.325, 0.225, 0.05, Ph), (0.30, 0.20, 0.045, Ph + 0.05)], T)
        tower(m, [(0.30, 0.20, 0.045, Ph + 0.05), (0.34, 0.24, 0.05, Ph + H), (0.34, 0.24, 0.05, Ph + H + 0.012)], G)
        shell(m, [(0.355, 0.255, 0.055, Ph + H), (0.355, 0.255, 0.055, Ph + H + 0.045), (0.34, 0.24, 0.05, Ph + H + 0.06),
                  (0.295, 0.195, 0.035, Ph + H + 0.06), (0.285, 0.185, 0.03, Ph + H)], TD)
        tower(m, [(0.292, 0.192, 0.03, Ph + H - 0.005), (0.292, 0.192, 0.03, Ph + H + 0.015)], "h_glow")
        for k in range(7):                                    # bars across the hearth, their ends set into the rim
            x = -0.24 + k * 0.08
            m.prism([(x - 0.02, Ph + H + 0.01), (x + 0.02, Ph + H + 0.01), (x + 0.011, Ph + H + 0.04), (x - 0.011, Ph + H + 0.04)], -0.20, 0.20, "Y", TD)
    # the blower: its casing reaches from the crown to beside the hearth
    xw, yw = 0.385, -0.19
    case = (0.08, 0.10, 0.025)
    zc = Ph + 0.25 + hh / 2                                   # the casing's top
    with m.at((xw, yw, 0)):
        tower(m, [(0.085, 0.11, 0.03, P), (case[0], case[1], case[2], P + 0.04)], T)
        slab(m, case[0], case[1], P + 0.04, zc, case[2], ST, bevel=0.01)
        cc = cut_to(0.088, 0.108, case, 0.008)
        shell(m, [(0.088, 0.108, cc, zc - 0.01), (0.088, 0.108, cc, zc + 0.025), (0.078, 0.098, cc, zc + 0.04),
                  (0.06, 0.08, 0.016, zc + 0.04), (0.054, 0.074, 0.014, zc - 0.01)], TD)
        tower(m, [(0.058, 0.078, 0.015, zc - 0.015), (0.058, 0.078, 0.015, zc + 0.008)], SLIT)
        for y in (-0.028, 0.028):
            m.prism([(y - 0.012, zc + 0.005), (y + 0.012, zc + 0.005), (y + 0.007, zc + 0.028), (y - 0.007, zc + 0.028)], -0.064, 0.064, "X", ST)
    zp, ra, rf, yo, zt = Ph + 0.10, 0.03, 0.038, 0.447, 0.58 + e   # run height, pipe and flange radius, where the wall run stands, a boot's top

    def boot(x, d):
        bprism(m, [(d * 0.39, zt - 0.15), (d * 0.39, zt), (d * 0.492, zt), (d * 0.492, zt - 0.06), (d * 0.44, zt - 0.15)],
               x - 0.042, x + 0.042, "X", T, bevel=0.008)
        m.cyl(rf, 0.022, (x, d * yo, zt + 0.011), TD, seg=8)

    ya, xa = -0.25, -0.345
    m.pipe([(xw - 0.05, ya, zp), (xa + 0.045, ya, zp), (xa, ya - 0.045, zp), (xa, -yo + 0.045, zp), (xa, -yo, zp - 0.045),
            (xa, -yo, zt - 0.02)], ra, ST)
    m.cyl(rf, 0.024, (xw - case[0] - 0.012, ya, zp), TD, seg=8, axis="X", rot=(rad(22.5), 0, 0))
    boot(xa, -1)
    for x in (-0.20, 0.02):                                   # two branches, square into the hearth's wall, each through a collar
        m.pipe([(x, ya, zp), (x, yt - 0.17, zp)], 0.022, ST)
        m.cyl(0.031, 0.018, (x, yt - 0.213, zp), TD, seg=8, axis="Y")
    m.pipe([(xw, yw + case[1] - 0.03, zp), (xw, yo - 0.045, zp), (xw, yo, zp - 0.045), (xw, yo, zt - 0.02)], ra, ST)
    m.cyl(rf, 0.024, (xw, yw + case[1] + 0.012, zp), TD, seg=8, axis="Y")
    boot(xw, 1)
    with on_end(m, 1, xt + 0.332, yt, Ph + 0.25 + hh / 2):    # tap port in the hearth's far end, above the pipe
        octa(m, 0.05, 0.05, -0.006, 0.006, "h_glow")
        oct_ring(m, 0.078, 0.03, -0.022, 0.022, T)


smelter11.frame, smelter11.shadow, smelter11.res = {"iso": (3.5, 0.95), "side": (3.4, 1.1), "top": (3.2, 0.6), "end": (2.6, 1.1)}, True, 1400
_hero.HEROES["smelter11"] = smelter11


def seat(m, half, mk_low=T, mk_up=G, nose=0.055, inner=0.348):
    """A machine's seat on the belt, as former5 has it: over each rail a dark sill and on it a grey bed
    with a flat top, both sloping down at their ends. `half` is how far the bed's flat top reaches each
    way. (The belt collar it replaces has a stepped, leaning face and a narrow top, which whatever
    stands on it overhangs: the developer marked that joint on the former and again on the smelter.)
    With a short `nose` the bed ends in a plain chamfer instead of a slope, for a machine whose tunnel
    mouth stands at the bed's end: a slope would stick out in front of the mouth."""
    Zc = 0.385
    low = [(0.356, 0.04), (0.494, 0.04), (0.494, 0.245), (0.468, 0.29), (0.356, 0.29)]
    low_end = [(0.356, 0.04), (0.494, 0.04), (0.494, 0.215), (0.468, 0.245), (0.356, 0.245)]
    up = [(inner, 0.27), (0.49, 0.27), (0.49, 0.357), (0.466, Zc), (inner, Zc)]       # `inner`: how near the belt the bed's top comes
    up_end = [(inner, 0.27), (0.49, 0.27), (0.49, 0.295), (0.466, 0.30), (inner, 0.30)]
    short = nose < 0.03
    if short:
        up_end = [(inner + nose, 0.27), (0.49 - nose, 0.27), (0.49 - nose, 0.357 - nose), (0.466 - nose, Zc - nose), (inner + nose, Zc - nose)]
    a, b = half + (0.045 if short else 0.075), half
    for sy in SIDES:
        loft_x(m, [(x, [(sy * y, z) for y, z in o]) for x, o in ((-a - 0.04, low_end), (-a, low), (a, low), (a + 0.04, low_end))], mk_low)
        loft_x(m, [(x, [(sy * y, z) for y, z in o]) for x, o in ((-b - nose, up_end), (-b, up), (b, up), (b + nose, up_end))], mk_up)
    return Zc


def smelter12(m):
    """Smelter, 3x1 (hitbox 3x1x2). smelter8 is the one the developer liked best; he asked for it taller
    so that it is not dull, then for it rougher, busier and more complicated, with more pipes (his
    friend's word), and marked the joint between body and belt.
    So: the same body astride the belt, on a designed seat instead of a belt collar; a taller firebox
    with taller fire mouths; on the hood a waist with a fire slit each side, and on the waist the wide
    hearth, banded and bolted, open to the fire. The blower stands at the far end's front corner as it
    did, taller, with a dial let into its face. The pipes are one system: a ring main leaves the blower
    two ways and runs round the hearth, front and back, sending two branches into each long wall, and
    drops at the near end into a boot on each pier, the front drop through a valve with a handwheel;
    two lower pipes leave the blower and drop into boots on the far piers. Every pier has its boot.
    Nothing is taken from the big machines' look (no frame, no plenum, no stacks)."""
    e, w, hh = 0.20, 0.34, 0.10
    run(m, -1.5, 1.5, braces=(-4 / 3, -1.0, 1.0, 4 / 3))
    cover(m, BX, 1, sole=False)
    cover(m, -BX, -1, sole=False)
    seat(m, BX + 0.312, nose=0.012, inner=0.358)              # the bed ends under the mouths' end frames, and stays behind their jambs
    hy, hc, xp, he, top = 0.40, 0.355, 0.30, 0.408, 0.712 + e
    bprism(m, [(-xp, -hc), (xp, -hc), (xp, hc), (-xp, hc)], 0.37, top, "Z", G, bevel=0.012)
    for sx in SIDES:
        x0, x1 = sorted((sx * xp, sx * BX))
        bprism(m, [(x0, -hy), (x1, -hy), (x1, hy), (x0, hy)], 0.37, top, "Z", G, bevel=0.012)
    bprism(m, [(-he, 0.70 + e), (-he, 0.74 + e), (-0.30, 0.90 + e), (0.30, 0.90 + e), (he, 0.74 + e), (he, 0.70 + e)], -BX, BX, "X", TD, bevel=0.016)
    for d in SIDES:                                           # the fire mouths
        with on_side(m, d, d * hc, 0.535 + e / 2):
            m.box((0.27, 0.15 + e, 0.008), (0, 0, 0.002), "h_glow")
            for k in range(4):
                x = -0.09 + k * 0.06
                m.prism([(x - 0.016, 0.004), (x + 0.016, 0.004), (x + 0.008, 0.019), (x - 0.008, 0.019)], -0.10 - e / 2, 0.10 + e / 2, "Y", TD)
            ring(m, 0.185, 0.125 + e / 2, [(0.0, -0.004), (0.012, 0.03), (0.036, 0.03), (0.05, -0.004)], T, c=0.04)
    P = 0.90 + e
    Ph = P + w
    H = 0.40 + hh
    xt, yt = -0.07, 0.03
    with m.at((xt, yt, 0)):                                   # the waist, and on it the hearth
        tower(m, [(0.315, 0.215, 0.05, P), (0.25, 0.16, 0.04, P + 0.06)], T)
        tower(m, [(0.25, 0.16, 0.04, P + 0.06), (0.25, 0.16, 0.04, Ph - 0.045)], G)
        tower(m, [(0.25, 0.16, 0.04, Ph - 0.045), (0.325, 0.225, 0.05, Ph)], TD)
        tower(m, [(0.325, 0.225, 0.05, Ph), (0.30, 0.20, 0.045, Ph + 0.05)], T)
        tower(m, [(0.30, 0.20, 0.045, Ph + 0.05), (0.34, 0.24, 0.05, Ph + H), (0.34, 0.24, 0.05, Ph + H + 0.012)], G)
        t1, t2 = 0.62, 0.76                                   # a heavy band round the walls, following their lean
        tower(m, [(0.314 + 0.04 * t1, 0.214 + 0.04 * t1, 0.055, Ph + 0.05 + (H - 0.05) * t1),
                  (0.314 + 0.04 * t2, 0.214 + 0.04 * t2, 0.055, Ph + 0.05 + (H - 0.05) * t2)], TD)
        shell(m, [(0.355, 0.255, 0.055, Ph + H), (0.355, 0.255, 0.055, Ph + H + 0.045), (0.34, 0.24, 0.05, Ph + H + 0.06),
                  (0.295, 0.195, 0.035, Ph + H + 0.06), (0.285, 0.185, 0.03, Ph + H)], TD)
        tower(m, [(0.292, 0.192, 0.03, Ph + H - 0.005), (0.292, 0.192, 0.03, Ph + H + 0.015)], "h_glow")
        for k in range(7):
            x = -0.24 + k * 0.08
            m.prism([(x - 0.02, Ph + H + 0.01), (x + 0.02, Ph + H + 0.01), (x + 0.011, Ph + H + 0.04), (x - 0.011, Ph + H + 0.04)], -0.20, 0.20, "Y", TD)
    zband = Ph + 0.05 + (H - 0.05) * (t1 + t2) / 2
    for d in SIDES:
        with on_side(m, d, yt + d * 0.16, (P + 0.06 + Ph - 0.045) / 2, xc=xt):   # the waist's fire slits
            fire_window(m, bars=5, hx=0.16, hy=(w - 0.105) / 2 - 0.03)
        for dx in (-0.21, -0.07, 0.07, 0.21):                 # bolts in the band
            with on_side(m, d, yt + d * 0.24, zband, xc=xt + dx):
                m.cyl(0.015, 0.016, (0, 0, 0.004), LT, seg=6)
    with on_end(m, -1, xt - 0.318, yt, Ph + 0.20):            # tap port in the hearth's near end, below the band
        octa(m, 0.05, 0.05, -0.006, 0.006, "h_glow")
        oct_ring(m, 0.078, 0.03, -0.022, 0.022, T)
    # the blower
    xw, yw = 0.385, -0.19
    case = (0.08, 0.10, 0.025)
    zc = Ph + 0.25 + hh / 2
    with m.at((xw, yw, 0)):
        tower(m, [(0.085, 0.11, 0.03, P), (case[0], case[1], case[2], P + 0.04)], T)
        slab(m, case[0], case[1], P + 0.04, zc, case[2], ST, bevel=0.01)
        cc = cut_to(0.088, 0.108, case, 0.008)
        shell(m, [(0.088, 0.108, cc, zc - 0.01), (0.088, 0.108, cc, zc + 0.025), (0.078, 0.098, cc, zc + 0.04),
                  (0.06, 0.08, 0.016, zc + 0.04), (0.054, 0.074, 0.014, zc - 0.01)], TD)
        tower(m, [(0.058, 0.078, 0.015, zc - 0.015), (0.058, 0.078, 0.015, zc + 0.008)], SLIT)
        for y in (-0.028, 0.028):
            m.prism([(y - 0.012, zc + 0.005), (y + 0.012, zc + 0.005), (y + 0.007, zc + 0.028), (y - 0.007, zc + 0.028)], -0.064, 0.064, "X", ST)
    with on_side(m, -1, yw - case[1], zc - 0.12, xc=xw):      # a dial let into the casing's face: a raised rim, the face inside it
        ring_round(m, 0.05, 0.037, -0.004, 0.022, TD, seg=12)
        m.cyl(0.038, 0.008, (0, 0, 0.006), "h_white", seg=12)
        m.box((0.008, 0.028, 0.005), (-0.013 * math.sin(-0.9), 0.013 * math.cos(-0.9), 0.0125), "h_red", rot=-0.9)
        m.cyl(0.0115, 0.009, (0, 0, 0.0155), TD, seg=6)
    # The pipes: one system out of the blower. No bend lies inside a flange, no pipe meets a wall at a slant,
    # and each drop ends straight down in a boot on a pier.
    zp, zq = Ph + 0.10, P + 0.10                              # the ring main's height, the lower pipes' height
    ra, rf, yo, zt, xb = 0.034, 0.046, 0.452, 0.58 + e, 0.385 # pipe and flange radius, where the drops stand, a boot's top, the piers' middle
    ya, yb_ = yt - 0.275, yt + 0.275                          # the ring main's two runs, the same distance off the hearth's walls

    def boot(x, d):
        bprism(m, [(d * 0.39, zt - 0.15), (d * 0.39, zt), (d * 0.494, zt), (d * 0.494, zt - 0.06), (d * 0.44, zt - 0.15)],
               x - 0.046, x + 0.046, "X", T, bevel=0.008)
        m.cyl(rf, 0.022, (x, d * yo, zt + 0.011), TD, seg=8)
        with on_side(m, d, d * hy, 0.50, xc=x):               # a heavy bolt in the pier under each boot
            m.cyl(0.022, 0.018, (0, 0, 0.006), LT, seg=6)

    # ring main, front run: out of the casing's near face, along the hearth, round the corner, over the eave, down
    m.pipe([(xw - 0.05, ya, zp), (-xb + 0.045, ya, zp), (-xb, ya - 0.045, zp), (-xb, -yo + 0.045, zp), (-xb, -yo, zp - 0.045),
            (-xb, -yo, zt - 0.02)], ra, ST)
    m.cyl(rf, 0.024, (xw - case[0] - 0.012, ya, zp), TD, seg=8, axis="X", rot=(rad(22.5), 0, 0))
    # ring main, back run: out of the casing's back, round the far end, along the hearth's back, over the eave, down
    m.pipe([(xw, yw + case[1] - 0.03, zp), (xw, yb_ - 0.045, zp), (xw - 0.045, yb_, zp), (-xb + 0.045, yb_, zp), (-xb, yb_ + 0.045, zp),
            (-xb, yo - 0.045, zp), (-xb, yo, zp - 0.045), (-xb, yo, zt - 0.02)], ra, ST)
    m.cyl(rf, 0.024, (xw, yw + case[1] + 0.012, zp), TD, seg=8, axis="Y")
    for x in (-0.20, 0.02):                                   # two branches from each run, square into the hearth's wall, each through a collar
        for d, yr in ((-1, ya), (1, yb_)):
            m.pipe([(x, yr, zp), (x, yt + d * 0.17, zp)], 0.024, ST)
            m.cyl(0.034, 0.018, (x, yt + d * 0.215, zp), TD, seg=8, axis="Y")
    # the lower pipes: out of the casing's front and back, over the eaves, down into the far piers
    m.pipe([(xw, yw - case[1] + 0.03, zq), (xw, -yo + 0.045, zq), (xw, -yo, zq - 0.045), (xw, -yo, zt - 0.02)], ra, ST)
    m.cyl(rf, 0.024, (xw, yw - case[1] - 0.012, zq), TD, seg=8, axis="Y")
    m.pipe([(xw, yw + case[1] - 0.03, zq), (xw, yo - 0.045, zq), (xw, yo, zq - 0.045), (xw, yo, zt - 0.02)], ra, ST)
    m.cyl(rf, 0.024, (xw, yw + case[1] + 0.012, zq), TD, seg=8, axis="Y")
    for x in (-xb, xb):
        for d in SIDES:
            boot(x, d)
    # a valve in the front drop at the near end, its handwheel turned to the end
    zv = (zp + zt) / 2
    with m.at((-xb, -yo, 0)):
        slab(m, 0.046, 0.044, zv - 0.06, zv + 0.06, 0.014, TD, bevel=0.008)
    with on_end(m, -1, -xb - 0.046, -yo, zv):
        m.cyl(0.014, 0.05, (0, 0, 0.02), ST, seg=8)
        ring_round(m, 0.045, 0.03, 0.034, 0.052, "h_red", seg=12)
        for k in range(2):
            m.box((0.07, 0.012, 0.01), (0, 0, 0.043), ST, rot=k * math.pi / 2)


smelter12.frame, smelter12.shadow, smelter12.res = {"iso": (3.6, 0.98), "side": (3.4, 1.1), "top": (3.2, 0.6), "end": (2.6, 1.1)}, True, 1600
_hero.HEROES["smelter12"] = smelter12


def cog(m, r, teeth=8, mk=G):
    """A gear wheel lying on a panel, to be built inside on_side or on_end."""
    m.cyl(r * 0.82, 0.014, (0, 0, 0.011), mk, seg=12)
    for k in range(teeth):
        a_ = 2 * math.pi * k / teeth
        m.box((r * 0.36, r * 0.30, 0.012), (r * 0.88 * math.cos(a_), r * 0.88 * math.sin(a_), 0.0095), mk, rot=a_)
    m.cyl(r * 0.30, 0.008, (0, 0, 0.021), TD, seg=6)


def smelter13(m):
    """Smelter, 3x1 (hitbox 3x1x2). A new start: the developer dropped every earlier smelter ("시안이
    있으니까 자꾸 빙빙 도는 것 같음") and said to take the Islands smelter's design and work it over in
    our way, as the former was. So this follows that machine's build, in our own parts and under our
    rules (fat parts, a real fire, nothing touching its neighbour, the same seat on the belt as the
    former): a body astride the belt between two tunnel mouths; on it a dark deck that overhangs; on
    the deck, toward the far end, the big hearth box, a dark rim round its open top and the fire under
    a row of bars, a louvre in its end and a tap port in its front; at the near end two fat pipes that
    rise out of the deck, turn through box elbows and go into the hearth's end wall, and between them
    two leaning struts that brace the box; along the deck's edges, before and behind the box, rows of
    capped stubs. In the body's front a fire mouth, and two fat pipes that come out of the wall and
    drop into a dark sump on the seat; in its back a fire mouth and a let-in panel with two gears."""
    run(m, -1.5, 1.5, braces=(-4 / 3, -1.0, 1.0, 4 / 3))
    cover(m, BX, 1, sole=False)
    cover(m, -BX, -1, sole=False)
    Zs = seat(m, BX + 0.312, nose=0.012, inner=0.358)
    hy, hc, xp, top = 0.40, 0.355, 0.30, 0.90
    bprism(m, [(-xp, -hc), (xp, -hc), (xp, hc), (-xp, hc)], 0.37, top, "Z", G, bevel=0.012)
    for sx in SIDES:
        x0, x1 = sorted((sx * xp, sx * BX))
        bprism(m, [(x0, -hy), (x1, -hy), (x1, hy), (x0, hy)], 0.37, top, "Z", G, bevel=0.012)
        for d in SIDES:                                       # two heavy bolts in each pier's face
            for z in (0.50, 0.78):
                with on_side(m, d, d * hy, z, xc=sx * 0.385):
                    m.cyl(0.022, 0.018, (0, 0, 0.006), LT, seg=6)
    Zd = 0.965                                                # the deck's top
    slab(m, 0.50, 0.47, 0.885, Zd, 0.05, TD, bevel=0.016)
    # the body's front: a fire mouth, and two fat pipes out of the wall, down into a sump on the seat
    with on_side(m, -1, -hc, 0.655, xc=-0.16):
        fire_window(m, bars=3, hx=0.105, hy=0.17)
    xs_, yd, rp = (0.06, 0.18), -0.43, 0.042
    for x in xs_:
        m.pipe([(x, -hc + 0.015, 0.80), (x, yd + 0.045, 0.80), (x, yd, 0.755), (x, yd, 0.50)], rp, LT)
        m.cyl(0.058, 0.022, (x, -hc - 0.011, 0.80), TD, seg=8, axis="Y")
        m.cyl(0.056, 0.022, (x, yd, 0.531), TD, seg=8)
    with m.at(((xs_[0] + xs_[1]) / 2, yd, 0)):
        slab(m, 0.125, 0.063, Zs - 0.01, 0.52, 0.02, T, bevel=0.01)
    m.cyl(0.022, 0.02, ((xs_[0] + xs_[1]) / 2 + 0.133, yd, 0.455), LT, seg=6, axis="X")   # the sump's drain plug
    # the body's back: a fire mouth, and a let-in panel with two gears
    with on_side(m, 1, hc, 0.655, xc=0.14):
        fire_window(m, bars=3, hx=0.115, hy=0.17)
    with on_side(m, 1, hc, 0.655, xc=-0.14):
        framed(m, 0.24, 0.26)
        with m.at((-0.035, -0.03, 0)):
            cog(m, 0.062)
        with m.at((0.052, 0.045, 0), rz=rad(22.5)):
            cog(m, 0.046, teeth=6)
    # the hearth box, on the deck toward the far end
    xt, bh = 0.13, (0.30, 0.28)
    Hb = Zd + 0.64
    with m.at((xt, 0, 0)):
        tower(m, [(bh[0] + 0.025, bh[1] + 0.025, 0.045, Zd - 0.01), (bh[0], bh[1], 0.04, Zd + 0.05)], T)
        slab(m, bh[0], bh[1], Zd + 0.04, Hb, 0.04, G, bevel=0.022)
        shell(m, [(bh[0] + 0.025, bh[1] + 0.025, 0.05, Hb - 0.02), (bh[0] + 0.025, bh[1] + 0.025, 0.05, Hb + 0.045), (bh[0] + 0.01, bh[1] + 0.01, 0.045, Hb + 0.06),
                  (bh[0] - 0.035, bh[1] - 0.035, 0.03, Hb + 0.06), (bh[0] - 0.045, bh[1] - 0.045, 0.026, Hb - 0.02)], TD)
        tower(m, [(bh[0] - 0.038, bh[1] - 0.038, 0.026, Hb - 0.006), (bh[0] - 0.038, bh[1] - 0.038, 0.026, Hb + 0.016)], "h_glow")
        for k in range(6):                                    # bars across the fire, their ends set into the rim
            x = -0.20 + k * 0.08
            m.prism([(x - 0.02, Hb + 0.011), (x + 0.02, Hb + 0.011), (x + 0.011, Hb + 0.042), (x - 0.011, Hb + 0.042)], -(bh[1] - 0.04), bh[1] - 0.04, "Y", TD)
    zm = Zd + 0.34                                            # the middle height of the box's walls
    with on_end(m, 1, xt + bh[0], 0, zm):                     # a louvre in the far end
        vent(m, 0.17, 0.15)
    with on_side(m, -1, -bh[1], zm, xc=xt - 0.13):            # front: a bolted plate, and the tap port
        bolted(m, 0.22, 0.28, LT, r=0.016)
    with on_side(m, -1, -bh[1], zm, xc=xt + 0.13):
        octa(m, 0.05, 0.05, -0.006, 0.01, "h_glow")
        oct_ring(m, 0.078, 0.03, -0.01, 0.024, T)
    with on_side(m, 1, bh[1], zm, xc=xt):                     # back: a framed panel
        framed(m, 0.38, 0.30, LT)
    # at the near end: two fat pipes out of the deck, through box elbows, into the hearth's end wall
    xr, rr = -0.36, 0.055
    for sy in SIDES:
        with m.at((xr, sy * 0.18, 0)):
            octa(m, rr + 0.03, rr + 0.012, Zd - 0.01, Zd + 0.05, G)
            octa(m, rr, rr, Zd + 0.045, Zd + 0.16, LT)
            octa(m, rr * 0.86, rr * 0.86, Zd + 0.155, zm - 0.07, G)
            slab(m, 0.07, 0.07, zm - 0.075, zm + 0.075, 0.018, G, bevel=0.012)
        m.cyl(rr * K, xt - bh[0] - xr - 0.07 + 0.03, ((xt - bh[0] + xr + 0.07) / 2, sy * 0.18, zm), LT, seg=8, axis="X", rot=(rad(22.5), 0, 0))
    for sy in SIDES:                                          # and between them two leaning struts that brace the box
        ya, yb2 = sorted((sy * 0.028, sy * 0.073))
        m.prism([(-0.455, Zd - 0.005), (-0.375, Zd - 0.005), (xt - bh[0] + 0.01, Zd + 0.47), (xt - bh[0] + 0.01, Zd + 0.56)], ya, yb2, "Y", ST)
    m.box((0.12, 0.19, 0.03), (-0.415, 0, Zd + 0.008), G, bevel=0.01)        # the struts' shoe
    # capped stubs along the deck's edges, before and behind the box
    for sy in SIDES:
        for x in (0.0, 0.13, 0.26):
            with m.at((x, sy * 0.385, 0)):
                m.cyl(0.046, 0.022, (0, 0, Zd + 0.008), G, seg=6)
                m.cyl(0.034, 0.07, (0, 0, Zd + 0.05), LT, seg=6)
                m.cyl(0.043, 0.028, (0, 0, Zd + 0.096), G, seg=6)


smelter13.frame, smelter13.shadow, smelter13.res = {"iso": (3.5, 0.9), "side": (3.4, 1.0), "top": (3.2, 0.6), "end": (2.6, 1.0)}, True, 1600
_hero.HEROES["smelter13"] = smelter13


def smelter_heights(m):
    """Not a machine: the smelter at three heights in a row, with a figure as tall as a character (1.67
    cells) beside each, to choose a height. From the far side: as it was (1.36), taller (1.70), and
    taller still on a waist (2.0)."""
    for y, kw in ((2.0, dict(e=0.0, hh=0.0, w=0.0)), (0.0, dict(e=0.20, hh=0.14, w=0.0)), (-2.0, dict(e=0.20, hh=0.10, w=0.34))):
        with m.at((0, y, 0)):
            smelter11(m, **kw)
        with m.at((-1.28, y - 0.74, 0)):                      # the figure, clear of the body: legs, body, head
            tower(m, [(0.11, 0.07, 0.02, 0.0), (0.11, 0.07, 0.02, 0.66)], TD)
            tower(m, [(0.165, 0.085, 0.025, 0.66), (0.165, 0.085, 0.025, 1.30)], "h_white")
            tower(m, [(0.10, 0.10, 0.03, 1.31), (0.10, 0.10, 0.03, 1.67)], LT)


smelter_heights.frame, smelter_heights.shadow, smelter_heights.res = {"iso": (6.6, 0.9), "side": (5.0, 1.2), "top": (7.0, 0.6), "end": (7.0, 1.2)}, True, 2600
_hero.HEROES["smelter_heights"] = smelter_heights


def gauges(m, hw, hh, turns=(0.75, -1.15)):
    """An instrument panel, to be built inside on_side or on_end: a raised outline round a dark field, and
    let into the field a row of dials, each a raised rim round a white face, its needle running out from
    the centre. The needles point different ways."""
    m.box((2 * hw - 0.06, 2 * hh - 0.06, 0.008), (0, 0, 0.004), TD)
    ring(m, hw, hh, [(0.0, -0.004), (0.008, 0.03), (0.03, 0.03), (0.038, -0.004)], G, c=0.03)
    n = len(turns)
    step = (2 * hw - 0.10) / n
    for k, turn in enumerate(turns):
        with m.at((-(n - 1) * step / 2 + k * step, 0, 0)):
            ring_round(m, 0.052, 0.039, 0.006, 0.026, LT, seg=12)
            m.cyl(0.04, 0.008, (0, 0, 0.012), "h_white", seg=12)
            m.box((0.009, 0.031, 0.005), (-0.0145 * math.sin(turn), 0.0145 * math.cos(turn), 0.0185), "h_red", rot=turn)
            m.cyl(0.011, 0.009, (0, 0, 0.0215), TD, seg=8)


def smelter10(m, paint=None):
    """REJECTED (2026-10-08): the developer found it bad, and said why: former5's look (a frame on rod
    bundles, a plenum under stacks, long ducts) is for big machines, and the smelter may be smaller and
    needs a look of its own, to be talked through before anything is built.
    Smelter, 4x2 (hitbox 4x2x3), in the look the developer confirmed with former5: fat masses, crowded
    surfaces, grey with one paint colour, the added parts joined into one system, nothing touching its
    neighbour. What the machine is has not changed since smelter8, which the developer approved: ore
    goes through a firebox with fire mouths in its walls, under an open hearth with the fire under a
    row of bars and a glowing tap port in its end.
    The belt runs along the far row, through the firebox. On the firebox lies the painted body, with a
    row of framed panels, an instrument panel and a badge. On the body's roof: the hearth; round it,
    on four bundles of rods, a painted frame left open above the fire (the grammar the developer found
    in Islands' machines: a frame is open above whatever gives off heat or smoke); a fat pipe from the
    hearth's end into the plain end wall of a plenum, out of which two fat stacks rise, one taller than
    the other; and a blower beside the plenum, its louvre to the front and its pipe into the plenum's
    side."""
    paint = paint or PY
    yb, X = 0.5, 1.25
    with m.at((0, yb, 0)):
        bed(m, -2.0, 2.0)
        m.box((4.0, BH * 2, 0.03), (0, 0, BZ - 0.015), "h_belt")
        for x in (-1.80, 1.80):                               # one whole pair of arrows on each open stretch
            chev(m, x)
        for x in (-1.87, 1.87):
            buttress(m, x)
        cover(m, X, 1, sole=False)
        cover(m, -X, -1, sole=False)
        collar(m, -X - 0.318, X + 0.318, mk=T)
    y0, y1 = -0.90, 0.94
    yc, hy = (y0 + y1) / 2, (y1 - y0) / 2
    bx, by = X - 0.08, hy - 0.08                              # the painted body's half sizes
    Zf, Zr = 0.985, 1.32                                      # the firebox's top, the body's roof
    zw, zb = (0.37 + Zf) / 2, (Zf + Zr) / 2                   # the middle heights of the two walls
    bprism(m, [(-X - 0.012, y0 - 0.012), (X + 0.012, y0 - 0.012), (X + 0.012, 0.02), (-X - 0.012, 0.02)], 0.0, 0.39, "Z", T, bevel=0.014)   # the foot, in the near row
    with m.at((0, yc, 0)):
        slab(m, X, hy, 0.37, Zf, 0.05, G, bevel=0.022)        # firebox
        slab(m, bx, by, Zf - 0.01, Zr, 0.045, paint, bevel=0.022)   # the painted body
    # the firebox's walls: on each, everything keeps at least 0.05 of bare wall round it
    for x in (-0.72, -0.08):                                  # front: two fire mouths, a door, a louvre
        with on_side(m, -1, y0, zw, xc=x):
            fire_window(m, bars=6, hx=0.28, hy=0.18)
    with on_side(m, -1, y0, zw, xc=0.50):
        framed(m, 0.34, 0.42, LT)
        m.box((0.022, 0.11, 0.022), (0.10, 0, 0.02), TD)
    with on_side(m, -1, y0, zw, xc=0.90):
        vent(m, 0.17, 0.18)
    for x in (-0.62, 0.62):                                   # back: two fire mouths and a bolted plate between
        with on_side(m, 1, y1, zw, xc=x):
            fire_window(m, bars=6, hx=0.28, hy=0.18)
    with on_side(m, 1, y1, zw, xc=0.0):
        bolted(m, 0.40, 0.36, LT)
    for d, y in ((-1, y0), (1, y1)):                          # heavy bolts in the corners of both long walls
        for x in (-X + 0.085, X - 0.085):
            for z in (0.45, 0.91):
                with on_side(m, d, y, z, xc=x):
                    m.cyl(0.028, 0.02, (0, 0, 0.008), LT, seg=6)
    for sx in SIDES:                                          # each end wall, beside the belt's mouth: a louvre
        with on_end(m, sx, sx * X, -0.45, zw):
            vent(m, 0.28, 0.18)
    # the painted body's walls
    yp = yc - by
    for x, w in ((-0.85, 0.26), (-0.53, 0.26), (-0.275, 0.13), (-0.085, 0.13), (0.105, 0.13)):
        with on_side(m, -1, yp, zb, xc=x):
            framed(m, w, 0.22)
    with on_side(m, -1, yp, zb, xc=0.50):
        gauges(m, 0.22, 0.10)
    with on_side(m, -1, yp, zb, xc=0.88):
        m.cyl(0.075, 0.022, (0, 0, 0.008), "h_red", seg=6)
        m.cyl(0.04, 0.012, (0, 0, 0.024), "h_white", seg=6)
    for x in (-0.80, -0.48, -0.16, 0.16, 0.48, 0.80):
        with on_side(m, 1, yc + by, zb, xc=x):
            framed(m, 0.22, 0.22)
    for d, y in ((-1, yp), (1, yc + by)):
        for x in (-bx + 0.11, bx - 0.11):
            for z in (Zf + 0.05, Zr - 0.055):
                with on_side(m, d, y, z, xc=x):
                    m.cyl(0.026, 0.016, (0, 0, 0.006), G, seg=6)
    for sx in SIDES:
        with on_end(m, sx, sx * bx, yc, zb):
            bolted(m, 0.60, 0.20, G, r=0.016)
    # the hearth, on the roof
    xt = -0.42
    with m.at((xt, yc, 0)):
        tower(m, [(0.44, 0.36, 0.06, Zr - 0.01), (0.46, 0.38, 0.065, Zr + 0.34), (0.46, 0.38, 0.065, Zr + 0.36)], G)
        shell(m, [(0.49, 0.41, 0.075, Zr + 0.33), (0.49, 0.41, 0.075, Zr + 0.40), (0.465, 0.385, 0.065, Zr + 0.425),
                  (0.40, 0.32, 0.045, Zr + 0.425), (0.385, 0.305, 0.04, Zr + 0.33)], TD)
        tower(m, [(0.395, 0.315, 0.042, Zr + 0.322), (0.395, 0.315, 0.042, Zr + 0.372)], "h_glow")   # the fire, showing above the walls' top
        for k in range(6):                                    # bars across the hearth, their ends set into the rim
            x = -0.30 + k * 0.12
            m.prism([(x - 0.03, Zr + 0.366), (x + 0.03, Zr + 0.366), (x + 0.017, Zr + 0.412), (x - 0.017, Zr + 0.412)], -0.33, 0.33, "Y", TD)
        # the frame round the hearth, open above the fire, on four bundles of rods, each bundle on a pad
        z0, z1 = Zr + 0.62, Zr + 0.77
        RX, RY = 0.63, 0.55
        for sx in SIDES:
            for sy in SIDES:
                m.box((0.15, 0.14, 0.03), (sx * (RX - 0.0375), sy * (RY - 0.034), Zr + 0.01), G, bevel=0.008)
                for dx, dy in ((0.0, 0.0), (-0.075, 0.0), (0.0, -0.068)):
                    m.box((0.044, 0.044, z0 + 0.02 - Zr - 0.02), (sx * (RX + dx), sy * (RY + dy), (z0 + 0.02 + Zr + 0.02) / 2), LT, bevel=0.008)
        frame_ring(m, 0.70, 0.62, z0, z1, 0.17, paint)
        frame_ring(m, 0.693, 0.613, z0 - 0.03, z0 + 0.004, 0.15, TD)
    with on_end(m, -1, xt - 0.445, yc, Zr + 0.18):            # tap port in the hearth's end
        octa(m, 0.075, 0.075, -0.008, 0.012, "h_glow")
        oct_ring(m, 0.115, 0.045, -0.04, 0.035, T)
    # the smoke's way: out of the hearth's other end, along the roof, into the plenum's plain end wall, up two stacks
    rd, zq = 0.10, Zr + 0.145
    px0, px1, ph, pz = 0.42, 1.09, 0.20, Zr + 0.36
    xa = xt + 0.445
    m.cyl(rd * K, px0 - xa + 0.03, ((px0 + xa) / 2, yc, zq), LT, seg=8, axis="X", rot=(rad(22.5), 0, 0))
    m.cyl((rd + 0.022) * K, 0.06, ((px0 + xa) / 2, yc, zq), G, seg=8, axis="X", rot=(rad(22.5), 0, 0))
    with m.at(((px0 + px1) / 2, yc, 0)):
        slab(m, (px1 - px0) / 2, ph, Zr - 0.01, pz, 0.04, G, bevel=0.02)
        slab(m, (px1 - px0) / 2 + 0.012, ph + 0.012, pz - 0.05, pz + 0.012, cut_to((px1 - px0) / 2 + 0.012, ph + 0.012, ((px1 - px0) / 2, ph, 0.04), 0.012), LT, bevel=0.012)
    for x, top in ((0.605, 2.42), (0.905, 2.80)):
        fat_stack(m, x, yc, pz, top, 0.105, foot=0.035)
    with on_side(m, 1, yc + ph, Zr + 0.155, xc=(px0 + px1) / 2):   # a hatch in the plenum's far face
        bolted(m, 0.28, 0.15, LT, r=0.014)
    # the blower, in front of the plenum: its louvre to the front, its pipe into the plenum's side
    xw, yw, case = 0.80, yc - 0.54, (0.22, 0.16, 0.03)
    with m.at((xw, yw, 0)):
        slab(m, case[0], case[1], Zr - 0.01, Zr + 0.27, case[2], ST, bevel=0.016)
        slab(m, case[0] + 0.015, case[1] + 0.015, Zr + 0.25, Zr + 0.31, cut_to(case[0] + 0.015, case[1] + 0.015, case, 0.015), TD, bevel=0.014)
        octa(m, 0.07, 0.07, Zr + 0.30, Zr + 0.37, ST)
    with on_side(m, -1, yw - case[1], Zr + 0.13, xc=xw):
        vent(m, 0.16, 0.09)
    ya, yq = yw + case[1], yc - ph
    m.cyl(0.06 * K, yq - ya + 0.03, (xw, (ya + yq) / 2, Zr + 0.14), LT, seg=8, axis="Y", rot=(0, rad(22.5), 0))
    m.cyl(0.078 * K, 0.045, (xw, (ya + yq) / 2, Zr + 0.14), G, seg=8, axis="Y", rot=(0, rad(22.5), 0))
    m.box((0.46, 0.20, 0.03), (0.78, yc + 0.55, Zr + 0.01), LT, bevel=0.012)                             # a hatch in the roof behind
    for sx in SIDES:
        for sy in SIDES:
            m.cyl(0.02, 0.012, (0.78 + sx * 0.19, yc + 0.55 + sy * 0.065, Zr + 0.03), TD, seg=6)


smelter10.frame, smelter10.shadow, smelter10.res = {"iso": (5.4, 1.2), "side": (5.0, 1.3), "top": (4.6, 0.6), "end": (3.6, 1.3)}, True, 1600
_hero.HEROES["smelter10"] = smelter10


def factory_mail(m):
    """Not a machine: a small factory to show what the game looks like, for the developer's letter to
    the makers of Islands. Two lines run side by side, each ore -> smelter (smelter8, the one he liked
    best) -> former: the far line through former5, the near line through former2. The far line runs
    straight into the assembler (assembler4), the near line turns left and right to reach its other
    input. The assembler's output climbs a ramp, crosses over another belt on a raised piece, and
    comes down a ramp again."""
    OX, OY = -0.5, 1.0
    R90 = rad(90)

    def put(fn, x, y, rz=0.0, z=0.0):
        with m.at((x + OX, y + OY, z), rz):
            fn(m)

    def thing(x, y, kind, z=0.0):                             # something riding the belt
        with m.at((x + OX, y + OY, z + BZ + 0.006)):
            if kind == "ore":
                m.box((0.26, 0.24, 0.18), (0, 0, 0.09), "h_ore", bevel=0.05)
            elif kind == "ingot":
                m.box((0.30, 0.16, 0.10), (0, 0, 0.05), "h_steel", bevel=0.03, taper=0.8)
            elif kind == "plate":
                m.box((0.30, 0.26, 0.04), (0, 0, 0.02), "h_lite", bevel=0.012)
            else:                                             # an assembled part: a plate with a boss on it
                m.box((0.30, 0.26, 0.05), (0, 0, 0.025), "h_lite", bevel=0.012)
                m.cyl(0.08, 0.07, (0, 0, 0.085), "h_steel", seg=6)

    for y, former in ((1, former5), (-3, former2)):           # the two lines
        for x in (-10, -9, -8):
            put(_belts.straight, x, y)
        put(smelter8, -6, y)
        put(_belts.straight, -4, y)
        put(former, -2, y - 0.5)
        put(_belts.straight, 0, y)
        thing(-10.1, y, "ore")
        thing(-9.2, y, "ore")
        thing(-8.3, y, "ore")
        thing(-4.0, y, "ingot")
        thing(0.0, y, "plate")
    put(_belts.straight, 1, 1)                                # the far line: straight in
    put(_belts.corner_left, 1, -3)                            # the near line: up two cells, then in
    put(_belts.straight, 1, -2, R90)
    put(_belts.corner_right, 1, -1, R90)
    thing(1.0, -2.0, "plate")
    put(assembler4, 3, 0)
    put(_belts.straight, 5, 0)                                # the output: up a ramp, over a crossing belt, down again
    put(lambda mm: _belts.ramp(mm, True, True), 6.5, 0)
    put(_belts.straight, 8, 0, 0.0, 1.0)
    put(lambda mm: _belts.ramp(mm, True, True, down=True), 9.5, 0)
    put(_belts.straight, 11, 0)
    thing(5.0, 0, "part")
    thing(8.0, 0, "part", 1.0)
    thing(11.0, 0, "part")
    for y in (-3, -2, -1, 0, 1, 2):                           # the belt that passes under the raised piece
        put(_belts.straight, 8, y, R90)
    for y in (-2.6, -1.4, 1.5):
        thing(8.0, y, "ore")


factory_mail.frame, factory_mail.shadow, factory_mail.res = {"iso": (23.0, 1.2), "side": (22.0, 1.6), "top": (23.0, 0.6), "end": (9.0, 1.6)}, True, 3200
_hero.HEROES["factory_mail"] = factory_mail


PAINTS = {"h_p1": "#cf5134", "h_p2": "#2f8f8a", "h_p3": "#3f6f9f", "h_p4": "#d9822b"}       # trial paints: vermilion, teal, steel blue, orange
fk.PAL.update(PAINTS)
fk.PAL.update({"h_neon": "#ee2f25"})                      # red neon, for a grate the furnace breathes through
fk.EMIT.update({"h_neon": 1.8})


def handwheel(m, r=0.11, mk="h_red"):
    """A valve handwheel standing off a wall, to be built inside on_side or on_end: a five-sided rim, one
    corner up, on a cross of spokes and a hub. (The developer asked for the rim angular, five- or
    six-sided, and for the wheels bigger; Islands' are five-sided too, and about a third of a wall high.)"""
    m.cyl(r * 0.26, 0.06, (0, 0, 0.026), ST, seg=6)
    with m.at((0, 0, 0), rz=rad(90)):
        ring_round(m, r, r * 0.70, 0.038, 0.066, mk, seg=5)
    for k in range(2):
        m.box((r * 1.36, r * 0.22, 0.014), (0, 0, 0.051), ST, rot=k * math.pi / 2)
    m.cyl(r * 0.20, 0.016, (0, 0, 0.066), LT, seg=6)


def grid(m, hw, hh, nx, ny):
    """A let-in panel of small raised squares in rows, to be built inside on_side or on_end."""
    m.box((2 * hw - 0.06, 2 * hh - 0.06, 0.008), (0, 0, 0.004), TD)
    ring(m, hw, hh, [(0.0, -0.004), (0.008, 0.026), (0.026, 0.026), (0.034, -0.004)], G, c=0.024)
    ax, ay = hw - 0.046, hh - 0.046
    sx_, sy_ = 2 * ax / nx, 2 * ay / ny
    for a_ in range(nx):
        for b_ in range(ny):
            m.box((sx_ - 0.016, sy_ - 0.016, 0.012), (-ax + (a_ + 0.5) * sx_, -ay + (b_ + 0.5) * sy_, 0.013), LT, bevel=0.004)


def mill6(m, paint="h_p1"):
    """REJECTED (2026-10-08): still too much after three rounds of trimming; the developer said to forget it.
    Steel mill, 3x3 (hitbox 3x3x3): iron and coal come in at the two mouths in the west, steel leaves
    by the mouth in the east. After two rejected attempts the developer said to go as the former went:
    follow the build of Islands' steel mill in our own parts, under the rules settled on former5.
    Two masses on one footing. In the west the machine room, low and long: a grey cabinet with a painted
    body on it, the two inlet mouths in its wall, each in a painted portal with a dark seam. In the east
    the furnace, tall: a grey block with a smaller upper block and a dark cap, and round it, on four
    bundles of rods, two painted frames, one at the furnace's waist and one above its top, the upper one
    crossed by two beams that leave a square open over the fat stack rising from the cap (a frame is
    left open above whatever smokes). The outlet mouth is in the furnace's east wall, in a portal like
    the inlets'. Two fat ducts leave the furnace's upper block, cross over the lower frame and turn
    down through box elbows into the machine room's roof; between the elbows stands a short fat stack.
    The fire shows in one place: two grates of red neon behind bars in the furnace's cap, under the
    upper frame's open bays."""
    g = 2 * (BH - 0.305)

    def portal(xa, d, y):                                     # two painted arches with a dark seam between, and the tunnel's dark
        with m.at((0, y, 0)):
            px = xa
            for th, w, tp, mk in ((0.08, 0.84 + g, 0.82, paint), (0.022, 0.79 + g, 0.795, SLIT), (0.08, 0.84 + g, 0.82, paint)):
                a_, b_ = sorted((px, px + d * th))
                m.prism(arch_pts(w, tp, hole_top=0.70, hw=BH + 0.01, c=0.085, ci=0.035), a_, b_, "X", mk)
                px += d * th
            m.box((0.02, 2 * BH + 0.01, 0.694 - BZ), (xa + d * 0.012, 0, (0.706 + BZ) / 2), SLIT)
            xo = xa + d * 0.182                               # the portal's outer face
            for sy_ in SIDES:                                 # each rail rises into the portal's leg, in the rail's own colour
                pts = [(xo - d * 0.006, 0.03), (xo + d * 0.13, 0.03), (xo + d * 0.13, 0.24), (xo + d * 0.10, 0.262), (xo - d * 0.006, 0.44)]
                bprism(m, pts if d > 0 else pts[::-1], *sorted((sy_ * 0.358, sy_ * 0.494)), "Y", R, bevel=0.008)

    # ---- the machine room, in the west
    xr0, xr1, yr = -1.05, -0.22, 1.42
    xr, hxr = (xr0 + xr1) / 2, (xr1 - xr0) / 2
    Zc, Zr = 0.90, 1.20                                       # the cabinet's top, the roof
    zc, zb = (0.12 + Zc) / 2, (Zc + Zr) / 2
    bodyr = (hxr - 0.05, yr - 0.06, 0.045)
    for sy in SIDES:
        with m.at((0, sy * 1.0, 0)):
            belt_stub(m, -1.5, xr0 + 0.02, -1.39, -1.455)
        portal(xr0, -1, sy * 1.0)
    with m.at((xr, 0, 0)):
        slab(m, hxr + 0.015, yr + 0.02, 0.0, 0.16, 0.03, T, bevel=0.012)
        slab(m, hxr, yr, 0.12, Zc, 0.035, G, bevel=0.02)     # corner cuts and bevels as on former5: cabinet 0.035 / 0.02, painted body 0.045 / 0.022
        slab(m, bodyr[0], bodyr[1], Zc - 0.01, Zr, bodyr[2], paint, bevel=0.022)
    with on_end(m, -1, xr0, -0.30, zc):                       # the cabinet's west wall, between the mouths: the machine's one louvre, and two big handwheels
        vent(m, 0.15, 0.17)
    for y in (0.07, 0.35):
        with on_end(m, -1, xr0, y, zc + 0.02):
            handwheel(m, 0.11)
    # The painted body's west wall. It was a row of eight equal square panels, which the developer found dull:
    # now a wide panel, three narrow ones, a bolted name plate, a panel of small squares and a badge.
    xbw = xr - bodyr[0]
    # (then five kinds of small thing; the developer's reading of Islands is a few fair-sized things, each one
    # something a machine would have: so a wide panel, a name plate, two more panels of other widths, a badge)
    for y, w in ((-0.90, 0.50), (0.38, 0.30), (0.70, 0.18)):
        with on_end(m, -1, xbw, y, zb):
            framed(m, w, 0.20)
    with on_end(m, -1, xbw, -0.25, zb):
        bolted(m, 0.50, 0.17, LT, r=0.016)
    with on_end(m, -1, xbw, 1.02, zb):
        m.cyl(0.075, 0.022, (0, 0, 0.008), "h_red", seg=6)
        m.cyl(0.04, 0.012, (0, 0, 0.024), "h_white", seg=6)
    for y in (-1.27, 1.27):
        for z in (Zc + 0.06, Zr - 0.06):
            with on_end(m, -1, xr - bodyr[0], y, z):
                m.cyl(0.026, 0.016, (0, 0, 0.006), G, seg=6)
    for d in SIDES:                                           # the room's two end walls: a door and a let-in panel
        with on_side(m, d, d * yr, zc, xc=xr - 0.17):
            framed(m, 0.30, 0.46, LT)
            m.box((0.022, 0.11, 0.022), (0.09 * -d, 0, 0.02), TD)
        with on_side(m, d, d * yr, zc, xc=xr + 0.185):
            framed(m, 0.24, 0.46)
        with on_side(m, d, d * bodyr[1], zb, xc=xr):
            if d < 0:                                         # the machine's one dial panel, on the near end
                gauges(m, 0.24, 0.10, turns=(0.75, -1.15, 0.2))
            else:
                bolted(m, 0.44, 0.17, LT, r=0.014)
    # ---- the furnace, in the east
    xf, fx, fy = 0.55, 0.50, 0.90                             # its middle, its half sizes
    Zl, Zu, Zk = 1.14, 1.72, 1.80                             # the lower block's top, the upper block's top, the cap's top
    with m.at((xf, 0, 0)):
        slab(m, 0.78, 1.14, 0.0, 0.14, 0.04, T, bevel=0.014)                                             # the footing the furnace and its rods stand on
        slab(m, fx, fy, 0.10, Zl, 0.035, G, bevel=0.02)
        slab(m, fx - 0.03, fy - 0.03, Zl - 0.01, Zu, 0.035, G, bevel=0.02)
        slab(m, fx, fy, Zu - 0.02, Zk, 0.035, TD, bevel=0.014)
        fa, fb = (1.19, 1.34), (2.22, 2.37)                   # the two frames
        RX, RY = 0.65, 1.03
        for sx in SIDES:
            for sy in SIDES:
                m.box((0.15, 0.14, 0.03), (sx * (RX - 0.0375), sy * (RY - 0.034), 0.15), G, bevel=0.008)
                for dx, dy in ((0.0, 0.0), (-0.075, 0.0), (0.0, -0.068)):
                    m.box((0.044, 0.044, fb[0] + 0.02 - 0.16), (sx * (RX + dx), sy * (RY + dy), (fb[0] + 0.02 + 0.16) / 2), LT, bevel=0.008)
        for z0, z1 in (fa, fb):
            frame_ring(m, 0.72, 1.10, z0, z1, 0.17, paint)
            frame_ring(m, 0.713, 1.093, z0 - 0.03, z0 + 0.004, 0.15, TD)
        for sy in SIDES:                                      # two beams across the upper frame, leaving a square open over the stack
            m.box((1.14, 0.15, fb[1] - fb[0] - 0.04), (0, sy * 0.36, (fb[0] + fb[1]) / 2), paint, bevel=0.014)
    fat_stack(m, xf, 0, Zk, 2.95, 0.19, foot=0.09)
    # In the cap, each side of the stack and under the frame's open bays: a grate of red neon behind bars, as if
    # the furnace breathed out through it. (They were bolted hatches; the stack's mouth glowed orange, which the
    # developer found odd, and is dark now like every other stack's.)
    for sy in SIDES:
        with m.at((xf, sy * 0.66, Zk)):
            m.box((0.42, 0.18, 0.014), (0, 0, 0.004), "h_neon")
            for k in range(5):
                x = -0.17 + k * 0.085
                m.prism([(x - 0.015, 0.009), (x + 0.015, 0.009), (x + 0.008, 0.03), (x - 0.008, 0.03)], -0.10, 0.10, "Y", LT)
            ring(m, 0.25, 0.13, [(0.0, -0.004), (0.01, 0.034), (0.034, 0.034), (0.046, -0.004)], TD, c=0.03)
    # The furnace's long walls, filled as Islands fills a big wall: not with many small fittings but with one
    # big let-in panel, and inside it a fair-sized door and a sight port. Above the frame, a bolted plate.
    for d in SIDES:
        with on_side(m, d, d * fy, 0.62, xc=xf):
            framed(m, 0.84, 0.74)
            with m.at((-0.18, -0.04, 0.006)):                 # a fair-sized door
                framed(m, 0.34, 0.56, LT)
                m.box((0.024, 0.13, 0.022), (0.105, 0, 0.02), TD)
            with m.at((0.20, 0.0, 0.008)):                    # and a sight port: a thick eight-sided rim round dark glass
                octa(m, 0.10, 0.10, -0.004, 0.012, SLIT)
                oct_ring(m, 0.145, 0.05, -0.006, 0.036, G)
                for k in range(4):
                    a_ = math.pi / 4 + k * math.pi / 2
                    m.cyl(0.016, 0.014, (0.118 * math.cos(a_), 0.118 * math.sin(a_), 0.04), TD, seg=6)
        with on_side(m, d, d * (fy - 0.03), (fa[1] + Zu - 0.02) / 2, xc=xf):
            bolted(m, 0.62, 0.22, LT, r=0.016)
    # the outlet, in the furnace's east wall
    belt_stub(m, xf + fx - 0.02, 1.5, 1.39, 1.455)
    portal(xf + fx, 1, 0.0)
    for y in (-0.67, 0.67):                                   # a tall let-in panel each side of the mouth
        with on_end(m, 1, xf + fx, y, 0.60):
            framed(m, 0.22, 0.56)
    with on_end(m, 1, xf + fx - 0.03, 0, (fa[1] + Zu - 0.02) / 2):
        bolted(m, 1.00, 0.22, LT, r=0.016)
    # ---- the two fat ducts: out of the furnace's upper block, over the lower frame, through box elbows, down into the room's roof
    rd, zq, xe = 0.105, 1.53, -0.62                           # the duct as fat as former5's, its elbows the same boxes
    xw = xf - fx + 0.03                                       # the upper block's west wall
    for sy in SIDES:
        y = sy * 0.50
        m.cyl(rd * K, xw - (xe + 0.14) + 0.04, ((xw + xe + 0.14) / 2, y, zq), LT, seg=8, axis="X", rot=(rad(22.5), 0, 0))
        m.cyl((rd + 0.022) * K, 0.07, ((xw + xe + 0.14) / 2 - 0.06, y, zq), G, seg=8, axis="X", rot=(rad(22.5), 0, 0))
        with m.at((xe, y, 0)):
            slab(m, 0.14, 0.14, zq - 0.14, zq + 0.14, 0.03, G, bevel=0.02)
            octa(m, rd + 0.05, rd + 0.02, Zr - 0.01, Zr + 0.08, G)
            octa(m, rd, rd, Zr + 0.07, zq - 0.13, LT)
    fat_stack(m, xe - 0.02, 0, Zr, 2.02, 0.10)                # a short fat stack between the elbows
    for sy in SIDES:                                          # a bolted hatch in the roof at each end
        m.box((0.40, 0.26, 0.03), (xr, sy * 1.0, Zr + 0.01), LT, bevel=0.012)
        for a_ in SIDES:
            for b_ in SIDES:
                m.cyl(0.02, 0.012, (xr + a_ * 0.15, sy * 1.0 + b_ * 0.085, Zr + 0.03), TD, seg=6)


mill6.frame, mill6.shadow, mill6.res = {"iso": (5.4, 1.45), "side": (5.0, 1.5), "top": (4.4, 0.6), "end": (4.4, 1.5)}, True, 1800
_hero.HEROES["mill6"] = mill6


def mill7(m, paint="h_p1"):
    """Steel mill, 3x3 (hitbox 3x3x3), begun again from nothing: the developer found mill6 still too much
    and said to forget it, not to cling to symmetry, and to ask of every grey plate, door and window
    what it is there to do. So this one is put together from what a steel furnace does, and every part
    has a job (the machine sheet's one line: iron and coal are carried up to the top of a high furnace,
    melt together in a hot blast, and run out as steel):
    - the receiving hall, low, along the west, where the two belts come in: one bolted cover between the
      mouths (to get at the conveyor inside) and one door in its south end (to walk in);
    - the charging incline, a cleated belt between two stringers, from a loading box on the hall's roof up
      to a hood on the furnace's top, on the north side;
    - the furnace, a tall eight-sided shaft on a wider hearth, hooped, inside two painted frames on rod
      bundles; its stack stands off-centre on the cap, and beside it one grate of red neon behind bars
      where the heat comes out;
    - the blower, on the hall's roof at the south end, its one louvre the air intake; from it the blast
      main runs east past a valve with a big handwheel and a pressure dial, over a pier, round a box
      elbow and into the ring main that goes round the furnace above the hearth, from which four
      nozzles blow into the shaft;
    - the tap house on the hearth's east side, where the steel leaves by the outlet belt."""
    g = 2 * (BH - 0.305)

    def portal(xa, d, y):                                     # two painted arches with a dark seam between; each rail rises into its leg
        with m.at((0, y, 0)):
            px = xa
            for th, w, tp, mk in ((0.08, 0.84 + g, 0.82, paint), (0.022, 0.79 + g, 0.795, SLIT), (0.08, 0.84 + g, 0.82, paint)):
                a_, b_ = sorted((px, px + d * th))
                m.prism(arch_pts(w, tp, hole_top=0.70, hw=BH + 0.01, c=0.085, ci=0.035), a_, b_, "X", mk)
                px += d * th
            m.box((0.02, 2 * BH + 0.01, 0.694 - BZ), (xa + d * 0.012, 0, (0.706 + BZ) / 2), SLIT)
            xo = xa + d * 0.182
            for sy_ in SIDES:
                pts = [(xo - d * 0.006, 0.03), (xo + d * 0.13, 0.03), (xo + d * 0.13, 0.24), (xo + d * 0.10, 0.262), (xo - d * 0.006, 0.44)]
                bprism(m, pts if d > 0 else pts[::-1], *sorted((sy_ * 0.358, sy_ * 0.494)), "Y", R, bevel=0.008)

    # ---- the receiving hall
    xh0, xh1, yh = -1.05, -0.36, 1.42
    xh, hxh = (xh0 + xh1) / 2, (xh1 - xh0) / 2
    Zh, Zd = 0.90, 0.96                                       # the wall's top, the deck
    for sy in SIDES:
        with m.at((0, sy * 1.0, 0)):
            belt_stub(m, -1.5, xh0 + 0.02, -1.39, -1.455)
        portal(xh0, -1, sy * 1.0)
    with m.at((xh, 0, 0)):
        slab(m, hxh + 0.015, yh + 0.02, 0.0, 0.16, 0.03, T, bevel=0.012)
        slab(m, hxh, yh, 0.12, Zh, 0.035, G, bevel=0.02)
        slab(m, hxh + 0.025, yh + 0.025, Zh - 0.015, Zd, 0.045, TD, bevel=0.014)
    with on_end(m, -1, xh0, 0.0, 0.50):                       # the cover over the conveyor inside, between the mouths
        bolted(m, 0.70, 0.46, LT, r=0.03)
    with on_side(m, -1, -yh, 0.47, xc=xh):                    # the door, in the south end
        framed(m, 0.34, 0.60, LT)
        m.box((0.024, 0.13, 0.022), (0.105, 0, 0.02), TD)
    # ---- the furnace
    xf = 0.45
    fa, fb = (1.26, 1.41), (2.38, 2.53)                       # the two frames
    RX = 0.70
    with m.at((xf, 0, 0)):
        slab(m, 0.80, 0.80, 0.0, 0.14, 0.04, T, bevel=0.014)  # the footing
        octa(m, 0.58, 0.58, 0.12, 0.74, G)                    # hearth
        octa(m, 0.61, 0.61, 0.72, 0.80, TD)
        octa(m, 0.58, 0.52, 0.79, 1.00, G)                    # bosh
        octa(m, 0.52, 0.44, 0.99, 1.98, G)                    # shaft
        octa(m, 0.479, 0.473, 1.66, 1.74, TD)                 # a hoop
        octa(m, 0.47, 0.47, 1.97, 2.05, TD)                   # cap
        for sx in SIDES:
            for sy in SIDES:
                m.box((0.15, 0.14, 0.03), (sx * (RX - 0.0375), sy * (RX - 0.034), 0.15), G, bevel=0.008)
                for dx, dy in ((0.0, 0.0), (-0.075, 0.0), (0.0, -0.068)):
                    m.box((0.044, 0.044, fb[0] + 0.02 - 0.16), (sx * (RX + dx), sy * (RX + dy), (fb[0] + 0.02 + 0.16) / 2), LT, bevel=0.008)
        for z0, z1 in (fa, fb):
            frame_ring(m, 0.77, 0.77, z0, z1, 0.17, paint)
            frame_ring(m, 0.763, 0.763, z0 - 0.03, z0 + 0.004, 0.15, TD)
    fat_stack(m, xf + 0.14, -0.10, 2.05, 2.95, 0.15, foot=0.06)   # the stack, off-centre on the cap
    with m.at((xf + 0.08, 0.25, 2.05)):                       # where the heat comes out: red neon behind bars
        m.box((0.26, 0.12, 0.014), (0, 0, 0.004), "h_neon")
        for k in range(4):
            x = -0.105 + k * 0.07
            m.prism([(x - 0.013, 0.009), (x + 0.013, 0.009), (x + 0.007, 0.03), (x - 0.007, 0.03)], -0.065, 0.065, "Y", LT)
        ring(m, 0.16, 0.09, [(0.0, -0.004), (0.01, 0.034), (0.03, 0.034), (0.04, -0.004)], TD, c=0.026)
    # the tap house, and the outlet
    with m.at((0.885, 0, 0)):
        slab(m, 0.165, 0.50, 0.12, 0.92, 0.035, G, bevel=0.02)
        slab(m, 0.18, 0.515, 0.90, 0.96, 0.045, TD, bevel=0.014)
    belt_stub(m, 1.03, 1.5, 1.39, 1.455)
    portal(1.05, 1, 0.0)
    # ---- the blast: blower, main, valve, ring main, nozzles
    zr, rd = 1.10, 0.105
    xb, yb_, case = -0.70, -1.05, (0.26, 0.30, 0.045)
    with m.at((xb, yb_, 0)):
        slab(m, case[0], case[1], Zd - 0.01, Zd + 0.46, case[2], paint, bevel=0.022)
        slab(m, case[0] + 0.015, case[1] + 0.015, Zd + 0.44, Zd + 0.51, cut_to(case[0] + 0.015, case[1] + 0.015, case, 0.015), TD, bevel=0.014)
    with on_end(m, -1, xb - case[0], yb_, Zd + 0.22):         # the air intake: the machine's one louvre
        vent(m, 0.22, 0.15)
    xe = xf                                                   # the elbow stands south of the furnace's middle
    xm0, xm1 = xb + case[0], xe - 0.14
    m.cyl(rd * K, xm1 - xm0 + 0.03, ((xm0 + xm1) / 2, yb_, zr), LT, seg=8, axis="X", rot=(rad(22.5), 0, 0))
    xv = -0.02                                                # the valve
    with m.at((xv, yb_, 0)):
        slab(m, 0.13, 0.13, zr - 0.14, zr + 0.14, 0.03, G, bevel=0.02)
        octa(m, 0.022, 0.022, zr + 0.13, zr + 0.25, ST)       # the dial's stem
    with on_side(m, -1, yb_ - 0.13, zr, xc=xv):
        handwheel(m, 0.13)
    m.cyl(0.075, 0.06, (xv, yb_, zr + 0.31), G, seg=12, axis="Y")                                        # the pressure dial, facing south
    with on_side(m, -1, yb_ - 0.03, zr + 0.31, xc=xv):
        ring_round(m, 0.075, 0.058, 0.0, 0.026, TD, seg=12)
        m.cyl(0.059, 0.008, (0, 0, 0.006), "h_white", seg=12)
        m.box((0.011, 0.044, 0.005), (-0.02 * math.sin(-0.8), 0.02 * math.cos(-0.8), 0.0125), "h_red", rot=-0.8)
        m.cyl(0.013, 0.009, (0, 0, 0.0155), TD, seg=6)
    for x in ((xm0 + xv - 0.13) / 2, (xv + 0.13 + xm1) / 2):  # a collar each side of the valve
        m.cyl((rd + 0.022) * K, 0.06, (x, yb_, zr), G, seg=8, axis="X", rot=(rad(22.5), 0, 0))
    xp = (xv + 0.13 + xm1) / 2                                # a pier under the main, below the second collar
    with m.at((xp, yb_, 0)):
        slab(m, 0.10, 0.13, 0.0, 0.07, 0.03, T, bevel=0.012)
        slab(m, 0.05, 0.075, 0.05, zr - 0.13, 0.015, ST, bevel=0.01)
        slab(m, 0.085, 0.115, zr - 0.15, zr - 0.09, 0.02, G, bevel=0.012)
    with m.at((xe, yb_, 0)):
        slab(m, 0.14, 0.14, zr - 0.14, zr + 0.14, 0.03, G, bevel=0.02)
    Rr, rr = 0.66, 0.07                                       # the ring main: how far out it runs, how fat it is
    m.cyl(rd * K, -Rr - (yb_ + 0.14) + 0.06, (xe, (yb_ + 0.14 - Rr) / 2, zr), LT, seg=8, axis="Y", rot=(0, rad(22.5), 0))
    for k in range(8):
        with m.at((xf, 0, 0), rz=rad(45 * k)):
            m.cyl(rr * K, 2 * Rr * math.tan(rad(22.5)) + 0.02, (0, -Rr, zr), LT, seg=8, axis="X", rot=(rad(22.5), 0, 0))
        with m.at((xf, 0, 0), rz=rad(45 * k + 22.5)):
            m.box((0.17, 0.17, 0.18), (0, -Rr / math.cos(rad(22.5)), zr), G, bevel=0.022)
    for k in (1, 3, 5, 7):                                    # four nozzles from the ring into the shaft
        with m.at((xf, 0, 0), rz=rad(45 * k)):
            m.cyl(0.045 * K, 0.15, (0, -0.555, zr), ST, seg=8, axis="Y", rot=(0, rad(22.5), 0))
    # ---- the charging incline, on the north side: a loading box on the hall's roof, a cleated belt between two stringers, a hood on the cap
    yi = 0.30
    p0, p1 = (-0.84, 1.00), (xf - 0.33, 2.09)
    L = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
    u = ((p1[0] - p0[0]) / L, (p1[1] - p0[1]) / L)
    n_ = (-u[1], u[0])

    def P(s_, h):
        return (p0[0] + u[0] * s_ + n_[0] * h, p0[1] + u[1] * s_ + n_[1] * h)

    m.prism([P(0, -0.035), P(L, -0.035), P(L, 0.02), P(0, 0.02)], yi - 0.10, yi + 0.10, "Y", "h_belt")
    for sy in SIDES:
        m.prism([P(-0.02, -0.07), P(L + 0.02, -0.07), P(L + 0.02, 0.06), P(-0.02, 0.06)], *sorted((yi + sy * 0.10, yi + sy * 0.145)), "Y", LT)
    for k in range(1, 9):
        s_ = k * L / 9
        m.prism([P(s_ - 0.014, 0.02), P(s_ + 0.014, 0.02), P(s_ + 0.008, 0.046), P(s_ - 0.008, 0.046)], yi - 0.09, yi + 0.09, "Y", LT)
    with m.at((-0.80, yi, 0)):                                # the loading box
        slab(m, 0.16, 0.19, Zd - 0.01, Zd + 0.22, 0.035, G, bevel=0.02)
        slab(m, 0.175, 0.205, Zd + 0.20, Zd + 0.26, 0.045, TD, bevel=0.014)
    with m.at((xf - 0.25, yi, 0)):                            # the hood over the furnace's mouth
        slab(m, 0.12, 0.17, 2.04, 2.27, 0.035, G, bevel=0.02)
        slab(m, 0.135, 0.185, 2.25, 2.31, 0.045, TD, bevel=0.014)
    xs_ = -0.46                                               # a trestle under the incline, on the hall's roof
    st = (xs_ - p0[0] - n_[0] * -0.07) / u[0]
    zt = P(st, -0.07)[1]
    for sy in SIDES:
        m.box((0.045, 0.04, zt + 0.02 - Zd), (xs_, yi + sy * 0.1225, (zt + 0.02 + Zd) / 2), ST, bevel=0.008)
    m.box((0.11, 0.33, 0.03), (xs_, yi, Zd + 0.008), G, bevel=0.01)


mill7.frame, mill7.shadow, mill7.res = {"iso": (5.6, 1.45), "side": (5.0, 1.5), "top": (4.4, 0.6), "end": (4.4, 1.5)}, True, 1800
_hero.HEROES["mill7"] = mill7


def hexbolt(m, r=0.04):
    """A heavy six-sided bolt head on a washer, to be built inside on_side or on_end."""
    m.cyl(r * 1.25, 0.012, (0, 0, 0.004), "h_dark", seg=12)
    m.cyl(r, 0.03, (0, 0, 0.02), LT, seg=6)


def sunk(m, w, h):
    """A big let-in panel in steps, to be built inside on_side or on_end: a thick raised frame, a field
    set back inside it, and a raised panel standing in the field. A wall's own relief, not a fitting."""
    m.box((w - 0.10, h - 0.10, 0.008), (0, 0, 0.004), "h_dark")
    ring(m, w / 2, h / 2, [(0.0, -0.004), (0.012, 0.032), (0.05, 0.032), (0.062, -0.004)], G, c=0.04)
    m.box((w - 0.26, h - 0.24, 0.02), (0, 0, 0.016), G, bevel=0.008)


def mill8(m, paint="h_p1"):
    """REJECTED (2026-10-08): built in parts of its own, so it did not look of a kind with former5 ("왤케
    일관성이 없노"). Its layout lives on in mill9, which is made of former5's parts.
    Steel mill, 3x3 (hitbox 3x3x3), a through machine: one belt runs along the near row, carrying
    iron and coal together, and the steel leaves on it. The developer set the real Islands steel mill
    beside mill7 and found the difference plain; the cause under two failed layouts was the belts (two
    inlets on one side would not take that machine's build), so he changed the machine to one belt
    through, as the former has, and this follows the Islands mill mass for mass with its proportions
    read off the picture, in our own parts.
    The near block is as big in section as a tunnel mouth, the belt running through it end to end; at
    each end two painted bands with a dark seam wrap right round it. On its long face, to one side:
    a louvre over a panel of squares, and two big five-sided handwheels, one higher than the other;
    heavy bolts at the corners; the rest plain. On its roof two fat ribbed ducts rise into box elbows
    and run back into the furnace, and a short fat ribbed stack stands at the far end.
    The furnace behind is the bigger block, in two courses, its walls let in in steps, heavy bolts at
    their corners. Pairs of slim posts stand at its corners; a flat painted frame wraps it at the
    joint of the courses, and a wider one, flat and broad, lies over its top like a table, crossed by
    two beams that leave a window over the fat six-sided stack in the middle of the roof. Either side
    of the stack, under the open bays, the roof is slotted: red neon behind pale bars."""
    g = 2 * (BH - 0.305)
    yb = -1.0
    # ---- the near block, the belt through it
    X, hy = 1.19, 0.44
    with m.at((0, yb, 0)):
        belt_stub(m, -1.5, -X + 0.02, -1.41, -1.41)
        belt_stub(m, X - 0.02, 1.5, 1.41, 1.41)
        slab(m, X - 0.01, hy + 0.015, 0.0, 0.16, 0.03, T, bevel=0.012)
        slab(m, X, hy, 0.12, 0.90, 0.035, G, bevel=0.02)
        slab(m, X - 0.262, hy + 0.015, 0.88, 0.98, 0.04, "h_dark", bevel=0.016)                         # the lid, between the bands
        for d in SIDES:                                       # at each end: two painted bands round the block, a dark seam between
            px = d * (X + 0.01)
            for th, w, tp, mk in ((0.12, 0.95, 1.01, paint), (0.025, 0.90, 0.985, SLIT), (0.12, 0.95, 1.01, paint)):
                a_, b_ = sorted((px, px - d * th))
                m.prism(arch_pts(w, tp, hole_top=0.70, hw=BH + 0.01, c=0.085, ci=0.035), a_, b_, "X", mk)
                px -= d * th
            m.box((0.02, 2 * BH + 0.01, 0.694 - BZ), (d * (X - 0.004), 0, (0.706 + BZ) / 2), SLIT)
            xo = d * (X + 0.01)
            for sy_ in SIDES:                                 # each rail rises into the band's leg
                pts = [(xo - d * 0.006, 0.03), (xo + d * 0.11, 0.03), (xo + d * 0.11, 0.24), (xo + d * 0.085, 0.262), (xo - d * 0.006, 0.44)]
                bprism(m, pts if d > 0 else pts[::-1], *sorted((sy_ * 0.358, sy_ * 0.494)), "Y", R, bevel=0.008)
    yf = yb - hy                                              # the long face: to one side, a louvre over a panel of squares, two handwheels
    with on_side(m, -1, yf, 0.62, xc=0.0):
        vent(m, 0.25, 0.18)
    with on_side(m, -1, yf, 0.26, xc=0.0):
        grid(m, 0.25, 0.10, 4, 2)
    for x, z in ((0.46, 0.40), (0.74, 0.60)):
        with on_side(m, -1, yf, z, xc=x):
            handwheel(m, 0.15)
    for x in (-0.86, 0.87):
        for z in (0.20, 0.81):
            with on_side(m, -1, yf, z, xc=x):
                hexbolt(m)
    # ---- the furnace
    yc, fx, fy = 0.43, 1.12, 0.79
    Z1, Z2, Z3 = 0.98, 1.66, 1.72                             # the lower course's top, the upper course's top, the roof
    with m.at((0, yc, 0)):
        slab(m, 1.27, 0.94, 0.0, 0.14, 0.04, T, bevel=0.014)
        slab(m, fx, fy, 0.10, Z1 + 0.02, 0.035, G, bevel=0.02)
        slab(m, fx - 0.05, fy - 0.05, Z1 + 0.01, Z2, 0.035, G, bevel=0.02)
        slab(m, fx - 0.03, fy - 0.03, Z2 - 0.02, Z3, 0.04, "h_dark", bevel=0.016)
        RX, RY = fx + 0.075, fy + 0.075
        for sx in SIDES:                                      # pairs of slim posts at the corners
            for sy in SIDES:
                m.box((0.22, 0.12, 0.03), (sx * (RX - 0.04), sy * RY, 0.15), G, bevel=0.008)
                for dx in (0.0, -0.08):
                    m.box((0.05, 0.05, 2.22 - 0.16), (sx * (RX + dx), sy * RY, (2.22 + 0.16) / 2), LT, bevel=0.008)
        frame_ring(m, fx + 0.145, fy + 0.145, Z1 + 0.0, Z1 + 0.08, 0.14, paint)                          # the flat frame at the joint of the courses
        frame_ring(m, fx + 0.14, fy + 0.14, Z1 - 0.022, Z1 + 0.004, 0.125, TD)
        tz = (2.20, 2.28)                                     # the broad flat frame over the top
        frame_ring(m, fx + 0.28, fy + 0.25, tz[0], tz[1], 0.26, paint)
        frame_ring(m, fx + 0.27, fy + 0.24, tz[0] - 0.022, tz[0] + 0.004, 0.24, TD)
        for sx in SIDES:                                      # two beams across it, leaving a window over the stack
            m.box((0.18, 2 * (fy + 0.25) - 0.26, tz[1] - tz[0] - 0.02), (sx * 0.50, 0, (tz[0] + tz[1]) / 2), paint, bevel=0.012)
        # the stack: a broad foot, ribs, a funnel with a real hollow
        m.cyl(0.46, 0.09, (0, 0, Z3 + 0.04), G, seg=6)
        for k in range(6):                                    # the picture's stack is tall and plainly ribbed, and stands well above the frame
            wide = k % 2 == 0
            m.cyl(0.34 if wide else 0.26, 0.124, (0, 0, Z3 + 0.085 + 0.06 + k * 0.12), LT if wide else G, seg=6)
        zf = Z3 + 0.085 + 6 * 0.12
        m.cyl(0.30, 0.18, (0, 0, zf + 0.085), G, seg=6, r2=0.40)
        m.cyl(0.42, 0.05, (0, 0, zf + 0.19), LT, seg=6)
        m.cyl(0.33, 0.02, (0, 0, zf + 0.212), SLIT, seg=6)
        for sx in SIDES:                                      # the roof's slots, under the open bays: red neon behind pale bars
            with m.at((sx * 0.80, 0, Z3)):
                m.box((0.26, 0.46, 0.014), (0, 0, 0.004), "h_neon")
                for k in range(4):
                    y = -0.165 + k * 0.11
                    m.prism([(y - 0.02, 0.009), (y + 0.02, 0.009), (y + 0.012, 0.032), (y - 0.012, 0.032)], -0.14, 0.14, "X", LT)
                ring(m, 0.17, 0.27, [(0.0, -0.004), (0.012, 0.036), (0.034, 0.036), (0.046, -0.004)], G, c=0.03)
    zl, zu = (0.12 + Z1) / 2, (Z1 + 0.08 + Z2 - 0.02) / 2    # the middle heights of the two courses' walls
    for sx in SIDES:                                          # the end walls: let in in steps, bolts at the corners
        with on_end(m, sx, sx * fx, yc, zl):
            sunk(m, 1.16, 0.56)
        for y in (yc - 0.69, yc + 0.69):
            for z in (0.24, Z1 - 0.10):
                with on_end(m, sx, sx * fx, y, z):
                    hexbolt(m)
        with on_end(m, sx, sx * (fx - 0.05), yc, zu):
            sunk(m, 1.10, 0.36)
    with on_side(m, 1, yc + fy, zl, xc=0.0):                  # the back wall
        sunk(m, 1.80, 0.56)
    for x in (-1.02, 1.02):
        for z in (0.24, Z1 - 0.10):
            with on_side(m, 1, yc + fy, z, xc=x):
                hexbolt(m)
    with on_side(m, 1, yc + fy - 0.05, zu, xc=0.0):
        sunk(m, 1.70, 0.36)
    # ---- on the near block's roof: two fat ribbed ducts into the furnace, and a short fat stack
    Zr, rd, zq = 0.98, 0.13, 1.30
    ys = yc - fy + 0.05                                       # the furnace's upper wall, facing the near block
    for x in (-0.40, 0.20):
        with m.at((x, yb + 0.02, 0)):
            octa(m, rd + 0.04, rd + 0.01, Zr - 0.01, Zr + 0.06, G)
            octa(m, rd, rd, Zr + 0.05, zq - 0.16, LT)
            slab(m, 0.17, 0.17, zq - 0.17, zq + 0.17, 0.035, G, bevel=0.022)
        y0, y1 = yb + 0.02 + 0.17, ys + 0.03
        n = 5
        step = (y1 - y0) / n
        for k in range(n):
            wide = k % 2 == 1
            m.cyl((rd if wide else rd * 0.74) * K, step + 0.004, (x, y0 + (k + 0.5) * step, zq), LT if wide else G, seg=8, axis="Y", rot=(0, rad(22.5), 0))
    with m.at((0.82, yb, 0)):
        octa(m, 0.16, 0.13, Zr - 0.01, Zr + 0.07, G)
        for k in range(5):
            wide = k % 2 == 0
            octa(m, 0.125 if wide else 0.095, 0.125 if wide else 0.095, Zr + 0.06 + k * 0.12, Zr + 0.06 + (k + 1) * 0.12 + 0.004, LT if wide else G)
        octa(m, 0.10, 0.14, Zr + 0.66, Zr + 0.74, G)
        oct_ring(m, 0.145, 0.04, Zr + 0.735, Zr + 0.775, LT)
        octa(m, 0.105, 0.105, Zr + 0.72, Zr + 0.757, SLIT)


mill8.frame, mill8.shadow, mill8.res = {"iso": (5.4, 1.3), "side": (5.0, 1.4), "top": (4.4, 0.6), "end": (4.4, 1.4)}, True, 1800
_hero.HEROES["mill8"] = mill8


def mill9(m, paint="h_p1"):
    """REJECTED (2026-10-08): "존나 밋밋함. 그냥 사각형 위에 꾸며두는 느낌". A box with fittings on it.
    Steel mill, 3x3 (hitbox 3x3x3), a through machine: mill8's layout built out of former5's parts.
    mill8 followed the Islands mill mass for mass but in parts of its own (broad flat frames, pairs of
    posts, a six-sided ribbed stack, ribbed ducts, stepped walls, washers under the bolts), and the
    developer asked why it was so inconsistent with the former. So everything here is the former's:
    the grey cabinet with a painted body on it, the square-section painted frames on their dark plates
    round bundles of three rods, the eight-sided fat stack, the plain fat duct with collars and box
    elbows, the framed doors and panels, the louvre in its dark frame, the small pale bolts, the badge,
    the dial panel, and the same corner cuts.
    The near block carries the belt end to end, a painted portal with a dark seam at each mouth: a
    cabinet with a door, the louvre and two big handwheels on its long face, a painted body with a row
    of framed panels and a badge. Behind it the furnace: a cabinet in two courses under a dark cap,
    the two frames round it (at the joint of the courses and above the cap, the upper crossed by two
    beams that leave a window over the stack), red neon grates in the cap under the open bays. Two fat
    ducts rise from the near block's roof through box elbows and run back into the furnace's upper
    course; a short fat stack stands beside them."""
    g = 2 * (BH - 0.305)
    yb = -1.0

    def portal(xa, d):                                        # two painted arches with a dark seam between; each rail rises into its leg
        px = xa
        for th, w, tp, mk in ((0.08, 0.84 + g, 0.82, paint), (0.022, 0.79 + g, 0.795, SLIT), (0.08, 0.84 + g, 0.82, paint)):
            a_, b_ = sorted((px, px + d * th))
            m.prism(arch_pts(w, tp, hole_top=0.70, hw=BH + 0.01, c=0.085, ci=0.035), a_, b_, "X", mk)
            px += d * th
        m.box((0.02, 2 * BH + 0.01, 0.694 - BZ), (xa + d * 0.012, 0, (0.706 + BZ) / 2), SLIT)
        xo = xa + d * 0.182
        for sy_ in SIDES:
            pts = [(xo - d * 0.006, 0.03), (xo + d * 0.13, 0.03), (xo + d * 0.13, 0.24), (xo + d * 0.10, 0.262), (xo - d * 0.006, 0.44)]
            bprism(m, pts if d > 0 else pts[::-1], *sorted((sy_ * 0.358, sy_ * 0.494)), "Y", R, bevel=0.008)

    # ---- the near block, the belt through it
    X, hy = 1.05, 0.44
    Zc, Zr = 0.86, 1.12                                       # the cabinet's top, the body's roof
    body = (X - 0.08, hy - 0.08, 0.045)
    with m.at((0, yb, 0)):
        belt_stub(m, -1.5, -X + 0.02, -1.41, -1.44)
        belt_stub(m, X - 0.02, 1.5, 1.41, 1.44)
        portal(-X, -1)
        portal(X, 1)
        slab(m, X - 0.01, hy + 0.015, 0.0, 0.16, 0.03, T, bevel=0.012)
        slab(m, X, hy, 0.12, Zc, 0.035, G, bevel=0.02)
        slab(m, body[0], body[1], Zc - 0.01, Zr, body[2], paint, bevel=0.022)
    yf, yp = yb - hy, yb - body[1]
    zc_, zb_ = (0.12 + Zc) / 2, (Zc + Zr) / 2
    with on_side(m, -1, yf, zc_, xc=-0.36):                   # the cabinet's long face, made simpler: the louvre, two handwheels, corner bolts
        vent(m, 0.31, 0.21)
    for x, z in ((0.48, 0.40), (0.76, 0.58)):
        with on_side(m, -1, yf, z, xc=x):
            handwheel(m, 0.14)
    for x in (-X + 0.068, X - 0.068):
        for z in (0.21, Zc - 0.09):
            with on_side(m, -1, yf, z, xc=x):
                m.cyl(0.028, 0.02, (0, 0, 0.008), LT, seg=6)
    for x, w in ((-0.52, 0.52), (0.02, 0.32)):                # the body's long face, made simpler: two panels and a badge
        with on_side(m, -1, yp, zb_, xc=x):
            framed(m, w, 0.18)
    with on_side(m, -1, yp, zb_, xc=0.50):
        m.cyl(0.075, 0.022, (0, 0, 0.008), "h_red", seg=6)
        m.cyl(0.04, 0.012, (0, 0, 0.024), "h_white", seg=6)
    with on_end(m, -1, -body[0], yb, zb_):                    # the body's end: the dial panel
        gauges(m, 0.20, 0.10)
    # ---- the furnace
    yc, fx, fy = 0.43, 1.12, 0.79
    Z1, Z2, Z3 = 1.00, 1.76, 1.84                             # the lower course's top, the upper course's top, the cap
    fa, fb = (Z1 - 0.01, Z1 + 0.14), (2.30, 2.45)             # the two frames
    RX, RY = fx + 0.10, fy + 0.10
    with m.at((0, yc, 0)):
        slab(m, fx + 0.20, fy + 0.20, 0.0, 0.14, 0.04, T, bevel=0.014)
        slab(m, fx, fy, 0.10, Z1 + 0.01, 0.035, G, bevel=0.02)
        slab(m, fx - 0.03, fy - 0.03, Z1, Z2, 0.035, G, bevel=0.02)
        slab(m, fx, fy, Z2 - 0.02, Z3, 0.035, TD, bevel=0.014)
        for sx in SIDES:
            for sy in SIDES:
                m.box((0.15, 0.14, 0.03), (sx * (RX - 0.0375), sy * (RY - 0.034), 0.15), G, bevel=0.008)
                for dx, dy in ((0.0, 0.0), (-0.075, 0.0), (0.0, -0.068)):
                    m.box((0.044, 0.044, fb[0] + 0.02 - 0.16), (sx * (RX + dx), sy * (RY + dy), (fb[0] + 0.02 + 0.16) / 2), LT, bevel=0.008)
        for z0, z1 in (fa, fb):
            frame_ring(m, fx + 0.18, fy + 0.18, z0, z1, 0.17, paint)
            frame_ring(m, fx + 0.173, fy + 0.173, z0 - 0.03, z0 + 0.004, 0.15, TD)
        for sx in SIDES:                                      # two beams across the upper frame, leaving a window over the stack
            m.box((0.15, 2 * (fy + 0.18) - 0.30, fb[1] - fb[0] - 0.04), (sx * 0.42, 0, (fb[0] + fb[1]) / 2), paint, bevel=0.014)
        for sx in SIDES:                                      # in the cap, under the open bays: red neon behind bars
            with m.at((sx * 0.78, 0, Z3)):
                m.box((0.18, 0.42, 0.014), (0, 0, 0.004), "h_neon")
                for k in range(5):
                    y = -0.17 + k * 0.085
                    m.prism([(y - 0.015, 0.009), (y + 0.015, 0.009), (y + 0.008, 0.03), (y - 0.008, 0.03)], -0.10, 0.10, "X", LT)
                ring(m, 0.13, 0.25, [(0.0, -0.004), (0.01, 0.034), (0.034, 0.034), (0.046, -0.004)], TD, c=0.03)
    with m.at((0, yc, 0)):                                    # the stack's base, filling the middle of the cap
        slab(m, 0.36, 0.36, Z3 - 0.01, Z3 + 0.16, 0.06, G, bevel=0.02)
        slab(m, 0.372, 0.372, Z3 + 0.11, Z3 + 0.172, cut_to(0.372, 0.372, (0.36, 0.36, 0.06), 0.012), LT, bevel=0.012)
    fat_stack(m, 0, yc, Z3 + 0.16, 2.95, 0.21, foot=0.07)
    zl, zu = (0.10 + fa[0] - 0.03) / 2, (fa[1] + Z2 - 0.02) / 2   # the middle heights of the walls below and above the lower frame
    for sx in SIDES:                                          # the end walls: two doors below, a bolted plate above
        for y in (yc - 0.30, yc + 0.30):
            with on_end(m, sx, sx * fx, y, zl):
                framed(m, 0.34, 0.50, LT)
                m.box((0.022, 0.11, 0.022), (0.10, 0, 0.02), TD)
        for y in (yc - fy + 0.068, yc + fy - 0.068):
            for z in (0.21, fa[0] - 0.12):
                with on_end(m, sx, sx * fx, y, z):
                    m.cyl(0.028, 0.02, (0, 0, 0.008), LT, seg=6)
        for y in (yc - 0.48, yc, yc + 0.48):                  # upright ribs brace the upper course
            with on_end(m, sx, sx * (fx - 0.03), y, zu):
                m.box((0.075, Z2 - 0.02 - fa[1], 0.045), (0, 0, 0.02), LT, bevel=0.01)
    with on_side(m, 1, yc + fy, zl, xc=-0.45):                # the back wall: a louvre and two panels below, a bolted plate above
        vent(m, 0.31, 0.21)
    for x in (0.25, 0.70):
        with on_side(m, 1, yc + fy, zl, xc=x):
            framed(m, 0.34, 0.42)
    for x in (-fx + 0.068, fx - 0.068):
        for z in (0.21, fa[0] - 0.12):
            with on_side(m, 1, yc + fy, z, xc=x):
                m.cyl(0.028, 0.02, (0, 0, 0.008), LT, seg=6)
    for x in (-0.84, -0.28, 0.28, 0.84):
        with on_side(m, 1, yc + fy - 0.03, zu, xc=x):
            m.box((0.075, Z2 - 0.02 - fa[1], 0.045), (0, 0, 0.02), LT, bevel=0.01)
    for x in (-0.84, -0.10, 0.62):                            # and on the wall facing the near block, clear of the two ducts
        with on_side(m, -1, yc - fy + 0.03, zu, xc=x):
            m.box((0.075, Z2 - 0.02 - fa[1], 0.045), (0, 0, 0.02), LT, bevel=0.01)
    # ---- the ducts: out of the near block's roof, through box elbows, back into the furnace's upper course
    rd, zq = 0.105, 1.46
    ys = yc - fy + 0.03
    for x in (-0.40, 0.20):
        with m.at((x, yb, 0)):
            octa(m, rd + 0.05, rd + 0.02, Zr - 0.01, Zr + 0.08, G)
            octa(m, rd, rd, Zr + 0.07, zq - 0.13, LT)
            slab(m, 0.14, 0.14, zq - 0.14, zq + 0.14, 0.03, G, bevel=0.02)
        y0 = yb + 0.14
        m.cyl(rd * K, ys - y0 + 0.04, (x, (y0 + ys) / 2, zq), LT, seg=8, axis="Y", rot=(0, rad(22.5), 0))
        m.cyl((rd + 0.022) * K, 0.07, (x, (y0 + ys) / 2 - 0.05, zq), G, seg=8, axis="Y", rot=(0, rad(22.5), 0))
    fat_stack(m, 0.70, yb, Zr, 2.02, 0.10)


mill9.frame, mill9.shadow, mill9.res = {"iso": (5.4, 1.4), "side": (5.0, 1.5), "top": (4.4, 0.6), "end": (4.4, 1.5)}, True, 1800
_hero.HEROES["mill9"] = mill9


def mill10(m, paint="h_p1"):
    """REJECTED (2026-10-09): "많이 구림. 폐기".
    Steel mill, 3x3 (hitbox 3x3x3), a through machine, the belt along the middle row. mill9 was a box
    with fittings on it ("그냥 사각형 위에 꾸며두는 느낌"); what makes former5 work is that its form is a
    skeleton with a mass hung inside it, not a box. So here the form is changed, not the trim: this is
    a steel converter, built of former5's parts.
    Over the belt stands an open tower, three painted frames on four bundles of rods, as the former's
    is. In it hangs the vessel: eight-sided, a narrow bottom with its tap over the belt, a wide belly,
    a shoulder drawn in to an open mouth that glows red inside; a painted ring round its belly carries
    it on two fat trunnions that run into bearing blocks astride the middle frame. Under the top frame,
    hung from two cross beams, a hood stands over the mouth, and its stack rises through the frame.
    East of the tower the belt runs through the blower house, a cabinet under a painted body, a
    painted portal at each mouth. On its roof at the south end stands the blower's casing, its one
    louvre the air intake; from it the blast main runs west through the open air, past a valve with a
    big handwheel standing on a pier, round a box elbow and into the south bearing block: the blast
    goes into the vessel through its trunnion."""
    g = 2 * (BH - 0.305)
    xt = -0.42                                                # the tower's and the vessel's middle

    def portal(xa, d):
        px = xa
        for th, w, tp, mk in ((0.08, 0.84 + g, 0.82, paint), (0.022, 0.79 + g, 0.795, SLIT), (0.08, 0.84 + g, 0.82, paint)):
            a_, b_ = sorted((px, px + d * th))
            m.prism(arch_pts(w, tp, hole_top=0.70, hw=BH + 0.01, c=0.085, ci=0.035), a_, b_, "X", mk)
            px += d * th
        m.box((0.02, 2 * BH + 0.01, 0.694 - BZ), (xa + d * 0.012, 0, (0.706 + BZ) / 2), SLIT)
        xo = xa + d * 0.182
        for sy_ in SIDES:
            pts = [(xo - d * 0.006, 0.03), (xo + d * 0.13, 0.03), (xo + d * 0.13, 0.24), (xo + d * 0.10, 0.262), (xo - d * 0.006, 0.44)]
            bprism(m, pts if d > 0 else pts[::-1], *sorted((sy_ * 0.358, sy_ * 0.494)), "Y", R, bevel=0.008)

    # ---- the belt, open under the tower
    bed(m, -1.5, 1.5)
    m.box((3.0, BH * 2, 0.03), (0, 0, BZ - 0.015), "h_belt")
    for x in (-4 / 3, -1.0, -0.74, -0.02):
        chev(m, x)
    for x in (-4 / 3, -1.0):
        buttress(m, x)
    with m.at((xt, 0, 0)):
        seat(m, 0.30)                                         # the pouring bed under the vessel, the same seat the former stands on
        m.box((0.32, 0.26, 0.022), (0, 0, BZ + 0.017), LT, bevel=0.006)
    # ---- the tower: three frames on four bundles of rods, standing on a sill each side of the belt
    fz = ((0.86, 1.01), (1.37, 1.52), (2.46, 2.61))
    RX = 0.65
    for sy in SIDES:
        with m.at((xt, sy * RX, 0)):
            slab(m, 0.76, 0.115, 0.0, 0.16, 0.03, T, bevel=0.012)
    with m.at((xt, 0, 0)):
        for sx in SIDES:
            for sy in SIDES:
                m.box((0.15, 0.14, 0.03), (sx * (RX - 0.0375), sy * (RX - 0.034), 0.17), G, bevel=0.008)
                for dx, dy in ((0.0, 0.0), (-0.075, 0.0), (0.0, -0.068)):
                    m.box((0.044, 0.044, fz[2][0] + 0.02 - 0.18), (sx * (RX + dx), sy * (RX + dy), (fz[2][0] + 0.02 + 0.18) / 2), LT, bevel=0.008)
        for z0, z1 in fz:
            frame_ring(m, 0.72, 0.72, z0, z1, 0.17, paint)
            frame_ring(m, 0.713, 0.713, z0 - 0.03, z0 + 0.004, 0.15, TD)
        # the vessel
        zt = (fz[1][0] + fz[1][1]) / 2                        # the trunnions' height: the middle frame's
        # It hangs tipped a little on its trunnions, mouth toward the inlet side, as a converter stands when
        # it is blowing: the form is not upright and square, and the fire in its mouth can be seen.
        from mathutils import Matrix
        m.stack.append(m.stack[-1] @ Matrix.Translation((0, 0, zt)) @ Matrix.Rotation(rad(-16), 4, "Y") @ Matrix.Translation((0, 0, -zt)))
        octa(m, 0.07, 0.07, 0.82, 0.97, ST)                   # the tap
        octa(m, 0.26, 0.46, 0.95, 1.25, G)
        octa(m, 0.46, 0.46, 1.24, 1.66, G)
        octa(m, 0.50, 0.50, zt - 0.06, zt + 0.06, paint)      # the ring that carries it
        octa(m, 0.475, 0.475, 1.60, 1.65, TD)
        octa(m, 0.46, 0.30, 1.65, 1.96, G)
        oct_ring(m, 0.34, 0.07, 1.95, 2.04, TD)               # the mouth's lip, and the fire inside it
        octa(m, 0.275, 0.275, 1.955, 2.012, "h_neon")
        m.stack.pop()
        for sy in SIDES:
            m.cyl(0.09 * K, 0.15, (0, sy * 0.565, zt), LT, seg=8, axis="Y", rot=(0, rad(22.5), 0))
            with m.at((0, sy * 0.665, 0)):                    # a bearing block astride the frame's beam
                slab(m, 0.14, 0.125, zt - 0.145, zt + 0.145, 0.03, G, bevel=0.02)
                slab(m, 0.152, 0.137, zt + 0.125, zt + 0.185, cut_to(0.152, 0.137, (0.14, 0.125, 0.03), 0.012), TD, bevel=0.012)
        # the hood, hung from two beams under the top frame
        for y in (-0.26, 0.26):
            m.prism([(y - 0.055, 2.385), (y + 0.055, 2.385), (y + 0.04, 2.465), (y - 0.04, 2.465)], -0.62, 0.62, "X", G)
        octa(m, 0.42, 0.22, 2.22, 2.42, G)
        oct_ring(m, 0.45, 0.05, 2.20, 2.26, LT)
    fat_stack(m, xt, 0, 2.40, 2.98, 0.165, foot=0.03)
    # ---- the blower house, east of the tower, the belt through it
    hx0, hx1, hy0, hy1 = 0.36, 1.16, -1.26, 0.62
    xh, yh = (hx0 + hx1) / 2, (hy0 + hy1) / 2
    hxh, hyh = (hx1 - hx0) / 2, (hy1 - hy0) / 2
    Zc, Zr = 0.86, 1.12
    body = (hxh - 0.08, hyh - 0.08, 0.045)
    portal(hx0, -1)
    portal(hx1, 1)
    with m.at((xh, yh, 0)):
        slab(m, hxh - 0.01, hyh - 0.01, 0.0, 0.16, 0.03, T, bevel=0.012)
        slab(m, hxh, hyh, 0.12, Zc, 0.035, G, bevel=0.02)
        slab(m, body[0], body[1], Zc - 0.01, Zr, body[2], paint, bevel=0.022)
    zc_, zb_ = (0.12 + Zc) / 2, (Zc + Zr) / 2
    with on_side(m, -1, hy0, zc_, xc=xh):                     # the door, in the south end, where one walks in
        framed(m, 0.34, 0.46, LT)
        m.box((0.022, 0.11, 0.022), (0.10, 0, 0.02), TD)
    for x in (hx0 + 0.068, hx1 - 0.068):
        for z in (0.21, Zc - 0.09):
            with on_side(m, -1, hy0, z, xc=x):
                m.cyl(0.028, 0.02, (0, 0, 0.008), LT, seg=6)
    with on_side(m, -1, yh - body[1], zb_, xc=xh):            # the dial panel, over the door
        gauges(m, 0.22, 0.10)
    with on_end(m, -1, xh - body[0], -0.78, zb_):             # the badge
        m.cyl(0.075, 0.022, (0, 0, 0.008), "h_red", seg=6)
        m.cyl(0.04, 0.012, (0, 0, 0.024), "h_white", seg=6)
    # the blower's casing on the roof, its louvre the air intake
    xb, yb_, case = xh, -0.98, (0.26, 0.18, 0.035)
    Zk = 1.70
    with m.at((xb, yb_, 0)):
        slab(m, case[0], case[1], Zr - 0.01, Zk, case[2], G, bevel=0.02)
        slab(m, case[0] + 0.015, case[1] + 0.015, Zk - 0.02, Zk + 0.04, cut_to(case[0] + 0.015, case[1] + 0.015, case, 0.015), TD, bevel=0.014)
    with on_side(m, -1, yb_ - case[1], (Zr + Zk) / 2 - 0.01, xc=xb):
        vent(m, 0.20, 0.19)
    fat_stack(m, xh, 0.25, Zr, 1.95, 0.10)                    # a short fat stack on the roof's north end
    # ---- the blast main: out of the casing, through the open air past a valve on a pier, round an elbow, into the south bearing
    rd, zq = 0.105, zt
    x0, x1 = xb - case[0], xt + 0.14
    m.cyl(rd * K, x0 - x1 + 0.03, ((x0 + x1) / 2, yb_, zq), LT, seg=8, axis="X", rot=(rad(22.5), 0, 0))
    xv = 0.11
    with m.at((xv, yb_, 0)):
        slab(m, 0.13, 0.13, zq - 0.14, zq + 0.14, 0.03, G, bevel=0.02)
        slab(m, 0.10, 0.13, 0.0, 0.07, 0.03, T, bevel=0.012)                                             # the pier under it
        slab(m, 0.05, 0.075, 0.05, zq - 0.13, 0.015, ST, bevel=0.01)
    with on_side(m, -1, yb_ - 0.13, zq, xc=xv):
        handwheel(m, 0.14)
    for x in ((x0 + xv + 0.13) / 2, (xv - 0.13 + x1) / 2):
        m.cyl((rd + 0.022) * K, 0.06, (x, yb_, zq), G, seg=8, axis="X", rot=(rad(22.5), 0, 0))
    with m.at((xt, yb_, 0)):
        slab(m, 0.14, 0.14, zq - 0.14, zq + 0.14, 0.03, G, bevel=0.02)
    ya, yq = yb_ + 0.14, -0.79
    m.cyl(rd * K, yq - ya + 0.05, (xt, (ya + yq) / 2, zq), LT, seg=8, axis="Y", rot=(0, rad(22.5), 0))


mill10.frame, mill10.shadow, mill10.res = {"iso": (5.6, 1.45), "side": (5.0, 1.5), "top": (4.4, 0.6), "end": (4.4, 1.5)}, True, 1800
_hero.HEROES["mill10"] = mill10


def mouth3(m, xa, d, paint, depth=0.182, ears=True, wide=False):
    """The grade 3 mouth, to be built with the belt's middle at y = 0, on the wall at xa, opening toward
    d. The developer's rule: every conveyor mouth of one grade looks the same (the low grades share the
    ribbed folding cover, d.cover; grade 2 and grade 3 each have their own), so every grade 3 machine
    calls this. Returns how far out the mouth's face stands.
    At its plainest (depth 0.182): two painted arches with a dark seam between them, the tunnel's dark,
    and each rail rising in its own colour into the arch's leg (`ears`).
    The developer then asked for every mouth to be deep, so that things go into it and not through a
    wall, and longer still; and for the odd bits beside it to go. So with a greater depth the two
    painted arches stand that far out, on a grey sleeve over a dark-lined throat, a third painted band
    against the wall; with wide=True the arches are as wide as the belt's rails, which then run
    straight into their legs, and with ears=False nothing stands on the rails beside the mouth."""
    g = 2 * (BH - 0.305)
    wp, ws, wk = (0.988, 0.95, 0.955) if wide else (0.84 + g, 0.79 + g, 0.80 + g)   # the painted arches, the seams, the sleeve
    back = 0.102 if depth > 0.40 else 0.0                     # a painted band and a seam against the wall, when the mouth is long
    sleeve = max(0.0, depth - 0.182 - back)
    px = xa
    if back:
        for th, w, tp, mk in ((0.08, wp, 0.82, paint), (0.022, ws, 0.795, SLIT)):
            a_, b_ = sorted((px, px + d * th))
            m.prism(arch_pts(w, tp, hole_top=0.70, hw=BH + 0.01, c=0.085, ci=0.035), a_, b_, "X", mk)
            px += d * th
    if sleeve:
        a_, b_ = sorted((px, px + d * sleeve))
        m.prism(arch_pts(wk, 0.80, hole_top=0.702, hw=BH + 0.012, c=0.085, ci=0.035), a_, b_, "X", G)
        a_, b_ = sorted((xa + d * 0.02, xa + d * (depth - 0.03)))                                         # the throat's dark lining
        m.prism(arch_pts(2 * (BH + 0.03), 0.72, hole_top=0.694, hw=BH + 0.004, c=0.05, ci=0.035), a_, b_, "X", TD)
        px += d * sleeve
    for th, w, tp, mk in ((0.08, wp, 0.82, paint), (0.022, ws, 0.795, SLIT), (0.08, wp, 0.82, paint)):
        a_, b_ = sorted((px, px + d * th))
        m.prism(arch_pts(w, tp, hole_top=0.70, hw=BH + 0.01, c=0.085, ci=0.035), a_, b_, "X", mk)
        px += d * th
    m.box((0.02, 2 * BH + 0.01, 0.694 - BZ), (xa + d * 0.012, 0, (0.706 + BZ) / 2), SLIT)
    if ears:
        xo = xa + d * depth
        for sy_ in SIDES:
            pts = [(xo - d * 0.006, 0.03), (xo + d * 0.13, 0.03), (xo + d * 0.13, 0.24), (xo + d * 0.10, 0.262), (xo - d * 0.006, 0.44)]
            bprism(m, pts if d > 0 else pts[::-1], *sorted((sy_ * 0.358, sy_ * 0.494)), "Y", R, bevel=0.008)
    return depth


def mill11(m, paint="h_p1"):
    """REJECTED (2026-10-09): "기차인 줄. 뇌절이 너무 심했다". Three systems of pipe on one body is too much.
    Steel mill, 3x3 (hitbox 3x3x3), a through machine, the belt along the middle row. The developer
    dropped the converter (mill10) and with it the idea of acting out the process: iron and coal go
    into a machine and steel comes out, and what happens inside is not shown. His words for this one:
    in the former's manner, but closed where the former's press is open; a big rectangular body, very
    complicated to look at, with pipes, louvres and round pipework all on it.
    So the body is the former's house grown large (a grey cabinet under a painted body), the belt
    through it from mouth to mouth (mouth3), and the complication is three systems of pipe standing
    off it rather than plates laid on it:
    - at the south-west corner a banded drum on the ground; from it a fat main runs along the south
      side on piers, past a valve with a big handwheel, to two tees; from each tee a riser climbs the
      wall (the first through a second valve), turns over the eave in a box elbow and runs into the
      side of a plenum on the roof, out of which three fat stacks rise, each taller than the last;
    - on the roof's west end a round separator, banded, coned, with a small stack of its own, and a
      short pipe from it into the plenum's end;
    - along the roof's north edge a return duct on saddles between two box elbows that turn down into
      the roof.
    Behind the pipes the walls carry little: a louvre and a door a side, a row of panels and a badge,
    one dial panel."""
    belt_stub(m, -1.5, -1.03, -1.39, -1.455)
    belt_stub(m, 1.03, 1.5, 1.39, 1.455)
    X, hy = 1.05, 0.72
    Zc, Zr = 0.84, 1.30                                       # the cabinet's top, the roof
    body = (X - 0.08, hy - 0.08, 0.045)
    mouth3(m, -X, -1, paint)
    mouth3(m, X, 1, paint)
    slab(m, X - 0.01, hy + 0.015, 0.0, 0.16, 0.03, T, bevel=0.012)
    slab(m, X, hy, 0.12, Zc, 0.035, G, bevel=0.02)
    slab(m, body[0], body[1], Zc - 0.01, Zr, body[2], paint, bevel=0.022)
    zc_, zb_ = (0.12 + Zc) / 2, (Zc + Zr) / 2
    # ---- the walls, kept quiet behind the pipes
    with on_side(m, -1, -hy, zc_, xc=-0.30):                  # south: a louvre and a door below; panels and a badge above
        vent(m, 0.31, 0.21)
    with on_side(m, -1, -hy, zc_, xc=0.82):
        framed(m, 0.34, 0.46, LT)
        m.box((0.022, 0.11, 0.022), (-0.10, 0, 0.02), TD)
    for x, w in ((-0.72, 0.36), (-0.38, 0.22)):
        with on_side(m, -1, -body[1], zb_, xc=x):
            framed(m, w, 0.30)
    with on_side(m, -1, -body[1], zb_, xc=0.86):
        m.cyl(0.09, 0.022, (0, 0, 0.008), "h_red", seg=6)
        m.cyl(0.048, 0.012, (0, 0, 0.024), "h_white", seg=6)
    with on_side(m, 1, hy, zc_, xc=0.45):                     # north: a louvre and a door below; the dial panel between two panels above
        vent(m, 0.31, 0.21)
    with on_side(m, 1, hy, zc_, xc=-0.50):
        framed(m, 0.34, 0.46, LT)
        m.box((0.022, 0.11, 0.022), (0.10, 0, 0.02), TD)
    with on_side(m, 1, body[1], zb_, xc=0.0):
        gauges(m, 0.24, 0.11, turns=(0.75, -1.15, 0.2))
    for x in (-0.62, 0.62):
        with on_side(m, 1, body[1], zb_, xc=x):
            framed(m, 0.36, 0.30)
    for d in SIDES:
        for x in (-X + 0.068, X - 0.068):
            for z in (0.21, Zc - 0.09):
                with on_side(m, d, d * hy, z, xc=x):
                    m.cyl(0.028, 0.02, (0, 0, 0.008), LT, seg=6)
    for sx in SIDES:                                          # the body's ends, above the mouths: a bolted plate
        with on_end(m, sx, sx * body[0], 0, zb_):
            bolted(m, 0.70, 0.26, G, r=0.02)
    # ---- on the roof: the plenum and its three stacks
    rd = 0.105
    xa0, xa1, ya, pa = -0.05, 0.85, -0.20, 0.22               # the plenum: its ends, its middle line, its half width
    pz = Zr + 0.36
    with m.at(((xa0 + xa1) / 2, ya, 0)):
        slab(m, (xa1 - xa0) / 2, pa, Zr - 0.01, pz, 0.04, G, bevel=0.02)
        slab(m, (xa1 - xa0) / 2 + 0.012, pa + 0.012, pz - 0.05, pz + 0.012, cut_to((xa1 - xa0) / 2 + 0.012, pa + 0.012, ((xa1 - xa0) / 2, pa, 0.04), 0.012), LT, bevel=0.012)
    for x, top in ((0.115, 2.15), (0.40, 2.50), (0.685, 2.85)):
        fat_stack(m, x, ya, pz, top, 0.10, foot=0.035)
    # ---- system one: drum, main, valve, tees, risers, elbows, into the plenum's side
    ym, zm, zq = -1.0, 0.42, Zr + 0.18                        # the main's line and height; the height the risers turn over at
    xd = -0.85                                                # the drum
    with m.at((xd, ym, 0)):
        octa(m, 0.23, 0.21, 0.0, 0.08, T)
        octa(m, 0.20, 0.20, 0.07, 1.05, G)
        for z in (0.26, 0.82):
            octa(m, 0.213, 0.213, z, z + 0.06, TD)
        octa(m, 0.20, 0.10, 1.04, 1.18, G)
        octa(m, 0.055, 0.055, 1.17, 1.27, ST)
        octa(m, 0.075, 0.075, 1.26, 1.30, TD)
    xt1, xt2, xv = 0.15, 0.60, -0.32                          # the two tees, the valve
    for x0, x1 in ((xd + 0.20, xt1 - 0.14), (xt1 + 0.14, xt2 - 0.14)):
        m.cyl(rd * K, x1 - x0 + 0.03, ((x0 + x1) / 2, ym, zm), LT, seg=8, axis="X", rot=(rad(22.5), 0, 0))
    for x in ((xd + 0.20 + xv - 0.13) / 2, (xv + 0.13 + xt1 - 0.14) / 2, (xt1 + xt2) / 2):
        m.cyl((rd + 0.022) * K, 0.06, (x, ym, zm), G, seg=8, axis="X", rot=(rad(22.5), 0, 0))
    for x in (xv, xt1, xt2):                                  # the valve and the tees are boxes on piers
        with m.at((x, ym, 0)):
            slab(m, 0.14 if x != xv else 0.13, 0.14 if x != xv else 0.13, zm - 0.14, zm + 0.14, 0.03, G, bevel=0.02)
            slab(m, 0.10, 0.13, 0.0, 0.07, 0.03, T, bevel=0.012)
            slab(m, 0.05, 0.075, 0.05, zm - 0.13, 0.015, ST, bevel=0.01)
    with on_side(m, -1, ym - 0.13, zm, xc=xv):
        handwheel(m, 0.14)
    zv = 0.95                                                 # the valve in the first riser
    for x in (xt1, xt2):
        with m.at((x, ym, 0)):
            octa(m, rd, rd, zm + 0.13, zq - 0.13, LT)
            slab(m, 0.14, 0.14, zq - 0.14, zq + 0.14, 0.03, G, bevel=0.02)
            if x == xt1:
                slab(m, 0.13, 0.13, zv - 0.13, zv + 0.13, 0.03, G, bevel=0.02)
            else:
                octa(m, rd + 0.022, rd + 0.022, zv - 0.03, zv + 0.03, G)
        y0, y1 = ym + 0.14, ya - pa
        m.cyl(rd * K, y1 - y0 + 0.04, (x, (y0 + y1) / 2, zq), LT, seg=8, axis="Y", rot=(0, rad(22.5), 0))
        m.cyl((rd + 0.022) * K, 0.06, (x, (y0 + y1) / 2 - 0.03, zq), G, seg=8, axis="Y", rot=(0, rad(22.5), 0))
    with on_side(m, -1, ym - 0.13, zv, xc=xt1):
        handwheel(m, 0.14)
    # ---- system two: the separator on the roof's west end, and its pipe into the plenum's end
    xs_, ys_ = -0.55, -0.12
    with m.at((xs_, ys_, 0)):
        octa(m, 0.29, 0.27, Zr - 0.01, Zr + 0.07, G)
        octa(m, 0.26, 0.26, Zr + 0.06, Zr + 0.62, LT)
        for z in (Zr + 0.16, Zr + 0.46):
            octa(m, 0.273, 0.273, z, z + 0.06, G)
        octa(m, 0.26, 0.11, Zr + 0.61, Zr + 0.83, G)
    fat_stack(m, xs_, ys_, Zr + 0.82, 2.52, 0.085, foot=0.03)
    x0, x1 = xs_ + 0.26, xa0
    m.cyl(0.08 * K, x1 - x0 + 0.04, ((x0 + x1) / 2, -0.14, zq), LT, seg=8, axis="X", rot=(rad(22.5), 0, 0))
    m.cyl(0.10 * K, 0.05, ((x0 + x1) / 2, -0.14, zq), G, seg=8, axis="X", rot=(rad(22.5), 0, 0))
    # ---- system three: the return duct along the roof's north edge
    yr, zr2 = 0.42, Zr + 0.19
    for sx in SIDES:
        with m.at((sx * 0.75, yr, 0)):
            octa(m, rd + 0.05, rd + 0.02, Zr - 0.01, Zr + 0.06, G)
            slab(m, 0.14, 0.14, Zr + 0.05, Zr + 0.33, 0.03, G, bevel=0.02)
        with m.at((sx * 0.30, yr, 0)):
            slab(m, 0.06, 0.13, Zr - 0.01, Zr + 0.10, 0.02, G, bevel=0.012)                              # a saddle
        m.cyl((rd + 0.022) * K, 0.06, (sx * 0.30, yr, zr2), G, seg=8, axis="X", rot=(rad(22.5), 0, 0))
    m.cyl(rd * K, 1.22 + 0.03, (0, yr, zr2), LT, seg=8, axis="X", rot=(rad(22.5), 0, 0))


mill11.frame, mill11.shadow, mill11.res = {"iso": (5.6, 1.4), "side": (5.0, 1.5), "top": (4.4, 0.6), "end": (4.4, 1.5)}, True, 1800
_hero.HEROES["mill11"] = mill11


def mill12(m, paint="h_p1"):
    """Steel mill, 3x3 (hitbox 3x3x3), a through machine, the belt along the near row. After the bland one
    (mill9) and the overdone one (mill11) the developer named the mark: lopsided as the Islands mill
    is, neither bland nor overdone; and he corrected my reading of that machine from a picture taken
    in the game: its stack does not stand in the middle of the furnace but in one corner, and the top
    frame's inner beams make a window over that corner only.
    So, in former5's parts and no more of them than the Islands mill carries:
    - two masses of plainly different size: the low long block the belt runs through (a mouth3 at each
      end), and behind it the furnace, taller, in two courses under a dark cap;
    - two frames round the furnace on bundles of rods, one at the joint of its courses, one above the
      cap, the upper one broader and standing out past the rods;
    - the fat stack in the furnace's back corner on a broad base, under a window made by one beam along
      the frame and one across; red neon grates in the cap under the other bays;
    - two fat ducts from the low block's roof over into the furnace, and a short fat stack beside them;
    - the small things gathered on one part of the low block's face (a louvre and two handwheels, one
      higher than the other), the rest of it bare."""
    yb = -1.0
    X, hy = 1.05, 0.44
    Zc, Zl = 0.88, 0.96                                       # the low block's wall top, its lid
    with m.at((0, yb, 0)):
        belt_stub(m, -1.5, -X + 0.02, -1.39, -1.455)
        belt_stub(m, X - 0.02, 1.5, 1.39, 1.455)
        mouth3(m, -X, -1, paint)
        mouth3(m, X, 1, paint)
        slab(m, X - 0.01, hy + 0.015, 0.0, 0.16, 0.03, T, bevel=0.012)
        slab(m, X, hy, 0.12, Zc, 0.035, G, bevel=0.02)
        slab(m, X + 0.015, hy + 0.015, Zc - 0.02, Zl, 0.045, TD, bevel=0.014)
    yf = yb - hy
    with on_side(m, -1, yf, 0.50, xc=0.05):                   # the low block's face: everything small is here, to one side
        vent(m, 0.25, 0.19)
    for x, z in ((0.52, 0.40), (0.78, 0.60)):
        with on_side(m, -1, yf, z, xc=x):
            handwheel(m, 0.14)
    for x in (-X + 0.068, X - 0.068):
        for z in (0.21, Zc - 0.11):
            with on_side(m, -1, yf, z, xc=x):
                m.cyl(0.028, 0.02, (0, 0, 0.008), LT, seg=6)
    # ---- the furnace
    yc, fx, fy = 0.43, 1.00, 0.79
    Z1, Z2, Z3 = 1.00, 1.70, 1.78
    fa, fb = (Z1 - 0.01, Z1 + 0.14), (2.26, 2.41)
    RX, RY = fx + 0.10, fy + 0.10
    xs_, ys_ = -0.50, 0.36                                    # the stack, in the back corner (measured from the furnace's middle)
    with m.at((0, yc, 0)):
        slab(m, fx + 0.20, fy + 0.20, 0.0, 0.14, 0.04, T, bevel=0.014)
        slab(m, fx, fy, 0.10, Z1 + 0.01, 0.035, G, bevel=0.02)
        slab(m, fx - 0.03, fy - 0.03, Z1, Z2, 0.035, G, bevel=0.02)
        slab(m, fx, fy, Z2 - 0.02, Z3, 0.035, TD, bevel=0.014)
        for sx in SIDES:
            for sy in SIDES:
                m.box((0.15, 0.14, 0.03), (sx * (RX - 0.0375), sy * (RY - 0.034), 0.15), G, bevel=0.008)
                for dx, dy in ((0.0, 0.0), (-0.075, 0.0), (0.0, -0.068)):
                    m.box((0.044, 0.044, fb[0] + 0.02 - 0.16), (sx * (RX + dx), sy * (RY + dy), (fb[0] + 0.02 + 0.16) / 2), LT, bevel=0.008)
        frame_ring(m, fx + 0.18, fy + 0.18, fa[0], fa[1], 0.17, paint)
        frame_ring(m, fx + 0.173, fy + 0.173, fa[0] - 0.03, fa[0] + 0.004, 0.15, TD)
        frame_ring(m, fx + 0.26, fy + 0.26, fb[0], fb[1], 0.26, paint)                                   # the upper frame, broader, standing out past the rods
        frame_ring(m, fx + 0.253, fy + 0.253, fb[0] - 0.03, fb[0] + 0.004, 0.24, TD)
        bz, bh = (fb[0] + fb[1]) / 2, fb[1] - fb[0] - 0.04
        yx = ys_ - 0.41                                       # one beam along the frame, in front of the stack
        m.box((2 * fx + 0.04, 0.15, bh), (0, yx, bz), paint, bevel=0.014)
        xy = xs_ + 0.42                                       # and one across, from that beam to the back: the window over the stack
        m.box((0.15, fy - yx - 0.075 + 0.04, bh), (xy, (yx + 0.075 + fy + 0.02) / 2 - 0.01, bz), paint, bevel=0.014)
        with m.at((xs_, ys_, 0)):                             # the stack's base
            slab(m, 0.30, 0.30, Z3 - 0.01, Z3 + 0.14, 0.05, G, bevel=0.02)
            slab(m, 0.312, 0.312, Z3 + 0.09, Z3 + 0.152, cut_to(0.312, 0.312, (0.30, 0.30, 0.05), 0.012), LT, bevel=0.012)
        for gx, gy, w, h in ((0.30, 0.41, 0.22, 0.44), (0.70, 0.41, 0.22, 0.44), (-0.40, -0.44, 0.44, 0.20)):   # red neon behind bars, under the other bays
            with m.at((gx, gy, Z3)):
                m.box((w - 0.08, h - 0.08, 0.014), (0, 0, 0.004), "h_neon")
                n = max(3, round(max(w, h) / 0.085) - 1)
                for k_ in range(n):
                    t_ = -(n - 1) * 0.0425 + k_ * 0.085
                    if h > w:
                        m.prism([(t_ - 0.015, 0.009), (t_ + 0.015, 0.009), (t_ + 0.008, 0.03), (t_ - 0.008, 0.03)], -(w / 2 - 0.03), w / 2 - 0.03, "X", LT)
                    else:
                        m.prism([(t_ - 0.015, 0.009), (t_ + 0.015, 0.009), (t_ + 0.008, 0.03), (t_ - 0.008, 0.03)], -(h / 2 - 0.03), h / 2 - 0.03, "Y", LT)
                ring(m, w / 2, h / 2, [(0.0, -0.004), (0.01, 0.034), (0.034, 0.034), (0.046, -0.004)], TD, c=0.03)
    fat_stack(m, xs_, yc + ys_, Z3 + 0.14, 2.92, 0.20, foot=0.07)
    zl, zu = (0.10 + fa[0] - 0.03) / 2, (fa[1] + Z2 - 0.02) / 2
    for sx in SIDES:                                          # the end walls: one big let-in panel with a door in it; a bolted plate above
        with on_end(m, sx, sx * fx, yc, zl):
            framed(m, 1.10, 0.56)
            with m.at((0.28, -0.03, 0.006)):
                framed(m, 0.30, 0.42, LT)
                m.box((0.022, 0.11, 0.022), (-0.09, 0, 0.02), TD)
        with on_end(m, sx, sx * (fx - 0.03), yc, zu):
            bolted(m, 0.80, 0.30, G, r=0.02)
    with on_side(m, 1, yc + fy, zl, xc=-0.38):                # the back wall: a big panel and a louvre; a bolted plate above
        framed(m, 0.90, 0.56)
    with on_side(m, 1, yc + fy, zl, xc=0.50):
        vent(m, 0.31, 0.21)
    with on_side(m, 1, yc + fy - 0.03, zu, xc=0.0):
        bolted(m, 1.20, 0.30, G, r=0.02)
    with on_side(m, -1, yc - fy + 0.03, zu, xc=-0.52):        # the wall over the low block: a bolted plate beside the ducts
        bolted(m, 0.60, 0.30, G, r=0.02)
    # ---- two fat ducts from the low block's roof over into the furnace; a short fat stack beside them
    rd, zq = 0.105, 1.42
    ys2 = yc - fy + 0.03
    for x in (0.10, 0.55):
        with m.at((x, yb, 0)):
            octa(m, rd + 0.05, rd + 0.02, Zl - 0.01, Zl + 0.08, G)
            octa(m, rd, rd, Zl + 0.07, zq - 0.13, LT)
            slab(m, 0.14, 0.14, zq - 0.14, zq + 0.14, 0.03, G, bevel=0.02)
        y0 = yb + 0.14
        m.cyl(rd * K, ys2 - y0 + 0.04, (x, (y0 + ys2) / 2, zq), LT, seg=8, axis="Y", rot=(0, rad(22.5), 0))
        m.cyl((rd + 0.022) * K, 0.07, (x, (y0 + ys2) / 2 - 0.06, zq), G, seg=8, axis="Y", rot=(0, rad(22.5), 0))
    fat_stack(m, 0.88, yb, Zl, 1.86, 0.10)


mill12.frame, mill12.shadow, mill12.res = {"iso": (5.4, 1.4), "side": (5.0, 1.5), "top": (4.4, 0.6), "end": (4.4, 1.5)}, True, 1800
_hero.HEROES["mill12"] = mill12


def mill13(m, paint="h_p1"):
    """Steel mill, 3x3 (hitbox 3x3x3), a through machine, the belt along the near row. Set beside former5
    at one scale, mill12 had half the former's detail for half as much surface again, and a grade 3
    machine that turns two things into a third should look more complicated than a press, not less.
    Measured across every draft, what was rejected was never the amount but the kind: small things
    stuck on flat walls (mill6), pipes wound round a box (mill11). The former's kind is structure. The
    developer's word for this one: moderately more pipes and stacks.
    So mill12's lopsided layout, a little smaller, with one more joint in its structure:
    - the low block is the former's house (cabinet under a painted body, no dark lid), the belt through
      it, a mouth3 at each end;
    - on its roof a plenum with three fat stacks, each taller than the last, as on the former; two
      straight ducts cross from the furnace's upper course into the plenum's side, and at the roof's
      other end a third rises through a box elbow and crosses higher up;
    - the furnace behind, in two courses under a plain roof, its fat stack in the back corner under the
      frame's window, red grates under the other bays."""
    yb = -1.0
    X, hy = 1.05, 0.44
    Zc, Zr = 0.86, 1.12
    body = (X - 0.08, hy - 0.08, 0.045)
    with m.at((0, yb, 0)):
        belt_stub(m, -1.5, -X + 0.02, -1.39, -1.455)
        belt_stub(m, X - 0.02, 1.5, 1.39, 1.455)
        mouth3(m, -X, -1, paint)
        mouth3(m, X, 1, paint)
        slab(m, X - 0.01, hy + 0.015, 0.0, 0.16, 0.03, T, bevel=0.012)
        slab(m, X, hy, 0.12, Zc, 0.035, G, bevel=0.02)
        slab(m, body[0], body[1], Zc - 0.01, Zr, body[2], paint, bevel=0.022)
    yf, yp = yb - hy, yb - body[1]
    zc_, zb_ = (0.12 + Zc) / 2, (Zc + Zr) / 2
    with on_side(m, -1, yf, zc_, xc=0.05):                    # the cabinet's face: a louvre and two handwheels to one side, corner bolts
        vent(m, 0.25, 0.19)
    for x, z in ((0.52, 0.39), (0.78, 0.57)):
        with on_side(m, -1, yf, z, xc=x):
            handwheel(m, 0.14)
    for x in (-X + 0.068, X - 0.068):
        for z in (0.21, Zc - 0.09):
            with on_side(m, -1, yf, z, xc=x):
                m.cyl(0.028, 0.02, (0, 0, 0.008), LT, seg=6)
    for x, w in ((-0.62, 0.40), (-0.22, 0.24)):               # the body's face: two panels, a badge, the dial panel
        with on_side(m, -1, yp, zb_, xc=x):
            framed(m, w, 0.18)
    with on_side(m, -1, yp, zb_, xc=0.12):
        m.cyl(0.075, 0.022, (0, 0, 0.008), "h_red", seg=6)
        m.cyl(0.04, 0.012, (0, 0, 0.024), "h_white", seg=6)
    with on_side(m, -1, yp, zb_, xc=0.58):
        gauges(m, 0.22, 0.10)
    # ---- the furnace
    yc, fx, fy = 0.36, 0.90, 0.70
    Z1, Z2, Z3 = 1.00, 1.70, 1.78
    fa, fb = (Z1 - 0.01, Z1 + 0.14), (2.26, 2.41)
    RX, RY = fx + 0.10, fy + 0.10
    xs_, ys_ = -0.45, 0.30                                    # the stack, in the back corner
    with m.at((0, yc, 0)):
        slab(m, fx + 0.20, fy + 0.20, 0.0, 0.14, 0.04, T, bevel=0.014)
        slab(m, fx, fy, 0.10, Z1 + 0.01, 0.035, G, bevel=0.02)
        slab(m, fx - 0.03, fy - 0.03, Z1, Z2, 0.035, G, bevel=0.02)
        slab(m, fx - 0.01, fy - 0.01, Z2 - 0.02, Z3, 0.04, "h_dark", bevel=0.016)                       # a plain roof, not a dark lid
        for sx in SIDES:
            for sy in SIDES:
                m.box((0.15, 0.14, 0.03), (sx * (RX - 0.0375), sy * (RY - 0.034), 0.15), G, bevel=0.008)
                for dx, dy in ((0.0, 0.0), (-0.075, 0.0), (0.0, -0.068)):
                    m.box((0.044, 0.044, fb[0] + 0.02 - 0.16), (sx * (RX + dx), sy * (RY + dy), (fb[0] + 0.02 + 0.16) / 2), LT, bevel=0.008)
        frame_ring(m, fx + 0.18, fy + 0.18, fa[0], fa[1], 0.17, paint)
        frame_ring(m, fx + 0.173, fy + 0.173, fa[0] - 0.03, fa[0] + 0.004, 0.15, TD)
        frame_ring(m, fx + 0.26, fy + 0.26, fb[0], fb[1], 0.26, paint)
        frame_ring(m, fx + 0.253, fy + 0.253, fb[0] - 0.03, fb[0] + 0.004, 0.24, TD)
        bz, bh = (fb[0] + fb[1]) / 2, fb[1] - fb[0] - 0.04
        yx, xy = ys_ - 0.39, xs_ + 0.40
        m.box((2 * fx + 0.04, 0.15, bh), (0, yx, bz), paint, bevel=0.014)
        m.box((0.15, fy - yx - 0.075 + 0.04, bh), (xy, (yx + 0.075 + fy + 0.02) / 2 - 0.01, bz), paint, bevel=0.014)
        with m.at((xs_, ys_, 0)):
            slab(m, 0.28, 0.28, Z3 - 0.01, Z3 + 0.14, 0.05, G, bevel=0.02)
            slab(m, 0.292, 0.292, Z3 + 0.09, Z3 + 0.152, cut_to(0.292, 0.292, (0.28, 0.28, 0.05), 0.012), LT, bevel=0.012)
        for gx, gy, w, h in ((0.30, 0.33, 0.22, 0.42), (0.62, 0.33, 0.22, 0.42), (-0.30, -0.42, 0.44, 0.20)):
            with m.at((gx, gy, Z3)):
                m.box((w - 0.08, h - 0.08, 0.014), (0, 0, 0.004), "h_neon")
                n = max(3, round(max(w, h) / 0.085) - 1)
                for k_ in range(n):
                    t_ = -(n - 1) * 0.0425 + k_ * 0.085
                    if h > w:
                        m.prism([(t_ - 0.015, 0.009), (t_ + 0.015, 0.009), (t_ + 0.008, 0.03), (t_ - 0.008, 0.03)], -(w / 2 - 0.03), w / 2 - 0.03, "X", LT)
                    else:
                        m.prism([(t_ - 0.015, 0.009), (t_ + 0.015, 0.009), (t_ + 0.008, 0.03), (t_ - 0.008, 0.03)], -(h / 2 - 0.03), h / 2 - 0.03, "Y", LT)
                ring(m, w / 2, h / 2, [(0.0, -0.004), (0.01, 0.034), (0.034, 0.034), (0.046, -0.004)], TD, c=0.03)
    fat_stack(m, xs_, yc + ys_, Z3 + 0.14, 2.92, 0.19, foot=0.07)
    zl, zu = (0.10 + fa[0] - 0.03) / 2, (fa[1] + Z2 - 0.02) / 2
    for sx in SIDES:                                          # the end walls: one big let-in panel with a door in it, corner bolts; a bolted plate above
        with on_end(m, sx, sx * fx, yc, zl):
            framed(m, 1.00, 0.56)
            with m.at((0.25, -0.03, 0.006)):
                framed(m, 0.30, 0.42, LT)
                m.box((0.022, 0.11, 0.022), (-0.09, 0, 0.02), TD)
        for y in (yc - fy + 0.068, yc + fy - 0.068):
            for z in (0.21, fa[0] - 0.13):
                with on_end(m, sx, sx * fx, y, z):
                    m.cyl(0.028, 0.02, (0, 0, 0.008), LT, seg=6)
        with on_end(m, sx, sx * (fx - 0.03), yc, zu):
            bolted(m, 0.70, 0.30, G, r=0.02)
    with on_side(m, 1, yc + fy, zl, xc=-0.32):
        framed(m, 0.80, 0.56)
    with on_side(m, 1, yc + fy, zl, xc=0.46):
        vent(m, 0.31, 0.21)
    with on_side(m, 1, yc + fy - 0.03, zu, xc=0.0):
        bolted(m, 1.10, 0.30, G, r=0.02)
    # ---- on the low block's roof: the plenum and its three stacks, fed by two straight ducts from the furnace
    rd = 0.105
    xa0, xa1, pa = -0.02, 0.90, 0.20
    pz = Zr + 0.36
    with m.at(((xa0 + xa1) / 2, yb, 0)):
        slab(m, (xa1 - xa0) / 2, pa, Zr - 0.01, pz, 0.04, G, bevel=0.02)
        slab(m, (xa1 - xa0) / 2 + 0.012, pa + 0.012, pz - 0.05, pz + 0.012, cut_to((xa1 - xa0) / 2 + 0.012, pa + 0.012, ((xa1 - xa0) / 2, pa, 0.04), 0.012), LT, bevel=0.012)
    for x, top in ((0.165, 2.00), (0.44, 2.30), (0.715, 2.60)):
        fat_stack(m, x, yb, pz, top, 0.095, foot=0.035)
    ys2, zq = yc - fy + 0.03, Zr + 0.18
    for x in (0.24, 0.66):
        y0 = yb + pa
        m.cyl(rd * K, ys2 - y0 + 0.05, (x, (y0 + ys2) / 2, zq), LT, seg=8, axis="Y", rot=(0, rad(22.5), 0))
        m.cyl((rd + 0.022) * K, 0.07, (x, (y0 + ys2) / 2, zq), G, seg=8, axis="Y", rot=(0, rad(22.5), 0))
    # and at the roof's other end a third duct, up through a box elbow and across higher
    xw, zq2 = -0.55, 1.54
    with m.at((xw, yb, 0)):
        octa(m, rd + 0.05, rd + 0.02, Zr - 0.01, Zr + 0.08, G)
        octa(m, rd, rd, Zr + 0.07, zq2 - 0.13, LT)
        slab(m, 0.14, 0.14, zq2 - 0.14, zq2 + 0.14, 0.03, G, bevel=0.02)
    y0 = yb + 0.14
    m.cyl(rd * K, ys2 - y0 + 0.04, (xw, (y0 + ys2) / 2, zq2), LT, seg=8, axis="Y", rot=(0, rad(22.5), 0))
    for y in (y0 + 0.14, ys2 - 0.12):
        m.cyl((rd + 0.022) * K, 0.07, (xw, y, zq2), G, seg=8, axis="Y", rot=(0, rad(22.5), 0))


mill13.frame, mill13.shadow, mill13.res = {"iso": (5.4, 1.4), "side": (5.0, 1.5), "top": (4.4, 0.6), "end": (4.4, 1.5)}, True, 1800
_hero.HEROES["mill13"] = mill13


def grate(m, w, h, bars_along="y"):
    """A big grate let into a roof, to be built with its middle on the roof's surface at the origin: red
    neon behind a few heavy bars in a thick raised rim. The heat's way out of a furnace."""
    m.box((w - 0.12, h - 0.12, 0.022), (0, 0, 0.001), "h_neon")
    span, across = (w, h) if bars_along == "y" else (h, w)
    n = max(3, round((span - 0.16) / 0.13))
    step = (span - 0.16) / n
    for k_ in range(n):
        t_ = -(n - 1) * step / 2 + k_ * step
        sec = [(t_ - 0.028, 0.01), (t_ + 0.028, 0.01), (t_ + 0.016, 0.05), (t_ - 0.016, 0.05)]
        if bars_along == "y":
            m.prism(sec, -(across / 2 - 0.04), across / 2 - 0.04, "Y", TD)
        else:
            m.prism(sec, -(across / 2 - 0.04), across / 2 - 0.04, "X", TD)
    ring(m, w / 2, h / 2, [(0.0, -0.004), (0.014, 0.056), (0.05, 0.056), (0.066, -0.004)], G, c=0.045)


def mill14(m, paint="h_p1", trim=False):
    """Steel mill, 3x3 (hitbox 3x3x3), a through machine, the belt along the near row: the first machine
    put together from the kit (kitset.py), at the developer's word. mill13's lopsided layout, which he
    found better than what came before, with the kit's pieces in place of parts drawn for it:
    - the mouths are the kit's grade 3 mouth (three thick painted ribs, deep), so the low block's walls
      stand further back from the cell's edge;
    - on the low block's roof the kit's rising three stacks on their plenum, two straight kit pipes from
      the furnace into the plenum's side, and a third through the kit's elbow, crossing higher; every
      pipe ringed at the pitch and swelling into a flange where it meets a wall;
    - in the furnace's back corner the kit's big stack, straight on the roof (the developer had the
      plate under it taken away).
    In the furnace's roof one big grate of red neon behind heavy bars (for a steel mill the grate should
    be big), the frame above it left open: one beam only, between the grate and the stack.
    Nothing is stuck on the walls: the developer had every "3D decal" taken off (2026-10-09), the ribs,
    the let-in panels and doors, the louvres, handwheels, panels, badge, dials and corner bolts. They
    are still here, behind trim=True, should any come back."""
    kit = kitset
    yb = -1.0
    X, hy = 0.90, 0.46                                        # the walls stand back: the mouths are 0.46 deep
    Zc, Zr = 0.88, 1.14
    body = (X - 0.08, hy - 0.08, 0.045)
    with m.at((0, yb, 0)):
        run(m, -1.5, 1.5, braces=(-1.44, 1.44))
        kit.mouth(m, -X, -1, 3, paint)
        kit.mouth(m, X, 1, 3, paint)
        slab(m, X - 0.01, hy - 0.01, 0.0, 0.16, 0.03, T, bevel=0.012)
        slab(m, X, hy, 0.12, Zc, 0.035, G, bevel=0.02)
        slab(m, body[0], body[1], Zc - 0.01, Zr, body[2], paint, bevel=0.022)
    if trim:
        yf, yp = yb - hy, yb - body[1]
        zc_, zb_ = (0.12 + Zc) / 2, (Zc + Zr) / 2
        with on_side(m, -1, yf, zc_, xc=-0.12):                   # the cabinet's face: a louvre, two handwheels, corner bolts
            vent(m, 0.25, 0.19)
        for x, z in ((0.36, 0.40), (0.62, 0.58)):
            with on_side(m, -1, yf, z, xc=x):
                handwheel(m, 0.14)
        for x in (-X + 0.068, X - 0.068):
            for z in (0.21, Zc - 0.09):
                with on_side(m, -1, yf, z, xc=x):
                    m.cyl(0.028, 0.02, (0, 0, 0.008), LT, seg=6)
        for x, w in ((-0.52, 0.40), (-0.14, 0.24)):               # the body's face: two panels, a badge, the dial panel
            with on_side(m, -1, yp, zb_, xc=x):
                framed(m, w, 0.18)
        with on_side(m, -1, yp, zb_, xc=0.14):
            m.cyl(0.075, 0.022, (0, 0, 0.008), "h_red", seg=6)
            m.cyl(0.04, 0.012, (0, 0, 0.024), "h_white", seg=6)
        with on_side(m, -1, yp, zb_, xc=0.52):
            gauges(m, 0.20, 0.10)
    # ---- the furnace
    yc, fx, fy = 0.36, 0.90, 0.70
    Z1, Z2, Z3 = 0.98, 1.70, 1.76
    fa, fb = (Z1 - 0.01, Z1 + 0.14), (2.26, 2.41)
    RX, RY = fx + 0.10, fy + 0.10
    xs_, ys_ = -0.47, 0.30                                    # the big stack, in the back corner
    with m.at((0, yc, 0)):
        slab(m, fx + 0.20, fy + 0.20, 0.0, 0.14, 0.04, T, bevel=0.014)
        slab(m, fx, fy, 0.10, Z1 + 0.01, 0.035, G, bevel=0.02)
        slab(m, fx - 0.03, fy - 0.03, Z1, Z2, 0.035, G, bevel=0.02)
        slab(m, fx - 0.01, fy - 0.01, Z2 - 0.02, Z3, 0.04, "h_dark", bevel=0.016)
        for sx in SIDES:
            for sy in SIDES:
                m.box((0.15, 0.14, 0.03), (sx * (RX - 0.0375), sy * (RY - 0.034), 0.15), G, bevel=0.008)
                for dx, dy in ((0.0, 0.0), (-0.075, 0.0), (0.0, -0.068)):
                    m.box((0.044, 0.044, fb[0] + 0.02 - 0.16), (sx * (RX + dx), sy * (RY + dy), (fb[0] + 0.02 + 0.16) / 2), LT, bevel=0.008)
        frame_ring(m, fx + 0.18, fy + 0.18, fa[0], fa[1], 0.17, paint)
        frame_ring(m, fx + 0.173, fy + 0.173, fa[0] - 0.03, fa[0] + 0.004, 0.15, TD)
        frame_ring(m, fx + 0.26, fy + 0.26, fb[0], fb[1], 0.26, paint)
        frame_ring(m, fx + 0.253, fy + 0.253, fb[0] - 0.03, fb[0] + 0.004, 0.24, TD)
        xy = xs_ + 0.40                                       # the one beam across the top frame, between the stack and the grate
        m.box((0.15, 2 * fy + 0.04, fb[1] - fb[0] - 0.04), (xy, 0, (fb[0] + fb[1]) / 2), paint, bevel=0.014)
        with m.at((0.38, 0.0, Z3)):                           # the big grate, under the open bay
            grate(m, 0.86, 1.04)
        with m.at((xs_, ys_, 0)):
            kit.k_stack_one(m, Z3, h=1.16, base=False)       # no plate under it (the developer, 2026-10-09)
    if trim:
        zl, zu = (0.10 + fa[0] - 0.03) / 2, (fa[1] + Z2 - 0.02) / 2
        rib = (0.075, Z2 - 0.02 - fa[1], 0.045)
        for sx in SIDES:                                          # the end walls: a big let-in panel with a door, corner bolts; ribs above
            with on_end(m, sx, sx * fx, yc, zl):
                framed(m, 1.00, 0.56)
                with m.at((0.25, -0.03, 0.006)):
                    framed(m, 0.30, 0.42, LT)
                    m.box((0.022, 0.11, 0.022), (-0.09, 0, 0.02), TD)
            for y in (yc - fy + 0.068, yc + fy - 0.068):
                for z in (0.21, fa[0] - 0.13):
                    with on_end(m, sx, sx * fx, y, z):
                        m.cyl(0.028, 0.02, (0, 0, 0.008), LT, seg=6)
            for y in (yc - 0.42, yc, yc + 0.42):
                with on_end(m, sx, sx * (fx - 0.03), y, zu):
                    m.box(rib, (0, 0, 0.02), LT, bevel=0.01)
        with on_side(m, 1, yc + fy, zl, xc=-0.32):                # the back wall: a panel and a louvre; ribs above
            framed(m, 0.80, 0.56)
        with on_side(m, 1, yc + fy, zl, xc=0.46):
            vent(m, 0.31, 0.21)
        for x in (-0.60, -0.20, 0.20, 0.60):
            with on_side(m, 1, yc + fy - 0.03, zu, xc=x):
                m.box(rib, (0, 0, 0.02), LT, bevel=0.01)
    # ---- on the low block's roof: the kit's three rising stacks, and the pipes from the furnace
    xp, zq = 0.26, Zr + kit.DUCT_AT
    with m.at((xp, yb, 0)):
        kit.k_stack_rise3(m, Zr)
    ys2 = yc - fy + 0.03                                      # the furnace's upper wall, facing the low block
    for x in (0.05, 0.47):
        kit._run_y(m, yb + 0.20 - 0.012, ys2 + 0.012, x, zq)
    xw, zq2 = -0.55, 1.53                                     # the third: up through an elbow, across higher
    kit._riser(m, xw, yb, Zr, zq2 - kit.INTO)
    kit._elbow(m, xw, yb, zq2)
    kit._run_y(m, yb + kit.INTO, ys2 + 0.012, xw, zq2)
    if trim:
        for x in (-0.25, 0.80):                                   # two ribs on the furnace's wall over the low block, clear of the pipes
            with on_side(m, -1, ys2, zu, xc=x):
                m.box(rib, (0, 0, 0.02), LT, bevel=0.01)


mill14.frame, mill14.shadow, mill14.res = {"iso": (5.4, 1.4), "side": (5.0, 1.5), "top": (4.4, 0.6), "end": (4.4, 1.5)}, True, 1800
_hero.HEROES["mill14"] = mill14


def cmp_former_mill(m):
    """Not a machine: the confirmed former and the latest steel mill side by side at one scale, with a
    figure as tall as a character between them, to compare the two."""
    with m.at((-2.3, 0.5, 0)):
        former5(m)
    with m.at((2.1, 0.0, 0)):
        mill14(m)
    with m.at((-0.35, -1.2, 0)):
        tower(m, [(0.11, 0.07, 0.02, 0.0), (0.11, 0.07, 0.02, 0.66)], TD)
        tower(m, [(0.165, 0.085, 0.025, 0.66), (0.165, 0.085, 0.025, 1.30)], "h_white")
        tower(m, [(0.10, 0.10, 0.03, 1.31), (0.10, 0.10, 0.03, 1.67)], LT)


cmp_former_mill.frame, cmp_former_mill.shadow, cmp_former_mill.res = {"iso": (9.6, 1.4), "side": (9.0, 1.5), "top": (9.0, 0.6), "end": (6.0, 1.5)}, True, 2800
_hero.HEROES["cmp_former_mill"] = cmp_former_mill


def former5_paints(m):
    """Not a machine: former5 four times, each in a different trial paint, to choose a colour of our own."""
    for (x, y), key in zip(((-2.3, 1.9), (2.3, 1.9), (-2.3, -1.9), (2.3, -1.9)), PAINTS):
        with m.at((x, y, 0)):
            former5(m, key)


former5_paints.frame, former5_paints.shadow, former5_paints.res = {"iso": (10.6, 1.4), "side": (9.0, 1.5), "top": (9.0, 0.6), "end": (8.0, 1.5)}, True, 2600
_hero.HEROES["former5_paints"] = former5_paints


def formers_cmp(m):
    """Not a machine: the two formers side by side on a short line each, to compare a machine after
    Satisfactory (far) with one after Islands (near)."""
    for y, fn in ((1.5, former2), (-1.5, former3)):
        for x in (-3, -2, 2, 3):
            with m.at((x, y + 0.5, 0)):
                _belts.straight(m)
        with m.at((0, y, 0)):
            fn(m)


formers_cmp.frame, formers_cmp.shadow = {"iso": (8.2, 1.3), "side": (7.4, 1.5), "top": (7.0, 0.6), "end": (5.6, 1.5)}, True
formers_cmp.res = 2000
_hero.HEROES["formers_cmp"] = formers_cmp


def belts_stack(m):
    """Not a machine: three lines of conveyor one cell above another, each two straights, a ramp without
    trestles and a straight one cell higher, with things riding them, to judge the room between stacked
    belts and stacked ramps. Nothing holds the upper lines up: what carries a stacked belt is not
    designed yet."""
    for k in range(3):
        for x in (-2, -1):
            with m.at((x, 0, k)):
                _belts.straight(m)
        with m.at((0.5, 0, k)):
            _belts.ramp_bare(m)
        with m.at((2, 0, k + 1)):
            _belts.straight(m)
        for x, mk in ((-2.1 + 0.35 * k, "h_ore"), (-0.9 + 0.2 * k, "h_copper")):
            m.box((0.30, 0.28, 0.22), (x, 0, k + BZ + 0.116), mk, bevel=0.05)
        m.box((0.30, 0.28, 0.22), (2.0, 0, k + 1 + BZ + 0.116), "h_ore", bevel=0.05)


belts_stack.frame, belts_stack.shadow = {"iso": (6.6, 1.7), "side": (5.6, 1.8), "top": (5.4, 0.6), "end": (3.2, 1.8)}, True
_hero.HEROES["belts_stack"] = belts_stack
F11 = {"iso": (1.9, 0.25), "side": (1.6, 0.4), "top": (1.5, 0.3), "end": (1.6, 0.4)}
F21R = {"iso": (3.3, 0.7), "side": (2.8, 0.8), "top": (2.6, 0.5), "end": (2.2, 0.8)}
for _n, _f, _fr in (("belt_straight", _belts.straight, F11), ("belt_right", _belts.corner_right, F11), ("belt_left", _belts.corner_left, F11),
                    ("belt_ramp2", _belts.ramp, F21R), ("belt_ramp_start", _belts.ramp_start, F21R),
                    ("belt_ramp_mid", _belts.ramp_mid, F21R), ("belt_ramp_end", _belts.ramp_end, F21R),
                    ("belt_ramp_down", _belts.ramp_down, F21R), ("belt_ramp_down_start", _belts.ramp_down_start, F21R),
                    ("belt_ramp_down_mid", _belts.ramp_down_mid, F21R), ("belt_ramp_down_end", _belts.ramp_down_end, F21R)):
    _f.frame, _f.shadow = _fr, True
    _hero.HEROES[_n] = _f

def smelter9(m):
    """Smelter, 4x2, grade 2 (hitbox 4x2x2). The same machine as smelter8, which the developer approved,
    at the size of the real Islands smelter: beside a character in the game smelter8 stood waist high
    and looked like a toy, and a screenshot of the original showed it head high and half as wide again
    as a belt. The belt stays one cell wide; it is the body that has grown, and its parts with it.
    The belt runs along the far row. The body straddles it and fills the near row: a dark foot, a
    light firebox with a fire mouth each side of the middle in both long walls, under a dark sloped
    hood. On the hood's crown lie the wide hearth box, open at the top, the fire under a row of bars,
    a glowing tap port in its end; and the blower, a square casing whose open top is its intake. From
    each side of the blower a fat pipe runs out, turns once in the open and runs along the hearth
    into a boot on its wall."""
    yb, X = 0.5, 1.25
    with m.at((0, yb, 0)):
        bed(m, -2.0, 2.0)
        m.box((4.0, BH * 2, 0.03), (0, 0, BZ - 0.015), "h_belt")
        for x in (-1.80, 1.80):                               # one whole pair of arrows on each open stretch
            chev(m, x)
        for x in (-1.87, 1.87):
            buttress(m, x)
        cover(m, X, 1, sole=False)
        cover(m, -X, -1, sole=False)
        collar(m, -X - 0.318, X + 0.318, mk=T)
    y0, y1 = -0.90, 0.94
    yc, hy = (y0 + y1) / 2, (y1 - y0) / 2
    bprism(m, [(-X - 0.012, y0 - 0.012), (X + 0.012, y0 - 0.012), (X + 0.012, 0.02), (-X - 0.012, 0.02)], 0.0, 0.39, "Z", T, bevel=0.014)   # the foot, in the near row
    with m.at((0, yc, 0)):
        slab(m, X, hy, 0.37, 0.985, 0.05, G, bevel=0.022)     # firebox
        P = 1.17
        bprism(m, [(-hy - 0.03, 0.96), (-hy - 0.03, 1.02), (-0.62, P), (0.62, P), (hy + 0.03, 1.02), (hy + 0.03, 0.96)], -X - 0.02, X + 0.02, "X", TD, bevel=0.022)   # hood
    for d, y in ((-1, y0), (1, y1)):                          # fire mouths in both long walls
        for x in (-0.62, 0.62):
            with on_side(m, d, y, 0.67, xc=x):
                fire_window(m, bars=6, hx=0.30, hy=0.18)
        with on_side(m, d, y, 0.67, xc=0.0):
            bolted(m, 0.40, 0.36, LT)
    for sx in SIDES:                                          # each end wall, beside the mouth: a tall vent
        with on_end(m, sx, sx * X, (y0 + 0.0) / 2, 0.67):
            vent(m, 0.30, 0.20)
    # the hearth box
    xt = -0.34
    with m.at((xt, yc, 0)):
        tower(m, [(0.60, 0.47, 0.08, P - 0.01), (0.555, 0.425, 0.07, P + 0.09)], T)
        tower(m, [(0.555, 0.425, 0.07, P + 0.08), (0.62, 0.49, 0.08, P + 0.64), (0.62, 0.49, 0.08, P + 0.66)], G)
        shell(m, [(0.648, 0.518, 0.09, P + 0.64), (0.648, 0.518, 0.09, P + 0.715), (0.62, 0.49, 0.08, P + 0.742),
                  (0.545, 0.415, 0.055, P + 0.742), (0.53, 0.40, 0.05, P + 0.64)], TD)
        tower(m, [(0.54, 0.41, 0.052, P + 0.63), (0.54, 0.41, 0.052, P + 0.668)], "h_glow")
        for k in range(8):                                    # bars across the hearth, their ends set into the rim
            x = -0.42 + k * 0.12
            m.prism([(x - 0.032, P + 0.662), (x + 0.032, P + 0.662), (x + 0.018, P + 0.71), (x - 0.018, P + 0.71)], -0.43, 0.43, "Y", TD)
    with on_end(m, -1, xt - 0.575, yc, P + 0.36):             # tap port in the hearth's end; the wall leans, so it stands as a boss
        octa(m, 0.095, 0.095, -0.008, 0.01, "h_glow")
        oct_ring(m, 0.145, 0.055, -0.04, 0.035, T)
    # the blower
    xw = 0.86
    case = (0.24, 0.25, 0.045)
    with m.at((xw, yc, 0)):
        tower(m, [(0.265, 0.275, 0.05, P - 0.01), (case[0], case[1], case[2], P + 0.06)], T)
        slab(m, case[0], case[1], P + 0.05, P + 0.38, case[2], ST, bevel=0.016)
        cc = cut_to(0.255, 0.265, case, 0.012)
        shell(m, [(0.255, 0.265, cc, P + 0.365), (0.255, 0.265, cc, P + 0.42), (0.238, 0.248, cc, P + 0.442),
                  (0.185, 0.195, 0.03, P + 0.442), (0.172, 0.182, 0.026, P + 0.365)], TD)
        tower(m, [(0.18, 0.19, 0.028, P + 0.355), (0.18, 0.19, 0.028, P + 0.39)], SLIT)
        for y in (-0.085, 0.085):
            m.prism([(y - 0.022, P + 0.385), (y + 0.022, P + 0.385), (y + 0.012, P + 0.425), (y - 0.012, P + 0.425)], -0.20, 0.20, "X", ST)
    # air pipes: out of each side of the casing through a flange, one turn in the open, along the hearth, into a boot on its wall
    zp, ra, rf, yo, xe = P + 0.24, 0.075, 0.098, 0.685, xt + 0.24
    for d in SIDES:
        m.pipe([(xw, yc + d * (case[1] - 0.03), zp), (xw, yc + d * (yo - 0.09), zp), (xw - 0.09, yc + d * yo, zp), (xe - 0.02, yc + d * yo, zp)], ra, ST, seg=10)
        m.cyl(rf, 0.03, (xw, yc + d * (case[1] + 0.015), zp), TD, seg=8, axis="Y", rot=(0, rad(22.5), 0))
        with m.at((xe - 0.12, yc + d * 0.63, 0)):             # the boot: a shouldered block on the hearth's wall, the pipe into its end
            tower(m, [(0.12, 0.185, 0.035, zp - 0.135), (0.12, 0.185, 0.035, zp + 0.075), (0.085, 0.15, 0.03, zp + 0.135)], T)
        m.cyl(rf, 0.03, (xe + 0.015, yc + d * yo, zp), TD, seg=8, axis="X", rot=(rad(22.5), 0, 0))


smelter9.frame, smelter9.shadow = {"iso": (4.6, 0.9), "side": (4.6, 1.1), "top": (4.2, 0.6), "end": (3.2, 1.1)}, True
_hero.HEROES["smelter9"] = smelter9

for _n, _f in (("smelter5a", smelter5a), ("smelter5b", smelter5b), ("smelter5c", smelter5c)):
    _f.frame, _f.shadow = F31, True
    _hero.HEROES[_n] = _f

assembler4.frame, assembler4.shadow = F33, True
_hero.HEROES["assembler4"] = assembler4

for _name, _fn, _frame in (("smelter2", smelter2, F31), ("washer2", washer2, F31), ("extractor2", extractor2, F21),
                           ("assembler3", assembler3, F33)):
    _fn.frame, _fn.shadow = _frame, True
    _hero.HEROES[_name] = _fn

from . import kitset  # noqa: E402,F401  (the kit registers its pieces as heroes; it reads this module's helpers at call time)
