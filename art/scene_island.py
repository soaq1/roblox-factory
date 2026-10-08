# A mood check, not a game asset: the small factory (set2.factory1) standing on a floating island of
# textured blocks, with a few trees and a figure for scale, under a daylight sky. It is here to judge
# whether the machines' look sits well with the blocks' look.
# Run:  Blender --background --python art/scene_island.py -- [out=<folder>] [only=a,b,c] [preview] [blend=<file>]
#   a = the whole island from a three-quarter angle, b = from a player's eye height, c = close on a smelter and a former
#   preview = small and rough, to check the framing quickly
import sys, os, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
sys.argv = sys.argv[:1] + ["--", "none"]          # keep factorykit from rendering its own catalog

import bpy, bmesh
from mathutils import Vector, Matrix, Euler
from bpy_extras.object_utils import world_to_camera_view
import factorykit as fk
from v2 import base, hero, works, pairs, bay, set2

rad, lin = math.radians, fk.lin
TEX = os.path.join(HERE, "textures")
OUT = os.path.expanduser(next((a.split("=", 1)[1] for a in args if a.startswith("out=")),
                              "~/Desktop/DevFolder/roblox-factory-preview/0 지금 보는 것"))
ONLY = next((a.split("=", 1)[1].split(",") for a in args if a.startswith("only=")), ["a", "b", "c"])
PREVIEW = "preview" in args
BLEND = next((a.split("=", 1)[1] for a in args if a.startswith("blend=")), "")
scene, col = fk.scene, fk.col


def rgb(r, g, b):
    return (lin(r / 255), lin(g / 255), lin(b / 255), 1)


def plain(name, colour):
    m = bpy.data.materials.new(name)
    if m.node_tree is None:
        m.use_nodes = True
    bsdf = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = colour
    bsdf.inputs["Roughness"].default_value = 0.9
    return m


def pictured(name):
    """A block face wearing one of the 32 px pictures, with its pixels kept crisp."""
    m = plain("blk_" + name, (1, 1, 1, 1))
    nt = m.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(os.path.join(TEX, name + ".png"))
    tex.interpolation = "Closest"
    tex.extension = "REPEAT"
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    return m


def link(mesh, name):
    ob = bpy.data.objects.new(name, mesh)
    col.objects.link(ob)
    return ob


# ============================ THE FACTORY ============================
base.set_style("d")
fm = fk.Model("factory")
hero.HEROES[next((a.split("=", 1)[1] for a in args if a.startswith("layout=")), "factory1")](fm)      # layout=<name> picks another layout
factory = fk.place(fm.done(), (0, 0, 0))
for o in bpy.context.selected_objects:
    o.select_set(False)
bpy.context.view_layer.objects.active = factory
factory.select_set(True)
try:
    bpy.ops.object.shade_smooth_by_angle(angle=rad(34))
except Exception:
    pass
wn = factory.modifiers.new("WeightedNormal", "WEIGHTED_NORMAL")      # as base.show() does: flats stay flat
wn.keep_sharp, wn.weight, wn.mode = True, 100, "FACE_AREA"
fv = [v.co for v in factory.data.vertices]
F_LO = Vector((min(v.x for v in fv), min(v.y for v in fv), min(v.z for v in fv)))
F_HI = Vector((max(v.x for v in fv), max(v.y for v in fv), max(v.z for v in fv)))
print(f"ISLAND factory box x {F_LO.x:.2f}..{F_HI.x:.2f}  y {F_LO.y:.2f}..{F_HI.y:.2f}  z {F_LO.z:.2f}..{F_HI.z:.2f}")


# ============================ THE ISLAND ============================
# The game's starting island (IslandGen.luau) is a disc of radius 7.3 with a wobbling edge: grass, then
# dirt, then stone narrowing downward. This one is the same idea stretched to hold the factory: a
# rounded oblong on top, and under each top cell a column whose depth grows with its distance from the
# edge, unevenly, so the underside hangs in ragged steps.
# The factory's cells have their edges on half numbers along x and whole numbers along y, so a block in
# column (i, j) spans x i-0.5..i+0.5 and y j..j+1, and the machines' feet line up with the block grid.
AX, BY, CORNER = 14.5, 7.0, 3.4          # half length, half width, how square the corners are
SPARE = 2                                 # cells of grass guaranteed all round the factory


def wobble(x, y):                         # the same wobble as IslandGen
    return 0.55 * math.sin(x * 1.3 + y * 0.7) + 0.35 * math.cos(y * 1.9 - x * 0.4)


def chance(i, j, s):                      # a repeatable number from 0 up to 1 for a cell
    v = math.sin(i * 12.9898 + j * 78.233 + s * 37.719) * 43758.5453
    return v - math.floor(v)


TREES = ((-12, 4, 11), (3, 5, 5), (12, -5, 23))           # column i, column j, seed. The middle one stands where no view
                                                          # lines its trunk up with a machine's top, or it seems to grow out of it
STAND = (-12, -5)                                         # the column the eye-height camera stands on

top = set()
for i in range(-17, 18):
    for j in range(-10, 10):
        x, y = i, j + 0.5
        d = ((abs(x) / AX) ** CORNER + (abs(y) / BY) ** CORNER) ** (1 / CORNER)
        if d * BY + 0.7 * wobble(x, y) <= BY - 0.15:
            top.add((i, j))
for i in range(math.floor(F_LO.x + 0.5) - SPARE, math.ceil(F_HI.x - 0.5) + SPARE + 1):   # room for the factory
    for j in range(math.floor(F_LO.y) - SPARE, math.ceil(F_HI.y) + SPARE):
        top.add((i, j))
for ti, tj in [t[:2] for t in TREES] + [STAND]:           # and firm ground under each tree and the camera
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            top.add((ti + di, tj + dj))
near4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
for _ in range(2):                                        # no lone teeth, no one-cell bites
    top -= {c for c in top if sum((c[0] + a, c[1] + b) in top for a, b in near4) <= 1}
    top |= {(i, j) for i in range(-17, 18) for j in range(-10, 10)
            if (i, j) not in top and sum((i + a, j + b) in top for a, b in near4) >= 3}

void = [(i, j) for i in range(-19, 20) for j in range(-12, 12) if (i, j) not in top]
solid = {}                                                # (i, j, k) -> kind; k counts down from the top
for (i, j) in top:
    edge = min(math.hypot(i - a, j - b) for a, b in void)                  # 1 at the rim, about 7 in the middle
    keel = 0.82 + 0.30 * math.sin(i * 0.42 + 0.8) + 0.18 * math.cos(i * 0.9 - 1.3)   # deeper in some stretches
    depth = 1 + int((edge - 1) * 0.95 * keel + 1.3 * chance(i, j, 1) - 0.15)
    if edge > 2.5 and chance(i, j, 2) < 0.07:
        depth += 1 + int(chance(i, j, 4) * 2)             # now and then a tooth hangs lower
    depth = max(1, depth)
    for k in range(depth):
        solid[(i, j, k)] = "grass" if k == 0 else "dirt" if k == 1 or (k == 2 and chance(i, j, 3) < 0.4) else "stone"

# which picture each face wears: (top, side, bottom), as art/blocks.py defines the blocks
WEAR = {"grass": ("grass_top", "grass_side", "grass_bottom"),
        "dirt": ("grass_bottom", "dirt_side", "grass_bottom"),
        "stone": ("stone_top", "stone_top", "stone_top")}
PICS = ["grass_top", "grass_side", "grass_bottom", "dirt_side", "stone_top"]
verts, faces, face_mat = [], [], []
for (i, j, k), kind in solid.items():
    x0, x1, y0, y1, z0, z1 = i - 0.5, i + 0.5, j, j + 1, -(k + 1), -k
    sides = (                                             # neighbour, which picture, corners (counter-clockwise from outside, picture upright)
        ((i, j, k - 1), 0, ((x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1))),
        ((i, j, k + 1), 2, ((x0, y1, z0), (x1, y1, z0), (x1, y0, z0), (x0, y0, z0))),
        ((i, j - 1, k), 1, ((x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1))),
        ((i, j + 1, k), 1, ((x1, y1, z0), (x0, y1, z0), (x0, y1, z1), (x1, y1, z1))),
        ((i + 1, j, k), 1, ((x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1))),
        ((i - 1, j, k), 1, ((x0, y1, z0), (x0, y0, z0), (x0, y0, z1), (x0, y1, z1))),
    )
    for other, which, corners in sides:
        if other in solid:                                # a face against another block is never seen: leave it out
            continue
        n = len(verts)
        verts.extend(corners)
        faces.append((n, n + 1, n + 2, n + 3))
        face_mat.append(PICS.index(WEAR[kind][which]))
me = bpy.data.meshes.new("island")
me.from_pydata(verts, [], faces)
for name in PICS:
    me.materials.append(pictured(name))
me.polygons.foreach_set("material_index", face_mat)
uv = me.uv_layers.new(name="uv")
uv.data.foreach_set("uv", [c for _ in faces for c in (0, 0, 1, 0, 1, 1, 0, 1)])
me.update()
island = link(me, "island")
xs, ys = [c[0] for c in top], [c[1] for c in top]
kinds = list(solid.values())
print(f"ISLAND top {max(xs) - min(xs) + 1} x {max(ys) - min(ys) + 1} cells ({len(top)} cells), "
      f"{len(solid)} blocks (grass {kinds.count('grass')}, dirt {kinds.count('dirt')}, stone {kinds.count('stone')}), "
      f"deepest {max(c[2] for c in solid) + 1}, {len(faces)} faces drawn of {len(solid) * 6}")


# ============================ TREES ============================
# TreeGen.luau, carried over: a trunk in four pieces that leans and bows, three or four branches forking
# from its top and one going straight up, and at the end of each a mass of four lumps of leaves in
# three greens. The game measures in studs with three studs to a cell; here one unit is a cell.
def tree_shape(seed):
    state = [int(abs(seed)) % 2147483646 + 1]

    def roll():
        state[0] = (state[0] * 48271) % 2147483647
        return state[0] / 2147483647

    def between(lo, hi):
        return lo + (hi - lo) * roll()

    for _ in range(4):
        roll()
    height = between(15, 18.5)
    trunk_top = height * 0.6
    foot = between(0.95, 1.15)
    lean_x, lean_z = between(-1.6, 1.6), between(-1.6, 1.6)
    bend_turn = between(0, math.pi * 2)
    bend = between(0.3, 0.8)
    limbs, lumps = [], []                 # limbs: (a, b, radius, is trunk); lumps: (place, size, turn, shade)
    p = (0.0, 0.0, 0.0)
    for i in range(1, 5):
        t = i / 4
        bow = math.sin(t * math.pi) * bend
        n = (lean_x * t + math.cos(bend_turn) * bow, trunk_top * t, lean_z * t + math.sin(bend_turn) * bow)
        limbs.append((p, n, foot * (1.3 - 0.8 * ((i - 0.5) / 4) ** 0.7), True))
        p = n
    px, py, pz = p
    forks = 3 if roll() < 0.5 else 4
    leaf = between(3.4, 4.0)
    turn = between(0, math.pi * 2)

    def mass(x, y, z, radius):
        for i in range(1, 5):
            spread = 0 if i == 1 else radius * 0.5
            size = radius * (1.5 if i == 1 else between(0.95, 1.25))
            place = (x + between(-1, 1) * spread, y + between(-0.4, 0.6) * spread, z + between(-1, 1) * spread)
            spin = (between(-0.45, 0.45), between(0, math.pi), between(-0.45, 0.45))
            lumps.append((place, (size, size * 0.72, size), spin, (i - 1) % 3))

    for k in range(1, forks + 1):
        angle = turn + math.pi * 2 * (k - 1) / forks + between(-0.4, 0.4)
        reach = leaf * between(0.95, 1.4)
        rise = height * between(0.22, 0.34)
        mid = (px + math.cos(angle) * reach * 0.5, py + rise * 0.45, pz + math.sin(angle) * reach * 0.5)
        tip = (px + math.cos(angle) * reach, py + rise, pz + math.sin(angle) * reach)
        limbs.append((p, mid, foot * 0.4, False))
        limbs.append((mid, tip, foot * 0.26, False))
        mass(tip[0], py + rise + leaf * 0.2, tip[2], leaf * between(0.82, 1.0))
    limbs.append((p, (px, height * 0.92, pz), foot * 0.3, False))
    mass(px, height * 0.92 + leaf * 0.15, pz, leaf * 1.12)
    return limbs, lumps


def cell(p):                              # a place in the game's studs (y up) -> cells (z up)
    return Vector((p[0], p[2], p[1])) / 3


tb = bmesh.new()                          # all the trees in one mesh: bark, then three greens
for ti, tj, seed in TREES:
    at = Vector((ti, tj + 0.5, 0))
    limbs, lumps = tree_shape(seed)
    for a, b, r, trunk in limbs:
        a, b, r = cell(a), cell(b), r / 3
        length = (b - a).length + r * 0.6
        turn = (b - a).to_track_quat("Z", "Y").to_matrix().to_4x4()
        made = bmesh.ops.create_cone(tb, cap_ends=True, segments=7 if trunk else 5, radius1=r, radius2=r * 0.84,
                                     depth=length, matrix=Matrix.Translation(at + (a + b) / 2) @ turn)
        for f in {f for v in made["verts"] for f in v.link_faces}:
            f.material_index = 0
    for n, (place, size, spin, shade) in enumerate(lumps):
        # a lumpy faceted ball, stretched to the size of this mass of leaves (as Tree.luau draws it)
        mat = (Matrix.Translation(at + cell(place)) @ Euler((spin[0], spin[2], spin[1])).to_matrix().to_4x4()
               @ Matrix.Diagonal((size[0] / 3 * 1.15, size[2] / 3 * 1.15, size[1] / 3 * 1.15, 1)))
        made = bmesh.ops.create_icosphere(tb, subdivisions=2, radius=0.5)
        for vn, v in enumerate(made["verts"]):
            v.co = mat @ (v.co * (0.90 + 0.22 * chance(vn, n, seed)))
        for f in {f for v in made["verts"] for f in v.link_faces}:
            f.material_index = 1 + shade
tme = bpy.data.meshes.new("trees")
tb.to_mesh(tme)
tb.free()
tme.materials.append(plain("bark", rgb(111, 76, 48)))                      # the colours Tree.luau uses
for n, c in enumerate(((47, 125, 51), (60, 149, 57), (87, 178, 70))):
    tme.materials.append(plain(f"leaf{n}", rgb(*c)))
trees = link(tme, "trees")


# ============================ A FIGURE FOR SCALE ============================
# A blocky figure five studs tall, which is 1.67 cells: legs and body two studs each, a head of one.
def figure(where, facing):
    S = 1 / 3
    parts = (                              # size, centre, colour
        ((0.94 * S, 0.94 * S, 2 * S), (-0.5 * S, 0, 1 * S), 2), ((0.94 * S, 0.94 * S, 2 * S), (0.5 * S, 0, 1 * S), 2),
        ((2 * S, 1 * S, 2 * S), (0, 0, 3 * S), 1),
        ((0.94 * S, 0.94 * S, 2 * S), (-1.5 * S, 0, 3 * S), 0), ((0.94 * S, 0.94 * S, 2 * S), (1.5 * S, 0, 3 * S), 0),
        ((1.15 * S, 1.15 * S, 1 * S), (0, 0, 4.5 * S), 0),
    )
    b = bmesh.new()
    for n, (size, centre, mi) in enumerate(parts):
        before = set(b.faces)
        made = bmesh.ops.create_cube(b, size=1, matrix=Matrix.Translation(centre) @ Matrix.Diagonal((*size, 1)))
        edges = list({e for v in made["verts"] for e in v.link_edges})
        bmesh.ops.bevel(b, geom=edges, offset=0.1 if n == 5 else 0.03, segments=2 if n == 5 else 1, affect="EDGES")   # no raw corners; the head rounder
        for f in b.faces:
            if f not in before:
                f.material_index = mi
    for f in b.faces:
        f.smooth = False
    fme = bpy.data.meshes.new("figure")
    b.to_mesh(fme)
    b.free()
    for name, c in (("fig_skin", (236, 200, 150)), ("fig_shirt", (62, 118, 186)), ("fig_legs", (64, 72, 86))):
        fme.materials.append(plain(name, rgb(*c)))
    ob = link(fme, "figure")
    ob.location, ob.rotation_euler = where, (0, 0, facing)
    return ob


FIGURE_AT = Vector((-1.95, -3.75, 0))      # on the grass in front of the near line, between smelter and former
figure(FIGURE_AT, rad(-20))


# ============================ DAYLIGHT ============================
# The camera sees a sky that pales toward the horizon and stays pale below it (the void); everything
# else is lit by an even pale blue from all round, so sides turned from the sun are dim, not black.
nt = fk.world.node_tree
for n in list(nt.nodes):
    nt.nodes.remove(n)
N = nt.nodes.new
coord, split, ramp = N("ShaderNodeTexCoord"), N("ShaderNodeSeparateXYZ"), N("ShaderNodeValToRGB")
seen, fill, path, mix, outw = N("ShaderNodeBackground"), N("ShaderNodeBackground"), N("ShaderNodeLightPath"), N("ShaderNodeMixShader"), N("ShaderNodeOutputWorld")
el = ramp.color_ramp.elements
el[0].position, el[0].color = 0.0, rgb(196, 226, 250)          # far below: haze
el[1].position, el[1].color = 1.0, rgb(58, 132, 226)           # straight up
for pos, c in ((0.44, (176, 216, 250)), (0.52, (150, 202, 248)), (0.72, (96, 164, 238))):
    e = el.new(pos)
    e.color = rgb(*c)
remap = N("ShaderNodeMapRange")                                 # looking down -1 .. up +1  ->  0 .. 1
remap.inputs["From Min"].default_value, remap.inputs["From Max"].default_value = -1, 1
nt.links.new(coord.outputs["Generated"], split.inputs[0])
nt.links.new(split.outputs["Z"], remap.inputs["Value"])
nt.links.new(remap.outputs["Result"], ramp.inputs["Fac"])
nt.links.new(ramp.outputs["Color"], seen.inputs["Color"])
seen.inputs["Strength"].default_value = 1.0
fill.inputs["Color"].default_value = (0.80, 0.90, 1.0, 1)
fill.inputs["Strength"].default_value = 0.62
nt.links.new(path.outputs["Is Camera Ray"], mix.inputs["Fac"])
nt.links.new(fill.outputs["Background"], mix.inputs[1])
nt.links.new(seen.outputs["Background"], mix.inputs[2])
nt.links.new(mix.outputs["Shader"], outw.inputs["Surface"])

sun = fk.sun
sun.data.energy, sun.data.angle = 2.7, rad(5)                   # a slightly wide sun: soft-edged shadows
sun.data.color = (1.0, 0.96, 0.88)
fk.aim(sun, (7, -9, 13), (0, 0, 0))                             # from the front right, high


# ============================ CAMERAS AND PICTURES ============================
cam, cd = fk.cam, fk.cd
cd.type, cd.sensor_width, cd.clip_start, cd.clip_end = "PERSP", 36, 0.05, 500
scene.render.film_transparent = False
scene.render.engine = "CYCLES"
scene.cycles.samples = 12 if PREVIEW else 64
try:
    scene.cycles.use_denoising = True
except Exception:
    pass
scene.render.image_settings.file_format = "JPEG"
scene.render.image_settings.quality = 92
scene.render.resolution_percentage = 100


def frame(target, toward, points, lens, res, fill_to=0.90):
    """Aim at `target` from the direction `toward` and back off until every point is inside the picture,
    then slide the picture sideways and up so the points sit in its middle."""
    scene.render.resolution_x, scene.render.resolution_y = res
    cd.lens, cd.shift_x, cd.shift_y = lens, 0, 0
    target, toward = Vector(target), Vector(toward).normalized()
    lo, hi = (1 - fill_to) / 2, (1 + fill_to) / 2
    for _ in range(3):
        dist = 4.0
        while dist < 300:
            fk.aim(cam, target + toward * dist, target)
            bpy.context.view_layer.update()
            seen_at = [world_to_camera_view(scene, cam, Vector(p)) for p in points]
            if all(s.z > 0 and lo <= s.x <= hi and lo <= s.y <= hi for s in seen_at):
                break
            dist *= 1.03
        cx = (min(s.x for s in seen_at) + max(s.x for s in seen_at)) / 2 - 0.5
        cy = (min(s.y for s in seen_at) + max(s.y for s in seen_at)) / 2 - 0.5
        cd.shift_x += cx
        cd.shift_y += cy * res[1] / res[0]
    return dist


def box_points(lo, hi):
    return [(x, y, z) for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])]


def take(name, res):
    if PREVIEW:
        scene.render.resolution_x, scene.render.resolution_y = res[0] * 2 // 5, res[1] * 2 // 5
    os.makedirs(OUT, exist_ok=True)
    scene.render.filepath = os.path.join(OUT, name + ".jpg")
    bpy.ops.render.render(write_still=True)
    print("ISLAND wrote", scene.render.filepath)


everything = [tuple(v.co) for v in island.data.vertices] + [tuple(v.co) for v in trees.data.vertices] + box_points(F_LO, F_HI)

if "a" in ONLY:        # the whole island with the void round it, from the front left and above
    elev, turn = rad(21), rad(238)
    d = frame((0, 0, 0), (math.cos(elev) * math.cos(turn), math.cos(elev) * math.sin(turn), math.sin(elev)),
              everything, 45, (2000, 1250), fill_to=0.90)
    print(f"ISLAND a: camera {d:.1f} cells away")
    take("섬-공장-전체", (2000, 1250))

if "b" in ONLY:        # a player standing on the grass at the front left corner, looking along the factory
    scene.render.resolution_x, scene.render.resolution_y = 2000, 1125
    cd.lens, cd.shift_x, cd.shift_y = 21, 0, 0
    fk.aim(cam, (STAND[0] - 0.2, STAND[1] + 0.45, 1.5), (1.5, -0.6, 1.25))      # eyes 1.5 cells up on a 1.67 cell body
    take("섬-공장-눈높이", (2000, 1125))

if "c" in ONLY:        # close on the near smelter and former, with the figure, a tree behind and the island's front edge below
    elev, turn = rad(19), rad(244)
    frame((-2.6, -2.0, 1.1), (math.cos(elev) * math.cos(turn), math.cos(elev) * math.sin(turn), math.sin(elev)),
          box_points((-7.2, -4.4, 0.0), (1.6, -0.8, 2.6)) + [(3, 5.5, 5.0), (-5.5, -6.5, -2.0), (1.5, -6.5, -2.0)],
          40, (2000, 1300), fill_to=0.94)
    take("섬-공장-가까이", (2000, 1300))

if BLEND:
    bpy.ops.wm.save_as_mainfile(filepath=os.path.expanduser(BLEND))
print("ISLAND done", ONLY)
