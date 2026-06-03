from flask import Blueprint, render_template, jsonify, request
from app import cache
from app.services import korean_service

korean_bp = Blueprint("korean", __name__)

SPARKLINE_INDICES = {
    "KOSPI":    "1001",
    "KOSDAQ":   "2001",
    "KOSPI200": "1028",
}


@korean_bp.route("/")
@cache.cached(timeout=14400, query_string=True)   # 4시간 — 장마감 기준
def index():
    market = request.args.get("market", "KOSPI")

    last_day    = korean_service.get_last_trading_day()
    indices     = korean_service.get_market_indices()
    gainers, losers = korean_service.get_top_movers(market)
    recommendations = korean_service.get_recommendations(market)
    breadth     = korean_service.get_market_breadth(market)
    sectors     = korean_service.get_sector_performance()
    vol_leaders = korean_service.get_volume_leaders(market)

    sparklines = {}
    for name, ticker in SPARKLINE_INDICES.items():
        sparklines[name] = korean_service.get_sparkline_data(ticker)

    # YYYY-MM-DD 형식으로 변환
    base_date = f"{last_day[:4]}-{last_day[4:6]}-{last_day[6:]}"

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
        base_date=base_date,
    )


@korean_bp.route("/api/news")
@cache.cached(timeout=3600)   # 뉴스는 1시간
def api_news():
    from app.services import news_service
    return jsonify(news_service.get_korean_market_news())
