# UX/UI- & Mobile-Review – Fahrverein Planetal e.V.

> Rolle: UX/UI- und Mobile-Design-Spezialist
> Modus: **Nur Analyse, keine Code-Änderungen.**
> Stand: 2026-06-20
> Geprüft: `app/templates/boilerplate/*`, `app/templates/main/*`, `app/templates/index.html`, `app/static/css/site.css`, `app/static/js/nav.js`, `app/static/vendor/flowbite/flowbite.min.css`, `app/main/routes.py`

---

## 0. Kernaussage / TL;DR

Die Seite hat eine solide, saubere Grundstruktur (Flowbite-Cards, semantisches HTML, gute SEO/Schema.org, Skip-Link-Idee, ARIA am Dropdown vorhanden). **Aber:** Das größte Problem ist **technisch, nicht gestalterisch**: Die Templates wurden gegen einen **vollen Tailwind-Build** geschrieben, ausgeliefert wird aber eine **gepurgte `flowbite.min.css`**, in der zahlreiche genutzte Klassen schlicht **fehlen**. Dadurch rendern mehrere Design-Elemente (Akzent-Borders, Hover-Zooms, Dropdown-Animation, Fokus-Ringe, Skip-Link, `prose`-Textformatierung) **gar nicht** wie im Markup beabsichtigt.

→ **Empfehlung #1 (Hoch):** Lokalen Tailwind-Build einführen ODER die fehlenden Klassen sauber in `site.css` nachliefern. Ohne diesen Schritt verpufft jede weitere Design-Verbesserung, weil neue Klassen nicht greifen. Details in **Abschnitt 7**.

Darauf aufbauend fehlt für das Ziel „modern, einladend, etwas spielerisch, laien-tauglich“ vor allem:
- eine **klare Startseite mit Hero + Haupt-CTA** (aktuell kein einziger Call-to-Action auf `/`),
- **konsistente Buttons/Farben** (aktuell 4 verschiedene Blau/Grün-Töne, uneinheitliche Radien),
- **responsive Typo-Skalierung** (Hero-H1 `text-5xl` ohne Mobile-Stufe = zu groß auf Handys),
- **echte, lauffähige Micro-Transitions** (statt im Markup vorhandener, aber toter Klassen),
- **Barrierefreiheit** (Fokus-Ringe + Skip-Link rendern nicht; Dark-Mode-Klassen sind toter Ballast).

---

## 1. Überblick: Templates & tatsächliche Routen

| Route | Template | Inhalt | Anmerkung |
|---|---|---|---|
| `/` | `templates/index.html` | Willkommen + Bild-Carousel + 3 Karten | Echte Startseite |
| `/verein` | `main/verein.html` | 11 farbige Info-Karten | Überschrift „Fahrverein Planetal e.V. in Reckahn“ |
| `/kontakt` | `main/kontakt.html` | „Unser Vorstand“ (Personen-Grid) | Name „Kontakt“ ↔ Inhalt „Vorstand“ unscharf |
| `/veranstaltungen` | `main/veranstaltungen.html` | Termine, Zukunftspläne, Download-Formulare | |
| `/berichte/<jahr>` | `main/berichte.html` | Erlebnisberichte + Galerie | Über Nav-Dropdown erreichbar |
| `/formcenter/` | `main/formcenter.html` | PDF-Kacheln | |
| `/vereinsdaten` | `main/vereinsdaten.html` | Adresse/Bank/Beiträge | |
| `/impressum`, `/datenschutz` | `main/*.html` | Rechtstexte | |

**Toter Code:** `app/templates/main/index.html` enthält nur den Platzhaltertext „This is the /index route of the main folder!“ und wird von **keiner** Route gerendert (`/` nutzt `index.html` im Root). → Löschen (S).

---

## 2. Design-System-Bewertung

### 2.1 Typografie
- **Font:** Die vendored CSS setzt `font-family: Inter, …`, aber **Inter wird nirgends geladen** (`layout.html` hat keinen Font-`<link>`, kein `@font-face`). Faktisch rendert der System-Fallback (`system-ui`). Nicht falsch, aber „Inter“ ist eine Illusion. → bewusst entscheiden (Inter laden für modernen Look, oder Fallback dokumentieren).
- **Hierarchie uneinheitlich:** H1 ist mal `text-5xl` (`verein.html:7`, `veranstaltungen.html:7`, `vereinsdaten.html:6`), mal `text-4xl` (`kontakt.html:5`, `impressum.html:5`), mal `text-3xl` (`formcenter.html:4`, `berichte.html:4`). Keine durchgängige Skala.
- **Keine responsive Skalierung der großen Headlines:** `text-5xl` (= 48px) wird auf Mobil **nicht** verkleinert (kein `text-3xl md:text-5xl`). Auf einem 360px-Display wirkt das gedrungen und kann umbrechen. Positiv-Ausnahme: `index.html:6` macht es richtig (`text-4xl md:text-5xl lg:text-6xl`).

### 2.2 Farbwelt
- **Akzent-Wildwuchs:** `verein.html` nutzt 10 verschiedene farbige Kartenkopf-Balken (`bg-blue-500`, `green-500`, `purple-500`, `yellow-500`, `red-500`, `indigo-500`, `teal-500`, `orange-500`, `gray-800`, `pink-500`, `verein.html:19–155`). Das ist „spielerisch“, wirkt aber **zufällig statt systematisch** und es gibt **keine definierte Markenfarbe**. Für einen Pferde-/Fahrverein wäre eine warme, naturnahe Primärfarbe (Grün/Braun/Bordeaux) mit 1–2 Akzenten stimmiger und ruhiger.
- **Button-Farben uneinheitlich:** `bg-blue-600` (`verein.html:145`, `veranstaltungen.html:109`) vs. `bg-blue-500`/`bg-green-500` (`formcenter.html:22,25`). Zwei Blautöne + Grün ohne semantische Logik.

### 2.3 Spacing / Whitespace
- Vertikaler Rhythmus springt: `py-16` (verein/veranstaltungen/vereinsdaten) vs. `py-8` (formcenter/berichte) vs. gar kein Wrapper-Padding (`kontakt.html`, `verein-Vorstand`). Wirkt von Seite zu Seite unterschiedlich „dicht“.
- Karten-Gaps: `gap-4` (`index/verein` Karten) vs. `gap-6`/`gap-8` (formcenter, kontakt). Kein einheitliches Grid-Gap-Token.

### 2.4 Cards & Buttons (Konsistenz)
- Radien gemischt: `rounded` vs. `rounded-lg` vs. `rounded` an Buttons. Schatten gemischt: `shadow`, `shadow-md`, `shadow-lg`.
- Kein wiederverwendbares Button-/Card-Makro → jede Seite definiert ihre Buttons per Inline-Klassen neu (Wartungsrisiko, Inkonsistenz vorprogrammiert).

### 2.5 Visuelle Hierarchie
- `verein.html`: 11 gleichwertige Karten ohne Gewichtung/Reihenfolge-Logik → „Bleiwüste in Kacheln“. Wichtige Karte (Vereinsdaten-CTA) geht zwischen Dekokarten unter.
- Startseite hat **keinen** primären Handlungspfad (siehe 4.2).

---

## 3. Mobile-Friendliness

### 3.1 Navigation / Hamburger
- **Breakpoint `lg` (1024px):** Die Desktop-Nav erscheint erst ab 1024px; zwischen ~768–1023px (Tablets, Quer-Handy) gibt es das **Hamburger-Menü** – vertretbar, aber bei nur 5–7 Links wäre `md` (768px) angenehmer und nutzt die Breite besser.
- **Marken-Schriftzug:** `nav.html:5` `text-2xl … whitespace-nowrap` + 32px-Logo. „Fahrverein Planetal e.V.“ ist auf sehr schmalen Geräten (≤360px) breit; mit `whitespace-nowrap` **kein** Umbruch erlaubt → Risiko, dass Logo+Text den Hamburger eng zusammendrängen. Prüfen, ggf. auf Mobil `text-xl` + erlaubtem Umbruch.
- **Dropdown-Position auf Mobil:** Das Erlebnisberichte-Dropdown ist `absolute right-0` (`nav.html:35`). Im **eingeklappten** Mobile-Menü (Liste ist `flex-col`) ist ein absolut positioniertes, rechtsbündiges Overlay verwirrend – es schwebt über den darunterliegenden Links statt sie zu verschieben. Auf Mobil sollte es als **Inline-Accordion** (statisch im Fluss) erscheinen.
- **Doppeltes JS-Handling:** Flowbite-Collapse (`data-collapse-toggle`) wird über `flowbite.min.js` betrieben, das Dropdown aber über **eigenes** `nav.js`. Zwei Mechanismen nebeneinander → Wartungslast und potenzielle Konflikte (Outside-Click schließt Dropdown, aber nicht das Mobile-Menü).

### 3.2 Touch-Targets
- Nav-Links mobil: `py-2 pl-3 pr-4` (`nav.html:21 ff.`) ≈ 40px Höhe – knapp unter der empfohlenen **48px**-Marke (WCAG 2.5.5 / Apple HIG). Für ältere Nutzer grenzwertig.
- Footer-Links (`footer.html:18–20`) sind reine Textlinks ohne Padding → kleine Tap-Fläche, dazu **untereinander mit `space-y-4`** – auf Mobil ok, auf Desktop aber unnötig vertikal gestapelt (siehe 3.4).

### 3.3 Responsive Grids / Überlauf
- `verein.html` Karten `grid-cols-1 md:grid-cols-2` – ok.
- `berichte.html:23` Galerie nutzt eine **manuelle 4-Spalten-Masonry** per `loop.index0 % 4` über 4 verschachtelte Grids. Auf Mobil `grid-cols-2`. Die Modulo-Verteilung erzeugt bei wenigen Bildern leere Spalten und ist schwer wartbar. Für „spielerisch“ wäre ein simples `columns-2 md:columns-3` (CSS-Columns) oder Lightbox robuster.
- `veranstaltungen.html:43` IBAN/lange Tabellenwerte und in `vereinsdaten.html:34` die IBAN `DE43 16062073 …` können auf schmalen Screens knapp werden – kein `break-words` an den `<p>`. Niedrig-Risiko.
- **Carousel** (`index.html:33`): `h-56 md:h-96` mit `object-cover` ist mobil ok. Aber Bilder ohne `width`/`height`-Attribut → **Layout-Shift (CLS)** beim Laden.

### 3.4 Footer-Layout
- `footer.html:17–21`: Die Link-Spalte ist auch auf Desktop `flex-col … space-y-4` → drei Links stehen **untereinander** statt nebeneinander. Wirkt auf Desktop ungewollt hoch/leer. Besser: `flex-row` ab `md`.

---

## 4. Bedienbarkeit für Laien (ältere/nicht technikaffine Mitglieder)

### 4.1 Navigationsklarheit
- Menüpunkt **„Formularcenter“** ist Fachjargon. Laien verstehen „Formulare & Downloads“ oder „Anmeldungen“ besser.
- **„Kontakt“** öffnet „Unser Vorstand“ (Personenliste) – inhaltlich sinnvoll, aber es fehlt ein klassischer „So erreichen Sie uns“-Block (E-Mail/Telefon/Adresse zentral). Eine echte Kontakt-/Anfahrt-Sektion (ggf. mit Karte) würde Erwartung erfüllen.
- **Erlebnisberichte** sind nur als Dropdown nach Jahren erreichbar – ohne JS/bei Hover-Unsicherheit (ältere Nutzer) schwer zu finden. Eine eigene Übersichtsseite „Berichte“ mit Jahr-Kacheln wäre niedrigschwelliger.

### 4.2 Call-to-Actions
- **Startseite hat keinen einzigen CTA.** Kein „Mitglied werden“, „Kontakt aufnehmen“, „Nächster Kutschertag“. Für „einladend“ ist das die größte verschenkte Chance. Empfehlung: 1 klarer Primär-Button im Hero + 1 sekundärer.
- Vereinsweit gibt es nur **einen** „Mehr erfahren“-Button (`verein.html:144`) und Download-Buttons. Handlungspfade für Interessenten fehlen.

### 4.3 Verständlichkeit
- Texte sind gut lesbar und freundlich. Tippfehler: `veranstaltungen.html:79` „Taum“ → „Raum“. Geschäftsadresse weicht ab: `vereinsdaten.html:19` „Krahner Straße 03“ vs. `impressum.html:12` „Krahner Straße 1“ – inhaltliche Inkonsistenz prüfen.
- Datenschutz enthält Platzhalter `[Hosting-Anbieter einfügen]` / `[E-Mail-Dienst einfügen]` (`datenschutz.html:53–54`) – rechtlich/vertrauensseitig ungünstig, sollte gefüllt werden.

### 4.4 Barrierefreiheit (Kontraste, Fokus, ARIA, Schrift)
- **Skip-Link rendert nicht sichtbar:** `layout.html:27` nutzt `focus:not-sr-only` – diese Klasse **fehlt in der vendored CSS** (verifiziert). Der Link bleibt damit beim Fokussieren unsichtbar → der gut gemeinte A11y-Mechanismus ist **wirkungslos**.
- **Fokus-Ringe rendern nicht:** Buttons/Links nutzen `focus:outline-none` **plus** `focus-visible:ring-2 …` (`nav.html:8,27,73,79`, `index.html:57,65`). `focus-visible:ring-2` **fehlt in der vendored CSS** (verifiziert) → es wird der Outline entfernt, aber **kein Ersatz** gezeichnet. Resultat: **schlechtere** Tastatur-Sichtbarkeit als ganz ohne diese Klassen. Kritisch für ältere Nutzer mit Tastatur/Vergrößerung.
- **Kontrast:** Fließtext `text-gray-500`/`text-gray-600` auf weiß ist okay, aber `text-gray-400` für Footer-Copyright (`footer.html:7`) und teils Impressum (`text-gray-500`) ist für ältere Augen grenzwertig. Body-Text mind. `text-gray-700` empfehlen.
- **Bilder ohne aussagekräftigen Alt teils ok**, aber Vorstand-Foto `alt="{{ funktion }}"` (`kontakt.html:12`) beschreibt die Funktion statt der Person.
- **Dark-Mode = toter Ballast:** 129 `dark:`-Klassen in den Templates, aber **kein Dark-Mode-Toggle** und `<html>` trägt **kein** `.dark` (`layout.html:2`). Diese Klassen tun nichts, blähen aber das Markup auf und suggerieren ein nicht vorhandenes Feature. Entweder Dark-Mode **richtig** umsetzen (Toggle + `class`-Strategie) oder die `dark:`-Klassen entfernen.

---

## 5. Transitions / Micro-Interactions (Ist-Zustand vs. real lauffähig)

**Wichtig:** Mehrere „Transition“-Klassen im Markup sind **nicht in der vendored CSS enthalten** und damit **tot**. Verifiziert per `grep` gegen `flowbite.min.css`:

| Klasse | Verwendung | In vendored CSS? | Effekt heute |
|---|---|---|---|
| `scale-95` / `scale-100` | Nav-Dropdown-Animation (`nav.html:35`, `nav.js`) | **FEHLT** | Dropdown skaliert **nicht**, nur Opacity-Fade greift |
| `hover:scale-105` | Galerie-Bild-Zoom (`berichte.html:29`) | **FEHLT** | **Kein** Hover-Zoom |
| `hover:shadow-xl` | Karte (`verein.html:133`) | **FEHLT** | **Kein** Hover-Lift |
| `hover:shadow-lg` | Formcenter-Kachel (`formcenter.html:8`) | **FEHLT** | **Kein** Hover-Lift |
| `border-l-4` | Hinweis-Box (`veranstaltungen.html:16`, `berichte.html:15`) | **FEHLT** | **Kein** linker Akzentbalken |
| `prose` / `max-w-none` greift, aber `prose` | Termin-/Berichtstext (`veranstaltungen.html:50`, `berichte.html:17`) | **FEHLT** | **Keine** Typo-Formatierung des HTML-Inhalts |
| `opacity-75` | Abgelaufene Termine (`veranstaltungen.html:29`) | **FEHLT** | Abgelaufene Termine werden **nicht** ausgegraut |
| `md:col-span-2` | Breite Karte (`verein.html:154`) | **FEHLT** | Karte spannt **nicht** über 2 Spalten |
| `max-h-60` | Dropdown-Scrollcap (`nav.html:36`) | **FEHLT** | Lange Jahresliste wird **nicht** gedeckelt |
| `transition-shadow`, `duration-500`, `scroll-smooth` | div. | **FEHLT** | unwirksam |
| `transition`, `duration-300`, `opacity-0/100`, `rotate-180`, `ease-out`, `transition-transform` | Nav/Carousel | **vorhanden** | funktionieren |

**Fazit:** Das Dropdown hat heute nur ein Opacity-Fade (Scale tot), das Pfeil-Icon rotiert korrekt (`rotate-180` vorhanden). Galerie-Zoom, Karten-Hover-Lifts, Akzent-Borders und `prose`-Formatierung sind **nicht sichtbar**. Das erklärt vermutlich einen „flachen“ Gesamteindruck trotz vorhandener Markup-Absicht.

**Wo zusätzlich sanfte Übergänge fehlen (sinnvoll):**
- Seiten-/Nav-Link-Hover ohne `transition-colors` an den Hauptlinks (`nav.html:21 ff.`) → harter Farbwechsel.
- Buttons ohne `transition` an einigen Stellen (`formcenter.html:22,25`).
- Kein sanftes Einblenden des Mobile-Menüs (Flowbite-Collapse toggelt `hidden` hart).
- Carousel ok (`duration-700 ease-in-out` vorhanden).

---

## 6. Priorisierte Befundliste (Ort · Problem · Empfehlung · Aufwand)

### HOCH

**H1 · Fehlende Utility-Klassen in vendored CSS (Design rendert nicht)**
Ort: gesamtes `app/static/vendor/flowbite/flowbite.min.css` vs. Templates (siehe Tabelle Abschnitt 5).
Problem: `border-l-4`, `prose`, `hover:scale-105`, `hover:shadow-xl/lg`, `scale-95/100`, `opacity-75`, `md:col-span-2`, `max-h-60`, `focus-visible:ring-2`, `focus:not-sr-only` u.a. fehlen → tote Klassen, kaputte Optik & A11y.
Empfehlung: Lokalen Tailwind-Build einführen **oder** alle real genutzten Fehl-Klassen in `site.css` nachliefern (Abschnitt 7 + Anhang A liefert Snippets).
Aufwand: **M** (site.css-Weg) bzw. **M–L** (Build-Setup).

**H2 · Skip-Link & Fokus-Ringe wirkungslos (A11y-Regression)**
Ort: `layout.html:27`; `nav.html:8,27,73,79`; `index.html:57,65`.
Problem: `focus:not-sr-only` und `focus-visible:ring-2` fehlen → Skip-Link bleibt unsichtbar, Fokus wird per `focus:outline-none` entfernt ohne Ersatz.
Empfehlung: Klassen nachliefern (Anhang A) **oder** in `site.css` eigene `:focus-visible`-Ringe + sichtbaren Skip-Link definieren. Niemals `outline:none` ohne Ersatzring.
Aufwand: **S**.

**H3 · Startseite ohne CTA / ohne Hero-Handlungspfad**
Ort: `index.html:3–29`.
Problem: Kein primärer Call-to-Action; Ziel „einladend, handlungsleitend“ verfehlt.
Empfehlung (Vorher→Nachher): Hero um Button-Paar ergänzen, z.B.
`<a class="px-6 py-3 rounded-lg bg-emerald-600 text-white …">Mitglied werden</a>` (primär) + `<a class="… border border-emerald-600 text-emerald-700">Termine ansehen</a>` (sekundär). Optional „Nächster Termin“-Teaser aus `Termin`-Query.
Aufwand: **S–M**.

**H4 · Responsive Typo der großen Headlines**
Ort: `verein.html:7`, `veranstaltungen.html:7`, `vereinsdaten.html:6` (`text-5xl` ohne Mobile-Stufe).
Problem: 48px-Headline auf 360px-Display zu groß / Umbruch.
Empfehlung: `text-3xl md:text-4xl lg:text-5xl` (analog zu `index.html:6`).
Aufwand: **S**.

**H5 · Dark-Mode-Klassen ohne Dark-Mode (toter Ballast + falsche Erwartung)**
Ort: 129 `dark:`-Vorkommen in `main/*` + `layout.html:2` (kein `.dark`), kein Toggle.
Problem: Wirkungslos, Markup aufgebläht.
Empfehlung: Entweder Dark-Mode echt umsetzen (Toggle-Button + `documentElement.classList.toggle('dark')` + `lg:dark:`-Pattern wie in site.css schon angelegt) **oder** `dark:`-Klassen entfernen. Für die Laien-Zielgruppe ist Dark-Mode optional; sauberes Entfernen ist der pragmatische Weg.
Aufwand: **M**.

### MITTEL

**M1 · Button-/Farb-Inkonsistenz, keine Markenfarbe**
Ort: `verein.html:145` (`bg-blue-600`), `formcenter.html:22,25` (`bg-green-500`/`bg-blue-500`), `veranstaltungen.html:109` (`bg-blue-600`).
Problem: Mehrere Blau/Grün-Töne, kein System.
Empfehlung: Eine Primärfarbe (Vorschlag warm/naturnah, z.B. `emerald`/`amber`) definieren, ein wiederverwendbares Button-Makro `boilerplate/macros/ui.html` (`btn_primary`, `btn_secondary`) anlegen und überall verwenden.
Aufwand: **M**.

**M2 · Mobile-Dropdown verhält sich als rechtsbündiges Overlay**
Ort: `nav.html:26–47`, `nav.js`.
Problem: Im eingeklappten Menü schwebt das Dropdown `absolute right-0` über den Links.
Empfehlung: Auf `<lg` `static`/`relative` + volle Breite (Inline-Accordion), nur ab `lg` als Overlay. Z.B. zusätzliche Klassen `lg:absolute lg:right-0` und mobil im Fluss.
Aufwand: **M**.

**M3 · Kartenkopf-Farb-Wildwuchs (verein.html)**
Ort: `verein.html:19,34,58,71,86,98,110,122,134,155`.
Problem: 10 zufällige Farben → unruhig, kein Branding.
Empfehlung: Auf 2–3 Markenakzente reduzieren oder Farbe semantisch koppeln (z.B. „Termine“=amber, „Verein“=emerald). „Spielerisch“ über dezente Hover-Lifts/Icons statt Regenbogen.
Aufwand: **S–M**.

**M4 · Footer-Links auf Desktop vertikal gestapelt**
Ort: `footer.html:17`.
Problem: `flex-col space-y-4` auch im Desktop.
Empfehlung: `flex-col md:flex-row md:space-y-0 md:space-x-6`.
Aufwand: **S**.

**M5 · Flash-Messages ohne Icon/Schließen, mehrere Messages verschmelzen**
Ort: `flash_message.html:12–37`.
Problem: Bei mehreren Messages werden sie ohne Trennung in einen Block gerendert; kein Dismiss, kein Icon. Für Laien wenig auffällig.
Empfehlung: Pro Message eigene Box (Schleife innerhalb des Containers trennen), Icon + optionaler Flowbite-Dismiss (`data-dismiss-target`), `transition` fürs Ausblenden.
Aufwand: **S–M**.

**M6 · Carousel-Bilder unoptimiert → Performance/CLS**
Ort: `index.html:36,43,50`; Dateien `promo1.webp` 1.8 MB, `promo2` 932 KB, `promo3` 788 KB.
Problem: ~3.5 MB Startseiten-Bilder, keine `width`/`height` → langsamer Aufbau, Layout-Shift; auf Vereinsmitglieder mit schwachem Mobilnetz spürbar.
Empfehlung: Bilder auf ~1600px / <250 KB reskalieren, `width`/`height` setzen, erstes Bild `loading="eager"` + `fetchpriority="high"`, Rest `lazy`.
Aufwand: **S** (Bilder) / **S** (Attribute).

**M7 · „Formularcenter“ + „Kontakt“ Naming/Erwartung**
Ort: `nav.html:61–63`, `kontakt.html`.
Problem: Fachbegriff bzw. Erwartungsbruch.
Empfehlung: „Formulare & Downloads“; Kontakt-Seite um „So erreichen Sie uns“-Block (E-Mail/Tel/Adresse, ggf. Karte) ergänzen.
Aufwand: **S–M**.

### NIEDRIG

**N1 · Toter Platzhalter-Template** `main/index.html` → löschen. (S)
**N2 · Tippfehler/Inkonsistenz:** `veranstaltungen.html:79` „Taum“→„Raum“; Adresse `vereinsdaten.html:19` vs. `impressum.html:12`. (S)
**N3 · Datenschutz-Platzhalter** `datenschutz.html:53–54` füllen. (S)
**N4 · Inter-Font:** bewusst laden (`<link>` zu lokal gehosteter Inter) oder Fallback dokumentieren; selbst-hosten wegen DSGVO (kein Google-CDN). (S–M)
**N5 · `berichte.html` Masonry per Modulo** → auf CSS-`columns` umstellen + optional Lightbox. (M)
**N6 · `break-words` an IBAN/langen Werten** (`vereinsdaten.html:34`, `veranstaltungen.html:43`). (S)
**N7 · Touch-Targets** Nav-Links mobil auf min. 48px erhöhen (`py-3`). (S)
**N8 · Doppeltes Menü-JS** (Flowbite-Collapse + eigenes `nav.js`) langfristig vereinheitlichen. (M)

---

## 7. Technische Constraint: Lokaler Tailwind-Build – ja oder nein?

**Befund:** Die Templates sind gegen ein **volles** Tailwind geschrieben; ausgeliefert wird eine **gepurgte** `flowbite.min.css` (149 KB), in der genau die selten genutzten Klassen fehlen. `site.css` liefert bereits 4 `lg:`-Klassen nach (FV-09) – das bestätigt das Problem, deckt es aber nur punktuell ab. Bei jeder neuen Design-Iteration läuft man erneut in „Klasse existiert nicht“.

### Option A – Lokaler Tailwind-Build einführen (empfohlen, mittelfristig)
**Pro:**
- Alle Utility-Klassen verfügbar; neue Design-Iterationen ohne „fehlt-in-CSS“-Fallen.
- Tree-Shaking/Purge **automatisch korrekt** (scannt die Templates) → kleinste, korrekte CSS.
- `@tailwindcss/typography` (`prose`) und `forms`-Plugin verfügbar → Termin-/Berichtstexte und Formulare sehen ohne Handarbeit gut aus.
- Eigene Markenfarbe/Spacing-Tokens zentral in `tailwind.config.js` → löst M1/M3 sauber.
- Kann CDN-Abhängigkeit (FV-02) mitlösen.

**Contra:**
- Build-Toolchain (Node/npm) in einem reinen Flask-Projekt → CI/Deploy-Schritt nötig (`npm run build:css`).
- Kleiner Lernaufwand/Maintenance; aktuell ist „kein Node“ ein bewusster Vorteil.

**Pragmatische Umsetzung (ohne Dauer-Node-Server):** Tailwind **CLI** als einmaliger Build-Step, Output `app/static/css/app.css` eingecheckt. Kein Runtime-Node nötig, nur beim Ändern der Styles.
```
npx tailwindcss -i ./app/assets/app.css -o ./app/static/css/app.css --minify
// tailwind.config.js: content: ["./app/templates/**/*.html"], plugins: [typography, forms]
```

### Option B – Bei `site.css` + vendored Klassen bleiben (kurzfristig, sofort)
**Pro:** Keine Toolchain, sofort umsetzbar, voller Kontrolle, klein.
**Contra:** Jede fehlende Klasse muss manuell nachgepflegt werden; fehleranfällig, skaliert schlecht; `prose` von Hand nachzubauen ist mühsam.

### Empfehlung
- **Sofort (S–M):** Die in Abschnitt 5 gelisteten **konkret genutzten** Fehl-Klassen in `site.css` nachliefern (Anhang A) → behebt H1/H2 ohne Toolchain.
- **Mittelfristig (M–L):** Auf **Option A (Tailwind CLI)** umstellen, sobald ein Redesign mit eigener Markenfarbe ansteht. Dann `site.css`-Workarounds entfernen. Das ist der nachhaltige Weg für „modern + iterierbar“.

---

## Anhang A · Konkrete `site.css`-Nachlieferungen (sofort, ohne Build)

> Behebt H1/H2 für die real genutzten Klassen. Werte aus Tailwind-Defaults.

```css
/* --- Akzent-Borders (veranstaltungen/berichte Hinweis-Boxen) --- */
.border-l-4 { border-left-width: 4px; }

/* --- Karten-Hover-Lifts --- */
.transition-shadow { transition-property: box-shadow; transition-duration: .3s; }
.hover\:shadow-lg:hover { box-shadow: 0 10px 15px -3px rgb(0 0 0/.1), 0 4px 6px -4px rgb(0 0 0/.1); }
.hover\:shadow-xl:hover { box-shadow: 0 20px 25px -5px rgb(0 0 0/.1), 0 8px 10px -6px rgb(0 0 0/.1); }

/* --- Galerie-Zoom + Dropdown-Scale --- */
.scale-95  { --tw-scale-x:.95; --tw-scale-y:.95; transform: scale(.95); }
.scale-100 { --tw-scale-x:1;   --tw-scale-y:1;   transform: scale(1); }
.hover\:scale-105:hover { transform: scale(1.05); }

/* --- Layout/Deko --- */
.opacity-75 { opacity:.75; }
.max-h-60 { max-height:15rem; }
@media (min-width:768px){ .md\:col-span-2 { grid-column: span 2 / span 2; } }

/* --- A11y: sichtbarer Fokusring + Skip-Link (ersetzt fehlende Klassen) --- */
.focus-visible\:ring-2:focus-visible {
  outline: 2px solid transparent; outline-offset: 2px;
  box-shadow: 0 0 0 2px #fff, 0 0 0 4px #2563eb;
}
.focus\:not-sr-only:focus {
  position: static; width:auto; height:auto; margin:0; overflow:visible;
  clip:auto; white-space:normal;
}

/* --- Optional: prose-Ersatz light (Termin-/Berichtstext) --- */
.prose :where(p):not(:last-child){ margin-bottom:1rem; }
.prose :where(h2,h3){ font-weight:700; margin:1.25rem 0 .5rem; }
.prose :where(ul){ list-style:disc; padding-left:1.25rem; margin:.5rem 0; }
.prose :where(a){ color:#2563eb; text-decoration:underline; }
```

> Für vollwertiges `prose` ist `@tailwindcss/typography` (Option A) klar besser – obiges ist nur die pragmatische Brücke.

---

## Anhang B · Verifikationsmethode

Klassenexistenz wurde per `grep -F` gegen `app/static/vendor/flowbite/flowbite.min.css` geprüft (Tailwind escaped `:`→`\:` in CSS-Selektoren). „FEHLT“ = Selektor nicht in der vendored Datei vorhanden und nicht in `site.css` nachgeliefert. Routen-Zuordnung aus `app/main/routes.py`. Bildgrößen via `du -h`.
