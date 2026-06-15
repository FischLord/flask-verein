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
