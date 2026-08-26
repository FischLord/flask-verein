"""

HTML-Bereinigung für Freitext aus dem WYSIWYG-Editor.
----------------

Vorstandsbeschluss 2026-06-15: Freitext (z. B. Termin-Beschreibung)
wird als HTML gespeichert. Damit kein gefährliches Markup in die
Datenbank oder auf die öffentliche Seite gelangt, wird jede Eingabe
serverseitig mit *bleach* gegen eine strenge Allowlist bereinigt.

Das Ergebnis ist sicheres HTML und darf in Templates mit ``| safe``
ausgegeben werden.
"""
import re

import bleach

# Erlaubte Tags – bewusst klein gehalten (laien-tauglicher Editor).
ALLOWED_TAGS = [
    "p", "br", "strong", "em",
    "ul", "ol", "li",
    "a", "h2", "h3", "blockquote",
]

# Protokolle für Links – kein javascript:, data: o. Ä.
ALLOWED_PROTOCOLS = ["http", "https", "mailto"]

# href MUSS explizit mit einem erlaubten Schema beginnen. Grund:
# bleach/urlparse stuft Werte wie "javascript:1" (Ziffern nach dem
# Doppelpunkt) als schemalos ein und würde sie sonst durchlassen.
_SAFE_HREF = re.compile(r"^\s*(https?://|mailto:)", re.IGNORECASE)


def _attribute_filter(tag, name, value):
    """
    Allowlist-Callback für bleach: erlaubt ausschließlich ein
    streng geprüftes ``href`` an ``<a>``-Tags.
    """
    if tag == "a" and name == "href":
        return bool(_SAFE_HREF.match(value or ""))
    return False


def clean_html(raw: str) -> str:
    """
    Bereinigt rohes HTML gegen die strenge Allowlist.

    Nicht erlaubte Tags/Attribute werden entfernt (strip=True), der
    Textinhalt bleibt erhalten.

    :param raw: rohes HTML, z. B. aus dem WYSIWYG-Editor
    :return: bereinigtes HTML (leerer String bei leerer Eingabe)
    """
    if not raw:
        return ""

    cleaned = bleach.clean(
        raw,
        tags=ALLOWED_TAGS,
        attributes=_attribute_filter,
        protocols=ALLOWED_PROTOCOLS,
        strip=True,
    )
    return cleaned.strip()
