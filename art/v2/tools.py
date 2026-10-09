# Hand tools. The first two, at the developer's word (2026-10-10): a wooden pickaxe and a wooden axe.
#
#   pick_wood   a wooden pickaxe: a two-pointed head, thick where the handle goes through it
#   axe_wood    a wooden axe: a blade that widens and drops to a beard, a short poll behind
#   tools_wood  the two side by side, turned to show their heads from the side
#
# A tool stands upright with the foot of its handle at the origin and its head along x. It is drawn in
# studs (a character is five tall) and scaled down to the models' unit, a cell of three studs.
from mathutils import Matrix
import factorykit as fk
from . import hero as _hero
from .base import loft_x, octa

fk.PAL.update({"w_handle": "#6a4a35", "w_wood": "#c49a62", "w_wood_d": "#a67c4a", "w_cord": "#d9c79a"})
STUD = 1.0 / 3.0


def in_studs(fn):
    def wrapped(m, *a, **k):
        m.stack.append(m.stack[-1] @ Matrix.Scale(STUD, 4))
        fn(m, *a, **k)
        m.stack.pop()
    wrapped.__doc__ = fn.__doc__
    return wrapped


def section(hy, z0, z1):
    """A cross-section across a head: a rectangle hy to each side of the middle, from z0 up to z1, its four
    corners cut."""
    c = min(hy * 0.55, (z1 - z0) * 0.25, 0.06)
    return [(-hy, z0 + c), (-hy, z1 - c), (-hy + c, z1), (hy - c, z1), (hy, z1 - c), (hy, z0 + c), (hy - c, z0), (-hy + c, z0)]


def handle(m, top):
    """A wooden handle: eight-sided, swelling to a knob at its foot and thinning a little toward the head,
    with two turns of cord under the head to hold it."""
    octa(m, 0.19, 0.15, 0.0, 0.16, "w_handle")
    octa(m, 0.15, 0.125, 0.14, 0.42, "w_handle")
    octa(m, 0.125, 0.105, 0.40, top, "w_handle")
    octa(m, 0.115, 0.115, top - 0.01, top + 0.05, "w_wood_d")          # the handle's end, seen above the head


def cord(m, z):
    for k in (0, 1):
        octa(m, 0.15, 0.15, z + k * 0.10, z + k * 0.10 + 0.075, "w_cord")


@in_studs
def pick_wood(m):
    """A wooden pickaxe, 3.6 studs long: the head is one piece of pale wood, thick and square where the
    handle goes through it and drawn out each way into a point that drops as it goes."""
    zc, reach, drop = 3.12, 1.42, 0.50
    handle(m, zc + 0.24)
    cord(m, zc - 0.48)
    st = []
    for x, hy, hz in ((-reach, 0.035, 0.045), (-1.10, 0.075, 0.095), (-0.70, 0.11, 0.135), (-0.27, 0.14, 0.17),
                      (-0.23, 0.20, 0.235), (0.23, 0.20, 0.235), (0.27, 0.14, 0.17), (0.70, 0.11, 0.135), (1.10, 0.075, 0.095), (reach, 0.035, 0.045)):
        z = zc - drop * (abs(x) / reach) ** 1.9
        st.append((x, section(hy, z - hz, z + hz)))
    loft_x(m, st, "w_wood")
    for x in (-0.25, 0.25):                                   # the two edges of the thick middle, in darker wood
        z = zc - drop * (abs(x) / reach) ** 1.9
        loft_x(m, [(x - 0.035, section(0.215, z - 0.25, z + 0.25)), (x + 0.035, section(0.215, z - 0.25, z + 0.25))], "w_wood_d")


@in_studs
def axe_wood(m):
    """A wooden axe, 3.6 studs long: a square eye round the handle, a short poll behind it, and in front a
    blade that thins to its edge while it widens, most of all downward into a beard."""
    zc = 3.02
    handle(m, zc + 0.26)
    cord(m, zc - 0.52)
    loft_x(m, [(x, section(hy, zc + lo, zc + hi)) for x, hy, lo, hi in (
        (-0.44, 0.11, -0.16, 0.16), (-0.38, 0.15, -0.20, 0.20),             # the poll
        (-0.25, 0.15, -0.20, 0.20), (-0.21, 0.20, -0.245, 0.245),           # the eye, a little proud
        (0.21, 0.20, -0.245, 0.245), (0.25, 0.14, -0.20, 0.20),
        (0.55, 0.11, -0.34, 0.24), (0.90, 0.07, -0.62, 0.34),               # the blade, dropping to its beard
        (1.12, 0.03, -0.74, 0.36), (1.20, 0.012, -0.70, 0.33))], "w_wood")
    for x in (-0.23, 0.23):
        loft_x(m, [(x - 0.035, section(0.215, zc - 0.26, zc + 0.26)), (x + 0.035, section(0.215, zc - 0.26, zc + 0.26))], "w_wood_d")


def tools_wood(m):
    turn = -0.7853981633974483                                # toward the picture's eye, so the heads show from the side
    with m.at((-0.52, 0.52, 0), turn):
        pick_wood(m)
    with m.at((0.52, -0.52, 0), turn):
        axe_wood(m)


for _name, _fn, _frame in (("pick_wood", pick_wood, (1.9, 0.62)), ("axe_wood", axe_wood, (1.9, 0.62)), ("tools_wood", tools_wood, (3.1, 0.62))):
    _fn.frame, _fn.shadow, _fn.res = {k: _frame for k in ("iso", "side", "top", "end")}, True, 1600
    _hero.HEROES[_name] = _fn
