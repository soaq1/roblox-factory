# Builds catalog/index.html from catalog/catalog.json and the rendered thumbnails.
import json, os, html

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "catalog")
data = json.load(open(os.path.join(OUT, "catalog.json"), encoding="utf-8"))

FAMILIES = [
    ("운반", "아이템을 옮기고, 나누고, 합치고, 골라내는 장치"),
    ("공급", "아무것도 넣지 않아도 자원을 내보내는 기계"),
    ("변환", "재료 하나를 받아 정해진 결과물로 바꾸는 기계"),
    ("조합", "재료 둘 이상을 받아 하나로 만드는 기계"),
    ("포장·판매", "묶어서 물체 수를 줄이고, 코인으로 바꾸는 기계"),
    ("동력", "다른 기계를 돌리는 전력을 만드는 기계"),
]
SIDE = {"W": "뒤", "E": "앞", "N": "왼쪽", "S": "오른쪽"}


def ports_text(ports):
    ins = [SIDE[s] for s, k, _ in ports if k == "in"]
    outs = [SIDE[s] for s, k, _ in ports if k == "out"]
    parts = []
    if ins:
        parts.append(f"입구 {len(ins)}")
    if outs:
        parts.append(f"출구 {len(outs)}")
    return " · ".join(parts) if parts else "벨트"


cards = {f: [] for f, _ in FAMILIES}
for m in data["machines"]:
    size = f'{m["size"][0]}×{m["size"][1]}칸'
    cards[m["fam"]].append(f'''
    <figure class="card">
      <div class="shot"><img src="img/{m["key"]}.png" alt="{html.escape(m["ko"])}" loading="lazy"></div>
      <figcaption>
        <h3>{html.escape(m["ko"])}</h3>
        <p class="recipe">{html.escape(m["recipe"])}</p>
        <p class="meta">{size} · {ports_text(m["ports"])} · 삼각형 {m["tris"]:,}</p>
      </figcaption>
    </figure>''')

sections = "".join(f'''
  <section>
    <h2>{f} <span class="count">{len(cards[f])}</span></h2>
    <p class="lede">{d}</p>
    <div class="grid">{"".join(cards[f])}</div>
  </section>''' for f, d in FAMILIES if cards[f])

total = len(data["machines"])
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
  body {{ margin: 0; background: var(--bg); color: var(--text);
         font: 16px/1.6 -apple-system, "Apple SD Gothic Neo", "Pretendard", sans-serif; }}
  main {{ max-width: 1180px; margin: 0 auto; padding: 40px 20px 80px; }}
  h1 {{ font-size: 34px; margin: 0 0 6px; letter-spacing: -0.02em; }}
  .sub {{ color: var(--dim); margin: 0 0 28px; }}
  h2 {{ font-size: 24px; margin: 56px 0 2px; padding-bottom: 10px; border-bottom: 1px solid var(--line); }}
  .count {{ color: var(--dim); font-size: 16px; font-weight: 400; margin-left: 6px; }}
  .lede {{ color: var(--dim); margin: 10px 0 20px; }}
  .hero img, .items img {{ width: 100%; display: block; border-radius: 10px; }}
  .items {{ background: var(--panel); border: 1px solid var(--line); border-radius: 10px; padding: 8px; }}
  .legend {{ display: flex; flex-wrap: wrap; gap: 10px 22px; margin: 18px 0 0; padding: 0; list-style: none;
            color: var(--dim); font-size: 14px; }}
  .legend i {{ display: inline-block; width: 12px; height: 12px; border-radius: 3px; margin-right: 7px;
              vertical-align: -1px; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 16px; }}
  .card {{ margin: 0; background: var(--panel); border: 1px solid var(--line); border-radius: 10px;
          overflow: hidden; }}
  .shot {{ aspect-ratio: 1; background: #16181b; }}
  .shot img {{ width: 100%; height: 100%; object-fit: contain; display: block; }}
  figcaption {{ padding: 12px 14px 14px; }}
  h3 {{ margin: 0 0 4px; font-size: 17px; color: var(--link); }}
  .recipe {{ margin: 0 0 8px; font-size: 14.5px; }}
  .meta {{ margin: 0; font-size: 12.5px; color: var(--dim); font-variant-numeric: tabular-nums; }}
</style>
</head>
<body>
<main>
  <h1>공장 기계 카탈로그</h1>
  <p class="sub">기계와 벨트 {total}종 · 시험 제작본 · 모든 모델은 스크립트로 생성</p>
  <div class="hero"><img src="img/_line.png" alt="벨트로 연결한 공장 예시"></div>
  <ul class="legend">
    <li><i style="background:var(--in)"></i>노란 테두리는 입구</li>
    <li><i style="background:var(--out)"></i>청록 테두리는 출구</li>
    <li><i style="background:#ff5a1f"></i>주황 발광은 열</li>
    <li><i style="background:#4aa8d8"></i>파랑은 물</li>
    <li><i style="background:#d9483b"></i>빨강은 움직이는 부품</li>
  </ul>
  {sections}
  <section>
    <h2>아이템 <span class="count">{len(data["items"])}</span></h2>
    <p class="lede">벨트 위를 굴러다니는 물체들</p>
    <div class="items"><img src="img/_items.png" alt="아이템 모음"></div>
  </section>
</main>
</body>
</html>
'''
open(os.path.join(OUT, "index.html"), "w", encoding="utf-8").write(page)
print("wrote", os.path.join(OUT, "index.html"), "machines:", total)
