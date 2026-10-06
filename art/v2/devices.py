# v2 models: devices that move items by physics, devices that decide, and the sign (물리 장치, 판단 장치, 표시).
import math
import factorykit as fk
from factorykit import rad
from .kit import (machine2, bx, on, trough, stub, vent, panel, hexbolt, badge, gauge, buttons, slots, lamp, band,
                  chimney, frame_tower, hopper, skirt, body, rocks, HALF, BELT_Z)

E2_OUT = (("E", "out", 0),)
W2_IN = (("W", "in", 0),)


@machine2("funnel", (2, 1), E2_OUT)
def funnel(m):
    """A wide mouth on legs that catches whatever falls in and sets it on the belt."""
    stub(m, 0.0, 1, 1.0, "out")
    with m.at((-0.5, 0, 0)):
        T = body(m, 0.56, t=0.07)
        for x in (-0.36, 0.36):
            for y in (-0.32, 0.32):
                bx(m, (x - 0.045, x + 0.045), (y - 0.045, y + 0.045), (T, T + 0.34), "g3")
        bx(m, (-0.22, 0.22), (-0.20, 0.20), (T, T + 0.34), "g2")
        hopper(m, 0, 0, T + 0.30, w=0.92, h=0.50, d=0.84)
        with on(m, "S", 0.0, -0.44, 0.32):
            vent(m, 0.40, 0.18, 3)


@machine2("chute", (2, 1), items=False)
def chute(m):
    """A polished slide from one cell up down to belt height. Nothing powers it."""
    m.prism([(-1, 1.05), (1, 0.05), (1, 0.24), (-1, 1.24)], -0.35, 0.35, "Y", "g3")
    m.prism([(-1, 1.24), (1, 0.24), (1, 0.27), (-1, 1.27)], -0.33, 0.33, "Y", "white")
    for s in (-1, 1):
        lo, hi = sorted((s * 0.33, s * 0.42))
        m.prism([(-1, 1.05), (1, 0.05), (1, 0.44), (-1, 1.44)], lo, hi, "Y", "g1")
        lo, hi = sorted((s * 0.42, s * HALF))
        m.prism([(-1, 1.05), (1, 0.05), (1, 0.24), (-1, 1.24)], lo, hi, "Y", "g1")
    bx(m, (-1.0, -0.90), (-0.42, 0.42), (1.20, 1.62), "g2")
    for x in (-0.86, -0.25):
        h = 0.05 + (1 - x) / 2
        for s in (-1, 1):
            m.box((0.09, 0.09, h), (x, s * 0.37, h / 2), "g2")
            m.box((0.20, 0.16, 0.05), (x, s * 0.37, 0.025), "g3")
        m.box((0.06, 0.74, 0.06), (x, 0, h * 0.45), "g3")
    m.box((0.10, 1.0, 0.16), (0.946, 0, 0.08), "g2")


@machine2("blower", (1, 1), items=False)
def blower(m):
    """A fan in a round shroud, motor behind it."""
    bx(m, (-0.42, 0.42), (-0.40, 0.40), (0.0, 0.16), "g4")
    bx(m, (-0.34, 0.24), (-0.30, 0.30), (0.16, 0.44), "g2")
    m.cyl(0.42, 0.30, (0.10, 0, 0.84), "g2", seg=10, axis="X")
    m.cyl(0.46, 0.07, (0.27, 0, 0.84), "g4", seg=10, axis="X")
    m.cyl(0.37, 0.02, (0.30, 0, 0.84), "hole", seg=10, axis="X")
    for k in range(5):
        a = k * 2 * math.pi / 5
        m.box((0.03, 0.12, 0.30), (0.305, math.sin(a) * 0.18, 0.84 + math.cos(a) * 0.18), "g1", rot=(-a, 0, 0))
    m.cyl(0.09, 0.06, (0.33, 0, 0.84), "red", seg=8, axis="X")
    m.cyl(0.22, 0.30, (-0.20, 0, 0.84), "g3", seg=8, axis="X")
    m.cyl(0.24, 0.05, (-0.14, 0, 0.84), "g5", seg=8, axis="X")
    for s in (-1, 1):
        bx(m, (-0.02, 0.18), (s * 0.30 - 0.04, s * 0.30 + 0.04), (0.44, 0.62), "g3")


@machine2("lift", (2, 1), W2_IN)
def lift(m):
    """A vertical belt with shelves inside a frame carries items up two cells and tips them out."""
    stub(m, 0.0, -1, 1.0, "in")
    with m.at((0.5, 0, 0)):
        bx(m, (-0.46, 0.46), (-0.46, 0.46), (0.0, 0.16), "g4")
        bx(m, (-0.44, -0.20), (-0.40, 0.40), (0.16, 0.90), "g2")
        frame_tower(m, (-0.40, 0.40), (-0.40, 0.40), 0.16, (1.10, 2.05, 3.0), post=0.06, beam=0.12)
        bx(m, (-0.06, 0.02), (-0.30, 0.30), (0.20, 2.84), "tread")
        for i in range(6):
            bx(m, (0.02, 0.24), (-0.28, 0.28), (0.44 + i * 0.44, 0.48 + i * 0.44), "g1")
        for z in (0.24, 2.84):
            m.cyl(0.10, 0.66, (-0.02, 0, z), "g5", seg=8, axis="Y")
        m.box((0.56, 0.62, 0.05), (0.42, 0, 2.26), "g1", rot=(0, rad(14), 0))
        for s in (-1, 1):
            m.box((0.56, 0.05, 0.16), (0.42, s * 0.31, 2.30), "g3", rot=(0, rad(14), 0))
        with on(m, "S", -0.32, -0.40, 0.52):
            buttons(m, ("lampg", "red"))


@machine2("launcher", (2, 1), W2_IN)
def launcher(m):
    """A sprung arm on a turntable throws items in an arc."""
    stub(m, 0.0, -1, 1.0, "in")
    with m.at((0.5, 0, 0)):
        bx(m, (-0.5, -0.40), (-0.46, 0.46), (0.0, 0.98), "g2")
        m.cyl(0.47, 0.16, (0, 0, 0.08), "g4", seg=10)
        m.cyl(0.40, 0.34, (0, 0, 0.33), "g2", seg=10)
        m.cyl(0.43, 0.06, (0, 0, 0.53), "g5", seg=10)
        for s in (-1, 1):
            m.prism([(-0.30, 0.56), (0.02, 0.56), (-0.14, 0.98)], min(s * 0.22, s * 0.28), max(s * 0.22, s * 0.28), "Y", "g3")
        m.cyl(0.04, 0.66, (-0.14, 0, 0.94), "g5", seg=6, axis="Y")
        a = rad(-36)
        m.box((1.04, 0.30, 0.07), (0.10, 0, 1.12), "g1", rot=(0, a, 0))
        for s in (-1, 1):
            m.box((1.04, 0.04, 0.14), (0.10, s * 0.17, 1.15), "g3", rot=(0, a, 0))
        m.box((0.10, 0.36, 0.30), (0.50, 0, 1.47), "red", rot=(0, a, 0))
        for i in range(5):
            m.cyl(0.08 if i % 2 == 0 else 0.055, 0.07, (0.22, 0, 0.60 + i * 0.07), "g1", seg=6)


def beltpiece(m):
    trough(m, -0.5, 0.5)


@machine2("sensor", (1, 1), items=False)
def sensor(m):
    """Two posts and a beam of light across the belt."""
    beltpiece(m)
    for s in (-1, 1):
        y = s * 0.44
        bx(m, (-0.07, 0.07), (y - 0.06, y + 0.06), (0.24, 0.98), "g2")
        bx(m, (-0.09, 0.09), (y - 0.08, y + 0.08), (0.98, 1.08), "g5")
        m.box((0.07, 0.03, 0.07), (0, s * 0.37, 0.74), "lampr")
    m.box((0.014, 0.74, 0.014), (0, 0, 0.74), "lampr")
    m.box((0.16, 0.05, 0.12), (0.0, -0.51, 0.52), "g5")
    m.box((0.05, 0.02, 0.05), (0.0, -0.54, 0.52), "lampg")


@machine2("gate", (1, 1), items=False)
def gate(m):
    """A door that drops across the belt, striped so you can see it from far away."""
    beltpiece(m)
    for s in (-1, 1):
        y = s * 0.44
        bx(m, (-0.07, 0.07), (y - 0.06, y + 0.06), (0.24, 1.30), "g2")
    bx(m, (-0.10, 0.10), (-0.52, 0.52), (1.30, 1.44), "g4")
    bx(m, (-0.03, 0.03), (-0.36, 0.36), (0.62, 1.20), "red")
    for z in (0.74, 0.96):
        bx(m, (-0.034, 0.034), (-0.36, 0.36), (z, z + 0.09), "white")
    m.cyl(0.07, 0.28, (0, 0, 1.58), "g1", seg=8)
    m.cyl(0.09, 0.05, (0, 0, 1.74), "g5", seg=8)


@machine2("counter", (1, 1), items=False)
def counter(m):
    """An arch over the belt with a number display."""
    beltpiece(m)
    for s in (-1, 1):
        y = s * 0.44
        bx(m, (-0.07, 0.07), (y - 0.06, y + 0.06), (0.24, 0.92), "g2")
    bx(m, (-0.16, 0.16), (-0.52, 0.52), (0.92, 1.34), "g2")
    bx(m, (-0.19, 0.19), (-0.55, 0.55), (1.34, 1.40), "g4")
    with on(m, "E", 0.16, 0, 1.13):
        m.box((0.84, 0.02, 0.28), (0, -0.01, 0), "hole")
        for i in range(3):
            x = -0.26 + i * 0.26
            for dz in (-0.09, 0.0, 0.09):
                m.box((0.13, 0.014, 0.03), (x, -0.024, dz), "lampg")
            for dx, dz in ((-0.065, 0.045), (0.065, 0.045), (-0.065, -0.045), (0.065, -0.045)):
                if (i + int(dx > 0) + int(dz > 0)) % 3:
                    m.box((0.03, 0.014, 0.075), (x + dx, -0.024, dz), "lampg")


def plate(m):
    """The flat base Islands gives its signal blocks."""
    bx(m, (-0.44, 0.44), (-0.44, 0.44), (0.0, 0.14), "g3")
    bx(m, (-0.40, 0.40), (-0.40, 0.40), (0.14, 0.20), "g1")
    return 0.20


def terminal(m, x, y, z):
    m.box((0.16, 0.16, 0.14), (x, y, z + 0.07), "g5")
    m.box((0.05, 0.05, 0.08), (x, y, z + 0.18), "copper")


@machine2("switch", (1, 1), items=False)
def switch(m):
    """A big lever with a red knob."""
    T = plate(m)
    bx(m, (-0.16, 0.16), (-0.22, 0.22), (T, T + 0.16), "g5")
    bx(m, (-0.04, 0.04), (-0.16, 0.16), (T + 0.16, T + 0.18), "hole")
    m.box((0.07, 0.07, 0.56), (0, -0.12, T + 0.40), "g2", rot=(rad(26), 0, 0))
    m.cyl(0.10, 0.14, (0, -0.25, T + 0.68), "red", seg=8, rot=(rad(26), 0, 0))
    terminal(m, 0.28, 0.26, T)
    m.box((0.05, 0.02, 0.05), (-0.26, -0.26, T + 0.01), "lampg")


@machine2("logic", (1, 1), items=False)
def logic(m):
    """A chip on a plate: two terminals in, one out."""
    T = plate(m)
    bx(m, (-0.18, 0.18), (-0.20, 0.20), (T, T + 0.12), "g5")
    for y in (-0.14, 0.0, 0.14):
        for s in (-1, 1):
            m.box((0.08, 0.04, 0.03), (s * 0.21, y, T + 0.03), "g1")
    m.cyl(0.035, 0.02, (-0.10, 0.12, T + 0.125), "g1", seg=8)
    terminal(m, -0.28, 0.24, T)
    terminal(m, -0.28, -0.24, T)
    terminal(m, 0.28, 0.0, T)
    for y in (0.24, -0.24):
        m.box((0.12, 0.03, 0.012), (-0.16, y * 0.75, T + 0.006), "copper")
    m.box((0.10, 0.03, 0.012), (0.20, 0.0, T + 0.006), "copper")


@machine2("beacon", (1, 1), items=False)
def beacon(m):
    """A signal tower: green, yellow, red."""
    m.cyl(0.32, 0.12, (0, 0, 0.06), "g4", seg=8)
    m.cyl(0.22, 0.16, (0, 0, 0.20), "g2", seg=8)
    m.cyl(0.055, 0.84, (0, 0, 0.70), "g3", seg=6)
    for i, c in enumerate(("lampg", "spark", "lampr")):
        m.cyl(0.14, 0.17, (0, 0, 1.20 + i * 0.22), c, seg=8)
        m.cyl(0.16, 0.05, (0, 0, 1.31 + i * 0.22), "g5", seg=8)
    m.cyl(0.10, 0.06, (0, 0, 1.80), "g3", seg=8, r2=0.04)


@machine2("timer", (1, 1), items=False)
def timer(m):
    """A clock face on a stand."""
    T = plate(m)
    bx(m, (-0.12, 0.12), (-0.08, 0.08), (T, T + 0.22), "g3")
    m.cyl(0.36, 0.12, (0, 0, T + 0.54), "g2", seg=12, axis="Y")
    m.cyl(0.38, 0.04, (0, -0.05, T + 0.54), "g4", seg=12, axis="Y")
    m.cyl(0.31, 0.02, (0, -0.066, T + 0.54), "white", seg=12, axis="Y")
    for k in range(4):
        a = k * math.pi / 2
        m.box((0.03, 0.012, 0.07), (math.sin(a) * 0.25, -0.08, T + 0.54 + math.cos(a) * 0.25), "g5", rot=(0, a, 0))
    m.box((0.03, 0.014, 0.22), (0.0, -0.084, T + 0.63), "g5")
    m.box((0.025, 0.014, 0.16), (0.06, -0.084, T + 0.59), "red", rot=(0, rad(48), 0))
    m.cyl(0.03, 0.02, (0, -0.09, T + 0.54), "g5", seg=6, axis="Y")
    for s in (-1, 1):
        m.cyl(0.07, 0.08, (s * 0.20, 0, T + 0.93), "g1", seg=8)
    terminal(m, 0.30, 0.28, T)


@machine2("sign", (1, 1), items=False)
def sign(m):
    """A board on a post."""
    rocks(m, ((0.10, 0.06, 0.05, 0.10), (-0.10, 0.02, 0.04, 0.08), (0.0, -0.10, 0.04, 0.07)))
    bx(m, (-0.05, 0.05), (-0.05, 0.05), (0.0, 0.84), "wood_dark")
    bx(m, (-0.44, 0.44), (-0.045, 0.045), (0.70, 1.30), "wood")
    for z in (0.67, 1.28):
        bx(m, (-0.47, 0.47), (-0.06, 0.06), (z, z + 0.05), "wood_dark")
    for i, w in enumerate((0.58, 0.44, 0.52)):
        m.box((w, 0.012, 0.05), (-0.02 * i, -0.05, 1.14 - i * 0.14), "wood_dark")
