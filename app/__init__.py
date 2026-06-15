from datetime import datetime

from flask import Flask, abort
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from .modules.util.config import eval_bool_env_var

db = SQLAlchemy()
login = LoginManager()
# Hinweis: Für Mehr-Worker-Produktion sollte ein storage_uri
# (z. B. Redis) konfiguriert werden.
limiter = Limiter(key_func=get_remote_address)


def create_app(config_class=Config):
    app = Flask(__name__, template_folder="templates")
    app.config.from_object(Config)

    if not app.config.get("SECRET_KEY"):
        raise RuntimeError(
            "SECRET_KEY fehlt – in .env setzen (fester, zufälliger Wert)."
        )

    db.init_app(app)
    login.init_app(app)
    login.login_view = "auth.login"
    limiter.init_app(app)

    from app.main import main as main

    app.register_blueprint(main)

    from app.main.formcenter import formcenter
    app.register_blueprint(formcenter, url_prefix='/formcenter')

    from app.auth import auth as auth

    app.register_blueprint(auth)

    from app import errors

    app.register_blueprint(errors.error)

    @app.before_request
    def maintenance_mode():
        # If maintenance mode is enabled, return a 503
        if eval_bool_env_var(app.config["MAINTENANCE_MODE"]):
            abort(503)

    @app.after_request
    def set_security_headers(response):
        # 'unsafe-inline' bei style ist Übergang; Nonce-Härtung folgt.
        # Inline-Scripts sind ausgelagert, daher script-src 'self'.
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "img-src 'self' data:; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "font-src 'self'; "
            "object-src 'none'; "
            "base-uri 'self'; "
            "frame-ancestors 'none'; "
            "form-action 'self'"
        )
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=()"
        )
        # Nur über HTTPS wirksam; alternativ am Reverse-Proxy setzen.
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
        return response

    @app.context_processor
    def inject_current_year():
        return {"current_year": datetime.now().year}

    return app
