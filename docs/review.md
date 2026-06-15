# Lean Security-/Code-Review – flask-verein (fahrverein-planetal.de)

**Stand:** 2026-06-15 · **Methode:** read-only Quelltext-Review (kein Live-Pentest, kein automatischer Scan)
**Prüfobjekt:** Flask-App `flask-verein` (App-Factory, Jinja2, Flowbite), Remote `github.com/FischLord/flask-verein`
**Hinweis:** Dies ersetzt das alte Audit unter `fv-planetal-website/docs/audit/` – jenes bezog sich auf einen obsoleten Prototyp und gilt hier **nicht**.

> Befund-IDs `FV-NN` sind die verbindliche Referenz für Folgearbeiten/Commits.

---

## 0. Akute Sicherheitsmaßnahme: DB im öffentlichen Repo (FV-01)

`app.db` (SQLite, enthält `users`-Tabelle mit 1 Konto = Login/Admin) war im **öffentlichen** GitHub-Repo eingecheckt – inkl. Passwort-Hash, in der gesamten Git-History.

- **Erledigt (lokal):** `app.db` aus dem Git-Tracking entfernt (`git rm --cached`), DB-Dateien in `.gitignore`. Commit `f255ada` auf Branch `security/remove-tracked-db` (nicht gepusht).
- **Offen (Freigabe nötig, destruktiv/öffentlich):**
  1. **History bereinigen + Force-Push** (entfernt `app.db` aus allen alten Commits):
     ```bash
     pipx install git-filter-repo            # oder: pip install git-filter-repo
     cd ~/repos/flask-verein
     git filter-repo --path app.db --invert-paths --force
     git remote add origin https://github.com/FischLord/flask-verein.git
     git push origin --force --all && git push origin --force --tags
     ```
  2. **Login-Passwort des `users`-Eintrags ändern** und **`SECRET_KEY` in `.env` rotieren** – der wirksamste Schutz, da der Hash bereits exponiert war (Repo public ⇒ ggf. bereits kopiert/indexiert).

---

## 1. Befunde nach Schweregrad

### 🔴 Hoch

**FV-01 · User-DB im öffentlichen Repo** — siehe Abschnitt 0 (in Arbeit).

**FV-02 · Drittanbieter-CDN ohne Einwilligung/SRI**
- Ort: `app/templates/boilerplate/layout.html:23,39` (Flowbite CSS+JS von `cdnjs.cloudflare.com`), `app/templates/main/kontakt.html` (Platzhalterbilder von `fakeimg.pl`).
- Risiko: DSGVO – Besucher-IP wird ohne Einwilligung an US-CDNs übertragen, in der Datenschutzerklärung nicht genannt. Zusätzlich Supply-Chain-Risiko (kein `integrity`/SRI-Hash) und Ausfallrisiko (Seite ohne CDN unstyled / Menü kaputt).
- Empfehlung: Flowbite CSS+JS **lokal** unter `app/static/` ausliefern; Platzhalterbilder lokal hinterlegen.

**FV-03 · Keine Security-HTTP-Header**
- Ort: keine `after_request`-/Talisman-Logik vorhanden.
- Fehlend: CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, HSTS, Permissions-Policy.
- Empfehlung: zentral via `@app.after_request` oder `flask-talisman` setzen.

**FV-04 · Login ohne Brute-Force-Schutz**
- Ort: `app/auth/routes.py` `/login`.
- Befund: öffentlicher Login, kein Rate-Limit/Lockout. (Generische Fehlermeldung „credentials are invalid" ist vorhanden – gut.)
- Empfehlung: `Flask-Limiter` (z. B. 5 Versuche/Minute/IP).

**FV-05 · `SECRET_KEY`-Fallback erzeugt instabile Sessions**
- Ort: `config.py:17` `SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)`.
- Befund: fehlt der Key in `.env`, wird bei jedem (Worker-)Neustart ein neuer Key generiert → Sessions/Logins/CSRF brechen, besonders unter gunicorn mit mehreren Workern.
- Empfehlung: festen `SECRET_KEY` aus `.env` erzwingen (beim Start hart fehlschlagen, wenn nicht gesetzt).

### 🟡 Mittel

**FV-06 · Offene Registrierung** — `app/auth/routes.py` `/register` ist live erreichbar (Nav-Links nur auskommentiert); jeder kann Konten anlegen.
- **Entscheidung (2026-06-15): deaktivieren.** Umsetzung offen: Route entfernen/sperren bzw. hinter Admin/Feature-Flag.

**FV-07 · Private Kontaktdaten auf /kontakt** — `kontakt.html:14,16` private Handynr. `0162 9177860` (Klartext) + private `web.de`-Mail (offener `mailto:`).
- **Entscheidung (2026-06-15): akzeptiert** – bewusst veröffentlichter Vereinskontakt, Einwilligung liegt vor. Keine Änderung.

**FV-08 · Path-Traversal-Härtung in `/berichte/<folder>`** — `app/main/routes.py:54-58` baut Pfad per `os.path.join` mit User-Input; `..`-Segmente möglich.
- Empfehlung: `werkzeug.utils.safe_join` verwenden oder `folder` gegen die bekannte `reports`-Liste validieren.

**FV-09 · Kein lokaler Tailwind-Build** — keine `tailwind.config`/Build-Pipeline; nur Flowbite-CDN-CSS eingebunden. Tailwind-Utility-Klassen werden so evtl. nicht vollständig ausgeliefert.
- Empfehlung: Styling in Produktion verifizieren; ggf. lokalen Tailwind-Build einführen (löst zusammen mit FV-02 die CDN-Abhängigkeit).

### ⚪ Niedrig

**FV-10 · Falsche Error-Templates** — `app/errors.py` rendert für 400/403/405 jeweils `errors/401.html`, obwohl `400/403/405.html` existieren.

**FV-11 · `created_at`-Default-Bug** — `app/models.py:14` `default=datetime.utcnow()` wird einmalig bei Import ausgewertet (alle Datensätze gleiche Zeit). → `default=datetime.utcnow` (callable); `utcnow` ist zudem deprecated (3.12) → `lambda: datetime.now(timezone.utc)`.

**FV-12 · `password_hash` String(128) zu kurz** — scrypt-Hashes ~162 Zeichen; auf SQLite unkritisch (Länge ignoriert), bricht aber bei DB-Migration. → 256.

**FV-13 · Barrierefreiheit Navigation** — `nav.html:27` (und Carousel-Buttons in `index.html`) `focus:outline-none` ohne sichtbaren Fokus (WCAG 2.4.7); Dropdown-Button ohne `aria-expanded/haspopup/controls`; Escape schließt das Dropdown nicht; kein Skip-Link; `<nav>` nicht in `<header>`.

**FV-14 · Englische Auth-Texte** — „Sign In", „Your credentials are invalid", „You've signed out", „Account successfully registered" im sonst deutschen Auftritt.

**FV-15 · Footer-Jahr statisch** — `footer.html:7` „© 2025" hartkodiert → dynamisch (`{{ now().year }}` o. ä.).

**FV-16 · Toter Code** — `routes.py:1-13,18-33` übergeben viele ungenutzte `*_version`-Variablen + ungenutzte Imports an `index.html`; ungenutztes Template `app/templates/main/index.html`.

---

## 2. Positiv (bewusst gut gelöst)

- Saubere App-Factory + Blueprints; **CSRF** via Flask-WTF; gepinnte `requirements.txt`; Wartungsmodus.
- Eigene Fehlerseiten (404/500 …), `.env`/`config.py`-Trennung, `wsgi.py`, CI-Lint (flake8).
- Gute SEO: Meta/OG/Canonical, generierte `sitemap.xml`, `robots.txt`; `lang="de"`; sinnvolle `sr-only`-Labels.

---

## 3. Empfohlene nächste Umsetzungs-Batches

1. **Sicherheit abschließen:** FV-01 (History-Purge/Force-Push/Passwort), FV-03 (Header), FV-04 (Rate-Limit), FV-05 (SECRET_KEY), FV-06 (Registrierung deaktivieren).
2. **Datenschutz/Robustheit:** FV-02 (CDN → lokal), FV-08 (safe_join), FV-09 (Tailwind verifizieren).
3. **Qualität/Aufräumen:** FV-10, FV-11, FV-12, FV-13, FV-14, FV-15, FV-16.

*Erstellt im read-only Review; am Anwendungscode wurde außer der DB-Tracking-Entfernung (FV-01) nichts geändert.*
