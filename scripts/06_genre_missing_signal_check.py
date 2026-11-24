# -*- coding: utf-8 -*-
# ─────────────────────────────────────────────────────────────────────────────
# [용도] 06. 장르 결측 그룹 vs 장르 확보 그룹 실측 비교
#        (글로벌 히트율 10.9% vs 29.9%, 평균 데뷔 규모 3.8 vs 15.1개국)
#        — 장르 "결측"이 무작위가 아니라 저인지도 작품을 대변하는 신호임을 검증
# [환경] Python 3.15.2 (Windows) / pandas 3.1.1, numpy 2.5.4 — requirements.txt 참고
#        실행: python scripts/06_genre_missing_signal_check.py
# [경로] ROOT = 스크립트 위치 기준 프로젝트 루트 (scripts/ 상위)
# ─────────────────────────────────────────────────────────────────────────────
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

c_old = pd.read_csv(ROOT / "data/raw/all-weeks-countries.csv", sep=",", encoding="cp1252")
c_new = pd.read_csv(ROOT / "data/raw/all-weeks-countries_2026-11-11.tsv", sep="\t")
c_all = pd.concat([c_old, c_new]).drop_duplicates()
g_all = pd.concat([
    pd.read_csv(ROOT / "data/raw/all-weeks-global.csv", sep=","),
    pd.read_csv(ROOT / "data/raw/all-weeks-global_2026-11-11.tsv", sep="\t")]).drop_duplicates()

hits = set(g_all.show_title.unique())
cat = pd.read_csv(ROOT / "data/interim/netflix_titles_catalog.csv")
gen = cat.set_index("show_title").imdb_genres.fillna("").astype(str).str.strip()

titles = pd.DataFrame({"show_title": sorted(c_all.show_title.unique())})
titles["has_genre"] = titles.show_title.map(gen).fillna("").str.strip().ne("")
titles["is_hit"] = titles.show_title.isin(hits).astype(int)
cnt = c_all.groupby("show_title").country_name.nunique()
titles["국가수"] = titles.show_title.map(cnt)

g = titles.groupby("has_genre").agg(
    작품수=("show_title", "size"),
    글로벌히트율=("is_hit", "mean"),
    평균진입국가수=("국가수", "mean"))
g.index = ["결측(장르 미확보)", "장르 확보"]
g["글로벌히트율"] = (g["글로벌히트율"] * 100).round(1)
g["평균진입국가수"] = g["평균진입국가수"].round(1)
print(g.to_string())
