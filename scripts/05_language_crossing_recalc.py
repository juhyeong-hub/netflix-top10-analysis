# -*- coding: utf-8 -*-
# ─────────────────────────────────────────────────────────────────────────────
# [용도] 05. 언어 교차 매트릭스(12행) 최종 재계산
#        출신언어 = 글로벌 차트 카테고리(English/Non-English) 판정,
#        혼합 카테고리 8편·국가 차트 미진입 19편 제외 → 영어 1,734 / 비영어 1,824
# [환경] Python 3.15.2 (Windows) / pandas 3.1.1, numpy 2.5.4 — requirements.txt 참고
#        실행: python scripts/05_language_crossing_recalc.py
# [경로] ROOT = 스크립트 위치 기준 프로젝트 루트 (scripts/ 상위)
# ─────────────────────────────────────────────────────────────────────────────
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

g_all = pd.concat([
    pd.read_csv(ROOT / "data/raw/all-weeks-global.csv", sep=","),
    pd.read_csv(ROOT / "data/raw/all-weeks-global_2026-11-11.tsv", sep="\t")]).drop_duplicates()
c_all = pd.concat([
    pd.read_csv(ROOT / "data/raw/all-weeks-countries.csv", sep=",", encoding="cp1252"),
    pd.read_csv(ROOT / "data/raw/all-weeks-countries_2026-11-11.tsv", sep="\t")]).drop_duplicates()

cc = pd.read_csv(ROOT / "references/country_continent.csv")
CONT = dict(zip(cc.country_name, cc["대륙"]))
EN_MARKETS = {"United States", "United Kingdom", "Canada", "Australia", "Ireland", "New Zealand"}

hits = set(g_all.show_title.unique())
c_titles = set(c_all.show_title.unique())
g_all["lang_cat"] = g_all.category.str.contains("Non-English").map({True: "비영어", False: "영어"})
lang_sets = g_all.groupby("show_title").lang_cat.apply(set)
only_en = {t for t, s in lang_sets.items() if s == {"영어"}}
only_ne = {t for t, s in lang_sets.items() if s == {"비영어"}}
no_country = hits - c_titles
pop_en = only_en - no_country
pop_ne = only_ne - no_country

ever = c_all.groupby("show_title").country_name.apply(set)

# ---- cmat: 기존 표 구조(6 타깃 그룹 × 2 출신 = 12행) 유지 ----
targets = {"영어권": EN_MARKETS}
for k, name in [("유럽", "유럽(비영어)"), ("아시아", "아시아"), ("남미", "남미"),
                ("아프리카", "아프리카"), ("오세아니아", "오세아니아(비영어)")]:
    targets[name] = {c for c in CONT if CONT[c] == k and c not in EN_MARKETS}

rows = []
for origin, pop in [("영어", pop_en), ("비영어", pop_ne)]:
    pop_ever = ever.loc[ever.index.isin(pop)]
    for tname, grp in targets.items():
        rate = pop_ever.apply(lambda cs: bool(cs & grp)).mean() * 100
        rows.append({"출신언어": origin, "타깃시장": tname, "진입률": round(rate, 1), "표본": len(pop)})
cmat = pd.DataFrame(rows)
cmat.to_csv(ROOT / "data/processed/language_crossing_matrix.csv", index=False, encoding="utf-8-sig")
print("== cmat (12행) ==")
print(cmat.to_string(index=False))
ne_en = cmat[(cmat.출신언어 == "비영어") & (cmat.타깃시장 == "영어권")].진입률.iloc[0]
en_ne = cmat[(cmat.출신언어 == "영어") & (cmat.타깃시장.isin(["유럽(비영어)", "아시아", "남미", "아프리카", "오세아니아(비영어)"]))].진입률.mean()
print(f"\n지표: 비영어→영어권 {ne_en}% | 영어→비영어권 5그룹 평균 {en_ne:.1f}%")
