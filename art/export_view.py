# A few v2 machines as meshes for Studio's 3D importer, to look at inside the game before deciding
# anything. Not the game's model pipeline: nothing here is read by the game.
# Run:  Blender --background --python art/export_view.py -- [file=<name>] [names]
# Writes art/export/view/view_models.fbx (with palette.png inside it) and view_info.json.
#
# Each machine is one object named v_<name>, coloured through a small palette picture as the game's
# own meshes are (art/factorykit.py, "meshes"). Faces that should glow are split off into objects
# named v_<name>__<palette key>, so that they can be given the Neon material in Studio.
# One cell is 3 studs. The machines stand 18 studs apart along X.
import sys, os, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
sys.argv = sys.argv[:1] + ["--", "none"]          # keep factorykit from rendering its own catalog

import bpy, bmesh
from mathutils import Matrix
import factorykit as fk
from v2 import base, hero, works, pairs, bay, set2  # noqa: F401  (set2 registers its machines in hero.HEROES)

base.set_style("d")
NAMES = [a for a in args if "=" not in a] or ["smelter8", "crusher3", "former2", "assembler4"]
FILE = next((a.split("=", 1)[1] for a in args if a.startswith("file=")), "view")          # file=<name> writes <name>_models.fbx and <name>_info.json
GLOW = ("h_glow", "h_core", "h_neon")
OUT = os.path.join(HERE, "export", "view")
os.makedirs(OUT, exist_ok=True)
S, STEP = 3.0, 18.0

keys_all = list(fk.PAL.keys())
COLS, SW = 16, 8
ROWS = (len(keys_all) + COLS - 1) // COLS
W, H = COLS * SW, max(64, ROWS * SW)
img = bpy.data.images.new("palette", W, H, alpha=False)
px = [1.0] * (W * H * 4)
for n, key in enumerate(keys_all):
    h = fk.PAL[key].lstrip("#")
    rgb = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    for yy in range((n // COLS) * SW, (n // COLS) * SW + SW):
        for xx in range((n % COLS) * SW, (n % COLS) * SW + SW):
            o = (yy * W + xx) * 4
            px[o:o + 3] = rgb
img.pixels = px
img.filepath_raw = os.path.join(OUT, "palette.png")
img.file_format = "PNG"
img.save()
pal_mat = bpy.data.materials.new("palette")
pal_mat.use_nodes = True
tex = pal_mat.node_tree.nodes.new("ShaderNodeTexImage")
tex.image = img
tex.interpolation = "Closest"
bsdf = next(n for n in pal_mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
pal_mat.node_tree.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])


def swatch_uv(key):
    n = keys_all.index(key)
    return ((n % COLS + 0.5) * SW / W, (n // COLS + 0.5) * SW / H)


def part(mesh, name, keep, shift):
    """The faces of `mesh` whose palette key passes `keep`, as an object pointing into the palette picture."""
    keys = [m.name for m in mesh.materials]
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if not keep(keys[f.material_index])], context="FACES")
    if not bm.faces:
        bm.free()
        return None
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
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
    fk.col.objects.link(ob)
    return ob


objects, info = [], {}
for i, name in enumerate(NAMES):
    m = fk.Model(name)
    hero.HEROES[name](m)
    mesh = m.done()
    at = (i * STEP, 0.0, 0.0)
    body = part(mesh, "v_" + name, lambda k: k not in GLOW, at)
    objects.append(body)
    xs = [v.co for v in body.data.vertices]
    lo = [min(c[j] for c in xs) - at[j] for j in range(3)]
    hi = [max(c[j] for c in xs) - at[j] for j in range(3)]
    neon = {}
    for key in GLOW:
        ob = part(mesh, f"v_{name}__{key}", lambda k, key=key: k == key, at)
        if ob:
            objects.append(ob)
            neon[ob.name] = fk.PAL[key]
    info["v_" + name] = {                                      # in Roblox axes and studs
        "at": [at[0], at[2], -at[1]],
        "center": [round((hi[0] + lo[0]) / 2, 3), round((hi[2] + lo[2]) / 2, 3), round(-(hi[1] + lo[1]) / 2, 3)],
        "size": [round(hi[0] - lo[0], 3), round(hi[2] - lo[2], 3), round(hi[1] - lo[1], 3)],
        "tris": m.tris, "neon": neon,
    }

for other in bpy.context.view_layer.objects:
    other.select_set(False)
for ob in objects:
    ob.select_set(True)
bpy.context.view_layer.objects.active = objects[0]
bpy.ops.export_scene.fbx(
    filepath=os.path.join(OUT, FILE + "_models.fbx"), use_selection=True, object_types={"MESH"},
    global_scale=0.01, colors_type="SRGB", mesh_smooth_type="FACE", bake_anim=False,
    add_leaf_bones=False, axis_forward="-Z", axis_up="Y", path_mode="COPY", embed_textures=True)
json.dump(info, open(os.path.join(OUT, FILE + "_info.json"), "w", encoding="utf-8", newline="\n"), indent=1)
print("VIEW done", {k: (v["size"], v["tris"]) for k, v in info.items()})
