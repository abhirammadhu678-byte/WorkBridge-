document.addEventListener("DOMContentLoaded", function () {
  const form = document.getElementById("workCompletionForm");
  if (!form) return;

  const completionDate = document.getElementById("completion_date");
  const status = document.getElementById("work_status");
  const remarks = document.getElementById("remarks");
  const formErrorsDiv = document.getElementById("form-errors");

  function clearErrors() {
    formErrorsDiv.innerHTML = "";
    const fieldErrors = document.querySelectorAll(".field-error");
    fieldErrors.forEach((el) => (el.textContent = ""));
  }

  form.addEventListener("submit", function (e) {
    clearErrors();
    const errors = [];

    // Completion date validation
    if (!completionDate.value) {
      errors.push("Completion date is required.");
    } else {
      const selected = new Date(completionDate.value);
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      if (selected > today) {
        errors.push("Completion date cannot be in the future.");
      }
    }

    // Status validation
    if (!status.value) {
      errors.push("Please select a work status.");
    }

    // Remarks rules: require remarks when status is not 'Completed'
    if (status.value && status.value !== "Completed") {
      if (!remarks.value || !remarks.value.trim()) {
        errors.push("Remarks are required when work is not fully completed.");
        const rerr = document.getElementById("remarks-error");
        if (rerr) rerr.textContent = "Required for selected status.";
      }
    }

    // Remarks max length
    if (remarks.value && remarks.value.length > 1000) {
      errors.push("Remarks cannot exceed 1000 characters.");
      const rerr = document.getElementById("remarks-error");
      if (rerr) rerr.textContent = "Max 1000 characters.";
    }

    if (errors.length) {
      e.preventDefault();
      formErrorsDiv.innerHTML =
        "<ul>" +
        errors
          .map(function (msg) {
            return "<li>" + msg + "</li>";
          })
          .join("") +
        "</ul>";
      formErrorsDiv.focus && formErrorsDiv.focus();
      return false;
    }
  });

  // Clear errors as user interacts
  [completionDate, status, remarks].forEach(function (el) {
    if (!el) return;
    el.addEventListener("input", function () {
      formErrorsDiv.innerHTML = "";
      const rerr = document.getElementById("remarks-error");
      if (rerr) rerr.textContent = "";
    });
    el.addEventListener("change", function () {
      formErrorsDiv.innerHTML = "";
    });
  });
});
