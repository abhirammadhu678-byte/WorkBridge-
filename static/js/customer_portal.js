/**
 * WorkBridgeMini - Customer Portal Interactive Scripts
 */

document.addEventListener('DOMContentLoaded', function () {
  // =========================================================
  // 1. STAR RATING INTERACTION
  // =========================================================
  const starButtons = document.querySelectorAll('.star-btn');
  const ratingInput = document.getElementById('rating') || document.getElementById('rating_input');
  const ratingLabel = document.getElementById('rating_label_display');

  const ratingDescriptions = {
    1: '⭐ 1 Star - Poor Experience',
    2: '⭐⭐ 2 Stars - Needs Improvement',
    3: '⭐⭐⭐ 3 Stars - Good / Average Work',
    4: '⭐⭐⭐⭐ 4 Stars - Very Good & Reliable',
    5: '⭐⭐⭐⭐⭐ 5 Stars - Outstanding Performance!'
  };

  if (starButtons.length && ratingInput) {
    function highlightStars(val) {
      starButtons.forEach(btn => {
        const starVal = parseInt(btn.getAttribute('data-value'), 10);
        if (starVal <= val) {
          btn.classList.add('active');
        } else {
          btn.classList.remove('active');
        }
      });
    }

    starButtons.forEach(btn => {
      btn.addEventListener('mouseenter', function () {
        const val = parseInt(this.getAttribute('data-value'), 10);
        starButtons.forEach(b => {
          const v = parseInt(b.getAttribute('data-value'), 10);
          if (v <= val) b.classList.add('hovered');
          else b.classList.remove('hovered');
        });
        if (ratingLabel) {
          ratingLabel.textContent = ratingDescriptions[val] || '';
        }
      });

      btn.addEventListener('mouseleave', function () {
        starButtons.forEach(b => b.classList.remove('hovered'));
        const currentVal = parseInt(ratingInput.value, 10) || 0;
        highlightStars(currentVal);
        if (ratingLabel) {
          ratingLabel.textContent = currentVal ? (ratingDescriptions[currentVal] || '') : 'Click to select rating';
        }
      });

      btn.addEventListener('click', function (e) {
        e.preventDefault();
        const val = parseInt(this.getAttribute('data-value'), 10);
        ratingInput.value = val;
        highlightStars(val);
        if (ratingLabel) {
          ratingLabel.textContent = ratingDescriptions[val] || '';
        }
        // Remove error if any
        const err = document.getElementById('rating-error');
        if (err) err.textContent = '';
      });
    });

    // Initial highlight if value exists
    if (ratingInput.value) {
      const initialVal = parseInt(ratingInput.value, 10);
      highlightStars(initialVal);
      if (ratingLabel) {
        ratingLabel.textContent = ratingDescriptions[initialVal] || '';
      }
    }
  }

  // =========================================================
  // 2. MODAL & LIGHTBOX HANDLER
  // =========================================================
  const modalOverlay = document.getElementById('globalModal');
  const modalImage = document.getElementById('modalImage');
  const modalTitle = document.getElementById('modalTitle');
  const modalDesc = document.getElementById('modalDesc');
  const modalCloseBtn = document.getElementById('modalCloseBtn');

  window.openImageModal = function (src, title, desc) {
    if (!modalOverlay || !modalImage) return;
    modalImage.src = src;
    if (modalTitle) modalTitle.textContent = title || 'Portfolio Showcase';
    if (modalDesc) modalDesc.textContent = desc || '';
    modalOverlay.classList.add('active');
    document.body.style.overflow = 'hidden';
  };

  window.closeGlobalModal = function () {
    if (!modalOverlay) return;
    modalOverlay.classList.remove('active');
    document.body.style.overflow = '';
    if (modalImage) modalImage.src = '';
  };

  if (modalCloseBtn) {
    modalCloseBtn.addEventListener('click', closeGlobalModal);
  }

  if (modalOverlay) {
    modalOverlay.addEventListener('click', function (e) {
      if (e.target === modalOverlay) {
        closeGlobalModal();
      }
    });
  }

  // =========================================================
  // 3. DATE RESTRICTIONS & FORM VALIDATION
  // =========================================================
  const todayStr = new Date().toISOString().split('T')[0];

  // Job post work_date should not be past
  const jobWorkDateInput = document.getElementById('id_work_date') || document.querySelector('input[name="work_date"]');
  if (jobWorkDateInput) {
    jobWorkDateInput.setAttribute('min', todayStr);
  }

  // Work completion completion_date should not be future
  const completionDateInput = document.getElementById('completion_date') || document.querySelector('input[name="completion_date"]');
  if (completionDateInput) {
    completionDateInput.setAttribute('max', todayStr);
    if (!completionDateInput.value) {
      completionDateInput.value = todayStr;
    }
  }

  // =========================================================
  // 4. LIVE CLIENT-SIDE FILTER FOR MY JOBS
  // =========================================================
  const jobFilterInput = document.getElementById('jobSearchInput');
  const jobDurationFilter = document.getElementById('jobDurationFilter');
  const jobCards = document.querySelectorAll('.job-item-card');

  function filterJobCards() {
    if (!jobCards.length) return;
    const query = jobFilterInput ? jobFilterInput.value.toLowerCase().trim() : '';
    const duration = jobDurationFilter ? jobDurationFilter.value : '';

    let visibleCount = 0;
    jobCards.forEach(card => {
      const title = card.getAttribute('data-title') || '';
      const location = card.getAttribute('data-location') || '';
      const skills = card.getAttribute('data-skills') || '';
      const cardDuration = card.getAttribute('data-duration') || '';

      const matchQuery = !query || title.includes(query) || location.includes(query) || skills.includes(query);
      const matchDuration = !duration || cardDuration === duration;

      if (matchQuery && matchDuration) {
        card.style.display = '';
        visibleCount++;
      } else {
        card.style.display = 'none';
      }
    });

    const emptyFilterNotice = document.getElementById('filterEmptyState');
    if (emptyFilterNotice) {
      emptyFilterNotice.style.display = visibleCount === 0 ? 'block' : 'none';
    }
  }

  if (jobFilterInput) jobFilterInput.addEventListener('input', filterJobCards);
  if (jobDurationFilter) jobDurationFilter.addEventListener('change', filterJobCards);

  // =========================================================
  // 5. LIVE CLIENT-SIDE FILTER FOR APPLICANTS
  // =========================================================
  const applicantFilterInput = document.getElementById('applicantSearchInput');
  const applicantStatusFilter = document.getElementById('applicantStatusFilter');
  const applicantItems = document.querySelectorAll('.applicant-item-filter');

  function filterApplicants() {
    if (!applicantItems.length) return;
    const query = applicantFilterInput ? applicantFilterInput.value.toLowerCase().trim() : '';
    const status = applicantStatusFilter ? applicantStatusFilter.value : '';

    applicantItems.forEach(item => {
      const name = (item.getAttribute('data-name') || '').toLowerCase();
      const skills = (item.getAttribute('data-skills') || '').toLowerCase();
      const college = (item.getAttribute('data-college') || '').toLowerCase();
      const itemStatus = item.getAttribute('data-status') || '';

      const matchQuery = !query || name.includes(query) || skills.includes(query) || college.includes(query);
      const matchStatus = !status || itemStatus === status;

      if (matchQuery && matchStatus) {
        item.style.display = '';
      } else {
        item.style.display = 'none';
      }
    });
  }

  if (applicantFilterInput) applicantFilterInput.addEventListener('input', filterApplicants);
  if (applicantStatusFilter) applicantStatusFilter.addEventListener('change', filterApplicants);
});
