"""
news_service.py
Reuters 기사를 Google News RSS를 통해 종목별로 가져옵니다.
"""
import feedparser
from datetime import datetime
import re

# Google News RSS — reuters.com 한정 검색
_GNEWS = "https://news.google.com/rss/search?q={query}+site:reuters.com&hl=en-US&gl=US&ceid=US:en"

# ────────────────────────────────────────────────
# 종목별 Reuters 검색 쿼리
# ────────────────────────────────────────────────
STOCK_QUERIES = {
    # 국내
    "005930": "Samsung+Electronics",
    "000660": "SK+Hynix",
    # M7
    "AAPL":  "Apple+Inc",
    "MSFT":  "Microsoft",
    "AMZN":  "Amazon",
    "GOOGL": "Alphabet+Google",
    "GOOG":  "Alphabet+Google",
    "META":  "Meta+Platforms",
    "NVDA":  "Nvidia",
    "TSLA":  "Tesla",
    # 반도체
    "AMD":   "AMD+Advanced+Micro+Devices",
    "INTC":  "Intel+semiconductor",
    "QCOM":  "Qualcomm",
    "AVGO":  "Broadcom",
    "MU":    "Micron+Technology",
    "TSM":   "TSMC+Taiwan+Semiconductor",
    "ASML":  "ASML",
    "AMAT":  "Applied+Materials",
    "TXN":   "Texas+Instruments",
    "KLAC":  "KLA+Corporation",
    "LRCX":  "Lam+Research",
    "ARM":   "ARM+Holdings",
    "MRVL":  "Marvell+Technology",
    # AI
    "PLTR":  "Palantir",
    "AI":    "C3.ai",
    "SNOW":  "Snowflake",
    "PATH":  "UiPath",
    "SOUN":  "SoundHound+AI",
    "BBAI":  "BigBear.ai",
    "UPST":  "Upstart",
    # 양자컴퓨팅
    "IONQ":  "IonQ+quantum",
    "RGTI":  "Rigetti+Computing",
    "QBTS":  "D-Wave+Quantum",
    "QUBT":  "Quantum+Computing+Inc",
    "IBM":   "IBM+quantum",
    "HON":   "Honeywell+quantum",
}

# ────────────────────────────────────────────────
# 국내시장 뉴스 대상
# ────────────────────────────────────────────────
KOREAN_NEWS_TARGETS = {
    "005930": ("삼성전자",  "Samsung+Electronics+chip+memory"),
    "000660": ("SK하이닉스", "SK+Hynix+HBM+memory"),
}

# ────────────────────────────────────────────────
# 미국시장 카테고리별 쿼리
# ────────────────────────────────────────────────
US_NEWS_CATEGORIES = {
    "M7 빅테크": [
        "Nvidia+AI",
        "Apple+stock",
        "Microsoft+AI+Azure",
        "Amazon+AWS+AI",
        "Meta+AI+stock",
        "Tesla+stock",
    ],
    "반도체": [
        "semiconductor+chip+shortage",
        "TSMC+chip",
        "AMD+Intel+chip",
        "Qualcomm+ARM+chip",
        "HBM+memory+chip",
    ],
    "AI·데이터": [
        "artificial+intelligence+investment",
        "Palantir+AI",
        "OpenAI+ChatGPT",
        "AI+chip+data+center",
    ],
    "양자컴퓨팅": [
        "quantum+computing+stock",
        "IonQ+Rigetti+quantum",
        "Google+Microsoft+quantum",
    ],
}


# ────────────────────────────────────────────────
# 내부 헬퍼
# ────────────────────────────────────────────────

def _strip_source(title: str) -> str:
    """Google News는 제목 끝에 ' - Reuters' 를 붙임 → 제거."""
    return re.sub(r"\s*-\s*Reuters\s*$", "", title).strip()


def _parse_feed(url: str, max_items: int = 8) -> list:
    try:
        feed = feedparser.parse(url, request_headers={"User-Agent": "Mozilla/5.0"})
        articles = []
        for entry in feed.entries[:max_items]:
            pub = entry.get("published_parsed")
            try:
                pub_str = datetime(*pub[:6]).strftime("%Y-%m-%d %H:%M") if pub else ""
            except Exception:
                pub_str = ""

            raw_title = entry.get("title", "")
            title = _strip_source(raw_title)
            link  = entry.get("link", "")
            if not title or not link:
                continue

            articles.append({
                "title":     title,
                "link":      link,
                "summary":   (entry.get("summary") or "")[:250],
                "source":    "Reuters",
                "published": pub_str,
            })
        return articles
    except Exception:
        return []


def _dedup_sort(articles: list, max_n: int) -> list:
    seen, unique = set(), []
    for a in articles:
        if a["title"] and a["title"] not in seen:
            seen.add(a["title"])
            unique.append(a)
    unique.sort(key=lambda x: x["published"], reverse=True)
    return unique[:max_n]


# ────────────────────────────────────────────────
# 공개 API
# ────────────────────────────────────────────────

def get_stock_news(ticker: str, max_items: int = 10) -> list:
    """종목 상세 페이지용 Reuters 기사 목록."""
    query = STOCK_QUERIES.get(ticker.upper())
    if query:
        url = _GNEWS.format(query=query)
        articles = _parse_feed(url, max_items)
        if articles:
            return articles
    # 검색어 없으면 yfinance 뉴스로 대체
    return _get_yf_news(ticker, max_items)


def get_korean_market_news() -> dict:
    """국내시장 페이지용 — 삼성전자 · SK하이닉스 Reuters 기사."""
    result = {}
    for ticker, (name, query) in KOREAN_NEWS_TARGETS.items():
        url = _GNEWS.format(query=query)
        articles = _parse_feed(url, 6)
        result[ticker] = {"ticker": ticker, "name": name, "articles": articles}
    return result


def get_us_market_news() -> dict:
    """미국시장 페이지용 — 카테고리별 Reuters 기사."""
    result = {}
    for category, queries in US_NEWS_CATEGORIES.items():
        raw = []
        for q in queries[:3]:           # 카테고리당 최대 3번 RSS 호출
            raw.extend(_parse_feed(_GNEWS.format(query=q), 4))
        result[category] = _dedup_sort(raw, 8)
    return result


def _get_yf_news(ticker: str, max_items: int = 10) -> list:
    """Fallback: yfinance 뉴스 (Reuters 우선 정렬)."""
    try:
        import yfinance as yf
        raw = yf.Ticker(ticker).news or []
        articles = []
        for item in raw[:max_items]:
            pub = item.get("providerPublishTime")
            pub_str = datetime.fromtimestamp(pub).strftime("%Y-%m-%d %H:%M") if pub else ""
            publisher = item.get("publisher", "")
            articles.append({
                "title":      item.get("title", ""),
                "link":       item.get("link", ""),
                "summary":    "",
                "source":     publisher,
                "published":  pub_str,
                "_is_reuters": "reuters" in publisher.lower(),
            })
        articles.sort(key=lambda x: (not x["_is_reuters"], x["published"]), reverse=False)
        return articles
    except Exception:
        return []
