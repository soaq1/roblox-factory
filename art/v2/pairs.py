# v2 pairs: ten machines, each built two ways, to compare.
#
#   through form  the item rides a level conveyor into a tunnel in the machine and out the other side
#                 (foundation D). Hero names without a suffix: crusher, smelter, press, washer, ...
#   open form     no tunnel. A machine that works in a vessel is a tower fed from above by a raised belt,
#                 its product leaving by a slot at the foot. A machine that reshapes the item is an open
#                 frame over a plain level belt, doing its work in plain sight. Hero names end in _x.
#
# Both forms of a vessel machine share one body, so the comparison is of the form and not of the design.
import math
import factorykit as fk
from . import base as _base
from . import hero as _hero
from .base import rad, G, T, TD, W, D, SLIT, SIDES, BX, BY, BZ, gear, side_pipe, side_panel, octa, oct_ring, bx
from .kit import arch_pts
from .hero import sunk_frame
from .works import belt, foundation_t, drop, openpress

fk.PAL.update({"h_water": "#5aa6c8", "h_wood": "#8f6d47", "h_wood_l": "#cfb388", "h_paint": "#2f9e94",
               "h_mix": "#8b877c"})
K = 1.0 / math.cos(math.pi / 8)
FRAME_DROP1 = {"iso": (3.5, 0.50), "side": (3.4, 0.80), "top": (3.2, 0.6), "end": (2.4, 0.80)}
FRAME_DROP2 = {"iso": (4.4, 0.92), "side": (4.0, 1.25), "top": (3.2, 0.6), "end": (3.4, 1.25)}
FRAME_OPEN = {"iso": (3.3, 0.72), "side": (3.4, 0.95), "top": (3.2, 0.6), "end": (2.6, 1.0)}


def register(name, fn, frame=None):
    fn.__name__ = name
    if frame:
        fn.frame = frame
    _hero.HEROES[name] = fn
    return fn


def through(body, foot=None):
    """The through form of a vessel machine: its body on foundation D, on the foot that suits it."""
    return lambda m: body(m, _base.foundation(m, foot=foot))


def raised_feed(m, z):
    """A length of conveyor on a trestle, ending over the machine."""
    with m.at((0, 0, z)):
        belt(m, -1.5, -0.5)
    for x in (-1.34, -0.66):
        for s in SIDES:
            bx(m, (x - 0.06, x + 0.06), tuple(sorted((s * 0.34, s * 0.46))), (0.0, z + 0.02), D, bevel=0.02)
            bx(m, (x - 0.10, x + 0.10), tuple(sorted((s * 0.30, s * 0.50))), (0.0, 0.09), T, bevel=0.025)
        for k in range(1, int(z) + 1):
            m.box((0.07, 0.70, 0.07), (x, 0, z * (k - 0.38) / int(z)), D)


def out_slot(m):
    """The slot at the foot of a tower where the product comes out, and the belt that takes it away."""
    m.prism(arch_pts(0.62, 0.64, hole_top=0.54, hw=0.23, c=0.06, ci=0.03), 0.47, 0.50, "X", D)
    m.box((0.02, 0.46, 0.30), (0.478, 0, 0.40), SLIT)
    belt(m, 0.5, 1.5)


def chute(m, x0, z0, x1, z1, hw=0.15):
    """An open trough down which the charge slides from the end of the feed belt into the machine."""
    m.prism([(x0, z0), (x1, z1), (x1, z1 - 0.05), (x0, z0 - 0.05)], -hw, hw, "Y", D)
    for s in SIDES:
        lo, hi = sorted((s * hw, s * (hw + 0.045)))
        m.prism([(x0, z0 + 0.10), (x1, z1 + 0.10), (x1, z1 - 0.05), (x0, z0 - 0.05)], lo, hi, "Y", G)


def scene(m, feed=1.0, spout=None, items=None):
    """What stands round a tower: the raised feed belt, the chute if there is one, the slot and the belt
    that takes the product away, and whatever is riding on them. It is built turned half round, so the
    feed comes from behind the machine and the product leaves toward the camera."""
    with m.at((0, 0, 0), math.pi):
        out_slot(m)
        raised_feed(m, feed)
        if spout:
            chute(m, -0.50, feed + 0.27, *spout)
        if items:
            items(m)


def tower(body, feed=1.0, spout=None, items=None):
    """The open form of a vessel machine: its body on a tower, fed from above."""
    def build(m):
        body(m, foundation_t(m))
        scene(m, feed, spout, items)
    return build


def styled_t(fn, **kw):
    """Build one of the earlier hero machines on the tower instead of on foundation D."""
    def build(m):
        old, _base.STYLE = _base.STYLE, "t"
        fn(m, **kw)
        _base.STYLE = old
    return build


def lumps(m, pts, size, mk):
    for x, y, z, r in pts:
        m.box(size, (x, y, z), mk, bevel=min(size) * 0.25, rot=r)


def louvre(m, d, yp, x, z, w=0.16, h=0.15):
    """A sunk grille on a side wall."""
    sunk_frame(m, d, yp, x, z, w, h, mk=T)
    m.box((w, 0.008, h), (x, yp + d * 0.002, z), SLIT)
    for i in range(3):
        m.box((w, 0.02, 0.022), (x, yp + d * 0.012, z + (i - 1) * 0.048), G)


def handwheel(m, d, yp, x, z, r=0.12):
    """A spoked wheel on a side wall, for setting something by hand."""
    y0, y1 = sorted((yp + d * 0.004, yp + d * 0.028))
    ro, ri = r, r * 0.76
    for j in range(12):
        a0, a1 = math.pi * j / 6, math.pi * (j + 1) / 6
        m.prism([(x + ro * math.cos(a0), z + ro * math.sin(a0)), (x + ro * math.cos(a1), z + ro * math.sin(a1)),
                 (x + ri * math.cos(a1), z + ri * math.sin(a1)), (x + ri * math.cos(a0), z + ri * math.sin(a0))],
                y0, y1, "Y", T)
    m.box((2 * ri + 0.01, 0.016, 0.032), (x, yp + d * 0.014, z), T)
    m.box((0.032, 0.016, 2 * ri + 0.01), (x, yp + d * 0.014, z), T)
    m.cyl(0.036, 0.036, (x, yp + d * 0.018, z), "h_lite", seg=8, axis="Y")


def pedestals(m, hw=0.44, top=0.62):
    """The two blocks an open-frame machine stands on, one astride each rail of the belt."""
    for d in SIDES:
        bx(m, (-hw - 0.03, hw + 0.03), tuple(sorted((d * 0.36, d * 0.50))), (0.0, 0.15), T, bevel=0.035)
        bx(m, (-hw, hw), tuple(sorted((d * 0.33, d * 0.485))), (0.10, top), G, bevel=0.04)


# ============================ VESSEL MACHINES ============================
def washer_body(m, Z):
    """Washer: an eight-sided tub of water as wide as the body, with a paddle wheel turning in it, its
    shaft carried in a bearing on each side of the rim. A porthole in each side wall shows the water."""
    for d in SIDES:
        yp = side_panel(m, d, w=0.50, h=0.30, z=Z - 0.24)
        m.cyl(0.105, 0.03, (0, yp, Z - 0.24), T, seg=12, axis="Y")           # porthole
        m.cyl(0.078, 0.012, (0, yp + d * 0.004, Z - 0.24), "h_water", seg=12, axis="Y")
    bx(m, (-0.43, 0.43), (-0.37, 0.37), (Z - 0.02, Z + 0.07), G, bevel=0.03)
    oct_ring(m, 0.43, 0.06, Z + 0.05, Z + 0.40, G)
    octa(m, 0.40, 0.40, Z + 0.05, Z + 0.10, D)
    octa(m, 0.375, 0.375, Z + 0.10, Z + 0.31, "h_water")
    oct_ring(m, 0.455, 0.10, Z + 0.37, Z + 0.44, D)
    gear(m, 0.24, 0.40, (0, 0, Z + 0.42), T, teeth=8, root=0.52, base=0.30, tip=0.16)
    m.cyl(0.115, 0.44, (0, 0, Z + 0.42), D, seg=8, axis="Y")
    m.cyl(0.05, 0.84, (0, 0, Z + 0.42), "h_lite", seg=8, axis="Y")
    for d in SIDES:
        m.box((0.20, 0.10, 0.15), (0, d * 0.40, Z + 0.44), G, bevel=0.025)   # bearing on the rim


def kiln_body(m, Z):
    """Kiln: a banded eight-sided drum that draws in to a neck, like a bottle kiln, with the fire showing
    down the neck. Each side wall has a stoke hole with the fire set back behind bars."""
    for d in SIDES:
        yp = side_panel(m, d, w=0.52, h=0.34, z=Z - 0.27)
        sunk_frame(m, d, yp, 0, Z - 0.27, 0.24, 0.16, t=0.04, mk=T)
        m.box((0.24, 0.008, 0.16), (0, yp + d * 0.002, Z - 0.27), "h_glow")
        for i in range(3):
            m.box((0.24, 0.018, 0.022), (0, yp + d * 0.024, Z - 0.27 + (i - 1) * 0.05), TD)
    bx(m, (-0.45, 0.45), (-0.41, 0.41), (Z - 0.02, Z + 0.07), D, bevel=0.025)
    octa(m, 0.40, 0.40, Z + 0.05, Z + 0.40, G)
    for zz in (Z + 0.13, Z + 0.32):
        octa(m, 0.416, 0.416, zz - 0.022, zz + 0.022, D)
    octa(m, 0.40, 0.25, Z + 0.40, Z + 0.62, G)
    octa(m, 0.25, 0.21, Z + 0.62, Z + 0.74, G)
    oct_ring(m, 0.26, 0.085, Z + 0.72, Z + 0.80, D)
    octa(m, 0.176, 0.176, Z + 0.70, Z + 0.745, "h_glow")


def mixer_body(m, Z, walls=True):
    """Mixer: a wide pan with stirring arms turning in the mix, driven from a gearbox on a bridge that
    spans the pan."""
    for d in (SIDES if walls else ()):
        zc = Z - 0.25
        yp = side_panel(m, d, w=0.46, h=0.34, z=zc)
        for sx in SIDES:                                      # discharge gate: guides, and the gate half raised
            m.box((0.04, 0.03, 0.30), (sx * 0.155, yp + d * 0.013, zc), G)
        m.box((0.27, 0.008, 0.28), (0, yp + d * 0.002, zc), SLIT)
        m.box((0.27, 0.008, 0.11), (0, yp + d * 0.005, zc - 0.085), "h_mix")
        m.box((0.27, 0.02, 0.15), (0, yp + d * 0.011, zc + 0.065), T)
        m.box((0.19, 0.03, 0.032), (0, yp + d * 0.016, zc + 0.02), D)
    bx(m, (-0.43, 0.43), (-0.37, 0.37), (Z - 0.02, Z + 0.07), G, bevel=0.03)
    oct_ring(m, 0.44, 0.06, Z + 0.05, Z + 0.30, G)
    octa(m, 0.40, 0.40, Z + 0.05, Z + 0.10, D)
    octa(m, 0.385, 0.385, Z + 0.10, Z + 0.20, "h_mix")
    oct_ring(m, 0.46, 0.085, Z + 0.27, Z + 0.33, D)
    for r in (45, -45):
        m.box((0.66, 0.07, 0.05), (0, 0, Z + 0.27), T, rot=rad(r))
    for sx in SIDES:
        for sy in SIDES:
            m.box((0.05, 0.16, 0.12), (sx * 0.215, sy * 0.215, Z + 0.21), T, rot=rad(45 * sx * sy))
    m.cyl(0.045, 0.22, (0, 0, Z + 0.36), "h_lite", seg=8)
    for d in SIDES:
        bx(m, (-0.12, 0.12), tuple(sorted((d * 0.35, d * 0.47))), (Z + 0.30, Z + 0.46), D, bevel=0.025)
    bx(m, (-0.10, 0.10), (-0.46, 0.46), (Z + 0.43, Z + 0.56), G, bevel=0.03)
    m.cyl(0.17 * K, 0.18, (0, 0, Z + 0.64), G, seg=8, rot=rad(22.5))
    m.cyl(0.185 * K, 0.045, (0, 0, Z + 0.565), D, seg=8, rot=rad(22.5))
    m.cyl(0.12 * K, 0.06, (0, 0, Z + 0.76), D, seg=8, rot=rad(22.5))


def ore(m):
    lumps(m, [(-1.20, 0.05, 1.39, 0.3), (-0.82, -0.06, 1.39, 1.1)], (0.17, 0.15, 0.13), T)


def ore2(m):
    lumps(m, [(-1.20, 0.05, 2.39, 0.3), (-0.82, -0.06, 2.39, 1.1)], (0.17, 0.15, 0.13), T)


def _crusher_x(m):
    styled_t(_hero.crusher)(m)
    scene(m, 1.0, None, lambda m: (ore(m), lumps(m, [(0.72, 0.07, 0.34, 0.4), (0.80, -0.08, 0.34, 1.0),
          (1.02, 0.02, 0.34, 0.2), (1.12, 0.10, 0.34, 0.9), (1.20, -0.07, 0.34, 1.3)], (0.08, 0.075, 0.065), T)))


def _smelter_x(m):
    styled_t(_hero.smelter, flues=False)(m)
    scene(m, 2.0, (-0.20, 1.80), lambda m: (ore2(m), m.box((0.24, 0.13, 0.09), (1.0, 0, 0.352), "h_steel", bevel=0.02)))


def _washer_items(m):
    lumps(m, [(-1.20, 0.05, 1.37, 0.3), (-0.80, -0.05, 1.37, 1.1)], (0.11, 0.10, 0.09), T)
    lumps(m, [(0.80, 0.05, 0.345, 0.5), (1.15, -0.05, 0.345, 1.2)], (0.11, 0.10, 0.09), "h_steel")


def _kiln_items(m):
    for x in (-1.20, -0.82):
        m.cyl(0.085, 0.36, (x, 0, 2.39), "h_wood", seg=8, axis="X")
    lumps(m, [(0.80, 0.05, 0.35, 0.5), (1.15, -0.05, 0.35, 1.2)], (0.13, 0.11, 0.10), SLIT)


def _mixer_items(m):
    lumps(m, [(-1.20, 0.05, 1.37, 0.3), (-0.80, -0.05, 1.37, 1.1)], (0.12, 0.11, 0.09), "h_wood_l")
    for x in (0.82, 1.16):
        m.box((0.20, 0.20, 0.12), (x, 0, 0.365), "h_mix", bevel=0.02)


register("crusher_x", _crusher_x, FRAME_DROP1)
register("smelter_x", _smelter_x, FRAME_DROP2)
register("washer_x", tower(washer_body, items=_washer_items), FRAME_DROP1)
register("kiln_x", tower(kiln_body, feed=2.0, spout=(-0.19, 1.70), items=_kiln_items), FRAME_DROP2)
register("mixer_x", tower(mixer_body, items=_mixer_items), FRAME_DROP1)
register("washer", through(washer_body, _base.foot_drain))
register("kiln", through(kiln_body, _base.foot_hearth))
register("mixer", through(mixer_body, _base.foot_springs))
register("press_x", openpress, FRAME_OPEN)


# ============================ RESHAPING MACHINES ============================
def saw_blade(m, zc, r):
    gear(m, r, 0.03, (0, 0, zc), "h_steel", teeth=18, root=0.88, base=0.80, tip=0.10)
    m.cyl(0.10, 0.08, (0, 0, zc), D, seg=10, axis="Y")


def saw_hood(m, zc, ro, ri, foot, hw=0.07):
    """The guard over the top half of the blade: a thick arch, its feet running down to `foot`."""
    outer = [(ro * K * math.cos(a), zc + ro * K * math.sin(a)) for a in (rad(22.5 + 45 * i) for i in range(4))]
    inner = [(ri * K * math.cos(a), zc + ri * K * math.sin(a)) for a in (rad(22.5 + 45 * i) for i in range(4))]
    pts = [(ro, foot), (ro, zc)] + outer + [(-ro, zc), (-ro, foot), (-ri, foot), (-ri, zc)] + inner[::-1] + [(ri, zc), (ri, foot)]
    m.prism(pts, -hw, hw, "Y", G)


def saw(m):
    """Sawmill, through form: the blade stands up through the roof between two bearing blocks, under a
    thick guard, with a flywheel on each end of its arbor."""
    Z = _base.foundation(m, foot=_base.foot_bin)
    zc = Z + 0.10
    for d in SIDES:
        yp = side_panel(m, d, w=0.40, h=0.32, z=Z - 0.30)
        handwheel(m, d, yp, 0, Z - 0.30, r=0.125)
        bx(m, (-0.16, 0.16), tuple(sorted((d * 0.13, d * 0.40))), (Z - 0.02, Z + 0.26), G, bevel=0.035)
        m.cyl(0.19, 0.05, (0, d * 0.452, zc), D, seg=12, axis="Y")
        m.cyl(0.07, 0.07, (0, d * 0.455, zc), "h_lite", seg=8, axis="Y")
    m.cyl(0.045, 0.90, (0, 0, zc), "h_lite", seg=8, axis="Y")
    saw_blade(m, zc, 0.34)
    saw_hood(m, zc, 0.43, 0.375, Z - 0.02)


def saw_x(m):
    """Sawmill, open form: a gantry over the belt carries the arbor, and the blade cuts the log as it
    rides underneath."""
    belt(m, -1.5, 1.5)
    pedestals(m)
    zc = 0.75
    for d in SIDES:
        bx(m, (-0.15, 0.15), tuple(sorted((d * 0.33, d * 0.485))), (0.58, 1.22), G, bevel=0.035)
        m.cyl(0.18, 0.04, (0, d * 0.478, zc), D, seg=12, axis="Y")
        m.cyl(0.07, 0.05, (0, d * 0.482, zc), "h_lite", seg=8, axis="Y")
    m.cyl(0.045, 0.80, (0, 0, zc), "h_lite", seg=8, axis="Y")
    saw_blade(m, zc, 0.37)
    saw_hood(m, zc, 0.46, 0.405, zc)
    bx(m, (-0.17, 0.17), (-0.485, 0.485), (1.19, 1.36), G, bevel=0.04)
    m.cyl(0.10, 0.50, (-1.0, 0, 0.405), "h_wood", seg=8, axis="X")
    for s in SIDES:
        m.box((0.46, 0.085, 0.16), (-0.05, s * 0.055, 0.385), "h_wood_l")
        m.box((0.48, 0.09, 0.05), (1.0, s * 0.075, 0.33), "h_wood_l")


def roller(m):
    """Rolling mill, through form: a roll stand on the roof, two housings holding a work roll and a
    backing roll, tied by a cap that carries the screws."""
    Z = _base.foundation(m, foot=_base.foot_anchor)
    for d in SIDES:
        zc = Z - 0.26
        yp = side_panel(m, d, w=0.62, h=0.30, z=zc)
        y0, y1 = sorted((yp, yp + d * 0.022))                 # pinion cover: one long lozenge, a boss on each shaft
        m.prism([(-0.26, zc - 0.05), (-0.20, zc - 0.11), (0.20, zc - 0.11), (0.26, zc - 0.05), (0.26, zc + 0.05),
                 (0.20, zc + 0.11), (-0.20, zc + 0.11), (-0.26, zc + 0.05)], y0, y1, "Y", T)
        for sx in SIDES:
            m.cyl(0.072, 0.03, (sx * 0.135, yp + d * 0.017, zc), D, seg=12, axis="Y")
            m.cyl(0.04, 0.034, (sx * 0.135, yp + d * 0.019, zc), "h_lite", seg=8, axis="Y")
        bx(m, (-0.21, 0.21), tuple(sorted((d * 0.25, d * 0.42))), (Z - 0.02, Z + 0.60), G, bevel=0.035)
        m.cyl(0.085, 0.07, (0, d * 0.30, Z + 0.755), D, seg=6)
        m.cyl(0.045, 0.14, (0, d * 0.30, Z + 0.82), "h_lite", seg=6)
    m.cyl(0.11, 0.56, (0, 0, Z + 0.14), "h_steel", seg=12, axis="Y")
    m.cyl(0.15, 0.56, (0, 0, Z + 0.40), "h_lite", seg=12, axis="Y")
    bx(m, (-0.23, 0.23), (-0.43, 0.43), (Z + 0.56, Z + 0.73), G, bevel=0.04)
    bx(m, (-0.36, 0.36), (-0.20, 0.20), (Z - 0.02, Z + 0.035), D, bevel=0.0)


def roller_x(m):
    """Rolling mill, open form: the roll stand straddles the belt and the ingot is squeezed into a bar as
    it passes between the rolls."""
    belt(m, -1.5, 1.5)
    for d in SIDES:
        bx(m, (-0.27, 0.27), tuple(sorted((d * 0.36, d * 0.50))), (0.0, 0.15), T, bevel=0.035)
        bx(m, (-0.23, 0.23), tuple(sorted((d * 0.335, d * 0.485))), (0.10, 1.14), G, bevel=0.04)
        m.box((0.26, 0.012, 0.66), (0, d * 0.487, 0.63), D)
        for z, r in ((0.47, 0.075), (0.77, 0.10)):
            m.cyl(r, 0.014, (0, d * 0.492, z), G, seg=10, axis="Y")
        m.cyl(0.09, 0.07, (0, d * 0.30, 1.315), D, seg=6)
        m.cyl(0.048, 0.16, (0, d * 0.30, 1.39), "h_lite", seg=6)
    m.cyl(0.12, 0.68, (0, 0, 0.47), "h_steel", seg=12, axis="Y")
    m.cyl(0.17, 0.68, (0, 0, 0.77), "h_lite", seg=12, axis="Y")
    bx(m, (-0.25, 0.25), (-0.49, 0.49), (1.10, 1.28), G, bevel=0.04)
    m.box((0.26, 0.15, 0.09), (-1.0, 0, 0.352), "h_steel", bevel=0.02)
    m.box((0.22, 0.15, 0.09), (-0.24, 0, 0.352), "h_steel")
    m.box((0.34, 0.10, 0.045), (0.26, 0, 0.329), "h_steel")
    m.box((0.56, 0.10, 0.045), (1.0, 0, 0.329), "h_steel")


def tank(m, x, y, z0, r=0.16, h=0.36):
    m.cyl(r * K, h, (x, y, z0 + h / 2), G, seg=8, rot=rad(22.5))
    m.cyl(r * K * 1.05, 0.09, (x, y, z0 + h * 0.42), "h_paint", seg=8, rot=rad(22.5))
    m.cyl(r * K, 0.07, (x, y, z0 + h + 0.035), D, seg=8, r2=r * K * 0.5, rot=rad(22.5))


def painter(m):
    """Painter, through form: two paint tanks on the roof with the valve block between them, and a sight
    glass on each side wall."""
    Z = _base.foundation(m, foot=_base.foot_drain)
    for d in SIDES:
        yp = side_panel(m, d, w=0.62, h=0.26, z=Z - 0.26)
        sunk_frame(m, d, yp, 0, Z - 0.26, 0.34, 0.09, mk=T)
        m.box((0.34, 0.008, 0.09), (0, yp + d * 0.002, Z - 0.26), "h_paint")
    bx(m, (-0.45, 0.45), (-0.34, 0.34), (Z - 0.02, Z + 0.08), G, bevel=0.03)
    for sx in SIDES:
        tank(m, sx * 0.25, 0, Z + 0.06, r=0.18, h=0.42)
    bx(m, (-0.085, 0.085), (-0.14, 0.14), (Z + 0.06, Z + 0.30), D, bevel=0.025)


def painter_x(m):
    """Painter, open form: a portal over the belt with the paint tanks on top and a bar of nozzles under
    its beam, spraying whatever passes."""
    belt(m, -1.5, 1.5)
    for d in SIDES:
        bx(m, (-0.23, 0.23), tuple(sorted((d * 0.36, d * 0.50))), (0.0, 0.15), T, bevel=0.035)
    m.prism(arch_pts(0.97, 1.16, hole_top=0.94, hw=0.335, c=0.06, ci=0.09), -0.19, 0.19, "X", G)
    for d in SIDES:
        tank(m, 0, d * 0.28, 1.15)
    bx(m, (-0.10, 0.10), (-0.125, 0.125), (1.15, 1.36), D, bevel=0.025)
    m.box((0.11, 0.52, 0.07), (0, 0, 0.905), D)
    for y in (-0.17, 0.0, 0.17):
        m.cyl(0.018, 0.09, (0, y, 0.825), "h_lite", seg=8, r2=0.048)
    m.box((0.22, 0.22, 0.20), (-1.0, 0, 0.405), "h_lite", bevel=0.02)
    for x in (0.0, 1.0):
        m.box((0.22, 0.22, 0.20), (x, 0, 0.405), "h_paint", bevel=0.02)


def link(m, d, p, q, half, xh, mk):
    (y0, z0), (y1, z1) = p, q
    L = math.hypot(y1 - y0, z1 - z0)
    ny, nz = -(z1 - z0) / L * half, (y1 - y0) / L * half
    m.prism([(d * (y0 + ny), z0 + nz), (d * (y1 + ny), z1 + nz), (d * (y1 - ny), z1 - nz), (d * (y0 - ny), z0 - nz)],
            -xh, xh, "X", mk)


def arm(m, d, base, elbow, wrist):
    """A two-jointed arm on a turret. `base` is the (y, z) of the turret's foot on the d = +1 side."""
    yb, zb = base
    m.cyl(0.13 * K, 0.10, (0, d * yb, zb + 0.05), D, seg=8, rot=rad(22.5))
    m.box((0.14, 0.16, 0.14), (0, d * yb, zb + 0.15), G, bevel=0.02)
    sh = (yb, zb + 0.21)
    m.cyl(0.095, 0.21, (0, d * yb, sh[1]), T, seg=8, axis="X")
    link(m, d, sh, elbow, 0.055, 0.07, G)
    m.cyl(0.08, 0.19, (0, d * elbow[0], elbow[1]), T, seg=8, axis="X")
    link(m, d, elbow, wrist, 0.042, 0.052, G)
    m.cyl(0.058, 0.15, (0, d * wrist[0], wrist[1]), T, seg=8, axis="X")
    m.box((0.11, 0.04, 0.14), (0, d * (wrist[0] - 0.025), wrist[1] - 0.105), D)


def assembler(m):
    """Assembler, through form: two arms on the roof work on a part held on a turntable between them."""
    Z = _base.foundation(m, foot=_base.foot_beams)
    for d in SIDES:
        zc = Z - 0.25
        yp = side_panel(m, d, w=0.58, h=0.30, z=zc)
        sunk_frame(m, d, yp, 0, zc, 0.40, 0.17, mk=T)         # display: a dark screen with three lines on it
        m.box((0.40, 0.008, 0.17), (0, yp + d * 0.002, zc), SLIT)
        for i, w in enumerate((0.30, 0.18, 0.24)):
            m.box((w, 0.006, 0.02), (0, yp + d * 0.008, zc + (1 - i) * 0.045), "h_line")
    bx(m, (-0.45, 0.45), (-0.40, 0.40), (Z - 0.02, Z + 0.07), G, bevel=0.03)
    octa(m, 0.19, 0.19, Z + 0.05, Z + 0.13, D)
    m.box((0.20, 0.18, 0.10), (0, 0, Z + 0.18), "h_steel", bevel=0.02)
    m.box((0.12, 0.08, 0.06), (0, 0, Z + 0.26), "h_lite")
    for d in SIDES:
        arm(m, d, (0.29, Z + 0.06), (0.25, Z + 0.72), (0.085, Z + 0.43))


def assembler_x(m):
    """Assembler, open form: an arm on a pedestal each side of the belt, the two fitting a part onto the
    frame that has stopped between them."""
    belt(m, -1.5, 1.5)
    pedestals(m)
    for d in SIDES:
        arm(m, d, (0.41, 0.62), (0.34, 1.34), (0.095, 0.78))
    for x, done in ((-1.0, False), (0.0, True), (1.0, True)):
        m.box((0.30, 0.26, 0.16), (x, 0, 0.385), "h_steel", bevel=0.02)
        if done:
            m.box((0.14, 0.09, 0.07), (x, 0, 0.50 + (0.10 if x == 0.0 else 0.0)), "h_lite")


for name, fn, frame in (("saw", saw, None), ("saw_x", saw_x, FRAME_OPEN), ("roller", roller, None),
                        ("roller_x", roller_x, FRAME_OPEN), ("painter", painter, None),
                        ("painter_x", painter_x, FRAME_OPEN), ("assembler", assembler, None),
                        ("assembler_x", assembler_x, FRAME_OPEN)):
    register(name, fn, frame)

PAIRS = ("crusher", "smelter", "washer", "kiln", "mixer", "press", "saw", "roller", "painter", "assembler")
