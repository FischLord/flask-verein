from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    DateField,
    TextAreaField,
    BooleanField,
    SubmitField,
)
from wtforms.validators import DataRequired, Length, Optional


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


class ActionForm(FlaskForm):
    """
    Feldloses Formular – liefert nur das CSRF-Token für
    POST-Aktionen ohne Eingabefelder (Löschen, Veröffentlicht
    umschalten).
    """

    submit = SubmitField("Bestätigen")
