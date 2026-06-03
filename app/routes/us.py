from flask import Blueprint, render_template, jsonify
from app import cache
from app.services import us_service

us_bp = Blueprint("us", __name__)


@us_bp.route("/")
@cache.cached(timeout=300)
def index():
    indices = us_service.get_market_indices()
    gainers, losers = us_service.get_top_movers()
    recommendations = us_service.get_recommendations()
    return render_template(
        "us.html",
        indices=indices,
        gainers=gainers,
        losers=losers,
        recommendations=recommendations,
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
