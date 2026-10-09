# The kit: sub-assemblies modelled once and put together into machines afterwards (the developer's idea,
# 2026-10-09: "저런 크고 작은 부분들을 미리 모델링해두고, 나중에는 조립하는 방식"). Every piece is built of
# former5's parts, stands on z = z0 at its own origin, and is registered as a hero of its own so that it can
# be drawn alone for the catalogue. A machine is then a layout of these plus the one mass that is its own.
#
#   stacks   k_stack_rise3, k_stack_one, k_stack_pair, k_stack_row2
#   pipes    k_pipe_straight, k_pipe_elbow, k_pipe_valve, k_pipe_bridge
#   drums    k_drum_band, k_drum_cone
#   towers   k_tower2, k_tower3
#   houses   k_house_s, k_house_m, k_house_l
#   mouths   k_mouth_low (the ribbed folding cover of the low grades), k_mouth3 (grade 3)
#
# Joints: a fat duct is 0.105 in radius everywhere; a plenum is 0.36 high and takes a duct in a plain wall
# 0.18 above its foot; a box elbow is 0.28 on a side.
import math
from . import hero as _hero
from . import set2 as s2

RD = 0.105               # the fat duct's radius
PLEN = 0.36              # a plenum's height
DUCT_AT = 0.18           # how high above its foot a plenum takes a duct


def _plenum(m, hx, hy, z0):
    s2.slab(m, hx, hy, z0 - 0.01, z0 + PLEN, 0.04, s2.G, bevel=0.02)
    s2.slab(m, hx + 0.012, hy + 0.012, z0 + PLEN - 0.05, z0 + PLEN + 0.012, s2.cut_to(hx + 0.012, hy + 0.012, (hx, hy, 0.04), 0.012), s2.LT, bevel=0.012)
    return z0 + PLEN


def k_stack_rise3(m, z0=0.0):
    """Stacks, rising three: a plenum and three fat stacks in a row, each taller than the last (former5's)."""
    pz = _plenum(m, 0.46, 0.20, z0)
    for x, top in ((-0.285, 0.90), (0.0, 1.20), (0.285, 1.50)):
        s2.fat_stack(m, x, 0, pz, z0 + top, 0.095, foot=0.035)


def k_stack_one(m, z0=0.0):
    """Stacks, the big one: one fat stack on a broad base."""
    s2.slab(m, 0.28, 0.28, z0 - 0.01, z0 + 0.14, 0.05, s2.G, bevel=0.02)
    s2.slab(m, 0.292, 0.292, z0 + 0.09, z0 + 0.152, s2.cut_to(0.292, 0.292, (0.28, 0.28, 0.05), 0.012), s2.LT, bevel=0.012)
    s2.fat_stack(m, 0, 0, z0 + 0.14, z0 + 1.28, 0.19, foot=0.07)


def k_stack_pair(m, z0=0.0):
    """Stacks, fat and thin: a short plenum with one fat stack and a thinner, shorter one beside it."""
    pz = _plenum(m, 0.36, 0.20, z0)
    s2.fat_stack(m, -0.14, 0, pz, z0 + 1.40, 0.13, foot=0.04)
    s2.fat_stack(m, 0.20, 0, pz, z0 + 0.98, 0.08, foot=0.03)


def k_stack_row2(m, z0=0.0):
    """Stacks, two abreast: a short plenum with two equal stacks."""
    pz = _plenum(m, 0.34, 0.20, z0)
    for x in (-0.16, 0.16):
        s2.fat_stack(m, x, 0, pz, z0 + 1.25, 0.105, foot=0.035)


def _run_x(m, x0, x1, y, z, collars=()):
    m.cyl(RD * s2.K, x1 - x0, ((x0 + x1) / 2, y, z), s2.LT, seg=8, axis="X", rot=(s2.rad(22.5), 0, 0))
    for x in collars:
        m.cyl((RD + 0.022) * s2.K, 0.06, (x, y, z), s2.G, seg=8, axis="X", rot=(s2.rad(22.5), 0, 0))


def _pier(m, x, y, top):
    with m.at((x, y, 0)):
        s2.slab(m, 0.10, 0.13, 0.0, 0.07, 0.03, s2.T, bevel=0.012)
        s2.slab(m, 0.05, 0.075, 0.05, top, 0.015, s2.ST, bevel=0.01)


def _elbow(m, x, y, z):
    with m.at((x, y, 0)):
        s2.slab(m, 0.14, 0.14, z - 0.14, z + 0.14, 0.03, s2.G, bevel=0.02)


def _riser(m, x, y, z0, z1):
    with m.at((x, y, 0)):
        s2.octa(m, RD + 0.05, RD + 0.02, z0 - 0.01, z0 + 0.08, s2.G)
        s2.octa(m, RD, RD, z0 + 0.07, z1, s2.LT)


def k_pipe_straight(m, L=1.1, z=0.45):
    """Pipe, straight: a fat duct on two piers, a collar at each end and one in the middle."""
    _run_x(m, -L / 2, L / 2, 0, z, collars=(-L / 2 + 0.05, 0.0, L / 2 - 0.05))
    for x in (-L / 4, L / 4):
        _pier(m, x, 0, z - RD + 0.01)


def k_pipe_elbow(m, H=0.95, L=0.75, z0=0.0):
    """Pipe, one turn: up out of a foot, through a box elbow, and away level."""
    _riser(m, 0, 0, z0, z0 + H - 0.13)
    _elbow(m, 0, 0, z0 + H)
    _run_x(m, 0.14 - 0.01, L, 0, z0 + H, collars=((0.14 + L) / 2,))


def k_pipe_valve(m, L=1.2, z=0.45):
    """Pipe, with a valve: a fat duct through a valve box with a five-sided handwheel, the box on a pier."""
    _run_x(m, -L / 2, L / 2, 0, z, collars=(-L / 2 + 0.05, -L / 4 - 0.02, L / 4 + 0.02, L / 2 - 0.05))
    with m.at((0, 0, 0)):
        s2.slab(m, 0.13, 0.13, z - 0.14, z + 0.14, 0.03, s2.G, bevel=0.02)
    _pier(m, 0, 0, z - 0.13)
    with s2.on_side(m, -1, -0.13, z, xc=0.0):
        s2.handwheel(m, 0.14)


def k_pipe_bridge(m, H=1.15, L=0.95, z0=0.0):
    """Pipe, over: up, across through two box elbows, and down again (the former's duct)."""
    for x in (-L / 2, L / 2):
        _riser(m, x, 0, z0, z0 + H - 0.13)
        _elbow(m, x, 0, z0 + H)
    _run_x(m, -L / 2 + 0.13, L / 2 - 0.13, 0, z0 + H, collars=(-L / 6, L / 6))


def k_drum_band(m, z0=0.0):
    """Drum, banded: an upright eight-sided drum with two hoops, a drawn-in top and a capped vent."""
    s2.octa(m, 0.23, 0.21, z0, z0 + 0.08, s2.T)
    s2.octa(m, 0.20, 0.20, z0 + 0.07, z0 + 1.05, s2.G)
    for z in (0.26, 0.82):
        s2.octa(m, 0.213, 0.213, z0 + z, z0 + z + 0.06, s2.TD)
    s2.octa(m, 0.20, 0.10, z0 + 1.04, z0 + 1.18, s2.G)
    s2.octa(m, 0.055, 0.055, z0 + 1.17, z0 + 1.27, s2.ST)
    s2.octa(m, 0.075, 0.075, z0 + 1.26, z0 + 1.30, s2.TD)


def k_drum_cone(m, z0=0.0):
    """Drum, coned: a wider banded drum under a cone, a small stack out of the cone's top."""
    s2.octa(m, 0.29, 0.27, z0 - 0.01, z0 + 0.07, s2.G)
    s2.octa(m, 0.26, 0.26, z0 + 0.06, z0 + 0.62, s2.LT)
    for z in (0.16, 0.46):
        s2.octa(m, 0.273, 0.273, z0 + z, z0 + z + 0.06, s2.G)
    s2.octa(m, 0.26, 0.11, z0 + 0.61, z0 + 0.83, s2.G)
    s2.fat_stack(m, 0, 0, z0 + 0.82, z0 + 1.30, 0.085, foot=0.03)


def _tower(m, paint, hx, hy, levels, z0=0.0):
    rx, ry = hx - 0.07, hy - 0.05
    top = levels[-1]
    for sx in s2.SIDES:
        for sy in s2.SIDES:
            m.box((0.15, 0.14, 0.03), (sx * (rx - 0.0375), sy * (ry - 0.034), z0 + 0.015), s2.G, bevel=0.008)
            for dx, dy in ((0.0, 0.0), (-0.075, 0.0), (0.0, -0.068)):
                m.box((0.044, 0.044, top + 0.02 - 0.02), (sx * (rx + dx), sy * (ry + dy), z0 + (top + 0.04) / 2), s2.LT, bevel=0.008)
    for z in levels:
        s2.frame_ring(m, hx, hy, z0 + z, z0 + z + 0.15, 0.17, paint)
        s2.frame_ring(m, hx - 0.007, hy - 0.007, z0 + z - 0.03, z0 + z + 0.004, 0.15, s2.TD)


def k_tower2(m, paint=None, z0=0.0):
    """Tower, two frames: four bundles of three rods carrying two painted frames."""
    _tower(m, paint or s2.PY, 0.60, 0.54, (0.85, 1.75), z0)


def k_tower3(m, paint=None, z0=0.0):
    """Tower, three frames: the former's, four bundles of three rods carrying three painted frames."""
    _tower(m, paint or s2.PY, 0.545, 0.49, (0.92, 1.58, 2.46), z0)


def _house(m, paint, hx, hy, doors, louvre, panels):
    """A cabinet under a painted body, standing on a dark footing: on its front, `doors` framed doors, a
    louvre if asked for, corner bolts; on the body's front, panels of the widths given, and a badge."""
    Zc, Zr = 0.665, 1.10
    body = (hx - 0.08, hy - 0.08, 0.045)
    s2.slab(m, hx - 0.01, hy - 0.01, 0.0, 0.16, 0.03, s2.T, bevel=0.012)
    s2.slab(m, hx, hy, 0.12, Zc, 0.035, s2.G, bevel=0.02)
    s2.slab(m, body[0], body[1], Zc - 0.01, Zr, body[2], paint, bevel=0.022)
    x = -hx + 0.30
    for _ in range(doors):
        with s2.on_side(m, -1, -hy, 0.40, xc=x):
            s2.framed(m, 0.36, 0.42, s2.LT)
            m.box((0.022, 0.11, 0.022), (0.11, 0, 0.02), s2.TD)
        x += 0.42
    if louvre:
        with s2.on_side(m, -1, -hy, 0.40, xc=hx - 0.42):
            s2.vent(m, 0.31, 0.21)
    for xb in (-hx + 0.07, hx - 0.07):
        for z in (0.21, 0.59):
            with s2.on_side(m, -1, -hy, z, xc=xb):
                m.cyl(0.028, 0.02, (0, 0, 0.008), s2.LT, seg=6)
    x = -body[0] + 0.14
    for w in panels:
        with s2.on_side(m, -1, -body[1], 0.88, xc=x + w / 2):
            s2.framed(m, w, 0.28)
        x += w + 0.06
    with s2.on_side(m, -1, -body[1], 0.88, xc=body[0] - 0.17):
        m.cyl(0.085, 0.022, (0, 0, 0.008), "h_red", seg=6)
        m.cyl(0.045, 0.012, (0, 0, 0.024), "h_white", seg=6)
    return Zr


def k_house_s(m, paint=None):
    """House, small: a cabinet with one door under a painted body with one panel and a badge."""
    return _house(m, paint or s2.PY, 0.50, 0.40, 1, False, (0.30,))


def k_house_m(m, paint=None):
    """House, middling: the former's, two doors and a louvre, five panels and a badge."""
    return _house(m, paint or s2.PY, 0.86, 0.47, 2, True, (0.20, 0.28, 0.14, 0.14, 0.14))


def k_house_l(m, paint=None):
    """House, long: two doors and a louvre, a wide panel, a narrow one and a badge."""
    return _house(m, paint or s2.PY, 1.10, 0.47, 2, True, (0.52, 0.32, 0.14, 0.14))


def _stub_wall(m, hy=0.60, top=1.0):
    s2.slab(m, 0.17, hy, 0.0, top, 0.035, s2.G, bevel=0.02)


def k_mouth_low(m):
    """Mouth of the low grades: the ribbed folding cover over the belt (the smelter's)."""
    s2.run(m, -0.9, 0.02, braces=(-0.75,))
    s2.cover(m, 0.0, -1)
    with m.at((0.19, 0, 0)):
        _stub_wall(m, 0.50, 0.90)


def k_mouth3(m, paint=None):
    """Mouth of grade 3: two painted arches with a dark seam, each rail rising into the arch's leg."""
    s2.belt_stub(m, -0.9, 0.02, -0.55, -0.80)
    s2.mouth3(m, 0.0, -1, paint or s2.PY)
    with m.at((0.19, 0, 0)):
        _stub_wall(m, 0.60, 1.0)


KIT = [
    ("k_stack_rise3", k_stack_rise3, "굴뚝 1  차례로 셋", 2.3, 0.75),
    ("k_stack_one", k_stack_one, "굴뚝 2  굵은 하나", 2.3, 0.65),
    ("k_stack_pair", k_stack_pair, "굴뚝 3  굵은 것과 가는 것", 2.3, 0.70),
    ("k_stack_row2", k_stack_row2, "굴뚝 4  나란한 둘", 2.3, 0.65),
    ("k_pipe_straight", k_pipe_straight, "관 1  곧은 것", 2.3, 0.35),
    ("k_pipe_elbow", k_pipe_elbow, "관 2  한 번 꺾임", 2.3, 0.55),
    ("k_pipe_valve", k_pipe_valve, "관 3  밸브 달림", 2.3, 0.35),
    ("k_pipe_bridge", k_pipe_bridge, "관 4  넘어가는 것", 2.3, 0.65),
    ("k_drum_band", k_drum_band, "통 1  띠 두른 통", 2.3, 0.65),
    ("k_drum_cone", k_drum_cone, "통 2  고깔 쓴 통", 2.3, 0.65),
    ("k_tower2", k_tower2, "탑 1  틀 둘", 3.6, 1.0),
    ("k_tower3", k_tower3, "탑 2  틀 셋", 3.6, 1.35),
    ("k_house_s", k_house_s, "집 1  작은 것", 3.2, 0.55),
    ("k_house_m", k_house_m, "집 2  중간", 3.2, 0.55),
    ("k_house_l", k_house_l, "집 3  긴 것", 3.2, 0.55),
    ("k_mouth_low", k_mouth_low, "입구  낮은 급", 2.6, 0.45),
    ("k_mouth3", k_mouth3, "입구  3급", 2.6, 0.45),
]
for _name, _fn, _label, _size, _zc in KIT:
    _fn.frame, _fn.shadow, _fn.res = {"iso": (_size, _zc), "side": (_size, _zc), "top": (_size, 0.6), "end": (_size, _zc)}, True, 720
    _hero.HEROES[_name] = _fn
