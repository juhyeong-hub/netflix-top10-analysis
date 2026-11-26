# -*- coding: utf-8 -*-
"""Netflix Top 10 글로벌 확산 분석 — Streamlit 대시보드"""
# ─────────────────────────────────────────────────────────────────────────────
# 환경: Python 3.15.2 (Windows) / pandas 3.1.1, numpy 2.5.4,
#       scikit-learn 1.9.1, lightgbm 4.7.0, joblib 1.6.0,
#       shap 0.54.1, streamlit 1.67.0 — requirements.txt 참고
# 실행: python -m streamlit run app/streamlit_app.py
#       (또는 https://netflix-top10-analysis-by-juhyeonglee.streamlit.app/)
# 데이터: data/processed·references·models 하위 파일 필요 — GitHub 저장소에 포함
# 분석 파이프라인: scripts/01~17 참고 (수집→반영→재계산→검증→그래프)
# ─────────────────────────────────────────────────────────────────────────────
from pathlib import Path
import hashlib
import joblib
import numpy as np
import pandas as pd
import altair as alt
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
FIG = ROOT / "reports" / "figures"

st.set_page_config(page_title="Netflix Top 10 글로벌 확산 분석", page_icon="🎬", layout="wide")

# ---- Netflix 테마 ----
st.markdown("""
<style>
/* ===== Netflix 다크 테마 (클라우드 강제 적용) ===== */

/* 1. 배경 전면 다크 */
section[data-testid="stSidebar"] { background-color: #141414 !important; }
section[data-testid="stSidebar"] * { color: #e5e5e5 !important; }
header[data-testid="stHeader"] { background-color: #0b0b0b !important; }
div[data-testid="stAppViewContainer"] { background-color: #0b0b0b !important; }
div[data-testid="stAppViewContainer"] section[data-testid="stMain"],
div[data-testid="stAppViewContainer"] section[data-testid="stMain"] div.block-container {
    background-color: #0b0b0b !important;
}
body { background-color: #0b0b0b !important; color: #ffffff !important; }

/* 2. 텍스트 전면 흰색 (최우선) */
[data-testid="stAppViewContainer"],
[data-testid="stAppViewContainer"] *,
[data-testid="stHeader"], [data-testid="stHeader"] *,
.stMarkdown p, .stMarkdown span, .stMarkdown div,
label, p, span, td, th, li, code {
    color: #ffffff !important;
}
h1 { color: #e50914 !important; font-weight: 800 !important; }
h2, h3, h4 { color: #e5e5e5 !important; }
h2 { border-left: 4px solid #e50914; padding-left: 10px; }

/* 3. 캡션 */
div[data-testid="stCaption"], div[data-testid="stCaption"] p {
    color: #b3b3b3 !important;
}

/* 4. 메트릭 카드 */
.stMetric {
    background-color: #141414 !important;
    border: 1px solid #232323 !important;
    border-left: 3px solid #e50914 !important;
    border-radius: 10px !important; padding: 14px !important;
}
div[data-testid="stMetricValue"] { color: #e50914 !important; font-weight: 700 !important; }
div[data-testid="stMetric"] label { color: #b3b3b3 !important; }

/* 5. 탭 */
div[data-testid="stTabs"] [role="tablist"] { gap: 6px; }
div[data-testid="stTabs"] [role="tab"] {
    background: #141414 !important; color: #e5e5e5 !important;
    border-radius: 8px 8px 0 0 !important; border: 1px solid #232323 !important;
    border-bottom: none !important; padding: 8px 18px !important; font-weight: 600 !important;
}
div[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    background: #e50914 !important; color: white !important; border-color: #e50914 !important;
    box-shadow: 0 2px 8px rgba(229,9,20,0.3) !important;
}
div[data-testid="stTabs"] [role="tabpanel"] { color: #ffffff !important; }

/* 6. 데이터프레임 (표) */
div[data-testid="stDataFrame"] {
    background-color: #141414 !important;
    border: 1px solid #232323 !important; border-radius: 8px !important;
}
div[data-testid="stDataFrame"] * { color: #ffffff !important; }
div[data-testid="stDataFrame"] thead th {
    background-color: #1f1f1f !important; color: #e50914 !important;
    border-bottom: 2px solid #e50914 !important;
}
div[data-testid="stDataFrame"] tbody td {
    background-color: #141414 !important; color: #ffffff !important;
    border-bottom: 1px solid #232323 !important;
}
div[data-testid="stDataFrame"] tbody tr:hover td {
    background-color: #232323 !important;
}

/* 7. 위젯 */
div[data-baseweb="select"] > div {
    background-color: #141414 !important; color: #ffffff !important;
    border-color: #444 !important;
}
div[data-baseweb="select"] span { color: #ffffff !important; }
div[data-baseweb="popover"] * {
    color: #ffffff !important; background-color: #141414 !important;
}
div[role="radiogroup"] label, label[data-testid="stCheckbox"] span {
    color: #ffffff !important;
}
div[data-testid="stSlider"] { color: #ffffff !important; }
div[data-testid="stSlider"] [data-testid="stThumbContainer"] {
    background-color: #e50914 !important;
}
div[data-testid="stSlider"] [role="slider"] { color: #e50914 !important; }

/* 8. 경고/정보/성공 박스 */
div[data-testid="stAlert"] {
    background-color: #141414 !important;
    border: 1px solid #444 !important; border-radius: 8px !important;
}
div[data-testid="stAlert"] * { color: #ffffff !important; }
div[data-testid="stExpander"] {
    background-color: #141414 !important;
    border: 1px solid #232323 !important; border-radius: 8px !important;
}
div[data-testid="stExpander"] * { color: #ffffff !important; }

/* 9. 프로그레스 바 */
div[data-testid="stProgress"] > div > div > div {
    background-color: #e50914 !important;
}

/* 10. 버튼 */
.stButton button {
    background-color: #e50914 !important; color: white !important;
    border: none !important; border-radius: 6px !important;
}

/* 11. 스크롤바 */
::-webkit-scrollbar { width: 6px; background: #141414; }
::-webkit-scrollbar-thumb { background: #333; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #e50914; }

/* 12. 차트 배경 (Altair/Plotly) */
div[data-testid="stArrow"] { background-color: transparent !important; }
div[data-testid="stVegaChart"] path[fill] { fill-opacity: 1; }
[data-testid="stAppViewContainer"] [data-red="1"],
[data-testid="stAppViewContainer"] [data-red="1"] * {
    color: #e50914 !important;
}
[data-testid="stAppViewContainer"] :red { color: #e50914 !important; }
</style>
""", unsafe_allow_html=True)

GLOSSARY = {
    "데뷔": "그 작품이 어떤 나라의 Top 10 차트에 처음 진입한 것. 데뷔 국가 = 가장 먼저 Top 10에 들어간 나라.",
    "발자국": "작품이 데뷔 직후 어느 나라 차트에 먼저 떴는지의 기록. 이 기록만으로 미래 확산을 예측한다.",
    "미러 효과": "어떤 나라 차트가 세계 차트를 그대로 복사해 보여주는 성질. 그 나라에 오르는 것이 그 나라의 인기라기보다 전 세계 히트의 따라잡기.",
    "시장 파워(셰어)": "글로벌 시청시간 중 그 시장이 실제로 만드는 비중. 시청량을 직접 만들면 파워, 따라 보면 미러.",
    "시장 밀도": "인구 대비 넷플릭스 수요의 농도(파워/인구). 캐나다 11.9 vs 인도 0.66 - 같은 인구라도 시장 무게가 다르다.",
}
GLOSS_MD = "### 한눈에 보는 용어\n" + "\n".join(f"- **{k}**: {v}" for k, v in GLOSSARY.items())


@st.cache_data
def load_data():
    pvi = pd.read_csv(ROOT / "data/processed/country_population_vs_influence.csv")
    power = pd.read_csv(ROOT / "data/processed/country_market_power.csv")
    pop_y = pd.read_csv(ROOT / "references/country_population_by_year.csv")
    cmat = pd.read_csv(D := ROOT / "data/processed/language_crossing_matrix.csv")
    genre_c = pd.read_csv(ROOT / "data/processed/genre_preferences_by_continent.csv")
    genre_n = pd.read_csv(ROOT / "data/processed/genre_preferences_by_country.csv")
    blocks = pd.read_csv(ROOT / "data/processed/market_power_blocks_v3.csv")
    results = pd.read_csv(ROOT / "data/processed/model_35week_results.csv")
    dens_res = pd.read_csv(ROOT / "data/processed/model_v22_density_results.csv")
    dens_reg = pd.read_csv(ROOT / "data/processed/model_v22_density_reg.csv")
    power_period = pd.read_csv(ROOT / "data/processed/market_power_rolling_yearly.csv", index_col=0)
    ablation = pd.read_csv(ROOT / "data/processed/population_feature_ablation.csv")
    return pvi, power, pop_y, cmat, genre_c, genre_n, blocks, results, ablation, dens_res, dens_reg, power_period

def bundle_signature():
    return hashlib.md5((ROOT / "models" / "model_v2_lgbm.joblib").read_bytes()).hexdigest()

@st.cache_resource
def load_model(_sig):
    return joblib.load(ROOT / "models" / "model_v2_lgbm.joblib")

@st.cache_data
def load_tags():
    cat_meta = pd.read_csv(ROOT / "data/interim/netflix_titles_catalog.csv")
    cat_meta["genres_clean"] = cat_meta.imdb_genres.fillna("").astype(str).str.strip()
    tag_cnt = cat_meta.genres_clean[cat_meta.genres_clean != ""].str.split(",").explode().str.strip().value_counts()
    TAGS = [t for t in tag_cnt.index if tag_cnt[t] >= 30][:22]
    GEN_MAP = {r.show_title: set(t.strip() for t in r.genres_clean.split(",") if t.strip())
               for _, r in cat_meta.iterrows()}
    return TAGS, GEN_MAP

TAGS, GEN_MAP = load_tags()

pvi, power, pop_y, cmat, genre_c, genre_n, blocks, results, ablation, dens_res, dens_reg, power_period = load_data()
bundle = load_model(bundle_signature())
EN_MARKETS = {"United States", "United Kingdom", "Canada", "Australia", "Ireland", "New Zealand"}
ORDER = ["유럽", "아시아", "북중미", "남미", "아프리카", "오세아니아"]
CONT = dict(pd.read_csv(ROOT / "references/country_continent.csv").values)
KO = pd.read_csv(ROOT / "references/country_names_ko.csv")
KO = dict(zip(KO.country_name, KO.country_ko))
GENRE_KO = {"Action": "액션", "Adventure": "어드벤처", "Animation": "애니메이션", "Biography": "전기",
            "Comedy": "코미디", "Crime": "범죄", "Documentary": "다큐멘터리", "Drama": "드라마",
            "Family": "가족", "Fantasy": "판타지", "Game-Show": "게임쇼", "History": "역사",
            "Horror": "호러", "Music": "음악", "Musical": "뮤지컬", "Mystery": "미스터리",
            "Reality-TV": "리얼리티", "Romance": "로맨스", "Sci-Fi": "SF", "Sport": "스포츠",
            "Thriller": "스릴러", "War": "전쟁", "Western": "서부극"}
POWER_DF = power.set_index("country")
PWR = (POWER_DF.나라파워셰어 * 1000).to_dict()
POP24 = POWER_DF.인구2024.to_dict()
DENS = {y: POWER_DF[f"파워/인구비_{y}"].to_dict() for y in range(2021, 2027)}

st.title("🎬 Netflix Top 10 글로벌 확산 분석")
st.caption("데이터: 넷플릭스 글로벌/94개국 주간 Top 10 (2021-07-04 ~ 2026-11-15, 281주) · 인구: UN WPP 2024 · 장르: IMDb+JustWatch (커버 99.7%)")

tab1, tab2, tab3, tab5, tab6, tab4, tab7 = st.tabs(
    ["📊 개요", "🧭 시장 파워 & 미러", "🗣️ 언어 장벽", "🔮 확산 예측 시뮬레이터", "🔎 나라 탐색기", "🤖 모델 성능", "💡 인사이트"])

# ================= 탭 1: 개요 =================
with tab1:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("분석 기간", "5년 4개월", "2021.7 ~ 2026.11 (281주)")
    c2.metric("다루는 국가", "94개국", "러시아 2022.3 이후 제외")
    c3.metric("고유 작품", "12,486편", "장르 커버 99.7% (IMDb+JustWatch)")
    c4.metric("글로벌 히트", "3,585편", "6대륙 전부 도달 1,657편")
    st.info("핵심 통찰: 차트에 '오르는가'보다 **어느 나라에서 오르는가**가 확산을 결정합니다. "
            "나라별 영향력 지표는 시장 파워와 미러 효과가 섞여 있어 해석 시 분리가 필요합니다.")
    st.markdown(GLOSS_MD)

# ================= 탭 2: 시장 파워 & 미러 =================
with tab2:
    st.markdown("### 블록/국가별 파워")
    st.caption("미러 시장은 0에 수렴")
    st.caption("혼자 서는 시장은 분리, 나머지는 취향끼리 묶음")
    bb = blocks.sort_values("파워셰어", ascending=False)
    st.bar_chart(bb.set_index("블록")[["파워셰어"]], height=380, color="#e50914")
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("### 국가별 사분면 (파워 × 미러)")
        q_filter = st.multiselect("사분면 필터", ["파워+미러", "파워형(독립시장)", "순수미러", "저활성"],
                                  default=["파워+미러", "파워형(독립시장)"])
        show = power[power.사분면.isin(q_filter)]
        show["국가"] = show.country.map(KO)
        st.dataframe(show[["국가", "블록", "나라파워셰어", "리프트(미러)", "사분면"]]
                     .style.format({"나라파워셰어": "{:.2%}", "리프트(미러)": "{:.2f}"}), height=380)
        st.warning("**⚠️ 미러 효과 유의 — 정의: 세계 차트를 그대로 따라 보는 나라의 성질**\n\n"
                   "순수미러 41개국(룩셈부르크·우루과이·모리셔스·칠레 등)의 높은 '영향력 계수'는 "
                   "그 나라 시장이 글로벌 히트를 만든 것이 아니라 **글로벌 히트를 그대로 따라 본 것**입니다.\n\n"
                   "차트 순위를 시장 파워로 해석하기 전에 사분면 분류를 먼저 확인하세요.")
    st.markdown("### 시간에 따른 파워 이동 (연도별)")
    lt = power_period.T[["미국", "인도", "브라질", "캐나다", "동아시아", "멕시코"]].reset_index().rename(columns={"index": "기간"})
    lt = lt.melt(id_vars="기간", var_name="블록", value_name="파워셰어")
    lt["파워셰어"] = (lt["파워셰어"] * 100).round(1)
    porder = ["2021H2", "2022", "2023", "2024", "2025", "2026H1"]
    palette = {"미국": "#ffffff", "인도": "#e50914", "브라질": "#ff8787", "캐나다": "#b3b3b3", "동아시아": "#ffd6d6", "멕시코": "#7a7a7a"}
    xenc = alt.X("기간:N", sort=porder, axis=alt.Axis(labelColor="#e5e5e5", titleColor="#b3b3b3"), scale=alt.Scale(padding=50))
    line = alt.Chart(lt).mark_line(point=True).encode(
        x=xenc,
        y=alt.Y("파워셰어:Q", title="파워셰어 (%)", axis=alt.Axis(labelColor="#e5e5e5", titleColor="#b3b3b3", gridColor="#333")),
        color=alt.Color("블록:N", scale=alt.Scale(domain=list(palette), range=[palette[b] for b in palette]), legend=None),
        tooltip=[alt.Tooltip("블록:N", title="블록"), alt.Tooltip("기간:N", title="기간"), alt.Tooltip("파워셰어:Q", format=".1f", title="파워셰어 (%)")])
    last = lt[lt.기간 == "2026H1"]
    labels = alt.Chart(last).mark_text(align="left", dx=6, fontSize=11, fontWeight="bold").encode(
        x=alt.X("기간:N", sort=porder), y="파워셰어:Q", text=alt.Text("파워셰어:Q", format=".1f"),
        color=alt.Color("블록:N", scale=alt.Scale(domain=list(palette), range=[palette[b] for b in palette]), legend=None))
    st.altair_chart((line + labels).properties(background="#0b0b0b"), use_container_width=True)
    st.caption("미국 누적 1위 → 2026H1 4위(13.4%)")

    st.markdown("### 블록 파워 vs 인구 (파워/인구 비율 = 시장 성숙도)")
    bb2 = bb.sort_values("파워/인구비", ascending=False)
    bbar = alt.Chart(bb2).mark_bar(color="#e50914").encode(
        x=alt.X("파워/인구비:Q", title="파워/인구비 — 인구 대비 넷플릭스 수요의 농도"),
        y=alt.Y("블록:N", sort="-x", title=None),
        tooltip=[alt.Tooltip("블록:N", title="블록"),
                 alt.Tooltip("파워/인구비:Q", format=".2f", title="파워/인구비"),
                 alt.Tooltip("파워셰어:Q", format=".2%", title="파워셰어")],
    )
    st.altair_chart(bbar, use_container_width=True)
    st.caption("파워/인구비 — 인구 대비 수요 농도")


# ================= 탭 3: 언어 장벽 =================
with tab3:
    st.caption("3,558편 · 영어권 = 모국어 시장 6개국")
    en_n = int(cmat[cmat.출신언어 == "영어"].표본.iloc[0])
    ne_n = int(cmat[cmat.출신언어 == "비영어"].표본.iloc[0])
    st.caption(f"영어 {en_n:,}편 / 비영어 {ne_n:,}편")
    hm_wide = cmat.pivot(index="출신언어", columns="타깃시장", values="진입률")
    hm_wide = hm_wide[["영어권", "유럽(비영어)", "아시아", "남미", "아프리카", "오세아니아(비영어)"]]
    hm_long = hm_wide.reset_index().melt(id_vars="출신언어", var_name="타깃시장", value_name="진입률")
    hm_long["표본"] = hm_long.출신언어.map({"영어": 1734, "비영어": 1824})
    hbase = alt.Chart(hm_long).encode(
        x=alt.X("타깃시장:N", sort=["영어권", "유럽(비영어)", "아시아", "남미", "아프리카", "오세아니아(비영어)"],
                axis=alt.Axis(labelColor="#e5e5e5", titleColor="#b3b3b3", labelFontSize=11)),
        y=alt.Y("출신언어:N", sort=["영어", "비영어"],
                axis=alt.Axis(labelColor="#e5e5e5", titleColor="#b3b3b3", labelFontSize=11.5)),
        tooltip=[alt.Tooltip("출신언어:N", title="출신언어"),
                 alt.Tooltip("타깃시장:N", title="타깃시장"),
                 alt.Tooltip("진입률:Q", format=".1f", title="진입률 (%)"),
                 alt.Tooltip("표본:Q", format=",", title="표본")],
    )
    hrect = hbase.mark_rect().encode(
        color=alt.Color("진입률:Q", scale=alt.Scale(range=["#2a2a2a", "#7a0c12", "#e50914"]), legend=None))
    htext = hbase.mark_text(fontSize=14, fontWeight="bold", color="#ffffff").encode(
        text=alt.Text("진입률:Q", format=".1f"))
    st.altair_chart((hrect + htext).properties(background="#0b0b0b"), use_container_width=True)
    st.caption("진입률 (%)")
    m1, m2, m3 = st.columns(3)
    ne_en = cmat[(cmat.출신언어 == "비영어") & (cmat.타깃시장 == "영어권")].진입률.iloc[0]
    NE_TARGETS = ["유럽(비영어)", "아시아", "남미", "아프리카", "오세아니아(비영어)"]
    en_ne = cmat[(cmat.출신언어 == "영어") & (cmat.타깃시장.isin(NE_TARGETS))].진입률.mean()
    m1.metric("비영어 히트 → 영어권", f"{ne_en}%", "5년간 23~24% 정체")
    m2.metric("영어 히트 → 비영어권 평균", f"{en_ne:.1f}%", "비영어 5개 시장 그룹 평균")
    m3.metric("영어권 전용 데뷔의 히트율", "19.4%", "다중 대륙 데뷔는 82.0%")
    st.markdown("### 비영어 히트의 장르별 영어권 통과율")
    st.caption("스릴러·범죄는 통과율 높고 코미디·음악은 낮다")
    genre_c_bar = pd.read_csv(ROOT / "data/processed/language_barrier_by_genre.csv").set_index("장르")
    genre_c_bar = genre_c_bar.rename(index=GENRE_KO)
    st.bar_chart(genre_c_bar["영어권진입률"], height=380, color="#e50914")

with tab5:
    st.markdown("### 신작 확산 예측 시뮬레이터")
    snap = st.radio("예측 시점", ["데뷔 후 1주 (빠른 의사결정)", "데뷔 후 4주 (정밀 확인)"],
                    horizontal=True, index=0)
    snap_key = "1주차" if "1주" in snap else "4주차"
    if snap_key == "1주차":
        st.info("1주차 = 조기 판단용. 정밀도 0.85, 회귀 오차 ±5.0개국")
    else:
        st.info("4주차 = 정밀 확인용. 정밀도 0.87, 확산 오차 ±2.8개국")
    st.caption("상대 비교용")
    st.caption("상대 비교용")
    ALL_COUNTRIES = sorted(power.country.unique())
    mode = st.radio("선택 방식", ["국가 선택 (정밀)", "대륙 선택 (빠름)"], horizontal=True)

    if mode == "국가 선택 (정밀)":
        sel_countries = st.multiselect(f"진입 국가 (데뷔 후 {snap_key} 내 Top 10 진입)", ALL_COUNTRIES,
                                       default=["South Korea", "Japan", "Taiwan"],
                                       format_func=lambda c: KO.get(c, c))
    else:
        entered = st.multiselect("진입 대륙", ORDER, default=["아시아", "남미"])
        per = {"남미": ["Brazil", "Argentina", "Chile", "Colombia", "Peru", "Ecuador", "Venezuela", "Bolivia", "Paraguay", "Uruguay"],
               "아시아": ["South Korea", "Japan", "Taiwan", "Hong Kong", "India", "Indonesia", "Malaysia",
                       "Singapore", "Philippines", "Vietnam", "Thailand", "Pakistan", "Bangladesh"],
               "북중미": ["United States", "Canada", "Mexico", "Costa Rica", "Panama", "Guatemala"],
               "유럽": ["United Kingdom", "France", "Germany", "Spain", "Italy", "Netherlands", "Sweden"],
               "아프리카": ["Nigeria", "South Africa", "Kenya", "Egypt", "Morocco"],
               "오세아니아": ["Australia", "New Zealand", "New Caledonia"]}
        # 선택한 대륙의 전체 국가를 후보로 표시 — 사용자가 직접 골라서 선택
        available = [c for k in entered for c in per[k]]
        sel_countries = st.multiselect(f"진입 국가 (선택한 대륙: {', '.join(entered)})", available,
                                       default=available[:5],
                                       format_func=lambda c: KO.get(c, c))
        n_countries = st.slider("진입 국가 수 (정보 표시용)", len(sel_countries), 94, len(sel_countries), disabled=True)
    debut_country = st.selectbox("데뷔 국가 (가장 먼저 진입한 나라)", sel_countries,
                                 format_func=lambda c: KO.get(c, c))
    tv = st.radio("형식", ["TV", "Films"], horizontal=True)
    lang_origin = st.radio("출신 언어", ["영어", "비영어"], horizontal=True)
    genres = st.multiselect("장르 (IMDb+JustWatch)", TAGS, default=["Drama"],
                            format_func=lambda t: GENRE_KO.get(t, t))
    debut_year = st.selectbox("데뷔 연도", list(range(2021, 2027)), index=3)
    model = bundle["models"][f"{snap_key}_글로벌히트_lgbm"]
    model6 = bundle["models"][f"{snap_key}_6대륙도달_lgbm"]
    cal_g = bundle["models"].get(f"{snap_key}_글로벌히트_lgbm_calibrated")
    cal_s = bundle["models"].get(f"{snap_key}_6대륙도달_lgbm_calibrated")
    feats = bundle["feature_names"]

    row = {name: 0.0 for name in feats}
    sel = list(dict.fromkeys(sel_countries))
    row["진입국가수"] = len(sel)
    conts = {CONT[c] for c in sel}
    row["진입대륙수"] = len(conts)
    for k in ORDER:
        row[f"{k}국가수"] = sum(1 for c in sel if CONT[c] == k)
    debut_cont = CONT.get(debut_country)
    for k in ORDER:
        row[f"첫진입_{k}"] = int(k == debut_cont)
    row["TV여부"] = int(tv == "TV")
    row["데뷔영어권"] = int(lang_origin == "영어")
    row["진입시장파워"] = sum(PWR.get(c, 0) for c in sel)
    PY = pop_y.set_index("country_name")
    row["진입시장인구_log"] = np.log1p(sum(PY.loc[c, str(debut_year)] for c in sel))
    row["진입시장밀도합"] = sum(DENS[debut_year].get(c, 0) or 0 for c in sel)
    row["진입시장밀도평균"] = row["진입시장밀도합"] / max(len(sel), 1)
    for tag in TAGS:
        row[f"장르_{tag}"] = int(tag in genres)
    row["장르결측"] = int(len(genres) == 0)

    Xin = pd.DataFrame([row])[feats].to_numpy().astype(float)
    raw_g = model.predict_proba(Xin)[0, 1]
    p_g = cal_g.predict_proba(Xin)[0, 1] if cal_g is not None else raw_g
    raw_s = model6.predict_proba(Xin)[0, 1]
    p_s = cal_s.predict_proba(Xin)[0, 1] if cal_s is not None else raw_s
    a, b = st.columns(2)
    a.metric(f"🌍 글로벌 Top 10 도달 확률 ({snap_key} 발자국)", f"{p_g*100:.1f}%")
    b.metric(f"🌐 6대륙 전부 도달 확률 ({snap_key})", f"{p_s*100:.1f}%")
    st.progress(min(p_g, 1.0))
    st.caption(f"모델: {bundle.get('model_name', '?')} · 학습: {bundle.get('trained_at', '?')} · 피처 {len(feats)}개 · 보정 전 확률: 글로벌 {raw_g*100:.1f}% / 6대륙 {raw_s*100:.1f}%")
    ko_names = ", ".join(KO.get(c, c) for c in sel)
    st.caption(f"선택 국가 {len(sel)}개 · 진입 대륙 {len(conts)}개 · 데뷔 {KO.get(debut_country, debut_country)} ({debut_year}) · "
               f"시장파워 합 {row['진입시장파워']:.1f} · 밀도합 {row['진입시장밀도합']:.1f}")
    st.caption("선택 국가: " + ko_names)

    import shap
    with st.expander("이 예측의 기여 분해 (SHAP)"):
        explainer = shap.TreeExplainer(model)
        sv = explainer.shap_values(Xin, check_additivity=False)
        sv = sv[1] if isinstance(sv, list) else sv
        if sv.ndim == 3:
            sv = sv[:, :, 1]
        contrib = pd.Series(sv[0], index=feats)
        top = pd.concat([contrib.nlargest(5), contrib.nsmallest(5)])
        for k, v in top.items():
            st.markdown(f"{'🟢' if v > 0 else '🔴'} **{k}**: {v:+.2f}")

with tab6:
    st.markdown("### 나라 탐색기")
    _countries_sorted = sorted(power.country.unique())
    sel = st.selectbox("나라 선택", _countries_sorted,
                       index=_countries_sorted.index("South Korea") if "South Korea" in _countries_sorted else 0,
                       format_func=lambda c: KO.get(c, c))
    r = power[power.country == sel].iloc[0]
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("시장 파워 셰어", f"{r.나라파워셰어*100:.2f}%")
    k2.metric("미러 리프트", f"{r['리프트(미러)']:.2f}", "높으면 글로벌 따라감")
    k3.metric("사분면", r.사분면)
    k4.metric("블록", r.블록)
    blk = r.블록
    if blk in power_period.index:
        mv = power_period.loc[blk].to_frame(name="파워셰어 (%)")
        st.line_chart(mv, color="#e50914", height=260)
        st.caption(f"{blk} 파워 이동")
    else:
        st.caption("이 국가는 블록 단위 파워 추이 데이터가 없습니다.")
    st.metric("파워/인구비 (2026년 기준)", f"{r['파워/인구비_2026']:.2f}",
              f"2021년 {r['파워/인구비_2021']:.2f} 대비 변화 {r['파워/인구비_2026'] - r['파워/인구비_2021']:+.2f}")

with tab4:
    st.markdown("### 모델 성능 — LightGBM v2.2 (최종 모델)")
    st.caption("학습 9,936편 → 테스트 1,443편 (35주 분할)")

    st.markdown("#### 📊 지표 정의")
    st.markdown("""
| 지표 | 정의 | 좋을수록 |
|---|---|---|
| **AUC** | 히트작을 비히트작보다 '더 높은 확률'로 예측하는 능력. 0.5=동전, 1.0=완벽 | ↑ |
| **정확도** | 모델의 전체 판정 중 맞힌 비율 (히트 + 비히트 모두 포함) | ↑ |
| **정밀도** | 모델이 '히트'라고 판정한 것 중 실제 히트인 비율. 높으면 잘못된 투자가 적음 | ↑ |
| **재현율** | 실제 히트작 중 모델이 잡아낸 비율. 높으면 놓치는 히트가 적음 | ↑ |
| **F1** | 정밀도와 재현율의 조화 평균 | ↑ |
| **MAE** | 예측 확산 국가 수와 실제 확산 국가 수의 평균 오차 (개국 단위) | ↓ |
""")

    st.markdown("#### 📊 1주차 성능 (조기 판단용)")
    one = dens_res[(dens_res.스냅샷 == "1주차") & (dens_res.target != "국가수")].drop(columns=["MSE(Brier)"])
    st.dataframe(one, hide_index=True, height=140)
    st.caption("MAE 5.0개국")

    st.markdown("#### 📊 4주차 성능 (정밀 확인)")
    four = dens_res[(dens_res.스냅샷 == "4주차") & (dens_res.target != "국가수")].drop(columns=["MSE(Brier)"])
    st.dataframe(four, hide_index=True, height=140)
    st.caption("MAE 2.78개국")

    st.image(str(FIG / "15_shap_35week.png"), caption="v2.2 SHAP 요약 — 진입시장밀도합이 4위에 등장", width=520)

    st.markdown("### 인구가 원인인가? — 소거 실험")
    st.caption('인구 피처 소거 실험')
    st.dataframe(ablation, hide_index=True)
    st.markdown("""
**이 실험이 말하는 것**: 인구 피처를 넣어도 AUC +0.9pp(미미), 회귀는 불변.
→ '미국·브라질 차트 → 글로벌 확산'은 **인구 때문이 아니라 넷플릭스 시청량이 그 시장에 집중**되어 있기 때문.
""")


st.sidebar.markdown("## 📁 데이터 출처")
st.sidebar.markdown("""
- 넷플릭스 Top 10: top10.netflix.com (2021.7~2026.11)
- 인구: UN WPP 2024 (OWID 재배포)
- 장르: IMDb 비상업 데이터셋
- 모델: 로지스틱 회귀 + LightGBM (시간 분할 검증)
""")


# ================= 탭 7: 인사이트 =================
with tab7:
    st.markdown("### 핵심 인사이트")
    st.caption("보고서 인사이트 기반")
    INSIGHTS = [
        ("미국 단독 진입은 최선이 아니다",
         "영어권 전용 데뷔의 글로벌 히트율은 19.4%, 다중 대륙 동시 데뷔는 82.0% — 배포 범위를 넓힐수록 확산 확률이 올라가는 구조다.",
         "신작 배포 시 ", "동시 공개를 기본 설계로", " — 더빙·자막 비용은 제작 예산의 일부로 미리 확보한다."),
        ("인구가 아니라 파워·밀도가 핵심",
         "인도(14.5억)보다 캐나다(4천만)의 파워 밀도가 훨씬 높다. 인구 피처 추가의 예측 기여는 AUC +0.009에 그쳤다.",
         "마케팅 예산을 ", "인구 순위가 아니라 밀도 순위로 배분", " — 캐나다(11.9)·호주(5.8) 같은 소인구 고효율 시장을 우선한다."),
        ("미러 효과 유의",
         "파나마·우루과이·룩셈부르크의 높은 동시 진입률은 따라잡기다. 진짜 파워 시장(미국·인도·브라질·캐나다 등)과 순수 미러 41개국을 구분해야 한다.",
         "나라별 성과 리포트에 ", "파워/미러 태그를 부착", " — 순수 미러 41개국은 마케팅 투자 불필요, 투자는 파워 시장으로 한정해 낭비를 막는다."),
        ("언어 장벽은 장르로 일부 극복된다 — 비영어 히트의 영어권 통과율은 평균 23.8% — 미스터리·스릴러·범죄(32~34%)는 벽이 낮다",
         "",
         "비영어 원작 투자 심사에 ", "장르별 영어권 통과율을 반영", " — 미스터리·스릴러·범죄(32~34%)는 글로벌 베팅 가치가 높다."),
        ("시장 파워는 이동한다",
         "멕시코 영향력 감소(16.6%→1.4%), 인도·브라질 부상, 동아시아의 2022년 이후 등장 — 시장 지도는 고정되지 않는다.",
         "지속적 갱신 필요 — ", "반년 단위 파워 재추정으로 시장 우선순위를 갱신", ". 멕시코(16.6%→1.4%)는 단일 시장 과의존의 위험 사례이고, 인도·브라질·동아시아의 부상은 현지 제작 투자 확대 신호로 읽는다."),
        ("2단계 확산 예측 — 1주차 + 4주차",
         "1주차 정밀도 0.85로 조기 판단, 4주차 0.87로 정밀 확인 — 조기 의사결정과 정밀 확인을 분리해 사용할 수 있다.",
         "", "1주차 조기 판단 + 4주차 정밀 확인의 2단계 운영", " — 진입 첫 주 진입 국가 수·밀도를 시뮬레이터에 넣어 점수화하고, 마케팅 증폭·현지화 확장을 1주 안에 결정한다. 4주차 재평가로 점진 확산형을 보완하며, 확률은 절대값이 아니라 동시 진입 후보 간 상대 비교로 사용한다."),
    ]
    for i, (title, body, pre, red, post) in enumerate(INSIGHTS, 1):
        with st.container(border=True):
            st.markdown(f"**{i}. {title}**")
            if body:
                st.markdown(body)
            st.markdown(
                f'<b>→ 실무 적용</b> {pre}<span data-red="1"><b><u style="text-underline-offset:3px;">{red}</u></b></span>{post}',
                unsafe_allow_html=True)
    st.info("**한계** — 순위 데이터는 시청 시간의 세분량을 담지 않아 파워 추정은 순위 패턴 기반 구조적 추정이며, "
            "상관관계와 인과관계는 구분된다 — 진입/확산이 글로벌 히트를 유발한다는 인과 증명이 아니라 경향성이다.")