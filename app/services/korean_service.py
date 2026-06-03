from pykrx import stock
from datetime import datetime, timedelta
import pandas as pd


def _today():
    return datetime.now().strftime("%Y%m%d")


def _prev_date(days=1):
    return (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")


def get_market_indices():
    today = _today()
    indices = {
        "KOSPI": "1001",
        "KOSDAQ": "2001",
        "KOSPI200": "1028",
    }
    result = []
    for name, ticker in indices.items():
        try:
            df = stock.get_index_ohlcv(today, today, ticker)
            if df.empty:
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
                    "name": name,
                    "close": round(float(latest["종가"]), 2),
                    "change_pct": change_pct,
                    "volume": int(latest["거래량"]),
                })
        except Exception:
            pass
    return result


def get_top_movers(market="KOSPI", top_n=10):
    today = _today()
    try:
        df = stock.get_market_ohlcv(today, market=market)
        if df.empty:
            df = stock.get_market_ohlcv(_prev_date(3), market=market)
        if df.empty:
            return [], []

        df = df[df["거래량"] > 0].copy()
        df["등락률"] = df["등락률"].astype(float)

        gainers = df.nlargest(top_n, "등락률").reset_index()
        losers = df.nsmallest(top_n, "등락률").reset_index()

        def build_list(sub):
            rows = []
            for _, row in sub.iterrows():
                ticker = row.get("티커") or row.get("종목코드") or row.name
                name = stock.get_market_ticker_name(str(ticker))
                rows.append({
                    "ticker": str(ticker),
                    "name": name,
                    "close": round(float(row["종가"]), 0),
                    "change_pct": round(float(row["등락률"]), 2),
                    "volume": int(row["거래량"]),
                })
            return rows

        return build_list(gainers), build_list(losers)
    except Exception as e:
        return [], []


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
                df["MA5"] = df["종가"].rolling(5).mean()
                df["MA20"] = df["종가"].rolling(20).mean()
                latest = df.iloc[-1]
                prev = df.iloc[-2]
                # Golden cross signal: MA5 crosses above MA20
                golden = (prev["MA5"] <= prev["MA20"]) and (latest["MA5"] > latest["MA20"])
                # Volume surge
                avg_vol = df["거래량"].iloc[:-1].mean()
                vol_surge = latest["거래량"] > avg_vol * 1.5
                # Positive momentum
                momentum = latest["등락률"] > 0

                score = sum([golden * 3, vol_surge * 2, momentum * 1])
                if score >= 2:
                    name = stock.get_market_ticker_name(ticker)
                    candidates.append({
                        "ticker": ticker,
                        "name": name,
                        "close": round(float(latest["종가"]), 0),
                        "change_pct": round(float(latest["등락률"]), 2),
                        "volume": int(latest["거래량"]),
                        "score": score,
                        "signal": "골든크로스" if golden else ("거래량급등" if vol_surge else "상승모멘텀"),
                    })
            except Exception:
                continue
        candidates.sort(key=lambda x: x["score"], reverse=True)
        return candidates[:top_n]
    except Exception:
        return []
