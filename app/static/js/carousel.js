/**
 * Eigenes Carousel-Script für den Fahrverein Planetal
 * Behebt den Wrap-around-Bug bei der Slide-Richtung
 */
document.addEventListener('DOMContentLoaded', function() {
  const carousels = document.querySelectorAll('[data-carousel]');

  carousels.forEach(function(carousel) {
    const items = carousel.querySelectorAll('[data-carousel-item]');
    const prevBtn = carousel.querySelector('[data-carousel-prev]');
    const nextBtn = carousel.querySelector('[data-carousel-next]');

    if (items.length === 0) return;

    let currentIndex = 0;
    let isAnimating = false;

    // Initiales Setup - erstes Item sichtbar
    items.forEach((item, index) => {
      item.classList.add('absolute', 'inset-0', 'transition-all', 'duration-700', 'ease-in-out');
      if (index === 0) {
        item.classList.remove('hidden');
        item.style.transform = 'translateX(0)';
        item.style.opacity = '1';
        item.style.zIndex = '20';
      } else {
        item.classList.add('hidden');
        item.style.transform = 'translateX(100%)';
        item.style.opacity = '0';
        item.style.zIndex = '10';
      }
    });

    function slideTo(newIndex, direction) {
      if (isAnimating || newIndex === currentIndex) return;
      isAnimating = true;

      const currentItem = items[currentIndex];
      const newItem = items[newIndex];

      // Bestimme die Slide-Richtung
      // direction: 'next' = nach links schieben, 'prev' = nach rechts schieben
      const slideOutTransform = direction === 'next' ? 'translateX(-100%)' : 'translateX(100%)';
      const slideInStart = direction === 'next' ? 'translateX(100%)' : 'translateX(-100%)';

      // Neues Item vorbereiten (außerhalb des Sichtbereichs)
      newItem.classList.remove('hidden');
      newItem.style.transform = slideInStart;
      newItem.style.opacity = '0';
      newItem.style.zIndex = '20';

      // Kurze Verzögerung für CSS-Transition
      requestAnimationFrame(() => {
        requestAnimationFrame(() => {
          // Aktuelles Item rausschieben
          currentItem.style.transform = slideOutTransform;
          currentItem.style.opacity = '0';
          currentItem.style.zIndex = '10';

          // Neues Item reinschieben
          newItem.style.transform = 'translateX(0)';
          newItem.style.opacity = '1';
        });
      });

      // Nach der Animation aufräumen
      setTimeout(() => {
        currentItem.classList.add('hidden');
        currentIndex = newIndex;
        isAnimating = false;
      }, 700);
    }

    function next() {
      const newIndex = (currentIndex + 1) % items.length;
      slideTo(newIndex, 'next');
    }

    function prev() {
      const newIndex = (currentIndex - 1 + items.length) % items.length;
      slideTo(newIndex, 'prev');
    }

    // Event Listener
    if (nextBtn) {
      nextBtn.addEventListener('click', next);
    }

    if (prevBtn) {
      prevBtn.addEventListener('click', prev);
    }

    // Optional: Automatisches Sliding (alle 5 Sekunden)
    if (carousel.dataset.carousel === 'slide') {
      setInterval(next, 5000);
    }

    // Keyboard Navigation
    carousel.addEventListener('keydown', function(e) {
      if (e.key === 'ArrowLeft') {
        prev();
      } else if (e.key === 'ArrowRight') {
        next();
      }
    });

    // Touch/Swipe Support
    let touchStartX = 0;
    let touchEndX = 0;

    carousel.addEventListener('touchstart', function(e) {
      touchStartX = e.changedTouches[0].screenX;
    }, { passive: true });

    carousel.addEventListener('touchend', function(e) {
      touchEndX = e.changedTouches[0].screenX;
      const diff = touchStartX - touchEndX;

      if (Math.abs(diff) > 50) { // Mindestens 50px swipe
        if (diff > 0) {
          next(); // Swipe nach links = nächstes Bild
        } else {
          prev(); // Swipe nach rechts = vorheriges Bild
        }
      }
    }, { passive: true });
  });
});
