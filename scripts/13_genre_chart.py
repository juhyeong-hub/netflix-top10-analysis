# -*- coding: utf-8 -*-
# ─────────────────────────────────────────────────────────────────────────────
# [용도] 13. 장르별 영어권 통과율 그래프 생성 (18_genre_barrier.png)
#        language_barrier_by_genre.csv 기반 가로 막대그래프 — 전체 평균 23.8% 점선,
#        레드 = 통과율 30% 이상(긴밀감 장르), 회색 = 18% 미만
# [환경] Python 3.15.2 (Windows) / pandas 3.1.1, matplotlib 3.11.2 — requirements.txt 참고
#        (한국어 렌더링: Malgun Gothic)
#        실행: python scripts/13_genre_chart.py
# [경로] ROOT = 스크립트 위치 기준 프로젝트 루트 (scripts/ 상위)
# ─────────────────────────────────────────────────────────────────────────────
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "reports" / "figures"

df = pd.read_csv(ROOT / "data/processed/language_barrier_by_genre.csv")
KO = {"Drama": "드라마", "Comedy": "코미디", "Action": "액션", "Thriller": "스릴러", "Crime": "범죄",
      "Romance": "로맨스", "Family": "가족", "Animation": "애니메이션", "Fantasy": "판타지",
      "Documentary": "다큐멘터리", "Reality-TV": "리얼리티", "Sci-Fi": "SF", "Horror": "호러",
      "History": "역사", "Mystery": "미스터리", "Biography": "전기", "Adventure": "어드벤처"}
df["label"] = df.장르.map(lambda g: f"{KO.get(g, g)} ({g})")
df = df.sort_values("영어권진입률", ascending=True)

plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False
fig, ax = plt.subplots(figsize=(8.8, 5.6), dpi=160)
colors = ["#e50914" if r >= 30 else ("#c9c9c9" if r < 18 else "#888888") for r in df.영어권진입률]
ax.barh(range(len(df)), df.영어권진입률, height=0.62, color=colors, zorder=3)
ax.set_yticks(range(len(df)))
ax.set_yticklabels(df.label, fontsize=10.5)
ax.set_xlim(0, 40)
ax.set_xlabel("비영어 출신 히트의 영어권 차트 진입률 (%)", fontsize=10, color="#555")
for i, (rate, n_) in enumerate(zip(df.영어권진입률, df.표본)):
    ax.text(rate + 0.3, i, f"{rate:.1f}%  (표본 {n_:,})", va="center", fontsize=9.5,
            fontweight="bold", color="#141414")
ax.axvline(23.8, color="#999", lw=1.4, ls="--", zorder=2)
ax.text(23.9, len(df) - 0.4, "전체 평균 23.8%", fontsize=9.5, color="#666")
ax.grid(axis="x", color="#eee", zorder=0)
for s in ["top", "right", "left"]:
    ax.spines[s].set_visible(False)
ax.spines["bottom"].set_color("#ccc")
ax.tick_params(left=False, bottom=False)
fig.tight_layout()
fig.savefig(FIG / "18_genre_barrier.png", facecolor="white", bbox_inches="tight")
plt.close(fig)
print("그래프 생성 완료: 18_genre_barrier.png")
