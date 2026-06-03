from flask import Blueprint, render_template, jsonify
from datetime import datetime
from app import cache
from app.services import us_service

us_bp = Blueprint("us", __name__)

SPARKLINE_INDICES = {
    "S&P 500":   "^GSPC",
    "NASDAQ":    "^IXIC",
    "Dow Jones": "^DJI",
    "VIX":       "^VIX",
}


@us_bp.route("/")
@cache.cached(timeout=300)
def index():
    indices     = us_service.get_market_indices()
    gainers, losers = us_service.get_top_movers()
    recommendations = us_service.get_recommendations()
    sectors     = us_service.get_sector_performance()
    fear_greed  = us_service.get_fear_greed()
    vol_leaders = us_service.get_volume_leaders()

    sparklines = {}
    for name, ticker in SPARKLINE_INDICES.items():
        sparklines[name] = us_service.get_sparkline_data(ticker)

    breadth = us_service.get_market_breadth()
    now = datetime.now().strftime("%Y-%m-%d %H:%M ET")
    return render_template(
        "us.html",
        indices=indices,
        gainers=gainers,
        losers=losers,
        recommendations=recommendations,
        sectors=sectors,
        fear_greed=fear_greed,
        vol_leaders=vol_leaders,
        sparklines=sparklines,
        breadth=breadth,
        now=now,
    )


@us_bp.route("/api/movers")
@cache.cached(timeout=300)
def api_movers():
    gainers, losers = us_service.get_top_movers()
    return jsonify({"gainers": gainers, "losers": losers})


@us_bp.route("/api/recommendations")
@cache.cached(timeout=300)
def api_recommendations():
    recs = us_service.get_recommendations()
    return jsonify({"recommendations": recs})


@us_bp.route("/api/data")
@cache.cached(timeout=60)
def api_data():
    """Fast refresh endpoint: indices + breadth + movers + fear_greed."""
    indices     = us_service.get_market_indices()
    gainers, losers = us_service.get_top_movers()
    fear_greed  = us_service.get_fear_greed()
    vol_leaders = us_service.get_volume_leaders()
    return jsonify({
        "indices":     indices,
        "gainers":     gainers,
        "losers":      losers,
        "fear_greed":  fear_greed,
        "vol_leaders": vol_leaders,
        "updated_at":  datetime.now().strftime("%H:%M:%S"),
    })
