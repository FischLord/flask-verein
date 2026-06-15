from flask_wtf import FlaskForm
from wtforms import EmailField, StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length


class RegistrationForm(FlaskForm):
    first_name = StringField(
        "Vorname", validators=[DataRequired(), Length(min=2, max=30)]
    )
    last_name = StringField(
        "Nachname", validators=[DataRequired(), Length(min=2, max=30)]
    )
    email = EmailField("E-Mail", validators=[DataRequired(), Email()])
    password = PasswordField("Passwort", validators=[DataRequired()])
    repeat_password = PasswordField(
        "Passwort wiederholen", validators=[DataRequired()]
    )
    submit = SubmitField("Registrieren")


class LoginForm(FlaskForm):
    email = EmailField("E-Mail", validators=[DataRequired(), Email()])
    password = PasswordField("Passwort", validators=[DataRequired()])
    submit = SubmitField("Anmelden")
