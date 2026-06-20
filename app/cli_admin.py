"""
Flask-CLI - Verwaltung von Login-Konten (Admin/Verwaltung).
-----------------------------------------------------------

Konten fuer den geschuetzten Verwaltungsbereich anlegen oder das
Passwort eines bestehenden Kontos neu setzen. So bleibt die
Konto-Verwaltung reproduzierbar (die SQLite-DB ist gitignored).

Aufruf::

    # Neues Konto anlegen oder Passwort aktualisieren
    flask --app app create-admin --email admin@example.com --password "Geheim123"

    # Vor- und Nachname optional setzen
    flask --app app create-admin -e a@b.de -p "Geheim123" --first Max --last Muster

Hinweise:
- Ist die E-Mail bereits vergeben, wird das Passwort (und optional der
  Name) des bestehenden Kontos aktualisiert - kein Duplikat.
- Das Passwort wird ausschliesslich als Hash gespeichert.
"""
import click
from flask.cli import with_appcontext

from app import db
from app.models import Users


@click.command("create-admin")
@click.option("--email", "-e", required=True, help="E-Mail (Login-Name).")
@click.option(
    "--password", "-p", required=True,
    help="Passwort (wird nur als Hash gespeichert).",
)
@click.option("--first", "first_name", default=None, help="Vorname (optional).")
@click.option("--last", "last_name", default=None, help="Nachname (optional).")
@with_appcontext
def create_admin(email, password, first_name, last_name):
    """Legt ein Verwaltungs-Konto an oder setzt dessen Passwort neu."""
    email = email.strip().lower()
    user = Users.query.filter_by(email=email).first()

    if user is None:
        user = Users(email=email)
        if first_name:
            user.first_name = first_name
        if last_name:
            user.last_name = last_name
        user.set_password(password)
        db.session.add(user)
        action = "angelegt"
    else:
        if first_name:
            user.first_name = first_name
        if last_name:
            user.last_name = last_name
        user.set_password(password)
        action = "aktualisiert"

    db.session.commit()
    click.echo(f"Konto {action}: {email}")
