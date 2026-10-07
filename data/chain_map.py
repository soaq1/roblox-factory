# -*- coding: utf-8 -*-
# 사슬 지도: 레시피 초안 v2(data/recipes_v2.json)의 기계 15종이 무엇을 받아 무엇을 내놓고, 그 물건이 어디로 가는지를 한 장으로 그립니다.
# 실행:  python3 data/recipes_v2.py && python3 data/chain_map.py   ->  docs/chain-map.html
# (v1 초안을 14종에 나눠 담아 본 첫 지도는 docs/chain-map-v1.html 에 그대로 남겨 두었습니다.)
import collections, html, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
d = json.load(open(os.path.join(HERE, "recipes_v2.json"), encoding="utf-8"))
v1 = json.load(open(os.path.join(HERE, "recipes.json"), encoding="utf-8"))
N, MK = d["names"], {m["key"]: m["ko"] for m in d["machines"]}
proc, craft = d["process"], d["craft"]

# 판정은 아래 숫자를 보고 사람이 내린 것입니다.
VERDICT = {
    "extractor": ("ok", "모든 것의 시작입니다."),
    "logger": ("ok", "판자 말고도 숯이 윤활유, 전해액, 강철의 재료가 되어 통나무 줄이 더 중요해졌습니다."),
    "harvester": ("ok", "기름 작물은 윤활유를 거쳐 모터로, 목화는 천으로 갑니다. 밭이 공장의 원료가 됐습니다. 밀과 빵은 업데이트로 미뤘습니다."),
    "pump": ("ok", "세척기와 혼합기가 꼭 필요해지면서 물도 꼭 필요해졌습니다."),
    "crusher": ("ok", "강철 줄의 첫 단계가 됐고, 자갈은 콘크리트로, 구리 가루는 전해액으로 갑니다."),
    "washer": ("mid", "강철을 만들려면 반드시 거쳐야 합니다. 역할은 생겼지만, 새 물건을 만드는 기계가 아니라 통과해야 하는 문에 가깝습니다."),
    "smelter": ("ok", "주괴, 유리, 벽돌, 숯. 일이 가장 많은 기계입니다."),
    "press": ("ok", "판에 더해 기름 짜기와 천 누르기까지 맡았습니다."),
    "roller": ("ok", "막대와 선. 프레스와 짝을 이루는 등뼈입니다."),
    "cutter": ("ok", "판자, 기어, 볼트, 석재. 쓰이는 곳이 없던 볼트가 강화판의 재료가 됐습니다. 나무·돌·쇠·보석을 한 기계가 자르는 것은 여전히 정할 일입니다."),
    "mixer": ("ok", "윤활유(모터), 전해액(전지), 콘크리트(제철소와 핵 제련소). 부품의 재료를 만드는 기계가 됐습니다."),
    "blast": ("ok", "강철과 합금. 후반 기계의 관문입니다."),
    "assembler": ("ok", "부품 여덟 가지. 모터는 재료 네 줄이 여기서 만납니다."),
    "packer": ("ok", "큰 관문(핵 제련소, 작업대 3단계)이 상자를 요구하면서 할 일이 생겼습니다. 파는 쪽과의 관계는 개발자가 정합니다."),
    "coreforge": ("ok", "사슬의 끝입니다. 상자를 받아 광맥 핵을 만들고, 그 핵이 다시 추출기가 됩니다."),
}
VNAME = {"ok": "역할 뚜렷", "mid": "문 노릇", "weak": "역할 약함", "open": "역할 미정"}


def nm(k):
    return N.get(k, k)


cons = collections.defaultdict(collections.Counter)
for r in proc:
    for i in r["ins"]:
        cons[i][MK[r["machine"]]] += 1
for c in craft:
    for i in c["ins"]:
        cons[i]["기계 만들기" if c["bench"] == "machine" else "조합"] += 1
for need in d["upgrades"].values():
    for i in need:
        cons[i]["작업대 승급"] += 1
for f in d["fuel"]:
    cons[f]["연료"] += 1


def chip(k, cls=""):
    new = " new" if k in d["new_items"] else ""
    return f'<span class="chip {cls}{new}">{html.escape(nm(k))}</span>'


def goes(k):
    c = cons.get(k, {})
    if not c:
        return '<span class="none">쓰이는 곳 없음</span>'
    order = [m for m in c if m not in ("기계 만들기", "조합", "작업대 승급", "연료")]
    parts = order + [f'{t} {c[t]}곳' for t in ("기계 만들기", "조합") if c.get(t)] + [t for t in ("연료", "작업대 승급") if c.get(t)]
    return ", ".join(parts)


rows = []
for m in d["machines"]:
    k = m["key"]
    rs = [r for r in proc if r["machine"] == k]
    ins = list(collections.OrderedDict((i, 1) for r in rs for i in r["ins"]))
    outs = list(collections.OrderedDict((o, 1) for r in rs for o in r["outs"])) or d["sources"].get(k, [])
    v, why = VERDICT[k]
    if k == "packer":
        ins, cnt = [], f'같은 물건 {d["crate"]}개 → 1상자 (임시 값)'
        out_html = "".join(f'<li>{chip(o)}<span class="to">{goes(o)}</span></li>' for o in outs)
    else:
        cnt = f'레시피 {len(rs)}개' if rs else "넣는 것 없이 내놓음"
        out_html = "".join(f'<li>{chip(o)}<span class="to">{goes(o)}</span></li>' for o in outs)
    in_html = "".join(chip(i, "in") for i in ins) or ('<span class="mute">어떤 물건이든</span>' if k == "packer" else '<span class="mute">없음</span>')
    grade = f'<span class="grade g{m["grade"]}">{m["grade"]}급</span>' if m["grade"] else '<span class="grade g0">큰 목표</span>'
    rows.append(f'''<article class="row v-{v}">
  <header><h3>{m["ko"]}</h3>{grade}<span class="verdict">{VNAME[v]}</span><p class="act">{m["act"]} · {cnt}</p></header>
  <div class="io"><div class="ins"><h4>받는 것</h4>{in_html}</div>
    <div class="outs"><h4>내놓는 것과 그것이 가는 곳</h4><ul>{out_html}</ul></div></div>
  <p class="why">{why}</p>
</article>''')


# 한 물건이 나오기까지: 가장 짧은 길의 나무와, 거치는 공정 수, 원료 줄 수
def analyse(data, names):
    recs = [(r["ins"], r["outs"], r["machine"]) for r in data["process"]] + [(c["ins"], {c["out"]: c["n"]}, "조합") for c in data["craft"]]
    depth, best = {i: 0 for i in data["raw"]}, {}
    for _ in range(40):
        for ins, outs, mach in recs:
            if all(i in depth for i in ins):
                dd = 1 + max([depth[i] for i in ins] or [0])
                for o in outs:
                    if o not in depth or dd < depth[o]:
                        depth[o], best[o] = dd, (ins, mach)

    def walk(item, seen, ops, raws):
        if item in seen:
            return
        seen.add(item)
        if item in best:
            ops.append(item)
            for i in best[item][0]:
                walk(i, seen, ops, raws)
        else:
            raws.add(item)

    def stats(item):
        if item not in depth:
            return None
        seen, ops, raws = set(), [], set()
        walk(item, seen, ops, raws)
        return depth[item], len(ops), len(raws)
    return depth, best, stats


depth2, best2, stats2 = analyse(d, N)
_, _, stats1 = analyse(v1, {})
cmp_rows = ""
for key, label in (("ingot_steel", "강철 주괴"), ("motor", "모터"), ("assembler", "조립기 (기계)"), ("coreforge", "핵 제련소 (기계)"), ("wb_all", "통합 작업대")):
    a, b = stats1(key), stats2(key)
    cmp_rows += f"<tr><td>{label}</td><td class='num'>{a[0]} → <b>{b[0]}</b></td><td class='num'>{a[1]} → <b>{b[1]}</b></td><td class='num'>{a[2]} → <b>{b[2]}</b></td></tr>"


def tree(item, lvl=0, seen=None):
    seen = set() if seen is None else seen
    if item not in best2:
        return f'<li><span class="chip in">{nm(item)}</span> <span class="to">원료</span></li>'
    ins, mach = best2[item]
    who = MK.get(mach, "작업대 조합")
    again = item in seen
    seen.add(item)
    kids = "" if again else "<ul>" + "".join(tree(i, lvl + 1, seen) for i in ins) + "</ul>"
    note = " (위와 같음)" if again else ""
    return f'<li>{chip(item)} <span class="to">{who}{note}</span>{kids}</li>'


motor_tree = "<ul class='tree'>" + tree("motor") + "</ul>"

top = collections.Counter()
for c in craft:
    for i in c["ins"]:
        top[i] += 1
top_html = "".join(f'<li><b>{nm(k)}</b><span class="bar" style="width:{v * 6}px"></span><span class="num">{v}</span></li>' for k, v in top.most_common(14))
all_outs = collections.OrderedDict((o, 1) for r in proc for o in r["outs"])
orphans = [o for o in all_outs if not cons.get(o)]
orph_html = "".join(chip(o, "bad") for o in orphans) or "없습니다."
dropped = ", ".join(html.escape(nm(k) if k in N else {m_["key"]: m_["ko"] for m_ in json.load(open(os.path.join(ROOT, "art", "catalog", "catalog.json"), encoding="utf-8"))["machines"]}.get(k, k)) for k in d["dropped_machines"] if not k.startswith("extractor_"))

STAGES = [("0. 꺼낸다", ["extractor", "logger", "harvester", "pump"], "원석, 석탄, 통나무, 작물, 물"),
          ("1. 늘리고 걸러 낸다", ["crusher", "washer"], "분쇄 광석, 정제 광석, 자갈, 모래"),
          ("2. 녹인다", ["smelter"], "주괴, 유리, 벽돌, 숯"),
          ("3. 모양을 낸다", ["press", "roller", "cutter"], "판, 막대, 선, 판자, 기어, 볼트, 기름, 천"),
          ("4. 섞는다", ["mixer"], "윤활유, 전해액, 콘크리트"),
          ("5~7. 합친다", ["blast", "assembler"], "강철, 기계 틀, 강화판, 전자석, 모터, 회로, 강철 틀"),
          ("8. 뭉친다", ["packer"], "상자"),
          ("끝", ["coreforge"], "광맥 핵 → 다시 추출기로")]
gr = {m["key"]: m["grade"] for m in d["machines"]}
stage_html = "".join(
    f'<div class="stage"><h4>{t}</h4>' + "".join(f'<span class="m g{gr[k]}">{MK[k]}</span>' for k in ms) + f'<p>{note}</p></div>' +
    ('<div class="arrow">→</div>' if i < len(STAGES) - 1 else "") for i, (t, ms, note) in enumerate(STAGES))

page = f'''<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>사슬 지도</title>
<style>
:root {{ --bg:#f4f3ef; --ink:#22252a; --mute:#666c74; --card:#fff; --line:#dcdad3; --chip:#ecebe6; --in:#e3ecf2; --new:#f6e3c5;
        --ok:#2f7d54; --mid:#a8741a; --weak:#b4472f; --open:#6a5acd; --g0:#7a4fb5; --g1:#8a9199; --g2:#3f7fa6; --g3:#b5632a; }}
@media (prefers-color-scheme: dark) {{ :root {{ --bg:#1b1d21; --ink:#e9e7e2; --mute:#a0a6ae; --card:#25282d; --line:#3a3e45; --chip:#33373e; --in:#2c3b47; --new:#5a4420;
        --ok:#5fbf8b; --mid:#e0ad52; --weak:#ef8a72; --open:#a99cf0; --g0:#b99af0; --g1:#9aa1a9; --g2:#6fb3dc; --g3:#e59a62; }} }}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--bg); color:var(--ink); font:16px/1.6 -apple-system, "Apple SD Gothic Neo", "Malgun Gothic", sans-serif; }}
main {{ max-width:1080px; margin:0 auto; padding:32px 16px 72px; }}
h1 {{ font-size:30px; margin:0 0 4px; letter-spacing:-0.02em; }}
h2 {{ font-size:21px; margin:48px 0 4px; }}
.lead {{ color:var(--mute); margin:0 0 16px; }}
.box {{ background:var(--card); border:1px solid var(--line); border-radius:10px; padding:16px 20px; }}
.find li {{ margin:6px 0; }}
.flow {{ display:flex; align-items:stretch; gap:6px; overflow-x:auto; padding-bottom:6px; }}
.stage {{ flex:1 0 132px; background:var(--card); border:1px solid var(--line); border-radius:10px; padding:10px; }}
.stage h4 {{ margin:0 0 8px; font-size:13px; color:var(--mute); font-weight:600; }}
.stage p {{ margin:8px 0 0; font-size:12px; color:var(--mute); }}
.stage .m {{ display:block; font-weight:700; padding:3px 8px; margin:4px 0; border-radius:6px; border-left:5px solid; background:var(--chip); font-size:15px; }}
.arrow {{ align-self:center; color:var(--mute); font-size:18px; }}
.g0 {{ border-color:var(--g0); }} .g1 {{ border-color:var(--g1); }} .g2 {{ border-color:var(--g2); }} .g3 {{ border-color:var(--g3); }}
.row {{ background:var(--card); border:1px solid var(--line); border-left:6px solid var(--ok); border-radius:10px; padding:14px 18px; margin:12px 0; }}
.row.v-mid {{ border-left-color:var(--mid); }} .row.v-weak {{ border-left-color:var(--weak); }} .row.v-open {{ border-left-color:var(--open); }}
.row header {{ display:flex; flex-wrap:wrap; align-items:baseline; gap:8px 10px; }}
.row h3 {{ margin:0; font-size:19px; }}
.grade {{ font-size:12px; font-weight:700; padding:1px 8px; border:2px solid; border-radius:20px; }}
.grade.g0 {{ color:var(--g0); }} .grade.g1 {{ color:var(--g1); }} .grade.g2 {{ color:var(--g2); }} .grade.g3 {{ color:var(--g3); }}
.verdict {{ font-size:13px; font-weight:700; color:var(--ok); }}
.v-mid .verdict {{ color:var(--mid); }} .v-weak .verdict {{ color:var(--weak); }} .v-open .verdict {{ color:var(--open); }}
.act {{ flex-basis:100%; margin:0; color:var(--mute); font-size:14px; }}
.io {{ display:grid; grid-template-columns:minmax(0, 1fr) minmax(0, 2fr); gap:16px; margin-top:10px; }}
@media (max-width:640px) {{ .io {{ grid-template-columns:1fr; }} }}
h4 {{ margin:0 0 6px; font-size:13px; color:var(--mute); font-weight:600; }}
.chip {{ display:inline-block; background:var(--chip); border-radius:6px; padding:1px 8px; margin:2px 4px 2px 0; font-size:14px; }}
.chip.in {{ background:var(--in); }} .chip.new {{ background:var(--new); font-weight:600; }} .chip.bad {{ outline:2px solid var(--weak); }}
.outs ul {{ list-style:none; margin:0; padding:0; }}
.outs li {{ display:flex; flex-wrap:wrap; align-items:baseline; gap:2px 6px; padding:2px 0; border-top:1px solid var(--line); }}
.outs li:first-child {{ border-top:0; }}
.to {{ font-size:13px; color:var(--mute); }}
.none {{ color:var(--weak); font-weight:600; }} .mute {{ color:var(--mute); }}
.why {{ margin:10px 0 0; font-size:14px; }}
table {{ width:100%; border-collapse:collapse; font-size:15px; }}
th, td {{ text-align:left; padding:6px 8px; border-top:1px solid var(--line); vertical-align:top; }}
th {{ color:var(--mute); font-weight:600; border-top:0; }}
.num {{ text-align:right; font-variant-numeric:tabular-nums; }}
.scroll {{ overflow-x:auto; }}
.tree, .tree ul {{ list-style:none; margin:0; padding-left:22px; border-left:2px solid var(--line); }}
.tree {{ border-left:0; padding-left:0; }}
.tree li {{ margin:3px 0; }}
.top {{ list-style:none; margin:0; padding:0; }}
.top li {{ display:flex; align-items:center; gap:8px; padding:2px 0; font-size:14px; }}
.top b {{ flex:0 0 96px; font-weight:600; }}
.bar {{ height:10px; background:var(--g2); border-radius:3px; }}
.key {{ display:flex; flex-wrap:wrap; gap:6px 16px; font-size:13px; color:var(--mute); margin:8px 0 0; }}
.key i {{ display:inline-block; width:12px; height:12px; border-radius:3px; vertical-align:-1px; margin-right:5px; }}
footer {{ margin-top:40px; font-size:13px; color:var(--mute); }}
a {{ color:inherit; }}
</style></head><body><main>
<h1>사슬 지도</h1>
<p class="lead">레시피 초안 v2입니다. 기계 14종과 핵 제련소가 무엇을 받아 무엇을 내놓고, 그 물건이 어디로 가는지입니다. 전부 제안이고 숫자는 임시입니다.</p>

<div class="box"><ul class="find">
  <li><b>고리가 닫혔습니다.</b> 추출기 → 공장 → 부품 → 상자 → 핵 제련소 → 광맥 핵 → 다시 추출기.</li>
  <li><b>역할이 약한 기계가 없어졌습니다.</b> 첫 지도에서 약했던 세척기, 혼합기, 물 펌프, 수확기와 비어 있던 포장기에 모두 할 일이 생겼습니다. 세척기만은 물건을 만든다기보다 거쳐야 하는 문에 가깝습니다.</li>
  <li><b>길어지기보다 넓어졌습니다.</b> 조립기 한 대를 만들기까지 가장 긴 줄은 5단계에서 6단계로 한 단계 늘었지만, 거쳐야 하는 공정은 10개에서 25개로, 필요한 원료 줄은 3개에서 7개로 늘었습니다. 아래 표에 있습니다.</li>
  <li><b>새 물건은 다섯 가지입니다.</b> 윤활유, 전해액, 강화판, 전자석, 강철 틀. 주황색 칩으로 표시했습니다.</li>
  <li><b>남은 구멍.</b> 쓰이는 곳 없는 물건: {", ".join(nm(o) for o in orphans) or "없음"}. 그리고 물건이 공장 밖 어디로 가는지(파는 구조)는 여전히 비어 있습니다.</li>
</ul></div>

<h2>한 줄로 보면</h2>
<p class="lead">왼쪽에서 오른쪽으로 물건이 흘러가고, 끝에서 나온 광맥 핵이 맨 왼쪽의 추출기로 돌아갑니다. 왼쪽 띠의 색은 급입니다.</p>
<div class="flow">{stage_html}</div>
<div class="key"><span><i style="background:var(--g1)"></i>1급</span><span><i style="background:var(--g2)"></i>2급</span><span><i style="background:var(--g3)"></i>3급</span><span><i style="background:var(--g0)"></i>큰 목표</span></div>

<h2>얼마나 깊어졌나</h2>
<p class="lead">v1 초안과 같은 잣대로 쟀습니다. 가장 짧은 길 기준이고, 화살표 왼쪽이 v1, 오른쪽이 v2입니다.</p>
<div class="box scroll"><table>
<tr><th>만들 것</th><th class="num">가장 긴 줄의 단계</th><th class="num">거치는 공정 수</th><th class="num">필요한 원료 줄</th></tr>{cmp_rows}</table></div>

<h2>예: 모터 하나가 나오기까지</h2>
<p class="lead">오른쪽 글씨는 그 물건을 만드는 기계입니다. 주황색이 새로 생긴 물건입니다.</p>
<div class="box">{motor_tree}</div>

<h2>기계별로</h2>
<p class="lead">"기계 만들기 N곳"은 그 물건을 재료로 쓰는 기계 레시피의 수, "조합 N곳"은 그 밖의 조합(도구, 블록, 장치) 수입니다.</p>
<div class="key"><span><i style="background:var(--ok)"></i>역할 뚜렷</span><span><i style="background:var(--mid)"></i>문 노릇</span><span><i style="background:var(--new)"></i>새로 생긴 물건</span></div>
{"".join(rows)}

<h2>가장 많이 쓰이는 재료</h2>
<p class="lead">조합 레시피 {len(craft)}가지에서 재료로 쓰이는 횟수입니다.</p>
<div class="box"><ul class="top">{top_html}</ul></div>

<h2>쓰이는 곳이 없는 물건</h2>
<div class="box">{orph_html}</div>

<h2>업데이트로 미룬 것</h2>
<div class="box"><p style="margin:0"><b>기계</b>: {dropped}.</p><p style="margin:8px 0 0"><b>사슬</b>: 밀 → 빵(음식 가지), 원유 → 연료·플라스틱·타르(석유 가지), 체질로 광석 얻기, 주조로 기계 틀 찍기, 절삭 날.</p></div>

<footer>판정(역할 뚜렷 등)은 숫자를 보고 내린 의견입니다. 숫자는 <code>data/recipes_v2.json</code>에서 자동으로 센 것이고, 수량과 시간, 한 상자의 개수는 전부 임시 값입니다. 레시피 전체는 <a href="recipes-v2.md">recipes-v2.md</a>, 처음 그린 지도는 <a href="chain-map-v1.html">chain-map-v1.html</a>. 다시 만들려면 <code>python3 data/recipes_v2.py &amp;&amp; python3 data/chain_map.py</code>.</footer>
</main></body></html>'''
out = os.path.join(ROOT, "docs", "chain-map.html")
open(out, "w", encoding="utf-8", newline="\n").write(page)
print("wrote", out, "| orphans:", [nm(o) for o in orphans])
