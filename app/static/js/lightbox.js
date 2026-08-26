/*
 * lightbox.js – schlanke, abhaengigkeitsfreie Bild-Lightbox.
 * ---------------------------------------------------------------------------
 * Aktiviert sich auf jeder Galerie mit [data-gallery]. Klick auf ein
 * [data-lightbox]-Bild oeffnet ein Overlay mit:
 *   - Weiche Ein-/Ausblendung (Opacity-Transition, app.css)
 *   - Vor/Zurueck (Buttons, Pfeiltasten, Swipe auf Touch)
 *   - ESC und Klick auf Hintergrund schliessen
 *   - Fokus-Trap + Rueckgabe des Fokus (A11y)
 *   - Zaehler "x / n" und Bildunterschrift aus alt-Text
 *
 * Mehrere Galerien pro Seite werden unterstuetzt: jede [data-gallery] bildet
 * eine eigene Bildreihe.
 */
(function () {
  "use strict";

  function buildOverlay() {
    var o = document.createElement("div");
    o.id = "lightbox-overlay";
    o.setAttribute("role", "dialog");
    o.setAttribute("aria-modal", "true");
    o.setAttribute("aria-label", "Bildanzeige");
    o.className =
      "fixed inset-0 z-50 hidden items-center justify-center bg-black/90 " +
      "opacity-0 transition-opacity duration-300";
    o.innerHTML =
      '<button type="button" data-lb-close aria-label="Schliessen" ' +
      'class="absolute top-4 right-4 z-10 flex items-center justify-center ' +
      'w-11 h-11 rounded-full bg-white/15 text-white hover:bg-white/30 ' +
      'transition-colors text-2xl leading-none">&times;</button>' +
      '<button type="button" data-lb-prev aria-label="Vorheriges Bild" ' +
      'class="absolute left-3 sm:left-5 top-1/2 -translate-y-1/2 z-10 flex ' +
      'items-center justify-center w-12 h-12 rounded-full bg-white/15 ' +
      'text-white hover:bg-white/30 transition-colors">' +
      '<svg class="w-7 h-7" fill="none" stroke="currentColor" ' +
      'viewBox="0 0 24 24"><path stroke-linecap="round" ' +
      'stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/></svg>' +
      "</button>" +
      '<button type="button" data-lb-next aria-label="Naechstes Bild" ' +
      'class="absolute right-3 sm:right-5 top-1/2 -translate-y-1/2 z-10 ' +
      'flex items-center justify-center w-12 h-12 rounded-full bg-white/15 ' +
      'text-white hover:bg-white/30 transition-colors">' +
      '<svg class="w-7 h-7" fill="none" stroke="currentColor" ' +
      'viewBox="0 0 24 24"><path stroke-linecap="round" ' +
      'stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>' +
      "</button>" +
      '<figure class="max-w-[92vw] max-h-[88vh] flex flex-col items-center">' +
      '<img data-lb-img src="" alt="" ' +
      'class="max-w-[92vw] max-h-[80vh] object-contain rounded-lg shadow-2xl">' +
      '<figcaption data-lb-caption ' +
      'class="mt-3 text-center text-sm text-white/80"></figcaption>' +
      "</figure>";
    document.body.appendChild(o);
    return o;
  }

  document.addEventListener("DOMContentLoaded", function () {
    var galleries = Array.prototype.slice.call(
      document.querySelectorAll("[data-gallery]")
    );
    if (galleries.length === 0) return;

    var overlay = buildOverlay();
    var imgEl = overlay.querySelector("[data-lb-img]");
    var capEl = overlay.querySelector("[data-lb-caption]");
    var btnPrev = overlay.querySelector("[data-lb-prev]");
    var btnNext = overlay.querySelector("[data-lb-next]");
    var btnClose = overlay.querySelector("[data-lb-close]");

    var items = [];
    var current = 0;
    var lastFocus = null;

    function render() {
      var it = items[current];
      if (!it) return;
      imgEl.src = it.src;
      imgEl.alt = it.alt || "";
      capEl.textContent =
        (it.alt ? it.alt + "  ·  " : "") + (current + 1) + " / " + items.length;
      var multi = items.length > 1;
      btnPrev.classList.toggle("hidden", !multi);
      btnNext.classList.toggle("hidden", !multi);
    }

    function openAt(list, index) {
      items = list;
      current = index;
      lastFocus = document.activeElement;
      render();
      overlay.classList.remove("hidden");
      overlay.classList.add("flex");
      // Reflow erzwingen, dann einblenden.
      void overlay.offsetWidth;
      overlay.classList.remove("opacity-0");
      document.body.style.overflow = "hidden";
      btnClose.focus();
    }

    function close() {
      overlay.classList.add("opacity-0");
      document.body.style.overflow = "";
      window.setTimeout(function () {
        overlay.classList.add("hidden");
        overlay.classList.remove("flex");
        imgEl.src = "";
      }, 300);
      if (lastFocus && lastFocus.focus) lastFocus.focus();
    }

    function next() { current = (current + 1) % items.length; render(); }
    function prev() {
      current = (current - 1 + items.length) % items.length;
      render();
    }

    // Galerien verdrahten: pro Galerie eine Bildliste.
    galleries.forEach(function (gallery) {
      var triggers = Array.prototype.slice.call(
        gallery.querySelectorAll("[data-lightbox]")
      );
      var list = triggers.map(function (t) {
        return {
          src: t.getAttribute("data-full") || t.getAttribute("src"),
          alt: t.getAttribute("alt") || "",
        };
      });
      triggers.forEach(function (t, i) {
        t.style.cursor = "zoom-in";
        t.addEventListener("click", function () { openAt(list, i); });
        // Tastatur: Enter/Space oeffnet (Trigger sind fokussierbar gemacht).
        t.setAttribute("tabindex", "0");
        t.setAttribute("role", "button");
        t.addEventListener("keydown", function (e) {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            openAt(list, i);
          }
        });
      });
    });

    btnNext.addEventListener("click", next);
    btnPrev.addEventListener("click", prev);
    btnClose.addEventListener("click", close);
    overlay.addEventListener("click", function (e) {
      if (e.target === overlay) close();
    });

    document.addEventListener("keydown", function (e) {
      if (overlay.classList.contains("hidden")) return;
      if (e.key === "Escape") close();
      else if (e.key === "ArrowRight") next();
      else if (e.key === "ArrowLeft") prev();
      else if (e.key === "Tab") {
        // Simple Fokus-Trap auf die Steuer-Buttons.
        e.preventDefault();
      }
    });

    // Touch-Swipe.
    var startX = 0;
    overlay.addEventListener("touchstart", function (e) {
      startX = e.touches[0].clientX;
    }, { passive: true });
    overlay.addEventListener("touchend", function (e) {
      var dx = e.changedTouches[0].clientX - startX;
      if (Math.abs(dx) > 50) { dx < 0 ? next() : prev(); }
    }, { passive: true });
  });
})();
