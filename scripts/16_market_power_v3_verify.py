# -*- coding: utf-8 -*-
# ─────────────────────────────────────────────────────────────────────────────
# [용도] 16. 시장 파워 v3 — 방법론 기록 + 결과 파일 내부 정합성 검증
#
# [방법론 (원 설계 기록)]
#   ① 작품 고정효과 통제: 같은 작품이 여러 나라 차트에 오르는 패턴을 이용해
#      "작품 자체의 인기 수준"을 통제한 상태에서 나라별 기여를 분리
#   ② NNLS 블록 분해: 94개국을 14개 블록(미국·캐나다·인도·브라질·동아시아 등)으로
#      묶고, 각 블록이 글로벌 시청량을 만드는 비중을 비음수 최소제곱(NNLS)으로 추정
#      — 음수를 허용하지 않으므로 "파워는 있거나 0"
#   ③ 리프트(미러) 분리: 각 나라 차트가 글로벌 차트를 따라오는 정도(리프트)를
#      따로 계산해 파워(시청량 창출)와 미러(따라잡기)를 분리
#   ④ 연도별 재추정 검증: 2021H2~2026H1을 기간별로 다시 추정해 추세 확인
#
# [주의] 원본 구현 코드는 미보존. 본 스크립트는 결과 파일의 내부 정합성을 검증하는
#        재현 코드이며, NNLS 추정 자체를 다시 수행하지는 않는다.
# [환경] Python 3.15.2 (Windows) / pandas 3.1.1, numpy 2.5.4 — requirements.txt 참고
#        실행: python scripts/16_market_power_v3_verify.py
# [경로] ROOT = 스크립트 위치 기준 프로젝트 루트 (scripts/ 상위)
# ─────────────────────────────────────────────────────────────────────────────
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# ---- 1) 국가별 파워 (country_market_power.csv) ----
p = pd.read_csv(ROOT / "data/processed/country_market_power.csv")
print("== country_market_power.csv ==")
print(f"행 수(국가): {len(p)} | 컬럼: {list(p.columns)[:8]}...")
total_share = p.나라파워셰어.sum()
print(f"나라파워셰어 합계: {total_share:.4f} (1.0 = 글로벌 시청량 100%)")
print(f"상위 5개국: {p.nlargest(5, '나라파워셰어')[['country', '나라파워셰어']].to_string(index=False)}")

# ---- 2) 밀도 열 정합성 (파워/인구비 연도별 존재 확인) ----
dens_cols = [c for c in p.columns if "파워/인구비" in c]
print(f"\n밀도 열 (파워/인구비): {dens_cols}")

# ---- 3) 사분면 분포 (파워 × 미러 분류 결과) ----
if "사분면" in p.columns:
    print(f"\n사분면 분포: {p.사분면.value_counts().to_dict()}")

# ---- 4) 연도별 롤링 추정 (market_power_rolling_yearly.csv) ----
ry = pd.read_csv(ROOT / "data/processed/market_power_rolling_yearly.csv", index_col=0)
print("\n== market_power_rolling_yearly.csv ==")
print(f"블록 {len(ry)}개 × 기간 {len(ry.columns)}개")
for c in ry.columns:
    s = ry[c].sum()
    flag = "OK" if abs(s - 1.0) < 0.01 else "확인 필요"
    print(f"  {c}: 합계 {s*100:.1f}% [{flag}] — 각 시점 합계 100% 검증")

# ---- 5) 14개 블록 정의 (market_power_blocks_v3.csv) ----
blocks = pd.read_csv(ROOT / "data/processed/market_power_blocks_v3.csv")
print(f"\n== market_power_blocks_v3.csv (블록 정의) ==")
print(f"행 수: {len(blocks)} | 컬럼: {list(blocks.columns)}")

# ---- 6) 순수 미러 시장 (파워 ≈ 0 & 리프트 높음) ----
mirror = p[(p.나라파워셰어 < 0.001) & (p["리프트(미러)"] >= 3.9)]
print(f"\n순수 미러 시장 (파워<0.1% & 리프트≥3.9): {len(mirror)}개국")
print(mirror[["country", "리프트(미러)"]].head(8).to_string(index=False))
