import os
from datetime import date

from flask import (
    render_template, redirect, url_for, flash, abort, current_app, request,
)
from flask_login import login_required

from app import db
from app.admin import admin
from app.admin.forms import (
    TerminForm, VorstandForm, BerichtForm, BildUploadForm, BildForm,
    ActionForm,
)
from app.models import (
    Termin, Vorstandsmitglied, Bericht, BerichtBild,
)
from app.modules.util.html import clean_html
from app.modules.util.images import (
    save_image, delete_image, ImageValidationError,
)

# Unterordner unter UPLOAD_FOLDER für Uploads. In den DB-Spalten wird
# jeweils NUR der Dateiname abgelegt (Konvention mit public:
# public rendert uploads/<typ>/<dateiname>).
VORSTAND_SUBDIR = "vorstand"
BERICHTE_SUBDIR = "berichte"


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


# ---------------------------------------------------------------------
# Erlebnisberichte
# ---------------------------------------------------------------------

def _add_bilder(files, bericht):
    """
    Speichert hochgeladene Dateien als BerichtBild-Einträge.

    :return: (anzahl_ok, fehlerliste) – fehlerhafte/ungültige Dateien
             werden übersprungen, gültige gespeichert.
    """
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    start = max((b.reihenfolge for b in bericht.bilder), default=-1) + 1
    anzahl_ok = 0
    fehler = []
    for datei in files:
        if not datei or not getattr(datei, "filename", ""):
            continue
        try:
            gespeichert = save_image(
                datei, upload_folder, subdir=BERICHTE_SUBDIR
            )
        except ImageValidationError as exc:
            fehler.append(f"{datei.filename}: {exc}")
            continue
        bericht.bilder.append(
            BerichtBild(
                dateiname=os.path.basename(gespeichert),
                reihenfolge=start,
            )
        )
        start += 1
        anzahl_ok += 1
    return anzahl_ok, fehler


@admin.route("/berichte")
@login_required
def berichte_list():
    """Liste aller Erlebnisberichte."""
    berichte = Bericht.query.order_by(
        Bericht.jahr.desc(),
        Bericht.reihenfolge.asc(),
        Bericht.titel.asc(),
    ).all()
    return render_template(
        "admin/berichte/list.html",
        title="Erlebnisberichte",
        berichte=berichte,
        action_form=ActionForm(),
    )


@admin.route("/berichte/neu", methods=["GET", "POST"])
@login_required
def bericht_neu():
    """Neuen Bericht anlegen (Bilder folgen auf der Bearbeiten-Seite)."""
    form = BerichtForm()
    if form.validate_on_submit():
        bericht = Bericht(
            jahr=form.jahr.data,
            titel=form.titel.data,
            text=clean_html(form.text.data),
            reihenfolge=form.reihenfolge.data or 0,
            veroeffentlicht=form.veroeffentlicht.data,
        )
        db.session.add(bericht)
        db.session.commit()
        flash(
            "Bericht wurde angelegt. Jetzt kannst du Bilder hinzufügen.",
            "success",
        )
        return redirect(
            url_for("admin.bericht_bearbeiten", bericht_id=bericht.id)
        )

    if request.method == "GET":
        form.jahr.data = date.today().year
    return render_template(
        "admin/berichte/form.html",
        title="Bericht anlegen",
        form=form,
        modus="neu",
    )


@admin.route("/berichte/<int:bericht_id>/bearbeiten",
             methods=["GET", "POST"])
@login_required
def bericht_bearbeiten(bericht_id):
    """Bericht-Texte bearbeiten und Bilder verwalten."""
    bericht = db.session.get(Bericht, bericht_id)
    if bericht is None:
        abort(404)

    form = BerichtForm(obj=bericht)
    if form.validate_on_submit():
        bericht.jahr = form.jahr.data
        bericht.titel = form.titel.data
        bericht.text = clean_html(form.text.data)
        bericht.reihenfolge = form.reihenfolge.data or 0
        bericht.veroeffentlicht = form.veroeffentlicht.data
        db.session.commit()
        flash("Bericht wurde gespeichert.", "success")
        return redirect(
            url_for("admin.bericht_bearbeiten", bericht_id=bericht.id)
        )

    return render_template(
        "admin/berichte/bearbeiten.html",
        title="Bericht bearbeiten",
        form=form,
        bericht=bericht,
        upload_form=BildUploadForm(),
        bild_form=BildForm(),
        action_form=ActionForm(),
    )


@admin.route("/berichte/<int:bericht_id>/bilder", methods=["POST"])
@login_required
def bericht_bilder_hinzufuegen(bericht_id):
    """Mehrere Bilder zu einem Bericht hochladen (CSRF, nur POST)."""
    bericht = db.session.get(Bericht, bericht_id)
    if bericht is None:
        abort(404)

    form = BildUploadForm()
    if not form.validate_on_submit():
        abort(400)

    anzahl_ok, fehler = _add_bilder(form.bilder.data or [], bericht)
    if anzahl_ok:
        db.session.commit()
        flash(f"{anzahl_ok} Bild(er) hinzugefügt.", "success")
    if fehler:
        flash(
            "Einige Dateien wurden abgelehnt: " + "; ".join(fehler),
            "danger",
        )
    if not anzahl_ok and not fehler:
        flash("Keine Datei ausgewählt.", "warning")
    return redirect(
        url_for("admin.bericht_bearbeiten", bericht_id=bericht.id)
    )


@admin.route("/berichte/bild/<int:bild_id>/aktualisieren",
             methods=["POST"])
@login_required
def bericht_bild_aktualisieren(bild_id):
    """Alt-Text/Reihenfolge eines Bildes aktualisieren."""
    bild = db.session.get(BerichtBild, bild_id)
    if bild is None:
        abort(404)

    form = BildForm()
    if not form.validate_on_submit():
        abort(400)

    bild.alt_text = form.alt_text.data or None
    bild.reihenfolge = form.reihenfolge.data or 0
    db.session.commit()
    flash("Bild wurde aktualisiert.", "success")
    return redirect(
        url_for("admin.bericht_bearbeiten", bericht_id=bild.bericht_id)
    )


@admin.route("/berichte/bild/<int:bild_id>/loeschen", methods=["POST"])
@login_required
def bericht_bild_loeschen(bild_id):
    """Einzelnes Bild löschen (Datei + Datensatz)."""
    bild = db.session.get(BerichtBild, bild_id)
    if bild is None:
        abort(404)

    form = ActionForm()
    if not form.validate_on_submit():
        abort(400)

    bericht_id = bild.bericht_id
    delete_image(
        os.path.join(BERICHTE_SUBDIR, bild.dateiname),
        current_app.config["UPLOAD_FOLDER"],
    )
    db.session.delete(bild)
    db.session.commit()
    flash("Bild wurde gelöscht.", "success")
    return redirect(
        url_for("admin.bericht_bearbeiten", bericht_id=bericht_id)
    )


@admin.route("/berichte/<int:bericht_id>/veroeffentlichen",
             methods=["POST"])
@login_required
def bericht_veroeffentlichen(bericht_id):
    """Veröffentlicht-Status umschalten (CSRF, nur POST)."""
    bericht = db.session.get(Bericht, bericht_id)
    if bericht is None:
        abort(404)

    form = ActionForm()
    if not form.validate_on_submit():
        abort(400)

    bericht.veroeffentlicht = not bericht.veroeffentlicht
    db.session.commit()
    if bericht.veroeffentlicht:
        flash("Bericht ist jetzt öffentlich sichtbar.", "success")
    else:
        flash("Bericht ist jetzt verborgen.", "success")
    return redirect(url_for("admin.berichte_list"))


@admin.route("/berichte/<int:bericht_id>/loeschen",
             methods=["GET", "POST"])
@login_required
def bericht_loeschen(bericht_id):
    """Bericht inkl. aller Bilder löschen (Bestätigungsseite + POST)."""
    bericht = db.session.get(Bericht, bericht_id)
    if bericht is None:
        abort(404)

    form = ActionForm()
    if form.validate_on_submit():
        upload_folder = current_app.config["UPLOAD_FOLDER"]
        for bild in list(bericht.bilder):
            delete_image(
                os.path.join(BERICHTE_SUBDIR, bild.dateiname), upload_folder
            )
        db.session.delete(bericht)
        db.session.commit()
        flash("Bericht wurde gelöscht.", "success")
        return redirect(url_for("admin.berichte_list"))

    return render_template(
        "admin/berichte/loeschen.html",
        title="Bericht löschen",
        bericht=bericht,
        form=form,
    )
