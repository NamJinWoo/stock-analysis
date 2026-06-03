from flask import Flask
from flask_caching import Cache
from config import Config

cache = Cache()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    cache.init_app(app)

    from app.routes.main import main_bp
    from app.routes.korean import korean_bp
    from app.routes.us import us_bp
    from app.routes.stock import stock_bp
    from app.routes.api import api_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(korean_bp, url_prefix="/korean")
    app.register_blueprint(us_bp, url_prefix="/us")
    app.register_blueprint(stock_bp)
    app.register_blueprint(api_bp)

    return app
