# Writes models to one FBX file for Studio's 3D importer.
#   Blender --background --python art/export_fbx.py -- out=<file.fbx> [gap=<studs>] <name> <name> ...
# Each model becomes one object named after it, in studs, standing side by side. Colour is a small
# palette picture every face points into (vertex colours come into Studio too dark); the picture is
# written beside the file and also packed into it.
# Studio centres every mesh on the middle of its bounding box and turns it half a turn about the
# vertical. So <file>_info.json records, for each model, its size and where its own origin (the foot
# it stands on) ends up inside the imported MeshPart, in the MeshPart's axes.
import sys, os, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
args = sys.argv[sys.argv.index("--") + 1:]
out = os.path.abspath(next(a[4:] for a in args if a.startswith("out=")))
names = [a for a in args if "=" not in a]
gap = next((float(a[4:]) for a in args if a.startswith("gap=")), 4.0)
sys.argv = sys.argv[:1] + ["--", "none"]
import bpy  # noqa: E402
from mathutils import Matrix  # noqa: E402
import factorykit as fk  # noqa: E402
from v2 import base, hero, works, pairs, bay, set2  # noqa: E402,F401
base.set_style("d")

STUDS, GAP, SW = 3.0, gap, 16          # studs to a model unit, studs between models, pixels to a swatch
models = []
for name in names:
    m = fk.Model(name)
    hero.HEROES[name](m)
    models.append((name, m.done(), list(m.mats)))
keys = sorted({k for _, _, mats in models for k in mats})
cols = 1
while cols * cols < len(keys):
    cols *= 2
size = cols * SW
img = bpy.data.images.new("palette", size, size, alpha=False)
px = [1.0] * (size * size * 4)
for n, key in enumerate(keys):
    h = fk.PAL[key].lstrip("#")
    rgb = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    for yy in range(n // cols * SW, n // cols * SW + SW):
        for xx in range(n % cols * SW, n % cols * SW + SW):
            o = (yy * size + xx) * 4
            px[o:o + 3] = rgb
img.pixels = px
img.filepath_raw = os.path.splitext(out)[0] + "_palette.png"
img.file_format = "PNG"
img.save()
mat = bpy.data.materials.new("palette")
mat.use_nodes = True
tex = mat.node_tree.nodes.new("ShaderNodeTexImage")
tex.image = img
tex.interpolation = "Closest"
bsdf = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
mat.node_tree.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])

for ob in list(bpy.context.scene.collection.all_objects):
    bpy.data.objects.remove(ob)
objects, info = [], {}
for i, (name, mesh, mats) in enumerate(models):
    me = mesh.copy()
    uv = me.uv_layers.new(name="UVMap")
    for poly in me.polygons:
        n = keys.index(mats[poly.material_index])
        for li in poly.loop_indices:
            uv.data[li].uv = ((n % cols + 0.5) / cols, (n // cols + 0.5) / cols)
    me.materials.clear()
    me.materials.append(mat)
    me.transform(Matrix.Scale(STUDS, 4))
    lo = [min(v.co[k] for v in me.vertices) for k in range(3)]
    hi = [max(v.co[k] for v in me.vertices) for k in range(3)]
    mid = [(lo[k] + hi[k]) / 2 for k in range(3)]
    info[name] = {"size": [round(hi[0] - lo[0], 3), round(hi[2] - lo[2], 3), round(hi[1] - lo[1], 3)],
                  "origin": [round(mid[0], 3), round(-mid[2], 3), round(-mid[1], 3)], "faces": len(me.polygons)}
    me.transform(Matrix.Translation(((i - (len(models) - 1) / 2) * GAP, 0, 0)))
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    ob.select_set(True)
    objects.append(ob)
bpy.context.view_layer.objects.active = objects[0]
bpy.ops.export_scene.fbx(
    filepath=out, use_selection=True, object_types={"MESH"}, global_scale=0.01, mesh_smooth_type="FACE",
    bake_anim=False, add_leaf_bones=False, axis_forward="-Z", axis_up="Y", path_mode="COPY", embed_textures=True)
json.dump(info, open(os.path.splitext(out)[0] + "_info.json", "w", newline="\n"), indent=1)
print("INFO", info)
print("FBX", out, [(n, len(me.polygons)) for n, me, _ in models], keys)
