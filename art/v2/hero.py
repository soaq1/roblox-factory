# v2 hero machines: built one at a time on the measured foundation in base.py and reviewed large.
# Rules: no thin plate lying on a body; every part has a job and every pipe a start and an end; the two
# sides of the belt match and so do the two ends; small parts are few and deliberate.
import math
from .base import (rad, G, T, TD, W, D, SLIT, SIDES, BX, BY, foundation, gear, wall_pipe, side_panel, hex_stack,
                   bx, frustum)

HEROES = {}


def hero(fn):
    HEROES[fn.__name__] = fn
    return fn


@hero
def crusher(m):
    """A gearbox block with the hopper growing out of it. The hopper is really open, with two toothed
    rolls down inside; its walls are ribbed and its rim is thick, with a stud at each corner. Each side
    wall carries a panel with the gear train (a big gear between two idlers) and a dust pipe at each end
    of the panel running from under the hopper down into the plinth."""
    Z = foundation(m)
    for d in SIDES:
        yp = side_panel(m, d)
        y = d * BY
        gear(m, 0.118, 0.024, (0, yp, 0.60), T, teeth=12)
        m.cyl(0.07, 0.03, (0, yp + d * 0.002, 0.60), TD, seg=10, axis="Y")
        m.cyl(0.03, 0.04, (0, yp + d * 0.004, 0.60), D, seg=6, axis="Y")
        for sx in SIDES:
            gear(m, 0.06, 0.024, (sx * 0.176, yp, 0.60), T, teeth=8, half_step=True)
            m.cyl(0.03, 0.03, (sx * 0.176, yp + d * 0.002, 0.60), TD, seg=8, axis="Y")
            m.box((0.035, 0.02, 0.20), (sx * 0.29, yp, 0.60), T)
            for k in range(2):
                m.box((0.03, 0.014, 0.03), (sx * 0.335, yp, 0.49 + k * 0.22), D)
            m.box((0.05, 0.03, 0.05), (sx * 0.30, y + d * 0.012, 0.385), T)
            wall_pipe(m, sx * 0.415, d, y, Z + 0.20)
    bx(m, (-0.43, 0.43), (-0.37, 0.37), (Z - 0.02, Z + 0.10), G, bevel=0.03)
    H0, H1, wt = Z + 0.08, Z + 0.46, 0.045
    for d in SIDES:
        yb, yt = sorted((d * 0.33, d * (0.33 - wt)))
        yb2, yt2 = sorted((d * 0.48, d * (0.48 - wt)))
        frustum(m, ((-0.40, 0.40), (yb, yt)), ((-0.55, 0.55), (yb2, yt2)), H0, H1, G)
        xb, xt = sorted((d * 0.40, d * (0.40 - wt)))
        xb2, xt2 = sorted((d * 0.55, d * (0.55 - wt)))
        frustum(m, ((xb, xt), (-0.33, 0.33)), ((xb2, xt2), (-0.48, 0.48)), H0, H1, G)
        for xr in (-0.30, 0.0, 0.30):
            m.prism([(d * 0.33, H0), (d * 0.48, H1), (d * 0.515, H1), (d * 0.365, H0)], xr - 0.022, xr + 0.022, "X", D)
        for yr in (-0.22, 0.22):
            m.prism([(d * 0.40, H0), (d * 0.55, H1), (d * 0.585, H1), (d * 0.435, H0)], yr - 0.022, yr + 0.022, "Y", D)
    RX, RY, rw = (-0.585, 0.585), (-0.515, 0.515), 0.075
    for ys in ((RY[0], RY[0] + rw), (RY[1] - rw, RY[1])):
        bx(m, RX, ys, (H1 - 0.01, H1 + 0.075), G, bevel=0.022)
    for xs in ((RX[0], RX[0] + rw), (RX[1] - rw, RX[1])):
        bx(m, xs, (RY[0] + rw, RY[1] - rw), (H1 - 0.01, H1 + 0.075), G, bevel=0.0)
    for sx in SIDES:
        for sy in SIDES:
            m.cyl(0.03, 0.03, (sx * 0.547, sy * 0.477, H1 + 0.085), D, seg=6)
    bx(m, (-0.37, 0.37), (-0.30, 0.30), (H0 - 0.01, H0 + 0.02), SLIT, bevel=0.0)
    for sx in SIDES:
        m.cyl(0.10, 0.56, (sx * 0.15, 0, H0 + 0.13), "h_steel", seg=10, axis="Y")
        for i, yy in enumerate((-0.20, -0.0667, 0.0667, 0.20)):
            gear(m, 0.15, 0.08, (sx * 0.15, yy, H0 + 0.13), T, teeth=8, root=0.74, base=0.56, tip=0.30,
                 half_step=i in (1, 2))
