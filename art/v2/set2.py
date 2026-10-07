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
    """Assembler, 3x3: two inputs side by side, one output. Two arms on an open deck, under a pair of
    dark steel arches, fit parts from a tray at each side onto the frame on the turntable between them.
    A control cabin stands between the inputs and a ribbed power cabinet at each back corner."""
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
            for y in (-0.42, 0.42):
                bx(m, (0.0, 0.05), (y - 0.07, y + 0.07), (0.0, 0.84), D, bevel=0.02)
            m.box((0.04, 0.50, 0.40), (0.045, 0, 0.42), G, bevel=0.028)
            m.box((0.012, 0.012, 0.34), (0.022, 0, 0.42), SLIT)
            for s in SIDES:
                m.box((0.02, 0.03, 0.12), (0.018, s * 0.05, 0.42), T)
            m.box((0.012, 0.62, 0.09), (0.026, 0, 0.73), "h_glass")
            for y in (-0.31, -0.105, 0.105, 0.31):
                m.box((0.02, 0.025, 0.10), (0.022, y, 0.73), D)
    # control cabin between the inputs
    x0 = -1.15
    bx(m, (-1.18, -0.48), (-0.40, 0.40), (0.0, 0.16), T, bevel=0.04)
    bx(m, (x0, -0.48), (-0.37, 0.37), (0.12, 0.90), G, bevel=0.04)
    bx(m, (-1.17, -0.48), (-0.39, 0.39), (0.86, 0.97), TD, bevel=0.025)
    m.box((0.02, 0.50, 0.26), (x0 - 0.004, 0, 0.56), SLIT)
    for sz in SIDES:
        m.box((0.045, 0.58, 0.04), (x0 - 0.012, 0, 0.56 + sz * 0.15), T)
    for s in SIDES:
        m.box((0.045, 0.04, 0.30), (x0 - 0.012, s * 0.27, 0.56), T)
    for i, w in enumerate((0.38, 0.24, 0.30)):
        m.box((0.008, w, 0.03), (x0 - 0.016, 0, 0.56 + (1 - i) * 0.07), "h_core")
    # a ribbed power cabinet at each back corner, with its duct into the hall
    for sy in SIDES:
        ys = tuple(sorted((sy * 0.64, sy * 1.38)))
        bx(m, (0.56, 1.40), tuple(sorted((sy * 0.60, sy * 1.42))), (0.0, 0.16), T, bevel=0.04)
        bx(m, (0.60, 1.36), ys, (0.12, 1.02), ST, bevel=0.04)
        bx(m, (0.58, 1.38), tuple(sorted((sy * 0.62, sy * 1.40))), (0.98, 1.10), TD, bevel=0.03)
        for k in range(5):
            m.box((0.05, 0.04, 0.72), (0.70 + k * 0.14, sy * 1.39, 0.56), LT)
        for k in range(4):
            m.box((0.04, 0.06, 0.72), (1.37, sy * (0.76 + k * 0.17), 0.56), LT)
        for x in (0.82, 1.14):
            m.cyl(0.06, 0.16, (x, sy * 1.0, 1.18), LT, seg=8)
            m.cyl(0.085, 0.04, (x, sy * 1.0, 1.25), TD, seg=8)
        bx(m, (0.46, 0.64), tuple(sorted((sy * 0.86, sy * 1.14))), (0.62, 0.84), ST, bevel=0.025)
    # on the deck
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


for _name, _fn, _frame in (("smelter2", smelter2, F31), ("washer2", washer2, F31), ("extractor2", extractor2, F21),
                           ("assembler3", assembler3, F33)):
    _fn.frame, _fn.shadow = _frame, True
    _hero.HEROES[_name] = _fn
