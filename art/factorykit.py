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
    "pcb": "#2f9e5b", "slurry": "#9aa6ad", "white": "#f2f0ea", "floor": "#d9dcdf",
}
EMIT = {"glow": 3.0, "spark": 1.5}
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
        m.prism([(y + o, z) for y, z in frame], d - 0.10, d, "X", "light")
        m.prism([(y + o, z) for y, z in lip], d - 0.06, d - 0.01, "X",
                "accent" if kind == "in" else "out")
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
@machine("drill", "채굴 드릴", "공급", "광맥 위에 놓으면 광석(구리, 철, 석탄, 돌)을 캐냄",
         ports=(E_OUT,), outs=("ore_cu",), ortho=5.0, tz=1.0)
def _drill(m, T):
    vent(m)
    bolts(m)
    m.cyl(0.29, 0.04, (0, 0, T + 0.02), "mid", seg=10)
    m.cyl(0.23, 0.01, (0, 0, T + 0.043), "hole", seg=10)
    fz = gantry(m, T, 0.98)
    for s in (-1, 1):
        m.box((0.74, 0.04, 0.04), (0, s * 0.37, T + 0.50), "mid")
        m.box((0.04, 0.74, 0.04), (s * 0.37, 0, T + 0.50), "mid")
    m.box((0.48, 0.48, 0.30), (0, 0, fz - 0.17), "body", bevel=0.05)
    m.box((0.54, 0.54, 0.07), (0, 0, fz + 0.06), "light", bevel=0.015)
    m.cyl(0.07, 0.10, (0.12, 0.12, fz + 0.14), "mid", seg=6)
    z = fz - 0.32
    m.cyl(0.05, 0.22, (0, 0, z - 0.11), "mid", seg=8)
    z -= 0.22
    for h, r_top, r_bot, mk in ((0.15, 0.22, 0.15, "red"), (0.13, 0.17, 0.10, "mid"),
                                (0.12, 0.12, 0.02, "red")):
        m.cyl(r_bot, h, (0, 0, z - h / 2), mk, seg=8, r2=r_top)
        z -= h


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


@machine("smelter", "제련로", "변환", "광석 → 주괴 (구리, 철)",
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


@machine("seller", "판매기", "포장·판매", "들어온 아이템을 코인으로 바꿈",
         ports=(W_IN,), ins=("crate",), ortho=4.9, tz=0.95)
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


# ============================ ITEMS ============================
def build_items():
    items = {}

    def it(name, fn):
        m = Model("item_" + name)
        fn(m)
        items[name] = m.done()

    def ore(nug):
        def f(m):
            m.ico(0.13, (0, 0, 0.10), "stone", squash=0.8, jitter=0.18)
            m.ico(0.05, (0.07, -0.04, 0.15), nug, jitter=0.2)
            m.ico(0.04, (-0.06, 0.05, 0.14), nug, jitter=0.2)
        return f

    def ingot(mk):
        return lambda m: m.box((0.28, 0.14, 0.09), (0, 0, 0.045), mk, bevel=0.012, taper=0.78)

    def bar(mk, band):
        return lambda m: barrel(m, (0, 0, 0), mk, r=0.10, h=0.26, band=band)

    def pile(mk):
        def f(m):
            for (x, y, r) in ((0, 0, 0.07), (0.09, 0.03, 0.055), (-0.07, 0.06, 0.05), (0.01, -0.08, 0.05)):
                m.ico(r, (x, y, r * 0.8), mk, squash=0.85, jitter=0.2)
        return f

    it("ore_cu", ore("copper"))
    it("ore_fe", ore("iron"))
    it("coal", lambda m: m.ico(0.12, (0, 0, 0.09), "coal", squash=0.8, jitter=0.2))
    it("stone", lambda m: m.ico(0.13, (0, 0, 0.10), "stone", squash=0.8, jitter=0.18))
    it("crushed", pile("copper"))
    it("clean", pile("gold"))
    it("sand", lambda m: m.cyl(0.14, 0.12, (0, 0, 0.06), "sand", seg=8, r2=0.03))
    it("ingot_cu", ingot("copper"))
    it("ingot_fe", ingot("iron"))
    it("ingot_steel", ingot("steel"))
    it("plate_cu", lambda m: m.box((0.26, 0.22, 0.035), (0, 0, 0.018), "copper", bevel=0.008))
    it("coil", lambda m: (m.cyl(0.11, 0.10, (0, 0, 0.05), "copper", seg=10),
                          m.cyl(0.05, 0.11, (0, 0, 0.05), "hole", seg=8)))
    it("gear", lambda m: m.gear(0.13, 0.06, (0, 0, 0.03), "iron", teeth=8, axis="Z"))
    it("board", lambda m: (m.box((0.24, 0.20, 0.025), (0, 0, 0.013), "pcb"),
                           m.box((0.08, 0.08, 0.03), (0.03, 0.02, 0.035), "hole"),
                           m.box((0.14, 0.02, 0.012), (-0.03, -0.06, 0.03), "gold")))
    it("plastic", lambda m: m.box((0.20, 0.20, 0.10), (0, 0, 0.05), "white", bevel=0.03))
    it("glass", lambda m: m.box((0.24, 0.03, 0.22), (0, 0, 0.11), "glass", rot=(rad(12), 0, 0)))
    it("log", lambda m: (m.cyl(0.09, 0.34, (0, 0, 0.09), "wood_dark", seg=8, axis="Y"),
                         m.cyl(0.07, 0.35, (0, 0, 0.09), "wood_light", seg=8, axis="Y")))
    it("plank", lambda m: m.box((0.14, 0.34, 0.045), (0, 0, 0.023), "wood"))
    it("stone_block", lambda m: m.box((0.20, 0.20, 0.20), (0, 0, 0.10), "stone", bevel=0.02))
    it("concrete", lambda m: m.box((0.22, 0.22, 0.16), (0, 0, 0.08), "slurry", bevel=0.02))
    it("wheat", lambda m: [m.box((0.035, 0.035, 0.26), (x, y, 0.13), "wheat_head", taper=0.5)
                           for x, y in ((0, 0), (0.05, 0.03), (-0.04, 0.04), (0.02, -0.05))])
    it("flour", lambda m: (m.box((0.18, 0.14, 0.20), (0, 0, 0.10), "cream", bevel=0.04, taper=0.8),
                           m.box((0.10, 0.08, 0.04), (0, 0, 0.21), "wood")))
    it("bread", lambda m: m.box((0.24, 0.13, 0.11), (0, 0, 0.055), "bread", bevel=0.04))
    it("barrel_water", bar("water", "mid"))
    it("barrel_oil", bar("oil", "red"))
    it("barrel_fuel", bar("red", "dark"))
    it("crate", lambda m: crate(m, (0, 0, 0), s=0.26))
    it("motor", lambda m: (m.cyl(0.10, 0.24, (0, 0, 0.11), "steel", seg=8, axis="X"),
                           m.cyl(0.11, 0.06, (0, 0, 0.11), "copper", seg=8, axis="X"),
                           m.cyl(0.03, 0.34, (0, 0, 0.11), "light", seg=6, axis="X"),
                           m.box((0.16, 0.16, 0.03), (0, 0, 0.015), "dark")))
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
    for i, s in enumerate(shown):
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
    items_row = list(ITEMS)
    per = (len(items_row) + 1) // 2
    for i, name in enumerate(items_row):
        r, c = divmod(i, per)
        u = (c - (per - 1) / 2) * 0.46
        v = (0.5 - r) * 0.95
        place(ITEMS[name], (u - v, -80 + u + v, 0))
    shoot(os.path.join(OUT, "img", "_items.png"), (0, -80, 0.1), 10.6, (2000, 520), True)
    meta = [{k: s[k] for k in ("key", "ko", "fam", "recipe", "ports", "size", "tris", "colors", "ins", "outs")}
            for s in shown]
    json.dump({"machines": meta, "items": items_row}, open(os.path.join(OUT, "catalog.json"), "w"),
              ensure_ascii=False, indent=1)

# ============================ CONNECTED LINE ============================
if "line" in ARGS:
    B = Vector((0, 200, 0))
    E, Wd, Sd = 0.0, math.pi, -math.pi / 2

    def put(key, x, y, rz=0.0, mx=False, my=False):
        return place(MESH[key], B + Vector((x, y, 0)), rz, mx, my)

    def item(name, x, y):
        place(ITEMS[name], B + Vector((x, y, 0.30)), rng.uniform(0, 1.5))

    # top row, flowing east
    put("drill", -4, 2)
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
    put("seller", -4, -2, mx=True)
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

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "factorykit.blend"))
print("ALL done")
