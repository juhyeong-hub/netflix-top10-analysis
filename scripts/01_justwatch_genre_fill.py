# -*- coding: utf-8 -*-
# ─────────────────────────────────────────────────────────────────────────────
# [용도] 01. JustWatch GraphQL로 IMDb 장르 미확보 853편의 장르 수집
#        → data/processed/genre_missing_justwatch.csv 저장 (요청 간격 0.8초, 재개 지원)
# [환경] Python 3.15.2 (Windows) / pandas 3.1.1, numpy 2.5.4 — requirements.txt 참고
#        외부 API: apis.justwatch.com/graphql (API 키 불필요, 네트워크 연결 필요)
#        실행: python scripts/01_justwatch_genre_fill.py
# [경로] ROOT = 스크립트 위치 기준 프로젝트 루트 (scripts/ 상위)
# ─────────────────────────────────────────────────────────────────────────────
import json
import os
import ssl
import time
import urllib.request

import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/processed/genre_missing_justwatch.csv"

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

QUERY = """query {
  searchTitles(source: "/kr", country: "KR", filter: {searchQuery: "%s"}, first: 5) {
    edges { node {
      id objectId objectType
      content(country: "KR", language: "ko") {
        title fullPath originalReleaseYear
        genres { shortName translation(language: "ko") }
      }
    } }
  }
}"""

def gql(title):
    esc = title.replace("\\", "\\\\").replace('"', '\\"')
    payload = {"query": QUERY % esc}
    req = urllib.request.Request(
        "https://apis.justwatch.com/graphql",
        data=json.dumps(payload).encode(),
        headers={
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0",
            "Origin": "https://www.justwatch.com",
            "Referer": "https://www.justwatch.com/kr",
        })
    with urllib.request.urlopen(req, timeout=30, context=ctx) as r:
        return json.loads(r.read().decode())

def search_genre(title, netflix_cat):
    d = gql(title)
    edges = d.get("data", {}).get("searchTitles", {}).get("edges", []) or []
    want = "MOVIE" if netflix_cat == "Films" else "SHOW"
    pool = [e["node"] for e in edges if e.get("node")]
    cands = [n for n in pool if n.get("objectType") == want] or pool
    if not cands:
        return "", "", "", ""
    n = cands[0]
    c = n.get("content") or {}
    short = "|".join(g.get("shortName", "") for g in (c.get("genres") or []))
    ko = "|".join((g.get("translation") or "") for g in (c.get("genres") or []))
    return c.get("title", ""), c.get("originalReleaseYear", ""), short, ko

# ---- 데이터 준비 ----
c_old = pd.read_csv(ROOT / "data/raw/all-weeks-countries.csv", sep=",", encoding="cp1252")
c_new = pd.read_csv(ROOT / "data/raw/all-weeks-countries_2026-11-11.tsv", sep="\t")
c_all = pd.concat([c_old, c_new]).drop_duplicates()
cat = pd.read_csv(ROOT / "data/interim/netflix_titles_catalog.csv")
catmap = cat.set_index("show_title").netflix_category.to_dict()
cat_gen = cat.set_index("show_title").imdb_genres.fillna("").astype(str).str.strip()

titles = sorted(c_all.show_title.unique())
missing_all = [t for t in titles if cat_gen.get(t, "") == ""]
print(f"장르 결측: {len(missing_all)}편 / 전체 {len(titles)}편", flush=True)

# 재개: 성공한 것만 스킵
done = set()
if os.path.exists(OUT):
    prev = pd.read_csv(OUT)
    done = set(prev[prev.has_result].show_title)
    print(f"기존 진행분(성공): {len(done)}편", flush=True)

todo = [t for t in missing_all if t not in done]
print(f"남은 작업: {len(todo)}편", flush=True)

rows = []
t0 = time.time()
for i, t in enumerate(todo):
    ncat = catmap.get(t, "")
    matched, year, short, ko = "", "", "", ""
    ok = False
    for attempt in range(3):
        try:
            matched, year, short, ko = search_genre(t, ncat)
            ok = bool(short)
            break
        except Exception as e:
            if attempt == 2:
                print(f"  최종실패 {t}: {type(e).__name__}", flush=True)
            time.sleep(3 + attempt * 4)
    rows.append({"show_title": t, "netflix_category": ncat, "has_result": ok,
                 "matched_title": matched, "matched_year": year,
                 "genres_short": short, "genres_ko": ko})
    if (i + 1) % 50 == 0 or i == len(todo) - 1:
        df = pd.DataFrame(rows)
        if os.path.exists(OUT):
            df = pd.concat([pd.read_csv(OUT), df])
        df.to_csv(OUT, index=False, encoding="utf-8-sig")
        rate = (df.has_result.sum() / len(df) * 100) if len(df) else 0
        print(f"  {i+1}/{len(todo)} | 누적 저장 {len(df)}편 | 매칭률 {rate:.0f}% | 경과 {int(time.time()-t0)}초", flush=True)
    time.sleep(0.8)

df = pd.read_csv(OUT)
print(f"\n최종: {len(df)}편 처리, 매칭 성공 {int(df.has_result.sum())}편 ({df.has_result.mean()*100:.0f}%)", flush=True)
