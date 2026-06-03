"""
api.py — Universal search API and search redirect route.
Routes:
  GET /api/search?q=<query>&market=<korean|us>  → JSON list
  GET /search?q=<query>&market=<korean|us>       → redirect to detail page
"""
from flask import Blueprint, jsonify, request, redirect, url_for
from app.services.us_service import SP500_TICKERS

api_bp = Blueprint("api", __name__)


def _search_korean(q):
    """Search Korean tickers and names via pykrx."""
    results = []
    try:
        from pykrx import stock as krx
        from datetime import datetime
        today = datetime.now().strftime("%Y%m%d")
        tickers = krx.get_market_ticker_list(today, market="ALL")
        q_lower = q.lower()
        for ticker in tickers:
            try:
                name = krx.get_market_ticker_name(ticker) or ""
                if q_lower in ticker.lower() or q_lower in name.lower():
                    results.append({"ticker": ticker, "name": name, "market": "korean"})
                    if len(results) >= 20:
                        break
            except Exception:
                continue
    except Exception:
        pass
    return results


def _search_us(q):
    """Search US tickers from SP500_TICKERS list."""
    results = []
    q_upper = q.upper()
    q_lower = q.lower()
    for ticker in SP500_TICKERS:
        if q_upper in ticker or q_lower in ticker.lower():
            results.append({"ticker": ticker, "name": ticker, "market": "us"})
    return results[:20]


@api_bp.route("/api/search")
def search_api():
    q = request.args.get("q", "").strip()
    market = request.args.get("market", "us").lower()
    if not q:
        return jsonify([])

    if market == "korean":
        results = _search_korean(q)
    else:
        results = _search_us(q)

    return jsonify(results)


@api_bp.route("/search")
def search_redirect():
    q = request.args.get("q", "").strip()
    market = request.args.get("market", "us").lower()
    if not q:
        if market == "korean":
            return redirect(url_for("korean.index"))
        return redirect(url_for("us.index"))

    # Try exact match first
    if market == "korean":
        try:
            from pykrx import stock as krx
            from datetime import datetime
            today = datetime.now().strftime("%Y%m%d")
            tickers = krx.get_market_ticker_list(today, market="ALL")
            q_upper = q.upper()
            # Exact ticker match
            if q_upper in [t.upper() for t in tickers]:
                return redirect(url_for("stock.korean_detail", ticker=q_upper))
            # Name match
            for ticker in tickers:
                name = krx.get_market_ticker_name(ticker) or ""
                if q.lower() in name.lower():
                    return redirect(url_for("stock.korean_detail", ticker=ticker))
        except Exception:
            pass
        return redirect(url_for("korean.index"))
    else:
        q_upper = q.upper()
        if q_upper in [t.upper() for t in SP500_TICKERS]:
            return redirect(url_for("stock.us_detail", ticker=q_upper))
        # Partial match
        for ticker in SP500_TICKERS:
            if q_upper in ticker:
                return redirect(url_for("stock.us_detail", ticker=ticker))
        return redirect(url_for("us.index"))
