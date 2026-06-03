"""
stock.py — Stock detail pages and chart data API.
Routes:
  /stock/korean/<ticker>  → Korean stock detail
  /stock/us/<ticker>      → US stock detail
  /stock/api/chart/<market>/<ticker>  → JSON chart data (AJAX)
"""
from flask import Blueprint, render_template, jsonify, request, abort
from app import cache
from app.services import detail_service

stock_bp = Blueprint("stock", __name__, url_prefix="/stock")


@stock_bp.route("/korean/<ticker>")
def korean_detail(ticker):
    ticker = ticker.upper()
    info = detail_service.get_korean_stock_info(ticker)
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
def us_detail(ticker):
    ticker = ticker.upper()
    info = detail_service.get_us_stock_info(ticker)
    chart_data = detail_service.get_us_chart_data(ticker, period="3mo")
    return render_template(
        "stock_detail.html",
        info=info,
        chart_data=chart_data,
        market="us",
        ticker=ticker,
        default_period="3mo",
    )


@stock_bp.route("/api/chart/<market>/<ticker>")
@cache.cached(timeout=120, query_string=True)
def chart_api(market, ticker):
    ticker = ticker.upper()
    period = request.args.get("period", "3mo")
    valid_periods = {"1wk", "1mo", "3mo", "6mo", "1y"}
    if period not in valid_periods:
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
