from flask import Blueprint, render_template, jsonify, request
from app import cache
from app.services import detail_service

stock_bp = Blueprint("stock", __name__, url_prefix="/stock")


@stock_bp.route("/korean/<ticker>")
@cache.cached(timeout=14400, query_string=True)   # 4시간
def korean_detail(ticker):
    ticker = ticker.upper()
    info       = detail_service.get_korean_stock_info(ticker)
    chart_data = detail_service.get_korean_chart_data(ticker, period="3mo")
    return render_template(
        "stock_detail.html",
        info=info,
        chart_data=chart_data,
        market="korean",
        ticker=ticker,
        default_period="3mo",
    )


@stock_bp.route("/us/<ticker>")
@cache.cached(timeout=14400, query_string=True)   # 4시간
def us_detail(ticker):
    ticker = ticker.upper()
    info       = detail_service.get_us_stock_info(ticker)
    chart_data = detail_service.get_us_chart_data(ticker, period="3mo")
    return render_template(
        "stock_detail.html",
        info=info,
        chart_data=chart_data,
        market="us",
        ticker=ticker,
        default_period="3mo",
    )


@stock_bp.route("/api/news/<market>/<ticker>")
@cache.cached(timeout=3600, query_string=True)   # 1시간
def news_api(market, ticker):
    from app.services import news_service
    articles = news_service.get_stock_news(ticker.upper())
    return jsonify({"ticker": ticker.upper(), "articles": articles})


@stock_bp.route("/api/chart/<market>/<ticker>")
@cache.cached(timeout=14400, query_string=True)   # 4시간 — EOD 차트
def chart_api(market, ticker):
    ticker = ticker.upper()
    period = request.args.get("period", "3mo")
    if period not in {"1wk", "1mo", "3mo", "6mo", "1y"}:
        period = "3mo"

    if market == "korean":
        data = detail_service.get_korean_chart_data(ticker, period=period)
    elif market == "us":
        data = detail_service.get_us_chart_data(ticker, period=period)
    else:
        return jsonify({"error": "unknown market"}), 400

    if data is None:
        return jsonify({"error": "no data"}), 404
    return jsonify(data)
