# v2 machines with a side port: those that take a second material and those that give a second product.
# All are 3x1 through machines; the second material goes in, or the second product comes out, by a mouth
# in the side wall, and there is one in each side wall so either side will do.
import math
from . import pairs as _pairs
from .base import hex_stack
from .works import ring_pipe
from .d import *          # noqa: F401,F403
from .d import through, neck, K


def refinery(m, Z):
    """Refinery: a tall banded column on a reboiler drum. A pipe leaves the column each side and runs
    down into a receiver."""
    neck(m, Z, 0.44, 0.40, 0.05)
    octa(m, 0.33, 0.33, Z + 0.03, Z + 0.26, G)
    octa(m, 0.345, 0.345, Z + 0.20, Z + 0.26, D)
    octa(m, 0.21, 0.21, Z + 0.26, Z + 1.30, G)
    for z in (Z + 0.55, Z + 0.85, Z + 1.15):
        octa(m, 0.235, 0.235, z - 0.03, z + 0.03, D)
    octa(m, 0.21, 0.11, Z + 1.30, Z + 1.42, D)
    m.cyl(0.07, 0.12, (0, 0, Z + 1.48), G, seg=8)
    for d in SIDES:
        side_pipe(m, 0.0, [(d * 0.19, Z + 1.00), (d * 0.37, Z + 1.00), (d * 0.37, Z + 0.24)], r=0.045, mk=W)
        m.cyl(0.062, 0.03, (0, d * 0.225, Z + 1.00), D, seg=8, axis="Y")
        m.cyl(0.062, 0.03, (0, d * 0.37, Z + 0.27), D, seg=8)


def recycler(m, Z):
    """Recycler: two toothed shafts turn against each other in an open bin, and a lifting magnet hangs
    over it from a beam."""
    neck(m, Z, 0.46, 0.40, 0.05)
    for s in SIDES:
        bx(m, (-0.47, 0.47), tuple(sorted((s * 0.34, s * 0.41))), (Z + 0.02, Z + 0.40), G, bevel=0.025)
        bx(m, tuple(sorted((s * 0.40, s * 0.47))), (-0.41, 0.41), (Z + 0.02, Z + 0.40), G, bevel=0.025)
        gear(m, 0.165, 0.66, (s * 0.165, 0, Z + 0.22), T, teeth=6, root=0.60, base=0.50, tip=0.24, half_step=s > 0)
        bx(m, tuple(sorted((s * 0.39, s * 0.47))), (-0.09, 0.09), (Z + 0.38, Z + 0.92), G, bevel=0.025)
    m.box((0.80, 0.68, 0.03), (0, 0, Z + 0.06), SLIT)
    bx(m, (-0.47, 0.47), (-0.10, 0.10), (Z + 0.86, Z + 1.00), G, bevel=0.035)
    m.cyl(0.03, 0.26, (0, 0, Z + 0.74), "h_lite", seg=8)
    m.cyl(0.15, 0.08, (0, 0, Z + 0.60), D, seg=12)
    m.cyl(0.11, 0.03, (0, 0, Z + 0.655), T, seg=12)


def sieve(m, Z):
    """Sieve: a screen pitched like a roof between two gable ends. What passes drops through to the
    belt; what does not slides off either side."""
    neck(m, Z, 0.46, 0.40, 0.05)
    bx(m, (-0.38, 0.38), (-0.30, 0.30), (Z + 0.02, Z + 0.20), D, bevel=0.03)
    for sx in SIDES:
        a, b = sorted((sx * 0.38, sx * 0.47))
        m.prism([(-0.44, Z + 0.02), (0.44, Z + 0.02), (0.44, Z + 0.26), (0.0, Z + 0.60), (-0.44, Z + 0.26)], a, b, "X", G)
    for s in SIDES:
        m.prism([(0.0, Z + 0.50), (s * 0.44, Z + 0.16), (s * 0.44, Z + 0.12), (0.0, Z + 0.46)], -0.38, 0.38, "X", SLIT)
        for i in range(4):
            y0 = 0.06 + i * 0.10
            z0 = Z + 0.50 - (y0 / 0.44) * 0.34
            m.prism([(s * y0, z0 + 0.012), (s * (y0 + 0.03), z0 - 0.011), (s * (y0 + 0.03), z0 - 0.04), (s * y0, z0 - 0.017)],
                    -0.38, 0.38, "X", G)
    m.cyl(0.075, 0.36, (0, 0, Z + 0.56), T, seg=8, axis="X")
    for sx in SIDES:
        m.cyl(0.095, 0.04, (sx * 0.17, 0, Z + 0.56), D, seg=8, axis="X")


def blast(m, Z):
    """Blast furnace: a dark hearth, a stack that draws in as it climbs to a bell at the top, and a gas
    main that leaves one shoulder, arches over the top and comes down to the other."""
    octa(m, 0.41, 0.41, Z - 0.02, Z + 0.24, T)
    oct_ring(m, 0.44, 0.10, Z + 0.22, Z + 0.31, D)
    octa(m, 0.41, 0.25, Z + 0.28, Z + 1.10, G)
    for z in (Z + 0.52, Z + 0.80):
        a = 0.41 - (z - (Z + 0.28)) / 0.82 * 0.16
        octa(m, a + 0.022, a + 0.010, z - 0.028, z + 0.028, D)
    oct_ring(m, 0.29, 0.08, Z + 1.07, Z + 1.16, D)
    octa(m, 0.22, 0.11, Z + 1.12, Z + 1.26, G)
    m.pipe([(-0.27, 0, Z + 0.86), (-0.27, 0, Z + 1.34), (-0.12, 0, Z + 1.52), (0.12, 0, Z + 1.52), (0.27, 0, Z + 1.34),
            (0.27, 0, Z + 0.86)], 0.05, W, seg=8)
    for sx in SIDES:
        m.cyl(0.07, 0.035, (sx * 0.27, 0, Z + 0.90), D, seg=8)
        for k in range(3):                                    # tuyere peepholes in the hearth, lit from within
            y = (k - 1) * 0.11
            m.box((0.012, 0.055, 0.075), (sx * 0.412, y, Z + 0.10), "h_glow")
        m.box((0.03, 0.36, 0.03), (sx * 0.418, 0, Z + 0.155), TD)
        m.box((0.03, 0.36, 0.03), (sx * 0.418, 0, Z + 0.045), TD)


def assembler(m, Z):
    """Assembler: two arms on the roof work on a part held on a turntable between them."""
    neck(m, Z, 0.45, 0.40)
    octa(m, 0.19, 0.19, Z + 0.05, Z + 0.13, D)
    m.box((0.20, 0.18, 0.10), (0, 0, Z + 0.18), "h_steel", bevel=0.02)
    m.box((0.12, 0.08, 0.06), (0, 0, Z + 0.26), "h_lite")
    for d in SIDES:
        _pairs.arm(m, d, (0.29, Z + 0.06), (0.25, Z + 0.72), (0.085, Z + 0.43))


def circuit(m, Z):
    """Circuit maker: a board lies on a flat bed and a head rides over it on a bridge."""
    bx(m, (-0.46, 0.46), (-0.40, 0.40), (Z - 0.02, Z + 0.15), G, bevel=0.035)
    m.box((0.62, 0.44, 0.02), (0, 0, Z + 0.16), "h_pcb")
    for y in (-0.13, 0.0, 0.13):
        m.box((0.50, 0.018, 0.006), (0, y, Z + 0.172), "h_oil")
    for d in SIDES:
        m.box((0.90, 0.06, 0.08), (0, d * 0.35, Z + 0.19), D)
        bx(m, (-0.08, 0.08), tuple(sorted((d * 0.29, d * 0.42))), (Z + 0.20, Z + 0.58), G, bevel=0.025)
    bx(m, (-0.09, 0.09), (-0.43, 0.43), (Z + 0.50, Z + 0.63), G, bevel=0.03)
    bx(m, (-0.13, 0.13), (-0.11, 0.11), (Z + 0.36, Z + 0.70), T, bevel=0.03)
    m.cyl(0.02, 0.14, (0, 0, Z + 0.29), "h_lite", seg=8, r2=0.06)


def oven(m, Z):
    """Oven: a banded vault with a mouth at each end, the fire glowing inside behind its bars, and a
    flue on the crown."""
    neck(m, Z, 0.46, 0.41, 0.05)
    vault = [(-0.40, Z + 0.02), (-0.40, Z + 0.24), (-0.25, Z + 0.46), (0.25, Z + 0.46), (0.40, Z + 0.24), (0.40, Z + 0.02)]
    m.prism(vault, -0.44, 0.44, "X", G)
    big = [(y * 1.04, Z + 0.02 + (z - Z - 0.02) * 1.04) for y, z in vault]
    for x in (-0.24, 0.24):
        m.prism(big, x - 0.03, x + 0.03, "X", D)
    for sx in SIDES:
        a, b = sorted((sx * 0.44, sx * 0.47))
        m.prism(arch_pts(0.50, Z + 0.40, hole_top=Z + 0.32, hw=0.17, c=0.08, ci=0.05), a, b, "X", T)
        m.box((0.012, 0.34, 0.26), (sx * 0.446, 0, Z + 0.19), "h_glow")
        for k in range(3):
            m.box((0.02, 0.34, 0.022), (sx * 0.462, 0, Z + 0.09 + k * 0.075), TD)
    hex_stack(m, 0, 0, Z + 0.45, 0.34, r=0.085)


def alloy(m, Z):
    """Alloy furnace: two pots of different metal stand side by side, each pouring down a short runner
    into the well between them."""
    neck(m, Z, 0.46, 0.40, 0.05)
    for sx in SIDES:
        with m.at((sx * 0.25, 0, 0)):
            octa(m, 0.17, 0.205, Z + 0.04, Z + 0.54, G)
            octa(m, 0.20, 0.20, Z + 0.25, Z + 0.31, D)
            oct_ring(m, 0.225, 0.06, Z + 0.51, Z + 0.58, D)
            octa(m, 0.17, 0.17, Z + 0.50, Z + 0.545, "h_glow" if sx < 0 else "h_oil")
    bx(m, (-0.07, 0.07), (-0.16, 0.16), (Z + 0.02, Z + 0.22), D, bevel=0.02)
    m.box((0.10, 0.24, 0.02), (0, 0, Z + 0.205), "h_glow")
    for s in SIDES:
        m.box((0.03, 0.30, 0.04), (s * 0.06, 0, Z + 0.225), TD)
        m.box((0.15, 0.03, 0.04), (0, s * 0.135, Z + 0.225), TD)


def manufacturer(m, Z):
    """Manufacturer: a works under a saw-tooth roof, each tooth glazed on its upright face."""
    bx(m, (-0.47, 0.47), (-0.42, 0.42), (Z - 0.02, Z + 0.40), G, bevel=0.03)
    for c in (-0.30, 0.0, 0.30):
        m.prism([(c - 0.15, Z + 0.38), (c + 0.15, Z + 0.38), (c - 0.15, Z + 0.66)], -0.42, 0.42, "Y", G)
        m.box((0.012, 0.74, 0.20), (c - 0.153, 0, Z + 0.52), "h_glass")
        for y in (-0.25, 0.0, 0.25):
            m.box((0.02, 0.03, 0.22), (c - 0.156, y, Z + 0.52), D)
        m.box((0.03, 0.86, 0.035), (c - 0.15, 0, Z + 0.655), D)
    for d in SIDES:
        for sx in SIDES:
            m.box((0.20, 0.012, 0.16), (sx * 0.22, d * 0.424, Z + 0.20), "h_glass")
            for sz in SIDES:
                m.box((0.24, 0.03, 0.025), (sx * 0.22, d * 0.428, Z + 0.20 + sz * 0.09), D)
            for k in SIDES:
                m.box((0.025, 0.03, 0.16), (sx * 0.22 + k * 0.11, d * 0.428, Z + 0.20), D)


through("refinery", refinery, sides="out")
through("recycler", recycler, sides="out")
through("sieve", sieve, sides="out")
through("blast", blast, sides="in")
through("assembler", assembler, sides="in")
through("circuit", circuit, sides="in")
through("mixer", lambda m, Z: _pairs.mixer_body(m, Z, walls=False), sides="in")
through("oven", oven, sides="in")
through("alloy", alloy, sides="in")
through("manufacturer", manufacturer, sides="in")
