from flask import Blueprint, render_template, jsonify, request
from datetime import datetime
from app import cache
from app.services import korean_service

korean_bp = Blueprint("korean", __name__)

SPARKLINE_INDICES = {
    "KOSPI":    "1001",
    "KOSDAQ":   "2001",
    "KOSPI200": "1028",
}


@korean_bp.route("/")
@cache.cached(timeout=300)
def index():
    market = request.args.get("market", "KOSPI")
    indices     = korean_service.get_market_indices()
    gainers, losers = korean_service.get_top_movers(market)
    recommendations = korean_service.get_recommendations(market)
    breadth     = korean_service.get_market_breadth(market)
    sectors     = korean_service.get_sector_performance()
    vol_leaders = korean_service.get_volume_leaders(market)

    sparklines = {}
    for name, ticker in SPARKLINE_INDICES.items():
        sparklines[name] = korean_service.get_sparkline_data(ticker)

    now = datetime.now().strftime("%Y-%m-%d %H:%M KST")
    return render_template(
        "korean.html",
        indices=indices,
        gainers=gainers,
        losers=losers,
        recommendations=recommendations,
        breadth=breadth,
        sectors=sectors,
        vol_leaders=vol_leaders,
        sparklines=sparklines,
        market=market,
        now=now,
    )


@korean_bp.route("/api/movers")
@cache.cached(timeout=300, query_string=True)
def api_movers():
    market = request.args.get("market", "KOSPI")
    gainers, losers = korean_service.get_top_movers(market)
    return jsonify({"gainers": gainers, "losers": losers})


@korean_bp.route("/api/recommendations")
@cache.cached(timeout=300, query_string=True)
def api_recommendations():
    market = request.args.get("market", "KOSPI")
    recs = korean_service.get_recommendations(market)
    return jsonify({"recommendations": recs})


@korean_bp.route("/api/data")
@cache.cached(timeout=60, query_string=True)
def api_data():
    """Fast refresh endpoint: indices + breadth + movers."""
    market = request.args.get("market", "KOSPI")
    indices = korean_service.get_market_indices()
    gainers, losers = korean_service.get_top_movers(market)
    breadth = korean_service.get_market_breadth(market)
    vol_leaders = korean_service.get_volume_leaders(market)
    return jsonify({
        "indices":     indices,
        "gainers":     gainers,
        "losers":      losers,
        "breadth":     breadth,
        "vol_leaders": vol_leaders,
        "updated_at":  datetime.now().strftime("%H:%M:%S"),
    })
