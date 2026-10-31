/**
 * WorkBridgeMini - Global UI & UX Interactive Library
 */

document.addEventListener('DOMContentLoaded', function () {
  initMobileNav();
  initAlertDismissal();
  initModals();
});

/**
 * Mobile Navigation Drawer
 */
function initMobileNav() {
  const toggleBtn = document.getElementById('wbMobileNavToggle');
  const drawer = document.getElementById('wbMobileNavDrawer');
  const backdrop = document.getElementById('wbNavBackdrop');

  if (!toggleBtn || !drawer) return;

  function toggleMenu(open) {
    const isOpen = open !== undefined ? open : !drawer.classList.contains('open');
    if (isOpen) {
      drawer.classList.add('open');
      if (backdrop) backdrop.classList.add('open');
      toggleBtn.setAttribute('aria-expanded', 'true');
      toggleBtn.innerHTML = '✕';
      document.body.style.overflow = 'hidden';
    } else {
      drawer.classList.remove('open');
      if (backdrop) backdrop.classList.remove('open');
      toggleBtn.setAttribute('aria-expanded', 'false');
      toggleBtn.innerHTML = '☰';
      document.body.style.overflow = '';
    }
  }

  toggleBtn.addEventListener('click', function (e) {
    e.stopPropagation();
    toggleMenu();
  });

  if (backdrop) {
    backdrop.addEventListener('click', function () {
      toggleMenu(false);
    });
  }

  // Close on Escape
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && drawer.classList.contains('open')) {
      toggleMenu(false);
    }
  });

  // Close on window resize if larger than mobile breakpoint
  window.addEventListener('resize', function () {
    if (window.innerWidth > 768 && drawer.classList.contains('open')) {
      toggleMenu(false);
    }
  });
}

/**
 * Auto-dismiss Flash Alerts
 */
function initAlertDismissal() {
  const alerts = document.querySelectorAll('.alert-item, .alert-toast');
  alerts.forEach(function (alert) {
    // Add close button if not present
    if (!alert.querySelector('.alert-close')) {
      const closeBtn = document.createElement('button');
      closeBtn.type = 'button';
      closeBtn.className = 'alert-close';
      closeBtn.innerHTML = '&times;';
      closeBtn.setAttribute('aria-label', 'Close alert');
      closeBtn.onclick = function () {
        dismissAlert(alert);
      };
      alert.appendChild(closeBtn);
    } else {
      const existingBtn = alert.querySelector('.alert-close');
      existingBtn.onclick = function () {
        dismissAlert(alert);
      };
    }

    // Auto dismiss after 5.5s
    setTimeout(function () {
      dismissAlert(alert);
    }, 5500);
  });
}

function dismissAlert(alertEl) {
  if (!alertEl || !alertEl.parentElement) return;
  alertEl.style.transition = 'opacity 0.25s ease, transform 0.25s ease, max-height 0.25s ease, margin 0.25s ease, padding 0.25s ease';
  alertEl.style.opacity = '0';
  alertEl.style.transform = 'translateY(-10px)';
  alertEl.style.maxHeight = alertEl.offsetHeight + 'px';
  
  setTimeout(function () {
    alertEl.style.maxHeight = '0';
    alertEl.style.paddingTop = '0';
    alertEl.style.paddingBottom = '0';
    alertEl.style.marginTop = '0';
    alertEl.style.marginBottom = '0';
    setTimeout(function () {
      if (alertEl.parentElement) {
        alertEl.remove();
      }
    }, 250);
  }, 250);
}

/**
 * Generic Modal Lightbox Handlers
 */
function initModals() {
  // Close modals on overlay click or elements with data-modal-close
  document.querySelectorAll('.modal-overlay').forEach(function (modal) {
    modal.addEventListener('click', function (e) {
      if (e.target === modal) {
        closeModal(modal.id);
      }
    });
  });

  document.querySelectorAll('[data-modal-close]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      const modalId = btn.getAttribute('data-modal-close');
      closeModal(modalId);
    });
  });
}

function openModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.add('show');
    document.body.style.overflow = 'hidden';
  }
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.remove('show');
    document.body.style.overflow = '';
  }
}

// Attach to window for inline onclick compatibility
window.openModal = openModal;
window.closeModal = closeModal;
window.dismissAlert = dismissAlert;
