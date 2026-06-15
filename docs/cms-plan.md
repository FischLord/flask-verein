# CMS-Plan – flask-verein (fahrverein-planetal.de)

**Status:** Entwurf v0.1 (in Arbeit) · **Stand:** 2026-06-15
**Ziel:** Nicht-technische Vorstandsmitglieder pflegen Inhalte selbst – ohne HTML/Deploy.
**Basis:** bestehende Produktions-App `flask-verein` (App-Factory, SQLAlchemy/SQLite,
Flask-Login, Flask-WTF). KEIN zweiter Runtime, kein Stack-Bruch.

> Offene Punkte sind unten in Abschnitt 9 gesammelt und im Text mit „❓" markiert.

---

## 1. Kontext & Ausgangslage

Aktuell sind die pflegebedürftigen Inhalte verstreut/statisch:
- **Veranstaltungen** – hartkodiert in `app/templates/main/veranstaltungen.html`.
- **Vorstand** – hartkodiert in `app/templates/main/kontakt.html`.
- **Erlebnisberichte** – Dateisystem: `app/static/berichte/<jahr>/[<event>/]*.webp` + optional
  `text.txt`; gerendert über `erlebnisberichte()` (`app/main/routes.py`) und den
  Context-Processor `inject_reports`.
- **News/Infos** – existiert noch nicht.
- Datenbank: nur `Users`-Modell (`app/models.py`); Auth via Flask-Login (`/login`),
  Registrierung deaktiviert (FV-06).
- **Keine Migrations-Infrastruktur** (kein Flask-Migrate/Alembic, kein `create_all`).
- Vorhandenes Bild-Tooling: `pic_to_webp.py` (Pillow → webp); `pillow`/`webptools` in
  `requirements.txt`. CLI-Gerüst: `cli/kettle.py` (Click-Group, erweiterbar).

## 2. Entscheidungen (2026-06-15, verbindlich)

- **Admin-Ansatz:** maßgeschneiderte, deutschsprachige CRUD-Formulare im bestehenden
  Flask-WTF/Blueprint/Flask-Login-Stil (NICHT Flask-Admin/Directus) – laien-freundlich.
- **Bereiche:** Veranstaltungen/Termine (**Pilot**), Vorstand, Erlebnisberichte, News/Infos.
- **Erlebnisberichte:** in die **DB migrieren** (Modelle + Bild-Upload mit Resize), bestehende
  Ordner per einmaligem Importer übernehmen.

## 3. Architektur-Überblick

- Neuer Blueprint **`app/admin/`** (`url_prefix="/admin"`), **alle** Views `@login_required`.
  Struktur analog zu `app/auth/`: `routes.py`, `forms.py`, `__init__.py`.
- Admin-Templates unter `app/templates/admin/` mit eigenem schlankem Admin-Layout
  (`admin/layout.html`), klaren deutschen Formularen + Flash-Bestätigungen.
- Öffentliche Templates rendern künftig aus der DB statt hartkodiert.
- **Single Source:** je Inhaltstyp ein Modell; Seite (und ggf. Footer) lesen daraus.
- Wiederverwendung: Flask-WTF-CSRF (schon aktiv), Flash-Mechanik
  (`boilerplate/flash_message.html`), Login-Decorators, `kettle`-CLI, Pillow-Tooling.

## 4. Datenmodell (Entwurf, `app/models.py`)

Stil wie bestehendes `Users` (typannotierte Spalten). ❓Rich-Text vs. Klartext s. u.

- **Termin** (`termine`): `id`, `titel` (String 120), `datum` (Date), `uhrzeit` (String/Time,
  optional), `ort` (String 200), `beschreibung` (Text), `veroeffentlicht` (Bool, default True),
  `created_at`, `updated_at`. Property `abgelaufen` = `datum < heute`.
- **Vorstandsmitglied** (`vorstand`): `id`, `name`, `funktion`, `reihenfolge` (Int),
  `spruch` (Text, optional), `telefon` (optional), `email` (optional), `foto` (Dateiname,
  optional), `sichtbar` (Bool). (Telefon/E-Mail bewusst optional – vgl. FV-07.)
- **Bericht** (`berichte`): `id`, `jahr` (Int), `titel`, `slug` (für URL), `text` (Text),
  `datum`/`reihenfolge`, `veroeffentlicht`. 1:n zu Bildern.
- **BerichtBild** (`bericht_bilder`): `id`, `bericht_id` (FK), `dateiname`, `reihenfolge`,
  `alt_text`.
- **News** (`news`): `id`, `titel`, `slug`, `inhalt` (Text), `datum`, `veroeffentlicht`.

## 5. Admin-Bereich (CRUD)

- Pro Modell: Liste (mit Veröffentlicht-Schalter), Anlegen, Bearbeiten, Löschen
  (Lösch-Bestätigung). Formulare als Flask-WTF (`app/admin/forms.py`) mit serverseitiger
  Validierung; Datumsfelder als `DateField`/Date-Picker.
- **Bild-Upload** (Vorstand-Foto, Bericht-Bilder): Util `app/modules/util/images.py` aus
  `pic_to_webp.py` ableiten → Datei validieren (Pillow `Image.open`/`verify`),
  auf Maximalkante verkleinern, als `.webp` speichern, zufälliger Dateiname.
  Ablage unter `app/static/uploads/<typ>/` (in `.gitignore`).
- Admin-Navigation/Login-Link nur sichtbar, wenn `current_user.is_authenticated`
  (der auskommentierte Auth-Block in `nav.html` lässt sich dafür reaktivieren).

## 6. Öffentliche Templates auf DB umstellen

- `veranstaltungen.html` → Schleife über `Termin` (veröffentlicht), sortiert nach `datum`,
  Vergangene automatisch als „Abgelaufen" markiert.
- `kontakt.html` → Schleife über `Vorstandsmitglied` (`sichtbar`, nach `reihenfolge`).
- Erlebnisberichte: `erlebnisberichte()` + `inject_reports` lesen aus `Bericht`/`BerichtBild`
  statt aus dem Dateisystem; Dropdown aus DB. URL künftig per `slug`/`jahr`.

## 7. Migrationen & Daten-Import

- **Flask-Migrate (Alembic)** einführen (in `requirements.txt`, `migrate.init_app` in der
  Factory). Workflow `flask db migrate`/`upgrade`. Erste Migration legt alle neuen Tabellen
  an (Users bleibt unverändert). ❓Alternative wäre ein simples `db.create_all()` per
  `kettle`-Befehl – Flask-Migrate ist aber zukunftssicherer.
- **Berichte-Importer** als einmaliger CLI-Befehl (`kettle import-berichte` bzw. `flask`-CLI):
  läuft `app/static/berichte/<jahr>/[<event>/]` ab, legt `Bericht`/`BerichtBild` an, übernimmt
  `text.txt` → `Bericht.text`, verschiebt/kopiert Bilder nach `uploads/berichte/`.
  ⚠️ Erst ausführen, **nachdem** dein aktueller (uncommitteter) `berichte/2019`-Umzug
  abgeschlossen ist, damit die Quelle stabil ist.

## 8. Sicherheit (Definition of Done je dynamischer Funktion)

- Alle Admin-Routen `@login_required`; Schreibaktionen nur via POST mit CSRF (Flask-WTF).
- Strenge serverseitige Validierung; Upload-Härtung (Extension-Whitelist, Pillow-Verify,
  Größenlimit `MAX_CONTENT_LENGTH`, zufällige Dateinamen, Speicherung außerhalb Templates).
- Ausgabe: Jinja-Autoescape; Freitext als Klartext + `nl2br` (wie heute) – ❓WYSIWYG/HTML
  nur mit Sanitizer (bleach) als spätere Option.
- Backups: SQLite-Datei + `uploads/` regelmäßig sichern (Cron/Skript).

## 9. Offene Punkte (vor/while build zu klären)

- ❓**Migrationen:** Flask-Migrate ok (Empfehlung) oder simples `create_all` per CLI?
- ❓**Texte:** Klartext + `nl2br` zum Start (Empfehlung) oder gleich WYSIWYG/HTML (+Sanitizer)?
- ❓**Vorstand-Footer:** Soll der Vorstand künftig auch im Footer erscheinen (dann eine Quelle
  via Context-Processor) – aktuell zeigt der Footer keinen Vorstand.
- ❓**Berichte-URLs:** weiter nach Jahr (`/berichte/2019`) oder Slug? Mehrere Events pro Jahr?
- ❓**Rollen:** ein gemeinsamer Admin-Login (heute) genügt – oder mehrere Vorstands-Konten
  mit Rollen? (Registrierung bleibt sonst deaktiviert.)
- ❓**Uploads-Ort/Backup:** Pfad + Backup-Routine festlegen.

## 10. Phasen-Fahrplan

| Phase | Inhalt | Ergebnis |
|-------|--------|----------|
| **0 – Fundament** | Flask-Migrate, `app/admin`-Blueprint (login-geschützt) + Admin-Layout, Bild-Util (Pillow resize/webp), `uploads/` + .gitignore | Sichere Admin-Basis |
| **1 – Pilot Veranstaltungen** | `Termin`-Modell, Admin-CRUD, `veranstaltungen.html` aus DB, Auto-„abgelaufen" | Vorstand pflegt Termine selbst |
| **2 – Vorstand** | `Vorstandsmitglied`-Modell + CRUD + Foto-Upload, `kontakt.html` aus DB | Vorstand pflegbar, eine Quelle |
| **3 – Erlebnisberichte** | `Bericht`/`BerichtBild`, Upload mit Resize, Importer der Alt-Ordner, Route/Dropdown aus DB | Berichte fortführbar, Code entschlackt |
| **4 – News/Infos + Härtung** | `News`-Modell + CRUD, finale Upload-/Backup-/Rechte-Härtung | Vollständige Laien-Pflege |

## 11. Verifikation (je Phase)

- Lokal auf `:5001` (vgl. `docs/review.md`): Admin-CRUD durchklicken, öffentliche Seite
  zeigt DB-Inhalte, nicht eingeloggt → `/admin` leitet auf Login.
- `flake8` (CI-Gate) bleibt grün; neue Routen mit Smoke-Checks (Status, CSRF, Auth).
- Bild-Upload: Resize/webp greift, ungültige Datei wird abgelehnt.

---

*Entwurf – wird gemeinsam iteriert. Quelle der Wahrheit fürs Repo: dieses Dokument unter
`docs/cms-plan.md`. Lean-Review/Sicherheitsstand: `docs/review.md`.*
