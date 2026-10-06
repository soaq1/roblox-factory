# v2 ultimate machines: the two great works that the whole factory builds toward. Each fills 5x5 cells.
import math
from .supply import crystal
from .d import *          # noqa: F401,F403
from .d import free, run, cover, frame, frustum, K


def port(m, origin, inward, out=False, duct=1.2):
    """A port in the edge of a great work: a cell of conveyor under a folding cover, then a duct that
    runs on into the machine."""
    with frame(m, origin, inward):
        run(m, 0.0, 0.5, flow=-1 if out else 1)
        cover(m, 0.13, 1)
        bx(m, (0.47, duct), (-0.36, 0.36), (0.20, 0.72), G, bevel=0.045)
        for x in (0.62, 0.92):
            if x + 0.06 < duct:
                bx(m, (x - 0.05, x + 0.05), (-0.385, 0.385), (0.20, 0.745), D, bevel=0.02)


def deck(m):
    bx(m, (-2.47, 2.47), (-2.47, 2.47), (0.0, 0.16), T, bevel=0.05)
    bx(m, (-2.38, 2.38), (-2.38, 2.38), (0.12, 0.25), G, bevel=0.035)


def coreforge(m):
    """Core forge: four great pylons lean in over a banded vessel and hold a new vein core in the air
    above the bright pool in its mouth. Two materials come in on the west, a third on the south, and
    the finished core leaves on the east."""
    deck(m)
    port(m, (-2.5, 1.0), (1, 0), duct=1.45)
    port(m, (-2.5, -1.0), (1, 0), duct=1.45)
    port(m, (0.0, -2.5), (0, 1), duct=1.30)
    port(m, (2.5, 0.0), (-1, 0), out=True, duct=1.30)
    octa(m, 1.30, 1.30, 0.22, 0.64, T)
    octa(m, 1.30, 1.08, 0.62, 1.30, G)
    for z in (0.84, 1.08):
        a = 1.30 - (z - 0.62) / 0.68 * 0.22
        octa(m, a + 0.035, a + 0.02, z - 0.04, z + 0.04, D)
    oct_ring(m, 1.15, 0.26, 1.26, 1.43, D)
    octa(m, 0.90, 0.90, 1.20, 1.34, "h_core")
    for sx in SIDES:
        for sy in SIDES:
            b = (tuple(sorted((sx * 1.50, sx * 2.10))), tuple(sorted((sy * 1.50, sy * 2.10))))
            t = (tuple(sorted((sx * 0.62, sx * 0.92))), tuple(sorted((sy * 0.62, sy * 0.92))))
            frustum(m, b, t, 0.22, 2.80, G)
            bx(m, tuple(sorted((sx * 1.44, sx * 2.16))), tuple(sorted((sy * 1.44, sy * 2.16))), (0.20, 0.42), D, bevel=0.05)
            bx(m, tuple(sorted((sx * 0.56, sx * 0.98))), tuple(sorted((sy * 0.56, sy * 0.98))), (2.76, 2.94), D, bevel=0.04)
    crystal(m, 0, 0, 1.62, 0.40, "h_gem")


def reactor(m):
    """Endless engine: a ring of eight coils round a core whose light shows between its bars, joined to
    the ring by four arms, under a tall spire."""
    deck(m)
    octa(m, 1.60, 1.60, 0.22, 0.30, D)
    oct_ring(m, 2.25, 0.72, 0.22, 0.92, G)
    for k in range(8):
        with m.at((0, 0, 0), k * math.pi / 4):
            bx(m, (1.47, 2.31), (-0.44, 0.44), (0.20, 1.06), T, bevel=0.06)
            for y in (-0.22, 0.0, 0.22):
                bx(m, (1.44, 2.34), (y - 0.045, y + 0.045), (0.18, 1.10), "h_lite", bevel=0.0)
            bx(m, (0.60, 0.74), (-0.07, 0.07), (0.56, 1.00), D, bevel=0.0)
    for k in range(4):
        with m.at((0, 0, 0), k * math.pi / 2 + math.pi / 4):
            bx(m, (0.66, 1.56), (-0.17, 0.17), (0.34, 0.76), G, bevel=0.05)
    octa(m, 0.70, 0.70, 0.22, 0.58, G)
    octa(m, 0.60, 0.60, 0.56, 1.00, "h_core")
    octa(m, 0.72, 0.72, 0.98, 1.32, G)
    octa(m, 0.72, 0.42, 1.32, 1.66, G)
    oct_ring(m, 0.50, 0.14, 1.62, 1.74, D)
    octa(m, 0.26, 0.20, 1.66, 2.50, G)
    for z in (1.95, 2.25):
        octa(m, 0.29, 0.29, z - 0.035, z + 0.035, D)
    octa(m, 0.20, 0.0, 2.50, 2.86, D)


free("coreforge", (5, 5), coreforge, ports=(("W", "in", 1), ("W", "in", -1), ("S", "in", 0), ("E", "out", 0)))
free("reactor", (5, 5), reactor, items=False)
