# UX/UX-Rework – Master-Synthese & Umsetzungsplan

**Stand:** 2026-06-20 · **Phase:** Analyse abgeschlossen, Umsetzung ausstehend
**Basis:** 5 Detail-Reports (01 UI/UX · 02 Galerie · 03 Slider/Veranstaltungen · 04 Content · 05 SEO)

---

## 🔑 Der eine rote Faden (betrifft 4 von 5 Reports)

**Die ausgelieferte `app/static/vendor/flowbite/flowbite.min.css` ist „gepurged".**
Sie enthält nur die Klassen, die beim ursprünglichen Build erkannt wurden. **Sehr viele
in den Templates genutzte Klassen existieren darin gar nicht** und rendern deshalb **nicht**:

| Tote Klasse (verifiziert MISSING) | Folge | Report |
|---|---|---|
| `focus-visible:ring-2` (+ `focus:outline-none`) | **Keine Fokusringe** → Tastatur-A11y kaputt | 01 |
| `hover:scale-105`, `hover:shadow-xl` | Kein Karten-/Galerie-Hover-Effekt | 01, 02 |
| `prose` | Berichts-/Termin-Texte ohne Typografie | 02, 03 |
| `border-l-4`, `opacity-75` | Hinweisbox + „Abgelaufen"-Dimmen fehlen | 03 |
| `scale-95/100` | Dropdown-Animation springt statt smooth | 01 |
| `columns-*`, `md:col-span-2`, `max-h-60` | Layout-Defekte | 01, 02 |

**Konsequenz:** Jede neue Design-Verbesserung mit Tailwind-Klassen **verpufft**, solange
das nicht gelöst ist. → **Das ist Entscheidung #1, bevor irgendetwas anderes umgesetzt wird.**

### Entscheidung #1: Tailwind-Build vs. site.css-Nachpflege

| Option | Pro | Contra |
|---|---|---|
| **A) Lokaler Tailwind-Build (CLI)** | Alle Klassen verfügbar, echte Markenfarbe, `prose`, zukunftssicher, sauber | Einmaliger Setup (Node/Tailwind-CLI als Build-Step, kein Runtime-Node), Build-Schritt im Deploy |
| **B) Fehl-Klassen in `site.css` nachliefern** | Kein Build, schnell, `site.css` existiert schon | Manuell, wächst mit jeder neuen Klasse, fehleranfällig, kein `prose` |

**Meine Empfehlung: Option A (Tailwind-CLI-Build).** Wir machen ohnehin ein größeres
Rework mit neuer Galerie, Markenfarbe, vielen neuen Komponenten. Ein einmaliger
`tailwindcss`-CLI-Build (input.css → output.css, kein Node-Runtime nötig) löst die
Wurzel statt symptomatisch Klassen nachzupflegen. Das Vendored-CSS bleibt als Fallback.

---

## 🐛 Der Slider-Bug (explizit gewünscht) – Ursache gefunden

**Datei: `app/templates/index.html:31-73`** (NICHT `main/index.html` – das ist ein toter Stub).

**Root-Cause „3-Slide-Sweep":** Flowbite hält bei **genau 3 Slides** immer alle drei
gleichzeitig aktiv (left/middle/right, keiner `hidden`). Beim Wechsel Bild 1 ↔ Bild 3 fährt
der unbeteiligte dritte Slide mit `transition-transform duration-700` von -100% nach +100%
→ **fegt 200% quer durchs Bild**. Exakt das vom Kunden beschriebene Symptom. Kein CSS-Bug,
sondern Flowbite-Verhalten bei 3 Slides.

**Fix-Richtung:** Cross-Fade (Opacity) statt Translate, als kleiner eigener Slider
(~30 Zeilen JS). Opacity-Klassen sind im Purge vorhanden. Alternativ 4. Slide ergänzen
(Workaround). Zusätzlich: Bilder sind **6000×4000px / 1,8 MB** → auf ~1600px runter (spart ~3-4 MB).

---

## 📋 Priorisierter Umsetzungsplan (Vorschlag in 4 Wellen)

### Welle 1 – Fundament & Quick-Wins (größter Hebel, wenig Risiko)
1. **Entscheidung #1 umsetzen** (Tailwind-Build ODER site.css-Nachpflege) → schaltet alles frei
2. **Slider-Bug fixen** (Cross-Fade) + Hero-Bilder verkleinern
3. **Fokusringe/A11y** reparieren (kein `outline:none` ohne Ersatz)
4. **SEO Quick-Wins**: pro Route eigener `title` + `meta description` (Duplicate beheben),
   `APP_NAME` Branding-Bug (`config.py:21` „Fv" → „Fahrverein"), Hero-Bild `loading="eager"`

### Welle 2 – Die 3 explizit gewünschten Problemzonen
5. **Galerie/Erlebnisberichte neu**: Übersichtsseite `/berichte` (Jahre als Cards) +
   Detailseite mit echtem Grid (aspect-ratio) + Lightbox (Swipe/←→/ESC, ~3KB Vanilla-JS) +
   Thumbnails serverseitig + alt-Texte
6. **Veranstaltungen aufräumen**: 4 vermischte Inhaltstypen trennen → kommende/vergangene
   Termine als Cards, „Entwicklungsprojekte" als Vereinsinfo, Download-Karten reparieren
   (**tote 404-PDF-Links!**), Hinweisbox fixen
7. **DB befüllen**: 6 Vorstandsmitglieder + Termine (Daten in Report 04, **Rückfragen offen**)

### Welle 3 – Design-System & „einladend/spielerisch"
8. **Markenfarbe** definieren (Vorschlag naturnah: emerald/amber) statt 10 Zufallsfarben
9. **Button-/Card-Makros** (`boilerplate/macros/ui.html`) für Konsistenz
10. **Startseiten-CTA** (aktuell keiner!) – „Mitglied werden" / „Nächster Kutschertag"
11. **Smooth Transitions** wo es passt (Hover-Lifts, Dropdown, Flash-Dismiss)
12. Mobile-Feinschliff: Hero-H1-Größen, Mobile-Dropdown inline, Footer-Layout, Touch-Targets

### Welle 4 – SEO-Tiefe & Politur
13. **JSON-LD SportsClub/LocalBusiness** zentral, NAP-Konsistenz (Hausnummer 1 vs. 3 klären)
14. **Sitemap** um `/berichte/<jahr>` erweitern, `width/height` an Bilder (CLS)
15. Jahreszahlen dynamisch, toten `main/index.html`-Stub entfernen, Datenschutz prüfen
16. Kontaktformular: Mailversand-Backend prüfen/implementieren oder entfernen

---

## ❓ Offene Rückfragen an den Kunden (blockieren Welle 2/4)

1. **Tailwind-Build ja/nein?** (Entscheidung #1 – meine Empfehlung: ja)
2. **Kutschertag-Datum?** Live steht Platzhalter „xx. September 2025" → echtes Datum?
3. **Planungsjahr:** 2025-Stand übernehmen oder direkt 2026 planen?
4. **Hausnummer** Geschäftsstelle: **1 oder 3**? (Impressum vs. Vereinsdaten widersprüchlich)
5. **Vorstand:** E-Mail-Adressen + Fotos vorhanden? (für `/admin/vorstand`)
6. **Kontaktformular:** Soll echter Mailversand funktionieren?
7. **Markenfarbe:** Freie Hand (Vorschlag naturnah grün/amber) oder konkrete Wunschfarbe?
8. **Tote PDF-Downloads** auf /veranstaltungen: aktuelle Formulare liefern oder Sektion entfernen?

---

## Aufwandsschätzung grob
- Welle 1: **M** (Fundament entscheidet alles)
- Welle 2: **L** (Galerie + Veranstaltungen sind die dicksten Brocken)
- Welle 3: **M**
- Welle 4: **M**
