# v2 second set: four more machines in the manner of the big furnace the developer picked (bay.blast3x with
# grey accents): light walls, a dark deck, dark steel for frames and vessels, the big plain faces broken
# up by buttresses, bands, staves and windows, the same conveyor and folding-cover mouths, and rendered
# with soft shadows.
import math
from . import hero as _hero
from . import pairs as _pairs
from .base import foot_hearth, foot_drain
from .supply import crystal
from .d import *          # noqa: F401,F403
from .d import run, cover, block, frame, stub_form, strip, frustum, K

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

for _n, _f in (("smelter5a", smelter5a), ("smelter5b", smelter5b), ("smelter5c", smelter5c)):
    _f.frame, _f.shadow = F31, True
    _hero.HEROES[_n] = _f

assembler4.frame, assembler4.shadow = F33, True
_hero.HEROES["assembler4"] = assembler4

for _name, _fn, _frame in (("smelter2", smelter2, F31), ("washer2", washer2, F31), ("extractor2", extractor2, F21),
                           ("assembler3", assembler3, F33)):
    _fn.frame, _fn.shadow = _frame, True
    _hero.HEROES[_name] = _fn
