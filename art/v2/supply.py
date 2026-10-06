# v2 supply machines: they give without being fed, or tend the field. Each stands on a cell of its own
# with a belt along the cell to its east (or, for the seeder, bringing seed in from the west).
import math
from .d import *          # noqa: F401,F403
from .d import stub, free, stub_form, neck, K, frustum, strip, hatch, lamps, lever, vent_round


def crystal(m, x, y, z, r, mk):
    m.cyl(0.0, r * 1.5, (x, y, z + r * 0.75), mk, seg=6, r2=r)
    m.cyl(r, r * 0.9, (x, y, z + r * 1.95), mk, seg=6, r2=0.0)


def extractor(core):
    def body(m, Z):
        """Extractor: four pylons lean in round a socket in the deck. With a vein core set in it, the
        core hangs in the air between them over the socket's light."""
        neck(m, Z, 0.46, 0.41, 0.06)
        oct_ring(m, 0.28, 0.09, Z + 0.04, Z + 0.12, D)
        octa(m, 0.19, 0.19, Z + 0.04, Z + 0.075, "h_core" if core else SLIT)
        for sx in SIDES:
            for sy in SIDES:
                xs0, xs1 = sorted((sx * 0.24, sx * 0.42)), sorted((sx * 0.13, sx * 0.24))
                ys0, ys1 = sorted((sy * 0.22, sy * 0.39)), sorted((sy * 0.12, sy * 0.22))
                frustum(m, (tuple(xs0), tuple(ys0)), (tuple(xs1), tuple(ys1)), Z + 0.04, Z + 0.72, G)
                m.box((0.14, 0.13, 0.07), (sx * 0.185, sy * 0.17, Z + 0.745), D, bevel=0.015)
        if core:
            crystal(m, 0, 0, Z + 0.26, 0.185, core)
    return body


def logger(m, Z):
    """Logger: felled logs lie stacked in a cradle on the deck, and a crane at the back holds the next
    one in its tongs."""
    neck(m, Z, 0.46, 0.41, 0.06)
    for x in (-0.20, 0.26):
        bx(m, (x - 0.05, x + 0.05), (-0.34, 0.34), (Z + 0.04, Z + 0.13), D, bevel=0.015)
    for y, z in ((-0.115, Z + 0.215), (0.115, Z + 0.215)):
        m.cyl(0.105, 0.66, (0.03, y, z), "h_wood", seg=8, axis="X")
        for sx in SIDES:
            m.cyl(0.085, 0.012, (0.03 + sx * 0.33, y, z), "h_wood_l", seg=8, axis="X")
    bx(m, (-0.47, -0.35), (-0.08, 0.08), (Z + 0.04, Z + 1.00), G, bevel=0.03)
    bx(m, (-0.47, 0.16), (-0.065, 0.065), (Z + 0.92, Z + 1.05), G, bevel=0.03)
    m.cyl(0.03, 0.26, (0.03, 0, Z + 0.80), "h_lite", seg=8)
    m.cyl(0.105, 0.50, (0.03, 0, Z + 0.50), "h_wood", seg=8, axis="X")
    for s in SIDES:
        m.prism([(0.0, Z + 0.70), (s * 0.15, Z + 0.56), (s * 0.13, Z + 0.42), (s * 0.085, Z + 0.44), (s * 0.10, Z + 0.55),
                 (0.0, Z + 0.63)], -0.02, 0.08, "X", D)


def pump(m, Z):
    """Water pump: a banded barrel with a flywheel each side stands in an open tank of the water it has
    raised."""
    neck(m, Z, 0.46, 0.41, 0.06)
    oct_ring(m, 0.42, 0.06, Z + 0.04, Z + 0.30, G)
    octa(m, 0.37, 0.37, Z + 0.04, Z + 0.22, "h_water")
    oct_ring(m, 0.44, 0.09, Z + 0.27, Z + 0.33, D)
    octa(m, 0.16, 0.16, Z + 0.04, Z + 0.86, G)
    for z in (Z + 0.42, Z + 0.72):
        octa(m, 0.18, 0.18, z - 0.025, z + 0.025, D)
    octa(m, 0.16, 0.08, Z + 0.86, Z + 0.95, D)
    m.cyl(0.045, 0.72, (0, 0, Z + 0.58), "h_lite", seg=8, axis="Y")
    for d in SIDES:
        m.cyl(0.19, 0.05, (0, d * 0.30, Z + 0.58), D, seg=12, axis="Y")
        m.cyl(0.07, 0.07, (0, d * 0.305, Z + 0.58), "h_lite", seg=8, axis="Y")


def harvester(m, Z):
    """Harvester: a reel of paddles turns at the front between two arms and sweeps the crop back into
    the grain tank behind it."""
    neck(m, Z, 0.46, 0.41, 0.06)
    for d in SIDES:
        bx(m, (-0.44, -0.02), tuple(sorted((d * 0.33, d * 0.42))), (Z + 0.04, Z + 0.46), G, bevel=0.03)
        m.cyl(0.07, 0.05, (-0.23, d * 0.43, Z + 0.34), D, seg=8, axis="Y")
    gear(m, 0.215, 0.62, (-0.23, 0, Z + 0.34), "h_wood_l", teeth=6, root=0.30, base=0.22, tip=0.14)
    m.cyl(0.05, 0.70, (-0.23, 0, Z + 0.34), "h_lite", seg=8, axis="Y")
    for s in SIDES:
        bx(m, (0.04, 0.47), tuple(sorted((s * 0.33, s * 0.41))), (Z + 0.04, Z + 0.56), G, bevel=0.025)
    bx(m, (0.04, 0.11), (-0.41, 0.41), (Z + 0.04, Z + 0.56), G, bevel=0.025)
    bx(m, (0.40, 0.47), (-0.41, 0.41), (Z + 0.04, Z + 0.56), G, bevel=0.025)
    m.box((0.32, 0.68, 0.40), (0.255, 0, Z + 0.28), "h_oil")


def seeder(m, Z):
    """Seeder: a long seed box feeds three drop tubes that run down its back wall into the ground."""
    neck(m, Z, 0.46, 0.41, 0.06)
    m.prism([(-0.30, Z + 0.50), (-0.12, Z + 0.06), (0.12, Z + 0.06), (0.30, Z + 0.50)], -0.42, 0.42, "Y", G)
    for s in SIDES:
        m.box((0.66, 0.05, 0.06), (0, s * 0.415, Z + 0.50), D)
        m.box((0.05, 0.88, 0.06), (s * 0.31, 0, Z + 0.50), D)
    m.box((0.57, 0.78, 0.012), (0, 0, Z + 0.506), "h_oil")
    for y in (-0.27, 0.0, 0.27):
        m.cyl(0.05, Z + 0.10, (-0.48, y, (Z + 0.10) / 2), W, seg=8)
        m.cyl(0.07, 0.05, (-0.48, y, Z + 0.07), D, seg=8)
        m.cyl(0.07, 0.07, (-0.48, y, 0.035), D, seg=8, r2=0.05)


def pumpjack(m):
    """Pumpjack, 3x1: the engine and crank stand on the body; the beam rocks on a post over the west
    cell and its horsehead works the well at the far end."""
    Z = stub_form(m)
    neck(m, Z, 0.46, 0.41, 0.06)
    bx(m, (-1.50, -0.47), (-0.46, 0.46), (0.0, 0.12), T, bevel=0.035)
    bx(m, (-0.02, 0.44), (-0.30, 0.30), (Z + 0.04, Z + 0.40), G, bevel=0.04)             # engine house
    for d in SIDES:
        m.cyl(0.22, 0.06, (-0.24, d * 0.34, Z + 0.28), D, seg=12, axis="Y")               # crank discs
        m.box((0.16, 0.06, 0.20), (-0.24, d * 0.34, Z + 0.12), T, bevel=0.02)
        m.box((0.05, 0.05, 0.60), (-0.20, d * 0.34, Z + 0.64), "h_lite")                  # pitman arms
        m.prism([(-1.02, 0.10), (-0.66, 0.10), (-0.80, 1.72), (-0.88, 1.72)], *sorted((d * 0.20, d * 0.30)), "Y", G)
    m.cyl(0.04, 0.76, (-0.24, 0, Z + 0.28), "h_lite", seg=8, axis="Y")
    m.cyl(0.07, 0.66, (-0.84, 0, 1.72), D, seg=8, axis="Y")
    m.box((1.42, 0.13, 0.14), (-0.60, 0, 1.80), G, bevel=0.03)
    m.prism([(-1.25, 1.90), (-1.36, 1.84), (-1.42, 1.66), (-1.38, 1.46), (-1.25, 1.46)], -0.085, 0.085, "Y", T)
    m.cyl(0.022, 1.02, (-1.40, 0, 0.94), "h_lite", seg=6)
    m.cyl(0.11, 0.20, (-1.40, 0, 0.22), G, seg=8)
    m.cyl(0.14, 0.05, (-1.40, 0, 0.145), D, seg=8)
    m.cyl(0.075, 0.12, (-1.40, 0, 0.38), D, seg=8)


def sprinkler(m):
    """Sprinkler, 1x1: a standpipe on a small tank, with a two-armed head that turns at the top."""
    octa(m, 0.34, 0.34, 0.0, 0.07, T)
    octa(m, 0.30, 0.30, 0.05, 0.34, G)
    octa(m, 0.315, 0.315, 0.22, 0.28, D)
    octa(m, 0.30, 0.12, 0.34, 0.44, D)
    m.cyl(0.055, 0.56, (0, 0, 0.70), W, seg=8)
    m.cyl(0.085, 0.09, (0, 0, 1.00), D, seg=8)
    m.cyl(0.035, 0.80, (0, 0, 1.00), W, seg=8, axis="X")
    for sx in SIDES:
        m.cyl(0.03, 0.10, (sx * 0.42, 0, 1.04), D, seg=8, r2=0.055)


stub("extractor_empty", extractor(None), fit=lambda m, d, yp, z: strip(m, d, yp, z, SLIT))
stub("extractor_fe", extractor("h_ore"), fit=lambda m, d, yp, z: strip(m, d, yp, z, "h_core"))
stub("extractor_coal", extractor("h_coal"), fit=lambda m, d, yp, z: strip(m, d, yp, z, "h_core"))
stub("logger", logger, fit=lambda m, d, yp, z: hatch(m, d, yp, 0, z))
stub("pump", pump, fit=lambda m, d, yp, z: vent_round(m, d, yp, 0, z))
free("pumpjack", (3, 1), pumpjack, ports=(("E", "out", 0),))
stub("harvester", harvester, fit=lambda m, d, yp, z: lamps(m, d, yp, z))
free("sprinkler", (1, 1), sprinkler, items=False)
stub("seeder", seeder, flow=-1, fit=lambda m, d, yp, z: lever(m, d, yp, 0, z))
