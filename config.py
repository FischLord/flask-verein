import os
import pathlib

basedir = pathlib.Path(__file__).parent.absolute()


def _eval_bool(value, default=False):
    """Interpretiert gaengige Wahrheits-Strings aus .env als bool."""
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "t", "yes", "on"}


class Config(object):
    """
    Config values for the application (used by Flask and third-party packages).

    Values are set in the `.env` file. If no `.env` file is found,
    it will default use the default values below (where applicable).
    """

    FLASK_APP = "app.py"
    SECRET_KEY = os.environ.get("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL"
    ) or "sqlite:///" + os.path.join(basedir, "app.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    APP_NAME = os.environ.get("APP_NAME") or "Fahrverein Planetal e.V."
    MAINTENANCE_MODE = os.environ.get("MAINTENANCE_MODE") or False
    REGISTRATION_ENABLED = os.environ.get("REGISTRATION_ENABLED") or False

    # Datei-Uploads (CMS). UPLOAD_FOLDER wird in der App-Factory auf einen
    # absoluten Pfad (app/static/uploads) gesetzt, wenn hier nicht via
    # Umgebungsvariable überschrieben.
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER")
    MAX_CONTENT_LENGTH = int(
        os.environ.get("MAX_CONTENT_LENGTH") or 8 * 1024 * 1024
    )

    # --- E-Mail-Versand (Kontaktformular) -------------------------------
    # Werte aus .env. Ohne MAIL_SERVER ist der Versand deaktiviert; das
    # Kontaktformular zeigt dann einen freundlichen Fallback (mailto).
    MAIL_SERVER = os.environ.get("MAIL_SERVER")
    MAIL_PORT = int(os.environ.get("MAIL_PORT") or 587)
    MAIL_USE_TLS = _eval_bool(os.environ.get("MAIL_USE_TLS"), default=True)
    MAIL_USE_SSL = _eval_bool(os.environ.get("MAIL_USE_SSL"), default=False)
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    # Absender (Default = MAIL_USERNAME) und Empfaenger der Anfragen.
    MAIL_DEFAULT_SENDER = (
        os.environ.get("MAIL_DEFAULT_SENDER")
        or os.environ.get("MAIL_USERNAME")
    )
    CONTACT_RECIPIENT = (
        os.environ.get("CONTACT_RECIPIENT") or "fvplanetal@web.de"
    )
