# Deploy- & Härtungshinweise – flask-verein

Kurzreferenz für den Produktionsbetrieb (ergänzt `docs/cms-plan.md` §8).

## 1. Umgebung / Konfiguration

- **`.env` (nicht im Git):** mindestens `SECRET_KEY` (fester, zufälliger
  Wert – sonst startet die App nicht). Optional `DATABASE_URL`,
  `UPLOAD_FOLDER`, `MAINTENANCE_MODE`, `MAX_CONTENT_LENGTH`,
  `APP_NAME`, `REGISTRATION_ENABLED`.
- `REGISTRATION_ENABLED` bleibt **aus** (Self-Service-Registrierung
  deaktiviert); Konten nur manuell anlegen.
- Secrets generieren: `python -c "import secrets; print(secrets.token_hex(32))"`.

## 2. App starten (WSGI)

- Nicht den Flask-Dev-Server nutzen. Stattdessen z. B. Gunicorn:
  `gunicorn -w 3 -b 127.0.0.1:8000 wsgi:app`
  (`wsgi.py` exportiert bereits `app = create_app()`).
- Davor ein Reverse-Proxy (nginx) mit **HTTPS** (Let's Encrypt). Die App
  setzt bereits CSP, HSTS, `X-Frame-Options: DENY`,
  `X-Content-Type-Options: nosniff` u. a. (`app/__init__.py`). HSTS wirkt
  nur über HTTPS – TLS am Proxy terminieren.
- **Rate-Limiting:** Flask-Limiter nutzt aktuell In-Memory-Storage
  (nur für 1 Worker korrekt). Bei mehreren Gunicorn-Workern einen
  gemeinsamen `storage_uri` (z. B. Redis) konfigurieren.

## 3. Datenbank / Migrationen

- Schema-Updates nach jedem Deploy: `flask --app app db upgrade`.
- SQLite-Datei `app.db` liegt im Repo-Verzeichnis und ist in
  `.gitignore` – **niemals committen** (enthält Nutzerdaten).

### 3.1 ⚠️ Einmaliger Schritt beim Erst-Deploy: `db stamp`

Die **bestehende Produktions-DB wurde ohne Flask-Migrate angelegt**
(`db.create_all()`) und besitzt deshalb keine `alembic_version`-Tabelle.
Alembic hält sie für leer und will die Baseline-Migration erneut fahren –
`db upgrade` bricht mit `table users already exists` ab und hinterlässt
einen halb migrierten Zustand.

Deshalb **vor dem allerersten `db upgrade`** die Baseline stempeln:

```bash
flask --app app db stamp 7c9e6b2eb1b4   # Baseline: users-Tabelle
flask --app app db upgrade              # spielt nur cms_tables + drop_news
```

- Nur **einmalig** nötig. Prüfen, ob es schon erledigt ist:
  `sqlite3 app.db "select * from alembic_version;"` – liefert die Abfrage
  eine Zeile, ist die DB unter Alembic-Kontrolle und `db stamp` entfällt.
- Bei einer **frisch angelegten, leeren** DB entfällt der Stamp ebenfalls;
  dort läuft `db upgrade` von `None` aus komplett durch.
- Vor dem Stamp eine Kopie der `app.db` ziehen (siehe §5).

### 3.2 Ablauf Erst-Deploy (Reihenfolge)

1. Code holen (`git fetch && git reset --hard origin/main` – das
   Server-Repo hat nach dem History-Purge eine abweichende History).
2. Python-Abhängigkeiten: `pip install -r requirements.txt`.
3. **CSS bauen** – siehe §3.3.
4. `flask --app app db stamp 7c9e6b2eb1b4` (nur beim Erst-Deploy, §3.1).
5. `flask --app app db upgrade`.
6. `flask --app app seed-stammdaten` – legt die Stammdaten (Vorstand,
   Kutschertag-Termine) an. Idempotent, kann gefahrlos wiederholt werden.
7. Berichte importieren – siehe §3.4.
8. Dienst neu starten: `systemctl restart flaskapp`.

### 3.3 CSS-Build gehört in den Deploy

`app/static/css/app.css` ist ein **Build-Artefakt und `.gitignore`d** –
nach einem frischen Checkout ist die Seite ohne diesen Schritt ungestylt:

```bash
npm ci
npm run build:css
```

Alternative, wenn auf dem Server kein Node installiert werden soll: lokal
`npm run build:css` laufen lassen und die erzeugte `app/static/css/app.css`
per `scp`/`rsync` hochladen. Der Schritt muss nach **jedem** Deploy laufen,
bei dem sich Templates oder `input.css` geändert haben (Tailwind erzeugt
nur die tatsächlich genutzten Utility-Klassen).

### 3.4 Berichte-Quelldaten vor `import-berichte` bereitstellen

`flask --app app import-berichte` liest aus
`app/static/berichte/<jahr>/…`. Dieses Verzeichnis ist **untracked** und
nach `git reset --hard` nicht zwingend vorhanden. Die Originale liegen auf
dem VPS unter `/home/flaskuser/berichte-archiv` (98 MB) und müssen vorher
zurückkopiert werden:

```bash
cp -a /home/flaskuser/berichte-archiv/. \
      /home/flaskuser/flask-verein/app/static/berichte/
flask --app app import-berichte --dry-run   # Vorschau prüfen (9 Berichte)
flask --app app import-berichte             # echter Import
```

Der Importer liest die Quelldateien nur, er verschiebt oder löscht nichts.
Die konvertierten Bilder landen unter `UPLOAD_FOLDER/berichte/`.

### 3.5 Weitere untracked Pfade, die den Deploy überleben müssen

`app/static/forms/` (bis auf die im Repo geführten Formulare),
`app/static/uploads/` und `app/static/berichte/` sind nicht im Git und
überstehen `git reset --hard` – trotzdem vor dem Deploy sichern.

## 4. Dateirechte & Uploads

- `app/static/uploads/` (Vorstand-Fotos, Bericht-Bilder) ist in
  `.gitignore` – nicht im Git, nur per Backup gesichert.
- Upload-Härtung ist serverseitig aktiv: Extension-Whitelist,
  Pillow-`verify()`, Resize auf Maximalkante, WebP, zufällige
  Dateinamen, `MAX_CONTENT_LENGTH` (Default 8 MB).
- Schreibrechte minimal halten: nur der App-Benutzer braucht Schreibzugriff
  auf `app.db` und `app/static/uploads/`. Restliche Repo-Dateien read-only.

## 5. Backups

- `scripts/backup.sh` sichert `app.db` (transaktionssicher via
  `sqlite3 .backup`) **und** `app/static/uploads/` in ein
  Zeitstempel-Archiv `backups/backup-<YYYYMMDD-HHMMSS>.tar.gz`.
- Per Cron automatisieren, z. B. täglich 03:30:
  ```cron
  30 3 * * * /pfad/zu/flask-verein/scripts/backup.sh >> \
      /var/log/flask-verein-backup.log 2>&1
  ```
- Stellschrauben über Umgebungsvariablen: `BACKUP_DIR` (Ziel),
  `RETENTION_DAYS` (alte Archive löschen, Default 30; `0` = nie).
- **Off-Site:** Archive zusätzlich auf einen anderen Host/Speicher kopieren
  (ein Backup auf demselben Server schützt nicht vor Server-Verlust).
- Restore regelmäßig testen: Archiv entpacken, `app.db` + `uploads/`
  zurückspielen, App starten.

## 6. Wartungsmodus

- `MAINTENANCE_MODE=True` in der `.env` liefert für alle Anfragen `503`
  (siehe `before_request` in der Factory). Nach Änderung App neu starten.
