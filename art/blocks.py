# Basic blocks: plain cubes with small 32px textures (12 triangles each).
# The style is provisional. Writes textures to art/textures and thumbnails to art/catalog/img/blocks.
# Run:  Blender --background --python blocks.py
import bpy, bmesh, math, os, random, json
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
TEX = os.path.join(HERE, "textures")
OUT = os.path.join(HERE, "catalog")
IMG = os.path.join(OUT, "img", "blocks")
os.makedirs(TEX, exist_ok=True)
os.makedirs(IMG, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
col = scene.collection
rng = random.Random(21)
R = 32


def lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hexrgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def shade(h, k):
    """Lighten (k > 0) or darken (k < 0) a hex colour."""
    r, g, b = hexrgb(h)
    f = (lambda c: c + (1 - c) * k) if k > 0 else (lambda c: c * (1 + k))
    return "#%02x%02x%02x" % tuple(round(max(0, min(1, f(c))) * 255) for c in (r, g, b))


# ---------------- drawing ----------------
def grid(c):
    return [[c] * R for _ in range(R)]


def px(g, x, y, c):
    if 0 <= x < R and 0 <= y < R:
        g[y][x] = c


def fill(g, x0, y0, w, h, c):
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            px(g, x, y, c)


def line(g, x0, y0, x1, y1, c):
    n = max(abs(x1 - x0), abs(y1 - y0), 1)
    for i in range(n + 1):
        px(g, round(x0 + (x1 - x0) * i / n), round(y0 + (y1 - y0) * i / n), c)


def border(g, c, inset=0):
    for i in range(inset, R - inset):
        for a, b in ((i, inset), (i, R - 1 - inset), (inset, i), (R - 1 - inset, i)):
            px(g, a, b, c)


def scatter(g, n, draw, y_max=None, margin=3, gap=7):
    used, tries = [], 0
    while len(used) < n and tries < 300:
        tries += 1
        x, y = rng.randrange(margin, R - margin), rng.randrange(margin, y_max or R - margin)
        if all(abs(x - a) + abs(y - b) > gap for a, b in used):
            used.append((x, y))
            draw(g, x, y, len(used))
    return g


def plus(g, x, y, c):
    for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
        px(g, x + dx, y + dy, c)


# ---------------- colours ----------------
GRASS, DIRT, STONE, SAND = "#6dbd58", "#9a6a44", "#a1a7ae", "#e3cf9a"
WOOD, BRICK, MORTAR = "#c99c61", "#b5553c", "#d6d0c6"


# ---------------- textures ----------------
def t_grass_top():
    return scatter(grid(GRASS), 6, lambda g, x, y, i: plus(g, x, y, shade(GRASS, 0.25 if i % 2 else -0.18))
                   if i <= 4 else px(g, x, y, shade(GRASS, -0.18)))


def dirt_body(g, y_max=None, band=True):
    if band:
        for x in range(R):
            fill(g, x, 9 + (1 if (x // 4) % 2 else 0), 1, 3, shade(DIRT, -0.15))

    def mark(g, x, y, i):
        if i <= 2:
            fill(g, x, y, 2, 2, "#b3aca6")
            fill(g, x, y - 1, 2, 1, shade(DIRT, -0.2))
        else:
            fill(g, x, y, 3, 1, shade(DIRT, 0.15 if i % 2 else -0.15))
    return scatter(g, 6, mark, y_max)


def t_dirt_top():
    return dirt_body(grid(DIRT), band=False)


def t_dirt_side():
    return dirt_body(grid(DIRT))


def t_grass_side():
    g = dirt_body(grid(DIRT), y_max=R - 7)
    fill(g, 0, R - 4, R, 4, shade(GRASS, -0.14))
    return g


def t_farm_top():
    g = grid(shade(DIRT, -0.2))
    for y in range(2, R, 6):
        fill(g, 0, y, R, 2, shade(DIRT, -0.38))
        fill(g, 0, y + 2, R, 1, shade(DIRT, -0.08))
    return g


def t_stone(base=STONE):
    g = grid(base)
    fill(g, 0, 15, 21, 17, shade(base, 0.07))
    fill(g, 0, 0, 11, 15, shade(base, -0.06))
    L = shade(base, -0.25)
    fill(g, 0, 15, 21, 1, L)
    fill(g, 21, 16, 11, 1, L)
    fill(g, 21, 15, 1, 2, L)
    fill(g, 20, 16, 1, 16, L)
    fill(g, 11, 0, 1, 15, L)
    for (x, y) in ((5, 24), (26, 8), (15, 6)):
        fill(g, x, y, 2, 1, shade(base, 0.2))
    return g


def t_ore(c):
    g = t_stone()

    def gem(g, x, y, i):
        fill(g, x, y, 3, 3, c)
        fill(g, x, y + 2, 2, 1, shade(c, 0.4))
        fill(g, x + 2, y, 1, 2, shade(c, -0.25))
        px(g, x + 4, y + 3, shade(c, 0.2))
    return scatter(g, 5, gem, margin=4, gap=8)


def t_sand():
    g = grid(SAND)

    def mark(g, x, y, i):
        if i <= 3:
            for k in range(5):
                px(g, x + k, y + (1 if k in (1, 2, 3) else 0), shade(SAND, -0.12))
        else:
            px(g, x, y, shade(SAND, 0.4 if i % 2 else -0.2))
    return scatter(g, 8, mark, gap=6)


def t_gravel():
    base = "#8f8f93"
    g = grid(base)

    def peb(g, x, y, i):
        c = shade(base, (0.22, -0.18, 0.1, -0.08)[i % 4])
        fill(g, x, y, 3 + i % 2, 2 + (i // 2) % 2, c)
        fill(g, x, y - 1, 3 + i % 2, 1, shade(base, -0.3))
    return scatter(g, 16, peb, margin=2, gap=5)


def t_clay():
    base = "#b9a79a"
    g = grid(base)
    for y in (7, 16, 25):
        for x in range(R):
            if (x + y) % 9 > 1:
                px(g, x, y, shade(base, -0.1))
    return g


def t_log_side():
    base = shade(WOOD, -0.32)
    g = grid(base)
    for x in (3, 9, 14, 20, 26):
        for y in range(R):
            if (y + x * 3) % 13 > 2:
                px(g, x + (1 if (y // 7) % 2 else 0), y, shade(base, -0.25))
    return g


def t_log_top():
    g = grid(shade(WOOD, 0.25))
    border(g, shade(WOOD, -0.32))
    border(g, shade(WOOD, -0.32), 1)
    for inset in (6, 11):
        border(g, shade(WOOD, -0.05), inset)
    fill(g, 15, 15, 2, 2, shade(WOOD, -0.25))
    return g


def t_leaves():
    base = "#4f9f4d"
    g = grid(base)
    return scatter(g, 14, lambda g, x, y, i: fill(g, x, y, 2, 2, shade(base, 0.28 if i % 3 else -0.25)), margin=1, gap=5)


def t_planks():
    g = grid(WOOD)
    for b in range(4):
        fill(g, 0, b * 8, R, 8, WOOD if b % 2 == 0 else shade(WOOD, -0.06))
        fill(g, 0, b * 8, R, 1, shade(WOOD, -0.25))
        seam = (b * 11 + 6) % R
        fill(g, seam, b * 8, 1, 8, shade(WOOD, -0.25))
        for s_ in (-3, 3):
            px(g, (seam + s_) % R, b * 8 + 4, shade(WOOD, -0.25))
        fill(g, (seam + 12) % (R - 6), b * 8 + 5, 5, 1, shade(WOOD, 0.2))
    return g


def bricks(base, mortar, rows, cols, vary=True):
    g = grid(mortar)
    bh, bw = R // rows, R // cols
    for row in range(rows):
        off = 0 if row % 2 == 0 else bw // 2
        for k in range(-1, cols + 1):
            c = shade(base, rng.choice((0, 0, 0, -0.12, 0.1))) if vary else base
            fill(g, k * bw + off + 1, row * bh + 1, bw - 1, bh - 1, c)
    return g


def t_glass():
    base = "#bfe6ee"
    g = grid(base)
    border(g, shade(base, 0.6))
    border(g, shade(base, -0.15), 1)
    line(g, 6, 22, 12, 28, "#ffffff")
    line(g, 6, 16, 16, 26, shade(base, 0.6))
    return g


def t_concrete():
    base = "#9aa6ad"
    g = grid(base)
    scatter(g, 10, lambda g, x, y, i: px(g, x, y, shade(base, 0.25 if i % 2 else -0.18)), gap=5)
    for (x, y) in ((4, 4), (R - 6, 4), (4, R - 6), (R - 6, R - 6)):
        fill(g, x, y, 2, 2, shade(base, -0.25))
    fill(g, 0, 16, R, 1, shade(base, -0.1))
    return g


def t_asphalt():
    base = "#4b4b50"
    return scatter(grid(base), 14, lambda g, x, y, i: px(g, x, y, shade(base, 0.3 if i % 3 else -0.3)), margin=1, gap=4)


def t_quartz():
    base = "#eeede8"
    g = grid(base)
    border(g, shade(base, -0.12), 3)
    for i in range(4, R - 4):
        px(g, i, 4, "#ffffff")
        px(g, R - 5, i, "#ffffff")
    for (x, y) in ((7, 7), (R - 9, 7), (7, R - 9), (R - 9, R - 9)):
        plus(g, x, y, shade(base, -0.12))
    return g


def t_metal_block(base, sparkle=False):
    g = grid(base)
    for i in range(R):
        for t in range(2):
            px(g, i, R - 1 - t, shade(base, 0.35))
            px(g, t, i, shade(base, 0.35))
    for i in range(R):
        for t in range(2):
            px(g, i, t, shade(base, -0.28))
            px(g, R - 1 - t, i, shade(base, -0.28))
    border(g, shade(base, -0.15), 6)
    for i in range(7, R - 7):
        px(g, i, R - 8, shade(base, 0.3))
        px(g, 7, i, shade(base, 0.3))
    if sparkle:
        for (x, y) in ((12, 20), (20, 12), (17, 23)):
            plus(g, x, y, "#ffffff")
    return g


def t_coal_block():
    base = "#2f2d30"
    g = grid(base)
    for (x0, y0, x1, y1) in ((0, 10, 14, 0), (8, 31, 31, 12), (0, 22, 20, 31), (18, 0, 31, 8)):
        line(g, x0, y0, x1, y1, shade(base, 0.25))
    scatter(g, 5, lambda g, x, y, i: fill(g, x, y, 2, 1, shade(base, 0.45)), gap=8)
    return g


def t_tread():
    base = "#c2beb7"
    g = grid(base)
    for j in range(4):
        for i in range(4):
            x, y = 3 + i * 8, 3 + j * 8
            for k in range(4):
                px(g, x + (k if (i + j) % 2 else 3 - k), y + k, shade(base, -0.22))
                px(g, x + (k if (i + j) % 2 else 3 - k) + 1, y + k, shade(base, -0.22))
    border(g, shade(base, -0.28))
    return g


def t_grating():
    base = "#34373d"
    g = grid(base)
    for i in range(0, R, 4):
        fill(g, i, 0, 1, R, "#8f8b85")
        fill(g, 0, i, R, 1, "#8f8b85")
    border(g, "#c2beb7")
    return g


def t_cloth(base):
    g = grid(base)
    for i in range(0, R, 4):
        fill(g, i, 0, 1, R, shade(base, -0.1))
        fill(g, 0, i, R, 1, shade(base, -0.1))
    for y in range(0, R, 4):
        for x in range(0, R, 4):
            px(g, x, y, shade(base, 0.2))
    return g


# ---------------- block table: key, name, category, top, side, bottom ----------------
BLOCKS = []


def block(key, ko, cat, top, side=None, bottom=None):
    BLOCKS.append((key, ko, cat, top, side or top, bottom or top))


dirt_top = t_dirt_top()
block("grass", "잔디", "자연", t_grass_top(), t_grass_side(), dirt_top)
block("dirt", "흙", "자연", dirt_top, t_dirt_side(), dirt_top)
block("farmland", "경작지", "자연", t_farm_top(), t_dirt_side(), dirt_top)
block("stone", "돌", "자연", t_stone())
block("sand", "모래", "자연", t_sand())
block("gravel", "자갈", "자연", t_gravel())
block("clay", "점토", "자연", t_clay())
block("log", "통나무", "자연", t_log_top(), t_log_side())
block("leaves", "나뭇잎", "자연", t_leaves())
for key, ko, c in (("coal", "석탄", "#2f2d30"), ("cu", "구리", "#d9824c"), ("fe", "철", "#c9b8a6"),
                   ("au", "금", "#f4c542"), ("dia", "다이아", "#86e3ea")):
    block(f"ore_{key}", f"{ko} 광석", "광석", t_ore(c))
block("planks", "판자", "건축", t_planks())
block("stone_bricks", "석재 벽돌", "건축", bricks(STONE, shade(STONE, -0.28), 2, 2, vary=False))
block("bricks", "벽돌", "건축", bricks(BRICK, MORTAR, 4, 2))
block("glass", "유리", "건축", t_glass())
block("concrete", "콘크리트", "건축", t_concrete())
block("asphalt", "포장재", "건축", t_asphalt())
block("quartz", "석영", "건축", t_quartz())
for key, ko, c in (("fe", "철", "#8fa0b3"), ("cu", "구리", "#d9824c"), ("steel", "강철", "#5f7389"),
                   ("au", "금", "#f4c542")):
    block(f"block_{key}", f"{ko} 블록", "금속", t_metal_block(c))
block("block_dia", "다이아 블록", "금속", t_metal_block("#86e3ea", sparkle=True))
block("block_coal", "석탄 블록", "금속", t_coal_block())
block("tread", "금속 바닥", "금속", t_tread())
block("grating", "격자 바닥", "금속", t_grating())
for key, ko, c in (("white", "흰", "#f1efe9"), ("red", "빨간", "#d9483b"), ("yellow", "노란", "#f0b429"),
                   ("green", "초록", "#5aa85a"), ("blue", "파란", "#4a8fd8")):
    block(f"cloth_{key}", f"{ko} 천 블록", "색 블록", t_cloth(c))


# ---------------- build ----------------
_mat_cache = {}


def material(name, g):
    if id(g) in _mat_cache:
        return _mat_cache[id(g)]
    img = bpy.data.images.new(name, R, R, alpha=False)
    pxs = []
    for y in range(R):
        for x in range(R):
            pxs += [*hexrgb(g[y][x]), 1.0]
    img.pixels = pxs
    img.filepath_raw = os.path.join(TEX, name + ".png")
    img.file_format = "PNG"
    img.save()
    m = bpy.data.materials.new(name)
    if m.node_tree is None:
        m.use_nodes = True
    nt = m.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Roughness"].default_value = 0.95
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    tex.interpolation = "Closest"
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    _mat_cache[id(g)] = m
    return m


def cube(name, mats):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1)
    bm.normal_update()
    uv = bm.loops.layers.uv.new()
    for f in bm.faces:
        n = f.normal
        f.material_index = 0 if n.z > 0.5 else 2 if n.z < -0.5 else 1
        for l in f.loops:
            c = l.vert.co
            if abs(n.z) > 0.5:
                l[uv].uv = (c.x + 0.5, c.y + 0.5)
            elif abs(n.y) > 0.5:
                l[uv].uv = (c.x + 0.5, c.z + 0.5)
            else:
                l[uv].uv = (c.y + 0.5, c.z + 0.5)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for m in mats:
        me.materials.append(m)
    return me


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
sd.angle = math.radians(12)
sun = bpy.data.objects.new("sun", sd)
col.objects.link(sun)
aim(sun, (3, -6, 9), (0, 0, 0))
cd = bpy.data.cameras.new("cam")
cd.type = "ORTHO"
cd.ortho_scale = 2.0
cam = bpy.data.objects.new("cam", cd)
col.objects.link(cam)
scene.camera = cam
scene.render.engine = "CYCLES"
scene.cycles.samples = 16
scene.view_settings.view_transform = "Standard"
scene.render.film_transparent = True
scene.render.resolution_x = scene.render.resolution_y = 320

meta = []
for i, (key, ko, cat, top, side, bottom) in enumerate(BLOCKS):
    names = (f"{key}_top", f"{key}_side", f"{key}_bottom")
    mats = [material(n, g) for n, g in zip(names, (top, side, bottom))]
    ob = bpy.data.objects.new(key, cube("blk_" + key, mats))
    O = Vector((i * 8.0, 0, 0))
    ob.location = O
    col.objects.link(ob)
    aim(cam, O + Vector((14, -14, 12.5)), O)
    scene.render.filepath = os.path.join(IMG, key + ".png")
    bpy.ops.render.render(write_still=True)
    meta.append(dict(key=key, ko=ko, cat=cat))
json.dump(meta, open(os.path.join(OUT, "blocks.json"), "w"), ensure_ascii=False, indent=1)
print("BLOCKS done", len(meta))
