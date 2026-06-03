# 📈 StockRadar

국내(KOSPI/KOSDAQ) 및 미국(S&P 500/NASDAQ/DOW) 주식 시장을 한눈에 분석하는 Flask 기반 웹 애플리케이션입니다.

> **면책사항**: 본 서비스에서 제공하는 모든 정보는 투자 참고용이며, 투자 결정에 대한 책임은 전적으로 사용자 본인에게 있습니다.

---

## 🚀 주요 기능

### 🏠 홈 대시보드
- 실시간 한국(KST) / 미국(ET) 시장 시계
- 시장 개장·휴장 상태 표시
- 국내·미국 시장 진입 카드

### 🇰🇷 국내시장 (`/korean/`)
| 기능 | 설명 |
|------|------|
| **지수 카드** | KOSPI · KOSDAQ · KOSPI200 현재 지수 + 7일 스파크라인 차트 |
| **시장 폭** | 상승 / 하락 / 보합 종목 수 (도넛 차트 + 카운터) |
| **KOSPI 섹터 히트맵** | 전기전자·금융·의약품·화학 등 10개 섹터 등락률 색상 표시 |
| **상위 상승 종목** | 등락률 Top 10 (종목명 클릭 시 상세 페이지 이동) |
| **상위 하락 종목** | 하락률 Top 10 |
| **거래량 상위** | 당일 거래량 Top 10 |
| **오늘의 추천 종목** | 골든크로스 · 거래량급등 · 상승모멘텀 신호 기반 추천 |
| **KOSPI/KOSDAQ 전환** | 탭 버튼으로 시장 전환 |

### 🇺🇸 미국시장 (`/us/`)
| 기능 | 설명 |
|------|------|
| **지수 카드** | S&P 500 · NASDAQ · Dow Jones · VIX 지수 + 7일 스파크라인 |
| **Fear & Greed Index** | VIX 기반 공포탐욕 지수 (Extreme Fear → Extreme Greed) |
| **시장 폭** | S&P 500 구성종목 상승/하락/보합 현황 (도넛 차트) |
| **섹터 ETF 히트맵** | 11개 섹터 ETF (XLK·XLF·XLV 등) 등락률 색상 표시 |
| **Top Gainers / Losers** | 상위 상승·하락 종목 Top 10 |
| **Volume Leaders** | 거래량 상위 종목 |
| **Recommended Stocks** | Golden Cross · Volume Surge · Momentum 신호 기반 추천 |

### 📊 종목 상세 페이지 (`/stock/<market>/<ticker>`)
| 기능 | 설명 |
|------|------|
| **가격 헤더** | 현재가 · 등락 · 등락률 실시간 표시 |
| **기간 선택기** | 1W · 1M · 3M · 6M · 1Y (AJAX로 차트 재렌더링) |
| **가격 차트** | 종가 + MA5 · MA20 · MA60 + 볼린저 밴드 오버레이 |
| **거래량 차트** | 상승/하락 색상 구분 막대 차트 |
| **RSI 차트** | RSI(14) · 과매수(70) · 과매도(30) 기준선 |
| **MACD 차트** | MACD 라인 · 시그널 라인 · 히스토그램 |
| **기술적 신호 요약** | MA 크로스 · RSI · MACD · 볼린저밴드 Bullish/Bearish/Neutral |
| **주요 지표** | 시가총액 · PER · PBR · EPS · 배당수익률 · Beta · 52주 고/저가 |

### ⚡ 글로벌 기능
| 기능 | 설명 |
|------|------|
| **자동 새로고침** | 60초마다 AJAX로 데이터 갱신 (카운트다운 표시) |
| **다크 모드** | 라이트/다크 테마 토글 (localStorage 유지) |
| **종목 검색** | 상단 네비게이션 바 검색창 (국내·미국 선택 후 검색) |
| **5분 캐시** | 서버 사이드 캐싱으로 빠른 응답 |
| **반응형 디자인** | 모바일 · 태블릿 · 데스크탑 완전 지원 |

---

## 🛠 기술 스택

| 분류 | 기술 |
|------|------|
| **Backend** | Python 3.10+ · Flask 3 · Flask-Caching |
| **국내 데이터** | [pykrx](https://github.com/sharebook-kr/pykrx) (KRX 공식 데이터) |
| **미국 데이터** | [yfinance](https://github.com/ranaroussi/yfinance) (Yahoo Finance) |
| **기술 지표** | pandas (MA · RSI · MACD · 볼린저밴드 자체 계산) |
| **Frontend** | Bootstrap 5.3 · Chart.js 4.4 · Font Awesome 6 |
| **차트** | Chart.js (Line · Bar · Doughnut) |

---

## 📁 프로젝트 구조

```
stock-analysis/
├── app/
│   ├── __init__.py              # Flask 앱 팩토리 + 캐시 초기화
│   ├── routes/
│   │   ├── main.py              # 홈 라우트 (/)
│   │   ├── korean.py            # 국내시장 라우트 (/korean/*)
│   │   ├── us.py                # 미국시장 라우트 (/us/*)
│   │   ├── stock.py             # 종목 상세 + 차트 API (/stock/*)
│   │   └── api.py               # 검색 API (/api/search, /search)
│   ├── services/
│   │   ├── korean_service.py    # 국내 시장 데이터 (pykrx)
│   │   ├── us_service.py        # 미국 시장 데이터 (yfinance)
│   │   └── detail_service.py   # 종목 상세 + 기술 지표 계산
│   ├── templates/
│   │   ├── base.html            # 공통 레이아웃 (nav · footer)
│   │   ├── index.html           # 홈 대시보드
│   │   ├── korean.html          # 국내시장 페이지
│   │   ├── us.html              # 미국시장 페이지
│   │   ├── stock_detail.html    # 종목 상세 페이지
│   │   └── _market_page.html   # 공통 매크로 (change_badge)
│   └── static/
│       ├── css/style.css        # 다크모드 포함 전체 스타일
│       └── js/app.js            # 자동새로고침 · 다크모드 · 차트
├── config.py                    # Flask 설정
├── requirements.txt
└── run.py                       # 앱 진입점
```

---

## ⚙️ 설치 및 실행

### 1. 저장소 클론
```bash
git clone https://github.com/NamJinWoo/stock-analysis.git
cd stock-analysis
```

### 2. 가상환경 설정
```bash
python -m venv venv
source venv/bin/activate      # macOS/Linux
# venv\Scripts\activate       # Windows
```

### 3. 패키지 설치
```bash
pip install -r requirements.txt
```

### 4. 환경 변수 설정 (선택)
```bash
cp .env.example .env
# .env 파일에서 SECRET_KEY 값 변경
```

### 5. 실행
```bash
python run.py
```

브라우저에서 `http://localhost:5000` 접속

---

## 🌐 API 엔드포인트

### 시장 데이터 (자동새로고침용)
| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/korean/api/data?market=KOSPI` | 국내 지수·상승하락·거래량 JSON |
| GET | `/us/api/data` | 미국 지수·공포탐욕·상승하락 JSON |
| GET | `/korean/api/movers?market=KOSPI` | 국내 상승하락 종목 |
| GET | `/us/api/movers` | 미국 상승하락 종목 |

### 차트 데이터
| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/stock/api/chart/korean/<ticker>?period=3mo` | 국내 주식 OHLCV + 지표 |
| GET | `/stock/api/chart/us/<ticker>?period=3mo` | 미국 주식 OHLCV + 지표 |

`period` 옵션: `1wk` · `1mo` · `3mo` · `6mo` · `1y`

### 검색
| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/api/search?q=삼성&market=korean` | 종목 검색 JSON |
| GET | `/search?q=AAPL&market=us` | 검색 후 상세 페이지로 리다이렉트 |

---

## 📐 기술 지표 계산 방식

| 지표 | 계산식 |
|------|--------|
| **이동평균 (MA)** | `close.rolling(n).mean()` (n = 5, 20, 60) |
| **RSI** | Wilder's Smoothed Moving Average, period=14 |
| **MACD** | EMA(12) − EMA(26), Signal=EMA(9) |
| **볼린저밴드** | MA(20) ± 2σ |

### 추천 신호 점수 체계
| 신호 | 점수 |
|------|------|
| 골든크로스 (MA5 > MA20 전환) | +3 |
| 거래량 급등 (평균 대비 1.5배↑) | +2 |
| 상승 모멘텀 (당일 양봉) | +1 |

**2점 이상**인 종목만 추천 목록에 포함

### Fear & Greed (VIX 기반)
| VIX 범위 | 레이블 |
|----------|--------|
| < 15 | Extreme Greed |
| 15 ~ 20 | Greed |
| 20 ~ 25 | Neutral |
| 25 ~ 30 | Fear |
| ≥ 30 | Extreme Fear |

---

## 🔄 데이터 갱신 주기

| 데이터 | 캐시 TTL |
|--------|----------|
| 시장 지수 / 상승하락 | 60초 |
| 추천 종목 | 5분 |
| 종목 상세 차트 | 2분 |
| 섹터 / 공포탐욕 | 5분 |

---

## 📝 개발 로드맵

- [ ] 관심종목 (Watchlist) — localStorage 기반
- [ ] 52주 신고가 / 신저가 별도 섹션
- [ ] 경제 캘린더 (FOMC·CPI·고용지표)
- [ ] 캔들스틱 차트 (chartjs-chart-financial)
- [ ] 종목 뉴스 피드 연동
- [ ] 알림 기능 (목표가·손절가 도달 시 브라우저 알림)

---

## 📄 라이선스

MIT License — 자유롭게 사용·수정·배포 가능합니다.
