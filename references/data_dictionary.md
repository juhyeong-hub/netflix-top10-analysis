# 컬럼 사전 (Data Dictionary)

출처: Netflix Top 10 Weekly (공개 데이터셋) · 기간: 2021-07-04 ~ 2022-01-16 (29주)

## 공통 주의사항

- `all-weeks-countries.csv`는 **cp1252** 인코딩 (`encoding="cp1252"` 필수). `all-weeks-global.csv`는 UTF-8.
- `week`은 주 단위 집계 시점(일요일), `parse_dates=["week"]`으로 datetime 변환 권장.
- `season_title`의 `N/A`(→ NaN)는 영화에 시즌이 없어 생긴 **구조적 결측**. TV 3편(`Dave Chappelle: The Closer`, `Carrossel`, `Chiquititas`)은 시즌 구분이 없는 단일 작품.

## all-weeks-global.csv (1,160행 = 29주 × 4카테고리 × 10위)

| 컬럼 | 타입 | 설명 | 값 범위 / 예시 |
|---|---|---|---|
| `week` | date | 주간 집계일 | 2021-07-04 ~ 2022-01-16 |
| `category` | str | 언어×장르 | Films (English) / Films (Non-English) / TV (English) / TV (Non-English) |
| `weekly_rank` | int | 주간 순위(카테고리 내) | 1~10 (1이 가장 높음) |
| `show_title` | str | 작품명 | 고유 401개 |
| `season_title` | str | 시즌명 ("제목: Season N") | 영화 = N/A |
| `weekly_hours_viewed` | int | 주간 시청시간(시간) | 930,000 ~ 571,760,000 (최고: Squid Game) |
| `cumulative_weeks_in_top_10` | int | Top 10 누적 주차 | 1~18 |

## all-weeks-countries.csv (54,520행 = 94개국 × 29주 × 2카테고리 × 10위)

| 컬럼 | 타입 | 설명 | 값 범위 / 예시 |
|---|---|---|---|
| `country_name` | str | 국가명 | 94개국 |
| `country_iso2` | str | ISO 3166-1 alpha-2 | AR, KR, US … |
| `week` | date | 주간 집계일 | 글로벌과 동일 |
| `category` | str | 장르 | Films / TV (언어 구분 없음) |
| `weekly_rank` | int | 국가별 주간 순위 | 1~10 |
| `show_title` | str | 작품명 | 고유 2,006개 |
| `season_title` | str | 시즌명 | 영화 = N/A |
| `cumulative_weeks_in_top_10` | int | Top 10 누적 주차 | 1~29 |

> `weekly_hours_viewed`는 국가별 파일에 **없음**(글로벌에만 존재).

## 두 파일 조인

- 공통 키: `week` + `show_title` (+ 필요시 `category`)
- 예: 특정 작품의 글로벌 순위 vs 각국 순위 비교
