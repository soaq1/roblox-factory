# v2 models: machines that make, store and carry electricity (동력).
import math
import factorykit as fk
from factorykit import rad
from .kit import (machine2, bx, on, stub, vent, panel, hexbolt, badge, gauge, buttons, slots, lamp, band,
                  chimney, frame_tower, tank, hopper, skirt, body, HALF, BELT_Z)
from .kit import hull


def insulator(m, x, y, z, n=3):
    for i in range(n):
        m.cyl(0.06 if i % 2 == 0 else 0.04, 0.05, (x, y, z + 0.025 + i * 0.05), "white", seg=6)
    m.cyl(0.03, 0.05, (x, y, z + n * 0.05 + 0.025), "spark", seg=6)


@machine2("generator", (3, 2), (("W", "in", -0.5),))
def generator(m):
    """A firebox, a boiler drum and a dynamo wound with copper, on one bed."""
    with m.at((-0.5, -0.5, 0)):
        stub(m, 0.0, -1, 1.0, "in")
    bx(m, (-0.5, 1.46), (-0.96, 0.96), (0.0, 0.14), "g4")
    # firebox, where the fuel comes in
    hull(m, (-0.5, 0.36), (-0.94, -0.06), 1.04, z0=0.14)
    band(m, (-0.5, 0.36), (-0.94, -0.06), 1.04, t=0.08)
    with on(m, "S", -0.07, -0.94, 0.56):
        slots(m, 0.52, 0.30, 5)
    chimney(m, -0.20, -0.50, 1.12, 1.00, r=0.13, glow=True)
    # boiler drum along the back
    for x in (-0.20, 1.10):
        bx(m, (x - 0.07, x + 0.07), (0.16, 0.84), (0.14, 0.50), "g3")
    m.cyl(0.42, 1.80, (0.46, 0.50, 0.80), "tankc", seg=10, axis="X")
    for x in (-0.24, 0.46, 1.16):
        m.cyl(0.44, 0.08, (x, 0.50, 0.80), "tank_dark", seg=10, axis="X")
    m.cyl(0.10, 0.20, (0.46, 0.50, 1.28), "g3", seg=8)
    m.cyl(0.13, 0.05, (0.46, 0.50, 1.40), "red", seg=8)
    m.pipe([(0.10, 0.50, 1.20), (0.10, 0.50, 1.40), (0.10, -0.30, 1.40), (0.10, -0.30, 1.12)], 0.05, "g1", seg=6)
    # dynamo
    for y in (-0.80, -0.22):
        bx(m, (0.66, 1.34), (y - 0.04, y + 0.04), (0.14, 0.60), "g3")
    m.cyl(0.40, 0.50, (1.00, -0.51, 0.62), "g2", seg=12, axis="Y")
    for y in (-0.66, -0.51, -0.36):
        m.cyl(0.43, 0.07, (1.00, y, 0.62), "copper", seg=12, axis="Y")
    m.cyl(0.14, 0.08, (1.00, -0.80, 0.62), "red", seg=8, axis="Y")
    m.pipe([(0.36, -0.50, 0.62), (0.60, -0.50, 0.62)], 0.06, "g5", seg=6)
    insulator(m, 0.80, -0.36, 1.00)
    insulator(m, 1.20, -0.36, 1.00)
    with on(m, "S", 1.00, -0.84, 0.30):
        gauge(m, 0.09)


@machine2("incinerator", (2, 1), (("W", "in", 0),))
def incinerator(m):
    """A burn chamber with a hooded top and a tall flue."""
    stub(m, 0.0, -1, 1.0, "in")
    with m.at((0.5, 0, 0)):
        T = body(m, 0.96)
        bx(m, (-0.40, 0.40), (-0.36, 0.36), (T, T + 0.30), "g3", taper=0.62)
        bx(m, (-0.27, 0.27), (-0.24, 0.24), (T + 0.30, T + 0.36), "g4")
        chimney(m, 0, 0, T + 0.36, 1.10, r=0.14, seg=8, glow=True)
        with on(m, "S", 0.0, -0.44, 0.54):
            slots(m, 0.52, 0.40, 5)
        with on(m, "E", 0.50, 0.0, 0.54):
            vent(m, 0.44, 0.34, 5)
        skirt(m, (-0.40, 0.40), y=-0.5, depth=0.06, h=0.16)
        for x in (-0.36, 0.36):
            m.cyl(0.03, 0.03, (x, -0.455, 0.86), "g1", seg=6, axis="Y")


@machine2("windturbine", (1, 1), items=False)
def windturbine(m):
    """A tapering mast, a nacelle and three long blades."""
    m.cyl(0.38, 0.14, (0, 0, 0.07), "g4", seg=8)
    m.cyl(0.26, 0.20, (0, 0, 0.24), "g2", seg=8)
    m.cyl(0.16, 2.80, (0, 0, 1.74), "g1", seg=8, r2=0.09)
    for z in (1.10, 2.10):
        m.cyl(0.15, 0.05, (0, 0, z), "g3", seg=8)
    with m.at((0, 0, 3.24), rad(45)):
        m.box((0.26, 0.60, 0.26), (0, 0.08, 0), "g2")
        m.box((0.28, 0.20, 0.28), (0, 0.30, 0), "g4")
        m.cyl(0.11, 0.16, (0, -0.30, 0), "red", seg=8, axis="Y")
        for k in range(3):
            a = k * 2 * math.pi / 3 + 0.35
            m.box((0.17, 0.035, 1.24), (math.sin(a) * 0.68, -0.32, math.cos(a) * 0.68), "white", rot=(0, a, 0))
            m.box((0.10, 0.04, 0.30), (math.sin(a) * 0.20, -0.32, math.cos(a) * 0.20), "g3", rot=(0, a, 0))


@machine2("solar", (2, 2), items=False)
def solar(m):
    """A tilted array of dark cells on a frame."""
    t = rad(28)
    for x in (-0.76, 0.76):
        bx(m, (x - 0.05, x + 0.05), (-0.62, -0.52), (0.0, 0.34), "g3")
        bx(m, (x - 0.05, x + 0.05), (0.52, 0.62), (0.0, 0.96), "g3")
        m.box((0.24, 0.24, 0.05), (x, -0.57, 0.025), "g4")
        m.box((0.24, 0.24, 0.05), (x, 0.57, 0.025), "g4")
        m.box((0.05, 1.20, 0.05), (x, 0.0, 0.40), "g3", rot=(rad(-18), 0, 0))
    zc = 0.72
    m.box((1.86, 1.56, 0.07), (0, 0, zc), "g2", rot=(t, 0, 0))
    for i in range(4):
        for j in range(3):
            u, v = -0.675 + i * 0.45, -0.48 + j * 0.48
            m.box((0.41, 0.44, 0.03), (u, v * math.cos(t) - 0.05 * math.sin(t), zc + v * math.sin(t) + 0.05 * math.cos(t)),
                  "solar", rot=(t, 0, 0))
    bx(m, (0.50, 0.80), (0.30, 0.56), (0.0, 0.34), "g2")
    bx(m, (0.47, 0.83), (0.27, 0.59), (0.34, 0.39), "g4")
    insulator(m, 0.65, 0.43, 0.39, n=2)


@machine2("battery", (1, 1), items=False)
def battery(m):
    """A bank of cells with two terminals and a charge meter."""
    bx(m, (-0.46, 0.46), (-0.40, 0.40), (0.0, 0.12), "g4")
    for x in (-0.29, 0.0, 0.29):
        bx(m, (x - 0.13, x + 0.13), (-0.36, 0.36), (0.12, 0.90), "g2")
        bx(m, (x - 0.14, x + 0.14), (-0.37, 0.37), (0.74, 0.82), "spark")
    band(m, (-0.42, 0.42), (-0.36, 0.36), 0.90, t=0.07)
    for x, c in ((-0.22, "red"), (0.22, "g5")):
        m.cyl(0.08, 0.14, (x, 0.0, 1.04), c, seg=8)
        m.cyl(0.05, 0.06, (x, 0.0, 1.14), "g1", seg=8)
    m.box((0.50, 0.05, 0.05), (0.0, 0.0, 1.14), "copper")
    with on(m, "S", 0.0, -0.36, 0.44):
        m.box((0.56, 0.03, 0.26), (0, -0.015, 0), "g5")
        for i in range(5):
            m.box((0.08, 0.02, 0.18), (-0.20 + i * 0.10, -0.036, 0), "lampg" if i < 3 else "g4")


@machine2("pole", (1, 1), items=False)
def pole(m):
    """A timber pole with two crossarms, insulators and a transformer can."""
    m.cyl(0.24, 0.12, (0, 0, 0.06), "g4", seg=8)
    bx(m, (-0.07, 0.07), (-0.07, 0.07), (0.12, 3.10), "wood_dark")
    bx(m, (-0.06, 0.06), (-0.66, 0.66), (2.70, 2.80), "wood")
    bx(m, (-0.06, 0.06), (-0.44, 0.44), (2.28, 2.37), "wood")
    for y in (-0.58, 0.0, 0.58):
        insulator(m, 0.0, y, 2.80 if y else 3.10)
    for y in (-0.38, 0.38):
        insulator(m, 0.0, y, 2.37, n=2)
    for s in (-1, 1):
        m.box((0.04, 0.50, 0.04), (0.0, s * 0.24, 2.52), "wood", rot=(rad(s * 38), 0, 0))
    m.cyl(0.16, 0.44, (0.22, 0.0, 1.86), "g2", seg=8)
    m.cyl(0.18, 0.05, (0.22, 0.0, 2.10), "g4", seg=8)
    m.box((0.10, 0.10, 0.10), (0.10, 0.0, 1.86), "g5")
    m.box((0.02, 0.10, 0.14), (0.385, 0.0, 1.86), "spark")
