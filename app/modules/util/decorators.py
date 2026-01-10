from functools import wraps
from flask import redirect, url_for, flash, abort
from flask_login import current_user


def redirect_if_already_authenticated(f):
    """
    Redirects to the index page if the user is already authenticated.

    :return: redirect to `main.index`
    """

    @wraps(f)
    def is_authenticated(*args, **kwargs):
        if current_user.is_authenticated:
            return redirect(url_for("main.index"))
        return f(*args, **kwargs)

    return is_authenticated


def admin_required(f):
    """
    Schützt eine Route, sodass nur Admins Zugriff haben.
    Leitet nicht-eingeloggte User zum Login weiter.
    Gibt 403 zurück für eingeloggte Nicht-Admins.

    Verwendung:
        @app.route('/admin')
        @login_required
        @admin_required
        def admin_panel():
            ...
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Bitte melden Sie sich an.", "warning")
            return redirect(url_for("auth.login"))

        if not current_user.is_admin:
            abort(403)

        return f(*args, **kwargs)

    return decorated_function
