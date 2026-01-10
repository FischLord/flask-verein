import os
import secrets
import pathlib
from datetime import timedelta

basedir = pathlib.Path(__file__).parent.absolute()


class Config(object):
    """
    Config values for the application (used by Flask and third-party packages).

    Values are set in the `.env` file. If no `.env` file is found,
    it will default use the default values below (where applicable).
    """

    # Flask Core
    FLASK_APP = "app.py"
    SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)

    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL"
    ) or "sqlite:///" + os.path.join(basedir, "app.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Application
    APP_NAME = os.environ.get("APP_NAME") or "Fahrverein Planetal e.V."
    BASE_URL = os.environ.get("BASE_URL") or "https://fahrverein-planetal.de"
    MAINTENANCE_MODE = os.environ.get("MAINTENANCE_MODE") or False

    # Session Security
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "True").lower() == "true"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)

    # Rate Limiting
    RATELIMIT_ENABLED = os.environ.get("RATELIMIT_ENABLED", "True").lower() == "true"
    RATELIMIT_DEFAULT = "200 per day, 50 per hour"
    RATELIMIT_STORAGE_URL = "memory://"
    RATELIMIT_HEADERS_ENABLED = True
