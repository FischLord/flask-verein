"""

Bild-Upload-Utilities (Pillow).
----------------

Wird ab Phase 2 (Vorstand-Fotos, Bericht-Bilder) genutzt; in Phase 1
bereits angelegt. Abgeleitet von ``pic_to_webp.py``.

Härtung (vgl. cms-plan.md §8):
- Extension-Whitelist,
- Pillow ``verify()`` + ``load()`` (echtes Bild?),
- Verkleinern auf eine Maximalkante,
- Speicherung als ``.webp`` mit zufälligem Dateinamen,
- Ablage unter ``UPLOAD_FOLDER/<typ>/`` (außerhalb der Templates).
"""
import os
import secrets

from PIL import Image, UnidentifiedImageError

from werkzeug.utils import secure_filename

# Erlaubte Datei-Endungen für Uploads.
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp", "gif"}

# Maximale Kantenlänge (px) nach dem Verkleinern.
MAX_EDGE = 1600


class ImageValidationError(ValueError):
    """Hochgeladene Datei ist kein gültiges/erlaubtes Bild."""


def _extension_ok(filename: str) -> bool:
    """Prüft die Datei-Endung gegen die Whitelist."""
    if "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS


def save_image(file_storage, upload_folder, subdir="",
               max_edge=MAX_EDGE) -> str:
    """
    Validiert ein hochgeladenes Bild und speichert es als WebP.

    :param file_storage: ``FileStorage`` aus ``request.files``
    :param upload_folder: Basis-Verzeichnis (app.config["UPLOAD_FOLDER"])
    :param subdir: Untertyp-Ordner, z. B. "vorstand" oder "berichte"
    :param max_edge: maximale Kantenlänge in Pixel
    :return: relativer Dateiname (``subdir/<zufall>.webp``) für die DB
    :raises ImageValidationError: bei ungültiger/leerer/unerlaubter Datei
    """
    if file_storage is None or not getattr(file_storage, "filename", ""):
        raise ImageValidationError("Keine Datei ausgewählt.")

    filename = secure_filename(file_storage.filename)
    if not _extension_ok(filename):
        raise ImageValidationError("Dateityp nicht erlaubt.")

    # verify() entwertet das Image-Objekt -> danach erneut öffnen.
    try:
        file_storage.stream.seek(0)
        Image.open(file_storage.stream).verify()
        file_storage.stream.seek(0)
        image = Image.open(file_storage.stream)
        image.load()
    except (UnidentifiedImageError, OSError) as exc:
        raise ImageValidationError(
            "Datei ist kein gültiges Bild."
        ) from exc

    # Alpha/Palette -> RGB, damit WebP zuverlässig speichert.
    if image.mode in ("RGBA", "P", "LA"):
        image = image.convert("RGB")

    image.thumbnail((max_edge, max_edge))

    target_dir = os.path.join(upload_folder, subdir)
    os.makedirs(target_dir, exist_ok=True)

    name = f"{secrets.token_hex(16)}.webp"
    image.save(os.path.join(target_dir, name), "WEBP", quality=82)

    return os.path.join(subdir, name) if subdir else name


def delete_image(rel_name, upload_folder) -> bool:
    """
    Löscht eine zuvor gespeicherte Upload-Datei.

    :param rel_name: relativer Dateiname (Rückgabe von ``save_image``)
    :param upload_folder: Basis-Verzeichnis (app.config["UPLOAD_FOLDER"])
    :return: True, wenn eine Datei gelöscht wurde, sonst False
    """
    if not rel_name:
        return False
    # secure_filename pro Pfadsegment -> kein Verzeichniswechsel.
    parts = [secure_filename(p) for p in rel_name.split("/") if p]
    path = os.path.join(upload_folder, *parts)
    if os.path.isfile(path):
        os.remove(path)
        return True
    return False
