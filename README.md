# Netflix Top 10 Weekly Dataset 분석

Netflix 글로벌 및 국가별 주간 Top 10 데이터(2021-07-04 ~ 2022-01-16, 29주)의 탐색적 데이터 분석(EDA) 프로젝트입니다.

## 데이터 개요

| 파일 | 설명 | 크기 |
|---|---|---|
| `data/raw/all-weeks-global.csv` | 글로벌 주간 Top 10 (언어×장르 4카테고리, 시청시간 포함) | 1,160행 |
| `data/raw/all-weeks-countries.csv` | 94개국 주간 Top 10 (Films/TV, 시청시간 없음) | 54,520행 |

> ⚠️ `all-weeks-countries.csv`는 **cp1252 인코딩** — `pd.read_csv(..., encoding="cp1252")`로 읽어야 합니다.
> ⚠️ `data/raw`의 원본은 절대 수정하지 않습니다.

## 디렉터리 구조

```
├── data/
│   ├── raw/          # 원본 데이터. 절대 수정하지 않습니다
│   ├── interim/      # 전처리 중간 산출물
│   └── processed/    # 분석과 모델링에 바로 쓰는 데이터
├── notebooks/        # 주피터 노트북. 1.0-eda, 2.0-modeling 처럼 번호를 붙입니다
├── models/           # 학습한 모델 파일
├── reports/
│   └── figures/      # 리포트에 넣을 그래프 이미지
├── references/       # 데이터 설명서, 컬럼 사전
├── requirements.txt  # 재현에 필요한 패키지 목록
└── README.md         # 프로젝트 설명
```

## 실행 방법

```bash
pip install -r requirements.txt
jupyter notebook notebooks/1.0-eda.ipynb              # 1.0 EDA (기초 검진 + 탐색)
jupyter notebook notebooks/2.0-model-validation.ipynb # 2.0 시간 기반 모델 검증
jupyter notebook notebooks/3.0-modeling.ipynb         # 3.0 모델링 (취향 지도 B / 시장 편향 C / 확산 예측 A)
```

## EDA 요약 (상세: notebooks/1.0-eda.ipynb, 그림: reports/figures/)

1. **결측치** — `season_title`만 존재(약 50%): 영화는 시즌이 없어 원본의 `N/A`가 NaN으로 읽힌 **구조적 결측**. 실제 데이터 유실 아님.
2. **이상치** — `weekly_hours_viewed` 93만~5.7억 시간, IQR 상한(약 4,000만) 초과 106행(9.1%) = Squid Game 등 1위 히트작. 오류가 아닌 실제 효과라 삭제 금지, 로그 변환 고려.
3. **분포/불균형** — `weekly_rank`(1~10)와 `category`는 설계상 완전 균등. 작품 등장 빈도는 불균형(401편 중 37.2%가 1주만 등장, 10주+ 롱런 4.5%).
4. **상관관계** — 순위 숫자 ↔ 시청시간 r=-0.418(순위가 좋을수록 시청시간 많음), 시청시간 ↔ 누적주차 r≈0. 순위는 카테고리 내 기준이라 전체 상관이 완화됨.

## 모델링 요약 (상세: notebooks/3.0-modeling.ipynb · 검증: 2.0-model-validation.ipynb · 모델 파일: models/)

| 모델 | 질문 | 핵심 성능 (out-of-sample) |
|---|---|---|
| B 취향 지도 | 취향이 비슷한 나라끼리 묶이나? 어디로 확산 가능한가? | 3개 취향 블록(서양+중동+아프리카 / 동·남아시아 / 라틴), 대륙 간 확산 후보 51건 |
| C 시장 편향 | 어떤 시장이 글로벌 순위를 좌우하나? | AUC 0.929 — 미국·브라질 계수 최상위, 라틴 리프트 7배대 vs 일본 1.7배 |
| A 확산 예측 | 초기 발자국만으로 미래를 예측할 수 있나? | 글로벌 히트 AUC 0.871(1주차)~0.905(4주차), 6대륙 도달 0.935~0.965 |
| A' 회귀 | 몇 개국까지 퍼질까? | MAE 2.5개국, RMSE 6.1, R² 0.898 (4주차 발자국) |

**시간 기반 검증**: 무작위 분할이 아닌 "과거(11월 이전 데뷔) 학습 → 신작 테스트" 분할에서도 성능 유지 — 분류 AUC 0.932, 회귀 R² 0.978. (notebooks/2.0)

**한계**: ① 국가별 시청시간 없음(Top 10 진입 기준 분석) ② 표본 29주·단일 시즌(2021-22) ③ 예측 확률 캘리브레이션 미적용 ④ "글로벌 히트" 정의 자체에 대형 시장 편향(C가 입증) ⑤ Top 10 밖 미관측 및 후반 진입 167편 관측 잘림 ⑥ 초기 발자국 기반이라 늦게 확산되는 작품(Money Heist형) 예측 불가.
