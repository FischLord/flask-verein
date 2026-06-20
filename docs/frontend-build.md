# Frontend-Build (Tailwind + Flowbite)

Diese Website nutzt einen **einmaligen Build-Step** fuer CSS. Es laeuft **kein
Node zur Laufzeit** – Node/Tailwind werden nur zum Erzeugen von
`app/static/css/app.css` gebraucht. Die fertige `app.css` ist eingecheckt, der
Server liefert sie statisch aus.

## Wann muss neu gebaut werden?

Immer wenn sich **Tailwind-Klassen in Templates/JS aendern** (neue Klassen,
neue Dateien). Tailwind scannt die in `tailwind.config.js` unter `content`
gelisteten Pfade und nimmt nur tatsaechlich genutzte Klassen in `app.css` auf
("purge"). Eine Klasse, die in keinem Template steht, landet NICHT in der CSS.

## Befehle

```bash
npm install          # einmalig (Tooling, siehe package.json)
npm run build:css    # erzeugt app/static/css/app.css (minified)
npm run watch:css    # Watch-Modus waehrend der Entwicklung
```

## Dateien

- `tailwind.config.js` – Theme (Markenfarben `brand`/`accent`), Plugins
  (`@tailwindcss/typography` fuer `prose`, `flowbite/plugin`).
- `app/static/css/input.css` – Quelle: `@tailwind`-Direktiven + eigene
  Komponenten (`.btn-*`, `.card*`) und A11y-Fokusringe.
- `app/static/css/app.css` – **generiert**, eingecheckt, von `layout.html`
  eingebunden.
- `app/static/vendor/flowbite/flowbite.min.js` – Flowbite-JS bleibt vendored
  (Carousel/Collapse/Modal), unabhaengig vom CSS-Build.

## Deploy-Hinweis

Nach Template-Aenderungen `npm run build:css` ausfuehren und die aktualisierte
`app/static/css/app.css` mit committen/deployen. Wer nur Python-/Inhaltsdaten
aendert, braucht keinen CSS-Build.
