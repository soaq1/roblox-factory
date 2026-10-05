# Recipe draft. This file is the single source: running it checks the recipes against the catalog
# and writes docs/recipes.md and data/recipes.json.
#   python3 data/recipes.py
# Every number here is a first guess meant to be tuned once the game can be played.
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
catalog = json.load(open(os.path.join(ROOT, "art", "catalog", "catalog.json"), encoding="utf-8"))
block_list = json.load(open(os.path.join(ROOT, "art", "catalog", "blocks.json"), encoding="utf-8"))

ITEM = {i["key"]: i["ko"] for i in catalog["items"]}
MACHINE = {m["key"]: m["ko"] for m in catalog["machines"]}
BLOCK = {"block:" + b["key"]: b["ko"] + " (블록)" for b in block_list}
NAMES = {**ITEM, **MACHINE, **BLOCK}

BENCH = {"basic": "wb_basic", "tool": "wb_tool", "part": "wb_part", "machine": "wb_machine",
         "cook": "wb_cook", "elec": "wb_elec", "furn": "wb_furn"}
BENCH_KO = {"bag": "가방", "basic": "기본", "tool": "도구", "part": "부품", "machine": "기계",
            "cook": "조리대", "elec": "전기", "furn": "가구", "all": "통합"}

# ---------------------------------------------------------------- where things first come from
RAW = {
    "dirt_clod": "섬의 땅을 팜",
    "stone": "섬의 땅을 팜 · 돌 광맥 핵을 꽂은 추출기",
    "log": "나무를 벰 (묘목을 심어 기름) · 벌목기",
    "coal": "허브 광산 · 석탄 광맥 핵을 꽂은 추출기",
    "ore_cu": "허브 광산 · 구리 광맥 핵을 꽂은 추출기",
    "ore_fe": "허브 광산 · 철 광맥 핵을 꽂은 추출기",
    "ore_au": "허브 광산에서만 (핵 제련소가 있으면 금 광맥 핵)",
    "ore_dia": "허브 광산에서만 (핵 제련소가 있으면 다이아 광맥 핵)",
    "core_stone": "허브 광산에서 돌을 캐다 낮은 확률로",
    "core_coal": "허브 광산에서 석탄을 캐다 낮은 확률로",
    "core_cu": "허브 광산에서 구리를 캐다 낮은 확률로",
    "core_fe": "허브 광산에서 철을 캐다 낮은 확률로",
    "core_au": "핵 제련소에서만",
    "core_dia": "핵 제련소에서만",
    "monster_part": "몬스터를 잡아 낮은 확률로",
    "seed": "농부에게서 삼 · 작물을 거두면 일부가 씨앗으로 돌아옴",
    "sapling": "농부에게서 삼 · 나뭇잎을 부수면 가끔 나옴",
    "wheat": "밭에서 기름 (씨앗)",
    "cotton": "밭에서 기름 (씨앗)",
    "oilseed": "밭에서 기름 (씨앗)",
    "barrel_water": "물 펌프 (손으로 물을 뜨는 방법은 미정)",
    "barrel_oil": "펌프잭 (원유를 어디서 얻는지는 미정)",
    "crate": "포장기가 같은 아이템 8개를 묶어 만듦",
    "block:grass": "섬의 땅 · 흙 위에 저절로 번짐",
    "block:dirt": "섬의 땅",
    "block:stone": "섬의 땅",
    "block:log": "나무",
    "block:leaves": "나무",
    "block:ore_coal": "허브 광산",
    "block:ore_cu": "허브 광산",
    "block:ore_fe": "허브 광산",
    "block:ore_au": "허브 광산",
    "block:ore_dia": "허브 광산",
    "block:quartz": "미정",
}

# How many smelts one unit of fuel is good for.
FUEL = {"log": 1, "charcoal": 3, "coal": 4, "briquette": 4, "oilcan": 12, "barrel_fuel": 24}
FUEL_USERS = ["campfire", "hand_furnace", "smelter", "kiln", "oven", "blast", "alloy", "caster",
              "generator", "incinerator"]

# Machines that do not run without electricity (design document 8.15).
NEEDS_POWER = ["assembler", "circuit", "manufacturer", "gemcutter", "recycler", "painter", "magsep", "sorter",
               "lift", "launcher", "blower", "pusher", "sensor", "gate", "counter", "logic", "beacon", "timer",
               "coreforge"]

# ---------------------------------------------------------------- processing: one thing becomes another
# hand = where the same job is done by hand (None when another recipe covers the hand route)
# tool = a tool that must be held, not used up
PROCESS = []


def P(kind, machine, hand, ins, outs, secs, tool=None, note=""):
    PROCESS.append(dict(kind=kind, machine=machine, hand=hand, ins=ins, outs=outs, secs=secs, tool=tool, note=note))


for ore, crushed, clean, ingot in (("ore_fe", "crushed_fe", "clean_fe", "ingot_fe"),
                                   ("ore_cu", "crushed", "clean", "ingot_cu"),
                                   ("ore_au", "crushed_au", "clean_au", "ingot_au")):
    P("가열", "smelter", "hand_furnace", {ore: 1}, {ingot: 1}, 3, note="가장 짧은 길")
    P("분쇄", "crusher", "wb_part", {ore: 1}, {crushed: 2}, 2, tool="hammer")
    P("가열", "smelter", "hand_furnace", {crushed: 3}, {ingot: 2}, 6, note="부수기만 하면 1.3배")
    P("세척", "washer", "wb_basic", {crushed: 8, "barrel_water": 1}, {clean: 8, "slag": 2}, 8, tool="bucket")
    P("가열", "smelter", "hand_furnace", {clean: 1}, {ingot: 1}, 3, note="부수고 씻으면 2배")

P("가열", "kiln", "hand_furnace", {"sand": 2}, {"glass": 1}, 3)
P("가열", "kiln", "hand_furnace", {"clay": 1}, {"brick": 1}, 3)
P("가열", "kiln", "hand_furnace", {"log": 1}, {"charcoal": 1}, 4, note="석탄이 없을 때의 연료")
P("가열", "oven", "wb_cook", {"dough": 1}, {"bread": 1}, 4)
P("합금", "blast", "hand_furnace", {"ingot_fe": 4, "coal": 2}, {"ingot_steel": 4}, 12)
P("합금", "blast", "hand_furnace", {"ingot_fe": 4, "charcoal": 3}, {"ingot_steel": 4}, 16, note="석탄 없이 만드는 길")
P("합금", "alloy", "hand_furnace", {"ingot_cu": 1, "ingot_au": 1}, {"ingot_alloy": 2}, 8)

P("분쇄", "crusher", "wb_part", {"stone": 1}, {"gravel": 1}, 2, tool="hammer")
P("분쇄", "crusher", "wb_part", {"gravel": 1}, {"sand": 1}, 2, tool="hammer")
P("분쇄", "mill", "wb_cook", {"wheat": 1}, {"flour": 1}, 2)
P("걸러내기", "sieve", "wb_basic", {"gravel": 10}, {"sand": 8, "ore_fe": 1}, 10, note="광맥 핵 없이 철을 얻는 느린 길")
P("걸러내기", "sieve", "wb_basic", {"sand": 10}, {"ore_cu": 1}, 10, note="광맥 핵 없이 구리를 얻는 느린 길")

for metal in ("fe", "cu", "steel"):
    P("압연", "press", "wb_part", {f"ingot_{metal}": 1}, {f"plate_{metal}": 1}, 2, tool="hammer")
    P("인발", "wiredraw", "wb_part", {f"ingot_{metal}": 1}, {f"rod_{metal}": 2}, 2, tool="hammer")
P("압연", "press", "wb_part", {"ingot_steel": 2}, {"beam": 1}, 4, tool="hammer")
P("인발", "wiredraw", "wb_part", {"ingot_cu": 1}, {"coil": 2}, 2, tool="hammer")
P("인발", "wiredraw", "wb_part", {"ingot_au": 1}, {"wire_au": 2}, 2, tool="hammer")
P("절삭", "lathe", "wb_part", {"rod_fe": 1}, {"bolt": 4}, 2, tool="hammer")
P("절삭", "lathe", "wb_part", {"plate_fe": 1}, {"gear": 1}, 3, tool="hammer")
P("주조", "caster", None, {"ingot_fe": 4}, {"frame": 1}, 6, note="조립보다 철이 더 들지만 한 줄로 끝남")

P("절단", "sawmill", "bag", {"log": 1}, {"plank": 4, "sawdust": 1}, 2, note="손으로 하면 톱밥은 안 나옴")
P("절단", "stonecutter", "wb_basic", {"stone": 1}, {"stone_block": 1}, 2, tool="hammer")
P("절단", "gemcutter", "wb_tool", {"ore_dia": 1}, {"diamond": 1}, 6)
P("절단", "gemcutter", "wb_tool", {"diamond": 1}, {"blade": 1}, 8)
P("압축", "briquetter", "wb_basic", {"sawdust": 4}, {"briquette": 1}, 3, note="부산물이 연료가 됨")
P("압착", "oilpress", "wb_cook", {"oilseed": 4}, {"oilcan": 1}, 4, note="밭에서 얻는 연료")
P("직조", "loom", "wb_furn", {"cotton": 2}, {"cloth": 1}, 3)

P("혼합", "mixer", "wb_basic", {"dirt_clod": 4, "barrel_water": 1}, {"clay": 4}, 4, tool="bucket")
P("혼합", "mixer", "wb_basic", {"sand": 2, "gravel": 2, "barrel_water": 1}, {"concrete": 4}, 4, tool="bucket")
P("혼합", "mixer", "wb_cook", {"flour": 2, "barrel_water": 1}, {"dough": 4}, 3)
P("혼합", "mixer", "wb_basic", {"slag": 2, "tar": 1}, {"asphalt": 4}, 4, note="찌꺼기와 타르의 쓸모")
P("정유", "refinery", "hand_furnace", {"barrel_oil": 2}, {"barrel_fuel": 1, "plastic": 2, "tar": 1}, 10)

# ---------------------------------------------------------------- crafting at a workbench
# bench = (kind, tier). "bag" needs no workbench. An assembler can run any of these on its own.
CRAFT = []


def C(out, n, bench, tier, note="", **ins):
    ins = {k.replace("block__", "block:"): v for k, v in ins.items()}
    CRAFT.append(dict(out=out, n=n, bench=bench, tier=tier, ins=ins, note=note))


# parts and assemblies
C("frame", 1, "part", 1, plate_fe=2, rod_fe=2, note="거의 모든 기계의 뼈대")
C("motor", 1, "part", 2, coil=4, gear=2, frame=1, note="움직이는 기계의 재료")
C("cell", 1, "elec", 1, plate_cu=1, plate_fe=1, charcoal=2)
C("board", 1, "elec", 1, coil=3, glass=1)
C("board", 1, "elec", 2, coil=2, plastic=1, note="석유를 뚫은 뒤의 싼 길")
C("board_adv", 1, "elec", 3, board=2, wire_au=4, ingot_alloy=1)

# tools: head material + handle
TOOL_HEADS = {"pick": 3, "axe": 3, "shovel": 1, "hoe": 2, "sword": 2}
TIERS = [("wood", "plank", "plank", "bag", 0), ("stone", "stone", "plank", "bag", 0),
         ("iron", "ingot_fe", "plank", "tool", 1), ("steel", "ingot_steel", "rod_fe", "tool", 2),
         ("gold", "ingot_au", "rod_fe", "tool", 2), ("dia", "diamond", "rod_steel", "tool", 3)]
for shape, heads in TOOL_HEADS.items():
    for tier, head, handle, bench, level in TIERS:
        ins = {head: heads}
        ins[handle] = ins.get(handle, 0) + 2
        CRAFT.append(dict(out=f"{shape}_{tier}", n=1, bench=bench, tier=level, ins=ins, note=""))
C("hammer", 1, "basic", 1, ingot_fe=2, plank=1, note="손으로 부품을 만들 때 듦")
C("wrench", 1, "tool", 1, ingot_fe=2)
C("bucket", 1, "part", 1, plate_fe=3)
C("watering_can", 1, "tool", 1, plate_fe=3, plate_cu=1)
C("fishing_rod", 1, "basic", 1, plank=3, cloth=1)

# hand work
C("wb_basic", 1, "bag", 0, plank=8)
C("campfire", 1, "bag", 0, log=3, stone=8)
C("chest", 1, "bag", 0, plank=8)
C("hand_furnace", 1, "basic", 1, stone=40)
C("wb_tool", 1, "basic", 1, plank=10, stone=20, ingot_fe=10)
C("wb_part", 1, "basic", 1, plank=10, ingot_fe=20)
C("wb_machine", 1, "basic", 1, ingot_fe=50, stone=30, plank=20)
C("wb_cook", 1, "basic", 1, stone=20, plank=10)
C("wb_furn", 1, "basic", 1, plank=20)
C("wb_elec", 1, "basic", 2, ingot_cu=60, plate_fe=30, coil=40)
C("wb_all", 1, "machine", 3, ingot_au=200, diamond=50, motor=50, board_adv=50, plate_steel=500,
  note="일곱 작업대를 모두 3단계로 올린 뒤에 만듦")

# transport
C("belt", 4, "machine", 1, plate_fe=2, rod_fe=2)
C("belt_corner", 2, "machine", 1, plate_fe=2, rod_fe=2)
C("belt_ramp", 1, "machine", 1, plate_fe=3, rod_fe=4)
C("merger", 1, "machine", 1, plate_fe=3, rod_fe=2)
C("splitter", 1, "machine", 1, plate_fe=3, rod_fe=2, gear=2)
C("storage", 1, "machine", 1, plate_fe=6, plank=8)
C("sorter", 1, "machine", 3, frame=1, board=1, motor=1)
C("magsep", 1, "machine", 3, frame=1, coil=20, ingot_fe=10)
# physics devices
C("funnel", 1, "machine", 1, plate_fe=6)
C("chute", 1, "machine", 1, plate_fe=4, rod_fe=2)
C("blower", 1, "machine", 3, frame=1, motor=1, plate_fe=6)
C("lift", 1, "machine", 3, frame=2, motor=1, plate_fe=10)
C("launcher", 1, "machine", 3, frame=1, motor=1, plate_steel=4)
C("pusher", 1, "machine", 3, frame=1, motor=1)
# supply
C("extractor_empty", 1, "machine", 1, stone=40, ingot_fe=30, plank=10, monster_part=1,
  note="확정된 구성: 돌, 철 주괴, 나무, 몬스터 부품 하나")
C("extractor_fe", 1, "bag", 0, extractor_empty=1, core_fe=1, note="핵을 꽂음")
C("extractor_coal", 1, "bag", 0, extractor_empty=1, core_coal=1, note="핵을 꽂음")
C("logger", 1, "machine", 1, frame=1, gear=2, plate_fe=4)
C("harvester", 1, "machine", 1, frame=1, gear=2, plank=10)
C("seeder", 1, "machine", 1, frame=1, gear=1, plank=6)
C("sprinkler", 1, "machine", 1, rod_fe=4, plate_cu=2)
C("pump", 1, "machine", 2, frame=1, rod_fe=8, plate_cu=4)
C("pumpjack", 1, "machine", 3, frame=4, motor=2, plate_steel=20)
# processing
C("crusher", 1, "machine", 1, frame=1, gear=4, stone_block=10)
C("sawmill", 1, "machine", 1, frame=1, gear=2, plate_fe=4)
C("stonecutter", 1, "machine", 1, frame=1, plate_fe=6)
C("kiln", 1, "machine", 1, brick=30, plate_fe=4)
C("mill", 1, "machine", 1, frame=1, plank=20, stone_block=4, cloth=4)
C("sieve", 1, "machine", 1, frame=1, rod_fe=6, cloth=4)
C("briquetter", 1, "machine", 1, frame=1, plate_fe=6)
C("oilpress", 1, "machine", 1, frame=1, gear=2, plate_fe=4)
C("loom", 1, "machine", 1, frame=1, plank=16, rod_fe=4)
C("smelter", 1, "machine", 2, frame=4, brick=60, plate_fe=60, ingot_au=10,
  note="귀하고 만들기 어려운 기계. 금은 허브에서만 나옴")
C("washer", 1, "machine", 2, frame=1, plate_cu=8, rod_fe=6)
C("press", 1, "machine", 2, frame=2, plate_fe=20, ingot_steel=10)
C("wiredraw", 1, "machine", 2, frame=1, gear=4, ingot_steel=6)
C("lathe", 1, "machine", 2, frame=1, gear=6, ingot_steel=6)
C("caster", 1, "machine", 2, frame=2, brick=20, ingot_steel=10)
C("mixer", 1, "machine", 2, frame=1, plate_fe=12, gear=2)
C("oven", 1, "machine", 2, frame=1, brick=30, plate_fe=6)
C("blast", 1, "machine", 2, frame=10, brick=200, plate_steel=40, note="두 칸 폭의 큰 기계")
C("alloy", 1, "machine", 2, frame=2, brick=40, ingot_steel=20)
C("refinery", 1, "machine", 3, frame=6, plate_steel=40, rod_steel=30, motor=2)
C("gemcutter", 1, "machine", 3, frame=1, motor=1, blade=1, glass=4)
C("recycler", 1, "machine", 3, frame=2, motor=1, gear=8)
C("painter", 1, "machine", 3, frame=1, motor=1, glass=6)
C("assembler", 1, "machine", 3, frame=2, motor=2, board=2)
C("circuit", 1, "machine", 3, frame=2, motor=1, board=4, glass=8)
C("manufacturer", 1, "machine", 3, frame=10, motor=6, board=6, plate_steel=40)
# packing and trade
C("packer", 1, "machine", 2, frame=1, gear=2, plank=10)
C("vending", 1, "machine", 2, frame=2, glass=8, ingot_au=4)
# power
C("pole", 2, "elec", 1, log=2, coil=4, glass=1)
C("generator", 1, "elec", 1, frame=2, coil=30, plate_fe=10)
C("battery", 1, "elec", 2, frame=1, cell=8, plate_cu=4)
C("windturbine", 1, "elec", 2, frame=2, motor=1, plate_steel=6)
C("solar", 1, "elec", 2, glass=8, board=2, plate_steel=4)
C("incinerator", 1, "machine", 2, frame=1, brick=30, coil=10)
# logic
C("switch", 1, "elec", 1, plate_fe=2, coil=2)
C("beacon", 1, "elec", 1, rod_fe=2, glass=3, coil=2)
C("sensor", 1, "elec", 2, rod_fe=4, board=1, glass=1)
C("gate", 1, "elec", 2, rod_fe=4, plate_fe=2, motor=1)
C("counter", 1, "elec", 2, rod_fe=2, board=1)
C("timer", 1, "elec", 2, plate_fe=2, board=1)
C("logic", 1, "elec", 3, plate_fe=2, board=2)
# the big goal
C("coreforge", 1, "all", 0, plate_steel=2000, motor=300, board_adv=300, ingot_au=1000, diamond=200,
  monster_part=50, core_fe=10, core_coal=10, core_cu=10, core_stone=10)
C("reactor", 1, "all", 0, plate_steel=3000, board_adv=500, cell=1000, wire_au=2000, diamond=500, motor=500)

# blocks made from items
C("block:planks", 1, "basic", 1, plank=4)
C("block:stone_bricks", 1, "basic", 1, stone_block=4)
C("block:bricks", 1, "basic", 1, brick=4)
C("block:glass", 1, "basic", 1, glass=4)
C("block:concrete", 1, "basic", 1, concrete=4)
C("block:asphalt", 1, "basic", 1, asphalt=4)
C("block:sand", 1, "basic", 1, sand=4)
C("block:gravel", 1, "basic", 1, gravel=4)
C("block:clay", 1, "basic", 1, clay=4)
C("block:farmland", 1, "bag", 0, note="괭이로 흙을 갈아 만듦", block__dirt=1)
C("block:block_fe", 1, "basic", 1, ingot_fe=9)
C("block:block_cu", 1, "basic", 1, ingot_cu=9)
C("block:block_steel", 1, "basic", 1, ingot_steel=9)
C("block:block_au", 1, "basic", 1, ingot_au=9)
C("block:block_dia", 1, "basic", 1, diamond=9)
C("block:block_coal", 1, "basic", 1, coal=9)
C("block:tread", 4, "part", 1, plate_fe=4)
C("block:grating", 4, "part", 1, rod_fe=4)
for colour in ("white", "red", "yellow", "green", "blue"):
    C(f"block:cloth_{colour}", 1, "furn", 1, cloth=4, note="" if colour == "white" else "염료는 미정")

# ---------------------------------------------------------------- workbench tiers
# Tier 1 is the cost of making the bench (above). These are the costs of raising it.
UPGRADES = {
    ("basic", 2): dict(plank=40, stone=40, ingot_fe=20),
    ("basic", 3): dict(plate_fe=150, stone_block=100, ingot_steel=40),
    ("tool", 2): dict(ingot_fe=150, plate_fe=40),
    ("tool", 3): dict(ingot_steel=200, ingot_au=30, diamond=10),
    ("part", 2): dict(plate_fe=100, rod_fe=100, gear=20),
    ("part", 3): dict(plate_steel=150, motor=10),
    ("machine", 2): dict(ingot_fe=200, frame=10, gear=20),
    ("machine", 3): dict(ingot_steel=300, motor=30, board=30),
    ("cook", 2): dict(brick=40, plate_fe=20),
    ("cook", 3): dict(plate_steel=30, glass=40),
    ("elec", 2): dict(ingot_steel=150, board=30, coil=200),
    ("elec", 3): dict(wire_au=100, board=100, cell=40),
    ("furn", 2): dict(plank=100, cloth=20, glass=20),
    ("furn", 3): dict(ingot_steel=20, cloth=100, glass=100),
}

# ---------------------------------------------------------------- checks
problems = []


def known(key):
    return key in NAMES


for p in PROCESS:
    for key in list(p["ins"]) + list(p["outs"]) + [p["machine"]] + ([p["tool"]] if p["tool"] else []):
        if not known(key):
            problems.append(f"공정이 모르는 이름을 씀: {key}")
    if p["hand"] not in (None, "bag") and not known(p["hand"]):
        problems.append(f"공정의 손 작업 자리가 없음: {p['hand']}")
for c in CRAFT:
    for key in list(c["ins"]) + [c["out"]]:
        if not known(key):
            problems.append(f"조합이 모르는 이름을 씀: {key}")
for (bench, tier), cost in UPGRADES.items():
    for key in cost:
        if not known(key):
            problems.append(f"작업대 등급이 모르는 이름을 씀: {key}")
for key in list(RAW) + list(FUEL) + FUEL_USERS + NEEDS_POWER:
    if not known(key):
        problems.append(f"목록이 모르는 이름을 씀: {key}")


def reachable(hand_only):
    """Everything obtainable from the raw sources. With hand_only, machines may not be used."""
    have = set(RAW)
    tiers = {}  # bench kind -> highest tier reached
    changed = True
    while changed:
        changed = False
        for kind, key in BENCH.items():
            if key in have and tiers.get(kind, 0) < 1:
                tiers[kind] = 1
                changed = True
        for (kind, tier), cost in UPGRADES.items():
            if tiers.get(kind, 0) == tier - 1 and all(k in have for k in cost):
                tiers[kind] = tier
                changed = True
        if "wb_all" in have and not tiers.get("all"):
            tiers["all"] = 1
            changed = True
        for c in CRAFT:
            if c["out"] in have or not all(k in have for k in c["ins"]):
                continue
            ok = c["bench"] == "bag" or tiers.get(c["bench"], 0) >= max(c["tier"], 1)
            if c["out"] == "wb_all":
                ok = ok and all(tiers.get(k, 0) >= 3 for k in BENCH)
            if ok:
                have.add(c["out"])
                changed = True
        for p in PROCESS:
            if all(k in have for k in p["outs"]) or not all(k in have for k in p["ins"]):
                continue
            by_machine = not hand_only and p["machine"] in have
            by_hand = p["hand"] == "bag" or (p["hand"] in have and (not p["tool"] or p["tool"] in have))
            if by_machine or by_hand:
                have.update(p["outs"])
                changed = True
    return have, tiers


everything, _ = reachable(False)
by_hand, hand_tiers = reachable(True)
ultimate_only = {"core_au", "core_dia"}
no_source = sorted(k for k in list(ITEM) + list(MACHINE) + list(BLOCK) if k not in everything)
not_by_hand = sorted(k for k in ITEM if k in everything and k not in by_hand)

routes = {}
for p in PROCESS:
    for out in p["outs"]:
        routes.setdefault(out, []).append(p)
for c in CRAFT:
    routes.setdefault(c["out"], []).append(c)
several = sorted(k for k, v in routes.items() if len(v) >= 2 and k in ITEM)

# ---------------------------------------------------------------- write the document
def ko(key):
    return NAMES.get(key, key)


def amounts(d):
    return ", ".join(f"{ko(k)} {v}" for k, v in d.items()) if d else "-"


def bench_text(c):
    if c["bench"] == "bag":
        return "가방"
    if c["bench"] == "all":
        return "통합 작업대"
    return f"{BENCH_KO[c['bench']]} {c['tier']}단계"


def hand_text(p):
    if p["hand"] is None:
        return "-"
    where = "가방" if p["hand"] == "bag" else ko(p["hand"])
    return where + (f" + {ko(p['tool'])}" if p["tool"] else "")


L = []
A = L.append
A("# 레시피 초안\n")
A("무엇을 넣으면 무엇이 나오는지, 무엇을 만들려면 무엇이 몇 개 필요한지를 적은 표입니다. "
  "마인크래프트처럼 칸에 배치하는 방식이 아니라 **아이템과 개수만** 있습니다.\n")
A("- 이 문서는 `data/recipes.py`에서 자동으로 만들어집니다. 고칠 때는 그 파일을 고치고 `python3 data/recipes.py`를 실행합니다.")
A("- **숫자는 전부 초안입니다.** 실제로 해 보면서 조정할 값입니다.")
A("- 상인에게 사고파는 값은 적지 않았습니다. 파는 구조는 개발자가 직접 설계하기로 했습니다.")
A("- 전체 설계는 [게임 설계 문서](game-design.md)에 있습니다.\n")

A("## 1. 이 표를 짠 규칙\n")
A("| 규칙 | 내용 |")
A("|---|---|")
A("| 철이 기본 | 벨트든 기계든 철이 대량으로 들어갑니다. 여기에 그 기계의 성격을 정하는 재료가 조금 붙습니다. |")
A("| 손으로도 다 된다 | 기계가 하는 가공은 손 작업 자리에서도 똑같이 할 수 있습니다. 나오는 양도 같습니다. 기계는 그 일을 대신해 줄 뿐입니다. |")
A("| 양으로 미는 관문 | 작업대 등급과 큰 기계는 재료를 수백 개 요구합니다. 손으로도 모을 수 있지만 공장이 있으면 훨씬 쉽습니다. |")
A("| 길이 여러 갈래 | 같은 물건을 만드는 방법을 둘 이상 두려고 했습니다. 아래 9절에 목록이 있습니다. |")
A("| 귀한 것은 허브에서 | 금과 다이아는 추출기로 얻을 수 없습니다. 제련로처럼 중요한 기계에 금이 들어갑니다. |")
A("")

A("## 2. 처음 생기는 곳\n")
A("| 아이템 | 얻는 곳 |")
A("|---|---|")
for key, where in RAW.items():
    if not key.startswith("block:"):
        A(f"| {ko(key)} | {where} |")
A("")

A("## 3. 연료\n")
A("연료 하나로 제련을 몇 번 할 수 있는지입니다. 연료를 쓰는 기계는 어떤 연료든 받습니다.\n")
A("| 연료 | 제련 횟수 | 얻는 길 |")
A("|---|---|---|")
fuel_from = {"log": "나무", "charcoal": "통나무를 가마에 구움", "coal": "허브 광산, 석탄 추출기",
             "briquette": "톱밥을 압축", "oilcan": "기름 작물을 압착", "barrel_fuel": "원유를 정유"}
for key, n in FUEL.items():
    A(f"| {ko(key)} | {n} | {fuel_from[key]} |")
A("")
A("연료를 쓰는 것: " + ", ".join(ko(k) for k in FUEL_USERS) + "\n")
A("전기가 있어야 도는 것: " + ", ".join(ko(k) for k in NEEDS_POWER) + "\n")

A("## 4. 작업대\n")
A("작업대는 일곱 종이고 각각 3단계까지 올립니다. 1단계는 작업대를 처음 만드는 비용입니다.\n")
A("| 작업대 | 1단계 (만들기) | 2단계 | 3단계 |")
A("|---|---|---|---|")
for kind, key in BENCH.items():
    make = next(c for c in CRAFT if c["out"] == key)
    A(f"| {ko(key)} | {amounts(make['ins'])} ({bench_text(make)}) | {amounts(UPGRADES[(kind, 2)])} | {amounts(UPGRADES[(kind, 3)])} |")
wb_all = next(c for c in CRAFT if c["out"] == "wb_all")
A(f"| {ko('wb_all')} | {amounts(wb_all['ins'])} | - | - |")
A("")
A("통합 작업대는 일곱 작업대를 모두 3단계로 올린 뒤에 기계 작업대에서 만듭니다.\n")

A("## 5. 가공: 하나가 다른 것이 되는 과정\n")
A("같은 가공을 손으로 할 수도, 기계로 할 수도 있습니다. 시간은 기계 기준이고 단위는 초입니다.\n")
kinds = []
for p in PROCESS:
    if p["kind"] not in kinds:
        kinds.append(p["kind"])
for kind in kinds:
    A(f"### {kind}\n")
    A("| 넣는 것 | 나오는 것 | 기계 | 손으로 | 시간 | 비고 |")
    A("|---|---|---|---|---|---|")
    for p in PROCESS:
        if p["kind"] == kind:
            A(f"| {amounts(p['ins'])} | {amounts(p['outs'])} | {ko(p['machine'])} | {hand_text(p)} | {p['secs']} | {p['note']} |")
    A("")
A("포장기는 같은 아이템 8개를 상자 하나로 묶습니다. 분해기는 기계나 부품을 넣으면 들어간 재료의 절반을 돌려줍니다. 도색기의 염료는 아직 정하지 않았습니다.\n")


def craft_table(title, keys, lede=""):
    rows = [c for c in CRAFT if c["out"] in keys]
    if not rows:
        return
    A(f"### {title}\n")
    if lede:
        A(lede + "\n")
    A("| 만드는 것 | 수량 | 재료 | 만드는 곳 | 비고 |")
    A("|---|---|---|---|---|")
    for c in rows:
        A(f"| {ko(c['out'])} | {c['n']} | {amounts(c['ins'])} | {bench_text(c)} | {c['note']} |")
    A("")


A("## 6. 부품과 도구\n")
A("작업대에서 만드는 것들입니다. 조립기를 지으면 같은 레시피가 자동으로 돌아갑니다.\n")
craft_table("부품과 조립품", {"frame", "motor", "cell", "board", "board_adv"})
A("### 도구\n")
A("곡괭이, 도끼, 삽, 괭이, 검은 머리 재료와 자루 재료로 만듭니다. 머리 재료의 개수는 곡괭이 3, 도끼 3, 삽 1, 괭이 2, 검 2이고 자루는 2개입니다.\n")
A("| 등급 | 머리 | 자루 | 만드는 곳 |")
A("|---|---|---|---|")
tier_ko = {"wood": "나무", "stone": "돌", "iron": "철", "steel": "강철", "gold": "금", "dia": "다이아"}
for tier, head, handle, bench, level in TIERS:
    A(f"| {tier_ko[tier]} | {ko(head)} | {ko(handle)} | {'가방' if bench == 'bag' else BENCH_KO[bench] + ' ' + str(level) + '단계'} |")
A("")
craft_table("그 밖의 도구", {"hammer", "wrench", "bucket", "watering_can", "fishing_rod"})

A("## 7. 기계 만들기\n")
fams = []
for m in catalog["machines"]:
    if m["fam"] not in fams:
        fams.append(m["fam"])
for fam in fams:
    craft_table(fam, {m["key"] for m in catalog["machines"] if m["fam"] == fam})

A("## 8. 블록\n")
craft_table("아이템으로 만드는 블록", set(BLOCK))
A("땅에서 나오는 블록: " + ", ".join(ko(k).replace(" (블록)", "") for k in RAW if k.startswith("block:")) + "\n")

A("## 9. 길이 여러 갈래인 것\n")
A("만드는 방법이 둘 이상인 아이템입니다.\n")
A("| 아이템 | 방법 수 | 방법 |")
A("|---|---|---|")
for key in several:
    ways = []
    for r in routes[key]:
        ways.append(amounts(r["ins"]) + (f" ({ko(r['machine'])})" if "machine" in r else f" ({bench_text(r)})"))
    A(f"| {ko(key)} | {len(ways)} | {' / '.join(ways)} |")
A("")
A("철 주괴 하나를 얻는 세 가지 길을 비교하면 이렇습니다.\n")
A("| 길 | 거치는 것 | 광석 1개당 주괴 |")
A("|---|---|---|")
A("| 바로 녹이기 | 제련로 | 1 |")
A("| 부숴서 녹이기 | 분쇄기, 제련로 | 1.3 |")
A("| 부수고 씻어서 녹이기 | 분쇄기, 세척기(물 필요), 제련로 | 2 (찌꺼기도 나옴) |")
A("")

A("## 10. 자동 점검 결과\n")
A("이 문서를 만들 때마다 아래를 확인합니다.\n")
A("| 점검 | 결과 |")
A("|---|---|")
A(f"| 레시피가 카탈로그에 없는 이름을 쓰는가 | {'없음' if not problems else str(len(problems)) + '건'} |")
A(f"| 얻을 길이 없는 아이템, 기계, 블록 | {'없음' if not no_source else str(len(no_source)) + '개'} |")
A(f"| 기계 없이 손으로만 해도 모든 아이템을 만들 수 있는가 | {'예' if not [k for k in not_by_hand if k not in ultimate_only] else '아니오'} |")
A(f"| 손으로만 올릴 수 있는 작업대 등급 | {', '.join(BENCH_KO[k] + ' ' + str(v) + '단계' for k, v in hand_tiers.items() if k != 'all')} |")
A("")
if problems:
    A("모르는 이름:\n")
    for line in sorted(set(problems)):
        A(f"- {line}")
    A("")
if no_source:
    A("얻을 길이 없는 것:\n")
    for key in no_source:
        A(f"- {ko(key)}")
    A("")
leftover = [k for k in not_by_hand if k not in ultimate_only]
if leftover:
    A("손으로는 만들 수 없는 것:\n")
    for key in leftover:
        A(f"- {ko(key)}")
    A("")
A("금 광맥 핵과 다이아 광맥 핵은 핵 제련소에서만 나옵니다. 설계에서 정한 대로이고, 손으로 얻는 길이 없는 유일한 예외입니다.\n")

A("## 11. 정해야 할 것\n")
A("표를 짜면서 임의로 가정한 부분입니다.\n")
A("- **손으로 만들 때와 기계로 만들 때 나오는 양을 같게 두었습니다.** 기계가 더 많이 내게 할지는 정한 적이 없습니다.")
A("- **손으로 부품을 만들 때 망치를 들게 했습니다.** 손 작업을 조금 더 번거롭게 하려는 장치입니다.")
A("- **물을 손으로 어떻게 얻는지**를 정하지 않았습니다. 지금은 물 펌프가 있어야 물통이 나옵니다. 그래서 물이 드는 것(점토, 콘크리트, 반죽, 정제 광석)은 물 펌프를 만들기 전에는 손으로도 만들 수 없습니다.")
A("- **원유를 어디서 얻는지**를 정하지 않았습니다.")
A("- **블록과 아이템의 관계.** 돌 블록을 부수면 돌 아이템이 나오는지, 블록 그대로 나오는지를 정하지 않았습니다. 지금은 땅에서 나오는 블록과 같은 이름의 아이템을 따로 두고 있습니다.")
A("- **염료.** 색 블록과 도색기에 쓸 염료가 없습니다.")
A("- **석영**을 어디서 얻는지 정하지 않았습니다.")
A("- **구리 광맥 핵을 꽂은 추출기, 돌 광맥 핵을 꽂은 추출기**는 카탈로그에 그림이 없습니다. 철과 석탄만 있습니다.")
A("- 제련로에 금 주괴 10개를 넣었습니다. 원작의 제강소에 금이 들어갔던 것을 따른 것으로, 첫 제련로를 만들기 전에 허브에서 금을 캐서 손 화덕으로 녹여야 합니다.")
A("- 기계 작업대 2단계에 철 주괴 200개를 넣었습니다. 원작의 3단계 작업대가 400개였습니다.")
A("")

open(os.path.join(ROOT, "docs", "recipes.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
json.dump({"raw": RAW, "fuel": FUEL, "fuel_users": FUEL_USERS, "needs_power": NEEDS_POWER, "process": PROCESS,
           "craft": CRAFT, "upgrades": {f"{k}:{t}": v for (k, t), v in UPGRADES.items()}},
          open(os.path.join(HERE, "recipes.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

print(f"공정 {len(PROCESS)}개, 조합 {len(CRAFT)}개")
print("모르는 이름:", sorted(set(problems)) or "없음")
print("얻을 길 없음:", [ko(k) for k in no_source] or "없음")
print("손으로 불가:", [ko(k) for k in not_by_hand] or "없음")
print("손으로 오르는 작업대:", hand_tiers)
missing_machines = sorted(k for k in MACHINE if not any(c["out"] == k for c in CRAFT))
print("만드는 법이 없는 기계:", [ko(k) for k in missing_machines] or "없음")
sys.exit(1 if problems else 0)
