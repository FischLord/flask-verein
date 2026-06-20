import os
from datetime import datetime

from flask import Flask, abort
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_mail import Mail
from sqlalchemy import MetaData

from .modules.util.config import eval_bool_env_var

# Benannte Constraints – nötig für sichere SQLite-Migrationen
# (Flask-Migrate/Alembic mit render_as_batch=True).
naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

db = SQLAlchemy(metadata=MetaData(naming_convention=naming_convention))
migrate = Migrate()
login = LoginManager()
# Hinweis: Für Mehr-Worker-Produktion sollte ein storage_uri
# (z. B. Redis) konfiguriert werden.
limiter = Limiter(key_func=get_remote_address)
mail = Mail()


def create_app(config_class=Config):
    app = Flask(__name__, template_folder="templates")
    app.config.from_object(Config)

    if not app.config.get("SECRET_KEY"):
        raise RuntimeError(
            "SECRET_KEY fehlt – in .env setzen (fester, zufälliger Wert)."
        )

    # Upload-Verzeichnis: absoluter Pfad (app/static/uploads), sofern nicht
    # per UPLOAD_FOLDER-Umgebungsvariable überschrieben. In .gitignore.
    if not app.config.get("UPLOAD_FOLDER"):
        app.config["UPLOAD_FOLDER"] = os.path.join(
            app.root_path, "static", "uploads"
        )
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    db.init_app(app)
    # render_as_batch=True: SQLite kennt kein vollwertiges ALTER TABLE,
    # Alembic erzeugt dann Batch-Operationen.
    migrate.init_app(app, db, render_as_batch=True)
    login.init_app(app)
    login.login_view = "auth.login"
    limiter.init_app(app)
    mail.init_app(app)

    from app.main import main as main

    app.register_blueprint(main)

    from app.main.formcenter import formcenter
    app.register_blueprint(formcenter, url_prefix='/formcenter')

    from app.auth import auth as auth

    app.register_blueprint(auth)

    from app.admin import admin as admin

    app.register_blueprint(admin, url_prefix="/admin")

    from app import errors

    app.register_blueprint(errors.error)

    from app.cli import import_berichte
    from app.seed import seed_stammdaten

    app.cli.add_command(import_berichte)
    app.cli.add_command(seed_stammdaten)

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
