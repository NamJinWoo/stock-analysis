"""
detail_service.py — Chart data (OHLCV + MA5/MA20/MA60 + Bollinger + RSI + MACD)
and stock fundamental info for both Korean and US markets.
"""
import pandas as pd
from datetime import datetime, timedelta


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _nan_to_none(val):
    try:
        if val is None:
            return None
        if isinstance(val, float) and (val != val):  # NaN
            return None
        return round(float(val), 4)
    except (TypeError, ValueError):
        return None


def _calc_rsi(closes, period=14):
    delta = closes.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


def _calc_macd(closes, fast=12, slow=26, signal=9):
    ema_fast = closes.ewm(span=fast, adjust=False).mean()
    ema_slow = closes.ewm(span=slow, adjust=False).mean()
    macd = ema_fast - ema_slow
    sig = macd.ewm(span=signal, adjust=False).mean()
    return macd, sig, macd - sig


def _calc_bollinger(closes, period=20, k=2):
    ma = closes.rolling(period).mean()
    std = closes.rolling(period).std()
    return ma + k * std, ma, ma - k * std


def _series_to_list(s):
    return [_nan_to_none(v) for v in s]


def _period_to_days(period):
    mapping = {"1wk": 10, "1mo": 35, "3mo": 95, "6mo": 185, "1y": 370}
    return mapping.get(period, 95)


# ---------------------------------------------------------------------------
# Korean stock detail
# ---------------------------------------------------------------------------

def get_korean_chart_data(ticker, period="3mo"):
    """Return OHLCV + indicators for a Korean stock ticker."""
    try:
        from pykrx import stock as krx
        days = _period_to_days(period)
        today = datetime.now().strftime("%Y%m%d")
        start = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")

        df = krx.get_market_ohlcv(start, today, ticker)
        if df is None or df.empty:
            return None

        closes = df["종가"].astype(float)
        dates = [d.strftime("%Y-%m-%d") for d in df.index]

        ma5 = closes.rolling(5).mean()
        ma20 = closes.rolling(20).mean()
        ma60 = closes.rolling(60).mean()
        bb_upper, bb_mid, bb_lower = _calc_bollinger(closes)
        rsi = _calc_rsi(closes)
        macd, macd_sig, macd_hist = _calc_macd(closes)

        return {
            "dates": dates,
            "close": _series_to_list(closes),
            "open": _series_to_list(df["시가"].astype(float)),
            "high": _series_to_list(df["고가"].astype(float)),
            "low": _series_to_list(df["저가"].astype(float)),
            "volume": [int(v) for v in df["거래량"]],
            "ma5": _series_to_list(ma5),
            "ma20": _series_to_list(ma20),
            "ma60": _series_to_list(ma60),
            "bb_upper": _series_to_list(bb_upper),
            "bb_mid": _series_to_list(bb_mid),
            "bb_lower": _series_to_list(bb_lower),
            "rsi": _series_to_list(rsi),
            "macd": _series_to_list(macd),
            "macd_signal": _series_to_list(macd_sig),
            "macd_hist": _series_to_list(macd_hist),
        }
    except Exception:
        return None


def get_korean_stock_info(ticker):
    """Return fundamental data and technical signals for a Korean ticker."""
    try:
        from pykrx import stock as krx
        today = datetime.now().strftime("%Y%m%d")
        start_1mo = (datetime.now() - timedelta(days=35)).strftime("%Y%m%d")

        name = krx.get_market_ticker_name(ticker) or ticker

        # Price data
        df = krx.get_market_ohlcv(start_1mo, today, ticker)
        if df is None or df.empty:
            return {"ticker": ticker, "name": name}

        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) >= 2 else latest
        curr_close = float(latest["종가"])
        prev_close = float(prev["종가"])
        change = curr_close - prev_close
        change_pct = round((change / prev_close) * 100, 2) if prev_close else 0.0

        # 52-week high/low
        start_1y = (datetime.now() - timedelta(days=370)).strftime("%Y%m%d")
        try:
            df_1y = krx.get_market_ohlcv(start_1y, today, ticker)
            high_52w = float(df_1y["고가"].max()) if not df_1y.empty else None
            low_52w = float(df_1y["저가"].min()) if not df_1y.empty else None
        except Exception:
            high_52w = None
            low_52w = None

        # Fundamentals via pykrx
        per, pbr, eps, bps, div_yield = None, None, None, None, None
        market_cap = None
        try:
            fund = krx.get_market_fundamental(today, today, ticker)
            if fund is None or fund.empty:
                fund = krx.get_market_fundamental(start_1mo, today, ticker)
            if fund is not None and not fund.empty:
                row = fund.iloc[-1]
                per = _nan_to_none(row.get("PER"))
                pbr = _nan_to_none(row.get("PBR"))
                eps = _nan_to_none(row.get("EPS"))
                bps = _nan_to_none(row.get("BPS"))
                div_yield = _nan_to_none(row.get("DIV"))
        except Exception:
            pass

        try:
            cap_df = krx.get_market_cap(today, today, ticker)
            if cap_df is None or cap_df.empty:
                cap_df = krx.get_market_cap(start_1mo, today, ticker)
            if cap_df is not None and not cap_df.empty:
                market_cap = int(cap_df.iloc[-1]["시가총액"])
        except Exception:
            pass

        # Technical signals
        closes = df["종가"].astype(float)
        signals = _compute_signals(closes)

        return {
            "ticker": ticker,
            "name": name,
            "curr_close": curr_close,
            "change": round(change, 2),
            "change_pct": change_pct,
            "high_52w": high_52w,
            "low_52w": low_52w,
            "market_cap": market_cap,
            "per": per,
            "pbr": pbr,
            "eps": eps,
            "bps": bps,
            "div_yield": div_yield,
            "signals": signals,
            "market": "korean",
        }
    except Exception:
        return {"ticker": ticker, "name": ticker, "market": "korean"}


# ---------------------------------------------------------------------------
# US stock detail
# ---------------------------------------------------------------------------

def get_us_chart_data(ticker, period="3mo"):
    """Return OHLCV + indicators for a US stock ticker."""
    try:
        import yfinance as yf
        period_map = {"1wk": "5d", "1mo": "1mo", "3mo": "3mo", "6mo": "6mo", "1y": "1y"}
        yf_period = period_map.get(period, "3mo")

        t = yf.Ticker(ticker)
        df = t.history(period=yf_period)
        if df is None or df.empty:
            return None

        closes = df["Close"].astype(float)
        dates = [d.strftime("%Y-%m-%d") for d in df.index]

        ma5 = closes.rolling(5).mean()
        ma20 = closes.rolling(20).mean()
        ma60 = closes.rolling(60).mean()
        bb_upper, bb_mid, bb_lower = _calc_bollinger(closes)
        rsi = _calc_rsi(closes)
        macd, macd_sig, macd_hist = _calc_macd(closes)

        return {
            "dates": dates,
            "close": _series_to_list(closes),
            "open": _series_to_list(df["Open"].astype(float)),
            "high": _series_to_list(df["High"].astype(float)),
            "low": _series_to_list(df["Low"].astype(float)),
            "volume": [int(v) for v in df["Volume"]],
            "ma5": _series_to_list(ma5),
            "ma20": _series_to_list(ma20),
            "ma60": _series_to_list(ma60),
            "bb_upper": _series_to_list(bb_upper),
            "bb_mid": _series_to_list(bb_mid),
            "bb_lower": _series_to_list(bb_lower),
            "rsi": _series_to_list(rsi),
            "macd": _series_to_list(macd),
            "macd_signal": _series_to_list(macd_sig),
            "macd_hist": _series_to_list(macd_hist),
        }
    except Exception:
        return None


def get_us_stock_info(ticker):
    """Return fundamental data and technical signals for a US ticker."""
    try:
        import yfinance as yf
        t = yf.Ticker(ticker)
        info = {}
        try:
            info = t.info or {}
        except Exception:
            pass

        hist = pd.DataFrame()
        try:
            hist = t.history(period="1y")
        except Exception:
            pass

        name = info.get("longName") or info.get("shortName") or ticker

        curr_close = None
        change = None
        change_pct = None
        if not hist.empty:
            closes = hist["Close"].astype(float)
            curr_close = float(closes.iloc[-1])
            if len(closes) >= 2:
                prev_close = float(closes.iloc[-2])
                change = round(curr_close - prev_close, 2)
                change_pct = round((change / prev_close) * 100, 2) if prev_close else 0.0
            signals = _compute_signals(closes)
        else:
            signals = {}

        high_52w = _nan_to_none(info.get("fiftyTwoWeekHigh"))
        low_52w = _nan_to_none(info.get("fiftyTwoWeekLow"))
        market_cap = info.get("marketCap")
        pe_ratio = _nan_to_none(info.get("trailingPE"))
        eps = _nan_to_none(info.get("trailingEps"))
        div_yield = _nan_to_none(info.get("dividendYield"))
        if div_yield:
            div_yield = round(div_yield * 100, 2)
        beta = _nan_to_none(info.get("beta"))
        sector = info.get("sector", "")
        industry = info.get("industry", "")

        return {
            "ticker": ticker,
            "name": name,
            "curr_close": curr_close,
            "change": change,
            "change_pct": change_pct,
            "high_52w": high_52w,
            "low_52w": low_52w,
            "market_cap": market_cap,
            "per": pe_ratio,
            "eps": eps,
            "div_yield": div_yield,
            "beta": beta,
            "sector": sector,
            "industry": industry,
            "signals": signals,
            "market": "us",
        }
    except Exception:
        return {"ticker": ticker, "name": ticker, "market": "us"}


# ---------------------------------------------------------------------------
# Technical signal summary
# ---------------------------------------------------------------------------

def _compute_signals(closes):
    """Compute Bullish/Bearish/Neutral for 4 indicators."""
    signals = {}
    try:
        if len(closes) < 5:
            return signals

        ma5 = closes.rolling(5).mean()
        ma20 = closes.rolling(20).mean()

        # MA Cross signal
        if len(ma5.dropna()) >= 2 and len(ma20.dropna()) >= 2:
            prev_ma5 = ma5.iloc[-2]
            curr_ma5 = ma5.iloc[-1]
            prev_ma20 = ma20.iloc[-2]
            curr_ma20 = ma20.iloc[-1]
            if prev_ma5 <= prev_ma20 and curr_ma5 > curr_ma20:
                signals["ma_cross"] = "Bullish"
            elif prev_ma5 >= prev_ma20 and curr_ma5 < curr_ma20:
                signals["ma_cross"] = "Bearish"
            elif curr_ma5 > curr_ma20:
                signals["ma_cross"] = "Bullish"
            else:
                signals["ma_cross"] = "Bearish"
        else:
            signals["ma_cross"] = "Neutral"

        # RSI signal
        if len(closes) >= 15:
            rsi = _calc_rsi(closes)
            curr_rsi = rsi.iloc[-1]
            if curr_rsi is not None and not (curr_rsi != curr_rsi):
                if curr_rsi >= 70:
                    signals["rsi"] = "Bearish"
                elif curr_rsi <= 30:
                    signals["rsi"] = "Bullish"
                else:
                    signals["rsi"] = "Neutral"
                signals["rsi_value"] = round(float(curr_rsi), 2)
            else:
                signals["rsi"] = "Neutral"
        else:
            signals["rsi"] = "Neutral"

        # MACD signal
        if len(closes) >= 27:
            macd, macd_sig, _ = _calc_macd(closes)
            if len(macd.dropna()) >= 2 and len(macd_sig.dropna()) >= 2:
                prev_macd = macd.iloc[-2]
                curr_macd = macd.iloc[-1]
                prev_sig = macd_sig.iloc[-2]
                curr_sig = macd_sig.iloc[-1]
                if prev_macd <= prev_sig and curr_macd > curr_sig:
                    signals["macd"] = "Bullish"
                elif prev_macd >= prev_sig and curr_macd < curr_sig:
                    signals["macd"] = "Bearish"
                elif curr_macd > curr_sig:
                    signals["macd"] = "Bullish"
                else:
                    signals["macd"] = "Bearish"
            else:
                signals["macd"] = "Neutral"
        else:
            signals["macd"] = "Neutral"

        # Bollinger Band position
        if len(closes) >= 21:
            bb_upper, bb_mid, bb_lower = _calc_bollinger(closes)
            curr_price = closes.iloc[-1]
            curr_upper = bb_upper.iloc[-1]
            curr_lower = bb_lower.iloc[-1]
            if not (curr_upper != curr_upper) and not (curr_lower != curr_lower):
                if curr_price >= curr_upper:
                    signals["bb"] = "Bearish"
                elif curr_price <= curr_lower:
                    signals["bb"] = "Bullish"
                else:
                    signals["bb"] = "Neutral"
            else:
                signals["bb"] = "Neutral"
        else:
            signals["bb"] = "Neutral"

    except Exception:
        pass

    return signals
