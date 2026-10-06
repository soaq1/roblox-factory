# v2 base: the foundation every "hero" machine is built on, and the camera that shows it.
#
# The numbers were measured from Islands' Industrial Smelter render (see docs/specs/2026-10-06-models-v2.md):
# the chassis is one cell wide and three long, the body is as wide as the chassis and stands on a dark
# plinth with a light moulding, and six plates of alternating size wrap each tunnel mouth. What goes on
# top of that foundation is our own design. Units are grid cells.
import math, os
import bpy, bmesh
import factorykit as fk
from mathutils import Vector
from .kit import bx, arch_pts
from .forms import frustum

rad = math.radians
fk.PAL.update({
    "h_grey": "#b1b7b8", "h_dark": "#989e9f", "h_lite": "#c3c8c9", "h_taupe": "#675f5e", "h_taupe_d": "#544d4c",
    "h_belt": "#2c322e", "h_line": "#8f958f", "h_white": "#d6d6d3", "h_slit": "#3c4040", "h_steel": "#7f8687",
    "h_glow": "#ff5a2a",
})
fk.EMIT.update({"h_glow": 1.6})
G, T, TD, W, D, SLIT = "h_grey", "h_taupe", "h_taupe_d", "h_white", "h_dark", "h_slit"
# The conveyor and tunnel covers of foundation D have colours of their own, so a scheme can paint the
# machine body differently from the conveyor it stands on. By default they match the body.
fk.PAL.update({"h_rail": fk.PAL["h_grey"], "h_rail_d": fk.PAL["h_dark"]})
R, RD = "h_rail", "h_rail_d"
SIDES = (-1, 1)                       # used both for the two sides of the belt and for the two ends
BH, BZ = 0.305, 0.305                 # belt half width and belt surface height
BX, BY = 0.47, 0.43                   # half length and half width of the body block
RAIL = [(BH, 0.0), (0.50, 0.0), (0.50, 0.10), (0.385, 0.215), (0.385, 0.305), (0.36, 0.335), (BH, 0.335)]


def chassis(m, x0=-1.5, x1=1.5, gap=None):
    """The conveyor: bed, belt with thin arrow lines, rails with hex bolts. Rails and bed are one piece,
    so the cut end is a single clean face with no seams, and both ends are cut square at the cell
    boundary so it butts against the next belt or machine. `gap` leaves the rails out under a body,
    where the plinth takes their place."""
    L, cx = x1 - x0, (x0 + x1) / 2
    bed_top = BZ - 0.03
    section = [(-y, z) for y, z in RAIL[1:]] + [(-BH, bed_top), (BH, bed_top)] + list(reversed(RAIL[1:]))
    spans = [(x0, x1)] if gap is None else [(x0, gap[0]), (gap[1], x1)]
    for a, b in spans:
        m.prism(section, a, b, "X", G)
        n = max(1, round((b - a) * 4))
        for i in range(n):
            bxp = a + (i + 0.5) * (b - a) / n
            if gap is None or abs(bxp) > max(abs(gap[0]), abs(gap[1])) + 0.2:
                for s in SIDES:
                    m.cyl(0.027, 0.03, (bxp, s * 0.391, 0.262), G, seg=6, axis="Y")
    if gap is not None:
        m.box((gap[1] - gap[0], BH * 2, bed_top), ((gap[0] + gap[1]) / 2, 0, bed_top / 2), G)
    m.box((L, BH * 2, 0.03), (cx, 0, BZ - 0.015), "h_belt")
    x = x0 + 0.115
    while x < x1 - 0.05:
        for s in SIDES:
            m.box((0.013, 0.30, 0.004), (x - 0.02, s * 0.145, BZ + 0.002), "h_line", rot=s * 0.145)
        x += 0.19


def bellows(m, d, x=BX):
    """Six plates round a tunnel mouth at one end of the body. d is -1 for the west end, +1 for the east."""
    plates = ((0.07, 0.76, 0.725), (0.04, 0.70, 0.69), (0.04, 0.735, 0.71), (0.04, 0.69, 0.68),
              (0.04, 0.735, 0.71), (0.06, 0.78, 0.74))
    px = d * x
    for t, w, top in plates:
        a, b = sorted((px, px + d * t))
        m.prism(arch_pts(w, top, hole_top=top - 0.095, hw=0.31, c=0.03, ci=0.02), a, b, "X", G)
        px += d * (t + 0.008)
    m.box((0.02, 0.62, 0.34), (d * (x + 0.012), 0, 0.47), SLIT)


def foundation_a(m, top=0.82):
    """Foundation A, the one measured from Islands: chassis, bellows at both ends, dark plinth, light
    moulding and the body block. Returns the height of the block's top."""
    chassis(m, gap=(-0.56, 0.56))
    for d in SIDES:
        bellows(m, d)
    bx(m, (-0.56, 0.56), (-0.50, 0.50), (0.0, 0.25), T, bevel=0.05)
    bx(m, (-0.505, 0.505), (-0.46, 0.46), (0.225, 0.30), G, bevel=0.028)
    bx(m, (-BX, BX), (-BY, BY), (0.27, top), G, bevel=0.028)
    return top


def gear(m, r, depth, loc, mk, teeth=12, root=0.74, base=0.62, tip=0.20, half_step=False):
    """A gear cut as one outline: each tooth is wide at the root and tapers to a narrow flat tip, so its
    corners look cut back. Not a square stuck on a disc, and not a spike. It lies in the X-Z plane with a
    tooth pointing straight up, so it is its own mirror image left to right."""
    x, y, z = loc
    step = 2 * math.pi / teeth
    pts = []
    for k in range(teeth):
        c = math.pi / 2 + k * step + (step / 2 if half_step else 0.0)
        for a, rr in ((c - step * base / 2, r * root), (c - step * tip / 2, r), (c + step * tip / 2, r),
                      (c + step * base / 2, r * root)):
            pts.append((x + math.cos(a) * rr, z + math.sin(a) * rr))
    m.prism(pts, y - depth / 2, y + depth / 2, "Y", mk)


def side_pipe(m, x, path, r=0.036, mk=W, seg=8):
    """One continuous round pipe whose centre line lies in the plane at this x. `path` is a list of
    (y, z) points; each bend is mitred. Because every ring is laid out from the X axis, a pipe and its
    mirror image (across the belt or end to end) match exactly."""
    pts = [Vector((0.0, y, z)) for y, z in path]
    n = len(pts)
    seg_dir = [(pts[i + 1] - pts[i]).normalized() for i in range(n - 1)]
    bm = bmesh.new()
    rings = []
    for i in range(n):
        if i == 0:
            tan, k = seg_dir[0], 1.0
        elif i == n - 1:
            tan, k = seg_dir[-1], 1.0
        else:
            tan = (seg_dir[i - 1] + seg_dir[i]).normalized()
            k = 1.0 / max(seg_dir[i - 1].dot(tan), 0.5)
        nrm = Vector((0.0, -tan.z, tan.y))                    # in the plane of the path, square to it
        ring = []
        for j in range(seg):
            a = 2 * math.pi * j / seg
            ring.append(bm.verts.new(Vector((x, 0, 0)) + pts[i] + Vector((1, 0, 0)) * (r * math.cos(a))
                                     + nrm * (r * k * math.sin(a))))
        rings.append(ring)
    for a, b in zip(rings, rings[1:]):
        for j in range(seg):
            bm.faces.new((a[j], a[(j + 1) % seg], b[(j + 1) % seg], b[j]))
    bm.faces.new(rings[0])
    bm.faces.new(rings[-1])
    m._add(bm, mk)


def pipe_from_neck(m, px, d, z, neck_y, wall_y, foot=0.25, r=0.036, mk=W):
    """A pipe with both ends fixed to something: it leaves a flanged socket on the side of the neck above
    the body, runs out over the body's shoulder, turns down through one clean 45-degree bend, and drops
    into a flanged socket on top of the plinth."""
    yc = wall_y + d * (r + 0.004)
    c = 0.045
    side_pipe(m, px, [(neck_y - d * 0.03, z), (yc - d * c, z), (yc, z - c), (yc, foot - 0.02)], r, mk)
    m.cyl(r * 1.38, 0.028, (px, neck_y + d * 0.014, z), mk, seg=8, axis="Y")       # socket on the neck
    m.cyl(r * 1.38, 0.03, (px, yc, foot + 0.015), mk, seg=8)                        # socket on the plinth


def side_panel(m, d, w=0.74, h=0.30, z=0.60):
    """The raised panel on a side wall. Returns the y of its face, for whatever is mounted on it."""
    y = d * BY
    m.box((w, 0.04, h), (0, y + d * 0.012, z), G, bevel=0.028)
    return y + d * 0.036


def hex_stack(m, x, y, z0, h, r=0.07, mk=G, glow=False):
    """A flue of hex drums: a flared foot, drums of alternating width, a flared mouth."""
    m.cyl(r * 1.4, 0.06, (x, y, z0 + 0.03), D, seg=6)
    n = max(2, round((h - 0.06) / 0.17))
    t = (h - 0.06) / n
    for i in range(n):
        m.cyl(r * (1.0, 0.8)[i % 2], t, (x, y, z0 + 0.06 + (i + 0.5) * t), mk, seg=6)
    m.cyl(r * 0.85, 0.09, (x, y, z0 + h + 0.045), D, seg=6, r2=r * 1.3)
    m.cyl(r * 1.0, 0.01, (x, y, z0 + h + 0.092), "h_glow" if glow else SLIT, seg=6)


def symmetry_report(mesh):
    """How many vertices have no mirror partner across the belt and end to end (belt arrows excluded)."""
    pts = {(round(v.co.x, 2), round(v.co.y, 2), round(v.co.z, 2)) for v in mesh.vertices}
    across = sum(1 for p in pts if (p[0], -p[1], p[2]) not in pts)
    along = sum(1 for p in pts if (-p[0], p[1], p[2]) not in pts and not 0.30 <= p[2] <= 0.32)
    return across, along, len(pts)


def show(build, name, out_dir):
    """Build one model and render it from the catalog angle and straight on from the side, top and end."""
    m = fk.Model(name)
    build(m)
    mesh = m.done()
    ob = fk.place(mesh, (0, 0, 0))
    for o in bpy.context.selected_objects:
        o.select_set(False)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    try:
        bpy.ops.object.shade_smooth_by_angle(angle=rad(34))
    except Exception:
        pass
    scene = fk.scene
    fk.sun.hide_render = True
    fk.bg.inputs[0].default_value = (1, 1, 1, 1)
    fk.bg.inputs[1].default_value = 0.70
    if "hero_key" not in bpy.data.objects:
        sd = bpy.data.lights.new("hero_key", "SUN")
        sd.energy, sd.angle = 1.9, rad(4)
        try:
            sd.use_shadow = False
        except Exception:
            pass
        key = bpy.data.objects.new("hero_key", sd)
        fk.col.objects.link(key)
        fk.aim(key, (-7.0, -1.6, 9.0), (0, 0, 0))
    elev = rad(30)
    iso = Vector((-math.cos(elev) * math.cos(rad(45)), -math.cos(elev) * math.sin(rad(45)), math.sin(elev)))
    up = (-iso).cross(Vector((0, 0, 1))).normalized().cross(-iso)
    scene.render.film_transparent = True
    scene.render.resolution_x = scene.render.resolution_y = 1000
    scene.cycles.samples = 64
    os.makedirs(out_dir, exist_ok=True)
    views = (("", iso, up * 0.474, 2.871), ("_side", Vector((0, -1, 0.0001)), Vector((0, 0, 0.6)), 3.2),
             ("_top", Vector((0, -0.0001, 1)), Vector((0, 0, 0.6)), 3.2), ("_end", Vector((-1, 0.0001, 0.0001)), Vector((0, 0, 0.6)), 1.6))
    for suffix, v, c, scale in views:
        fk.cd.ortho_scale = scale
        fk.aim(fk.cam, c + v.normalized() * 30, c)
        scene.render.filepath = os.path.join(out_dir, name + suffix + ".png")
        bpy.ops.render.render(write_still=True)
    across, along, total = symmetry_report(mesh)
    print(f"HERO {name}: tris={m.tris} unmirrored across-belt={across} end-to-end={along} of {total}")
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out_dir, name + ".blend"))
    ob.hide_render = True
    ob.hide_viewport = True


def octa(m, a0, a1, z0, z1, mk):
    """An eight-sided solid with flats facing along and across the belt. a0 and a1 are the distances from
    the centre line to a flat at the bottom and at the top."""
    k = 1.0 / math.cos(math.pi / 8)
    m.cyl(a0 * k, z1 - z0, (0, 0, (z0 + z1) / 2), mk, seg=8, r2=a1 * k, rot=rad(22.5))


def oct_ring(m, a_out, t, z0, z1, mk):
    """An eight-sided ring with an open centre. Each of its eight bars is cut at an angle at both ends so
    that neighbours meet in a mitre, with no gap at the corners."""
    k = 1.0 / math.cos(math.pi / 8)
    ro, ri = a_out * k, (a_out - t) * k
    for j in range(8):
        a0 = math.pi / 8 + j * math.pi / 4
        a1 = a0 + math.pi / 4
        m.prism([(ro * math.cos(a0), ro * math.sin(a0)), (ro * math.cos(a1), ro * math.sin(a1)),
                 (ri * math.cos(a1), ri * math.sin(a1)), (ri * math.cos(a0), ri * math.sin(a0))], z0, z1, "Z", mk)


# ============================ FOUNDATIONS OF OUR OWN ============================
# Foundation A copies the proportions of Islands' conveyor, bellows and plinth closely enough to be a
# risk. B and C keep the same body block (so every hero machine fits unchanged) but replace those three
# things with shapes of our own. Pick one with set_style() before building.
STYLE = "a"
DARKS = {"a": ("#675f5e", "#544d4c"), "b": ("#56616c", "#434c56"), "c": ("#5c6063", "#484b4e")}


def set_style(style):
    """Choose the foundation. Call before anything is built: it also sets the dark accent colour."""
    global STYLE
    STYLE = style
    fk.PAL["h_taupe"], fk.PAL["h_taupe_d"] = DARKS[style]


def arrows(m, x0, x1, step=0.30):
    """Small solid arrowheads down the middle of the belt."""
    n = max(1, round((x1 - x0) / step))
    for i in range(n):
        x = x0 + (i + 0.5) * (x1 - x0) / n
        m.prism([(x - 0.045, -0.075), (x - 0.045, 0.075), (x + 0.06, 0.0)], BZ, BZ + 0.004, "Z", "h_line")


def chassis_section(m, right, x0, x1, bed_top):
    """A conveyor whose rails and bed are one outline. `right` lists the right-hand rail's points from the
    bed outward and down to the ground; the left rail is its mirror image."""
    section = [(-y, z) for y, z in reversed(right)] + [(-BH, bed_top), (BH, bed_top)] + list(right)
    m.prism(section, x0, x1, "X", G)
    m.box((x1 - x0, BH * 2, 0.03), ((x0 + x1) / 2, 0, BZ - 0.015), "h_belt")
    arrows(m, x0, x1)


def foundation_b(m, top=0.82):
    """Foundation B. The conveyor has an upright side wall with a flat shelf on it and a low guard along
    the belt; round axle caps run down the wall. It passes unbroken under the body, which is held to it
    by a saddle clamp near each corner. Each tunnel mouth is a hood that narrows toward a flanged
    opening hung with a strip curtain."""
    right = [(BH, 0.365), (BH + 0.05, 0.365), (BH + 0.05, 0.30), (0.455, 0.30), (0.50, 0.255), (0.50, 0.0)]
    chassis_section(m, right, -1.5, 1.5, BZ - 0.03)
    for i in range(12):
        x = -1.375 + i * 0.25
        if 0.60 < abs(x):
            for s in SIDES:
                m.cyl(0.03, 0.02, (x, s * 0.503, 0.14), D, seg=10, axis="Y")
    bx(m, (-BX, BX), (-BY, BY), (0.0, top), G, bevel=0.028)
    for d in SIDES:                                           # d: which side of the belt
        for sx in SIDES:
            xs = tuple(sorted((sx * 0.21, sx * 0.39)))
            ys = tuple(sorted((d * 0.40, d * 0.499)))
            bx(m, xs, ys, (0.0, 0.42), T, bevel=0.035)
            m.cyl(0.035, 0.02, (sx * 0.30, d * 0.505, 0.20), G, seg=6, axis="Y")
    for d in SIDES:                                           # d: which end of the body
        x0, x1 = d * BX, d * (BX + 0.24)
        m.prism([(x0, 0.80), (x1, 0.69), (x1, 0.62), (x0, 0.73)], -0.385, 0.385, "Y", G)
        for s in SIDES:
            ylo, yhi = sorted((s * 0.325, s * 0.385))
            m.prism([(x0, 0.28), (x1, 0.28), (x1, 0.66), (x0, 0.77)], ylo, yhi, "Y", G)
        a, b = sorted((x1, x1 + d * 0.05))
        m.prism(arch_pts(0.86, 0.74, hole_top=0.60, hw=0.315, c=0.05, ci=0.025), a, b, "X", D)
        for k in range(5):                                    # strip curtain
            m.box((0.012, 0.112, 0.27), (x1 + d * 0.02, -0.25 + k * 0.125, 0.465), SLIT)
        m.box((0.02, 0.62, 0.40), (d * (BX + 0.012), 0, 0.50), SLIT)
    return top


def foundation_c(m, top=0.82):
    """Foundation C. The conveyor has a stepped curb with long slots cut in its wall. The body stands on
    four corner feet over a recessed kick strip, with the curb passing under it. Each tunnel mouth is
    two deep hoods, one inside the other."""
    right = [(BH, 0.345), (0.385, 0.345), (0.385, 0.235), (0.50, 0.235), (0.50, 0.0)]
    chassis_section(m, right, -1.5, 1.5, BZ - 0.03)
    for i in range(12):
        x = -1.375 + i * 0.25
        if 0.62 < abs(x):
            for s in SIDES:
                m.box((0.15, 0.012, 0.045), (x, s * 0.501, 0.12), SLIT)
    bx(m, (-BX, BX), (-BY, BY), (0.0, top), G, bevel=0.028)
    for d in SIDES:
        m.box((BX * 2 - 0.10, 0.012, 0.085), (0, d * (BY + 0.002), 0.30), TD)          # kick strip
        for sx in SIDES:
            xs = tuple(sorted((sx * 0.33, sx * 0.50)))
            ys = tuple(sorted((d * 0.40, d * 0.499)))
            bx(m, xs, ys, (0.0, 0.30), T, bevel=0.035)
    for d in SIDES:
        x0 = d * BX
        for depth, w, tp, mk in ((0.14, 0.88, 0.80, G), (0.27, 0.78, 0.71, D)):
            a, b = sorted((x0, x0 + d * depth))
            m.prism(arch_pts(w, tp, hole_top=tp - 0.11, hw=0.315, c=0.07, ci=0.03), a, b, "X", mk)
        for s in SIDES:
            for z in (0.40, 0.70):
                m.cyl(0.026, 0.02, (d * (BX + 0.145), s * 0.395, z), D, seg=6, axis="X")
        m.box((0.02, 0.62, 0.40), (d * (BX + 0.012), 0, 0.50), SLIT)
    return top


def chevrons2(m, x0, x1, step=0.375):
    """Pairs of hairline chevrons down the belt, pointing the way it runs."""
    n = max(1, round((x1 - x0) / step))
    for i in range(n):
        xc = x0 + (i + 0.5) * (x1 - x0) / n
        for dx in (-0.035, 0.035):
            for s in SIDES:
                m.box((0.011, 0.26, 0.004), (xc + dx, s * 0.12, BZ + 0.002), "h_line", rot=s * 0.36)


def foundation_d(m, top=0.82):
    """Foundation D, our own, with the richness of A kept and its shapes changed.
    The rail leans in all the way up to a stout eight-sided cap, and is braced by a row of triangular
    buttresses instead of bolts. Each tunnel mouth is a folding cover of our own proportions: four
    broad-shouldered ridges with darker, smaller webs between them, closed by a heavier end frame. The
    body stands on two cross beams whose I-section ends show at each side, and has a chamfered base
    course of its own."""
    bed_top = BZ - 0.03
    right = [(BH, 0.352), (0.372, 0.352), (0.402, 0.326), (0.402, 0.292), (0.386, 0.276), (0.474, 0.055),
             (0.50, 0.055), (0.50, 0.0)]
    section = [(-y, z) for y, z in reversed(right)] + [(-BH, bed_top), (BH, bed_top)] + list(right)
    m.prism(section, -1.5, 1.5, "X", R)
    m.box((3.0, BH * 2, 0.03), (0, 0, BZ - 0.015), "h_belt")
    chevrons2(m, -1.5, 1.5)
    for x in (-4 / 3, -1.0, 1.0, 4 / 3):                      # buttresses along both rails, three to a cell
        for s in SIDES:
            pts = [(s * 0.40, 0.268), (s * 0.498, 0.17), (s * 0.498, 0.055), (s * 0.47, 0.055)]
            m.prism(pts, x - 0.022, x + 0.022, "X", RD)
    # two cross beams under the body; their I-section ends show at each side
    beam = [(-0.125, 0.0), (0.125, 0.0), (0.125, 0.065), (0.05, 0.10), (0.05, 0.175), (0.125, 0.21),
            (0.125, 0.27), (-0.125, 0.27), (-0.125, 0.21), (-0.05, 0.175), (-0.05, 0.10), (-0.125, 0.065)]
    for sx in SIDES:
        m.prism([(sx * 0.27 + px, pz) for px, pz in beam], -0.499, 0.499, "Y", T)
    bx(m, (-BX - 0.02, BX + 0.02), (-BY - 0.02, BY + 0.02), (0.262, 0.345), G, bevel=0.03)      # base course
    bx(m, (-BX, BX), (-BY, BY), (0.30, top), G, bevel=0.028)
    for d in SIDES:                                           # a folding cover on a sill at each end
        x0 = d * BX
        for s in SIDES:                                       # the sill stands on the rails, clear of the belt
            ys = tuple(sorted((s * 0.34, s * 0.458)))
            bx(m, tuple(sorted((x0, x0 + d * 0.345))), ys, (0.0, 0.31), R, bevel=0.03)
        px = x0
        folds = [(0.042, 0.84, 0.77, 0.315, R), (0.026, 0.77, 0.735, 0.335, RD)] * 4
        for th, w, tp, hw, mk in folds + [(0.066, 0.88, 0.79, 0.315, R)]:
            a, b = sorted((px, px + d * th))
            m.prism(arch_pts(w, tp, hole_top=tp - 0.11, hw=hw, c=0.085, ci=0.035), a, b, "X", mk)
            px += d * th
        m.box((0.02, 0.62, 0.40), (d * (BX + 0.012), 0, 0.50), SLIT)
    return top


FOUNDATIONS = {"a": foundation_a, "b": foundation_b, "c": foundation_c, "d": foundation_d}
DARKS["d"] = DARKS["a"]


def foundation(m, top=0.82):
    """Build whichever foundation set_style() chose. Returns the height of the body block's top."""
    return FOUNDATIONS[STYLE](m, top)


# ============================ COLOUR SCHEMES ============================
# The default greys and the warm dark accent were sampled from Islands' renders, which is a large part of
# why the machines still read as Islands. These schemes are trials of a colour identity of our own.
TINTS = {
    "sage": {"h_grey": "#9fb3a3", "h_dark": "#869a8b", "h_lite": "#b5c6b7", "h_taupe": "#4a5257",
             "h_taupe_d": "#3a4145", "h_white": "#dedfd6", "h_steel": "#8b9294"},
    "sand": {"h_grey": "#d2c6ae", "h_dark": "#b8ac94", "h_lite": "#e0d6c1", "h_taupe": "#3f586c",
             "h_taupe_d": "#314552", "h_white": "#efeae0", "h_steel": "#8f8a80"},
    "iron": {"h_grey": "#6d757c", "h_dark": "#596168", "h_lite": "#828a91", "h_taupe": "#d68a2c",
             "h_taupe_d": "#ad6d1e", "h_white": "#c8cccf", "h_steel": "#a3aaaf", "h_line": "#c9a24a"},
    # painted orange panels on a bare steel conveyor, after Satisfactory's colour language
    "ficsit": {"h_grey": "#e2893a", "h_dark": "#c2722e", "h_lite": "#eea258", "h_taupe": "#474d5a",
               "h_taupe_d": "#383d48", "h_white": "#dcddde", "h_steel": "#9aa0a6", "h_line": "#d9c56c",
               "h_rail": "#8c9298", "h_rail_d": "#747a80"},
}


def set_tint(name):
    """Recolour everything with one of TINTS. Call after set_style() and before anything is built."""
    c = TINTS[name]
    fk.PAL.update(c)
    fk.PAL["h_rail"] = c.get("h_rail", c["h_grey"])
    fk.PAL["h_rail_d"] = c.get("h_rail_d", c["h_dark"])
