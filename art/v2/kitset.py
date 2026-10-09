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
# Joints: a fat duct is 0.105 in radius everywhere, of whatever length is needed, carries a ring every 0.26
# along it (never plain), and swells into a socket at each end that meets another part;
# a plenum is 0.36 high and takes a duct in a plain wall 0.18 above its foot; a box elbow is 0.28 on a side.
import math
from . import hero as _hero
from . import set2 as s2

RD = 0.105               # the fat duct's radius
PLEN = 0.42              # a plenum's height: tall enough that a duct's socket sits wholly in plain wall under the rim
DUCT_AT = 0.20           # how high above its foot a plenum, or a drum's port, takes a duct


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


PITCH = 0.26             # every fat pipe carries a ring at this pitch (the developer: no pipe is ever plain;
RING = 0.06              # the rings repeat along it, as they do on the former's duct)


SOCK = (0.03, 0.06, 0.035) # a pipe's end where it meets another part: how much it swells, over what length, and its flange's thickness
SHORT = 0.42               # a pipe shorter than this has no room to swell: it ends in plain flanges


def _ring_at(lo, hi, clear=0.07):
    """Where the rings stand on a pipe from lo to hi: at the pitch, centred on the pipe, clear of its ends."""
    n = max(1, int((hi - lo - 2 * clear) / PITCH) + 1)
    mid = (lo + hi) / 2
    return [mid + (k - (n - 1) / 2) * PITCH for k in range(n)]


def _socket(m, axis, end, d, at, swell=True):
    """A pipe's end swelling into a flange where it meets another part (the developer: the joint grows a
    little there, naturally). `end` is where the pipe stops along `axis`, d which way it was going (+1 or
    -1), `at` its other two coordinates. With swell=False there is only the flange (a short pipe)."""
    grow, run_, thick = SOCK
    big = (RD + grow) * s2.K
    rot = {"X": (s2.rad(22.5), 0, 0), "Y": (0, s2.rad(22.5), 0), "Z": s2.rad(22.5)}[axis]

    def loc(c):
        return {"X": (c, at[0], at[1]), "Y": (at[0], c, at[1]), "Z": (at[0], at[1], c)}[axis]

    if swell:
        r_a, r_b = (RD * s2.K, big) if d > 0 else (big, RD * s2.K)
        m.cyl(r_a, run_, loc(end - d * (thick + run_ / 2)), s2.G, seg=8, axis=axis, r2=r_b, rot=rot)
    m.cyl(big, thick, loc(end - d * thick / 2), s2.G, seg=8, axis=axis, rot=rot)


def _run(m, axis, c0, c1, at, skip=(), ends=(True, True)):
    """A fat duct from c0 to c1 along `axis`, of any length: ringed at the pitch, and swelling into a socket
    at each end that meets another part. `skip` lists (lo, hi) stretches where something else sits on the
    pipe (a valve), and no ring is put there."""
    rot = {"X": (s2.rad(22.5), 0, 0), "Y": (0, s2.rad(22.5), 0), "Z": s2.rad(22.5)}[axis]

    def loc(c):
        return {"X": (c, at[0], at[1]), "Y": (at[0], c, at[1]), "Z": (at[0], at[1], c)}[axis]

    p0, p1 = c0 + (0.006 if ends[0] else 0.0), c1 - (0.006 if ends[1] else 0.0)     # the pipe stops inside its sockets' flanges
    m.cyl(RD * s2.K, p1 - p0, loc((p0 + p1) / 2), s2.LT, seg=8, axis=axis, rot=rot)
    short = c1 - c0 < SHORT                                    # too short to swell at both ends and still be a pipe between
    keep = (SOCK[2] if short else SOCK[1] + SOCK[2]) + 0.05
    lo, hi = c0 + (keep if ends[0] else 0.0), c1 - (keep if ends[1] else 0.0)
    if hi - lo >= RING:
        for c in _ring_at(lo, hi, clear=0.03):
            if not any(a - RING <= c <= b + RING for a, b in skip):
                m.cyl((RD + 0.022) * s2.K, RING, loc(c), s2.G, seg=8, axis=axis, rot=rot)
    if ends[0]:
        _socket(m, axis, c0, -1, at, swell=not short)
    if ends[1]:
        _socket(m, axis, c1, 1, at, swell=not short)


def _run_x(m, x0, x1, y, z, skip=(), ends=(True, True)):
    _run(m, "X", x0, x1, (y, z), skip, ends)


def _run_y(m, y0, y1, x, z, skip=(), ends=(True, True)):
    _run(m, "Y", y0, y1, (x, z), skip, ends)


def _pier(m, x, y, top):
    with m.at((x, y, 0)):
        s2.slab(m, 0.10, 0.13, 0.0, 0.07, 0.03, s2.T, bevel=0.012)
        s2.slab(m, 0.05, 0.075, 0.05, top, 0.015, s2.ST, bevel=0.01)


def _elbow(m, x, y, z):
    with m.at((x, y, 0)):
        s2.slab(m, 0.14, 0.14, z - 0.14, z + 0.14, 0.03, s2.G, bevel=0.02)


def _riser(m, x, y, z0, z1):
    """A fat duct standing up out of a flared foot to z1, ringed at the pitch, a socket at its top."""
    with m.at((x, y, 0)):
        s2.octa(m, RD + 0.05, RD + 0.02, z0 - 0.01, z0 + 0.08, s2.G)
    _run(m, "Z", z0 + 0.07, z1, (x, y), ends=(False, True))


def k_pipe_straight(m, L=1.1, z=0.45):
    """Pipe, straight: a fat ringed duct on two piers."""
    _run_x(m, -L / 2, L / 2, 0, z)
    for x in (-PITCH, PITCH):
        _pier(m, x, 0, z - RD + 0.01)


def k_pipe_elbow(m, H=0.95, L=0.80, z0=0.0):
    """Pipe, one turn: up out of a foot, through a box elbow, and away level, ringed all the way."""
    _riser(m, 0, 0, z0, z0 + H - 0.13)
    _elbow(m, 0, 0, z0 + H)
    _run_x(m, 0.14 - 0.01, L, 0, z0 + H)


def k_pipe_valve(m, L=1.3, z=0.45):
    """Pipe, with a valve: a fat ringed duct through a valve box with a five-sided handwheel, the box on a pier."""
    _run_x(m, -L / 2, L / 2, 0, z, skip=((-0.13, 0.13),))
    with m.at((0, 0, 0)):
        s2.slab(m, 0.13, 0.13, z - 0.14, z + 0.14, 0.03, s2.G, bevel=0.02)
    _pier(m, 0, 0, z - 0.13)
    with s2.on_side(m, -1, -0.13, z, xc=0.0):
        s2.handwheel(m, 0.14)


def k_pipe_bridge(m, H=1.15, L=1.06, z0=0.0):
    """Pipe, over: up, across through two box elbows, and down again (the former's duct), ringed all the way."""
    for x in (-L / 2, L / 2):
        _riser(m, x, 0, z0, z0 + H - 0.13)
        _elbow(m, x, 0, z0 + H)
    _run_x(m, -L / 2 + 0.13, L / 2 - 0.13, 0, z0 + H)


def _port(m, r, side, z0):
    """A pad on a drum's side for a duct to come in at: a plate a little bigger than the duct's socket,
    standing just proud of the drum, so that the socket sits wholly on it and not across the drum's
    corners. `side` is "E", "W", "N" or "S"."""
    dx, dy = {"E": (1, 0), "W": (-1, 0), "N": (0, 1), "S": (0, -1)}[side]
    w = 2 * (RD + SOCK[0]) + 0.04
    size = (0.07, w, w) if dx else (w, 0.07, w)
    m.box(size, (dx * (r + 0.005), dy * (r + 0.005), z0 + DUCT_AT), s2.G, bevel=0.012)
    return r + 0.04                                           # how far out the pad's face stands


def k_drum_band(m, z0=0.0, ports=("E",)):
    """Drum, banded: a fat upright eight-sided drum with two hoops high on it, a drawn-in top and a capped
    vent; a pad low on its side wherever a duct comes in."""
    r = 0.28
    s2.octa(m, r + 0.03, r + 0.01, z0, z0 + 0.05, s2.T)
    s2.octa(m, r, r, z0 + 0.04, z0 + 1.10, s2.G)
    for z in (0.52, 0.90):
        s2.octa(m, r + 0.013, r + 0.013, z0 + z, z0 + z + 0.06, s2.TD)
    s2.octa(m, r, 0.13, z0 + 1.09, z0 + 1.26, s2.G)
    s2.octa(m, 0.065, 0.065, z0 + 1.25, z0 + 1.35, s2.ST)
    s2.octa(m, 0.09, 0.09, z0 + 1.34, z0 + 1.38, s2.TD)
    for side in ports:
        _port(m, r, side, z0)
    return r + 0.04


def k_drum_cone(m, z0=0.0, ports=("E",)):
    """Drum, coned: a fat banded drum under a cone, a small stack out of the cone's top; a pad low on its
    side wherever a duct comes in."""
    r = 0.28
    s2.octa(m, r + 0.03, r + 0.01, z0 - 0.01, z0 + 0.05, s2.G)
    s2.octa(m, r, r, z0 + 0.04, z0 + 0.74, s2.LT)
    for z in (0.44, 0.62):
        s2.octa(m, r + 0.013, r + 0.013, z0 + z, z0 + z + 0.06, s2.G)
    s2.octa(m, r, 0.11, z0 + 0.73, z0 + 0.96, s2.G)
    s2.fat_stack(m, 0, 0, z0 + 0.95, z0 + 1.42, 0.085, foot=0.03)
    for side in ports:
        _port(m, r, side, z0)
    return r + 0.04


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
    """Mouth of the low grades: the ribbed folding cover over the belt (the smelter's), six folds deep, as
    wide as the rails so that they run straight into it."""
    s2.run(m, -1.2, 0.02, braces=(-1.05,))
    s2.cover(m, 0.0, -1, sole=False, n=6, wide=True)
    with m.at((0.19, 0, 0)):
        _stub_wall(m, 0.56, 0.95)


def k_mouth3(m, paint=None):
    """Mouth of grade 3: long, two painted arches with a dark seam at its face, a third against the wall, a
    grey sleeve over a dark throat between, as wide as the rails so that they run straight into it."""
    s2.belt_stub(m, -1.2, 0.02, -0.85, -1.05)
    s2.mouth3(m, 0.0, -1, paint or s2.PY, depth=0.46, ears=False, wide=True)
    with m.at((0.19, 0, 0)):
        _stub_wall(m, 0.60, 1.0)


def k_pipe_join(m):
    """Not a piece: a drum and a stack group joined by a long pipe, and a second drum joined by a short one,
    to show how a pipe meets another part. Each end goes a little way into the part."""
    with m.at((-1.05, 0, 0)):
        face = k_drum_band(m, ports=("E",))
    with m.at((0.55, 0, 0)):
        k_stack_row2(m, 0.0)
    _run_x(m, -1.05 + face - 0.012, 0.55 - 0.34 + 0.012, 0, DUCT_AT)
    with m.at((0.55, 0.82, 0)):
        face = k_drum_cone(m, ports=("S",))
    _run_y(m, 0.20 - 0.012, 0.82 - face + 0.012, 0.55, DUCT_AT)


k_pipe_join.frame, k_pipe_join.shadow, k_pipe_join.res = {"iso": (4.0, 0.72), "side": (4.0, 0.72), "top": (4.0, 0.6), "end": (4.0, 0.72)}, True, 1100
_hero.HEROES["k_pipe_join"] = k_pipe_join


KIT = [
    ("k_stack_rise3", k_stack_rise3, "굴뚝 1  차례로 셋", 2.3, 0.75),
    ("k_stack_one", k_stack_one, "굴뚝 2  굵은 하나", 2.3, 0.65),
    ("k_stack_pair", k_stack_pair, "굴뚝 3  굵은 것과 가는 것", 2.3, 0.70),
    ("k_stack_row2", k_stack_row2, "굴뚝 4  나란한 둘", 2.3, 0.65),
    ("k_pipe_straight", k_pipe_straight, "관 1  곧은 것", 2.3, 0.35),
    ("k_pipe_elbow", k_pipe_elbow, "관 2  한 번 꺾임", 2.3, 0.55),
    ("k_pipe_valve", k_pipe_valve, "관 3  밸브 달림", 2.3, 0.35),
    ("k_pipe_bridge", k_pipe_bridge, "관 4  넘어가는 것", 2.3, 0.65),
    ("k_drum_band", k_drum_band, "통 1  띠 두른 통", 2.6, 0.70),
    ("k_drum_cone", k_drum_cone, "통 2  고깔 쓴 통", 2.6, 0.72),
    ("k_tower2", k_tower2, "탑 1  틀 둘", 3.6, 1.0),
    ("k_tower3", k_tower3, "탑 2  틀 셋", 3.6, 1.35),
    ("k_house_s", k_house_s, "집 1  작은 것", 3.2, 0.55),
    ("k_house_m", k_house_m, "집 2  중간", 3.2, 0.55),
    ("k_house_l", k_house_l, "집 3  긴 것", 3.2, 0.55),
    ("k_mouth_low", k_mouth_low, "입구  낮은 급", 2.9, 0.45),
    ("k_mouth3", k_mouth3, "입구  3급", 2.9, 0.45),
]
for _name, _fn, _label, _size, _zc in KIT:
    _fn.frame, _fn.shadow, _fn.res = {"iso": (_size, _zc), "side": (_size, _zc), "top": (_size, 0.6), "end": (_size, _zc)}, True, 720
    _hero.HEROES[_name] = _fn
