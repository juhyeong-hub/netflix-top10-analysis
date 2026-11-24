# -*- coding: utf-8 -*-
# ─────────────────────────────────────────────────────────────────────────────
# [용도] 17. 모델 번들 재현·검증 — 학습된 모델의 예측이 저장소 기록과 일치하는지
#        결정적으로 재현 (모델 사용·평가는 완전 재현 가능 영역)
#
# [주의] 원본 학습 코드는 미보존. 재학습 자체는 시드·환경 차이로 결과가 달라질 수
#        있으므로, 본 스크립트는 "학습된 번들을 그대로 사용한 예측 재현"을 담당한다.
# [환경] Python 3.15.2 (Windows) / pandas 3.1.1, numpy 2.5.4,
#        scikit-learn 1.9.1, lightgbm 4.7.0, joblib 1.6.0 — requirements.txt 참고
#        실행: python scripts/17_model_bundle_verify.py
# [경로] ROOT = 스크립트 위치 기준 프로젝트 루트 (scripts/ 상위)
# ─────────────────────────────────────────────────────────────────────────────
import joblib
import pandas as pd
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# ---- 1) 번load + 메타 확인 ----
bundle = joblib.load(ROOT / "models/model_v2_lgbm.joblib")
print("== 번들 메타 ==")
print("모델명:", bundle["model_name"])
print("학습 시점:", bundle["trained_at"])
print("학습 구간:", bundle["training_window"])
print("테스트 구간:", bundle["test_window"])
print("피처 수:", len(bundle["feature_names"]))
print("모델 키:", list(bundle["models"].keys()))

# ---- 2) 성능 기록 대조 (model_35week_results.csv) ----
res = pd.read_csv(ROOT / "data/processed/model_35week_results.csv")
print("\n== model_35week_results.csv (시간 분할 성능 기록) ==")
print(res.to_string(index=False))

# ---- 3) 결정적 예측 재현 — 시뮬레이터 기본 조건 (한국·일본·대만, 1주차) ----
# 보고서 기록값: raw 56.9% → 보정 27.3%
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

model = bundle["models"]["1주차_글로벌히트_lgbm"]
cal_g = bundle["models"]["1주차_글로벌히트_lgbm_calibrated"]
raw = model.predict_proba(Xin)[0, 1]
cal = cal_g.predict_proba(Xin)[0, 1]
print(f"\n== 결정적 예측 재현 (기본 조건, 1주차) ==")
print(f"raw = {raw*100:.1f}% (기록: 56.9%)")
print(f"보정 = {cal*100:.1f}% (기록: 27.3%)")
ok = abs(raw*100 - 56.9) < 0.5 and abs(cal*100 - 27.3) < 0.5
print("재현 판정:", "성공 ✓ — 번들 예측이 기록과 일치" if ok else "불일치 — 번들/데이터 버전 확인 필요")
