# v2 models, kept beside v1 until a style is chosen. Nothing in the game reads these yet.
# Run:  Blender --background --python art/factorykit_v2.py -- [v2thumbs] [v2line] [eevee] [only=key,key]
import sys, os, json, math, importlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import bpy
import factorykit as fk          # v1: Model, palette, item meshes, lights, camera
from mathutils import Vector
from v2 import kit, base
base.set_style("d")              # every machine stands on foundation D

# Family modules register their models on import; this order is the catalog order.
for name in ("transport", "devices", "supply", "process", "combine", "power", "hand", "ultimate"):
    try:
        importlib.import_module("v2." + name)
    except ModuleNotFoundError as e:
        if e.name != "v2." + name:
            raise

ARGS = fk.ARGS
IMG = os.path.join(fk.OUT, "img", "v2")
os.makedirs(IMG, exist_ok=True)

MESH = {}
for s in kit.SPECS2:
    m = fk.Model("v2_" + s["key"])
    s["fn"](m)
    MESH[s["key"]] = m.done()
    s["tris"], s["colors"] = m.tris, len(m.mats)
    zs = [v.co.z for v in MESH[s["key"]].vertices]
    s["height"] = round(max(zs), 2)
    print(f"V2 {s['key']:16s} tris={m.tris:5d} colors={len(m.mats):2d} height={s['height']}")

# ---- framing: fit each model to the picture from the fixed catalog camera angle ----
CAM = Vector((14, -14, 12.5))
F = (-CAM).normalized()
R = F.cross(Vector((0, 0, 1))).normalized()
U = R.cross(F)


def fit(mesh):
    xs = [v.co.dot(R) for v in mesh.vertices]
    ys = [v.co.dot(U) for v in mesh.vertices]
    ds = [v.co.dot(F) for v in mesh.vertices]
    centre = R * (min(xs) + max(xs)) / 2 + U * (min(ys) + max(ys)) / 2 + F * (min(ds) + max(ds)) / 2
    return centre, max(max(xs) - min(xs), max(ys) - min(ys))


def stub_spot(s, side, off):
    """Where an item sits on a machine's own stub, just inside the footprint edge."""
    sx, sy = s["size"]
    inset = 0.34
    if side == "E":
        return Vector((sx / 2 - inset, off, kit.BELT_Z))
    if side == "W":
        return Vector((-sx / 2 + inset, off, kit.BELT_Z))
    if side == "N":
        return Vector((off, sy / 2 - inset, kit.BELT_Z))
    return Vector((off, -sy / 2 + inset, kit.BELT_Z))


if "v2thumbs" in ARGS:
    only = set()
    for a in ARGS:
        if a.startswith("only="):
            only |= set(a.split("=", 1)[1].split(","))
    out = next((os.path.expanduser(a.split("=", 1)[1]) for a in ARGS if a.startswith("out=")), IMG)
    res = int(next((a.split("=", 1)[1] for a in ARGS if a.startswith("res=")), 640))
    os.makedirs(out, exist_ok=True)
    for i, s in enumerate(kit.SPECS2):
        if only and s["key"] not in only:
            continue
        O = Vector((i * 60.0, -900, 0))
        fk.place(MESH[s["key"]], O)
        spots = []
        if s["items"]:
            ins, outs = list(s["ins"]), list(s["outs"])
            for side, kind, off in s["ports"]:
                name = (ins.pop(0) if ins else None) if kind == "in" else (outs.pop(0) if outs else None)
                if name and name in fk.ITEMS:
                    spot = stub_spot(s, side, off)
                    spot.z = base.BZ
                    fk.place(fk.ITEMS[name], O + spot, fk.rng.uniform(0, 1.2))
                    spots.append(spot + Vector((0, 0, 0.2)))
        base.shoot_fit(MESH[s["key"]], O, os.path.join(out, s["key"] + ".png"), res=res, extra=spots)
        print("V2THUMB", s["key"])

# ============================ CONNECTED FACTORY ============================
if "v2line" in ARGS:
    B = Vector((0, 900, 0))
    E_, S_, N_, W_ = 0.0, -math.pi / 2, math.pi / 2, math.pi

    def put(key, x, y, rz=0.0, mx=False, my=False):
        return fk.place(MESH[key], B + Vector((x, y, 0)), rz, mx, my)

    def item(name, x, y):
        if name in fk.ITEMS:
            fk.place(fk.ITEMS[name], B + Vector((x, y, base.BZ)), fk.rng.uniform(0, 1.5))

    # iron line along the back, flowing east. A 3x1 machine is centred on a cell; a 2x1 one between two.
    put("extractor_fe", -7.5, 6)
    put("belt", -6, 6)
    put("crusher", -4, 6)
    put("belt", -2, 6)
    put("smelter", 0, 6)
    put("belt", 2, 6)
    put("splitter", 3, 6)
    put("belt", 4, 6)
    put("press", 6, 6)
    put("belt", 8, 6)
    put("assembler", 10, 6)
    put("belt", 12, 6)
    put("storage", 14, 6)
    # the splitter's side exit runs south, turns east and feeds the blast furnace
    put("belt", 3, 5, S_)
    put("belt", 3, 4, S_)
    put("belt_corner", 3, 3, S_, my=True)     # coming south, leaving east
    put("belt", 4, 3)
    put("blast", 6, 3)
    put("belt", 8, 3)
    put("packer", 10, 3)
    put("belt", 12, 3)
    put("chest", 13.1, 3)
    # coal comes round to the blast furnace's side mouth
    put("extractor_coal", 4.5, 0)
    put("belt_corner", 6, 0, my=True)         # coming east, leaving north
    put("belt", 6, 1, N_)
    put("belt", 6, 2, N_)
    # things that stand on their own
    put("generator", -4.5, 2.5)
    put("pole", -2, 1.5)
    put("pole", 1, 0.5)
    put("windturbine", -8.5, -1.5)
    put("battery", -6.5, 3)
    put("wb_machine", -4.5, -1.2)
    put("wb_basic", -2, -1.3)
    put("campfire", 0, -1.4)
    put("vending", 14, 1.2)
    put("beacon", 2, 7.4)

    for n, x, y in (("ore_fe", -6.1, 6), ("crushed", -2.1, 6), ("ingot_fe", 2.0, 6), ("ingot_fe", 4.0, 6.03),
                    ("ingot_fe", 3.0, 4.6), ("ingot_fe", 4.0, 3.0), ("plate_fe", 8.0, 6), ("gear", 12.0, 6),
                    ("coal", 6.0, 1.0), ("coal", 6.03, 1.9), ("ingot_steel", 8.0, 3.0), ("crate", 12.0, 3.0)):
        item(n, x, y)

    # a figure for scale: a Roblox character is about 5 studs tall, a grid cell is 3 studs
    fig = fk.Model("figure")
    for sx in (-1, 1):
        fig.box((0.30, 0.30, 0.64), (sx * 0.16, 0, 0.32), "g5")
        fig.box((0.28, 0.30, 0.62), (sx * 0.48, 0, 0.96), "sand")
    fig.box((0.64, 0.32, 0.64), (0, 0, 0.96), "water")
    fig.cyl(0.21, 0.36, (0, 0, 1.47), "sand", seg=10)
    fk.place(fig.done(), B + Vector((0.6, 4.4, 0)), -0.6)

    fl = fk.Model("floor2")
    fl.box((26.4, 12.4, 0.30), (3.3, 2.8, -0.15), "floor", bevel=0.04)
    for x in range(-10, 17):
        fl.box((0.02, 12.0, 0.004), (x + 0.5, 2.8, 0.002), "light")
    for y in range(-4, 9):
        fl.box((26.0, 0.02, 0.004), (3.3, y + 0.5, 0.002), "light")
    fk.place(fl.done(), B)
    base.hero_light()
    fk.scene.cycles.samples = 72
    fk.cd.ortho_scale = 27.5
    c = B + Vector((3.3, 2.8, 0.9))
    fk.aim(fk.cam, c + base.ISO * 80, c)
    fk.scene.render.film_transparent = False
    fk.scene.render.resolution_x, fk.scene.render.resolution_y = 2400, 1350
    fk.scene.render.filepath = os.path.join(IMG, "_line.png")
    bpy.ops.render.render(write_still=True)
    print("V2LINE done")

meta = [{k: s[k] for k in ("key", "ko", "fam", "recipe", "ports", "size", "tris", "colors", "height", "v1size")}
        for s in kit.SPECS2]
json.dump({"machines": meta}, open(os.path.join(fk.OUT, "v2.json"), "w", encoding="utf-8", newline="\n"),
          ensure_ascii=False, indent=1)
print("V2 done", len(meta))
