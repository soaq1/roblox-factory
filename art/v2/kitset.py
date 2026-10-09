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
#   mouths   k_mouth_low, k_mouth3 (both built by mouth())
#   others   k_hopper, k_blower, k_gears, k_walk, k_hoist (what complicates a machine besides stacks and pipes)
#
# Joints: a fat duct is 0.105 in radius everywhere, of whatever length is needed, carries a ring every 0.26
# along it (never plain), and swells into a socket at each end that meets another part;
# a plenum is 0.36 high and takes a duct in a plain wall 0.18 above its foot; a box elbow is 0.28 on a side.
import math
from . import hero as _hero
from . import set2 as s2
from .base import loft_x, offset_closed

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


def k_drum_band(m, z0=0.0, ports=()):
    """Drum, banded: a fat upright eight-sided drum with two hoops, a drawn-in top and a capped vent. It
    stands by itself: the developer does not want ducts run into it ("띠 두른 통에 왜 자꾸 배관을
    연결하는데"), so it has no port unless one is asked for."""
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


def k_drum_cone(m, z0=0.0, ports=()):
    """Drum, coned: a fat banded drum under a cone, a small stack out of the cone's top. No port unless one
    is asked for."""
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


def _rib(m, x0, x1, w, top, hole_top, mk, soft=0.016, hw=None):
    """One rib of a mouth: an arch over the belt from x0 to x1, its edges cut back by `soft` so that it is
    rounded off rather than sharp (the developer: the mouths' ribs are to be softened)."""
    o = s2.arch_pts(w, top, hole_top=hole_top, hw=hw or s2.BH + 0.01, c=0.085, ci=0.035)[::-1]
    a, b = sorted((x0, x1))
    st = [(a, offset_closed(o, soft)), (a + soft, o), (b - soft, o), (b, offset_closed(o, soft))] if soft else [(a, o), (b, o)]
    loft_x(m, st, mk)


def mouth(m, xa, d, grade, paint=None):
    """A conveyor mouth on the wall at xa, opening toward d, the belt's middle at y = 0. Every mouth of one
    grade is this same thing, and every machine calls this rather than drawing its own.
    All grades: deep and long, so that things go into it and not through a wall; as wide as the belt's
    rails, which run straight into its legs (nothing stands on the rails beside it); and made of a few
    thick ribs with a gap between each, their edges rounded off, not of many thin ones.
    grade "low": three plain grey ribs, and lower than the others.
    grade 3: three painted ribs at full height, the gaps a grey sleeve, the throat lined dark.
    Returns how far out the mouth reaches."""
    low = grade == "low"
    top, web_top = (0.70, 0.655) if low else (0.82, 0.775)
    hole = top - 0.115
    rib_mk, web_mk = (s2.R, s2.RD) if low else (paint or s2.PY, s2.G)
    parts = [("web", 0.05), ("rib", 0.095), ("web", 0.055), ("rib", 0.095), ("web", 0.055), ("rib", 0.11)]
    px = xa
    for kind, th in parts:
        nx = px + d * th
        if kind == "rib":
            _rib(m, px, nx, 0.988, top, hole, rib_mk)
        else:
            _rib(m, px - d * 0.004, nx + d * 0.004, 0.93, web_top, hole + 0.002, web_mk, soft=0.0, hw=s2.BH + 0.012)
        px = nx
    depth = abs(px - xa)
    if not low:                                               # the throat's dark lining
        a_, b_ = sorted((xa + d * 0.02, xa + d * (depth - 0.03)))
        m.prism(s2.arch_pts(2 * (s2.BH + 0.03), hole + 0.02, hole_top=hole - 0.006, hw=s2.BH + 0.004, c=0.05, ci=0.035), a_, b_, "X", s2.TD)
    m.box((0.02, 2 * s2.BH + 0.01, hole - 0.006 - s2.BZ), (xa + d * 0.012, 0, (hole + 0.006 + s2.BZ) / 2), s2.SLIT)
    return depth


def k_mouth_low(m):
    """Mouth of the low grades: three thick grey ribs with gaps between, lower than the others."""
    s2.run(m, -1.2, 0.02, braces=(-1.05,))
    mouth(m, 0.0, -1, "low")
    with m.at((0.19, 0, 0)):
        _stub_wall(m, 0.56, 0.90)


def k_mouth3(m, paint=None):
    """Mouth of grade 3: three thick painted ribs on a grey sleeve over a dark throat."""
    s2.run(m, -1.2, 0.02, braces=(-1.05,))               # the same belt as any other, arrows at the same pitch
    mouth(m, 0.0, -1, 3, paint)
    with m.at((0.19, 0, 0)):
        _stub_wall(m, 0.60, 1.0)


def k_hopper(m, z0=0.0):
    """Hopper: a funnel that spreads upward from a neck to a wide rimmed mouth with a real hollow, a band
    round its waist, on a collar. Where material goes in and gathers."""
    s2.slab(m, 0.21, 0.21, z0 - 0.01, z0 + 0.06, 0.04, s2.T, bevel=0.012)
    s2.tower(m, [(0.16, 0.16, 0.035, z0 + 0.05), (0.16, 0.16, 0.035, z0 + 0.14), (0.38, 0.38, 0.07, z0 + 0.52), (0.38, 0.38, 0.07, z0 + 0.535)], s2.G)
    s2.tower(m, [(0.262, 0.262, 0.052, z0 + 0.31), (0.297, 0.297, 0.058, z0 + 0.37)], s2.LT)            # the band, on the slope
    s2.shell(m, [(0.405, 0.405, 0.075, z0 + 0.52), (0.405, 0.405, 0.075, z0 + 0.59), (0.39, 0.39, 0.07, z0 + 0.605),
                 (0.33, 0.33, 0.05, z0 + 0.605), (0.315, 0.315, 0.045, z0 + 0.52)], s2.TD)
    s2.tower(m, [(0.322, 0.322, 0.047, z0 + 0.515), (0.322, 0.322, 0.047, z0 + 0.545)], s2.SLIT)


def k_blower(m, z0=0.0):
    """Blower: a round casing standing on edge on a base, its outlet rising square from one side to a flange
    a duct can start from, its intake a rimmed hole in the face with a hub and three arms."""
    zc = z0 + 0.40
    with m.at((0, 0, 0)):
        s2.slab(m, 0.30, 0.17, z0, z0 + 0.12, 0.03, s2.T, bevel=0.012)
    m.cyl(0.31, 0.24, (0, 0, zc), s2.G, seg=12, axis="Y", rot=(0, s2.rad(15), 0))
    m.cyl(0.325, 0.06, (0, 0, zc), s2.LT, seg=12, axis="Y", rot=(0, s2.rad(15), 0))                    # a band round the casing's edge
    m.box((0.24, 0.20, 0.36), (0.185, 0, zc + 0.24), s2.G, bevel=0.02)                                   # the outlet, rising off the casing's side
    with m.at((0.185, 0, 0)):
        s2.slab(m, 0.145, 0.125, zc + 0.40, zc + 0.46, 0.03, s2.LT, bevel=0.012)
        s2.slab(m, 0.095, 0.075, zc + 0.44, zc + 0.47, 0.02, s2.SLIT, bevel=0.004)
    with s2.on_side(m, -1, -0.12, zc, xc=0.0):                # the intake
        s2.ring_round(m, 0.19, 0.135, -0.004, 0.035, s2.TD, seg=12)
        m.cyl(0.14, 0.01, (0, 0, 0.004), s2.SLIT, seg=12)
        m.cyl(0.04, 0.03, (0, 0, 0.02), s2.ST, seg=8)
        for k in range(3):
            a_ = s2.rad(90 + 120 * k)
            m.box((0.022, 0.12, 0.014), (0.085 * math.cos(a_), 0.085 * math.sin(a_), 0.024), s2.ST, rot=a_ - math.pi / 2)


def k_gears(m, paint=None, z0=0.0):
    """Gears: a big toothed wheel and a small one in mesh, each on a shaft between two bearing blocks, on a
    base. The one part that is seen to turn."""
    paint = paint or s2.PY
    s2.slab(m, 0.56, 0.22, z0, z0 + 0.08, 0.03, s2.T, bevel=0.012)
    for x, zc, r, teeth in ((-0.14, z0 + 0.50, 0.36, 12), (0.33, z0 + 0.30, 0.17, 8)):
        m.gear(r, 0.09, (x, 0, zc), s2.G, teeth=teeth, axis="Y")
        m.cyl(r * 0.50, 0.11, (x, 0, zc), paint, seg=8, axis="Y", rot=(0, s2.rad(22.5), 0))             # a painted hub
        m.cyl(0.04, 0.40, (x, 0, zc), s2.ST, seg=8, axis="Y", rot=(0, s2.rad(22.5), 0))                 # the shaft
        for sy in s2.SIDES:                                   # a bearing block each side, on a pedestal
            with m.at((x, sy * 0.16, 0)):
                s2.slab(m, 0.075, 0.04, z0 + 0.06, zc - 0.05, 0.015, s2.LT, bevel=0.008)
                s2.slab(m, 0.085, 0.05, zc - 0.07, zc + 0.07, 0.02, s2.G, bevel=0.012)


def k_walk(m, L=1.4, z=0.85):
    """Walkway: a deck on two legs with a kerb, a rail and a mid-rail on stout posts along its outer side,
    and a ladder down to the ground at one end. The way up to look after a machine, and a measure of
    how big the machine is."""
    m.box((L, 0.32, 0.04), (0, 0, z), s2.TD, bevel=0.008)
    m.box((L - 0.02, 0.03, 0.07), (0, -0.138, z + 0.03), s2.LT, bevel=0.006)                             # the kerb
    for x in (-L / 2 + 0.05, 0.0, L / 2 - 0.05):
        m.box((0.045, 0.045, 0.40), (x, -0.138, z + 0.22), s2.LT, bevel=0.008)
    m.box((L, 0.05, 0.05), (0, -0.138, z + 0.43), s2.LT, bevel=0.01)
    m.box((L - 0.06, 0.03, 0.03), (0, -0.138, z + 0.25), s2.ST)
    for x in (-L / 2 + 0.16, L / 2 - 0.42):                   # the legs
        with m.at((x, 0.09, 0)):
            s2.slab(m, 0.07, 0.07, 0.0, 0.05, 0.02, s2.T, bevel=0.01)
            s2.slab(m, 0.035, 0.035, 0.04, z - 0.015, 0.01, s2.ST, bevel=0.006)
    xl = L / 2 + 0.035                                        # the ladder, at the +x end
    for sy in s2.SIDES:
        m.box((0.035, 0.035, z + 0.30), (xl, sy * 0.11, (z + 0.30) / 2), s2.LT, bevel=0.006)
    n = int((z - 0.10) / 0.13)
    for k in range(n + 1):
        m.box((0.028, 0.22, 0.028), (xl, 0, 0.12 + k * 0.13), s2.ST)


def k_hoist(m, paint=None, L=1.3, z0=0.0):
    """Hoist: a painted beam between two brackets, dark flanges above and below it, a trolley under it, a
    chain and a hook. For changing what is heavy; it stands across the top of a tower."""
    paint = paint or s2.PY
    zb = z0 + 0.32
    for x in (-L / 2 + 0.10, L / 2 - 0.10):
        with m.at((x, 0, 0)):
            s2.slab(m, 0.07, 0.10, z0, zb - 0.092, 0.02, s2.G, bevel=0.012)
    m.box((L, 0.10, 0.15), (0, 0, zb), paint, bevel=0.012)
    for dz in (-0.085, 0.085):
        m.box((L, 0.17, 0.03), (0, 0, zb + dz), s2.TD, bevel=0.008)
    xt = 0.18                                                 # the trolley
    m.box((0.20, 0.23, 0.07), (xt, 0, zb - 0.135), s2.G, bevel=0.012)
    for sx in s2.SIDES:
        for sy in s2.SIDES:
            m.cyl(0.035, 0.03, (xt + sx * 0.06, sy * 0.105, zb - 0.075), s2.LT, seg=8, axis="Y")
    m.box((0.028, 0.028, 0.20), (xt, 0, zb - 0.265), s2.ST)
    with m.at((xt, 0, 0)):
        s2.octa(m, 0.05, 0.05, zb - 0.42, zb - 0.36, s2.TD)
    m.box((0.03, 0.03, 0.09), (xt, 0, zb - 0.46), s2.ST)     # the hook: a shank, a bend, a tip
    m.box((0.09, 0.03, 0.03), (xt + 0.03, 0, zb - 0.505), s2.ST)
    m.box((0.03, 0.03, 0.06), (xt + 0.06, 0, zb - 0.475), s2.ST)


def k_pipe_join(m):
    """Not a piece, and not a layout to copy: only the two cases of a pipe meeting another part, kept apart
    so that neither crowds the other. In front, a long pipe between two plenums; behind, a short one
    from a plenum into a plain wall. Each end goes a little way into the part. (The first version packed
    three stack groups together, and the developer asked whether it was overdone on purpose.)"""
    with m.at((-0.70, -0.55, 0)):
        k_stack_row2(m)
    with m.at((0.75, -0.55, 0)):
        k_stack_pair(m)
    _run_x(m, -0.70 + 0.34 - 0.012, 0.75 - 0.36 + 0.012, -0.55, DUCT_AT)
    with m.at((-0.45, 0.85, 0)):
        k_stack_row2(m)
    with m.at((0.40, 0.85, 0)):
        s2.slab(m, 0.14, 0.42, 0.0, 0.80, 0.035, s2.G, bevel=0.02)
    _run_x(m, -0.45 + 0.34 - 0.012, 0.40 - 0.14 + 0.012, 0.85, DUCT_AT)


k_pipe_join.frame, k_pipe_join.shadow, k_pipe_join.res = {"iso": (4.2, 0.72), "side": (4.2, 0.72), "top": (4.2, 0.6), "end": (4.2, 0.72)}, True, 1100
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
    ("k_hopper", k_hopper, "깔때기", 2.0, 0.32),
    ("k_blower", k_blower, "송풍기", 2.0, 0.42),
    ("k_gears", k_gears, "톱니바퀴", 2.4, 0.42),
    ("k_walk", k_walk, "발판과 사다리", 2.5, 0.62),
    ("k_hoist", k_hoist, "들보와 갈고리", 2.0, 0.22),
    ("k_mouth_low", k_mouth_low, "입구  낮은 급", 2.9, 0.45),
    ("k_mouth3", k_mouth3, "입구  3급", 2.9, 0.45),
]
for _name, _fn, _label, _size, _zc in KIT:
    _fn.frame, _fn.shadow, _fn.res = {"iso": (_size, _zc), "side": (_size, _zc), "top": (_size, 0.6), "end": (_size, _zc)}, True, 720
    _hero.HEROES[_name] = _fn
