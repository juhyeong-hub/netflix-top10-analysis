# -*- coding: utf-8 -*-
# ─────────────────────────────────────────────────────────────────────────────
# [용도] 10. 시뮬레이터 조건별 확률 검증 — 기본 3개국/미국 단독/대륙 조합 등
#        raw vs Isotonic 보정 확률 비교 (보고서 시뮬레이터 표의 수치 출처)
# [환경] Python 3.15.2 (Windows) / pandas 3.1.1, numpy 2.5.4,
#        scikit-learn 1.9.1, lightgbm 4.7.0, joblib 1.6.0 — requirements.txt 참고
#        실행: python scripts/10_simulator_sweep.py
# [경로] ROOT = 스크립트 위치 기준 프로젝트 루트 (scripts/ 상위)
# ─────────────────────────────────────────────────────────────────────────────
import joblib
import pandas as pd
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

power = pd.read_csv(ROOT / "data/processed/country_market_power.csv")
pop_y = pd.read_csv(ROOT / "references/country_population_by_year.csv")
CONT = dict(pd.read_csv(ROOT / "references/country_continent.csv").values)
POWER_DF = power.set_index("country")
PWR = (POWER_DF.나라파워셰어 * 1000).to_dict()
DENS = {y: POWER_DF[f"파워/인구비_{y}"].to_dict() for y in range(2021, 2027)}
PY = pop_y.set_index("country_name")

bundle = joblib.load(ROOT / "models/model_v2_lgbm.joblib")
feats = bundle["feature_names"]
ORDER = ["유럽", "아시아", "북중미", "남미", "아프리카", "오세아니아"]
TAGS = [t[3:] for t in feats if t.startswith("장르_")]

def pred(sel, debut, tv="TV", lang="영어", genres=["Drama"], year=2024, snap="1주차"):
    row = {name: 0.0 for name in feats}
    sel = list(dict.fromkeys(sel))
    row["진입국가수"] = len(sel)
    conts = {CONT[c] for c in sel}
    row["진입대륙수"] = len(conts)
    for k in ORDER:
        row[f"{k}국가수"] = sum(1 for c in sel if CONT[c] == k)
    debut_cont = CONT.get(debut)
    for k in ORDER:
        row[f"첫진입_{k}"] = int(k == debut_cont)
    row["TV여부"] = int(tv == "TV")
    row["데뷔영어권"] = int(lang == "영어")
    row["진입시장파워"] = sum(PWR.get(c, 0) for c in sel)
    row["진입시장인구_log"] = np.log1p(sum(PY.loc[c, str(year)] for c in sel))
    row["진입시장밀도합"] = sum(DENS[year].get(c, 0) or 0 for c in sel)
    row["진입시장밀도평균"] = row["진입시장밀도합"] / max(len(sel), 1)
    for tag in TAGS:
        row[f"장르_{tag}"] = int(tag in genres)
    row["장르결측"] = int(len(genres) == 0)
    Xin = pd.DataFrame([row])[feats].to_numpy().astype(float)
    model = bundle["models"][f"{snap}_글로벌히트_lgbm"]
    cal_g = bundle["models"].get(f"{snap}_글로벌히트_lgbm_calibrated")
    raw = model.predict_proba(Xin)[0, 1]
    p = cal_g.predict_proba(Xin)[0, 1] if cal_g is not None else raw
    return raw * 100, p * 100

CASES = [
    ("기본 3개국 (한일대만)", ["South Korea", "Japan", "Taiwan"], "South Korea"),
    ("대륙모드 기본 5개국 (한일대만+홍콩+인도)", ["South Korea", "Japan", "Taiwan", "Hong Kong", "India"], "South Korea"),
    ("아시아 전체 13개국", ["South Korea", "Japan", "Taiwan", "Hong Kong", "India", "Indonesia", "Malaysia",
                        "Singapore", "Philippines", "Vietnam", "Thailand", "Pakistan", "Bangladesh"], "South Korea"),
    ("아시아+남미 전체 23개국", ["South Korea", "Japan", "Taiwan", "Hong Kong", "India", "Indonesia", "Malaysia",
                          "Singapore", "Philippines", "Vietnam", "Thailand", "Pakistan", "Bangladesh",
                          "Brazil", "Argentina", "Chile", "Colombia", "Peru", "Ecuador", "Venezuela",
                          "Bolivia", "Paraguay", "Uruguay"], "South Korea"),
    ("미국 단독", ["United States"], "United States"),
    ("영어권 6개국", ["United States", "United Kingdom", "Canada", "Australia", "Ireland", "New Zealand"], "United States"),
    ("미국+한일", ["United States", "South Korea", "Japan"], "United States"),
]

for name, sel, debut in CASES:
    r1, p1 = pred(sel, debut, snap="1주차")
    r4, p4 = pred(sel, debut, snap="4주차")
    print(f"{name}: 국가 {len(sel)}개")
    print(f"   1주차: raw={r1:.1f}% 보정={p1:.1f}% | 4주차: raw={r4:.1f}% 보정={p4:.1f}%")
