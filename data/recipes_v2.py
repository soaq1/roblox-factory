# -*- coding: utf-8 -*-
# 레시피 초안 v2 (제안). 기계 13종과 핵 제련소, 깊은 사슬, 상자로 뭉치기.
# 설계 문서 8.19~8.21절에 따라 다시 짠 것이고, 게임에는 아직 들어가지 않습니다. 게임이 읽는 것은 여전히 recipes.py 입니다.
# 실행:  python3 data/recipes_v2.py   ->  data/recipes_v2.json, docs/recipes-v2.md
import collections, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
old = json.load(open(os.path.join(HERE, "recipes.json"), encoding="utf-8"))
catalog = json.load(open(os.path.join(ROOT, "art", "catalog", "catalog.json"), encoding="utf-8"))
KO = {i["key"]: i["ko"] for i in catalog["items"]}
KO.update({m["key"]: m["ko"] for m in catalog["machines"]})
KO.update({"barrel_water": "물통", "oilcan": "식물 기름", "lube": "윤활유", "electrolyte": "전해액", "plate_r": "강화판",
           "magnet": "전자석", "frame_steel": "강철 틀", "extractor_empty": "빈 추출기", "wb_all": "통합 작업대",
           "belt_corner_l": "코너 벨트 (왼쪽)", "extractor_cu": "추출기 (구리 광맥 핵)"})
NEW_ITEMS = ["lube", "electrolyte", "plate_r", "magnet", "frame_steel"]

CRATE = 50          # 임시: 같은 물건 몇 개가 한 상자가 되는가 (v1 초안은 8)

# 기계: (키, 이름, 급, 동작)
MACHINES = [("extractor", "추출기", 1, "광맥 핵에서 원석을 내놓음"), ("logger", "벌목기", 1, "곁의 나무를 통나무로 내놓음"),
            ("harvester", "수확기", 2, "밭에서 다 자란 것을 내놓음"), ("pump", "물 펌프", 2, "물을 끌어올려 내놓음"),
            ("crusher", "분쇄기", 1, "부숨"), ("washer", "세척기", 2, "씻음"), ("smelter", "용광로", 2, "녹이고 구움"),
            ("former", "성형기", 2, "끼운 틀대로 모양을 냄"), ("cutter", "절단기", 1, "자름"),
            ("mixer", "혼합기", 3, "섞음"), ("blast", "제철소", 3, "함께 녹여 합금으로"), ("assembler", "조립기", 3, "부품을 합침"),
            ("packer", "포장기", 2, "상자로 뭉침"), ("coreforge", "핵 제련소", 0, "광맥 핵을 만듦 (큰 목표)")]
MK = {k: ko for k, ko, _, _ in MACHINES}
KO.update(MK)

RAW = {
    "stone": "섬의 땅을 팜 · 돌 광맥 핵을 꽂은 추출기", "coal": "허브 광산 · 석탄 광맥 핵을 꽂은 추출기",
    "ore_cu": "허브 광산 · 구리 광맥 핵을 꽂은 추출기", "ore_fe": "허브 광산 · 철 광맥 핵을 꽂은 추출기",
    "ore_au": "허브 광산에서만 (핵 제련소가 있으면 금 광맥 핵)", "ore_dia": "허브 광산에서만 (핵 제련소가 있으면 다이아 광맥 핵)",
    "log": "나무를 벰 · 벌목기", "cotton": "밭에서 기름 · 수확기", "oilseed": "밭에서 기름 · 수확기", "barrel_water": "물 펌프",
    "dirt_clod": "섬의 땅을 팜", "monster_part": "몬스터를 잡아 낮은 확률로", "seed": "농부에게서 삼", "sapling": "농부에게서 삼",
}
SOURCES = {"extractor": ["stone", "coal", "ore_cu", "ore_fe"], "logger": ["log"], "harvester": ["cotton", "oilseed"],
           "pump": ["barrel_water"]}
FUEL = {"log": 1, "charcoal": 3, "coal": 4, "briquette": 4, "oilcan": 12}
FUEL_USERS = ["smelter", "blast"]

PROCESS = []


def P(machine, kind, ins, outs, secs, note=""):
    PROCESS.append({"machine": machine, "kind": kind, "ins": ins, "outs": outs, "secs": secs, "note": note})


def crate(item):
    return "crate:" + item


def name(k):
    if k.startswith("crate:"):
        return name(k[6:]) + " 상자"
    if k.startswith("block:"):
        return KO.get(k, k[6:] + " 블록")
    return KO.get(k, k)


# 성형기에 끼우는 틀 (설계 문서 8.23절). 틀을 얻는 법과 틀을 만드는 재료는 미정.
MOULDS = {"판 틀": "주괴를 눌러 판으로", "막대 틀": "주괴를 뽑아 막대와 들보로", "선 틀": "주괴를 가늘게 뽑아 선으로",
          "볼트 틀": "막대를 끊어 볼트로", "기어 틀": "판을 따 내어 기어로"}

# 겹 1. 늘리고 걸러 낸다
for m in ("fe", "cu", "au"):
    c = "crushed" if m == "cu" else "crushed_" + m
    P("crusher", "분쇄", {"ore_" + m: 1}, {c: 2}, 2)
P("crusher", "분쇄", {"stone": 1}, {"gravel": 1}, 2)
P("crusher", "분쇄", {"gravel": 1}, {"sand": 1}, 2)
for m in ("fe", "cu", "au"):
    c, k = ("crushed", "clean") if m == "cu" else ("crushed_" + m, "clean_" + m)
    P("washer", "세척", {c: 8, "barrel_water": 1}, {k: 8, "slag": 2}, 6, "찌꺼기는 콘크리트의 재료")
# 겹 2. 녹인다
for m in ("fe", "cu", "au"):
    c, k = ("crushed", "clean") if m == "cu" else ("crushed_" + m, "clean_" + m)
    P("smelter", "가열", {"ore_" + m: 1}, {"ingot_" + m: 1}, 3, "가장 짧은 길")
    P("smelter", "가열", {c: 3}, {"ingot_" + m: 2}, 3, "부수면 1.3배")
    P("smelter", "가열", {k: 1}, {"ingot_" + m: 1}, 3, "부수고 씻으면 2배")
P("smelter", "가열", {"sand": 2}, {"glass": 1}, 3)
P("smelter", "가열", {"clay": 1}, {"brick": 1}, 3)
P("smelter", "가열", {"log": 1}, {"charcoal": 1}, 3, "석탄이 없을 때의 연료")
# 겹 3. 모양을 낸다
for m in ("fe", "cu", "steel"):
    P("former", "판 틀", {"ingot_" + m: 1}, {"plate_" + m: 1}, 2)
for m in ("fe", "cu", "steel"):
    P("former", "막대 틀", {"ingot_" + m: 1}, {"rod_" + m: 2}, 2)
P("former", "막대 틀", {"ingot_steel": 2}, {"beam": 1}, 4)
P("former", "선 틀", {"ingot_cu": 1}, {"coil": 2}, 2)
P("former", "선 틀", {"ingot_au": 1}, {"wire_au": 2}, 2)
P("former", "볼트 틀", {"rod_fe": 1}, {"bolt": 4}, 2)
P("former", "기어 틀", {"plate_fe": 1}, {"gear": 1}, 3)
# 프레스가 하던 일 가운데 쇠가 아닌 것. 성형기가 판 틀로 맡아 두었지만 어느 기계의 일인지는 정해야 함.
OPEN_NOTE = "쇠가 아닌 것을 누르는 일. 어느 기계가 맡을지 미정"
P("former", "판 틀", {"oilseed": 4}, {"oilcan": 1}, 4, "연료이자 윤활유의 원료. " + OPEN_NOTE)
P("former", "판 틀", {"cotton": 2}, {"cloth": 1}, 3, OPEN_NOTE)
P("former", "판 틀", {"sawdust": 4}, {"briquette": 1}, 3, "부산물이 연료가 됨. " + OPEN_NOTE)
P("cutter", "자르기", {"log": 1}, {"plank": 4, "sawdust": 1}, 2)
P("cutter", "자르기", {"stone": 1}, {"stone_block": 1}, 2)
P("cutter", "자르기", {"ore_dia": 1}, {"diamond": 1}, 6)
# 겹 4. 섞는다
P("mixer", "섞기", {"oilcan": 1, "charcoal": 1}, {"lube": 2}, 4, "모터에 들어감")
P("mixer", "섞기", {"barrel_water": 1, "charcoal": 2, "clean": 1}, {"electrolyte": 2}, 4, "전지에 들어감. 씻은 구리 가루로만 만듦")
P("mixer", "섞기", {"gravel": 2, "slag": 1, "barrel_water": 1}, {"concrete": 4}, 4, "큰 기계의 기초")
P("mixer", "섞기", {"dirt_clod": 4, "barrel_water": 1}, {"clay": 4}, 4, "벽돌의 원료")
# 겹 7. 강철
P("blast", "합금", {"ingot_fe": 4, "coal": 2}, {"ingot_steel": 4}, 8, "철 주괴를 석탄과 함께 한 번 더 구움. 손으로는 손 화덕에서")
P("blast", "합금", {"ingot_fe": 4, "charcoal": 3}, {"ingot_steel": 4}, 8, "석탄 없이 만드는 길")
P("blast", "합금", {"ingot_cu": 1, "ingot_au": 1}, {"ingot_alloy": 2}, 8)
# 겹 5~7. 부품 (조립기. 손으로는 부품 작업대와 전기 작업대에서)
PARTS = [("frame", {"plate_fe": 2, "rod_fe": 2}, "거의 모든 기계의 뼈대"), ("plate_r", {"plate_fe": 2, "bolt": 4}, "볼트로 죈 두 겹 철판"),
         ("magnet", {"coil": 4, "rod_fe": 1}, "철심에 구리선을 감음"), ("board", {"coil": 3, "glass": 1}, ""),
         ("cell", {"rod_cu": 1, "plate_fe": 1, "electrolyte": 1}, "구리 막대가 극이 됨"),
         ("motor", {"magnet": 2, "gear": 2, "frame": 1, "lube": 1}, "재료 네 줄이 만남"),
         ("frame_steel", {"beam": 2, "plate_r": 2, "rod_steel": 4}, "후반 기계의 뼈대"),
         ("board_adv", {"board": 2, "wire_au": 4, "ingot_alloy": 1}, "")]
for out, ins, note in PARTS:
    P("assembler", "조립", ins, {out: 1}, 4, note)

# 기계를 만드는 재료 (기계 작업대). 1급은 얕은 재료만, 2급은 기계 틀과 강화판, 3급은 모터·회로·강철 틀.
BUILD = {
    "extractor_empty": (1, {"stone": 40, "ingot_fe": 30, "plank": 10, "monster_part": 1}, "확정된 구성. 여기에 광맥 핵을 꽂음"),
    "logger": (1, {"plate_fe": 8, "rod_fe": 4, "gear": 2}, ""),
    "crusher": (1, {"plate_fe": 8, "gear": 4, "stone_block": 10}, ""),
    "cutter": (1, {"plate_fe": 6, "rod_fe": 4, "gear": 2}, ""),
    "smelter": (2, {"frame": 4, "brick": 40, "ingot_steel": 20, "ingot_au": 10, "monster_part": 1},
                "얻기 힘든 기계 (설계 문서 8.11절). 손으로 만든 강철, 허브의 금, 몬스터의 부품이 모두 듦"),
    "former": (2, {"frame": 4, "plate_r": 6, "gear": 8, "rod_fe": 12},
               "프레스와 롤러를 합친 큰 기계(3×2칸). 재료는 손 작업 자리에서 만들어 첫 대를 지음. 틀은 따로 듦"),
    "washer": (2, {"frame": 1, "plate_cu": 8, "glass": 4}, ""),
    "pump": (2, {"frame": 1, "rod_fe": 8, "plate_cu": 4}, ""),
    "harvester": (2, {"frame": 1, "gear": 2, "plank": 10}, ""),
    "packer": (2, {"frame": 1, "plate_r": 2, "plank": 10}, ""),
    "mixer": (2, {"frame": 2, "gear": 4, "plate_cu": 12, "glass": 6}, ""),
    "blast": (2, {"frame": 10, "plate_r": 20, "brick": 200, "concrete": 60}, "큰 기계. 콘크리트 기초가 필요"),
    "assembler": (3, {"frame_steel": 2, "motor": 4, "board": 4}, ""),
    "coreforge": (3, {crate("frame_steel"): 4, crate("motor"): 4, crate("board_adv"): 2, crate("concrete"): 10}, "큰 목표. 상자째로 요구"),
}
# 핵 제련소: 상자를 받아 광맥 핵을 만든다. 수량은 전부 임시.
for core, ins in (("core_stone", {crate("stone_block"): 40, "diamond": 1}), ("core_coal", {crate("coal"): 40, "diamond": 2}),
                  ("core_cu", {crate("ingot_cu"): 20, "diamond": 2}), ("core_fe", {crate("ingot_fe"): 20, "diamond": 2}),
                  ("core_au", {crate("ingot_au"): 20, "diamond": 10}), ("core_dia", {crate("ingot_steel"): 20, crate("diamond"): 10})):
    P("coreforge", "핵 제련", ins, {core: 1}, 600, "임시 값")

# v1에서 물려받는 조합: 도구, 블록, 가구, 가방, 전기 장치, 운반·장치류 기계. 빠진 기계와 위에서 다시 정한 것은 제외.
REDEFINED = set(BUILD) | {p[0] for p in PARTS}
DROPPED = {"kiln", "oven", "mill", "briquetter", "oilpress", "stonecutter", "sawmill", "wiredraw", "lathe", "caster", "loom",
           "gemcutter", "recycler", "painter", "sieve", "refinery", "pumpjack", "circuit", "manufacturer", "alloy", "seeder",
           "sprinkler", "extractor_fe", "extractor_coal", "extractor_cu"}
CRAFT = []
for out, (tier, ins, note) in BUILD.items():
    CRAFT.append({"out": out, "n": 1, "bench": "machine", "tier": tier, "ins": ins, "note": note})
for core, ko_ in (("stone", "돌"), ("coal", "석탄"), ("cu", "구리"), ("fe", "철"), ("au", "금"), ("dia", "다이아")):
    KO["extractor_" + core] = f"추출기 ({ko_} 광맥 핵)"
    CRAFT.append({"out": "extractor_" + core, "n": 1, "bench": "bag", "tier": 0, "ins": {"extractor_empty": 1, "core_" + core: 1}, "note": "핵을 꽂음"})
carried = [c for c in old["craft"] if c["out"] not in REDEFINED and c["out"] not in DROPPED]

# 큰 수량을 요구하는 관문은 상자로 받는다 (작업대 3단계 승급과 통합 작업대).
UPGRADES = {}
for k, need in old["upgrades"].items():
    UPGRADES[k] = {(crate(i) if k.endswith(":3") and n >= 100 else i): (n // CRATE if k.endswith(":3") and n >= 100 else n) for i, n in need.items()}
for c in carried:
    if c["out"] == "wb_all":
        c = dict(c, ins={(crate(i) if n >= 50 else i): (max(1, n // CRATE) if n >= 50 else n) for i, n in c["ins"].items()})
    CRAFT.append(c)

# 상자: 포장기가 같은 물건 CRATE개를 한 상자로. 실제로 요구되는 상자만 레시피로 적는다(규칙은 모든 물건에 같음).
wanted = collections.OrderedDict()
for src in [r["ins"] for r in PROCESS] + [c["ins"] for c in CRAFT] + list(UPGRADES.values()):
    for i in src:
        if i.startswith("crate:"):
            wanted[i] = 1
for c in wanted:
    P("packer", "포장", {c[6:]: CRATE}, {c: 1}, 5)

# 만들 수 있는지와 깊이(원료에서 몇 단계인가)
depth = {i: 0 for i in RAW}
recs = [(r["ins"], r["outs"]) for r in PROCESS] + [(c["ins"], {c["out"]: c["n"]}) for c in CRAFT]
for _ in range(40):
    for ins, outs in recs:
        if all(i in depth for i in ins):
            d = 1 + max([depth[i] for i in ins] or [0])
            for o in outs:
                if o not in depth or d < depth[o]:
                    depth[o] = d
unmade = [c for c in CRAFT if c["out"] not in depth]
CRAFT = [c for c in CRAFT if c["out"] in depth]

json.dump({"version": 2, "crate": CRATE, "machines": [{"key": k, "ko": ko, "grade": g, "act": a} for k, ko, g, a in MACHINES],
           "names": {k: name(k) for k in set(depth) | {i for ins, outs in recs for i in list(ins) + list(outs)}},
           "new_items": NEW_ITEMS, "moulds": MOULDS, "raw": RAW, "sources": SOURCES, "fuel": FUEL, "fuel_users": FUEL_USERS, "process": PROCESS,
           "craft": CRAFT, "upgrades": UPGRADES, "depth": depth,
           "dropped_machines": sorted(DROPPED), "unmade": [c["out"] for c in unmade]},
          open(os.path.join(HERE, "recipes_v2.json"), "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)


# ---------------------------------------------------------------- the readable document
def amt(d):
    return ", ".join(f"{name(i)} {n}" for i, n in d.items()) or "없음"


L = ["# 레시피 초안 v2 (제안)", "",
     "기계 13종과 핵 제련소를 기준으로 다시 짠 레시피입니다. 설계 문서 8.19~8.21절의 결정(기계는 동작, 깊은 사슬, 상자로 뭉치기)과 8.23절의 결정(프레스와 롤러를 틀을 끼워 쓰는 성형기 하나로 합침)을 따랐습니다.", "",
     "- 이 문서는 `data/recipes_v2.py`에서 자동으로 만들어집니다. 고칠 때는 그 파일을 고치고 `python3 data/recipes_v2.py`를 실행합니다.",
     "- **제안입니다.** 개발자가 보고 고칠 초안이고, 게임에는 아직 들어가지 않았습니다. 게임은 여전히 [v1 레시피](recipes.md)를 씁니다.",
     "- **숫자는 전부 임시입니다.** 수량, 시간, 한 상자의 개수 모두 해 보면서 고칠 값입니다.",
     "- 상인에게 사고파는 값은 적지 않았습니다. 파는 구조는 개발자가 직접 설계합니다.",
     "- 기계가 하는 일은 손 작업 자리에서도 똑같이 할 수 있습니다(설계 원칙 5). 양도 같습니다.",
     "- 물건이 어디로 흘러가는지는 [사슬 지도](chain-map.html)에서 그림으로 볼 수 있습니다.", "",
     "## 1. 원료", "", "| 물건 | 얻는 곳 |", "|---|---|"]
L += [f"| {name(k)} | {v} |" for k, v in RAW.items()]
L += ["", "## 2. 기계가 하는 일", ""]
for k, ko, g, act in MACHINES:
    rs = [r for r in PROCESS if r["machine"] == k]
    grade = f"{g}급" if g else "큰 목표"
    L += [f"### {ko} ({grade}) — {act}", ""]
    if k in SOURCES:
        L += ["넣는 것 없이 내놓습니다: " + ", ".join(name(i) for i in SOURCES[k]) + ".", ""]
        continue
    if k == "packer":
        L += [f"같은 물건 {CRATE}개를 한 상자로 뭉칩니다. 어떤 물건이든 됩니다. 지금 상자를 요구하는 곳은 큰 관문들입니다: " +
              ", ".join(name(r_) for r_ in wanted) + ".", ""]
        continue
    if k == "former":
        L += ["틀을 끼우면 그 틀대로 일합니다. 틀은 아이템이고, 끼운 틀이 기계 겉에서 보입니다. 틀을 얻는 법은 정하지 않았습니다.", "",
              "| 틀 | 넣는 것 | 나오는 것 | 시간(초) | 비고 |", "|---|---|---|---|---|"]
        L += [f"| {r['kind']} | {amt(r['ins'])} | {amt(r['outs'])} | {r['secs']} | {r['note']} |" for r in rs]
        L.append("")
        continue
    L += ["| 넣는 것 | 나오는 것 | 시간(초) | 비고 |", "|---|---|---|---|"]
    L += [f"| {amt(r['ins'])} | {amt(r['outs'])} | {r['secs']} | {r['note']} |" for r in rs]
    L.append("")
L += ["## 3. 기계를 만드는 재료", "", "기계 작업대에서 만듭니다. 급이 오를수록 더 깊은 사슬의 부품이 듭니다.", "",
      "| 기계 | 작업대 단계 | 재료 | 비고 |", "|---|---|---|---|"]
L += [f"| {name(o)} | {t} | {amt(ins)} | {note} |" for o, (t, ins, note) in BUILD.items()]
L += ["", "## 4. 작업대 승급", "", "3단계 승급은 큰 수량을 상자로 받습니다.", "", "| 작업대:단계 | 재료 |", "|---|---|"]
L += [f"| {k} | {amt(v)} |" for k, v in UPGRADES.items()]
L += ["", "## 5. 깊이", "", "원료에서 몇 단계를 거쳐야 나오는가입니다(가장 짧은 길 기준).", "", "| 물건 | 단계 |", "|---|---|"]
for k in ("ingot_fe", "plate_fe", "gear", "frame", "plate_r", "magnet", "lube", "motor", "ingot_steel", "beam", "frame_steel",
          "board_adv", "assembler", "crate:motor", "coreforge", "core_fe"):
    L.append(f"| {name(k)} | {depth.get(k, '?')} |")
L += ["", "## 6. v1에서 빠진 것", "",
      "출시 목록 밖으로 미룬 것들입니다. 버린 것이 아니라 업데이트로 가지를 열 때 꺼내 씁니다.", "",
      "- **기계**: " + ", ".join(KO.get(m, m) for m in sorted(DROPPED) if not m.startswith("extractor_")) + ".",
      "- **사슬**: 밀 → 밀가루 → 반죽 → 빵(음식 가지), 원유 → 연료통·플라스틱·타르 → 포장재(석유 가지), 체질로 광석 얻기, 주조로 기계 틀 찍기.",
      "- **만들 수 없게 된 조합**: " + (", ".join(name(c["out"]) for c in unmade) or "없음") + "."]
open(os.path.join(ROOT, "docs", "recipes-v2.md"), "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")
print("process", len(PROCESS), "craft", len(CRAFT), "carried", len(carried), "unmade", [name(c["out"]) for c in unmade])
print("depth:", {name(k): depth.get(k) for k in ("motor", "frame_steel", "assembler", "coreforge", "core_fe", "board_adv")})
print("max depth", max(depth.values()), [name(k) for k, v in depth.items() if v == max(depth.values())][:6])
