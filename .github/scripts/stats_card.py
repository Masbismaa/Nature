"""Bikin kartu statistik GitHub bertema lembah hijau (stats.svg, langs.svg, valley.svg).

Jalan di GitHub Actions, ambil data lewat GraphQL pakai GITHUB_TOKEN,
terus nulis SVG ke folder output. Tanpa library tambahan, cukup Python bawaan.
"""

import json
import os
import sys
import urllib.request
from datetime import date, timedelta

USERNAME = os.environ.get("GH_USER", "Masbismaa")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
OUT_DIR = sys.argv[1] if len(sys.argv) > 1 else "dist"

INK = "#2E3A32"
PEN = "#3E6B48"
CORAL = "#C8553D"
SOFT = "#66705F"
PAPER = "#F7F1E3"
HAND = "'Bitter','Rockwell',Georgia,serif"
MONO = "Consolas,'SFMono-Regular',Menlo,monospace"
BAR_COLORS = ["#6FA35E", "#F2C14E", "#C8553D", "#4F83A8", "#7C6A9E", "#D98F3E"]

QUERY = """
query($login: String!) {
  user(login: $login) {
    followers { totalCount }
    repositories(ownerAffiliations: OWNER, isFork: false, first: 100, orderBy: {field: PUSHED_AT, direction: DESC}) {
      totalCount
      nodes {
        stargazerCount
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name } }
        }
      }
    }
    contributionsCollection {
      totalCommitContributions
      totalPullRequestContributions
      totalIssueContributions
      contributionCalendar {
        totalContributions
        weeks { contributionDays { contributionCount date } }
      }
    }
  }
}
"""


def fetch():
    # ambil data user dari GraphQL GitHub
    body = json.dumps({"query": QUERY, "variables": {"login": USERNAME}}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=body,
        headers={"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as res:
        data = json.load(res)
    if "errors" in data or not data.get("data", {}).get("user"):
        raise RuntimeError(json.dumps(data.get("errors", data))[:300])
    return data["data"]["user"]


def mock():
    # data palsu buat ngetes lokal tanpa internet
    days, start = [], date.today() - timedelta(days=364)
    for i in range(365):
        d = start + timedelta(days=i)
        days.append({"date": d.isoformat(), "contributionCount": (i * 7) % 5 if i % 9 else 0})
    weeks = [{"contributionDays": days[i:i + 7]} for i in range(0, 365, 7)]
    langs = [("Python", 52000), ("JavaScript", 21000), ("PHP", 12000), ("HTML", 9000), ("CSS", 6000), ("Dart", 3000)]
    return {
        "followers": {"totalCount": 12},
        "repositories": {"totalCount": 9, "nodes": [{"stargazerCount": 3, "languages": {"edges": [{"size": s, "node": {"name": n}} for n, s in langs]}}]},
        "contributionsCollection": {
            "totalCommitContributions": 214, "totalPullRequestContributions": 18, "totalIssueContributions": 7,
            "contributionCalendar": {"totalContributions": 312, "weeks": weeks},
        },
    }


def streaks(weeks):
    # hitung streak sekarang & terpanjang dari kalender kontribusi
    days = [d for w in weeks for d in w["contributionDays"]]
    days.sort(key=lambda d: d["date"])
    longest = run = 0
    for d in days:
        run = run + 1 if d["contributionCount"] > 0 else 0
        longest = max(longest, run)
    current = 0
    for i, d in enumerate(reversed(days)):
        if d["contributionCount"] > 0:
            current += 1
        elif i == 0:
            continue  # hari ini belum commit, streak belum putus
        else:
            break
    return current, longest


def esc(text):
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def paper(w, h):
    return f'<rect width="{w}" height="{h}" rx="16" fill="#F7F1E3"/>'


def frame(w, h):
    # kartu krem dengan bingkai hijau lembut, kayak buku sketsa di padang rumput
    return f"""<defs>
  </defs>
  {paper(w, h)}
  <rect x="8" y="8" width="{w-16}" height="{h-16}" rx="10" fill="#FFFBF1" stroke="#DCD3BC" stroke-width="2"/><rect x="8" y="8" width="6" height="{h-16}" fill="#C8553D"/>
  <path d="M26 26 q10 -14 22 -8 q-4 14 -22 8 z" fill="#6FA35E"/>"""


STYLE = """
    @keyframes fade { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: none; } }
    @keyframes grow { from { transform: scaleX(0); } to { transform: scaleX(1); } }
    @keyframes draw { to { stroke-dashoffset: 0; } }
    .f { opacity: 0; animation: fade .6s ease-out forwards; }
    .g { transform-box: fill-box; transform-origin: left; animation: grow .9s cubic-bezier(.6,.1,.2,1) both; }
    .d { stroke-dasharray: 400; stroke-dashoffset: 400; animation: draw 1.2s ease-out .4s forwards; }
"""


def stats_svg(u):
    cc = u["contributionsCollection"]
    cur, longest = streaks(cc["contributionCalendar"]["weeks"])
    stars = sum(r["stargazerCount"] for r in u["repositories"]["nodes"])
    items = [
        ("kontribusi setahun", cc["contributionCalendar"]["totalContributions"]),
        ("commit", cc["totalCommitContributions"]),
        ("pull request", cc["totalPullRequestContributions"]),
        ("issue", cc["totalIssueContributions"]),
        ("repository", u["repositories"]["totalCount"]),
        ("bintang", stars),
    ]
    w, h = 440, 230
    cells = []
    for i, (label, value) in enumerate(items):
        col, row = i % 3, i // 3
        x, y = 34 + col * 130, 104 + row * 62
        cells.append(
            f'<g class="f" style="animation-delay:{0.15 + i * 0.12:.2f}s">'
            f'<text x="{x}" y="{y}" font-family="{HAND}" font-size="28" font-weight="700" fill="{INK}">{esc(value)}</text>'
            f'<text x="{x}" y="{y + 20}" font-family="{HAND}" font-size="13" fill="{SOFT}">{esc(label)}</text></g>'
        )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
  <style>{STYLE}</style>
  {frame(w, h)}
  <text x="30" y="46" font-family="{HAND}" font-size="20" font-weight="700" fill="{PEN}">catatan aktivitas</text>
  <path class="d" d="M30 56 Q 110 50, 196 58" fill="none" stroke="{CORAL}" stroke-width="3.5" stroke-linecap="round"/>
  <g class="f" style="animation-delay:.2s" transform="rotate(4 360 44)">
    <rect x="300" y="22" width="118" height="46" rx="8" fill="#3E6B48"/>
    <text x="359" y="42" text-anchor="middle" font-family="{HAND}" font-size="13" fill="#FFFFFF">streak {cur} hari</text>
    <text x="359" y="59" text-anchor="middle" font-family="{HAND}" font-size="11" fill="#EAF4E4">terpanjang {longest}</text>
  </g>
  {"".join(cells)}
</svg>
"""


def langs_svg(u):
    totals = {}
    for repo in u["repositories"]["nodes"]:
        for edge in repo["languages"]["edges"]:
            totals[edge["node"]["name"]] = totals.get(edge["node"]["name"], 0) + edge["size"]
    top = sorted(totals.items(), key=lambda kv: kv[1], reverse=True)[:6]
    grand = sum(totals.values()) or 1
    w, h = 440, 230
    rows = []
    if not top:
        rows.append(f'<text x="30" y="120" font-family="{HAND}" font-size="16" fill="{SOFT}">belum ada kode publik</text>')
    for i, (name, size) in enumerate(top):
        pct = size / grand * 100
        y = 78 + i * 24
        bar_w = max(6, 230 * size / top[0][1])
        rows.append(
            f'<g class="f" style="animation-delay:{0.1 + i * 0.1:.2f}s">'
            f'<text x="30" y="{y + 12}" font-family="{HAND}" font-size="14" fill="{INK}">{esc(name)}</text>'
            f'<rect class="g" style="animation-delay:{0.3 + i * 0.1:.2f}s" x="128" y="{y}" width="{bar_w:.1f}" height="15" rx="4" fill="{BAR_COLORS[i % len(BAR_COLORS)]}" stroke="#2E3A32" stroke-opacity=".25" stroke-width="1"/>'
            f'<text x="{136 + bar_w:.1f}" y="{y + 12}" font-family="{MONO}" font-size="12" fill="{SOFT}">{pct:.1f}%</text></g>'
        )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
  <style>{STYLE}</style>
  {frame(w, h)}
  <text x="30" y="46" font-family="{HAND}" font-size="20" font-weight="700" fill="{PEN}">bahasa paling sering</text>
  <path class="d" d="M30 56 Q 120 50, 222 58" fill="none" stroke="{CORAL}" stroke-width="3.5" stroke-linecap="round"/>
  {"".join(rows)}
</svg>
"""


def valley_svg(u):
    # grafik kontribusi setahun + elang yang meluncur menumbuhkan kotaknya satu per satu
    weeks = u["contributionsCollection"]["contributionCalendar"]["weeks"][-53:]
    total = u["contributionsCollection"]["contributionCalendar"]["totalContributions"]
    cell, gap, left, top = 12, 3, 40, 70
    cols = len(weeks)
    w = left * 2 + cols * (cell + gap)
    h = top + 7 * (cell + gap) + 46
    cycle, fly = 10, 7.0
    levels = ["#CFE6B8", "#9BC47A", "#6FA35E", "#3E6B48"]
    counts = [d["contributionCount"] for wk in weeks for d in wk["contributionDays"]]
    peak = max(counts) if counts else 0

    def level(c):
        if c <= 0 or peak == 0:
            return None
        return levels[min(3, int((c / peak) * 4 - 1e-9))]

    empty, filled = [], []
    for ci, wk in enumerate(weeks):
        x = left + ci * (cell + gap)
        delay = ci / max(1, cols - 1) * fly
        for day in wk["contributionDays"]:
            ri = date.fromisoformat(day["date"]).isoweekday() % 7
            y = top + ri * (cell + gap)
            empty.append(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="3" fill="#F2EAD6"/>')
            color = level(day["contributionCount"])
            if color:
                filled.append(
                    f'<rect class="c" style="animation-delay:{delay:.2f}s" x="{x}" y="{y}" width="{cell}" height="{cell}" rx="3" '
                    f'fill="{color}"/>'
                )

    # jalur lentera: melayang pelan di atas grid, dari kiri ke kanan
    y0 = top - 26
    x_end = left + cols * (cell + gap)
    seg = (x_end - left) / 6
    path = f"M{left - 30} {y0} " + " ".join(
        f"Q {left + seg * (i + 0.5):.1f} {y0 + (18 if i % 2 == 0 else -12)}, {left + seg * (i + 1):.1f} {y0}" for i in range(6)
    ) + f" L {w + 60} {y0 - 30}"

    style = f"""
    @keyframes pop {{ 0% {{ transform: scale(0); }} 4% {{ transform: scale(1.25); }} 7%, 90% {{ transform: scale(1); }} 100% {{ transform: scale(0); }} }}
    .c {{ transform-box: fill-box; transform-origin: center; transform: scale(0); animation: pop {cycle}s ease-out infinite; }}
    @keyframes trail {{ 0% {{ stroke-dashoffset: 1000; opacity: 1; }} 78% {{ stroke-dashoffset: 0; opacity: 1; }} 90% {{ opacity: 1; }} 100% {{ stroke-dashoffset: 0; opacity: 0; }} }}
    .trail {{ stroke-dasharray: 1000; stroke-dashoffset: 1000; animation: trail {cycle}s linear infinite; }}
    @keyframes fade {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
    .f {{ animation: fade .8s ease-out both; }}
"""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
  <style>{style}</style>
  {frame(w, h)}
  <text x="{left}" y="36" font-family="{HAND}" font-size="18" font-weight="700" fill="{PEN}" class="f">jejak elang di lembah</text>
  <text x="{w - left}" y="36" text-anchor="end" font-family="{HAND}" font-size="14" fill="{SOFT}" class="f">{total} kontribusi setahun</text>
  {"".join(empty)}
  {"".join(filled)}
  <path class="trail" pathLength="1000" d="{path}" fill="none" stroke="{PEN}" stroke-width="1.6" stroke-linecap="round" opacity=".45"/>
  <g>
    <g><animateTransform attributeName="transform" type="scale" values="1 1;1 .55;1 1" dur="1.2s" repeatCount="indefinite"/>
      <path d="M-34 2 C -24 -10, -12 -12, 0 0 C 12 -12, 24 -10, 34 2 C 24 -4, 12 -2, 0 6 C -12 -2, -24 -4, -34 2 Z" fill="#2E3A32"/>
    </g>
    <path d="M-3 0 C -3 -4, 3 -4, 3 0 L 0 8 Z" fill="#3A2E24"/>
    <animateMotion dur="{cycle}s" repeatCount="indefinite" keyPoints="0;1;1" keyTimes="0;{fly / cycle + 0.08:.2f};1" calcMode="linear" path="{path}"/>
  </g>
  <g font-family="{HAND}" font-size="12" fill="{SOFT}">
    <text x="{left}" y="{h - 18}">sedikit</text>
    {"".join(f'<rect x="{left + 50 + i * 18}" y="{h - 29}" width="12" height="12" rx="3" fill="{c}"/>' for i, c in enumerate(levels))}
    <text x="{left + 50 + 4 * 18 + 6}" y="{h - 18}">banyak</text>
  </g>
</svg>
"""


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    user = mock() if os.environ.get("MOCK") else fetch()
    with open(os.path.join(OUT_DIR, "stats.svg"), "w", encoding="utf-8") as f:
        f.write(stats_svg(user))
    with open(os.path.join(OUT_DIR, "langs.svg"), "w", encoding="utf-8") as f:
        f.write(langs_svg(user))
    with open(os.path.join(OUT_DIR, "valley.svg"), "w", encoding="utf-8") as f:
        f.write(valley_svg(user))
    print("kartu statistik selesai dibuat di", OUT_DIR)


if __name__ == "__main__":
    main()
