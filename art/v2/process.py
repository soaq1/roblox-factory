# v2 process machines: one material in at the west end, one product out at the east.
# Each is a body on foundation D. Its foot and the fitting on its side walls suit its own work, so that no
# two machines share the same pair.
import math
from . import hero as _hero
from . import pairs as _pairs
from .kit import machine2
from .d import *          # noqa: F401,F403  (the shared parts are this file's vocabulary)
from .d import through, panel, lamps, crank, hatch, lever, drawers, vent_round, peep, strip, neck, K

machine2("smelter")(_hero.smelter)
machine2("crusher")(_hero.crusher)
machine2("press")(_hero.press)
machine2("sawmill")(_pairs.saw)
machine2("painter")(_pairs.painter)
through("washer", _pairs.washer_body, foot_drain)
through("kiln", _pairs.kiln_body, foot_hearth)


def stonecutter(m, Z):
    """Stone cutter: a gang saw. Three long blades hang in a sash inside an open cage and work down
    through the block lying on the bed."""
    for d in SIDES:
        yp, z = panel(m, d, Z)
        lamps(m, d, yp, z)
    neck(m, Z, 0.46, 0.39)
    m.box((0.52, 0.38, 0.24), (0, 0, Z + 0.18), "h_stone", bevel=0.02)
    for sx in SIDES:
        for sy in SIDES:
            bx(m, tuple(sorted((sx * 0.36, sx * 0.46))), tuple(sorted((sy * 0.28, sy * 0.38))), (Z + 0.04, Z + 0.72), G, bevel=0.025)
        bx(m, tuple(sorted((sx * 0.35, sx * 0.47))), (-0.39, 0.39), (Z + 0.66, Z + 0.78), G, bevel=0.03)
        m.box((0.07, 0.50, 0.09), (sx * 0.29, 0, Z + 0.52), D)
    for sy in SIDES:
        bx(m, (-0.47, 0.47), tuple(sorted((sy * 0.27, sy * 0.39))), (Z + 0.66, Z + 0.78), G, bevel=0.03)
    for y in (-0.12, 0.0, 0.12):
        m.box((0.64, 0.016, 0.30), (0, y, Z + 0.40), "h_steel")


def wiredraw(m, Z):
    """Wire drawer: the drawn wire winds onto one big reel, carried in a bearing stand each side."""
    for d in SIDES:
        yp, z = panel(m, d, Z, w=0.56)
        crank(m, d, yp, -0.07, z)
        bx(m, (-0.13, 0.13), tuple(sorted((d * 0.30, d * 0.42))), (Z - 0.02, Z + 0.46), G, bevel=0.035)
        m.cyl(0.31, 0.045, (0, d * 0.245, Z + 0.38), D, seg=16, axis="Y")
    neck(m, Z, 0.44, 0.40, 0.05)
    m.cyl(0.235, 0.45, (0, 0, Z + 0.38), "h_copper", seg=16, axis="Y")
    m.cyl(0.05, 0.86, (0, 0, Z + 0.38), "h_lite", seg=8, axis="Y")


def mill(m, Z):
    """Mill: a runner stone turning on a bed stone, fed from a small hopper held over its eye on four
    posts."""
    for d in SIDES:
        yp, z = panel(m, d, Z, w=0.48)
        hatch(m, d, yp, 0, z)
    neck(m, Z, 0.44, 0.40, 0.05)
    octa(m, 0.41, 0.41, Z + 0.03, Z + 0.20, T)
    m.cyl(0.37, 0.13, (0, 0, Z + 0.265), "h_stone", seg=16)
    m.cyl(0.38, 0.03, (0, 0, Z + 0.215), D, seg=16)
    m.cyl(0.085, 0.02, (0, 0, Z + 0.325), SLIT, seg=10)
    for sx in SIDES:
        for sy in SIDES:
            m.box((0.055, 0.055, 0.48), (sx * 0.27, sy * 0.255, Z + 0.44), D)
    frustum(m, ((-0.07, 0.07), (-0.07, 0.07)), ((-0.25, 0.25), (-0.25, 0.25)), Z + 0.36, Z + 0.70, G)
    for s in SIDES:
        m.box((0.60, 0.06, 0.07), (0, s * 0.255, Z + 0.705), D)
        m.box((0.06, 0.45, 0.07), (s * 0.27, 0, Z + 0.705), D)
    m.box((0.45, 0.45, 0.01), (0, 0, Z + 0.695), "h_wood_l")


def briquetter(m, Z):
    """Briquetter: two opposed rams squeeze the charge in a die block between them, the whole thing
    held together by four tie rods."""
    for d in SIDES:
        yp, z = panel(m, d, Z)
        lever(m, d, yp, 0, z)
    neck(m, Z, 0.46, 0.38, 0.05)
    bx(m, (-0.15, 0.15), (-0.30, 0.30), (Z - 0.02, Z + 0.50), D, bevel=0.03)
    for sx in SIDES:
        m.cyl(0.19 * K, 0.22, (sx * 0.33, 0, Z + 0.26), G, seg=8, axis="X", rot=(rad(22.5), 0, 0))
        m.cyl(0.215 * K, 0.05, (sx * 0.445, 0, Z + 0.26), D, seg=8, axis="X", rot=(rad(22.5), 0, 0))
        m.cyl(0.09, 0.10, (sx * 0.19, 0, Z + 0.26), "h_steel", seg=10, axis="X")
        bx(m, tuple(sorted((sx * 0.25, sx * 0.41))), (-0.16, 0.16), (Z - 0.02, Z + 0.10), G, bevel=0.02)
    for sy in SIDES:
        for z in (Z + 0.10, Z + 0.42):
            m.cyl(0.03, 0.94, (0, sy * 0.25, z), "h_lite", seg=8, axis="X")


def oilpress(m, Z):
    """Oil press: a screw bears down through a yoke onto a banded cage of seed, and the oil gathers in
    the pan round its foot."""
    for d in SIDES:
        yp, z = panel(m, d, Z)
        strip(m, d, yp, z, "h_oil")
        bx(m, (-0.07, 0.07), tuple(sorted((d * 0.33, d * 0.43))), (Z - 0.02, Z + 0.86), G, bevel=0.025)
    neck(m, Z, 0.44, 0.40, 0.05)
    oct_ring(m, 0.40, 0.05, Z + 0.03, Z + 0.15, D)
    octa(m, 0.355, 0.355, Z + 0.03, Z + 0.09, "h_oil")
    octa(m, 0.25, 0.25, Z + 0.08, Z + 0.50, "h_wood")
    for z in (Z + 0.16, Z + 0.29, Z + 0.42):
        octa(m, 0.265, 0.265, z - 0.02, z + 0.02, D)
    octa(m, 0.23, 0.23, Z + 0.50, Z + 0.56, D)
    m.cyl(0.055, 0.50, (0, 0, Z + 0.80), "h_lite", seg=8)
    for i in range(6):
        m.cyl(0.072, 0.018, (0, 0, Z + 0.60 + i * 0.045), "h_steel", seg=8)
    bx(m, (-0.09, 0.09), (-0.44, 0.44), (Z + 0.82, Z + 0.95), G, bevel=0.03)
    m.cyl(0.11, 0.07, (0, 0, Z + 0.985), D, seg=6)
    m.cyl(0.032, 0.66, (0, 0, Z + 1.07), T, seg=8, axis="X")
    for sx in SIDES:
        m.cyl(0.05, 0.07, (sx * 0.33, 0, Z + 1.07), D, seg=8, axis="X")


def lathe(m, Z):
    """Lathe: the work spins between a headstock and a tailstock while a tool post on the cross slide
    closes on it from each side."""
    for d in SIDES:
        yp, z = panel(m, d, Z)
        drawers(m, d, yp, 0, z)
    neck(m, Z, 0.46, 0.38, 0.05)
    bx(m, (-0.47, 0.47), (-0.17, 0.17), (Z + 0.02, Z + 0.15), D, bevel=0.03)
    for sx in SIDES:
        bx(m, tuple(sorted((sx * 0.25, sx * 0.47))), (-0.26, 0.26), (Z + 0.10, Z + 0.56), G, bevel=0.045)
        m.cyl(0.14, 0.07, (sx * 0.225, 0, Z + 0.36), D, seg=12, axis="X")
    m.cyl(0.075, 0.40, (0, 0, Z + 0.36), "h_steel", seg=12, axis="X")
    bx(m, (-0.09, 0.09), (-0.34, 0.34), (Z + 0.13, Z + 0.22), G, bevel=0.02)
    for sy in SIDES:
        bx(m, (-0.055, 0.055), tuple(sorted((sy * 0.10, sy * 0.25))), (Z + 0.22, Z + 0.40), T, bevel=0.02)


def caster(m, Z):
    """Caster: a ladle of metal hangs on trunnions between two posts, over the mould it pours into."""
    for d in SIDES:
        yp, z = panel(m, d, Z, w=0.42, h=0.32)
        peep(m, d, yp, 0, z)
        bx(m, (-0.11, 0.11), tuple(sorted((d * 0.32, d * 0.43))), (Z - 0.02, Z + 0.66), G, bevel=0.03)
        m.cyl(0.055, 0.12, (0, d * 0.30, Z + 0.55), "h_lite", seg=8, axis="Y")
    neck(m, Z, 0.46, 0.40, 0.05)
    bx(m, (-0.36, 0.36), (-0.22, 0.22), (Z + 0.02, Z + 0.15), D, bevel=0.02)
    for sx in SIDES:
        m.box((0.20, 0.30, 0.02), (sx * 0.19, 0, Z + 0.135), "h_glow")
        m.box((0.03, 0.34, 0.035), (sx * 0.305, 0, Z + 0.155), T)
        m.box((0.03, 0.34, 0.035), (sx * 0.075, 0, Z + 0.155), T)
        for sy in SIDES:
            m.box((0.26, 0.03, 0.035), (sx * 0.19, sy * 0.165, Z + 0.155), T)
    octa(m, 0.19, 0.25, Z + 0.36, Z + 0.70, G)
    oct_ring(m, 0.27, 0.055, Z + 0.68, Z + 0.74, D)
    octa(m, 0.215, 0.215, Z + 0.64, Z + 0.695, "h_glow")
    octa(m, 0.20, 0.20, Z + 0.50, Z + 0.56, D)


def loom(m, Z):
    """Loom: warp runs from a beam at one end to the cloth roll at the other, through two heddle
    frames hung from the top of an open frame."""
    for d in SIDES:
        yp, z = panel(m, d, Z, w=0.48)
        hatch(m, d, yp, 0, z)
        bx(m, (-0.45, 0.45), tuple(sorted((d * 0.31, d * 0.40))), (Z + 0.56, Z + 0.66), G, bevel=0.025)
        for sx in SIDES:
            m.box((0.08, 0.08, 0.60), (sx * 0.40, d * 0.355, Z + 0.28), G)
            m.box((0.12, 0.10, 0.14), (sx * 0.34, d * 0.34, Z + 0.15), D, bevel=0.02)
    neck(m, Z, 0.46, 0.40, 0.05)
    for sx, mk, r in ((-1, "h_lite", 0.085), (1, "h_cloth", 0.11)):
        m.cyl(r, 0.60, (sx * 0.34, 0, Z + 0.15 + (r - 0.085)), mk, seg=10, axis="Y")
    m.box((0.66, 0.56, 0.014), (0, 0, Z + 0.238), "h_cloth")
    for x in (-0.07, 0.07):
        m.box((0.035, 0.62, 0.28), (x, 0, Z + 0.40), D)
    bx(m, (-0.11, 0.11), (-0.40, 0.40), (Z + 0.56, Z + 0.68), G, bevel=0.03)


def gemcutter(m, Z):
    """Gem cutter: a steel lap turns on a pedestal, and a bridge over it holds a stone down onto the
    lap on each side."""
    for d in SIDES:
        yp, z = panel(m, d, Z, w=0.42, h=0.32)
        vent_round(m, d, yp, 0, z)
        bx(m, (-0.09, 0.09), tuple(sorted((d * 0.33, d * 0.43))), (Z - 0.02, Z + 0.56), G, bevel=0.025)
        m.box((0.05, 0.05, 0.20), (0, d * 0.17, Z + 0.37), "h_lite")
        m.cyl(0.0, 0.07, (0, d * 0.17, Z + 0.245), "h_gem", seg=6, r2=0.06)
        m.cyl(0.06, 0.03, (0, d * 0.17, Z + 0.295), "h_gem", seg=6)
    neck(m, Z, 0.44, 0.40, 0.05)
    octa(m, 0.30, 0.26, Z + 0.03, Z + 0.15, D)
    m.cyl(0.31, 0.05, (0, 0, Z + 0.18), "h_steel", seg=16)
    m.cyl(0.10, 0.02, (0, 0, Z + 0.21), D, seg=10)
    bx(m, (-0.10, 0.10), (-0.44, 0.44), (Z + 0.46, Z + 0.60), G, bevel=0.03)
    m.cyl(0.14 * K, 0.12, (0, 0, Z + 0.66), D, seg=8, rot=rad(22.5))


through("stonecutter", stonecutter, foot_drain)
through("wiredraw", wiredraw, foot_anchor)
through("mill", mill, foot_beams)
through("briquetter", briquetter, foot_anchor)
through("oilpress", oilpress, foot_drain)
through("lathe", lathe, foot_bin)
through("caster", caster, foot_hearth)
through("loom", loom, foot_beams)
through("gemcutter", gemcutter, foot_springs)
