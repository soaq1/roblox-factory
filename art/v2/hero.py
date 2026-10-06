# v2 hero machines: built one at a time on the measured foundation in base.py and reviewed large.
# Rules: no thin plate lying on a body; every part has a job; pipes go only on machines where something
# plausibly flows, and then each is fixed at both ends to something that makes sense; the two sides of
# the belt match and so do the two ends; small parts are few and deliberate.
import math
from .base import (rad, G, T, TD, W, D, SLIT, SIDES, BX, BY, foundation, gear, pipe_from_neck, side_pipe, side_panel,
                   hex_stack, octa, oct_ring, bx, frustum)

HEROES = {}


def hero(fn):
    HEROES[fn.__name__] = fn
    return fn


@hero
def crusher(m):
    """A gearbox block with the hopper growing out of it. The hopper is really open, with two toothed
    rolls down inside; its walls are ribbed and its rim is thick, with a stud at each corner. Each side
    wall carries a panel with the gear train (a big gear between two idlers) and, at each end, a bracket
    under the hopper that the hopper's rib carries on from. There are no pipes: nothing here flows."""
    Z = foundation(m)
    for d in SIDES:
        yp = side_panel(m, d, w=0.66)
        y = d * BY
        gear(m, 0.118, 0.024, (0, yp, 0.60), T, teeth=12)
        m.cyl(0.07, 0.03, (0, yp + d * 0.002, 0.60), TD, seg=10, axis="Y")
        m.cyl(0.03, 0.04, (0, yp + d * 0.004, 0.60), D, seg=6, axis="Y")
        for sx in SIDES:
            gear(m, 0.062, 0.024, (sx * 0.17, yp, 0.60), T, teeth=8, half_step=True)
            m.cyl(0.03, 0.03, (sx * 0.17, yp + d * 0.002, 0.60), TD, seg=8, axis="Y")
            m.box((0.035, 0.02, 0.20), (sx * 0.27, yp, 0.60), T)
            px = sx * 0.405
            m.prism([(y, Z - 0.30), (y + d * 0.068, Z + 0.0), (y + d * 0.068, Z + 0.10), (d * 0.37, Z + 0.10),
                     (d * 0.37, Z - 0.02), (y, Z - 0.02)], px - 0.03, px + 0.03, "X", D)
    bx(m, (-0.43, 0.43), (-0.37, 0.37), (Z - 0.02, Z + 0.10), G, bevel=0.03)
    H0, H1, wt = Z + 0.08, Z + 0.46, 0.045
    for d in SIDES:
        yb, yt = sorted((d * 0.33, d * (0.33 - wt)))
        yb2, yt2 = sorted((d * 0.48, d * (0.48 - wt)))
        frustum(m, ((-0.40, 0.40), (yb, yt)), ((-0.55, 0.55), (yb2, yt2)), H0, H1, G)
        xb, xt = sorted((d * 0.40, d * (0.40 - wt)))
        xb2, xt2 = sorted((d * 0.55, d * (0.55 - wt)))
        frustum(m, ((xb, xt), (-0.33, 0.33)), ((xb2, xt2), (-0.48, 0.48)), H0, H1, G)
        for xr in (-0.405, 0.0, 0.405):
            hw = 0.03 if xr else 0.022
            m.prism([(d * 0.33, H0), (d * 0.48, H1), (d * 0.515, H1), (d * 0.365, H0)], xr - hw, xr + hw, "X", D)
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
            gear(m, 0.15, 0.08, (sx * 0.15, yy, H0 + 0.13), T, teeth=8, root=0.72, base=0.58, tip=0.20,
                 half_step=i in (1, 2))


@hero
def smelter(m):
    """A firebox block carrying an eight-sided shaft as wide as the block itself: banded, narrowing
    upward, open at the top with the melt glowing inside its thick rim. An uptake flue runs up each end
    of the shaft, strapped to it, and stands clear above the rim. Each side wall carries a panel with the
    fire door in the middle and a draught port either side of it, and cooling fins at each end."""
    Z = foundation(m)
    for d in SIDES:
        yp = side_panel(m, d, w=0.66)
        y = d * BY
        m.box((0.30, 0.03, 0.22), (0, yp + d * 0.008, 0.60), T)
        m.box((0.23, 0.02, 0.155), (0, yp + d * 0.02, 0.60), SLIT)
        for i in range(4):
            m.box((0.03, 0.012, 0.125), (-0.075 + i * 0.05, yp + d * 0.028, 0.60), "h_glow")
        for sx in SIDES:
            m.cyl(0.05, 0.024, (sx * 0.245, yp, 0.60), T, seg=8, axis="Y")
            m.cyl(0.028, 0.03, (sx * 0.245, yp + d * 0.002, 0.60), TD, seg=8, axis="Y")
            for k in range(3):
                m.box((0.02, 0.035, 0.44), (sx * (0.385 + k * 0.032), y + d * 0.012, 0.56), D)
    bx(m, (-0.47, 0.47), (-0.40, 0.40), (Z - 0.02, Z + 0.10), G, bevel=0.03)
    N = Z + 0.10
    octa(m, 0.385, 0.385, N - 0.02, N + 0.08, D)
    octa(m, 0.355, 0.285, N + 0.06, N + 0.62, G)
    for z, a in ((N + 0.24, 0.336), (N + 0.42, 0.314)):
        octa(m, a, a - 0.005, z, z + 0.04, D)
    oct_ring(m, 0.335, 0.075, N + 0.60, N + 0.72, G)
    octa(m, 0.262, 0.262, N + 0.62, N + 0.655, "h_glow")
    for sx in SIDES:
        x = sx * 0.415
        m.cyl(0.075, 0.05, (x, 0.0, N + 0.025), D, seg=8)
        m.cyl(0.055, 0.86, (x, 0.0, N + 0.43), G, seg=8)
        m.cyl(0.05, 0.10, (x, 0.0, N + 0.91), D, seg=8, r2=0.075)
        m.cyl(0.06, 0.01, (x, 0.0, N + 0.962), SLIT, seg=8)
        for z, inner in ((N + 0.26, 0.33), (N + 0.50, 0.30)):
            lo, hi = sorted((sx * inner, x))
            bx(m, (lo, hi), (-0.07, 0.07), (z, z + 0.05), D, bevel=0.0)
