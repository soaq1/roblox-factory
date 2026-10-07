# Looks for faces of different parts that lie in exactly the same plane and overlap.
# Two such faces flicker against each other in a viewport (z-fighting) and render black in Cycles.
# Run through art/check_models.py.
import bmesh
from collections import defaultdict


def _clip(poly, a, b):
    """The part of a convex 2D polygon to the left of the line a -> b."""
    out = []
    for i in range(len(poly)):
        p, q = poly[i], poly[(i + 1) % len(poly)]
        sp = (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])
        sq = (b[0] - a[0]) * (q[1] - a[1]) - (b[1] - a[1]) * (q[0] - a[0])
        if sp >= 0:
            out.append(p)
        if (sp > 0 and sq < 0) or (sp < 0 and sq > 0):
            t = sp / (sp - sq)
            out.append((p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t))
    return out


def _area(poly):
    return 0.5 * sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1] for i in range(len(poly)))


def coplanar(mesh, tol=2e-4, min_area=2e-5):
    """Pairs of parts with overlapping faces in one plane. Returns a list of
    (area, facing, (material, centre) of each part, where), largest first. `facing` is "same" when both
    faces look the same way (they fight on screen) and "back" when they look at each other (a butt joint)."""
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bm.verts.ensure_lookup_table()
    parent = list(range(len(bm.verts)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    for e in bm.edges:
        a, b = find(e.verts[0].index), find(e.verts[1].index)
        if a != b:
            parent[a] = b
    mats = [mt.name for mt in mesh.materials]
    box, mat = {}, {}
    for f in bm.faces:
        isl = find(f.verts[0].index)
        mat[isl] = mats[f.material_index] if mats else "?"
        lo, hi = box.setdefault(isl, ([1e9] * 3, [-1e9] * 3))
        for v in f.verts:
            for k in range(3):
                lo[k], hi[k] = min(lo[k], v.co[k]), max(hi[k], v.co[k])
    groups = defaultdict(list)
    for f in bm.faces:
        n = f.normal
        if f.calc_area() < 1e-7:
            continue
        sign = 1.0
        for c in n:
            if abs(c) > 1e-3:
                sign = 1.0 if c > 0 else -1.0
                break
        cn = n * sign
        d = cn.dot(f.verts[0].co)
        groups[(round(cn.x, 3), round(cn.y, 3), round(cn.z, 3))].append((d, sign, f, find(f.verts[0].index), cn))
    found = defaultdict(lambda: [0.0, None])
    for tris in groups.values():
        tris.sort(key=lambda t: t[0])
        for i, (d, sign, f, isl, cn) in enumerate(tris):
            u = cn.orthogonal().normalized()
            w = cn.cross(u)
            pa = [(v.co.dot(u), v.co.dot(w)) for v in f.verts]
            if _area(pa) < 0:
                pa.reverse()
            ax0, ax1 = min(p[0] for p in pa), max(p[0] for p in pa)
            ay0, ay1 = min(p[1] for p in pa), max(p[1] for p in pa)
            for d2, sign2, g, isl2, _ in tris[i + 1:]:
                if d2 - d > tol:
                    break
                if isl2 == isl:
                    continue
                pb = [(v.co.dot(u), v.co.dot(w)) for v in g.verts]
                if min(p[0] for p in pb) >= ax1 or max(p[0] for p in pb) <= ax0 or min(p[1] for p in pb) >= ay1 or max(p[1] for p in pb) <= ay0:
                    continue
                if _area(pb) < 0:
                    pb.reverse()
                poly = pa
                for k in range(3):
                    poly = _clip(poly, pb[k], pb[(k + 1) % 3])
                    if len(poly) < 3:
                        break
                if len(poly) < 3:
                    continue
                a = abs(_area(poly))
                if a < min_area:
                    continue
                if sign == sign2 and mat[isl] == mat[isl2]:
                    continue                                  # same colour, same way: cannot be told apart
                if abs(cn.z) > 0.999 and abs(d) < tol and sign == sign2:
                    continue                                  # undersides resting on the ground
                key = (min(isl, isl2), max(isl, isl2), "same" if sign == sign2 else "back")
                found[key][0] += a
                found[key][1] = f.calc_center_median().copy()
    out = []
    for (a, b, facing), (area, where) in found.items():
        def tag(i):
            lo, hi = box[i]
            return mat[i], tuple(round((lo[k] + hi[k]) / 2, 3) for k in range(3)), tuple(round(hi[k] - lo[k], 3) for k in range(3))
        out.append((area, facing, tag(a), tag(b), tuple(round(c, 3) for c in where)))
    bm.free()
    return sorted(out, key=lambda r: (r[1] != "same", -r[0]))
