import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta


INDICES = {
    "S&P 500": "^GSPC",
    "NASDAQ": "^IXIC",
    "Dow Jones": "^DJI",
    "VIX": "^VIX",
}

SP500_TICKERS = [
    "AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "GOOG", "TSLA", "BRK-B",
    "UNH", "JPM", "V", "XOM", "LLY", "JNJ", "MA", "PG", "HD", "CVX",
    "AVGO", "MRK", "ABBV", "COST", "PEP", "KO", "WMT", "AMD", "CRM", "NFLX",
    "BAC", "DIS", "ADBE", "CSCO", "ACN", "MCD", "PFE", "TMO", "NEE", "LIN",
    "TXN", "ORCL", "AMGN", "PM", "RTX", "QCOM", "UPS", "HON", "IBM", "GE",
]


def get_market_indices():
    result = []
    for name, ticker in INDICES.items():
        try:
            t = yf.Ticker(ticker)
            hist = t.history(period="2d")
            if len(hist) >= 2:
                curr = hist["Close"].iloc[-1]
                prev = hist["Close"].iloc[-2]
                change_pct = round((curr - prev) / prev * 100, 2)
            elif len(hist) == 1:
                curr = hist["Close"].iloc[-1]
                change_pct = 0.0
            else:
                continue
            result.append({
                "name": name,
                "ticker": ticker,
                "close": round(float(curr), 2),
                "change_pct": change_pct,
            })
        except Exception:
            pass
    return result


def get_top_movers(tickers=None, top_n=10):
    if tickers is None:
        tickers = SP500_TICKERS
    data = []
    raw = yf.download(tickers, period="2d", auto_adjust=True, progress=False)
    close = raw["Close"] if "Close" in raw else raw.get("Adj Close", pd.DataFrame())
    if close.empty:
        return [], []
    for ticker in tickers:
        try:
            if ticker not in close.columns:
                continue
            prices = close[ticker].dropna()
            if len(prices) < 2:
                continue
            curr = float(prices.iloc[-1])
            prev = float(prices.iloc[-2])
            change_pct = round((curr - prev) / prev * 100, 2)
            vol_series = raw["Volume"][ticker].dropna() if "Volume" in raw else pd.Series()
            volume = int(vol_series.iloc[-1]) if not vol_series.empty else 0
            data.append({
                "ticker": ticker,
                "name": ticker,
                "close": round(curr, 2),
                "change_pct": change_pct,
                "volume": volume,
            })
        except Exception:
            continue
    data.sort(key=lambda x: x["change_pct"], reverse=True)
    gainers = data[:top_n]
    losers = sorted(data, key=lambda x: x["change_pct"])[:top_n]
    return gainers, losers


def get_recommendations(tickers=None, top_n=10):
    if tickers is None:
        tickers = SP500_TICKERS
    raw = yf.download(tickers, period="3mo", auto_adjust=True, progress=False)
    close = raw["Close"] if "Close" in raw else raw.get("Adj Close", pd.DataFrame())
    volume = raw["Volume"] if "Volume" in raw else pd.DataFrame()
    if close.empty:
        return []

    candidates = []
    for ticker in tickers:
        try:
            if ticker not in close.columns:
                continue
            prices = close[ticker].dropna()
            if len(prices) < 20:
                continue
            ma5 = prices.rolling(5).mean()
            ma20 = prices.rolling(20).mean()
            latest_price = float(prices.iloc[-1])
            prev_price = float(prices.iloc[-2])
            change_pct = round((latest_price - prev_price) / prev_price * 100, 2)

            golden = (ma5.iloc[-2] <= ma20.iloc[-2]) and (ma5.iloc[-1] > ma20.iloc[-1])

            vol_surge = False
            if ticker in volume.columns:
                vols = volume[ticker].dropna()
                if len(vols) >= 10:
                    avg_vol = float(vols.iloc[:-1].mean())
                    vol_surge = float(vols.iloc[-1]) > avg_vol * 1.5

            momentum = change_pct > 0
            score = sum([golden * 3, vol_surge * 2, momentum * 1])
            if score >= 2:
                signal = "Golden Cross" if golden else ("Volume Surge" if vol_surge else "Momentum")
                candidates.append({
                    "ticker": ticker,
                    "name": ticker,
                    "close": round(latest_price, 2),
                    "change_pct": change_pct,
                    "volume": int(volume[ticker].dropna().iloc[-1]) if ticker in volume.columns and not volume[ticker].dropna().empty else 0,
                    "score": score,
                    "signal": signal,
                })
        except Exception:
            continue
    candidates.sort(key=lambda x: x["score"], reverse=True)
    return candidates[:top_n]
