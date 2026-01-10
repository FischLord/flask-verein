import logging
from logging.handlers import RotatingFileHandler
import os

from flask import Flask, abort
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from .modules.util.config import eval_bool_env_var

db = SQLAlchemy()
login = LoginManager()
migrate = Migrate()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
)


def create_app(config_class=Config):
    app = Flask(__name__, template_folder="templates")
    app.config.from_object(Config)

    # Extensions initialisieren
    db.init_app(app)
    login.init_app(app)
    login.login_view = "auth.login"
    migrate.init_app(app, db)

    # Rate Limiter nur wenn aktiviert
    if app.config.get("RATELIMIT_ENABLED", True):
        limiter.init_app(app)

    # Logging konfigurieren
    configure_logging(app)

    # Blueprints registrieren
    from app.main import main
    app.register_blueprint(main)

    from app.main.formcenter import formcenter
    app.register_blueprint(formcenter, url_prefix='/formcenter')

    from app.auth import auth
    app.register_blueprint(auth)

    from app import errors
    app.register_blueprint(errors.error)

    # Security Headers für alle Responses
    @app.after_request
    def add_security_headers(response):
        # Content Security Policy
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        # Permissions Policy (ersetzt Feature-Policy)
        response.headers['Permissions-Policy'] = (
            'geolocation=(), microphone=(), camera=()'
        )

        return response

    @app.before_request
    def maintenance_mode():
        # If maintenance mode is enabled, return a 503
        if eval_bool_env_var(app.config["MAINTENANCE_MODE"]):
            abort(503)

    return app


def configure_logging(app):
    """Konfiguriert das Logging-System für die Anwendung"""
    # Nur wenn nicht im Debug-Modus
    if not app.debug and not app.testing:
        # Log-Verzeichnis erstellen falls nicht vorhanden
        if not os.path.exists('logs'):
            os.mkdir('logs')

        # Rotating File Handler (max 10MB, 10 Backups)
        file_handler = RotatingFileHandler(
            'logs/fahrverein.log',
            maxBytes=10240000,
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s '
            '[in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info('Fahrverein Planetal Startup')
