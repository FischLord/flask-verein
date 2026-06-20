# Slider- & Veranstaltungs-Review – Fahrverein Planetal e.V.

> Rolle: Frontend-Debugging- & Layout-Spezialist
> Modus: **Nur Analyse, keine Code-Änderungen.**
> Stand: 2026-06-20
> Geprüft (vollständig gelesen, nicht geraten):
> `app/templates/index.html` (echter Slider!), `app/templates/main/index.html` (Stub),
> `app/templates/main/veranstaltungen.html`, `app/main/routes.py`, `app/main/formcenter.py`,
> `app/templates/main/formcenter.html`, `app/models.py` (Termin), `app/static/js/nav.js`,
> `app/static/css/site.css`, `app/templates/boilerplate/layout.html`,
> `app/static/vendor/flowbite/flowbite.min.{js,css}` (Carousel-Logik + Klassen-Purge verifiziert),
> DB-Inhalt `app.db` (Tabelle `termine`), `app/static/forms/`, `app/static/promo{1,2,3}.webp`.

---

## 0. Kernaussage / TL;DR

**A) Slider-Bug "Bild 1 auf Bild 3 komische Bewegungen":**
Der Slider steckt **nicht** in `app/templates/main/index.html` (das ist nur ein Platzhalter mit dem Text *"This is the /index route of the main folder!"*), sondern in **`app/templates/index.html`** – diese Datei wird von der Route `/` gerendert (`app/main/routes.py:11-13`).

Es ist ein **Flowbite-Carousel mit exakt 3 Slides** (`data-carousel="static"`). Die Ursache des Bugs ist **kein** CSS-Purge-Problem (alle nötigen Klassen existieren in der gepurgten CSS) und auch keine Doppel-Initialisierung. Es ist der **klassische Flowbite-„3-Slide-Sweep"**: Bei genau 3 Bildern sind *links + Mitte + rechts* gleichzeitig **alle** Slides – keiner bleibt `hidden`. Beim Weiterschalten muss derjenige Slide, der von der einen Außenkante zur gegenüberliegenden wechselt, **mit `transition-transform` über die volle Breite (200 %) durchs Bild fahren**. Sichtbar als „Geister-Sweep" von Bild 3 (bzw. Bild 2), genau wenn man zwischen Bild 1 und Bild 3 wechselt. → Fix-Richtung: **Fade-Carousel** (Opacity statt Translate) oder eigener Mini-Slider; Schnell-Repro: 4. Slide ergänzen, dann verschwindet der Sweep sofort.

**B) Veranstaltungen wirkt überladen:**
Eine einzige Seite mischt **vier völlig verschiedene Inhaltstypen** mit identischem Karten-Styling (alles `p-6 bg-white rounded-lg shadow border`): dynamische DB-Termine, statische „Entwicklungsprojekte" (Vision), ein riesiges Branding-Bild, und einen **statischen Download-Block, dessen 3 PDF-Links alle ins Leere führen (404)** und der den vorhandenen `/formcenter` dupliziert. Dazu fehlen Hierarchie, Datums-Chips und eine Trennung kommende/vergangene Termine. Aktuell sind **0 Termine** in der DB → Besucher sehen nur den Leer-Platzhalter, dann Vision-Texte, ein großes Logo und kaputte Downloads.

---

# TEIL A — STARTSEITEN-SLIDER

## A.1 Wo der Slider wirklich liegt (Korrektur zum Auftrag)

| Annahme im Auftrag | Realität |
|---|---|
| Slider in `app/templates/main/index.html` | **Falsch.** Diese Datei ist ein 1-Zeilen-Stub (`This is the /index route of the main folder!`) und wird **nirgends gerendert**. |
| — | Route `/` → `render_template("index.html")` (`app/main/routes.py:12-13`) → **`app/templates/index.html`**. Dort steht das Carousel (Zeilen **31–73**). |

`app/templates/index.html:31-73` enthält das Markup. `flowbite.min.js` wird **einmal** in `boilerplate/layout.html:43` (am `</body>`) geladen. `nav.js` betrifft nur das Nav-Dropdown – **keine** Carousel-Berührung, also **keine Doppel-Initialisierung**.

## A.2 Faktenlage der Implementierung

Markup (gekürzt, `app/templates/index.html`):

```html
31  <div id="promo-carousel" class="relative w-full mb-8" data-carousel="static">
33    <div class="relative h-56 overflow-hidden rounded-lg md:h-96">
35      <div class="hidden duration-700 ease-in-out" data-carousel-item>
36        <img src=".../promo1.webp" class="absolute block w-full h-full object-cover" ... loading="lazy">
42      <div class="hidden duration-700 ease-in-out" data-carousel-item> ... promo2.webp ...
49      <div class="hidden duration-700 ease-in-out" data-carousel-item> ... promo3.webp ...
57    <button ... data-carousel-prev> ...
65    <button ... data-carousel-next> ...
```

Wichtige Eigenschaften:

1. **Genau 3 `data-carousel-item`.**
2. **Kein** `data-carousel-item="active"` an einem Slide → Flowbite `defaultPosition = 0` (Slide 1 startet aktiv). Das ist ok, aber undeterministisch dokumentiert.
3. **`data-carousel="static"`** → **kein** Autoplay (`cycle()` wird nicht aufgerufen). Der Bug ist also rein **klick-/transition-getrieben**, kein Timer.
4. Auto-Init von Flowbite hängt am **`load`-Event** (nicht `DOMContentLoaded`): am Bundle-Ende steht
   `new Events("load",[...,initCarousels,...]).init()`. Bei den großen Bildern (s. A.5) initialisiert das Carousel also erst **spät** (nach allen Bild-Loads).

## A.3 Was Flowbite zur Laufzeit macht (aus `flowbite.min.js` verifiziert)

Bei Init fügt Flowbite **jedem** Item hinzu:
```
classList.add("absolute","inset-0","transition-transform","transform")
```
Dann `slideTo(active)`. Die Kern-Logik (Originalcode, leicht formatiert):

```js
slideTo(t){
  e = items[t];
  i = {
    left:   e.position===0          ? items[len-1] : items[e.position-1],
    middle: e,
    right:  e.position===len-1      ? items[0]     : items[e.position+1]
  };
  _rotate(i); ...
}
_rotate(t){
  this._items.map(x => x.el.classList.add("hidden"));         // erst ALLE ausblenden
  t.left.el  .classList.add("-translate-x-full","z-10");      // parkt LINKS  (-100%)
  t.middle.el.classList.add("translate-x-0","z-20");          // MITTE sichtbar (0%, oben)
  t.right.el .classList.add("translate-x-full","z-10");       // parkt RECHTS (+100%)
}
next(){ pos===len-1 ? items[0] : items[pos+1]; slideTo(...) } // Wrap-around
prev(){ pos===0     ? items[len-1] : items[pos-1]; slideTo(...) }
```

**Klassen-Check in `flowbite.min.css` (gepurgt) — alle vorhanden:**

| Klasse | Selektor in CSS | Status |
|---|---|---|
| `-translate-x-full` | `.-translate-x-full{--tw-translate-x:-100%}` | ✅ vorhanden |
| `translate-x-full` | `.translate-x-full{--tw-translate-x:100%}` | ✅ |
| `translate-x-0` | `.translate-x-0{--tw-translate-x:0px}` | ✅ |
| `transition-transform` | ✅ | ✅ |
| `transform` | ✅ | ✅ |
| `duration-700`, `ease-in-out` | ✅ / ✅ | ✅ |
| `absolute`, `inset-0`, `hidden`, `block` | ✅ alle | ✅ |
| `z-10`, `z-20`, `z-30` | ✅ alle | ✅ |
| `h-56`, `md:h-96` | ✅ / ✅ | ✅ |

→ **Befund: Die CSS ist NICHT die Ursache.** Anders als beim Galerie-Review (dort fehlten `hover:scale-105`, `prose` etc.) sind hier **alle** Carousel-relevanten Utilities im Purge erhalten geblieben. Das Carousel *animiert* also korrekt – das ist gerade das Problem.

## A.4 Root-Cause: der „3-Slide-Sweep" (konkrete Reproduktion)

Slides: **A=promo1 (pos0), B=promo2 (pos1), C=promo3 (pos2)**. Jedes Item trägt
`transition-transform transform duration-700 ease-in-out` → **jede** Translate-Änderung wird über 700 ms **animiert**.

**Startzustand S0 (A aktiv):**
```
left = C → -translate-x-full (-100 %, links geparkt)
mid  = A → translate-x-0     (   0 %, sichtbar, z-20)
right= B → translate-x-full  (+100 %, rechts geparkt)
```
Bei 3 Items ist `left+middle+right` = **alle 3** → **kein** Item bleibt `hidden`. Genau hier liegt der Defekt.

**Klick „weiter" (A→B):** Ziel B, neue Zuordnung
```
left = A → -100 %   (A schiebt sauber nach links raus)        ✓
mid  = B →    0 %   (B schiebt sauber von rechts rein)        ✓
right= C → +100 %   ABER: C war eben noch bei -100 % (links)!
```
→ **C (Bild 3) animiert von -100 % nach +100 %, also volle 200 % quer durchs Bild** (unter B, weil z-10 < z-20). Das ist die „komische Bewegung": **Bild 3 fliegt quer durch, sobald man von Bild 1 weg/zu Bild 3 schaltet.**

**Klick „zurück" (A→C, Wrap-around):** Ziel C
```
left = B → -100 %   ABER: B war eben bei +100 % (rechts)!  → B fegt 200 % quer
mid  = C →    0 %   (C rein von links)                         ✓
right= A → +100 %   (A raus nach rechts)                       ✓
```
→ Beim direkten Sprung **Bild 1 ↔ Bild 3** fegt jeweils der dritte, „unbeteiligte" Slide über die volle Breite. **Das ist exakt das vom Kunden beschriebene Symptom.**

**Warum tritt das bei „normalen" Flowbite-Carousels nicht auf?** Bei ≥ 4 Slides bleibt der gegenüberliegende Slide auf `hidden` (`display:none`) und kann nicht sichtbar mitfegen. **Nur bei exakt 3 Slides** ist jeder Slide immer Teil des `left/middle/right`-Tripels → keiner ist je `hidden` → der Kanten-Wechsler fegt sichtbar durch. Bekanntes Flowbite-Verhalten bei 3-Bild-Carousels.

### Schnell-Repro / Hypothese-Verifikation (für den Entwickler)
- **Beweis A:** Temporär einen **4. `data-carousel-item`** einfügen → der Sweep verschwindet sofort (4. Slide bleibt beim Schalten `hidden`). Bestätigt: 3-Slide-Window ist die Ursache.
- **Beweis B:** In DevTools beim Klick die 3 Item-Divs beobachten → man sieht, wie ein nicht-benachbarter Slide von `-translate-x-full` auf `translate-x-full` wechselt (200 %-Animation), statt `hidden` zu bleiben.

## A.5 Empfohlene Fix-Richtung (3 Optionen, ohne TW-Build)

**Option 1 – Fade statt Slide (empfohlen, robust):** Den Translate-Mechanismus durch Cross-Fade ersetzen. Die nötigen Klassen sind im Purge **vorhanden**: `opacity-0` ✅, `opacity-100` ✅, `transition-opacity` ✅, `duration-700` ✅ (`duration-1000` fehlt → 700 nutzen).
- Saubere Variante: **eigener Mini-Slider** (~30 Zeilen) als `app/static/js/slider.js`, der die 3 Items per `opacity`/`z-index` ein-/ausblendet (kein Flowbite-Carousel für dieses Widget). Beseitigt den Sweep vollständig, deterministisch, plus optionales Autoplay via `setInterval` + Pause-on-hover. Aufwand **M**.

**Option 2 – Flowbite behalten, Transform neutralisieren (kleinster Eingriff):** In `site.css` für `#promo-carousel [data-carousel-item]` `transform:none` erzwingen und stattdessen Opacity an `z-20` (Mitte) koppeln. Stoppt den Sweep; echtes Faden braucht aber zusätzliche Logik, da Flowbite nur Translate/`z`-Klassen toggelt, nicht Opacity. Aufwand **S–M**, etwas „hacky".

**Option 3 – Mehr Slides (nur als Workaround/Beweis):** ≥ 4 Slides → Sweep weg, aber inhaltlich nur sinnvoll, wenn es mehr echte Promo-Bilder gibt. Aufwand **S**, keine echte Lösung.

**Begleit-Fixes am Slider (unabhängig vom Bug):**
- `app/templates/index.html:39` – **promo1 nicht `loading="lazy"`**: Slide 1 ist der LCP/above-the-fold. `loading="lazy"` + spätes `load`-Init verzögert das erste Bild. → erstes Bild `loading="eager"`/`fetchpriority="high"`, restliche lazy.
- **Bildgrößen absurd:** promo1 = **6000×4000 px / 1,8 MB**, promo2/3 = 5184×3456. Angezeigt wird ein Kasten `h-56`/`md:h-96` (max ~384 px hoch). → auf ~1600 px Breite runterskalieren (Projekt hat bereits `pic_to_webp.py`). Spart ~3–4 MB pro Startseiten-Load.
- **Kein `data-carousel-item="active"`** gesetzt (`index.html:35`). Funktioniert (default 0), sollte aber explizit am ersten Slide stehen für deterministischen Erststand.
- **Keine Indikatoren/Pagination** (`data-carousel-slide-to`) – optional, verbessert Orientierung bei 3 Bildern.

---

# TEIL B — VERANSTALTUNGEN / TERMINE

## B.1 Faktenlage: Seitenaufbau `app/templates/main/veranstaltungen.html`

| Block | Zeilen | Typ | Problem |
|---|---|---|---|
| Header (h1 `text-5xl` + p) | 6–13 | statisch | h1 sehr groß; ok |
| „Wichtiger Hinweis" (blaue Box) | 16–20 | statisch | nutzt **`border-l-4`** → **fehlt in gepurgter CSS** → linker Akzentstrich rendert nicht; generischer Füll-Hinweis |
| „Unsere Termine" (DB-Loop) | 23–63 | **dynamisch** | aktuell **0 Termine** in DB → nur Leer-Platzhalter sichtbar |
| → Termin-Karte | 29–52 | dynamisch | `opacity-75` (abgelaufen) **fehlt in CSS**; `prose max-w-none` (Beschreibung) **`prose` fehlt** → HTML-Beschreibung ohne Typografie |
| „Entwicklungsprojekte" (2 Karten) | 66–83 | **hardcodiert** | Vision/About-Inhalt, kein „Termin"; lange Texte; Tippfehler |
| Großes Bild `vereinsschriftzug.webp` | 86–91 | statisch | Branding mitten im Event-Flow, schiebt Inhalt runter |
| „Anmeldung & Formulare Kutschertag" | 94–148 | **hardcodiert** | dupliziert `/formcenter`; **3 PDF-Links → 404** |
| → 3 Download-Karten | 103–134 | hardcodiert | s. B.3 (alle Dateien fehlen) |
| Anmeldewege-Liste | 136–146 | statisch | ok |

Route: `app/main/routes.py:82-90` – `Termin.query.filter_by(veroeffentlicht=True).order_by(Termin.datum.asc())`. **Keine** Trennung kommende/vergangene; abgelaufene Termine werden mitgeladen und nur per (nicht renderndem) `opacity-75` + Badge markiert.

## B.2 Warum es überladen / unaufgeräumt wirkt (Diagnose)

1. **Vier Themen auf einer Seite ohne Trennung:** echte Termine + Zukunftsvision + Branding-Bild + Download-Center. Das sind eigentlich 3–4 verschiedene Seiten/Sektionen.
2. **Monotones Karten-Einerlei:** **jeder** Block ist `p-6 bg-white rounded-lg shadow border border-gray-200` (Zeilen 29, 56, 69, 75, 96). Alles gleich schwer → keine visuelle Hierarchie, „Wand aus weißen Kästen".
3. **Überschriften zu groß & repetitiv:** drei `h2 text-3xl` (24, 67, 95), viele `h3 text-2xl`. Auf Mobile fressen die Headlines den Schirm.
4. **Lange Fließtexte** in Projekten (72, 77–80) und Formular-Intro (97–100) = Textwände statt scanbarer Infos.
5. **Keine Datums-Optik:** Termine sind reine Listen `Datum:/Uhrzeit:/Ort:` (42–46). Kein Tag/Monat-Chip, nichts schnell Erfassbares.
6. **Keine Trennung kommende vs. vergangene Termine:** flache `space-y-6`-Liste, abgelaufene mittendrin; der Faded-Effekt (`opacity-75`) rendert nicht mal.
7. **Redundanz + Defekt:** Der Download-Block (94–148) macht dasselbe wie `/formcenter` (das PDFs **dynamisch** auflistet), nur hardcodiert und mit **toten Links** (B.3).
8. **Branding-Bild als Fremdkörper:** `vereinsschriftzug.webp` (86–91) zwischen Terminen und Downloads bricht den Lesefluss.
9. **CSS-Purge-Lücken** (gleiche Grundursache wie Review 01/02 – kein TW-Build): `border-l-4`, `opacity-75`, `prose` fehlen in `flowbite.min.css` → Hinweis-Box, Abgelaufen-Dimmen und Termin-Beschreibungstypografie sind **optisch tot**.

## B.3 Harter Defekt: tote Download-Links (404)

`app/static/forms/` enthält **nur** `Dokuments.rar` (1,5 MB). Die drei verlinkten Dateien existieren **nicht**:

| Link (`veranstaltungen.html`) | Datei | Status |
|---|---|---|
| Zeile 107 | `forms/FA-2 Fahraufgabe.pdf` | ❌ 404 |
| Zeile 117 | `forms/Nennungsformular Fahrer 2023.pdf` | ❌ 404 |
| Zeile 127 | `forms/Nennungsformular Reiter 2023.pdf` | ❌ 404 |

→ Alle drei „Herunterladen"-Buttons liefern 404. (Zusätzlich: `/formcenter` zeigt aktuell **gar keine PDFs**, weil im Ordner nur eine `.rar` liegt – `formcenter.py:13` erlaubt nur `pdf`.)

## B.4 Inhaltliche Kleinfehler

- `veranstaltungen.html:79` – Tippfehler **„Taum"** → „Raum".
- `veranstaltungen.html:72` – typografische Quotes `„Dachdeckerhindernis"` mit „ … " gemischt; inkonsistent.

## B.5 Konkreter Strukturvorschlag (Soll)

**Reihenfolge & Gruppierung (oben → unten):**
1. **Kompakter Header** (h1 auf `text-3xl md:text-4xl` runter), kurzer Subtext. Optional Anker-Chips („Kommende Termine · Downloads").
2. **Kommende Termine** = Primärsektion. Karten-Grid `grid-cols-1 md:grid-cols-2` mit:
   - **Datums-Chip** (Tag groß / Monat klein, z. B. links als farbiger Block),
   - Titel, Ort (Icon), Uhrzeit, 1–2 Zeilen Kurzbeschreibung (truncate),
   - optional CTA „Details/Anmelden".
   - Route: nur `datum >= today` (s. B.6).
3. **Vergangene Termine** = sekundär: in `<details>` (zugeklappt) oder gedämpfte Mini-Liste / Link „Archiv". Route: `datum < today`.
4. **„Wichtiger Hinweis"** entfernen oder als dezente Inline-Notiz an die Termin-Sektion hängen (nicht als eigene große Box mit kaputtem `border-l-4`).
5. **Entwicklungsprojekte/Vision** → **raus aus dieser Seite**: gehört nach `/verein` („Über uns / Ausblick"). Falls hier bleibend: klar abgetrennt unter einem Divider, leichteres Styling (kein voller Card-Block, z. B. 2-spaltige schlanke Liste), Texte kürzen.
6. **Großes Schriftzug-Bild** entfernen (oder in Footer/Hero verschieben) – kein Event-Inhalt.
7. **Downloads** zu **einem** schlanken Callout zusammenfassen: ein Button „Alle Formulare im Formularcenter" → `/formcenter` (das listet PDFs ohnehin dynamisch). Den hardcodierten 3-Karten-Block entfernen. **Voraussetzung:** die echten PDFs in `app/static/forms/` ablegen, sonst bleibt es leer/404.
8. **Anmeldewege** (WhatsApp/E-Mail) als kompakte Box am Seitenende behalten.

**Card-Design Termine (Beispielstruktur, mobile-first):**
```
[ 12 ]  Kutschertag 2026
[ OKT]  📍 Reckahn · 🕒 10:00 Uhr
        Kurzbeschreibung … (max-w, line-clamp-2)        [Details →]
```
Datums-Chip aus `termin.datum.strftime('%d')` / `'%b'`; vorhandene Klassen (`rounded-lg`, `shadow`, `grid-cols-1`, `md:grid-cols-2` ✅ alle im Purge) genügen. **Achtung:** `prose`, `opacity-75`, `border-l-4`, `line-clamp-*` fehlen im Purge → entweder vermeiden oder in `site.css` nachliefern (gleicher Mechanismus wie die bereits dort ergänzten `lg:`-Klassen).

## B.6 Route-Verbesserung (für die Trennung)

`app/main/routes.py:82-90` so erweitern, dass kommende/vergangene getrennt ans Template gehen:
```python
heute = date.today()
kommende  = Termin.query.filter_by(veroeffentlicht=True)\
              .filter(Termin.datum >= heute).order_by(Termin.datum.asc()).all()
vergangene= Termin.query.filter_by(veroeffentlicht=True)\
              .filter(Termin.datum <  heute).order_by(Termin.datum.desc()).all()
```
(Die `abgelaufen`-Property in `models.py:73-76` existiert bereits und kann clientseitig weiter genutzt werden.)

---

## C. Priorisierte Empfehlungen

Aufwand: **S** ≤ 1 h · **M** ≤ halber Tag · **L** > 1 Tag.

### Hoch
| # | Thema | Datei:Zeile | Aufwand | Maßnahme |
|---|---|---|---|---|
| H1 | **Slider-Sweep-Bug** | `app/templates/index.html:31-55` (+ neue `static/js/slider.js`) | M | Fade-Slider statt Flowbite-Translate (Opacity-Klassen vorhanden). Repro/Beweis vorab: 4. Slide testweise → Sweep weg. |
| H2 | **Tote PDF-Downloads (404)** | `veranstaltungen.html:107,117,127` + `app/static/forms/` | S | Entweder echte PDFs ablegen **oder** Block durch Link auf `/formcenter` ersetzen. |
| H3 | **Termine kommende/vergangene trennen** | `routes.py:82-90` + `veranstaltungen.html:23-63` | M | Route splitten (B.6), vergangene in `<details>`/Archiv. |
| H4 | **Promo-Bilder verkleinern + LCP** | `index.html:36-39`; `static/promo*.webp` | S | promo1 6000×4000/1,8 MB → ~1600 px; erstes Bild `eager`/`fetchpriority=high`, Rest lazy. |

### Mittel
| # | Thema | Datei:Zeile | Aufwand | Maßnahme |
|---|---|---|---|---|
| M1 | **Card-Redesign Termine** (Datums-Chip, Grid, Hierarchie) | `veranstaltungen.html:27-54` | M | scanbare Karten `grid-cols-1 md:grid-cols-2`, Tag/Monat-Chip. |
| M2 | **Entwicklungsprojekte verschieben** | `veranstaltungen.html:66-83` → `main/verein.html` | M | Vision raus aus Events; Texte kürzen. |
| M3 | **Download-Block entschlacken** (Dedupe zu `/formcenter`) | `veranstaltungen.html:94-148` | S | einen Callout-Button statt 3 hardcodierter Karten. |
| M4 | **CSS-Purge-Lücken nachliefern** | `static/css/site.css` (+ Nutzung in `veranstaltungen.html:16,29,50`) | S | `border-l-4`, `opacity-75`, (`prose`-Minimalsatz) ergänzen – analog vorhandener `lg:`-Fixes. |
| M5 | **`data-carousel-item="active"` setzen** | `index.html:35` | S | deterministischer Erststand. |

### Niedrig
| # | Thema | Datei:Zeile | Aufwand | Maßnahme |
|---|---|---|---|---|
| N1 | Tippfehler „Taum"→„Raum" | `veranstaltungen.html:79` | S | Textkorrektur. |
| N2 | Quotes vereinheitlichen | `veranstaltungen.html:72` | S | konsistente Typografie. |
| N3 | „Wichtiger Hinweis" entfernen/abschwächen | `veranstaltungen.html:16-20` | S | generischen Füll-Hinweis kürzen/inline. |
| N4 | Großes Schriftzug-Bild entfernen/verschieben | `veranstaltungen.html:86-91` | S | nicht eventrelevant. |
| N5 | Slider-Indikatoren (Pagination) | `index.html:31-73` | S | `data-carousel-slide-to`-Punkte für Orientierung. |
| N6 | Header h1 verkleinern | `veranstaltungen.html:7` | S | `text-5xl` → `text-3xl md:text-4xl`. |
| N7 | Stub aufräumen | `app/templates/main/index.html` | S | ungenutzte Platzhalterdatei (verwirrt: enthält Hinweis auf „/index", ist aber tot) entfernen/dokumentieren. |

---

## D. Slider-Bug – Kurzfassung für den Entwickler

- **Datei:** `app/templates/index.html:31-73` (NICHT `main/index.html`).
- **Symptom:** Beim Wechsel zwischen Bild 1 und Bild 3 fegt ein dritter Slide über die volle Breite.
- **Ursache:** Flowbite-`_rotate` hält bei **genau 3 Slides** *alle* drei als `left/middle/right` aktiv (keiner `hidden`). Der Kanten-Wechsler animiert mit `transition-transform duration-700` von `-translate-x-full` nach `translate-x-full` (200 % Sweep). **Kein** CSS-Purge-Fehler (alle Klassen vorhanden), **keine** Doppel-Init, **kein** Autoplay (`data-carousel="static"`).
- **Repro/Beweis:** 4. `data-carousel-item` ergänzen → Sweep verschwindet (der Nicht-Nachbar bleibt `hidden`).
- **Fix:** Cross-Fade statt Translate (Opacity-Klassen sind im Purge vorhanden) – am saubersten als kleiner eigener Slider; alternativ in `site.css` `transform:none` für `#promo-carousel [data-carousel-item]` erzwingen und Sichtbarkeit über `z`/Opacity steuern.
