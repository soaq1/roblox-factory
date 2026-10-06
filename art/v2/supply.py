# v2 models: machines that bring materials in without being fed (공급).
import math
import factorykit as fk
from factorykit import rad
from .kit import (machine2, bx, on, inline, stub, vent, panel, hexbolt, badge, gauge, buttons, slots, lamp, band,
                  chimney, frame_tower, tank, flange, hopper, skirt, port, body, tee, tee_body, TEE_IN, TEE_OUT,
                  rocks, HALF, BELT_Z, W_IN, E_OUT)

E2_OUT = (("E", "out", 0),)
W2_IN = (("W", "in", 0),)


def source(m, **kw):
    """2x1 layout for a machine that only gives: body in the west cell, output stub in the east cell."""
    stub(m, 0.0, 1, 1.0, "out", **kw)


def extractor(core):
    def build(m):
        """A stone-and-iron plinth with four claws. A vein core floats between them and ore comes out the side."""
        source(m)
        with m.at((-0.5, 0, 0)):
            bx(m, (-0.5, 0.5), (-0.46, 0.46), (0.0, 0.16), "rock_dark")
            m.cyl(0.50, 0.50, (0, 0, 0.41), "rock", seg=8, r2=0.44, rot=rad(22.5))
            m.cyl(0.47, 0.08, (0, 0, 0.70), "g4", seg=8, rot=rad(22.5))
            m.cyl(0.38, 0.14, (0, 0, 0.81), "g2", seg=8, rot=rad(22.5))
            m.cyl(0.24, 0.05, (0, 0, 0.895), "g5", seg=8, rot=rad(22.5))
            m.cyl(0.17, 0.012, (0, 0, 0.922), core or "hole", seg=8, rot=rad(22.5))
            for k in range(4):
                a = k * math.pi / 2 + math.pi / 4
                with m.at((math.cos(a) * 0.34, math.sin(a) * 0.34, 0.74), a):
                    m.box((0.13, 0.15, 0.50), (0, 0, 0.25), "g2")
                    m.box((0.15, 0.17, 0.07), (0, 0, 0.20), "g4")
                    m.box((0.10, 0.11, 0.34), (-0.10, 0, 0.60), "g1", rot=(0, rad(-34), 0))
                    m.cyl(0.05, 0.19, (0, 0, 0.48), "g5", seg=6, axis="Y")
            # runes on the plinth: this is the one machine that runs on magic
            for k in range(8):
                a = k * math.pi / 4
                m.box((0.035, 0.05, 0.16), (math.cos(a) * 0.455, math.sin(a) * 0.455, 0.42), core or "g5",
                      rot=a)
            if core:
                fk.crystal(m, (0, 0, 1.52), 0.20, core)
                for k, (r, dz, s_) in enumerate(((0.36, 0.22, 0.06), (0.33, -0.04, 0.045), (0.38, 0.10, 0.04))):
                    a = 0.6 + k * 2.2
                    fk.crystal(m, (math.cos(a) * r, math.sin(a) * r, 1.52 + dz), s_, core)
    return build


machine2("extractor_empty", (2, 1), E2_OUT)(extractor(None))
machine2("extractor_fe", (2, 1), E2_OUT)(extractor("core_fe"))
machine2("extractor_coal", (2, 1), E2_OUT)(extractor("core_coal"))


@machine2("logger", (2, 1), E2_OUT)
def logger(m):
    """A saw on a swinging boom, with cut logs stacked on the deck."""
    source(m)
    with m.at((-0.5, 0, 0)):
        T = body(m, 0.80)
        bx(m, (-0.34, -0.10), (0.06, 0.34), (T, T + 0.70), "g2")
        bx(m, (-0.37, -0.07), (0.03, 0.37), (T + 0.70, T + 0.78), "g4")
        m.box((0.12, 0.12, 0.95), (-0.22, -0.16, T + 0.86), "g3", rot=(rad(38), 0, 0))
        m.gear(0.34, 0.035, (-0.22, -0.50, T + 1.20), "white", teeth=14, axis="X")
        m.cyl(0.09, 0.09, (-0.22, -0.50, T + 1.20), "red", seg=8, axis="X")
        m.cyl(0.07, 0.30, (-0.22, 0.20, T + 0.50), "g5", seg=8, axis="Y")
        for i, (y, z) in enumerate(((-0.24, 0.085), (-0.06, 0.085), (-0.15, 0.24))):
            m.cyl(0.085, 0.46, (0.20, y, T + z), "wood_light", seg=8, axis="X")
            m.cyl(0.086, 0.012, (0.432, y, T + z), "wood", seg=8, axis="X")
        with on(m, "S", -0.20, -0.44, 0.42):
            vent(m, 0.30, 0.24, 4)
        with on(m, "S", 0.24, -0.44, 0.42):
            buttons(m, ("lampg", "red"))
        skirt(m, (-0.44, 0.44), y=-0.5, depth=0.06, h=0.14)


@machine2("pump", (2, 1), E2_OUT)
def pump(m):
    """A water tank, a pump barrel and an intake pipe going down into the ground."""
    source(m)
    with m.at((-0.5, 0, 0)):
        T = body(m, 0.66, band_mk="g3", t=0.07, out=0.02)
        m.cyl(0.30, 0.56, (-0.12, 0.08, T + 0.28), "g1", seg=10)
        m.cyl(0.31, 0.16, (-0.12, 0.08, T + 0.40), "water", seg=10)
        m.cyl(0.33, 0.06, (-0.12, 0.08, T + 0.59), "g3", seg=10)
        m.cyl(0.10, 0.06, (-0.12, 0.08, T + 0.65), "g5", seg=8)
        m.cyl(0.11, 0.40, (0.30, -0.22, T + 0.20), "g2", seg=8)
        m.cyl(0.13, 0.05, (0.30, -0.22, T + 0.42), "g4", seg=8)
        m.cyl(0.03, 0.26, (0.30, -0.22, T + 0.57), "g1", seg=6)
        m.box((0.30, 0.05, 0.05), (0.22, -0.22, T + 0.70), "red", rot=(0, rad(-14), 0))
        m.pipe([(0.30, -0.22, T + 0.30), (0.10, -0.22, T + 0.30), (0.10, 0.0, T + 0.30)], 0.045, "water_light", seg=6)
        m.pipe([(-0.36, -0.47, 0.0), (-0.36, -0.47, T + 0.20), (-0.30, -0.20, T + 0.20)], 0.06, "water", seg=6)
        m.cyl(0.09, 0.05, (-0.36, -0.47, 0.025), "g4", seg=8)
        with on(m, "S", 0.10, -0.44, 0.36):
            gauge(m, 0.10)


@machine2("pumpjack", (3, 2), (("E", "out", -0.5),))
def pumpjack(m):
    """An oil well: a walking beam on an A-frame, the horse-head at one end and the counterweight at the other."""
    with m.at((0.5, -0.5, 0)):
        stub(m, 0.0, 1, 1.0, "out")
    bx(m, (-1.46, 1.46), (-0.04, 0.96), (0.0, 0.14), "g4")
    bx(m, (-1.40, 1.40), (0.02, 0.90), (0.14, 0.22), "g2")
    bx(m, (-1.46, 0.5), (-0.96, -0.04), (0.0, 0.14), "g4")
    bx(m, (-1.40, 0.46), (-0.90, 0.02), (0.14, 0.22), "g2")
    # A-frame
    for s in (-1, 1):
        for y in (0.22, 0.70):
            m.box((0.08, 0.08, 1.62), (0.10 + s * 0.26, y, 1.0), "g3", rot=(0, rad(-s * 18), 0))
        m.box((0.60, 0.06, 0.06), (0.10, 0.46 + s * 0.24, 0.80), "g3")
    m.box((0.22, 0.62, 0.14), (0.10, 0.46, 1.80), "g5")
    # walking beam
    with m.at((0.10, 0.46, 1.92)):
        a = rad(9)
        m.box((2.20, 0.16, 0.18), (0, 0, 0), "g2", rot=(0, a, 0))
        m.box((2.00, 0.18, 0.05), (0, 0, 0.0), "g4", rot=(0, a, 0))
        m.prism([(-1.42, 0.16), (-1.10, 0.42), (-1.02, 0.42), (-1.02, -0.14), (-1.30, -0.30)], -0.11, 0.11, "Y", "g3")
        m.box((0.36, 0.42, 0.46), (0.98, 0, -0.26), "badge")
        m.box((0.40, 0.46, 0.06), (0.98, 0, -0.26), "stripe")
    m.cyl(0.02, 1.50, (-1.20, 0.46, 0.98), "g5", seg=6)
    m.cyl(0.10, 0.34, (-1.20, 0.46, 0.39), "g2", seg=8)
    m.cyl(0.13, 0.06, (-1.20, 0.46, 0.25), "g4", seg=8)
    # engine block and belt wheel
    bx(m, (0.66, 1.24), (0.16, 0.76), (0.22, 0.74), "g2")
    bx(m, (0.62, 1.28), (0.12, 0.80), (0.74, 0.82), "g4")
    m.cyl(0.24, 0.07, (0.95, 0.10, 0.56), "g5", seg=12, axis="Y")
    m.cyl(0.07, 0.10, (0.95, 0.08, 0.56), "red", seg=8, axis="Y")
    chimney(m, 1.08, 0.60, 0.82, 0.44, r=0.07)
    # barrels by the output
    with m.at((0.5, -0.5, 0)):
        bx(m, (-0.5, 0.0), (-0.44, 0.44), (0.14, 0.86), "g2")
        band(m, (-0.5, 0.0), (-0.44, 0.44), 0.86, t=0.07)
        with on(m, "S", -0.25, -0.44, 0.52):
            vent(m, 0.30, 0.26, 4)
    fk.barrel(m, (-0.60, -0.56, 0.22), mk="oil", r=0.14, h=0.36, band="g3")
    fk.barrel(m, (-0.94, -0.44, 0.22), mk="oil", r=0.14, h=0.36, band="g3")
    m.pipe([(-1.20, 0.34, 0.30), (-1.20, -0.10, 0.30), (-0.30, -0.10, 0.30), (-0.10, -0.40, 0.50), (0.0, -0.40, 0.50)],
           0.05, "g1", seg=6)


@machine2("harvester", (2, 1), E2_OUT)
def harvester(m):
    """A reel of paddles sweeps the crop into the bin behind it."""
    source(m)
    with m.at((-0.5, 0, 0)):
        T = body(m, 0.62, t=0.07)
        bx(m, (-0.10, 0.46), (-0.36, 0.36), (T, T + 0.50), "g2")
        bx(m, (-0.06, 0.42), (-0.32, 0.32), (T + 0.47, T + 0.51), "wheat")
        band(m, (-0.10, 0.46), (-0.36, 0.36), T + 0.50, t=0.04, mk="g4", out=0.02)
        for s in (-1, 1):
            m.box((0.34, 0.05, 0.10), (-0.26, s * 0.40, T + 0.30), "g3")
            m.cyl(0.24, 0.04, (-0.30, s * 0.40, T + 0.32), "g5", seg=10, axis="Y")
        m.cyl(0.04, 0.84, (-0.30, 0, T + 0.32), "g5", seg=6, axis="Y")
        for k in range(5):
            a = k * 2 * math.pi / 5
            m.box((0.03, 0.76, 0.16), (-0.30 + math.cos(a) * 0.17, 0, T + 0.32 + math.sin(a) * 0.17), "red",
                  rot=(0, -a + math.pi / 2, 0))
        with on(m, "S", 0.18, -0.44, 0.34):
            vent(m, 0.30, 0.20, 3)


@machine2("sprinkler", (1, 1), items=False)
def sprinkler(m):
    """A pedestal with a spinning head and four nozzles."""
    m.cyl(0.36, 0.14, (0, 0, 0.07), "g4", seg=8)
    m.cyl(0.26, 0.26, (0, 0, 0.27), "g2", seg=8, r2=0.14)
    m.cyl(0.12, 0.26, (0, 0, 0.53), "g3", seg=8)
    m.cyl(0.14, 0.20, (0, 0, 0.76), "g2", seg=8, r2=0.28)
    m.cyl(0.30, 0.08, (0, 0, 0.90), "g1", seg=8)
    m.cyl(0.20, 0.05, (0, 0, 0.965), "water", seg=8)
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        with m.at((0, 0, 0.90), a):
            m.cyl(0.035, 0.22, (0.36, 0, 0.03), "g3", seg=6, axis="X", rot=(0, rad(-12), 0))
            m.cyl(0.05, 0.06, (0.47, 0, 0.055), "water_light", seg=6, axis="X", rot=(0, rad(-12), 0))


@machine2("seeder", (2, 1), W2_IN)
def seeder(m):
    """Seed goes in the hopper; three drop tubes plant it."""
    stub(m, 0.0, -1, 1.0, "in")
    with m.at((0.5, 0, 0)):
        T = body(m, 0.70)
        Z = hopper(m, -0.08, 0, T, w=0.56, h=0.34, fill="wheat", d=0.66)
        bx(m, (0.24, 0.46), (-0.38, 0.38), (T, T + 0.24), "g3")
        for y in (-0.26, 0.0, 0.26):
            m.pipe([(0.20, y, T + 0.20), (0.44, y, T + 0.12), (0.47, y, 0.30)], 0.045, "g1", seg=6)
            m.cyl(0.07, 0.10, (0.47, y, 0.26), "red", seg=6, r2=0.03)
        with on(m, "S", -0.12, -0.44, 0.38):
            buttons(m, ("lampg", "spark"))
        skirt(m, (-0.44, 0.30), y=-0.5, depth=0.06, h=0.14)
