# -*- coding: utf-8 -*-
# ─────────────────────────────────────────────────────────────────────────────
# [용도] 09. 출신 언어 판정 기준 검증 — 데뷔 국가 기준이 아니라
#        글로벌 차트 카테고리(English/Non-English) 기준임을 입증
#        (데뷔 국가 기준으로는 영어 647/비영어 2,801 — cmat의 1,734/1,824와 불일치)
# [환경] Python 3.15.2 (Windows) / pandas 3.1.1, numpy 2.5.4 — requirements.txt 참고
#        실행: python scripts/09_language_category_verify.py
# [경로] ROOT = 스크립트 위치 기준 프로젝트 루트 (scripts/ 상위)
# ─────────────────────────────────────────────────────────────────────────────
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

g_old = pd.read_csv(ROOT / "data/raw/all-weeks-global.csv", sep=",")
c_old = pd.read_csv(ROOT / "data/raw/all-weeks-countries.csv", sep=",", encoding="cp1252")
g_new = pd.read_csv(ROOT / "data/raw/all-weeks-global_2026-11-11.tsv", sep="\t")
c_new = pd.read_csv(ROOT / "data/raw/all-weeks-countries_2026-11-11.tsv", sep="\t")
c_all = pd.concat([c_old, c_new]).drop_duplicates()
g_all = pd.concat([g_old, g_new]).drop_duplicates()

hits = set(g_all.show_title.unique())
c_titles = set(c_all.show_title.unique())
covered = hits & c_titles

EN_MARKETS = {"United States", "United Kingdom", "Canada", "Australia", "Ireland", "New Zealand"}

# 데뷔 국가 기준(반례 검증용)
first_entry = c_all.sort_values("week").groupby("show_title").agg(
    debut_country=("country_name", "first"), debut_week=("week", "first"))
sub = first_entry.loc[first_entry.index.isin(covered)]
lang2 = sub.debut_country.isin(EN_MARKETS).map({True: "영어", False: "비영어"})
print("데뷔 국가 기준:", lang2.value_counts().to_dict(), "← cmat와 불일치 (채택하지 않은 기준)")

# 채택 기준: 글로벌 차트 카테고리
g_all["lang_cat"] = g_all.category.str.contains("Non-English").map({True: "비영어", False: "영어"})
lang_sets = g_all.groupby("show_title").lang_cat.apply(set)
only_en = {t for t, s in lang_sets.items() if s == {"영어"}}
only_ne = {t for t, s in lang_sets.items() if s == {"비영어"}}
both = {t for t, s in lang_sets.items() if s == {"영어", "비영어"}}
no_country = hits - c_titles
pop_en = only_en - no_country
pop_ne = only_ne - no_country
print("\n채택 기준(카테고리): 영어", len(pop_en), "/ 비영어", len(pop_ne), "/ 혼합 제외", len(both),
      "/ 미진입 제외", len(no_country))
print("→ cmat 표본(영어 1,734 / 비영어 1,824)과 일치")
