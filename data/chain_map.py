# -*- coding: utf-8 -*-
# 사슬 지도: 출시 후보 14종의 기계가 무엇을 받아 무엇을 내놓고, 그 물건이 어디로 가는지를 한 장으로 그립니다.
# 지금의 레시피 초안(data/recipes.json, 기계 23종 기준)을 14종에 나눠 담아 본 것이라, 초안의 구멍이 그대로 보입니다.
# 실행:  python3 data/chain_map.py   ->  docs/chain-map.html
import collections, html, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
data = json.load(open(os.path.join(HERE, "recipes.json"), encoding="utf-8"))
catalog = json.load(open(os.path.join(ROOT, "art", "catalog", "catalog.json"), encoding="utf-8"))
KO = {i["key"]: i["ko"] for i in catalog["items"]}
KO.update({m["key"]: m["ko"] for m in catalog["machines"]})
KO.update({"barrel_water": "물통", "crate": "상자"})

# 옛 기계(초안의 23종)를 출시 후보 14종의 어느 동작에 담을지. 여기 없는 옛 기계는 "자리가 없는 레시피"로 나옵니다.
FOLD = {"smelter": "용광로", "kiln": "용광로", "oven": "용광로", "crusher": "분쇄기", "mill": "분쇄기", "washer": "세척기",
        "press": "프레스", "briquetter": "프레스", "oilpress": "프레스", "sawmill": "절단기", "stonecutter": "절단기",
        "gemcutter": "절단기", "lathe": "절단기", "wiredraw": "롤러", "mixer": "혼합기", "blast": "제철소", "alloy": "제철소"}
BENCH = {"machine": "기계", "basic": "기본", "tool": "도구", "elec": "전기", "bag": "가방", "part": "부품", "furn": "가구", "all": "통합"}

# 14종: (이름, 급, 동작 한 줄, 판정, 판정 설명). 판정은 자료를 보고 사람이 내린 것입니다.
MACHINES = [
    ("추출기", 1, "광맥 핵에서 원석을 내놓음", "ok", "모든 것의 시작입니다. 역할이 분명합니다."),
    ("벌목기", 1, "곁의 나무를 통나무로 내놓음", "ok", "판자가 조합 33곳에 쓰여서 통나무 줄은 꼭 필요합니다."),
    ("수확기", 2, "밭에서 다 자란 것을 내놓음", "weak", "밀은 빵에서 끝나는데 빵은 쓰이는 곳이 없습니다. 목화는 천이 되어야 하는데 천을 짜는 기계가 14종에 없습니다."),
    ("물 펌프", 2, "물을 끌어올려 내놓음", "weak", "물이 쓰이는 곳은 세척기와 혼합기뿐입니다. 둘의 역할이 약하면 펌프도 같이 약해집니다."),
    ("분쇄기", 1, "부숨", "mid", "광석을 부수는 것은 제련 양을 1.3배로 늘리는 선택 사항입니다. 꼭 필요한 일은 돌을 자갈과 모래로 만드는 것 하나입니다."),
    ("세척기", 2, "씻음", "weak", "부순 광석을 씻어 제련 양을 2배로 늘리는 것이 전부입니다. 새 물건을 만들지 않고, 없어도 공장이 돌아갑니다."),
    ("용광로", 1, "녹이고 구움", "ok", "주괴 없이는 아무것도 못 만듭니다. 유리, 벽돌, 숯까지 맡으면 일이 가장 많은 기계입니다."),
    ("프레스", 2, "눌러서 판으로", "ok", "철판이 조합 33곳에 쓰입니다. 사슬의 등뼈입니다."),
    ("롤러", 2, "늘여서 막대와 선으로", "ok", "철 막대가 조합 28곳, 구리선이 10곳에 쓰입니다. 프레스와 짝을 이루는 등뼈입니다."),
    ("절단기", 1, "자르고 깎음", "ok", "판자(33곳)와 기어(13곳)가 여기서 나옵니다. 다만 나무, 돌, 보석, 쇠를 다 자르는 셈이라 한 기계로 볼지 정해야 합니다."),
    ("제철소", 3, "둘을 함께 녹여 합금으로", "ok", "강철과 강철판, 강철 막대가 합쳐 27곳에 쓰입니다. 후반 기계의 관문입니다."),
    ("혼합기", 3, "여럿을 섞음", "weak", "나오는 것이 점토, 콘크리트, 반죽, 포장재로 전부 건축 블록이나 음식 쪽이고, 조합에 쓰이는 곳이 각각 한 곳뿐입니다. 3급(가장 값진 것을 만드는 기계)이라기엔 약합니다."),
    ("조립기", 3, "부품을 합쳐 완성품으로", "ok", "제 레시피가 따로 없고, 작업대에서 하는 조합을 대신 돌립니다. 기계 틀(43곳), 모터(18곳), 회로 기판(10곳)이 여기서 나오므로 실제로는 가장 중요합니다."),
    ("포장기", 2, "상자에 담음", "open", "레시피가 없습니다. 상자에 담아 파는 쪽의 기계인데, 파는 구조가 아직 정해지지 않아 역할이 비어 있습니다."),
]
VERDICT = {"ok": "역할 뚜렷", "mid": "절반만 필요", "weak": "역할 약함", "open": "역할 미정"}

proc, craft = data["process"], data["craft"]
consumers = collections.defaultdict(collections.Counter)      # 물건 -> 그것을 쓰는 곳
for r in proc:
    who = FOLD.get(r["machine"], "옛 " + KO.get(r["machine"], r["machine"]))
    for i in r["ins"]:
        consumers[i][who] += 1
for c in craft:
    for i in c["ins"]:
        consumers[i]["조합"] += 1
for need in data["upgrades"].values():
    for i in need:
        consumers[i]["작업대 승급"] += 1
for f in data["fuel"]:
    consumers[f]["연료"] += 1

by = collections.defaultdict(list)
for r in proc:
    by[FOLD.get(r["machine"], "옛 " + KO.get(r["machine"], r["machine"]))].append(r)

# 손으로 넣은 것: 레시피 표에 기계 이름으로 안 잡히는 공급 기계와 조립기
SOURCE = {"추출기": ([], ["stone", "coal", "ore_cu", "ore_fe"]), "벌목기": ([], ["log"]),
          "수확기": ([], ["wheat", "cotton", "oilseed"]), "물 펌프": ([], ["barrel_water"])}
ASSEMBLED = ["frame", "motor", "board", "cell", "board_adv"]
craft_by_out = collections.defaultdict(list)
for c in craft:
    craft_by_out[c["out"]].append(c)


def name(k):
    return KO.get(k, k.replace("block:", "") + " 블록" if k.startswith("block:") else k)


def chip(k, cls=""):
    return f'<span class="chip {cls}">{html.escape(name(k))}</span>'


def goes(k):
    c = consumers.get(k, {})
    if not c:
        return '<span class="none">쓰이는 곳 없음</span>'
    parts = []
    if c.get("조합"):
        parts.append(f'조합 {c["조합"]}곳')
    parts += [m for m in c if m not in ("조합", "작업대 승급", "연료") and not m.startswith("옛 ")]
    if c.get("연료"):
        parts.append("연료")
    if c.get("작업대 승급"):
        parts.append("작업대 승급")
    old = [m for m in c if m.startswith("옛 ")]
    if old and not parts:
        return f'<span class="none">{", ".join(old)}에만 쓰임 (14종에 없음)</span>'
    return ", ".join(parts)


rows = []
for ko, grade, act, verdict, why in MACHINES:
    if ko in SOURCE:
        ins, outs, n = SOURCE[ko][0], SOURCE[ko][1], 0
    elif ko == "조립기":
        ins = list(collections.OrderedDict((i, 1) for o in ASSEMBLED for c in craft_by_out[o] for i in c["ins"]))
        outs, n = ASSEMBLED, sum(len(craft_by_out[o]) for o in ASSEMBLED)
    elif ko == "포장기":
        ins, outs, n = [], ["crate"], 0
    else:
        rs = by.get(ko, [])
        ins = list(collections.OrderedDict((i, 1) for r in rs for i in r["ins"]))
        outs = list(collections.OrderedDict((o, 1) for r in rs for o in r["outs"]))
        n = len(rs)
    out_html = "".join(f'<li>{chip(o)}<span class="to">{goes(o)}</span></li>' for o in outs)
    in_html = "".join(chip(i, "in") for i in ins) or '<span class="mute">없음</span>'
    cnt = f'레시피 {n}개' if n else ("넣는 것 없이 내놓음" if ko in SOURCE else "레시피 없음")
    rows.append(f'''<article class="row v-{verdict}">
  <header><h3>{ko}</h3><span class="grade g{grade}">{grade}급</span><span class="verdict">{VERDICT[verdict]}</span>
    <p class="act">{act} · {cnt}</p></header>
  <div class="io"><div class="ins"><h4>받는 것</h4>{in_html}</div>
    <div class="outs"><h4>내놓는 것과 그것이 가는 곳</h4><ul>{out_html}</ul></div></div>
  <p class="why">{why}</p>
</article>''')

# 자리가 없는 레시피
homeless = []
for m, rs in by.items():
    if not m.startswith("옛 "):
        continue
    for r in rs:
        a = " + ".join(f'{name(i)} {q}' for i, q in r["ins"].items())
        b = " + ".join(f'{name(o)} {q}' for o, q in r["outs"].items())
        used = sum(consumers[o].get("조합", 0) for o in r["outs"])
        homeless.append((m[2:], a, b, used))
home_html = "".join(f"<tr><td>{m}</td><td>{a}</td><td>{b}</td><td class='num'>{u}</td></tr>" for m, a, b, u in homeless)

all_outs = collections.OrderedDict((o, 1) for r in proc for o in r["outs"])
orphans = [o for o in all_outs if not consumers.get(o)]
orph_html = "".join(chip(o, "bad") for o in orphans)

top = collections.Counter()
for c in craft:
    for i in c["ins"]:
        top[i] += 1
top_html = "".join(f'<li><b>{name(k)}</b><span class="bar" style="width:{v * 5}px"></span><span class="num">{v}</span></li>' for k, v in top.most_common(14))
bench_count = collections.Counter(c["bench"] for c in craft)
bench_html = ", ".join(f"{BENCH.get(k, k)} {v}" for k, v in bench_count.most_common())

STAGES = [("꺼낸다", ["추출기", "벌목기", "수확기", "물 펌프"], "원석, 통나무, 작물, 물"),
          ("늘린다 (선택)", ["분쇄기", "세척기"], "부수고 씻으면 주괴가 2배"),
          ("녹인다", ["용광로"], "주괴, 유리, 벽돌, 숯"),
          ("모양을 낸다", ["프레스", "롤러", "절단기"], "판, 막대, 선, 판자, 기어"),
          ("합친다", ["제철소", "혼합기", "조립기"], "강철, 기계 틀, 모터, 회로"),
          ("그다음", [], "기계·도구·블록을 조합 / 파는 구조는 미정")]
gr = {m[0]: m[1] for m in MACHINES}
stage_html = "".join(
    f'<div class="stage"><h4>{t}</h4>' + "".join(f'<span class="m g{gr[m]}">{m}</span>' for m in ms) +
    f'<p>{note}</p></div>' + ('<div class="arrow">→</div>' if i < len(STAGES) - 1 else "")
    for i, (t, ms, note) in enumerate(STAGES))

page = f'''<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>사슬 지도</title>
<style>
:root {{ --bg:#f4f3ef; --ink:#22252a; --mute:#666c74; --card:#fff; --line:#dcdad3; --chip:#ecebe6; --in:#e3ecf2;
        --ok:#2f7d54; --mid:#a8741a; --weak:#b4472f; --open:#6a5acd; --g1:#8a9199; --g2:#3f7fa6; --g3:#b5632a; }}
@media (prefers-color-scheme: dark) {{ :root {{ --bg:#1b1d21; --ink:#e9e7e2; --mute:#a0a6ae; --card:#25282d; --line:#3a3e45; --chip:#33373e; --in:#2c3b47;
        --ok:#5fbf8b; --mid:#e0ad52; --weak:#ef8a72; --open:#a99cf0; --g1:#9aa1a9; --g2:#6fb3dc; --g3:#e59a62; }} }}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--bg); color:var(--ink); font:16px/1.6 -apple-system, "Apple SD Gothic Neo", "Malgun Gothic", sans-serif; }}
main {{ max-width:1080px; margin:0 auto; padding:32px 16px 72px; }}
h1 {{ font-size:30px; margin:0 0 4px; letter-spacing:-0.02em; }}
h2 {{ font-size:21px; margin:48px 0 4px; }}
.lead {{ color:var(--mute); margin:0 0 16px; }}
.box {{ background:var(--card); border:1px solid var(--line); border-radius:10px; padding:16px 20px; }}
.find li {{ margin:6px 0; }}
.flow {{ display:flex; align-items:stretch; gap:6px; overflow-x:auto; padding-bottom:6px; }}
.stage {{ flex:1 0 150px; background:var(--card); border:1px solid var(--line); border-radius:10px; padding:12px; }}
.stage h4 {{ margin:0 0 8px; font-size:14px; color:var(--mute); font-weight:600; }}
.stage p {{ margin:8px 0 0; font-size:13px; color:var(--mute); }}
.stage .m {{ display:block; font-weight:700; padding:3px 8px; margin:4px 0; border-radius:6px; border-left:5px solid; background:var(--chip); }}
.arrow {{ align-self:center; color:var(--mute); font-size:20px; }}
.m.g1, .grade.g1 {{ border-color:var(--g1); }} .m.g2, .grade.g2 {{ border-color:var(--g2); }} .m.g3, .grade.g3 {{ border-color:var(--g3); }}
.row {{ background:var(--card); border:1px solid var(--line); border-left:6px solid var(--ok); border-radius:10px; padding:14px 18px; margin:12px 0; }}
.row.v-mid {{ border-left-color:var(--mid); }} .row.v-weak {{ border-left-color:var(--weak); }} .row.v-open {{ border-left-color:var(--open); }}
.row header {{ display:flex; flex-wrap:wrap; align-items:baseline; gap:8px 10px; }}
.row h3 {{ margin:0; font-size:19px; }}
.grade {{ font-size:12px; font-weight:700; padding:1px 8px; border:2px solid; border-radius:20px; }}
.grade.g1 {{ color:var(--g1); }} .grade.g2 {{ color:var(--g2); }} .grade.g3 {{ color:var(--g3); }}
.verdict {{ font-size:13px; font-weight:700; color:var(--ok); }}
.v-mid .verdict {{ color:var(--mid); }} .v-weak .verdict {{ color:var(--weak); }} .v-open .verdict {{ color:var(--open); }}
.act {{ flex-basis:100%; margin:0; color:var(--mute); font-size:14px; }}
.io {{ display:grid; grid-template-columns:minmax(0, 1fr) minmax(0, 2fr); gap:16px; margin-top:10px; }}
@media (max-width:640px) {{ .io {{ grid-template-columns:1fr; }} }}
h4 {{ margin:0 0 6px; font-size:13px; color:var(--mute); font-weight:600; }}
.chip {{ display:inline-block; background:var(--chip); border-radius:6px; padding:1px 8px; margin:2px 4px 2px 0; font-size:14px; }}
.chip.in {{ background:var(--in); }} .chip.bad {{ outline:2px solid var(--weak); }}
.outs ul {{ list-style:none; margin:0; padding:0; }}
.outs li {{ display:flex; flex-wrap:wrap; align-items:baseline; gap:2px 6px; padding:2px 0; border-top:1px solid var(--line); }}
.outs li:first-child {{ border-top:0; }}
.to {{ font-size:13px; color:var(--mute); }}
.none {{ color:var(--weak); font-weight:600; }} .mute {{ color:var(--mute); }}
.why {{ margin:10px 0 0; font-size:14px; }}
table {{ width:100%; border-collapse:collapse; font-size:14px; }}
th, td {{ text-align:left; padding:6px 8px; border-top:1px solid var(--line); vertical-align:top; }}
th {{ color:var(--mute); font-weight:600; border-top:0; }}
.num {{ text-align:right; font-variant-numeric:tabular-nums; }}
.scroll {{ overflow-x:auto; }}
.top {{ list-style:none; margin:0; padding:0; }}
.top li {{ display:flex; align-items:center; gap:8px; padding:2px 0; font-size:14px; }}
.top b {{ flex:0 0 96px; font-weight:600; }}
.bar {{ height:10px; background:var(--g2); border-radius:3px; }}
.key {{ display:flex; flex-wrap:wrap; gap:6px 16px; font-size:13px; color:var(--mute); margin:8px 0 0; }}
.key i {{ display:inline-block; width:12px; height:12px; border-radius:3px; vertical-align:-1px; margin-right:5px; }}
footer {{ margin-top:40px; font-size:13px; color:var(--mute); }}
</style></head><body><main>
<h1>사슬 지도</h1>
<p class="lead">출시 후보 14종의 기계가 무엇을 받아 무엇을 내놓고, 그 물건이 어디로 가는지입니다. 지금의 레시피 초안을 14종에 나눠 담아 본 것이라 초안의 구멍이 그대로 보입니다.</p>

<div class="box"><ul class="find">
  <li><b>등뼈는 다섯 기계입니다.</b> 용광로 → 프레스·롤러·절단기 → 조립기. 조합 144가지 가운데 기계 틀이 43곳, 철판 33곳, 판자 33곳, 철 막대 28곳에 쓰입니다.</li>
  <li><b>역할이 약한 기계가 넷입니다.</b> 세척기, 혼합기, 물 펌프, 수확기. 없어도 공장이 돌아가거나, 내놓는 물건이 거의 안 쓰입니다.</li>
  <li><b>포장기는 역할이 비어 있습니다.</b> 파는 구조가 정해져야 할 일이 생깁니다.</li>
  <li><b>물건이 마지막에 가는 곳이 "더 많은 기계 만들기"뿐입니다.</b> 조합 144가지 가운데 53가지가 기계입니다. 가치가 불명확한 이유가 여기 있습니다. 공장이 만든 것이 공장 밖 어디로 가는지가 아직 없습니다.</li>
  <li><b>14종에 담을 자리가 없는 레시피가 {len(homeless)}개</b> 있고, 그중 천(8곳에 쓰임)과 기계 틀을 한 줄로 찍는 길이 걸립니다.</li>
</ul></div>

<h2>한 줄로 보면</h2>
<p class="lead">왼쪽에서 오른쪽으로 물건이 흘러갑니다. 왼쪽 띠의 색은 급입니다.</p>
<div class="flow">{stage_html}</div>
<div class="key"><span><i style="background:var(--g1)"></i>1급</span><span><i style="background:var(--g2)"></i>2급</span><span><i style="background:var(--g3)"></i>3급</span></div>

<h2>기계별로</h2>
<p class="lead">"조합 N곳"은 그 물건을 재료로 쓰는 조합 레시피의 수입니다. 많을수록 그 기계가 중요합니다.</p>
<div class="key"><span><i style="background:var(--ok)"></i>역할 뚜렷</span><span><i style="background:var(--mid)"></i>절반만 필요</span><span><i style="background:var(--weak)"></i>역할 약함</span><span><i style="background:var(--open)"></i>역할 미정</span></div>
{"".join(rows)}

<h2>가장 많이 쓰이는 재료</h2>
<p class="lead">조합 레시피 144가지(작업대별: {bench_html})에서 재료로 쓰이는 횟수입니다.</p>
<div class="box"><ul class="top">{top_html}</ul></div>

<h2>14종에 자리가 없는 레시피</h2>
<p class="lead">초안에 있던 옛 기계의 일인데, 14종의 어느 동작에도 담기 어려운 것들입니다. 버리거나, 어느 기계에 맡기거나, 업데이트로 미뤄야 합니다.</p>
<div class="box scroll"><table><tr><th>옛 기계</th><th>받는 것</th><th>내놓는 것</th><th class="num">조합에 쓰이는 곳</th></tr>{home_html}</table></div>

<h2>어디에도 쓰이지 않는 물건</h2>
<p class="lead">기계가 만들기는 하는데 받아 주는 곳이 없습니다. 쓸 곳을 만들거나 지워야 합니다.</p>
<div class="box">{orph_html}</div>

<footer>판정(역할 뚜렷, 약함 등)은 위 숫자를 보고 내린 의견입니다. 숫자는 레시피 초안에서 자동으로 센 것이고, 초안의 수량과 시간은 전부 임시 값입니다. 옛 기계를 14종에 나눠 담은 방식(가마와 오븐을 용광로에, 제재기·석재 절단기·보석 절삭기·선반을 절단기에 등)은 제안입니다. 다시 만들려면 <code>python3 data/chain_map.py</code>.</footer>
</main></body></html>'''
out = os.path.join(ROOT, "docs", "chain-map.html")
open(out, "w", encoding="utf-8", newline="\n").write(page)
print("wrote", out, "homeless", len(homeless), "orphans", [name(o) for o in orphans])
