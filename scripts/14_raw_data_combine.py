# -*- coding: utf-8 -*-
# ─────────────────────────────────────────────────────────────────────────────
# [용도] 14. 원본 데이터 결합·정리 — 구(2021-07~2022-01) + 신(2022-01~2026-11)
#        데이터를 결합해 분석 기준 테이블을 만든다
#        출력: data/interim/all-weeks-combined_global.csv / _countries.csv
# [환경] Python 3.15.2 (Windows) / pandas 3.1.1, numpy 2.5.4 — requirements.txt 참고
#        실행: python scripts/14_raw_data_combine.py
# [경로] ROOT = 스크립트 위치 기준 프로젝트 루트 (scripts/ 상위)
# [재현] 입력(raw 파일 4개)이 같으면 출력이 결정적으로 동일함 — 완전 재현 가능
#        ※ 하위 분석 스크립트(05~08)는 이 결합 과정을 내장하고 있어 독립 실행 가능
# ─────────────────────────────────────────────────────────────────────────────
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# ---- 1) 구형 데이터 (2021-07-04 ~ 2022-01-16, 쉼표 구분 / 국가별 파일은 cp1252) ----
g_old = pd.read_csv(ROOT / "data/raw/all-weeks-global.csv", sep=",")
c_old = pd.read_csv(ROOT / "data/raw/all-weeks-countries.csv", sep=",", encoding="cp1252")
print(f"구형 global: {len(g_old)}행 ({g_old.week.min()} ~ {g_old.week.max()})")
print(f"구형 countries: {len(c_old)}행 ({c_old.week.min()} ~ {c_old.week.max()})")

# ---- 2) 신형 데이터 (2022-01-23 ~ 2026-11-15, 탭 구분 TSV) ----
g_new = pd.read_csv(ROOT / "data/raw/all-weeks-global_2026-11-11.tsv", sep="\t")
c_new = pd.read_csv(ROOT / "data/raw/all-weeks-countries_2026-11-11.tsv", sep="\t")
print(f"신형 global: {len(g_new)}행 ({g_new.week.min()} ~ {g_new.week.max()})")
print(f"신형 countries: {len(c_new)}행 ({c_new.week.min()} ~ {c_new.week.max()})")

# ---- 3) 결합 + 완전 중복 제거 ----
g_all = pd.concat([g_old, g_new]).drop_duplicates()
c_all = pd.concat([c_old, c_new]).drop_duplicates()
print(f"\n결합 global: {len(g_all)}행 | 고유 작품 {g_all.show_title.nunique()}편")
print(f"결합 countries: {len(c_all)}행 | 고유 작품 {c_all.show_title.nunique()}편 | 국가 {c_all.country_name.nunique()}개국")
print(f"분석 기간: {c_all.week.min()} ~ {c_all.week.max()} ({c_all.week.nunique()}주)")

# ---- 4) 저장 (중간 산출물 — data/interim) ----
g_all.to_csv(ROOT / "data/interim/all-weeks-combined_global.csv", index=False, encoding="utf-8-sig")
c_all.to_csv(ROOT / "data/interim/all-weeks-combined_countries.csv", index=False, encoding="utf-8-sig")
print("\n저장 완료: data/interim/all-weeks-combined_global.csv, _countries.csv")

# ---- 5) 기대치 대조 ----
assert g_all.week.nunique() == 281, "주차 수 불일치!"
assert c_all.country_name.nunique() == 94, "국가 수 불일치!"
assert c_all.show_title.nunique() == 12486, "고유 작품 수 불일치!"
print("기대치 대조 통과: 281주 · 94개국 · 12,486편 ✓")
