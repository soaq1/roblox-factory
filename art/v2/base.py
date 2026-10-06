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
SIDES = (-1, 1)                       # used both for the two sides of the belt and for the two ends
BH, BZ = 0.305, 0.305                 # belt half width and belt surface height
BX, BY = 0.47, 0.43                   # half length and half width of the body block
RAIL = [(BH, 0.0), (0.50, 0.0), (0.50, 0.10), (0.385, 0.215), (0.385, 0.305), (0.36, 0.335), (BH, 0.335)]


def chassis(m, x0=-1.5, x1=1.5, gap=None):
    """The conveyor: bed, belt with thin arrow lines, rails with hex bolts. Both ends are cut square at
    the cell boundary so it butts against the next belt or machine. `gap` leaves the rails out under a
    body, where the plinth takes their place."""
    L, cx = x1 - x0, (x0 + x1) / 2
    m.box((L, BH * 2 - 0.004, 0.275), (cx, 0, 0.1375), G)
    m.box((L, BH * 2 - 0.004, 0.03), (cx, 0, BZ - 0.015), "h_belt")
    spans = [(x0, x1)] if gap is None else [(x0, gap[0]), (gap[1], x1)]
    for a, b in spans:
        m.prism(RAIL, a, b, "X", G)
        m.prism([(-y, z) for y, z in RAIL], a, b, "X", G)
        n = max(1, round((b - a) * 4))
        for i in range(n):
            bxp = a + (i + 0.5) * (b - a) / n
            if gap is None or abs(bxp) > max(abs(gap[0]), abs(gap[1])) + 0.2:
                for s in SIDES:
                    m.cyl(0.027, 0.03, (bxp, s * 0.391, 0.262), G, seg=6, axis="Y")
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


def foundation(m, top=0.82):
    """Chassis, bellows at both ends, dark plinth, light moulding and the body block. Returns the height
    of the block's top."""
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
