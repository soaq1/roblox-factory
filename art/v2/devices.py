# v2 devices: things that move items by falling, blowing, lifting and throwing, and things that sense
# and decide.
import math
from .d import *          # noqa: F401,F403
from .d import stub, free, run, chev, neck, hatch, lever, lamps, frustum, K


def funnel(m, Z):
    """Funnel: a wide hopper on the deck. Whatever is thrown in comes out along the belt."""
    neck(m, Z, 0.46, 0.41, 0.06)
    frustum(m, ((-0.22, 0.22), (-0.20, 0.20)), ((-0.48, 0.48), (-0.46, 0.46)), Z + 0.04, Z + 0.52, G)
    for s in SIDES:
        m.box((1.00, 0.06, 0.07), (0, s * 0.455, Z + 0.52), D)
        m.box((0.06, 0.92, 0.07), (s * 0.475, 0, Z + 0.52), D)
        m.prism([(s * 0.30, Z + 0.06), (s * 0.34, Z + 0.06), (s * 0.455, Z + 0.47), (s * 0.415, Z + 0.47)], -0.03, 0.03, "Y", D)
    m.box((0.88, 0.84, 0.012), (0, 0, Z + 0.522), SLIT)
    m.box((0.50, 0.46, 0.012), (0, 0, Z + 0.526), "h_belt")


def chute(m):
    """Drop chute, 2x1: an open trough on two trestles, down which items slide from one cell up to
    the level of a belt."""
    m.prism([(-1, 1.25), (1, 0.33), (1, 0.27), (-1, 1.19)], -0.30, 0.30, "Y", RD)
    for s in SIDES:
        a, b = sorted((s * 0.30, s * 0.38))
        m.prism([(-1, 1.43), (1, 0.51), (1, 0.27), (-1, 1.19)], a, b, "Y", R)
    for x, h in ((-0.72, 1.07), (0.30, 0.60)):
        for s in SIDES:
            bx(m, (x - 0.055, x + 0.055), tuple(sorted((s * 0.26, s * 0.37))), (0.0, h), D, bevel=0.02)
            bx(m, (x - 0.10, x + 0.10), tuple(sorted((s * 0.22, s * 0.42))), (0.0, 0.08), T, bevel=0.025)
        m.box((0.07, 0.56, 0.07), (x, 0, h * 0.55), D)


def blower(m):
    """Blower, 1x1: a fan in an eight-sided shroud on a pedestal."""
    bx(m, (-0.44, 0.44), (-0.34, 0.34), (0.0, 0.10), T, bevel=0.03)
    bx(m, (-0.36, 0.36), (-0.28, 0.28), (0.06, 0.40), G, bevel=0.04)
    m.cyl(0.42 * K, 0.36, (0, 0, 0.80), G, seg=8, axis="Y", rot=(0, rad(22.5), 0))
    m.cyl(0.45 * K, 0.07, (0, -0.16, 0.80), D, seg=8, axis="Y", rot=(0, rad(22.5), 0))
    m.cyl(0.36 * K, 0.372, (0, 0, 0.80), SLIT, seg=8, axis="Y", rot=(0, rad(22.5), 0))
    for s in SIDES:
        gear(m, 0.33, 0.02, (0, s * 0.19, 0.80), "h_lite", teeth=5, root=0.30, base=0.62, tip=0.50)
        m.cyl(0.085, 0.05, (0, s * 0.20, 0.80), T, seg=8, axis="Y")


def lift(m, Z):
    """Lift: a chain of buckets runs up an open tower and tips out of a spout at the top, two cells
    up."""
    neck(m, Z, 0.46, 0.41, 0.06)
    for sx in SIDES:
        for sy in SIDES:
            m.box((0.09, 0.09, 1.32), (sx * 0.36, sy * 0.32, Z + 0.70), G)
        bx(m, tuple(sorted((sx * 0.31, sx * 0.41))), (-0.37, 0.37), (Z + 0.60, Z + 0.69), D, bevel=0.02)
    bx(m, (-0.43, 0.43), (-0.39, 0.39), (Z + 1.30, Z + 1.56), G, bevel=0.04)
    m.box((0.10, 0.44, 1.30), (0.0, 0, Z + 0.68), "h_belt")
    for k in range(4):
        bx(m, (-0.22, -0.04), (-0.19, 0.19), (Z + 0.14 + k * 0.30, Z + 0.28 + k * 0.30), T, bevel=0.02)
    m.prism([(-0.43, Z + 1.32), (-0.50, Z + 1.24), (-0.50, Z + 1.14), (-0.43, Z + 1.16)], -0.24, 0.24, "Y", D)


def launcher(m, Z):
    """Launcher: a sprung carriage on an inclined rail throws the item up and away."""
    neck(m, Z, 0.46, 0.41, 0.06)
    for s in SIDES:
        a, b = sorted((s * 0.20, s * 0.30))
        m.prism([(0.40, Z + 0.04), (0.46, Z + 0.04), (-0.40, Z + 0.86), (-0.46, Z + 0.78), (-0.46, Z + 0.70)], a, b, "Y", G)
        m.prism([(-0.30, Z + 0.04), (-0.20, Z + 0.04), (-0.20, Z + 0.52), (-0.30, Z + 0.62)], a, b, "Y", D)
    m.prism([(0.38, Z + 0.07), (-0.42, Z + 0.81), (-0.44, Z + 0.77), (0.36, Z + 0.03)], -0.20, 0.20, "Y", RD)
    m.prism([(0.10, Z + 0.37), (-0.06, Z + 0.52), (0.02, Z + 0.62), (0.18, Z + 0.47)], -0.17, 0.17, "Y", T)
    for k in range(4):
        x = 0.36 - k * 0.06
        m.prism([(x, Z + 0.12 + k * 0.055), (x - 0.03, Z + 0.15 + k * 0.055), (x + 0.05, Z + 0.24 + k * 0.055),
                 (x + 0.08, Z + 0.21 + k * 0.055)], -0.10, 0.10, "Y", "h_red")


def arch(m, zt, hx=0.08, mk=G):
    """A slim arch over a belt cell, standing on its rails. Returns the height of the beam's underside."""
    for s in SIDES:
        bx(m, (-hx - 0.03, hx + 0.03), tuple(sorted((s * 0.34, s * 0.50))), (0.0, 0.40), mk, bevel=0.03)
        bx(m, (-hx, hx), tuple(sorted((s * 0.35, s * 0.47))), (0.36, zt), mk, bevel=0.025)
    bx(m, (-hx - 0.01, hx + 0.01), (-0.48, 0.48), (zt - 0.04, zt + 0.10), mk, bevel=0.03)
    return zt - 0.04


def sensor(m):
    """Sensor, 1x1: an eye on an arch looks down at the belt."""
    run(m, -0.5, 0.5)
    z = arch(m, 0.92)
    m.cyl(0.11, 0.08, (0, 0, z - 0.04), T, seg=10)
    m.cyl(0.07, 0.03, (0, 0, z - 0.085), "h_core", seg=10)


def gate(m):
    """Gate, 1x1: a door slides down between two posts and stops the belt's load."""
    run(m, -0.5, 0.5)
    z = arch(m, 1.16, hx=0.10)
    bx(m, (-0.035, 0.035), (-0.335, 0.335), (0.56, z + 0.02), T, bevel=0.0)
    m.box((0.08, 0.50, 0.05), (0, 0, 0.585), D)
    bx(m, (-0.13, 0.13), (-0.15, 0.15), (z + 0.12, z + 0.30), D, bevel=0.03)


def counter(m):
    """Counter, 1x1: an arch with a number board on top that counts what passes."""
    run(m, -0.5, 0.5)
    z = arch(m, 0.90)
    bx(m, (-0.11, 0.11), (-0.40, 0.40), (z + 0.12, z + 0.50), D, bevel=0.03)
    for sx in SIDES:
        x = sx * 0.112
        m.box((0.012, 0.66, 0.26), (x, 0, z + 0.31), SLIT)
        for yc in (-0.17, 0.17):
            for dz in (-0.09, 0.0, 0.09):
                m.box((0.016, 0.16, 0.026), (x + sx * 0.002, yc, z + 0.31 + dz), "h_core")
            for dy in (-0.085, 0.085):
                m.box((0.016, 0.026, 0.21), (x + sx * 0.002, yc + dy, z + 0.31), "h_core")


def switch(m):
    """Switch, 1x1: a big lever in a slotted box."""
    bx(m, (-0.36, 0.36), (-0.28, 0.28), (0.0, 0.09), T, bevel=0.03)
    bx(m, (-0.32, 0.32), (-0.24, 0.24), (0.05, 0.40), G, bevel=0.04)
    m.box((0.44, 0.07, 0.02), (0, 0, 0.405), SLIT)
    for s in SIDES:
        m.box((0.50, 0.04, 0.05), (0, s * 0.065, 0.415), D)
    m.box((0.07, 0.05, 0.56), (0.07, 0, 0.62), "h_lite", rot=(0, rad(22), 0))
    m.cyl(0.085, 0.13, (0.175, 0, 0.88), "h_red", seg=8, rot=(0, rad(22), 0))
    m.cyl(0.07, 0.30, (0, 0, 0.38), D, seg=8, axis="Y")


def logic(m):
    """Logic box, 1x1: a block with one big chip on it, legs down both sides, and a light on top."""
    bx(m, (-0.40, 0.40), (-0.40, 0.40), (0.0, 0.09), T, bevel=0.03)
    bx(m, (-0.36, 0.36), (-0.36, 0.36), (0.05, 0.36), G, bevel=0.04)
    bx(m, (-0.24, 0.24), (-0.20, 0.20), (0.40, 0.54), D, bevel=0.02)
    for s in SIDES:
        for k in range(4):
            x = -0.18 + k * 0.12
            m.box((0.05, 0.05, 0.04), (x, s * 0.23, 0.45), "h_lite")
            m.box((0.05, 0.04, 0.12), (x, s * 0.26, 0.40), "h_lite")
    m.cyl(0.07, 0.03, (-0.12, 0, 0.545), T, seg=10)
    m.cyl(0.045, 0.012, (-0.12, 0, 0.553), "h_core", seg=10)


def beacon(m):
    """Signal light, 1x1: a lamp in a cage on a post."""
    octa(m, 0.30, 0.30, 0.0, 0.08, T)
    octa(m, 0.24, 0.16, 0.06, 0.26, G)
    m.cyl(0.075, 0.70, (0, 0, 0.60), G, seg=8)
    octa(m, 0.17, 0.17, 0.93, 1.00, D)
    octa(m, 0.115, 0.115, 1.00, 1.24, "h_glow")
    k = 0.145
    for sx in SIDES:
        for sy in SIDES:
            m.box((0.035, 0.035, 0.26), (sx * k, sy * k, 1.12), D)
    octa(m, 0.19, 0.10, 1.24, 1.34, D)


def timer(m):
    """Timer, 1x1: a clock face on a stout post."""
    bx(m, (-0.34, 0.34), (-0.26, 0.26), (0.0, 0.09), T, bevel=0.03)
    bx(m, (-0.14, 0.14), (-0.12, 0.12), (0.05, 0.62), G, bevel=0.035)
    m.cyl(0.36, 0.20, (0, 0, 0.92), G, seg=12, axis="Y")
    for s in SIDES:
        m.cyl(0.30, 0.012, (0, s * 0.097, 0.92), "h_white", seg=12, axis="Y")
        m.cyl(0.37, 0.03, (0, s * 0.095, 0.92), D, seg=12, axis="Y")
        m.cyl(0.30, 0.034, (0, s * 0.094, 0.92), "h_white", seg=12, axis="Y")
        m.box((0.035, 0.014, 0.22), (0, s * 0.114, 1.02), T)
        m.box((0.16, 0.014, 0.035), (0.07, s * 0.114, 0.92), T)
        m.cyl(0.035, 0.02, (0, s * 0.116, 0.92), T, seg=8, axis="Y")


def sign(m):
    """Sign, 1x1: a framed board on two posts."""
    for sx in SIDES:
        m.box((0.09, 0.09, 1.20), (sx * 0.36, 0, 0.60), "h_wood")
        bx(m, tuple(sorted((sx * 0.28, sx * 0.44))), (-0.10, 0.10), (0.0, 0.08), T, bevel=0.025)
    bx(m, (-0.46, 0.46), (-0.045, 0.045), (0.58, 1.16), "h_wood_l", bevel=0.02)
    for s in SIDES:
        for k, w in enumerate((0.62, 0.44, 0.54)):
            m.box((w, 0.012, 0.045), (0, s * 0.048, 1.00 - k * 0.13), "h_wood")


stub("funnel", funnel, fit=lambda m, d, yp, z: hatch(m, d, yp, 0, z))
free("chute", (2, 1), chute, items=False)
free("blower", (1, 1), blower, items=False)
stub("lift", lift, flow=-1, fit=lambda m, d, yp, z: lamps(m, d, yp, z))
stub("launcher", launcher, flow=-1, fit=lambda m, d, yp, z: lever(m, d, yp, 0, z))
free("sensor", (1, 1), sensor, items=False)
free("gate", (1, 1), gate, items=False)
free("counter", (1, 1), counter, items=False)
free("switch", (1, 1), switch, items=False)
free("logic", (1, 1), logic, items=False)
free("beacon", (1, 1), beacon, items=False)
free("timer", (1, 1), timer, items=False)
free("sign", (1, 1), sign, items=False)
