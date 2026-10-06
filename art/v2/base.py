# v2 base: the foundation every "hero" machine is built on, and the camera that shows it.
#
# The numbers were measured from Islands' Industrial Smelter render (see docs/specs/2026-10-06-models-v2.md):
# the chassis is one cell wide and three long, the body is as wide as the chassis and stands on a dark
# plinth with a light moulding, and six plates of alternating size wrap each tunnel mouth. What goes on
# top of that foundation is our own design. Units are grid cells.
import math, os
import bpy
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


def gear(m, r, depth, loc, mk, teeth=12, root=0.78, base=0.60, tip=0.34, half_step=False):
    """A gear cut as one outline: each tooth is wide at the root and narrower at a flat tip. It lies in
    the X-Z plane with a tooth pointing straight up, so it is its own mirror image left to right."""
    x, y, z = loc
    step = 2 * math.pi / teeth
    pts = []
    for k in range(teeth):
        c = math.pi / 2 + k * step + (step / 2 if half_step else 0.0)
        for a, rr in ((c - step * base / 2, r * root), (c - step * tip / 2, r), (c + step * tip / 2, r),
                      (c + step * base / 2, r * root)):
            pts.append((x + math.cos(a) * rr, z + math.sin(a) * rr))
    m.prism(pts, y - depth / 2, y + depth / 2, "Y", mk)


def wall_pipe(m, px, d, wall_y, z_top, foot=0.25, r=0.042, mk=W):
    """A round pipe that leaves a side wall, turns down through a 45-degree elbow and runs to the plinth.
    It is made of straight pieces so that mirrored copies are exact mirror images."""
    out = wall_y + d * 0.062
    m.cyl(r, 0.07, (px, wall_y + d * 0.005, z_top), mk, seg=8, axis="Y")
    m.cyl(r, 0.075, (px, wall_y + d * 0.047, z_top - 0.022), mk, seg=8, axis="Y", rot=(d * rad(45), 0, 0))
    m.cyl(r, z_top - 0.045 - foot, (px, out, (z_top - 0.045 + foot) / 2), mk, seg=8)
    m.cyl(r * 1.32, 0.03, (px, out, foot + 0.012), mk, seg=8)
    m.cyl(r * 1.32, 0.025, (px, wall_y + d * 0.012, z_top), mk, seg=8, axis="Y")


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
