# v2 power: machines that make electricity, store it and carry it.
import math
from .base import hex_stack
from .d import *          # noqa: F401,F403
from .d import stub, free, neck, strip, peep, frustum, K


def generator(m, Z):
    """Coal generator: a banded boiler lies along the deck with a steam dome on it and a stack at the
    far end; the dynamo's flywheel turns on each side."""
    neck(m, Z, 0.46, 0.41, 0.06)
    for x in (-0.26, 0.26):
        bx(m, (x - 0.07, x + 0.07), (-0.30, 0.30), (Z + 0.04, Z + 0.20), D, bevel=0.02)
    m.cyl(0.27 * K, 0.90, (0, 0, Z + 0.40), G, seg=8, axis="X", rot=(rad(22.5), 0, 0))
    for x in (-0.30, 0.0, 0.30):
        m.cyl(0.285 * K, 0.05, (x, 0, Z + 0.40), D, seg=8, axis="X", rot=(rad(22.5), 0, 0))
    m.cyl(0.11 * K, 0.16, (0.15, 0, Z + 0.72), G, seg=8, rot=rad(22.5))
    m.cyl(0.11 * K, 0.06, (0.15, 0, Z + 0.83), D, seg=8, r2=0.05 * K, rot=rad(22.5))
    hex_stack(m, -0.28, 0, Z + 0.62, 0.52, r=0.085)
    for d in SIDES:
        m.cyl(0.20, 0.05, (0.0, d * 0.40, Z + 0.40), D, seg=12, axis="Y")
        m.cyl(0.07, 0.07, (0.0, d * 0.405, Z + 0.40), "h_lite", seg=8, axis="Y")


def incinerator(m, Z):
    """Incinerator: a square firebox with a fire door, and a tall tapering chimney on it."""
    neck(m, Z, 0.46, 0.41, 0.06)
    bx(m, (-0.38, 0.38), (-0.34, 0.34), (Z + 0.04, Z + 0.36), T, bevel=0.03)
    frustum(m, ((-0.27, 0.27), (-0.25, 0.25)), ((-0.15, 0.15), (-0.15, 0.15)), Z + 0.34, Z + 1.36, G)
    for k in range(3):
        z = Z + 0.58 + k * 0.28
        a = 0.27 - (z - Z - 0.34) / 1.02 * 0.12 + 0.012
        bx(m, (-a, a), (-a + 0.02, a - 0.02), (z - 0.025, z + 0.025), D, bevel=0.0)
    bx(m, (-0.18, 0.18), (-0.18, 0.18), (Z + 1.34, Z + 1.44), D, bevel=0.025)
    m.box((0.24, 0.24, 0.012), (0, 0, Z + 1.442), SLIT)
    for d in SIDES:
        m.box((0.30, 0.012, 0.16), (0, d * 0.342, Z + 0.20), "h_glow")
        for k in range(4):
            m.box((0.022, 0.03, 0.16), (-0.105 + k * 0.07, d * 0.352, Z + 0.20), TD)
        for sz in SIDES:
            m.box((0.38, 0.04, 0.035), (0, d * 0.35, Z + 0.20 + sz * 0.095), D)


def windturbine(m):
    """Wind turbine, 1x1: a tapering mast, a nacelle, three blades."""
    octa(m, 0.34, 0.34, 0.0, 0.09, T)
    octa(m, 0.26, 0.17, 0.06, 0.34, G)
    m.cyl(0.13, 1.90, (0, 0, 1.25), G, seg=8, r2=0.075)
    bx(m, (-0.13, 0.13), (-0.26, 0.20), (2.14, 2.38), G, bevel=0.04)
    m.cyl(0.10, 0.12, (0, -0.31, 2.26), D, seg=8, axis="Y")
    m.cyl(0.0, 0.10, (0, -0.42, 2.26), D, seg=8, axis="Y", r2=0.08)
    for k in range(3):
        a = math.pi / 2 + k * 2 * math.pi / 3
        c, s = math.cos(a), math.sin(a)
        pts = [(r * c - w * s, 2.26 + r * s + w * c) for r, w in ((0.08, -0.05), (0.30, -0.09), (1.05, -0.025), (1.05, 0.02), (0.28, 0.05), (0.08, 0.04))]
        m.prism(pts, -0.335, -0.305, "Y", "h_white")


def solar(m):
    """Solar panel, 2x2: a glazed array tilted to the sun on a frame, with its inverter behind."""
    for sx in SIDES:
        for y, h in ((-0.70, 0.30), (0.70, 0.80)):
            bx(m, tuple(sorted((sx * 0.62, sx * 0.74))), (y - 0.06, y + 0.06), (0.0, h), D, bevel=0.02)
            bx(m, tuple(sorted((sx * 0.56, sx * 0.80))), (y - 0.11, y + 0.11), (0.0, 0.07), T, bevel=0.025)
        m.prism([(-0.70, 0.22), (0.70, 0.72), (0.70, 0.80), (-0.70, 0.30)], *sorted((sx * 0.63, sx * 0.73)), "X", D)
    m.prism([(-0.93, 0.21), (0.93, 0.88), (0.93, 0.95), (-0.93, 0.28)], -0.96, 0.96, "X", G)
    m.prism([(-0.89, 0.292), (0.89, 0.932), (0.89, 0.952), (-0.89, 0.312)], -0.92, 0.92, "X", "h_solar")
    for x in (-0.46, 0.0, 0.46):
        m.prism([(-0.89, 0.297), (0.89, 0.937), (0.89, 0.957), (-0.89, 0.317)], x - 0.012, x + 0.012, "X", "h_glass")
    for k in range(1, 4):
        y = -0.89 + k * 0.445
        z = 0.312 + (y + 0.89) / 1.78 * 0.64
        m.prism([(y - 0.012, z - 0.002), (y + 0.012, z + 0.006), (y + 0.012, z + 0.012), (y - 0.012, z + 0.004)], -0.92, 0.92, "X", "h_glass")
    bx(m, (-0.22, 0.22), (0.72, 0.94), (0.0, 0.46), G, bevel=0.035)
    m.box((0.26, 0.012, 0.10), (0, 0.943, 0.30), "h_core")


def battery(m):
    """Battery, 1x1: a banded cell with two terminals on top and a charge gauge in each side."""
    bx(m, (-0.44, 0.44), (-0.38, 0.38), (0.0, 0.10), T, bevel=0.03)
    bx(m, (-0.40, 0.40), (-0.34, 0.34), (0.06, 0.88), G, bevel=0.04)
    for z in (0.26, 0.74):
        bx(m, (-0.415, 0.415), (-0.355, 0.355), (z - 0.03, z + 0.03), D, bevel=0.0)
    bx(m, (-0.34, 0.34), (-0.28, 0.28), (0.86, 0.93), D, bevel=0.02)
    for sx, mk in ((-1, "h_red"), (1, T)):
        m.cyl(0.085, 0.14, (sx * 0.18, 0, 0.99), "h_lite", seg=8)
        m.cyl(0.10, 0.05, (sx * 0.18, 0, 1.075), mk, seg=8)
    for d in SIDES:
        y = d * 0.342
        m.box((0.40, 0.012, 0.34), (0, y, 0.50), SLIT)
        for k in range(4):
            m.box((0.34, 0.014, 0.055), (0, y + d * 0.002, 0.385 + k * 0.077), "h_paint" if k < 3 else TD)
        for sz in SIDES:
            m.box((0.47, 0.035, 0.035), (0, y + d * 0.008, 0.50 + sz * 0.19), T)
        for sx in SIDES:
            m.box((0.035, 0.035, 0.38), (sx * 0.218, y + d * 0.008, 0.50), T)


def pole(m):
    """Power pole, 1x1: a timber mast with a braced cross arm and three insulators."""
    bx(m, (-0.20, 0.20), (-0.20, 0.20), (0.0, 0.10), T, bevel=0.03)
    m.box((0.13, 0.13, 2.30), (0, 0, 1.15), "h_wood")
    m.box((1.10, 0.11, 0.11), (0, 0, 2.04), "h_wood")
    for sx in SIDES:
        m.prism([(sx * 0.05, 1.62), (sx * 0.11, 1.62), (sx * 0.46, 1.99), (sx * 0.40, 1.99)], -0.03, 0.03, "Y", D)
    for x in (-0.44, 0.0, 0.44):
        z = 2.095 if x else 2.30
        m.cyl(0.035, 0.06, (x, 0, z + 0.03), D, seg=8)
        m.cyl(0.065, 0.05, (x, 0, z + 0.085), "h_white", seg=8)
        m.cyl(0.05, 0.05, (x, 0, z + 0.135), "h_white", seg=8)


stub("generator", generator, flow=-1, fit=lambda m, d, yp, z: strip(m, d, yp, z, "h_oil"))
stub("incinerator", incinerator, flow=-1, fit=lambda m, d, yp, z: peep(m, d, yp, 0, z))
free("windturbine", (1, 1), windturbine, items=False)
free("solar", (2, 2), solar, items=False)
free("battery", (1, 1), battery, items=False)
free("pole", (1, 1), pole, items=False)
