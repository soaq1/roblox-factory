# Render v2 hero machines one at a time, large, from four directions.
# Run:  Blender --background --python art/hero_render.py -- out=<folder> [base=a|b|c] crusher [more names]
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
sys.argv = sys.argv[:1] + ["--", "none"]          # keep factorykit from rendering its own catalog

import factorykit as fk
from v2 import base, hero

out = next((a.split("=", 1)[1] for a in args if a.startswith("out=")), os.path.join(HERE, "catalog", "img", "hero"))
style = next((a.split("=", 1)[1] for a in args if a.startswith("base=")), "a")
base.set_style(style)             # one foundation per run: a (measured from Islands), b or c (our own)
names = [a for a in args if "=" not in a] or list(hero.HEROES)
for name in names:
    base.show(hero.HEROES[name], name if style == "a" else f"{name}_{style}", os.path.expanduser(out))
print("HERO done", names)
