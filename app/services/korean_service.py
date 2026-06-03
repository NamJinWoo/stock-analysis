from pykrx import stock
from datetime import datetime, timedelta
import pandas as pd


KOSPI_SECTORS = {
    "전기전자": "1014",
    "금융업":   "1022",
    "의약품":   "1010",
    "화학":     "1009",
    "철강금속": "1012",
    "운수장비": "1016",
    "건설업":   "1019",
    "통신업":   "1021",
    "서비스업": "1026",
    "유통업":   "1017",
}


def _today():
    return datetime.now().strftime("%Y%m%d")


def _prev_date(days=1):
    return (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")


def get_last_trading_day():
    """Return most recent date string (YYYYMMDD) that has KOSPI data."""
    today = _today()
    for offset in range(0, 7):
        candidate = (datetime.now() - timedelta(days=offset)).strftime("%Y%m%d")
        try:
            df = stock.get_index_ohlcv(candidate, candidate, "1001")
            if df is not None and not df.empty:
                return candidate
        except Exception:
            continue
    return today


def get_market_indices():
    today = _today()
    indices = {
        "KOSPI":    "1001",
        "KOSDAQ":   "2001",
        "KOSPI200": "1028",
    }
    result = []
    for name, ticker in indices.items():
        try:
            df = stock.get_index_ohlcv(today, today, ticker)
            if df is None or df.empty:
                df = stock.get_index_ohlcv(_prev_date(3), today, ticker)
            if not df.empty:
                latest = df.iloc[-1]
                prev_df = stock.get_index_ohlcv(_prev_date(5), today, ticker)
                change_pct = 0.0
                if len(prev_df) >= 2:
                    prev_close = prev_df.iloc[-2]["종가"]
                    curr_close = prev_df.iloc[-1]["종가"]
                    if prev_close:
                        change_pct = round((curr_close - prev_close) / prev_close * 100, 2)
                result.append({
                    "name":       name,
                    "ticker":     ticker,
                    "close":      round(float(latest["종가"]), 2),
                    "change_pct": change_pct,
                    "volume":     int(latest["거래량"]),
                })
        except Exception:
            pass
    return result


def get_sparkline_data(index_ticker):
    """Return last 7 trading days of close prices for an index."""
    try:
        end = _today()
        start = _prev_date(14)
        df = stock.get_index_ohlcv(start, end, index_ticker)
        if df is None or df.empty:
            return []
        closes = df["종가"].astype(float).tail(7).tolist()
        return [round(c, 2) for c in closes]
    except Exception:
        return []


def get_market_breadth(market="KOSPI"):
    """Return advancers/decliners/unchanged counts for market breadth."""
    try:
        today = _today()
        df = stock.get_market_ohlcv(today, market=market)
        if df is None or df.empty:
            df = stock.get_market_ohlcv(_prev_date(3), market=market)
        if df is None or df.empty:
            return {"advancers": 0, "decliners": 0, "unchanged": 0}

        df = df[df["거래량"] > 0].copy()
        changes = df["등락률"].astype(float)
        advancers = int((changes > 0).sum())
        decliners = int((changes < 0).sum())
        unchanged = int((changes == 0).sum())
        return {"advancers": advancers, "decliners": decliners, "unchanged": unchanged}
    except Exception:
        return {"advancers": 0, "decliners": 0, "unchanged": 0}


def get_sector_performance():
    """Return KOSPI sector index performance list."""
    today = _today()
    start = _prev_date(5)
    result = []
    for name, ticker in KOSPI_SECTORS.items():
        try:
            df = stock.get_index_ohlcv(start, today, ticker)
            if df is None or df.empty:
                continue
            if len(df) >= 2:
                curr = float(df.iloc[-1]["종가"])
                prev = float(df.iloc[-2]["종가"])
                change_pct = round((curr - prev) / prev * 100, 2) if prev else 0.0
            else:
                curr = float(df.iloc[-1]["종가"])
                change_pct = 0.0
            result.append({"name": name, "ticker": ticker, "close": curr, "change_pct": change_pct})
        except Exception:
            continue
    return result


def get_top_movers(market="KOSPI", top_n=10):
    today = _today()
    try:
        df = stock.get_market_ohlcv(today, market=market)
        if df is None or df.empty:
            df = stock.get_market_ohlcv(_prev_date(3), market=market)
        if df is None or df.empty:
            return [], []

        df = df[df["거래량"] > 0].copy()
        df["등락률"] = df["등락률"].astype(float)

        gainers = df.nlargest(top_n, "등락률").reset_index()
        losers  = df.nsmallest(top_n, "등락률").reset_index()

        def build_list(sub):
            rows = []
            for _, row in sub.iterrows():
                ticker = row.get("티커") or row.get("종목코드") or row.name
                name = stock.get_market_ticker_name(str(ticker))
                rows.append({
                    "ticker":     str(ticker),
                    "name":       name,
                    "close":      round(float(row["종가"]), 0),
                    "change_pct": round(float(row["등락률"]), 2),
                    "volume":     int(row["거래량"]),
                })
            return rows

        return build_list(gainers), build_list(losers)
    except Exception:
        return [], []


def get_volume_leaders(market="KOSPI", top_n=10):
    """Return top N stocks by trading volume."""
    today = _today()
    try:
        df = stock.get_market_ohlcv(today, market=market)
        if df is None or df.empty:
            df = stock.get_market_ohlcv(_prev_date(3), market=market)
        if df is None or df.empty:
            return []

        df = df[df["거래량"] > 0].copy()
        top = df.nlargest(top_n, "거래량").reset_index()
        rows = []
        for _, row in top.iterrows():
            ticker = row.get("티커") or row.get("종목코드") or row.name
            name = stock.get_market_ticker_name(str(ticker))
            rows.append({
                "ticker":     str(ticker),
                "name":       name,
                "close":      round(float(row["종가"]), 0),
                "change_pct": round(float(row["등락률"]), 2),
                "volume":     int(row["거래량"]),
            })
        return rows
    except Exception:
        return []


def get_recommendations(market="KOSPI", top_n=10):
    today = _today()
    start = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")
    try:
        tickers = stock.get_market_ticker_list(today, market=market)
        candidates = []
        for ticker in tickers[:200]:
            try:
                df = stock.get_market_ohlcv(start, today, ticker)
                if len(df) < 10:
                    continue
                df["MA5"]  = df["종가"].rolling(5).mean()
                df["MA20"] = df["종가"].rolling(20).mean()
                latest = df.iloc[-1]
                prev   = df.iloc[-2]
                golden = (prev["MA5"] <= prev["MA20"]) and (latest["MA5"] > latest["MA20"])
                avg_vol   = df["거래량"].iloc[:-1].mean()
                vol_surge = latest["거래량"] > avg_vol * 1.5
                momentum  = latest["등락률"] > 0
                score = sum([golden * 3, vol_surge * 2, momentum * 1])
                if score >= 2:
                    name = stock.get_market_ticker_name(ticker)
                    candidates.append({
                        "ticker":     ticker,
                        "name":       name,
                        "close":      round(float(latest["종가"]), 0),
                        "change_pct": round(float(latest["등락률"]), 2),
                        "volume":     int(latest["거래량"]),
                        "score":      score,
                        "signal":     "골든크로스" if golden else ("거래량급등" if vol_surge else "상승모멘텀"),
                    })
            except Exception:
                continue
        candidates.sort(key=lambda x: x["score"], reverse=True)
        return candidates[:top_n]
    except Exception:
        return []
