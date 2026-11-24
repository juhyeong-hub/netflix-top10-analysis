# -*- coding: utf-8 -*-
# ─────────────────────────────────────────────────────────────────────────────
# [용도] 04. JustWatch 장르를 카탈로그에 반영 (IMDb 장르 코드 매핑)
#        + 전체 장르 커버리지 재계산 + 언어장벽 장르별 통과율 재계산
# [환경] Python 3.15.2 (Windows) / pandas 3.1.1, numpy 2.5.4 — requirements.txt 참고
#        실행: python scripts/04_catalog_genre_update.py
# [경로] ROOT = 스크립트 위치 기준 프로젝트 루트 (scripts/ 상위)
# ─────────────────────────────────────────────────────────────────────────────
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# JustWatch shortName → IMDb 장르 태그 매핑
JW2IMDB = {
    "drm": "Drama", "cmy": "Comedy", "act": "Action", "trl": "Thriller",
    "crm": "Crime", "rma": "Romance", "fml": "Family", "ani": "Animation",
    "fnt": "Fantasy", "doc": "Documentary", "rly": "Reality-TV", "scf": "Sci-Fi",
    "hrr": "Horror", "hst": "History", "wes": "Western", "war": "War",
    "spo": "Sport", "msc": "Music", "mys": "Mystery", "bio": "Biography",
    "adn": "Adventure", "kid": "Kids",
}
NOT_GENRE = {"eur"}  # 유럽에서 제작 — 장르 아님

jw = pd.read_csv(ROOT / "data/processed/genre_missing_justwatch.csv")
jw = jw[jw.has_result]

def jw_to_imdb(s):
    out = []
    for c in str(s).split("|"):
        c = c.strip()
        if c in NOT_GENRE:
            continue
        if c in JW2IMDB:
            out.append(JW2IMDB[c])
    return ",".join(sorted(set(out)))

jw["genres_filled"] = jw.genres_short.map(jw_to_imdb)
n_unmapped = (jw.genres_filled == "").sum()
print(f"매핑 성공: {(jw.genres_filled!='').sum()}편 | 매핑 실패(미등록 코드만): {n_unmapped}편")

# ---- catalog 갱신 ----
cat = pd.read_csv(ROOT / "data/interim/netflix_titles_catalog.csv")
cat["genre_source"] = cat.imdb_genres.fillna("").astype(str).str.strip().ne("").map({True: "imdb", False: ""})
fill_map = dict(zip(jw.show_title, jw.genres_filled))
mask = cat.imdb_genres.fillna("").astype(str).str.strip().eq("") & cat.show_title.isin(fill_map)
cat.loc[mask, "imdb_genres"] = cat.loc[mask, "show_title"].map(fill_map)
cat.loc[mask & cat.imdb_genres.ne(""), "genre_source"] = "justwatch"
cat.to_csv(ROOT / "data/interim/netflix_titles_catalog.csv", index=False, encoding="utf-8-sig")
print(f"catalog 갱신: {mask.sum()}편 채움 | genre_source 열 추가")

# ---- 커버리지 재계산 ----
c_old = pd.read_csv(ROOT / "data/raw/all-weeks-countries.csv", sep=",", encoding="cp1252")
c_new = pd.read_csv(ROOT / "data/raw/all-weeks-countries_2026-11-11.tsv", sep="\t")
c_all = pd.concat([c_old, c_new]).drop_duplicates()
titles = sorted(c_all.show_title.unique())
gen_all = cat.set_index("show_title").imdb_genres.fillna("").astype(str).str.strip()
cov = sum(1 for t in titles if gen_all.get(t, "")) / len(titles) * 100
print(f"\n장르 커버리지: {cov:.1f}% (기존 93.2%) — 미확보 {sum(1 for t in titles if not gen_all.get(t,''))}편")

# ---- 언어장벽 장르표 재계산 (결측분 반영) ----
g_old = pd.read_csv(ROOT / "data/raw/all-weeks-global.csv", sep=",")
g_new = pd.read_csv(ROOT / "data/raw/all-weeks-global_2026-11-11.tsv", sep="\t")
g_all = pd.concat([g_old, g_new]).drop_duplicates()
EN_MARKETS = {"United States", "United Kingdom", "Canada", "Australia", "Ireland", "New Zealand"}
hits = set(g_all.show_title.unique())
g_all["lang_cat"] = g_all.category.str.contains("Non-English").map({True: "비영어", False: "영어"})
lang_sets = g_all.groupby("show_title").lang_cat.apply(set)
only_ne = {t for t, s in lang_sets.items() if s == {"비영어"}}
no_country = hits - set(c_all.show_title.unique())
pop_ne = only_ne - no_country
ever = c_all.groupby("show_title").country_name.apply(set)
entered_ne = ever.loc[ever.index.isin(pop_ne)].apply(lambda cs: bool(cs & EN_MARKETS))

ne_titles = pd.Series(sorted(pop_ne), name="show_title")
df_ne = pd.DataFrame({"show_title": ne_titles.values})
df_ne["genres"] = df_ne.show_title.map(gen_all)
df_ne["entered_en"] = df_ne.show_title.map(entered_ne)
df_ne_cov = df_ne.genres.str.strip().ne("").mean() * 100
print(f"비영어 표본 {len(pop_ne)}편의 장르 커버: {df_ne_cov:.1f}%")
df_ne = df_ne[df_ne.genres.str.strip() != ""]
df_ne["장르"] = df_ne.genres.apply(lambda s: [t.strip() for t in s.split(",") if t.strip()])
ex = df_ne.explode("장르")
gstat = ex.groupby("장르").agg(표본=("entered_en", "size"), 영어권진입률=("entered_en", "mean"))
gstat["영어권진입률"] = (gstat.영어권진입률 * 100).round(1)
gstat = gstat[gstat.표본 >= 50].sort_values("영어권진입률", ascending=False).reset_index()
gstat[["장르", "표본", "영어권진입률"]].to_csv(ROOT / "data/processed/language_barrier_by_genre.csv", index=False, encoding="utf-8-sig")
print("\n== 재계산된 장르별 영어권 통과율 ==")
print(gstat.to_string(index=False))
