# v2 models: belts and the devices that route items (운반).
import math
import factorykit as fk
from factorykit import rad, SIDE_ANG
from .kit import (machine2, bx, on, trough, chevron, collar, port_arch, inline, vent, panel, hexbolt, lamp,
                  band, buttons, RAILP, HALF, BELT_Z, W_IN, E_OUT)


@machine2("belt", (1, 1), items=False)
def belt(m):
    trough(m, -0.5, 0.5)


@machine2("belt_corner", (1, 1), items=False)
def belt_corner(m):
    """Right turn: enters from W travelling +X, leaves to S."""
    m.box((0.90, 0.90, 0.24), (0, 0, 0.12), "g3")
    m.box((0.83, 0.66, 0.06), (-0.085, 0, BELT_Z - 0.03), "tread")
    m.box((0.66, 0.17, 0.06), (0, -0.415, BELT_Z - 0.03), "tread")
    m.prism(RAILP, -0.5, HALF, "X", "g1")
    m.prism(RAILP, -0.5, HALF, "Y", "g1")
    bx(m, (0.31, 0.48), (0.31, 0.48), (0.0, 0.46), "g2")
    bx(m, (-0.5, -0.33), (-HALF, -0.33), (0.0, 0.39), "g1")
    bx(m, (-0.52, -0.31), (-0.48, -0.31), (0.39, 0.43), "g3")
    for x, y, a in ((-0.30, 0.0, 0.0), (0.0, -0.02, rad(-45)), (0.0, -0.30, rad(-90))):
        with m.at((x, y, 0), a):
            chevron(m, 0)
    m.box((0.10, 0.996, 0.16), (-0.446, 0, 0.08), "g2")
    m.box((0.996, 0.10, 0.16), (0, -0.446, 0.08), "g2")
    for x in (-0.25, 0.2):
        m.cyl(0.028, 0.03, (x, HALF + 0.004, 0.145), "g3", seg=6, axis="Y")
    for y in (-0.25, 0.2):
        m.cyl(0.028, 0.03, (HALF + 0.004, y, 0.145), "g3", seg=6, axis="X")


@machine2("belt_ramp", (2, 1), items=False)
def belt_ramp(m):
    """Two cells long, rises one cell. Enters low at W, leaves high at E."""
    a = math.atan2(1, 2)
    m.prism([(-1, 0.05), (1, 1.05), (1, 1.24), (-1, 0.24)], -0.35, 0.35, "Y", "g3")
    m.prism([(-1, 0.24), (1, 1.24), (1, 1.30), (-1, 0.30)], -0.33, 0.33, "Y", "tread")
    for s in (-1, 1):
        lo, hi = sorted((s * 0.33, s * 0.42))
        m.prism([(-1, 0.05), (1, 1.05), (1, 1.39), (-1, 0.39)], lo, hi, "Y", "g1")
        lo, hi = sorted((s * 0.42, s * HALF))
        m.prism([(-1, 0.05), (1, 1.05), (1, 1.24), (-1, 0.24)], lo, hi, "Y", "g1")
    for i in range(6):
        x = -0.83 + i * 0.33
        m.box((0.02, 0.60, 0.006), (x, 0, 0.303 + (x + 1) / 2), "treadline", rot=(0, -a, 0))
    # legs under the high half, the way Islands props its ramp
    for x in (0.25, 0.86):
        h = 0.05 + (x + 1) / 2
        for s in (-1, 1):
            m.box((0.09, 0.09, h), (x, s * 0.37, h / 2), "g2")
            m.box((0.20, 0.16, 0.05), (x, s * 0.37, 0.025), "g3")
        m.box((0.06, 0.74, 0.06), (x, 0, h * 0.45), "g3")
    for s in (-1, 1):
        m.box((0.70, 0.05, 0.05), (0.56, s * 0.37, 0.42), "g3", rot=(0, -a * 1.5, 0))
    m.box((0.10, 1.0, 0.16), (-0.946, 0, 0.08), "g2")


def junction(m, ports, core=0.34, top=0.92):
    """One-cell routing block: a core with a ribbed, colour-arched mouth on each port side."""
    bx(m, (-0.46, 0.46), (-0.46, 0.46), (0.0, 0.10), "g4")
    bx(m, (-core, core), (-core, core), (0.05, top), "g2")
    open_sides = {side for side, _, _ in ports}
    for side, kind, _ in ports:
        with m.at((0, 0, 0), SIDE_ANG[side]):
            m.box((0.5 - core, 0.70, 0.24), (core + (0.5 - core) / 2, 0, 0.12), "g3")
            m.box((0.5 - core, 0.66, 0.06), (core + (0.5 - core) / 2, 0, BELT_Z - 0.03), "tread")
            m.box((0.02, 0.66, 0.50), (core + 0.011, 0, BELT_Z + 0.25), "hole")
            xe = collar(m, core, 1, n=1, top=top + 0.02)
            port_arch(m, xe, 1, kind, top=top + 0.07, double=False)
    for side in "ENWS":
        if side not in open_sides:
            with on(m, side, 0, 0, 0):
                bx(m, (-0.42, 0.42), (-0.44, -core), (0.05, top - 0.14), "g3")
                with m.at((0, -0.44, 0.42)):
                    vent(m, 0.44, 0.26, 4)
    bx(m, (-core - 0.03, core + 0.03), (-core - 0.03, core + 0.03), (top, top + 0.05), "g4")
    bx(m, (-0.27, 0.27), (-0.27, 0.27), (top + 0.05, top + 0.09), "g1")
    for sx in (-1, 1):
        for sy in (-1, 1):
            m.cyl(0.025, 0.02, (sx * 0.22, sy * 0.22, top + 0.10), "g3", seg=6)
    return top + 0.09


@machine2("splitter", (1, 1), (W_IN, E_OUT, ("S", "out", 0)), items=False)
def splitter(m):
    T = junction(m, (W_IN, E_OUT, ("S", "out", 0)))
    fk.arrow(m, 0.06, 0.0, T, 0.0, "out", s=0.10)
    fk.arrow(m, -0.04, -0.10, T, rad(-90), "out", s=0.10)
    m.cyl(0.05, 0.03, (-0.13, 0.10, T + 0.015), "accent", seg=8)


@machine2("merger", (1, 1), (W_IN, ("N", "in", 0), E_OUT), items=False)
def merger(m):
    T = junction(m, (W_IN, ("N", "in", 0), E_OUT))
    fk.arrow(m, -0.10, 0.0, T, 0.0, "accent", s=0.09)
    fk.arrow(m, 0.0, 0.12, T, rad(-90), "accent", s=0.09)
    m.cyl(0.05, 0.03, (0.14, -0.06, T + 0.015), "out", seg=8)


@machine2("sorter", (1, 1), (W_IN, E_OUT, ("S", "out", 0)), items=False)
def sorter(m):
    T = junction(m, (W_IN, E_OUT, ("S", "out", 0)), top=1.0)
    # a filter funnel on the lid and a lamp mast: this is the block that picks one item out
    m.cyl(0.15, 0.10, (0, 0, T + 0.05), "water", seg=3, r2=0.05, rot=rad(-30))
    m.box((0.05, 0.05, 0.42), (0.22, 0.22, T + 0.21), "g3")
    m.box((0.10, 0.10, 0.09), (0.22, 0.22, T + 0.44), "lampg")
    m.box((0.12, 0.12, 0.03), (0.22, 0.22, T + 0.50), "g5")


@machine2("magsep", (1, 1), (W_IN, E_OUT, ("S", "out", 0)), items=False)
def magsep(m):
    T = junction(m, (W_IN, E_OUT, ("S", "out", 0)), top=0.95)
    # a horseshoe magnet stands on the lid, poles toward the side exit
    for s in (-1, 1):
        m.box((0.10, 0.26, 0.10), (s * 0.13, -0.05, T + 0.20), "red")
        m.box((0.10, 0.09, 0.10), (s * 0.13, -0.22, T + 0.20), "g1")
    m.box((0.36, 0.10, 0.10), (0, 0.09, T + 0.20), "red")
    for s in (-1, 1):
        m.box((0.06, 0.06, 0.15), (s * 0.13, 0.09, T + 0.075), "g5")


@machine2("pusher", (1, 1), (W_IN, E_OUT, ("S", "out", 0)), items=False)
def pusher(m):
    T = junction(m, (W_IN, E_OUT, ("S", "out", 0)), top=0.90)
    # the ram and its cylinder lie across the lid, pointing at the side exit
    m.box((0.26, 0.30, 0.20), (0, 0.16, T + 0.10), "g3")
    m.cyl(0.07, 0.30, (0, -0.02, T + 0.11), "g1", seg=8, axis="Y")
    m.box((0.30, 0.06, 0.22), (0, -0.20, T + 0.11), "red")
    for s in (-1, 1):
        m.cyl(0.025, 0.24, (s * 0.10, 0.0, T + 0.11), "g5", seg=6, axis="Y")


@machine2("storage", (3, 1), (W_IN, E_OUT))
def storage(m):
    """A container on the line. Ribbed like a shipping box, with a level meter on the front."""
    inline(m)
    bx(m, (-0.5, 0.5), (-0.44, 0.44), (0.05, 1.42), "g2")
    for x in (-0.38, -0.19, 0.0, 0.19, 0.38):
        bx(m, (x - 0.04, x + 0.04), (-HALF, HALF), (0.34, 1.36), "g3")
    band(m, (-0.5, 0.5), (-HALF, HALF), 0.20, t=0.10, out=0.0)
    band(m, (-0.5, 0.5), (-HALF, HALF), 1.42, t=0.09, out=0.02)
    bx(m, (-0.40, 0.40), (-0.36, 0.36), (1.51, 1.58), "g1")
    bx(m, (-0.12, 0.12), (-0.10, 0.10), (1.58, 1.64), "g3")
    with on(m, "S", 0, -HALF, 0.85):
        m.box((0.30, 0.03, 0.62), (0, -0.015, 0), "g5")
        for i in range(5):
            m.box((0.22, 0.02, 0.085), (0, -0.036, -0.24 + i * 0.12), "lampg" if i < 3 else "g4")
