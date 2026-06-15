document.addEventListener('DOMContentLoaded', function () {
  const dropdownButton = document.getElementById('dropdownButton');
  const dropdown = document.getElementById('dropdown');
  let isOpen = false;

  function openDropdown() {
    isOpen = true;
    dropdown.classList.remove('hidden');
    // Erzwingt ein Reflow, damit die Transition korrekt startet
    void dropdown.offsetWidth;
    dropdown.classList.remove('opacity-0', 'scale-95');
    dropdown.classList.add('opacity-100', 'scale-100');
    // Icon rotieren lassen
    dropdownButton.querySelector('svg').classList.add('rotate-180');
    dropdownButton.setAttribute('aria-expanded', 'true');
  }

  function closeDropdown(returnFocus) {
    isOpen = false;
    dropdown.classList.remove('opacity-100', 'scale-100');
    dropdown.classList.add('opacity-0', 'scale-95');
    // Icon zurückdrehen
    dropdownButton.querySelector('svg').classList.remove('rotate-180');
    dropdownButton.setAttribute('aria-expanded', 'false');
    setTimeout(() => {
      dropdown.classList.add('hidden');
    }, 300); // Dauer entspricht der Transition
    if (returnFocus) {
      dropdownButton.focus();
    }
  }

  dropdownButton.addEventListener('click', function (e) {
    e.preventDefault();
    if (isOpen) {
      closeDropdown(false);
    } else {
      openDropdown();
    }
  });

  // Schließt das Dropdown, wenn außerhalb geklickt wird
  document.addEventListener('click', function (e) {
    if (!dropdown.contains(e.target) && !dropdownButton.contains(e.target)) {
      if (isOpen) {
        closeDropdown(false);
      }
    }
  });

  // Schließt das Dropdown per Escape-Taste und gibt Fokus zurück
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && isOpen) {
      closeDropdown(true);
    }
  });
});
