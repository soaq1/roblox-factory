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


def _asm_lower(m):
    """Assembler, 3x3: two inputs side by side, one output. The hall, the mouths, a control cabin
    between the inputs and a power cabinet with folded walls at each back corner."""
    for sy in SIDES:
        with m.at((0, sy * 1.0, 0)):
            run(m, -1.5, -0.5, braces=(-4 / 3, -1.0))
            cover(m, -0.5, -1)
    run(m, 0.5, 1.5, braces=(1.0, 4 / 3))
    cover(m, 0.5, 1)
    bx(m, (-0.52, 0.52), (-1.49, 1.49), (0.0, 0.20), T, bevel=0.045)
    bx(m, (-0.50, 0.50), (-1.47, 1.47), (0.16, 0.86), G, bevel=0.035)
    bx(m, (-0.53, 0.53), (-1.50, 1.50), (0.82, 0.96), TD, bevel=0.03)
    for sy in SIDES:
        with frame(m, (0, sy * 1.5), (0, -sy)):
            for y in (-0.42, 0.42):                           # buttresses that thin toward the top
                m.prism([(0.0, 0.0), (0.05, 0.0), (0.05, 0.84), (0.032, 0.84), (0.0, 0.34)], y - 0.075, y + 0.075, "Y", D)
            m.box((0.04, 0.50, 0.40), (0.045, 0, 0.42), G, bevel=0.028)
            m.box((0.012, 0.012, 0.34), (0.022, 0, 0.42), SLIT)
            for s in SIDES:
                m.cyl(0.013, 0.13, (0.014, s * 0.05, 0.42), T, seg=6)
            m.box((0.012, 0.62, 0.09), (0.026, 0, 0.73), "h_glass")
            m.prism([(0.03, 0.675), (0.008, 0.69), (0.008, 0.77), (0.03, 0.785)], -0.335, -0.31, "Y", D)
            m.prism([(0.03, 0.675), (0.008, 0.69), (0.008, 0.77), (0.03, 0.785)], 0.31, 0.335, "Y", D)
            for y in (-0.105, 0.105):
                m.box((0.018, 0.022, 0.095), (0.022, y, 0.73), D, bevel=0.006)
    # control cabin between the inputs, with a bezelled screen
    x0 = -1.15
    bx(m, (-1.18, -0.48), (-0.40, 0.40), (0.0, 0.16), T, bevel=0.04)
    bx(m, (x0, -0.48), (-0.37, 0.37), (0.12, 0.90), G, bevel=0.04)
    bx(m, (-1.17, -0.48), (-0.39, 0.39), (0.86, 0.97), TD, bevel=0.03)
    m.box((0.012, 0.50, 0.26), (x0 - 0.002, 0, 0.56), SLIT)
    for sz in SIDES:
        zi, zo = 0.56 + sz * 0.13, 0.56 + sz * 0.195
        m.prism([(x0, zi), (x0 - 0.034, zi + sz * 0.014), (x0 - 0.034, zo - sz * 0.012), (x0, zo)], -0.315, 0.315, "Y", T)
    for s in SIDES:
        yi, yo = s * 0.25, s * 0.315
        m.prism([(x0, yi), (x0 - 0.034, yi + s * 0.014), (x0 - 0.034, yo - s * 0.012), (x0, yo)], 0.416, 0.704, "Z", T)
    for i, w in enumerate((0.38, 0.24, 0.30)):
        m.box((0.008, w, 0.03), (x0 - 0.01, 0, 0.56 + (1 - i) * 0.07), "h_core")
    # a power cabinet at each back corner: its outer walls are folded into ribs
    for sy in SIDES:
        y0, y1 = sorted((sy * 0.66, sy * 1.36))
        bx(m, (0.56, 1.42), tuple(sorted((sy * 0.60, sy * 1.42))), (0.0, 0.16), T, bevel=0.04)
        corrugated(m, 0.60, 1.36, y0, y1, 0.12, 1.02, ("ymin" if sy < 0 else "ymax", "xmax"), ST)
        bx(m, (0.57, 1.41), tuple(sorted((sy * 0.62, sy * 1.41))), (0.98, 1.10), TD, bevel=0.035)
        for x in (0.82, 1.14):
            m.cyl(0.055, 0.14, (x, sy * 1.0, 1.17), LT, seg=8, r2=0.035)
            m.cyl(0.075, 0.05, (x, sy * 1.0, 1.255), TD, seg=8, r2=0.045)
        bx(m, (0.46, 0.64), tuple(sorted((sy * 0.86, sy * 1.14))), (0.62, 0.84), ST, bevel=0.035)


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


def strut(m, x0, x1, y, z, r=0.045, mk=ST):
    """An eight-sided tie running along the belt between two frames, with a collar at each end."""
    m.cyl(r * K, x1 - x0, ((x0 + x1) / 2, y, z), mk, seg=8, axis="X", rot=(rad(22.5), 0, 0))
    for x in (x0 + 0.13, x1 - 0.13):
        m.cyl(r * K * 1.5, 0.05, (x, y, z), TD, seg=8, axis="X", rot=(rad(22.5), 0, 0))


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
    taper_link(m, d, sh, elbow, 0.065, 0.045, 0.097, ST)      # a darker spine down the middle of the link
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
    """An open parts bin: a tray that flares toward its rim, dark inside."""
    m.box((w, l, h), (x, y, z + h / 2 - 0.005), ST, bevel=0.018, taper=1.20)
    m.box((w * 1.20 - 0.09, l * 1.20 - 0.09, 0.012), (x, y, z + h - 0.002), SLIT)


def assembler4(m):
    """Assembler, 3x3, second version: the same lower works, with the upper works built like the mouths.
    Two H-section portals on tapered bases, tied by eight-sided struts, carry a box girder with a hoist;
    the deck has a sloped kerb and seams; two tapered arms on stepped turrets work on the frame clamped
    to a rimmed turntable, each fed from a flared bin."""
    _asm_lower(m)
    Z = 0.96
    # deck: a kerb with a sloped inner face round the edge, and seams across the floor
    for s in SIDES:
        m.prism([(s * 1.50, Z - 0.02), (s * 1.50, Z + 0.035), (s * 1.475, Z + 0.06), (s * 1.445, Z + 0.06), (s * 1.40, Z - 0.02)],
                -0.53, 0.53, "X", ST)
        m.prism([(s * 0.53, Z - 0.02), (s * 0.53, Z + 0.035), (s * 0.505, Z + 0.06), (s * 0.475, Z + 0.06), (s * 0.43, Z - 0.02)],
                -1.42, 1.42, "Y", ST)
    for y in (-1.0, -0.5, 0.5, 1.0):
        m.box((0.84, 0.014, 0.006), (0, y, Z + 0.003), ST)
    # portals, tied by struts and carrying the hoist girder
    with m.at((0, 0, Z)):
        for x in (-0.33, 0.33):
            h_portal(m, x, 2.80, 1.30, 0.24)
    for s in SIDES:
        strut(m, -0.33, 0.33, s * 1.28, Z + 0.66)
        strut(m, -0.33, 0.33, s * 1.02, Z + 1.21)
    bx(m, (-0.50, 0.50), (-0.12, 0.12), (Z + 1.29, Z + 1.45), TD, bevel=0.045)
    for sx in SIDES:
        m.cyl(0.165 * K, 0.08, (sx * 0.50, 0, Z + 1.37), T, seg=8, axis="X", rot=(rad(22.5), 0, 0))
    m.prism([(-0.045, Z + 1.30), (0.045, Z + 1.30), (0.07, Z + 1.215), (-0.07, Z + 1.215)], -0.44, 0.44, "X", ST)
    bx(m, (-0.11, 0.11), (-0.13, 0.13), (Z + 1.09, Z + 1.22), G, bevel=0.035)
    m.cyl(0.075, 0.30, (0, 0, Z + 1.10), T, seg=8, axis="Y")
    m.cyl(0.085, 0.03, (0, 0, Z + 1.02), "h_core", seg=10)
    # turntable with the frame clamped to it
    octa(m, 0.40, 0.40, Z - 0.01, Z + 0.07, T)
    octa(m, 0.34, 0.31, Z + 0.07, Z + 0.14, ST)
    oct_ring(m, 0.36, 0.055, Z + 0.10, Z + 0.155, LT)
    m.box((0.44, 0.36, 0.20), (0, 0, Z + 0.23), G, bevel=0.035, taper=0.86)
    m.box((0.28, 0.20, 0.012), (0, 0, Z + 0.334), TD)
    m.box((0.16, 0.12, 0.08), (0, 0, Z + 0.375), "h_copper", bevel=0.02, taper=0.8)
    for sx in SIDES:
        for sy in SIDES:
            m.box((0.085, 0.085, 0.11), (sx * 0.245, sy * 0.20, Z + 0.185), D, bevel=0.018, taper=0.65, rot=rad(45))
    for d in SIDES:
        arm4(m, d, 0.70, Z, (0.56, Z + 1.04), (0.20, Z + 0.72))
        bin4(m, -0.02, d * 1.06, Z)
        m.box((0.11, 0.09, 0.08), (-0.09, d * 1.05, Z + 0.10), "h_copper", bevel=0.018)
        m.box((0.11, 0.09, 0.08), (0.07, d * 1.07, Z + 0.10), LT, bevel=0.018)
    # chute to the output
    m.prism([(0.38, Z + 0.07), (0.86, 0.86), (0.86, 0.78), (0.38, Z - 0.01)], -0.17, 0.17, "Y", T)
    for s in SIDES:
        a, b = sorted((s * 0.17, s * 0.225))
        m.prism([(0.38, Z + 0.17), (0.86, 0.96), (0.86, 0.78), (0.38, Z - 0.01)], a, b, "Y", G)


assembler4.frame, assembler4.shadow = F33, True
_hero.HEROES["assembler4"] = assembler4

for _name, _fn, _frame in (("smelter2", smelter2, F31), ("washer2", washer2, F31), ("extractor2", extractor2, F21),
                           ("assembler3", assembler3, F33)):
    _fn.frame, _fn.shadow = _frame, True
    _hero.HEROES[_name] = _fn
