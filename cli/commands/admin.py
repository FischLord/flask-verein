import click
import sys
import os

# Füge das Projekt-Root zum Pfad hinzu
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from util import ClickUtils


@click.group("admin")
def admin():
    """Admin-Benutzerverwaltung"""
    pass


@admin.command("create")
@click.option("--email", "-e", prompt="E-Mail", help="E-Mail-Adresse des Admins")
@click.option("--first-name", "-f", prompt="Vorname", help="Vorname des Admins")
@click.option("--last-name", "-l", prompt="Nachname", help="Nachname des Admins")
@click.option(
    "--password", "-p",
    prompt="Passwort",
    hide_input=True,
    confirmation_prompt=True,
    help="Passwort für den Admin"
)
def create_admin(email: str, first_name: str, last_name: str, password: str):
    """Erstellt einen neuen Admin-Benutzer"""

    spinner = ClickUtils.Spinner("Erstelle Admin-Benutzer...")
    spinner.start()

    try:
        # Flask-App initialisieren (für Datenbankzugriff)
        from app import create_app, db
        from app.models import Users

        app = create_app()

        with app.app_context():
            # Prüfen ob E-Mail bereits existiert
            existing_user = Users.query.filter_by(email=email).first()
            if existing_user:
                spinner.stop()
                if existing_user.is_admin:
                    click.secho(f"Fehler: Ein Admin mit dieser E-Mail existiert bereits.", fg="red")
                else:
                    # User existiert, aber ist kein Admin - upgraden
                    click.secho(f"Benutzer existiert bereits. Upgrade zu Admin? (y/n): ", fg="yellow", nl=False)
                    if click.getchar().lower() == 'y':
                        existing_user.is_admin = True
                        db.session.commit()
                        click.echo()
                        click.secho(f"Benutzer {email} wurde zum Admin befördert.", fg="green")
                    else:
                        click.echo()
                        click.secho("Abgebrochen.", fg="yellow")
                return

            # Passwort-Stärke prüfen
            from app.modules.util.auth import check_password_strength
            if not check_password_strength(password):
                spinner.stop()
                click.secho(
                    "Fehler: Passwort ist zu schwach. "
                    "Mindestens 8 Zeichen, ein Großbuchstabe, keine Wiederholungen.",
                    fg="red"
                )
                return

            # Neuen Admin erstellen
            admin_user = Users(
                email=email,
                first_name=first_name,
                last_name=last_name,
                is_admin=True
            )
            admin_user.set_password(password)

            db.session.add(admin_user)
            db.session.commit()

            spinner.stop()
            click.secho(f"Admin-Benutzer erfolgreich erstellt!", fg="green")
            click.secho(f"  E-Mail: {email}", fg="white")
            click.secho(f"  Name: {first_name} {last_name}", fg="white")

    except Exception as e:
        spinner.stop()
        click.secho(f"Fehler: {str(e)}", fg="red")
        raise


@admin.command("list")
def list_admins():
    """Zeigt alle Admin-Benutzer an"""

    try:
        from app import create_app
        from app.models import Users

        app = create_app()

        with app.app_context():
            admins = Users.query.filter_by(is_admin=True).all()

            if not admins:
                click.secho("Keine Admin-Benutzer gefunden.", fg="yellow")
                click.secho("Erstellen Sie einen mit: python -m cli.kettle admin create", fg="white")
                return

            click.secho(f"\nAdmin-Benutzer ({len(admins)}):", fg="green")
            click.secho("-" * 50, fg="white")

            for admin in admins:
                click.secho(
                    f"  {admin.id}: {admin.first_name} {admin.last_name} <{admin.email}>",
                    fg="white"
                )

            click.secho("-" * 50, fg="white")

    except Exception as e:
        click.secho(f"Fehler: {str(e)}", fg="red")


@admin.command("revoke")
@click.argument("email")
def revoke_admin(email: str):
    """Entzieht einem Benutzer die Admin-Rechte"""

    try:
        from app import create_app, db
        from app.models import Users

        app = create_app()

        with app.app_context():
            user = Users.query.filter_by(email=email).first()

            if not user:
                click.secho(f"Fehler: Kein Benutzer mit E-Mail {email} gefunden.", fg="red")
                return

            if not user.is_admin:
                click.secho(f"Benutzer {email} ist kein Admin.", fg="yellow")
                return

            # Prüfen ob es der letzte Admin ist
            admin_count = Users.query.filter_by(is_admin=True).count()
            if admin_count <= 1:
                click.secho(
                    "Fehler: Kann letzten Admin nicht entfernen. "
                    "Erstellen Sie zuerst einen anderen Admin.",
                    fg="red"
                )
                return

            user.is_admin = False
            db.session.commit()

            click.secho(f"Admin-Rechte von {email} wurden entzogen.", fg="green")

    except Exception as e:
        click.secho(f"Fehler: {str(e)}", fg="red")
