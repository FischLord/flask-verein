/*
 * WYSIWYG-Anbindung (Quill 1.3.7) für das Admin-CMS.
 * ------------------------------------------------------------
 * Bindet einen schlanken Editor an jedes <textarea class="js-wysiwyg">.
 * Beim Absenden des Formulars wird das erzeugte HTML in das Textarea
 * zurückgeschrieben; der Server bereinigt es zusätzlich mit bleach
 * (siehe app/modules/util/html.py).
 *
 * Hinweis CSP: Diese Datei wird lokal ausgeliefert (script-src 'self').
 * Es werden keine Inline-Skripte verwendet.
 */
(function () {
  "use strict";

  // Bewusst kleine, laienfreundliche Werkzeugleiste. Die hier
  // erzeugten Tags decken sich mit der Server-Allowlist (bleach).
  var TOOLBAR = [
    [{ header: [2, 3, false] }],
    ["bold", "italic"],
    [{ list: "ordered" }, { list: "bullet" }],
    ["blockquote", "link"],
    ["clean"]
  ];

  // Quill erzeugt die Werkzeugleiste selbst und beschriftet die Knoepfe
  // nur per CSS-Icon. Ohne Textalternative sagt ein Screenreader lediglich
  // "Schaltflaeche" an; deshalb hier nachtraeglich beschriften.
  var BUTTON_LABELS = [
    ["button.ql-bold", "Fett"],
    ["button.ql-italic", "Kursiv"],
    ['button.ql-list[value="ordered"]', "Nummerierte Liste"],
    ['button.ql-list[value="bullet"]', "Aufzählung"],
    ["button.ql-blockquote", "Zitat"],
    ["button.ql-link", "Link einfügen"],
    ["button.ql-clean", "Formatierung entfernen"]
  ];

  function labelToolbar(container) {
    if (!container) {
      return;
    }
    BUTTON_LABELS.forEach(function (eintrag) {
      var knopf = container.querySelector(eintrag[0]);
      if (knopf) {
        knopf.setAttribute("aria-label", eintrag[1]);
        knopf.setAttribute("title", eintrag[1]);
      }
    });
    // Ueberschriften-Auswahl: Quill ersetzt das <select> durch ein
    // eigenes Picker-Widget, das ebenfalls unbeschriftet ist.
    var picker = container.querySelector(".ql-header");
    if (picker) {
      picker.setAttribute("aria-label", "Absatzformat");
      picker.setAttribute("title", "Absatzformat");
    }
  }

  function initEditor(textarea) {
    var wrapper = document.createElement("div");
    wrapper.className = "js-wysiwyg-editor bg-white";
    textarea.parentNode.insertBefore(wrapper, textarea);

    // Original-Textarea verstecken (Quill schreibt vor dem Absenden
    // den HTML-Inhalt zurück).
    textarea.style.display = "none";

    var quill = new Quill(wrapper, {
      theme: "snow",
      modules: { toolbar: TOOLBAR }
    });

    // Etwas Höhe, damit das Eingabefeld gut bedienbar ist.
    quill.root.style.minHeight = "12rem";

    var toolbar = quill.getModule("toolbar");
    labelToolbar(toolbar && toolbar.container);

    if (textarea.value) {
      quill.clipboard.dangerouslyPasteHTML(textarea.value);
    }

    var form = textarea.closest("form");
    if (form) {
      form.addEventListener("submit", function () {
        var html = quill.root.innerHTML;
        // Komplett leerer Editor -> leeren String speichern.
        if (html === "<p><br></p>") {
          html = "";
        }
        textarea.value = html;
      });
    }
  }

  document.addEventListener("DOMContentLoaded", function () {
    if (typeof Quill === "undefined") {
      return; // Editor nicht geladen -> Textarea bleibt nutzbar.
    }
    var areas = document.querySelectorAll("textarea.js-wysiwyg");
    Array.prototype.forEach.call(areas, initEditor);
  });
})();
