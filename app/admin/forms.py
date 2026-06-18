from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (
    StringField,
    DateField,
    IntegerField,
    TextAreaField,
    BooleanField,
    MultipleFileField,
    SubmitField,
)
from wtforms.validators import (
    DataRequired,
    Length,
    Optional,
    Email,
    NumberRange,
)

from app.modules.util.images import ALLOWED_EXTENSIONS


class TerminForm(FlaskForm):
    """Anlegen/Bearbeiten eines Termins (Veranstaltung)."""

    titel = StringField(
        "Titel", validators=[DataRequired(), Length(min=2, max=120)]
    )
    datum = DateField("Datum", validators=[DataRequired()])
    uhrzeit = StringField(
        "Uhrzeit (optional)", validators=[Optional(), Length(max=20)]
    )
    ort = StringField(
        "Ort (optional)", validators=[Optional(), Length(max=200)]
    )
    # HTML aus dem WYSIWYG-Editor; wird serverseitig mit clean_html
    # bereinigt, bevor es gespeichert wird.
    beschreibung = TextAreaField("Beschreibung", validators=[Optional()])
    veroeffentlicht = BooleanField("Sofort veröffentlichen", default=True)
    submit = SubmitField("Speichern")


class VorstandForm(FlaskForm):
    """Anlegen/Bearbeiten eines Vorstandsmitglieds."""

    name = StringField(
        "Name", validators=[DataRequired(), Length(min=2, max=120)]
    )
    funktion = StringField(
        "Funktion", validators=[DataRequired(), Length(min=2, max=120)]
    )
    reihenfolge = IntegerField(
        "Reihenfolge",
        default=0,
        validators=[Optional(), NumberRange(min=0)],
    )
    # Kurzes Zitat – reiner Text (kein HTML), public rendert nl2br.
    spruch = TextAreaField(
        "Spruch / Zitat (optional)",
        validators=[Optional(), Length(max=500)],
    )
    telefon = StringField(
        "Telefon (optional)", validators=[Optional(), Length(max=50)]
    )
    email = StringField(
        "E-Mail (optional)",
        validators=[Optional(), Email(), Length(max=120)],
    )
    foto = FileField(
        "Foto (optional)",
        validators=[
            FileAllowed(
                sorted(ALLOWED_EXTENSIONS),
                "Nur Bilddateien: jpg, jpeg, png, webp, gif.",
            )
        ],
    )
    foto_entfernen = BooleanField("Vorhandenes Foto entfernen")
    sichtbar = BooleanField("Sichtbar auf der Website", default=True)
    submit = SubmitField("Speichern")


class BerichtForm(FlaskForm):
    """Anlegen/Bearbeiten eines Erlebnisberichts (ohne Bilder)."""

    jahr = IntegerField(
        "Jahr",
        validators=[DataRequired(), NumberRange(min=1900, max=2100)],
    )
    titel = StringField(
        "Titel", validators=[DataRequired(), Length(min=2, max=200)]
    )
    # HTML aus dem WYSIWYG-Editor; serverseitig mit clean_html bereinigt.
    text = TextAreaField("Text", validators=[Optional()])
    reihenfolge = IntegerField(
        "Reihenfolge",
        default=0,
        validators=[Optional(), NumberRange(min=0)],
    )
    veroeffentlicht = BooleanField("Sofort veröffentlichen", default=True)
    submit = SubmitField("Speichern")


class BildUploadForm(FlaskForm):
    """Mehrere Bilder zu einem Bericht hochladen."""

    bilder = MultipleFileField("Bilder hinzufügen")
    submit = SubmitField("Hochladen")


class BildForm(FlaskForm):
    """Bearbeiten eines einzelnen Bericht-Bilds (Alt-Text/Reihenfolge)."""

    alt_text = StringField(
        "Bildbeschreibung (Alt-Text)",
        validators=[Optional(), Length(max=255)],
    )
    reihenfolge = IntegerField(
        "Reihenfolge",
        default=0,
        validators=[Optional(), NumberRange(min=0)],
    )
    submit = SubmitField("Speichern")


class NewsForm(FlaskForm):
    """Anlegen/Bearbeiten eines News-/Info-Beitrags."""

    titel = StringField(
        "Titel", validators=[DataRequired(), Length(min=2, max=200)]
    )
    # Optionales URL-Kürzel; leer -> wird aus dem Titel erzeugt.
    slug = StringField(
        "URL-Kürzel (optional)", validators=[Optional(), Length(max=200)]
    )
    datum = DateField("Datum", validators=[Optional()])
    # HTML aus dem WYSIWYG-Editor; serverseitig mit clean_html bereinigt.
    inhalt = TextAreaField("Inhalt", validators=[Optional()])
    veroeffentlicht = BooleanField("Sofort veröffentlichen", default=True)
    submit = SubmitField("Speichern")


class ActionForm(FlaskForm):
    """
    Feldloses Formular – liefert nur das CSRF-Token für
    POST-Aktionen ohne Eingabefelder (Löschen, Veröffentlicht/
    Sichtbar umschalten).
    """

    submit = SubmitField("Bestätigen")
