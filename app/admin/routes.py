from flask_login import login_required

from app.admin import admin


@admin.route("/")
@login_required
def index():
    """Übergabe-Skelett (Phase 0). Ab Phase 1 baut der admin-Agent hier
    die login-geschützten CRUD-Ansichten aus."""
    return (
        "<h1>Admin-Bereich</h1>"
        "<p>Platzhalter – CRUD folgt ab Phase 1.</p>"
    )
