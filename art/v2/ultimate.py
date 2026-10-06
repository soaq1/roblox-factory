# v2 models: the two end-game machines (궁극의 장치). They are five cells across and tower over everything else.
import math
import factorykit as fk
from factorykit import rad
from .kit import (machine2, bx, on, stub, port, vent, panel, hexbolt, badge, gauge, buttons, slots, lamp, band,
                  chimney, frame_tower, tank, E_OUT)
from .kit import hull


def platform(m, half=1.9, top=1.10):
    bx(m, (-half, half), (-half, half), (0.0, 0.18), "g4")
    hull(m, (-half + 0.06, half - 0.06), (-half + 0.06, half - 0.06), top, z0=0.18, span=1.25, post=0.10)
    band(m, (-half + 0.06, half - 0.06), (-half + 0.06, half - 0.06), top, t=0.12)
    for side in ("S", "E"):
        f = half - 0.06
        for a in (-1.2, 1.2):
            with on(m, side, *((a, -f) if side == "S" else (f, a)), 0.66):
                vent(m, 0.60, 0.40, 6)
        for a in (-0.62, 0.62):
            with on(m, side, *((a, -f) if side == "S" else (f, a)), 0.84):
                badge(m, 0.12)
    return top + 0.12


@machine2("coreforge", (5, 5), (("W", "in", 1), ("W", "in", -1), ("S", "in", 0), E_OUT))
def coreforge(m):
    """Four great claws hold a vein core while it grows over a pool of molten metal."""
    for y in (1, -1):
        with m.at((-1.9, y, 0)):
            stub(m, 0.0, -1, 0.6, "in")
    port(m, "S", 0, -1.9, "in", L=0.6)
    stub(m, 1.9, 1, 0.6, "out")
    T = platform(m)
    m.cyl(1.56, 0.20, (0, 0, T + 0.10), "g3", seg=8, rot=rad(22.5))
    m.cyl(1.26, 0.20, (0, 0, T + 0.30), "g1", seg=8, rot=rad(22.5))
    m.cyl(0.90, 0.16, (0, 0, T + 0.48), "g5", seg=8, rot=rad(22.5))
    m.cyl(0.74, 0.02, (0, 0, T + 0.565), "glow", seg=8, rot=rad(22.5))
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        with m.at((math.cos(a) * 1.30, math.sin(a) * 1.30, T + 0.20), a):
            m.box((0.36, 0.42, 1.56), (0, 0, 0.78), "g2")
            m.box((0.42, 0.48, 0.14), (0, 0, 0.56), "g4")
            m.box((0.42, 0.48, 0.14), (0, 0, 1.20), "g4")
            m.box((0.28, 0.32, 1.16), (-0.36, 0, 1.92), "g1", rot=(0, rad(-36), 0))
            m.box((0.20, 0.24, 0.40), (-0.74, 0, 2.44), "g3", rot=(0, rad(-62), 0))
            m.cyl(0.15, 0.54, (0, 0, 1.52), "g5", seg=6, axis="Y")
            m.box((0.04, 0.16, 0.44), (0.19, 0, 0.88), "core_gold")
    C = (0, 0, T + 2.30)
    fk.crystal(m, C, 0.52, "core_gold")
    for k, (r, dz, s_) in enumerate(((0.95, 0.5, 0.14), (0.85, -0.2, 0.10), (1.0, 0.1, 0.09), (0.8, 0.8, 0.08))):
        a = 0.6 + k * 1.7
        fk.crystal(m, (math.cos(a) * r, math.sin(a) * r, C[2] + dz), s_, "core_gold")
    fk.tilted_ring(m, (0, 0, C[2] + 0.4), 0.90, 0.035, (rad(22), rad(10), 0), "g5")
    fk.tilted_ring(m, (0, 0, C[2] + 0.4), 1.04, 0.03, (rad(-18), rad(24), 0), "frame")
    frame_tower(m, (-1.98, 1.98), (-1.98, 1.98), 0.0, (T + 1.50, T + 3.30), post=0.09, beam=0.20)
    for x, y in ((-1.50, -1.50), (1.50, -1.50), (1.50, 1.50)):
        chimney(m, x, y, T, 1.10, r=0.16, glow=True)
    tank(m, -1.48, 1.48, T, 0.26, 0.90, seg=10, rings=2)
    m.pipe([(1.50, -1.20, T + 0.30), (0.90, -1.20, T + 0.30), (0.90, -0.80, T + 0.30)], 0.07, "g1", seg=6)
    m.pipe([(-1.50, -1.20, T + 0.30), (-0.90, -1.20, T + 0.30), (-0.90, -0.80, T + 0.30)], 0.07, "g1", seg=6)


@machine2("reactor", (5, 5), items=False)
def reactor(m):
    """A containment sphere ringed with coils. Four pylons draw the power off it."""
    T = platform(m)
    m.cyl(1.50, 0.22, (0, 0, T + 0.11), "g3", seg=10)
    m.cyl(1.10, 0.50, (0, 0, T + 0.47), "g2", seg=10, r2=0.80)
    m.cyl(0.84, 0.10, (0, 0, T + 0.77), "g4", seg=10)
    Z = T + 1.80
    m.ico(1.06, (0, 0, Z), "g1")
    m.cyl(1.04, 0.22, (0, 0, Z), "spark", seg=12)
    m.cyl(1.10, 0.07, (0, 0, Z + 0.15), "g5", seg=12)
    m.cyl(1.10, 0.07, (0, 0, Z - 0.15), "g5", seg=12)
    m.cyl(0.50, 0.14, (0, 0, Z + 0.98), "g4", seg=10)
    m.cyl(0.34, 0.26, (0, 0, Z + 1.16), "g3", seg=10)
    m.cyl(0.26, 0.012, (0, 0, Z + 1.296), "spark", seg=10)
    fk.tilted_ring(m, (0, 0, Z), 1.36, 0.06, (rad(58), 0, 0), "copper")
    fk.tilted_ring(m, (0, 0, Z), 1.36, 0.06, (rad(-58), 0, 0), "copper")
    fk.tilted_ring(m, (0, 0, Z), 1.50, 0.05, (0, rad(64), 0), "frame")
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        x, y = math.cos(a) * 1.46, math.sin(a) * 1.46
        m.box((0.44, 0.44, 0.30), (x, y, T + 0.15), "g4")
        for i in range(10):
            m.cyl(0.17 if i % 2 == 0 else 0.12, 0.16, (x, y, T + 0.38 + i * 0.16), "copper" if i % 2 == 0 else "g5", seg=8)
        m.cyl(0.07, 0.34, (x, y, T + 2.10), "g1", seg=6)
        m.ico(0.13, (x, y, T + 2.36), "spark")
        m.pipe([(x, y, T + 2.36), (x * 0.72, y * 0.72, T + 2.80), (x * 0.36, y * 0.36, Z + 1.10)], 0.025, "spark", seg=5)
    frame_tower(m, (-1.98, 1.98), (-1.98, 1.98), 0.0, (T + 1.30, T + 3.40), post=0.09, beam=0.20)
    for sx in (-1, 1):
        for i in range(5):
            bx(m, (sx * 1.66 - 0.05, sx * 1.66 + 0.05), (-0.60 + i * 0.26, -0.48 + i * 0.26), (T, T + 0.46), "g3")
