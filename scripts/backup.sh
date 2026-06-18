#!/usr/bin/env bash
#
# backup.sh – Sichert die SQLite-Datenbank (app.db) und die Upload-Dateien
# (app/static/uploads/) der flask-verein-App in ein Zeitstempel-Archiv.
#
# Aufruf:
#   scripts/backup.sh
#
# Konfiguration (optional, via Umgebungsvariablen):
#   BACKUP_DIR=/pfad/zu/backups   Zielverzeichnis (Default: <repo>/backups)
#   RETENTION_DAYS=30             Alte Archive löschen (0 = nie löschen)
#
# Cron-Beispiel (täglich 03:30, Ausgabe ins Log):
#   30 3 * * * /pfad/zu/flask-verein/scripts/backup.sh >> \
#       /var/log/flask-verein-backup.log 2>&1
#
set -euo pipefail

# Repo-Wurzel = übergeordnetes Verzeichnis dieses Skripts.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

DB_FILE="${REPO_ROOT}/app.db"
UPLOADS_DIR="${REPO_ROOT}/app/static/uploads"

BACKUP_DIR="${BACKUP_DIR:-${REPO_ROOT}/backups}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"

TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
WORK_DIR="$(mktemp -d)"
trap 'rm -rf "${WORK_DIR}"' EXIT

mkdir -p "${BACKUP_DIR}"

# 1) Datenbank sichern – möglichst transaktionssicher via sqlite3 .backup
#    (funktioniert auch bei laufender App); sonst einfache Kopie.
if [ -f "${DB_FILE}" ]; then
    if command -v sqlite3 >/dev/null 2>&1; then
        sqlite3 "${DB_FILE}" ".backup '${WORK_DIR}/app.db'"
    else
        echo "WARN: sqlite3 nicht gefunden – kopiere DB-Datei direkt." >&2
        cp -p "${DB_FILE}" "${WORK_DIR}/app.db"
    fi
else
    echo "WARN: ${DB_FILE} nicht gefunden – Datenbank wird übersprungen." >&2
fi

# 2) Upload-Dateien sichern (Vorstand-Fotos, Bericht-Bilder).
if [ -d "${UPLOADS_DIR}" ]; then
    cp -a "${UPLOADS_DIR}" "${WORK_DIR}/uploads"
else
    echo "WARN: ${UPLOADS_DIR} nicht gefunden – Uploads übersprungen." >&2
fi

# 3) Archiv schreiben.
ARCHIVE="${BACKUP_DIR}/backup-${TIMESTAMP}.tar.gz"
tar -czf "${ARCHIVE}" -C "${WORK_DIR}" .
echo "Backup erstellt: ${ARCHIVE}"

# 4) Alte Backups gemäß Aufbewahrungsdauer aufräumen.
if [ "${RETENTION_DAYS}" -gt 0 ]; then
    find "${BACKUP_DIR}" -maxdepth 1 -type f -name 'backup-*.tar.gz' \
        -mtime "+${RETENTION_DAYS}" -delete
fi
