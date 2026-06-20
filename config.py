import os
import pathlib

basedir = pathlib.Path(__file__).parent.absolute()


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
