# Build v2 models without rendering and report faces of different parts that share a plane and overlap.
# Run:  Blender --background --python art/check_models.py -- [all] smelter3 assembler4
#   same : both faces look the same way. These flicker on screen and must be fixed.
#   back : the faces look at each other (two parts butted). Listed only with `all`.
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
sys.argv = sys.argv[:1] + ["--", "none"]

import factorykit as fk
from v2 import base, hero, works, pairs, bay, set2, check

base.set_style("d")
every = "all" in args
for name in [a for a in args if a != "all"]:
    m = fk.Model(name)
    hero.HEROES[name](m)
    rows = check.coplanar(m.done())
    same = [r for r in rows if r[1] == "same"]
    print(f"CHECK {name}: {len(same)} same-facing, {len(rows) - len(same)} butted")
    for area, facing, a, b, where in (rows if every else same):
        print(f"  {facing} area={area:.4f} at {where}: {a[0]} c={a[1]} s={a[2]}  x  {b[0]} c={b[1]} s={b[2]}")
