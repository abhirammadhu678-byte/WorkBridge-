document.addEventListener("DOMContentLoaded", function () {
  const form = document.getElementById("ratingReviewForm");
  if (!form) return;

  const rating = document.getElementById("rating");
  const review = document.getElementById("review_comment");
  const formErrorsDiv = document.getElementById("form-errors");

  function clearErrors() {
    if (formErrorsDiv) formErrorsDiv.innerHTML = "";
    const fieldErrors = document.querySelectorAll(".field-error");
    fieldErrors.forEach((el) => (el.textContent = ""));
  }

  form.addEventListener("submit", function (e) {
    clearErrors();
    const errors = [];

    // Rating required and range
    if (!rating.value) {
      errors.push("Please select a rating between 1 and 5.");
    } else {
      const val = parseInt(rating.value, 10);
      if (isNaN(val) || val < 1 || val > 5) {
        errors.push("Invalid rating selected.");
      }
    }

    // Require review when rating is less than 5
    if (rating.value && parseInt(rating.value, 10) < 5) {
      if (!review.value || !review.value.trim()) {
        errors.push("Please provide a review comment for ratings less than 5.");
        const rerr = document.getElementById("review-error");
        if (rerr) rerr.textContent = "Required for ratings below 5.";
      }
    }

    // Max length
    if (review.value && review.value.length > 1000) {
      errors.push("Review comment cannot exceed 1000 characters.");
      const rerr = document.getElementById("review-error");
      if (rerr) rerr.textContent = "Max 1000 characters.";
    }

    if (errors.length) {
      e.preventDefault();
      formErrorsDiv.innerHTML =
        "<ul>" +
        errors
          .map(function (m) {
            return "<li>" + m + "</li>";
          })
          .join("") +
        "</ul>";
      formErrorsDiv.focus && formErrorsDiv.focus();
      return false;
    }
  });

  [rating, review].forEach(function (el) {
    if (!el) return;
    el.addEventListener("input", function () {
      if (formErrorsDiv) formErrorsDiv.innerHTML = "";
      const rerr = document.getElementById("review-error");
      if (rerr) rerr.textContent = "";
    });
    el.addEventListener("change", function () {
      if (formErrorsDiv) formErrorsDiv.innerHTML = "";
    });
  });
});
