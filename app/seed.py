"""
Flask-CLI – Seed der oeffentlichen Stammdaten (Vorstand & Kutschertag).
-----------------------------------------------------------------------

Die Datenbank ist bewusst nicht im Repo (``.gitignore``: ``*.db``). Damit
ein frisch aufgesetztes System dennoch reproduzierbar mit den oeffentlich
bekannten Stammdaten startet, legt dieser Befehl sie idempotent an:

- Vorstand (6 Mitglieder, Stand 2026) mit Funktion, Reihenfolge, Spruch
  und – nur wo oeffentlich gewuenscht – Telefon.
- Reckahner Kutschertag 2026 (12.09.2026) als Termin.

Idempotenz: Bereits vorhandene Eintraege (per Name bzw. Datum erkannt)
werden uebersprungen, nie ueberschrieben oder doppelt angelegt.

Aufruf::

    flask --app app seed-stammdaten            # legt fehlende Daten an
    flask --app app seed-stammdaten --dry-run  # nur Vorschau
"""
from datetime import date

import click
from flask.cli import with_appcontext

from app import db
from app.models import Termin, Vorstandsmitglied

# Vorstand laut Live-Seite (Stand 2026). Telefon nur dort, wo oeffentlich
# erwuenscht (DSGVO-bewusst). E-Mails/Fotos folgen spaeter ueber das Admin.
VORSTAND = [
    {
        "name": "Jacquelin Bredt",
        "funktion": "Vorsitzende",
        "reihenfolge": 1,
        "telefon": "0162 9177860",
        "spruch": (
            "Diejenige, die den Laden zusammenhält – mit Charme und einem "
            "Telefon in der Hand."
        ),
    },
    {
        "name": "Denise Matthe",
        "funktion": "Stellvertretende Vorsitzende",
        "reihenfolge": 2,
        "spruch": (
            "Die ruhige Hand, die das Ruder übernimmt, wenn's mal stürmisch "
            "wird."
        ),
    },
    {
        "name": "Stefanie-Kirstin Sailer",
        "funktion": "Kassenwart",
        "reihenfolge": 3,
        "spruch": (
            "Die, die weiß, wo jeder Cent steckt – und immer den Überblick "
            "behält."
        ),
    },
    {
        "name": "Janneck Lehmann",
        "funktion": "Jugendwart & Internetseite",
        "reihenfolge": 4,
        "spruch": "Der Jugendflüsterer und Web-Guru – bringt alles ins Netz.",
    },
    {
        "name": "Sarah Hohmann",
        "funktion": "Schriftführer",
        "reihenfolge": 5,
        "spruch": "Schreibt schneller als die meisten reden können.",
    },
    {
        "name": "Christina Herrmann",
        "funktion": "Facebook & Social Media",
        "reihenfolge": 6,
        "spruch": "Teilt alles – und findet immer den perfekten Hashtag.",
    },
]

# Naechster grosser Vereinstermin.
KUTSCHERTAG = {
    "titel": "Reckahner Kutschertag 2026",
    "datum": date(2026, 9, 12),
    "uhrzeit": "10:00",
    "ort": (
        "Reitplatz Reckahn, Krahner Straße 01, "
        "14797 Kloster Lehnin OT Reckahn"
    ),
    "beschreibung": (
        "<p>Unser großes Vereinshighlight: Dressur- und Hindernisfahren, "
        "Showprogramm rund um Pferd und Kutsche, dazu Speisen und Getränke "
        "für die ganze Familie. Alle Pferdefreunde und Gäste sind herzlich "
        "willkommen!</p>"
    ),
}


@click.command("seed-stammdaten")
@click.option(
    "--dry-run", is_flag=True,
    help="Nur anzeigen, was angelegt wuerde; nichts schreiben.",
)
@with_appcontext
def seed_stammdaten(dry_run):
    """Legt Vorstand & Kutschertag-Termin idempotent an."""
    neu_vorstand = 0
    for daten in VORSTAND:
        if Vorstandsmitglied.query.filter_by(name=daten["name"]).first():
            click.echo(f"  · Vorstand vorhanden: {daten['name']}")
            continue
        click.secho(f"  + Vorstand neu:      {daten['name']}", fg="green")
        neu_vorstand += 1
        if not dry_run:
            db.session.add(Vorstandsmitglied(sichtbar=True, **daten))

    neu_termin = 0
    if Termin.query.filter_by(datum=KUTSCHERTAG["datum"]).first():
        click.echo(f"  · Termin vorhanden:  {KUTSCHERTAG['titel']}")
    else:
        click.secho(f"  + Termin neu:        {KUTSCHERTAG['titel']}", fg="green")
        neu_termin += 1
        if not dry_run:
            db.session.add(Termin(veroeffentlicht=True, **KUTSCHERTAG))

    if dry_run:
        click.secho(
            f"\n--dry-run: Es wurde NICHTS geschrieben "
            f"({neu_vorstand} Vorstand, {neu_termin} Termin offen).",
            fg="yellow", bold=True,
        )
        return

    db.session.commit()
    click.secho(
        f"\nSeed fertig: {neu_vorstand} Vorstandsmitglieder, "
        f"{neu_termin} Termin angelegt.",
        fg="green", bold=True,
    )
