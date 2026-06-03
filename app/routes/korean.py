from flask import Blueprint, render_template, jsonify, request
from app import cache
from app.services import korean_service

korean_bp = Blueprint("korean", __name__)


@korean_bp.route("/")
@cache.cached(timeout=300)
def index():
    indices = korean_service.get_market_indices()
    gainers, losers = korean_service.get_top_movers("KOSPI")
    recommendations = korean_service.get_recommendations("KOSPI")
    return render_template(
        "korean.html",
        indices=indices,
        gainers=gainers,
        losers=losers,
        recommendations=recommendations,
        market="KOSPI",
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
