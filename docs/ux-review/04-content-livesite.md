# Content-Abgleich Live-Site ↔ lokale App

**Stand:** 2026-06-20 · **Quelle Live:** https://fahrverein-planetal.de (HTTP 200, per curl extrahiert)
**Methode:** Live-Seiten geladen, HTML zu Text gestrippt, mit lokalen Templates + DB-Inhalt verglichen.

> Hinweis: E-Mail-Adressen sind auf der Live-Site per „[email protected]"-Obfuskation
> geschützt. Klartext-Adresse `kontakt@fahrverein-planetal.de` stammt aus dem lokalen
> Impressum-Template (identisch gepflegt). Private Handynummer aus Live-`/kontakt`.

---

## 0. Kernbefund (kritisch)

**Die statischen Textseiten sind aktuell – die Datenbank ist leer.**

| Inhalt | Live-Site | Lokal (DB/Template) | Status |
|---|---|---|---|
| **Vorstand** (6 Personen) | vollständig sichtbar | **DB: 0 Einträge** | ❌ FEHLT komplett |
| **Termine/Veranstaltungen** | Kutschertag 2025 etc. | **DB: 0 Einträge** | ❌ FEHLT komplett |
| Impressum (Adresse, VR, Steuer) | vorhanden | Template identisch | ✅ aktuell |
| Vereinsdaten (Bank, Beiträge) | vorhanden | Template identisch | ✅ aktuell |
| Verein-Text | vorhanden | Template identisch | ✅ aktuell |
| Startseite-Texte | vorhanden | Template identisch | ✅ aktuell |

**Konsequenz:** Lokal rendern `/kontakt` (Vorstand) und `/veranstaltungen` (Termine)
aktuell **leer bzw. mit Platzhaltertext** ("Aktuell sind keine Termine eingetragen").
Das ist der größte inhaltliche Unterschied zur Live-Site. Beide Bereiche sind jetzt
DB-/CMS-gestützt und müssen einmalig befüllt werden.

---

## 1. Vorstand – Daten zum Eintragen (DB-Modell `Vorstandsmitglied`)

Modellfelder: `name`, `funktion`, `reihenfolge`, `spruch`, `telefon`, `email`, `foto`, `sichtbar`.
Quelle: Live `/kontakt`. Reihenfolge wie dort dargestellt.

| # | name | funktion | telefon | spruch (Live-Zitat) |
|---|------|----------|---------|---------------------|
| 1 | Jacquelin Bredt | Vorsitzende | 0162 9177860 | „Diejenige, die den Laden zusammenhält – mit Charme und einem Telefon in der Hand." |
| 2 | Denise Matthe | Stellvertretende Vorsitzende | – | „Die ruhige Hand, die das Ruder übernimmt, wenn's mal stürmisch wird." |
| 3 | Stefanie-Kirstin Sailer | Kassenwart | – | „Die, die weiß, wo jeder Cent steckt – und immer den Überblick behält." |
| 4 | Janneck Lehmann | Jugendwart & Internetseite | – | „Der Jugendflüsterer und Web-Guru – bringt alles ins Netz." |
| 5 | Sarah Hohmann | Schriftführer | – | „Schreibt schneller als die meisten reden können." |
| 6 | Christina Herrmann | Facebook & Social Media | – | „Teilt alles – und findet immer den perfekten Hashtag." |

**❓ Rückfragen an Kunden:**
- E-Mail je Vorstand? (Live zeigt nur bei Vorsitzender eine obfuskierte Mail.)
- Fotos vorhanden? (`foto`-Feld) Falls ja, wo liegen sie?
- Telefon nur bei Jacquelin? (DSGVO: bewusst, lt. Review FV-07 akzeptiert.)
- Funktionsbezeichnungen: „Kassenwart"/„Schriftführer" gendern oder so lassen?

---

## 2. Termine – Daten zum Eintragen (DB-Modell `Termin`)

Modellfelder: `titel`, `datum`, `uhrzeit`, `ort`, `beschreibung`, `veroeffentlicht`.
Quelle: Live `/veranstaltungen`. **Achtung: Live-Daten sind von 2025 und teils mit Platzhaltern.**

| titel | datum | uhrzeit | ort | beschreibung |
|---|---|---|---|---|
| 11. Reckahner Kutschertag | **❓ xx.09.2025** (Live unklar!) | 10:00 Uhr | Reit-/Fahrplatz Kloster Lehnin OT Reckahn, Göttiner Landstr. | Dressuren (FA2), Aktionsralley, Hindernisfahren. Anmeldung ab August möglich. |

**❓ Rückfragen an Kunden:**
- Der Kutschertag steht live mit „**xx. September 2025**" (Platzhalter!) – das echte Datum?
- Soll für **2026** geplant werden (Daten sind aus 2025)? Welche Termine sind aktuell?
- Die „Entwicklungsprojekte" (Dachdeckerhindernis, Reitplatz) sind **keine Termine**,
  sondern Vereinsinfos → gehören nicht ins Termin-Modell, eher auf /verein oder als
  eigener Block (siehe Report 03).

---

## 3. Statische Seiten – Abgleich (alle aktuell, kleine Mängel)

### 3.1 Impressum (`impressum.html`)
Live = lokal identisch:
- Geschäftsstelle: **Krahner Straße 1, 14797 Kloster Lehnin OT Reckahn**
- E-Mail: kontakt@fahrverein-planetal.de
- Vorstand: Jacquelin Bredt (Vors.), Denise Matthe (stellv.)
- Vereinsregister: Amtsgericht Potsdam **VR 3487 P** · FN-Nr. 1800563 · LSB-Nr. 690271
- Finanzamt Brandenburg a.d. Havel, Steuer-Nr. 048/140/07206
- Hosting: privater Server Janneck Lehmann, Domain STRATO
- Verantwortlich § 6 MDStV: Janneck Lehmann ✅

### 3.2 Vereinsdaten (`vereinsdaten.html`)
Live = lokal identisch:
- Adresse: **Krahner Straße 03** ⚠️ (Impressum sagt „1" – NAP-Inkonsistenz, vgl. SEO-Report 05)
- FN-Nr. 1800563 · LSB-Nr. 690271
- Bank: Brandenburger Bank · IBAN DE43 1606 2073 0000 0620 81 · BIC GENODEF1BRB
- Beiträge: 24 € (bis 21 J.), 36 € (ab 21 J.), fällig bis Ende März ✅

**❓ Rückfrage:** Hausnummer korrekt – **1 oder 3**? Bitte einheitlich machen.

### 3.3 Verein (`verein.html`)
Live = lokal identisch. Inhaltlich gut & aktuell:
- gegründet 2012, ~25 Mitglieder, Hoher Fläming/Reckahn
- 80×40 m Dressurplatz, Reckahner Kutschertag, Jugendarbeit
- Nachwuchs: Helene Matthe, Janneck Lehmann
- ⚠️ Enthält „Vereinsentwicklung **2025**" → Jahreszahl pflegen.

### 3.4 Startseite (`index.html`)
Live = lokal identisch. Texte gut. (Slider-Bug & Hero siehe Report 03/01.)

### 3.5 Datenschutz (`datenschutz.html`)
**❓ Nicht im Detail gegen Live abgeglichen** – bitte prüfen ob Standard-Datenschutz
vorhanden und aktuell (Review FV-02 nannte CDN-Themen, inzwischen lokal).

---

## 4. Platzhalter / Überarbeitungswürdiges (lokal)

| Ort | Problem | Empfehlung | Aufwand |
|---|---|---|---|
| `app/templates/main/index.html` (Stub) | **Toter 1-Zeilen-Stub**, echte Startseite ist `templates/index.html` | Stub löschen oder klarstellen (vgl. Report 03) | S |
| `kontakt.html` Kontaktformular | „Nachricht senden" – **gibt es einen Mail-Versand-Backend-Handler?** Prüfen ob Formular funktioniert oder Deko | Backend prüfen/implementieren oder entfernen | M |
| Jahreszahlen „2025" | mehrfach hartcodiert (Verein, Veranstaltungen, Footer © 2025) | dynamisch `{{ now.year }}` bzw. pflegen | S |
| Vorstands-Fotos | `foto`-Feld leer → Avatare? | Fotos beschaffen oder Initial-Avatar | M |
| „xx. September" Kutschertag | Platzhalter-Datum live UND als Vorlage | echtes Datum erfragen | S |

---

## 5. Zusammenfassung „Daten-zum-Eintragen" (Kunde bestätigt)

**Sofort befüllbar über Admin-CMS, sobald bestätigt:**
1. **6 Vorstandsmitglieder** (Tabelle Abschnitt 1) → `/admin/vorstand`
2. **Termine 2025/2026** (Abschnitt 2) → `/admin/termine` — **Datum Kutschertag fehlt**
3. **Hausnummer-Klärung** (1 vs. 3) → Template-Fix
4. **E-Mails/Fotos Vorstand** → optional

**Offene Rückfragen gebündelt:**
- [ ] Echtes Datum 11. Reckahner Kutschertag?
- [ ] Planung 2026 oder erstmal 2025-Stand übernehmen?
- [ ] Hausnummer Geschäftsstelle: 1 oder 3?
- [ ] Vorstand: E-Mails + Fotos vorhanden?
- [ ] Kontaktformular: funktionierender Mailversand gewünscht?
- [ ] „Entwicklungsprojekte" als Vereinsinfo statt Termin – ok?
