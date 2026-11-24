# -*- coding: utf-8 -*-
# ─────────────────────────────────────────────────────────────────────────────
# [용도] 03. JustWatch 수집 CSV 중복 정리 (중간 저장 로직의 중복 제거, 마지막 상태 유지)
#        + 장르 분포 요약
# [환경] Python 3.15.2 (Windows) / pandas 3.1.1 — requirements.txt 참고
#        실행: python scripts/03_justwatch_dedupe.py
# [경로] ROOT = 스크립트 위치 기준 프로젝트 루트 (scripts/ 상위)
# ─────────────────────────────────────────────────────────────────────────────
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/processed/genre_missing_justwatch.csv"

df = pd.read_csv(OUT)
print("정리 전:", len(df), "행")
df = df.drop_duplicates(subset="show_title", keep="last")
df = df.sort_values("show_title").reset_index(drop=True)
df.to_csv(OUT, index=False, encoding="utf-8-sig")
print("정리 후:", len(df), "행")
print("매칭 성공:", int(df.has_result.sum()), f"({df.has_result.mean()*100:.0f}%)")

print("\n== 장르 분포 (매칭된 것들, shortName 기준) ===")
g = df[df.has_result].genres_short.str.split("|").explode()
print(g.value_counts().head(15).to_string())

print("\n== 매칭 실패 샘플 ==")
fail = df[~df.has_result].show_title.tolist()
print(fail[:15])

print("\n== 매칭 성공 샘플 ==")
s = df[df.has_result].head(8)
for _, r in s.iterrows():
    print(f"  {r.show_title} → {r.matched_title} ({r.matched_year}) | {r.genres_ko}")
