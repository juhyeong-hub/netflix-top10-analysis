# -*- coding: utf-8 -*-
# ─────────────────────────────────────────────────────────────────────────────
# [용도] 12. 시장 파워 그래프 생성
#        16_power_top8.png (국가별 파워셰어 상위 8개국 막대그래프)
#        17_power_trend.png (블록별 파워셰어 연도별 추이 선그래프)
# [환경] Python 3.15.2 (Windows) / pandas 3.1.1, matplotlib 3.11.2 — requirements.txt 참고
#        (한국어 렌더링: Malgun Gothic)
#        실행: python scripts/12_power_charts.py
# [경로] ROOT = 스크립트 위치 기준 프로젝트 루트 (scripts/ 상위)
# ─────────────────────────────────────────────────────────────────────────────
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "reports" / "figures"

plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False

RED, DARK, GRAY, LGRAY = "#e50914", "#141414", "#7a7a7a", "#c9c9c9"

# ===== 1) 국가별 시장 파워 상위 8개국 =====
names = ["미국", "인도", "브라질", "캐나다", "일본", "멕시코", "인도네시아", "대한민국"]
vals = [20.14, 18.51, 16.45, 9.13, 8.83, 7.90, 3.72, 3.69]
dens = [3.03, 0.66, 4.05, 11.86, 3.79, 3.12, 0.68, 3.76]

fig, ax = plt.subplots(figsize=(8.6, 4.3), dpi=160)
y = range(len(names))
ax.barh(y, vals, height=0.62, color=[RED] * 6 + [LGRAY] * 2, zorder=3)
ax.set_yticks(list(y))
ax.set_yticklabels(names, fontsize=11)
ax.invert_yaxis()
ax.set_xlim(0, 24)
ax.set_xlabel("글로벌 시청량 중 그 시장이 실제로 만드는 비중 (%, 파워셰어)", fontsize=9.5, color="#555")
for i, (v, d) in enumerate(zip(vals, dens)):
    ax.text(v + 0.25, i, f"{v:.1f}%", va="center", fontsize=10, fontweight="bold", color=DARK)
    ax.text(v + 2.6, i, f"밀도 {d}", va="center", fontsize=8.5, color=GRAY)
ax.grid(axis="x", color="#eee", zorder=0)
for s in ["top", "right", "left"]:
    ax.spines[s].set_visible(False)
ax.spines["bottom"].set_color("#ccc")
ax.tick_params(left=False, bottom=False)
fig.tight_layout()
fig.savefig(FIG / "16_power_top8.png", facecolor="white", bbox_inches="tight")
plt.close(fig)

# ===== 2) 시간에 따른 파워 이동 =====
periods = ["2021H2", "2022", "2023", "2024", "2025", "2026H1"]
series = {
    "미국":     ([19.7, 7.1, 18.4, 15.1, 21.8, 13.4], DARK),
    "인도":     ([12.1, 27.4, 18.6, 20.7, 19.4, 23.7], RED),
    "브라질":   ([18.8, 13.7, 13.9, 14.6, 18.6, 21.3], "#b20710"),
    "캐나다":   ([20.2, 7.3, 7.1, 8.1, 7.7, 8.4], GRAY),
    "동아시아": ([0.0, 13.8, 13.1, 20.2, 12.0, 15.2], "#ff7562"),
    "멕시코":   ([16.6, 11.2, 12.2, 8.6, 1.5, 1.4], LGRAY),
}
fig, ax = plt.subplots(figsize=(8.6, 4.5), dpi=160)
x = range(len(periods))
offsets = {"인도": 0.5, "브라질": -0.5, "동아시아": 0.7, "미국": -0.7, "캐나다": 0.3, "멕시코": -0.3}
for name, (v, c) in series.items():
    ax.plot(list(x), v, color=c, lw=2.2, marker="o", ms=4.5, zorder=3)
    ax.annotate(f"{name} {v[-1]:.1f}", (len(periods) - 1 + 0.08, v[-1] + offsets.get(name, 0)),
                fontsize=9, color=c, va="center", fontweight="bold")
ax.set_xticks(list(x))
ax.set_xticklabels(periods, fontsize=10)
ax.set_xlim(-0.3, len(periods) - 0.25)
ax.set_ylim(-1.5, 29)
ax.set_ylabel("블록별 파워셰어 (%)", fontsize=9.5, color="#555")
ax.grid(axis="y", color="#eee", zorder=0)
for s in ["top", "right"]:
    ax.spines[s].set_visible(False)
ax.spines["left"].set_color("#ccc")
ax.spines["bottom"].set_color("#ccc")
ax.tick_params(left=False, bottom=False)
fig.tight_layout()
fig.savefig(FIG / "17_power_trend.png", facecolor="white", bbox_inches="tight")
plt.close(fig)
print("그래프 2장 생성 완료: 16_power_top8.png, 17_power_trend.png")
