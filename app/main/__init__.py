from flask import Blueprint

main = Blueprint("main", __name__)

# Import am Dateiende: routes.py importiert seinerseits "main" von hier,
# der Import registriert die Views am Blueprint (Flask-Standardmuster).
from app.main import routes  # noqa: E402,F401
