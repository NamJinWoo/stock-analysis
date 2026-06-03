from flask import Blueprint, render_template, jsonify
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
@cache.cached(timeout=14400)   # 4시간 — 장마감 기준
def index():
    indices     = us_service.get_market_indices()
    gainers, losers = us_service.get_top_movers()
    recommendations = us_service.get_recommendations()
    sectors     = us_service.get_sector_performance()
    fear_greed  = us_service.get_fear_greed()
    vol_leaders = us_service.get_volume_leaders()
    breadth     = us_service.get_market_breadth()
    base_date   = us_service.get_last_trading_day()

    sparklines = {}
    for name, ticker in SPARKLINE_INDICES.items():
        sparklines[name] = us_service.get_sparkline_data(ticker)

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
        base_date=base_date,
    )


@us_bp.route("/api/news")
@cache.cached(timeout=3600)   # 뉴스는 1시간
def api_news():
    from app.services import news_service
    return jsonify(news_service.get_us_market_news())
