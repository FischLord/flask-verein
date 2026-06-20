"""
Formulare des oeffentlichen Bereichs (main).
--------------------------------------------

Aktuell: Kontaktformular mit serverseitiger Validierung, CSRF-Schutz
(Flask-WTF) und einem versteckten Honeypot-Feld gegen einfache Bots.
"""
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Email, Length, ValidationError


class ContactForm(FlaskForm):
    name = StringField(
        "Name",
        validators=[DataRequired(message="Bitte gib deinen Namen an."),
                    Length(min=2, max=80)],
    )
    email = StringField(
        "E-Mail",
        validators=[DataRequired(message="Bitte gib deine E-Mail an."),
                    Email(message="Bitte eine gültige E-Mail-Adresse angeben."),
                    Length(max=120)],
    )
    betreff = StringField(
        "Betreff",
        validators=[DataRequired(message="Bitte gib einen Betreff an."),
                    Length(min=3, max=120)],
    )
    nachricht = TextAreaField(
        "Nachricht",
        validators=[DataRequired(message="Bitte schreib uns ein paar Zeilen."),
                    Length(min=10, max=5000)],
    )
    # Honeypot: fuer Menschen unsichtbar (CSS), Bots fuellen es oft aus.
    # Heisst bewusst neutral ("website"), damit Bots es ansteuern.
    website = StringField("Website")

    submit = SubmitField("Nachricht senden")

    def validate_website(self, field):
        """Honeypot: Wenn ausgefuellt, als Spam behandeln."""
        if field.data:
            raise ValidationError("Spam erkannt.")
