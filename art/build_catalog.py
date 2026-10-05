# Builds catalog/index.html from catalog.json, blocks.json and the rendered thumbnails.
import json, os, html

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "catalog")
data = json.load(open(os.path.join(OUT, "catalog.json"), encoding="utf-8"))
blocks_path = os.path.join(OUT, "blocks.json")
blocks = json.load(open(blocks_path, encoding="utf-8")) if os.path.exists(blocks_path) else []

FAMILIES = [
    ("운반", "아이템을 옮기고, 나누고, 합치고, 골라내는 장치"),
    ("물리 장치", "떨어뜨리고, 밀고, 올리고, 쏘아 보내는 장치. 아이템이 실제로 굴러가는 게임이라 가능한 것들"),
    ("판단 장치", "신호를 만들고 조건에 따라 공장을 움직이는 장치"),
    ("공급", "아무것도 넣지 않아도 자원을 내보내거나, 밭과 나무를 돌보는 기계"),
    ("변환", "재료 하나를 받아 정해진 결과물로 바꾸는 기계"),
    ("조합", "재료 둘 이상을 받아 하나로 만드는 기계"),
    ("포장·판매", "묶어서 물체 수를 줄이고, 플레이어끼리 사고파는 장치"),
    ("동력", "전력을 만들고, 모으고, 나르는 기계"),
    ("궁극의 장치", "자동화의 자동화. 이 게임의 가장 큰 목표물"),
    ("손 작업", "공장이 없을 때 손으로 만드는 자리. 공장은 이 일을 대신해 줌"),
]
ITEM_CATS = ["도구", "원석과 광물", "광석 가공", "주괴", "금속 부품", "조립품", "건축 재료",
             "나무와 연료", "농산물과 음식", "광맥 핵", "포장"]
BLOCK_CATS = ["자연", "광석", "건축", "금속", "색 블록"]


def ports_text(ports):
    ins = sum(1 for _, k, _ in ports if k == "in")
    outs = sum(1 for _, k, _ in ports if k == "out")
    parts = ([f"입구 {ins}"] if ins else []) + ([f"출구 {outs}"] if outs else [])
    return " · ".join(parts) if parts else "출입구 없음"


def section(title, count, lede, body):
    return f'''
  <section id="{html.escape(title)}">
    <h2>{html.escape(title)} <span class="count">{count}</span></h2>
    <p class="lede">{html.escape(lede)}</p>
    {body}
  </section>'''


machine_cards = {f: [] for f, _ in FAMILIES}
for m in data["machines"]:
    machine_cards[m["fam"]].append(f'''
    <figure class="card">
      <div class="shot"><img src="img/{m["key"]}.png" alt="{html.escape(m["ko"])}" loading="lazy"></div>
      <figcaption>
        <h3>{html.escape(m["ko"])}</h3>
        <p class="recipe">{html.escape(m["recipe"])}</p>
        <p class="meta">{m["size"][0]}×{m["size"][1]}칸 · {ports_text(m["ports"])} · 삼각형 {m["tris"]:,}</p>
      </figcaption>
    </figure>''')
machine_html = "".join(section(f, len(machine_cards[f]), d, f'<div class="grid">{"".join(machine_cards[f])}</div>')
                       for f, d in FAMILIES if machine_cards[f])


def small_grid(entries, folder, cats):
    out = []
    for cat in cats:
        tiles = "".join(f'''
      <figure class="tile">
        <div class="shot"><img src="img/{folder}/{e["key"]}.png" alt="{html.escape(e["ko"])}" loading="lazy"></div>
        <figcaption>{html.escape(e["ko"])}</figcaption>
      </figure>''' for e in entries if e["cat"] == cat)
        if tiles:
            n = sum(1 for e in entries if e["cat"] == cat)
            out.append(f'<h3 class="cat">{html.escape(cat)} <span class="count">{n}</span></h3>'
                       f'<div class="tiles">{tiles}</div>')
    return "".join(out)


items_html = section("아이템", len(data["items"]), "손에 들거나 벨트 위를 굴러다니는 물건들. 도구부터 공장을 거친 재료까지",
                     small_grid(data["items"], "items", ITEM_CATS))
blocks_html = section("블록", len(blocks), "섬을 이루는 정육면체 블록. 스타일은 아직 확정하지 않은 시험 제작본",
                      small_grid(blocks, "blocks", BLOCK_CATS)) if blocks else ""

total = len(data["machines"])
nav = "".join(f'<a href="#{html.escape(t)}">{html.escape(t)}</a>'
              for t in [f for f, _ in FAMILIES if machine_cards[f]] + ["아이템"] + (["블록"] if blocks else []))

page = f'''<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>공장 기계 카탈로그</title>
<style>
  :root {{
    --bg: #1c1e22; --panel: #24272c; --line: #353a41; --text: #e9eaec; --dim: #9aa0a8;
    --in: #f0b429; --out: #35b8a6; --link: #58b6e8;
  }}
  * {{ box-sizing: border-box; }}
  html {{ scroll-behavior: smooth; }}
  body {{ margin: 0; background: var(--bg); color: var(--text);
         font: 16px/1.6 -apple-system, "Apple SD Gothic Neo", "Pretendard", sans-serif; }}
  main {{ max-width: 1180px; margin: 0 auto; padding: 40px 20px 80px; }}
  h1 {{ font-size: 34px; margin: 0 0 6px; letter-spacing: -0.02em; }}
  .sub {{ color: var(--dim); margin: 0 0 20px; }}
  nav {{ display: flex; flex-wrap: wrap; gap: 8px; margin: 0 0 28px; }}
  nav a {{ color: var(--link); text-decoration: none; font-size: 14px; padding: 5px 11px;
          border: 1px solid var(--line); border-radius: 999px; }}
  nav a:hover {{ background: var(--panel); }}
  h2 {{ font-size: 24px; margin: 56px 0 2px; padding-bottom: 10px; border-bottom: 1px solid var(--line); }}
  .count {{ color: var(--dim); font-size: 0.7em; font-weight: 400; margin-left: 6px; }}
  .lede {{ color: var(--dim); margin: 10px 0 20px; }}
  .hero img {{ width: 100%; display: block; border-radius: 10px; }}
  .legend {{ display: flex; flex-wrap: wrap; gap: 10px 22px; margin: 18px 0 0; padding: 0; list-style: none;
            color: var(--dim); font-size: 14px; }}
  .legend i {{ display: inline-block; width: 12px; height: 12px; border-radius: 3px; margin-right: 7px;
              vertical-align: -1px; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 16px; }}
  .card {{ margin: 0; background: var(--panel); border: 1px solid var(--line); border-radius: 10px;
          overflow: hidden; }}
  .shot {{ aspect-ratio: 1; background: #16181b; }}
  .shot img {{ width: 100%; height: 100%; object-fit: contain; display: block; }}
  .card figcaption {{ padding: 12px 14px 14px; }}
  .card h3 {{ margin: 0 0 4px; font-size: 17px; color: var(--link); }}
  .recipe {{ margin: 0 0 8px; font-size: 14.5px; }}
  .meta {{ margin: 0; font-size: 12.5px; color: var(--dim); font-variant-numeric: tabular-nums; }}
  h3.cat {{ font-size: 17px; margin: 28px 0 12px; }}
  .tiles {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(118px, 1fr)); gap: 10px; }}
  .tile {{ margin: 0; background: var(--panel); border: 1px solid var(--line); border-radius: 8px;
          overflow: hidden; }}
  .tile figcaption {{ padding: 7px 8px 9px; font-size: 13px; text-align: center; line-height: 1.35; }}
</style>
</head>
<body>
<main>
  <h1>공장 기계 카탈로그</h1>
  <p class="sub">기계와 장치 {total}종 · 아이템 {len(data["items"])}종 · 블록 {len(blocks)}종 · 시험 제작본 · 모든 모델은 스크립트로 생성</p>
  <nav>{nav}</nav>
  <div class="hero"><img src="img/_line.png" alt="벨트로 연결한 공장 예시"></div>
  <ul class="legend">
    <li><i style="background:var(--in)"></i>노란 테두리는 입구</li>
    <li><i style="background:var(--out)"></i>청록 테두리는 출구</li>
    <li><i style="background:#ff5a1f"></i>주황 발광은 열</li>
    <li><i style="background:#4aa8d8"></i>파랑은 물</li>
    <li><i style="background:#d9483b"></i>빨강은 움직이는 부품</li>
  </ul>
  {machine_html}
  {items_html}
  {blocks_html}
</main>
</body>
</html>
'''
open(os.path.join(OUT, "index.html"), "w", encoding="utf-8").write(page)
print("wrote index.html: machines", total, "items", len(data["items"]), "blocks", len(blocks))
