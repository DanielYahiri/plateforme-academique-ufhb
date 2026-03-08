function toggleMenu() {
  const nav = document.getElementById('navLinks');
  nav.classList.toggle('open');
}

document.addEventListener('DOMContentLoaded', function() {

  // Dropdown mobile au clic
  document.querySelectorAll('.nav-dropdown > a').forEach(function(el) {
    el.addEventListener('click', function(e) {
      if (window.innerWidth <= 768) {
        e.preventDefault();
        el.closest('.nav-dropdown').classList.toggle('open');
      }
    });
  });

  // Fermer menu si clic extérieur
  document.addEventListener('click', function(e) {
    const nav = document.getElementById('navLinks');
    const burger = document.querySelector('.burger');
    if (nav && burger && !nav.contains(e.target) && !burger.contains(e.target)) {
      nav.classList.remove('open');
    }
  });

  // Admin link
  checkAdminLink();
});

function checkAdminLink() {
  try {
    const u = JSON.parse(localStorage.getItem('user') || '{}');
    const el = document.getElementById('nav-admin-link');
    if (!el) return;
    el.style.display = u.role === 'admin' ? 'block' : 'none';
  } catch(e) {}
}