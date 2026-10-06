# v2 models: the places where things are made by hand (손 작업).
# These are not factory steel. Like Islands' early stations they are wood, stone and clay, with tools lying on them.
import math
import factorykit as fk
from factorykit import rad
from .kit import machine2, bx, on, rocks, buttons, lamp, badge, vent


@machine2("campfire", (1, 1), items=False)
def campfire(m):
    """A ring of stones, logs leaning together, a flame."""
    m.cyl(0.34, 0.04, (0, 0, 0.02), "charcoal", seg=10)
    for k in range(8):
        a = k * math.pi / 4
        m.ico(0.15, (math.cos(a) * 0.37, math.sin(a) * 0.37, 0.09), "rock" if k % 2 else "rock_dark", squash=0.8, jitter=0.18)
    for k in range(4):
        with m.at((0, 0, 0), k * math.pi / 2 + 0.4):
            m.cyl(0.065, 0.52, (0.13, 0, 0.24), "wood", seg=6, rot=(0, rad(-30), 0))
            m.cyl(0.066, 0.012, (0.26, 0, 0.018), "wood_light", seg=6, rot=(0, rad(-30), 0))
    m.cyl(0.13, 0.40, (0, 0, 0.44), "glow", seg=6, r2=0.01)
    m.cyl(0.08, 0.26, (0.05, -0.06, 0.36), "spark", seg=5, r2=0.005)
    m.cyl(0.06, 0.20, (-0.07, 0.04, 0.34), "spark", seg=5, r2=0.005)


@machine2("hand_furnace", (1, 1), items=False)
def hand_furnace(m):
    """A clay furnace shaped like a bottle, standing in a bed of stones."""
    for k in range(9):
        a = k * 2 * math.pi / 9
        m.ico(0.17, (math.cos(a) * 0.33, math.sin(a) * 0.33, 0.12), "rock" if k % 2 else "rock_dark", squash=0.85, jitter=0.2)
    m.cyl(0.36, 0.30, (0, 0, 0.36), "clayp", seg=8, r2=0.32)
    m.cyl(0.32, 0.50, (0, 0, 0.76), "clayp", seg=8, r2=0.17)
    m.cyl(0.17, 0.18, (0, 0, 1.10), "clayp", seg=8, r2=0.22)
    m.cyl(0.225, 0.04, (0, 0, 1.21), "g4", seg=8)
    m.cyl(0.16, 0.012, (0, 0, 1.232), "glow", seg=8)
    with m.at((0, 0, 0), rad(45)):
        m.box((0.26, 0.10, 0.26), (0, -0.33, 0.46), "g4")
        m.box((0.18, 0.04, 0.18), (0, -0.375, 0.46), "glow")
    m.cyl(0.07, 0.34, (0.34, 0.30, 0.30), "wood", seg=6, axis="Y", rot=rad(30))


@machine2("chest", (1, 1), items=False)
def chest(m):
    """A timber box with iron straps and a curved lid."""
    bx(m, (-0.42, 0.42), (-0.30, 0.30), (0.05, 0.50), "wood")
    for z in (0.16, 0.30):
        bx(m, (-0.424, 0.424), (-0.304, 0.304), (z, z + 0.014), "wood_dark")
    m.cyl(0.30, 0.83, (0, 0, 0.52), "wood_dark", seg=10, axis="X", rot=(rad(18), 0, 0))
    for x in (-0.28, 0.28):
        bx(m, (x - 0.055, x + 0.055), (-0.32, 0.32), (0.0, 0.52), "g4")
        m.cyl(0.32, 0.11, (x, 0, 0.52), "g4", seg=10, axis="X", rot=(rad(18), 0, 0))
    bx(m, (-0.45, 0.45), (-0.33, 0.33), (0.46, 0.54), "g4")
    for x in (-0.40, 0.40):
        for y in (-0.28, 0.28):
            bx(m, (x - 0.05, x + 0.05), (y - 0.05, y + 0.05), (0.0, 0.08), "g5")
    m.box((0.12, 0.05, 0.16), (0, -0.345, 0.48), "gold")
    m.box((0.03, 0.02, 0.05), (0, -0.375, 0.46), "hole")


@machine2("wb_basic", (1, 1), items=False)
def wb_basic(m):
    """A tree stump with a plan, a saw and a mallet on it: the first place anything gets made."""
    m.cyl(0.40, 0.52, (0, 0, 0.26), "wood_dark", seg=8, r2=0.35)
    m.cyl(0.35, 0.04, (0, 0, 0.54), "wood_light", seg=8)
    m.cyl(0.20, 0.012, (0, 0, 0.562), "wood", seg=8)
    for k in range(5):
        a = k * 2 * math.pi / 5 + 0.3
        with m.at((math.cos(a) * 0.36, math.sin(a) * 0.36, 0), a):
            m.box((0.34, 0.16, 0.16), (0.06, 0, 0.07), "wood_dark", taper=0.4, rot=(0, rad(18), 0))
    m.box((0.36, 0.26, 0.012), (-0.03, 0.05, 0.574), "paper", rot=rad(20))
    with m.at((0.12, 0.10, 0.58), rad(-30)):
        m.box((0.04, 0.04, 0.20), (0, 0, 0.10), "wood")
        m.box((0.16, 0.10, 0.10), (0, 0, 0.24), "toolred")
    with m.at((-0.02, -0.16, 0.578), rad(24)):
        m.box((0.36, 0.09, 0.012), (0, 0, 0.006), "g1")
        m.box((0.12, 0.11, 0.03), (0.23, 0, 0.015), "gold")


def bench2(m, top="wood", frame="wood_dark", back="wood", w=0.94, h=0.72, shelf=True):
    """A two-cell bench: legs, stretcher, top, and a back board with a shelf."""
    for x in (-w + 0.10, w - 0.10):
        for y in (-0.30, 0.30):
            bx(m, (x - 0.05, x + 0.05), (y - 0.05, y + 0.05), (0.0, h - 0.08), frame)
        bx(m, (x - 0.04, x + 0.04), (-0.30, 0.30), (0.16, 0.23), frame)
    bx(m, (-w + 0.10, w - 0.10), (0.26, 0.33), (0.16, 0.23), frame)
    bx(m, (-w, w), (-0.42, 0.42), (h - 0.08, h), top)
    bx(m, (-w + 0.04, w - 0.04), (-0.40, 0.40), (h - 0.16, h - 0.08), frame)
    if shelf:
        for x in (-w + 0.07, w - 0.07):
            bx(m, (x - 0.045, x + 0.045), (0.33, 0.42), (h, h + 0.70), frame)
        bx(m, (-w + 0.07, w - 0.07), (0.36, 0.40), (h + 0.10, h + 0.56), back)
        bx(m, (-w, w), (0.18, 0.44), (h + 0.70, h + 0.76), top)
    return h


@machine2("wb_tool", (2, 1), items=False)
def wb_tool(m):
    """Anvil, hammer, and a pickaxe head hanging on the board."""
    T = bench2(m)
    fk.p_anvil(m, -0.36, -0.04, T)
    fk.p_hammer(m, 0.10, -0.18, T, rad(25))
    m.box((0.50, 0.03, 0.07), (0.34, 0.345, T + 0.36), "iron", rot=(0, rad(8), 0))
    m.box((0.05, 0.03, 0.34), (0.34, 0.35, T + 0.26), "wood_light")
    m.box((0.05, 0.03, 0.40), (-0.30, 0.35, T + 0.30), "g1")
    m.box((0.14, 0.03, 0.05), (-0.30, 0.35, T + 0.14), "wood_dark")
    fk.crate(m, (0.56, -0.02, T), s=0.24, rot=rad(12))
    for i, c in enumerate(("iron", "copper", "gold")):
        m.box((0.16, 0.08, 0.05), (-0.10 + i * 0.03, 0.10, T + 0.025 + i * 0.05), c, taper=0.8)
    for i in range(3):
        m.box((0.12, 0.10, 0.10), (-0.50 + i * 0.5, 0.30, T + 0.81), ("wood_dark", "g3", "wood_dark")[i])


@machine2("wb_part", (2, 1), items=False)
def wb_part(m):
    """A vise, cut gears and stacked plate."""
    T = bench2(m, top="wood_light")
    fk.p_vise(m, -0.50, -0.16, T)
    m.gear(0.15, 0.04, (0.02, -0.12, T + 0.02), "iron", teeth=8, axis="Z")
    m.gear(0.10, 0.04, (0.20, 0.04, T + 0.02), "iron", teeth=6, axis="Z")
    m.gear(0.12, 0.04, (0.04, -0.10, T + 0.06), "steel", teeth=7, axis="Z")
    for i in range(4):
        m.box((0.26, 0.20, 0.03), (0.56, -0.08, T + 0.015 + i * 0.032), "iron", rot=rad(i * 6))
    for i in range(3):
        m.cyl(0.02, 0.40, (-0.10 + i * 0.05, 0.22, T + 0.02), "steel", seg=6, axis="X")
    m.gear(0.14, 0.03, (-0.40, 0.345, T + 0.34), "g3", teeth=8, axis="Y")
    m.gear(0.10, 0.03, (-0.14, 0.345, T + 0.30), "g3", teeth=6, axis="Y")
    m.box((0.30, 0.03, 0.05), (0.40, 0.345, T + 0.34), "iron")
    m.box((0.22, 0.14, 0.12), (0.50, 0.30, T + 0.82), "toolred")
    m.box((0.08, 0.04, 0.03), (0.50, 0.30, T + 0.895), "g5")


@machine2("wb_machine", (2, 1), items=False)
def wb_machine(m):
    """A steel desk with drawers and wall cabinets, a plan spread out, a small machine half built."""
    T = bench2(m, top="g2", frame="g5", shelf=False)
    for x in (-0.60, 0.60):
        bx(m, (x - 0.24, x + 0.24), (-0.36, 0.36), (0.20, T - 0.08), "g3")
        for z in (0.30, 0.46):
            m.box((0.38, 0.02, 0.12), (x, -0.37, z), "g1")
            m.box((0.10, 0.02, 0.025), (x, -0.385, z), "g5")
    for x in (-0.86, 0.86):
        bx(m, (x - 0.04, x + 0.04), (0.33, 0.42), (T, T + 1.00), "g5")
    bx(m, (-0.92, 0.92), (0.10, 0.44), (T + 0.56, T + 1.00), "g1")
    bx(m, (-0.94, 0.94), (0.08, 0.46), (T + 1.00, T + 1.06), "g5")
    for x in (-0.46, 0.0, 0.46):
        m.box((0.02, 0.012, 0.36), (x, 0.094, T + 0.78), "g5")
    for x in (-0.62, -0.30, 0.16, 0.62):
        m.box((0.02, 0.02, 0.10), (x, 0.086, T + 0.74), "g5")
    m.box((0.46, 0.34, 0.012), (-0.10, -0.06, T + 0.006), "paper", rot=rad(8))
    m.cyl(0.03, 0.40, (0.14, -0.04, T + 0.03), "paper", seg=6, axis="Y", rot=rad(8))
    fk.p_mini_machine(m, 0.56, -0.02, T)
    m.box((0.24, 0.15, 0.13), (-0.62, 0.02, T + 0.065), "toolred")
    m.box((0.10, 0.04, 0.035), (-0.62, 0.02, T + 0.15), "g5")
    fk.p_hammer(m, -0.14, -0.30, T, rad(-20))
    m.cyl(0.04, 0.08, (0.22, 0.20, T + 0.04), "lampg", seg=8)
    m.cyl(0.04, 0.08, (0.32, 0.24, T + 0.04), "spark", seg=8)


@machine2("wb_cook", (2, 1), items=False)
def wb_cook(m):
    """A kitchen table: a pot on the fire, a board, vegetables and bread."""
    T = bench2(m, top="wood_dark", frame="wood", shelf=False)
    fk.p_pot(m, -0.52, 0.0, T)
    m.box((0.36, 0.24, 0.03), (0.0, -0.10, T + 0.015), "wood_light", rot=rad(-8))
    m.box((0.22, 0.03, 0.012), (0.02, -0.12, T + 0.036), "g1", rot=rad(30))
    for x, y, c, r in ((0.30, 0.16, "red", 0.06), (0.40, 0.08, "red", 0.055), (0.20, 0.22, "leaf", 0.06),
                       (0.52, 0.20, "leaf_light", 0.05)):
        m.ico(r, (x, y, T + r * 0.8), c, squash=0.85, jitter=0.1)
    m.box((0.22, 0.12, 0.09), (0.60, -0.18, T + 0.045), "bread", bevel=0.02, rot=rad(15))
    for i, x in enumerate((-0.16, -0.06)):
        m.cyl(0.04, 0.12, (x, 0.24, T + 0.06), "white", seg=8)
        m.cyl(0.042, 0.02, (x, 0.24, T + 0.13), "g3", seg=8)
    m.cyl(0.10, 0.12, (0.72, 0.22, T + 0.06), "brick", seg=8, r2=0.12)
    for k in range(5):
        m.box((0.014, 0.014, 0.20), (0.72 + math.cos(k * 1.3) * 0.04, 0.22 + math.sin(k * 1.3) * 0.04, T + 0.22), "wheat")
        m.ico(0.025, (0.72 + math.cos(k * 1.3) * 0.04, 0.22 + math.sin(k * 1.3) * 0.04, T + 0.33), "wheat_head")
    bx(m, (-0.70, 0.70), (-0.34, 0.34), (0.26, 0.30), "wood")


@machine2("wb_elec", (2, 1), items=False)
def wb_elec(m):
    """A dark bench under a lamp: a circuit board, a reel of wire, a meter."""
    T = bench2(m, top="navy", frame="wood_dark", back="g2")
    fk.p_pcb(m, -0.10, -0.12, T)
    m.cyl(0.12, 0.14, (-0.56, 0.02, T + 0.07), "copper", seg=10)
    for z in (0.0, 0.14):
        m.cyl(0.15, 0.02, (-0.56, 0.02, T + z + 0.01), "g3", seg=10)
    bx(m, (0.40, 0.70), (-0.14, 0.14), (T, T + 0.20), "g2")
    with on(m, "S", 0.55, -0.14, T + 0.11):
        m.box((0.22, 0.02, 0.10), (0, -0.01, 0), "hole")
        m.box((0.16, 0.014, 0.03), (0, -0.022, 0), "lampg")
    m.box((0.30, 0.025, 0.025), (0.14, -0.22, T + 0.03), "g5", rot=rad(35))
    m.box((0.08, 0.035, 0.035), (0.05, -0.285, T + 0.03), "toolred", rot=rad(35))
    m.pipe([(0.60, 0.36, T + 0.76), (0.60, 0.20, T + 0.90), (0.40, 0.0, T + 0.86)], 0.022, "g5", seg=6)
    m.cyl(0.10, 0.10, (0.36, -0.04, T + 0.82), "spark", seg=8, r2=0.04)
    for i, c in enumerate(("red", "spark", "lampg", "water")):
        m.cyl(0.05, 0.10, (-0.60 + i * 0.16, 0.30, T + 0.81), c, seg=8)
    with on(m, "S", -0.30, 0.36, T + 0.34):
        buttons(m, ("lampg", "spark", "red"))


@machine2("wb_furn", (2, 1), items=False)
def wb_furn(m):
    """A joiner's bench: a chair coming together, a saw, tins of paint."""
    T = bench2(m, top="wood_light")
    with m.at((-0.44, -0.04, T), rad(20)):
        for x in (-0.11, 0.11):
            for y in (-0.11, 0.11):
                m.box((0.035, 0.035, 0.22), (x, y, 0.11), "wood")
        m.box((0.28, 0.28, 0.035), (0, 0, 0.235), "wood_dark")
        m.box((0.28, 0.035, 0.26), (0, 0.125, 0.38), "wood")
    m.box((0.44, 0.012, 0.11), (0.20, -0.24, T + 0.07), "g1", rot=(rad(80), 0, rad(-12)))
    m.box((0.12, 0.03, 0.10), (0.44, -0.29, T + 0.03), "wood_dark", rot=rad(-12))
    for x, c in ((0.50, "red"), (0.66, "water"), (0.58, "spark")):
        y = 0.06 if c != "spark" else 0.20
        m.cyl(0.07, 0.13, (x, y, T + 0.065), "g1", seg=8)
        m.cyl(0.062, 0.012, (x, y, T + 0.132), c, seg=8)
    for i in range(3):
        m.box((0.60, 0.10, 0.035), (0.10, 0.16, T + 0.018 + i * 0.037), "wood", rot=rad(i * 4 - 4))
    m.box((0.40, 0.03, 0.30), (-0.30, 0.345, T + 0.34), "wood_light")
    m.box((0.30, 0.012, 0.20), (-0.30, 0.328, T + 0.34), "leaf_light")
    for i in range(3):
        m.box((0.14, 0.12, 0.12), (-0.50 + i * 0.5, 0.30, T + 0.82), ("wood", "wood_dark", "wood")[i])


@machine2("wb_all", (3, 1), items=False)
def wb_all(m):
    """Every bench in one: a long steel station with cabinets overhead and all the tools laid out."""
    w = 1.44
    for x in (-1.20, -0.40, 0.40, 1.20):
        bx(m, (x - 0.30, x + 0.30), (-0.36, 0.36), (0.10, 0.66), "g3")
        for z in (0.26, 0.48):
            m.box((0.50, 0.02, 0.16), (x, -0.37, z), "g1")
            m.box((0.14, 0.02, 0.03), (x, -0.385, z), "g5")
    bx(m, (-w, w), (-0.40, 0.40), (0.0, 0.10), "g5")
    bx(m, (-w - 0.02, w + 0.02), (-0.44, 0.44), (0.66, 0.76), "g2")
    bx(m, (-w - 0.03, w + 0.03), (-0.455, 0.455), (0.69, 0.73), "frame")
    T = 0.76
    for x in (-w + 0.07, 0.0, w - 0.07):
        bx(m, (x - 0.04, x + 0.04), (0.34, 0.43), (T, T + 1.04), "g5")
    bx(m, (-w + 0.04, w - 0.04), (0.38, 0.42), (T, T + 0.60), "g2")
    bx(m, (-w, w), (0.08, 0.44), (T + 0.60, T + 1.06), "g1")
    bx(m, (-w - 0.02, w + 0.02), (0.06, 0.46), (T + 1.06, T + 1.12), "g5")
    for i in range(6):
        x = -1.20 + i * 0.48
        m.box((0.02, 0.012, 0.38), (x - 0.24, 0.074, T + 0.83), "g5")
        m.box((0.02, 0.02, 0.10), (x - 0.04, 0.066, T + 0.78), "g5")
    fk.p_anvil(m, -1.10, -0.06, T)
    fk.p_vise(m, -0.56, -0.18, T)
    fk.p_mini_machine(m, 0.02, -0.02, T)
    fk.p_pcb(m, 0.56, -0.14, T)
    fk.p_pot(m, 1.10, -0.02, T)
    m.box((0.40, 0.28, 0.012), (-0.50, 0.12, T + 0.006), "paper", rot=rad(-6))
    m.box((0.24, 0.15, 0.13), (0.62, 0.14, T + 0.065), "toolred")
    for x, c in ((-1.0, "lampg"), (-0.2, "spark"), (0.6, "lampr")):
        with on(m, "S", x, 0.38, T + 0.30):
            lamp(m, c, r=0.05)
    with on(m, "S", 1.05, 0.38, T + 0.30):
        badge(m, 0.10)
    with on(m, "S", 0.25, 0.38, T + 0.30):
        vent(m, 0.34, 0.24, 4)
