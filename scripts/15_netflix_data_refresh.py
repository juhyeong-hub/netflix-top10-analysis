# -*- coding: utf-8 -*-
# ─────────────────────────────────────────────────────────────────────────────
# [용도] 15. 추가 데이터(2026-11-11 갱신분) 수집 절차 가이드 + 다운로드 파일 검증
#        수집 자체는 브라우저 다운로드(수동)이고, 본 스크립트는 절차 문서화 +
#        내려받은 파일의 정합성(기간·행수·작품 수)을 검증한다
# [환경] Python 3.15.2 (Windows) / pandas 3.1.1 — requirements.txt 참고
#        실행: python scripts/15_netflix_data_refresh.py
# [절차] 1) https://top10.netflix.com/downloads 접속
#        2) All Weeks Global / All Weeks Countries TSV 다운로드
#        3) 다운로드일을 접미사로 붙여 data/raw/에 저장
#           예: all-weeks-global_2026-11-11.tsv, all-weeks-countries_2026-11-11.tsv
#        4) 본 스크립트 실행 → 기존 구형 파일과 결합 가능한지 검증
# [경로] ROOT = 스크립트 위치 기준 프로젝트 루트 (scripts/ 상위)
# [재현] 다운로드 시점에 따라 사이트 데이터가 갱신되므로 완전 동일 수집은 보장되지
#        않음 — 커밋된 raw 파일(2026-11-11 수집본)을 그대로 쓰면 보고서와 동일
# ─────────────────────────────────────────────────────────────────────────────
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def inspect(path, sep, **kw):
    df = pd.read_csv(path, sep=sep, **kw)
    return df

print("== 1) 저장된 raw 파일 목록과 검증 ==")
targets = [
    ("data/raw/all-weeks-global.csv", ",", {}),
    ("data/raw/all-weeks-countries.csv", ",", {"encoding": "cp1252"}),
    ("data/raw/all-weeks-global_2026-11-11.tsv", "\t", {}),
    ("data/raw/all-weeks-countries_2026-11-11.tsv", "\t", {}),
]
for rel, sep, kw in targets:
    p = ROOT / rel
    df = inspect(p, sep, **kw)
    wc = [c for c in df.columns if "week" in c.lower()]
    period = f"{df[wc[0]].min()} ~ {df[wc[0]].max()}" if wc else "?"
    print(f"  {rel}")
    print(f"    행 {len(df):,} | 기간 {period} | 고유 작품 {df.show_title.nunique():,}편")

print("\n== 2) 결합 가능성 검증 (구형 끝 = 신형 시작과 이어지는지) ==")
g_old = inspect(ROOT / "data/raw/all-weeks-global.csv", ",")
g_new = inspect(ROOT / "data/raw/all-weeks-global_2026-11-11.tsv", "\t")
print(f"구형 마지막 주: {g_old.week.max()} / 신형 첫 주: {g_new.week.min()}")
gap_ok = pd.to_datetime(g_old.week.max()) + pd.Timedelta(days=7) == pd.to_datetime(g_new.week.min())
print("주차 연속성:", "OK — 결합 가능" if gap_ok else "확인 필요 (구형/신형 사이 빈 주차 발생)")

print("\n== 3) 결합 후 기대치 ==")
c_new = inspect(ROOT / "data/raw/all-weeks-countries_2026-11-11.tsv", "\t")
c_all = pd.concat([inspect(ROOT / "data/raw/all-weeks-countries.csv", ",", encoding="cp1252"), c_new]).drop_duplicates()
print(f"결합 countries: {len(c_all):,}행 | {c_all.week.nunique()}주 | {c_all.country_name.nunique()}개국 | "
      f"{c_all.show_title.nunique():,}편 — 281주·94개국·12,486편과 대조")
