# -*- coding: utf-8 -*-
# ─────────────────────────────────────────────────────────────────────────────
# [용도] 11. 모델 번들 검증 — 학습 메타데이터·피처·raw vs Isotonic 보정 예측 비교
#        보고서 "Isotonic 확률 보정" 섹션의 근거 (보정 전 56.9% → 보정 후 27.3%)
# [환경] Python 3.15.2 (Windows) / pandas 3.1.1, numpy 2.5.4,
#        scikit-learn 1.9.1, lightgbm 4.7.0, joblib 1.6.0 — requirements.txt 참고
#        실행: python scripts/11_calibration_check.py
# [경로] ROOT = 스크립트 위치 기준 프로젝트 루트 (scripts/ 상위)
# ─────────────────────────────────────────────────────────────────────────────
import joblib
import pandas as pd
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

bundle = joblib.load(ROOT / "models/model_v2_lgbm.joblib")
print("모델명:", bundle["model_name"])
print("학습 시점:", bundle["trained_at"])
print("학습 구간:", bundle["training_window"])
print("테스트 구간:", bundle["test_window"])
print("피처 수:", len(bundle["feature_names"]))

r = pd.read_csv(ROOT / "data/processed/model_retrain_20261115_results.csv")
print("\n== retrain 결과 파일 ==")
print(r.to_string(index=False))

# 시뮬레이터 기본 조건으로 raw vs 보정 비교
power = pd.read_csv(ROOT / "data/processed/country_market_power.csv")
pop_y = pd.read_csv(ROOT / "references/country_population_by_year.csv")
CONT = dict(pd.read_csv(ROOT / "references/country_continent.csv").values)
POWER_DF = power.set_index("country")
PWR = (POWER_DF.나라파워셰어 * 1000).to_dict()
DENS = {y: POWER_DF[f"파워/인구비_{y}"].to_dict() for y in range(2021, 2027)}
PY = pop_y.set_index("country_name")
feats = bundle["feature_names"]
ORDER = ["유럽", "아시아", "북중미", "남미", "아프리카", "오세아니아"]
TAGS = [t[3:] for t in feats if t.startswith("장르_")]

row = {name: 0.0 for name in feats}
sel = ["South Korea", "Japan", "Taiwan"]
row["진입국가수"] = len(sel)
row["진입대륙수"] = 1
for k in ORDER:
    row[f"{k}국가수"] = sum(1 for c in sel if CONT[c] == k)
    row[f"첫진입_{k}"] = int(k == "아시아")
row["TV여부"] = 1
row["데뷔영어권"] = 1
row["진입시장파워"] = sum(PWR.get(c, 0) for c in sel)
row["진입시장인구_log"] = np.log1p(sum(PY.loc[c, "2024"] for c in sel))
row["진입시장밀도합"] = sum(DENS[2024].get(c, 0) or 0 for c in sel)
row["진입시장밀도평균"] = row["진입시장밀도합"] / 3
for tag in TAGS:
    row[f"장르_{tag}"] = int(tag == "Drama")
row["장르결측"] = 0
Xin = pd.DataFrame([row])[feats].to_numpy().astype(float)

for snap in ["1주차", "4주차"]:
    model = bundle["models"][f"{snap}_글로벌히트_lgbm"]
    cal_g = bundle["models"].get(f"{snap}_글로벌히트_lgbm_calibrated")
    raw = model.predict_proba(Xin)[0, 1]
    p = cal_g.predict_proba(Xin)[0, 1] if cal_g is not None else raw
    print(f"\n[{snap}] raw={raw*100:.1f}% → 보정={p*100:.1f}%")
