# Factory art kit: shared palette, chassis and port grammar, belts, machines, items.
# Run:  Blender --background --python factorykit.py -- [thumbs] [line] [eevee]
import bpy, bmesh, math, os, random, json, sys
from contextlib import contextmanager
from mathutils import Vector, Matrix, Euler

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "catalog")
os.makedirs(os.path.join(OUT, "img"), exist_ok=True)
ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ["thumbs", "line"]

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
col = scene.collection
rng = random.Random(7)
rad = math.radians

PAL = {
    # machine metal
    "body": "#c2beb7", "light": "#e4e1db", "mid": "#8f8b85", "dark": "#484643",
    "belt": "#2b2a29", "beltmark": "#5d5a56", "hole": "#141516",
    # meaning colours
    "accent": "#f0b429",      # input port
    "out": "#35b8a6",         # output port
    "glow": "#ff5a1f",        # heat
    "water": "#4aa8d8", "water_light": "#9ad6f0",
    "red": "#d9483b", "spark": "#ffd84a",
    # materials handled
    "gold": "#f4c542", "gold_dark": "#d19a1c", "copper": "#d9824c", "iron": "#8fa0b3",
    "steel": "#5f7389", "coal": "#2f2d30", "oil": "#2a2530", "stone": "#a4a8ae",
    "stone_dark": "#878c93", "sand": "#e3cf9a", "glass": "#bfe6ee",
    "wood": "#c99c61", "wood_dark": "#a87d47", "wood_light": "#e3c58f",
    "brick": "#b5553c", "brick_dark": "#9c4631", "mortar": "#d6d0c6",
    "wheat": "#cdb850", "wheat_head": "#ecd465", "cream": "#efe2c8", "bread": "#d39a55",
    "pcb": "#2f9e5b", "diamond": "#86e3ea", "clay": "#b9a79a", "charcoal": "#3b3632", "tar": "#1e1b22",
    "slag": "#6e6a70", "cotton": "#f4f2ee", "dough": "#ead9b0", "asphalt": "#4b4b50", "dirt": "#9a6a44",
    "leaf": "#4f9f4d", "leaf_light": "#7cc468", "dirt_dark": "#7d5437", "copper_light": "#f2a878",
    "core_stone": "#c9cdd2", "core_gold": "#ffd24a", "core_dia": "#8ff0f5", "monster": "#9a62e0", "solar": "#2c4a78", "core_fe": "#a9c4e2", "core_coal": "#4b4654", "core_cu": "#f2a06a", "slurry": "#9aa6ad", "white": "#f2f0ea", "floor": "#d9dcdf",
}
EMIT = {"glow": 3.0, "spark": 1.5, "core_fe": 0.9, "core_cu": 0.9, "core_coal": 0.15, "core_gold": 0.9, "core_dia": 1.1, "core_stone": 0.4, "monster": 0.9}
_mats = {}


def lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def MAT(key):
    if key not in _mats:
        h = PAL[key].lstrip("#")
        rgb = [lin(int(h[i:i + 2], 16) / 255) for i in (0, 2, 4)]
        m = bpy.data.materials.new(key)
        if m.node_tree is None:
            m.use_nodes = True
        bsdf = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        bsdf.inputs["Base Color"].default_value = (*rgb, 1)
        bsdf.inputs["Roughness"].default_value = 0.9
        if key in EMIT:
            bsdf.inputs["Emission Color"].default_value = (*rgb, 1)
            bsdf.inputs["Emission Strength"].default_value = EMIT[key]
        _mats[key] = m
    return _mats[key]


AXIS = {"Z": Matrix.Identity(4),
        "X": Matrix.Rotation(math.pi / 2, 4, "Y"),
        "Y": Matrix.Rotation(-math.pi / 2, 4, "X")}


class Model:
    """Accumulates geometry into one mesh, one material slot per palette key."""

    def __init__(self, name):
        self.name, self.bm, self.mats = name, bmesh.new(), []
        self.stack = [Matrix.Identity(4)]

    @contextmanager
    def at(self, loc=(0, 0, 0), rz=0.0):
        self.stack.append(self.stack[-1] @ Matrix.Translation(Vector(loc))
                          @ Matrix.Rotation(rz, 4, "Z"))
        yield
        self.stack.pop()

    def _add(self, tbm, mk, loc=(0, 0, 0), rot=0.0):
        bmesh.ops.recalc_face_normals(tbm, faces=tbm.faces[:])
        r = (Matrix.Rotation(rot, 4, "Z") if isinstance(rot, (int, float))
             else Euler(rot, "XYZ").to_matrix().to_4x4())
        mx = self.stack[-1] @ Matrix.Translation(Vector(loc)) @ r
        bmesh.ops.transform(tbm, matrix=mx, verts=tbm.verts[:])
        me = bpy.data.meshes.new("tmp")
        tbm.to_mesh(me)
        tbm.free()
        n = len(self.bm.faces)
        self.bm.from_mesh(me)
        bpy.data.meshes.remove(me)
        if mk not in self.mats:
            self.mats.append(mk)
        idx = self.mats.index(mk)
        for f in list(self.bm.faces)[n:]:
            f.material_index = idx

    def box(self, size, loc, mk, bevel=0.0, taper=1.0, rot=0.0):
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1)
        for v in bm.verts:
            k = taper if v.co.z > 0 else 1.0
            v.co = Vector((v.co.x * size[0] * k, v.co.y * size[1] * k, v.co.z * size[2]))
        if bevel:
            bmesh.ops.bevel(bm, geom=bm.edges[:], offset=bevel, segments=1,
                            affect="EDGES", profile=0.5)
        self._add(bm, mk, loc, rot)

    def cyl(self, r, depth, loc, mk, seg=8, axis="Z", r2=None, rot=0.0):
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r,
                              radius2=r if r2 is None else r2, depth=depth,
                              matrix=AXIS[axis])
        self._add(bm, mk, loc, rot)

    def gear(self, r, depth, loc, mk, teeth=8, axis="X", rot=0.0):
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, segments=teeth * 2, radius1=r * 0.78,
                              radius2=r * 0.78, depth=depth)
        for i in range(teeth):
            mm = (Matrix.Rotation(i * 2 * math.pi / teeth, 4, "Z")
                  @ Matrix.Translation((r * 0.86, 0, 0))
                  @ Matrix.Diagonal((r * 0.34, r * 0.30, depth, 1)))
            bmesh.ops.create_cube(bm, size=1, matrix=mm)
        bmesh.ops.transform(bm, matrix=AXIS[axis], verts=bm.verts[:])
        self._add(bm, mk, loc, rot)

    def ico(self, r, loc, mk, squash=1.0, jitter=0.0):
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=1, radius=r)
        for v in bm.verts:
            v.co *= 1 + rng.uniform(-jitter, jitter)
            v.co.z *= squash
        self._add(bm, mk, loc)

    def prism(self, pts, lo, hi, axis, mk):
        """Extrude a 2D outline. X takes (y, z), Y takes (x, z), Z takes (x, y)."""
        bm = bmesh.new()
        if axis == "X":
            verts, vec = [bm.verts.new((lo, a, b)) for a, b in pts], (hi - lo, 0, 0)
        elif axis == "Y":
            verts, vec = [bm.verts.new((a, lo, b)) for a, b in pts], (0, hi - lo, 0)
        else:
            verts, vec = [bm.verts.new((a, b, lo)) for a, b in pts], (0, 0, hi - lo)
        face = bm.faces.new(verts)
        ext = bmesh.ops.extrude_face_region(bm, geom=[face])
        moved = [e for e in ext["geom"] if isinstance(e, bmesh.types.BMVert)]
        bmesh.ops.translate(bm, verts=moved, vec=vec)
        self._add(bm, mk)

    def pipe(self, pts, r, mk, seg=8):
        pts = [Vector(p) for p in pts]
        n = len(pts)
        sd = [(pts[i + 1] - pts[i]).normalized() for i in range(n - 1)]
        tang = [sd[0]] + [(sd[i - 1] + sd[i]).normalized() for i in range(1, n - 1)] + [sd[-1]]
        ref = Vector((0, 0, 1)) if abs(tang[0].z) < 0.9 else Vector((1, 0, 0))
        nrm = tang[0].cross(ref).normalized()
        bm = bmesh.new()
        rings = []
        for i in range(n):
            if i > 0:
                nrm = tang[i - 1].rotation_difference(tang[i]) @ nrm
            b = tang[i].cross(nrm).normalized()
            k = 1.0 / max(sd[i - 1].dot(tang[i]), 0.5) if 0 < i < n - 1 else 1.0
            rings.append([bm.verts.new(pts[i] + (nrm * math.cos(a) + b * math.sin(a)) * r * k)
                          for a in [j * 2 * math.pi / seg for j in range(seg)]])
        for a, b_ in zip(rings, rings[1:]):
            for j in range(seg):
                bm.faces.new((a[j], a[(j + 1) % seg], b_[(j + 1) % seg], b_[j]))
        bm.faces.new(rings[0])
        bm.faces.new(rings[-1])
        self._add(bm, mk)

    def ring(self, r, tube, z, mk, cx=0.0, cy=0.0, seg=10):
        pts = [(cx + r * math.cos(i * 2 * math.pi / seg), cy + r * math.sin(i * 2 * math.pi / seg), z)
               for i in range(seg + 1)]
        self.pipe(pts, tube, mk, seg=6)

    def done(self):
        me = bpy.data.meshes.new(self.name)
        self.bm.to_mesh(me)
        self.bm.free()
        for mk in self.mats:
            me.materials.append(MAT(mk))
        me.calc_loop_triangles()
        self.tris = len(me.loop_triangles)
        return me


# ---- primitive log -------------------------------------------------------------------------
# Alongside the mesh, every model keeps a list of the simple shapes it was built from
# (boxes, cylinders, balls). The game rebuilds machines from these with Roblox's basic parts.
PRIMS = {}


def _rot(rot):
    return Matrix.Rotation(rot, 4, "Z") if isinstance(rot, (int, float)) else Euler(rot, "XYZ").to_matrix().to_4x4()


def _log(self, shape, size, local, mk):
    if getattr(self, "mute", 0):
        return
    if not hasattr(self, "prims"):
        self.prims = []
    self.prims.append((shape, tuple(size), self.stack[-1] @ local, mk))


Model._log = _log
_box, _cyl, _gear, _ico, _prism, _pipe, _done = (Model.box, Model.cyl, Model.gear, Model.ico, Model.prism,
                                                 Model.pipe, Model.done)


def _box_logged(self, size, loc, mk, bevel=0.0, taper=1.0, rot=0.0):
    k = (1 + taper) / 2
    self._log("b", (size[0] * k, size[1] * k, size[2]), Matrix.Translation(Vector(loc)) @ _rot(rot), mk)
    _box(self, size, loc, mk, bevel, taper, rot)


def _cyl_logged(self, r, depth, loc, mk, seg=8, axis="Z", r2=None, rot=0.0):
    radius = r if r2 is None else (r + r2) / 2
    self._log("c", (depth, radius * 2, radius * 2), Matrix.Translation(Vector(loc)) @ _rot(rot) @ AXIS[axis], mk)
    _cyl(self, r, depth, loc, mk, seg, axis, r2, rot)


def _gear_logged(self, r, depth, loc, mk, teeth=8, axis="X", rot=0.0):
    self._log("c", (depth, r * 1.9, r * 1.9), Matrix.Translation(Vector(loc)) @ _rot(rot) @ AXIS[axis], mk)
    _gear(self, r, depth, loc, mk, teeth, axis, rot)


def _ico_logged(self, r, loc, mk, squash=1.0, jitter=0.0):
    d = r * 2 * (2 + squash) / 3
    self._log("s", (d, d, d), Matrix.Translation(Vector(loc)), mk)
    _ico(self, r, loc, mk, squash, jitter)


def _prism_logged(self, pts, lo, hi, axis, mk):
    a = [p[0] for p in pts]
    b = [p[1] for p in pts]
    ca, cb, cl = (min(a) + max(a)) / 2, (min(b) + max(b)) / 2, (lo + hi) / 2
    sa, sb, sl = max(a) - min(a), max(b) - min(b), abs(hi - lo)
    if axis == "X":
        size, centre = (sl, sa, sb), (cl, ca, cb)
    elif axis == "Y":
        size, centre = (sa, sl, sb), (ca, cl, cb)
    else:
        size, centre = (sa, sb, sl), (ca, cb, cl)
    self._log("b", size, Matrix.Translation(Vector(centre)), mk)
    _prism(self, pts, lo, hi, axis, mk)


def _pipe_logged(self, pts, r, mk, seg=8):
    vs = [Vector(p) for p in pts]
    for a, b in zip(vs, vs[1:]):
        d = b - a
        if d.length > 1e-6:
            turn = d.to_track_quat("Z", "Y").to_matrix().to_4x4()
            self._log("c", (d.length + r, r * 2, r * 2), Matrix.Translation((a + b) / 2) @ turn, mk)
    _pipe(self, pts, r, mk, seg)


def _done_logged(self):
    PRIMS[self.name] = getattr(self, "prims", [])
    return _done(self)


Model.box, Model.cyl, Model.gear, Model.ico = _box_logged, _cyl_logged, _gear_logged, _ico_logged
Model.prism, Model.pipe, Model.done = _prism_logged, _pipe_logged, _done_logged


@contextmanager
def muted(m):
    """Build geometry without logging it, for shapes that are logged by hand instead."""
    m.mute = getattr(m, "mute", 0) + 1
    yield
    m.mute -= 1


def place(mesh, loc, rz=0.0, mirror_x=False, mirror_y=False):
    ob = bpy.data.objects.new(mesh.name, mesh)
    ob.location = loc
    ob.rotation_euler = (0, 0, rz)
    ob.scale = (-1 if mirror_x else 1, -1 if mirror_y else 1, 1)
    col.objects.link(ob)
    return ob


# ============================ KIT PARTS ============================
RAIL = [(0.34, 0.10), (0.48, 0.10), (0.48, 0.29), (0.43, 0.36), (0.34, 0.36)]
SIDE_ANG = {"E": 0.0, "N": math.pi / 2, "W": math.pi, "S": -math.pi / 2}


def chev(m, x, y, ang=0.0, z=0.302):
    with m.at((x, y, z), ang):
        for s in (-1, 1):
            m.box((0.19, 0.04, 0.012), (0, s * 0.07, 0), "beltmark", rot=-s * rad(49))


def port(m, side, kind, off=0.0, sx=1, sy=1):
    """Tunnel mouth on one side. Yellow lip = input, teal lip = output."""
    d = (sx if side in "EW" else sy) / 2
    o = off if side in ("E", "S") else -off
    with m.at((0, 0, 0), SIDE_ANG[side]):
        c, hw, top = 0.07, 0.47, 0.80
        frame = [(-hw, 0.02), (-hw, top - c), (-hw + c, top), (hw - c, top), (hw, top - c),
                 (hw, 0.02), (0.36, 0.02), (0.36, 0.66), (-0.36, 0.66), (-0.36, 0.02)]
        lip = [(-0.36, 0.30), (-0.36, 0.66), (0.36, 0.66), (0.36, 0.30),
               (0.31, 0.30), (0.31, 0.61), (-0.31, 0.61), (-0.31, 0.30)]
        lip_colour = "accent" if kind == "in" else "out"
        with muted(m):
            m.prism([(y + o, z) for y, z in frame], d - 0.10, d, "X", "light")
            m.prism([(y + o, z) for y, z in lip], d - 0.06, d - 0.01, "X", lip_colour)
        for side_y in (-0.415, 0.415):
            m._log("b", (0.10, 0.11, 0.78), Matrix.Translation((d - 0.05, o + side_y, 0.41)), "light")
            m._log("b", (0.05, 0.05, 0.36), Matrix.Translation((d - 0.035, o + side_y * 0.807, 0.48)), lip_colour)
        m._log("b", (0.10, 0.94, 0.14), Matrix.Translation((d - 0.05, o, 0.73)), "light")
        m._log("b", (0.05, 0.72, 0.05), Matrix.Translation((d - 0.035, o, 0.635)), lip_colour)
        m.box((0.012, 0.72, 0.36), (d - 0.054, o, 0.48), "hole")
        m.box((0.10, 0.72, 0.22), (d - 0.05, o, 0.13), "dark")
        m.box((0.10, 0.68, 0.06), (d - 0.05, o, 0.27), "belt")


def chassis(m, sx=1, sy=1, ports=(), h=0.80):
    m.box((sx - 0.04, sy - 0.04, 0.12), (0, 0, 0.06), "dark", bevel=0.02)
    m.box((sx - 0.12, sy - 0.12, h), (0, 0, 0.10 + h / 2), "body", bevel=0.05)
    m.box((sx - 0.02, sy - 0.02, 0.07), (0, 0, 0.135 + h), "dark", bevel=0.02)
    for side, kind, off in ports:
        port(m, side, kind, off, sx, sy)
    return 0.17 + h


def frame_strips(m, x, y, z, w, h):
    for dz in (-h / 2, h / 2):
        m.box((w + 0.08, 0.035, 0.04), (x, y - 0.015, z + dz), "light")
    for dx in (-w / 2, w / 2):
        m.box((0.04, 0.035, h + 0.08), (x + dx, y - 0.015, z), "light")


def window(m, fill, x=0.0, z=0.50, w=0.42, h=0.26, sy=1):
    y = -(sy / 2 - 0.06)
    frame_strips(m, x, y, z, w, h)
    m.box((w, 0.012, h), (x, y - 0.004, z), fill)
    return y - 0.012


def vent(m, x=0.0, z=0.50, w=0.42, h=0.26, sy=1, n=4):
    y = window(m, "light", x, z, w, h, sy)
    for i in range(n):
        m.box((w - 0.10, 0.02, 0.024), (x, y, z - h / 2 + (i + 0.75) * h / (n + 0.5)), "dark")


def gauge(m, x=0.0, z=0.50, sy=1, r=0.10):
    y = -(sy / 2 - 0.06)
    m.cyl(r, 0.03, (x, y - 0.01, z), "dark", seg=10, axis="Y")
    m.cyl(r * 0.76, 0.035, (x, y - 0.012, z), "white", seg=10, axis="Y")
    m.box((0.012, 0.014, r * 0.7), (x + 0.02, y - 0.032, z + 0.02), "red", rot=(0, rad(30), 0))


def bolts(m, sx=1, sy=1):
    y = -(sy / 2 - 0.06)
    for x in (-(sx / 2 - 0.14), sx / 2 - 0.14):
        for z in (0.20, 0.82):
            m.cyl(0.022, 0.03, (x, y - 0.005, z), "mid", seg=6, axis="Y")


def stack(m, x, y, z0, h=0.86, r=0.085, glow=False):
    m.cyl(r, h, (x, y, z0 + h / 2), "body", seg=8)
    for f in (0.04, 0.55):
        m.cyl(r + 0.023, 0.05, (x, y, z0 + h * f), "mid", seg=8)
    m.cyl(r, 0.10, (x, y, z0 + h + 0.05), "dark", seg=8, r2=r + 0.043)
    m.cyl(r, 0.01, (x, y, z0 + h + 0.102), "glow" if glow else "hole", seg=8)


def tank(m, x, y, z0, r, h, mk="light", seg=10, bands=2, cone=True, band_mk="mid"):
    m.cyl(r, h, (x, y, z0 + h / 2), mk, seg=seg)
    for i in range(bands):
        m.cyl(r + 0.018, 0.05, (x, y, z0 + h * (i + 0.5) / bands), band_mk, seg=seg)
    if cone:
        m.cyl(r, r * 0.45, (x, y, z0 + h + r * 0.225), mk, seg=seg, r2=r * 0.4)
        m.cyl(r * 0.4, 0.05, (x, y, z0 + h + r * 0.45 + 0.02), "dark", seg=seg)
    return z0 + h


def hopper(m, x, y, z0, w=0.74, h=0.36, mk="body", fill="hole"):
    b = 0.58
    m.box((w * b, w * b, h), (x, y, z0 + h / 2), mk, taper=1 / b)
    m.box((w + 0.06, w + 0.06, 0.05), (x, y, z0 + h), "dark", bevel=0.012)
    m.box((w - 0.08, w - 0.08, 0.02), (x, y, z0 + h + 0.02), fill)
    return z0 + h + 0.03


def crate(m, loc, s=0.30, rot=0.0):
    x, y, z = loc
    with m.at((x, y, z), rot):
        m.box((s, s, s), (0, 0, s / 2), "wood")
        for dz in (0.12, 0.88):
            m.box((s + 0.02, s + 0.02, s * 0.14), (0, 0, s * dz), "wood_dark")
        for dx in (-1, 1):
            for dy in (-1, 1):
                m.box((s * 0.14, s * 0.14, s), (dx * s * 0.45, dy * s * 0.45, s / 2), "wood_dark")


def barrel(m, loc, mk="oil", r=0.12, h=0.32, band="mid"):
    x, y, z = loc
    m.cyl(r, h, (x, y, z + h / 2), mk, seg=8)
    for f in (0.2, 0.8):
        m.cyl(r + 0.012, 0.03, (x, y, z + h * f), band, seg=8)


def arrow(m, x, y, z, ang, mk, s=0.15):
    pts = [(-s, -s * 0.35), (0, -s * 0.35), (0, -s * 0.8), (s, 0),
           (0, s * 0.8), (0, s * 0.35), (-s, s * 0.35)]
    with m.at((x, y, z), ang):
        m.prism(pts, 0, 0.025, "Z", mk)


def gantry(m, T, h, span=0.37, post="mid", beam="dark"):
    for x in (-span, span):
        for y in (-span, span):
            m.box((0.07, 0.07, h), (x, y, T + h / 2), post)
    for s in (-1, 1):
        m.box((span * 2 + 0.12, 0.09, 0.09), (0, s * span, T + h), beam, bevel=0.015)
        m.box((0.09, span * 2 + 0.12, 0.09), (s * span, 0, T + h), beam, bevel=0.015)
    return T + h


# ============================ BELTS ============================
def belt_straight(m):
    m.box((1.0, 0.80, 0.14), (0, 0, 0.07), "dark")
    m.prism(RAIL, -0.5, 0.5, "X", "body")
    m.prism([(-y, z) for y, z in RAIL], -0.5, 0.5, "X", "body")
    for s in (-1, 1):
        m.box((0.62, 0.012, 0.045), (0, s * 0.482, 0.20), "mid")
    m.box((1.0, 0.68, 0.06), (0, 0, 0.27), "belt")
    for cx in (-0.33, 0.0, 0.33):
        chev(m, cx, 0)


def belt_corner(m):
    """Right turn: enters from W travelling +X, leaves to S."""
    m.box((0.98, 0.98, 0.14), (0, 0, 0.07), "dark")
    m.box((0.84, 0.68, 0.06), (-0.08, 0, 0.27), "belt")
    m.box((0.68, 0.18, 0.06), (0, -0.41, 0.27), "belt")
    m.prism(RAIL, -0.5, 0.34, "X", "body")
    m.prism(RAIL, -0.5, 0.34, "Y", "body")
    m.box((0.14, 0.14, 0.26), (0.41, 0.41, 0.23), "body", bevel=0.02)
    m.box((0.16, 0.16, 0.26), (-0.42, -0.42, 0.23), "body", bevel=0.02)
    m.box((0.5, 0.012, 0.045), (-0.05, 0.482, 0.20), "mid")
    m.box((0.012, 0.5, 0.045), (0.482, -0.05, 0.20), "mid")
    chev(m, -0.30, 0.0, 0)
    chev(m, 0.02, -0.02, rad(-45))
    chev(m, 0.0, -0.32, rad(-90))


def belt_ramp(m):
    """Two blocks long, rises one block. Enters low at W, leaves high at E."""
    a = math.atan2(1, 2)
    m.prism([(-1, 0.10), (1, 1.10), (1, 1.24), (-1, 0.24)], -0.40, 0.40, "Y", "dark")
    m.prism([(-1, 0.24), (1, 1.24), (1, 1.30), (-1, 0.30)], -0.34, 0.34, "Y", "belt")
    for lo, hi in ((0.34, 0.48), (-0.48, -0.34)):
        m.prism([(-1, 0.10), (1, 1.10), (1, 1.36), (-1, 0.36)], lo, hi, "Y", "body")
    for i in range(6):
        x = -0.83 + i * 0.33
        m.box((0.035, 0.58, 0.012), (x, 0, 0.30 + (x + 1) / 2 + 0.004), "beltmark", rot=(0, -a, 0))
    for x in (0.15, 0.85):
        hgt = 0.10 + (x + 1) / 2
        for s in (-1, 1):
            m.box((0.08, 0.08, hgt), (x, s * 0.36, hgt / 2), "mid")
            m.box((0.16, 0.16, 0.04), (x, s * 0.36, 0.02), "dark")


# ============================ MACHINE TOPS ============================
SPECS = []


def machine(key, ko, fam, recipe, ports=(), size=(1, 1), ortho=4.7, tz=0.75,
            ins=(), outs=(), chassis_on=True, show=True, note=""):
    def deco(fn):
        SPECS.append(dict(key=key, ko=ko, fam=fam, recipe=recipe, ports=ports, size=size,
                          ortho=ortho, tz=tz, ins=ins, outs=outs, fn=fn,
                          chassis=chassis_on, show=show, note=note))
        return fn
    return deco


W_IN, E_OUT, S_IN, S_OUT, N_IN = ("W", "in", 0), ("E", "out", 0), ("S", "in", 0), ("S", "out", 0), ("N", "in", 0)

# ---- 운반 ----
machine("belt", "직선 벨트", "운반", "아이템을 한 방향으로 옮김", chassis_on=False,
        ortho=3.0, tz=0.2)(lambda m, T: belt_straight(m))
machine("belt_corner", "코너 벨트", "운반", "진행 방향을 90도 꺾음 (좌·우 대칭형)", chassis_on=False,
        ortho=3.0, tz=0.2)(lambda m, T: belt_corner(m))
machine("belt_ramp", "경사 벨트", "운반", "두 칸에 걸쳐 한 칸 높이를 올림", chassis_on=False,
        size=(2, 1), ortho=4.2, tz=0.6)(lambda m, T: belt_ramp(m))


@machine("splitter", "분배기", "운반", "들어온 아이템을 두 방향으로 번갈아 내보냄",
         ports=(W_IN, E_OUT, S_OUT), ins=("ingot_cu",), outs=("ingot_cu", "ingot_cu"))
def _splitter(m, T):
    m.cyl(0.38, 0.06, (0, 0, T + 0.03), "light", seg=12)
    m.cyl(0.10, 0.12, (0, 0, T + 0.09), "mid", seg=8)
    arrow(m, -0.22, 0, T + 0.06, 0, "accent")
    arrow(m, 0.24, 0, T + 0.06, 0, "out")
    arrow(m, 0, -0.24, T + 0.06, rad(-90), "out")
    stack_lamp(m, 0.36, 0.36, T, "out")


@machine("merger", "합류기", "운반", "두 줄을 한 줄로 합침",
         ports=(W_IN, N_IN, E_OUT), ins=("plate_cu", "coil"), outs=("plate_cu",))
def _merger(m, T):
    m.box((0.76, 0.76, 0.06), (0, 0, T + 0.03), "light", bevel=0.015)
    m.cyl(0.10, 0.12, (0, 0, T + 0.09), "mid", seg=8)
    arrow(m, -0.22, 0, T + 0.06, 0, "accent")
    arrow(m, 0, 0.22, T + 0.06, rad(-90), "accent")
    arrow(m, 0.24, 0, T + 0.06, 0, "out")
    vent(m)
    bolts(m)


def stack_lamp(m, x, y, T, mk):
    m.cyl(0.035, 0.16, (x, y, T + 0.08), "mid", seg=6)
    m.cyl(0.05, 0.07, (x, y, T + 0.19), mk, seg=6)


@machine("sorter", "분류기", "운반", "지정한 아이템만 옆으로 빼내고 나머지는 통과",
         ports=(W_IN, E_OUT, S_OUT), ins=("ore_cu",), outs=("stone", "ore_cu"))
def _sorter(m, T):
    for y in (-0.38, 0.38):
        m.box((0.07, 0.07, 0.46), (-0.05, y, T + 0.23), "mid")
    m.box((0.10, 0.90, 0.09), (-0.05, 0, T + 0.48), "dark", bevel=0.015)
    m.box((0.22, 0.22, 0.15), (-0.05, 0, T + 0.37), "body", bevel=0.03)
    m.cyl(0.07, 0.04, (-0.05, 0, T + 0.28), "dark", seg=8)
    m.cyl(0.05, 0.05, (-0.05, 0, T + 0.275), "water_light", seg=8)
    m.box((0.26, 0.26, 0.04), (0.28, 0.26, T + 0.02), "light", bevel=0.01)
    m.ico(0.08, (0.28, 0.26, T + 0.10), "copper", jitter=0.15)
    stack_lamp(m, 0.36, -0.36, T, "out")


@machine("storage", "보관함", "운반", "아이템을 쌓아 두었다가 순서대로 내보내는 완충 창고",
         ports=(W_IN, E_OUT), ins=("plate_cu",), outs=("plate_cu",))
def _storage(m, T):
    m.box((0.84, 0.84, 0.66), (0, 0, T + 0.33), "body", bevel=0.03)
    for x in (-0.40, 0.40):
        for y in (-0.40, 0.40):
            m.box((0.10, 0.10, 0.70), (x, y, T + 0.35), "dark")
    m.box((0.92, 0.92, 0.07), (0, 0, T + 0.70), "dark", bevel=0.02)
    for x in (-0.20, -0.07, 0.06):
        m.box((0.04, 0.02, 0.54), (x, -0.425, T + 0.33), "mid")
    for y in (-0.15, 0.0, 0.15):
        m.box((0.02, 0.04, 0.54), (0.425, y, T + 0.33), "mid")
    m.box((0.12, 0.02, 0.46), (0.24, -0.425, T + 0.33), "hole")
    for i in range(3):
        m.box((0.08, 0.025, 0.10), (0.24, -0.428, T + 0.17 + i * 0.13), "out")
    m.box((0.30, 0.30, 0.05), (0, 0, T + 0.76), "light", bevel=0.01)
    window(m, "hole")
    for i, hh in enumerate((0.08, 0.14, 0.20)):
        m.box((0.07, 0.02, hh), (-0.11 + i * 0.11, -0.452, 0.39 + hh / 2), "out")
    bolts(m)


# ---- 공급 ----
def extractor_top(m, T, core):
    """Socket and claws on the deck. With a vein core fitted, the crystal floats in the claws."""
    y = window(m, core or "hole")
    for x in (-0.10, 0.0, 0.10):
        m.box((0.03, 0.02, 0.26), (x, y, 0.50), "dark")
    bolts(m)
    m.cyl(0.38, 0.06, (0, 0, T + 0.03), "light", seg=8)
    m.cyl(0.23, 0.05, (0, 0, T + 0.075), "dark", seg=8)
    m.cyl(0.16, 0.012, (0, 0, T + 0.102), core or "hole", seg=8)
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        with m.at((math.cos(a) * 0.31, math.sin(a) * 0.31, T + 0.06), a):
            m.box((0.10, 0.11, 0.34), (0, 0, 0.17), "body", bevel=0.02)
            m.box((0.08, 0.08, 0.28), (-0.08, 0, 0.455), "light", rot=(0, rad(-35), 0))
            m.cyl(0.04, 0.13, (0, 0, 0.34), "dark", seg=6, axis="Y")
    if core:
        crystal(m, (0, 0, T + 0.64), 0.17, core)
        for k, (r, dz, s_) in enumerate(((0.33, 0.20, 0.05), (0.30, -0.02, 0.04), (0.34, 0.10, 0.035))):
            a = 0.6 + k * 2.2
            crystal(m, (math.cos(a) * r, math.sin(a) * r, T + 0.64 + dz), s_, core)


def crystal(m, loc, r, mk):
    x, y, z = loc
    with muted(m):
        m.cyl(r, r * 1.8, (x, y, z + r * 0.9), mk, seg=6, r2=0.004)
        m.cyl(0.004, r * 1.1, (x, y, z - r * 0.55), mk, seg=6, r2=r)
    m._log("b", (r * 1.5, r * 1.5, r * 1.5),
           Matrix.Translation((x, y, z + r * 0.4)) @ Euler((rad(45), rad(35.26), 0), "XYZ").to_matrix().to_4x4(), mk)


machine("extractor_empty", "빈 추출기", "공급",
        "돌, 철 주괴, 나무, 몬스터 부품으로 조립. 광맥 핵을 꽂기 전에는 아무것도 나오지 않음",
        ports=(E_OUT,), ortho=4.9, tz=0.9)(lambda m, T: extractor_top(m, T, None))
machine("extractor_fe", "추출기 (철 광맥 핵)", "공급", "꽂은 광맥 핵에 맞는 원석을 계속 내보냄",
        ports=(E_OUT,), outs=("ore_fe",), ortho=4.9, tz=0.9)(lambda m, T: extractor_top(m, T, "core_fe"))
machine("extractor_coal", "추출기 (석탄 광맥 핵)", "공급", "핵만 바꿔 꽂으면 다른 원석이 나옴",
        ports=(E_OUT,), outs=("coal",), ortho=4.9, tz=0.9)(lambda m, T: extractor_top(m, T, "core_coal"))
machine("extractor_cu", "추출기 (구리 광맥 핵)", "공급", "", ports=(E_OUT,), show=False)(
    lambda m, T: extractor_top(m, T, "core_cu"))


@machine("logger", "벌목기", "공급", "주변 나무를 베어 통나무를 내보냄",
         ports=(E_OUT,), outs=("log",), ortho=5.0, tz=0.9)
def _logger(m, T):
    vent(m)
    bolts(m)
    m.cyl(0.20, 0.14, (-0.18, 0.12, T + 0.07), "mid", seg=8)
    m.box((0.14, 0.14, 0.78), (-0.18, 0.12, T + 0.39), "body", bevel=0.02)
    m.box((0.11, 1.00, 0.11), (-0.18, -0.30, T + 0.80), "dark", bevel=0.02)
    m.box((0.08, 0.08, 0.30), (-0.18, -0.74, T + 0.64), "mid")
    m.gear(0.28, 0.03, (-0.18, -0.74, T + 0.50), "light", teeth=12, axis="X")
    m.cyl(0.07, 0.07, (-0.18, -0.74, T + 0.50), "red", seg=8, axis="X")
    for (y, z) in ((0.16, 0.09), (0.36, 0.09), (0.26, 0.25)):
        m.cyl(0.095, 0.52, (0.20, y, T + z), "wood_dark", seg=8, axis="X")
        m.cyl(0.075, 0.54, (0.20, y, T + z), "wood_light", seg=8, axis="X")


@machine("pump", "물 펌프", "공급", "물을 끌어올려 물통으로 내보냄",
         ports=(E_OUT,), outs=("barrel_water",), ortho=4.9, tz=0.9)
def _pump(m, T):
    gauge(m, x=-0.18)
    bolts(m)
    top = tank(m, -0.05, 0.10, T, 0.30, 0.52)
    m.cyl(0.308, 0.17, (-0.05, 0.10, T + 0.26), "water", seg=10)
    m.gear(0.09, 0.03, (-0.05, 0.10, top + 0.21), "red", teeth=6, axis="Z")
    m.pipe([(0.20, -0.10, T + 0.34), (0.20, -0.44, T + 0.34), (0.20, -0.56, T + 0.26),
            (0.20, -0.56, 0.02)], 0.07, "light")
    m.cyl(0.10, 0.05, (0.20, -0.56, 0.03), "dark", seg=8)
    m.cyl(0.09, 0.04, (0.20, -0.56, 0.55), "mid", seg=8)


@machine("pumpjack", "펌프잭", "공급", "유전 위에 놓으면 원유통을 내보냄",
         ports=(("E", "out", 0),), size=(2, 1), outs=("barrel_oil",), ortho=6.0, tz=1.0)
def _pumpjack(m, T):
    vent(m, x=-0.45, sy=1)
    gauge(m, x=0.35)
    m.box((0.36, 0.32, 0.95), (-0.15, 0, T + 0.475), "mid", taper=0.35)
    m.box((1.55, 0.13, 0.15), (-0.15, 0, T + 1.0), "body", rot=(0, rad(-12), 0), bevel=0.02)
    m.box((0.24, 0.16, 0.46), (-0.90, 0, T + 0.76), "red", bevel=0.04)
    m.cyl(0.02, 0.50, (-0.93, 0, T + 0.30), "dark", seg=6)
    m.cyl(0.08, 0.16, (-0.93, 0, T + 0.08), "dark", seg=8)
    m.gear(0.27, 0.07, (0.52, 0.0, T + 0.42), "dark", teeth=10, axis="Y")
    m.box((0.14, 0.09, 0.30), (0.52, -0.02, T + 0.56), "red")
    m.box((0.06, 0.06, 0.62), (0.56, 0.0, T + 0.86), "mid", rot=(0, rad(8), 0))
    m.box((0.34, 0.44, 0.28), (0.78, 0.0, T + 0.14), "body", bevel=0.04)
    barrel(m, (0.20, -0.33, T), "oil", band="red")


@machine("harvester", "수확기", "공급", "앞쪽 밭의 다 자란 작물을 거둬들임",
         ports=(E_OUT,), outs=("wheat",), ortho=4.9, tz=0.8)
def _harvester(m, T):
    hopper(m, 0, 0.05, T, w=0.72, h=0.34, fill="wheat_head")
    for (x, y) in ((-0.15, 0.1), (0.12, -0.05), (0.05, 0.2)):
        m.box((0.10, 0.10, 0.10), (x, y, T + 0.40), "wheat", taper=0.4, rot=rng.uniform(0, 1.5))
    for x in (-0.42, 0.42):
        m.box((0.05, 0.24, 0.06), (x, -0.56, 0.44), "dark")
    m.cyl(0.04, 0.86, (0, -0.66, 0.44), "mid", seg=6, axis="X")
    for k in range(4):
        m.box((0.80, 0.02, 0.32), (0, -0.66, 0.44), "wood", rot=(rad(k * 45), 0, 0))
    bolts(m)


# ---- 변환 ----
@machine("crusher", "분쇄기", "변환", "광석 → 분쇄 광석(수량 2배), 돌 → 모래",
         ports=(W_IN, E_OUT), ins=("ore_cu",), outs=("crushed",))
def _crusher(m, T):
    top = hopper(m, 0, 0.04, T, w=0.80, h=0.38)
    for y in (-0.07, 0.15):
        m.gear(0.12, 0.52, (0, y, top - 0.02), "mid", teeth=8, axis="X")
    m.gear(0.23, 0.05, (-0.12, -0.47, 0.52), "mid", teeth=10, axis="Y")
    m.cyl(0.07, 0.07, (-0.12, -0.475, 0.52), "red", seg=8, axis="Y")
    m.gear(0.10, 0.05, (0.24, -0.47, 0.40), "dark", teeth=6, axis="Y")
    bolts(m)


@machine("washer", "세척기", "변환", "분쇄 광석 → 정제 광석 (제련 수율이 오름)",
         ports=(W_IN, E_OUT), ins=("crushed",), outs=("clean",))
def _washer(m, T):
    y = window(m, "water")
    for (x, z) in ((-0.10, 0.46), (0.08, 0.55), (0.14, 0.43)):
        m.box((0.05, 0.02, 0.05), (x, y, z), "water_light")
    bolts(m)
    m.box((0.66, 0.28, 0.07), (0, -0.28, T + 0.035), "dark", bevel=0.015)
    m.box((0.58, 0.20, 0.02), (0, -0.28, T + 0.075), "water_light")
    for x in (-0.20, 0.20):
        top = tank(m, x, 0.20, T, 0.17, 0.46, cone=False)
        m.cyl(0.15, 0.04, (x, 0.20, top + 0.02), "water", seg=10)
        m.pipe([(x, 0.20, top), (x, 0.20, top + 0.14), (x, 0.12, top + 0.22),
                (x, -0.20, top + 0.22), (x, -0.28, top + 0.14), (x, -0.28, T + 0.07)],
               0.045, "water", seg=6)


@machine("smelter", "제련로", "변환", "광석 → 주괴. 석탄이나 숯 같은 연료를 함께 넣어야 함",
         ports=(W_IN, E_OUT), ins=("ore_cu",), outs=("ingot_cu",), ortho=4.9, tz=0.95)
def _smelter(m, T):
    y = window(m, "glow")
    for x in (-0.12, -0.04, 0.04, 0.12):
        m.box((0.03, 0.02, 0.26), (x, y, 0.50), "dark")
    bolts(m)
    hx, hy = -0.06, 0.10
    m.box((0.68, 0.68, 0.05), (hx, hy, T + 0.025), "light", bevel=0.012)
    m.box((0.62, 0.62, 0.42), (hx, hy, T + 0.21), "body", bevel=0.05, taper=0.76)
    gz = T + 0.42
    m.box((0.56, 0.56, 0.06), (hx, hy, gz + 0.02), "dark", bevel=0.015)
    m.box((0.44, 0.44, 0.02), (hx, hy, gz + 0.055), "mid")
    for i in range(4):
        yy = hy - 0.135 + i * 0.09
        m.box((0.42, 0.045, 0.03), (hx, yy, gz + 0.075), "light")
        if i < 3:
            m.box((0.36, 0.02, 0.02), (hx, yy + 0.045, gz + 0.067), "glow")
    stack(m, 0.31, -0.31, T)
    m.pipe([(-0.24, -0.34, T), (-0.24, -0.34, T + 0.16), (-0.24, -0.29, T + 0.21),
            (-0.24, -0.10, T + 0.21)], 0.06, "light")
    m.cyl(0.09, 0.035, (-0.24, -0.34, T + 0.017), "mid", seg=8)
    for x in (-0.04, 0.09):
        m.cyl(0.05, 0.05, (x, -0.37, T + 0.025), "light", seg=6)
        m.cyl(0.03, 0.05, (x, -0.37, T + 0.07), "mid", seg=6)


@machine("kiln", "가마", "변환", "모래 → 유리, 통나무 → 숯",
         ports=(W_IN, E_OUT), ins=("sand",), outs=("glass",), ortho=4.8, tz=0.85)
def _kiln(m, T):
    y = window(m, "glow", w=0.30, h=0.24)
    m.box((0.30, 0.02, 0.05), (0, y, 0.40), "brick_dark")
    bolts(m)
    m.cyl(0.43, 0.44, (0, 0.03, T + 0.22), "brick", seg=8, r2=0.33)
    for f, r in ((0.12, 0.41), (0.30, 0.365)):
        m.cyl(r, 0.025, (0, 0.03, T + f), "mortar", seg=8)
    m.cyl(0.33, 0.22, (0, 0.03, T + 0.55), "brick_dark", seg=8, r2=0.17)
    m.cyl(0.19, 0.07, (0, 0.03, T + 0.69), "dark", seg=8)
    m.cyl(0.12, 0.012, (0, 0.03, T + 0.728), "glow", seg=8)
    m.box((0.22, 0.03, 0.20), (0, -0.375, T + 0.14), "hole")
    m.box((0.16, 0.035, 0.13), (0, -0.38, T + 0.12), "glow")
    m.box((0.30, 0.05, 0.05), (0, -0.375, T + 0.26), "mortar")


@machine("sawmill", "제재기", "변환", "통나무 → 판자",
         ports=(W_IN, E_OUT), ins=("log",), outs=("plank",))
def _sawmill(m, T):
    vent(m)
    bolts(m)
    m.box((0.80, 0.05, 0.02), (0, -0.08, T + 0.01), "hole")
    m.gear(0.36, 0.03, (0.0, -0.08, T + 0.10), "light", teeth=12, axis="Y")
    m.cyl(0.08, 0.09, (0.0, -0.08, T + 0.10), "red", seg=8, axis="Y")
    m.box((0.10, 0.14, 0.52), (-0.40, -0.08, T + 0.26), "dark")
    m.box((0.46, 0.14, 0.07), (-0.20, -0.08, T + 0.52), "dark", bevel=0.015)
    for i in range(3):
        m.box((0.62, 0.17, 0.05), (0.05, 0.28, T + 0.03 + i * 0.055),
              "wood" if i % 2 == 0 else "wood_light")
    m.cyl(0.085, 0.50, (0.05, -0.34, T + 0.085), "wood_dark", seg=8, axis="X")
    m.cyl(0.065, 0.52, (0.05, -0.34, T + 0.085), "wood_light", seg=8, axis="X")


@machine("stonecutter", "석재 절단기", "변환", "돌 → 석재 블록",
         ports=(W_IN, E_OUT), ins=("stone",), outs=("stone_block",), ortho=4.8, tz=0.85)
def _stonecutter(m, T):
    vent(m)
    bolts(m)
    for y in (-0.40, 0.40):
        m.box((0.09, 0.09, 0.62), (0, y, T + 0.31), "mid")
    m.box((0.12, 0.94, 0.10), (0, 0, T + 0.64), "dark", bevel=0.02)
    m.box((0.22, 0.24, 0.16), (0, 0.05, T + 0.54), "body", bevel=0.03)
    m.cyl(0.05, 0.05, (0, 0.05, T + 0.72), "red", seg=6)
    m.box((0.56, 0.016, 0.26), (0, 0.05, T + 0.34), "light")
    m.box((0.36, 0.20, 0.24), (0, 0.17, T + 0.12), "stone", bevel=0.02)
    m.box((0.36, 0.13, 0.24), (0, -0.04, T + 0.12), "stone", bevel=0.02)
    m.box((0.36, 0.07, 0.24), (0.02, -0.26, T + 0.12), "stone_dark", bevel=0.015, rot=rad(8))


@machine("press", "압연 프레스", "변환", "주괴 → 판재",
         ports=(W_IN, E_OUT), ins=("ingot_cu",), outs=("plate_cu",), ortho=5.0, tz=1.0)
def _press(m, T):
    gauge(m, x=-0.17)
    m.box((0.14, 0.02, 0.20), (0.18, -0.452, 0.50), "hole")
    for i, mk in enumerate(("out", "accent", "red")):
        m.cyl(0.028, 0.03, (0.18, -0.46, 0.43 + i * 0.07), mk, seg=6, axis="Y")
    bolts(m)
    m.box((0.76, 0.76, 0.08), (0, 0, T + 0.04), "mid", bevel=0.015)
    for x in (-0.29, 0.29):
        for y in (-0.29, 0.29):
            m.cyl(0.05, 0.80, (x, y, T + 0.40), "light", seg=8)
    m.box((0.78, 0.78, 0.18), (0, 0, T + 0.86), "body", bevel=0.04)
    m.cyl(0.17, 0.24, (0, 0, T + 1.07), "mid", seg=10)
    m.cyl(0.12, 0.05, (0, 0, T + 1.21), "dark", seg=10)
    m.cyl(0.09, 0.34, (0, 0, T + 0.62), "light", seg=8)
    m.box((0.50, 0.50, 0.09), (0, 0, T + 0.43), "accent", bevel=0.015)
    for x in (-0.15, 0.0, 0.15):
        m.box((0.07, 0.51, 0.092), (x, 0, T + 0.43), "dark")
    m.box((0.34, 0.34, 0.03), (0, 0, T + 0.095), "copper")


@machine("wiredraw", "신선기", "변환", "구리 주괴 → 구리선 묶음",
         ports=(W_IN, E_OUT), ins=("ingot_cu",), outs=("coil",))
def _wiredraw(m, T):
    vent(m)
    bolts(m)
    sx_, sz = 0.14, T + 0.40
    m.cyl(0.25, 0.34, (sx_, 0, sz), "copper", seg=10, axis="Y")
    for y in (-0.19, 0.19):
        m.cyl(0.33, 0.04, (sx_, y, sz), "mid", seg=10, axis="Y")
        m.box((0.12, 0.06, 0.40), (sx_, y * 1.45, T + 0.20), "dark", taper=0.6)
    m.cyl(0.05, 0.62, (sx_, 0, sz), "dark", seg=6, axis="Y")
    m.box((0.22, 0.34, 0.26), (-0.30, 0, T + 0.13), "body", bevel=0.03)
    m.cyl(0.06, 0.10, (-0.18, 0, T + 0.18), "dark", seg=6, axis="X", r2=0.025)
    m.box((0.22, 0.02, 0.02), (-0.06, 0, T + 0.20), "copper", rot=(0, rad(-25), 0))


@machine("refinery", "정유탑", "변환", "원유 → 연료통 + 플라스틱 (출구 둘)",
         ports=(W_IN, E_OUT, S_OUT), ins=("barrel_oil",), outs=("barrel_fuel", "plastic"),
         ortho=7.4, tz=1.75)
def _refinery(m, T):
    cx, cy = -0.10, 0.10
    top = tank(m, cx, cy, T, 0.27, 1.90, mk="cream", bands=0)
    for f in (0.12, 0.38, 0.64, 0.90):
        m.cyl(0.292, 0.05, (cx, cy, T + 1.90 * f), "mid", seg=10)
    m.cyl(0.40, 0.03, (cx, cy, T + 1.22), "dark", seg=10)
    m.ring(0.40, 0.018, T + 1.38, "mid", cx, cy)
    for k in range(5):
        a = k * 2 * math.pi / 5
        m.box((0.02, 0.02, 0.16), (cx + 0.40 * math.cos(a), cy + 0.40 * math.sin(a), T + 1.30), "mid")
    for x in (-0.07, 0.05):
        m.box((0.02, 0.02, 1.20), (cx + x, cy - 0.285, T + 0.60), "dark")
    for i in range(8):
        m.box((0.14, 0.02, 0.02), (cx - 0.01, cy - 0.285, T + 0.10 + i * 0.15), "dark")
    m.pipe([(cx + 0.20, cy, top - 0.15), (0.32, cy, top - 0.15), (0.36, cy, top - 0.22),
            (0.36, cy, T)], 0.05, "mid", seg=6)
    m.cyl(0.035, 2.50, (0.34, 0.38, T + 1.25), "dark", seg=6)
    m.ico(0.075, (0.34, 0.38, T + 2.55), "glow", squash=1.3)
    barrel(m, (-0.32, -0.33, T), "red", band="dark")
    barrel(m, (0.10, -0.36, T), "oil", band="red")


@machine("mill", "제분기", "변환", "밀 → 밀가루",
         ports=(W_IN, E_OUT), ins=("wheat",), outs=("flour",), ortho=5.4, tz=1.1)
def _mill(m, T):
    vent(m)
    bolts(m)
    m.box((0.66, 0.66, 0.90), (0, 0.06, T + 0.45), "wood", taper=0.70)
    for z in (0.22, 0.55):
        k = 1 - 0.30 * z / 0.90
        m.box((0.67 * k, 0.67 * k, 0.03), (0, 0.06, T + z), "wood_dark")
    m.box((0.60, 0.60, 0.26), (0, 0.06, T + 1.03), "wood_dark", taper=0.08)
    m.box((0.14, 0.02, 0.20), (0, -0.20, T + 0.20), "hole")
    hub = (0, -0.34, T + 0.66)
    m.cyl(0.03, 0.20, (0, -0.27, T + 0.66), "dark", seg=6, axis="Y")
    m.cyl(0.07, 0.07, hub, "dark", seg=8, axis="Y")
    with m.at(hub):
        for k in range(4):
            a = rad(20 + k * 90)
            m.box((0.03, 0.03, 0.64), (math.sin(a) * 0.36, 0, math.cos(a) * 0.36), "wood_dark",
                  rot=(0, a, 0))
            m.box((0.17, 0.015, 0.44), (math.sin(a) * 0.44 + math.cos(a) * 0.07, 0,
                                         math.cos(a) * 0.44 - math.sin(a) * 0.07), "wood_light",
                  rot=(0, a, 0))


# ---- 조합 ----
@machine("blast", "고로", "조합", "철 주괴 + 석탄 → 강철 주괴",
         ports=(("W", "in", -0.5), ("S", "in", -0.5), ("E", "out", -0.5)), size=(2, 2),
         ins=("ingot_fe", "coal"), outs=("ingot_steel",), ortho=8.0, tz=1.5)
def _blast(m, T):
    cx, cy = -0.05, 0.12
    m.cyl(0.74, 0.80, (cx, cy, T + 0.40), "body", seg=10, r2=0.64)
    for z, r in ((0.10, 0.74), (0.62, 0.675)):
        m.cyl(r, 0.07, (cx, cy, T + z), "dark", seg=10)
    for k in range(10):
        a = k * 2 * math.pi / 10 + 0.31
        m.box((0.035, 0.13, 0.08), (cx + 0.712 * math.cos(a), cy + 0.712 * math.sin(a), T + 0.30),
              "glow", rot=a)
    m.ring(0.86, 0.065, T + 0.46, "light", cx, cy)
    for k in range(5):
        a = k * 2 * math.pi / 5 + 0.3
        m.box((0.05, 0.05, 0.46), (cx + 0.86 * math.cos(a), cy + 0.86 * math.sin(a), T + 0.23), "mid")
    m.cyl(0.64, 0.42, (cx, cy, T + 1.01), "mid", seg=10, r2=0.36)
    m.cyl(0.36, 0.34, (cx, cy, T + 1.39), "body", seg=10)
    m.cyl(0.43, 0.08, (cx, cy, T + 1.60), "dark", seg=10)
    m.cyl(0.26, 0.012, (cx, cy, T + 1.645), "glow", seg=10)
    dz = tank(m, 0.68, 0.70, T, 0.20, 0.70, mk="light")
    m.pipe([(cx + 0.30, cy + 0.15, T + 1.45), (cx + 0.52, cy + 0.36, T + 1.62),
            (0.68, 0.70, T + 1.45), (0.68, 0.70, dz + 0.14)], 0.075, "light")
    stack(m, -0.74, 0.76, T, h=2.1, r=0.11)
    m.box((0.22, 0.46, 0.09), (0.36, -0.74, T + 0.045), "dark", bevel=0.015)
    m.box((0.12, 0.44, 0.02), (0.36, -0.74, T + 0.095), "glow")
    for (x, y) in ((-0.74, -0.30), (-0.74, -0.74)):
        m.box((0.30, 0.30, 0.22), (x, y, T + 0.11), "coal", bevel=0.05)
    vent(m, x=0.5, sy=2)
    gauge(m, x=0.05, sy=2)


@machine("assembler", "조립기", "조합", "판재 + 구리선 → 기계 부품",
         ports=(W_IN, S_IN, E_OUT), ins=("plate_cu", "coil"), outs=("gear",), ortho=4.9, tz=0.9)
def _assembler(m, T):
    assembler_top(m, T)


def assembler_top(m, T):
    m.cyl(0.27, 0.05, (0.10, -0.06, T + 0.025), "dark", seg=10)
    m.gear(0.15, 0.05, (0.10, -0.06, T + 0.075), "iron", teeth=8, axis="Z")
    bx, by = -0.27, 0.27
    m.cyl(0.15, 0.14, (bx, by, T + 0.07), "mid", seg=8)
    ang = math.atan2(-0.33, 0.37)
    with m.at((bx, by, T + 0.14), ang):
        a1, a2 = rad(25), rad(112)
        e1 = Vector((math.sin(a1) * 0.50, 0, math.cos(a1) * 0.50))
        m.box((0.10, 0.10, 0.50), e1 / 2, "light", rot=(0, a1, 0))
        m.cyl(0.075, 0.14, e1, "dark", seg=8, axis="Y")
        d2 = Vector((math.sin(a2), 0, math.cos(a2)))
        m.box((0.08, 0.08, 0.36), e1 + d2 * 0.18, "light", rot=(0, a2, 0))
        e2 = e1 + d2 * 0.36
        m.cyl(0.06, 0.12, e2, "dark", seg=8, axis="Y")
        for s in (-1, 1):
            m.box((0.03, 0.03, 0.12), e2 + Vector((0.02, s * 0.05, -0.07)), "red")
    stack_lamp(m, 0.38, 0.38, T, "spark")
    m.box((0.22, 0.16, 0.12), (-0.30, -0.30, T + 0.06), "body", bevel=0.02)


@machine("assembler_n", "조립기", "조합", "", ports=(W_IN, N_IN, E_OUT), show=False)
def _assembler_n(m, T):
    assembler_top(m, T)
    vent(m)
    bolts(m)


@machine("circuit", "회로 제작기", "조합", "구리선 + 플라스틱 → 회로 기판",
         ports=(W_IN, S_IN, E_OUT), ins=("coil", "plastic"), outs=("board",))
def _circuit(m, T):
    m.box((0.84, 0.84, 0.28), (0, 0, T + 0.14), "light", bevel=0.04)
    pz = T + 0.29
    m.box((0.52, 0.42, 0.02), (-0.04, 0.02, pz), "pcb")
    for (x, y, w, h) in ((-0.16, 0.10, 0.20, 0.02), (-0.06, -0.06, 0.02, 0.18),
                         (0.06, 0.12, 0.16, 0.02), (0.10, -0.10, 0.12, 0.02)):
        m.box((w, h, 0.012), (x, y, pz + 0.012), "gold")
    for (x, y) in ((-0.18, -0.08), (0.12, 0.02)):
        m.box((0.10, 0.10, 0.03), (x, y, pz + 0.02), "hole")
    for x in (-0.38, 0.38):
        m.box((0.06, 0.06, 0.28), (x, 0.02, T + 0.42), "mid")
    m.box((0.84, 0.07, 0.07), (0, 0.02, T + 0.58), "dark", bevel=0.012)
    m.box((0.14, 0.14, 0.14), (0.08, 0.02, T + 0.50), "body", bevel=0.02)
    m.cyl(0.025, 0.10, (0.08, 0.02, T + 0.40), "water_light", seg=6, r2=0.04)
    stack_lamp(m, -0.36, 0.36, T + 0.28, "out")


@machine("mixer", "혼합기", "조합", "모래 + 물통 → 콘크리트",
         ports=(W_IN, S_IN, E_OUT), ins=("sand", "barrel_water"), outs=("concrete",),
         ortho=4.9, tz=0.9)
def _mixer(m, T):
    m.cyl(0.39, 0.46, (0, 0.02, T + 0.23), "light", seg=12)
    m.cyl(0.405, 0.05, (0, 0.02, T + 0.12), "mid", seg=12)
    m.cyl(0.42, 0.05, (0, 0.02, T + 0.46), "dark", seg=12)
    m.cyl(0.35, 0.012, (0, 0.02, T + 0.49), "slurry", seg=12)
    for x in (-0.44, 0.44):
        m.box((0.08, 0.12, 0.66), (x, 0.02, T + 0.33), "mid")
    m.box((0.96, 0.12, 0.09), (0, 0.02, T + 0.68), "dark", bevel=0.02)
    m.box((0.24, 0.24, 0.22), (0, 0.02, T + 0.83), "body", bevel=0.04)
    m.cyl(0.07, 0.05, (0, 0.02, T + 0.96), "red", seg=8)
    m.cyl(0.03, 0.20, (0, 0.02, T + 0.58), "mid", seg=6)
    for k in range(2):
        m.box((0.36, 0.05, 0.02), (0, 0.02, T + 0.50), "mid", rot=rad(35 + k * 90))
    m.pipe([(0.30, 0.44, T), (0.30, 0.44, T + 0.60), (0.30, 0.36, T + 0.66),
            (0.22, 0.22, T + 0.60)], 0.045, "water", seg=6)


@machine("oven", "제빵 오븐", "조합", "밀가루 + 물통 → 빵",
         ports=(W_IN, S_IN, E_OUT), ins=("flour", "barrel_water"), outs=("bread",))
def _oven(m, T):
    m.box((0.80, 0.74, 0.44), (-0.02, 0.06, T + 0.22), "cream", bevel=0.13)
    m.box((0.84, 0.78, 0.05), (-0.02, 0.06, T + 0.025), "mid", bevel=0.012)
    m.box((0.40, 0.03, 0.22), (-0.02, -0.30, T + 0.19), "hole")
    m.box((0.32, 0.035, 0.15), (-0.02, -0.305, T + 0.17), "glow")
    m.box((0.48, 0.05, 0.05), (-0.02, -0.31, T + 0.32), "brick")
    for x in (-0.11, 0.05):
        m.box((0.11, 0.05, 0.07), (x, -0.31, T + 0.13), "bread", bevel=0.02)
    m.cyl(0.07, 0.34, (0.22, 0.26, T + 0.58), "body", seg=8)
    m.cyl(0.13, 0.08, (0.22, 0.26, T + 0.80), "dark", seg=8, r2=0.02)
    m.box((0.30, 0.20, 0.03), (0.50 - 0.22, -0.36, T + 0.015), "light")


@machine("manufacturer", "제조 공장", "조합", "기계 부품 + 회로 기판 + 강철 → 모터",
         ports=(("W", "in", 0.5), ("W", "in", -0.5), ("S", "in", -0.5), ("E", "out", -0.5)),
         size=(2, 2), ins=("gear", "board", "ingot_steel"), outs=("motor",), ortho=7.6, tz=1.1)
def _manufacturer(m, T):
    m.box((1.82, 1.82, 0.50), (0, 0, T + 0.25), "body", bevel=0.04)
    rz = T + 0.50
    for x0 in (-0.90, -0.30, 0.30):
        m.prism([(x0, rz), (x0 + 0.60, rz), (x0 + 0.60, rz + 0.36)], -0.88, 0.88, "Y", "dark")
        m.box((0.014, 1.56, 0.22), (x0 + 0.605, 0, rz + 0.19), "water_light")
        for y in (-0.52, 0.0, 0.52):
            m.box((0.02, 0.04, 0.24), (x0 + 0.607, y, rz + 0.19), "mid")
    stack(m, -0.62, 0.70, rz, h=0.95, r=0.10)
    stack(m, -0.20, 0.70, rz, h=0.70, r=0.08)
    for x in (0.10, 0.52):
        m.box((0.30, 0.02, 0.22), (x, -0.915, T + 0.27), "hole")
        frame_strips(m, x, -0.905, T + 0.27, 0.30, 0.22)
        m.box((0.02, 0.025, 0.22), (x, -0.918, T + 0.27), "light")
    m.gear(0.16, 0.04, (0.86, -0.925, T + 0.27), "accent", teeth=8, axis="Y")
    vent(m, x=0.5, sy=2)
    gauge(m, x=0.05, sy=2)
    m.box((0.02, 0.60, 0.24), (0.915, 0.35, T + 0.27), "hole")
    for y in (0.12, 0.35, 0.58):
        m.box((0.03, 0.03, 0.26), (0.92, y, T + 0.27), "light")


# ---- 포장·판매·동력 ----
@machine("packer", "포장기", "포장·판매", "같은 아이템 8개 → 상자 1개 (물체 수를 줄임)",
         ports=(W_IN, E_OUT), ins=("plate_cu",), outs=("crate",), ortho=5.0, tz=0.95)
def _packer(m, T):
    vent(m)
    bolts(m)
    fz = gantry(m, T, 0.80)
    crate(m, (0, 0, T), s=0.44)
    m.box((0.52, 0.52, 0.05), (0, 0, T + 0.58), "light", bevel=0.012)
    m.cyl(0.05, 0.22, (0, 0, T + 0.70), "mid", seg=8)
    m.box((0.30, 0.30, 0.12), (0, 0, fz + 0.01), "body", bevel=0.03)
    m.cyl(0.11, 0.06, (0.0, -0.37, T + 0.42), "accent", seg=10, axis="Y")
    m.cyl(0.05, 0.07, (0.0, -0.37, T + 0.42), "dark", seg=8, axis="Y")


@machine("seller", "판매기", "포장·판매", "", ports=(W_IN,), show=False)
def _seller(m, T):
    y = window(m, "hole")
    for i, h in enumerate((0.07, 0.13, 0.19)):
        m.box((0.07, 0.02, h), (-0.11 + i * 0.11, y, 0.39 + h / 2), "gold")
    bolts(m)
    ry = 0.08
    m.box((0.68, 0.58, 0.05), (0, ry, T + 0.025), "light", bevel=0.012)
    m.box((0.62, 0.52, 0.34), (0, ry, T + 0.17), "body", bevel=0.05)
    m.box((0.30, 0.02, 0.045), (0, ry - 0.262, T + 0.22), "hole")
    m.cyl(0.04, 0.26, (0, ry, T + 0.47), "mid", seg=6)
    cz = T + 0.84
    m.cyl(0.27, 0.07, (0, ry, cz), "gold", seg=12, axis="Y")
    m.cyl(0.20, 0.09, (0, ry, cz), "gold_dark", seg=12, axis="Y")
    m.box((0.06, 0.11, 0.22), (0, ry, cz), "gold")
    for x in (-0.07, 0.07):
        m.box((0.03, 0.11, 0.05), (x, ry, cz), "gold")


@machine("generator", "석탄 발전기", "동력", "석탄이나 연료통을 태워 주변 기계에 전력을 공급",
         ports=(W_IN,), ins=("coal",), ortho=4.9, tz=0.9)
def _generator(m, T):
    gauge(m, x=-0.17)
    bolts(m)
    gz = T + 0.34
    m.cyl(0.27, 0.60, (0.0, 0.10, gz), "dark", seg=10, axis="X")
    m.cyl(0.21, 0.66, (0.0, 0.10, gz), "mid", seg=10, axis="X")
    for x in (-0.18, 0.0, 0.18):
        m.cyl(0.285, 0.08, (x, 0.10, gz), "copper", seg=10, axis="X")
    for x in (-0.22, 0.22):
        m.box((0.10, 0.50, 0.14), (x, 0.10, T + 0.07), "mid", bevel=0.02)
    for x in (-0.09, 0.09):
        m.cyl(0.035, 0.14, (x, 0.10, gz + 0.33), "white", seg=6)
        m.cyl(0.02, 0.05, (x, 0.10, gz + 0.42), "copper", seg=6)
    stack(m, -0.34, -0.30, T, h=0.70, r=0.075)
    m.box((0.30, 0.03, 0.36), (0.26, -0.36, T + 0.26), "dark", bevel=0.01)
    bolt = [(0.03, 0.14), (-0.08, -0.01), (-0.01, -0.01), (-0.05, -0.14), (0.08, 0.03), (0.01, 0.03)]
    m.prism([(0.26 + x, T + 0.26 + z) for x, z in bolt], -0.385, -0.37, "Y", "spark")
    m.box((0.04, 0.04, 0.10), (0.26, -0.36, T + 0.05), "mid")


# ============================ PHYSICS DEVICES ============================
@machine("funnel", "깔때기", "물리 장치", "위에서 떨어지는 아이템을 받아 벨트로 내보냄. 높낮이만 맞추면 동력이 필요 없음",
         ports=(E_OUT,), outs=("ore_fe",), ortho=4.9, tz=0.9)
def _funnel(m, T):
    vent(m)
    bolts(m)
    top = hopper(m, 0, 0, T, w=0.90, h=0.52)
    for s in (-1, 1):
        m.box((1.00, 0.06, 0.05), (0, s * 0.47, top), "accent")
        m.box((0.06, 1.00, 0.05), (s * 0.47, 0, top), "accent")


@machine("chute", "낙하 통로", "물리 장치", "높은 곳에서 낮은 곳으로 미끄러뜨림. 동력이 필요 없지만 내려가는 쪽으로만 감",
         chassis_on=False, size=(2, 1), ortho=4.4, tz=0.6)
def _chute(m, T):
    m.prism([(-1, 1.24), (1, 0.24), (1, 0.30), (-1, 1.30)], -0.34, 0.34, "Y", "light")
    for lo, hi in ((0.34, 0.42), (-0.42, -0.34)):
        m.prism([(-1, 1.24), (1, 0.24), (1, 0.48), (-1, 1.48)], lo, hi, "Y", "body")
    for x in (-0.85, -0.15):
        hgt = 1.24 - (x + 1) / 2
        for s in (-1, 1):
            m.box((0.08, 0.08, hgt), (x, s * 0.36, hgt / 2), "mid")
            m.box((0.16, 0.16, 0.04), (x, s * 0.36, 0.02), "dark")
    m.box((0.10, 0.84, 0.20), (0.95, 0, 0.12), "dark")


@machine("blower", "송풍기", "물리 장치", "바람으로 아이템을 밀어냄. 가벼운 것은 멀리, 무거운 것은 조금만 밀림",
         chassis_on=False, ortho=3.6, tz=0.6)
def _blower(m, T):
    m.box((0.96, 0.96, 0.12), (0, 0, 0.06), "dark", bevel=0.02)
    for y in (-0.30, 0.30):
        m.box((0.50, 0.10, 0.30), (0, y, 0.25), "mid")
    cz = 0.74
    m.cyl(0.44, 0.50, (0.05, 0, cz), "body", seg=12, axis="X")
    m.cyl(0.37, 0.52, (0.05, 0, cz), "hole", seg=12, axis="X")
    for k in range(3):
        m.box((0.04, 0.70, 0.13), (0.30, 0, cz), "light", rot=(rad(k * 60), 0, 0))
    m.cyl(0.09, 0.08, (0.32, 0, cz), "red", seg=8, axis="X")
    m.box((0.34, 0.44, 0.44), (-0.33, 0, cz - 0.05), "mid", bevel=0.04)
    arrow(m, 0.36, 0, 0.12, 0, "out", s=0.10)


@machine("lift", "수직 승강기", "물리 장치", "아이템을 두 칸 위로 올림",
         ports=(W_IN,), ins=("ore_fe",), ortho=7.8, tz=1.7)
def _lift(m, T):
    vent(m)
    bolts(m)
    m.box((0.60, 0.60, 1.10), (0, 0, T + 0.55), "mid", bevel=0.03)
    m.box((0.30, 0.02, 0.96), (0, -0.305, T + 0.55), "hole")
    for i in range(4):
        m.box((0.20, 0.07, 0.10), (0, -0.33, T + 0.16 + i * 0.26), "light")
    with m.at((0, 0, 2.0)):
        m.box((0.88, 0.88, 0.80), (0, 0, 0.50), "body", bevel=0.05)
        m.box((0.98, 0.98, 0.07), (0, 0, 0.935), "dark", bevel=0.02)
        port(m, "E", "out")
        m.cyl(0.16, 0.10, (0, 0, 1.02), "red", seg=8)


@machine("launcher", "발사기", "물리 장치", "아이템을 포물선으로 쏘아 보냄. 벨트 없이 먼 곳이나 높은 곳으로 보낼 수 있음",
         ports=(W_IN,), ins=("ingot_cu",), ortho=5.2, tz=1.0)
def _launcher(m, T):
    gauge(m)
    bolts(m)
    m.cyl(0.30, 0.12, (0, 0, T + 0.06), "mid", seg=10)
    a = rad(50)
    d = Vector((math.sin(a), 0, math.cos(a)))
    c = Vector((0.02, 0, T + 0.16))
    m.cyl(0.19, 0.80, c + d * 0.40, "body", seg=10, rot=(0, a, 0))
    m.cyl(0.21, 0.07, c + d * 0.80, "out", seg=10, rot=(0, a, 0))
    m.cyl(0.14, 0.02, c + d * 0.845, "hole", seg=10, rot=(0, a, 0))
    for t in (0.14, 0.26, 0.38):
        m.cyl(0.215, 0.05, c + d * t, "red", seg=10, rot=(0, a, 0))
    for y in (-0.26, 0.26):
        m.box((0.10, 0.07, 0.36), (0.02, y, T + 0.24), "dark", taper=0.6)


@machine("pusher", "밀대", "물리 장치", "신호가 오면 지나가는 아이템을 옆으로 밀어냄",
         ports=(W_IN, E_OUT, S_OUT), ins=("stone",), outs=("stone", "ore_fe"))
def _pusher(m, T):
    m.box((0.36, 0.40, 0.26), (0, 0.24, T + 0.13), "body", bevel=0.03)
    for x in (-0.10, 0.0, 0.10):
        m.box((0.05, 0.41, 0.262), (x, 0.24, T + 0.13), "accent" if x else "dark")
    m.cyl(0.05, 0.36, (0, -0.10, T + 0.13), "light", seg=8, axis="Y")
    m.box((0.46, 0.06, 0.22), (0, -0.30, T + 0.12), "red", bevel=0.015)
    stack_lamp(m, 0.36, 0.36, T, "spark")


# ============================ LOGIC DEVICES ============================
@machine("sensor", "감지기", "판단 장치", "벨트 위를 지나가는 아이템을 보고 신호를 냄. 종류나 개수를 조건으로 걸 수 있음",
         chassis_on=False, ortho=3.6, tz=0.5)
def _sensor(m, T):
    belt_straight(m)
    for s in (-1, 1):
        m.box((0.06, 0.06, 0.86), (0, s * 0.52, 0.43), "mid")
    m.box((0.11, 1.12, 0.09), (0, 0, 0.88), "dark", bevel=0.015)
    m.box((0.24, 0.24, 0.16), (0, 0, 0.77), "body", bevel=0.03)
    m.cyl(0.08, 0.04, (0, 0, 0.68), "dark", seg=8)
    m.cyl(0.055, 0.05, (0, 0, 0.675), "water_light", seg=8)
    stack_lamp(m, 0, 0.52, 0.90, "spark")


@machine("gate", "여닫이 문", "판단 장치", "신호에 따라 벨트를 막거나 엶",
         chassis_on=False, ortho=3.6, tz=0.5)
def _gate(m, T):
    belt_straight(m)
    for s in (-1, 1):
        m.box((0.10, 0.06, 0.80), (0, s * 0.52, 0.40), "mid")
    m.box((0.14, 1.12, 0.10), (0, 0, 0.84), "dark", bevel=0.015)
    m.box((0.05, 0.70, 0.34), (0, 0, 0.60), "red")
    for y in (-0.20, 0.0, 0.20):
        m.box((0.052, 0.07, 0.34), (0, y, 0.60), "light")
    m.cyl(0.07, 0.22, (0, 0, 1.00), "light", seg=8)
    m.cyl(0.09, 0.05, (0, 0, 0.91), "mid", seg=8)


@machine("counter", "계수기", "판단 장치", "지나간 아이템을 세고, 정한 수가 차면 신호를 냄",
         chassis_on=False, ortho=3.6, tz=0.5)
def _counter(m, T):
    belt_straight(m)
    m.box((0.07, 0.07, 0.70), (0.0, -0.53, 0.35), "mid")
    m.box((0.40, 0.10, 0.26), (0.0, -0.53, 0.80), "dark", bevel=0.02)
    m.box((0.32, 0.02, 0.18), (0.0, -0.585, 0.80), "hole")
    for i, x in enumerate((-0.10, 0.0, 0.10)):
        for z in (0.86, 0.80, 0.74):
            m.box((0.06, 0.02, 0.02), (x, -0.598, z), "spark")
        m.box((0.02, 0.02, 0.07), (x + 0.035, -0.598, 0.83), "spark")
        m.box((0.02, 0.02, 0.07), (x - 0.035, -0.598, 0.77 if i % 2 else 0.83), "spark")
    m.cyl(0.06, 0.04, (0, -0.30, 0.36), "red", seg=8, axis="Y")
    m.box((0.04, 0.26, 0.04), (0, -0.42, 0.40), "mid")


@machine("switch", "스위치", "판단 장치", "손으로 켜고 끄는 신호",
         chassis_on=False, ortho=2.6, tz=0.3)
def _switch(m, T):
    m.box((0.50, 0.50, 0.06), (0, 0, 0.03), "dark", bevel=0.015)
    m.box((0.34, 0.28, 0.34), (0, 0, 0.23), "body", bevel=0.04)
    m.box((0.06, 0.20, 0.02), (0, 0, 0.405), "hole")
    m.cyl(0.025, 0.30, (0, 0.05, 0.52), "light", seg=6, rot=(rad(-25), 0, 0))
    m.ico(0.06, (0, 0.115, 0.655), "red")
    m.cyl(0.04, 0.03, (0.11, -0.141, 0.26), "out", seg=6, axis="Y")
    m.cyl(0.04, 0.03, (-0.11, -0.141, 0.26), "dark", seg=6, axis="Y")


@machine("logic", "논리 회로함", "판단 장치", "신호 둘을 받아 조건이 맞으면 신호를 내보냄 (그리고, 또는, 아니면)",
         chassis_on=False, ortho=2.9, tz=0.25)
def _logic(m, T):
    m.box((0.80, 0.60, 0.06), (0, 0, 0.03), "dark", bevel=0.015)
    m.box((0.70, 0.50, 0.30), (0, 0, 0.21), "body", bevel=0.04)
    m.box((0.52, 0.34, 0.02), (0, 0, 0.365), "pcb")
    for (x, y, w, h) in ((-0.12, 0.08, 0.22, 0.02), (-0.12, -0.08, 0.22, 0.02),
                         (0.10, 0.0, 0.20, 0.02), (0.0, 0.0, 0.02, 0.18)):
        m.box((w, h, 0.012), (x, y, 0.378), "gold")
    m.box((0.10, 0.12, 0.04), (0.0, 0.0, 0.39), "hole")
    for y in (-0.12, 0.12):
        m.cyl(0.05, 0.08, (-0.38, y, 0.20), "accent", seg=6, axis="X")
    m.cyl(0.05, 0.08, (0.38, 0, 0.20), "out", seg=6, axis="X")
    for i, mk in enumerate(("glow", "spark", "out")):
        m.cyl(0.025, 0.03, (-0.16 + i * 0.16, -0.255, 0.24), mk, seg=6, axis="Y")


@machine("beacon", "신호등", "판단 장치", "신호를 받으면 켜짐. 공장 상태를 멀리서 확인",
         chassis_on=False, ortho=3.4, tz=0.75)
def _beacon(m, T):
    m.cyl(0.24, 0.08, (0, 0, 0.04), "dark", seg=8)
    m.cyl(0.05, 0.80, (0, 0, 0.48), "mid", seg=8)
    for i, mk in enumerate(("out", "spark", "red")):
        z = 0.95 + i * 0.19
        m.cyl(0.12, 0.15, (0, 0, z), mk, seg=8)
        m.cyl(0.13, 0.03, (0, 0, z - 0.09), "dark", seg=8)
    m.cyl(0.13, 0.06, (0, 0, 1.44), "dark", seg=8, r2=0.05)


@machine("timer", "타이머", "판단 장치", "정해 둔 간격마다 신호를 냄",
         chassis_on=False, ortho=2.8, tz=0.3)
def _timer(m, T):
    m.box((0.56, 0.44, 0.06), (0, 0, 0.03), "dark", bevel=0.015)
    m.box((0.48, 0.32, 0.50), (0, 0, 0.31), "body", bevel=0.05)
    m.cyl(0.19, 0.03, (0, -0.165, 0.33), "dark", seg=12, axis="Y")
    m.cyl(0.16, 0.035, (0, -0.167, 0.33), "white", seg=12, axis="Y")
    m.box((0.02, 0.015, 0.12), (0, -0.19, 0.38), "dark")
    m.box((0.09, 0.015, 0.02), (0.04, -0.19, 0.33), "red")
    m.cyl(0.06, 0.06, (0, 0, 0.59), "red", seg=8)
    m.cyl(0.04, 0.06, (0.26, 0, 0.25), "out", seg=6, axis="X")


# ============================ SIGNS ============================
@machine("sign", "표지판", "표시", "글자를 적어 세워 둠. 앞면과 뒷면에 보임",
         chassis_on=False, ortho=2.4, tz=0.45)
def _sign(m, T):
    m.box((0.08, 0.08, 0.62), (0, 0, 0.31), "wood_dark")
    m.box((0.07, 0.92, 0.50), (0, 0, 0.84), "wood")
    m.box((0.09, 0.96, 0.05), (0, 0, 1.10), "wood_dark")
    m.box((0.09, 0.96, 0.05), (0, 0, 0.58), "wood_dark")


# ============================ HAND WORK ============================
@machine("campfire", "모닥불", "손 작업", "가장 처음 쓰는 불. 재료와 땔감을 직접 넣고 기다림",
         chassis_on=False, ortho=2.6, tz=0.15)
def _campfire(m, T):
    for k in range(8):
        a = k * math.pi / 4
        m.ico(0.10, (math.cos(a) * 0.32, math.sin(a) * 0.32, 0.06), "stone" if k % 2 else "stone_dark",
              squash=0.7, jitter=0.15)
    for k in range(3):
        m.cyl(0.055, 0.50, (0, 0, 0.08 + k * 0.03), "wood_dark", seg=6, axis="X", rot=k * math.pi / 3)
    m.ico(0.14, (0, 0, 0.24), "glow", squash=1.5, jitter=0.1)
    m.ico(0.09, (0.03, 0.02, 0.34), "spark", squash=1.6, jitter=0.1)
    m.ico(0.07, (-0.08, 0.04, 0.20), "glow", squash=1.3)


@machine("hand_furnace", "손 화덕", "손 작업", "돌로 쌓은 화덕. 광석과 땔감을 손으로 넣어 주괴를 만듦",
         chassis_on=False, ortho=3.6, tz=0.6)
def _hand_furnace(m, T):
    m.box((0.92, 0.92, 0.14), (0, 0, 0.07), "stone_dark", bevel=0.03)
    m.box((0.82, 0.82, 0.70), (0, 0, 0.49), "stone", bevel=0.05, taper=0.92)
    m.box((0.86, 0.86, 0.09), (0, 0, 0.885), "stone_dark", bevel=0.03)
    m.box((0.40, 0.03, 0.30), (0, -0.405, 0.40), "hole")
    m.box((0.30, 0.035, 0.18), (0, -0.41, 0.36), "glow")
    m.box((0.50, 0.06, 0.07), (0, -0.41, 0.585), "brick")
    for x in (-0.25, 0.25):
        m.box((0.07, 0.06, 0.34), (x, -0.41, 0.40), "brick")
    m.box((0.56, 0.14, 0.05), (0, -0.46, 0.20), "stone_dark")
    m.box((0.34, 0.34, 0.40), (0, 0.14, 1.13), "brick", taper=0.8, bevel=0.03)
    m.box((0.36, 0.36, 0.07), (0, 0.14, 1.36), "stone_dark", bevel=0.02)


def bench(m, top="wood", w=0.96, d=0.78):
    m.box((w, d, 0.10), (0, 0, 0.72), top, bevel=0.02)
    for x in (-(w / 2 - 0.08), w / 2 - 0.08):
        for y in (-(d / 2 - 0.08), d / 2 - 0.08):
            m.box((0.10, 0.10, 0.67), (x, y, 0.335), "wood_dark")
    m.box((w - 0.16, 0.05, 0.08), (0, -(d / 2 - 0.08), 0.30), "wood_dark")
    m.box((w, 0.05, 0.56), (0, d / 2 - 0.025, 1.05), "wood_dark")
    m.box((w + 0.04, 0.09, 0.05), (0, d / 2 - 0.025, 1.35), "wood")
    return 0.77, d / 2 - 0.06


def p_hammer(m, x, y, z, rz=0.0):
    with m.at((x, y, z), rz):
        m.box((0.24, 0.03, 0.03), (0, 0, 0.015), "wood_light")
        m.box((0.06, 0.12, 0.06), (0.11, 0, 0.03), "mid")


def p_anvil(m, x, y, z):
    with m.at((x, y, z)):
        m.box((0.26, 0.18, 0.06), (0, 0, 0.03), "dark")
        m.box((0.14, 0.12, 0.10), (0, 0, 0.11), "dark")
        m.box((0.34, 0.16, 0.08), (0, 0, 0.20), "dark", bevel=0.015)
        m.cyl(0.05, 0.16, (0.25, 0, 0.20), "dark", seg=6, axis="X", r2=0.012)
        m.box((0.14, 0.06, 0.03), (-0.02, 0, 0.255), "glow")


def p_vise(m, x, y, z):
    with m.at((x, y, z)):
        m.box((0.20, 0.16, 0.05), (0, 0, 0.025), "dark")
        m.box((0.05, 0.16, 0.15), (-0.06, 0, 0.125), "mid")
        m.box((0.05, 0.16, 0.15), (0.05, 0, 0.125), "mid")
        m.cyl(0.02, 0.22, (0.15, 0, 0.11), "light", seg=6, axis="X")
        m.box((0.02, 0.14, 0.02), (0.26, 0, 0.11), "red")
        m.box((0.06, 0.10, 0.02), (-0.005, 0, 0.19), "copper")


def p_pot(m, x, y, z):
    with m.at((x, y, z)):
        m.cyl(0.13, 0.04, (0, 0, 0.02), "dark", seg=8)
        m.cyl(0.10, 0.012, (0, 0, 0.042), "glow", seg=8)
        m.cyl(0.14, 0.16, (0, 0, 0.13), "dark", seg=10)
        m.cyl(0.12, 0.012, (0, 0, 0.212), "cream", seg=10)
        for s in (-1, 1):
            m.box((0.05, 0.03, 0.02), (s * 0.16, 0, 0.17), "mid")


def p_pcb(m, x, y, z):
    with m.at((x, y, z)):
        m.box((0.26, 0.20, 0.02), (0, 0, 0.01), "pcb")
        m.box((0.16, 0.02, 0.012), (-0.02, 0.05, 0.024), "gold")
        m.box((0.02, 0.12, 0.012), (0.05, -0.02, 0.024), "gold")
        m.box((0.07, 0.07, 0.03), (-0.05, -0.04, 0.03), "hole")


def p_mini_machine(m, x, y, z):
    with m.at((x, y, z)):
        m.box((0.32, 0.32, 0.04), (0, 0, 0.02), "dark")
        m.box((0.28, 0.28, 0.22), (0, 0, 0.15), "body", bevel=0.03)
        m.box((0.32, 0.32, 0.03), (0, 0, 0.275), "dark")
        m.box((0.02, 0.18, 0.14), (0.145, 0, 0.13), "out")
        m.box((0.022, 0.12, 0.09), (0.146, 0, 0.12), "hole")


@machine("wb_basic", "기본 작업대", "손 작업", "건축 블록, 일반 물건, 다른 작업대를 만듦",
         chassis_on=False, ortho=3.8, tz=0.7)
def _wb_basic(m, T):
    z, wy = bench(m)
    for i in range(3):
        m.box((0.34, 0.12, 0.035), (-0.22, -0.08, z + 0.018 + i * 0.037), "wood_light" if i % 2 else "wood")
    p_hammer(m, 0.18, -0.10, z, rad(20))
    m.box((0.36, 0.012, 0.12), (-0.12, wy, 1.10), "light")
    m.box((0.10, 0.03, 0.13), (0.11, wy, 1.10), "wood")
    m.box((0.03, 0.02, 0.30), (0.32, wy, 1.08), "accent")
    m.box((0.16, 0.02, 0.03), (0.26, wy, 0.94), "accent")


@machine("wb_tool", "도구 작업대", "손 작업", "곡괭이, 무기, 갑옷을 만듦",
         chassis_on=False, ortho=3.8, tz=0.7)
def _wb_tool(m, T):
    z, wy = bench(m, top="mid")
    p_anvil(m, -0.14, -0.06, z)
    p_hammer(m, 0.26, -0.16, z, rad(-30))
    m.box((0.03, 0.02, 0.46), (-0.26, wy, 1.06), "wood_light", rot=(0, rad(20), 0))
    m.box((0.30, 0.03, 0.05), (-0.18, wy, 1.28), "iron", rot=(0, rad(20), 0))
    m.box((0.05, 0.015, 0.36), (0.20, wy, 1.10), "light")
    m.box((0.16, 0.025, 0.03), (0.20, wy, 0.91), "gold")
    m.box((0.035, 0.025, 0.09), (0.20, wy, 0.86), "wood_dark")


@machine("wb_part", "부품 작업대", "손 작업", "판재, 막대, 기어 같은 부품을 손으로 하나씩 만듦",
         chassis_on=False, ortho=3.8, tz=0.7)
def _wb_part(m, T):
    z, wy = bench(m, top="mid")
    p_vise(m, -0.24, -0.08, z)
    m.gear(0.12, 0.04, (0.12, -0.16, z + 0.02), "iron", teeth=8, axis="Z")
    for i in range(3):
        m.box((0.20, 0.16, 0.02), (0.28, 0.10, z + 0.01 + i * 0.022), "copper")
    for i in range(3):
        m.cyl(0.02, 0.30, (-0.02 + i * 0.045, 0.16, z + 0.02), "iron", seg=6, axis="Y")
    m.gear(0.13, 0.03, (-0.24, wy, 1.08), "dark", teeth=8, axis="Y")
    m.gear(0.09, 0.03, (-0.05, wy, 1.16), "mid", teeth=6, axis="Y")
    m.box((0.24, 0.02, 0.04), (0.26, wy, 1.12), "light")
    m.box((0.04, 0.02, 0.18), (0.16, wy, 1.05), "light")


@machine("wb_machine", "기계 작업대", "손 작업", "벨트, 기계, 추출기를 만듦",
         chassis_on=False, ortho=3.8, tz=0.7)
def _wb_machine(m, T):
    z, wy = bench(m, top="mid")
    p_mini_machine(m, -0.18, -0.06, z)
    m.box((0.26, 0.04, 0.02), (0.24, -0.18, z + 0.01), "mid", rot=rad(25))
    m.box((0.07, 0.08, 0.02), (0.34, -0.13, z + 0.01), "mid", rot=rad(25))
    m.gear(0.08, 0.03, (0.26, 0.10, z + 0.015), "iron", teeth=6, axis="Z")
    m.box((0.50, 0.012, 0.34), (-0.16, wy, 1.08), "steel")
    for (dx, dz, w, h) in ((0, 0.09, 0.36, 0.012), (0, -0.09, 0.36, 0.012), (-0.18, 0, 0.012, 0.19),
                           (0.18, 0, 0.012, 0.19), (0.04, 0, 0.012, 0.19)):
        m.box((w, 0.014, h), (-0.16 + dx, wy - 0.002, 1.08 + dz), "light")
    m.gear(0.13, 0.03, (0.30, wy, 1.10), "accent", teeth=8, axis="Y")


@machine("wb_cook", "조리대", "손 작업", "음식을 만듦",
         chassis_on=False, ortho=3.8, tz=0.7)
def _wb_cook(m, T):
    z, wy = bench(m, top="stone")
    p_pot(m, -0.24, 0.02, z)
    m.box((0.28, 0.20, 0.02), (0.20, -0.10, z + 0.01), "wood_light")
    m.box((0.16, 0.09, 0.07), (0.16, -0.08, z + 0.055), "bread", bevel=0.025)
    m.box((0.14, 0.02, 0.012), (0.30, -0.14, z + 0.03), "light", rot=rad(30))
    m.box((0.06, 0.025, 0.02), (0.22, -0.185, z + 0.03), "dark", rot=rad(30))
    for x, r in ((-0.26, 0.10), (-0.04, 0.08)):
        m.cyl(r, 0.025, (x, wy, 1.12), "dark", seg=10, axis="Y")
        m.box((0.03, 0.02, 0.14), (x, wy, 1.12 - r - 0.06), "dark")
    m.box((0.03, 0.02, 0.24), (0.22, wy, 1.10), "light")
    m.cyl(0.045, 0.03, (0.22, wy, 0.97), "light", seg=8, axis="Y")


@machine("wb_elec", "전기 작업대", "손 작업", "감지기, 스위치, 논리 회로 같은 전기 부품을 만듦",
         chassis_on=False, ortho=3.8, tz=0.7)
def _wb_elec(m, T):
    z, wy = bench(m, top="mid")
    p_pcb(m, -0.20, -0.08, z)
    m.cyl(0.09, 0.08, (0.22, 0.08, z + 0.04), "copper", seg=10)
    m.cyl(0.04, 0.09, (0.22, 0.08, z + 0.04), "hole", seg=8)
    m.box((0.08, 0.06, 0.05), (0.12, -0.20, z + 0.025), "dark")
    m.cyl(0.015, 0.24, (0.20, -0.20, z + 0.09), "light", seg=6, axis="X", rot=(0, rad(-20), 0))
    m.cyl(0.02, 0.05, (0.32, -0.20, z + 0.045), "red", seg=6, axis="X", rot=(0, rad(-20), 0))
    m.cyl(0.14, 0.03, (-0.22, wy, 1.10), "dark", seg=12, axis="Y")
    m.cyl(0.11, 0.035, (-0.22, wy - 0.002, 1.10), "white", seg=12, axis="Y")
    m.box((0.012, 0.014, 0.09), (-0.20, wy - 0.024, 1.12), "red", rot=(0, rad(35), 0))
    for i, mk in enumerate(("out", "spark", "red")):
        m.cyl(0.03, 0.03, (0.08 + i * 0.11, wy, 1.18), mk, seg=6, axis="Y")
    m.box((0.30, 0.02, 0.10), (0.19, wy, 1.00), "hole")
    for x in (-0.36, 0.36):
        m.cyl(0.03, 0.10, (x, 0.36, 1.42), "white", seg=6)
        m.cyl(0.018, 0.04, (x, 0.36, 1.48), "copper", seg=6)


@machine("wb_furn", "가구 작업대", "손 작업", "가구와 꾸미기 물건을 만듦",
         chassis_on=False, ortho=3.8, tz=0.7)
def _wb_furn(m, T):
    z, wy = bench(m)
    with m.at((-0.20, -0.04, z)):
        m.box((0.22, 0.22, 0.03), (0, 0, 0.16), "wood_light")
        for x in (-0.09, 0.09):
            for y in (-0.09, 0.09):
                m.box((0.03, 0.03, 0.16), (x, y, 0.08), "wood_light")
        m.box((0.22, 0.03, 0.20), (0, 0.095, 0.27), "wood_light")
    m.box((0.20, 0.07, 0.06), (0.22, -0.14, z + 0.03), "wood_dark", bevel=0.01)
    m.box((0.05, 0.05, 0.06), (0.26, -0.14, z + 0.09), "wood")
    for (x, y) in ((0.10, 0.04), (0.20, 0.10), (0.30, 0.02)):
        m.ico(0.035, (x, y, z + 0.02), "cream", squash=0.5, jitter=0.2)
    m.cyl(0.07, 0.34, (-0.20, wy, 1.16), "red", seg=8, axis="X")
    m.cyl(0.07, 0.34, (-0.20, wy, 1.00), "water", seg=8, axis="X")
    m.box((0.22, 0.02, 0.28), (0.26, wy, 1.08), "gold")
    m.box((0.16, 0.024, 0.22), (0.26, wy, 1.08), "glass")


@machine("wb_all", "통합 작업대", "손 작업", "모든 분류의 물건을 한곳에서 만듦. 아주 비싼 후반 설비",
         chassis_on=False, size=(2, 1), ortho=5.0, tz=0.75)
def _wb_all(m, T):
    z, wy = bench(m, top="mid", w=1.92)
    m.box((1.96, 0.82, 0.03), (0, 0, 0.655), "gold")
    m.box((1.96, 0.09, 0.03), (0, wy + 0.035, 1.39), "gold")
    p_anvil(m, -0.68, -0.06, z)
    p_vise(m, -0.26, -0.10, z)
    p_mini_machine(m, 0.14, -0.04, z)
    p_pcb(m, 0.50, -0.14, z)
    p_pot(m, 0.74, 0.08, z)
    m.gear(0.20, 0.04, (0, wy, 1.08), "gold", teeth=10, axis="Y")
    m.cyl(0.07, 0.05, (0, wy - 0.01, 1.08), "red", seg=8, axis="Y")
    m.box((0.36, 0.012, 0.12), (-0.62, wy, 1.12), "light")
    m.box((0.10, 0.03, 0.13), (-0.39, wy, 1.12), "wood")
    m.box((0.05, 0.015, 0.36), (0.44, wy, 1.10), "light")
    m.box((0.16, 0.025, 0.03), (0.44, wy, 0.91), "gold")
    m.cyl(0.10, 0.025, (0.72, wy, 1.12), "dark", seg=10, axis="Y")
    m.box((0.03, 0.02, 0.14), (0.72, wy, 0.96), "dark")
    for x in (-0.90, 0.90):
        stack_lamp(m, x, 0.33, 1.38, "spark")


@machine("chest", "상자", "손 작업", "물건을 넣어 두는 보관함",
         chassis_on=False, ortho=2.9, tz=0.3)
def _chest(m, T):
    m.box((0.84, 0.62, 0.44), (0, 0, 0.22), "wood", bevel=0.02)
    m.box((0.88, 0.66, 0.20), (0, 0, 0.54), "wood_dark", bevel=0.04)
    for x in (-0.30, 0.30):
        m.box((0.07, 0.68, 0.66), (x, 0, 0.33), "mid")
    m.box((0.10, 0.03, 0.12), (0, -0.325, 0.42), "gold")


# ============================ TRADE ============================
@machine("vending", "자판기", "포장·판매",
         "물건과 가격을 걸어 두면 다른 플레이어가 사 감. 사고 싶은 물건과 돈을 걸어 둘 수도 있음",
         chassis_on=False, ortho=4.6, tz=0.9)
def _vending(m, T):
    m.box((0.92, 0.70, 0.12), (0, 0, 0.06), "dark", bevel=0.02)
    m.box((0.86, 0.62, 1.40), (0, 0, 0.82), "body", bevel=0.05)
    m.box((0.58, 0.02, 0.70), (-0.10, -0.315, 1.02), "glass")
    frame_strips(m, -0.10, -0.31, 1.02, 0.58, 0.70)
    m.box((0.58, 0.03, 0.02), (-0.10, -0.325, 1.02), "light")
    m.box((0.16, 0.03, 0.07), (-0.24, -0.33, 0.80), "copper")
    m.box((0.12, 0.03, 0.12), (0.02, -0.33, 0.82), "iron")
    m.box((0.14, 0.03, 0.10), (-0.22, -0.33, 1.14), "wood")
    m.gear(0.07, 0.03, (0.04, -0.33, 1.18), "gold", teeth=6, axis="Y")
    m.box((0.16, 0.02, 0.44), (0.30, -0.315, 1.10), "hole")
    for i, h in enumerate((0.06, 0.10, 0.14)):
        m.box((0.03, 0.02, h), (0.26 + i * 0.04, -0.325, 1.16 + h / 2), "gold")
    m.box((0.10, 0.02, 0.02), (0.30, -0.325, 1.00), "spark")
    m.box((0.50, 0.03, 0.16), (-0.10, -0.315, 0.36), "hole")
    for i in range(5):
        m.box((0.184, 0.30, 0.04), (-0.368 + i * 0.184, -0.40, 1.56), "red" if i % 2 == 0 else "white",
              rot=(rad(-18), 0, 0))
    m.cyl(0.03, 0.14, (0, 0, 1.59), "mid", seg=6)
    m.cyl(0.14, 0.05, (0, 0, 1.76), "gold", seg=10, axis="Y")


# ============================ MORE FACTORIES ============================
@machine("briquetter", "압축기", "변환", "톱밥 → 연료 덩이. 버려지던 부산물이 연료가 됨",
         ports=(W_IN, E_OUT), ins=("sawdust",), outs=("briquette",), ortho=4.9, tz=0.95)
def _briquetter(m, T):
    vent(m)
    bolts(m)
    for x in (-0.26, 0.26):
        m.cyl(0.045, 0.62, (x, 0, T + 0.31), "light", seg=8)
    m.box((0.70, 0.30, 0.10), (0, 0, T + 0.64), "body", bevel=0.02)
    m.cyl(0.05, 0.50, (0, 0, T + 0.60), "mid", seg=8)
    m.box((0.30, 0.30, 0.08), (0, 0, T + 0.34), "dark")
    m.gear(0.20, 0.04, (0, 0, T + 0.88), "red", teeth=6, axis="Z")
    m.box((0.36, 0.36, 0.22), (0, 0, T + 0.11), "mid", bevel=0.02)
    for i, (x, y) in enumerate(((0.36, -0.36), (0.36, -0.24), (0.36, -0.30))):
        m.box((0.10, 0.10, 0.06), (x, y, T + 0.03 + (0.06 if i == 2 else 0)), "coal", bevel=0.01)


@machine("oilpress", "착유기", "변환", "기름 작물 → 식물 기름. 석탄도 석유도 없을 때의 연료",
         ports=(W_IN, E_OUT), ins=("seed",), outs=("oilcan",))
def _oilpress(m, T):
    gauge(m, x=-0.17)
    bolts(m)
    m.cyl(0.17, 0.62, (0.02, 0.06, T + 0.30), "body", seg=10, axis="X")
    for x in (-0.18, 0.02, 0.22):
        m.cyl(0.185, 0.05, (x, 0.06, T + 0.30), "mid", seg=10, axis="X")
    for x in (-0.24, 0.28):
        m.box((0.08, 0.30, 0.20), (x, 0.06, T + 0.10), "dark")
    hopper(m, -0.22, 0.06, T + 0.44, w=0.34, h=0.18, fill="wheat_head")
    m.gear(0.15, 0.04, (0.37, 0.06, T + 0.30), "red", teeth=6, axis="X")
    m.pipe([(0.10, -0.06, T + 0.22), (0.10, -0.26, T + 0.22), (0.10, -0.30, T + 0.18),
            (0.10, -0.30, T + 0.14)], 0.03, "light", seg=6)
    barrel(m, (0.10, -0.30, T), "wheat", r=0.10, h=0.12, band="mid")


@machine("lathe", "선반", "변환", "철 막대 → 볼트, 철판 → 기어. 깎아서 모양을 냄",
         ports=(W_IN, E_OUT), ins=("ingot_fe",), outs=("gear",))
def _lathe(m, T):
    vent(m)
    bolts(m)
    m.box((0.84, 0.30, 0.10), (0, 0, T + 0.05), "mid", bevel=0.02)
    m.box((0.24, 0.36, 0.36), (-0.30, 0, T + 0.28), "body", bevel=0.04)
    m.cyl(0.12, 0.08, (-0.14, 0, T + 0.30), "dark", seg=8, axis="X")
    m.cyl(0.045, 0.44, (0.10, 0, T + 0.30), "iron", seg=8, axis="X")
    m.box((0.12, 0.20, 0.26), (0.36, 0, T + 0.23), "body", bevel=0.03)
    m.box((0.10, 0.12, 0.12), (0.08, -0.16, T + 0.20), "red")
    m.box((0.03, 0.10, 0.03), (0.08, -0.08, T + 0.28), "light")
    m.gear(0.10, 0.03, (-0.43, 0, T + 0.30), "dark", teeth=6, axis="X")
    for i in range(3):
        m.cyl(0.03, 0.06, (0.20 + i * 0.07, 0.30, T + 0.03), "iron", seg=6)


@machine("alloy", "합금로", "조합", "두 가지 금속을 함께 녹여 합금 주괴로 만듦",
         ports=(W_IN, S_IN, E_OUT), ins=("ingot_cu", "ingot_fe"), outs=("ingot_alloy",), ortho=4.9, tz=0.9)
def _alloy(m, T):
    for y in (-0.30, 0.34):
        m.box((0.12, 0.08, 0.46), (-0.05, y, T + 0.23), "mid", taper=0.7)
    m.cyl(0.04, 0.74, (-0.05, 0.02, T + 0.42), "dark", seg=6, axis="Y")
    a = rad(18)
    m.cyl(0.22, 0.36, (-0.05, 0.02, T + 0.40), "dark", seg=8, r2=0.27, rot=(0, a, 0))
    m.cyl(0.21, 0.02, (-0.05 + math.sin(a) * 0.185, 0.02, T + 0.40 + math.cos(a) * 0.185), "glow",
          seg=8, rot=(0, a, 0))
    m.box((0.30, 0.26, 0.07), (0.30, 0.02, T + 0.035), "dark", bevel=0.01)
    for y in (-0.05, 0.09):
        m.box((0.20, 0.08, 0.02), (0.30, y, T + 0.075), "glow")
    stack(m, -0.36, 0.36, T, h=0.60, r=0.07)


@machine("caster", "주조기", "변환", "철 주괴 → 기계 틀. 조립보다 재료가 더 들지만 한 줄로 끝남",
         ports=(W_IN, E_OUT), ins=("ingot_fe",), outs=("frame",), ortho=4.9, tz=0.9)
def _caster(m, T):
    window(m, "glow", w=0.30, h=0.20)
    bolts(m)
    m.box((0.80, 0.40, 0.08), (0, -0.10, T + 0.04), "mid", bevel=0.015)
    for i, x in enumerate((-0.26, 0.0, 0.26)):
        m.box((0.20, 0.28, 0.10), (x, -0.10, T + 0.13), "dark", bevel=0.015)
        m.box((0.14, 0.20, 0.02), (x, -0.10, T + 0.185), "glow" if i < 2 else "iron")
    m.box((0.10, 0.10, 0.62), (0.0, 0.36, T + 0.31), "mid")
    m.box((0.08, 0.52, 0.08), (0.0, 0.12, T + 0.60), "dark")
    m.cyl(0.11, 0.16, (0.0, -0.10, T + 0.48), "dark", seg=8)
    m.cyl(0.09, 0.012, (0.0, -0.10, T + 0.565), "glow", seg=8)
    m.box((0.03, 0.03, 0.20), (0.0, -0.10, T + 0.30), "glow")


@machine("loom", "직조기", "변환", "목화 → 천",
         ports=(W_IN, E_OUT), outs=("cloth",), ortho=4.9, tz=0.9)
def _loom(m, T):
    vent(m)
    bolts(m)
    for y in (-0.36, 0.36):
        m.box((0.70, 0.06, 0.08), (0, y, T + 0.04), "wood_dark")
        for x in (-0.30, 0.30):
            m.box((0.07, 0.06, 0.62), (x, y, T + 0.31), "wood")
        m.box((0.70, 0.06, 0.07), (0, y, T + 0.60), "wood_dark")
    for i in range(9):
        m.box((0.56, 0.012, 0.012), (0, -0.28 + i * 0.07, T + 0.40), "cream")
    m.cyl(0.07, 0.66, (0.30, 0, T + 0.34), "red", seg=8, axis="Y")
    m.cyl(0.05, 0.66, (-0.30, 0, T + 0.44), "cream", seg=8, axis="Y")
    m.box((0.05, 0.70, 0.26), (0.02, 0, T + 0.44), "wood_light")
    m.box((0.16, 0.05, 0.03), (0.14, 0.10, T + 0.42), "wood_dark")


@machine("gemcutter", "보석 절삭기", "변환", "다이아 → 절삭 날. 고급 도구와 기계 강화 부품의 재료",
         ports=(W_IN, E_OUT), ins=("diamond",), outs=("blade",), ortho=4.9, tz=0.9)
def _gemcutter(m, T):
    gauge(m, x=-0.17)
    bolts(m)
    m.cyl(0.20, 0.06, (0.0, 0.0, T + 0.03), "light", seg=10)
    crystal(m, (0, 0, T + 0.14), 0.10, "water_light")
    m.box((0.12, 0.12, 0.54), (-0.30, 0.28, T + 0.27), "mid")
    m.box((0.46, 0.07, 0.07), (-0.13, 0.15, T + 0.54), "dark", rot=rad(-38))
    m.gear(0.13, 0.02, (0.04, 0.02, T + 0.46), "light", teeth=10, axis="Z")
    m.cyl(0.03, 0.10, (0.04, 0.02, T + 0.51), "red", seg=6)
    m.box((0.03, 0.03, 0.30), (0.30, -0.24, T + 0.15), "mid")
    m.cyl(0.11, 0.02, (0.30, -0.28, T + 0.36), "dark", seg=10, rot=(rad(60), 0, 0))
    m.cyl(0.085, 0.025, (0.30, -0.28, T + 0.36), "glass", seg=10, rot=(rad(60), 0, 0))
    stack_lamp(m, 0.36, 0.36, T, "spark")


@machine("recycler", "분해기", "변환", "기계나 부품을 넣으면 들어간 재료의 일부를 되돌려 받음",
         ports=(W_IN, E_OUT, S_OUT), ins=("gear",), outs=("ingot_fe", "coil"))
def _recycler(m, T):
    top = hopper(m, -0.06, 0.08, T, w=0.72, h=0.34)
    for y in (0.0, 0.16):
        m.gear(0.10, 0.46, (-0.06, y, top - 0.02), "red", teeth=6, axis="X")
    for k in range(3):
        a = k * 2 * math.pi / 3
        arrow(m, 0.37 + math.cos(a) * 0.07, -0.37 + math.sin(a) * 0.07, T, a + math.pi / 2 + 0.4, "out", s=0.055)


@machine("painter", "도색기", "변환", "블록 + 염료 → 색을 입힌 블록",
         ports=(W_IN, E_OUT), ortho=4.9, tz=0.9)
def _painter(m, T):
    vent(m)
    bolts(m)
    for i, mk in enumerate(("red", "accent", "water")):
        x = -0.26 + i * 0.26
        m.cyl(0.10, 0.30, (x, 0.30, T + 0.15), "light", seg=8)
        m.cyl(0.085, 0.04, (x, 0.30, T + 0.31), mk, seg=8)
        m.pipe([(x, 0.30, T + 0.33), (x, 0.30, T + 0.58), (x * 0.4, 0.14, T + 0.66),
                (x * 0.2, -0.04, T + 0.66)], 0.025, mk, seg=6)
    for s in (-1, 1):
        m.box((0.06, 0.06, 0.62), (s * 0.40, -0.06, T + 0.31), "mid")
    m.box((0.86, 0.07, 0.07), (0, -0.06, T + 0.63), "dark")
    m.box((0.22, 0.18, 0.12), (0, -0.06, T + 0.60), "body", bevel=0.02)
    m.cyl(0.03, 0.10, (0, -0.06, T + 0.50), "dark", seg=6, r2=0.05)
    m.box((0.28, 0.28, 0.24), (0, -0.10, T + 0.12), "water")


@machine("magsep", "자석 분리기", "운반", "철이 든 것만 옆으로 끌어내고 나머지는 통과시킴",
         ports=(W_IN, E_OUT, S_OUT), ins=("crushed",), outs=("stone", "ore_fe"), ortho=4.9, tz=0.9)
def _magsep(m, T):
    for y in (-0.22, 0.22):
        m.box((0.16, 0.14, 0.34), (0, y, T + 0.41), "red", bevel=0.02)
        m.box((0.16, 0.14, 0.10), (0, y, T + 0.19), "light", bevel=0.02)
    m.box((0.16, 0.58, 0.14), (0, 0, T + 0.65), "red", bevel=0.02)
    for s in (-1, 1):
        m.box((0.07, 0.07, 0.78), (s * 0.30, 0.40, T + 0.39), "mid")
    m.box((0.72, 0.08, 0.08), (0, 0.40, T + 0.78), "dark")
    m.box((0.08, 0.44, 0.08), (0, 0.20, T + 0.76), "dark")
    m.cyl(0.20, 0.04, (0, 0, T + 0.02), "dark", seg=10)
    stack_lamp(m, 0.38, -0.38, T, "out")


@machine("sieve", "체질기", "변환", "자갈이나 모래를 걸러 아주 적은 양의 광물을 얻음. 광맥 핵이 없어도 됨",
         ports=(W_IN, E_OUT, S_OUT), ins=("gravel",), outs=("sand", "ore_fe"))
def _sieve(m, T):
    a = rad(12)
    for x in (-0.32, 0.32):
        for y in (-0.30, 0.30):
            h = 0.27 if x < 0 else 0.14
            m.cyl(0.035, h, (x, y, T + h / 2), "red", seg=6)
    m.box((0.82, 0.74, 0.10), (0, 0, T + 0.27), "body", rot=(0, a, 0), bevel=0.02)
    m.box((0.70, 0.62, 0.02), (0, 0, T + 0.33), "hole", rot=(0, a, 0))
    for i in range(6):
        x = -0.30 + i * 0.12
        m.box((0.02, 0.62, 0.012), (x, 0, T + 0.345 - math.sin(a) * x), "light", rot=(0, a, 0))
    for i in range(4):
        m.box((0.70, 0.02, 0.012), (0, -0.24 + i * 0.16, T + 0.345), "light", rot=(0, a, 0))
    m.box((0.20, 0.20, 0.18), (-0.26, 0.0, T + 0.50), "mid", bevel=0.03)
    m.cyl(0.06, 0.06, (-0.26, -0.11, T + 0.50), "red", seg=8, axis="Y")


@machine("sprinkler", "물뿌리개", "공급", "주변 밭에 물을 줘서 작물이 빨리 자람",
         chassis_on=False, ortho=3.0, tz=0.4)
def _sprinkler(m, T):
    m.cyl(0.18, 0.08, (0, 0, 0.04), "dark", seg=8)
    m.cyl(0.05, 0.60, (0, 0, 0.38), "light", seg=8)
    m.cyl(0.08, 0.06, (0, 0, 0.20), "water", seg=8)
    m.box((0.44, 0.07, 0.07), (0, 0, 0.70), "mid", rot=rad(30))
    m.cyl(0.07, 0.10, (0, 0, 0.70), "red", seg=8)
    for k in range(8):
        a = k * math.pi / 4 + 0.3
        r = 0.34 + 0.08 * (k % 2)
        m.ico(0.035, (math.cos(a) * r, math.sin(a) * r, 0.62 - 0.12 * (k % 2)), "water_light", squash=1.3)


@machine("seeder", "파종기", "공급", "수확이 끝난 자리에 씨앗을 다시 심음",
         ports=(W_IN,), ins=("seed",), ortho=4.9, tz=0.8)
def _seeder(m, T):
    hopper(m, 0, 0.08, T, w=0.60, h=0.30, fill="wheat")
    bolts(m)
    m.box((0.10, 0.50, 0.08), (0, -0.62, 0.62), "dark")
    m.box((0.52, 0.08, 0.08), (0, -0.86, 0.62), "mid")
    for x in (-0.20, 0.0, 0.20):
        m.cyl(0.035, 0.40, (x, -0.86, 0.40), "light", seg=6)
        m.cyl(0.01, 0.12, (x, -0.86, 0.14), "red", seg=6, r2=0.05)


@machine("incinerator", "소각로", "동력", "필요 없는 것을 태워 없앰. 전력이 조금 나옴",
         ports=(W_IN,), ins=("sawdust",), ortho=5.6, tz=1.15)
def _incinerator(m, T):
    y = window(m, "glow")
    for x in (-0.12, 0.0, 0.12):
        m.box((0.03, 0.02, 0.26), (x, y, 0.50), "dark")
    bolts(m)
    m.box((0.66, 0.66, 0.44), (0, 0.04, T + 0.22), "brick", bevel=0.03)
    for z in (0.14, 0.30):
        m.box((0.67, 0.67, 0.02), (0, 0.04, T + z), "mortar")
    m.box((0.70, 0.70, 0.06), (0, 0.04, T + 0.47), "dark", bevel=0.015)
    m.box((0.26, 0.03, 0.16), (0, -0.30, T + 0.20), "hole")
    m.box((0.20, 0.035, 0.10), (0, -0.305, T + 0.18), "glow")
    stack(m, 0, 0.10, T + 0.50, h=0.95, r=0.11, glow=True)


@machine("windturbine", "풍력 터빈", "동력", "바람으로 전력을 만듦. 연료가 필요 없지만 출력이 들쭉날쭉함",
         chassis_on=False, ortho=7.6, tz=1.5)
def _windturbine(m, T):
    m.box((0.70, 0.70, 0.12), (0, 0, 0.06), "dark", bevel=0.02)
    m.cyl(0.13, 2.30, (0, 0, 1.27), "light", seg=8, r2=0.07)
    m.box((0.22, 0.42, 0.20), (0, 0.04, 2.48), "body", bevel=0.04)
    hub = (0, -0.22, 2.48)
    m.cyl(0.07, 0.10, hub, "red", seg=8, axis="Y")
    with m.at(hub):
        for k in range(3):
            a = rad(10 + k * 120)
            m.box((0.11, 0.03, 0.90), (math.sin(a) * 0.50, 0, math.cos(a) * 0.50), "white",
                  rot=(0, a, 0), taper=0.4)


@machine("solar", "태양광 패널", "동력", "낮 동안 전력을 만듦",
         chassis_on=False, ortho=3.2, tz=0.45)
def _solar(m, T):
    m.box((0.40, 0.40, 0.06), (0, 0, 0.03), "dark", bevel=0.015)
    m.cyl(0.05, 0.50, (0, 0, 0.30), "mid", seg=8)
    t = (rad(28), 0, 0)
    m.box((0.98, 0.80, 0.05), (0, 0, 0.62), "light", rot=t)
    m.box((0.90, 0.72, 0.02), (0, -0.014, 0.646), "solar", rot=t)
    for i in range(1, 4):
        m.box((0.012, 0.72, 0.008), (-0.45 + i * 0.225, -0.019, 0.657), "light", rot=t)
    m.box((0.90, 0.012, 0.008), (0, -0.019, 0.657), "light", rot=t)


@machine("battery", "축전지", "동력", "남는 전력을 모아 두었다가 모자랄 때 내보냄",
         chassis_on=False, ortho=3.4, tz=0.45)
def _battery(m, T):
    m.box((0.92, 0.72, 0.10), (0, 0, 0.05), "dark", bevel=0.02)
    m.box((0.84, 0.64, 0.66), (0, 0, 0.43), "body", bevel=0.05)
    m.box((0.88, 0.68, 0.08), (0, 0, 0.56), "mid")
    for x, mk in ((-0.22, "red"), (0.22, "dark")):
        m.cyl(0.07, 0.10, (x, 0, 0.81), "copper", seg=8)
        m.cyl(0.085, 0.04, (x, 0, 0.78), mk, seg=8)
    m.box((0.50, 0.02, 0.20), (0, -0.325, 0.34), "hole")
    for i in range(4):
        m.box((0.09, 0.025, 0.14), (-0.18 + i * 0.12, -0.33, 0.34), "out" if i < 3 else "dark")


@machine("pole", "전신주", "동력", "전선을 이어 전기를 나름. 전신주 주변 몇 칸 안의 기계가 전기를 받음",
         chassis_on=False, ortho=6.6, tz=1.15)
def _pole(m, T):
    m.box((0.36, 0.36, 0.10), (0, 0, 0.05), "dark", bevel=0.02)
    m.cyl(0.075, 2.10, (0, 0, 1.15), "wood_dark", seg=8, r2=0.055)
    m.box((0.90, 0.08, 0.08), (0, 0, 1.95), "wood", bevel=0.01)
    for s_ in (-1, 1):
        m.box((0.05, 0.05, 0.42), (s_ * 0.17, 0, 1.78), "wood", rot=(0, s_ * rad(-40), 0))
    for x in (-0.38, 0.0, 0.38):
        z = 2.24 if x == 0 else 1.99
        m.cyl(0.04, 0.10, (x, 0, z + 0.05), "white", seg=6)
        m.cyl(0.025, 0.04, (x, 0, z + 0.12), "copper", seg=6)
        for s_ in (-1, 1):
            m.box((0.012, 0.50, 0.012), (x, s_ * 0.26, z + 0.09), "dark", rot=(s_ * rad(-10), 0, 0))
    m.cyl(0.11, 0.26, (0.0, -0.14, 1.45), "mid", seg=8)
    m.cyl(0.115, 0.03, (0.0, -0.14, 1.59), "dark", seg=8)
    bolt = [(0.02, 0.07), (-0.04, -0.005), (-0.005, -0.005), (-0.025, -0.07), (0.04, 0.015), (0.005, 0.015)]
    m.prism([(x, 1.45 + z) for x, z in bolt], -0.262, -0.25, "Y", "spark")


# ============================ PLANTS ============================
@machine("plant_sapling", "묘목 (심은 것)", "식물", "잔디나 흙 위에 심으면 시간이 지나 나무가 됨",
         chassis_on=False, ortho=2.4, tz=0.3)
def _plant_sapling(m, T):
    m.box((0.07, 0.07, 0.40), (0, 0, 0.20), "wood_dark")
    m.ico(0.20, (0, 0, 0.50), "leaf", squash=0.9, jitter=0.1)
    m.ico(0.13, (0.10, 0.06, 0.66), "leaf_light", squash=0.9, jitter=0.1)
    m.ico(0.11, (-0.10, -0.04, 0.38), "leaf_light", squash=0.9, jitter=0.1)


def _wheat(m, height, ripe):
    m.box((0.96, 0.96, 0.03), (0, 0, 0.015), "dirt_dark")
    for ix in range(4):
        for iy in range(4):
            x = -0.36 + ix * 0.24 + rng.uniform(-0.03, 0.03)
            y = -0.36 + iy * 0.24 + rng.uniform(-0.03, 0.03)
            h = height * rng.uniform(0.85, 1.1)
            m.box((0.035, 0.035, h), (x, y, 0.03 + h / 2), "wheat" if ripe else "leaf_light")
            if ripe:
                m.box((0.08, 0.08, 0.16), (x, y, 0.03 + h + 0.06), "wheat_head", taper=0.5)


machine("crop_wheat_1", "밀 (싹)", "식물", "경작지에 씨앗을 심은 직후", chassis_on=False, ortho=2.6,
        tz=0.15)(lambda m, T: _wheat(m, 0.12, False))
machine("crop_wheat_2", "밀 (자라는 중)", "식물", "절반쯤 자람", chassis_on=False, ortho=2.6,
        tz=0.2)(lambda m, T: _wheat(m, 0.32, False))
machine("crop_wheat_3", "밀 (다 자람)", "식물", "거두면 밀과 씨앗이 나옴", chassis_on=False, ortho=2.6,
        tz=0.3)(lambda m, T: _wheat(m, 0.50, True))


# ============================ ULTIMATE DEVICES ============================
def tilted_ring(m, center, radius, tube, euler, mk, seg=14):
    rot = Euler(euler, "XYZ").to_matrix()
    c = Vector(center)
    pts = [c + rot @ Vector((radius * math.cos(i * 2 * math.pi / seg), radius * math.sin(i * 2 * math.pi / seg), 0))
           for i in range(seg + 1)]
    m.pipe(pts, tube, mk, seg=6)


@machine("coreforge", "핵 제련소", "궁극의 장치",
         "막대한 재료로 광맥 핵을 만들어 냄. 흔한 핵을 합쳐 더 좋은 핵으로, 끝내는 금과 다이아의 핵까지",
         ports=(("W", "in", -1), ("W", "in", 1), ("S", "in", 0), ("E", "out", 0)), size=(3, 3),
         ins=("core_fe", "ingot_steel", "ingot_au"), outs=("core_dia",), ortho=12.4, tz=2.1)
def _coreforge(m, T):
    m.box((2.5, 2.5, 0.16), (0, 0, T + 0.08), "mid", bevel=0.03)
    m.cyl(1.0, 0.14, (0, 0, T + 0.23), "dark", seg=12)
    m.cyl(0.62, 0.10, (0, 0, T + 0.35), "light", seg=12)
    m.cyl(0.40, 0.02, (0, 0, T + 0.41), "core_dia", seg=12)
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        with m.at((math.cos(a) * 0.95, math.sin(a) * 0.95, T + 0.16), a):
            m.box((0.28, 0.32, 1.20), (0, 0, 0.60), "body", bevel=0.05)
            m.box((0.30, 0.34, 0.10), (0, 0, 0.30), "dark")
            m.box((0.30, 0.34, 0.10), (0, 0, 0.90), "dark")
            m.box((0.22, 0.24, 1.00), (-0.265, 0, 1.62), "light", rot=(0, rad(-32), 0), bevel=0.03)
            m.cyl(0.11, 0.38, (0, 0, 1.20), "dark", seg=8, axis="Y")
    crystal(m, (0, 0, T + 2.05), 0.42, "core_dia")
    for k, mk in enumerate(("core_fe", "core_coal", "core_cu", "core_gold")):
        a = k * math.pi / 2
        x, y = math.cos(a) * 1.15, math.sin(a) * 1.15
        m.cyl(0.16, 0.50, (x, y, T + 0.41), "mid", seg=8)
        m.cyl(0.20, 0.06, (x, y, T + 0.69), "dark", seg=8)
        crystal(m, (x, y, T + 0.86), 0.11, mk)
        m.pipe([(x, y, T + 1.08), (x * 0.25, y * 0.25, T + 1.85)], 0.016, mk, seg=4)
    stack(m, -1.2, 1.2, T, h=1.8, r=0.12, glow=True)
    stack(m, 1.2, 1.2, T, h=1.4, r=0.10)
    for x in (-1, 1):
        y = window(m, "glow", x=x, sy=3)
        for dx in (-0.10, 0.0, 0.10):
            m.box((0.03, 0.02, 0.26), (x + dx, y, 0.50), "dark")
    for x in (-1.36, 1.36):
        for z in (0.20, 0.82):
            m.cyl(0.022, 0.03, (x, -1.445, z), "mid", seg=6, axis="Y")


@machine("reactor", "무한 동력로", "궁극의 장치",
         "연료 없이 전기를 끝없이 냄. 섬의 모든 기계를 최고 효율로 돌림",
         size=(3, 3), ortho=12.0, tz=1.9)
def _reactor(m, T):
    m.box((2.5, 2.5, 0.16), (0, 0, T + 0.08), "mid", bevel=0.03)
    m.cyl(0.95, 0.30, (0, 0, T + 0.31), "dark", seg=12, r2=0.72)
    m.cyl(0.50, 0.46, (0, 0, T + 0.69), "body", seg=12, r2=0.34)
    m.ring(0.98, 0.06, T + 0.42, "copper", seg=14)
    m.ring(0.80, 0.05, T + 0.56, "copper", seg=14)
    cz = T + 1.80
    m.ico(0.40, (0, 0, cz), "spark")
    m.cyl(0.10, 0.36, (0, 0, T + 1.10), "light", seg=8, r2=0.05)
    for e in ((0, 0, 0), (rad(90), 0, 0), (rad(90), 0, rad(90))):
        tilted_ring(m, (0, 0, cz), 0.74, 0.05, e, "light")
    tilted_ring(m, (0, 0, cz), 0.92, 0.035, (rad(55), 0, rad(35)), "mid")
    for sx_ in (-1, 1):
        for sy_ in (-1, 1):
            x, y = sx_ * 1.02, sy_ * 1.02
            m.box((0.34, 0.34, 1.70), (x, y, T + 1.01), "body", taper=0.5, bevel=0.03)
            m.box((0.36, 0.36, 0.10), (x, y, T + 0.50), "dark")
            for i in range(2):
                m.cyl(0.07, 0.10, (x, y, T + 1.92 + i * 0.12), "white", seg=8)
            m.cyl(0.035, 0.08, (x, y, T + 2.18), "copper", seg=6)
            m.pipe([(x, y, T + 2.20), (x * 0.36, y * 0.36, cz + 0.16)], 0.014, "spark", seg=4)
    for i in range(5):
        m.box((0.03, 0.70, 0.40), (-0.24 + i * 0.12, 1.10, T + 0.36), "light")
    y = window(m, "spark", x=0, sy=3, w=0.50, h=0.30)
    bolt = [(0.03, 0.11), (-0.07, -0.01), (-0.01, -0.01), (-0.045, -0.11), (0.07, 0.025), (0.01, 0.025)]
    m.prism([(x_, 0.50 + z_) for x_, z_ in bolt], y - 0.012, y, "Y", "dark")
    for x in (-1, 1):
        vent(m, x=x, sy=3)
    for x in (-0.5, 0.5):
        m.cyl(0.06, 0.16, (x, -1.20, T + 0.24), "white", seg=8)
        m.cyl(0.035, 0.06, (x, -1.20, T + 0.35), "copper", seg=6)


# ============================ ITEMS ============================
ITEM_SPECS = []
TOOL_RZ = math.pi / 4   # tools are built flat in the XZ plane and turned to face the camera


def reg(key, ko, cat, fn, ortho=0.80, tz=0.10, rz=0.0):
    ITEM_SPECS.append(dict(key=key, ko=ko, cat=cat, fn=fn, ortho=ortho, tz=tz, rz=rz))


# ---- shape helpers ----
def f_ore(nug):
    def f(m):
        m.ico(0.13, (0, 0, 0.10), "stone", squash=0.8, jitter=0.18)
        m.ico(0.05, (0.07, -0.04, 0.15), nug, jitter=0.2)
        m.ico(0.04, (-0.06, 0.05, 0.14), nug, jitter=0.2)
        m.ico(0.035, (0.0, -0.09, 0.09), nug, jitter=0.2)
    return f


def f_chunk(mk, r=0.13):
    return lambda m: m.ico(r, (0, 0, r * 0.75), mk, squash=0.8, jitter=0.18)


def f_pile(mk):
    def f(m):
        for (x, y, r) in ((0, 0, 0.07), (0.09, 0.03, 0.055), (-0.07, 0.06, 0.05), (0.01, -0.08, 0.05)):
            m.ico(r, (x, y, r * 0.8), mk, squash=0.85, jitter=0.2)
    return f


def f_heap(mk):
    return lambda m: m.cyl(0.14, 0.12, (0, 0, 0.06), mk, seg=8, r2=0.03)


def f_ingot(mk):
    return lambda m: m.box((0.28, 0.14, 0.09), (0, 0, 0.045), mk, bevel=0.012, taper=0.78)


def f_plate(mk):
    return lambda m: m.box((0.26, 0.22, 0.035), (0, 0, 0.018), mk, bevel=0.008)


def f_rods(mk):
    def f(m):
        for (x, z) in ((-0.035, 0.03), (0.035, 0.03), (0.0, 0.085)):
            m.cyl(0.03, 0.34, (x, 0, z), mk, seg=6, axis="Y")
    return f


def f_coil(mk):
    def f(m):
        m.cyl(0.11, 0.10, (0, 0, 0.05), mk, seg=10)
        m.cyl(0.05, 0.11, (0, 0, 0.05), "hole", seg=8)
    return f


def f_barrel(mk, band):
    return lambda m: barrel(m, (0, 0, 0), mk, r=0.10, h=0.26, band=band)


def f_core(mk):
    return lambda m: crystal(m, (0, 0, 0.14), 0.11, mk)


def f_block(mk, s=0.20, bevel=0.02):
    return lambda m: m.box((s, s, s), (0, 0, s / 2), mk, bevel=bevel)


def tool_handle(m, h=0.56):
    m.box((0.045, 0.045, h), (0, 0, h / 2), "wood_dark")


def f_pick(mk):
    def f(m):
        tool_handle(m)
        m.prism([(-0.30, 0.46), (-0.16, 0.56), (0, 0.60), (0.16, 0.56), (0.30, 0.46),
                 (0.16, 0.51), (0, 0.54), (-0.16, 0.51)], -0.03, 0.03, "Y", mk)
    return f


def f_axe(mk):
    def f(m):
        tool_handle(m)
        m.prism([(0.0, 0.43), (0.19, 0.38), (0.24, 0.50), (0.19, 0.62), (0.0, 0.57)], -0.03, 0.03, "Y", mk)
        m.box((0.08, 0.06, 0.10), (-0.04, 0, 0.50), mk)
    return f


def f_shovel(mk):
    def f(m):
        tool_handle(m, 0.50)
        m.prism([(-0.09, 0.46), (0.09, 0.46), (0.10, 0.62), (0.0, 0.72), (-0.10, 0.62)], -0.02, 0.02, "Y", mk)
        m.box((0.14, 0.05, 0.035), (0, 0, 0.02), "wood_dark")
    return f


def f_hoe(mk):
    def f(m):
        tool_handle(m)
        m.prism([(-0.02, 0.60), (0.22, 0.60), (0.24, 0.47), (0.17, 0.47), (0.15, 0.54), (-0.02, 0.54)],
                -0.03, 0.03, "Y", mk)
    return f


def f_sword(mk):
    def f(m):
        m.prism([(-0.045, 0.20), (0.045, 0.20), (0.045, 0.60), (0, 0.70), (-0.045, 0.60)], -0.015, 0.015, "Y", mk)
        m.box((0.22, 0.06, 0.04), (0, 0, 0.19), "dark")
        m.box((0.04, 0.04, 0.14), (0, 0, 0.10), "wood_dark")
        m.box((0.07, 0.06, 0.04), (0, 0, 0.02), "dark")
    return f


def build_items():
    T_ = dict(ortho=1.15, tz=0.36, rz=TOOL_RZ)
    tiers = (("wood", "나무", "wood"), ("stone", "돌", "stone"), ("iron", "철", "iron"),
             ("steel", "강철", "steel"), ("gold", "금", "gold"), ("dia", "다이아", "diamond"))
    for shape, ko, fn in (("pick", "곡괭이", f_pick), ("axe", "도끼", f_axe), ("shovel", "삽", f_shovel),
                          ("hoe", "괭이", f_hoe), ("sword", "검", f_sword)):
        for tk, tko, mk in tiers:
            reg(f"{shape}_{tk}", f"{tko} {ko}", "도구", fn(mk), **T_)

    def hammer(m):
        tool_handle(m, 0.50)
        m.box((0.26, 0.10, 0.12), (0, 0, 0.52), "mid", bevel=0.015)

    def wrench(m):
        m.box((0.05, 0.03, 0.44), (0, 0, 0.24), "light")
        m.prism([(-0.09, 0.44), (-0.09, 0.60), (-0.04, 0.60), (-0.04, 0.50), (0.04, 0.50), (0.04, 0.60),
                 (0.09, 0.60), (0.09, 0.44)], -0.018, 0.018, "Y", "light")
        m.box((0.07, 0.035, 0.05), (0, 0, 0.03), "red")

    def rod(m):
        m.box((0.03, 0.03, 0.72), (0.10, 0, 0.36), "wood_dark", rot=(0, rad(18), 0))
        m.cyl(0.05, 0.05, (0.02, 0, 0.16), "red", seg=8, axis="Y")
        m.box((0.008, 0.008, 0.40), (0.21, 0, 0.48), "white")
        m.ico(0.03, (0.21, 0, 0.27), "red")

    def bucket(m):
        m.cyl(0.10, 0.20, (0, 0, 0.10), "light", seg=10, r2=0.14)
        m.cyl(0.125, 0.012, (0, 0, 0.19), "water", seg=10)
        m.ring(0.13, 0.012, 0.21, "mid")

    def can(m):
        m.cyl(0.12, 0.20, (0, 0, 0.10), "out", seg=10)
        m.pipe([(0.10, 0, 0.06), (0.22, 0, 0.16), (0.28, 0, 0.26)], 0.022, "out", seg=6)
        m.cyl(0.04, 0.03, (0.29, 0, 0.27), "mid", seg=6, rot=(0, rad(50), 0))
        m.box((0.03, 0.03, 0.16), (-0.16, 0, 0.12), "mid")
        m.box((0.08, 0.03, 0.03), (-0.13, 0, 0.19), "mid")

    reg("hammer", "망치", "도구", hammer, **T_)
    reg("wrench", "렌치", "도구", wrench, **T_)
    reg("fishing_rod", "낚싯대", "도구", rod, ortho=1.3, tz=0.38, rz=TOOL_RZ)
    reg("bucket", "양동이", "도구", bucket, ortho=0.8, tz=0.12)
    reg("watering_can", "물뿌리개", "도구", can, ortho=0.9, tz=0.14, rz=TOOL_RZ)

    # ---- raw ----
    reg("stone", "돌", "원석과 광물", f_chunk("stone"))
    reg("coal", "석탄", "원석과 광물", f_chunk("coal", 0.12))
    reg("ore_cu", "구리 광석", "원석과 광물", f_ore("copper"))
    reg("ore_fe", "철 광석", "원석과 광물", f_ore("iron"))
    reg("ore_au", "금 광석", "원석과 광물", f_ore("gold"))
    reg("ore_dia", "다이아 원석", "원석과 광물", f_ore("diamond"))
    reg("diamond", "다이아", "원석과 광물", lambda m: crystal(m, (0, 0, 0.12), 0.09, "diamond"))
    reg("sand", "모래", "원석과 광물", f_heap("sand"))
    reg("gravel", "자갈", "원석과 광물", f_pile("stone_dark"))
    reg("clay", "점토", "원석과 광물", f_chunk("clay", 0.12))
    reg("dirt_clod", "흙", "원석과 광물", f_chunk("dirt", 0.12))

    # ---- ore processing ----
    for k, ko, mk in (("cu", "구리", "copper"), ("fe", "철", "iron"), ("au", "금", "gold")):
        reg("crushed" if k == "cu" else f"crushed_{k}", f"분쇄 {ko}광", "광석 가공", f_pile(mk))
    for k, ko, mk in (("cu", "구리", "copper_light"), ("fe", "철", "white"), ("au", "금", "spark")):
        reg("clean" if k == "cu" else f"clean_{k}", f"정제 {ko}광", "광석 가공",
            lambda m, mk=mk: (f_pile(mk)(m), m.box((0.24, 0.24, 0.02), (0, 0, 0.01), "water_light")))
    reg("slag", "찌꺼기", "광석 가공", f_pile("slag"))

    # ---- ingots ----
    for k, ko, mk in (("cu", "구리", "copper"), ("fe", "철", "iron"), ("steel", "강철", "steel"),
                      ("au", "금", "gold"), ("alloy", "합금", "gold_dark")):
        reg(f"ingot_{k}", f"{ko} 주괴", "주괴", f_ingot(mk))

    # ---- metal parts ----
    for k, ko, mk in (("cu", "구리", "copper"), ("fe", "철", "iron"), ("steel", "강철", "steel")):
        reg(f"plate_{k}", f"{ko}판", "금속 부품", f_plate(mk))
        reg(f"rod_{k}", f"{ko} 막대", "금속 부품", f_rods(mk))
    reg("coil", "구리선", "금속 부품", f_coil("copper"))
    reg("wire_au", "금선", "금속 부품", f_coil("gold"))
    reg("bolt", "볼트", "금속 부품", lambda m: [
        (m.cyl(0.03, 0.14, (x, y, 0.07), "iron", seg=6), m.cyl(0.05, 0.04, (x, y, 0.15), "iron", seg=6))
        for x, y in ((-0.06, -0.03), (0.06, 0.0), (0.0, 0.07))])
    reg("gear", "기어", "금속 부품", lambda m: m.gear(0.13, 0.06, (0, 0, 0.03), "iron", teeth=8, axis="Z"))
    reg("frame", "기계 틀", "금속 부품", lambda m: (
        m.box((0.26, 0.26, 0.05), (0, 0, 0.025), "iron"), m.box((0.26, 0.26, 0.05), (0, 0, 0.215), "iron"),
        [m.box((0.05, 0.05, 0.24), (x, y, 0.12), "iron") for x in (-0.105, 0.105) for y in (-0.105, 0.105)]))
    reg("beam", "강철 기둥", "금속 부품", lambda m: (
        m.box((0.16, 0.36, 0.03), (0, 0, 0.015), "steel"), m.box((0.16, 0.36, 0.03), (0, 0, 0.165), "steel"),
        m.box((0.03, 0.36, 0.14), (0, 0, 0.09), "steel")))
    reg("blade", "절삭 날", "금속 부품", lambda m: (
        m.gear(0.12, 0.02, (0, 0, 0.01), "diamond", teeth=10, axis="Z"), m.cyl(0.04, 0.03, (0, 0, 0.015), "mid", seg=6)))

    # ---- assemblies ----
    reg("motor", "모터", "조립품", lambda m: (
        m.cyl(0.10, 0.24, (0, 0, 0.11), "steel", seg=8, axis="X"), m.cyl(0.11, 0.06, (0, 0, 0.11), "copper", seg=8, axis="X"),
        m.cyl(0.03, 0.34, (0, 0, 0.11), "light", seg=6, axis="X"), m.box((0.16, 0.16, 0.03), (0, 0, 0.015), "dark")))
    reg("board", "회로 기판", "조립품", lambda m: (
        m.box((0.24, 0.20, 0.025), (0, 0, 0.013), "pcb"), m.box((0.08, 0.08, 0.03), (0.03, 0.02, 0.035), "hole"),
        m.box((0.14, 0.02, 0.012), (-0.03, -0.06, 0.03), "gold")))
    reg("board_adv", "고급 회로", "조립품", lambda m: (
        m.box((0.26, 0.22, 0.025), (0, 0, 0.013), "steel"), m.box((0.10, 0.10, 0.035), (0, 0, 0.04), "hole"),
        [m.box((0.02, 0.07, 0.012), (x, y, 0.03), "gold") for x in (-0.09, -0.05, 0.05, 0.09) for y in (-0.06, 0.06)],
        m.box((0.05, 0.05, 0.02), (0, 0, 0.067), "spark")))
    reg("cell", "전지", "조립품", lambda m: (
        m.cyl(0.08, 0.22, (0, 0, 0.11), "body", seg=8), m.cyl(0.082, 0.08, (0, 0, 0.11), "out", seg=8),
        m.cyl(0.035, 0.03, (0, 0, 0.235), "copper", seg=6)))
    reg("monster_part", "핵심 부품", "조립품", lambda m: (
        m.cyl(0.12, 0.04, (0, 0, 0.02), "dark", seg=8), crystal(m, (0, 0, 0.14), 0.07, "monster"),
        [m.box((0.03, 0.03, 0.14), (math.cos(a) * 0.09, math.sin(a) * 0.09, 0.09), "mid") for a in (0.5, 2.6, 4.7)]))

    # ---- building materials ----
    reg("plank", "판자", "건축 재료", lambda m: m.box((0.14, 0.34, 0.045), (0, 0, 0.023), "wood"))
    reg("stone_block", "석재", "건축 재료", f_block("stone"))
    reg("brick", "벽돌", "건축 재료", lambda m: m.box((0.24, 0.12, 0.09), (0, 0, 0.045), "brick", bevel=0.01))
    reg("glass", "유리", "건축 재료", lambda m: m.box((0.24, 0.03, 0.22), (0, 0, 0.11), "glass", rot=(rad(12), 0, 0)))
    reg("concrete", "콘크리트", "건축 재료", lambda m: m.box((0.22, 0.22, 0.16), (0, 0, 0.08), "slurry", bevel=0.02))
    reg("asphalt", "포장재", "건축 재료", lambda m: m.box((0.24, 0.24, 0.08), (0, 0, 0.04), "asphalt", bevel=0.01))
    reg("cloth", "천", "건축 재료", lambda m: (
        m.box((0.26, 0.20, 0.05), (0, 0, 0.025), "cream", bevel=0.015), m.box((0.27, 0.05, 0.052), (0, 0, 0.026), "red")))

    # ---- wood and fuel ----
    reg("log", "통나무", "나무와 연료", lambda m: (
        m.cyl(0.09, 0.34, (0, 0, 0.09), "wood_dark", seg=8, axis="Y"), m.cyl(0.07, 0.35, (0, 0, 0.09), "wood_light", seg=8, axis="Y")))
    reg("sawdust", "톱밥", "나무와 연료", f_pile("wood_light"))
    reg("charcoal", "숯", "나무와 연료", lambda m: (
        m.box((0.10, 0.22, 0.08), (0, 0, 0.04), "charcoal", rot=0.3), m.box((0.08, 0.18, 0.07), (0.06, 0.02, 0.10), "charcoal", rot=-0.5)))
    reg("briquette", "연료 덩이", "나무와 연료", lambda m: m.box((0.20, 0.14, 0.10), (0, 0, 0.05), "coal", bevel=0.02))
    reg("barrel_water", "물통", "나무와 연료", f_barrel("water", "mid"))
    reg("barrel_oil", "원유통", "나무와 연료", f_barrel("oil", "red"))
    reg("barrel_fuel", "연료통", "나무와 연료", f_barrel("red", "dark"))
    reg("oilcan", "식물 기름통", "나무와 연료", f_barrel("wheat", "mid"))
    reg("tar", "타르", "나무와 연료", f_barrel("tar", "mid"))
    reg("plastic", "플라스틱", "나무와 연료", f_block("white", 0.20, 0.03))

    # ---- farm ----
    reg("wheat", "밀", "농산물과 음식", lambda m: [
        m.box((0.035, 0.035, 0.26), (x, y, 0.13), "wheat_head", taper=0.5) for x, y in ((0, 0), (0.05, 0.03), (-0.04, 0.04), (0.02, -0.05))])
    reg("seed", "씨앗", "농산물과 음식", f_pile("wheat"))
    reg("flour", "밀가루", "농산물과 음식", lambda m: (
        m.box((0.18, 0.14, 0.20), (0, 0, 0.10), "cream", bevel=0.04, taper=0.8), m.box((0.10, 0.08, 0.04), (0, 0, 0.21), "wood")))
    reg("dough", "반죽", "농산물과 음식", lambda m: m.ico(0.11, (0, 0, 0.07), "dough", squash=0.65))
    reg("bread", "빵", "농산물과 음식", lambda m: m.box((0.24, 0.13, 0.11), (0, 0, 0.055), "bread", bevel=0.04))
    reg("cotton", "목화", "농산물과 음식", lambda m: (
        m.box((0.02, 0.02, 0.16), (0, 0, 0.08), "leaf"), m.ico(0.07, (0, 0, 0.20), "cotton", jitter=0.1),
        m.ico(0.05, (0.06, 0.02, 0.15), "cotton", jitter=0.1), m.ico(0.05, (-0.05, -0.03, 0.16), "cotton", jitter=0.1)))
    reg("oilseed", "기름 작물", "농산물과 음식", lambda m: (
        m.box((0.025, 0.025, 0.20), (0, 0, 0.10), "leaf"), m.cyl(0.10, 0.03, (0, -0.01, 0.24), "gold", seg=10, axis="Y"),
        m.cyl(0.055, 0.035, (0, -0.012, 0.24), "wood_dark", seg=8, axis="Y")), rz=TOOL_RZ)
    reg("sapling", "묘목", "농산물과 음식", lambda m: (
        m.ico(0.09, (0, 0, 0.05), "dirt", squash=0.7), m.box((0.025, 0.025, 0.18), (0, 0, 0.16), "wood_dark"),
        m.ico(0.08, (0, 0, 0.29), "leaf", jitter=0.1), m.ico(0.05, (0.05, 0.02, 0.35), "leaf_light", jitter=0.1)), ortho=0.9, tz=0.18)

    # ---- cores ----
    for k, ko, mk in (("stone", "돌", "core_stone"), ("coal", "석탄", "core_coal"), ("cu", "구리", "core_cu"),
                      ("fe", "철", "core_fe"), ("au", "금", "core_gold"), ("dia", "다이아", "core_dia")):
        reg(f"core_{k}", f"{ko} 광맥 핵", "광맥 핵", f_core(mk))

    reg("crate", "상자 (포장)", "포장", lambda m: crate(m, (0, 0, 0), s=0.26))

    items = {}
    for s in ITEM_SPECS:
        m = Model("item_" + s["key"])
        s["fn"](m)
        items[s["key"]] = m.done()
        s["tris"] = m.tris
    return items


# ============================ BUILD ============================
MESH = {}
for s in SPECS:
    m = Model(s["key"])
    T = chassis(m, s["size"][0], s["size"][1], s["ports"]) if s["chassis"] else 0.0
    s["fn"](m, T)
    MESH[s["key"]] = m.done()
    s["tris"], s["colors"] = m.tris, len(m.mats)
    print(f"KIT {s['key']:14s} tris={m.tris:5d} colors={len(m.mats)}")
ITEMS = build_items()


def port_cell(s, side, off):
    sx, sy = s["size"]
    if side == "E":
        return Vector((sx / 2 + 0.5, off, 0))
    if side == "W":
        return Vector((-sx / 2 - 0.5, off, 0))
    if side == "N":
        return Vector((off, sy / 2 + 0.5, 0))
    return Vector((off, -sy / 2 - 0.5, 0))


# ---- lighting ----
world = bpy.data.worlds.new("w")
if world.node_tree is None:
    world.use_nodes = True
bg = next(n for n in world.node_tree.nodes if n.type == "BACKGROUND")
bg.inputs[0].default_value = (lin(0.84), lin(0.90), lin(0.95), 1)
bg.inputs[1].default_value = 0.75
scene.world = world


def aim(ob, loc, target):
    ob.location = loc
    ob.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()


sd = bpy.data.lights.new("sun", "SUN")
sd.energy = 2.3
sd.angle = rad(12)
sun = bpy.data.objects.new("sun", sd)
col.objects.link(sun)
aim(sun, (3, -6, 9), (0, 0, 0))

if "eevee" in ARGS:
    for eng in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
        try:
            scene.render.engine = eng
            break
        except Exception:
            continue
else:
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 40
    try:
        scene.cycles.use_denoising = True
    except Exception:
        pass
scene.view_settings.view_transform = "Standard"

cd = bpy.data.cameras.new("cam")
cd.type = "ORTHO"
cam = bpy.data.objects.new("cam", cd)
col.objects.link(cam)
scene.camera = cam


def shoot(path, target, ortho, res, transparent):
    cd.ortho_scale = ortho
    t = Vector(target)
    aim(cam, t + Vector((14, -14, 12.5)), t)
    scene.render.film_transparent = transparent
    scene.render.resolution_x, scene.render.resolution_y = res
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)


# ============================ THUMBNAILS ============================
if "thumbs" in ARGS:
    shown = [s for s in SPECS if s["show"]]
    only = {a.split("=", 1)[1] for a in ARGS if a.startswith("only=")}
    for i, s in enumerate(shown):
        if only and s["key"] not in only:
            continue
        O = Vector((i * 40.0, 0, 0))
        place(MESH[s["key"]], O)
        ins, outs = list(s["ins"]), list(s["outs"])
        for side, kind, off in s["ports"]:
            c = port_cell(s, side, off)
            a = SIDE_ANG[side] + (math.pi if kind == "in" else 0.0)
            place(MESH["belt"], O + c, a)
            name = (ins.pop(0) if ins else None) if kind == "in" else (outs.pop(0) if outs else None)
            if name:
                place(ITEMS[name], O + c + Vector((0, 0, 0.30)), rng.uniform(0, 1.2))
        shoot(os.path.join(OUT, "img", s["key"] + ".png"), O + Vector((0, 0, s["tz"])),
              s["ortho"] * 0.74, (640, 640), True)
        print("THUMB", s["key"])

# ============================ CONNECTED LINE ============================
if "line" in ARGS:
    B = Vector((0, 200, 0))
    E, Wd, Sd = 0.0, math.pi, -math.pi / 2

    def put(key, x, y, rz=0.0, mx=False, my=False):
        return place(MESH[key], B + Vector((x, y, 0)), rz, mx, my)

    def item(name, x, y):
        place(ITEMS[name], B + Vector((x, y, 0.30)), rng.uniform(0, 1.5))

    # top row, flowing east
    put("extractor_cu", -4, 2)
    put("belt", -3, 2)
    put("crusher", -2, 2)
    put("belt", -1, 2)
    put("smelter", 0, 2)
    put("belt", 1, 2)
    put("splitter", 2, 2)
    put("belt", 3, 2)
    put("belt_corner", 4, 2)                 # E -> S
    for y in (1, 0, -1):
        put("belt", 4, y, Sd)
    put("belt_corner", 4, -2, Sd)            # S -> W
    # bottom row, flowing west (machines mirrored so their fronts still face the camera)
    put("press", 3, -2, mx=True)
    put("belt", 2, -2, Wd)
    put("belt", 1, -2, Wd)
    put("assembler_n", 0, -2, mx=True)
    put("belt", -1, -2, Wd)
    put("packer", -2, -2, mx=True)
    put("belt", -3, -2, Wd)
    put("storage", -4, -2, mx=True)
    # side branch: splitter south exit -> wire -> assembler north input
    put("belt", 2, 1, Sd)
    put("belt_corner", 2, 0, Sd)             # S -> W
    put("wiredraw", 1, 0, mx=True)
    put("belt_corner", 0, 0, Wd, my=True)    # W -> S (left turn)
    put("belt", 0, -1, Sd)

    for n, x, y in (("ore_cu", -3.2, 2), ("ore_cu", -2.8, 2.05), ("crushed", -1.2, 2), ("crushed", -0.8, 1.95),
                    ("ingot_cu", 0.85, 2), ("ingot_cu", 1.2, 2.05), ("ingot_cu", 3.0, 2), ("ingot_cu", 4.0, 1.2),
                    ("ingot_cu", 4.02, 0.1), ("ingot_cu", 3.97, -0.9), ("ingot_cu", 2.0, 1.1),
                    ("plate_cu", 2.2, -2), ("plate_cu", 1.3, -2.03), ("coil", 0.0, -0.1), ("coil", 0.02, -0.9),
                    ("gear", -0.8, -2), ("gear", -1.2, -1.97), ("crate", -3.0, -2)):
        item(n, x, y)

    fl = Model("floor")
    fl.box((11.4, 7.4, 0.30), (0, 0, -0.15), "floor", bevel=0.04)
    for x in range(-5, 6):
        fl.box((0.02, 7.0, 0.004), (x + 0.5, 0, 0.002), "light")
    for y in range(-4, 4):
        fl.box((11.0, 0.02, 0.004), (0, y + 0.5, 0.002), "light")
    place(fl.done(), B)
    scene.cycles.samples = 72
    shoot(os.path.join(OUT, "img", "_line.png"), B + Vector((0, 0, 0.6)), 14.2, (2200, 1400), False)
    print("LINE done")

# ============================ ITEM THUMBNAILS ============================
if "items" in ARGS:
    os.makedirs(os.path.join(OUT, "img", "items"), exist_ok=True)
    scene.cycles.samples = 24
    for i, s in enumerate(ITEM_SPECS):
        O = Vector((i * 6.0, -300, 0))
        place(ITEMS[s["key"]], O, s["rz"])
        shoot(os.path.join(OUT, "img", "items", s["key"] + ".png"), O + Vector((0, 0, s["tz"])),
              s["ortho"], (320, 320), True)
    print("ITEMS done", len(ITEM_SPECS))

# ============================ EXPORT FOR ROBLOX ============================
# One FBX per model, with the palette colours baked into vertex colours so each model stays a
# single mesh. Geometry is scaled so that one grid cell is 3 studs. Not yet verified in Studio.
if "export" in ARGS:
    EXPORT = os.path.join(HERE, "export")
    STUDS_PER_CELL = 3.0

    def srgb(key):
        h = PAL[key].lstrip("#")
        return [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]

    def export_mesh(mesh, folder, name):
        me = mesh.copy()
        keys = [m.name for m in me.materials]
        attr = me.color_attributes.new("Col", "BYTE_COLOR", "CORNER")
        for poly in me.polygons:
            r, g, b = srgb(keys[poly.material_index])
            for li in poly.loop_indices:
                attr.data[li].color_srgb = (r, g, b, 1.0)
        me.materials.clear()
        me.transform(Matrix.Scale(STUDS_PER_CELL, 4))
        ob = bpy.data.objects.new(name, me)
        col.objects.link(ob)
        for other in bpy.context.view_layer.objects:
            other.select_set(False)
        ob.select_set(True)
        bpy.context.view_layer.objects.active = ob
        os.makedirs(os.path.join(EXPORT, folder), exist_ok=True)
        bpy.ops.export_scene.fbx(
            filepath=os.path.join(EXPORT, folder, name + ".fbx"), use_selection=True, object_types={"MESH"},
            global_scale=0.01, colors_type="SRGB", mesh_smooth_type="FACE", bake_anim=False,
            add_leaf_bones=False, axis_forward="-Z", axis_up="Y")
        lo = [min(v.co[i] for v in me.vertices) for i in range(3)]
        hi = [max(v.co[i] for v in me.vertices) for i in range(3)]
        col.objects.unlink(ob)
        # Blender is Z-up; Roblox is Y-up. Sizes and centres are given in Roblox axes, in studs,
        # relative to the middle of the model's footprint on the ground.
        return {
            "size": [round(hi[0] - lo[0], 3), round(hi[2] - lo[2], 3), round(hi[1] - lo[1], 3)],
            "center": [round((hi[0] + lo[0]) / 2, 3), round((hi[2] + lo[2]) / 2, 3), round(-(hi[1] + lo[1]) / 2, 3)],
            "triangles": sum(len(p.vertices) - 2 for p in me.polygons),
        }

    index = {"studs_per_cell": STUDS_PER_CELL, "machines": {}, "items": {}}
    for s in SPECS:
        if s["show"]:
            index["machines"][s["key"]] = dict(export_mesh(MESH[s["key"]], "machines", s["key"]),
                                               name=s["ko"], cells=list(s["size"]))
    for s in ITEM_SPECS:
        index["items"][s["key"]] = dict(export_mesh(ITEMS[s["key"]], "items", s["key"]), name=s["ko"])
    json.dump(index, open(os.path.join(EXPORT, "models.json"), "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    print("EXPORT done", len(index["machines"]), len(index["items"]))

# ============================ MESHES FOR THE GAME ============================
# Whole models as real meshes, many to a file, for Studio's 3D importer. Each object is named
# m_<id> (machine), i_<id> (item); the game finds them by that name. Colour is carried two ways so
# that whichever the importer honours can be used: as vertex colours ("vc"), or as a small
# palette picture every face points into ("tex").
if "meshes" in ARGS:
    MESH_OUT = os.path.join(HERE, "export", "game")
    os.makedirs(MESH_OUT, exist_ok=True)
    S = 3.0
    keys_all = list(PAL.keys())
    COLS, SW = 16, 8  # swatches per row, pixels per swatch
    ROWS = (len(keys_all) + COLS - 1) // COLS
    W, H = COLS * SW, max(64, ROWS * SW)
    img = bpy.data.images.new("palette", W, H, alpha=False)
    px = [1.0] * (W * H * 4)
    for n, key in enumerate(keys_all):
        h = PAL[key].lstrip("#")
        rgb = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
        cx, cy = n % COLS, n // COLS
        for yy in range(cy * SW, cy * SW + SW):
            for xx in range(cx * SW, cx * SW + SW):
                o = (yy * W + xx) * 4
                px[o:o + 3] = rgb
    img.pixels = px
    img.filepath_raw = os.path.join(MESH_OUT, "palette.png")
    img.file_format = "PNG"
    img.save()
    pal_mat = bpy.data.materials.new("palette")
    pal_mat.use_nodes = True
    tex_node = pal_mat.node_tree.nodes.new("ShaderNodeTexImage")
    tex_node.image = img
    tex_node.interpolation = "Closest"
    pal_mat.node_tree.links.new(tex_node.outputs["Color"], pal_mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"])

    def swatch_uv(key):
        n = keys_all.index(key)
        return ((n % COLS + 0.5) * SW / W, (n // COLS + 0.5) * SW / H)

    def prepared(mesh, name, mode, shift=(0, 0, 0)):
        me = mesh.copy()
        keys = [m.name for m in me.materials]
        if mode == "vc":
            attr = me.color_attributes.new("Col", "BYTE_COLOR", "CORNER")
            for poly in me.polygons:
                h = PAL[keys[poly.material_index]].lstrip("#")
                r, g, b = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
                for li in poly.loop_indices:
                    attr.data[li].color_srgb = (r, g, b, 1.0)
            me.materials.clear()
        else:
            uv = me.uv_layers.new(name="UVMap")
            for poly in me.polygons:
                u, v = swatch_uv(keys[poly.material_index])
                for li in poly.loop_indices:
                    uv.data[li].uv = (u, v)
            me.materials.clear()
            me.materials.append(pal_mat)
        me.transform(Matrix.Scale(S, 4))
        me.transform(Matrix.Translation(shift))
        ob = bpy.data.objects.new(name, me)
        col.objects.link(ob)
        return ob

    def write(objects, filename):
        for other in bpy.context.view_layer.objects:
            other.select_set(False)
        for ob in objects:
            ob.select_set(True)
        bpy.context.view_layer.objects.active = objects[0]
        bpy.ops.export_scene.fbx(
            filepath=os.path.join(MESH_OUT, filename), use_selection=True, object_types={"MESH"},
            global_scale=0.01, colors_type="SRGB", mesh_smooth_type="FACE", bake_anim=False,
            add_leaf_bones=False, axis_forward="-Z", axis_up="Y", path_mode="COPY", embed_textures=True)
        for ob in objects:
            col.objects.unlink(ob)

    def plain(bm, name, shift):
        """A mesh with no colour of its own: the game tints it (leaves, bark)."""
        me = bpy.data.meshes.new(name)
        bm.to_mesh(me)
        bm.free()
        me.transform(Matrix.Translation(shift))
        ob = bpy.data.objects.new(name, me)
        col.objects.link(ob)
        return ob

    def leaf_blob(seed):
        """A lumpy faceted ball about one unit across; the game stretches it to each mass of leaves."""
        r = random.Random(seed)
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=2, radius=0.5)
        for v in bm.verts:
            v.co *= 1 + r.uniform(-0.2, 0.2)
        bmesh.ops.dissolve_limit(bm, angle_limit=rad(14), verts=bm.verts, edges=bm.edges)
        bmesh.ops.triangulate(bm, faces=bm.faces)
        return bm

    def limb():
        """A six-sided stick one unit long lying along X, a little thinner at the far end."""
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, segments=6, radius1=0.5, radius2=0.4, depth=1.0, cap_ends=True)
        bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(rad(90), 3, "Y"))
        return bm

    if "test" in ARGS:
        # A few things side by side, 6 studs apart along X, to see what the importer does with them.
        write([
            prepared(MESH["smelter"], "vc_smelter", "vc", (0, 0, 0)),
            prepared(MESH["smelter"], "tex_smelter", "tex", (6, 0, 0)),
            prepared(MESH["belt_corner"], "vc_belt_corner", "vc", (12, 0, 0)),
            prepared(MESH["belt_corner"], "tex_belt_corner", "tex", (18, 0, 0)),
            prepared(ITEMS["pick_wood"], "vc_pick_wood", "vc", (23, 0, 0)),
            prepared(ITEMS["pick_wood"], "tex_pick_wood", "tex", (26, 0, 0)),
        ], "import_test.fbx")
        print("MESHES test done")
    else:
        # Everything, laid out on a grid 12 studs apart so each can be told from its neighbours and
        # so the importer's scale and turn can be worked out afterwards from where things landed.
        # `info` records, in Roblox axes and studs, where each object was put and where the middle
        # of its mesh lies relative to its own origin (the middle of its footprint on the ground).
        objects, info, n = [], {}, 0

        def spot():
            return ((n % 15) * 12.0, (n // 15) * 12.0, 0.0)

        def note(name, ob, at):
            xs = [v.co for v in ob.data.vertices]
            lo = [min(c[i] for c in xs) - at[i] for i in range(3)]
            hi = [max(c[i] for c in xs) - at[i] for i in range(3)]
            info[name] = {
                "at": [at[0], at[2], -at[1]],
                "center": [round((hi[0] + lo[0]) / 2, 4), round((hi[2] + lo[2]) / 2, 4), round(-(hi[1] + lo[1]) / 2, 4)],
                "size": [round(hi[0] - lo[0], 4), round(hi[2] - lo[2], 4), round(hi[1] - lo[1], 4)],
            }
            objects.append(ob)

        for s in SPECS:
            at = spot()
            note("m_" + s["key"], prepared(MESH[s["key"]], "m_" + s["key"], "tex", at), at)
            n += 1
        for s in ITEM_SPECS:
            at = spot()
            note("i_" + s["key"], prepared(ITEMS[s["key"]], "i_" + s["key"], "tex", at), at)
            n += 1
        for k in (1, 2, 3):
            at = spot()
            note("t_leaf" + str(k), plain(leaf_blob(40 + k), "t_leaf" + str(k), at), at)
            n += 1
        at = spot()
        note("t_limb", plain(limb(), "t_limb", at), at)
        n += 1
        write(objects, "models.fbx")
        json.dump(info, open(os.path.join(MESH_OUT, "models_info.json"), "w", encoding="utf-8", newline="\n"), indent=0)
        print("MESHES done", len(info), "objects")

# ============================ GAME DATA ============================
# The primitive lists, converted to Roblox axes (Y up) and studs, for game/tools/gen_data.py.
if "gamedata" in ARGS:
    S = 3.0  # studs per cell
    TO_RBX = Matrix(((1, 0, 0), (0, 0, 1), (0, -1, 0)))
    TURN_X_TO_Y = Matrix(((0, -1, 0), (1, 0, 0), (0, 0, 1)))  # Roblox cylinders lie along X
    used = []

    def colour_index(mk):
        if mk not in used:
            used.append(mk)
        return used.index(mk)

    def convert(prims):
        out = []
        for shape, size, mx, mk in prims:
            rot = TO_RBX @ mx.to_3x3().normalized() @ TO_RBX.transposed()
            pos = TO_RBX @ mx.to_translation() * S
            if shape == "b":
                dims = (size[0] * S, size[2] * S, size[1] * S)
            elif shape == "c":
                rot = rot @ TURN_X_TO_Y
                dims = (size[0] * S, size[1] * S, size[2] * S)
            else:
                dims = (size[0] * S,) * 3
            if min(dims) < 0.02:
                continue
            row = [{"b": 0, "c": 1, "s": 2}[shape], *dims, pos.x, pos.y - S / 2, pos.z]
            row += [rot[i][j] for i in range(3) for j in range(3)]
            out.append([round(v, 3) for v in row] + [colour_index(mk)])
        return out

    game = {"machines": {}, "items": {}}
    for s in SPECS:
        prims = PRIMS[s["key"]]
        top = max((mx.to_translation().z + size[2] / 2 for _, size, mx, _ in prims), default=1.0)
        game["machines"][s["key"]] = {
            "name": s["ko"], "family": s["fam"], "note": s["recipe"], "cells": list(s["size"]),
            "ports": [[side, kind, off] for side, kind, off in s["ports"]],
            "height": round(top * S, 2), "chassis": s["chassis"], "prims": convert(prims),
        }
    for s in ITEM_SPECS:
        prims = PRIMS["item_" + s["key"]]
        lo = [min(mx.to_translation()[i] - size[i] / 2 for _, size, mx, _ in prims) for i in range(3)]
        hi = [max(mx.to_translation()[i] + size[i] / 2 for _, size, mx, _ in prims) for i in range(3)]
        volume = {}
        for shape, size, mx, mk in prims:
            volume[mk] = volume.get(mk, 0) + size[0] * size[1] * size[2]
        main = max(volume, key=volume.get)
        game["items"][s["key"]] = {
            "name": s["ko"], "category": s["cat"], "colour": colour_index(main), "prims": convert(prims),
            "size": [round(max(0.5, min(1.6, (hi[i] - lo[i]) * S)), 2) for i in (0, 2, 1)],
            "ball": all(shape == "s" for shape, _, _, _ in prims),
        }
    game["palette"] = [{"key": mk, "hex": PAL[mk], "neon": mk in EMIT} for mk in used]
    out_dir = os.path.join(os.path.dirname(HERE), "game", "tools")
    os.makedirs(out_dir, exist_ok=True)
    json.dump(game, open(os.path.join(out_dir, "modeldata.json"), "w", encoding="utf-8", newline="\n"), ensure_ascii=False)
    print("GAMEDATA done", len(game["machines"]), len(game["items"]), len(used), "colours",
          sum(len(m["prims"]) for m in game["machines"].values()), "parts")

meta = [{k: s[k] for k in ("key", "ko", "fam", "recipe", "ports", "size", "tris", "colors", "ins", "outs")}
        for s in SPECS if s["show"]]
items_meta = [{k: s[k] for k in ("key", "ko", "cat", "tris")} for s in ITEM_SPECS]
json.dump({"machines": meta, "items": items_meta}, open(os.path.join(OUT, "catalog.json"), "w", encoding="utf-8", newline="\n"),
          ensure_ascii=False, indent=1)

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "factorykit.blend"))
print("ALL done")
