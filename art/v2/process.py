# v2 models: machines that turn one material into another (변환).
import math
import factorykit as fk
from factorykit import rad
from .kit import (machine2, bx, on, inline, vent, panel, hexbolt, badge, gauge, buttons, slots, lamp, band,
                  chimney, frame_tower, tank, flange, hopper, skirt, port, body, tee, tee_body, TEE_IN, TEE_OUT,
                  HALF, BELT_Z, W_IN, E_OUT)


@machine2("smelter")
def smelter(m):
    """Firebox below, tapered hood above with a glowing grate, flue at the back."""
    inline(m)
    bx(m, (-0.5, 0.5), (-0.44, 0.44), (0.05, 0.80), "g2")
    band(m, (-0.5, 0.5), (-0.44, 0.44), 0.80, t=0.09)
    bx(m, (-0.40, 0.40), (-0.36, 0.36), (0.89, 1.32), "g1", taper=0.84)
    bx(m, (-0.37, 0.37), (-0.33, 0.33), (1.32, 1.39), "g4")
    bx(m, (-0.30, 0.30), (-0.26, 0.26), (1.37, 1.40), "hole")
    for i in range(5):
        m.box((0.05, 0.50, 0.03), (-0.24 + i * 0.12, 0, 1.405), "g3")
    for i in range(4):
        m.box((0.04, 0.44, 0.012), (-0.18 + i * 0.12, 0, 1.392), "glow")
    with on(m, "S", -0.20, -0.44, 0.47):
        slots(m, 0.34, 0.30, 4)
    with on(m, "S", 0.28, -0.44, 0.52):
        vent(m, 0.20, 0.30, 5)
    skirt(m, (-0.42, 0.10), y=-0.5, depth=0.07, h=0.22)
    # twin feed pipes dropping from the hood into the skirt
    for x in (-0.06, 0.04):
        m.pipe([(x, -0.36, 1.00), (x, -0.47, 0.94), (x, -0.47, 0.22)], 0.035, "white", seg=6)
    for x in (-0.33, -0.22):
        m.cyl(0.045, 0.06, (x, -0.47, 0.25), "g1", seg=6)
    chimney(m, 0.22, 0.20, 1.39, 0.50, r=0.10, glow=True)
    for x, y in ((-0.28, 0.24), (-0.14, 0.24)):
        m.cyl(0.04, 0.07, (x, y, 1.425), "g3", seg=6)


@machine2("crusher")
def crusher(m):
    """An open hopper over two toothed rolls, with the drive wheel on the front."""
    inline(m)
    bx(m, (-0.5, 0.5), (-0.44, 0.44), (0.05, 0.92), "g2")
    band(m, (-0.5, 0.5), (-0.44, 0.44), 0.92, t=0.08)
    T = hopper(m, 0, 0, 1.00, w=0.86, h=0.36, d=0.78)
    for s in (-1, 1):
        m.cyl(0.13, 0.62, (s * 0.15, 0, T - 0.04), "g3", seg=8, axis="Y")
        for i in range(4):
            m.gear(0.17, 0.06, (s * 0.15, -0.24 + i * 0.16, T - 0.04), "g5", teeth=6, axis="Y",
                   rot=(0, rad(15 * i + (0 if s < 0 else 30)), 0))
    with on(m, "S", -0.16, -0.44, 0.52):
        m.cyl(0.26, 0.05, (0, -0.025, 0), "g4", seg=12, axis="Y")
        m.gear(0.22, 0.05, (0, -0.07, 0), "g1", teeth=10, axis="Y")
        m.cyl(0.07, 0.07, (0, -0.10, 0), "red", seg=8, axis="Y")
    with on(m, "S", 0.26, -0.44, 0.40):
        m.gear(0.13, 0.05, (0, -0.045, 0), "g3", teeth=8, axis="Y")
        m.cyl(0.04, 0.07, (0, -0.07, 0), "g5", seg=6, axis="Y")
    with on(m, "S", 0.30, -0.44, 0.74):
        buttons(m, ("lampg", "red"))
    skirt(m, (-0.46, 0.46), y=-0.5, depth=0.06, h=0.14)


@machine2("sawmill")
def sawmill(m):
    """A low bed with the blade standing through it inside a guard frame."""
    inline(m)
    bx(m, (-0.5, 0.5), (-0.44, 0.44), (0.05, 0.70), "g2")
    band(m, (-0.5, 0.5), (-0.44, 0.44), 0.70, t=0.07, mk="g1", out=0.02)
    bx(m, (-0.34, 0.34), (-0.03, 0.03), (0.76, 0.79), "hole")
    m.gear(0.36, 0.03, (0.0, 0.0, 0.84), "white", teeth=14, axis="Y")
    m.cyl(0.08, 0.06, (0.0, 0.0, 0.84), "red", seg=8, axis="Y")
    frame_tower(m, (-0.42, 0.42), (-0.36, 0.36), 0.77, (1.34,), post=0.05, beam=0.10, mk="g4")
    bx(m, (-0.38, 0.38), (-0.06, 0.06), (1.20, 1.30), "g3")
    # a log waiting on the rest, and offcuts
    m.cyl(0.085, 0.50, (-0.10, -0.25, 0.86), "wood_light", seg=8, axis="X")
    m.cyl(0.085, 0.012, (-0.352, -0.25, 0.86), "wood", seg=8, axis="X")
    with on(m, "S", -0.22, -0.44, 0.40):
        buttons(m, ("spark", "lampg", "water", "red"))
    with on(m, "S", 0.26, -0.44, 0.40):
        vent(m, 0.24, 0.22, 3)
    skirt(m, (-0.30, 0.30), y=-0.5, depth=0.06, h=0.16)


@machine2("washer")
def washer(m):
    """An open wash trough on the deck, fed by two water tanks through hoses."""
    inline(m)
    T = body(m, 0.86, band_mk="g3", t=0.07, out=0.02)
    bx(m, (-0.40, 0.40), (-0.36, 0.08), (T, T + 0.12), "g1")
    bx(m, (-0.35, 0.35), (-0.31, 0.03), (T + 0.10, T + 0.126), "water")
    for x in (-0.22, 0.22):
        m.cyl(0.15, 0.46, (x, 0.26, T + 0.23), "g1", seg=8)
        m.cyl(0.155, 0.12, (x, 0.26, T + 0.42), "water", seg=8)
        m.cyl(0.17, 0.05, (x, 0.26, T + 0.505), "g3", seg=8)
        m.pipe([(x, 0.26, T + 0.52), (x, 0.26, T + 0.64), (x * 0.5, 0.02, T + 0.64), (x * 0.5, -0.14, T + 0.46),
                (x * 0.5, -0.14, T + 0.12)], 0.03, "water_light", seg=6)
    with on(m, "S", -0.24, -0.44, 0.48):
        gauge(m, 0.11)
    for x in (0.12, 0.32):
        m.pipe([(x, -0.47, 0.86), (x, -0.47, 0.20)], 0.04, "white", seg=6)
    for z in (0.36, 0.54, 0.72):
        m.box((0.22, 0.04, 0.04), (0.22, -0.47, z), "white")
    skirt(m, (-0.02, 0.46), y=-0.5, depth=0.07, h=0.20)


@machine2("kiln")
def kiln(m):
    """A brick oven: banded courses, iron straps, a domed crown and a brick flue."""
    inline(m)
    bx(m, (-0.5, 0.5), (-0.44, 0.44), (0.0, 0.18), "g4")
    bx(m, (-0.48, 0.48), (-0.42, 0.42), (0.18, 0.96), "brick")
    for z in (0.37, 0.56, 0.75):
        bx(m, (-0.484, 0.484), (-0.424, 0.424), (z, z + 0.025), "mortar")
    for x in (-0.38, 0.38):
        bx(m, (x - 0.035, x + 0.035), (-0.445, 0.445), (0.18, 0.96), "g4")
    m.cyl(0.50, 0.07, (0, 0, 0.995), "g4", seg=8, rot=rad(22.5))
    m.cyl(0.46, 0.30, (0, 0, 1.18), "brick_dark", seg=8, r2=0.28, rot=rad(22.5))
    m.cyl(0.28, 0.08, (0, 0, 1.37), "brick", seg=8, rot=rad(22.5))
    chimney(m, 0.0, 0.0, 1.41, 0.36, r=0.13, seg=8, mks=("brick", "brick_dark"))
    with on(m, "S", 0, -0.42, 0.55):
        slots(m, 0.30, 0.34, 3)
    for sx in (-1, 1):
        m.cyl(0.03, 0.03, (sx * 0.38, -0.455, 0.80), "g1", seg=6, axis="Y")
        m.cyl(0.03, 0.03, (sx * 0.38, -0.455, 0.34), "g1", seg=6, axis="Y")


@machine2("stonecutter")
def stonecutter(m):
    """A gang saw: three blades hang from a head on two posts over the block being cut."""
    inline(m)
    T = body(m, 0.66, t=0.07)
    bx(m, (-0.26, 0.26), (-0.22, 0.22), (T, T + 0.27), "stone")
    bx(m, (-0.26, 0.26), (-0.22, 0.22), (T + 0.27, T + 0.29), "stone_dark")
    for x in (-0.40, 0.40):
        bx(m, (x - 0.05, x + 0.05), (-0.07, 0.07), (T, T + 0.80), "g3")
    bx(m, (-0.48, 0.48), (-0.13, 0.13), (T + 0.70, T + 0.88), "g1")
    bx(m, (-0.34, 0.34), (-0.16, 0.16), (T + 0.88, T + 0.94), "g4")
    for y in (-0.12, 0.0, 0.12):
        bx(m, (-0.32, 0.32), (y - 0.012, y + 0.012), (T + 0.18, T + 0.70), "white")
    m.pipe([(0.30, 0.30, T), (0.30, 0.30, T + 0.50), (0.18, 0.18, T + 0.50)], 0.035, "water", seg=6)
    with on(m, "S", -0.24, -0.44, 0.38):
        vent(m, 0.28, 0.22, 3)
    with on(m, "S", 0.24, -0.44, 0.38):
        buttons(m, ("lampg", "red", "water"))
    skirt(m, (-0.34, 0.34), y=-0.5, depth=0.06, h=0.14)


@machine2("press")
def press(m):
    """Four columns carry a heavy head; the red ram comes down on the plate."""
    inline(m)
    T = body(m, 0.70)
    bx(m, (-0.30, 0.30), (-0.26, 0.26), (T, T + 0.08), "g5")
    bx(m, (-0.21, 0.21), (-0.16, 0.16), (T + 0.08, T + 0.11), "iron")
    for x in (-0.37, 0.37):
        for y in (-0.31, 0.31):
            m.cyl(0.05, 0.86, (x, y, T + 0.43), "g1", seg=8)
            m.cyl(0.07, 0.05, (x, y, T + 0.025), "g3", seg=8)
    bx(m, (-0.47, 0.47), (-0.41, 0.41), (T + 0.86, T + 1.10), "g3")
    bx(m, (-0.50, 0.50), (-0.44, 0.44), (T + 0.94, T + 1.02), "g4")
    bx(m, (-0.26, 0.26), (-0.22, 0.22), (T + 0.42, T + 0.56), "red")
    m.cyl(0.10, 0.32, (0, 0, T + 0.71), "g1", seg=8)
    m.cyl(0.17, 0.24, (0, 0, T + 1.22), "g2", seg=8)
    m.cyl(0.20, 0.05, (0, 0, T + 1.36), "g5", seg=8)
    with on(m, "S", -0.24, -0.44, 0.42):
        gauge(m, 0.11)
    with on(m, "S", 0.22, -0.44, 0.42):
        badge(m, 0.10)
    skirt(m, (-0.44, 0.44), y=-0.5, depth=0.06, h=0.14)


@machine2("wiredraw")
def wiredraw(m):
    """A die block pulls the wire thin; a big spool on a stand winds it up."""
    inline(m)
    T = body(m, 0.78)
    for y in (-0.33, 0.33):
        m.cyl(0.33, 0.06, (0.12, y, T + 0.40), "g3", seg=12, axis="Y")
        bx(m, (0.04, 0.20), (y - 0.035, y + 0.035), (T, T + 0.40), "g2")
    m.cyl(0.25, 0.60, (0.12, 0, T + 0.40), "copper", seg=12, axis="Y")
    m.cyl(0.06, 0.80, (0.12, 0, T + 0.40), "g5", seg=6, axis="Y")
    bx(m, (-0.44, -0.22), (-0.16, 0.16), (T, T + 0.26), "g5")
    bx(m, (-0.40, -0.26), (-0.10, 0.10), (T + 0.26, T + 0.32), "g1")
    m.cyl(0.02, 0.26, (-0.12, 0.0, T + 0.20), "copper_light", seg=6, axis="X")
    with on(m, "S", -0.22, -0.44, 0.42):
        vent(m, 0.26, 0.24, 4)
    with on(m, "S", 0.24, -0.44, 0.42):
        hexbolt(m, 0.06)
    skirt(m, (-0.10, 0.40), y=-0.5, depth=0.06, h=0.16)


@machine2("mill")
def mill(m):
    """A round stone housing with a feed hopper and a flour spout."""
    inline(m)
    T = body(m, 0.68, t=0.07)
    m.cyl(0.44, 0.24, (0, 0, T + 0.12), "stone", seg=10)
    m.cyl(0.46, 0.05, (0, 0, T + 0.25), "g4", seg=10)
    m.cyl(0.40, 0.18, (0, 0, T + 0.36), "stone_dark", seg=10)
    Z = hopper(m, 0, 0, T + 0.45, w=0.50, h=0.26, fill="wheat")
    for x, y in ((-0.10, 0.06), (0.08, -0.07), (0.02, 0.10)):
        m.ico(0.05, (x, y, Z + 0.02), "wheat_head", jitter=0.2)
    m.cyl(0.03, 0.30, (0.30, 0.30, T + 0.60), "g5", seg=6)
    m.cyl(0.06, 0.05, (0.30, 0.30, T + 0.76), "red", seg=8)
    with on(m, "S", 0.0, -0.44, 0.40):
        m.box((0.26, 0.10, 0.16), (0, -0.05, 0), "g1")
        m.box((0.20, 0.02, 0.10), (0, -0.10, 0), "cream")
    skirt(m, (-0.36, 0.36), y=-0.5, depth=0.06, h=0.14)


@machine2("briquetter")
def briquetter(m):
    """A hydraulic ram lying on the deck squeezes loose dust into bricks."""
    inline(m)
    T = body(m, 0.80)
    m.cyl(0.15, 0.50, (-0.20, 0.10, T + 0.19), "g1", seg=8, axis="X")
    for x in (-0.44, 0.04):
        m.cyl(0.18, 0.05, (x, 0.10, T + 0.19), "g3", seg=8, axis="X")
    m.cyl(0.06, 0.20, (0.14, 0.10, T + 0.19), "white", seg=8, axis="X")
    bx(m, (0.22, 0.46), (-0.10, 0.30), (T, T + 0.40), "g5")
    bx(m, (0.20, 0.48), (-0.12, 0.32), (T + 0.40, T + 0.46), "g4")
    for i, (x, y) in enumerate(((-0.30, -0.28), (-0.12, -0.28), (-0.21, -0.28))):
        m.box((0.16, 0.10, 0.07), (x, y, T + 0.035 + (0.075 if i == 2 else 0)), "charcoal")
    with on(m, "S", -0.22, -0.44, 0.42):
        gauge(m, 0.10)
    with on(m, "S", 0.22, -0.44, 0.42):
        vent(m, 0.26, 0.24, 4)
    skirt(m, (-0.44, 0.44), y=-0.5, depth=0.06, h=0.14)


@machine2("oilpress")
def oilpress(m):
    """A screw press in a slatted cage, dripping into a tray with a barrel beside it."""
    inline(m)
    T = body(m, 0.74)
    bx(m, (-0.34, 0.14), (-0.26, 0.26), (T, T + 0.06), "g5")
    bx(m, (-0.30, 0.10), (-0.22, 0.22), (T + 0.05, T + 0.07), "oil")
    for i in range(8):
        a = i * math.pi / 4
        m.box((0.035, 0.035, 0.40), (-0.10 + math.cos(a) * 0.18, math.sin(a) * 0.18, T + 0.30), "wood_dark")
    for z in (0.14, 0.44):
        m.cyl(0.21, 0.04, (-0.10, 0, T + z), "g4", seg=8)
    m.cyl(0.14, 0.10, (-0.10, 0, T + 0.55), "g3", seg=8)
    for i in range(4):
        m.cyl(0.05 if i % 2 else 0.035, 0.07, (-0.10, 0, T + 0.635 + i * 0.07), "g1", seg=6)
    m.box((0.50, 0.05, 0.05), (-0.10, 0, T + 0.93), "g5")
    for s in (-1, 1):
        m.cyl(0.04, 0.05, (-0.10 + s * 0.25, 0, T + 0.93), "red", seg=6)
    fk.barrel(m, (0.32, -0.20, T), mk="oil", r=0.11, h=0.28, band="g3")
    with on(m, "S", 0.0, -0.44, 0.42):
        vent(m, 0.34, 0.24, 4)
    skirt(m, (-0.40, 0.40), y=-0.5, depth=0.06, h=0.14)


@machine2("lathe")
def lathe(m):
    """Headstock and chuck at one end, tailstock at the other, the cutting tool between."""
    inline(m)
    T = body(m, 0.72, band_mk="g3", t=0.07, out=0.02)
    bx(m, (-0.46, -0.16), (-0.24, 0.24), (T, T + 0.44), "g2")
    bx(m, (-0.48, -0.14), (-0.26, 0.26), (T + 0.44, T + 0.50), "g4")
    m.cyl(0.17, 0.10, (-0.11, 0, T + 0.26), "g5", seg=8, axis="X")
    for a in (0, 2.09, 4.19):
        m.box((0.06, 0.07, 0.07), (-0.05, math.cos(a) * 0.11, T + 0.26 + math.sin(a) * 0.11), "g1")
    m.cyl(0.045, 0.44, (0.14, 0, T + 0.26), "iron", seg=8, axis="X")
    bx(m, (0.32, 0.46), (-0.14, 0.14), (T, T + 0.36), "g2")
    m.cyl(0.03, 0.10, (0.30, 0, T + 0.26), "g5", seg=6, axis="X", r2=0.01)
    bx(m, (0.02, 0.24), (-0.34, -0.10), (T, T + 0.12), "g3")
    bx(m, (0.08, 0.18), (-0.26, -0.14), (T + 0.12, T + 0.24), "red")
    m.box((0.03, 0.12, 0.03), (0.13, -0.10, T + 0.24), "white")
    for x, y in ((0.00, 0.30), (0.10, 0.34), (0.05, 0.26)):
        m.ico(0.03, (x, y, T + 0.03), "iron", jitter=0.3)
    with on(m, "S", -0.24, -0.44, 0.40):
        buttons(m, ("lampg", "red"))
    with on(m, "S", 0.20, -0.44, 0.40):
        vent(m, 0.30, 0.22, 3)
    skirt(m, (-0.44, 0.44), y=-0.5, depth=0.06, h=0.14)


@machine2("caster")
def caster(m):
    """A crucible tips molten metal into a mould tray."""
    inline(m)
    T = body(m, 0.72)
    bx(m, (-0.10, 0.44), (-0.30, 0.30), (T, T + 0.10), "g5")
    for x in (0.04, 0.24):
        for y in (-0.14, 0.14):
            bx(m, (x - 0.07, x + 0.07), (y - 0.10, y + 0.10), (T + 0.09, T + 0.106), "glow" if (x < 0.1) == (y < 0) else "hole")
    for y in (-0.36, 0.36):
        bx(m, (-0.40, -0.28), (y - 0.04, y + 0.04), (T, T + 0.74), "g3")
    m.cyl(0.03, 0.80, (-0.34, 0, T + 0.62), "g5", seg=6, axis="Y")
    with m.at((-0.30, 0, T + 0.58)):
        m.cyl(0.22, 0.34, (0, 0, 0), "g4", seg=8, r2=0.26, rot=(0, rad(28), 0))
        m.cyl(0.21, 0.02, (0.085, 0, 0.155), "glow", seg=8, rot=(0, rad(28), 0))
    m.box((0.04, 0.05, 0.30), (-0.02, 0, T + 0.36), "glow", rot=(0, rad(18), 0))
    with on(m, "S", -0.24, -0.44, 0.40):
        slots(m, 0.26, 0.22, 3)
    with on(m, "S", 0.24, -0.44, 0.40):
        vent(m, 0.24, 0.22, 3)
    skirt(m, (-0.44, 0.44), y=-0.5, depth=0.06, h=0.14)


@machine2("loom")
def loom(m):
    """A timber frame strung with warp threads, with the woven cloth rolling off the front."""
    inline(m)
    T = body(m, 0.60, band_mk="wood_dark", t=0.07, out=0.02)
    for x in (-0.42, 0.42):
        for y in (-0.36, 0.36):
            bx(m, (x - 0.04, x + 0.04), (y - 0.04, y + 0.04), (T, T + 0.86), "wood")
    for y in (-0.36, 0.36):
        bx(m, (-0.48, 0.48), (y - 0.045, y + 0.045), (T + 0.80, T + 0.88), "wood_dark")
    for x in (-0.42, 0.42):
        bx(m, (x - 0.045, x + 0.045), (-0.40, 0.40), (T + 0.52, T + 0.59), "wood_dark")
    for i in range(9):
        y = -0.28 + i * 0.07
        m.box((0.78, 0.012, 0.012), (0, y, T + 0.44), "cotton", rot=(0, rad(-12), 0))
    m.cyl(0.07, 0.74, (0.36, 0, T + 0.30), "cotton", seg=8, axis="Y")
    m.cyl(0.05, 0.74, (-0.36, 0, T + 0.62), "wood_light", seg=8, axis="Y")
    m.box((0.05, 0.70, 0.30), (0.02, 0, T + 0.50), "wood_light")
    with on(m, "S", 0.0, -0.44, 0.34):
        panel(m, 0.50, 0.22, mk="wood_light")


@machine2("gemcutter")
def gemcutter(m):
    """A cutting wheel faced with diamond, an arm holding the stone to it, and a lamp."""
    inline(m)
    T = body(m, 0.80)
    m.cyl(0.30, 0.06, (0.08, 0.06, T + 0.03), "g5", seg=12)
    m.cyl(0.26, 0.03, (0.08, 0.06, T + 0.075), "diamond", seg=12)
    m.cyl(0.05, 0.05, (0.08, 0.06, T + 0.10), "g1", seg=8)
    bx(m, (-0.44, -0.28), (-0.30, -0.14), (T, T + 0.34), "g2")
    m.box((0.40, 0.06, 0.06), (-0.18, -0.20, T + 0.34), "g3", rot=(0, rad(18), rad(20)))
    m.cyl(0.05, 0.10, (0.0, -0.14, T + 0.22), "diamond", seg=6, r2=0.005)
    m.pipe([(-0.34, 0.32, T), (-0.34, 0.32, T + 0.52), (-0.16, 0.20, T + 0.62)], 0.025, "g5", seg=6)
    m.cyl(0.07, 0.08, (-0.14, 0.18, T + 0.60), "spark", seg=8, r2=0.03, rot=(rad(40), rad(-40), 0))
    with on(m, "S", -0.22, -0.44, 0.42):
        panel(m, 0.30, 0.26)
    with on(m, "S", 0.24, -0.44, 0.42):
        buttons(m, ("water", "lampg"))
    skirt(m, (-0.44, 0.44), y=-0.5, depth=0.06, h=0.14)


@machine2("painter")
def painter(m):
    """A spray booth: three paint tanks on the roof feed nozzles over the block."""
    inline(m)
    T = body(m, 0.64, t=0.07)
    frame_tower(m, (-0.42, 0.42), (-0.36, 0.36), T, (T + 0.74,), post=0.05, beam=0.10, mk="g4")
    bx(m, (-0.44, 0.44), (-0.38, 0.38), (T + 0.74, T + 0.80), "g1")
    for x, c in ((-0.26, "red"), (0.0, "spark"), (0.26, "water")):
        m.cyl(0.10, 0.26, (x, 0.08, T + 0.93), c, seg=8)
        m.cyl(0.11, 0.04, (x, 0.08, T + 1.07), "g3", seg=8)
        m.cyl(0.025, 0.16, (x, 0.08, T + 0.66), "g5", seg=6)
        m.cyl(0.04, 0.05, (x, 0.08, T + 0.57), c, seg=6, r2=0.015)
    bx(m, (-0.17, 0.17), (-0.12, 0.22), (T, T + 0.30), "water")
    bx(m, (-0.30, 0.30), (-0.38, -0.34), (T + 0.30, T + 0.74), "glassb")
    with on(m, "S", 0.0, -0.44, 0.36):
        buttons(m, ("red", "spark", "water", "lampg"))
    skirt(m, (-0.40, 0.40), y=-0.5, depth=0.06, h=0.14)


@machine2("refinery", (3, 2), TEE_OUT)
def refinery(m):
    """A tall cracking column beside a short receiver tank; fuel leaves one way, plastic the other."""
    tee(m, "out")
    T = tee_body(m, 1.10)
    Z = tank(m, -0.14, 0.52, T, 0.30, 1.50, seg=10, rings=3)
    m.cyl(0.10, 0.20, (-0.14, 0.52, Z + 0.10), "g3", seg=8)
    m.cyl(0.13, 0.05, (-0.14, 0.52, Z + 0.22), "g5", seg=8)
    tank(m, 0.30, 0.26, T, 0.14, 0.60, mk="g1", seg=8, rings=2, rods=False)
    m.pipe([(0.30, 0.26, T + 0.68), (0.30, 0.26, T + 1.05), (0.14, 0.40, T + 1.05)], 0.04, "g3", seg=6)
    m.pipe([(-0.14, 0.20, T + 0.40), (-0.14, 0.12, T + 0.40), (-0.14, 0.12, T)], 0.05, "g3", seg=6)
    for z in (0.30, 0.70, 1.10):
        m.box((0.16, 0.03, 0.03), (-0.14, 0.20, T + z), "g5")
    with on(m, "E", 0.50, 0.50, 0.62):
        vent(m, 0.40, 0.30, 5)
    with on(m, "S", -0.34, 0.04, 1.14):
        badge(m, 0.08)


@machine2("recycler", (3, 2), TEE_OUT)
def recycler(m):
    """A shredder: a wide mouth with two rows of teeth, and two ways out."""
    tee(m, "out")
    T = tee_body(m, 1.12)
    Z = hopper(m, 0, 0.50, T, w=0.84, h=0.34, d=0.76)
    for s in (-1, 1):
        m.cyl(0.11, 0.60, (s * 0.14, 0.50, Z - 0.05), "g3", seg=8, axis="Y")
        for i in range(4):
            m.gear(0.15, 0.05, (s * 0.14, 0.26 + i * 0.16, Z - 0.05), "red", teeth=5, axis="Y",
                   rot=(0, rad(20 * i + (0 if s < 0 else 36)), 0))
    with on(m, "E", 0.50, 0.50, 0.62):
        vent(m, 0.40, 0.30, 5)
    with on(m, "S", 0.34, 0.04, 1.14):
        lamp(m, "lampg")
    with on(m, "S", -0.34, 0.04, 1.14):
        lamp(m, "lampr")


@machine2("sieve", (3, 2), TEE_OUT)
def sieve(m):
    """A sloping screen box shaking on springs; what falls through leaves by the side."""
    tee(m, "out")
    T = tee_body(m, 1.06, t=0.07)
    for x in (-0.36, 0.36):
        for y in (0.18, 0.82):
            for i in range(3):
                m.cyl(0.05 if i % 2 == 0 else 0.035, 0.06, (x, y, T + 0.03 + i * 0.06), "g1", seg=6)
    with m.at((0, 0.50, T + 0.30)):
        a = rad(-10)
        m.box((0.92, 0.80, 0.05), (0, 0, 0), "g3", rot=(0, a, 0))
        m.box((0.84, 0.70, 0.02), (0, 0, 0.035), "g5", rot=(0, a, 0))
        for s in (-1, 1):
            m.box((0.92, 0.05, 0.20), (0, s * 0.40, 0.09), "g2", rot=(0, a, 0))
        for i in range(6):
            m.box((0.012, 0.70, 0.012), (-0.35 + i * 0.14, 0, 0.05 + (-0.35 + i * 0.14) * math.tan(-a) * -1), "g1",
                  rot=(0, a, 0))
        for x, y in ((-0.2, 0.1), (0.05, -0.15), (0.2, 0.2), (-0.05, 0.22)):
            m.ico(0.05, (x, y, 0.09 + x * 0.17), "stone", jitter=0.25)
    with on(m, "E", 0.50, 0.50, 0.60):
        vent(m, 0.40, 0.28, 4)
