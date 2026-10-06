# v2 models: machines that take two or more materials (조합).
import math
import factorykit as fk
from factorykit import rad
from .kit import (machine2, bx, on, inline, stub, vent, panel, hexbolt, badge, gauge, buttons, slots, lamp, band,
                  chimney, frame_tower, tank, flange, hopper, skirt, port, body, tee, tee_body, TEE_IN, TEE_OUT,
                  HALF, BELT_Z, W_IN, E_OUT)
from .kit import hull


@machine2("blast", (3, 3), (W_IN, ("S", "in", 0), E_OUT))
def blast(m):
    """Blast furnace: a 3x3 machine block inside a painted steel frame, with the stack rising through it."""
    stub(m, -0.9, -1, 0.6, "in")
    stub(m, 0.9, 1, 0.6, "out")
    port(m, "S", 0, -0.9, "in", L=0.6)
    # machine block
    bx(m, (-0.9, 0.9), (-0.9, 0.9), (0.0, 0.14), "g4")
    hull(m, (-0.86, 0.86), (-0.86, 0.86), 1.10, z0=0.14)
    band(m, (-0.86, 0.86), (-0.86, 0.86), 1.10, t=0.10)
    bx(m, (-0.70, 0.70), (-0.70, 0.70), (1.20, 1.60), "g1")
    band(m, (-0.70, 0.70), (-0.70, 0.70), 1.60, t=0.07, mk="g3", out=0.03)
    # the furnace shaft
    m.cyl(0.46, 0.50, (0, 0.05, 1.92), "g2", seg=8, r2=0.36)
    m.cyl(0.38, 0.10, (0, 0.05, 2.22), "g4", seg=8)
    m.cyl(0.33, 0.44, (0, 0.05, 2.49), "g3", seg=8, r2=0.26)
    m.cyl(0.30, 0.08, (0, 0.05, 2.75), "g5", seg=8)
    m.cyl(0.24, 0.012, (0, 0.05, 2.792), "glow", seg=8)
    # frame
    frame_tower(m, (-0.98, 0.98), (-0.98, 0.98), 0.0, (1.72, 2.62), post=0.06, beam=0.14)
    # front details
    for x in (-0.52, 0.52):
        with on(m, "S", x, -0.86, 0.80):
            slots(m, 0.34, 0.12, 5, vertical=True)
    with on(m, "S", 0.52, -0.86, 0.45):
        vent(m, 0.34, 0.22, 4)
    with on(m, "S", -0.62, -0.86, 0.44):
        badge(m, 0.10)
    with on(m, "S", -0.40, -0.86, 0.44):
        badge(m, 0.10)
    with on(m, "E", 0.86, -0.52, 0.72):
        vent(m, 0.34, 0.40, 6)
    with on(m, "E", 0.86, 0.52, 0.72):
        panel(m, 0.34, 0.40)
    # side stacks and a pipe run across the deck
    chimney(m, 0.56, -0.52, 1.67, 0.62, r=0.11)
    chimney(m, -0.56, -0.52, 1.67, 0.40, r=0.09)
    m.pipe([(0.56, -0.30, 1.75), (0.30, -0.30, 1.75), (0.30, -0.10, 1.90)], 0.05, "g1", seg=6)
    m.cyl(0.03, 0.55, (-0.30, -0.56, 1.95), "g3", seg=6)


@machine2("assembler", (3, 2), TEE_IN)
def assembler(m):
    """A robot arm under a gantry puts the part together on a work plate."""
    tee(m, "in")
    T = tee_body(m, 1.10)
    frame_tower(m, (-0.42, 0.42), (0.10, 0.90), T, (T + 0.86,), post=0.05, beam=0.10)
    m.cyl(0.20, 0.05, (0.10, 0.50, T + 0.025), "g5", seg=10)
    m.gear(0.15, 0.05, (0.10, 0.50, T + 0.075), "iron", teeth=8, axis="Z")
    # arm: base, two links, a red tool
    m.cyl(0.11, 0.14, (-0.26, 0.50, T + 0.07), "g3", seg=8)
    m.box((0.09, 0.09, 0.44), (-0.22, 0.50, T + 0.32), "g1", rot=(0, rad(14), 0))
    m.cyl(0.07, 0.13, (-0.17, 0.50, T + 0.53), "g5", seg=8, axis="Y")
    m.box((0.36, 0.08, 0.08), (-0.03, 0.50, T + 0.47), "g1", rot=(0, rad(22), 0))
    m.cyl(0.035, 0.16, (0.11, 0.50, T + 0.33), "red", seg=6)
    bx(m, (0.24, 0.42), (0.14, 0.32), (T, T + 0.14), "g3")
    with on(m, "E", 0.50, 0.50, 0.62):
        vent(m, 0.40, 0.30, 5)
    with on(m, "S", 0.34, 0.04, 1.14):
        lamp(m, "lampg")


@machine2("circuit", (3, 2), TEE_IN)
def circuit(m):
    """A clean cabinet: the board lies under a glass hood while a head places parts on it."""
    tee(m, "in")
    T = tee_body(m, 1.10, mk="g1", band_mk="g3")
    bx(m, (-0.34, 0.34), (0.18, 0.82), (T, T + 0.05), "g5")
    bx(m, (-0.26, 0.26), (0.26, 0.74), (T + 0.05, T + 0.07), "pcb")
    for x, y in ((-0.14, 0.38), (0.06, 0.58), (0.14, 0.36), (-0.08, 0.62)):
        m.box((0.07, 0.07, 0.03), (x, y, T + 0.085), "g5")
    for x in (-0.20, 0.0, 0.20):
        m.box((0.012, 0.40, 0.006), (x, 0.50, T + 0.073), "gold")
    for x in (-0.38, 0.38):
        for y in (0.14, 0.86):
            bx(m, (x - 0.03, x + 0.03), (y - 0.03, y + 0.03), (T, T + 0.50), "g3")
    bx(m, (-0.42, 0.42), (0.10, 0.90), (T + 0.50, T + 0.56), "g2")
    bx(m, (-0.38, 0.38), (0.10, 0.13), (T + 0.05, T + 0.50), "glassb")
    m.box((0.70, 0.06, 0.06), (0, 0.50, T + 0.44), "g5")
    m.box((0.12, 0.14, 0.12), (0.08, 0.50, T + 0.36), "red")
    m.cyl(0.02, 0.16, (0.08, 0.50, T + 0.22), "g1", seg=6)
    m.cyl(0.14, 0.08, (-0.22, 0.70, T + 0.60), "copper", seg=10)
    m.cyl(0.16, 0.02, (-0.22, 0.70, T + 0.65), "g3", seg=10)
    with on(m, "E", 0.50, 0.50, 0.62):
        buttons(m, ("lampg", "spark", "water", "red"))


@machine2("mixer", (3, 2), TEE_IN)
def mixer(m):
    """A tilted drum on a cradle, with a water line running into its mouth."""
    tee(m, "in")
    T = tee_body(m, 1.06)
    for x in (-0.30, 0.30):
        bx(m, (x - 0.05, x + 0.05), (0.20, 0.80), (T, T + 0.30), "g3")
    with m.at((0, 0.50, T + 0.56)):
        tilt = (rad(-32), 0, 0)
        m.cyl(0.40, 0.30, (0, 0.0, 0.0), "tankc", seg=10, rot=tilt)
        m.cyl(0.40, 0.26, (0, -0.148, 0.237), "tankc", seg=10, r2=0.26, rot=tilt)
        m.cyl(0.24, 0.02, (0, -0.225, 0.36), "g5", seg=10, rot=tilt)
        m.cyl(0.42, 0.07, (0, 0.03, -0.045), "g4", seg=10, rot=tilt)
        m.cyl(0.40, 0.22, (0, 0.138, -0.22), "tank_dark", seg=10, r2=0.5 * 0.5, rot=(rad(-32) + math.pi, 0, 0))
    m.pipe([(0.40, 0.84, T), (0.40, 0.84, T + 1.16), (0.10, 0.40, T + 1.16), (0.04, 0.32, T + 1.00)], 0.04, "water", seg=6)
    with on(m, "E", 0.50, 0.50, 0.62):
        gauge(m, 0.12)
    with on(m, "S", -0.34, 0.04, 1.10):
        lamp(m, "lampg")


@machine2("oven", (3, 2), TEE_IN)
def oven(m):
    """A baking oven: an arched door glowing on the side, loaves cooling on top, a flue at the back."""
    tee(m, "in")
    T = tee_body(m, 1.20, mk="g1", band_mk="g4")
    bx(m, (-0.40, 0.40), (0.14, 0.86), (T, T + 0.34), "g2")
    bx(m, (-0.44, 0.44), (0.10, 0.90), (T + 0.34, T + 0.40), "g4")
    for i, (x, y) in enumerate(((-0.18, 0.36), (0.10, 0.44), (-0.04, 0.66))):
        m.box((0.22, 0.13, 0.09), (x, y, T + 0.445), "bread", bevel=0.02, rot=rad(20 * i))
    chimney(m, 0.28, 0.74, T + 0.40, 0.46, r=0.09)
    with on(m, "E", 0.50, 0.50, 0.66):
        slots(m, 0.46, 0.34, 4, vertical=False)
    with on(m, "E", 0.50, 0.50, 0.99):
        m.box((0.40, 0.05, 0.05), (0, -0.04, 0), "g5")
    with on(m, "S", 0.0, 0.14, T + 0.18):
        vent(m, 0.44, 0.18, 3)


@machine2("alloy", (3, 2), TEE_IN)
def alloy(m):
    """Two small crucibles pour into one large one."""
    tee(m, "in")
    T = tee_body(m, 1.06)
    m.cyl(0.30, 0.34, (0.12, 0.42, T + 0.17), "g4", seg=8, r2=0.36)
    m.cyl(0.38, 0.05, (0.12, 0.42, T + 0.36), "g5", seg=8)
    m.cyl(0.30, 0.012, (0.12, 0.42, T + 0.388), "glow", seg=8)
    for x, y, c in ((-0.30, 0.24, "copper"), (-0.30, 0.74, "iron")):
        bx(m, (x - 0.07, x + 0.07), (y - 0.07, y + 0.07), (T, T + 0.52), "g3")
        m.cyl(0.14, 0.20, (x + 0.06, y, T + 0.62), "g2", seg=8, r2=0.18, rot=(0, rad(30), 0))
        m.cyl(0.13, 0.012, (x + 0.11, y, T + 0.705), "glow", seg=8, rot=(0, rad(30), 0))
        m.box((0.035, 0.035, 0.26), (x + 0.26, y + (0.42 - y) * 0.5, T + 0.50), "glow", rot=(0, rad(40), 0))
        m.box((0.10, 0.10, 0.05), (x, y, T + 0.03), c)
    chimney(m, 0.36, 0.82, T, 0.80, r=0.08, glow=True)
    with on(m, "E", 0.50, 0.50, 0.62):
        slots(m, 0.40, 0.28, 5)


@machine2("manufacturer", (3, 3), (W_IN, ("N", "in", 0), ("S", "in", 0), E_OUT))
def manufacturer(m):
    """A whole workshop in one frame: three lines come in, a gantry crane works over the bench, one line leaves."""
    stub(m, -0.9, -1, 0.6, "in")
    stub(m, 0.9, 1, 0.6, "out")
    port(m, "S", 0, -0.9, "in", L=0.6)
    port(m, "N", 0, 0.9, "in", L=0.6)
    bx(m, (-0.9, 0.9), (-0.9, 0.9), (0.0, 0.14), "g4")
    hull(m, (-0.86, 0.86), (-0.86, 0.86), 1.12, z0=0.14)
    band(m, (-0.86, 0.86), (-0.86, 0.86), 1.12, t=0.10)
    T = 1.22
    frame_tower(m, (-0.98, 0.98), (-0.98, 0.98), 0.0, (T + 0.62, T + 1.30), post=0.06, beam=0.14)
    # work bench with the motor being built
    bx(m, (-0.34, 0.34), (-0.34, 0.34), (T, T + 0.16), "g5")
    m.cyl(0.20, 0.36, (0, 0, T + 0.34), "g1", seg=10, axis="X")
    m.cyl(0.23, 0.08, (-0.10, 0, T + 0.34), "copper", seg=10, axis="X")
    m.cyl(0.23, 0.08, (0.08, 0, T + 0.34), "copper", seg=10, axis="X")
    m.cyl(0.05, 0.56, (0, 0, T + 0.34), "g5", seg=6, axis="X")
    # gantry crane on the upper ring
    m.box((2.00, 0.14, 0.12), (0, 0.10, T + 1.16), "g3")
    m.box((0.26, 0.24, 0.18), (0.14, 0.10, T + 1.04), "red")
    m.cyl(0.015, 0.40, (0.14, 0.10, T + 0.76), "g5", seg=6)
    m.box((0.12, 0.10, 0.06), (0.14, 0.10, T + 0.56), "g5")
    # corner cabinets and stacks
    bx(m, (-0.80, -0.44), (0.44, 0.80), (T, T + 0.54), "g1")
    band(m, (-0.80, -0.44), (0.44, 0.80), T + 0.54, t=0.05, mk="g3", out=0.02)
    bx(m, (0.44, 0.80), (0.44, 0.80), (T, T + 0.34), "g2")
    chimney(m, 0.62, 0.62, T + 0.34, 0.70, r=0.11)
    chimney(m, -0.66, -0.66, T, 0.56, r=0.09)
    tank(m, 0.62, -0.62, T, 0.16, 0.50, mk="g1", seg=8, rings=2, rods=False)
    for x in (-0.52, 0.52):
        with on(m, "S", x, -0.86, 0.80):
            slots(m, 0.34, 0.12, 5, mk="lampg")
    with on(m, "S", 0.52, -0.86, 0.45):
        vent(m, 0.34, 0.22, 4)
    with on(m, "S", -0.52, -0.86, 0.45):
        buttons(m, ("lampg", "spark", "water", "red"), s=0.06)
    with on(m, "E", 0.86, -0.52, 0.66):
        vent(m, 0.34, 0.40, 6)
    with on(m, "E", 0.86, 0.52, 0.66):
        badge(m, 0.12)


@machine2("packer")
def packer(m):
    """Two square chutes drop into a crate held in the frame."""
    inline(m)
    T = body(m, 0.62, t=0.07)
    frame_tower(m, (-0.42, 0.42), (-0.36, 0.36), T, (T + 0.74,), post=0.05, beam=0.10, mk="g4")
    fk.crate(m, (0.0, 0.0, T), s=0.40)
    for x in (-0.18, 0.18):
        bx(m, (x - 0.13, x + 0.13), (-0.14, 0.14), (T + 0.74, T + 1.04), "g2")
        bx(m, (x - 0.16, x + 0.16), (-0.17, 0.17), (T + 1.04, T + 1.10), "g4")
        bx(m, (x - 0.10, x + 0.10), (-0.11, 0.11), (T + 1.085, T + 1.105), "hole")
        bx(m, (x - 0.07, x + 0.07), (-0.08, 0.08), (T + 0.56, T + 0.74), "g3")
    with on(m, "S", -0.22, -0.44, 0.34):
        buttons(m, ("lampg", "red"))
    with on(m, "S", 0.24, -0.44, 0.34):
        vent(m, 0.24, 0.20, 3)
    skirt(m, (-0.40, 0.40), y=-0.5, depth=0.06, h=0.14)


@machine2("vending", (1, 1), items=False)
def vending(m):
    """A shop cabinet: goods behind the glass, a price panel, a slot for coins and a tray at the bottom."""
    bx(m, (-0.42, 0.42), (-0.34, 0.34), (0.0, 0.10), "g5")
    bx(m, (-0.44, 0.44), (-0.36, 0.36), (0.10, 1.78), "frame")
    bx(m, (-0.46, 0.46), (-0.38, 0.38), (1.78, 1.86), "g1")
    with on(m, "S", -0.10, -0.36, 1.12):
        m.box((0.50, 0.03, 0.96), (0, -0.015, 0), "g5")
        m.box((0.44, 0.02, 0.90), (0, -0.036, 0), "navy")
        for i in range(3):
            m.box((0.44, 0.07, 0.025), (0, -0.05, -0.36 + i * 0.30), "g1")
            for j, c in enumerate(("copper", "iron", "gold")):
                m.box((0.09, 0.05, 0.12), (-0.14 + j * 0.14, -0.055, -0.29 + i * 0.30), (c, "wood", "pcb")[(i + j) % 3])
    with on(m, "S", 0.30, -0.36, 1.20):
        m.box((0.16, 0.03, 0.42), (0, -0.015, 0), "g1")
        m.box((0.10, 0.02, 0.10), (0, -0.036, 0.12), "lampg")
        m.box((0.03, 0.02, 0.10), (0, -0.036, -0.04), "hole")
        m.box((0.09, 0.03, 0.05), (0, -0.04, -0.15), "gold")
    with on(m, "S", 0.0, -0.36, 0.36):
        m.box((0.60, 0.04, 0.24), (0, -0.02, 0), "g1")
        m.box((0.50, 0.02, 0.14), (0, -0.045, 0), "hole")
