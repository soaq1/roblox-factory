# v2 models, kept beside v1 until a style is chosen. Nothing in the game reads these yet.
# Run:  Blender --background --python art/factorykit_v2.py -- [v2thumbs] [v2line] [eevee] [only=key,key]
import sys, os, json, math, importlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import bpy
import factorykit as fk          # v1: Model, palette, item meshes, lights, camera
from mathutils import Vector
from v2 import kit

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
    fk.scene.cycles.samples = 32
    for i, s in enumerate(kit.SPECS2):
        if only and s["key"] not in only:
            continue
        O = Vector((i * 60.0, -900, 0))
        fk.place(MESH[s["key"]], O)
        if s["items"]:
            ins, outs = list(s["ins"]), list(s["outs"])
            for side, kind, off in s["ports"]:
                name = (ins.pop(0) if ins else None) if kind == "in" else (outs.pop(0) if outs else None)
                if name and name in fk.ITEMS:
                    fk.place(fk.ITEMS[name], O + stub_spot(s, side, off), fk.rng.uniform(0, 1.2))
        centre, extent = fit(MESH[s["key"]])
        fk.shoot(os.path.join(IMG, s["key"] + ".png"), O + centre, extent * 1.12, (640, 640), True)
        print("V2THUMB", s["key"])

# ============================ CONNECTED FACTORY ============================
if "v2line" in ARGS:
    B = Vector((0, 900, 0))
    E_, S_, N_, W_ = 0.0, -math.pi / 2, math.pi / 2, math.pi

    def put(key, x, y, rz=0.0, mx=False, my=False):
        return fk.place(MESH[key], B + Vector((x, y, 0)), rz, mx, my)

    def item(name, x, y):
        if name in fk.ITEMS:
            fk.place(fk.ITEMS[name], B + Vector((x, y, kit.BELT_Z)), fk.rng.uniform(0, 1.5))

    # iron line along the back, flowing east
    put("extractor_fe", -6.5, 5)
    put("belt", -5, 5)
    put("crusher", -3, 5)
    put("belt", -1, 5)
    put("smelter", 1, 5)
    put("sensor", 3, 5)
    put("splitter", 4, 5)
    put("belt", 5, 5)
    put("press", 7, 5)
    put("belt", 9, 5)
    put("assembler", 11, 4.5)
    put("belt", 13, 5)
    put("storage", 15, 5)
    # the splitter's side exit runs down to the blast furnace
    put("belt", 4, 4, S_)
    put("belt", 4, 3, S_)
    put("belt_corner", 4, 2, S_, my=True)     # coming south, leaving east
    put("belt", 5, 2)
    put("blast", 7, 2)
    put("belt", 9, 2)
    put("packer", 11, 2)
    put("belt", 13, 2)
    put("chest", 14.2, 2)
    # coal comes in from the south
    put("extractor_coal", 4.5, 0)
    put("belt", 6, 0)
    put("belt_corner", 7, 0, my=True)         # coming east, leaving north
    # copper wire for the assembler
    put("belt", 11, 3, N_)
    # things that stand on their own
    put("generator", -4, 1.5)
    put("pole", -1.5, 0)
    put("pole", 1.5, -1)
    put("windturbine", -7, -1)
    put("wb_machine", -5.5, -1.2)
    put("wb_basic", -3.2, -1.3)
    put("beacon", 3, 6)
    put("battery", -1.5, 2)
    put("vending", 15.5, 1.6)

    for n, x, y in (("ore_fe", -5.5, 5), ("ore_fe", -5.0, 5.05), ("crushed", -1.2, 5), ("crushed", -0.7, 4.95),
                    ("ingot_fe", 2.7, 5), ("ingot_fe", 3.3, 5.03), ("ingot_fe", 5.2, 5), ("ingot_fe", 4.0, 3.6),
                    ("ingot_fe", 4.02, 2.8), ("ingot_fe", 5.1, 2.0), ("plate_fe", 8.8, 5), ("plate_fe", 9.3, 4.97),
                    ("coal", 5.8, 0.0), ("coal", 6.3, 0.03), ("coal", 7.0, 0.2), ("ingot_steel", 8.8, 2.0),
                    ("ingot_steel", 9.3, 2.02), ("gear", 12.8, 5), ("gear", 13.3, 5.03), ("crate", 12.9, 2.0),
                    ("coil", 11.0, 3.1), ("coil", 11.02, 2.7)):
        item(n, x, y)

    # a figure for scale: a Roblox character is about 5 studs tall, a grid cell is 3 studs
    fig = fk.Model("figure")
    for sx in (-1, 1):
        fig.box((0.30, 0.30, 0.64), (sx * 0.16, 0, 0.32), "g5")
        fig.box((0.28, 0.30, 0.62), (sx * 0.48, 0, 0.96), "sand")
    fig.box((0.64, 0.32, 0.64), (0, 0, 0.96), "water")
    fig.cyl(0.21, 0.36, (0, 0, 1.47), "sand", seg=10)
    fk.place(fig.done(), B + Vector((1.0, 3.4, 0)), -0.6)

    fl = fk.Model("floor2")
    fl.box((26.4, 10.4, 0.30), (4.5, 2.5, -0.15), "floor", bevel=0.04)
    for x in range(-8, 18):
        fl.box((0.02, 10.0, 0.004), (x + 0.5, 2.5, 0.002), "light")
    for y in range(-3, 8):
        fl.box((26.0, 0.02, 0.004), (4.5, y + 0.5, 0.002), "light")
    fk.place(fl.done(), B)
    fk.scene.cycles.samples = 72
    fk.shoot(os.path.join(IMG, "_line.png"), B + Vector((4.5, 2.5, 1.1)), 27.0, (2400, 1250), False)
    print("V2LINE done")

meta = [{k: s[k] for k in ("key", "ko", "fam", "recipe", "ports", "size", "tris", "colors", "height", "v1size")}
        for s in kit.SPECS2]
json.dump({"machines": meta}, open(os.path.join(fk.OUT, "v2.json"), "w", encoding="utf-8", newline="\n"),
          ensure_ascii=False, indent=1)
print("V2 done", len(meta))
