/**
 * Tailwind-Konfiguration – Fahrverein Planetal e.V.
 * ---------------------------------------------------------------------------
 * Einmaliger Build-Step (kein Node zur Laufzeit):
 *   npm install        (einmalig)
 *   npm run build:css  (erzeugt app/static/css/app.css)
 *
 * Markenwelt: naturnah/warm, passend zu Pferdesport & brandenburgischer
 * Landschaft. Primaer = Forstgruen ("brand"), Akzent = warmes Amber/Gold.
 */
module.exports = {
  // Dark-Mode bewusst per Klasse (.dark) statt OS-Preference, damit ohne
  // aktiven Toggle KEINE ungewollten dunklen Flaechen entstehen.
  darkMode: "class",
  content: [
    "./app/templates/**/*.html",
    "./app/**/*.py",
    "./app/static/js/**/*.js",
    "./node_modules/flowbite/**/*.js",
  ],
  theme: {
    extend: {
      colors: {
        // Primaere Markenfarbe: warmes, naturnahes Gruen
        brand: {
          50: "#f1f8f3",
          100: "#dcefe1",
          200: "#bbdfc6",
          300: "#8dc7a1",
          400: "#5aa876",
          500: "#388a57",
          600: "#286e44",
          700: "#205838",
          800: "#1c462e",
          900: "#173a27",
          950: "#0c2016",
        },
        // Akzent: warmes Amber/Gold (Kutsche, Herbst, Kutschertag)
        accent: {
          50: "#fdf8ed",
          100: "#f9eccc",
          200: "#f3d795",
          300: "#ecbd5d",
          400: "#e6a435",
          500: "#de8a1d",
          600: "#c46c16",
          700: "#a35016",
          800: "#853f18",
          900: "#6e3517",
          950: "#3f1c0a",
        },
      },
      fontFamily: {
        sans: [
          "Inter",
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "Segoe UI",
          "Roboto",
          "Helvetica Neue",
          "Arial",
          "sans-serif",
        ],
      },
      borderRadius: {
        xl: "0.875rem",
        "2xl": "1.25rem",
      },
    },
  },
  plugins: [
    require("@tailwindcss/typography"),
    require("flowbite/plugin"),
  ],
};
