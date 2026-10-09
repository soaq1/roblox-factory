# A look to judge, not game assets: the same patch of ground twice, once of square blocks and once
# of blocks with their edges cut as the machines' are, each with a belt, a tree and a figure on it.
# The developer asked (2026-10-09) whether blocks should have cut edges to sit with the factory look;
# this shows what that does to a stretch of ground, where every block meets its neighbours.
from . import hero as _hero
from . import belts, trees
import factorykit as fk

fk.PAL.update({"b_grass": "#79c267", "b_dirt": "#8b5e3c", "b_stone": "#9a9fa3"})


def block(m, x, y, top, mk_top, mk_body, bevel):
    """One block, a cell each way, its top at `top`: a body with a cap of another colour."""
    m.box((1.0, 1.0, 0.82), (x, y, top - 0.18 - 0.41), mk_body, bevel=bevel)
    m.box((1.0, 1.0, 0.18), (x, y, top - 0.09), mk_top, bevel=bevel)


def patch(m, bevel):
    for i in range(-3, 3):
        for j in range(-2, 2):
            step = 1 if (i <= -2 and j >= 0) else 0            # a raised corner, to show a step in the ground
            block(m, i + 0.5, j + 0.5, 0.0, "b_grass", "b_dirt", bevel)
            if step:
                block(m, i + 0.5, j + 0.5, 1.0, "b_grass", "b_dirt", bevel)
    for i in (0, 1):                                           # two stone blocks standing on the ground
        block(m, 1.5 + i, 1.5, 1.0, "b_stone", "b_stone", bevel)
    with m.at((0.0, -1.5, 0)):
        for k in (-2, -1, 0, 1, 2):
            with m.at((k + 0.5, 0, 0)):
                belts.straight(m)
    with m.at((-0.5, 0.6, 0)):
        trees.figure(m)
    with m.at((-2.3, 1.2, 1.0)):
        trees.oak_a(m)


def joined(m, bevel=0.045):
    """The same patch, built as the developer meant it: an edge is cut only where both faces that meet
    at it are open to the air. Where a block has a neighbour, the edges round that face stay square, so
    blocks side by side run on as one surface, and only the outside of the whole is cut."""
    import bmesh
    from mathutils import Vector
    cells = {}
    for i in range(-3, 3):
        for j in range(-2, 2):
            cells[(i, j, -1)] = "g"
            if i <= -2 and j >= 0:
                cells[(i, j, 0)] = "g"
    for i in (1, 2):
        cells[(i, 1, 0)] = "s"
    for (i, j, k), kind in cells.items():
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        open_ = lambda n: (i + round(n.x), j + round(n.y), k + round(n.z)) not in cells
        cut = [e for e in bm.edges if all(open_(f.normal) for f in e.link_faces)]
        if cut:
            bmesh.ops.bevel(bm, geom=cut, offset=bevel, segments=1, affect="EDGES", profile=0.5)
        before = len(m.bm.faces)
        body, top = ("b_stone", "b_stone") if kind == "s" else ("b_dirt", "b_grass")
        m._add(bm, body, (i + 0.5, j + 0.5, k + 0.5))
        if top not in m.mats:
            m.mats.append(top)
        m.bm.faces.ensure_lookup_table()
        grass_on_top = (i, j, k + 1) not in cells
        for f in m.bm.faces[before:]:
            f.normal_update()
            if grass_on_top and f.normal.z > 0.3:
                f.material_index = m.mats.index(top)
    with m.at((0.0, -1.5, 0)):
        for k in (-2, -1, 0, 1, 2):
            with m.at((k + 0.5, 0, 0)):
                belts.straight(m)
    with m.at((-0.5, 0.6, 0)):
        trees.figure(m)
    with m.at((-2.3, 1.2, 1.0)):
        trees.oak_a(m)


def blocks_joined(m):
    """Square blocks, and blocks cut only on the outside, side by side."""
    with m.at((-4.2, 0, 0)):
        patch(m, 0.0)
    with m.at((4.2, 0, 0)):
        joined(m)


blocks_joined.frame = {k: (15.5, 1.6) for k in ("iso", "side", "top", "end")}
blocks_joined.shadow, blocks_joined.res = True, 2400
_hero.HEROES["blocks_joined"] = blocks_joined


def blocks_edges(m):
    with m.at((-4.2, 0, 0)):
        patch(m, 0.0)
    with m.at((4.2, 0, 0)):
        patch(m, 0.045)


blocks_edges.frame = {k: (15.5, 1.6) for k in ("iso", "side", "top", "end")}
blocks_edges.shadow, blocks_edges.res = True, 2400
_hero.HEROES["blocks_edges"] = blocks_edges
