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


def blocks_edges(m):
    with m.at((-4.2, 0, 0)):
        patch(m, 0.0)
    with m.at((4.2, 0, 0)):
        patch(m, 0.045)


blocks_edges.frame = {k: (15.5, 1.6) for k in ("iso", "side", "top", "end")}
blocks_edges.shadow, blocks_edges.res = True, 2400
_hero.HEROES["blocks_edges"] = blocks_edges
