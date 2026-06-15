from flask import render_template, redirect, url_for, flash, abort
from flask_login import login_required

from app import db
from app.admin import admin
from app.admin.forms import TerminForm, ActionForm
from app.models import Termin
from app.modules.util.html import clean_html


@admin.route("/")
@login_required
def index():
    """Einstieg in den Verwaltungsbereich (Übersicht/Kacheln)."""
    return render_template(
        "admin/index.html", title="Übersicht"
    )


@admin.route("/termine")
@login_required
def termine_list():
    """Liste aller Termine mit Status und Aktionen."""
    termine = Termin.query.order_by(Termin.datum.desc()).all()
    return render_template(
        "admin/termine/list.html",
        title="Termine",
        termine=termine,
        action_form=ActionForm(),
    )


@admin.route("/termine/neu", methods=["GET", "POST"])
@login_required
def termin_neu():
    """Neuen Termin anlegen."""
    form = TerminForm()
    if form.validate_on_submit():
        termin = Termin(
            titel=form.titel.data,
            datum=form.datum.data,
            uhrzeit=form.uhrzeit.data or None,
            ort=form.ort.data or None,
            beschreibung=clean_html(form.beschreibung.data),
            veroeffentlicht=form.veroeffentlicht.data,
        )
        db.session.add(termin)
        db.session.commit()
        flash("Termin wurde angelegt.", "success")
        return redirect(url_for("admin.termine_list"))

    return render_template(
        "admin/termine/form.html",
        title="Termin anlegen",
        form=form,
        modus="neu",
    )


@admin.route("/termine/<int:termin_id>/bearbeiten",
             methods=["GET", "POST"])
@login_required
def termin_bearbeiten(termin_id):
    """Bestehenden Termin bearbeiten."""
    termin = db.session.get(Termin, termin_id)
    if termin is None:
        abort(404)

    form = TerminForm(obj=termin)
    if form.validate_on_submit():
        termin.titel = form.titel.data
        termin.datum = form.datum.data
        termin.uhrzeit = form.uhrzeit.data or None
        termin.ort = form.ort.data or None
        termin.beschreibung = clean_html(form.beschreibung.data)
        termin.veroeffentlicht = form.veroeffentlicht.data
        db.session.commit()
        flash("Termin wurde gespeichert.", "success")
        return redirect(url_for("admin.termine_list"))

    return render_template(
        "admin/termine/form.html",
        title="Termin bearbeiten",
        form=form,
        modus="bearbeiten",
        termin=termin,
    )


@admin.route("/termine/<int:termin_id>/veroeffentlichen",
             methods=["POST"])
@login_required
def termin_veroeffentlichen(termin_id):
    """Veröffentlicht-Status umschalten (CSRF-geschützt, nur POST)."""
    termin = db.session.get(Termin, termin_id)
    if termin is None:
        abort(404)

    form = ActionForm()
    if not form.validate_on_submit():
        abort(400)

    termin.veroeffentlicht = not termin.veroeffentlicht
    db.session.commit()
    if termin.veroeffentlicht:
        flash("Termin ist jetzt öffentlich sichtbar.", "success")
    else:
        flash("Termin ist jetzt verborgen.", "success")
    return redirect(url_for("admin.termine_list"))


@admin.route("/termine/<int:termin_id>/loeschen",
             methods=["GET", "POST"])
@login_required
def termin_loeschen(termin_id):
    """Termin löschen – mit Bestätigungsseite (GET) und POST-Aktion."""
    termin = db.session.get(Termin, termin_id)
    if termin is None:
        abort(404)

    form = ActionForm()
    if form.validate_on_submit():
        db.session.delete(termin)
        db.session.commit()
        flash("Termin wurde gelöscht.", "success")
        return redirect(url_for("admin.termine_list"))

    return render_template(
        "admin/termine/loeschen.html",
        title="Termin löschen",
        termin=termin,
        form=form,
    )
