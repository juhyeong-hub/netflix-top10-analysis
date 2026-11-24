# -*- coding: utf-8 -*-
# ─────────────────────────────────────────────────────────────────────────────
# [용도] 08. 언어 교차 표본(영어 1,734 / 비영어 1,824, 합 3,558) 산출 과정 재현
#        글로벌 히트 3,585편 중 혼합 카테고리 8편·국가 차트 미진입 19편 제외 검증
# [환경] Python 3.15.2 (Windows) / pandas 3.1.1, numpy 2.5.4 — requirements.txt 참고
#        실행: python scripts/08_crossing_sample_verify.py
# [경로] ROOT = 스크립트 위치 기준 프로젝트 루트 (scripts/ 상위)
# ─────────────────────────────────────────────────────────────────────────────
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

g_old = pd.read_csv(ROOT / "data/raw/all-weeks-global.csv", sep=",")
c_old = pd.read_csv(ROOT / "data/raw/all-weeks-countries.csv", sep=",", encoding="cp1252")
g_new = pd.read_csv(ROOT / "data/raw/all-weeks-global_2026-11-11.tsv", sep="\t")
c_new = pd.read_csv(ROOT / "data/raw/all-weeks-countries_2026-11-11.tsv", sep="\t")
g_all = pd.concat([g_old, g_new]).drop_duplicates()
c_all = pd.concat([c_old, c_new]).drop_duplicates()

hits = set(g_all.show_title.unique())
c_titles = set(c_all.show_title.unique())
g_all["lang_cat"] = g_all.category.str.contains("Non-English").map({True: "비영어", False: "영어"})
lang_sets = g_all.groupby("show_title").lang_cat.apply(set)

only_en = {t for t, s in lang_sets.items() if s == {"영어"}}
only_ne = {t for t, s in lang_sets.items() if s == {"비영어"}}
both = {t for t, s in lang_sets.items() if s == {"영어", "비영어"}}
no_country = hits - c_titles
print("국가 차트 미등장:", len(no_country))
print("혼합 카테고리(둘 다 등장):", len(both), sorted(both))

measurable = (only_en | only_ne) - no_country
print("\n영어 카테고리 표본:", len(only_en - no_country))
print("비영어 카테고리 표본:", len(only_ne - no_country))
print("합계:", len(measurable))
print("\n→ cmat 표본: 영어 1,734 / 비영어 1,824 (합 3,558) | 현재 데이터 기준 글로벌 히트", len(hits))
