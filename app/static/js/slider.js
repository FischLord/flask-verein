/*
 * slider.js – schlanker Cross-Fade-Slider fuer die Startseite.
 * ---------------------------------------------------------------------------
 * Ersetzt den Flowbite-"translate"-Carousel, der bei GENAU 3 Slides den
 * bekannten "3-Slide-Sweep"-Bug zeigte (der unbeteiligte dritte Slide fuhr
 * 200% quer durchs Bild). Hier blenden die Slides per Opacity weich ueber,
 * unabhaengig von der Slide-Anzahl. Mit Autoplay, Pause bei Hover/Fokus,
 * Prev/Next, Dots, Tastatur- und reduced-motion-Unterstuetzung.
 */
(function () {
  "use strict";

  function initSlider(root) {
    var slides = Array.prototype.slice.call(
      root.querySelectorAll("[data-slide]")
    );
    if (slides.length === 0) return;

    var dots = Array.prototype.slice.call(
      root.querySelectorAll("[data-slide-dot]")
    );
    var prevBtn = root.querySelector("[data-slide-prev]");
    var nextBtn = root.querySelector("[data-slide-next]");
    var interval = parseInt(root.getAttribute("data-slide-interval"), 10) || 6000;
    var prefersReduced = window.matchMedia(
      "(prefers-reduced-motion: reduce)"
    ).matches;

    var current = 0;
    var timer = null;

    function show(index) {
      current = (index + slides.length) % slides.length;
      slides.forEach(function (slide, i) {
        var active = i === current;
        // Opacity-Cross-Fade ueber Tailwind-Klassen (in app.css vorhanden).
        slide.classList.toggle("opacity-100", active);
        slide.classList.toggle("opacity-0", !active);
        slide.classList.toggle("z-10", active);
        slide.classList.toggle("z-0", !active);
        slide.setAttribute("aria-hidden", active ? "false" : "true");
      });
      dots.forEach(function (dot, i) {
        var active = i === current;
        dot.classList.toggle("bg-white", active);
        dot.classList.toggle("bg-white/50", !active);
        dot.setAttribute("aria-current", active ? "true" : "false");
      });
    }

    function next() { show(current + 1); }
    function prev() { show(current - 1); }

    function start() {
      if (prefersReduced || slides.length < 2) return;
      stop();
      timer = window.setInterval(next, interval);
    }
    function stop() {
      if (timer) { window.clearInterval(timer); timer = null; }
    }

    if (nextBtn) nextBtn.addEventListener("click", function () { next(); start(); });
    if (prevBtn) prevBtn.addEventListener("click", function () { prev(); start(); });
    dots.forEach(function (dot, i) {
      dot.addEventListener("click", function () { show(i); start(); });
    });

    // Pause bei Hover/Fokus (nutzerfreundlich, A11y).
    root.addEventListener("mouseenter", stop);
    root.addEventListener("mouseleave", start);
    root.addEventListener("focusin", stop);
    root.addEventListener("focusout", start);

    // Tastatur: Pfeiltasten, wenn der Slider Fokus hat.
    root.addEventListener("keydown", function (e) {
      if (e.key === "ArrowLeft") { prev(); start(); }
      else if (e.key === "ArrowRight") { next(); start(); }
    });

    show(0);
    start();
  }

  document.addEventListener("DOMContentLoaded", function () {
    Array.prototype.slice
      .call(document.querySelectorAll("[data-slider]"))
      .forEach(initSlider);
  });
})();
