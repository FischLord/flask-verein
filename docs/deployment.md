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
