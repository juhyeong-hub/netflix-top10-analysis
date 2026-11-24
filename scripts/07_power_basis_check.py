# -*- coding: utf-8 -*-
# ─────────────────────────────────────────────────────────────────────────────
# [용도] 07. 누적 파워셰어(그림 2 기준) vs 기간별 파워(그림 3 기준) 차이 검증
#        미국: 누적 20.14% (1위) vs 2026H1 13.4% (4위) — 두 그림의 기준 차이 입증
# [환경] Python 3.15.2 (Windows) / pandas 3.1.1, numpy 2.5.4 — requirements.txt 참고
#        실행: python scripts/07_power_basis_check.py
# [경로] ROOT = 스크립트 위치 기준 프로젝트 루트 (scripts/ 상위)
# ─────────────────────────────────────────────────────────────────────────────
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

p = pd.read_csv(ROOT / "data/processed/country_market_power.csv")
us = p[p.country == "United States"].iloc[0]
print("== 그림 2 기준: 전 기간(281주) 누적 추정 ==")
print(f"미국 나라파워셰어: {us['나라파워셰어']*100:.2f}%  (전체 1위)")

ry = pd.read_csv(ROOT / "data/processed/market_power_rolling_yearly.csv", index_col=0)
print("\n== 그림 3 기준: 기간별 각각 재추정 (각 시점 합계 100%) ==")
col = ry["2026H1"].sort_values(ascending=False)
for k, v in col.head(5).items():
    print(f"  {k}: {v*100:.1f}%")
print("2026H1 합계:", round(ry['2026H1'].sum()*100, 1), "%")

# 미국: 기간별 값의 기간가중 평균 vs 누적값
w = {"2021H2": 0.5, "2022": 1.0, "2023": 1.0, "2024": 1.0, "2025": 1.0, "2026H1": 0.5}
us_vals = ry.loc["미국"]
num = sum(us_vals[c] * 100 * w[c] for c in w)
den = sum(w.values())
print(f"\n미국 기간별 값: {[f'{us_vals[c]*100:.1f}' for c in w]}")
print(f"미국 기간가중 평균: {num/den:.1f}%  vs  누적 추정 20.14%")
