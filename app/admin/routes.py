import os

from flask import (
    render_template, redirect, url_for, flash, abort, current_app,
)
from flask_login import login_required

from app import db
from app.admin import admin
from app.admin.forms import TerminForm, VorstandForm, ActionForm
from app.models import Termin, Vorstandsmitglied
from app.modules.util.html import clean_html
from app.modules.util.images import (
    save_image, delete_image, ImageValidationError,
)

# Unterordner unter UPLOAD_FOLDER für Vorstands-Fotos. In der Spalte
# `foto` wird NUR der Dateiname abgelegt (Konvention mit public:
# public rendert uploads/vorstand/<foto>).
VORSTAND_SUBDIR = "vorstand"


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


# ---------------------------------------------------------------------
# Vorstand
# ---------------------------------------------------------------------

def _store_foto(form, mitglied):
    """
    Verarbeitet das Foto-Feld eines VorstandForm.

    Lädt ggf. ein neues Foto hoch (ersetzt das alte) oder entfernt das
    vorhandene Foto auf Wunsch. Speichert in der Spalte ``foto`` nur den
    Dateinamen.

    :raises ImageValidationError: bei ungültiger Bilddatei
    """
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    datei = form.foto.data

    if datei and getattr(datei, "filename", ""):
        # Neues Foto -> validieren/speichern, danach altes löschen.
        gespeichert = save_image(
            datei, upload_folder, subdir=VORSTAND_SUBDIR
        )
        if mitglied.foto:
            delete_image(
                os.path.join(VORSTAND_SUBDIR, mitglied.foto), upload_folder
            )
        mitglied.foto = os.path.basename(gespeichert)
    elif form.foto_entfernen.data and mitglied.foto:
        delete_image(
            os.path.join(VORSTAND_SUBDIR, mitglied.foto), upload_folder
        )
        mitglied.foto = None


def _apply_vorstand_fields(form, mitglied):
    """Überträgt die Textfelder des Formulars auf das Modell."""
    mitglied.name = form.name.data
    mitglied.funktion = form.funktion.data
    mitglied.reihenfolge = (
        form.reihenfolge.data if form.reihenfolge.data is not None else 0
    )
    mitglied.spruch = form.spruch.data or None
    mitglied.telefon = form.telefon.data or None
    mitglied.email = form.email.data or None
    mitglied.sichtbar = form.sichtbar.data


@admin.route("/vorstand")
@login_required
def vorstand_list():
    """Liste aller Vorstandsmitglieder, sortiert nach Reihenfolge."""
    mitglieder = Vorstandsmitglied.query.order_by(
        Vorstandsmitglied.reihenfolge.asc(), Vorstandsmitglied.name.asc()
    ).all()
    return render_template(
        "admin/vorstand/list.html",
        title="Vorstand",
        mitglieder=mitglieder,
        action_form=ActionForm(),
    )


@admin.route("/vorstand/neu", methods=["GET", "POST"])
@login_required
def vorstand_neu():
    """Neues Vorstandsmitglied anlegen."""
    form = VorstandForm()
    if form.validate_on_submit():
        mitglied = Vorstandsmitglied()
        _apply_vorstand_fields(form, mitglied)
        try:
            _store_foto(form, mitglied)
        except ImageValidationError as exc:
            flash(str(exc), "danger")
            return render_template(
                "admin/vorstand/form.html",
                title="Vorstandsmitglied anlegen",
                form=form,
                modus="neu",
            )
        db.session.add(mitglied)
        db.session.commit()
        flash("Vorstandsmitglied wurde angelegt.", "success")
        return redirect(url_for("admin.vorstand_list"))

    return render_template(
        "admin/vorstand/form.html",
        title="Vorstandsmitglied anlegen",
        form=form,
        modus="neu",
    )


@admin.route("/vorstand/<int:mitglied_id>/bearbeiten",
             methods=["GET", "POST"])
@login_required
def vorstand_bearbeiten(mitglied_id):
    """Vorstandsmitglied bearbeiten."""
    mitglied = db.session.get(Vorstandsmitglied, mitglied_id)
    if mitglied is None:
        abort(404)

    form = VorstandForm(obj=mitglied)
    if form.validate_on_submit():
        _apply_vorstand_fields(form, mitglied)
        try:
            _store_foto(form, mitglied)
        except ImageValidationError as exc:
            flash(str(exc), "danger")
            return render_template(
                "admin/vorstand/form.html",
                title="Vorstandsmitglied bearbeiten",
                form=form,
                modus="bearbeiten",
                mitglied=mitglied,
            )
        db.session.commit()
        flash("Vorstandsmitglied wurde gespeichert.", "success")
        return redirect(url_for("admin.vorstand_list"))

    return render_template(
        "admin/vorstand/form.html",
        title="Vorstandsmitglied bearbeiten",
        form=form,
        modus="bearbeiten",
        mitglied=mitglied,
    )


@admin.route("/vorstand/<int:mitglied_id>/sichtbar", methods=["POST"])
@login_required
def vorstand_sichtbar(mitglied_id):
    """Sichtbar-Status umschalten (CSRF-geschützt, nur POST)."""
    mitglied = db.session.get(Vorstandsmitglied, mitglied_id)
    if mitglied is None:
        abort(404)

    form = ActionForm()
    if not form.validate_on_submit():
        abort(400)

    mitglied.sichtbar = not mitglied.sichtbar
    db.session.commit()
    if mitglied.sichtbar:
        flash("Mitglied ist jetzt öffentlich sichtbar.", "success")
    else:
        flash("Mitglied ist jetzt verborgen.", "success")
    return redirect(url_for("admin.vorstand_list"))


@admin.route("/vorstand/<int:mitglied_id>/loeschen",
             methods=["GET", "POST"])
@login_required
def vorstand_loeschen(mitglied_id):
    """Vorstandsmitglied löschen (mit Bestätigungsseite + Foto)."""
    mitglied = db.session.get(Vorstandsmitglied, mitglied_id)
    if mitglied is None:
        abort(404)

    form = ActionForm()
    if form.validate_on_submit():
        if mitglied.foto:
            delete_image(
                os.path.join(VORSTAND_SUBDIR, mitglied.foto),
                current_app.config["UPLOAD_FOLDER"],
            )
        db.session.delete(mitglied)
        db.session.commit()
        flash("Vorstandsmitglied wurde gelöscht.", "success")
        return redirect(url_for("admin.vorstand_list"))

    return render_template(
        "admin/vorstand/loeschen.html",
        title="Vorstandsmitglied löschen",
        mitglied=mitglied,
        form=form,
    )
