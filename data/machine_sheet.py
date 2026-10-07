# -*- coding: utf-8 -*-
# 기계 설계표: 기계마다 급, 크기, 높이, 벨트가 붙는 꼴, 주인공과 조연을 한 장에 모읍니다. 모델을 만들기 전에 정하는 표입니다.
# 실행:  python3 data/machine_sheet.py   ->  docs/machine-sheet.html
# 전부 제안입니다. 개발자가 보고 고칩니다. 크기의 단위는 칸(1칸 = 3스터드, 캐릭터 키는 1.67칸쯤).
import html, math, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# (이름, 급, 꼴, 가로(벨트 방향), 세로, 높이, 입구 수, 출구 수, 청사진, 컨셉, 주인공, 조연, 실루엣, 모델 상태)
M = [
 ("추출기", 1, "내놓기만", 2, 1, 1.6, 0, 1, False, "꽂아 둔 광맥 핵에서 원석이 맺혀 떨어져 나온다",
  "기둥 셋이 공중에 붙든 빛나는 핵", "", "낮은 받침 위에 선 세 기둥, 그 사이에 뜬 핵", "예전 것 있음 (다시 만들어야 함)"),
 ("벌목기", 1, "내놓기만", 2, 1, 1.6, 0, 1, False, "곁의 나무를 집어 와 통나무로 내놓는다",
  "통나무를 문 집게 팔", "", "몸통에서 옆으로 뻗은 굵은 팔 하나", "없음"),
 ("분쇄기", 1, "지나감", 3, 1, 1.3, 1, 1, False, "돌과 광석이 맞물려 도는 톱니 사이로 떨어져 으깨진다",
  "열린 깔때기 속의 톱니 롤 둘", "", "위로 벌어진 넓은 깔때기", "만듦 (crusher3)"),
 ("절단기", 1, "지나감", 3, 1, 1.4, 1, 1, False, "통나무와 돌이 도는 톱날 밑을 지나며 갈라진다",
  "몸통 위로 반쯤 솟은 큰 원형 톱날", "", "둥근 톱날과 그 반달 덮개", "없음"),
 ("용광로", 2, "지나감", 4, 2, 1.9, 1, 1, True, "광석이 불 속으로 들어가 녹았다가 주괴로 굳어 나온다",
  "위가 열린 넓은 화로 상자. 창살 밑으로 불이 보임", "송풍기와 거기서 양쪽으로 나와 화로 상자를 따라 달리는 굵은 바람 관 둘, 쇳물 꼭지, 양쪽 벽의 불구멍", "짙은 지붕을 인 넓은 몸통 위에 큰 화로 상자와 작은 송풍기", "만듦 (smelter9). 통과한 smelter8을 실제 아일랜드 용광로 크기(4×2칸)로 키운 것. 게임 안에서 크기 확인 전"),
 ("성형기", 2, "지나감", 3, 2, 1.95, 1, 1, False, "주괴가 들어가면, 끼워 둔 틀의 모양대로 찍혀 판이나 막대나 볼트가 되어 나온다",
  "굵은 기둥 넷 위에 얹힌 큰 머리. 기둥마다 불거지고, 윗가장자리에 짙은 띠를 두름", "두꺼운 테를 두른 입구와 그 위의 비스듬한 덮개, 옆의 세로 통풍 창, 머리 위의 열린 틀, 고리 달린 배기 굴뚝, 낮은 받침판과 꺾인 버팀 다리, 받침판 위의 틀 선반과 틀 받이와 큰 바퀴", "높은 몸통 위에 네 기둥과 네 귀가 불거진 머리, 옆에 붙은 낮은 받침판과 바퀴", "만듦 (former2). 덩어리는 새티스팩토리의 제작기를 따름. 2급이라 화면과 로봇 팔은 뺌. 개발자 확인 전"),
 ("세척기", 2, "지나감", 3, 1, 1.5, 1, 1, False, "흙 묻은 광석이 물통에 잠겨 휘저어지고, 찌꺼기가 떨어져 깨끗해진다",
  "물이 찬 통과 물을 휘젓는 바퀴", "찌꺼기가 빠지는 관", "위가 열린 물통과 그 위로 솟은 바퀴", "예전 것 있음"),
 ("포장기", 2, "지나감", 3, 1, 1.6, 1, 1, False, "낱개로 들어온 물건이 차곡차곡 쌓여 한 상자로 묶여 나온다",
  "채워지는 상자", "상자를 감는 띠와 띠 감개", "틀 안에 놓인 상자", "없음"),
 ("수확기", 2, "내놓기만", 2, 1, 1.5, 0, 1, False, "앞의 밭에서 다 자란 것을 쓸어 담아 내놓는다",
  "도는 갈퀴", "곡식이 찬 통", "앞으로 내민 갈퀴 바퀴", "없음"),
 ("물 펌프", 2, "내놓기만", 2, 1, 2.0, 0, 1, False, "땅속의 물을 끌어올려 내놓는다",
  "오르내리는 펌프대", "돌림바퀴, 물이 찬 통", "기둥 위에서 끄덕이는 긴 대", "없음"),
 ("혼합기", 3, "합침", 3, 3, 2.2, 2, 1, False, "여러 재료가 한 통에 담겨 젓개에 섞이고, 한 덩어리가 되어 나온다",
  "넓은 통과 그 안에서 도는 젓개", "재료가 떨어지는 깔때기 둘, 젓개를 돌리는 구동부, 받침 틀", "굵은 다리 위에 올린 큰 통", "예전 것 있음"),
 ("제철소", 3, "합침", 3, 3, 3.75, 2, 1, True, "철과 석탄이 높은 화로 꼭대기로 실려 올라가, 뜨거운 바람 속에서 함께 녹아 강철로 흘러나온다",
  "건물 위로 솟은 화로와, 그 앞에 화로보다 높이 선 승강 통로", "어깨가 비스듬한 긴 건물과 짙은 끝벽, 두꺼운 테를 두른 입구 둘과 그 사이의 기둥(통풍 창, 덮개 판, 화면 하나), 화덕의 불 창과 쇳물 꼭지, 화로 위의 고리 달린 굴뚝 둘, 송풍기와 굵은 관, 버팀 다리", "어깨진 낮은 건물 위에 선 굵은 화로, 그 앞의 사다리 같은 통로, 꼭대기의 굴뚝 둘", "없음. 시안 둘을 버림: blast4(\"2급보다 구리다\"), blast5(주조소를 따른 것, \"역대급 별로\"). 다시 만들어야 함"),
 ("조립기", 3, "합침", 3, 3, 2.6, 2, 1, True, "부품들이 작업대에 놓이고, 팔이 하나씩 집어 틀에 끼워 완성품이 된다",
  "돌림판 위에서 일하는 팔 둘", "부품 통, 뼈대, 조종실, 전원함", "뼈대 둘이 감싼 열린 작업대", "만듦 (assembler4). 기준 모델"),
 ("핵 제련소", 0, "큰 목표", 5, 5, 5.0, 4, 1, True, "상자째 들어온 재료가 가운데의 방에서 오래 눌리고 달궈져 광맥 핵 하나로 맺힌다",
  "가운데에서 자라나는 핵", "사방의 상자 입구, 핵을 누르는 큰 장치, 열을 내보내는 탑", "섬에서 가장 높은 건물", "없음. 생김새는 미정"),
]
GN = {0: "큰 목표", 1: "1급", 2: "2급", 3: "3급"}
C = 22            # pixels per cell
MAN = 1.67        # character height in cells


def top(w, d, g, ins, outs, form):
    """Footprint from above: belt runs left to right."""
    W, D = w * C, d * C
    belts = ""
    by = D / 2 if d == 1 else D - C / 2                       # a two-row machine carries its belt along the front row
    if form == "지나감":
        belts = f'<rect x="0" y="{by - 5}" width="{W}" height="10" class="belt"/>'
    elif form == "내놓기만":
        belts = f'<rect x="{C}" y="{D / 2 - 5}" width="{W - C}" height="10" class="belt"/>'
    elif form == "합침":
        ys = [D / 6, 5 * D / 6] if ins == 2 else [D / 2]
        belts = "".join(f'<rect x="0" y="{y - 5}" width="{C}" height="10" class="belt"/>' for y in ys)
        belts += f'<rect x="{W - C}" y="{D / 2 - 5}" width="{C}" height="10" class="belt"/>'
    else:
        belts = "".join(f'<rect x="{x}" y="{y}" width="{bw}" height="{bh}" class="belt"/>' for x, y, bw, bh in
                        ((0, D / 2 - 5, C, 10), (W / 2 - 5, 0, 10, C), (W / 2 - 5, D - C, 10, C), (W - C, D / 2 - 5, C, 10)))
    def arrow(x, y, dx, dy):                                  # a port: a small arrow at the middle of a cell's edge
        s_ = 4
        if dx:
            return f'<polygon points="{x - dx * s_},{y - s_} {x + dx * s_},{y} {x - dx * s_},{y + s_}" class="port"/>'
        return f'<polygon points="{x - s_},{y - dy * s_} {x},{y + dy * s_} {x + s_},{y - dy * s_}" class="port"/>'
    if form == "지나감":
        belts += arrow(6, by, 1, 0) + arrow(W - 6, by, 1, 0)
    elif form == "내놓기만":
        belts += arrow(W - 6, D / 2, 1, 0)
    elif form == "합침":
        belts += "".join(arrow(6, y, 1, 0) for y in ys) + arrow(W - 6, D / 2, 1, 0)
    else:
        belts += arrow(6, D / 2, 1, 0) + arrow(W / 2, 6, 0, 1) + arrow(W / 2, D - 6, 0, -1) + arrow(W - 6, D / 2, 1, 0)
    grid = "".join(f'<line x1="{i * C}" y1="0" x2="{i * C}" y2="{D}" class="grid"/>' for i in range(1, w)) + \
           "".join(f'<line x1="0" y1="{j * C}" x2="{W}" y2="{j * C}" class="grid"/>' for j in range(1, d))
    return f'<svg width="{W + 2}" height="{D + 2}" viewBox="-1 -1 {W + 2} {D + 2}"><rect width="{W}" height="{D}" rx="3" class="body g{g}"/>{grid}{belts}</svg>'


def side(w, h, g, c=C, tall=None):
    """Height from the side, with a character for scale. `tall` is the canvas height in cells."""
    tall = tall or max(math.ceil(h - 1e-9), MAN) + 0.25
    W, H, top_h, man, gut = w * c, tall * c, h * c, MAN * c, c * 1.3
    r = c * 0.27
    hit = math.ceil(h - 1e-9) * c
    return (f'<svg width="{W + gut:.0f}" height="{H + 2:.0f}" viewBox="0 0 {W + gut:.0f} {H + 2:.0f}">'
            f'<rect x="0.5" y="{H - hit + 0.5:.1f}" width="{W - 1}" height="{hit - 0.5:.1f}" class="hit"/>'
            f'<rect x="0" y="{H - top_h:.1f}" width="{W}" height="{top_h:.1f}" rx="4" class="body g{g}"/>'
            f'<rect x="0" y="{H - 0.36 * c:.1f}" width="{W}" height="{0.36 * c:.1f}" class="belt"/>'
            f'<g class="man"><circle cx="{W + gut * 0.6:.1f}" cy="{H - man + r:.1f}" r="{r:.1f}"/>'
            f'<rect x="{W + gut * 0.6 - r * 0.8:.1f}" y="{H - man + 2 * r + 1:.1f}" width="{r * 1.6:.1f}" height="{man - 2 * r - 1:.1f}" rx="2"/></g>'
            f'<line x1="0" y1="{H:.1f}" x2="{W + gut:.0f}" y2="{H:.1f}" class="ground"/></svg>')


cards = ""
for name, g, form, w, d, h, ins, outs, bp, concept, hero, extra, sil, state in M:
    io = f"입구 {ins} · 출구 {outs}" if ins else f"출구 {outs}"
    cards += f'''<article class="card">
  <header><h3>{name}</h3><span class="grade g{g}">{GN[g]}</span>{'<span class="bp">청사진</span>' if bp else ''}</header>
  <p class="concept">{html.escape(concept)}</p>
  <div class="draw"><figure>{top(w, d, g, ins, outs, form)}<figcaption>위에서 · {w}×{d}칸</figcaption></figure>
    <figure>{side(w, h, g)}<figcaption>옆에서 · 보이는 높이 {h:g}칸</figcaption></figure></div>
  <dl><div><dt>자리</dt><dd><b>{w}×{d}칸, 높이 {math.ceil(h - 1e-9)}칸</b> (히트박스. 보이는 높이는 {h:g}칸)</dd></div>
    <div><dt>꼴</dt><dd>{form} · {io}</dd></div>
    <div><dt>실루엣</dt><dd>{html.escape(sil)}</dd></div>
    <div><dt>주인공</dt><dd>{html.escape(hero)}</dd></div>
    <div><dt>조연</dt><dd>{html.escape(extra) or "없음 (1급은 주인공 하나와 벽의 층 한 겹)"}</dd></div>
    <div><dt>모델</dt><dd>{html.escape(state)}</dd></div></dl>
</article>'''

ladder = "".join(f'<figure>{side(w, h, g, c=12, tall=5.2)}<figcaption>{name}<br>{h:g} → {math.ceil(h - 1e-9)}칸</figcaption></figure>'
                 for name, g, form, w, d, h, *_ in sorted(M, key=lambda r: (r[5], r[3] * r[4])))

page = f'''<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>기계 설계표</title>
<style>
:root {{ --bg:#f4f3ef; --ink:#22252a; --mute:#666c74; --card:#fff; --line:#dcdad3; --belt:#4a5058; --grid:#00000022;
        --g0:#8d6bc4; --g1:#9aa1a9; --g2:#5c9ac0; --g3:#cf8246; --bp:#2f7d54; }}
@media (prefers-color-scheme: dark) {{ :root {{ --bg:#1b1d21; --ink:#e9e7e2; --mute:#a0a6ae; --card:#25282d; --line:#3a3e45; --belt:#14161a; --grid:#ffffff22;
        --g0:#a98ce0; --g1:#868d95; --g2:#4f8fb6; --g3:#c9783c; --bp:#5fbf8b; }} }}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--bg); color:var(--ink); font:16px/1.6 -apple-system, "Apple SD Gothic Neo", "Malgun Gothic", sans-serif; }}
main {{ max-width:1120px; margin:0 auto; padding:32px 16px 72px; }}
h1 {{ font-size:30px; margin:0 0 4px; letter-spacing:-0.02em; }}
h2 {{ font-size:21px; margin:48px 0 4px; }}
.lead {{ color:var(--mute); margin:0 0 16px; }}
.box {{ background:var(--card); border:1px solid var(--line); border-radius:10px; padding:16px 20px; }}
.box li {{ margin:5px 0; }}
table {{ width:100%; border-collapse:collapse; font-size:15px; }}
th, td {{ text-align:left; padding:6px 8px; border-top:1px solid var(--line); vertical-align:top; }}
th {{ color:var(--mute); font-weight:600; border-top:0; }}
.scroll {{ overflow-x:auto; }}
.ladder {{ display:flex; align-items:flex-end; gap:8px; justify-content:space-between; overflow-x:auto; padding:16px 20px; background:var(--card); border:1px solid var(--line); border-radius:10px; }}
figure {{ margin:0; text-align:center; font-size:12px; color:var(--mute); }}
.ladder figcaption {{ margin-top:4px; white-space:nowrap; }}
.grid2 {{ display:grid; grid-template-columns:repeat(auto-fill, minmax(330px, 1fr)); gap:14px; }}
.card {{ background:var(--card); border:1px solid var(--line); border-radius:10px; padding:14px 16px; }}
.card header {{ display:flex; align-items:baseline; gap:8px; flex-wrap:wrap; }}
.card h3 {{ margin:0; font-size:19px; }}
.grade {{ font-size:12px; font-weight:700; padding:1px 8px; border:2px solid; border-radius:20px; }}
.grade.g0 {{ color:var(--g0); }} .grade.g1 {{ color:var(--g1); }} .grade.g2 {{ color:var(--g2); }} .grade.g3 {{ color:var(--g3); }}
.bp {{ font-size:12px; font-weight:700; color:var(--bp); border:2px solid var(--bp); border-radius:20px; padding:1px 8px; }}
.concept {{ margin:6px 0 10px; font-size:14px; color:var(--mute); }}
.draw {{ display:flex; align-items:flex-end; gap:18px; padding:8px 0 10px; overflow-x:auto; }}
.body.g0 {{ fill:var(--g0); }} .body.g1 {{ fill:var(--g1); }} .body.g2 {{ fill:var(--g2); }} .body.g3 {{ fill:var(--g3); }}
.belt {{ fill:var(--belt); }} .port {{ fill:#fff; }} .hit {{ fill:none; stroke:var(--mute); stroke-width:1; stroke-dasharray:3 3; }} .grid {{ stroke:var(--grid); stroke-width:1; }} .ground {{ stroke:var(--mute); stroke-width:1; }}
.man {{ fill:var(--mute); }}
dl {{ margin:0; font-size:14px; }}
dl div {{ display:grid; grid-template-columns:64px 1fr; gap:8px; border-top:1px solid var(--line); padding:5px 0; }}
dt {{ color:var(--mute); }} dd {{ margin:0; }}
footer {{ margin-top:40px; font-size:13px; color:var(--mute); }}
</style></head><body><main>
<h1>기계 설계표</h1>
<p class="lead">모델을 만들기 전에 기계마다 크기, 높이, 꼴, 볼거리를 정하는 표입니다. 전부 제안이고, 보고 고치시면 됩니다. 1칸은 3스터드이고, 그림 옆의 사람은 캐릭터 키(1.67칸쯤)입니다.</p>

<h2>정하는 규칙</h2>
<div class="box"><ul style="margin:0; padding-left:20px">
  <li><b>히트박스는 정수 칸입니다(개발자 확정).</b> 가로, 세로, 높이 모두 정수 칸이고, 보이는 모델은 그 안에서 소수 칸이어도 됩니다. 모델은 히트박스 밖으로 나가지 않습니다. 그림의 점선이 히트박스입니다.</li>
  <li><b>따로 놓는 벨트와 맞물립니다(개발자 확정).</b> 입구와 출구는 항상 칸 한 변의 한가운데에 있고(그림의 흰 화살표), 기계에 붙은 벨트는 따로 놓는 벨트와 폭, 높이, 난간이 똑같으며 칸 경계에서 반듯하게 끝납니다. 그래서 어느 벨트를 대도 이음매 없이 이어집니다.</li>
  <li><b>꼴은 셋입니다.</b> 내놓기만 하는 기계는 벨트가 한쪽에만 붙고(2×1칸), 재료 하나를 받는 기계는 벨트가 몸통을 지나가고(3×1칸), 둘 이상을 받아 합치는 기계는 입구가 여럿입니다(3×3칸).</li>
  <li><b>높이는 급을 따라갑니다.</b> 보이는 높이는 1급이 캐릭터 키보다 낮거나 비슷하게(1.3~1.6칸), 2급은 조금 높게(1.5~2칸), 3급은 올려다보게(2.2~3.5칸), 큰 목표는 섬에서 가장 높게(5칸). 히트박스로는 1급과 2급이 모두 2칸, 3급이 3~4칸, 핵 제련소가 5칸입니다.</li>
  <li><b>볼거리도 급을 따라갑니다.</b> 1급은 주인공 하나, 2급은 주인공과 그것을 움직이는 장치 한둘, 3급은 주인공과 조연 여럿에 구조물.</li>
  <li><b>연료와 물은 같은 벨트로 받습니다.</b> 용광로의 석탄, 세척기의 물통은 재료와 한 벨트에 섞여 들어오는 것으로 보고 입구를 하나로 쳤습니다. 입구가 여럿인 기계는 합치는 기계 셋과 핵 제련소뿐입니다.</li>
  <li><b>청사진이 필요한 기계</b>는 문턱이 되는 넷으로 잡았습니다: 용광로, 제철소, 조립기, 핵 제련소.</li>
</ul></div>

<h2>높이를 한 줄로</h2>
<p class="lead">낮은 것부터 늘어놓았습니다. 색칠한 부분이 보이는 높이, 점선이 히트박스(정수 칸)입니다. 숫자는 "보이는 높이 → 히트박스 높이".</p>
<div class="ladder">{ladder}</div>

<h2>기계별로</h2>
<div class="grid2">{cards}</div>

<footer>크기는 겉모습만이 아니라 섬에서 차지하는 자리, 곧 게임 규칙입니다. 게임 코드는 아직 모든 기계를 1칸으로 다루므로, 여기서 정한 크기를 쓰려면 코드도 바꿔야 합니다. 컨셉 문장은 설계 문서 8.18절, 급은 8.20절, 모델링 원칙은 <code>docs/modeling-principles.md</code>. 다시 만들려면 <code>python3 data/machine_sheet.py</code>.</footer>
</main></body></html>'''
out = os.path.join(ROOT, "docs", "machine-sheet.html")
open(out, "w", encoding="utf-8", newline="\n").write(page)
print("wrote", out, len(M), "machines")
