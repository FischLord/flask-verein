# 05 - Technical SEO Review

**Projekt:** Fahrverein Planetal e.V. (Flask / Jinja2 / App-Factory)
**Domain:** https://fahrverein-planetal.de
**Standort:** Krahner Straße, 14797 Kloster Lehnin OT Reckahn (Brandenburg)
**Scope:** Nur Analyse, keine Code-Änderungen.
**Stand:** 2026-06-20

---

## 0. Executive Summary

Die Aussage des Auftraggebers ("SEO fehlt komplett") ist **zu pessimistisch**. Es existiert
bereits eine solide Basis:

- Sprechende, deutschsprachige meta description + keywords im Layout
- Open-Graph-Tags
- Canonical-URL (dynamisch über `request.path`)
- robots.txt + dynamisch generierte sitemap.xml
- Strukturierte Daten: JSON-LD `SportsClub` (/verein), Microdata `Event` (/veranstaltungen),
  `Article`/`ImageGallery` (/berichte), `Organization`-Fragmente
- Saubere Heading-Struktur (1× H1 pro Seite), Skip-Link, Alt-Texte überwiegend vorhanden

Die eigentlichen Probleme sind **systematisch und mit wenig Aufwand behebbar**:

| # | Problem | Schwere |
|---|---------|---------|
| 1 | **Duplicate Titles + Duplicate Descriptions** auf allen öffentlichen Seiten (keine Route übergibt `title`, description global im Layout) | **Hoch** |
| 2 | **Riesige Hero-Bilder** (promo1.webp 6000×4000 px / 1,8 MB) bei `loading="lazy"` auf dem LCP-Element | **Hoch** |
| 3 | **NAP-Inkonsistenz**: Hausnummer "1" (Impressum) vs. "03" (Vereinsdaten); JSON-LD-Adresse ohne Straße/PLZ | **Hoch** |
| 4 | **sitemap.xml enthält keine `/berichte/<jahr>`-Seiten** (dynamische Routen werden hart ausgeschlossen) | **Mittel** |
| 5 | Kein zentrales `LocalBusiness`/`SportsClub`-JSON-LD im Layout (nur auf /verein, unvollständig) | **Mittel** |
| 6 | Fehlende `width`/`height` an allen `<img>` → Layout-Shift (CLS) | **Mittel** |
| 7 | Marken-Inkonsistenz im `<title>`: `APP_NAME = "Fv Planetal e.V."` (abgekürzt) vs. "Fahrverein Planetal e.V." in OG/Content | **Mittel** |
| 8 | OG unvollständig/statisch (og:url hardcoded auf Startseite, og:image = 197×149 px Logo, kein og:locale/site_name, keine Twitter Cards) | **Mittel** |

---

## 1. Bestandsaufnahme

### 1.1 `app/templates/boilerplate/layout.html`

| Element | Status | Fundstelle | Bewertung |
|---------|--------|-----------|-----------|
| `lang="de"` | ✅ vorhanden | `layout.html:2` | korrekt |
| `<html itemscope itemtype="https://schema.org/Organization">` | ⚠️ deklariert, aber **leer** | `layout.html:2` | Keine `itemprop name/url/logo` → Google sieht leere Organization. Entweder befüllen oder durch JSON-LD ersetzen. |
| `<meta charset>` / `viewport` | ✅ | `layout.html:4-5` | korrekt |
| `meta description` | ⚠️ **global/statisch** | `layout.html:6` | Identisch auf jeder Seite → Duplicate Descriptions. |
| `meta keywords` | ⚠️ obsolet | `layout.html:7` | Wird von Google ignoriert, schadet nicht. Keyword-Stuffing-Geruch ("FV Planetal e.V., Planetal, Fahrverein Planetal..."). Niedrige Prio. |
| `meta author` | ✅ | `layout.html:8` | ok |
| Open Graph | ⚠️ teilweise | `layout.html:11-15` | `og:title` dynamisch (gut), `og:description` statisch, **`og:url` hart auf `https://fahrverein-planetal.de`** (für alle Seiten gleich, ignoriert `request.path`), `og:image` = `logo.webp` (197×149 px, zu klein; Empfehlung ≥1200×630). Fehlt: `og:site_name`, `og:locale`, `og:image:width/height`, `og:image:alt`. |
| Twitter Cards | ❌ fehlen | – | `twitter:card`, `twitter:title` etc. nicht vorhanden. |
| Canonical | ✅ dynamisch | `layout.html:18` | `https://fahrverein-planetal.de{{ request.path }}` – sauber, ohne Query-String. Gut. |
| `<title>`-Pattern | ⚠️ | `layout.html:21` | `{% if title %}{{ title }} - {% endif %}{{ config['APP_NAME'] }}`. Pattern ist gut, ABER keine Route übergibt `title` (siehe 1.4) **und** `APP_NAME = "Fv Planetal e.V."` (abgekürzt, `config.py:21`). |
| Favicon | ✅ | `layout.html:22` | nutzt `logo.webp` |
| Skip-Link / a11y | ✅ | `layout.html:27` | "Zum Inhalt springen" vorhanden, gut. |
| `theme-color`, `hreflang`, `<meta name="robots">` | ❌ fehlen | – | Bei monolingualer DE-Seite ist hreflang verzichtbar; robots-meta optional. |

### 1.2 `app/main/routes.py` – Sitemap / robots / Routen

**`generate_sitemap(app)` (`routes.py:105-160`):**

```python
for rule in app.url_map.iter_rules():
    if "GET" in rule.methods and not rule.arguments:   # <-- Zeile 140
```

- ⚠️ **`not rule.arguments` schließt ALLE dynamischen Routen aus.** Damit fehlen sämtliche
  `/berichte/<int:jahr>`-Seiten in der Sitemap (`routes.py:33`). Das sind die **inhaltlich
  reichsten, am häufigsten aktualisierten** Seiten (DB-Inhalt: Berichte + Bildergalerien).
- ⚠️ **Substring-Matching für Excludes** (`routes.py:145-146`): `any(excl in endpoint ...)`.
  Funktioniert aktuell, ist aber fragil – `'admin' in endpoint` / `'static' in path` würden
  auch unbeabsichtigte Treffer ausschließen, sobald eine Route diese Teilstrings enthält.
- ⚠️ **`lastmod = datetime.utcnow()`** (`routes.py:137`) wird bei **jedem Abruf** neu gesetzt →
  signalisiert Suchmaschinen "alles hat sich gerade geändert". Sollte stabil sein (z. B.
  `updated_at` aus DB für Termine/Berichte, statisch für Info-Seiten).
- ✅ Termine landen indirekt korrekt über die statische `/veranstaltungen`-Route (Einzelseite).
- ✅ priority/changefreq pro Seite sinnvoll gepflegt (`routes.py:125-134`).

**Excluded laut Code:** `static, admin, login, logout, register, robots.txt, sitemap.xml`
(`routes.py:119-122`). Plus implizit alle dynamischen Routen.

**`/robots.txt` (`routes.py:101-103`):** liefert die statische Datei via `send_from_directory`.
**`/sitemap.xml` (`routes.py:162-168`):** `Content-Type: application/xml` + `X-Robots-Tag: noindex` (gut – Sitemap selbst soll nicht indexiert werden).

### 1.3 `app/static/robots.txt`

```
User-agent: *
Allow: /
Sitemap: https://fahrverein-planetal.de/sitemap.xml
```

✅ Korrekt und vollständig. `Allow: /`, absolute Sitemap-URL. Keine versehentlichen Blocks.
(Hinweis: Es existieren faktisch zwei Wege zur robots.txt – die statische Datei wird sowohl
über `/robots.txt`-Route als auch über `/static/robots.txt` ausgeliefert; unkritisch.)

### 1.4 Strukturierte Daten – Inventar

| Seite | Typ | Format | Fundstelle | Vollständigkeit |
|-------|-----|--------|-----------|-----------------|
| Layout (`<html>`) | Organization | Microdata | `layout.html:2` | ❌ leer (keine Properties) |
| /verein | SportsClub | **JSON-LD** | `verein.html:170-200` | ⚠️ gut, aber ohne `streetAddress`, `postalCode`, `geo`, `telephone`, `email`, `url`, `logo`/`image` |
| /verein | SportsClub + PostalAddress | Microdata | `verein.html:3,137` | ⚠️ Doppelung zu JSON-LD; Adresse leer |
| /veranstaltungen | Event | Microdata | `veranstaltungen.html:30,39-40` | ⚠️ nur `name`, `startDate`, `location`(String), `description`. Fehlt: `endDate`, `eventStatus`, `organizer`, `location` als `Place` mit Adresse, `offers`. **Kein JSON-LD.** |
| /berichte/&lt;jahr&gt; | Article + ImageGallery + ImageObject | Microdata **und** JSON-LD | `berichte.html:2,11,23,28,47-67` | ✅ am besten ausgebaut; Microdata + JSON-LD redundant |
| /formcenter (in veranstaltungen) | Organization | Microdata | `veranstaltungen.html:136-146` | ⚠️ Fragment |

**Befund Format-Mix:** Microdata und JSON-LD werden gemischt; teils redundant auf derselben
Seite (verein, berichte). `http://schema.org` (8×) vs. `https://schema.org` (3×) inkonsistent
(beide gültig, aber uneinheitlich). **Empfehlung: durchgängig JSON-LD** (entkoppelt von Markup,
leichter wartbar, Google-Präferenz) und Microdata entfernen.

---

## 2. Pro öffentliche Seite: Title + Description

**Kernbefund:** Keine einzige öffentliche Route in `routes.py`/`formcenter.py` übergibt einen
`title`-Parameter an `render_template`. Verifiziert per grep:

```
$ grep -rn "render_template" app/ | grep -i title
app/errors.py: ... title="..."        # nur Error-Seiten
app/auth/routes.py:33: ... title="Anmelden"   # nur Login (nicht öffentlich relevant)
```

→ **Alle 9 öffentlichen Seiten rendern denselben `<title>`:** `Fv Planetal e.V.`
(da `title` leer ist, bleibt nur `config['APP_NAME']`). Das ist ein klassisches **Duplicate-Title-Problem** und zugleich ein **Branding-Problem** ("Fv" statt "Fahrverein").

| Route | Template | eigener Title? | eigene Description? | H1 | Status |
|-------|----------|:---:|:---:|:---:|--------|
| `/` index | `index.html` | ❌ | ❌ (global) | 1 (if/else) | Duplicate |
| `/verein` | `main/verein.html` | ❌ | ❌ | 1 | Duplicate |
| `/kontakt` | `main/kontakt.html` | ❌ | ❌ | 1 ("Unser Vorstand") | Duplicate |
| `/veranstaltungen` | `main/veranstaltungen.html` | ❌ | ❌ | 1 | Duplicate |
| `/berichte/<jahr>` | `main/berichte.html` | ❌ | ❌ | 1 | Duplicate + nicht in Sitemap |
| `/formcenter/` | `main/formcenter.html` | ❌ | ❌ | 1 | Duplicate |
| `/impressum` | `main/impressum.html` | ❌ | ❌ | 1 | Duplicate (akzeptabel, sollte noindex sein – optional) |
| `/datenschutz` | `main/datenschutz.html` | ❌ | ❌ | 1 | Duplicate (s. o.) |
| `/vereinsdaten` | `main/vereinsdaten.html` | ❌ | ❌ | 1 | Duplicate |

**Empfehlung:** Pro Route `title=...` und (über einen neuen Jinja-Block oder Variable)
`meta_description=...` übergeben. Konkrete Vorschläge in Abschnitt 6.

---

## 3. Technisches On-Page-SEO

### 3.1 Headings
- ✅ **Genau 1× H1 pro Seite** (verifiziert). `index.html` zeigt zwei H1 im Quelltext, aber im
  `{% if/else %}` (eingeloggt/ausgeloggt) rendert nur eine → korrekt.
- ✅ Heading-Hierarchie sauber (H1 → H2 → H3, keine Sprünge). Impressum/Datenschutz nutzen H2/H3
  konsistent.
- ⚠️ `index.html:10` setzt ein `<h2>` ("Ihr Treffpunkt...") **innerhalb** des Subtitle-Blocks
  direkt unter der H1 – valide, aber semantisch eher ein Untertitel; geringfügig.

### 3.2 Alt-Texte
- ✅ Hero/Carousel (`index.html:36-53`), Schriftzug (`veranstaltungen.html:88`, `verein.html:48`):
  beschreibende, keyword-relevante Alt-Texte. Sehr gut.
- ⚠️ **Vorstandsfotos** (`kontakt.html:12`): `alt="{{ mitglied.funktion }}"` → z. B. nur
  "Vorsitzende" statt "Jacquelin Bredt – Vorsitzende Fahrverein Planetal". Name fehlt.
- ⚠️ **Logo** (`nav.html:4`): `alt="Vereinslogo"` generisch; besser "Fahrverein Planetal e.V. Logo".
- ✅ Bericht-Bilder (`berichte.html:31`): Fallback-Alt aus Titel sinnvoll.

### 3.3 Bild-Optimierung (kritisch)

```
app/static/promo1.webp   6000 × 4000 px   1.860.514 Bytes (1,8 MB)
app/static/promo2.webp   5184 × 3456 px     951.678 Bytes
app/static/promo3.webp   5184 × 3456 px     803.292 Bytes
app/static/vereinsschriftzug.webp  960 × 85 px   18.930 Bytes
app/static/logo.webp      197 × 149 px        6.648 Bytes
```

- 🔴 **Die drei Promo-Bilder werden in voller Auflösung (bis 6000 px) ausgeliefert**, obwohl der
  Container max. `h-96` (384 px Höhe) groß ist (`index.html:33`). ~3,6 MB für einen Slider, der
  unter 1600 px Breite braucht. Massive Verschwendung von LCP/Bandbreite, schlechter Core-Web-Vital-Wert.
- 🔴 **Alle drei Slides haben `loading="lazy"`** (`index.html:39,46,53`). Das **erste, sichtbare
  Slide ist das LCP-Element** und darf NICHT lazy sein – `loading="eager"` + `fetchpriority="high"`.
  Die hinteren Slides dürfen lazy bleiben.
- 🔴 **Kein `width`/`height` an irgendeinem `<img>`** (verifiziert: kein einziges `width=`/`height=`-Attribut
  in Templates) → Cumulative Layout Shift (CLS), schlechter Web-Vital.
- 🟡 Kein `srcset`/`sizes` → keine responsive Auslieferung; Mobile lädt dieselben Riesenbilder.
- 🟡 `app/static/uploads/berichte` = **27 MB** – Bericht-Uploads vermutlich ebenfalls unoptimiert
  (es existiert `pic_to_webp.py` als Konvertierungs-Helfer im Repo-Root – sollte konsequent für
  Größenbeschränkung genutzt werden).

**Geschätztes Einsparpotenzial:** Promo-Bilder auf 1600 px / ~150-250 KB → **~90 % kleiner**.

### 3.4 Interne Verlinkung
- ✅ Hauptnav verlinkt verein, berichte (Jahres-Dropdown aus DB, `nav.html:37-44`), kontakt,
  veranstaltungen, formcenter. Footer verlinkt impressum, datenschutz, kontakt.
- ⚠️ `/vereinsdaten` ist **nur** über einen Button auf `/verein` erreichbar (`verein.html:144`),
  nicht über Nav/Footer → schwächere interne Verlinkung, dafür in Sitemap enthalten.
- ⚠️ Kein sichtbarer Link zu `/berichte/<jahr>` außerhalb des JS-Dropdowns; bei deaktiviertem JS
  schlechter crawlbar (Dropdown-Links sind aber im HTML vorhanden, also crawlbar). OK.
- 🟡 Es gibt **keine Übersichtsseite `/berichte`** (nur `/berichte/<jahr>`). Eine Hub-Seite würde
  interne Verlinkung + Sitemap-Struktur verbessern.

### 3.5 Tote/auffällige Dateien
- `app/templates/main/index.html` enthält nur den Text *"This is the /index route of the main folder!"*
  und wird **nicht verwendet** (die `/`-Route rendert `templates/index.html`). Dead Code, harmlos,
  aber aufräumen.

---

## 4. Local SEO

### 4.1 NAP-Konsistenz (Name, Address, Phone) – **inkonsistent**

| Quelle | Adresse | Fundstelle |
|--------|---------|-----------|
| Impressum | Krahner Straße **1**, 14797 Kloster Lehnin OT Reckahn | `impressum.html:12-13` |
| Vereinsdaten | Krahner Straße **03**, 14797 Kloster Lehnin OT Reckahn | `vereinsdaten.html:18-20` |
| Datenschutz | Krahner Str. **1**, 14797 Kloster Lehnin OT Reckahn | `datenschutz.html:11` |
| JSON-LD SportsClub | nur `addressLocality: "Reckahn"`, `addressRegion: "Brandenburg"`, **keine Straße, keine PLZ** | `verein.html:177-182` |

- 🔴 **Hausnummer widersprüchlich (1 vs. 03).** Für Local SEO / Google Business Profile muss NAP
  **exakt identisch** sein. Klären welche korrekt ist und überall vereinheitlichen.
- 🔴 JSON-LD-Adresse ist unvollständig und nennt "Reckahn" als `addressLocality`, amtlich ist die
  Gemeinde **Kloster Lehnin** (OT Reckahn), PLZ **14797**. `streetAddress` + `postalCode` fehlen.
- ⚠️ **Keine Telefonnummer** als zentrale NAP-Angabe (nur einzelne Vorstands-Telefone in DB).
- ⚠️ **Keine Geo-Koordinaten** (`geo`/`latitude`/`longitude`), kein `openingHours`, kein `url`,
  kein `sameAs` (z. B. Facebook/Instagram) im Schema.

### 4.2 LocalBusiness / SportsActivityLocation
- ✅ `SportsClub` (JSON-LD) ist der **passende** Typ für einen Sportverein und enthält bereits
  `event` (Reckahner Kutschertag) + `facility` (SportsActivityLocation Dressurplatz). Gute Basis.
- ⚠️ Nur auf `/verein` vorhanden → erscheint nicht auf der wichtigsten Seite (`/`). Ein zentrales
  Org/LocalBusiness-JSON-LD gehört ins Layout (jede Seite) oder mindestens auf die Startseite.
- ⚠️ `SportsClub` ist **kein** Subtyp von `LocalBusiness`; für lokale Rich Results (Maps, Knowledge
  Panel) empfiehlt sich zusätzlich `LocalBusiness`/`SportsActivityLocation` mit `geo` + `address`,
  oder die Eigenschaften am `SportsClub` voll auszufüllen (address, geo, telephone, url, logo, sameAs).

---

## 5. Priorisierte Maßnahmen

Aufwand: **S** ≤30 min · **M** ≤halber Tag · **L** mehrtägig.

### 🔴 HOCH

| # | Maßnahme | Datei:Zeile | Umsetzung | Aufwand |
|---|----------|-------------|-----------|:---:|
| H1 | **Eindeutige Titles je Seite** | `routes.py` (alle Routen), `layout.html:21` | Jeder Route `title="..."` mitgeben (Werte s. 6.1). `APP_NAME` in `config.py:21` auf "Fahrverein Planetal e.V." korrigieren. | S |
| H2 | **Eindeutige meta descriptions je Seite** | `layout.html:6`, alle Templates | Jinja-Block `{% block meta_description %}` im Layout + Override je Template; oder `meta_description`-Var je Route. Werte s. 6.1. | M |
| H3 | **LCP-Bild nicht lazy + Bilder verkleinern** | `index.html:36-53` | Slide 1: `loading="eager" fetchpriority="high"`. Promo-Bilder offline auf ≤1600 px reskalieren (Tool `pic_to_webp.py` vorhanden). | S (Code) + M (Assets) |
| H4 | **NAP vereinheitlichen** | `impressum.html:12`, `vereinsdaten.html:18`, `datenschutz.html:11`, `verein.html:177` | Hausnummer klären (1 vs. 03), überall identisch. JSON-LD-Adresse vervollständigen (street, PLZ, Ort=Kloster Lehnin). | S |

### 🟡 MITTEL

| # | Maßnahme | Datei:Zeile | Umsetzung | Aufwand |
|---|----------|-------------|-----------|:---:|
| M1 | **`/berichte/<jahr>` in Sitemap** | `routes.py:139-157` | Nach der statischen Schleife die veröffentlichten Bericht-Jahre aus DB ergänzen (`Bericht.jahr distinct`), `lastmod` aus echtem Datum. | M |
| M2 | **`width`/`height` an alle `<img>`** | `index.html`, `verein.html:47`, `veranstaltungen.html:87`, `kontakt.html:11`, `berichte.html:29`, `nav.html:4` | Intrinsische Maße setzen (verhindert CLS). | M |
| M3 | **Zentrales LocalBusiness/SportsClub-JSON-LD** | neu im `layout.html` head oder `index.html` | Vollständiges Snippet (s. 6.2) mit address, geo, telephone, email, url, logo, sameAs, openingHours. | M |
| M4 | **OG/Twitter vervollständigen** | `layout.html:11-15` | `og:url` dynamisch (`request.url`/canonical), `og:site_name`, `og:locale=de_DE`, größeres `og:image` (≥1200×630), `og:image:alt`, Twitter-Card-Tags. | S |
| M5 | **Event-JSON-LD je Termin** | `veranstaltungen.html:28-52` | Pro `termin` valides `Event`-JSON-LD (name, startDate, location als Place mit Adresse, organizer, eventStatus). Microdata ersetzen. | M |
| M6 | **`srcset`/`sizes` für Promo-Bilder** | `index.html:36-53` | Responsive Varianten (z. B. 640/1024/1600 px) generieren und ausliefern. | M |
| M7 | **Marken-Title `Fv` → `Fahrverein`** | `config.py:21` | `APP_NAME` korrigieren (deckt H1/M1 mit ab). | S |

### 🟢 NIEDRIG

| # | Maßnahme | Datei:Zeile | Aufwand |
|---|----------|-------------|:---:|
| N1 | Vorstands-Alt-Texte um Namen ergänzen | `kontakt.html:12` | S |
| N2 | Logo-Alt präzisieren ("Fahrverein Planetal e.V. Logo") | `nav.html:4` | S |
| N3 | Microdata vs. JSON-LD vereinheitlichen (durchgängig JSON-LD) | verein/berichte/veranstaltungen | M |
| N4 | `meta keywords` entfernen (obsolet) | `layout.html:7` | S |
| N5 | leeres `Organization`-Microdata am `<html>` befüllen oder entfernen | `layout.html:2` | S |
| N6 | `/berichte`-Hub-Übersichtsseite | neue Route/Template | M |
| N7 | Impressum/Datenschutz auf `noindex` (dünner Pflicht-Content) | routes/layout | S |
| N8 | toten Stub `app/templates/main/index.html` entfernen | – | S |
| N9 | http→https schema.org vereinheitlichen | diverse | S |

### Quick-Wins (≤1 h, größter Hebel)
1. `APP_NAME` korrigieren + `title=` je Route (H1/M7) → behebt Duplicate Titles **und** Branding.
2. LCP-Slide `eager`/`fetchpriority` + Promo-Bilder reskalieren (H3).
3. NAP-Hausnummer vereinheitlichen (H4).

### Größere Maßnahmen
- Vollständiges, zentrales LocalBusiness-JSON-LD + Event-JSON-LD (M3/M5).
- Responsive-Image-Pipeline mit `srcset` (M6) und Sitemap-Erweiterung um DB-Inhalte (M1).

---

## 6. Vorlagen

### 6.1 Konkrete Titles + Descriptions je Seite

> Title-Länge ~50-60 Zeichen, Description ~140-160 Zeichen. Brand-Suffix " – Fahrverein Planetal e.V."
> kommt automatisch aus dem Layout-Pattern, daher unten **nur der `title`-Teil ohne Suffix**.

| Route | `title=` (ohne Suffix) | meta_description |
|-------|------------------------|------------------|
| `/` | `Kutschfahrten & Reitsport in Reckahn` | Fahrverein Planetal e.V. in Reckahn (Brandenburg): Kutschfahrten, Reitsport, Ausfahrten und der jährliche Kutschertag. Seit 2012 für Pferdefreunde jeden Alters. |
| `/verein` | `Über den Verein` | Lernen Sie den Fahrverein Planetal e.V. kennen: 25 Pferdefreunde, Jugendarbeit, Dressurplatz und Fahrsport-Tradition seit 2012 in Reckahn, Hoher Fläming. |
| `/kontakt` | `Vorstand & Kontakt` | Kontakt zum Fahrverein Planetal e.V. in Reckahn: Vorstand, Ansprechpartner und Anfragen rund um Kutschfahrten, Reitsport und Mitgliedschaft. |
| `/veranstaltungen` | `Veranstaltungen & Termine` | Aktuelle Termine, Trainingstage und der Reckahner Kutschertag des Fahrvereins Planetal e.V. Jetzt Fahrsport-Veranstaltungen in Brandenburg entdecken. |
| `/berichte/<jahr>` | `Erlebnisberichte {{ jahr }}` | Fotos und Berichte aus {{ jahr }} vom Fahrverein Planetal e.V.: Kutschfahrten, Turniere und Kutschertag in Reckahn, Brandenburg. |
| `/formcenter/` | `Formularcenter` | Offizielle Nennungs- und Aufgabenformulare des Fahrvereins Planetal e.V. zum Download – u. a. für den Reckahner Kutschertag. |
| `/vereinsdaten` | `Vereinsdaten & Mitgliedschaft` | Geschäftsadresse, Bankverbindung, Register- und Mitgliedsdaten des Fahrvereins Planetal e.V. in Reckahn (Kloster Lehnin), Brandenburg. |
| `/impressum` | `Impressum` | Impressum und Anbieterkennzeichnung des Fahrvereins Planetal e.V., Krahner Straße, 14797 Kloster Lehnin OT Reckahn. |
| `/datenschutz` | `Datenschutz` | Datenschutzerklärung des Fahrvereins Planetal e.V. gemäß DSGVO: verarbeitete Daten, Zwecke, Rechtsgrundlagen und Ihre Rechte. |

**Umsetzungsskizze (Beispiel, KEINE Änderung – nur Vorlage):**
```python
# routes.py
@main.route("/verein")
def verein():
    return render_template(
        "main/verein.html",
        title="Über den Verein",
        meta_description="Lernen Sie den Fahrverein Planetal e.V. kennen: ...",
    )
```
```jinja
{# layout.html – description-Block statt statischer Zeile #}
<meta name="description"
      content="{{ meta_description | default('Fahrverein Planetal e.V. in Reckahn (Brandenburg): Kutschfahrten, Reitsport und der jährliche Kutschertag.') }}">
```

### 6.2 Vollständiges LocalBusiness / SportsClub JSON-LD (Vorlage fürs Layout/Startseite)

> Hausnummer **vor Verwendung verifizieren** (Impressum=1 vs. Vereinsdaten=03). Geo-Koordinaten
> aus Google Maps für die exakte Adresse einsetzen. `sameAs` mit echten Social-Profilen füllen
> oder entfernen.

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": ["SportsClub", "SportsActivityLocation"],
  "@id": "https://fahrverein-planetal.de/#organization",
  "name": "Fahrverein Planetal e.V.",
  "alternateName": "FV Planetal e.V.",
  "description": "Pferdesportverein in Reckahn (Hoher Fläming) mit Schwerpunkt Kutschfahrten und Reitsport. Aktive Jugendarbeit, Trainings und der jährliche Reckahner Kutschertag.",
  "url": "https://fahrverein-planetal.de",
  "logo": "https://fahrverein-planetal.de/static/logo.webp",
  "image": "https://fahrverein-planetal.de/static/promo1.webp",
  "foundingDate": "2012",
  "email": "kontakt@fahrverein-planetal.de",
  "telephone": "+49-XXXX-XXXXXXX",
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "Krahner Straße 1",
    "postalCode": "14797",
    "addressLocality": "Kloster Lehnin",
    "addressRegion": "Brandenburg",
    "addressCountry": "DE"
  },
  "geo": {
    "@type": "GeoCoordinates",
    "latitude": 52.31,
    "longitude": 12.66
  },
  "areaServed": {
    "@type": "AdministrativeArea",
    "name": "Hoher Fläming, Brandenburg"
  },
  "sport": ["Fahrsport", "Reitsport", "Kutschfahren"],
  "memberOf": {
    "@type": "Organization",
    "name": "Landessportbund Brandenburg"
  },
  "subOrganization": {
    "@type": "SportsActivityLocation",
    "name": "Dressurplatz Reckahn",
    "description": "80×40 m Dressurplatz für Training und Wettkämpfe im Fahrsport"
  },
  "event": {
    "@type": "SportsEvent",
    "name": "Reckahner Kutschertag",
    "description": "Jährliches Fahrsport-Event mit Dressurprüfungen und Hindernisfahren",
    "location": {
      "@type": "Place",
      "name": "Fahrverein Planetal e.V.",
      "address": {
        "@type": "PostalAddress",
        "streetAddress": "Krahner Straße 1",
        "postalCode": "14797",
        "addressLocality": "Kloster Lehnin",
        "addressCountry": "DE"
      }
    }
  },
  "sameAs": [
    "https://www.facebook.com/<profil>",
    "https://www.instagram.com/<profil>"
  ]
}
</script>
```

### 6.3 Event-JSON-LD je Termin (Vorlage für veranstaltungen.html)

```jinja
{% for termin in termine %}
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Event",
  "name": "{{ termin.titel }}",
  "startDate": "{{ termin.datum.isoformat() }}",
  "eventStatus": "https://schema.org/EventScheduled",
  "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
  {% if termin.beschreibung %}"description": {{ termin.beschreibung | striptags | tojson }},{% endif %}
  "location": {
    "@type": "Place",
    "name": {{ (termin.ort or 'Fahrverein Planetal e.V., Reckahn') | tojson }},
    "address": {
      "@type": "PostalAddress",
      "addressLocality": "Kloster Lehnin",
      "addressRegion": "Brandenburg",
      "addressCountry": "DE"
    }
  },
  "organizer": {
    "@type": "Organization",
    "name": "Fahrverein Planetal e.V.",
    "url": "https://fahrverein-planetal.de"
  }
}
</script>
{% endfor %}
```

### 6.4 Sitemap-Erweiterung um Berichte (Skizze)

```python
# nach der statischen Routen-Schleife in generate_sitemap():
jahre = (db.session.query(Bericht.jahr)
         .filter_by(veroeffentlicht=True).distinct()
         .order_by(Bericht.jahr.desc()).all())
for (jahr,) in jahre:
    url = f"{base_url}/berichte/{jahr}"
    sitemap_xml += "  <url>\n"
    sitemap_xml += f"    <loc>{url}</loc>\n"
    sitemap_xml += "    <changefreq>yearly</changefreq>\n"
    sitemap_xml += "    <priority>0.6</priority>\n"
    sitemap_xml += "  </url>\n"
```

---

## 7. Validierungs-/Test-Empfehlungen (nach Umsetzung)

- **Google Rich Results Test** + **Schema.org Validator** für JSON-LD (verein, veranstaltungen, berichte, Startseite).
- **PageSpeed Insights / Lighthouse**: LCP (Promo-Bild), CLS (width/height), Total Byte Weight.
- `curl -s https://fahrverein-planetal.de/sitemap.xml | xmllint --noout -` → XML valide + enthält `/berichte/*`.
- Crawl mit Screaming Frog: prüfen, dass alle 9 Seiten **unterschiedliche** Title + Description haben (Duplicate-Report leer).
- NAP-Abgleich: Impressum = Vereinsdaten = Datenschutz = JSON-LD = Google Business Profile.
