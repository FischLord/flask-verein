from flask import render_template, redirect, url_for, flash, abort
from flask_login import login_user, logout_user, login_required
from app.auth.forms import LoginForm
from app.auth import auth
from app.models import Users
from app import db, limiter

from app.modules.util.decorators import redirect_if_already_authenticated


@auth.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute", error_message="Zu viele Login-Versuche. Bitte warten.")
@redirect_if_already_authenticated
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(email=form.email.data).first()

        if user is None or not user.check_password(form.password.data):
            flash("Ungültige Anmeldedaten", "warning")
            return redirect(url_for("auth.login"))

        login_user(user)
        return redirect(url_for("main.index"))

    return render_template("auth/login.html", title="Anmelden", form=form)


@auth.route("/register", methods=["GET", "POST"])
def register():
    """
    Registrierung ist deaktiviert.
    Admin-Benutzer werden über CLI erstellt: flask admin create
    """
    flash("Die Registrierung ist deaktiviert. Bitte wenden Sie sich an den Administrator.", "info")
    return redirect(url_for("auth.login"))


@auth.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Sie wurden abgemeldet", "success")
    return redirect(url_for("auth.login"))
