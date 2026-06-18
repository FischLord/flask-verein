"""

Flask-CLI – Importer für Alt-Erlebnisberichte.
----------------

Liest die historischen Berichte aus ``app/static/berichte/<jahr>/...``
und legt daraus ``Bericht``- und ``BerichtBild``-Datensätze an. Die
Quelldateien werden ausschließlich gelesen/kopiert, niemals verschoben
oder gelöscht.

Aufruf::

    flask --app app import-berichte --dry-run   # Vorschau, schreibt nichts
    flask --app app import-berichte             # echter Import

Logik (vgl. Task #8):
- Jahr-Ordner mit Event-Unterordnern -> je Unterordner ein Bericht
  (Titel = Unterordner-Name). Lose Bilder direkt im Jahr-Ordner werden
  zusätzlich an einen Jahres-Bericht ("Erlebnisbericht <jahr>") gehängt.
- Jahr-Ordner ohne Unterordner -> ein Jahres-Bericht.
- ``text.txt`` (Klartext) wird zu sicherem HTML (Absätze/<br>) und mit
  ``clean_html`` (bleach) bereinigt.
- Bilder: pro Motiv genau eins. Viele Ordner enthalten beide Varianten
  (z. B. ``image.jpg`` UND ``image.webp``); nach Stem dedupliziert,
  ``.webp`` bevorzugt. Jedes Bild wird auf die Maximalkante verkleinert,
  als WebP mit Zufalls-Basename unter ``UPLOAD_FOLDER/berichte/``
  abgelegt – dieselben Parameter wie ``app/modules/util/images.py``.

Schutz:
- ``--dry-run`` schreibt nichts (keine DB-Inserts, keine Dateien).
- Ohne ``--force`` bricht der echte Lauf ab, sobald bereits Berichte in
  der Datenbank existieren (Doppelimport-Schutz).
"""
import os
import re
import secrets

import click
from flask import current_app
from flask.cli import with_appcontext
from markupsafe import escape
from PIL import Image, UnidentifiedImageError

from app import db
from app.models import Bericht, BerichtBild
from app.modules.util.html import clean_html

# Quell-Unterordner unter app/static (wird nur gelesen).
SOURCE_SUBDIR = "berichte"
# Ziel-Unterordner unter UPLOAD_FOLDER (wie im Admin-Upload).
TARGET_SUBDIR = "berichte"

# Bild-Parameter – identisch zu app/modules/util/images.py.
MAX_EDGE = 1600
WEBP_QUALITY = 82
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
# Bei Doppelvarianten (gleicher Stem) bevorzugte Endung.
PREFERRED_EXT = ".webp"


def _natural_key(name: str):
    """Sortierschlüssel für natürliche Reihenfolge (image2 vor image10)."""
    return [
        int(token) if token.isdigit() else token.lower()
        for token in re.split(r"(\d+)", name)
    ]


def _text_to_html(raw: str) -> str:
    """
    Wandelt Klartext in sicheres HTML um.

    Leerzeilen trennen Absätze (``<p>``), einfache Zeilenumbrüche werden
    zu ``<br>``. Sonderzeichen werden escaped; abschließend bereinigt
    ``clean_html`` (bleach) das Ergebnis gegen die Allowlist.
    """
    raw = (raw or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    if not raw:
        return ""
    parts = []
    for block in re.split(r"\n\s*\n", raw):
        lines = [
            str(escape(line.strip()))
            for line in block.split("\n")
            if line.strip()
        ]
        if lines:
            parts.append("<p>" + "<br>".join(lines) + "</p>")
    return clean_html("".join(parts))


def _read_text_file(folder: str):
    """Liest ``text.txt`` aus ``folder`` (oder None, wenn nicht vorhanden)."""
    path = os.path.join(folder, "text.txt")
    if not os.path.isfile(path):
        return None
    with open(path, "r", encoding="utf-8", errors="replace") as handle:
        return handle.read()


def _collect_images(folder: str):
    """
    Bilddateien in ``folder``, nach Stem dedupliziert (``.webp`` bevorzugt).

    :return: Liste absoluter Pfade, natürlich sortiert.
    """
    by_stem = {}
    for entry in os.listdir(folder):
        path = os.path.join(folder, entry)
        if not os.path.isfile(path):
            continue
        stem, ext = os.path.splitext(entry)
        ext = ext.lower()
        if ext not in IMAGE_EXTS:
            continue
        existing = by_stem.get(stem)
        if existing is None:
            by_stem[stem] = path
            continue
        existing_ext = os.path.splitext(existing)[1].lower()
        if existing_ext != PREFERRED_EXT and ext == PREFERRED_EXT:
            by_stem[stem] = path
    return [
        by_stem[stem]
        for stem in sorted(by_stem, key=_natural_key)
    ]


def _convert_image(src_path: str, target_dir: str) -> str:
    """
    Verkleinert ein Bild und speichert es als WebP mit Zufalls-Basename.

    Verwendet dieselben Parameter wie ``app/modules/util/images.py``
    (Pillow direkt, da hier Disk-Dateien statt FileStorage vorliegen).

    :return: Basename der gespeicherten Datei (für die DB).
    """
    image = Image.open(src_path)
    image.load()
    if image.mode in ("RGBA", "P", "LA"):
        image = image.convert("RGB")
    image.thumbnail((MAX_EDGE, MAX_EDGE))
    os.makedirs(target_dir, exist_ok=True)
    name = f"{secrets.token_hex(16)}.webp"
    image.save(os.path.join(target_dir, name), "WEBP", quality=WEBP_QUALITY)
    return name


def _build_plan(source_root: str):
    """
    Scannt das Quellverzeichnis und baut die Import-Vorschau.

    :return: Liste von Bericht-Plänen (Dicts: jahr, titel, reihenfolge,
             text_html, hat_text, bilder=[Quellpfade]).
    """
    plan = []
    if not os.path.isdir(source_root):
        return plan

    jahre = sorted(
        entry for entry in os.listdir(source_root)
        if os.path.isdir(os.path.join(source_root, entry))
    )
    for jahr_name in jahre:
        jahr_dir = os.path.join(source_root, jahr_name)
        try:
            jahr = int(jahr_name)
        except ValueError:
            # Unerwarteter Ordnername -> als Titel/Jahr 0 markieren.
            jahr = 0

        subdirs = sorted(
            entry for entry in os.listdir(jahr_dir)
            if os.path.isdir(os.path.join(jahr_dir, entry))
        )
        lose_bilder = _collect_images(jahr_dir)

        if subdirs:
            for index, sub in enumerate(subdirs):
                sub_dir = os.path.join(jahr_dir, sub)
                roh = _read_text_file(sub_dir)
                plan.append({
                    "jahr": jahr,
                    "titel": sub,
                    "reihenfolge": index,
                    "text_html": _text_to_html(roh) if roh else "",
                    "hat_text": roh is not None,
                    "bilder": _collect_images(sub_dir),
                })
            if lose_bilder:
                roh = _read_text_file(jahr_dir)
                plan.append({
                    "jahr": jahr,
                    "titel": f"Erlebnisbericht {jahr_name}",
                    "reihenfolge": len(subdirs),
                    "text_html": _text_to_html(roh) if roh else "",
                    "hat_text": roh is not None,
                    "bilder": lose_bilder,
                })
        else:
            roh = _read_text_file(jahr_dir)
            plan.append({
                "jahr": jahr,
                "titel": f"Erlebnisbericht {jahr_name}",
                "reihenfolge": 0,
                "text_html": _text_to_html(roh) if roh else "",
                "hat_text": roh is not None,
                "bilder": lose_bilder,
            })
    return plan


def _print_preview(plan):
    """Gibt die Vorschau (pro Jahr) auf der Konsole aus."""
    if not plan:
        click.secho("Keine Quelldaten gefunden.", fg="yellow")
        return

    aktuelles_jahr = None
    summe_berichte = 0
    summe_bilder = 0
    for eintrag in plan:
        if eintrag["jahr"] != aktuelles_jahr:
            aktuelles_jahr = eintrag["jahr"]
            click.secho(f"\n[{aktuelles_jahr}]", fg="cyan", bold=True)
        summe_berichte += 1
        summe_bilder += len(eintrag["bilder"])
        text_info = "text.txt: ja" if eintrag["hat_text"] else "text.txt: nein"
        click.echo(
            f"  - {eintrag['titel']!r} "
            f"(reihenfolge={eintrag['reihenfolge']}, "
            f"bilder={len(eintrag['bilder'])}, {text_info})"
        )
    click.secho(
        f"\nGesamt: {summe_berichte} Berichte, "
        f"{summe_bilder} Bilder.",
        fg="green",
        bold=True,
    )


def _execute_import(plan, target_dir):
    """Führt den echten Import durch (DB-Inserts + Bildkonvertierung)."""
    anzahl_berichte = 0
    anzahl_bilder = 0
    fehler = []
    for eintrag in plan:
        bericht = Bericht(
            jahr=eintrag["jahr"],
            titel=eintrag["titel"],
            text=eintrag["text_html"],
            reihenfolge=eintrag["reihenfolge"],
            veroeffentlicht=True,
        )
        for bild_index, src_path in enumerate(eintrag["bilder"]):
            try:
                name = _convert_image(src_path, target_dir)
            except (UnidentifiedImageError, OSError) as exc:
                fehler.append(f"{src_path}: {exc}")
                continue
            bericht.bilder.append(
                BerichtBild(
                    dateiname=name,
                    reihenfolge=bild_index,
                    alt_text="",
                )
            )
            anzahl_bilder += 1
        db.session.add(bericht)
        anzahl_berichte += 1
    db.session.commit()
    return anzahl_berichte, anzahl_bilder, fehler


@click.command("import-berichte")
@click.option(
    "--dry-run", is_flag=True,
    help="Nur Vorschau anzeigen, nichts schreiben.",
)
@click.option(
    "--force", is_flag=True,
    help="Import auch ausführen, wenn bereits Berichte existieren.",
)
@with_appcontext
def import_berichte(dry_run, force):
    """Importiert Alt-Erlebnisberichte aus app/static/berichte/."""
    source_root = os.path.join(
        current_app.root_path, "static", SOURCE_SUBDIR
    )
    target_dir = os.path.join(
        current_app.config["UPLOAD_FOLDER"], TARGET_SUBDIR
    )

    click.echo(f"Quelle: {source_root}")
    click.echo(f"Ziel:   {target_dir}")

    plan = _build_plan(source_root)
    _print_preview(plan)

    if dry_run:
        click.secho(
            "\n--dry-run: Es wurde NICHTS geschrieben.",
            fg="yellow", bold=True,
        )
        return

    vorhandene = db.session.query(Bericht).count()
    if vorhandene and not force:
        click.secho(
            f"\nAbbruch: Es existieren bereits {vorhandene} Berichte. "
            "Mit --force erzwingen.",
            fg="red", bold=True,
        )
        raise SystemExit(1)

    anzahl_berichte, anzahl_bilder, fehler = _execute_import(plan, target_dir)
    click.secho(
        f"\nImport fertig: {anzahl_berichte} Berichte, "
        f"{anzahl_bilder} Bilder.",
        fg="green", bold=True,
    )
    if fehler:
        click.secho(f"{len(fehler)} Bild-Fehler:", fg="red")
        for zeile in fehler:
            click.echo(f"  - {zeile}")
