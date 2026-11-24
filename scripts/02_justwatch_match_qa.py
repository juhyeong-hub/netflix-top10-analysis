# -*- coding: utf-8 -*-
# ─────────────────────────────────────────────────────────────────────────────
# [용도] 02. JustWatch 수집 결과 품질 검증 — 연도 교차검증 + 제목 유사도로
#        오매칭 의심 건 식별 → genre_missing_justwatch.csv 갱신
# [환경] Python 3.15.2 (Windows) / pandas 3.1.1 — requirements.txt 참고
#        실행: python scripts/02_justwatch_match_qa.py
# [경로] ROOT = 스크립트 위치 기준 프로젝트 루트 (scripts/ 상위)
# ─────────────────────────────────────────────────────────────────────────────
import re

import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
df = pd.read_csv(ROOT / "data/processed/genre_missing_justwatch.csv")
df = df[df.has_result].copy()

# 연도 추출: 원제목에 괄호 연도가 있으면 (예: "A Different World (1987)")
def orig_year(t):
    m = re.search(r"\((\d{4})\)", t)
    return int(m.group(1)) if m else None

df["orig_year"] = df.show_title.map(orig_year)
df["matched_year"] = pd.to_numeric(df.matched_year, errors="coerce")

# 1) 연도 교차검증: 원제 연도와 매칭 연도가 2년 이상 차이나면 오매칭 의심
mask_year = df.orig_year.notna() & df.matched_year.notna()
year_ok = (df.loc[mask_year, "orig_year"] - df.loc[mask_year, "matched_year"]).abs() <= 2
print(f"연도 교차검증 가능: {mask_year.sum()}건 | 연도 불일치(의심): {(~year_ok).sum()}건")

suspicious = df[mask_year & ~year_ok]
print("\n== 연도 불일치 샘플 10 ==")
for _, r in suspicious.head(10).iterrows():
    print(f"  {r.show_title} (원연도 {int(r.orig_year)}) → {r.matched_title} ({int(r.matched_year)}) | {r.genres_ko}")

# 2) 제목 유사도: 정규화한 원제와 매칭제목이 완전히 다르면 한국어화 매칭
def norm(s):
    s = re.sub(r"[\(\[\{].*?[\)\]\}]", "", str(s))
    s = re.sub(r"[^0-9a-zA-Z가-힣]", "", s).lower()
    return s

df["orig_norm"] = df.show_title.map(norm)
df["match_norm"] = df.matched_title.map(norm)
df["similar"] = df.apply(lambda r: (r.orig_norm in r.match_norm) or (r.match_norm in r.orig_norm) or (r.orig_norm == r.match_norm), axis=1)
n_similar = df.similar.sum()
print(f"\n제목 유사(원제 포함): {n_similar}건 | 한국어화 등 유사도 낮음: {len(df)-n_similar}건")
diff = df[~df.similar]
print("== 유사도 낮은 샘플 10 ==")
for _, r in diff.head(10).iterrows():
    print(f"  {r.show_title} → {r.matched_title} | {r.genres_ko}")

# 유사도 낮은 그룹의 연도 검증
d2 = diff[diff.orig_year.notna() & diff.matched_year.notna()]
ok2 = ((d2.orig_year - d2.matched_year).abs() <= 2).mean()
print(f"\n유사도 낮음 중 연도 검증 가능 {len(d2)}건 중 일치 {ok2*100:.0f}%")

# 종합 판단: 연도 불일치(검증 가능한 한) = 오매칭으로 탈락
sus_idx = set(suspicious.index)
final = df[~df.index.isin(sus_idx)]
print(f"\n최종 채택: {len(final)}편 (오매칭 의심 {len(sus_idx)}편 제외)")
final.to_csv(ROOT / "data/processed/genre_missing_justwatch.csv", index=False, encoding="utf-8-sig")
print("CSV 갱신 완료 (오매칭 의심 제거)")
